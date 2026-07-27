"""Repository knowledge contract (docs/repository-knowledge.md).

Knowledge is advisory, never authority. No derived fact or earned record mints
permission, satisfies a gate rule, changes a verdict, or substitutes for
captured evidence. This module only stores bounded knowledge below
``.git/pmo-knowledge/`` and every stored document says so explicitly.

The two storage classes are structural:

* derived facts are disposable working-tree facts bound to the repofacts index
  tree that produced them; a stale read refuses or takes an explicit recompute
  path;
* earned records are provenance-stamped delivery records and lessons in
  append-only, hash-chained JSONL files whose closed shapes and caps are checked
  both before append and during every read.

The core is deterministic, standard-library-only, and offline. Wall-clock time
is used only to stamp earned provenance. It is never part of derived-fact
identity or computation.
"""

from __future__ import annotations

import fcntl
import hashlib
import json
import os
import tempfile
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

from . import repofacts
from .model import DwError


KNOWLEDGE_KIND = "delivery-workbench-repository-knowledge"
KNOWLEDGE_SCHEMA_VERSION = 1
DERIVED_FACT_KIND = "derived-fact"
DELIVERY_RECORD_KIND = "delivery-record"
LESSON_KIND = "lesson"
EARNED_RECORD_KINDS = (DELIVERY_RECORD_KIND, LESSON_KIND)

DERIVED = "derived"
EARNED = "earned"
STORAGE_CLASSES = (DERIVED, EARNED)
KNOWLEDGE_ITEM_CLASSES = {
    DERIVED_FACT_KIND: DERIVED,
    DELIVERY_RECORD_KIND: EARNED,
    LESSON_KIND: EARNED,
}

_DERIVED_DOCUMENT_KIND = "delivery-workbench-derived-fact"
_EARNED_DOCUMENT_KIND = "delivery-workbench-earned-record"
_DERIVED_KEYS = {
    "kind",
    "schema_version",
    "fact_kind",
    "index_tree",
    "value",
    "starts_work",
    "authorizes",
    "satisfies_gate",
    "substitutes_for_evidence",
    "fact_hash",
}
_EARNED_KEYS = {
    "kind",
    "schema_version",
    "record_kind",
    "seq",
    "origin_kind",
    "origin",
    "timestamp",
    "head_sha",
    "detail",
    "prev_hash",
    "starts_work",
    "authorizes",
    "satisfies_gate",
    "substitutes_for_evidence",
    "record_hash",
}

# Exact scalar-only detail fields. A later writer may only supply one of these
# closed records; adding a field is a contract-version decision.
EARNED_RECORD_FIELDS = {
    DELIVERY_RECORD_KIND: ("story_id", "outcome", "summary", "evidence_ref"),
    LESSON_KIND: ("subject", "lesson", "supersedes"),
}
EARNED_FIELD_CAPS = {
    "story_id": 64,
    "outcome": 32,
    "summary": 500,
    "evidence_ref": 500,
    "subject": 200,
    "lesson": 1000,
    "supersedes": 80,
}
_ORIGIN_KINDS = ("run", "operator")
_AUTHORITY_MARKERS = {
    "starts_work": False,
    "authorizes": False,
    "satisfies_gate": False,
    "substitutes_for_evidence": False,
}


class KnowledgeRefusal(DwError):
    """A knowledge read that cannot answer safely."""


class MissingDerivedFact(KnowledgeRefusal):
    """The disposable derived cache has no requested fact."""


class StaleDerivedFact(KnowledgeRefusal):
    """A derived fact belongs to a different repofacts index tree."""

    def __init__(self, fact_kind: str, stored_index_tree: str,
                 current_index_tree: str) -> None:
        self.fact_kind = fact_kind
        self.stored_index_tree = stored_index_tree
        self.current_index_tree = current_index_tree
        super().__init__(
            "derived fact %s is stale: stored index tree %s, current %s"
            % (fact_kind, stored_index_tree, current_index_tree)
        )


class MalformedKnowledge(KnowledgeRefusal):
    """Stored knowledge is malformed, unsafe, or has lost chain integrity."""


