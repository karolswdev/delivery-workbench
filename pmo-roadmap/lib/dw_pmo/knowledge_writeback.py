"""Typed, terminal-only write-back into advisory earned knowledge.

This adapter may read repository knowledge to resolve lesson references and may
append earned records. It consumes a completed ledger projection; it never
returns a decision, verdict, grant, gate result, or evidence fact.
"""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Iterable, Mapping, Optional

from . import repofacts
from .knowledge import (
    CERTIFIED_LESSON_KIND,
    DELIVERY_RECORD_KIND,
    LESSON_DELIVERY_OBSERVATION_KIND,
    LESSON_KIND,
    MEMORY_DOCUMENT_BYTE_CAPS,
    MEMORY_DOCUMENT_FIELDS,
    MEMORY_DOCUMENT_ITEM_CAPS,
    MEMORY_DOCUMENT_SCHEMA_VERSION,
    MEMORY_STATES,
    MEMORY_WRITEBACK_KIND,
    TERMINAL_OUTCOME_KIND,
    TERMINAL_OUTCOME_STATES,
    EarnedRecordStore,
    KnowledgeRefusal,
    decode_identifier_list,
    encode_identifier_list,
    encode_lesson_locations,
)
from .model import DwError
from .repository_map import read_symbol_map


LESSON_OUTPUT_KIND = "delivery-workbench-lesson-output"
LESSON_OUTPUT_SCHEMA_VERSION = 1
LESSON_ARTIFACT_KIND = "lesson"
DEFAULT_MAX_LESSONS = 5
MAX_LESSONS_LIMIT = 50
MAX_LOCATION_REFERENCES = 8
CERTIFIED_HANDOFF_STATE = "story-certified"
CERTIFIED_HANDOFF_STOP = "integration-required"
CERTIFIED_NOT_INTEGRATED = "certified-not-integrated"
INTEGRATION_OBSERVATION_STATES = ("confirmed", "superseded")
_LESSON_DOCUMENT_KEYS = {"kind", "schema_version", "lessons"}
_LESSON_ITEM_KEYS = {"claim", "locations", "confidence", "supersedes"}
_CONFIDENCE = {"low", "medium", "high"}


def _identifier(value: object, label: str, cap: int) -> str:
    if not isinstance(value, str) or not value or len(value) > cap:
        raise DwError("%s must be a non-empty string at most %d chars" % (label, cap))
    if "\x00" in value or "\n" in value or "\r" in value:
        raise DwError("%s contains an unsafe character" % label)
    return value


def validate_lesson_output(document: object) -> dict:
    """Validate the only machine-output convention accepted for lessons."""
    if not isinstance(document, dict) or set(document) != _LESSON_DOCUMENT_KEYS:
        raise DwError("lesson output has non-exact fields")
    if (document["kind"] != LESSON_OUTPUT_KIND
            or document["schema_version"] != LESSON_OUTPUT_SCHEMA_VERSION):
        raise DwError("lesson output has the wrong contract identity")
    lessons = document["lessons"]
    if not isinstance(lessons, list) or len(lessons) > MAX_LESSONS_LIMIT:
        raise DwError("lesson output must contain at most %d lessons" % MAX_LESSONS_LIMIT)
    normalized = []
    for raw in lessons:
        if not isinstance(raw, dict) or set(raw) != _LESSON_ITEM_KEYS:
            raise DwError("lesson output item has non-exact fields")
        claim = _identifier(raw["claim"], "lesson claim", 1000)
        confidence = raw["confidence"]
        if confidence not in _CONFIDENCE:
            raise DwError("lesson confidence must be low, medium, or high")
        supersedes = raw["supersedes"]
        if not isinstance(supersedes, str) or len(supersedes) > 80:
            raise DwError("lesson supersedes must be a string at most 80 chars")
        if supersedes and (
            not supersedes.startswith("sha256:")
            or len(supersedes) != 71
            or any(char not in "0123456789abcdef" for char in supersedes[7:])
        ):
            raise DwError("lesson supersedes must reference an earned record hash")
        references = raw["locations"]
        if (
            not isinstance(references, list) or not references
            or len(references) > MAX_LOCATION_REFERENCES
        ):
            raise DwError("lesson locations must contain between 1 and 8 references")
        normalized.append({
            "claim": claim,
            "locations": [
                _identifier(item, "lesson location reference", 200)
                for item in references
            ],
            "confidence": confidence,
            "supersedes": supersedes,
        })
    return {
        "kind": LESSON_OUTPUT_KIND,
        "schema_version": LESSON_OUTPUT_SCHEMA_VERSION,
        "lessons": normalized,
    }


