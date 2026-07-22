"""Replayable bounded debate, council, meta-audit, and architect protocol.

This module is deliberately narrower than the Phase-26 program conductor.  It
compiles one already-assigned workflow debate into a finite protocol and
provides a pure append-only event machine for claims and typed receipts.  It
does not dispatch an agent, create a grant, write a repository, or advance a
roadmap.  The later conductor can place these transitions behind exact program
authority without reinterpreting council semantics.

Durable state contains declared artifact metadata, citations, concise verdict
rationales, aggregation facts, and lineage.  Prompt bodies, transport logs,
private reasoning, and artifact bodies are not accepted by the closed receipt
schema.

The contract is ``docs/programs.md`` (WLA-26-05).
"""

from __future__ import annotations

import hashlib
import re
from datetime import datetime, timezone
from typing import Any

from .model import DwError
from .orchestration import canonical_json


DELIBERATION_PLAN_KIND = "delivery-workbench-deliberation-plan"
DELIBERATION_EVENT_KIND = "delivery-workbench-deliberation-event"
DELIBERATION_PROJECTION_KIND = "delivery-workbench-deliberation-projection"
DELIBERATION_SIMULATION_KIND = "delivery-workbench-deliberation-simulation"
DELIBERATION_SCHEMA_VERSION = 1

COUNCIL_VERDICT_KIND = "delivery-workbench-council-verdict"
META_VERDICT_KIND = "delivery-workbench-meta-verdict"
ARCHITECT_VERDICT_KIND = "delivery-workbench-architecture-verdict"
COUNCIL_DECISION_KIND = "delivery-workbench-decision"

ROUND_STAGES = ("proposal", "critique", "rebuttal", "judgment")
VOTES = ("advance", "repair", "abstain")
JUDGMENT_RESULTS = (
    "advance", "repair", "redeliberate", "dissent", "quorum-lost",
    "checkpoint",
)
META_RESULTS = ("uphold", "overturn", "escalate")
ARCHITECT_RESULTS = ("approve", "repair", "escalate", "veto")

_SAFE_ID_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_.:/@-]{0,255}$")
_HASH_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
_REF_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:/@#-]{0,511}$")
_EVENT_KEYS = {
    "kind", "schema_version", "protocol_id", "seq", "event", "ts",
    "detail", "prev_hash", "event_hash",
}
_EVENT_DETAIL_KEYS = {
    "protocol_started": {
        "plan_hash", "program_run_id", "workflow_address", "council_id",
        "maximum",
    },
    "speaker_claimed": {
        "claim_id", "idempotency_key", "address", "round", "stage",
        "slot", "role", "seat_address", "agent", "profile", "principal_fingerprint",
        "assignment_generation", "workspace_domain", "session_binding_key",
        "execution", "packet",
    },
    "artifact_recorded": {
        "claim_id", "address", "artifact_kind", "content_hash",
        "content_ref", "bytes", "tokens", "citations", "vote",
        "submitted_result", "result", "rationale", "obligations",
        "aggregation", "route", "receipt_hash",
    },
    "member_replaced": {
        "binding_key", "role", "slot", "reason", "old", "new",
        "preserved_lineage", "invalidated_claim_id", "dissent_before",
    },
    "budget_exhausted": {
        "counter", "limit", "consumed", "requested", "active_claim_id",
        "route",
    },
}
_SUBMISSION_KEYS = {
    "kind", "content_hash", "content_ref", "bytes", "tokens", "citations",
    "vote", "result", "rationale", "obligations",
}
_OBLIGATION_KEYS = {
    "id", "kind", "statement", "priority", "blocking",
    "accountable_role", "target", "citations", "acceptance", "state",
}
OBLIGATION_KINDS = (
    "backlog", "technical-debt", "risk", "research", "follow-up",
)
OBLIGATION_PRIORITIES = ("critical", "high", "medium", "low")
_ARCHITECT_KEYS = {"boundary", "rubric", "evidence", "routes"}
_ARCHITECT_ROUTE_KEYS = {"approve", "repair", "escalate", "veto"}
_EXECUTION_KEYS = {
    "harness", "adapter", "adapter_version", "router", "provider",
    "model_vendor", "model_family", "model", "model_revision",
    "model_binding", "auth_domain_fingerprint", "capability_fingerprint",
}
_DECISION_KEYS = {
    "kind", "schema_version", "decision_type", "status", "protocol_id",
    "plan_hash", "assignment_hash", "program_run_id", "phase", "story",
    "workflow_address", "council_id", "charter_hash", "subject", "rubric",
    "round", "authority", "chair_seat", "participants",
    "source_receipt_hashes", "result", "rationale", "citations",
    "alternatives", "accepted_risks", "dissent", "obligations", "route",
    "issued_at", "protocol_ledger_head", "starts_work", "writes_state",
    "writes_repository", "writes_roadmap", "creates_grant", "payload_hash",
    "decision_hash",
}
_DECISION_AUTHORITY_KEYS = {
    "kind", "basis", "rule", "decider_seat", "decider",
    "checkpoint_port", "assignment_hash",
}
_DECIDER_KEYS = {
    "address", "role", "duty", "slot", "agent", "profile",
    "principal_fingerprint", "assignment_generation", "session_binding_key",
    "workspace_domain", "execution",
}
_PARTICIPANT_KEYS = {
    "address", "role", "slot", "agent", "profile",
    "principal_fingerprint", "assignment_generation", "workspace_domain",
    "session_binding_key", "execution",
}
_DECISION_DISSENT_KEYS = {
    "role", "slot", "principal_fingerprint", "vote", "receipt_hash",
}
_QUALITY_SUBJECT_KEYS = {
    "kind", "hash", "repository_hash", "program_hash", "program_run_id",
    "phase", "story", "workflow_address", "assignment_hash",
    "assignment_generation", "ledger_head", "implementer_principals",
}
_MUTATING_CAPABILITIES = {
    "workspace:write", "integration:apply", "contract:generate",
    "evidence:materialize", "git:commit", "git:push",
    "roadmap:story-start", "roadmap:story-complete",
    "roadmap:phase-advance",
}


class DeliberationError(DwError):
    """A closed protocol compilation, receipt, or replay refusal."""


def _sha(value: object) -> str:
    return "sha256:" + hashlib.sha256(
        canonical_json(value).encode("utf-8")
    ).hexdigest()


def _require(condition: bool, code: str, message: str) -> None:
    if not condition:
        raise DeliberationError(f"{code}: {message}")


def _exact(value: object, keys: set[str], label: str) -> dict[str, object]:
    _require(isinstance(value, dict), "wrong-type", f"{label} must be an object")
    mapping = value
    unknown = sorted(set(mapping) - keys)
    _require(not unknown, "unknown-key", f"{label} has unknown keys: {', '.join(unknown)}")
    return mapping


def _safe_string(value: object, label: str, *, reference: bool = False) -> str:
    pattern = _REF_RE if reference else _SAFE_ID_RE
    _require(isinstance(value, str) and bool(pattern.fullmatch(value)), "unsafe-value", f"{label} is not a safe bounded string")
    return value


def _hash(value: object, label: str) -> str:
    _require(isinstance(value, str) and bool(_HASH_RE.fullmatch(value)), "invalid-hash", f"{label} must be sha256:<hex>")
    return value


def _timestamp(value: object, label: str = "timestamp") -> datetime:
    _require(isinstance(value, str) and value.endswith("Z"), "invalid-time", f"{label} must be a UTC timestamp ending in Z")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise DeliberationError(f"invalid-time: {label} is not ISO-8601") from exc
    _require(parsed.tzinfo is not None, "invalid-time", f"{label} must include a timezone")
    return parsed.astimezone(timezone.utc)


def _bounded_text(value: object, label: str, maximum: int) -> str:
    _require(
        isinstance(value, str)
        and 0 < len(value.encode("utf-8")) <= maximum
        and "\x00" not in value,
        "invalid-text", f"{label} must be non-empty and at most {maximum} bytes",
    )
    return value


def _obligations(value: object) -> list[dict[str, object]]:
    _require(
        isinstance(value, list) and len(value) <= 64,
        "obligations-invalid",
        "council judgment must carry an explicit bounded obligations array",
    )
    result: list[dict[str, object]] = []
    seen: set[str] = set()
    for index, candidate in enumerate(value):
        label = f"obligations[{index}]"
        raw = _exact(candidate, _OBLIGATION_KEYS, label)
        _require(set(raw) == _OBLIGATION_KEYS, "obligations-invalid", f"{label} must use exact keys")
        obligation_id = _safe_string(raw.get("id"), f"{label}.id")
        _require(obligation_id not in seen, "obligations-invalid", "obligation ids must be unique")
        seen.add(obligation_id)
        kind = raw.get("kind")
        priority = raw.get("priority")
        _require(kind in OBLIGATION_KINDS, "obligations-invalid", f"{label}.kind is unsupported")
        _require(priority in OBLIGATION_PRIORITIES, "obligations-invalid", f"{label}.priority is unsupported")
        blocking = raw.get("blocking")
        _require(isinstance(blocking, bool), "obligations-invalid", f"{label}.blocking must be boolean")
        target = raw.get("target")
        _require(
            target is None or (
                isinstance(target, str) and bool(_REF_RE.fullmatch(target))
            ),
            "obligations-invalid", f"{label}.target must be null or a safe reference",
        )
        citations = raw.get("citations")
        _require(
            isinstance(citations, list) and 0 < len(citations) <= 32
            and all(isinstance(item, str) and _REF_RE.fullmatch(item) for item in citations)
            and len(set(citations)) == len(citations),
            "obligations-invalid", f"{label}.citations must be non-empty unique references",
        )
        _require(raw.get("state") == "open", "obligations-invalid", f"{label}.state must start open")
        result.append({
            "id": obligation_id,
            "kind": kind,
            "statement": _bounded_text(raw.get("statement"), f"{label}.statement", 2_000),
            "priority": priority,
            "blocking": blocking,
            "accountable_role": _safe_string(raw.get("accountable_role"), f"{label}.accountable_role"),
            "target": target,
            "citations": list(citations),
            "acceptance": _bounded_text(raw.get("acceptance"), f"{label}.acceptance", 2_000),
            "state": "open",
        })
    return result


def _rubric(value: object, label: str) -> dict[str, object]:
    mapping = _exact(value, {"slug", "semantic_hash", "criteria"}, label)
    slug = _safe_string(mapping.get("slug"), f"{label}.slug")
    semantic_hash = _hash(mapping.get("semantic_hash"), f"{label}.semantic_hash")
    criteria = mapping.get("criteria")
    _require(
        isinstance(criteria, list) and 0 < len(criteria) <= 100
        and all(isinstance(item, str) and _SAFE_ID_RE.fullmatch(item) for item in criteria)
        and len(set(criteria)) == len(criteria),
        "invalid-rubric", f"{label}.criteria must be a non-empty unique safe-id list",
    )
    return {"slug": slug, "semantic_hash": semantic_hash, "criteria": list(criteria)}


