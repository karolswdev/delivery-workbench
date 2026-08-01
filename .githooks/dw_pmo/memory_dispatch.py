"""Persisted, restart-safe recall wiring for agent dispatch.

The pure recall builder stays isolated in :mod:`dw_pmo.memory_recall`.  This
adapter turns an already-built knowledge packet into caller-supplied recall
inputs, freezes all audience slices below a run directory, and validates those
bytes before a conductor may attach one to an agent packet.
"""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
from pathlib import Path
from typing import Mapping

from .memory_recall import (
    AUDIENCES,
    MEMORY_RECALL_ITEM_FIELDS,
    MEMORY_RECALL_KIND,
    build_memory_recall,
)
from .model import DwError


MEMORY_RECALL_MANIFEST_KIND = "delivery-workbench-memory-recall-manifest"
MEMORY_RECALL_MANIFEST_SCHEMA_VERSION = 1
MEMORY_RECALL_PACKET_FIELD = "memory_recall"
_MEMORY_DIR = "memory"
_RECALL_DIR = "recalls"
_MANIFEST_KEYS = {
    "kind", "schema_version", "subject", "source_revision", "source_heads",
    "source_hash", "audiences", "manifest_hash",
}
_RECALL_KEYS = {
    "kind", "schema_version", "recall_id", "subject", "audience",
    "source_revision", "source_heads", "items", "exclusions", "byte_budget",
    "used_bytes", "starts_work", "authorizes", "satisfies_gate",
    "substitutes_for_evidence",
}
_AUTHORITY_KEYS = (
    "starts_work", "authorizes", "satisfies_gate", "substitutes_for_evidence",
)


class MemoryRecallActionNeeded(DwError):
    """Typed fail-closed state when frozen recall cannot be safely dispatched."""

    def __init__(self, reason: str, message: str) -> None:
        self.reason = reason
        super().__init__(message)


def canonical_memory_json(value: object) -> str:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
        allow_nan=False,
    )


def _sha(value: object) -> str:
    return "sha256:" + hashlib.sha256(
        canonical_memory_json(value).encode("utf-8")
    ).hexdigest()


def _safe_directory(run_dir: Path, scope: str | None) -> Path:
    run_dir = Path(run_dir).resolve()
    base = run_dir / _MEMORY_DIR
    if base.is_symlink():
        raise MemoryRecallActionNeeded(
            "malformed", "memory recall store must not be a symlink"
        )
    if base.exists() and not base.is_dir():
        raise MemoryRecallActionNeeded(
            "malformed", "memory recall store is not a directory"
        )
    if scope is None:
        return base
    digest = hashlib.sha256(scope.encode("utf-8")).hexdigest()[:24]
    memory = base / "scopes" / ("scope-" + digest)
    if memory.is_symlink() or (memory.exists() and not memory.is_dir()):
        raise MemoryRecallActionNeeded(
            "malformed", "scoped memory recall store is unsafe"
        )
    return memory


def _write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    if path.is_symlink():
        raise MemoryRecallActionNeeded(
            "malformed", "memory recall path must not be a symlink"
        )
    data = (canonical_memory_json(value) + "\n").encode("utf-8")
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


def _read_json(path: Path, label: str) -> dict:
    if not path.is_file() or path.is_symlink():
        raise MemoryRecallActionNeeded("missing", label + " is missing")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise MemoryRecallActionNeeded(
            "malformed", label + " is not valid UTF-8 JSON"
        ) from exc
    if not isinstance(value, dict):
        raise MemoryRecallActionNeeded("malformed", label + " must be an object")
    return value


def _bounded_summary(value: object) -> str:
    text = " ".join(str(value or "").split())
    return text[:1_000] or "Recorded repository knowledge item."


def _candidate_ref(kind: str, payload: Mapping[str, object]) -> str:
    explicit = (
        payload.get("source_ref")
        or payload.get("record_hash")
        or payload.get("receipt_id")
        or payload.get("decision_id")
    )
    return str(explicit) if explicit else _sha({"kind": kind, "payload": payload})


def _string_list(value: object) -> list[str]:
    if isinstance(value, str):
        return [value] if value else []
    if not isinstance(value, (list, tuple)):
        return []
    return sorted(set(
        str(item) for item in value
        if isinstance(item, (str, int)) and str(item)
    ))


def _location_fields(payload: Mapping[str, object]) -> dict:
    files = _string_list(payload.get("files", payload.get("changed_files", [])))
    symbols = _string_list(payload.get("symbols", []))
    if payload.get("file"):
        files.append(str(payload["file"]))
    if payload.get("symbol"):
        symbols.append(str(payload["symbol"]))
    result = {}
    if files:
        result["files"] = sorted(set(files))
    if symbols:
        result["symbols"] = sorted(set(symbols))
    locations = payload.get("locations")
    if isinstance(locations, list):
        result["locations"] = locations
    return result