def parse_lesson_output(data: bytes) -> dict:
    try:
        text = data.decode("utf-8")
        document = json.loads(text)
    except (UnicodeDecodeError, ValueError) as exc:
        raise DwError("lesson output must be UTF-8 JSON") from exc
    return validate_lesson_output(document)


def _symbol_model(root: Path) -> Optional[dict]:
    try:
        return read_symbol_map(root, repofacts.Derivation(root))["value"]
    except (DwError, KnowledgeRefusal, OSError):
        return None


def resolve_lesson_locations(root: Path, references: Iterable[str]) -> str:
    """Resolve each declared reference or label it unresolved explicitly."""
    model = _symbol_model(Path(root).resolve())
    if model is None:
        return encode_lesson_locations([
            {
                "reference": reference,
                "status": "unresolved",
                "reason": "symbol-map-unavailable",
            }
            for reference in references
        ])
    symbols = [item for item in model.get("symbols", []) if isinstance(item, dict)]
    tracked = {
        str(item.get("path", ""))
        for item in model.get("tracked_files", [])
        if isinstance(item, dict)
    }
    resolved = []
    for reference in references:
        matches = [
            item for item in symbols
            if reference in {
                str(item.get("name", "")),
                str(item.get("qualified_name", "")),
            }
        ]
        if len(matches) == 1:
            item = matches[0]
            resolved.append({
                "reference": reference,
                "status": "resolved",
                "file": str(item["file"]),
                "symbol": str(item["qualified_name"]),
                "line_start": int(item["line_start"]),
                "line_end": int(item["line_end"]),
            })
        elif not matches and reference in tracked:
            resolved.append({
                "reference": reference,
                "status": "resolved",
                "file": reference,
                "symbol": "",
                "line_start": 0,
                "line_end": 0,
            })
        else:
            resolved.append({
                "reference": reference,
                "status": "unresolved",
                "reason": "ambiguous-symbol" if matches else "not-in-symbol-map",
            })
    return encode_lesson_locations(resolved)


def delivery_detail_from_projection(projection: object) -> dict:
    """Derive the closed delivery shape only from completed ledger facts."""
    if not isinstance(projection, dict) or projection.get("state") != "complete":
        raise DwError("delivery write-back requires a complete ledger projection")
    facts = projection.get("delivery_facts")
    if not isinstance(facts, dict):
        raise DwError("complete ledger projection has no delivery facts")
    stories = decode_identifier_list(
        encode_identifier_list(facts.get("story_ids"), "story_ids"), "story_ids"
    )
    files = decode_identifier_list(
        encode_identifier_list(facts.get("files_touched"), "files_touched"),
        "files_touched",
    )
    obligations = decode_identifier_list(
        encode_identifier_list(facts.get("obligation_ids"), "obligation_ids"),
        "obligation_ids",
    )
    outcome = _identifier(facts.get("verdict_outcome"), "verdict outcome", 32)
    return {
        "story_ids": encode_identifier_list(stories, "story_ids"),
        "story_count": str(len(stories)),
        "files_touched": encode_identifier_list(files, "files_touched"),
        "file_count": str(len(files)),
        "verdict_outcome": outcome,
        "obligation_ids": encode_identifier_list(obligations, "obligation_ids"),
        "obligation_count": str(len(obligations)),
    }


def persist_completed_program(
    root: Path,
    projection: object,
    lesson_documents: Iterable[dict],
    *,
    max_lessons: int = DEFAULT_MAX_LESSONS,
    timestamp: Optional[datetime] = None,
) -> dict:
    """Append delivery and bounded lessons only for a completed program.

    Restarting this seam is safe: exact records from the same run and HEAD are
    returned rather than appended again.
    """
    if not isinstance(projection, dict) or projection.get("state") != "complete":
        return {
            "status": "not-terminal-success",
            "delivery_records": 0,
            "lessons": 0,
            "discarded_lessons": 0,
        }
    if (not isinstance(max_lessons, int) or isinstance(max_lessons, bool)
            or not 0 <= max_lessons <= MAX_LESSONS_LIMIT):
        raise DwError("max_lessons must be between 0 and %d" % MAX_LESSONS_LIMIT)
    run_id = _identifier(projection.get("run_id"), "lesson run id", 200)
    facts = projection.get("delivery_facts")
    if not isinstance(facts, dict):
        raise DwError("complete ledger projection has no delivery facts")
    head_sha = _identifier(facts.get("head_sha"), "delivery HEAD", 64)
    store = EarnedRecordStore(Path(root).resolve())
    delivery = store.append(
        DELIVERY_RECORD_KIND,
        delivery_detail_from_projection(projection),
        origin_kind="run",
        origin=run_id,
        head_sha=head_sha,
        timestamp=timestamp,
        deduplicate=True,
    )
    emitted = []
    for document in lesson_documents:
        emitted.extend(validate_lesson_output(document)["lessons"])
    accepted = emitted[:max_lessons]
    records = []
    for lesson in accepted:
        detail = {
            "claim": lesson["claim"],
            "locations": resolve_lesson_locations(root, lesson["locations"]),
            "confidence": lesson["confidence"],
            "supersedes": lesson["supersedes"],
        }
        records.append(store.append(
            LESSON_KIND,
            detail,
            origin_kind="run",
            origin=run_id,
            head_sha=head_sha,
            timestamp=timestamp,
            deduplicate=True,
        ))
    lesson_hashes = list(dict.fromkeys(
        record["record_hash"] for record in records
    ))
    return {
        "status": "persisted",
        "delivery_records": 1,
        "delivery_record_hash": delivery["record_hash"],
        "lessons": len(lesson_hashes),
        "lesson_hashes": lesson_hashes,
        "deduplicated_lessons": len(records) - len(lesson_hashes),
        "discarded_lessons": len(emitted) - len(accepted),
    }


