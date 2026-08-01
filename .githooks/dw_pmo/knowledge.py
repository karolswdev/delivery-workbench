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
CERTIFIED_LESSON_KIND = "certified-handoff-lesson"
LESSON_DELIVERY_OBSERVATION_KIND = "lesson-delivery-observation"
TERMINAL_OUTCOME_KIND = "terminal-outcome"
LESSON_INVENTORY_KIND = "delivery-workbench-knowledge-lessons"
MEMORY_RECALL_KIND = "delivery-workbench-memory-recall"
MEMORY_WRITEBACK_KIND = "delivery-workbench-memory-writeback"
DECISION_BASIS_KIND = "delivery-workbench-decision-basis"
MEMORY_DOCUMENT_SCHEMA_VERSION = 1
EARNED_RECORD_KINDS = (
    DELIVERY_RECORD_KIND,
    LESSON_KIND,
    CERTIFIED_LESSON_KIND,
    LESSON_DELIVERY_OBSERVATION_KIND,
    TERMINAL_OUTCOME_KIND,
)
LESSON_DELIVERY_STATES = (
    "certified-not-integrated",
    "confirmed",
    "superseded",
)
MEMORY_STATES = ("confirmed", "candidate", "superseded")
TERMINAL_OUTCOME_STATES = (
    "complete",
    "succeeded",
    "failed",
    "cancelled",
    "revoked",
    "lost",
    "timed-out",
    "exhausted",
    "expired",
    "blocked",
    "refused",
    "awaiting-certification",
)
_SUCCESSFUL_TERMINAL_OUTCOMES = {"complete", "succeeded"}

