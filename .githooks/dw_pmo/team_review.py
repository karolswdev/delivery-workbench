"""Readable team and review projections over exact organization facts.

The organization compiler and assignment engine remain authoritative for
roles, candidates, separation, councils, provenance, and refusal.  This module
only groups those facts around the questions a person asks before delivery:
who does the work, who reviews it independently, who decides contested
matters, who receives help or escalation, and who checks the reviewers.

The same stamped view is used for organization authoring and live assigned
teams.  A tracked policy can prove that distinct candidates exist; only a
runtime assignment can prove distinct principals, work areas, and session
bindings.  The projection never collapses those two claims.
"""

from __future__ import annotations

import re
from typing import Any, Optional

from .presentation import DIFFERENT_MODEL_FAMILY_COPY
from .test_baseline import build_failure_projection


TEAM_REVIEW_KIND = "delivery-workbench-team-review"
TEAM_REVIEW_SCHEMA_VERSION = 1

SECTION_ORDER = (
    "responsibilities",
    "independence",
    "decisions",
    "escalation",
    "audit",
)

SECTION_META = {
    "responsibilities": (
        "Work responsibilities",
        "Who does each kind of work?",
        "Name the primary responsibility, required coverage, and available backup.",
    ),
    "independence": (
        "Independent review",
        "Who reviews the work independently?",
        "Keep doing and reviewing separate in both policy and the later assignment.",
    ),
    "decisions": (
        "Contested decisions",
        "Who decides when reviewers disagree?",
        "Explain required agreement, objections, and the final decision owner.",
    ),
    "escalation": (
        "Help and escalation",
        "Who receives a request for help or an escalation?",
        "Show internal help, finite replacement, and the separate delivery-owner handoff.",
    ),
    "audit": (
        "Review of review",
        "Who checks reviewers and phase-level design?",
        "Disclose review auditing and architecture checks only when the delivery uses them.",
    ),
}

DUTY_LABELS = {
    "implementer": "Implementation",
    "verifier": "Independent review",
    "meta-verifier": "Review audit",
    "master-architect": "Architecture review",
    "researcher": "Research",
    "reviewer": "Review",
    "repairer": "Repair",
    "critic": "Critical perspective",
    "judge": "Contested decision",
}

DUTY_RESPONSIBILITIES = {
    "implementer": "Prepares the bounded change.",
    "verifier": "Reviews the completed change without altering it.",
    "meta-verifier": "Checks whether a review was conducted and supported correctly.",
    "master-architect": "Checks story or phase design at a separately declared boundary.",
    "researcher": "Collects bounded supporting information.",
    "reviewer": "Reviews the declared subject against saved criteria.",
    "repairer": "Repairs work after a review asks for change.",
    "critic": "Contributes an independent critical perspective to a governed discussion.",
    "judge": "Records the governed outcome for a contested decision.",
}

DUTY_WHEN = {
    "implementer": "When selected work is ready to be changed.",
    "verifier": "After the declared work and mechanical checks are ready for review.",
    "meta-verifier": "Only when a review group enables a separate audit.",
    "master-architect": "Only when a delivery plan declares a story or phase architecture check.",
    "researcher": "Only when another responsibility requests research.",
    "reviewer": "When a work flow requests the saved review.",
    "repairer": "Only after a failed review routes work to repair.",
    "critic": "Only during a declared governed discussion.",
    "judge": "Only after the declared participants and evidence are ready for a decision.",
}

DUTY_OUTCOMES = {
    "implementer": "Produces candidate work; it cannot mark its own work reviewed.",
    "verifier": "May pass the review or request repair through the declared work flow.",
    "meta-verifier": "May uphold the review or follow the saved overturn or escalation route.",
    "master-architect": "May allow progress or follow the delivery plan's repair, decision, or stop route.",
    "researcher": "Adds supporting material; it does not decide the outcome.",
    "reviewer": "Produces a review result that the calling work flow routes.",
    "repairer": "Produces repaired candidate work that must be reviewed again.",
    "critic": "Adds a preserved perspective; it does not decide by itself.",
    "judge": "Chooses only among outcomes allowed by the saved decision rule.",
}

EXHAUSTION_LABELS = {
    "block": "Keep the work blocked",
    "escalate": "Ask the separately authorized delivery owner",
    "checkpoint": "Wait for a named person to decide",
    "abort": "End this delivery",
}

DECISION_METHODS = {
    "majority": "More than half of the voting reviewers must agree.",
    "weighted": "Declared reviewer weights must reach the saved threshold.",
    "unanimous": "Every voting reviewer must agree.",
    "judge": "The named decision owner chooses from the allowed outcomes.",
}

TECHNICAL_REPLACEMENTS = (
    (r"\borganization\b", "team design"),
    (r"\bagents?\b", "team members"),
    (r"\bpools?\b", "candidate groups"),
    (r"\broles?\b", "responsibilities"),
    (r"\bprincipal\b", "execution identity"),
    (r"\bworkspace(?:_domain)?\b", "work area"),
    (r"\bsession(?:_binding)?\b", "work session"),
    (r"\bquorum\b", "required reviewer agreement"),
    (r"\bmeta[-_ ]verifier\b", "review auditor"),
    (r"\bmaster[-_ ]architect\b", "architecture reviewer"),
    (r"\bcapabilit(?:y|ies)\b", "allowed action"),
    (r"\bverdict\b", "review outcome"),
    (r"\bcompiler\b", "policy checker"),
)

INDEPENDENCE_CODES = {
    "missing-separation",
    "impossible-independence",
    "separation-violation",
    "provider-diversity-unsatisfied",
    "duplicate-principal",
    "role-order",
    "judgment-not-authorized",
    "capability-smuggling",
    "missing-verdict-schema",
}

DECISION_CODES = {
    "impossible-quorum",
    "invalid-threshold",
    "missing-route",
    "council-invalid",
}

AUDIT_CODES = {
    "missing-meta-verifier",
    "dissent-erasure",
}

ESCALATION_CODES = {
    "replacement-unrouted",
    "dangling-pool-reference",
    "unsupported-route",
}


def _copy(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _copy(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_copy(item) for item in value]
    return value


def _objects(value: object) -> list[dict[str, object]]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, dict)]


def _strings(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value if isinstance(item, str)]


def _assignment_diversity(value: object) -> dict[str, object]:
    if not isinstance(value, dict):
        return {}
    direct = value.get("diversity")
    if isinstance(direct, dict):
        return direct
    separation = value.get("separation")
    if not isinstance(separation, dict):
        return {}
    nested = separation.get("diversity")
    return nested if isinstance(nested, dict) else {}