def _subject(value: object) -> dict[str, object]:
    mapping = _exact(value, _QUALITY_SUBJECT_KEYS, "subject")
    _require(
        set(mapping) in ({"kind", "hash"}, _QUALITY_SUBJECT_KEYS),
        "invalid-subject",
        "subject must be the exact minimal or freshness-bound form",
    )
    result: dict[str, object] = {
        "kind": _safe_string(mapping.get("kind"), "subject.kind"),
        "hash": _hash(mapping.get("hash"), "subject.hash"),
    }
    if set(mapping) == {"kind", "hash"}:
        return result
    phase = mapping.get("phase")
    generation = mapping.get("assignment_generation")
    _require(isinstance(phase, int) and not isinstance(phase, bool) and phase > 0, "invalid-subject", "subject.phase must be positive")
    _require(isinstance(generation, int) and not isinstance(generation, bool) and generation > 0, "invalid-subject", "subject.assignment_generation must be positive")
    principals = mapping.get("implementer_principals")
    _require(
        isinstance(principals, list) and principals
        and len(principals) <= 128 and len(set(principals)) == len(principals),
        "invalid-subject", "subject implementer principals must be non-empty and unique",
    )
    result.update({
        "repository_hash": _hash(mapping.get("repository_hash"), "subject.repository_hash"),
        "program_hash": _hash(mapping.get("program_hash"), "subject.program_hash"),
        "program_run_id": _safe_string(mapping.get("program_run_id"), "subject.program_run_id", reference=True),
        "phase": phase,
        "story": _safe_string(mapping.get("story"), "subject.story"),
        "workflow_address": _safe_string(mapping.get("workflow_address"), "subject.workflow_address", reference=True),
        "assignment_hash": _hash(mapping.get("assignment_hash"), "subject.assignment_hash"),
        "assignment_generation": generation,
        "ledger_head": _hash(mapping.get("ledger_head"), "subject.ledger_head"),
        "implementer_principals": [
            _hash(item, f"subject.implementer_principals[{index}]")
            for index, item in enumerate(principals)
        ],
    })
    return result


def _evidence(value: object, label: str = "evidence") -> list[dict[str, str]]:
    _require(isinstance(value, list) and len(value) <= 100, "invalid-evidence", f"{label} must be a bounded array")
    receipts: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for index, raw in enumerate(value):
        mapping = _exact(raw, {"kind", "hash", "ref"}, f"{label}[{index}]")
        receipt = {
            "kind": _safe_string(mapping.get("kind"), f"{label}[{index}].kind"),
            "hash": _hash(mapping.get("hash"), f"{label}[{index}].hash"),
            "ref": _safe_string(mapping.get("ref"), f"{label}[{index}].ref", reference=True),
        }
        key = (receipt["hash"], receipt["ref"])
        _require(key not in seen, "duplicate-evidence", f"{label} repeats {receipt['ref']!r}")
        seen.add(key)
        receipts.append(receipt)
    return receipts


def _route(value: object, label: str) -> dict[str, str]:
    mapping = _exact(value, {"kind", "target"}, label)
    kind = mapping.get("kind")
    _require(kind in {"node", "terminal", "action"}, "invalid-route", f"{label}.kind is unsupported")
    return {
        "kind": str(kind),
        "target": _safe_string(mapping.get("target"), f"{label}.target"),
    }


def _execution(value: object, label: str = "execution") -> dict[str, object]:
    raw = _exact(value, _EXECUTION_KEYS, label)
    binding = raw.get("model_binding")
    _require(
        binding in {
            "exact-revision", "requested-alias",
            "adapter-default-unresolved",
        },
        "execution-invalid", f"{label}.model_binding is unsupported",
    )
    model = raw.get("model")
    revision = raw.get("model_revision")
    _require(
        model is None or (
            isinstance(model, str) and 0 < len(model.encode("utf-8")) <= 200
        ),
        "execution-invalid", f"{label}.model must be null or bounded",
    )
    _require(
        revision is None or (
            isinstance(revision, str)
            and 0 < len(revision.encode("utf-8")) <= 200
        ),
        "execution-invalid", f"{label}.model_revision must be null or bounded",
    )
    if binding == "exact-revision":
        _require(model is not None and revision is not None, "execution-invalid", f"{label} exact revision is incomplete")
    elif binding == "requested-alias":
        _require(model is not None, "execution-invalid", f"{label} alias binding has no requested model")
    else:
        _require(model is None and revision is None, "execution-invalid", f"{label} unresolved binding names a model")
    return {
        "harness": _safe_string(raw.get("harness"), f"{label}.harness"),
        "adapter": _safe_string(raw.get("adapter"), f"{label}.adapter"),
        "adapter_version": _safe_string(
            raw.get("adapter_version"), f"{label}.adapter_version"
        ),
        "router": _safe_string(raw.get("router"), f"{label}.router"),
        "provider": _safe_string(raw.get("provider"), f"{label}.provider"),
        "model_vendor": _safe_string(
            raw.get("model_vendor"), f"{label}.model_vendor"
        ),
        "model_family": _safe_string(
            raw.get("model_family"), f"{label}.model_family"
        ),
        "model": model,
        "model_revision": revision,
        "model_binding": binding,
        "auth_domain_fingerprint": _hash(
            raw.get("auth_domain_fingerprint"),
            f"{label}.auth_domain_fingerprint",
        ),
        "capability_fingerprint": _hash(
            raw.get("capability_fingerprint"),
            f"{label}.capability_fingerprint",
        ),
    }


def _member(role: dict[str, object], raw: dict[str, object]) -> dict[str, object]:
    packet = role.get("packet_policy")
    _require(isinstance(packet, dict), "assignment-invalid", f"role {role.get('role')!r} has no packet policy")
    workspace = packet.get("workspace")
    capabilities = packet.get("effective_capability_ceiling", [])
    _require(workspace == "read-only", "workspace-denied", f"deliberation role {role.get('role')!r} must be read-only")
    _require(isinstance(capabilities, list), "assignment-invalid", "effective capability ceiling must be a list")
    _require(not (_MUTATING_CAPABILITIES & set(capabilities)), "capability-denied", f"deliberation role {role.get('role')!r} has mutation authority")
    return {
        "binding_key": f"{role['role']}[{raw['slot']}]",
        "role": role["role"],
        "duty": role["duty"],
        "slot": raw["slot"],
        "address": raw["address"],
        "agent": raw["agent"],
        "profile": raw["profile"],
        "execution": _execution(raw.get("execution")),
        "principal_fingerprint": _hash(raw.get("principal_fingerprint"), "principal_fingerprint"),
        "assignment_generation": raw["assignment_generation"],
        "session_binding_key": _hash(raw.get("session_binding_key"), "session_binding_key"),
        "workspace_domain": raw["workspace_domain"],
        "capability_ceiling": list(capabilities),
        "packet_policy_hash": _sha(packet),
    }


def _find_debate(workflow: dict[str, object], selector: str | None) -> dict[str, object]:
    debates = workflow.get("debates")
    _require(isinstance(debates, list) and debates, "debate-missing", "compiled workflow has no debate")
    if selector is None:
        _require(len(debates) == 1, "debate-ambiguous", "select one debate address explicitly")
        return debates[0]
    matches = [
        item for item in debates
        if item.get("address") == selector or str(item.get("address", "")).endswith("/" + selector)
    ]
    _require(len(matches) == 1, "debate-missing", f"debate selector {selector!r} did not resolve uniquely")
    return matches[0]


def _find_role(assignment: dict[str, object], role_id: str) -> dict[str, object]:
    roles = assignment.get("roles")
    _require(isinstance(roles, list), "assignment-invalid", "assignment roles are absent")
    matches = [role for role in roles if role.get("role") == role_id]
    _require(len(matches) == 1, "role-unavailable", f"assigned role {role_id!r} did not resolve uniquely")
    _require(bool(matches[0].get("members")), "role-unavailable", f"assigned role {role_id!r} has no members")
    return matches[0]


def _architect_policy(
    assignment: dict[str, object],
    raw: object,
) -> tuple[dict[str, object] | None, dict[str, object] | None]:
    if raw is None:
        return None, None
    mapping = _exact(raw, _ARCHITECT_KEYS, "architect")
    boundary = mapping.get("boundary")
    _require(boundary in {"story", "phase"}, "invalid-boundary", "architect boundary must be story or phase")
    rubric = _rubric(mapping.get("rubric"), "architect.rubric")
    evidence = _evidence(mapping.get("evidence", []), "architect.evidence")
    routes_raw = _exact(mapping.get("routes"), _ARCHITECT_ROUTE_KEYS, "architect.routes")
    _require(set(routes_raw) == _ARCHITECT_ROUTE_KEYS, "missing-route", "architect must route every result")
    routes: dict[str, str] = {}
    for result in ARCHITECT_RESULTS:
        target = routes_raw.get(result)
        allowed = {"retain"} if result == "approve" else {"repair", "escalate", "block", "checkpoint", "abort"}
        _require(target in allowed, "invalid-route", f"architect route for {result!r} is unsupported")
        routes[result] = str(target)
    role = next(
        (item for item in assignment.get("roles", []) if item.get("duty") == "master-architect"),
        None,
    )
    _require(isinstance(role, dict) and len(role.get("members", [])) == 1, "role-unavailable", "architect review requires one assigned master architect")
    member = _member(role, role["members"][0])
    packet = role["packet_policy"]
    context = packet.get("context", {}).get("allow", [])
    _require(boundary in context, "visibility-denied", f"master architect cannot inspect declared {boundary} context")
    readable = set(packet.get("artifacts", {}).get("read", []))
    missing = sorted({item["kind"] for item in evidence} - readable)
    _require(not missing, "visibility-denied", f"master architect cannot read artifact kinds: {', '.join(missing)}")
    return {
        "boundary": boundary,
        "rubric": rubric,
        "evidence": evidence,
        "routes": routes,
        "authority": {
            "workspace": "read-only",
            "may_modify_implementation": False,
            "may_integrate": False,
            "may_commit": False,
            "may_push": False,
            "may_write_roadmap": False,
        },
    }, member


