"""Fail-closed, read-only projections over persisted memory history.

The projector reads frozen recall slices, terminal writeback receipts, and the
append-only earned ledger.  It never builds recall, refreshes repository
knowledge, dispatches an agent, or writes a terminal outcome.  CLI, MCP, and
HTTP adapters all call the functions in this module and serialize the returned
document with :func:`render_memory_projection`.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Iterable, Mapping, Optional

from . import repofacts
from .decision_basis import (
    DECISION_BASIS_EVENT,
    decision_subject,
    read_decision_bases,
)
from .knowledge import (
    EARNED_RECORD_KINDS,
    MEMORY_DOCUMENT_BYTE_CAPS,
    MEMORY_DOCUMENT_FIELDS,
    MEMORY_DOCUMENT_ITEM_CAPS,
    MEMORY_STATES,
    MEMORY_WRITEBACK_KIND,
    TERMINAL_OUTCOME_KIND,
    TERMINAL_OUTCOME_STATES,
    EarnedRecordStore,
    KnowledgeRefusal,
    decode_identifier_list,
)
from .knowledge_writeback import (
    MEMORY_WRITEBACK_STATUS_KIND,
    MEMORY_WRITEBACK_STATUS_SCHEMA_VERSION,
)
from .memory_dispatch import (
    AUDIENCES,
    MemoryRecallActionNeeded,
    _read_json as _read_recall_json,
    _sha,
    _validate_manifest,
    _validate_recall,
)
from .model import DwError


MEMORY_READ_KIND = "delivery-workbench-memory-read"
MEMORY_WRITEBACK_INVENTORY_KIND = "delivery-workbench-memory-writebacks"
MEMORY_RECORD_KIND = "delivery-workbench-memory-record"
MEMORY_READ_SCHEMA_VERSION = 1
MEMORY_READ_GROUPS = (
    "recalled", "used-as-basis", "written-back", "superseded", "excluded",
)
MEMORY_REFUSAL_REASONS = ("missing", "stale", "malformed", "tampered")
_AUTHORITY_MARKERS = {
    "starts_work": False,
    "authorizes": False,
    "satisfies_gate": False,
    "substitutes_for_evidence": False,
}
_STATUS_KEYS = {
    "kind", "schema_version", "terminal_event_ref", "status",
    "writeback_id", "record_hash", "reason",
}
_AUTHORITY_KEYS = tuple(_AUTHORITY_MARKERS)
_LIST_FIELDS = (
    "story_ids", "recalled_memory_ids", "decision_refs", "evidence_refs",
    "check_refs", "changed_files", "failure_signatures",
    "accepted_lesson_hashes",
)


class MemoryReadRefusal(DwError):
    """A complete persisted memory history cannot be returned safely."""

    def __init__(self, reason: str, message: str) -> None:
        if reason not in MEMORY_REFUSAL_REASONS:
            reason = "malformed"
        self.reason = reason
        super().__init__(message)


def render_memory_projection(document: Mapping[str, object]) -> str:
    """Return the canonical bytes shared by CLI and MCP text projections."""
    return json.dumps(
        document, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
        allow_nan=False,
    )


def _empty_groups() -> dict[str, list]:
    return {name: [] for name in MEMORY_READ_GROUPS}


def _refusal(kind: str, scope: Mapping[str, object], exc: BaseException) -> dict:
    reason = _refusal_reason(exc)
    return {
        "kind": kind,
        "schema_version": MEMORY_READ_SCHEMA_VERSION,
        "status": "refused",
        "scope": dict(scope),
        "refusal": {
            "kind": "delivery-workbench-memory-read-refusal",
            "reason": reason,
            "message": str(exc),
        },
        "groups": _empty_groups(),
        **_AUTHORITY_MARKERS,
    }


def _refusal_reason(exc: BaseException) -> str:
    if isinstance(exc, MemoryReadRefusal):
        return exc.reason
    if isinstance(exc, MemoryRecallActionNeeded):
        return exc.reason if exc.reason in MEMORY_REFUSAL_REASONS else "malformed"
    text = str(exc).casefold()
    if "stale" in text or "different subject" in text or "source revision changed" in text:
        return "stale"
    if "missing" in text or "not found" in text or "does not exist" in text:
        return "missing"
    if any(marker in text for marker in (
        "tamper", "hash", "identity", "differs", "chain integrity",
        "prev_hash", "short write", "orphan",
    )):
        return "tampered"
    return "malformed"


def _display_path(root: Path, path: Path) -> str:
    try:
        return str(path.resolve().relative_to(root.resolve()))
    except ValueError:
        return str(path.resolve())


def _earned_path(root: Path, record_kind: str) -> Path:
    return (
        repofacts.git_dir(root) / "pmo-knowledge" / "earned"
        / (record_kind + ".jsonl")
    )


def _json_object(path: Path, label: str) -> dict:
    if not path.is_file() or path.is_symlink():
        raise MemoryReadRefusal("missing", label + " is missing")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, ValueError) as exc:
        raise MemoryReadRefusal("malformed", label + " is not valid UTF-8 JSON") from exc
    if not isinstance(value, dict):
        raise MemoryReadRefusal("malformed", label + " must be a JSON object")
    return value


def _memory_directories(run_dir: Path) -> list[Path]:
    memory = run_dir / "memory"
    if memory.is_symlink() or (memory.exists() and not memory.is_dir()):
        raise MemoryReadRefusal("malformed", "memory store is unsafe")
    if not memory.is_dir():
        raise MemoryReadRefusal("missing", "persisted memory store is missing")
    result = []
    if (memory / "manifest.json").exists():
        result.append(memory)
    scopes = memory / "scopes"
    if scopes.exists():
        if scopes.is_symlink() or not scopes.is_dir():
            raise MemoryReadRefusal("malformed", "scoped memory store is unsafe")
        for scope in sorted(scopes.iterdir(), key=lambda item: item.name):
            if (
                scope.is_symlink() or not scope.is_dir()
                or not scope.name.startswith("scope-") or len(scope.name) != 30
                or any(char not in "0123456789abcdef" for char in scope.name[6:])
            ):
                raise MemoryReadRefusal("malformed", "scoped memory store has an unsafe entry")
            result.append(scope)
    if not result:
        raise MemoryReadRefusal("missing", "persisted memory recall manifest is missing")
    return result


def _read_recall_groups(root: Path, run_dir: Path) -> tuple[list[dict], list[dict]]:
    recalled = []
    excluded = []
    for memory in _memory_directories(run_dir):
        manifest_path = memory / "manifest.json"
        source_path = memory / "source.json"
        manifest = _validate_manifest(
            _read_recall_json(manifest_path, "memory recall manifest")
        )
        source = _read_recall_json(source_path, "memory recall source snapshot")
        source_hash = _sha(source)
        if manifest.get("source_hash") != source_hash:
            raise MemoryReadRefusal(
                "tampered", "memory recall source snapshot differs from its manifest"
            )
        expected_revision = _sha({
            "subject": manifest["subject"], "knowledge": source,
        })
        if manifest.get("source_revision") != expected_revision:
            raise MemoryReadRefusal(
                "stale", "memory recall source revision is stale"
            )
        source_heads = manifest.get("source_heads")
        if not isinstance(source_heads, dict):
            raise MemoryReadRefusal("malformed", "memory recall source heads are malformed")
        if (
            source_heads.get("knowledge_packet") != source_hash
            or source_heads.get("index_tree") != source.get("index_tree")
        ):
            raise MemoryReadRefusal(
                "stale", "memory recall source heads do not match the frozen source"
            )
        recalls_dir = memory / "recalls"
        if recalls_dir.is_symlink() or not recalls_dir.is_dir():
            raise MemoryReadRefusal("missing", "memory recall audience directory is missing")
        names = {
            path.name for path in recalls_dir.iterdir()
            if path.is_file() and not path.is_symlink()
        }
        expected_names = {audience + ".json" for audience in AUDIENCES}
        if names != expected_names or any(path.is_symlink() for path in recalls_dir.iterdir()):
            raise MemoryReadRefusal(
                "malformed", "memory recall audience inventory is incomplete or unexpected"
            )
        scope_name = None if memory == run_dir / "memory" else memory.name
        for audience in AUDIENCES:
            path = recalls_dir / (audience + ".json")
            document = _validate_recall(
                _read_recall_json(path, "memory recall audience slice"),
                manifest,
                audience,
            )
            for index, item in enumerate(document["items"]):
                source_ref = str(item["source_ref"])
                recalled.append({
                    **dict(item),
                    "record_hash": source_ref if _is_hash(source_ref) else None,
                    "recall_id": document["recall_id"],
                    "subject": document["subject"],
                    "audience": audience,
                    "ledger_coordinates": {
                        "path": _display_path(root, path),
                        "scope": scope_name,
                        "audience": audience,
                        "item_index": index,
                    },
                })
            for index, item in enumerate(document["exclusions"]):
                source_ref = str(item["source_ref"])
                excluded.append({
                    **dict(item),
                    "record_hash": source_ref if _is_hash(source_ref) else None,
                    "recall_id": document["recall_id"],
                    "subject": document["subject"],
                    "audience": audience,
                    "ledger_coordinates": {
                        "path": _display_path(root, path),
                        "scope": scope_name,
                        "audience": audience,
                        "exclusion_index": index,
                    },
                })
    return recalled, excluded


def _is_hash(value: object) -> bool:
    return (
        isinstance(value, str) and len(value) == 71 and value.startswith("sha256:")
        and all(char in "0123456789abcdef" for char in value[7:])
    )


def _validate_writeback_document(document: object) -> dict:
    expected = set(MEMORY_DOCUMENT_FIELDS[MEMORY_WRITEBACK_KIND])
    if not isinstance(document, dict) or set(document) != expected:
        raise MemoryReadRefusal("malformed", "memory writeback receipt has a non-exact shape")
    if document.get("kind") != MEMORY_WRITEBACK_KIND or document.get("schema_version") != 1:
        raise MemoryReadRefusal("malformed", "memory writeback receipt uses an unsupported contract")
    if any(document.get(key) is not False for key in _AUTHORITY_KEYS):
        raise MemoryReadRefusal("malformed", "memory writeback receipt claims forbidden authority")
    if document.get("origin_kind") not in {"run", "program"}:
        raise MemoryReadRefusal("malformed", "memory writeback origin kind is unsupported")
    if document.get("memory_state") not in MEMORY_STATES:
        raise MemoryReadRefusal("malformed", "memory writeback state is unsupported")
    if document.get("terminal_state") not in TERMINAL_OUTCOME_STATES:
        raise MemoryReadRefusal("malformed", "memory writeback terminal state is unsupported")
    if not _is_hash(document.get("subject")) or not _is_hash(document.get("source_revision")):
        raise MemoryReadRefusal("malformed", "memory writeback provenance is malformed")
    for field in _LIST_FIELDS:
        values = document.get(field)
        if not isinstance(values, list) or len(values) > MEMORY_DOCUMENT_ITEM_CAPS[MEMORY_WRITEBACK_KIND][field]:
            raise MemoryReadRefusal("malformed", "memory writeback %s is malformed" % field)
    if not isinstance(document.get("discarded_lesson_count"), int):
        raise MemoryReadRefusal("malformed", "memory writeback discarded count is malformed")
    unsigned = {
        "kind": document["kind"],
        "schema_version": document["schema_version"],
        **{
            key: value for key, value in document.items()
            if key not in {"kind", "schema_version", "writeback_id"}
        },
    }
    if document.get("writeback_id") != _sha(unsigned):
        raise MemoryReadRefusal("tampered", "memory writeback identity check failed")
    if len(render_memory_projection(document).encode("utf-8")) > MEMORY_DOCUMENT_BYTE_CAPS[MEMORY_WRITEBACK_KIND]["document"]:
        raise MemoryReadRefusal("malformed", "memory writeback receipt exceeds its byte cap")
    return document


def _record_document_matches(record: Mapping[str, object], document: Mapping[str, object]) -> bool:
    detail = record["detail"]
    if not isinstance(detail, Mapping):
        return False
    if (
        record.get("record_kind") != TERMINAL_OUTCOME_KIND
        or record.get("origin") != document.get("origin")
        or record.get("head_sha") != document.get("head_sha")
    ):
        return False
    scalar = {
        "receipt_id": document["writeback_id"],
        "subject": document["subject"],
        "terminal_state": document["terminal_state"],
        "memory_state": document["memory_state"],
        "discarded_lesson_count": str(document["discarded_lesson_count"]),
    }
    if any(detail.get(key) != value for key, value in scalar.items()):
        return False
    for field in _LIST_FIELDS:
        try:
            decoded = decode_identifier_list(str(detail.get(field, "")), field)
        except DwError:
            return False
        if decoded != document[field]:
            return False
    return True


def _origin_run_dir(root: Path, origin_kind: str, origin: str) -> Path:
    pattern = (
        r"^run-[0-9a-f]{24}$"
        if origin_kind == "run" else r"^program-[0-9a-f]{24}$"
    )
    if not re.fullmatch(pattern, origin or ""):
        raise MemoryReadRefusal("malformed", "unsafe %s run id" % origin_kind)
    git_dir = repofacts.git_dir(root).resolve()
    store_name = "pmo-orchestration" if origin_kind == "run" else "pmo-programs"
    runs = (git_dir / store_name / "runs").resolve()
    path = runs / origin
    if path.is_symlink():
        raise MemoryReadRefusal("malformed", "%s run path is unsafe" % origin_kind)
    if not path.is_dir():
        raise MemoryReadRefusal("missing", "%s run not found: %s" % (origin_kind, origin))
    if path.resolve().parent != runs:
        raise MemoryReadRefusal("malformed", "%s run path escapes its store" % origin_kind)
    return path


def _terminal_records(root: Path) -> list[dict]:
    return EarnedRecordStore(root).read(TERMINAL_OUTCOME_KIND)


def _writeback_entries(
    root: Path,
    records: Iterable[dict],
    *,
    run: Optional[str] = None,
    program: Optional[str] = None,
    story: Optional[str] = None,
    state: Optional[str] = None,
) -> list[dict]:
    records = list(records)
    superseded_by = {
        record["detail"]["supersedes"]: record["record_hash"]
        for record in records if record["detail"]["supersedes"]
    }
    selected = []
    for record in records:
        detail = record["detail"]
        origin = str(record["origin"])
        origin_kind = "program" if origin.startswith("program-") else "run"
        stories = decode_identifier_list(detail["story_ids"], "story_ids")
        if run is not None and (origin_kind != "run" or origin != run):
            continue
        if program is not None and (origin_kind != "program" or origin != program):
            continue
        if story is not None and story not in stories:
            continue
        if state is not None and state not in {detail["memory_state"], detail["terminal_state"]}:
            continue
        run_dir = _origin_run_dir(root, origin_kind, origin)
        memory = run_dir / "memory"
        receipt_path = memory / "writebacks" / (detail["receipt_id"][7:] + ".json")
        document = _validate_writeback_document(
            _json_object(receipt_path, "memory writeback receipt")
        )
        if not _record_document_matches(record, document):
            raise MemoryReadRefusal(
                "tampered", "memory writeback receipt differs from its earned record"
            )
        selected.append({
            "record_hash": record["record_hash"],
            "writeback_id": detail["receipt_id"],
            "origin_kind": origin_kind,
            "origin": origin,
            "story_ids": stories,
            "memory_state": detail["memory_state"],
            "terminal_state": detail["terminal_state"],
            "supersedes": detail["supersedes"] or None,
            "superseded_by": superseded_by.get(record["record_hash"]),
            "document": document,
            "ledger_coordinates": {
                "path": _display_path(
                    root,
                    _earned_path(root, TERMINAL_OUTCOME_KIND),
                ),
                "seq": record["seq"],
                "prev_hash": record["prev_hash"],
                "receipt_path": _display_path(root, receipt_path),
            },
        })
    return selected


def _validate_writeback_status(
    root: Path, run_dir: Path, entries: list[dict]
) -> None:
    memory = run_dir / "memory"
    status_path = memory / "writeback-status.json"
    receipt_dir = memory / "writebacks"
    has_receipts = receipt_dir.exists()
    if has_receipts and (receipt_dir.is_symlink() or not receipt_dir.is_dir()):
        raise MemoryReadRefusal("malformed", "memory writeback receipt store is unsafe")
    receipt_entries = list(receipt_dir.iterdir()) if has_receipts else []
    receipt_files = [
        path for path in receipt_entries if path.is_file() and not path.is_symlink()
    ]
    if any(
        path.is_symlink() or not path.is_file() or path.suffix != ".json"
        for path in receipt_entries
    ):
        raise MemoryReadRefusal(
            "malformed", "memory writeback receipt store has an unsafe entry"
        )
    if not entries and not receipt_files and not status_path.exists():
        return
    if not status_path.exists():
        raise MemoryReadRefusal("missing", "memory writeback status is missing")
    status = _json_object(status_path, "memory writeback status")
    if (
        set(status) != _STATUS_KEYS
        or status.get("kind") != MEMORY_WRITEBACK_STATUS_KIND
        or status.get("schema_version") != MEMORY_WRITEBACK_STATUS_SCHEMA_VERSION
    ):
        raise MemoryReadRefusal("malformed", "memory writeback status has a non-exact shape")
    if status.get("status") != "persisted":
        raise MemoryReadRefusal("malformed", "memory writeback requires operator repair")
    matching = [
        entry for entry in entries
        if entry["writeback_id"] == status.get("writeback_id")
        and entry["record_hash"] == status.get("record_hash")
        and entry["document"]["terminal_event_ref"] == status.get("terminal_event_ref")
    ]
    if len(matching) != 1:
        raise MemoryReadRefusal("tampered", "memory writeback status differs from persisted history")
    expected_receipts = {entry["writeback_id"][7:] + ".json" for entry in entries}
    actual_receipts = {path.name for path in receipt_files}
    if expected_receipts != actual_receipts:
        raise MemoryReadRefusal("tampered", "memory writeback receipt inventory is orphaned")


def _group_writebacks(entries: Iterable[dict]) -> tuple[list[dict], list[dict]]:
    written = []
    superseded = []
    for entry in entries:
        target = (
            superseded
            if entry["memory_state"] == "superseded" or entry["superseded_by"]
            else written
        )
        target.append(entry)
    return written, superseded


def _decision_entries(
    root: Path,
    run_dir: Path,
    origin_kind: str,
    origin: str,
    recalled: list[dict],
) -> tuple[list[dict], list[dict]]:
    """Verify receipt/ledger pairing and project recalled items actually cited."""
    documents = read_decision_bases(run_dir)
    if not documents:
        return [], []
    if origin_kind == "run":
        from .orchestration_run import _read_events
        events = _read_events(run_dir, origin)
    else:
        from .program_run import _events
        events = _events(run_dir, origin)
    event_by_hash = {str(event["event_hash"]): event for event in events}
    references = [
        event for event in events if event.get("event") == DECISION_BASIS_EVENT
    ]
    documents_by_id = {document["decision_id"]: document for document in documents}
    referenced_ids = []
    entries = []
    expected_subject = decision_subject(origin_kind, origin)
    for event in references:
        detail = event.get("detail")
        if not isinstance(detail, Mapping):
            raise MemoryReadRefusal("malformed", "decision basis ledger reference is malformed")
        decision_id = str(detail.get("decision_id") or "")
        document = documents_by_id.get(decision_id)
        if document is None:
            raise MemoryReadRefusal("tampered", "decision basis ledger reference is orphaned")
        if decision_id in referenced_ids:
            raise MemoryReadRefusal("tampered", "decision basis is referenced more than once")
        referenced_ids.append(decision_id)
        if (
            detail.get("decision_kind") != document["decision_kind"]
            or detail.get("basis_type") != document["basis_type"]
            or detail.get("resulting_ledger_event") != document["resulting_ledger_event"]
        ):
            raise MemoryReadRefusal("tampered", "decision basis differs from its ledger reference")
        result_event = event_by_hash.get(document["resulting_ledger_event"])
        if result_event is None or int(result_event["seq"]) >= int(event["seq"]):
            raise MemoryReadRefusal("tampered", "decision basis resulting event is absent or out of order")
        if document["subject"] != expected_subject:
            raise MemoryReadRefusal("stale", "decision basis belongs to a different subject")
        entries.append({
            **document,
            "event_id": decision_id,
            "origin_kind": origin_kind,
            "origin": origin,
            "originating_receipt_ref": (
                document["input_receipt_refs"][0]
                if document["input_receipt_refs"] else document["resulting_ledger_event"]
            ),
            "ledger_coordinates": {
                "path": _display_path(root, run_dir / "ledger.jsonl"),
                "result_seq": result_event["seq"],
                "reference_seq": event["seq"],
                "reference_event": event["event_hash"],
                "receipt_path": _display_path(
                    root,
                    run_dir / "memory" / "decisions" / (decision_id[7:] + ".json"),
                ),
            },
        })
    if set(referenced_ids) != set(documents_by_id):
        raise MemoryReadRefusal("tampered", "decision basis receipt inventory is orphaned")
    recalled_ids = {str(item.get("recall_id") or "") for item in recalled}
    for document in documents:
        if not set(document["memory_refs"]) <= recalled_ids:
            raise MemoryReadRefusal(
                "tampered", "decision basis cites memory outside frozen recall"
            )
    decisions_for_recall: dict[str, list[str]] = {}
    for document in documents:
        for recall_id in document["memory_refs"]:
            decisions_for_recall.setdefault(recall_id, []).append(document["decision_id"])
    used = []
    for item in recalled:
        refs = sorted(set(decisions_for_recall.get(str(item.get("recall_id") or ""), [])))
        if refs:
            used.append({**item, "decision_refs": refs})
    return sorted(entries, key=lambda item: (
        int(item["ledger_coordinates"]["result_seq"]), item["decision_id"]
    )), used


def _entry_matches(
    entry: Mapping[str, object],
    *,
    run: Optional[str],
    program: Optional[str],
    story: Optional[str],
    state: Optional[str],
) -> bool:
    if run is not None and (
        entry["origin_kind"] != "run" or entry["origin"] != run
    ):
        return False
    if program is not None and (
        entry["origin_kind"] != "program" or entry["origin"] != program
    ):
        return False
    if story is not None and story not in entry["story_ids"]:
        return False
    if state is not None and state not in {
        entry["memory_state"], entry["terminal_state"],
    }:
        return False
    return True


def build_memory_recall_projection(
    root: Path, *, run: Optional[str] = None, program: Optional[str] = None
) -> dict:
    """Read one run/program memory history without creating or refreshing it."""
    scope = {
        "kind": "program" if program is not None else "run",
        "id": program if program is not None else run,
    }
    try:
        if bool(run) == bool(program):
            raise MemoryReadRefusal(
                "malformed", "memory recall requires exactly one of run or program"
            )
        origin = str(program if program is not None else run)
        run_dir = _origin_run_dir(root, str(scope["kind"]), origin)
        recalled, excluded = _read_recall_groups(root, run_dir)
        records = [record for record in _terminal_records(root) if record["origin"] == origin]
        entries = _writeback_entries(
            root,
            records,
            **({"program": origin} if program is not None else {"run": origin}),
        )
        _validate_writeback_status(root, run_dir, entries)
        written, superseded = _group_writebacks(entries)
        decisions, used_as_basis = _decision_entries(
            root, run_dir, str(scope["kind"]), origin, recalled
        )
        return {
            "kind": MEMORY_READ_KIND,
            "schema_version": MEMORY_READ_SCHEMA_VERSION,
            "status": "ok",
            "scope": scope,
            "refusal": None,
            "groups": {
                "recalled": recalled,
                "used-as-basis": used_as_basis,
                "written-back": written,
                "superseded": superseded,
                "excluded": excluded,
            },
            "decisions": decisions,
            **_AUTHORITY_MARKERS,
        }
    except (DwError, KnowledgeRefusal, MemoryRecallActionNeeded, OSError, UnicodeError, ValueError) as exc:
        refused = _refusal(MEMORY_READ_KIND, scope, exc)
        refused["decisions"] = []
        return refused


def build_memory_writeback_projection(
    root: Path,
    *,
    run: Optional[str] = None,
    program: Optional[str] = None,
    story: Optional[str] = None,
    state: Optional[str] = None,
) -> dict:
    """List terminal writebacks with deterministic run/program/story/state filters."""
    scope = {
        "run": run, "program": program, "story": story, "state": state,
    }
    try:
        if run and program:
            raise MemoryReadRefusal(
                "malformed", "memory writebacks accepts at most one of run or program"
            )
        allowed_states = set(MEMORY_STATES) | set(TERMINAL_OUTCOME_STATES)
        if state is not None and state not in allowed_states:
            raise MemoryReadRefusal("malformed", "memory writeback state filter is unsupported")
        requested_dir = None
        if run is not None:
            requested_dir = _origin_run_dir(root, "run", run)
        elif program is not None:
            requested_dir = _origin_run_dir(root, "program", program)
        records = _terminal_records(root)
        all_entries = _writeback_entries(root, records)
        by_origin: dict[tuple[str, str], list[dict]] = {}
        for entry in all_entries:
            by_origin.setdefault(
                (entry["origin_kind"], entry["origin"]), []
            ).append(entry)
        for (origin_kind, origin), origin_entries in by_origin.items():
            _validate_writeback_status(
                root, _origin_run_dir(root, origin_kind, origin), origin_entries
            )
        if requested_dir is not None and not any(
            _entry_matches(
                entry, run=run, program=program, story=None, state=None
            )
            for entry in all_entries
        ):
            _validate_writeback_status(root, requested_dir, [])
        entries = [
            entry for entry in all_entries
            if _entry_matches(
                entry, run=run, program=program, story=story, state=state
            )
        ]
        return {
            "kind": MEMORY_WRITEBACK_INVENTORY_KIND,
            "schema_version": MEMORY_READ_SCHEMA_VERSION,
            "status": "ok",
            "filters": scope,
            "refusal": None,
            "writebacks": entries,
            "count": len(entries),
            **_AUTHORITY_MARKERS,
        }
    except (DwError, KnowledgeRefusal, MemoryRecallActionNeeded, OSError, UnicodeError, ValueError) as exc:
        refused = _refusal(MEMORY_WRITEBACK_INVENTORY_KIND, scope, exc)
        refused.pop("groups")
        refused["filters"] = refused.pop("scope")
        refused["writebacks"] = []
        refused["count"] = 0
        return refused


def build_memory_record_projection(root: Path, record_hash: str) -> dict:
    """Resolve one earned record hash after verifying every candidate chain."""
    scope = {"kind": "record", "id": record_hash}
    try:
        if not _is_hash(record_hash):
            raise MemoryReadRefusal("malformed", "memory record hash is malformed")
        matches = []
        records_by_kind = {}
        for record_kind in EARNED_RECORD_KINDS:
            records_by_kind[record_kind] = EarnedRecordStore(root).read(record_kind)
            matches.extend(
                record for record in records_by_kind[record_kind]
                if record["record_hash"] == record_hash
            )
        if len(matches) != 1:
            raise MemoryReadRefusal(
                "missing" if not matches else "tampered",
                "memory record not found" if not matches else "memory record hash is not unique",
            )
        record = matches[0]
        groups = _empty_groups()
        if record["record_kind"] == TERMINAL_OUTCOME_KIND:
            origin_records = [
                item for item in records_by_kind[TERMINAL_OUTCOME_KIND]
                if item["origin"] == record["origin"]
            ]
            origin_entries = _writeback_entries(root, origin_records)
            run_dir = _origin_run_dir(
                root,
                origin_entries[0]["origin_kind"],
                origin_entries[0]["origin"],
            )
            _validate_writeback_status(root, run_dir, origin_entries)
            entries = [
                entry for entry in origin_entries
                if entry["record_hash"] == record_hash
            ]
            written, superseded = _group_writebacks(entries)
            groups["written-back"] = written
            groups["superseded"] = superseded
        else:
            groups["recalled"] = [{
                "record_hash": record["record_hash"],
                "record_kind": record["record_kind"],
                "record": record,
                "ledger_coordinates": {
                    "path": _display_path(
                        root,
                        _earned_path(root, record["record_kind"]),
                    ),
                    "seq": record["seq"],
                    "prev_hash": record["prev_hash"],
                },
            }]
        return {
            "kind": MEMORY_RECORD_KIND,
            "schema_version": MEMORY_READ_SCHEMA_VERSION,
            "status": "ok",
            "scope": scope,
            "refusal": None,
            "groups": groups,
            **_AUTHORITY_MARKERS,
        }
    except (DwError, KnowledgeRefusal, MemoryRecallActionNeeded, OSError, UnicodeError, ValueError) as exc:
        return _refusal(MEMORY_RECORD_KIND, scope, exc)


def memory_http_status(document: Mapping[str, object]) -> int:
    """Map a typed read result to HTTP without changing its payload."""
    if document.get("status") == "ok":
        return 200
    refusal = document.get("refusal")
    reason = refusal.get("reason") if isinstance(refusal, Mapping) else None
    return 404 if reason == "missing" else 409