def _sha(value: object) -> str:
    encoded = json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def certified_lesson_receipt_id(
    terminal_receipt_id: str,
    ordinal: int,
    lesson: dict,
) -> str:
    """Derive one replay-stable lesson identity from the terminal receipt."""
    _identifier(terminal_receipt_id, "terminal lesson receipt id", 71)
    if not terminal_receipt_id.startswith("sha256:") or len(terminal_receipt_id) != 71:
        raise DwError("terminal lesson receipt id must be a sha256 reference")
    if not isinstance(ordinal, int) or isinstance(ordinal, bool) or ordinal < 0:
        raise DwError("certified lesson ordinal must be a non-negative integer")
    normalized = validate_lesson_output({
        "kind": LESSON_OUTPUT_KIND,
        "schema_version": LESSON_OUTPUT_SCHEMA_VERSION,
        "lessons": [lesson],
    })["lessons"][0]
    return _sha({
        "kind": "delivery-workbench-certified-lesson-receipt",
        "schema_version": 1,
        "terminal_receipt_id": terminal_receipt_id,
        "ordinal": ordinal,
        "lesson": normalized,
    })


def persist_certified_handoff(
    root: Path,
    *,
    run_id: str,
    story: str,
    subject: str,
    head_sha: str,
    verdict_ref: str,
    terminal_receipt_id: str,
    lesson_emissions: Iterable[dict],
    max_lessons: int = DEFAULT_MAX_LESSONS,
    frontier_state: str = CERTIFIED_HANDOFF_STATE,
    frontier_stop: str = CERTIFIED_HANDOFF_STOP,
    timestamp: Optional[datetime] = None,
) -> dict:
    """Persist bounded advisory lessons only at the exact certified handoff."""
    if (
        frontier_state != CERTIFIED_HANDOFF_STATE
        or frontier_stop != CERTIFIED_HANDOFF_STOP
    ):
        return {
            "status": "not-certified-handoff",
            "lessons": 0,
            "new_lessons": 0,
            "discarded_lessons": 0,
        }
    if (not isinstance(max_lessons, int) or isinstance(max_lessons, bool)
            or not 0 <= max_lessons <= MAX_LESSONS_LIMIT):
        raise DwError("max_lessons must be between 0 and %d" % MAX_LESSONS_LIMIT)
    run_id = _identifier(run_id, "certified lesson run id", 200)
    story = _identifier(story, "certified lesson story", 80)
    subject = _identifier(subject, "certified lesson subject", 71)
    verdict_ref = _identifier(verdict_ref, "certified lesson verdict", 71)
    _identifier(head_sha, "certified lesson HEAD", 64)
    _identifier(terminal_receipt_id, "terminal lesson receipt id", 71)

    emitted = []
    for raw in lesson_emissions:
        if not isinstance(raw, dict) or set(raw) != {
            "document", "adapter", "driver_profile", "emitter_receipt",
        }:
            raise DwError("certified lesson emission has non-exact fields")
        adapter = _identifier(raw["adapter"], "certified lesson adapter", 80)
        profile = _identifier(
            raw["driver_profile"], "certified lesson driver profile", 200
        )
        emitter = _identifier(
            raw["emitter_receipt"], "certified lesson emitter receipt", 71
        )
        for lesson in validate_lesson_output(raw["document"])["lessons"]:
            emitted.append((lesson, adapter, profile, emitter))
    accepted = emitted[:max_lessons]
    store = EarnedRecordStore(Path(root).resolve())
    existing_ids = {
        record["detail"]["receipt_id"]
        for record in store.read(CERTIFIED_LESSON_KIND)
    }
    records = []
    new_count = 0
    for ordinal, (lesson, adapter, profile, emitter) in enumerate(accepted):
        receipt_id = certified_lesson_receipt_id(
            terminal_receipt_id,
            ordinal,
            {**lesson, "supersedes": lesson["supersedes"]},
        )
        detail = {
            "receipt_id": receipt_id,
            "story": story,
            "subject": subject,
            "adapter": adapter,
            "driver_profile": profile,
            "verdict_ref": verdict_ref,
            "delivery_state": CERTIFIED_NOT_INTEGRATED,
            "claim": lesson["claim"],
            "locations": resolve_lesson_locations(root, lesson["locations"]),
            "confidence": lesson["confidence"],
            "supersedes": lesson["supersedes"],
        }
        record = store.append(
            CERTIFIED_LESSON_KIND,
            detail,
            origin_kind="run",
            origin=run_id,
            head_sha=head_sha,
            timestamp=timestamp,
            deduplicate=True,
        )
        records.append(record)
        if receipt_id not in existing_ids:
            new_count += 1
            existing_ids.add(receipt_id)
    return {
        "status": "persisted",
        "lessons": len(records),
        "new_lessons": new_count,
        "lesson_hashes": [record["record_hash"] for record in records],
        "receipt_ids": [record["detail"]["receipt_id"] for record in records],
        "deduplicated_lessons": len(records) - new_count,
        "discarded_lessons": len(emitted) - len(accepted),
    }