def _display(value: object) -> str:
    text = str(value or "").strip()
    if not text:
        return "Not chosen"
    return " ".join(part.capitalize() for part in re.split(r"[-_ ]+", text) if part)


def _plain(value: object) -> str:
    text = str(value or "").strip()
    for pattern, replacement in TECHNICAL_REPLACEMENTS:
        text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
    return text


def _sentence(value: str) -> str:
    text = value.strip()
    if not text:
        return ""
    return text[0].upper() + text[1:] + ("" if text.endswith((".", "!", "?")) else ".")


def _join_names(values: list[str]) -> str:
    values = [value for value in values if value]
    if not values:
        return "no one is chosen"
    if len(values) == 1:
        return values[0]
    if len(values) == 2:
        return f"{values[0]} and {values[1]}"
    return f"{', '.join(values[:-1])}, and {values[-1]}"


def _role_pointer(document: dict[str, object], role_id: str) -> str:
    for team_index, team in enumerate(_objects(document.get("teams"))):
        for role_index, role in enumerate(_objects(team.get("roles"))):
            if str(role.get("id") or "") == role_id:
                return f"/teams/{team_index}/roles/{role_index}"
    return "/teams"


def _diagnostic_role_ids(
    document: dict[str, object],
    diagnostic: dict[str, object],
) -> list[str]:
    pointer = str(diagnostic.get("pointer") or "/")
    result: list[str] = []
    match = re.match(r"^/teams/(\d+)/roles(?:/(\d+))?", pointer)
    teams = _objects(document.get("teams"))
    if match:
        try:
            team = teams[int(match.group(1))]
            roles = _objects(team.get("roles"))
            if match.group(2) is not None:
                role = roles[int(match.group(2))]
                result.append(str(role.get("id") or ""))
                result.extend(_strings(role.get("independent_from")))
            else:
                result.extend(
                    str(role.get("id") or "")
                    for role in roles
                    if role.get("duty") in {"implementer", "verifier"}
                )
        except (IndexError, TypeError, ValueError):
            pass
    message = str(diagnostic.get("message") or "")
    for quoted in re.findall(r"'([^']+)'", message):
        if any(
            quoted == str(role.get("id") or "")
            for team in teams
            for role in _objects(team.get("roles"))
        ):
            result.append(quoted)
    return list(dict.fromkeys(item for item in result if item))


def _section_for_diagnostic(diagnostic: dict[str, object]) -> str:
    code = str(diagnostic.get("code") or "")
    pointer = str(diagnostic.get("pointer") or "/")
    if code in INDEPENDENCE_CODES:
        return "independence"
    if code in DECISION_CODES:
        return "decisions"
    if code in AUDIT_CODES:
        return "audit"
    if code in ESCALATION_CODES or "/replacement" in pointer:
        return "escalation"
    if pointer.startswith("/councils"):
        if "/audit" in pointer or pointer.endswith("/meta_verifier"):
            return "audit"
        return "decisions"
    return "responsibilities"


def _correction(
    diagnostic: dict[str, object],
    section_id: str,
    role_ids: list[str],
) -> str:
    code = str(diagnostic.get("code") or "")
    names = _join_names([_display(item) for item in role_ids])
    fixed = {
        "missing-agents": "Add at least one bounded candidate for each required responsibility.",
        "missing-pools": "Create candidate groups that connect required responsibilities to available candidates.",
        "missing-teams": "Add one team with implementation and independent-review responsibilities.",
        "missing-roles": "Add the required implementation and independent-review responsibilities.",
        "missing-separation": (
            f"Keep {names} separate: require different candidates and a read-only reviewer."
            if role_ids else
            "Add one required implementer and one required independent reviewer, then keep their candidates separate."
        ),
        "impossible-independence": (
            f"Give {names} different candidates, profiles, and work areas."
            if role_ids else
            "Widen the candidate groups with distinct candidates, profiles, and work areas."
        ),
        "separation-violation": (
            f"Assign {names} to different execution identities, work areas, and work sessions."
            if role_ids else
            "Choose a separate reviewer identity, work area, and work session."
        ),
        "provider-diversity-unsatisfied": (
            "Choose a reviewer from a different model family."
        ),
        "duplicate-principal": "Require distinct reviewers for the saved agreement count.",
        "role-order": "Place the responsibility being reviewed before its independent reviewer.",
        "judgment-not-authorized": "Allow the independent reviewer to review the exact work responsibility.",
        "capability-smuggling": "Keep a read-only reviewer from carrying any write permission.",
        "missing-verdict-schema": "Choose the exact saved review-outcome format in Technical details.",
        "impossible-quorum": "Lower the required reviewer agreement or add enough distinct reviewers.",
        "invalid-threshold": "Make the agreement threshold match the chosen decision rule.",
        "missing-meta-verifier": "Choose a separate review auditor or turn off the audit.",
        "dissent-erasure": "Preserve earlier review history and disagreement when a reviewer is replaced.",
        "replacement-unrouted": "Choose when replacement is allowed or set the replacement count to zero.",
        "dangling-pool-reference": "Choose an existing candidate group for this responsibility or backup.",
        "unsupported-route": "Choose block, delivery-owner escalation, a named decision, or end delivery.",
        "unknown-key": "Open Technical details to inspect the unsupported field. It remains present and cannot be saved silently.",
    }
    if code in fixed:
        return fixed[code]
    remediation = _plain(diagnostic.get("remediation"))
    if remediation:
        return _sentence(remediation)
    return {
        "responsibilities": "Complete the affected work responsibility.",
        "independence": "Separate doing and reviewing with compatible candidates.",
        "decisions": "Complete the contested-decision rule.",
        "escalation": "Complete the finite replacement and escalation route.",
        "audit": "Complete the review-audit or architecture-check responsibility.",
    }[section_id]


def _affected_behavior(section_id: str) -> str:
    return {
        "responsibilities": "The team cannot determine who owns this work.",
        "independence": "The team cannot prove that work and review stay separate.",
        "decisions": "A contested review cannot reach a governed outcome safely.",
        "escalation": "Unavailable or failed work has no complete handoff.",
        "audit": "The review-of-review boundary is incomplete.",
    }[section_id]