def compile_deliberation_plan(
    workflow: dict[str, object],
    assignment: dict[str, object],
    *,
    council_id: str,
    program_run_id: str,
    phase: int,
    story: str,
    rubric: dict[str, object],
    subject: dict[str, object],
    evidence: list[dict[str, object]],
    debate_address: str | None = None,
    architect: dict[str, object] | None = None,
) -> dict[str, object]:
    """Compile one immutable, finite, already-assigned deliberation plan."""
    _require(workflow.get("kind") == "delivery-workbench-compiled-workflow", "workflow-invalid", "a compiled workflow is required")
    _require(assignment.get("kind") == "delivery-workbench-team-assignment", "assignment-invalid", "a team assignment is required")
    _require(bool(assignment.get("applicable")), "assignment-invalid", "team assignment is not applicable")
    _safe_string(council_id, "council_id")
    _safe_string(program_run_id, "program_run_id")
    _require(isinstance(phase, int) and not isinstance(phase, bool) and phase > 0, "invalid-phase", "phase must be positive")
    _safe_string(story, "story")

    debate = _find_debate(workflow, debate_address)
    workflow_address = str(debate["address"])
    councils = assignment.get("councils")
    _require(isinstance(councils, list), "assignment-invalid", "assignment councils are absent")
    matches = [item for item in councils if item.get("id") == council_id]
    _require(len(matches) == 1, "council-missing", f"council {council_id!r} did not resolve uniquely")
    council = matches[0]
    _require(bool(council.get("quorum_satisfiable")), "quorum-lost", "assigned council cannot satisfy distinct-principal quorum")
    _require(
        int(council.get("quorum", 0)) >= int(debate.get("quorum", 0)),
        "council-workflow-mismatch",
        "organization council quorum cannot weaken the workflow debate quorum",
    )

    participant_roles = list(debate.get("participants", []))
    judge_role_id = str(debate.get("judge_role"))
    council_roles = list(council.get("members", []))
    _require(set(council_roles) == set(participant_roles) | {judge_role_id}, "council-workflow-mismatch", "council members must exactly match debate speakers plus judge")
    _require(council.get("judge") == judge_role_id, "council-workflow-mismatch", "workflow and council judges differ")

    speakers: list[dict[str, object]] = []
    for role_id in participant_roles:
        role = _find_role(assignment, str(role_id))
        for raw_member in role["members"]:
            speakers.append(_member(role, raw_member))
    judge_role = _find_role(assignment, judge_role_id)
    _require(len(judge_role["members"]) == 1, "judge-cardinality", "debate requires exactly one assigned judge")
    judge = _member(judge_role, judge_role["members"][0])
    _require(judge["duty"] in {"judge", "verifier"}, "judgment-not-authorized", "council judge lacks a judgment duty")

    all_council = speakers + [judge]
    distinct_principals = sorted({str(item["principal_fingerprint"]) for item in all_council})
    _require(len(distinct_principals) >= int(council["quorum"]), "quorum-lost", "distinct assigned principals cannot reach quorum")

    audit = council.get("audit", {"mode": "none", "sample_size": 0, "on_overturn": "repair", "on_escalate": "escalate"})
    _require(isinstance(audit, dict), "council-invalid", "compiled council audit is absent")
    meta_member: dict[str, object] | None = None
    if audit.get("mode") != "none":
        meta_role_id = council.get("meta_verifier")
        _require(isinstance(meta_role_id, str), "role-unavailable", "enabled audit has no meta-verifier role")
        meta_role = _find_role(assignment, meta_role_id)
        _require(len(meta_role["members"]) == 1 and meta_role.get("duty") == "meta-verifier", "role-unavailable", "meta-audit requires one assigned meta-verifier")
        meta_member = _member(meta_role, meta_role["members"][0])
        _require(
            meta_member["principal_fingerprint"] not in {item["principal_fingerprint"] for item in all_council},
            "separation-violation", "meta-verifier shares a principal with an audited verdict author",
        )

    architect_policy, architect_member = _architect_policy(assignment, architect)
    normalized_rubric = _rubric(rubric, "rubric")
    normalized_subject = _subject(subject)
    if set(normalized_subject) == _QUALITY_SUBJECT_KEYS:
        _require(normalized_subject["program_run_id"] == program_run_id, "subject-mismatch", "quality subject program run differs from the deliberation")
        _require(normalized_subject["phase"] == phase, "subject-mismatch", "quality subject phase differs from the deliberation")
        _require(normalized_subject["story"] == story, "subject-mismatch", "quality subject story differs from the deliberation")
        _require(normalized_subject["workflow_address"] == workflow_address, "subject-mismatch", "quality subject workflow differs from the deliberation")
        _require(normalized_subject["assignment_hash"] == assignment["assignment_hash"], "subject-mismatch", "quality subject assignment differs from the deliberation")
    normalized_evidence = _evidence(evidence)

    maximum_rounds = int(debate["max_rounds"])
    artifact_bytes = int(debate["artifact_max_bytes"])
    artifact_tokens = int(debate["artifact_max_tokens"])
    starts_per_round = len(speakers) * 3 + 1
    debate_starts = starts_per_round * maximum_rounds
    auxiliary_starts = int(meta_member is not None) + int(architect_member is not None)
    maximum = {
        "rounds": maximum_rounds,
        "speaker_slots": len(speakers),
        "starts_per_round": starts_per_round,
        "agent_starts": debate_starts + auxiliary_starts,
        "artifacts": debate_starts + auxiliary_starts,
        "output_bytes": (debate_starts + auxiliary_starts) * artifact_bytes,
        "tokens": (debate_starts + auxiliary_starts) * artifact_tokens,
        "wall_seconds": (maximum_rounds + auxiliary_starts) * int(debate["round_timeout_seconds"]),
    }
    limits = council.get("budgets")
    _require(isinstance(limits, dict), "council-invalid", "compiled council budgets are absent")
    comparisons = {
        "rounds": "max_rounds",
        "agent_starts": "max_speaker_starts",
        "artifacts": "max_artifacts",
        "output_bytes": "max_output_bytes",
        "tokens": "max_tokens",
        "wall_seconds": "max_wall_seconds",
    }
    for actual, limit in comparisons.items():
        _require(int(maximum[actual]) <= int(limits[limit]), "council-budget-exceeded", f"compiled {actual} maximum {maximum[actual]} exceeds {limit}={limits[limit]}")

    decision = council.get("decision")
    _require(isinstance(decision, dict), "council-invalid", "compiled council decision policy is absent")
    for role_id in decision.get("veto_roles", []):
        _require(role_id in council_roles, "council-invalid", f"veto role {role_id!r} is not a member")
    primary_authority = (
        {
            "kind": "judge",
            "rule": None,
            "decider_seat": judge["address"],
        }
        if decision["method"] == "judge"
        else {
            "kind": "rule",
            "rule": decision["method"],
            "decider_seat": None,
        }
    )
    tie_authority = {
        "judge": {
            "kind": "judge", "rule": None,
            "decider_seat": judge["address"],
        },
        "checkpoint": {
            "kind": "checkpoint", "rule": None,
            "decider_seat": None,
        },
        "dissent": {
            "kind": "rule", "rule": "dissent",
            "decider_seat": None,
        },
    }[str(debate["tie_policy"])]
    authority_charter = {
        "primary": primary_authority,
        "tie": tie_authority,
        "chair_seat": judge["address"],
        "possible_agent_decider": (
            judge
            if primary_authority["kind"] == "judge"
            or tie_authority["kind"] == "judge"
            else None
        ),
        "checkpoint_port": (
            "program-decision-checkpoint"
            if tie_authority["kind"] == "checkpoint" else None
        ),
    }

    verdict_routes = debate.get("verdict_routes")
    _require(isinstance(verdict_routes, dict), "workflow-invalid", "compiled debate verdict routes are absent")
    routes = {
        result: _route(verdict_routes.get(result), f"debate.routes.{result}")
        for result in ("advance", "repair", "dissent", "quorum-lost", "exhausted")
    }
    routes["checkpoint"] = {"kind": "action", "target": "checkpoint"}

    schedule: list[dict[str, object]] = []
    for round_number in range(1, maximum_rounds + 1):
        for stage in ROUND_STAGES[:-1]:
            for member in speakers:
                schedule.append({
                    "address": f"{workflow_address}/round/{round_number}/{stage}/{member['binding_key']}",
                    "round": round_number,
                    "stage": stage,
                    "binding_key": member["binding_key"],
                    "role": member["role"],
                    "slot": member["slot"],
                })
        schedule.append({
            "address": f"{workflow_address}/round/{round_number}/judgment/{judge['binding_key']}",
            "round": round_number,
            "stage": "judgment",
            "binding_key": judge["binding_key"],
            "role": judge["role"],
            "slot": judge["slot"],
        })

    unsigned: dict[str, object] = {
        "kind": DELIBERATION_PLAN_KIND,
        "schema_version": DELIBERATION_SCHEMA_VERSION,
        "program_run_id": program_run_id,
        "phase": phase,
        "story": story,
        "workflow_address": workflow_address,
        "workflow_bundle_hash": workflow["bundle_hash"],
        "assignment_hash": assignment["assignment_hash"],
        "council_id": council_id,
        "council": {
            "members": council_roles,
            "quorum": council["quorum"],
            "workflow_quorum_floor": debate["quorum"],
            "distinct_principals": True,
            "decision": decision,
            "decision_authority": authority_charter,
            "audit": audit,
        },
        "debate": {
            "max_rounds": maximum_rounds,
            "artifact_max_bytes": artifact_bytes,
            "artifact_max_tokens": artifact_tokens,
            "round_timeout_seconds": debate["round_timeout_seconds"],
            "tie_policy": debate["tie_policy"],
            "dissent_policy": debate["dissent_policy"],
            "routes": routes,
        },
        "rubric": normalized_rubric,
        "subject": normalized_subject,
        "evidence": normalized_evidence,
        "speakers": speakers,
        "judge": judge,
        "meta_verifier": meta_member,
        "architect": architect_policy,
        "architect_member": architect_member,
        "round_schedule": schedule,
        "limits": dict(limits),
        "maximum": maximum,
        "proof": {
            "finite": True,
            "declared_artifacts_only": [
                "proposal", "critique", "rebuttal", "council-verdict",
                "meta-verdict", "architecture-verdict",
            ],
            "durable_bodies": False,
            "transport_transcript": False,
            "private_reasoning": False,
            "quorum_principals": distinct_principals,
            "aggregation": decision["method"],
            "tie_policy": debate["tie_policy"],
            "dissent_policy": debate["dissent_policy"],
            "verdict_effects": {
                "advance": "may-follow-declared-advance-route-after-required-audits",
                "repair": "follows-declared-repair-route",
                "redeliberate": "consumes-one-finite-round-or-exhausts",
                "dissent": "preserved-and-follows-declared-dissent-route",
                "quorum-lost": "follows-declared-quorum-loss-route",
            },
        },
        "starts_work": False,
        "dispatches_agents": False,
        "writes_run_state": False,
        "writes_repository": False,
        "writes_roadmap": False,
        "creates_grant": False,
        "requires_program_grant_for_dispatch": True,
    }
    plan_hash = _sha(unsigned)
    protocol_id = "delib-" + plan_hash.partition(":")[2][:24]
    return {**unsigned, "protocol_id": protocol_id, "plan_hash": plan_hash}


def simulate_deliberation(plan: dict[str, object]) -> dict[str, object]:
    _validate_plan(plan)
    return {
        "kind": DELIBERATION_SIMULATION_KIND,
        "schema_version": DELIBERATION_SCHEMA_VERSION,
        "protocol_id": plan["protocol_id"],
        "plan_hash": plan["plan_hash"],
        "round_schedule": plan["round_schedule"],
        "maximum": plan["maximum"],
        "limits": plan["limits"],
        "quorum": plan["council"]["quorum"],
        "decision": plan["council"]["decision"],
        "decision_authority": plan["council"]["decision_authority"],
        "audit": plan["council"]["audit"],
        "routes": plan["debate"]["routes"],
        "proof": plan["proof"],
        "starts_work": False,
        "dispatches_agents": False,
        "writes_run_state": False,
    }