def observe_lesson_integration(
    root: Path,
    *,
    run_id: str,
    story: str,
    commit_sha: str,
    delivery_state: str = "confirmed",
    timestamp: Optional[datetime] = None,
) -> dict:
    """Append confirmation or supersession; never rewrite the candidate lesson."""
    if delivery_state not in INTEGRATION_OBSERVATION_STATES:
        raise DwError("lesson delivery observation state is not contracted")
    store = EarnedRecordStore(Path(root).resolve())
    candidates = [
        record for record in store.read(CERTIFIED_LESSON_KIND)
        if record["origin"] == run_id and record["detail"]["story"] == story
    ]
    existing_ids = {
        record["detail"]["receipt_id"]
        for record in store.read(LESSON_DELIVERY_OBSERVATION_KIND)
    }
    records = []
    new_count = 0
    for lesson in candidates:
        detail = lesson["detail"]
        receipt_id = _sha({
            "kind": "delivery-workbench-lesson-delivery-observation-receipt",
            "schema_version": 1,
            "lesson_receipt_id": detail["receipt_id"],
            "lesson_record_hash": lesson["record_hash"],
            "delivery_state": delivery_state,
            "observed_commit": commit_sha,
        })
        observation = store.append(
            LESSON_DELIVERY_OBSERVATION_KIND,
            {
                "receipt_id": receipt_id,
                "lesson_receipt_id": detail["receipt_id"],
                "lesson_record_hash": lesson["record_hash"],
                "story": story,
                "subject": detail["subject"],
                "delivery_state": delivery_state,
                "observed_commit": commit_sha,
            },
            origin_kind="run",
            origin=run_id,
            head_sha=commit_sha,
            timestamp=timestamp,
            deduplicate=True,
        )
        records.append(observation)
        if receipt_id not in existing_ids:
            new_count += 1
            existing_ids.add(receipt_id)
    return {
        "status": "observed" if candidates else "no-candidates",
        "delivery_state": delivery_state,
        "observations": len(records),
        "new_observations": new_count,
        "observation_hashes": [record["record_hash"] for record in records],
    }


MEMORY_WRITEBACK_STATUS_KIND = "delivery-workbench-memory-writeback-status"
MEMORY_WRITEBACK_STATUS_SCHEMA_VERSION = 1
_MEMORY_WRITEBACK_STATUS_KEYS = {
    "kind", "schema_version", "terminal_event_ref", "status",
    "writeback_id", "record_hash", "reason",
}
_AUTHORITY_MARKERS = {
    "starts_work": False,
    "authorizes": False,
    "satisfies_gate": False,
    "substitutes_for_evidence": False,
}
_SUCCESSFUL_WRITEBACK_STATES = {"complete", "succeeded"}
_TERMINAL_PROJECTION_STATES = {
    "complete", "blocked", "cancelled", "revoked", "awaiting-certification",
    "expired", "exhausted",
}


def _canonical_json(value: object) -> str:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
        allow_nan=False,
    )


def _writeback_memory_dir(run_dir: Path) -> Path:
    base = Path(run_dir).resolve() / "memory"
    if base.is_symlink() or (base.exists() and not base.is_dir()):
        raise DwError("memory writeback store is unsafe")
    base.mkdir(parents=True, exist_ok=True, mode=0o700)
    return base