def _design_roles(
    document: dict[str, object],
    compiled: Optional[dict[str, object]],
) -> tuple[list[dict[str, object]], dict[str, dict[str, object]]]:
    agents = {
        str(item.get("id") or ""): item
        for item in _objects(document.get("agents"))
    }
    pools = {
        str(item.get("id") or ""): _strings(item.get("agents"))
        for item in _objects(document.get("pools"))
    }
    proof_by_team: dict[str, dict[str, object]] = {}
    if isinstance(compiled, dict):
        proof_by_team = {
            str(item.get("team") or ""): item
            for item in _objects(compiled.get("logical_assignment_proofs"))
        }
    roles: list[dict[str, object]] = []
    by_id: dict[str, dict[str, object]] = {}
    for team_index, team in enumerate(_objects(document.get("teams"))):
        team_id = str(team.get("id") or f"team-{team_index + 1}")
        proof = proof_by_team.get(team_id, {})
        witness = {
            str(item.get("role") or ""): item
            for item in _objects(proof.get("witness"))
        }
        for role_index, role in enumerate(_objects(team.get("roles"))):
            role_id = str(role.get("id") or f"responsibility-{role_index + 1}")
            duty = str(role.get("duty") or "")
            pool_id = str(role.get("pool") or "")
            primary_ids = pools.get(pool_id, [])
            replacement = role.get("replacement")
            replacement = replacement if isinstance(replacement, dict) else {}
            fallback_pool_ids = _strings(replacement.get("fallback_pools"))
            fallback_ids = [
                agent_id
                for fallback_pool in fallback_pool_ids
                for agent_id in pools.get(fallback_pool, [])
                if agent_id not in primary_ids
            ]

            def candidate(agent_id: str) -> dict[str, object]:
                agent = agents.get(agent_id, {})
                return {
                    "label": _display(agent_id),
                    "agent_id": agent_id,
                    "profile": agent.get("profile"),
                    "workspace_domain": agent.get("workspace_domain"),
                    "technical_details": {
                        "duties": _copy(agent.get("duties", [])),
                        "capability_ceiling": _copy(
                            agent.get("capability_ceiling", [])
                        ),
                        "max_concurrency": agent.get("max_concurrency"),
                    },
                }

            primary = [candidate(agent_id) for agent_id in primary_ids]
            fallback = [candidate(agent_id) for agent_id in fallback_ids]
            witness_item = witness.get(role_id)
            first_names = [str(item["label"]) for item in primary]
            coverage = (
                f"{_join_names(first_names)} "
                f"{'are' if len(first_names) != 1 else 'is'} first in line"
                if first_names else
                "No candidate is connected yet"
            )
            item = {
                "id": role_id,
                "team": team_id,
                "name": _display(role_id),
                "label": DUTY_LABELS.get(duty, _display(duty or role_id)),
                "responsibility": DUTY_RESPONSIBILITIES.get(
                    duty, "Performs the saved bounded responsibility."
                ),
                "when": DUTY_WHEN.get(
                    duty, "When the calling work flow requests this responsibility."
                ),
                "outcomes": DUTY_OUTCOMES.get(
                    duty, "Produces only the saved bounded output."
                ),
                "coverage": (
                    f"{coverage}; {role.get('cardinality') or 1} "
                    f"{'place is' if role.get('cardinality') == 1 else 'places are'} "
                    f"{'required' if role.get('required') else 'optional'}."
                ),
                "required": bool(role.get("required")),
                "cardinality": role.get("cardinality"),
                "primary_candidates": primary,
                "backup_candidates": fallback,
                "independent_from": _strings(role.get("independent_from")),
                "can_request_help_from": _strings(role.get("may_request")),
                "can_review": _strings(role.get("may_judge")),
                "replacement": {
                    "maximum": replacement.get("max_replacements"),
                    "eligible_reasons": _copy(replacement.get("reasons", [])),
                    "fallback_groups": fallback_pool_ids,
                    "when_exhausted": replacement.get("on_exhausted"),
                    "when_exhausted_label": EXHAUSTION_LABELS.get(
                        str(replacement.get("on_exhausted") or ""),
                        "No complete route is chosen",
                    ),
                    "preserves_review_history": bool(
                        replacement.get("preserve_history")
                    ),
                },
                "policy_witness": (
                    {
                        "available": True,
                        "candidate_id": witness_item.get("agent"),
                        "candidate": _display(witness_item.get("agent")),
                        "profile": witness_item.get("profile"),
                        "workspace_domain": witness_item.get("workspace_domain"),
                    }
                    if isinstance(witness_item, dict) else
                    {"available": False}
                ),
                "pointer": f"/teams/{team_index}/roles/{role_index}",
                "technical_details": {
                    "role_id": role_id,
                    "duty": duty,
                    "pool": pool_id,
                    "workspace": role.get("workspace"),
                    "capability_ceiling": _copy(
                        role.get("capability_ceiling", [])
                    ),
                    "driver_capabilities": _copy(
                        role.get("driver_capabilities", [])
                    ),
                    "resource_groups": _copy(role.get("resource_groups", [])),
                    "context": _copy(role.get("context", {})),
                    "artifacts": _copy(role.get("artifacts", {})),
                    "output_schema": role.get("output_schema"),
                    "verdict_schema": role.get("verdict_schema"),
                },
            }
            roles.append(item)
            by_id[role_id] = item
    return roles, by_id


def _policy_independence(
    roles: list[dict[str, object]],
    by_id: dict[str, dict[str, object]],
) -> list[dict[str, object]]:
    constraints: list[dict[str, object]] = []
    for role in roles:
        for other_id in _strings(role.get("independent_from")):
            other = by_id.get(other_id)
            left_label = str(
                other.get("name") if isinstance(other, dict) else _display(other_id)
            )
            right_label = str(role.get("name") or _display(role.get("id")))
            left_witness = (
                other.get("policy_witness", {})
                if isinstance(other, dict) else {}
            )
            right_witness = role.get("policy_witness", {})
            witnessed = (
                isinstance(left_witness, dict)
                and isinstance(right_witness, dict)
                and bool(left_witness.get("available"))
                and bool(right_witness.get("available"))
            )
            distinct_policy = bool(
                witnessed
                and left_witness.get("candidate_id")
                != right_witness.get("candidate_id")
                and left_witness.get("profile") != right_witness.get("profile")
                and left_witness.get("workspace_domain")
                != right_witness.get("workspace_domain")
            )
            status = "policy-ready" if distinct_policy else "required-at-assignment"
            constraints.append({
                "id": f"{role.get('team')}:{role.get('id')}:{other_id}",
                "roles": [other_id, str(role.get("id") or "")],
                "labels": [left_label, right_label],
                "status": status,
                "summary": (
                    f"{right_label} must be separate from {left_label}. "
                    + (
                        "The saved candidate groups can supply different candidates, profiles, and work areas."
                        if distinct_policy else
                        "The later assignment must still choose compatible separate candidates."
                    )
                ),
                "runtime_claim": (
                    "Not proven until a start plan binds separate execution identities and work sessions."
                ),
                "correction": (
                    f"Choose different candidates, profiles, and work areas for "
                    f"{left_label} and {right_label}."
                ),
                "pointer": role.get("pointer"),
                "technical_details": {
                    "principal": "must-differ",
                    "profile": "must-differ",
                    "workspace_domain": "must-differ",
                    "session_binding": "must-differ",
                    "policy_witness": {
                        "left": _copy(left_witness),
                        "right": _copy(right_witness),
                    },
                },
            })
    return constraints