DERIVED = "derived"
EARNED = "earned"
STORAGE_CLASSES = (DERIVED, EARNED)
KNOWLEDGE_ITEM_CLASSES = {
    DERIVED_FACT_KIND: DERIVED,
    DELIVERY_RECORD_KIND: EARNED,
    LESSON_KIND: EARNED,
    CERTIFIED_LESSON_KIND: EARNED,
    LESSON_DELIVERY_OBSERVATION_KIND: EARNED,
    TERMINAL_OUTCOME_KIND: EARNED,
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

# Exact scalar-only detail fields. Delivery identifiers are canonical JSON
# arrays encoded as bounded strings so the earned-record envelope remains
# scalar-only. They are produced by the ledger write-back adapter, never from
# agent prose. Lesson locations use the same convention for a closed list of
# resolved/unresolved references.
EARNED_RECORD_FIELDS = {
    DELIVERY_RECORD_KIND: (
        "story_ids", "story_count", "files_touched", "file_count",
        "verdict_outcome", "obligation_ids", "obligation_count",
    ),
    LESSON_KIND: ("claim", "locations", "confidence", "supersedes"),
    CERTIFIED_LESSON_KIND: (
        "receipt_id", "story", "subject", "adapter", "driver_profile",
        "verdict_ref", "delivery_state", "claim", "locations",
        "confidence", "supersedes",
    ),
    LESSON_DELIVERY_OBSERVATION_KIND: (
        "receipt_id", "lesson_receipt_id", "lesson_record_hash", "story",
        "subject", "delivery_state", "observed_commit",
    ),
    TERMINAL_OUTCOME_KIND: (
        "receipt_id", "subject", "terminal_state", "memory_state",
        "story_ids", "recalled_memory_ids", "decision_refs",
        "evidence_refs", "check_refs", "changed_files",
        "failure_signatures", "accepted_lesson_hashes",
        "discarded_lesson_count", "supersedes",
    ),
}
EARNED_FIELD_CAPS = {
    "story_ids": 2048,
    "story_count": 8,
    "files_touched": 8192,
    "file_count": 8,
    "verdict_outcome": 32,
    "obligation_ids": 2048,
    "obligation_count": 8,
    "claim": 1000,
    "locations": 8192,
    "confidence": 16,
    "supersedes": 80,
    "receipt_id": 71,
    "lesson_receipt_id": 71,
    "lesson_record_hash": 71,
    "story": 80,
    "subject": 71,
    "adapter": 80,
    "driver_profile": 200,
    "verdict_ref": 71,
    "delivery_state": 32,
    "observed_commit": 64,
    "terminal_state": 32,
    "memory_state": 16,
    "recalled_memory_ids": 8192,
    "decision_refs": 8192,
    "evidence_refs": 8192,
    "check_refs": 8192,
    "changed_files": 8192,
    "failure_signatures": 8192,
    "accepted_lesson_hashes": 8192,
    "discarded_lesson_count": 8,
}
_ORIGIN_KINDS = ("run", "operator")
_AUTHORITY_MARKERS = {
    "starts_work": False,
    "authorizes": False,
    "satisfies_gate": False,
    "substitutes_for_evidence": False,
}

# These are contract declarations for the documents built and persisted by the
# later memory stories. Closed top-level shapes and budgets live here so those
# adapters cannot invent broader or unbounded channels.
MEMORY_DOCUMENT_FIELDS = {
    MEMORY_RECALL_KIND: (
        "kind", "schema_version", "recall_id", "subject", "audience",
        "source_revision", "source_heads", "items", "exclusions",
        "byte_budget", "used_bytes", "starts_work", "authorizes",
        "satisfies_gate", "substitutes_for_evidence",
    ),
    MEMORY_WRITEBACK_KIND: (
        "kind", "schema_version", "writeback_id", "origin_kind", "origin",
        "terminal_state", "memory_state", "subject", "head_sha",
        "terminal_event_ref", "story_ids", "recalled_memory_ids",
        "decision_refs", "evidence_refs", "check_refs", "changed_files",
        "failure_signatures", "accepted_lesson_hashes",
        "discarded_lesson_count", "source_revision", "starts_work",
        "authorizes", "satisfies_gate", "substitutes_for_evidence",
    ),
    DECISION_BASIS_KIND: (
        "kind", "schema_version", "decision_id", "subject", "decision_kind",
        "basis_type", "outcome", "reason_code", "rule_ref", "score_ref",
        "input_receipt_refs", "memory_refs", "dissent_refs",
        "resulting_ledger_event", "source_revision", "starts_work",
        "authorizes", "satisfies_gate", "substitutes_for_evidence",
    ),
}
MEMORY_DOCUMENT_ID_FIELDS = {
    MEMORY_RECALL_KIND: "recall_id",
    MEMORY_WRITEBACK_KIND: "writeback_id",
    DECISION_BASIS_KIND: "decision_id",
}
MEMORY_DOCUMENT_BYTE_CAPS = {
    MEMORY_RECALL_KIND: {
        "document": 65536,
        "subject": 71,
        "audience": 32,
        "source_revision": 71,
        "source_heads": 8192,
        "items": 49152,
        "exclusions": 12288,
    },
    MEMORY_WRITEBACK_KIND: {
        "document": 65536,
        "origin": 200,
        "subject": 71,
        "terminal_event_ref": 200,
        "story_ids": 8192,
        "recalled_memory_ids": 8192,
        "decision_refs": 8192,
        "evidence_refs": 8192,
        "check_refs": 8192,
        "changed_files": 8192,
        "failure_signatures": 8192,
        "accepted_lesson_hashes": 8192,
        "source_revision": 71,
    },
    DECISION_BASIS_KIND: {
        "document": 32768,
        "subject": 71,
        "decision_kind": 64,
        "basis_type": 32,
        "outcome": 200,
        "reason_code": 80,
        "rule_ref": 200,
        "score_ref": 200,
        "input_receipt_refs": 8192,
        "memory_refs": 8192,
        "dissent_refs": 8192,
        "resulting_ledger_event": 200,
        "source_revision": 71,
    },
}
MEMORY_DOCUMENT_ITEM_CAPS = {
    MEMORY_RECALL_KIND: {
        "source_heads": 32,
        "items": 64,
        "match_reasons_per_item": 16,
        "exclusions": 128,
    },
    MEMORY_WRITEBACK_KIND: {
        "story_ids": 64,
        "recalled_memory_ids": 64,
        "decision_refs": 64,
        "evidence_refs": 64,
        "check_refs": 64,
        "changed_files": 256,
        "failure_signatures": 64,
        "accepted_lesson_hashes": 64,
    },
    DECISION_BASIS_KIND: {
        "input_receipt_refs": 64,
        "memory_refs": 64,
        "dissent_refs": 32,
    },
}
MEMORY_DOCUMENT_PROVENANCE_FIELDS = {
    MEMORY_RECALL_KIND: ("subject", "source_revision", "source_heads"),
    MEMORY_WRITEBACK_KIND: (
        "origin_kind", "origin", "subject", "head_sha",
        "terminal_event_ref", "source_revision",
    ),
    DECISION_BASIS_KIND: (
        "subject", "input_receipt_refs", "memory_refs",
        "resulting_ledger_event", "source_revision",
    ),
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

    def _read_document(self, fact_kind: str) -> dict:
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
        return document

    def read(self, fact_kind: str, current_index_tree: str) -> dict:
        """Read only if the current repofacts index tree still matches."""
        _validate_git_object(current_index_tree, "current_index_tree")
        document = self._read_document(fact_kind)
        if document["index_tree"] != current_index_tree:
            raise StaleDerivedFact(
                fact_kind, document["index_tree"], current_index_tree
            )
        return document

    def refresh(self, fact_kind: str, current_index_tree: str, compute) -> dict:
        """Recompute a fact, exposing an old value only to the refresh callback.

        The callback receives the validated previous document, or ``None`` when
        no cache exists.  A stale document is never returned as an answer; it is
        available only inside this explicit recomputation path so incremental
        derivations can reuse unchanged blob-bound work.
        """
        _validate_git_object(current_index_tree, "current_index_tree")
        try:
            previous = self._read_document(fact_kind)
        except MissingDerivedFact:
            previous = None
        return self.write(fact_kind, current_index_tree, compute(previous))

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


def encode_identifier_list(values: object, field: str) -> str:
    """Encode a deterministic, duplicate-free list for a scalar detail field."""
    if not isinstance(values, (list, tuple, set)):
        raise DwError("earned record %s must be a list of identifiers" % field)
    normalized = []
    for value in values:
        normalized.append(_validate_identifier(value, field, 500))
    return _canonical_json(sorted(set(normalized)))


def decode_identifier_list(value: object, field: str) -> list:
    if not isinstance(value, str):
        raise DwError("earned record %s must be a canonical identifier list" % field)
    try:
        decoded = json.loads(value)
    except ValueError as exc:
        raise DwError("earned record %s must be a canonical identifier list" % field) from exc
    if not isinstance(decoded, list):
        raise DwError("earned record %s must be a canonical identifier list" % field)
    normalized = [
        _validate_identifier(item, field, 500)
        for item in decoded
    ]
    if decoded != sorted(set(normalized)) or value != _canonical_json(decoded):
        raise DwError("earned record %s identifiers must be sorted and unique" % field)
    return decoded


def encode_lesson_locations(locations: object) -> str:
    if not isinstance(locations, list):
        raise DwError("lesson locations must be a list")
    if not locations or len(locations) > 8:
        raise DwError("lesson locations must contain between 1 and 8 references")
    # Validation also guarantees every nested field is closed and bounded.
    encoded = _canonical_json(locations)
    decode_lesson_locations(encoded)
    return encoded


def decode_lesson_locations(value: object) -> list:
    if not isinstance(value, str):
        raise DwError("lesson locations must be a canonical location list")
    try:
        locations = json.loads(value)
    except ValueError as exc:
        raise DwError("lesson locations must be a canonical location list") from exc
    if not isinstance(locations, list) or not locations or len(locations) > 8:
        raise DwError("lesson locations must contain between 1 and 8 references")
    for location in locations:
        if not isinstance(location, dict):
            raise DwError("lesson location must be an object")
        status = location.get("status")
        expected = (
            {"reference", "status", "file", "symbol", "line_start", "line_end"}
            if status == "resolved"
            else {"reference", "status", "reason"}
        )
        if set(location) != expected or status not in {"resolved", "unresolved"}:
            raise DwError("lesson location has non-exact fields")
        _validate_identifier(location["reference"], "lesson location reference", 200)
        if status == "unresolved":
            _validate_identifier(location["reason"], "lesson location reason", 80)
            continue
        _validate_identifier(location["file"], "lesson location file", 500)
        symbol = location["symbol"]
        if not isinstance(symbol, str) or len(symbol) > 500 or "\x00" in symbol:
            raise DwError("lesson location symbol must be at most 500 chars")
        start = location["line_start"]
        end = location["line_end"]
        if (not isinstance(start, int) or isinstance(start, bool)
                or not isinstance(end, int) or isinstance(end, bool)
                or start < 0 or end < start):
            raise DwError("lesson location line span is invalid")
    if value != _canonical_json(locations):
        raise DwError("lesson locations must use canonical JSON")
    return locations


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
    if record_kind == DELIVERY_RECORD_KIND:
        stories = decode_identifier_list(detail["story_ids"], "story_ids")
        files = decode_identifier_list(detail["files_touched"], "files_touched")
        obligations = decode_identifier_list(detail["obligation_ids"], "obligation_ids")
        for count_field, values in (
            ("story_count", stories),
            ("file_count", files),
            ("obligation_count", obligations),
        ):
            if detail[count_field] != str(len(values)):
                raise DwError("earned record %s does not match its identifiers" % count_field)
        outcome = detail["verdict_outcome"]
        if any(not (char.isalnum() or char in "-_.") for char in outcome):
            raise DwError("earned record verdict_outcome must be an identifier")
    elif record_kind in {LESSON_KIND, CERTIFIED_LESSON_KIND}:
        decode_lesson_locations(detail["locations"])
        if detail["confidence"] not in {"low", "medium", "high"}:
            raise DwError("lesson confidence must be low, medium, or high")
        if record_kind == CERTIFIED_LESSON_KIND:
            if detail["delivery_state"] != "certified-not-integrated":
                raise DwError("certified lesson must start certified-not-integrated")
            for field in ("receipt_id", "subject", "verdict_ref"):
                if (
                    not detail[field].startswith("sha256:")
                    or len(detail[field]) != 71
                    or any(char not in "0123456789abcdef" for char in detail[field][7:])
                ):
                    raise DwError("certified lesson %s must be a sha256 reference" % field)
    elif record_kind == LESSON_DELIVERY_OBSERVATION_KIND:
        if detail["delivery_state"] not in {"confirmed", "superseded"}:
            raise DwError("lesson delivery observation state must be confirmed or superseded")
        for field in (
            "receipt_id", "lesson_receipt_id", "lesson_record_hash", "subject",
        ):
            if (
                not detail[field].startswith("sha256:")
                or len(detail[field]) != 71
                or any(char not in "0123456789abcdef" for char in detail[field][7:])
            ):
                raise DwError("lesson delivery observation %s must be a sha256 reference" % field)
        _validate_git_object(detail["observed_commit"], "observed_commit")
    else:
        for field in ("receipt_id", "subject"):
            if (
                not detail[field].startswith("sha256:")
                or len(detail[field]) != 71
                or any(char not in "0123456789abcdef" for char in detail[field][7:])
            ):
                raise DwError("terminal outcome %s must be a sha256 reference" % field)
        if detail["terminal_state"] not in TERMINAL_OUTCOME_STATES:
            raise DwError("terminal outcome has an unknown terminal state")
        if detail["memory_state"] not in MEMORY_STATES:
            raise DwError("terminal outcome memory state must be confirmed, candidate, or superseded")
        if (
            detail["memory_state"] == "confirmed"
            and detail["terminal_state"] not in _SUCCESSFUL_TERMINAL_OUTCOMES
        ):
            raise DwError("unsuccessful terminal outcome cannot confirm a lesson")
        if detail["memory_state"] == "superseded" and not detail["supersedes"]:
            raise DwError("superseded terminal outcome must reference an earlier outcome")
        for field in (
            "story_ids", "recalled_memory_ids", "decision_refs",
            "evidence_refs", "check_refs", "changed_files",
            "failure_signatures", "accepted_lesson_hashes",
        ):
            values = decode_identifier_list(detail[field], field)
            if field == "accepted_lesson_hashes":
                for value in values:
                    if (
                        not value.startswith("sha256:")
                        or len(value) != 71
                        or any(char not in "0123456789abcdef" for char in value[7:])
                    ):
                        raise DwError(
                            "terminal outcome accepted lesson must be a sha256 reference"
                        )
        try:
            discarded = int(detail["discarded_lesson_count"])
        except ValueError:
            raise DwError("terminal outcome discarded lesson count must be an integer")
        if discarded < 0 or str(discarded) != detail["discarded_lesson_count"]:
            raise DwError("terminal outcome discarded lesson count must be non-negative")
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
               origin: str, head_sha: str, timestamp: datetime = None,
               deduplicate: bool = False) -> dict:
        """Append one closed earned record; no update or rewrite API exists.

        ``deduplicate`` is the restart-safe write-back mode: while holding the
        earned-store lock, return an exact record already written by the same
        run and HEAD instead of appending it twice.
        """
        _validate_detail(record_kind, detail)
        if not isinstance(deduplicate, bool):
            raise DwError("earned record deduplicate must be boolean")
        timestamp_text = _format_timestamp(timestamp or _utc_now())
        _validate_provenance(origin_kind, origin, timestamp_text, head_sha)
        with _earned_lock(self.root) as directory:
            path = directory / self._filename(record_kind)
            if path.is_symlink():
                raise DwError("refusing symlinked earned record chain")
            records = _read_records(path, record_kind)
            if deduplicate:
                receipt_id = detail.get("receipt_id")
                receipt_match = next((
                    record for record in records
                    if receipt_id and record["detail"].get("receipt_id") == receipt_id
                ), None)
                if receipt_match is not None:
                    if (
                        receipt_match["origin_kind"] != origin_kind
                        or receipt_match["origin"] != origin
                        or receipt_match["detail"] != detail
                    ):
                        raise DwError("earned record receipt id collides with different content")
                    return receipt_match
                existing = next((
                    record for record in records
                    if record["origin_kind"] == origin_kind
                    and record["origin"] == origin
                    and record["head_sha"] == head_sha
                    and record["detail"] == detail
                ), None)
                if existing is not None:
                    return existing
            if record_kind in {LESSON_KIND, CERTIFIED_LESSON_KIND} and detail["supersedes"]:
                earlier = {record["record_hash"] for record in records}
                if record_kind == CERTIFIED_LESSON_KIND:
                    earlier.update(
                        record["record_hash"]
                        for record in _read_records(
                            directory / self._filename(LESSON_KIND), LESSON_KIND
                        )
                    )
                if detail["supersedes"] not in earlier:
                    raise DwError(
                        "lesson supersedes must reference an earlier lesson"
                    )
            if record_kind == TERMINAL_OUTCOME_KIND and detail["supersedes"]:
                earlier = {record["record_hash"] for record in records}
                if detail["supersedes"] not in earlier:
                    raise DwError(
                        "terminal outcome supersedes must reference an earlier outcome"
                    )
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


def read_lesson_knowledge(root: Path) -> list:
    """Read legacy and certified lessons with append-only delivery observations."""
    store = EarnedRecordStore(Path(root).resolve())
    lessons = store.read(LESSON_KIND) + store.read(CERTIFIED_LESSON_KIND)
    observations = store.read(LESSON_DELIVERY_OBSERVATION_KIND)
    latest = {}
    for observation in observations:
        lesson_hash = observation["detail"]["lesson_record_hash"]
        prior = latest.get(lesson_hash)
        if prior is None or (
            observation["timestamp"], observation["seq"]
        ) > (prior["timestamp"], prior["seq"]):
            latest[lesson_hash] = observation
    resolved = []
    for record in lessons:
        observation = latest.get(record["record_hash"])
        if observation is None:
            resolved.append(record)
            continue
        resolved.append({
            **record,
            "effective_delivery_state": observation["detail"]["delivery_state"],
            "delivery_observation": observation,
        })
    return sorted(resolved, key=lambda item: (item["timestamp"], item["record_hash"]))


def build_lesson_inventory(root: Path) -> dict:
    """List every earned lesson with provenance and supersession audit links."""
    records = read_lesson_knowledge(Path(root).resolve())
    superseded_by = {
        record["detail"]["supersedes"]: record["record_hash"]
        for record in records
        if record["detail"]["supersedes"]
    }
    return {
        "kind": LESSON_INVENTORY_KIND,
        "schema_version": KNOWLEDGE_SCHEMA_VERSION,
        "lessons": [
            {
                "record_hash": record["record_hash"],
                "seq": record["seq"],
                "claim": record["detail"]["claim"],
                "locations": decode_lesson_locations(
                    record["detail"]["locations"]
                ),
                "confidence": record["detail"]["confidence"],
                "supersedes": record["detail"]["supersedes"],
                "superseded_by": superseded_by.get(record["record_hash"]),
                "origin_kind": record["origin_kind"],
                "origin": record["origin"],
                "head_sha": record["head_sha"],
                "recorded_at": record["timestamp"],
                "age_label": "recorded-at:" + record["timestamp"],
                "delivery_state": record.get(
                    "effective_delivery_state",
                    record["detail"].get("delivery_state"),
                ),
                "receipt_id": record["detail"].get("receipt_id"),
                "story": record["detail"].get("story"),
                "subject": record["detail"].get("subject"),
                "adapter": record["detail"].get("adapter"),
                "driver_profile": record["detail"].get("driver_profile"),
                "verdict_ref": record["detail"].get("verdict_ref"),
                "delivery_observation": record.get("delivery_observation"),
            }
            for record in records
        ],
        "count": len(records),
        "active_count": sum(
            record["record_hash"] not in superseded_by for record in records
        ),
        **_AUTHORITY_MARKERS,
    }


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
        "memory_documents": {
            "%s@%d" % (kind, MEMORY_DOCUMENT_SCHEMA_VERSION): {
                "kind": kind,
                "schema_version": MEMORY_DOCUMENT_SCHEMA_VERSION,
                "closed_fields": list(MEMORY_DOCUMENT_FIELDS[kind]),
                "identity": {
                    "field": MEMORY_DOCUMENT_ID_FIELDS[kind],
                    "algorithm": "sha256-canonical-json",
                    "inputs": [
                        field for field in MEMORY_DOCUMENT_FIELDS[kind]
                        if field != MEMORY_DOCUMENT_ID_FIELDS[kind]
                    ],
                },
                "byte_caps": dict(MEMORY_DOCUMENT_BYTE_CAPS[kind]),
                "item_caps": dict(MEMORY_DOCUMENT_ITEM_CAPS[kind]),
                "provenance_references": list(
                    MEMORY_DOCUMENT_PROVENANCE_FIELDS[kind]
                ),
                "authority_fields": dict(_AUTHORITY_MARKERS),
            }
            for kind in sorted(MEMORY_DOCUMENT_FIELDS)
        },
        "memory_states": list(MEMORY_STATES),
        "memory_state_rules": {
            "terminal_states": list(TERMINAL_OUTCOME_STATES),
            "confirmed_terminal_states": sorted(_SUCCESSFUL_TERMINAL_OUTCOMES),
            "unsuccessful_terminal_states": "candidate-or-superseded-only",
            "superseded_requires": "earlier-terminal-outcome-record-hash",
        },
        "freshness": "derived-index-tree-must-equal-current-index-tree",
        "authority_exclusion": {
            "mints_authority": False,
            "satisfies_gate": False,
            "substitutes_for_evidence": False,
        },
        "offline": True,
        "stdlib_only": True,
    }