def _atomic_json(path: Path, value: object) -> None:
    if path.is_symlink():
        raise DwError("memory writeback path must not be a symlink")
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    data = (_canonical_json(value) + "\n").encode("utf-8")
    descriptor, temporary_name = tempfile.mkstemp(
        prefix="." + path.name + ".", dir=str(path.parent)
    )
    temporary = Path(temporary_name)
    try:
        os.fchmod(descriptor, 0o600)
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


def _read_json_object(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, ValueError) as exc:
        raise DwError("memory writeback JSON is unreadable") from exc
    if not isinstance(value, dict):
        raise DwError("memory writeback JSON must be an object")
    return value


def _safe_hash(value: object, label: str) -> str:
    text = _identifier(value, label, 71)
    if (
        not text.startswith("sha256:") or len(text) != 71
        or any(char not in "0123456789abcdef" for char in text[7:])
    ):
        raise DwError("%s must be a sha256 reference" % label)
    return text


def _bounded_identifiers(values: Iterable[object], field: str) -> list[str]:
    cap = MEMORY_DOCUMENT_ITEM_CAPS[MEMORY_WRITEBACK_KIND][field]
    byte_cap = min(MEMORY_DOCUMENT_BYTE_CAPS[MEMORY_WRITEBACK_KIND][field], 6_000)
    result = []
    for raw in values:
        if len(result) >= cap:
            break
        text = " ".join(str(raw or "").split())
        if not text or len(text) > 1_000 or "\x00" in text:
            continue
        candidate = sorted(set(result + [text]))
        if len(_canonical_json(candidate).encode("utf-8")) > byte_cap:
            continue
        result = candidate
    return result


def _manifest_values(run_dir: Path) -> tuple[list[str], list[str]]:
    """Read only persisted, hash-valid recall manifests below this run."""
    memory = Path(run_dir).resolve() / "memory"
    paths = [memory / "manifest.json"]
    scopes = memory / "scopes"
    if scopes.is_dir() and not scopes.is_symlink():
        paths.extend(sorted(scopes.glob("scope-*/manifest.json")))
    recall_ids = []
    source_revisions = []
    for path in paths:
        if not path.is_file() or path.is_symlink():
            continue
        manifest = _read_json_object(path)
        required = {
            "kind", "schema_version", "subject", "source_revision",
            "source_heads", "source_hash", "audiences", "manifest_hash",
        }
        if set(manifest) != required:
            raise DwError("memory recall manifest has a non-exact shape")
        unsigned = {key: value for key, value in manifest.items() if key != "manifest_hash"}
        if manifest["manifest_hash"] != _sha(unsigned):
            raise DwError("memory recall manifest identity check failed")
        audiences = manifest["audiences"]
        if not isinstance(audiences, dict):
            raise DwError("memory recall manifest audiences are malformed")
        source_revisions.append(_safe_hash(
            manifest["source_revision"], "memory recall source revision"
        ))
        recall_ids.extend(
            _safe_hash(value, "recalled memory id") for value in audiences.values()
        )
    return sorted(set(recall_ids)), sorted(set(source_revisions))


def _terminal_state(projection: Mapping[str, object], origin_kind: str) -> str:
    state = str(projection.get("state") or "")
    if origin_kind == "program":
        return "timed-out" if state == "expired" else state
    if state == "awaiting-certification":
        return "succeeded"
    if state != "blocked":
        return state
    if projection.get("expired"):
        return "timed-out"
    wall = projection.get("budgets", {})
    if isinstance(wall, Mapping):
        budget = wall.get("max_wall_seconds", {})
        if (
            isinstance(budget, Mapping)
            and int(budget.get("used", 0)) >= int(budget.get("limit", 1))
        ):
            return "timed-out"
    routes = projection.get("routes", [])
    if isinstance(routes, list) and any(
        isinstance(item, Mapping) and item.get("action") == "exhausted"
        for item in routes
    ):
        return "exhausted"
    completed = projection.get("completed_claims", [])
    if isinstance(completed, list):
        outcomes = [
            str(item.get("outcome") or item.get("status") or "")
            for item in completed if isinstance(item, Mapping)
        ]
        if "lost" in outcomes:
            return "lost"
    return "failed"


def _projection_story_ids(
    projection: Mapping[str, object], origin_kind: str
) -> list[str]:
    if origin_kind == "program":
        values = projection.get("selected_stories")
        if not values and isinstance(projection.get("scope"), Mapping):
            values = projection["scope"].get("story_ids")  # type: ignore[index]
        return _bounded_identifiers(values if isinstance(values, list) else [], "story_ids")
    story = projection.get("story")
    if not isinstance(story, Mapping):
        return []
    value = story.get("story_id") or story.get("id")
    return _bounded_identifiers([value] if value else [], "story_ids")