def _policy_diversity(
    document: dict[str, object],
    by_id: dict[str, dict[str, object]],
) -> list[dict[str, object]]:
    constraints: list[dict[str, object]] = []
    for index, rule in enumerate(_objects(document.get("diversity"))):
        if rule.get("kind") != "provider-family":
            continue
        role_ids = _strings(rule.get("roles"))
        if len(role_ids) != 2:
            continue
        left = by_id.get(role_ids[0], {})
        right = by_id.get(role_ids[1], {})
        left_label = str(left.get("name") or _display(role_ids[0]))
        right_label = str(right.get("name") or _display(role_ids[1]))
        rule_id = str(rule.get("id") or f"provider-family-{index + 1}")
        constraints.append({
            "id": f"diversity:{rule_id}",
            "kind": "provider-family",
            "rule": rule_id,
            "roles": role_ids,
            "labels": [left_label, right_label],
            "status": "policy-ready",
            "summary": (
                f"{left_label}'s work must be {DIFFERENT_MODEL_FAMILY_COPY}."
            ),
            "runtime_claim": (
                "The later assignment must prove both model families are declared and different."
            ),
            "correction": "Choose a reviewer from a different model family.",
            "pointer": f"/diversity/{index}",
            "technical_details": {
                "rule": rule_id,
                "dimension": "provider-family",
                "fail_closed_when_undeclared": True,
            },
        })
    return constraints


def _design_councils(
    document: dict[str, object],
    roles: dict[str, dict[str, object]],
) -> list[dict[str, object]]:
    result: list[dict[str, object]] = []
    for index, raw in enumerate(_objects(document.get("councils"))):
        decision = raw.get("decision")
        decision = decision if isinstance(decision, dict) else {}
        audit = raw.get("audit")
        audit = audit if isinstance(audit, dict) else {}
        member_ids = _strings(raw.get("members"))
        member_labels = [
            str(roles.get(role_id, {}).get("name") or _display(role_id))
            for role_id in member_ids
        ]
        judge_id = str(raw.get("judge") or "")
        judge_label = str(
            roles.get(judge_id, {}).get("name") or _display(judge_id)
        )
        method = str(decision.get("method") or "majority")
        audit_mode = str(audit.get("mode") or "none")
        if audit_mode == "full":
            audit_summary = (
                "A separate review auditor checks every participant result."
            )
        elif audit_mode == "sample":
            audit_summary = (
                f"A separate review auditor checks {audit.get('sample_size') or 1} "
                "participant result(s)."
            )
        else:
            audit_summary = "No separate review audit runs."
        veto_ids = _strings(decision.get("veto_roles"))
        result.append({
            "id": str(raw.get("id") or f"review-group-{index + 1}"),
            "label": _display(raw.get("id") or f"review group {index + 1}"),
            "kind": "council",
            "description": (
                "A governed discussion in which declared perspectives share a matter before reaching one outcome."
            ),
            "when": (
                "Runs only when a saved work flow calls this review group."
            ),
            "members": member_ids,
            "member_labels": member_labels,
            "required_agreement": raw.get("quorum"),
            "required_agreement_summary": (
                f"At least {raw.get('quorum') or 'an unchosen number of'} "
                "distinct reviewers must participate."
            ),
            "decision_method": method,
            "decision_summary": DECISION_METHODS.get(
                method, "The saved decision rule determines the outcome."
            ),
            "decision_owner": judge_id,
            "decision_owner_label": judge_label,
            "decision_owner_summary": (
                f"{judge_label} records the governed outcome; "
                + (
                    "that responsibility chooses only from allowed outcomes."
                    if method == "judge" else
                    "the saved agreement rule remains decisive."
                )
            ),
            "dissent": (
                "A minority or objection remains visible. The calling work flow decides whether it requests repair, escalates, blocks, or waits for a person."
            ),
            "veto_roles": veto_ids,
            "veto_summary": (
                f"An objection from {_join_names([_display(item) for item in veto_ids])} prevents passage."
                if veto_ids else
                "No responsibility has a separate objection right."
            ),
            "audit": {
                "mode": audit_mode,
                "summary": audit_summary,
                "auditor": raw.get("meta_verifier"),
                "auditor_label": (
                    str(
                        roles.get(
                            str(raw.get("meta_verifier") or ""), {}
                        ).get("name")
                        or _display(raw.get("meta_verifier"))
                    )
                    if raw.get("meta_verifier") else "No review auditor"
                ),
                "on_overturn": audit.get("on_overturn"),
                "on_overturn_label": EXHAUSTION_LABELS.get(
                    str(audit.get("on_overturn") or ""),
                    _display(audit.get("on_overturn")),
                ),
                "on_escalate": audit.get("on_escalate"),
                "on_escalate_label": EXHAUSTION_LABELS.get(
                    str(audit.get("on_escalate") or ""),
                    _display(audit.get("on_escalate")),
                ),
            },
            "pointer": f"/councils/{index}",
            "technical_details": {
                "quorum": raw.get("quorum"),
                "distinct_principals": raw.get("distinct_principals"),
                "decision": _copy(decision),
                "audit": _copy(audit),
                "budgets": _copy(raw.get("budgets", {})),
            },
        })
    return result


def _design_provenance(
    authority: Optional[dict[str, object]],
) -> list[dict[str, object]]:
    if not isinstance(authority, dict):
        return []
    contract = authority.get("execution_contract")
    if not isinstance(contract, dict):
        return []
    result: list[dict[str, object]] = []
    for port in _objects(contract.get("ports")):
        selector = port.get("selector")
        selector = selector if isinstance(selector, dict) else {}
        constraints = port.get("constraints")
        constraints = constraints if isinstance(constraints, dict) else {}
        local = port.get("local_resolution")
        local = local if isinstance(local, dict) else {}
        result.append({
            "agent": port.get("agent"),
            "profile": selector.get("profile"),
            "workspace_domain": constraints.get("workspace_domain"),
            "provider": local.get("provider"),
            "provider_family": local.get("provider_family"),
            "model_vendor": local.get("model_vendor"),
            "model_family": local.get("model_family"),
            "model": local.get("model"),
            "model_revision": local.get("model_revision"),
            "model_binding": local.get("model_binding"),
            "auth_domain_fingerprint": local.get("auth_domain_fingerprint"),
            "principal_fingerprint": local.get("principal_fingerprint"),
            "capability_fingerprint": local.get("capability_fingerprint"),
            "configured": bool(local.get("configured")),
            "available": bool(local.get("available")),
            "session_binding_key": None,
        })
    return result