def _validate_plan(plan: dict[str, object]) -> None:
    _require(isinstance(plan, dict) and plan.get("kind") == DELIBERATION_PLAN_KIND, "plan-invalid", "compiled deliberation plan required")
    _require(plan.get("schema_version") == DELIBERATION_SCHEMA_VERSION, "plan-invalid", "unsupported deliberation schema")
    plan_hash = plan.get("plan_hash")
    _hash(plan_hash, "plan_hash")
    unsigned = {key: value for key, value in plan.items() if key not in {"plan_hash", "protocol_id"}}
    _require(_sha(unsigned) == plan_hash, "plan-stale", "deliberation plan hash does not match its content")
    expected_id = "delib-" + str(plan_hash).partition(":")[2][:24]
    _require(plan.get("protocol_id") == expected_id, "plan-stale", "deliberation protocol id is invalid")


def _event(
    plan: dict[str, object],
    events: list[dict[str, object]],
    kind: str,
    detail: dict[str, object],
    now: str,
) -> dict[str, object]:
    _timestamp(now)
    unsigned: dict[str, object] = {
        "kind": DELIBERATION_EVENT_KIND,
        "schema_version": DELIBERATION_SCHEMA_VERSION,
        "protocol_id": plan["protocol_id"],
        "seq": len(events) + 1,
        "event": kind,
        "ts": now,
        "detail": detail,
        "prev_hash": events[-1]["event_hash"] if events else "sha256:" + "0" * 64,
    }
    return {**unsigned, "event_hash": _sha(unsigned)}


def start_deliberation(plan: dict[str, object], now: str) -> list[dict[str, object]]:
    """Return a new in-memory protocol ledger; no external work is started."""
    _validate_plan(plan)
    detail = {
        "plan_hash": plan["plan_hash"],
        "program_run_id": plan["program_run_id"],
        "workflow_address": plan["workflow_address"],
        "council_id": plan["council_id"],
        "maximum": plan["maximum"],
    }
    events = [_event(plan, [], "protocol_started", detail, now)]
    replay_deliberation(plan, events)
    return events


def _initial_state(plan: dict[str, object], started: str) -> dict[str, Any]:
    members = {
        str(item["binding_key"]): dict(item)
        for item in list(plan["speakers"]) + [plan["judge"]]
        + ([plan["meta_verifier"]] if plan.get("meta_verifier") else [])
        + ([plan["architect_member"]] if plan.get("architect_member") else [])
    }
    return {
        "started": started,
        "members": members,
        "active": None,
        "claims": [],
        "completed_claims": [],
        "completed_addresses": set(),
        "submissions": [],
        "judgments": [],
        "meta_verdict": None,
        "architect_verdict": None,
        "replacements": [],
        "dissent": [],
        "budget": {"agent_starts": 0, "artifacts": 0, "output_bytes": 0, "tokens": 0},
        "budget_exhaustion": None,
    }


def _final_judgment(state: dict[str, Any]) -> dict[str, object] | None:
    return state["judgments"][-1] if state["judgments"] else None


def _source_verdicts(state: dict[str, Any]) -> list[str]:
    judgment = _final_judgment(state)
    if judgment is None:
        return []
    round_number = judgment["round"]
    values = [
        item["receipt_hash"] for item in state["submissions"]
        if item["round"] == round_number and item["stage"] == "rebuttal"
    ]
    values.append(judgment["receipt_hash"])
    return values


def _underlying_route(plan: dict[str, object], state: dict[str, Any]) -> dict[str, str] | None:
    judgment = _final_judgment(state)
    if judgment is None or judgment["result"] == "redeliberate":
        return None
    return dict(judgment["route"])


def _packet(plan: dict[str, object], state: dict[str, Any], spec: dict[str, object]) -> dict[str, object]:
    prior = [item["receipt_hash"] for item in state["submissions"]]
    common: dict[str, object] = {
        "schema": "delivery-workbench-deliberation-packet@1",
        "program_run_id": plan["program_run_id"],
        "phase": plan["phase"],
        "story": plan["story"],
        "workflow_address": plan["workflow_address"],
        "subject": plan["subject"],
        "rubric": plan["rubric"],
        "evidence": plan["evidence"],
        "prior_receipts": prior,
        "round": spec["round"],
        "stage": spec["stage"],
        "artifact_bounds": {
            "max_bytes": plan["debate"]["artifact_max_bytes"],
            "max_tokens": plan["debate"]["artifact_max_tokens"],
        },
        "excluded": ["prompt-body", "transport-transcript", "private-reasoning", "artifact-body"],
    }
    if spec["stage"] == "meta-audit":
        lineage = _source_verdicts(state)
        audit = plan["council"]["audit"]
        if audit["mode"] == "full":
            selected = list(lineage)
        else:
            ranked = sorted(lineage, key=lambda item: (_sha({"plan": plan["plan_hash"], "verdict": item}), item))
            selected = ranked[: int(audit["sample_size"])]
        common.update({
            "verdict_lineage": lineage,
            "audited_receipts": selected,
            "audit_mode": audit["mode"],
            "implementation_write_allowed": False,
        })
    elif spec["stage"] == "architect-review":
        common.update({
            "boundary": plan["architect"]["boundary"],
            "rubric": plan["architect"]["rubric"],
            "evidence": plan["architect"]["evidence"],
            "verdict_lineage": _source_verdicts(state)
            + ([state["meta_verdict"]["receipt_hash"]] if state["meta_verdict"] else []),
            "authority": plan["architect"]["authority"],
        })
    elif spec["stage"] == "judgment":
        common.update({
            "decision_authority": plan["council"]["decision_authority"],
            "obligations_required": True,
            "allowed_obligation_kinds": list(OBLIGATION_KINDS),
        })
    common["packet_hash"] = _sha(common)
    return common


def _next_spec(plan: dict[str, object], state: dict[str, Any]) -> dict[str, object] | None:
    if state["budget_exhaustion"] is not None:
        return None
    judgment = _final_judgment(state)
    if judgment is None:
        current_round = 1
    elif judgment["result"] == "redeliberate":
        current_round = int(judgment["round"]) + 1
    else:
        current_round = None
    if current_round is not None and current_round <= int(plan["debate"]["max_rounds"]):
        for item in plan["round_schedule"]:
            if item["round"] == current_round and item["address"] not in state["completed_addresses"]:
                return dict(item)
    if judgment is None:
        return None
    if judgment["result"] == "redeliberate":
        return None
    if plan.get("meta_verifier") is not None and state["meta_verdict"] is None:
        member = plan["meta_verifier"]
        return {
            "address": f"{plan['workflow_address']}/meta-audit/{member['binding_key']}",
            "round": judgment["round"],
            "stage": "meta-audit",
            "binding_key": member["binding_key"],
            "role": member["role"],
            "slot": member["slot"],
        }
    if state["meta_verdict"] is not None and state["meta_verdict"]["result"] != "uphold":
        return None
    if plan.get("architect_member") is not None and state["architect_verdict"] is None:
        member = plan["architect_member"]
        return {
            "address": f"{plan['workflow_address']}/architect-review/{plan['architect']['boundary']}/{member['binding_key']}",
            "round": judgment["round"],
            "stage": "architect-review",
            "binding_key": member["binding_key"],
            "role": member["role"],
            "slot": member["slot"],
        }
    return None


def _claim_detail(plan: dict[str, object], state: dict[str, Any], spec: dict[str, object]) -> dict[str, object]:
    member = state["members"].get(spec["binding_key"])
    _require(member is not None, "assignment-invalid", f"no current binding for {spec['binding_key']!r}")
    packet = _packet(plan, state, spec)
    idem = _sha({
        "protocol": plan["protocol_id"], "address": spec["address"],
        "generation": member["assignment_generation"], "action": "agent-artifact",
    })
    claim_id = _sha({"idempotency_key": idem, "principal": member["principal_fingerprint"]})
    return {
        "claim_id": claim_id,
        "idempotency_key": idem,
        "address": spec["address"],
        "round": spec["round"],
        "stage": spec["stage"],
        "slot": spec["slot"],
        "role": spec["role"],
        "seat_address": member["address"],
        "agent": member["agent"],
        "profile": member["profile"],
        "principal_fingerprint": member["principal_fingerprint"],
        "assignment_generation": member["assignment_generation"],
        "workspace_domain": member["workspace_domain"],
        "session_binding_key": member["session_binding_key"],
        "execution": member["execution"],
        "packet": packet,
    }


def _decision_authority(
    plan: dict[str, object],
    state: dict[str, Any],
    basis: str,
) -> dict[str, object]:
    judge = state["members"][str(plan["judge"]["binding_key"])]
    if basis in {"judge", "tie-judge", "judge-veto"}:
        decider = {
            key: judge[key]
            for key in (
                "address", "role", "duty", "slot", "agent", "profile",
                "principal_fingerprint", "assignment_generation",
                "session_binding_key", "workspace_domain", "execution",
            )
        }
        return {
            "kind": "judge",
            "basis": basis,
            "rule": None,
            "decider_seat": judge["address"],
            "decider": decider,
            "checkpoint_port": None,
            "assignment_hash": plan["assignment_hash"],
        }
    if basis == "tie-checkpoint":
        return {
            "kind": "checkpoint",
            "basis": basis,
            "rule": None,
            "decider_seat": None,
            "decider": None,
            "checkpoint_port": "program-decision-checkpoint",
            "assignment_hash": plan["assignment_hash"],
        }
    return {
        "kind": "rule",
        "basis": basis,
        "rule": (
            plan["council"]["decision"]["method"]
            if basis in {"majority", "weighted", "unanimous"}
            else basis
        ),
        "decider_seat": None,
        "decider": None,
        "checkpoint_port": None,
        "assignment_hash": plan["assignment_hash"],
    }


