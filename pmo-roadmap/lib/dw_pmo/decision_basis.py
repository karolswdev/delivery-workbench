"""Closed, content-free decision-basis receipts for bounded runs and programs.

A basis receipt names durable inputs and declared rules.  It never stores model
rationale, prompts, transcripts, or reconstructed reasoning.  Receipts are
content-addressed below an existing run's ``memory/decisions`` directory and a
companion event in that run's hash-chained ledger references every receipt.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import tempfile
from pathlib import Path
from typing import Iterable, Mapping, Optional

from .knowledge import (
    DECISION_BASIS_KIND,
    MEMORY_DOCUMENT_BYTE_CAPS,
    MEMORY_DOCUMENT_FIELDS,
    MEMORY_DOCUMENT_ITEM_CAPS,
)
from .model import DwError


DECISION_KINDS = ("scheduler", "failure-route", "verdict", "council", "terminal")
BASIS_TYPES = ("mechanical", "agent-reported", "panel-derived", "operator-supplied")
DECISION_BASIS_EVENT = "decision-basis-recorded"
DECISION_BASIS_SCHEMA_VERSION = 1
_AUTHORITY = {
    "starts_work": False,
    "authorizes": False,
    "satisfies_gate": False,
    "substitutes_for_evidence": False,
}
_HASH_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
_PRIVATE_FIELD_MARKERS = (
    "chain_of_thought", "chain-of-thought", "hidden_thinking", "hidden-thinking",
    "private_reasoning", "private-reasoning", "reasoning_trace", "reasoning-trace",
    "raw_reasoning", "raw-thinking", "full_transcript", "full-transcript",
    "internal_monologue", "scratchpad", "prompt", "transcript", "thinking",
)
_PRIVATE_VALUE_MARKERS = (
    "chain of thought", "hidden thinking", "private reasoning", "reasoning trace",
    "internal monologue", "full agent transcript", "<thinking>", "</thinking>",
)


def canonical_json(value: object) -> str:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
        allow_nan=False,
    )


def _sha(value: object) -> str:
    return "sha256:" + hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def _bounded_text(value: object, field: str, cap: int, *, empty: bool = False) -> str:
    if not isinstance(value, str):
        raise DwError("decision basis %s must be a string" % field)
    text = value.strip()
    if (not text and not empty) or len(text) > cap or any(char in text for char in "\r\n\x00"):
        raise DwError("decision basis %s is empty, unsafe, or exceeds %d chars" % (field, cap))
    _reject_private_content(text, field)
    return text


def _reject_private_content(value: object, path: str = "document") -> None:
    """Reject planted private-reasoning channels by name and by content shape."""
    if isinstance(value, Mapping):
        for key, item in value.items():
            folded = str(key).casefold().replace(" ", "_")
            if any(marker in folded for marker in _PRIVATE_FIELD_MARKERS):
                raise DwError("decision basis contains forbidden private-reasoning field: %s" % key)
            _reject_private_content(item, "%s.%s" % (path, key))
        return
    if isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            _reject_private_content(item, "%s[%d]" % (path, index))
        return
    if isinstance(value, str):
        folded = " ".join(value.casefold().split())
        if any(marker in folded for marker in _PRIVATE_VALUE_MARKERS):
            raise DwError("decision basis contains forbidden private-reasoning content at %s" % path)
        # A role-labelled multi-turn block is transcript-shaped even if it avoids
        # the explicit words above. References such as ``receipt:agent`` do not
        # match because each label must begin a line.
        role_lines = re.findall(r"(?m)^(?:user|assistant|system|agent|model)\s*:", value, re.I)
        if len(role_lines) >= 2:
            raise DwError("decision basis contains transcript-shaped content at %s" % path)


def _references(values: Iterable[object], field: str, cap: int) -> list[str]:
    if isinstance(values, (str, bytes)):
        raise DwError("decision basis %s must be a list" % field)
    normalized = []
    for value in values:
        normalized.append(_bounded_text(value, field, 500))
    result = sorted(set(normalized))
    if len(result) > cap:
        raise DwError("decision basis %s exceeds its item cap" % field)
    return result


def build_decision_basis(
    *,
    subject: str,
    decision_kind: str,
    basis_type: str,
    outcome: str,
    reason_code: str,
    rule_ref: str = "",
    score_ref: str = "",
    input_receipt_refs: Iterable[str] = (),
    memory_refs: Iterable[str] = (),
    dissent_refs: Iterable[str] = (),
    resulting_ledger_event: str,
    source_revision: str,
) -> dict:
    """Build and validate one deterministic ``decision-basis@1`` document."""
    if decision_kind not in DECISION_KINDS:
        raise DwError("decision basis kind is unsupported")
    if basis_type not in BASIS_TYPES:
        raise DwError("decision basis authority label is unsupported")
    caps = MEMORY_DOCUMENT_BYTE_CAPS[DECISION_BASIS_KIND]
    unsigned = {
        "kind": DECISION_BASIS_KIND,
        "schema_version": DECISION_BASIS_SCHEMA_VERSION,
        "subject": _bounded_text(subject, "subject", caps["subject"]),
        "decision_kind": decision_kind,
        "basis_type": basis_type,
        "outcome": _bounded_text(outcome, "outcome", caps["outcome"]),
        "reason_code": _bounded_text(reason_code, "reason_code", caps["reason_code"]),
        "rule_ref": _bounded_text(rule_ref, "rule_ref", caps["rule_ref"], empty=True),
        "score_ref": _bounded_text(score_ref, "score_ref", caps["score_ref"], empty=True),
        "input_receipt_refs": _references(
            input_receipt_refs, "input_receipt_refs",
            MEMORY_DOCUMENT_ITEM_CAPS[DECISION_BASIS_KIND]["input_receipt_refs"],
        ),
        "memory_refs": _references(
            memory_refs, "memory_refs",
            MEMORY_DOCUMENT_ITEM_CAPS[DECISION_BASIS_KIND]["memory_refs"],
        ),
        "dissent_refs": _references(
            dissent_refs, "dissent_refs",
            MEMORY_DOCUMENT_ITEM_CAPS[DECISION_BASIS_KIND]["dissent_refs"],
        ),
        "resulting_ledger_event": _bounded_text(
            resulting_ledger_event, "resulting_ledger_event",
            caps["resulting_ledger_event"],
        ),
        "source_revision": _bounded_text(
            source_revision, "source_revision", caps["source_revision"],
        ),
        **_AUTHORITY,
    }
    if not unsigned["rule_ref"] and not unsigned["score_ref"]:
        raise DwError("decision basis requires a rule or score reference")
    document = {
        "kind": unsigned["kind"],
        "schema_version": unsigned["schema_version"],
        "decision_id": _sha(unsigned),
        **{key: value for key, value in unsigned.items() if key not in {"kind", "schema_version"}},
    }
    return validate_decision_basis(document)


def validate_decision_basis(value: object) -> dict:
    _reject_private_content(value)
    expected = set(MEMORY_DOCUMENT_FIELDS[DECISION_BASIS_KIND])
    if not isinstance(value, dict) or set(value) != expected:
        raise DwError("decision basis has a non-exact shape")
    if value.get("kind") != DECISION_BASIS_KIND or value.get("schema_version") != 1:
        raise DwError("decision basis uses an unsupported contract")
    if value.get("decision_kind") not in DECISION_KINDS or value.get("basis_type") not in BASIS_TYPES:
        raise DwError("decision basis kind or authority label is unsupported")
    caps = MEMORY_DOCUMENT_BYTE_CAPS[DECISION_BASIS_KIND]
    for field in (
        "subject", "outcome", "reason_code", "resulting_ledger_event", "source_revision",
    ):
        _bounded_text(value[field], field, caps[field])
    for field in ("rule_ref", "score_ref"):
        _bounded_text(value[field], field, caps[field], empty=True)
    if not value["rule_ref"] and not value["score_ref"]:
        raise DwError("decision basis requires a rule or score reference")
    for field in ("input_receipt_refs", "memory_refs", "dissent_refs"):
        normalized = _references(
            value[field], field,
            MEMORY_DOCUMENT_ITEM_CAPS[DECISION_BASIS_KIND][field],
        )
        if normalized != value[field]:
            raise DwError("decision basis %s must be sorted and duplicate-free" % field)
    for field in ("decision_id", "resulting_ledger_event", "source_revision"):
        if not _HASH_RE.fullmatch(str(value[field])):
            raise DwError("decision basis %s must be a sha256 reference" % field)
    for key, expected_value in _AUTHORITY.items():
        if value.get(key) is not expected_value:
            raise DwError("decision basis claims forbidden authority")
    unsigned = {key: item for key, item in value.items() if key != "decision_id"}
    if value["decision_id"] != _sha(unsigned):
        raise DwError("decision basis identity check failed")
    if len(canonical_json(value).encode("utf-8")) > caps["document"]:
        raise DwError("decision basis exceeds its document byte cap")
    return dict(value)


def decision_subject(origin_kind: str, origin: str) -> str:
    return _sha({"origin_kind": origin_kind, "origin": origin})


def decision_context(projection: Mapping[str, object], node_id: Optional[str] = None) -> tuple[list[str], str]:
    """Return only recall IDs frozen and attached to the deciding node."""
    refs = []
    revisions = []
    for attachment in projection.get("memory_attachments", []):
        if not isinstance(attachment, Mapping):
            continue
        if node_id is not None and str(attachment.get("node_id")) != node_id:
            continue
        if attachment.get("recall_id"):
            refs.append(str(attachment["recall_id"]))
        if attachment.get("source_revision"):
            revisions.append(str(attachment["source_revision"]))
    if not refs and node_id is None:
        for recall in projection.get("memory_recalls", []):
            if not isinstance(recall, Mapping):
                continue
            if recall.get("recall_id"):
                refs.append(str(recall["recall_id"]))
            if recall.get("source_revision"):
                revisions.append(str(recall["source_revision"]))
    revision = sorted(set(revisions))[0] if revisions else _sha({
        "grant_hash": projection.get("grant_hash"),
        "plan_hash": projection.get("plan_hash"),
        "score": projection.get("score"),
        "terminal_event_ref": projection.get("terminal_event_ref"),
    })
    return sorted(set(refs)), revision


def _decision_directory(run_dir: Path, *, create: bool) -> Path:
    memory = Path(run_dir) / "memory"
    decisions = memory / "decisions"
    for path, label in ((memory, "memory"), (decisions, "decision basis")):
        if path.is_symlink() or (path.exists() and not path.is_dir()):
            raise DwError("%s store is unsafe" % label)
    if create:
        decisions.mkdir(parents=True, exist_ok=True, mode=0o700)
        os.chmod(memory, 0o700)
        os.chmod(decisions, 0o700)
    return decisions


def persist_decision_basis(run_dir: Path, document: Mapping[str, object]) -> tuple[dict, bool]:
    validated = validate_decision_basis(dict(document))
    directory = _decision_directory(run_dir, create=True)
    path = directory / (validated["decision_id"][7:] + ".json")
    if path.is_symlink():
        raise DwError("decision basis receipt path is unsafe")
    data = (canonical_json(validated) + "\n").encode("utf-8")
    if path.exists():
        try:
            existing = validate_decision_basis(json.loads(path.read_text(encoding="utf-8")))
        except (OSError, UnicodeError, ValueError) as exc:
            raise DwError("persisted decision basis is malformed") from exc
        if existing != validated:
            raise DwError("decision basis identity collides with different content")
        return existing, False
    descriptor, temporary_name = tempfile.mkstemp(prefix=".decision.", dir=str(directory))
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
    return validated, True


def read_decision_bases(run_dir: Path) -> list[dict]:
    directory = _decision_directory(run_dir, create=False)
    if not directory.exists():
        return []
    result = []
    for path in sorted(directory.iterdir(), key=lambda item: item.name):
        if path.is_symlink() or not path.is_file() or not re.fullmatch(r"[0-9a-f]{64}\.json", path.name):
            raise DwError("decision basis receipt inventory has an unsafe entry")
        try:
            document = validate_decision_basis(json.loads(path.read_text(encoding="utf-8")))
        except (OSError, UnicodeError, ValueError) as exc:
            raise DwError("persisted decision basis is malformed") from exc
        if path.stem != document["decision_id"][7:]:
            raise DwError("decision basis path and identity disagree")
        result.append(document)
    return sorted(result, key=lambda item: (item["resulting_ledger_event"], item["decision_id"]))


def ledger_event_detail(document: Mapping[str, object]) -> dict[str, object]:
    validated = validate_decision_basis(dict(document))
    return {
        "decision_id": validated["decision_id"],
        "decision_kind": validated["decision_kind"],
        "basis_type": validated["basis_type"],
        "resulting_ledger_event": validated["resulting_ledger_event"],
    }


def record_run_decision_basis(
    root: Path,
    run_id: str,
    projection: Mapping[str, object],
    *,
    decision_kind: str,
    basis_type: str,
    outcome: str,
    reason_code: str,
    rule_ref: str = "",
    score_ref: str = "",
    input_receipt_refs: Iterable[str] = (),
    memory_refs: Optional[Iterable[str]] = None,
    dissent_refs: Iterable[str] = (),
    node_id: Optional[str] = None,
    now=None,
) -> tuple[dict, dict[str, object]]:
    """Persist and ledger-reference one orchestration decision exactly once."""
    from . import orchestration_run

    recalled, revision = decision_context(projection, node_id)
    receipt_refs = list(input_receipt_refs)
    if not receipt_refs and projection.get("grant_hash"):
        receipt_refs = [str(projection["grant_hash"])]
    document = build_decision_basis(
        subject=decision_subject("run", run_id),
        decision_kind=decision_kind,
        basis_type=basis_type,
        outcome=outcome,
        reason_code=reason_code,
        rule_ref=rule_ref,
        score_ref=score_ref,
        input_receipt_refs=receipt_refs,
        memory_refs=recalled if memory_refs is None else memory_refs,
        dissent_refs=dissent_refs,
        resulting_ledger_event=str(projection["ledger_head"]),
        source_revision=revision,
    )
    run_dir = orchestration_run._run_dir(Path(root).resolve(), run_id)
    stored, _created = persist_decision_basis(run_dir, document)
    events = orchestration_run._read_events(run_dir, run_id)
    if not any(
        event.get("event") == DECISION_BASIS_EVENT
        and isinstance(event.get("detail"), Mapping)
        and event["detail"].get("decision_id") == stored["decision_id"]
        for event in events
    ):
        updated = orchestration_run.record_runtime_event(
            Path(root).resolve(), run_id, DECISION_BASIS_EVENT,
            ledger_event_detail(stored), str(events[-1]["event_hash"]), now=now,
        )
    else:
        updated = orchestration_run.replay_run(Path(root).resolve(), run_id, now=now)
    return stored, updated


def record_program_decision_basis(
    root: Path,
    run_id: str,
    projection: Mapping[str, object],
    *,
    decision_kind: str,
    basis_type: str,
    outcome: str,
    reason_code: str,
    rule_ref: str = "",
    score_ref: str = "",
    input_receipt_refs: Iterable[str] = (),
    memory_refs: Optional[Iterable[str]] = None,
    dissent_refs: Iterable[str] = (),
    node_id: Optional[str] = None,
    now=None,
) -> tuple[dict, dict[str, object]]:
    """Persist and ledger-reference one autonomous-program decision exactly once."""
    from . import program_run

    recalled, revision = decision_context(projection, node_id)
    receipt_refs = list(input_receipt_refs)
    if not receipt_refs and projection.get("grant_hash"):
        receipt_refs = [str(projection["grant_hash"])]
    document = build_decision_basis(
        subject=decision_subject("program", run_id),
        decision_kind=decision_kind,
        basis_type=basis_type,
        outcome=outcome,
        reason_code=reason_code,
        rule_ref=rule_ref,
        score_ref=score_ref,
        input_receipt_refs=receipt_refs,
        memory_refs=recalled if memory_refs is None else memory_refs,
        dissent_refs=dissent_refs,
        resulting_ledger_event=str(projection["ledger_head"]),
        source_revision=revision,
    )
    run_dir = program_run._run_dir(Path(root).resolve(), run_id)
    stored, _created = persist_decision_basis(run_dir, document)
    events = program_run._events(run_dir, run_id)
    if not any(
        event.get("event") == DECISION_BASIS_EVENT
        and isinstance(event.get("detail"), Mapping)
        and event["detail"].get("decision_id") == stored["decision_id"]
        for event in events
    ):
        updated = program_run.record_program_decision_basis(
            Path(root).resolve(), run_id, ledger_event_detail(stored),
            str(events[-1]["event_hash"]), now=now,
        )
    else:
        updated = program_run.replay_program(Path(root).resolve(), run_id, now=now)
    return stored, updated
