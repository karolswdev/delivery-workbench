"""Typed, terminal-only write-back into advisory earned knowledge.

This adapter may read repository knowledge to resolve lesson references and may
append earned records. It consumes a completed ledger projection; it never
returns a decision, verdict, grant, gate result, or evidence fact.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Iterable, Optional

from . import repofacts
from .knowledge import (
    CERTIFIED_LESSON_KIND,
    DELIVERY_RECORD_KIND,
    LESSON_DELIVERY_OBSERVATION_KIND,
    LESSON_KIND,
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