def _corrections(
    document: dict[str, object],
    validation: Optional[dict[str, object]],
) -> list[dict[str, object]]:
    diagnostics = (
        _objects(validation.get("diagnostics"))
        if isinstance(validation, dict) else []
    )
    result: list[dict[str, object]] = []
    for diagnostic in diagnostics:
        section_id = _section_for_diagnostic(diagnostic)
        role_ids = _diagnostic_role_ids(document, diagnostic)
        target = diagnostic.get("target")
        target = target if isinstance(target, dict) else {}
        result.append({
            "section_id": section_id,
            "decision": SECTION_META[section_id][0],
            "affected_behavior": _affected_behavior(section_id),
            "correction": _correction(diagnostic, section_id, role_ids),
            "conflicting_roles": role_ids,
            "conflicting_labels": [_display(item) for item in role_ids],
            "target": {
                "pointer": str(
                    target.get("pointer")
                    or diagnostic.get("pointer")
                    or "/"
                ),
                "node_id": target.get("node_id"),
                "field_id": target.get("field_id"),
            },
            "technical_details": {
                "source": diagnostic.get("source"),
                "pointer": diagnostic.get("pointer"),
                "code": diagnostic.get("code"),
                "message": diagnostic.get("message"),
                "remediation": diagnostic.get("remediation"),
            },
        })
    return result


def _section(
    section_id: str,
    step: int,
    answer: str,
    items: list[dict[str, object]],
    corrections: list[dict[str, object]],
    pointers: list[str],
) -> dict[str, object]:
    label, question, guidance = SECTION_META[section_id]
    count = sum(
        1 for item in corrections if item.get("section_id") == section_id
    )
    return {
        "id": section_id,
        "step": step,
        "label": label,
        "question": question,
        "guidance": guidance,
        "answer": answer,
        "items": _copy(items),
        "source_pointers": pointers,
        "status": "needs-attention" if count else "ready",
        "correction_count": count,
    }