def _projection_references(
    projection: Mapping[str, object], terminal_state: str
) -> tuple[list[str], list[str], list[str], list[str]]:
    decision_refs = []
    for request in projection.get("request_history", []):
        if isinstance(request, Mapping):
            decision_refs.extend([
                request.get("correlation_id"), request.get("response_hash"),
            ])
    for checkpoint in projection.get("checkpoints", []):
        if isinstance(checkpoint, Mapping) and checkpoint.get("decision"):
            decision_refs.append(_sha({
                "correlation_id": checkpoint.get("correlation_id"),
                "decision": checkpoint.get("decision"),
            }))
    for control in projection.get("controls", []):
        if isinstance(control, Mapping):
            decision_refs.append(control.get("token_hash"))
    for obligation in projection.get("obligations", []):
        if isinstance(obligation, Mapping):
            decision_refs.append(obligation.get("source_decision_hash"))
    evidence_refs = []
    check_refs = []
    for receipt in projection.get("node_receipts", []):
        if not isinstance(receipt, Mapping):
            continue
        target = check_refs if receipt.get("executor") == "check" else evidence_refs
        target.append(receipt.get("receipt_hash"))
    for claim in projection.get("completed_claims", []):
        if not isinstance(claim, Mapping) or not claim.get("receipt_hash"):
            continue
        category = str(claim.get("category") or "")
        target = check_refs if category == "check" else evidence_refs
        target.append(claim.get("receipt_hash"))
        if any(
            marker in category
            for marker in ("verdict", "decision", "checkpoint", "architecture")
        ):
            decision_refs.extend([
                claim.get("request_hash"), claim.get("receipt_hash"),
            ])
    failures = []
    if terminal_state not in _SUCCESSFUL_WRITEBACK_STATES:
        for claim in projection.get("completed_claims", []):
            if not isinstance(claim, Mapping):
                continue
            outcome = claim.get("outcome") or claim.get("status")
            if outcome and outcome != "succeeded":
                failures.append(_sha({
                    "node": claim.get("node_id") or claim.get("claim_id"),
                    "attempt": claim.get("attempt"),
                    "outcome": outcome,
                    "reason": claim.get("reason") or claim.get("completion_reason"),
                }))
        if not failures:
            failures.append(_sha({
                "terminal_state": terminal_state,
                "terminal_event_ref": projection.get("terminal_event_ref"),
            }))
    return (
        _bounded_identifiers(decision_refs, "decision_refs"),
        _bounded_identifiers(evidence_refs, "evidence_refs"),
        _bounded_identifiers(check_refs, "check_refs"),
        _bounded_identifiers(failures, "failure_signatures"),
    )


def _accepted_lesson_hashes(root: Path, origin: str) -> list[str]:
    store = EarnedRecordStore(Path(root).resolve())
    values = []
    for kind in (LESSON_KIND, CERTIFIED_LESSON_KIND):
        values.extend(
            record["record_hash"] for record in store.read(kind)
            if record["origin_kind"] == "run" and record["origin"] == origin
        )
    return _bounded_identifiers(values, "accepted_lesson_hashes")