def _judgment_analysis(
    plan: dict[str, object],
    state: dict[str, Any],
    round_number: int,
    submitted_result: str,
) -> tuple[str, dict[str, object], dict[str, str]]:
    votes = [
        item for item in state["submissions"]
        if item["round"] == round_number and item["stage"] == "rebuttal"
    ]
    by_principal: dict[str, dict[str, object]] = {}
    excluded: list[dict[str, object]] = []
    for vote in sorted(votes, key=lambda item: (str(item["role"]), int(item["slot"]))):
        principal = str(vote["principal_fingerprint"])
        if principal in by_principal:
            excluded.append({
                "role": vote["role"], "slot": vote["slot"],
                "principal_fingerprint": principal, "reason": "duplicate-principal",
                "receipt_hash": vote["receipt_hash"],
            })
        else:
            by_principal[principal] = vote
    unique_votes = list(by_principal.values())
    non_abstain = [item for item in unique_votes if item["vote"] != "abstain"]
    quorum_principals = {str(item["principal_fingerprint"]) for item in non_abstain}
    quorum_principals.add(str(plan["judge"]["principal_fingerprint"]))
    quorum = len(quorum_principals)
    decision = plan["council"]["decision"]
    weights = decision["weights"]
    advance_weight = sum(int(weights[item["role"]]) for item in non_abstain if item["vote"] == "advance")
    repair_weight = sum(int(weights[item["role"]]) for item in non_abstain if item["vote"] == "repair")
    advance_count = sum(item["vote"] == "advance" for item in non_abstain)
    repair_count = sum(item["vote"] == "repair" for item in non_abstain)
    method = decision["method"]
    threshold = int(decision["threshold"])
    vetoes = [
        item for item in non_abstain
        if item["role"] in decision["veto_roles"] and item["vote"] == "repair"
    ]

    allowed: set[str]
    basis: str
    if quorum < int(plan["council"]["quorum"]):
        allowed = {"quorum-lost"}
        basis = "quorum-lost"
    elif vetoes:
        allowed = {"repair"}
        basis = "veto"
    elif method == "judge":
        allowed = {"advance", "repair", "redeliberate"}
        basis = "judge"
    else:
        advance_score = advance_weight if method == "weighted" else advance_count
        repair_score = repair_weight if method == "weighted" else repair_count
        if method == "unanimous":
            if advance_count == threshold and repair_count == 0:
                clear = "advance"
            elif repair_count == threshold and advance_count == 0:
                clear = "repair"
            else:
                clear = None
        elif (advance_score >= threshold) != (repair_score >= threshold):
            clear = "advance" if advance_score >= threshold else "repair"
        else:
            clear = None
        if clear is not None:
            allowed = {clear}
            basis = method
        elif plan["debate"]["tie_policy"] == "judge":
            allowed = {"advance", "repair", "redeliberate"}
            basis = "tie-judge"
        elif plan["debate"]["tie_policy"] == "checkpoint":
            allowed = {"checkpoint"}
            basis = "tie-checkpoint"
        else:
            allowed = {"dissent"}
            basis = "tie-dissent"

    judge_veto = (
        plan["judge"]["role"] in decision["veto_roles"]
        and submitted_result == "repair"
    )
    if judge_veto:
        allowed.add("repair")
        basis = "judge-veto"
    if (
        plan["debate"]["dissent_policy"] == "veto"
        and submitted_result in {"advance", "repair"}
        and not vetoes
        and not judge_veto
    ):
        opposition = [item for item in non_abstain if item["vote"] != submitted_result]
        if opposition:
            allowed = {"dissent"}
            basis = "dissent-veto"
    _require(submitted_result in allowed, "judgment-invalid", f"judge result {submitted_result!r} is outside computed choices {sorted(allowed)}")
    result = submitted_result
    if result == "redeliberate" and round_number >= int(plan["debate"]["max_rounds"]):
        result = "exhausted"
    dissent = [
        {
            "role": item["role"], "slot": item["slot"],
            "principal_fingerprint": item["principal_fingerprint"],
            "vote": item["vote"], "receipt_hash": item["receipt_hash"],
        }
        for item in non_abstain
        if submitted_result in {"advance", "repair"} and item["vote"] != submitted_result
    ]
    aggregation = {
        "method": method,
        "threshold": threshold,
        "quorum_required": plan["council"]["quorum"],
        "quorum_observed": quorum,
        "distinct_non_abstaining_principals": sorted(quorum_principals),
        "advance_count": advance_count,
        "repair_count": repair_count,
        "abstention_count": len(unique_votes) - len(non_abstain),
        "advance_weight": advance_weight,
        "repair_weight": repair_weight,
        "vote_receipts": [item["receipt_hash"] for item in unique_votes],
        "excluded": excluded,
        "veto_receipts": [item["receipt_hash"] for item in vetoes],
        "basis": basis,
        "decision_authority": _decision_authority(plan, state, basis),
        "allowed_results": sorted(allowed),
        "dissent": dissent,
    }
    route = (
        {"kind": "internal", "target": f"round-{round_number + 1}"}
        if result == "redeliberate"
        else dict(plan["debate"]["routes"][result])
    )
    return result, aggregation, route


def _normalize_submission(
    plan: dict[str, object],
    claim: dict[str, object],
    submission: dict[str, object],
) -> dict[str, object]:
    mapping = _exact(submission, _SUBMISSION_KEYS, "submission")
    stage = str(claim["stage"])
    expected_kind = {
        "proposal": "proposal", "critique": "critique", "rebuttal": "rebuttal",
        "judgment": COUNCIL_VERDICT_KIND,
        "meta-audit": META_VERDICT_KIND,
        "architect-review": ARCHITECT_VERDICT_KIND,
    }[stage]
    _require(mapping.get("kind") == expected_kind, "artifact-kind-mismatch", f"{stage} requires {expected_kind!r}")
    content_hash = _hash(mapping.get("content_hash"), "submission.content_hash")
    content_ref = _safe_string(mapping.get("content_ref"), "submission.content_ref", reference=True)
    size = mapping.get("bytes")
    tokens = mapping.get("tokens")
    _require(isinstance(size, int) and not isinstance(size, bool) and 1 <= size <= int(plan["debate"]["artifact_max_bytes"]), "content-refused", "artifact bytes exceed the declared bound")
    _require(isinstance(tokens, int) and not isinstance(tokens, bool) and 1 <= tokens <= int(plan["debate"]["artifact_max_tokens"]), "content-refused", "artifact tokens exceed the declared bound")
    citations = mapping.get("citations")
    _require(
        isinstance(citations, list) and 0 < len(citations) <= 32
        and all(isinstance(item, str) and _REF_RE.fullmatch(item) for item in citations)
        and len(set(citations)) == len(citations),
        "citation-invalid", "submission citations must be a non-empty unique bounded reference list",
    )
    vote = mapping.get("vote")
    submitted_result = mapping.get("result")
    rationale = mapping.get("rationale")
    obligations: list[dict[str, object]] | None = None
    if stage == "rebuttal":
        _require(vote in VOTES, "vote-invalid", "rebuttal must carry advance, repair, or abstain vote")
    else:
        _require(vote is None, "unknown-content", "vote is legal only on a rebuttal")
    allowed_results: tuple[str, ...] = ()
    if stage == "judgment":
        allowed_results = JUDGMENT_RESULTS
    elif stage == "meta-audit":
        allowed_results = META_RESULTS
    elif stage == "architect-review":
        allowed_results = ARCHITECT_RESULTS
    if allowed_results:
        _require(submitted_result in allowed_results, "verdict-invalid", f"{stage} result is unsupported")
        _require(isinstance(rationale, str) and 0 < len(rationale.encode("utf-8")) <= min(int(size), 20_000), "rationale-invalid", "verdict rationale must be concise and bounded by artifact bytes")
    else:
        _require(submitted_result is None and rationale is None, "unknown-content", "result/rationale is legal only on a governed verdict")
    if stage == "judgment":
        _require("obligations" in mapping, "obligations-invalid", "council judgment omitted its obligations assertion")
        obligations = _obligations(mapping.get("obligations"))
    else:
        _require(mapping.get("obligations") is None, "unknown-content", "obligations are legal only on a council judgment")
    return {
        "artifact_kind": expected_kind,
        "content_hash": content_hash,
        "content_ref": content_ref,
        "bytes": size,
        "tokens": tokens,
        "citations": list(citations),
        "vote": vote,
        "submitted_result": submitted_result,
        "rationale": rationale,
        "obligations": obligations,
    }


def _artifact_detail(
    plan: dict[str, object],
    state: dict[str, Any],
    claim: dict[str, object],
    normalized: dict[str, object],
) -> dict[str, object]:
    result = None
    aggregation = None
    route = None
    stage = claim["stage"]
    if stage == "judgment":
        result, aggregation, route = _judgment_analysis(
            plan, state, int(claim["round"]), str(normalized["submitted_result"]),
        )
        _require(
            result != "advance"
            or not any(
                bool(item["blocking"])
                for item in normalized["obligations"]
            ),
            "blocking-obligation",
            "an advance decision cannot carry an open blocking obligation",
        )
    elif stage == "meta-audit":
        result = normalized["submitted_result"]
        underlying = _underlying_route(plan, state)
        _require(underlying is not None, "meta-invalid", "meta-audit has no underlying council verdict")
        if result == "uphold":
            route = underlying
        else:
            target = plan["council"]["audit"]["on_overturn" if result == "overturn" else "on_escalate"]
            route = {"kind": "action", "target": target}
        aggregation = {
            "audit_mode": claim["packet"]["audit_mode"],
            "audited_receipts": claim["packet"]["audited_receipts"],
            "verdict_lineage": claim["packet"]["verdict_lineage"],
            "original_verdict_preserved": True,
            "changes_implementation": False,
            "converts_judgment_to_fact": False,
        }
    elif stage == "architect-review":
        result = normalized["submitted_result"]
        underlying = (
            state["meta_verdict"]["route"]
            if state["meta_verdict"] is not None else _underlying_route(plan, state)
        )
        _require(underlying is not None, "architect-invalid", "architect review has no underlying governed route")
        target = plan["architect"]["routes"][result]
        route = dict(underlying) if target == "retain" else {"kind": "action", "target": target}
        aggregation = {
            "boundary": plan["architect"]["boundary"],
            "verdict_lineage": claim["packet"]["verdict_lineage"],
            "authority": plan["architect"]["authority"],
        }
    unsigned: dict[str, object] = {
        "claim_id": claim["claim_id"],
        "address": claim["address"],
        **normalized,
        "result": result,
        "aggregation": aggregation,
        "route": route,
    }
    return {**unsigned, "receipt_hash": _sha(unsigned)}