def _recall_inputs(knowledge: Mapping[str, object]) -> tuple[list[dict], dict]:
    revision = str(knowledge.get("index_tree") or "")
    if not revision:
        raise MemoryRecallActionNeeded(
            "malformed", "knowledge packet has no source index tree"
        )
    candidates: list[dict] = []
    query_files = []
    query_symbols = []
    query_tests = []
    query_failures = _string_list(knowledge.get("failure_signatures", []))

    for location in knowledge.get("verified_locations", []):
        if not isinstance(location, Mapping):
            continue
        file_name = str(location.get("file") or "")
        symbol = str(location.get("symbol") or "")
        if file_name:
            query_files.append(file_name)
        if symbol:
            query_symbols.append(symbol)
        candidates.append({
            "source_kind": "grounding",
            "source_ref": _candidate_ref("grounding", location),
            "source_revision": revision,
            "summary": _bounded_summary(
                "Verified location %s%s."
                % (file_name, (":" + symbol) if symbol else "")
            ),
            "delivery_state": "confirmed",
            "confidence": "certain",
            **_location_fields(location),
        })

    for snippet in knowledge.get("snippets", []):
        if not isinstance(snippet, Mapping):
            continue
        candidates.append({
            "source_kind": "repository-snippet",
            "source_ref": _candidate_ref("repository-snippet", snippet),
            "source_revision": revision,
            "summary": _bounded_summary(snippet.get("content")),
            "delivery_state": "confirmed",
            "confidence": "certain",
            **_location_fields(snippet),
        })

    for reference in knowledge.get("test_references", []):
        if not isinstance(reference, Mapping):
            continue
        file_name = str(reference.get("file") or "")
        if file_name:
            query_tests.append(file_name)
        candidates.append({
            "source_kind": "test-reference",
            "source_ref": _candidate_ref("test-reference", reference),
            "source_revision": revision,
            "summary": _bounded_summary(
                "Test reference %s for %s."
                % (file_name, str(reference.get("symbol") or "the selected work"))
            ),
            "delivery_state": "confirmed",
            "confidence": "certain",
            "test_names": [file_name] if file_name else [],
            **_location_fields(reference),
        })

    for lesson in knowledge.get("lessons", []):
        if not isinstance(lesson, Mapping):
            continue
        stories = _string_list(lesson.get("story_ids", []))
        if lesson.get("story"):
            stories.append(str(lesson["story"]))
        candidates.append({
            "source_kind": "lesson",
            "source_ref": _candidate_ref("lesson", lesson),
            "source_revision": revision,
            "summary": _bounded_summary(lesson.get("claim")),
            "delivery_state": str(lesson.get("delivery_state") or "candidate"),
            "confidence": lesson.get("confidence") or "unknown",
            "story_ids": sorted(set(stories)),
            "test_names": _string_list(lesson.get("test_names", [])),
            "failure_signatures": _string_list(
                lesson.get("failure_signatures", [])
            ),
            "audiences": lesson.get("audiences") or AUDIENCES,
            **_location_fields(lesson),
        })

    for outcome in knowledge.get("terminal_outcomes", []):
        if not isinstance(outcome, Mapping):
            continue
        terminal_state = str(outcome.get("terminal_state") or "unknown")
        memory_state = str(outcome.get("memory_state") or "candidate")
        candidates.append({
            "source_kind": "terminal-outcome",
            "source_ref": _candidate_ref("terminal-outcome", outcome),
            "source_revision": revision,
            "summary": _bounded_summary(
                outcome.get("summary")
                or "Terminal %s outcome retained as %s memory."
                % (terminal_state, memory_state)
            ),
            "delivery_state": memory_state,
            "confidence": outcome.get("confidence") or "certain",
            "story_ids": _string_list(outcome.get("story_ids", [])),
            "test_names": _string_list(outcome.get("test_names", [])),
            "failure_signatures": _string_list(
                outcome.get("failure_signatures", [])
            ),
            "audiences": outcome.get("audiences") or AUDIENCES,
            **_location_fields(outcome),
        })

    for decision in knowledge.get("decisions", []):
        if not isinstance(decision, Mapping):
            continue
        candidates.append({
            "source_kind": "decision",
            "source_ref": _candidate_ref("decision", decision),
            "source_revision": revision,
            "summary": _bounded_summary(
                decision.get("summary") or decision.get("outcome")
            ),
            "delivery_state": str(
                decision.get("delivery_state") or "confirmed"
            ),
            "confidence": decision.get("confidence") or "certain",
            "story_ids": _string_list(decision.get("story_ids", [])),
            "test_names": _string_list(decision.get("test_names", [])),
            "failure_signatures": _string_list(
                decision.get("failure_signatures", [])
            ),
            "audiences": decision.get("audiences") or AUDIENCES,
            **_location_fields(decision),
        })

    query = {
        "grounded_files": sorted(set(query_files)),
        "grounded_symbols": sorted(set(query_symbols)),
        "test_names": sorted(set(query_tests)),
        "failure_signatures": sorted(set(query_failures)),
    }
    return candidates, query