def build_terminal_writeback(
    *,
    origin_kind: str,
    origin: str,
    terminal_state: str,
    subject: str,
    head_sha: str,
    terminal_event_ref: str,
    story_ids: Iterable[object] = (),
    recalled_memory_ids: Iterable[object] = (),
    decision_refs: Iterable[object] = (),
    evidence_refs: Iterable[object] = (),
    check_refs: Iterable[object] = (),
    changed_files: Iterable[object] = (),
    failure_signatures: Iterable[object] = (),
    accepted_lesson_hashes: Iterable[object] = (),
    discarded_lesson_count: int = 0,
    source_revision: str,
    supersedes: str = "",
) -> dict:
    """Build one closed, bounded outcome receipt; no transcript-shaped input exists."""
    if origin_kind not in {"run", "program"}:
        raise DwError("memory writeback origin kind must be run or program")
    origin = _identifier(origin, "memory writeback origin", 200)
    if terminal_state not in TERMINAL_OUTCOME_STATES:
        raise DwError("memory writeback terminal state is unsupported")
    subject = _safe_hash(subject, "memory writeback subject")
    _identifier(head_sha, "memory writeback HEAD", 64)
    terminal_event_ref = _identifier(
        terminal_event_ref, "memory writeback terminal event reference", 200
    )
    source_revision = _safe_hash(source_revision, "memory writeback source revision")
    if (
        not isinstance(discarded_lesson_count, int)
        or isinstance(discarded_lesson_count, bool)
        or discarded_lesson_count < 0
        or discarded_lesson_count > 99_999_999
    ):
        raise DwError("discarded lesson count must be a bounded non-negative integer")
    memory_state = (
        "confirmed" if terminal_state in _SUCCESSFUL_WRITEBACK_STATES
        else "candidate"
    )
    if supersedes:
        _safe_hash(supersedes, "memory writeback superseded outcome")
        memory_state = "superseded"
    unsigned = {
        "kind": MEMORY_WRITEBACK_KIND,
        "schema_version": MEMORY_DOCUMENT_SCHEMA_VERSION,
        "origin_kind": origin_kind,
        "origin": origin,
        "terminal_state": terminal_state,
        "memory_state": memory_state,
        "subject": subject,
        "head_sha": head_sha,
        "terminal_event_ref": terminal_event_ref,
        "story_ids": _bounded_identifiers(story_ids, "story_ids"),
        "recalled_memory_ids": _bounded_identifiers(
            recalled_memory_ids, "recalled_memory_ids"
        ),
        "decision_refs": _bounded_identifiers(decision_refs, "decision_refs"),
        "evidence_refs": _bounded_identifiers(evidence_refs, "evidence_refs"),
        "check_refs": _bounded_identifiers(check_refs, "check_refs"),
        "changed_files": _bounded_identifiers(changed_files, "changed_files"),
        "failure_signatures": _bounded_identifiers(
            failure_signatures, "failure_signatures"
        ),
        "accepted_lesson_hashes": _bounded_identifiers(
            accepted_lesson_hashes, "accepted_lesson_hashes"
        ),
        "discarded_lesson_count": discarded_lesson_count,
        "source_revision": source_revision,
        **_AUTHORITY_MARKERS,
    }
    document = {
        "kind": unsigned["kind"],
        "schema_version": unsigned["schema_version"],
        "writeback_id": _sha(unsigned),
        **{
            key: value for key, value in unsigned.items()
            if key not in {"kind", "schema_version"}
        },
    }
    if set(document) != set(MEMORY_DOCUMENT_FIELDS[MEMORY_WRITEBACK_KIND]):
        raise DwError("memory writeback receipt differs from its closed contract")
    if len(_canonical_json(document).encode("utf-8")) > MEMORY_DOCUMENT_BYTE_CAPS[MEMORY_WRITEBACK_KIND]["document"]:
        raise DwError("memory writeback receipt exceeds its document byte cap")
    return document


def _writeback_detail(document: Mapping[str, object], supersedes: str) -> dict:
    return {
        "receipt_id": str(document["writeback_id"]),
        "subject": str(document["subject"]),
        "terminal_state": str(document["terminal_state"]),
        "memory_state": str(document["memory_state"]),
        "story_ids": encode_identifier_list(document["story_ids"], "story_ids"),
        "recalled_memory_ids": encode_identifier_list(
            document["recalled_memory_ids"], "recalled_memory_ids"
        ),
        "decision_refs": encode_identifier_list(document["decision_refs"], "decision_refs"),
        "evidence_refs": encode_identifier_list(document["evidence_refs"], "evidence_refs"),
        "check_refs": encode_identifier_list(document["check_refs"], "check_refs"),
        "changed_files": encode_identifier_list(document["changed_files"], "changed_files"),
        "failure_signatures": encode_identifier_list(
            document["failure_signatures"], "failure_signatures"
        ),
        "accepted_lesson_hashes": encode_identifier_list(
            document["accepted_lesson_hashes"], "accepted_lesson_hashes"
        ),
        "discarded_lesson_count": str(document["discarded_lesson_count"]),
        "supersedes": supersedes,
    }


def _status_document(
    terminal_event_ref: str,
    status: str,
    *,
    writeback_id: object = None,
    record_hash: object = None,
    reason: str = "",
) -> dict:
    document = {
        "kind": MEMORY_WRITEBACK_STATUS_KIND,
        "schema_version": MEMORY_WRITEBACK_STATUS_SCHEMA_VERSION,
        "terminal_event_ref": terminal_event_ref,
        "status": status,
        "writeback_id": writeback_id,
        "record_hash": record_hash,
        "reason": " ".join(reason.split())[:500],
    }
    if set(document) != _MEMORY_WRITEBACK_STATUS_KEYS:
        raise DwError("memory writeback status has the wrong shape")
    return document