def _council_decision(
    plan: dict[str, object],
    state: dict[str, Any],
    events: list[dict[str, object]],
) -> dict[str, object] | None:
    judgment = _final_judgment(state)
    if judgment is None or judgment["result"] == "redeliberate":
        return None
    decision_event_index = next(
        (
            index for index, event in enumerate(events)
            if event["event"] == "artifact_recorded"
            and event["detail"]["receipt_hash"] == judgment["receipt_hash"]
        ),
        None,
    )
    _require(decision_event_index is not None, "ledger-corrupt", "council judgment has no ledger event")
    source_receipts = [
        str(event["detail"]["receipt_hash"])
        for event in events[: decision_event_index + 1]
        if event["event"] == "artifact_recorded"
        and event["detail"]["artifact_kind"] in {
            "proposal", "critique", "rebuttal", COUNCIL_VERDICT_KIND,
        }
    ]
    participant_map: dict[tuple[str, int, int], dict[str, object]] = {}
    for item in state["submissions"]:
        if item["receipt_hash"] not in source_receipts:
            continue
        key = (
            str(item["role"]), int(item["slot"]),
            int(item["assignment_generation"]),
        )
        participant_map[key] = {
            field: item[field]
            for field in (
                "role", "slot", "agent", "profile", "principal_fingerprint",
                "assignment_generation", "workspace_domain",
                "session_binding_key", "execution",
            )
        }
        participant_map[key]["address"] = item["seat_address"]
    participants = [
        participant_map[key] for key in sorted(participant_map)
    ]
    authority = judgment["aggregation"]["decision_authority"]
    alternatives = [
        item for item in judgment["aggregation"]["allowed_results"]
        if item != judgment["result"]
    ]
    obligations = list(judgment["obligations"])
    payload: dict[str, object] = {
        "kind": COUNCIL_DECISION_KIND,
        "schema_version": DELIBERATION_SCHEMA_VERSION,
        "decision_type": "council",
        "status": (
            "checkpoint-required"
            if judgment["result"] == "checkpoint" else "decided"
        ),
        "protocol_id": plan["protocol_id"],
        "plan_hash": plan["plan_hash"],
        "assignment_hash": plan["assignment_hash"],
        "program_run_id": plan["program_run_id"],
        "phase": plan["phase"],
        "story": plan["story"],
        "workflow_address": plan["workflow_address"],
        "council_id": plan["council_id"],
        "charter_hash": _sha({
            "council": plan["council"],
            "debate": plan["debate"],
            "rubric": plan["rubric"],
            "subject": plan["subject"],
        }),
        "subject": plan["subject"],
        "rubric": plan["rubric"],
        "round": judgment["round"],
        "authority": authority,
        "chair_seat": plan["judge"]["address"],
        "participants": participants,
        "source_receipt_hashes": source_receipts,
        "result": judgment["result"],
        "rationale": judgment["rationale"],
        "citations": judgment["citations"],
        "alternatives": alternatives,
        "accepted_risks": [
            item["id"] for item in obligations if item["kind"] == "risk"
        ],
        "dissent": judgment["aggregation"]["dissent"],
        "obligations": obligations,
        "route": judgment["route"],
        "issued_at": judgment["issued_at"],
        "protocol_ledger_head": events[decision_event_index]["event_hash"],
        "starts_work": False,
        "writes_state": False,
        "writes_repository": False,
        "writes_roadmap": False,
        "creates_grant": False,
    }
    payload_hash = _sha(payload)
    stamped = {**payload, "payload_hash": payload_hash}
    return validate_council_decision(
        {**stamped, "decision_hash": _sha(stamped)}
    )


def validate_council_decision(value: object) -> dict[str, object]:
    """Validate one immutable decision emitted by a completed council round."""
    decision = _exact(value, _DECISION_KEYS, "decision")
    _require(set(decision) == _DECISION_KEYS, "decision-invalid", "decision must use exact keys")
    _require(decision.get("kind") == COUNCIL_DECISION_KIND, "decision-invalid", "decision kind is invalid")
    _require(decision.get("schema_version") == DELIBERATION_SCHEMA_VERSION, "decision-invalid", "decision schema is invalid")
    _require(decision.get("decision_type") == "council", "decision-invalid", "decision type is invalid")
    _require(decision.get("status") in {"decided", "checkpoint-required"}, "decision-invalid", "decision status is invalid")
    for field in (
        "protocol_id", "program_run_id", "workflow_address", "council_id",
    ):
        _safe_string(decision.get(field), f"decision.{field}", reference=True)
    for field in (
        "plan_hash", "assignment_hash", "charter_hash",
        "protocol_ledger_head", "payload_hash", "decision_hash",
    ):
        _hash(decision.get(field), f"decision.{field}")
    phase = decision.get("phase")
    round_number = decision.get("round")
    _require(isinstance(phase, int) and not isinstance(phase, bool) and phase > 0, "decision-invalid", "decision phase must be positive")
    _require(isinstance(round_number, int) and not isinstance(round_number, bool) and round_number > 0, "decision-invalid", "decision round must be positive")
    _safe_string(decision.get("story"), "decision.story")
    _subject(decision.get("subject"))
    _rubric(decision.get("rubric"), "decision.rubric")
    _safe_string(decision.get("chair_seat"), "decision.chair_seat", reference=True)

    authority = _exact(decision.get("authority"), _DECISION_AUTHORITY_KEYS, "decision.authority")
    _require(set(authority) == _DECISION_AUTHORITY_KEYS, "decision-invalid", "decision authority must use exact keys")
    authority_kind = authority.get("kind")
    _require(authority_kind in {"rule", "judge", "checkpoint"}, "decision-invalid", "decision authority kind is invalid")
    _safe_string(authority.get("basis"), "decision.authority.basis")
    _require(authority.get("assignment_hash") == decision.get("assignment_hash"), "decision-invalid", "decision authority assignment is stale")
    rule = authority.get("rule")
    if rule is not None:
        _safe_string(rule, "decision.authority.rule")
    checkpoint = authority.get("checkpoint_port")
    if checkpoint is not None:
        _safe_string(checkpoint, "decision.authority.checkpoint_port")

    raw_participants = decision.get("participants")
    _require(isinstance(raw_participants, list) and 0 < len(raw_participants) <= 128, "decision-invalid", "decision participants must be non-empty and bounded")
    participants: list[dict[str, object]] = []
    participant_keys: set[tuple[str, int, int]] = set()
    for index, raw in enumerate(raw_participants):
        label = f"decision.participants[{index}]"
        participant = _exact(raw, _PARTICIPANT_KEYS, label)
        _require(set(participant) == _PARTICIPANT_KEYS, "decision-invalid", f"{label} must use exact keys")
        normalized = {
            "address": _safe_string(participant.get("address"), f"{label}.address", reference=True),
            "role": _safe_string(participant.get("role"), f"{label}.role"),
            "slot": participant.get("slot"),
            "agent": _safe_string(participant.get("agent"), f"{label}.agent"),
            "profile": _safe_string(participant.get("profile"), f"{label}.profile"),
            "principal_fingerprint": _hash(participant.get("principal_fingerprint"), f"{label}.principal_fingerprint"),
            "assignment_generation": participant.get("assignment_generation"),
            "workspace_domain": _safe_string(participant.get("workspace_domain"), f"{label}.workspace_domain"),
            "session_binding_key": _hash(participant.get("session_binding_key"), f"{label}.session_binding_key"),
            "execution": _execution(participant.get("execution"), f"{label}.execution"),
        }
        _require(isinstance(normalized["slot"], int) and not isinstance(normalized["slot"], bool) and int(normalized["slot"]) > 0, "decision-invalid", f"{label}.slot must be positive")
        _require(isinstance(normalized["assignment_generation"], int) and not isinstance(normalized["assignment_generation"], bool) and int(normalized["assignment_generation"]) > 0, "decision-invalid", f"{label}.assignment_generation must be positive")
        key = (str(normalized["role"]), int(normalized["slot"]), int(normalized["assignment_generation"]))
        _require(key not in participant_keys, "decision-invalid", "decision repeats a participant generation")
        participant_keys.add(key)
        participants.append(normalized)

    decider = authority.get("decider")
    decider_seat = authority.get("decider_seat")
    if authority_kind == "judge":
        _safe_string(decider_seat, "decision.authority.decider_seat", reference=True)
        raw_decider = _exact(decider, _DECIDER_KEYS, "decision.authority.decider")
        _require(set(raw_decider) == _DECIDER_KEYS, "decision-invalid", "decision decider must use exact keys")
        _require(raw_decider.get("address") == decider_seat, "decision-invalid", "decider seat and decider address differ")
        normalized_decider = {
            "address": _safe_string(raw_decider.get("address"), "decision.authority.decider.address", reference=True),
            "role": _safe_string(raw_decider.get("role"), "decision.authority.decider.role"),
            "duty": _safe_string(raw_decider.get("duty"), "decision.authority.decider.duty"),
            "slot": raw_decider.get("slot"),
            "agent": _safe_string(raw_decider.get("agent"), "decision.authority.decider.agent"),
            "profile": _safe_string(raw_decider.get("profile"), "decision.authority.decider.profile"),
            "principal_fingerprint": _hash(raw_decider.get("principal_fingerprint"), "decision.authority.decider.principal_fingerprint"),
            "assignment_generation": raw_decider.get("assignment_generation"),
            "session_binding_key": _hash(raw_decider.get("session_binding_key"), "decision.authority.decider.session_binding_key"),
            "workspace_domain": _safe_string(raw_decider.get("workspace_domain"), "decision.authority.decider.workspace_domain"),
            "execution": _execution(raw_decider.get("execution"), "decision.authority.decider.execution"),
        }
        _require(isinstance(normalized_decider["slot"], int) and int(normalized_decider["slot"]) > 0, "decision-invalid", "decider slot must be positive")
        _require(isinstance(normalized_decider["assignment_generation"], int) and int(normalized_decider["assignment_generation"]) > 0, "decision-invalid", "decider generation must be positive")
        matching = [
            item for item in participants
            if all(item[field] == normalized_decider[field] for field in _PARTICIPANT_KEYS)
        ]
        _require(len(matching) == 1, "decision-invalid", "decider is not the exact preassigned council participant")
        _require(rule is None and checkpoint is None, "decision-invalid", "judge authority cannot also be a rule or checkpoint")
    elif authority_kind == "checkpoint":
        _require(decider is None and decider_seat is None and rule is None and checkpoint is not None, "decision-invalid", "checkpoint authority has an agent decider")
    else:
        _require(decider is None and decider_seat is None and rule is not None and checkpoint is None, "decision-invalid", "rule authority has an agent decider")

    receipts = decision.get("source_receipt_hashes")
    _require(isinstance(receipts, list) and receipts and len(receipts) <= 1_000 and len(set(receipts)) == len(receipts), "decision-invalid", "decision source receipts must be non-empty and unique")
    for index, receipt in enumerate(receipts):
        _hash(receipt, f"decision.source_receipt_hashes[{index}]")
    result = decision.get("result")
    _require(result in set(JUDGMENT_RESULTS) | {"exhausted"}, "decision-invalid", "decision result is unsupported")
    _bounded_text(decision.get("rationale"), "decision.rationale", 20_000)
    citations = decision.get("citations")
    _require(isinstance(citations, list) and citations and len(citations) <= 32 and len(set(citations)) == len(citations), "decision-invalid", "decision citations must be non-empty and unique")
    for index, citation in enumerate(citations):
        _safe_string(citation, f"decision.citations[{index}]", reference=True)
    alternatives = decision.get("alternatives")
    _require(isinstance(alternatives, list) and len(alternatives) <= len(JUDGMENT_RESULTS) and len(set(alternatives)) == len(alternatives), "decision-invalid", "decision alternatives are invalid")
    _require(all(item in set(JUDGMENT_RESULTS) | {"exhausted"} and item != result for item in alternatives), "decision-invalid", "decision alternatives contain an invalid result")
    obligations = _obligations(decision.get("obligations"))
    risk_ids = {item["id"] for item in obligations if item["kind"] == "risk"}
    accepted_risks = decision.get("accepted_risks")
    _require(isinstance(accepted_risks, list) and len(set(accepted_risks)) == len(accepted_risks) and set(accepted_risks) == risk_ids, "decision-invalid", "accepted risks differ from risk obligations")
    if result == "advance":
        _require(not any(bool(item["blocking"]) for item in obligations), "blocking-obligation", "advance decision carries a blocking obligation")
    dissent = decision.get("dissent")
    _require(isinstance(dissent, list) and len(dissent) <= 128, "decision-invalid", "decision dissent must be bounded")
    for index, raw in enumerate(dissent):
        item = _exact(raw, _DECISION_DISSENT_KEYS, f"decision.dissent[{index}]")
        _require(set(item) == _DECISION_DISSENT_KEYS, "decision-invalid", "decision dissent must use exact keys")
        _safe_string(item.get("role"), f"decision.dissent[{index}].role")
        _require(isinstance(item.get("slot"), int) and int(item["slot"]) > 0, "decision-invalid", "dissent slot must be positive")
        _hash(item.get("principal_fingerprint"), f"decision.dissent[{index}].principal_fingerprint")
        _require(item.get("vote") in VOTES, "decision-invalid", "dissent vote is invalid")
        _hash(item.get("receipt_hash"), f"decision.dissent[{index}].receipt_hash")
    _route(decision.get("route"), "decision.route")
    _timestamp(decision.get("issued_at"), "decision.issued_at")
    _require(
        decision.get("status") == ("checkpoint-required" if result == "checkpoint" else "decided"),
        "decision-invalid", "decision status and result differ",
    )
    for field in (
        "starts_work", "writes_state", "writes_repository",
        "writes_roadmap", "creates_grant",
    ):
        _require(decision.get(field) is False, "decision-invalid", f"decision cannot set {field}")
    payload = {
        key: item for key, item in decision.items()
        if key not in {"payload_hash", "decision_hash"}
    }
    _require(_sha(payload) == decision["payload_hash"], "decision-invalid", "decision payload hash does not match")
    stamped = {**payload, "payload_hash": decision["payload_hash"]}
    _require(_sha(stamped) == decision["decision_hash"], "decision-invalid", "decision hash does not match")
    return dict(decision)