def _validate_recall(document: object, manifest: Mapping[str, object], audience: str) -> dict:
    if not isinstance(document, dict) or set(document) != _RECALL_KEYS:
        raise MemoryRecallActionNeeded(
            "malformed", "persisted memory recall has a non-exact shape"
        )
    if document.get("kind") != MEMORY_RECALL_KIND or document.get("schema_version") != 1:
        raise MemoryRecallActionNeeded(
            "malformed", "persisted memory recall uses an unsupported contract"
        )
    if document.get("audience") != audience:
        raise MemoryRecallActionNeeded(
            "malformed", "persisted memory recall audience does not match its path"
        )
    if any(document.get(key) is not False for key in _AUTHORITY_KEYS):
        raise MemoryRecallActionNeeded(
            "malformed", "persisted memory recall claims forbidden authority"
        )
    if document.get("subject") != manifest.get("subject"):
        raise MemoryRecallActionNeeded(
            "stale", "persisted memory recall belongs to a different subject"
        )
    if (
        document.get("source_revision") != manifest.get("source_revision")
        or document.get("source_heads") != manifest.get("source_heads")
    ):
        raise MemoryRecallActionNeeded(
            "stale", "persisted memory recall source revision changed"
        )
    items = document.get("items")
    exclusions = document.get("exclusions")
    if not isinstance(items, list) or len(items) > 64:
        raise MemoryRecallActionNeeded("malformed", "persisted memory recall items are invalid")
    if not isinstance(exclusions, list) or len(exclusions) > 128:
        raise MemoryRecallActionNeeded(
            "malformed", "persisted memory recall exclusions are invalid"
        )
    unsigned = {
        "kind": document["kind"],
        "schema_version": document["schema_version"],
        **{
            key: value for key, value in document.items()
            if key not in {"kind", "schema_version", "recall_id"}
        },
    }
    if document.get("recall_id") != _sha(unsigned):
        raise MemoryRecallActionNeeded(
            "tampered", "persisted memory recall identity check failed"
        )
    used = len(canonical_memory_json(document).encode("utf-8"))
    if document.get("used_bytes") != used or used > 65_536:
        raise MemoryRecallActionNeeded(
            "tampered", "persisted memory recall byte count check failed"
        )
    expected_id = manifest.get("audiences", {}).get(audience)  # type: ignore[union-attr]
    if document.get("recall_id") != expected_id:
        raise MemoryRecallActionNeeded(
            "tampered", "persisted memory recall differs from its manifest"
        )
    for item in items:
        if not isinstance(item, dict) or set(item) != MEMORY_RECALL_ITEM_FIELDS:
            raise MemoryRecallActionNeeded(
                "malformed", "persisted memory recall item has a non-exact shape"
            )
        if item.get("advisory_only") is not True or any(
            item.get(key) is not False for key in _AUTHORITY_KEYS
        ):
            raise MemoryRecallActionNeeded(
                "malformed", "persisted memory recall item claims forbidden authority"
            )
    return document


def _validate_manifest(value: object) -> dict:
    if not isinstance(value, dict) or set(value) != _MANIFEST_KEYS:
        raise MemoryRecallActionNeeded(
            "malformed", "memory recall manifest has a non-exact shape"
        )
    if (
        value.get("kind") != MEMORY_RECALL_MANIFEST_KIND
        or value.get("schema_version") != MEMORY_RECALL_MANIFEST_SCHEMA_VERSION
    ):
        raise MemoryRecallActionNeeded(
            "malformed", "memory recall manifest uses an unsupported contract"
        )
    unsigned = {key: item for key, item in value.items() if key != "manifest_hash"}
    if value.get("manifest_hash") != _sha(unsigned):
        raise MemoryRecallActionNeeded(
            "tampered", "memory recall manifest identity check failed"
        )
    audiences = value.get("audiences")
    if not isinstance(audiences, dict) or set(audiences) != set(AUDIENCES):
        raise MemoryRecallActionNeeded(
            "malformed", "memory recall manifest has incomplete audience slices"
        )
    return value