def persist_terminal_writeback(
    root: Path,
    run_dir: Path,
    *,
    projection: Mapping[str, object],
    origin_kind: str,
    timestamp: Optional[datetime] = None,
    discarded_lesson_count: int = 0,
    supersedes: str = "",
) -> dict:
    """Persist one receipt and earned outcome with deterministic replay identity."""
    origin = _identifier(projection.get("run_id"), "memory writeback run id", 200)
    terminal_event_ref = _identifier(
        projection.get("terminal_event_ref"),
        "memory writeback terminal event reference",
        200,
    )
    terminal_state = _terminal_state(projection, origin_kind)
    if str(projection.get("state") or "") not in _TERMINAL_PROJECTION_STATES:
        raise DwError("memory writeback requires a terminal projection")
    recalled, revisions = _manifest_values(run_dir)
    source_revision = (
        revisions[0] if len(revisions) == 1
        else _sha({"recall_source_revisions": revisions})
    )
    stories = _projection_story_ids(projection, origin_kind)
    subject = _sha({
        "origin_kind": origin_kind,
        "origin": origin,
        "story_ids": stories,
    })
    decisions, evidence, checks, failures = _projection_references(
        projection, terminal_state
    )
    delivery = projection.get("delivery_facts")
    files = (
        delivery.get("files_touched", [])
        if isinstance(delivery, Mapping) else []
    )
    accepted = _accepted_lesson_hashes(root, origin)
    document = build_terminal_writeback(
        origin_kind=origin_kind,
        origin=origin,
        terminal_state=terminal_state,
        subject=subject,
        head_sha=str(
            (delivery.get("head_sha") if isinstance(delivery, Mapping) else None)
            or (
                projection.get("expected_repository", {}).get("head")
                if isinstance(projection.get("expected_repository"), Mapping)
                else None
            )
            or projection.get("head_sha")
        ),
        terminal_event_ref=terminal_event_ref,
        story_ids=stories,
        recalled_memory_ids=recalled,
        decision_refs=decisions,
        evidence_refs=evidence,
        check_refs=checks,
        changed_files=files,
        failure_signatures=failures,
        accepted_lesson_hashes=accepted,
        discarded_lesson_count=discarded_lesson_count,
        source_revision=source_revision,
        supersedes=supersedes,
    )
    store = EarnedRecordStore(Path(root).resolve())
    record = store.append(
        TERMINAL_OUTCOME_KIND,
        _writeback_detail(document, supersedes),
        origin_kind="run",
        origin=origin,
        head_sha=str(document["head_sha"]),
        timestamp=timestamp,
        deduplicate=True,
    )
    memory = _writeback_memory_dir(run_dir)
    receipt_path = memory / "writebacks" / (
        str(document["writeback_id"])[7:] + ".json"
    )
    if receipt_path.exists():
        if receipt_path.is_symlink() or _read_json_object(receipt_path) != document:
            raise DwError("persisted memory writeback receipt differs from replay")
        deduplicated = True
    else:
        _atomic_json(receipt_path, document)
        deduplicated = False
    status = _status_document(
        terminal_event_ref,
        "persisted",
        writeback_id=document["writeback_id"],
        record_hash=record["record_hash"],
    )
    _atomic_json(memory / "writeback-status.json", status)
    return {
        **status,
        "receipt_path": str(receipt_path),
        "deduplicated": deduplicated,
        "document": document,
    }


def read_terminal_writeback_status(run_dir: Path) -> dict | None:
    path = Path(run_dir).resolve() / "memory" / "writeback-status.json"
    if not path.exists():
        return None
    if path.is_symlink():
        return _status_document("unknown", "action-needed", reason="unsafe status path")
    try:
        value = _read_json_object(path)
        if set(value) != _MEMORY_WRITEBACK_STATUS_KEYS:
            raise DwError("memory writeback status has a non-exact shape")
        if value.get("kind") != MEMORY_WRITEBACK_STATUS_KIND or value.get("schema_version") != 1:
            raise DwError("memory writeback status uses an unsupported contract")
        if value.get("status") not in {"persisted", "action-needed"}:
            raise DwError("memory writeback status is unsupported")
        return value
    except DwError as exc:
        return _status_document("unknown", "action-needed", reason=exc.message)


def ensure_terminal_writeback(
    root: Path,
    run_dir: Path,
    *,
    projection: Mapping[str, object],
    origin_kind: str,
    timestamp: Optional[datetime] = None,
    discarded_lesson_count: int = 0,
) -> dict:
    """Call the terminal adapter once; preserve a typed failure for operator repair."""
    terminal_ref = str(projection.get("terminal_event_ref") or "")
    prior = read_terminal_writeback_status(run_dir)
    if prior is not None and prior.get("terminal_event_ref") == terminal_ref:
        return {**prior, "deduplicated": True}
    try:
        return persist_terminal_writeback(
            root,
            run_dir,
            projection=projection,
            origin_kind=origin_kind,
            timestamp=timestamp,
            discarded_lesson_count=discarded_lesson_count,
        )
    except (DwError, OSError, UnicodeError, ValueError) as exc:
        status = _status_document(
            terminal_ref or "unknown",
            "action-needed",
            reason="terminal writeback failed: " + str(exc),
        )
        try:
            memory = _writeback_memory_dir(run_dir)
            _atomic_json(memory / "writeback-status.json", status)
        except (DwError, OSError):
            pass
        return status