def _projection(plan: dict[str, object], state: dict[str, Any], events: list[dict[str, object]]) -> dict[str, object]:
    judgment = _final_judgment(state)
    decision = _council_decision(plan, state, events)
    next_spec = None if state["active"] is not None else _next_spec(plan, state)
    final_route = None
    final_result = None
    if state["budget_exhaustion"] is not None:
        final_route = state["budget_exhaustion"]["route"]
        final_result = "exhausted"
    elif state["architect_verdict"] is not None:
        final_route = state["architect_verdict"]["route"]
        final_result = state["architect_verdict"]["result"]
    elif state["meta_verdict"] is not None and state["meta_verdict"]["result"] != "uphold":
        final_route = state["meta_verdict"]["route"]
        final_result = state["meta_verdict"]["result"]
    elif judgment is not None and judgment["result"] != "redeliberate" and next_spec is None:
        final_route = (
            state["meta_verdict"]["route"]
            if state["meta_verdict"] is not None else judgment["route"]
        )
        final_result = judgment["result"]
    complete = final_route is not None
    return {
        "kind": DELIBERATION_PROJECTION_KIND,
        "schema_version": DELIBERATION_SCHEMA_VERSION,
        "protocol_id": plan["protocol_id"],
        "plan_hash": plan["plan_hash"],
        "state": "complete" if complete else ("waiting-receipt" if state["active"] else "ready"),
        "round": (judgment["round"] if judgment else 1),
        "active_claim": dict(state["active"]) if state["active"] else None,
        "next": next_spec,
        "budget": dict(state["budget"]),
        "limits": plan["limits"],
        "rounds": [
            {
                "round": number,
                "artifacts": [
                    item for item in state["submissions"] if item["round"] == number
                ],
                "judgment": next((item for item in state["judgments"] if item["round"] == number), None),
            }
            for number in sorted({item["round"] for item in state["submissions"]})
        ],
        "round_judgments": list(state["judgments"]),
        "council_decision": decision,
        "carried_obligations": (
            [
                {**item, "source_decision_hash": decision["decision_hash"]}
                for item in decision["obligations"]
            ]
            if decision is not None else []
        ),
        "meta_verdict": state["meta_verdict"],
        "architect_verdict": state["architect_verdict"],
        "dissent": list(state["dissent"]),
        "abstentions": [
            item for item in state["submissions"] if item.get("vote") == "abstain"
        ],
        "replacements": list(state["replacements"]),
        "completed_claims": list(state["completed_claims"]),
        "budget_exhaustion": state["budget_exhaustion"],
        "final_result": final_result,
        "route": final_route,
        "ledger_events": len(events),
        "ledger_head": events[-1]["event_hash"],
        "durable_content": {
            "artifact_bodies": False,
            "prompt_bodies": False,
            "transport_transcripts": False,
            "private_reasoning": False,
            "declared_metadata_and_rationales_only": True,
        },
        "dispatches_agents": False,
        "writes_repository": False,
        "writes_roadmap": False,
    }


def replay_deliberation(
    plan: dict[str, object],
    events: list[dict[str, object]],
) -> dict[str, object]:
    """Validate and replay the authoritative hash chain into a projection."""
    _validate_plan(plan)
    _require(isinstance(events, list) and events, "ledger-corrupt", "deliberation ledger is empty")
    state: dict[str, Any] | None = None
    previous = "sha256:" + "0" * 64
    previous_time: datetime | None = None
    for offset, event in enumerate(events):
        _require(isinstance(event, dict) and set(event) == _EVENT_KEYS, "ledger-corrupt", f"event {offset + 1} has non-exact keys")
        _require(event.get("kind") == DELIBERATION_EVENT_KIND and event.get("schema_version") == DELIBERATION_SCHEMA_VERSION, "ledger-corrupt", f"event {offset + 1} has wrong kind/schema")
        _require(event.get("protocol_id") == plan["protocol_id"] and event.get("seq") == offset + 1 and event.get("prev_hash") == previous, "ledger-corrupt", f"event {offset + 1} breaks identity/sequence/hash chain")
        unsigned = {key: value for key, value in event.items() if key != "event_hash"}
        _require(event.get("event_hash") == _sha(unsigned), "ledger-corrupt", f"event {offset + 1} hash check failed")
        kind = event.get("event")
        _require(kind in _EVENT_DETAIL_KEYS, "ledger-corrupt", f"event {offset + 1} has unsupported family")
        detail = event.get("detail")
        _require(isinstance(detail, dict) and set(detail) == _EVENT_DETAIL_KEYS[str(kind)], "ledger-corrupt", f"event {offset + 1} has non-exact detail")
        current_time = _timestamp(event.get("ts"), f"event {offset + 1} timestamp")
        _require(previous_time is None or current_time >= previous_time, "ledger-corrupt", "event time moves backwards")
        previous_time = current_time
        previous = str(event["event_hash"])

        if offset == 0:
            _require(kind == "protocol_started", "ledger-corrupt", "ledger must begin with protocol_started")
            expected = {
                "plan_hash": plan["plan_hash"], "program_run_id": plan["program_run_id"],
                "workflow_address": plan["workflow_address"], "council_id": plan["council_id"],
                "maximum": plan["maximum"],
            }
            _require(detail == expected, "ledger-corrupt", "start event does not bind the plan")
            state = _initial_state(plan, str(event["ts"]))
            continue
        _require(state is not None, "ledger-corrupt", "ledger state was not initialized")
        _require(state["budget_exhaustion"] is None, "ledger-corrupt", "event follows terminal budget exhaustion")
        if kind == "speaker_claimed":
            _require(state["active"] is None, "ledger-corrupt", "claim overlaps an active speaker")
            spec = _next_spec(plan, state)
            _require(spec is not None, "ledger-corrupt", "claim exists after protocol completion")
            expected = _claim_detail(plan, state, spec)
            _require(detail == expected, "ledger-corrupt", "claim differs from deterministic next speaker")
            _require(not any(item["claim_id"] == detail["claim_id"] for item in state["claims"]), "ledger-corrupt", "duplicate claim id")
            state["active"] = dict(detail)
            state["claims"].append(dict(detail))
            state["budget"]["agent_starts"] += 1
        elif kind == "artifact_recorded":
            claim = state["active"]
            _require(claim is not None and claim["claim_id"] == detail["claim_id"] and claim["address"] == detail["address"], "ledger-corrupt", "artifact does not close the active claim")
            receipt_unsigned = {key: value for key, value in detail.items() if key != "receipt_hash"}
            _require(detail["receipt_hash"] == _sha(receipt_unsigned), "ledger-corrupt", "artifact receipt hash is invalid")
            normalized = {
                key: detail[key] for key in (
                    "artifact_kind", "content_hash", "content_ref", "bytes", "tokens",
                    "citations", "vote", "submitted_result", "rationale",
                    "obligations",
                )
            }
            expected = _artifact_detail(plan, state, claim, normalized)
            _require(detail == expected, "ledger-corrupt", "artifact receipt violates protocol semantics")
            member = state["members"][f"{claim['role']}[{claim['slot']}]" ]
            stored = {
                **dict(detail),
                "round": claim["round"], "stage": claim["stage"],
                "role": claim["role"], "slot": claim["slot"],
                "seat_address": claim["seat_address"],
                "agent": claim["agent"], "profile": claim["profile"],
                "principal_fingerprint": claim["principal_fingerprint"],
                "assignment_generation": member["assignment_generation"],
                "workspace_domain": claim["workspace_domain"],
                "session_binding_key": claim["session_binding_key"],
                "execution": claim["execution"],
                "issued_at": event["ts"],
            }
            state["submissions"].append(stored)
            state["completed_addresses"].add(claim["address"])
            state["completed_claims"].append({
                "claim_id": claim["claim_id"], "address": claim["address"],
                "receipt_hash": detail["receipt_hash"], "invalidated": False,
            })
            state["active"] = None
            state["budget"]["artifacts"] += 1
            state["budget"]["output_bytes"] += int(detail["bytes"])
            state["budget"]["tokens"] += int(detail["tokens"])
            if claim["stage"] == "judgment":
                judgment = dict(stored)
                state["judgments"].append(judgment)
                state["dissent"].extend(judgment["aggregation"]["dissent"])
            elif claim["stage"] == "meta-audit":
                state["meta_verdict"] = dict(stored)
            elif claim["stage"] == "architect-review":
                state["architect_verdict"] = dict(stored)
        elif kind == "member_replaced":
            _require(
                state["active"] is not None or _next_spec(plan, state) is not None,
                "ledger-corrupt", "replacement exists after protocol completion",
            )
            binding = str(detail["binding_key"])
            current = state["members"].get(binding)
            _require(current is not None and detail["old"] == current, "ledger-corrupt", "replacement old binding is stale")
            new = detail["new"]
            _require(isinstance(new, dict) and new.get("binding_key") == binding and int(new.get("assignment_generation", 0)) > int(current["assignment_generation"]), "ledger-corrupt", "replacement generation/binding is invalid")
            _require(detail["dissent_before"] == [item["receipt_hash"] for item in state["dissent"]], "ledger-corrupt", "replacement does not preserve prior dissent")
            active = state["active"]
            invalidated = active["claim_id"] if active and f"{active['role']}[{active['slot']}]" == binding else None
            _require(detail["invalidated_claim_id"] == invalidated, "ledger-corrupt", "replacement invalidation receipt is incorrect")
            if invalidated:
                state["active"] = None
            state["members"][binding] = dict(new)
            state["replacements"].append(dict(detail))
        elif kind == "budget_exhausted":
            _require(detail["route"] == plan["debate"]["routes"]["exhausted"], "ledger-corrupt", "budget exhaustion uses an undeclared route")
            state["budget_exhaustion"] = dict(detail)
            state["active"] = None
    assert state is not None
    return _projection(plan, state, events)