def build_team_review(
    document: object,
    validation: object = None,
    compiled: object = None,
    simulation: object = None,
    authority: object = None,
    round_trip: object = None,
    assignment: object = None,
    test_failures: object = None,
) -> dict[str, object]:
    """Build the task-shaped organization design view.

    ``assignment`` is optional.  Program Studio usually has only policy and
    local-resolution facts; a caller with a pure team assignment can supply it
    to upgrade independence from policy-ready to runtime-proven.
    """
    raw = document if isinstance(document, dict) else {}
    validation_doc = validation if isinstance(validation, dict) else {}
    compiled_doc = compiled if isinstance(compiled, dict) else None
    simulation_doc = simulation if isinstance(simulation, dict) else {}
    authority_doc = authority if isinstance(authority, dict) else None
    round_trip_doc = round_trip if isinstance(round_trip, dict) else {}
    assignment_doc = assignment if isinstance(assignment, dict) else None
    failure_doc = test_failures if isinstance(test_failures, dict) else None
    failure_review = (
        build_failure_projection(failure_doc)
        if failure_doc is not None else None
    )

    roles, by_id = _design_roles(raw, compiled_doc)
    constraints = _policy_independence(roles, by_id)
    runtime_separation: dict[str, object] = {}
    if assignment_doc is not None:
        separation = assignment_doc.get("separation")
        if isinstance(separation, dict):
            runtime_separation = _copy(separation)
            facts = separation.get("facts")
            facts = facts if isinstance(facts, dict) else {}
            runtime_pair = {
                str(facts.get("implementer_role") or ""),
                str(facts.get("verifier_role") or ""),
            }
            if separation.get("passed"):
                for constraint in constraints:
                    if set(constraint.get("roles", [])) == runtime_pair:
                        constraint["status"] = "runtime-proven"
                        constraint["runtime_claim"] = (
                            "The current assignment proves separate execution identities, work areas, and work sessions."
                        )
            elif not separation.get("passed"):
                for constraint in constraints:
                    if set(constraint.get("roles", [])) == runtime_pair:
                        constraint["status"] = "needs-attention"
                        constraint["runtime_claim"] = (
                            "The current assignment cannot prove the required separation."
                        )
    diversity_constraints = _policy_diversity(raw, by_id)
    if assignment_doc is not None:
        diversity = _assignment_diversity(assignment_doc)
        receipts = {
            str(item.get("id") or ""): item
            for item in _objects(
                diversity.get("rules")
            )
        }
        for constraint in diversity_constraints:
            receipt = receipts.get(str(constraint.get("rule") or ""))
            if isinstance(receipt, dict) and receipt.get("passed"):
                constraint["status"] = "runtime-proven"
                constraint["runtime_claim"] = (
                    f"The current assignment is {DIFFERENT_MODEL_FAMILY_COPY}."
                )
                constraint["technical_details"]["families"] = _copy(
                    receipt.get("families", {})
                )
            elif isinstance(receipt, dict):
                constraint["status"] = "needs-attention"
                constraint["runtime_claim"] = (
                    "The current assignment is not reviewed by a different model family."
                )
    constraints.extend(diversity_constraints)
    councils = _design_councils(raw, by_id)
    corrections = _corrections(raw, validation_doc)

    independence_errors = [
        item for item in corrections
        if item["section_id"] == "independence"
    ]
    if independence_errors:
        for constraint in constraints:
            if (
                not constraint["roles"]
                or set(constraint["roles"])
                & {
                    role_id
                    for item in independence_errors
                    for role_id in item["conflicting_roles"]
                }
            ):
                constraint["status"] = "needs-attention"

    required_roles = [item for item in roles if item["required"]]
    responsibility_answer = (
        "; ".join(
            f"{item['label']}: "
            f"{_join_names([str(candidate['label']) for candidate in item['primary_candidates']])}"
            for item in required_roles
        )
        if required_roles else
        "No required work responsibility has been connected to a candidate yet."
    )
    review_roles = [
        item for item in roles
        if item["technical_details"]["duty"] in {
            "verifier", "reviewer", "meta-verifier", "master-architect"
        }
    ]
    review_pairs = [
        item for item in constraints
        if item["roles"]
        and by_id.get(
            item["roles"][-1], {}
        ).get("technical_details", {}).get("duty") in {"verifier", "reviewer"}
    ]
    if review_pairs:
        independence_answer = " ".join(
            str(item["summary"]) for item in review_pairs
        )
    elif review_roles:
        independence_answer = (
            "Review responsibilities exist, but no explicit separation is declared."
        )
    else:
        independence_answer = "No independent-review responsibility is defined."

    if councils:
        decision_answer = " ".join(
            f"{item['label']}: {item['decision_summary']} "
            f"{item['decision_owner_label']} records the outcome."
            for item in councils
        )
    else:
        judges = [
            item for item in roles
            if item["technical_details"]["duty"] == "judge"
        ]
        decision_answer = (
            f"{_join_names([str(item['label']) for item in judges])} "
            "is available only when a saved work flow declares a contested decision."
            if judges else
            "No contested-decision group is defined; ordinary independent review remains decisive."
        )

    help_items = [
        {
            "id": str(role["id"]),
            "label": str(role["name"]),
            "summary": (
                f"{role['name']} may ask "
                f"{_join_names([str(by_id.get(item, {}).get('name') or _display(item)) for item in role['can_request_help_from']])} "
                "for bounded help."
            ),
            "requests": _copy(role["can_request_help_from"]),
            "pointer": role["pointer"],
        }
        for role in roles if role["can_request_help_from"]
    ]
    escalation_items = [
        {
            "id": str(role["id"]),
            "label": str(role["name"]),
            "summary": (
                f"After {role['replacement']['maximum'] or 0} replacement"
                f"{'' if role['replacement']['maximum'] == 1 else 's'}, "
                f"{str(role['replacement']['when_exhausted_label']).lower()}."
            ),
            "recipient": (
                "delivery-owner"
                if role["replacement"]["when_exhausted"] == "escalate"
                else role["replacement"]["when_exhausted"]
            ),
            "pointer": role["pointer"],
        }
        for role in roles
    ]
    escalated = [
        item for item in escalation_items if item["recipient"] == "delivery-owner"
    ]
    escalation_answer = (
        "Internal help goes only to the named team responsibilities. "
        + (
            "If replacement is exhausted, escalation leaves the team and waits for the separately authorized delivery owner; this team draft does not name or impersonate that person."
            if escalated else
            "No responsibility currently routes exhausted replacement to the delivery owner."
        )
    )

    audit_roles = [
        item for item in roles
        if item["technical_details"]["duty"]
        in {"meta-verifier", "master-architect"}
    ]
    audited_councils = [
        item for item in councils if item["audit"]["mode"] != "none"
    ]
    audit_answer_parts = [
        f"{item['label']}: {item['audit']['summary']} "
        f"{item['audit']['auditor_label']} owns this check."
        for item in audited_councils
    ]
    for role in audit_roles:
        if role["technical_details"]["duty"] == "master-architect":
            audit_answer_parts.append(
                f"{role['name']} performs architecture review only at a separately declared story or phase architecture check."
            )
    audit_answer = (
        " ".join(audit_answer_parts)
        if audit_answer_parts else
        "No review audit or architecture check is enabled by this team design."
    )

    section_values = {
        "responsibilities": (responsibility_answer, roles, ["/agents", "/pools", "/teams"]),
        "independence": (independence_answer, constraints, ["/teams"]),
        "decisions": (decision_answer, councils, ["/councils"]),
        "escalation": (
            escalation_answer,
            help_items + escalation_items,
            ["/teams"],
        ),
        "audit": (
            audit_answer,
            audited_councils + audit_roles,
            ["/councils", "/teams"],
        ),
    }
    sections = [
        _section(
            section_id,
            index,
            section_values[section_id][0],
            section_values[section_id][1],
            corrections,
            section_values[section_id][2],
        )
        for index, section_id in enumerate(SECTION_ORDER, start=1)
    ]

    valid = bool(validation_doc.get("valid"))
    unknown = [
        str(item.get("pointer") or "/")
        for item in _objects(validation_doc.get("diagnostics"))
        if item.get("code") == "unknown-key"
    ]
    primary_independence_ready = any(
        {
            by_id.get(role_id, {}).get(
                "technical_details", {}
            ).get("duty")
            for role_id in item.get("roles", [])
        } == {"implementer", "verifier"}
        and item.get("status") in {"policy-ready", "runtime-proven"}
        for item in constraints
    )
    policy_ready = bool(
        valid
        and roles
        and any(
            item["technical_details"]["duty"] == "implementer"
            for item in roles
        )
        and any(
            item["technical_details"]["duty"] == "verifier"
            for item in roles
        )
        and primary_independence_ready
    )
    assignment_diversity = _assignment_diversity(assignment_doc)
    runtime_status = (
        "proven"
        if assignment_doc is not None
        and isinstance(assignment_doc.get("separation"), dict)
        and assignment_doc["separation"].get("passed")
        and (
            not assignment_diversity.get("rules")
            or assignment_diversity.get("passed")
        )
        else "refused" if assignment_doc is not None
        else "not-assigned"
    )
    review_sections = [
        {
            "id": section["id"],
            "label": section["label"],
            "answer": section["answer"],
            "status": section["status"],
        }
        for section in sections
    ]
    return {
        "kind": TEAM_REVIEW_KIND,
        "schema_version": TEAM_REVIEW_SCHEMA_VERSION,
        "context": "design",
        "applicable": True,
        "name": raw.get("slug"),
        **({"test_failures": failure_review} if failure_review is not None else {}),
        "title": raw.get("title") or raw.get("slug") or "Team and review",
        "status": "ready-to-review" if policy_ready else "needs-attention",
        "summary": (
            "This team design names work, independent review, contested decisions, help, escalation, and review auditing."
            if policy_ready else
            (
                f"This team design needs {len(corrections)} correction"
                f"{'s' if len(corrections) != 1 else ''} before it can be saved."
                if corrections else
                "This team design needs a checked independent-review pairing before it can be saved."
            )
        ),
        "policy_readiness": {
            "ready": policy_ready,
            "logical_assignment_proofs": _copy(
                compiled_doc.get("logical_assignment_proofs", [])
                if isinstance(compiled_doc, dict) else []
            ),
            "simulation_teams": _copy(simulation_doc.get("teams", [])),
        },
        "runtime_independence": {
            "status": runtime_status,
            "claim": (
                "A valid team policy proves compatible separate candidates exist; it does not claim a runtime identity or session before assignment."
                if runtime_status == "not-assigned" else
                (
                    "The supplied assignment proves exact runtime separation and is "
                    f"{DIFFERENT_MODEL_FAMILY_COPY}."
                    if diversity_constraints else
                    "The supplied assignment proves the exact runtime separation facts."
                )
                if runtime_status == "proven" else
                "The supplied assignment cannot prove every required runtime separation fact."
            ),
            "separation": runtime_separation,
        },
        "sections": sections,
        "responsibilities": roles,
        "quality_constraints": constraints,
        "review_groups": councils,
        "help_requests": help_items,
        "escalation_routes": escalation_items,
        "corrections": corrections,
        "review_before_save": {
            section_id: section_values[section_id][0]
            for section_id in SECTION_ORDER
        },
        "review_sections": review_sections,
        "progressive_details": {
            "independent_pair": any(
                item["technical_details"]["duty"] == "verifier"
                for item in roles
            ),
            "review_panel": any(
                item["technical_details"]["duty"] in {"verifier", "reviewer"}
                and int(item.get("cardinality") or 0) > 1
                for item in roles
            ),
            "council": bool(councils),
            "dissent": bool(councils),
            "judge": any(
                item["technical_details"]["duty"] == "judge"
                for item in roles
            ),
            "review_auditor": any(
                item["technical_details"]["duty"] == "meta-verifier"
                for item in roles
            ),
            "architecture_review": any(
                item["technical_details"]["duty"] == "master-architect"
                for item in roles
            ),
        },
        "technical_details": {
            "provenance": _design_provenance(authority_doc),
            "provider_model_do_not_prove_independence": True,
            "principal_workspace_session_remain_distinct": True,
            "credentials_exposed": False,
            "exact_role_ids_authoritative": True,
            "round_trip_lossless": bool(round_trip_doc.get("lossless")),
            "semantic_identity_preserved": bool(
                round_trip_doc.get("semantic_hash_preserved")
            ),
            "layout_identity_preserved": bool(
                round_trip_doc.get("layout_hash_preserved")
            ),
        },
        "edit_safety": {
            "targeted_edits_preserve_unedited_fields": True,
            "unknown_fields": unknown,
            "unknown_fields_preserved": bool(unknown),
            "invalid_save_refused": True,
            "exact_export_available": True,
        },
        "source_models": [
            "delivery-workbench-organization",
            "delivery-workbench-organization-validation",
            "delivery-workbench-compiled-organization",
            "delivery-workbench-organization-simulation",
            "delivery-workbench-program-studio-authority-preview",
            "delivery-workbench-program-studio-round-trip",
        ] + (
            ["delivery-workbench-team-assignment"]
            if assignment_doc is not None else []
        ),
        "starts_work": False,
        "writes_policy": False,
        "writes_roadmap": False,
        "writes_run_state": False,
        "creates_grant": False,
        "starts_process": False,
        "starts_observer": False,
        "sends_notification": False,
        "uses_network": False,
    }