def storage_class(item_kind: str) -> str:
    """Classify every contract item kind, refusing undeclared kinds."""
    try:
        return KNOWLEDGE_ITEM_CLASSES[item_kind]
    except KeyError:
        raise DwError("unknown repository knowledge item kind: %s" % item_kind)


def _canonical_json(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False, allow_nan=False)


def _sha(value: object) -> str:
    return "sha256:" + hashlib.sha256(
        _canonical_json(value).encode("utf-8")
    ).hexdigest()


def _validate_identifier(value: object, field: str, cap: int = 80) -> str:
    if not isinstance(value, str) or not value or len(value) > cap:
        raise DwError("knowledge %s must be a non-empty string at most %d chars"
                      % (field, cap))
    if "\n" in value or "\r" in value or "\x00" in value:
        raise DwError("knowledge %s contains an unsafe character" % field)
    return value


def _validate_git_object(value: object, field: str) -> str:
    value = _validate_identifier(value, field, 64)
    if len(value) not in (40, 64) or any(c not in "0123456789abcdef" for c in value):
        raise DwError("knowledge %s must be a full Git object id" % field)
    return value


def _validate_json_value(value: object, field: str = "value") -> None:
    """Accept deterministic JSON values and reject floats or exotic objects."""
    if value is None or isinstance(value, (bool, int, str)):
        return
    if isinstance(value, list):
        for item in value:
            _validate_json_value(item, field)
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if not isinstance(key, str):
                raise DwError("knowledge %s object keys must be strings" % field)
            _validate_json_value(item, field)
        return
    raise DwError("knowledge %s must contain deterministic JSON values" % field)


def _knowledge_root(root: Path) -> Path:
    store = repofacts.git_dir(Path(root)) / "pmo-knowledge"
    if store.is_symlink() or (store.exists() and not store.is_dir()):
        raise DwError("refusing non-directory repository knowledge store")
    return store


def _store_directory(root: Path, name: str, create: bool = False) -> Path:
    store = _knowledge_root(root)
    directory = store / name
    if directory.is_symlink() or (directory.exists() and not directory.is_dir()):
        raise DwError("refusing non-directory %s knowledge store" % name)
    if create:
        store.mkdir(parents=True, exist_ok=True, mode=0o700)
        os.chmod(store, 0o700)
        directory.mkdir(exist_ok=True, mode=0o700)
        os.chmod(directory, 0o700)
    return directory