def _append(
    plan: dict[str, object],
    events: list[dict[str, object]],
    kind: str,
    detail: dict[str, object],
    now: str,
) -> tuple[list[dict[str, object]], dict[str, object]]:
    appended = list(events) + [_event(plan, events, kind, detail, now)]
    projection = replay_deliberation(plan, appended)
    return appended, projection


def _elapsed(plan: dict[str, object], events: list[dict[str, object]], now: str) -> int:
    start = _timestamp(events[0]["ts"], "protocol start")
    current = _timestamp(now)
    return max(0, int((current - start).total_seconds()))


def _exhaust(
    plan: dict[str, object],
    events: list[dict[str, object]],
    projection: dict[str, object],
    *,
    counter: str,
    consumed: int,
    requested: int,
    limit: int,
    now: str,
) -> dict[str, object]:
    detail = {
        "counter": counter,
        "limit": limit,
        "consumed": consumed,
        "requested": requested,
        "active_claim_id": (
            projection["active_claim"]["claim_id"] if projection["active_claim"] else None
        ),
        "route": plan["debate"]["routes"]["exhausted"],
    }
    updated, replayed = _append(plan, events, "budget_exhausted", detail, now)
    return {"events": updated, "projection": replayed, "claim": None, "receipt": None, "appended": True}


def claim_next_deliberation(
    plan: dict[str, object],
    events: list[dict[str, object]],
    now: str,
) -> dict[str, object]:
    """Claim the deterministic next slot, or return the same unresolved claim."""
    projection = replay_deliberation(plan, events)
    if projection["active_claim"] is not None:
        return {"events": events, "projection": projection, "claim": projection["active_claim"], "appended": False}
    if projection["state"] == "complete":
        return {"events": events, "projection": projection, "claim": None, "appended": False}
    elapsed = _elapsed(plan, events, now)
    wall_limit = int(plan["limits"]["max_wall_seconds"])
    if elapsed > wall_limit:
        return _exhaust(plan, events, projection, counter="wall_seconds", consumed=elapsed, requested=0, limit=wall_limit, now=now)
    start_limit = int(plan["limits"]["max_speaker_starts"])
    consumed = int(projection["budget"]["agent_starts"])
    if consumed + 1 > start_limit:
        return _exhaust(plan, events, projection, counter="agent_starts", consumed=consumed, requested=1, limit=start_limit, now=now)
    # Replay already derives the deterministic next spec; rebuilding internal
    # state is intentionally centralized in the validated event walk.
    state = _state_from_events(plan, events)
    spec = _next_spec(plan, state)
    _require(spec is not None, "protocol-complete", "no deliberation claim remains")
    detail = _claim_detail(plan, state, spec)
    updated, replayed = _append(plan, events, "speaker_claimed", detail, now)
    return {"events": updated, "projection": replayed, "claim": detail, "appended": True}


def _state_from_events(plan: dict[str, object], events: list[dict[str, object]]) -> dict[str, Any]:
    """Replay into internal state after validating via the public projection."""
    replay_deliberation(plan, events)
    # The semantic walk is repeated without accepting any external fields.  It
    # keeps public projections compact while transition helpers share one model.
    state = _initial_state(plan, str(events[0]["ts"]))
    for event in events[1:]:
        kind = event["event"]
        detail = event["detail"]
        if kind == "speaker_claimed":
            state["active"] = dict(detail)
            state["claims"].append(dict(detail))
            state["budget"]["agent_starts"] += 1
        elif kind == "artifact_recorded":
            claim = state["active"]
            assert claim is not None
            member = state["members"][f"{claim['role']}[{claim['slot']}]" ]
            stored = {
                **dict(detail), "round": claim["round"], "stage": claim["stage"],
                "role": claim["role"], "slot": claim["slot"],
                "principal_fingerprint": claim["principal_fingerprint"],
                "assignment_generation": member["assignment_generation"],
            }
            state["submissions"].append(stored)
            state["completed_addresses"].add(claim["address"])
            state["completed_claims"].append({
                "claim_id": claim["claim_id"], "address": claim["address"],
                "receipt_hash": detail["receipt_hash"], "invalidated": False,
            })
            state["active"] = None
            state["budget"]["artifacts"] += 1
            state["budget"]["output_bytes"] += int(detail["bytes"])
            state["budget"]["tokens"] += int(detail["tokens"])
            if claim["stage"] == "judgment":
                state["judgments"].append(stored)
                state["dissent"].extend(stored["aggregation"]["dissent"])
            elif claim["stage"] == "meta-audit":
                state["meta_verdict"] = stored
            elif claim["stage"] == "architect-review":
                state["architect_verdict"] = stored
        elif kind == "member_replaced":
            if detail["invalidated_claim_id"]:
                state["active"] = None
            state["members"][detail["binding_key"]] = dict(detail["new"])
            state["replacements"].append(dict(detail))
        elif kind == "budget_exhausted":
            state["budget_exhaustion"] = dict(detail)
            state["active"] = None
    return state


def record_deliberation_submission(
    plan: dict[str, object],
    events: list[dict[str, object]],
    claim_id: str,
    submission: dict[str, object],
    now: str,
) -> dict[str, object]:
    """Record one typed bounded artifact, idempotently for an exact retry."""
    projection = replay_deliberation(plan, events)
    active = projection["active_claim"]
    if active is None:
        state = _state_from_events(plan, events)
        prior = next((item for item in state["submissions"] if item["claim_id"] == claim_id), None)
        _require(prior is not None, "claim-missing", "submission has no active or completed claim")
        claim = next(item for item in state["claims"] if item["claim_id"] == claim_id)
        normalized = _normalize_submission(plan, claim, submission)
        for key, value in normalized.items():
            _require(prior[key] == value, "idempotency-conflict", "completed claim received different content")
        return {"events": events, "projection": projection, "receipt": prior, "appended": False}
    _require(active["claim_id"] == claim_id, "claim-conflict", "submission does not match the active deterministic claim")
    normalized = _normalize_submission(plan, active, submission)
    elapsed = _elapsed(plan, events, now)
    wall_limit = int(plan["limits"]["max_wall_seconds"])
    if elapsed > wall_limit:
        return _exhaust(plan, events, projection, counter="wall_seconds", consumed=elapsed, requested=0, limit=wall_limit, now=now)
    checks = (
        ("artifacts", "max_artifacts", 1),
        ("output_bytes", "max_output_bytes", int(normalized["bytes"])),
        ("tokens", "max_tokens", int(normalized["tokens"])),
    )
    for counter, limit_name, requested in checks:
        consumed = int(projection["budget"][counter])
        limit = int(plan["limits"][limit_name])
        if consumed + requested > limit:
            return _exhaust(plan, events, projection, counter=counter, consumed=consumed, requested=requested, limit=limit, now=now)
    state = _state_from_events(plan, events)
    detail = _artifact_detail(plan, state, active, normalized)
    updated, replayed = _append(plan, events, "artifact_recorded", detail, now)
    receipt = next(item for item in replayed["completed_claims"] if item["claim_id"] == claim_id)
    return {"events": updated, "projection": replayed, "receipt": receipt, "appended": True}


def record_deliberation_replacement(
    plan: dict[str, object],
    events: list[dict[str, object]],
    replacement: dict[str, object],
    now: str,
) -> dict[str, object]:
    """Append one finite WLA-26-04 replacement without hiding prior dissent."""
    _require(replacement.get("kind") == "delivery-workbench-assignment-replacement" and bool(replacement.get("applicable")), "replacement-invalid", "an applicable assignment replacement plan is required")
    _require(bool(replacement.get("preserves_history")) and bool(replacement.get("capability_unchanged")), "replacement-invalid", "replacement must preserve history and capability ceiling")
    state = _state_from_events(plan, events)
    _require(
        state["active"] is not None or _next_spec(plan, state) is not None,
        "protocol-complete", "cannot replace a member after deliberation completes",
    )
    role_id = str(replacement.get("role"))
    slot = int(replacement.get("slot", 0))
    binding_key = f"{role_id}[{slot}]"
    old = state["members"].get(binding_key)
    _require(old is not None, "replacement-invalid", "replacement role slot is outside this protocol")
    old_source = replacement.get("old")
    new_source = replacement.get("new")
    _require(isinstance(old_source, dict) and isinstance(new_source, dict), "replacement-invalid", "replacement bindings are incomplete")
    _require(old_source.get("principal_fingerprint") == old["principal_fingerprint"] and old_source.get("assignment_generation") == old["assignment_generation"], "replacement-invalid", "replacement old binding is stale")
    role = {item["role"]: item for item in plan["speakers"] + [plan["judge"]]}.get(role_id)
    if role is None and plan.get("meta_verifier") and plan["meta_verifier"]["role"] == role_id:
        role = plan["meta_verifier"]
    if role is None and plan.get("architect_member") and plan["architect_member"]["role"] == role_id:
        role = plan["architect_member"]
    _require(role is not None, "replacement-invalid", "replacement role is not governed by this protocol")
    new = {
        **old,
        "agent": new_source["agent"],
        "profile": new_source["profile"],
        "execution": _execution(new_source.get("execution"), "replacement execution"),
        "principal_fingerprint": _hash(new_source.get("principal_fingerprint"), "replacement principal"),
        "assignment_generation": new_source["assignment_generation"],
        "session_binding_key": _hash(new_source.get("session_binding_key"), "replacement session binding"),
        "workspace_domain": new_source["workspace_domain"],
    }
    other_principals = {
        member["principal_fingerprint"] for key, member in state["members"].items()
        if key != binding_key
    }
    _require(new["principal_fingerprint"] not in other_principals, "duplicate-principal", "replacement would duplicate a council/auditor principal")
    active = state["active"]
    invalidated = active["claim_id"] if active and f"{active['role']}[{active['slot']}]" == binding_key else None
    detail = {
        "binding_key": binding_key,
        "role": role_id,
        "slot": slot,
        "reason": replacement["reason"],
        "old": old,
        "new": new,
        "preserved_lineage": replacement["preserved_lineage"],
        "invalidated_claim_id": invalidated,
        "dissent_before": [item["receipt_hash"] for item in state["dissent"]],
    }
    updated, replayed = _append(plan, events, "member_replaced", detail, now)
    return {"events": updated, "projection": replayed, "replacement": detail, "appended": True}