def build_live_team_review(
    organization: object,
    decisions: object = None,
    dissent: object = None,
    gates: object = None,
) -> dict[str, object]:
    """Build the same view shape over one already-assigned live team."""
    source = organization if isinstance(organization, dict) else {}
    roles = _objects(source.get("roles"))
    responsibilities: list[dict[str, object]] = []
    for role in roles:
        duty = str(role.get("duty") or "")
        responsibilities.append({
            "id": str(role.get("role") or ""),
            "team": source.get("team"),
            "name": _display(role.get("role")),
            "label": DUTY_LABELS.get(duty, _display(duty or role.get("role"))),
            "responsibility": DUTY_RESPONSIBILITIES.get(
                duty, "Performs the assigned bounded responsibility."
            ),
            "when": DUTY_WHEN.get(
                duty, "When the live work flow requests this responsibility."
            ),
            "outcomes": DUTY_OUTCOMES.get(
                duty, "Produces only the assigned bounded output."
            ),
            "coverage": (
                f"{_display(role.get('agent'))} is assigned through "
                f"{_display(role.get('profile'))}."
            ),
            "required": True,
            "cardinality": 1,
            "assigned": {
                "agent": role.get("agent"),
                "profile": role.get("profile"),
                "activity": role.get("activity"),
                "last_result": role.get("last_result"),
            },
            "pointer": None,
            "technical_details": {
                "address": role.get("address"),
                "role_id": role.get("role"),
                "duty": duty,
                "principal_fingerprint": role.get("principal_fingerprint"),
                "workspace_domain": role.get("workspace_domain"),
                "session_binding_key": role.get("session_binding_key"),
                "assignment_generation": role.get("assignment_generation"),
                "execution": _copy(role.get("execution", {})),
                "authority_ceiling": _copy(role.get("authority_ceiling", [])),
            },
        })
    separation = source.get("separation")
    separation = separation if isinstance(separation, dict) else {}
    separation_passed = bool(separation.get("passed"))
    implementer = next(
        (item for item in responsibilities if item["technical_details"]["duty"] == "implementer"),
        None,
    )
    verifier = next(
        (item for item in responsibilities if item["technical_details"]["duty"] == "verifier"),
        None,
    )
    constraints = []
    if implementer is not None and verifier is not None:
        constraints.append({
            "id": "live:implementer:verifier",
            "roles": [implementer["id"], verifier["id"]],
            "labels": [implementer["name"], verifier["name"]],
            "status": "runtime-proven" if separation_passed else "needs-attention",
            "summary": (
                f"{verifier['name']} is assigned separately from {implementer['name']}."
                if separation_passed else
                f"{verifier['name']} is not proven separate from {implementer['name']}."
            ),
            "runtime_claim": (
                "Separate execution identity, profile, work area, session binding, and read-only review are proven."
                if separation_passed else
                "Delivery remains stopped until every exact separation fact passes."
            ),
            "correction": (
                "Choose a different reviewer execution identity, work area, and work session."
            ),
            "pointer": None,
            "technical_details": _copy(separation.get("facts", {})),
        })
    diversity = _assignment_diversity(source)
    responsibility_names = {
        str(item["id"]): str(item["name"]) for item in responsibilities
    }
    for receipt in _objects(diversity.get("rules")):
        role_ids = _strings(receipt.get("roles"))
        labels = [
            responsibility_names.get(role_id, _display(role_id))
            for role_id in role_ids
        ]
        passed = bool(receipt.get("passed"))
        constraints.append({
            "id": f"live:diversity:{receipt.get('id')}",
            "kind": "provider-family",
            "rule": receipt.get("id"),
            "roles": role_ids,
            "labels": labels,
            "status": "runtime-proven" if passed else "needs-attention",
            "summary": (
                f"{labels[0] if labels else 'The work'} is {DIFFERENT_MODEL_FAMILY_COPY}."
                if passed else
                f"{labels[0] if labels else 'The work'} is not proven reviewed by a different model family."
            ),
            "runtime_claim": (
                "Both assigned model families are declared and different."
                if passed else
                "Delivery remains stopped until both model families are declared and different."
            ),
            "correction": "Choose a reviewer from a different model family.",
            "pointer": None,
            "technical_details": _copy(receipt),
        })
    councils = []
    for index, council in enumerate(_objects(source.get("councils"))):
        method = str(
            council.get("decision", {}).get("method")
            if isinstance(council.get("decision"), dict)
            else council.get("method") or "majority"
        )
        councils.append({
            "id": str(council.get("id") or f"review-group-{index + 1}"),
            "label": _display(council.get("id") or f"review group {index + 1}"),
            "kind": "council",
            "description": "A governed discussion over the assigned matter.",
            "members": _copy(
                council.get("assigned_members", council.get("members", []))
            ),
            "required_agreement": council.get("quorum"),
            "required_agreement_summary": (
                f"At least {council.get('quorum') or 'the saved number of'} distinct reviewers must participate."
            ),
            "decision_method": method,
            "decision_summary": DECISION_METHODS.get(
                method, "The saved decision rule determines the outcome."
            ),
            "decision_owner": council.get("judge"),
            "dissent": "Minority and objection records remain visible.",
            "technical_details": _copy(council),
        })

    diversity_passed = (
        bool(diversity.get("passed"))
        if diversity.get("rules") else True
    )
    runtime_passed = separation_passed and diversity_passed
    decision_docs = _objects(decisions)
    dissent_docs = _objects(dissent)
    gate_docs = _objects(gates)
    responsibility_answer = (
        "; ".join(
            f"{item['label']}: {_display(item['assigned']['agent'])}"
            for item in responsibilities
        )
        if responsibilities else
        "No live responsibility is assigned."
    )
    independence_answer = (
        " ".join(str(item["summary"]) for item in constraints)
        if constraints else
        "No implementer and independent-review pair is present."
    )
    decision_answer = (
        f"{len(councils)} governed review group"
        f"{'s' if len(councils) != 1 else ''}; "
        f"{len(decision_docs)} recorded contested decision"
        f"{'s' if len(decision_docs) != 1 else ''}; "
        f"{len(dissent_docs)} preserved disagreement record"
        f"{'s' if len(dissent_docs) != 1 else ''}."
        if councils or decision_docs else
        "No contested decision is active or recorded."
    )
    escalation_answer = (
        "If work escalates, it leaves the assigned team and waits for the separately authorized delivery owner; assigned team members cannot grant themselves that authority."
    )
    audit_answer = (
        f"{sum(1 for item in responsibilities if item['technical_details']['duty'] == 'meta-verifier')} review auditor"
        f"{'s' if sum(1 for item in responsibilities if item['technical_details']['duty'] == 'meta-verifier') != 1 else ''}, "
        f"{sum(1 for item in responsibilities if item['technical_details']['duty'] == 'master-architect')} architecture reviewer"
        f"{'s' if sum(1 for item in responsibilities if item['technical_details']['duty'] == 'master-architect') != 1 else ''}, "
        f"and {len(gate_docs)} recorded architecture or quality check"
        f"{'s' if len(gate_docs) != 1 else ''}."
    )
    section_values = {
        "responsibilities": (responsibility_answer, responsibilities),
        "independence": (independence_answer, constraints),
        "decisions": (decision_answer, councils + decision_docs),
        "escalation": (escalation_answer, []),
        "audit": (audit_answer, gate_docs),
    }
    sections = [
        _section(
            section_id,
            index,
            section_values[section_id][0],
            section_values[section_id][1],
            [],
            [],
        )
        for index, section_id in enumerate(SECTION_ORDER, start=1)
    ]
    provenance = [
        {
            "role": item["id"],
            "agent": item["assigned"]["agent"],
            "profile": item["assigned"]["profile"],
            "principal_fingerprint": item["technical_details"]["principal_fingerprint"],
            "workspace_domain": item["technical_details"]["workspace_domain"],
            "session_binding_key": item["technical_details"]["session_binding_key"],
            **_copy(item["technical_details"]["execution"]),
        }
        for item in responsibilities
    ]
    return {
        "kind": TEAM_REVIEW_KIND,
        "schema_version": TEAM_REVIEW_SCHEMA_VERSION,
        "context": "live",
        "applicable": True,
        "name": source.get("slug"),
        "title": f"{_display(source.get('team'))} team and review",
        "status": "ready" if runtime_passed else "needs-attention",
        "summary": (
            "Live ownership and review use the same responsibility and independence projection as Program Studio."
        ),
        "policy_readiness": {"ready": True},
        "runtime_independence": {
            "status": "proven" if runtime_passed else "refused",
            "claim": (
                (
                    "The assigned team proves every exact separation fact and is "
                    f"{DIFFERENT_MODEL_FAMILY_COPY}."
                    if diversity.get("rules") else
                    "The assigned team proves every exact separation fact."
                )
                if runtime_passed else
                "The assigned team does not prove every required review-separation fact."
            ),
            "separation": _copy(separation),
        },
        "sections": sections,
        "responsibilities": responsibilities,
        "quality_constraints": constraints,
        "review_groups": councils,
        "dissent": dissent_docs,
        "corrections": [],
        "review_before_save": {},
        "review_sections": [
            {
                "id": item["id"],
                "label": item["label"],
                "answer": item["answer"],
                "status": item["status"],
            }
            for item in sections
        ],
        "progressive_details": {
            "independent_pair": bool(constraints),
            "review_panel": False,
            "council": bool(councils),
            "dissent": bool(dissent_docs),
            "judge": any(
                item["technical_details"]["duty"] == "judge"
                for item in responsibilities
            ),
            "review_auditor": any(
                item["technical_details"]["duty"] == "meta-verifier"
                for item in responsibilities
            ),
            "architecture_review": any(
                item["technical_details"]["duty"] == "master-architect"
                for item in responsibilities
            ),
        },
        "technical_details": {
            "provenance": provenance,
            "provider_model_do_not_prove_independence": True,
            "principal_workspace_session_remain_distinct": True,
            "credentials_exposed": False,
            "roster_hash": source.get("roster_hash"),
            "assignment_hash": source.get("assignment_hash"),
        },
        "source_models": [
            "delivery-workbench-team-assignment",
            "delivery-workbench-program-event",
        ],
        "starts_work": False,
        "writes_policy": False,
        "writes_roadmap": False,
        "writes_run_state": False,
        "creates_grant": False,
        "starts_process": False,
        "starts_observer": False,
        "sends_notification": False,
        "uses_network": False,
    }