def persist_recall_slices(
    run_dir: Path,
    *,
    subject: str,
    knowledge: dict,
    story_criteria: str,
    story_ids: list[str],
    phase_ids: list[str],
    orchestration_tags: list[str],
    scope: str | None = None,
    require_existing: bool = False,
) -> tuple[dict[str, dict], bool]:
    """Create every frozen audience slice once, or validate and reuse all of them."""
    memory = _safe_directory(run_dir, scope)
    manifest_path = memory / "manifest.json"
    source_path = memory / "source.json"
    source_hash = _sha(knowledge)
    source_revision = _sha({"subject": subject, "knowledge": knowledge})
    source_heads = {
        "index_tree": str(knowledge.get("index_tree") or ""),
        "knowledge_packet": source_hash,
    }

    if not isinstance(require_existing, bool):
        raise MemoryRecallActionNeeded(
            "malformed", "memory recall existing-state flag must be boolean"
        )
    if require_existing and not memory.exists():
        raise MemoryRecallActionNeeded(
            "missing", "persisted memory recall store is missing"
        )
    if manifest_path.exists():
        manifest = _validate_manifest(_read_json(manifest_path, "memory recall manifest"))
        source = _read_json(source_path, "memory recall source snapshot")
        if _sha(source) != manifest.get("source_hash"):
            raise MemoryRecallActionNeeded(
                "tampered", "memory recall source snapshot differs from its manifest"
            )
        current_tree = str(knowledge.get("index_tree") or "")
        frozen_tree = str(manifest.get("source_heads", {}).get("index_tree") or "")  # type: ignore[union-attr]
        if not current_tree or current_tree != frozen_tree:
            raise MemoryRecallActionNeeded(
                "stale", "memory recall source revision is stale"
            )
        documents = {
            audience: _validate_recall(
                _read_json(memory / _RECALL_DIR / (audience + ".json"),
                           "memory recall audience slice"),
                manifest,
                audience,
            )
            for audience in AUDIENCES
        }
        return documents, False

    candidates, query = _recall_inputs(knowledge)
    documents = {
        audience: build_memory_recall(
            story_criteria,
            candidates,
            subject=subject,
            source_revision=source_revision,
            source_heads=source_heads,
            audience=audience,
            grounded_files=query["grounded_files"],
            grounded_symbols=query["grounded_symbols"],
            test_names=query["test_names"],
            failure_signatures=query["failure_signatures"],
            story_ids=story_ids,
            phase_ids=phase_ids,
            orchestration_tags=orchestration_tags,
        )
        for audience in AUDIENCES
    }
    unsigned_manifest = {
        "kind": MEMORY_RECALL_MANIFEST_KIND,
        "schema_version": MEMORY_RECALL_MANIFEST_SCHEMA_VERSION,
        "subject": subject,
        "source_revision": source_revision,
        "source_heads": source_heads,
        "source_hash": source_hash,
        "audiences": {
            audience: documents[audience]["recall_id"] for audience in AUDIENCES
        },
    }
    manifest = {**unsigned_manifest, "manifest_hash": _sha(unsigned_manifest)}
    if memory.exists():
        allowed = {"decisions"} if scope is None else set()
        entries = {path.name for path in memory.iterdir()}
        if entries - allowed:
            raise MemoryRecallActionNeeded(
                "malformed", "memory recall store has unexpected pre-existing entries"
            )
    memory.mkdir(parents=True, exist_ok=True, mode=0o700)
    _write_json(source_path, knowledge)
    for audience in AUDIENCES:
        _write_json(memory / _RECALL_DIR / (audience + ".json"), documents[audience])
    _write_json(manifest_path, manifest)
    return documents, True


def recall_audience(role: object) -> str:
    folded = str(role or "").casefold()
    if any(marker in folded for marker in ("judge", "verdict", "architect", "council")):
        return "judge"
    if any(marker in folded for marker in ("verif", "review", "test", "quality")):
        return "verifier"
    if any(marker in folded for marker in ("coordin", "lead", "manage", "orchestrat")):
        return "coordinator"
    return "implementer"


def recall_event_detail(document: Mapping[str, object]) -> dict[str, object]:
    return {
        "recall_id": document["recall_id"],
        "subject": document["subject"],
        "source_revision": document["source_revision"],
        "audience": document["audience"],
        "byte_count": document["used_bytes"],
        "included_item_count": len(document["items"]),  # type: ignore[arg-type]
        "exclusion_count": len(document["exclusions"]),  # type: ignore[arg-type]
    }