def _atomic_write(path: Path, value: object) -> None:
    fd, temp_name = tempfile.mkstemp(prefix=".%s." % path.name,
                                     dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(_canonical_json(value) + "\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(temp_name, 0o600)
        os.replace(temp_name, path)
    except OSError:
        try:
            os.unlink(temp_name)
        except OSError:
            pass
        raise


def _derived_document(fact_kind: str, index_tree: str, value: object) -> dict:
    """Build deterministic derived identity with no ambient input."""
    _validate_identifier(fact_kind, "fact_kind")
    _validate_git_object(index_tree, "index_tree")
    _validate_json_value(value)
    unsigned = {
        "kind": _DERIVED_DOCUMENT_KIND,
        "schema_version": KNOWLEDGE_SCHEMA_VERSION,
        "fact_kind": fact_kind,
        "index_tree": index_tree,
        "value": value,
        **_AUTHORITY_MARKERS,
    }
    return dict(unsigned, fact_hash=_sha(unsigned))


def _validate_derived(document: object) -> dict:
    if not isinstance(document, dict) or set(document) != _DERIVED_KEYS:
        raise MalformedKnowledge("derived fact has non-exact fields")
    if (document["kind"] != _DERIVED_DOCUMENT_KIND
            or document["schema_version"] != KNOWLEDGE_SCHEMA_VERSION):
        raise MalformedKnowledge("derived fact has the wrong contract identity")
    try:
        _validate_identifier(document["fact_kind"], "fact_kind")
        _validate_git_object(document["index_tree"], "index_tree")
        _validate_json_value(document["value"])
    except DwError as exc:
        raise MalformedKnowledge(str(exc)) from exc
    for key, expected in _AUTHORITY_MARKERS.items():
        if document[key] is not expected:
            raise MalformedKnowledge("derived fact violates authority exclusion")
    unsigned = {key: value for key, value in document.items()
                if key != "fact_hash"}
    if document["fact_hash"] != _sha(unsigned):
        raise MalformedKnowledge("derived fact hash check failed")
    return document


class DerivedFactStore:
    """Disposable index-tree-bound facts under ``derived/``."""

    def __init__(self, root: Path) -> None:
        self.root = Path(root)

    def _path(self, fact_kind: str, create: bool = False) -> Path:
        _validate_identifier(fact_kind, "fact_kind")
        directory = _store_directory(self.root, DERIVED, create=create)
        name = hashlib.sha256(fact_kind.encode("utf-8")).hexdigest() + ".json"
        path = directory / name
        if path.is_symlink():
            raise DwError("refusing symlinked derived fact")
        return path

    def write(self, fact_kind: str, index_tree: str, value: object) -> dict:
        """Replace one disposable cache entry with a fresh derivation."""
        document = _derived_document(fact_kind, index_tree, value)
        _atomic_write(self._path(fact_kind, create=True), document)
        return document

    def read(self, fact_kind: str, current_index_tree: str) -> dict:
        """Read only if the current repofacts index tree still matches."""
        _validate_git_object(current_index_tree, "current_index_tree")
        path = self._path(fact_kind)
        try:
            raw = path.read_text(encoding="utf-8")
        except FileNotFoundError:
            raise MissingDerivedFact("derived fact %s is not cached" % fact_kind)
        except OSError as exc:
            raise MalformedKnowledge("derived fact is unreadable") from exc
        try:
            document = json.loads(raw)
        except (UnicodeError, ValueError) as exc:
            raise MalformedKnowledge("derived fact is not valid JSON") from exc
        document = _validate_derived(document)
        if document["fact_kind"] != fact_kind:
            raise MalformedKnowledge("derived fact path and identity disagree")
        if document["index_tree"] != current_index_tree:
            raise StaleDerivedFact(
                fact_kind, document["index_tree"], current_index_tree
            )
        return document

    def read_or_recompute(self, fact_kind: str, current_index_tree: str,
                          compute) -> dict:
        """Use a fresh fact or explicitly recompute a missing/stale one."""
        try:
            return self.read(fact_kind, current_index_tree)
        except (MissingDerivedFact, StaleDerivedFact):
            return self.write(fact_kind, current_index_tree, compute())


def _utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(microsecond=0)


def _format_timestamp(value: datetime) -> str:
    if not isinstance(value, datetime) or value.tzinfo is None:
        raise DwError("earned record timestamp must be timezone-aware")
    utc = value.astimezone(timezone.utc).replace(microsecond=0)
    return utc.strftime("%Y-%m-%dT%H:%M:%SZ")


def _parse_timestamp(value: object) -> datetime:
    if not isinstance(value, str) or not value.endswith("Z"):
        raise DwError("earned record timestamp must be ISO-8601 UTC")
    try:
        parsed = datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError:
        raise DwError("earned record timestamp must be ISO-8601 UTC")
    if parsed.tzinfo is None or parsed.utcoffset().total_seconds() != 0:
        raise DwError("earned record timestamp must be ISO-8601 UTC")
    if _format_timestamp(parsed) != value:
        raise DwError("earned record timestamp must use whole-second UTC form")
    return parsed


def _validate_detail(record_kind: str, detail: object) -> dict:
    fields = EARNED_RECORD_FIELDS.get(record_kind)
    if fields is None:
        raise DwError("unknown earned record kind: %s" % record_kind)
    if not isinstance(detail, dict) or set(detail) != set(fields):
        raise DwError("earned record %s has non-exact detail fields" % record_kind)
    for field in fields:
        value = detail[field]
        cap = EARNED_FIELD_CAPS[field]
        if not isinstance(value, str) or len(value) > cap:
            raise DwError("earned record %s must be a string at most %d chars"
                          % (field, cap))
        if "\x00" in value:
            raise DwError("earned record %s contains an unsafe character" % field)
        if field != "supersedes" and not value:
            raise DwError("earned record %s may not be empty" % field)
    supersedes = detail.get("supersedes", "")
    if supersedes and (not supersedes.startswith("sha256:")
                       or len(supersedes) != 71
                       or any(c not in "0123456789abcdef"
                              for c in supersedes[7:])):
        raise DwError("lesson supersedes must reference an earned record hash")
    return detail


def _validate_provenance(origin_kind: object, origin: object,
                         timestamp: object, head_sha: object) -> datetime:
    if origin_kind not in _ORIGIN_KINDS:
        raise DwError("earned record origin_kind must be run or operator")
    _validate_identifier(origin, "origin", 200)
    parsed = _parse_timestamp(timestamp)
    _validate_git_object(head_sha, "head_sha")
    return parsed


def _earned_document(record_kind: str, seq: int, detail: dict,
                     origin_kind: str, origin: str, timestamp: str,
                     head_sha: str, prev_hash: object) -> dict:
    _validate_detail(record_kind, detail)
    _validate_provenance(origin_kind, origin, timestamp, head_sha)
    if not isinstance(seq, int) or isinstance(seq, bool) or seq < 0:
        raise DwError("earned record sequence must be a non-negative integer")
    if prev_hash is not None:
        _validate_identifier(prev_hash, "prev_hash", 71)
    unsigned = {
        "kind": _EARNED_DOCUMENT_KIND,
        "schema_version": KNOWLEDGE_SCHEMA_VERSION,
        "record_kind": record_kind,
        "seq": seq,
        "origin_kind": origin_kind,
        "origin": origin,
        "timestamp": timestamp,
        "head_sha": head_sha,
        "detail": detail,
        "prev_hash": prev_hash,
        **_AUTHORITY_MARKERS,
    }
    return dict(unsigned, record_hash=_sha(unsigned))


def _read_records(path: Path, record_kind: str) -> list:
    try:
        raw = path.read_bytes()
    except FileNotFoundError:
        return []
    except OSError as exc:
        raise MalformedKnowledge("earned record chain is unreadable") from exc
    if not raw or not raw.endswith(b"\n"):
        raise MalformedKnowledge("earned record chain is empty or truncated")
    records = []
    previous = None
    previous_time = None
    for offset, line in enumerate(raw.splitlines()):
        try:
            record = json.loads(line.decode("utf-8"))
        except (UnicodeDecodeError, ValueError) as exc:
            raise MalformedKnowledge(
                "earned record chain line %d is corrupt" % (offset + 1)
            ) from exc
        if not isinstance(record, dict) or set(record) != _EARNED_KEYS:
            raise MalformedKnowledge(
                "earned record chain line %d has non-exact fields" % (offset + 1)
            )
        if (record["kind"] != _EARNED_DOCUMENT_KIND
                or record["schema_version"] != KNOWLEDGE_SCHEMA_VERSION
                or record["record_kind"] != record_kind
                or record["seq"] != offset
                or record["prev_hash"] != previous):
            raise MalformedKnowledge(
                "earned record chain line %d breaks sequence or identity"
                % (offset + 1)
            )
        try:
            _validate_detail(record_kind, record["detail"])
            stamp = _validate_provenance(
                record["origin_kind"], record["origin"],
                record["timestamp"], record["head_sha"]
            )
        except DwError as exc:
            raise MalformedKnowledge(
                "earned record chain line %d is invalid: %s"
                % (offset + 1, exc)
            ) from exc
        for key, expected in _AUTHORITY_MARKERS.items():
            if record[key] is not expected:
                raise MalformedKnowledge(
                    "earned record chain line %d violates authority exclusion"
                    % (offset + 1)
                )
        unsigned = {key: value for key, value in record.items()
                    if key != "record_hash"}
        if record["record_hash"] != _sha(unsigned):
            raise MalformedKnowledge(
                "earned record chain line %d hash check failed" % (offset + 1)
            )
        if previous_time is not None and stamp < previous_time:
            raise MalformedKnowledge(
                "earned record chain line %d moves time backwards" % (offset + 1)
            )
        previous = record["record_hash"]
        previous_time = stamp
        records.append(record)
    return records


@contextmanager
def _earned_lock(root: Path):
    directory = _store_directory(root, EARNED, create=True)
    lock_path = directory / ".earned.lock"
    if lock_path.is_symlink():
        raise DwError("refusing symlinked earned knowledge lock")
    with lock_path.open("a+", encoding="utf-8") as handle:
        os.chmod(lock_path, 0o600)
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
        try:
            yield directory
        finally:
            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


class EarnedRecordStore:
    """Append-only, provenance-stamped records under ``earned/``."""

    def __init__(self, root: Path) -> None:
        self.root = Path(root)

    @staticmethod
    def _filename(record_kind: str) -> str:
        if record_kind not in EARNED_RECORD_KINDS:
            raise DwError("unknown earned record kind: %s" % record_kind)
        return record_kind + ".jsonl"

    def read(self, record_kind: str) -> list:
        """Read and re-verify every shape, cap, provenance stamp, and hash."""
        filename = self._filename(record_kind)
        directory = _store_directory(self.root, EARNED)
        path = directory / filename
        if path.is_symlink():
            raise MalformedKnowledge("refusing symlinked earned record chain")
        return _read_records(path, record_kind)

    def append(self, record_kind: str, detail: dict, *, origin_kind: str,
               origin: str, head_sha: str, timestamp: datetime = None) -> dict:
        """Append one closed earned record; no update or rewrite API exists."""
        _validate_detail(record_kind, detail)
        timestamp_text = _format_timestamp(timestamp or _utc_now())
        _validate_provenance(origin_kind, origin, timestamp_text, head_sha)
        with _earned_lock(self.root) as directory:
            path = directory / self._filename(record_kind)
            if path.is_symlink():
                raise DwError("refusing symlinked earned record chain")
            records = _read_records(path, record_kind)
            seq = len(records)
            prev_hash = records[-1]["record_hash"] if records else None
            # Whole-second UTC timestamps sort in chronological order.
            if records and timestamp_text < records[-1]["timestamp"]:
                raise DwError("earned record timestamp may not move backwards")
            document = _earned_document(
                record_kind, seq, dict(detail), origin_kind, origin,
                timestamp_text, head_sha, prev_hash
            )
            data = (_canonical_json(document) + "\n").encode("utf-8")
            with path.open("ab", buffering=0) as handle:
                os.chmod(path, 0o600)
                written = handle.write(data)
                if written != len(data):
                    raise DwError("short write while appending earned knowledge")
                os.fsync(handle.fileno())
            return document


def contract_document() -> dict:
    """Return the machine-readable ``repository-knowledge@1`` statement."""
    return {
        "kind": KNOWLEDGE_KIND,
        "schema_version": KNOWLEDGE_SCHEMA_VERSION,
        "contract": "%s@%d" % (KNOWLEDGE_KIND, KNOWLEDGE_SCHEMA_VERSION),
        "classes": {
            DERIVED: {
                "location": ".git/pmo-knowledge/derived/",
                "mutability": "disposable-cache",
                "provenance": ["repofacts-index-tree"],
                "deleting_changes": "latency-only",
            },
            EARNED: {
                "location": ".git/pmo-knowledge/earned/",
                "mutability": "append-only-jsonl",
                "provenance": ["origin-kind", "origin", "timestamp", "head-sha"],
                "deleting_changes": "history-only-no-authoritative-answer",
            },
        },
        "item_classes": dict(sorted(KNOWLEDGE_ITEM_CLASSES.items())),
        "earned_record_fields": {
            kind: list(fields)
            for kind, fields in sorted(EARNED_RECORD_FIELDS.items())
        },
        "earned_field_caps": dict(sorted(EARNED_FIELD_CAPS.items())),
        "freshness": "derived-index-tree-must-equal-current-index-tree",
        "authority_exclusion": {
            "mints_authority": False,
            "satisfies_gate": False,
            "substitutes_for_evidence": False,
        },
        "offline": True,
        "stdlib_only": True,
    }
