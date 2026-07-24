"""Task-shaped delivery-plan authoring projections.

This module does not compile, normalize, or mutate program/workflow policy.
It reorganizes the exact Program Studio document, graph, validation, and
round-trip models around the decisions a person makes while designing a
delivery.  Exact identifiers and diagnostics remain attached as technical
detail; every ordinary statement is source-traceable to the supplied models.
"""

from __future__ import annotations

import re
from typing import Any


DELIVERY_PLAN_AUTHORING_KIND = "delivery-workbench-delivery-plan-authoring"
DELIVERY_PLAN_AUTHORING_SCHEMA_VERSION = 1

SECTION_ORDER = (
    "scope",
    "flow",
    "quality",
    "decisions",
    "recovery",
    "stops",
    "limits",
)

SECTION_META = {
    "scope": (
        "Delivery scope",
        "What will be delivered?",
        "Name the roadmap work and the boundary this plan may cover.",
    ),
    "flow": (
        "Work flow",
        "How should work move?",
        "Describe the route from ready work through completion.",
    ),
    "quality": (
        "Quality and review",
        "What must be true before work can pass?",
        "Place checks and independent review where quality matters.",
    ),
    "decisions": (
        "Decision points",
        "When should a person decide?",
        "Name the closed choices that can pause, redirect, or stop work.",
    ),
    "recovery": (
        "Repair and escalation",
        "What happens when work does not pass?",
        "Make repair, help, and blocked-work routes visible before delivery.",
    ),
    "stops": (
        "Stop conditions",
        "When must delivery stop?",
        "State completion and safety stops explicitly.",
    ),
    "limits": (
        "Limits",
        "How much work may this delivery use?",
        "Keep time, attempts, work, and cost finite and reviewable.",
    ),
}

WORK_STEP_LABELS = {
    "agent": "Do the work",
    "check": "Run a check",
    "collect": "Gather the results",
    "bounded_run": "Complete one bounded delivery",
    "subflow": "Use a detailed work flow",
    "loop": "Repeat a bounded repair",
    "debate": "Compare perspectives",
    "verdict": "Review the outcome",
    "gate": "Check required evidence",
    "checkpoint": "Ask for a decision",
    "rail": "Perform a delivery action",
}

ADVANCED_STEP_TYPES = {"subflow", "loop", "debate", "gate", "rail", "bounded_run"}
QUALITY_STEP_TYPES = {"check", "verdict", "gate", "debate"}
DECISION_STEP_TYPES = {"checkpoint", "debate", "gate"}

BOUND_LABELS = {
    "max_rounds": "Maximum rounds",
    "max_attempts": "Maximum attempts",
    "timeout_seconds": "Time limit in seconds",
    "round_timeout_seconds": "Time limit per round in seconds",
    "artifact_max_bytes": "Maximum result size in bytes",
    "artifact_max_tokens": "Maximum result size in tokens",
    "quorum": "Required reviewer agreement",
    "freshness_seconds": "Review freshness in seconds",
}

BUDGET_LABELS = {
    "max_phases": "Maximum phases",
    "max_stories": "Maximum stories",
    "max_child_runs": "Maximum child deliveries",
    "max_agent_starts": "Maximum worker starts",
    "max_provider_starts": "Maximum provider starts",
    "max_model_starts": "Maximum model starts",
    "max_check_starts": "Maximum check starts",
    "max_loop_rounds": "Maximum repair rounds",
    "max_debate_rounds": "Maximum decision rounds",
    "max_councils": "Maximum review groups",
    "max_repairs_per_story": "Maximum repairs per story",
    "max_verdicts": "Maximum review outcomes",
    "max_obligations": "Maximum follow-up obligations",
    "max_obligation_materializations": "Maximum obligation updates",
    "max_obligation_dispositions": "Maximum obligation decisions",
    "max_integrations": "Maximum integrations",
    "max_commits": "Maximum commits",
    "max_pushes": "Maximum pushes",
    "max_nudges": "Maximum follow-up prompts",
    "max_artifact_bytes": "Maximum evidence bytes",
    "max_tokens": "Maximum model tokens",
    "max_observed_cost_microunits": "Maximum observed cost",
    "max_wall_seconds": "Maximum elapsed seconds",
}

STOP_LABELS = {
    "scope-complete": "All work in scope is complete",
    "checkpoint-required": "A named decision is required",
    "unresolved-dissent": "Review disagreement remains unresolved",
    "architect-veto": "The plan owner stops the delivery",
    "blocked-frontier": "The next work is blocked",
    "budget-exhausted": "A finite limit is reached",
    "grant-expired": "Permission expires",
    "grant-revoked": "Permission is withdrawn",
}

TECHNICAL_REPLACEMENTS = (
    (r"\bworkflow\b", "work flow"),
    (r"\bworkflows\b", "work flows"),
    (r"\bbinding\b", "work route"),
    (r"\bbindings\b", "work routes"),
    (r"\brubrics?\b", "review criteria"),
    (r"\bcapabilities\b", "allowed actions"),
    (r"\bcapability\b", "allowed action"),
    (r"\bgrant\b", "permission"),
    (r"\bfrontier\b", "next work"),
    (r"\bcompiler\b", "plan checker"),
    (r"\bnodes\b", "steps"),
    (r"\bnode\b", "step"),
    (r"\bquorum\b", "required reviewer agreement"),
    (r"\bmeta-verifier\b", "review auditor"),
)


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


def _plain(text: object) -> str:
    result = str(text or "").strip()
    for pattern, replacement in TECHNICAL_REPLACEMENTS:
        result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)
    return result


def _route_meaning(route: object) -> str:
    if not isinstance(route, dict):
        return "The next step is not yet defined."
    kind = route.get("kind")
    target = str(route.get("target") or "")
    if kind == "terminal":
        return "Finish the delivery."
    if kind == "node":
        return f"Continue to {target}." if target else "Continue to the next work."
    if kind == "action":
        meanings = {
            "block": "Stop with a blocker.",
            "checkpoint": "Ask for a decision.",
            "escalate": "Ask the named owner for help.",
            "abort": "Stop this delivery.",
        }
        return meanings.get(target, f"Take the declared {target} action.")
    return "Follow the declared outcome."


def _phase_range(value: object) -> str:
    if not isinstance(value, dict):
        return "Not chosen"
    start, end = value.get("from"), value.get("through")
    if start is None or end is None:
        return "Not chosen"
    return str(start) if start == end else f"{start} through {end}"


def _story_scope(value: object) -> str:
    if value == "all":
        return "Every story in the selected phases"
    if isinstance(value, dict):
        included = _strings(value.get("include"))
        if included:
            return ", ".join(included)
    return "No work selected"


def _program_sections(
    document: dict[str, object],
    graph: dict[str, object],
) -> dict[str, dict[str, object]]:
    scope = document.get("scope")
    scope = scope if isinstance(scope, dict) else {}
    bindings = _objects(document.get("bindings"))
    phase_gates = _objects(document.get("phase_gates"))
    nudges = _objects(document.get("nudges"))
    budgets = document.get("budgets")
    budgets = budgets if isinstance(budgets, dict) else {}
    stops = _strings(document.get("stop_conditions"))

    routes: list[dict[str, object]] = []
    for index, binding in enumerate(bindings):
        match = binding.get("match")
        match = match if isinstance(match, dict) else {}
        start = match.get("phase_from")
        end = match.get("phase_through")
        phase = _phase_range({"from": start, "through": end})
        review = _strings(binding.get("rubrics"))
        routes.append({
            "id": str(binding.get("id") or f"route-{index + 1}"),
            "label": str(binding.get("id") or f"Work route {index + 1}"),
            "summary": (
                f"Phases {phase} use {binding.get('workflow') or 'an unchosen work flow'}."
            ),
            "detail": (
                f"Team {binding.get('team') or 'not chosen'}"
                + (
                    f" · review criteria {', '.join(review)}"
                    if review else " · review criteria not chosen"
                )
            ),
            "pointer": f"/bindings/{index}",
            "advanced": False,
        })

    quality_items: list[dict[str, object]] = []
    for index, binding in enumerate(bindings):
        for criterion in _strings(binding.get("rubrics")):
            quality_items.append({
                "label": criterion,
                "summary": f"Required review criteria for {binding.get('id') or 'this work route'}.",
                "pointer": f"/bindings/{index}/rubrics",
            })
    for index, gate in enumerate(phase_gates):
        quality_items.append({
            "label": str(gate.get("id") or f"Phase review {index + 1}"),
            "summary": (
                f"{gate.get('role') or 'A named reviewer'} checks "
                f"{gate.get('rubric') or 'the chosen review criteria'} before phase completion."
            ),
            "pointer": f"/phase_gates/{index}",
        })

    decisions = [
        {
            "label": str(gate.get("id") or f"Decision {index + 1}"),
            "summary": (
                "Before a phase completes, "
                f"{gate.get('role') or 'the named owner'} may "
                f"{'stop work' if gate.get('on_fail') == 'block' else 'request a decision' if gate.get('on_fail') == 'checkpoint' else 'end the delivery'}."
            ),
            "pointer": f"/phase_gates/{index}",
        }
        for index, gate in enumerate(phase_gates)
    ]

    recovery = [{
        "label": "Blocked work",
        "summary": "Stop and surface the blocker before selecting more work.",
        "pointer": "/scope/blocked_policy",
    }]
    recovery.extend({
        "label": str(item.get("id") or f"Follow-up {index + 1}"),
        "summary": str(item.get("expectation") or "Prompt the named work route to repair a known failure."),
        "pointer": f"/nudges/{index}",
        "advanced": True,
    } for index, item in enumerate(nudges))

    limits = [
        {
            "label": BUDGET_LABELS.get(str(key), str(key).replace("_", " ").title()),
            "value": value,
            "pointer": f"/budgets/{key}",
        }
        for key, value in budgets.items()
    ]

    return {
        "scope": {
            "answer": (
                f"{scope.get('project') or 'No project'} · phases "
                f"{_phase_range(scope.get('phases'))} · {_story_scope(scope.get('stories'))}."
            ),
            "facts": [
                {"label": "Roadmap project", "value": scope.get("project") or "Not chosen", "pointer": "/scope/project"},
                {"label": "Phases", "value": _phase_range(scope.get("phases")), "pointer": "/scope/phases"},
                {"label": "Work", "value": _story_scope(scope.get("stories")), "pointer": "/scope/stories"},
            ],
            "items": [],
            "source_pointers": ["/scope"],
            "example": "Example: deliver one named phase, or a reviewed list of stories.",
        },
        "flow": {
            "answer": (
                f"{len(routes)} work route{'s' if len(routes) != 1 else ''} "
                "connect scoped work to a saved work flow."
                if routes else "No work route has been chosen yet."
            ),
            "facts": [],
            "items": routes,
            "source_pointers": ["/bindings"],
            "example": "Example: all stories in phase 27 use the implementation-and-review flow.",
        },
        "quality": {
            "answer": (
                f"{len(quality_items)} review point{'s' if len(quality_items) != 1 else ''} "
                "are visible before save."
                if quality_items else "No review point is defined yet."
            ),
            "facts": [],
            "items": quality_items,
            "source_pointers": ["/bindings", "/phase_gates"],
            "example": "Example: require story review, then an architecture check before phase completion.",
        },
        "decisions": {
            "answer": (
                f"{len(decisions)} named phase decision{'s' if len(decisions) != 1 else ''}."
                if decisions else "No phase decision point is defined."
            ),
            "facts": [],
            "items": decisions,
            "source_pointers": ["/phase_gates"],
            "example": "Example: if the phase review does not pass, stop and ask the plan owner.",
        },
        "recovery": {
            "answer": "Blocked work stops; optional follow-up prompts remain finite.",
            "facts": [],
            "items": recovery,
            "source_pointers": ["/scope/blocked_policy", "/nudges"],
            "example": "Example: failed review returns to repair; unresolved work becomes a blocker.",
        },
        "stops": {
            "answer": (
                f"{len(stops)} explicit stop condition{'s' if len(stops) != 1 else ''}."
                if stops else "No stop condition is defined yet."
            ),
            "facts": [],
            "items": [
                {
                    "label": STOP_LABELS.get(stop, stop.replace("-", " ").title()),
                    "summary": "",
                    "pointer": f"/stop_conditions/{index}",
                }
                for index, stop in enumerate(stops)
            ],
            "source_pointers": ["/stop_conditions"],
            "example": "Example: stop when scope completes, work is blocked, or a finite limit is reached.",
        },
        "limits": {
            "answer": (
                f"{len(limits)} finite limit{'s' if len(limits) != 1 else ''} are declared."
                if limits else "No finite limit is visible yet."
            ),
            "facts": limits,
            "items": [],
            "source_pointers": ["/budgets"],
            "example": "Example: cap stories, repair attempts, elapsed time, pushes, and model use.",
        },
    }


def _workflow_routes(node: dict[str, object]) -> list[tuple[str, object]]:
    result: list[tuple[str, object]] = []
    for key in (
        "on_success",
        "on_failure",
        "on_exhausted",
        "on_consensus",
        "on_repair",
        "on_dissent",
        "on_quorum_lost",
    ):
        if key in node:
            result.append((key.removeprefix("on_"), node.get(key)))
    routes = node.get("routes")
    if isinstance(routes, dict):
        result.extend((str(key), value) for key, value in routes.items())
    return result


def _workflow_step(
    node: dict[str, object],
    index: int,
    graph_nodes: dict[str, dict[str, object]],
) -> dict[str, object]:
    node_id = str(node.get("id") or f"step-{index + 1}")
    kind = str(node.get("type") or "unknown")
    graph_node = graph_nodes.get(node_id, {})
    purpose = (
        node.get("title")
        or node.get("description")
        or node.get("task")
        or node.get("prompt")
        or node.get("purpose")
        or WORK_STEP_LABELS.get(kind, "Complete a declared step")
    )
    dependencies = _strings(node.get("needs"))
    routes = [
        {"outcome": outcome.replace("_", " "), "meaning": _route_meaning(route)}
        for outcome, route in _workflow_routes(node)
    ]
    return {
        "id": node_id,
        "label": WORK_STEP_LABELS.get(kind, kind.replace("_", " ").title()),
        "summary": str(purpose),
        "detail": (
            f"After {', '.join(dependencies)}"
            if dependencies else "Starts when its declared inputs are ready"
        ),
        "outcomes": routes,
        "bounds": [
            {
                "label": BOUND_LABELS.get(str(key), str(key).replace("_", " ").title()),
                "value": value,
                "pointer": f"/nodes/{index}/{key}",
            }
            for key, value in (graph_node.get("bounds") or {}).items()
        ] if isinstance(graph_node.get("bounds"), dict) else [],
        "pointer": f"/nodes/{index}",
        "technical_type": kind,
        "advanced": kind in ADVANCED_STEP_TYPES,
    }


def _workflow_sections(
    document: dict[str, object],
    graph: dict[str, object],
) -> dict[str, dict[str, object]]:
    nodes = _objects(document.get("nodes"))
    parameters = _objects(document.get("parameters"))
    defaults = document.get("defaults")
    defaults = defaults if isinstance(defaults, dict) else {}
    terminals = _objects(document.get("terminals"))
    graph_nodes = {
        str(item.get("id")): item
        for item in _objects(graph.get("nodes"))
    }
    steps = [
        _workflow_step(node, index, graph_nodes)
        for index, node in enumerate(nodes)
    ]
    quality = [
        {
            "id": step["id"],
            "label": step["label"],
            "summary": step["summary"],
            "pointer": step["pointer"],
        }
        for step in steps
        if step["technical_type"] in QUALITY_STEP_TYPES
    ]
    decisions = [
        {
            "id": step["id"],
            "label": step["label"],
            "summary": step["summary"],
            "pointer": step["pointer"],
        }
        for step in steps
        if step["technical_type"] in DECISION_STEP_TYPES
    ]
    recovery: list[dict[str, object]] = []
    actions: set[str] = set()
    for index, node in enumerate(nodes):
        for outcome, route in _workflow_routes(node):
            if outcome in {"failure", "repair", "exhausted", "dissent", "quorum_lost"}:
                recovery.append({
                    "id": str(node.get("id") or f"step-{index + 1}"),
                    "label": f"{WORK_STEP_LABELS.get(str(node.get('type')), 'Work')} · {outcome.replace('_', ' ')}",
                    "summary": _route_meaning(route),
                    "pointer": f"/nodes/{index}/on_{outcome}",
                })
            if isinstance(route, dict) and route.get("kind") == "action":
                actions.add(str(route.get("target") or ""))
    limits = [
        bound
        for step in steps
        for bound in step.get("bounds", [])
        if isinstance(bound, dict)
    ]
    work_inputs = [
        {
            "label": str(parameter.get("id") or f"Input {index + 1}"),
            "value": (
                f"{parameter.get('type') or 'value'}"
                + (" · required" if parameter.get("required") else " · optional")
                + (
                    f" · default {defaults.get(parameter.get('id'))}"
                    if parameter.get("id") in defaults else ""
                )
            ),
            "pointer": f"/parameters/{index}",
        }
        for index, parameter in enumerate(parameters)
    ]

    stop_items = [
        {
            "label": str(terminal.get("meaning") or terminal.get("id") or f"Completion {index + 1}").replace("-", " ").title(),
            "summary": "A declared successful end to this work flow.",
            "pointer": f"/terminals/{index}",
        }
        for index, terminal in enumerate(terminals)
    ]
    stop_items.extend({
        "label": {
            "block": "Stop with a blocker",
            "checkpoint": "Pause for a decision",
            "escalate": "Stop and ask for help",
            "abort": "End this delivery",
        }.get(action, action.replace("-", " ").title()),
        "summary": "A declared non-success exit from the work flow.",
        "pointer": "/nodes",
    } for action in sorted(actions) if action)

    return {
        "scope": {
            "answer": (
                f"{len(work_inputs)} named work input{'s' if len(work_inputs) != 1 else ''}."
                if work_inputs else "This flow needs no named input."
            ),
            "facts": work_inputs,
            "items": [],
            "source_pointers": ["/parameters", "/defaults"],
            "example": "Example: receive the selected story id and the evidence required for review.",
        },
        "flow": {
            "answer": (
                f"{len(steps)} work step{'s' if len(steps) != 1 else ''} lead from ready work to an explicit outcome."
                if steps else "No work step is defined yet."
            ),
            "facts": [],
            "items": steps,
            "source_pointers": ["/nodes"],
            "example": "Example: prepare the work, implement it, run checks, then request review.",
        },
        "quality": {
            "answer": (
                f"{len(quality)} quality or review point{'s' if len(quality) != 1 else ''}."
                if quality else "No quality or review point is defined yet."
            ),
            "facts": [],
            "items": quality,
            "source_pointers": ["/nodes"],
            "example": "Example: run mechanical checks before an independent outcome review.",
        },
        "decisions": {
            "answer": (
                f"{len(decisions)} explicit decision point{'s' if len(decisions) != 1 else ''}."
                if decisions else "No explicit decision point is defined."
            ),
            "facts": [],
            "items": decisions,
            "source_pointers": ["/nodes"],
            "example": "Example: approve, request repair, or stop after a reviewed handoff.",
        },
        "recovery": {
            "answer": (
                f"{len(recovery)} failed-work route{'s' if len(recovery) != 1 else ''}."
                if recovery else "No repair or escalation route is visible yet."
            ),
            "facts": [],
            "items": recovery,
            "source_pointers": ["/nodes"],
            "example": "Example: one bounded repair, then stop and ask for help if it still fails.",
        },
        "stops": {
            "answer": (
                f"{len(stop_items)} completion or safety stop{'s' if len(stop_items) != 1 else ''}."
                if stop_items else "No completion or safety stop is defined."
            ),
            "facts": [],
            "items": stop_items,
            "source_pointers": ["/terminals", "/nodes"],
            "example": "Example: finish after review passes; stop if repair is exhausted.",
        },
        "limits": {
            "answer": (
                f"{len(limits)} finite step limit{'s' if len(limits) != 1 else ''}."
                if limits else "No finite step limit is visible yet."
            ),
            "facts": limits,
            "items": [],
            "source_pointers": ["/nodes"],
            "example": "Example: one implementation attempt, two repair rounds, and a time limit.",
        },
    }


def _diagnostic_section(
    family: str,
    document: dict[str, object],
    diagnostic: dict[str, object],
) -> str:
    pointer = str(diagnostic.get("pointer") or "/")
    if family == "program":
        if pointer.startswith("/scope"):
            return "scope"
        if pointer.startswith("/bindings"):
            return "flow"
        if pointer.startswith("/phase_gates"):
            return "decisions" if pointer.endswith("/on_fail") else "quality"
        if pointer.startswith("/nudges"):
            return "recovery"
        if pointer.startswith("/stop_conditions"):
            return "stops"
        if pointer.startswith("/budgets") or pointer.startswith("/mode_ceiling") or pointer.startswith("/requested_capabilities"):
            return "limits"
        if pointer.startswith("/organization"):
            return "flow"
        return "flow"

    match = re.match(r"^/nodes/(\d+)(.*)$", pointer)
    if match:
        nodes = _objects(document.get("nodes"))
        try:
            node = nodes[int(match.group(1))]
        except (IndexError, ValueError):
            node = {}
        suffix = match.group(2)
        kind = str(node.get("type") or "")
        if any(token in suffix for token in ("max_", "timeout", "freshness", "quorum", "bytes", "tokens")):
            return "limits"
        if any(token in suffix for token in ("on_failure", "on_repair", "on_exhausted", "on_dissent", "on_quorum_lost")):
            return "recovery"
        if kind in QUALITY_STEP_TYPES:
            return "quality"
        if kind in DECISION_STEP_TYPES:
            return "decisions"
        if kind == "loop":
            return "recovery"
        return "flow"
    if pointer.startswith("/parameters") or pointer.startswith("/defaults"):
        return "scope"
    if pointer.startswith("/terminals"):
        return "stops"
    if pointer.startswith("/layout"):
        return "flow"
    return "flow"


def _affected_behavior(section_id: str) -> str:
    return {
        "scope": "The plan cannot determine which work is inside this delivery.",
        "flow": "The route and order of work cannot be checked safely.",
        "quality": "The plan cannot determine when work has passed review.",
        "decisions": "A required choice or its outcome is incomplete.",
        "recovery": "Failed work has no safe repair or escalation route.",
        "stops": "The delivery does not have a complete finish or safety stop.",
        "limits": "The delivery is missing a finite, internally consistent limit.",
    }[section_id]


def _correction(diagnostic: dict[str, object], section_id: str) -> str:
    code = str(diagnostic.get("code") or "")
    fixed = {
        "missing-bindings": "Add at least one work route that covers the delivery scope.",
        "dangling-workflow-reference": "Choose a saved work flow that is available in this repository.",
        "dangling-role-reference": "Choose a team or review owner available to this delivery.",
        "dangling-rubric-reference": "Choose saved review criteria available to this delivery.",
        "scope-project-missing": "Choose one existing roadmap project.",
        "empty-scope": "Include at least one existing story in the delivery scope.",
        "missing-nodes": "Add at least one bounded work step.",
        "unhandled-terminal": "Give every work outcome an explicit next step or finish.",
        "dangling-terminal": "Choose a declared finish for this outcome.",
        "workflow-cycle": "Remove the open-ended cycle; use one bounded repair route when repetition is required.",
        "unknown-key": "Open Technical details to inspect the unsupported field. It remains in the source and cannot be saved silently.",
    }
    if code in fixed:
        return fixed[code]
    remediation = _plain(diagnostic.get("remediation"))
    if remediation:
        return remediation[0].upper() + remediation[1:] + ("" if remediation.endswith(".") else ".")
    return {
        "scope": "Complete the delivery scope.",
        "flow": "Complete the affected work route.",
        "quality": "Complete the affected quality or review point.",
        "decisions": "Complete the affected decision point.",
        "recovery": "Add a safe repair or escalation route.",
        "stops": "Add an explicit completion or safety stop.",
        "limits": "Provide a finite valid limit.",
    }[section_id]


def build_delivery_plan_authoring(
    family: str,
    document: object,
    validation: object,
    graph: object,
    round_trip: object,
) -> dict[str, object]:
    """Project one exact Studio document into ordered delivery decisions."""
    if family not in {"program", "workflow", "organization"}:
        raise ValueError(f"unsupported Program Studio family: {family}")
    raw = document if isinstance(document, dict) else {}
    validation_doc = validation if isinstance(validation, dict) else {}
    graph_doc = graph if isinstance(graph, dict) else {}
    round_trip_doc = round_trip if isinstance(round_trip, dict) else {}
    diagnostics = _objects(validation_doc.get("diagnostics"))
    applicable = family in {"program", "workflow"}

    if family == "program":
        section_values = _program_sections(raw, graph_doc)
        object_label = "delivery plan"
    elif family == "workflow":
        section_values = _workflow_sections(raw, graph_doc)
        object_label = "work flow"
    else:
        section_values = {
            section_id: {
                "answer": "Team and review authoring is available in its dedicated design view.",
                "facts": [],
                "items": [],
                "source_pointers": ["/"],
                "example": "",
            }
            for section_id in SECTION_ORDER
        }
        object_label = "team and review design"

    corrections: list[dict[str, object]] = []
    for diagnostic in diagnostics:
        section_id = _diagnostic_section(family, raw, diagnostic)
        target = diagnostic.get("target")
        target = target if isinstance(target, dict) else {}
        corrections.append({
            "section_id": section_id,
            "decision": SECTION_META[section_id][0],
            "affected_behavior": _affected_behavior(section_id),
            "correction": _correction(diagnostic, section_id),
            "target": {
                "pointer": str(target.get("pointer") or diagnostic.get("pointer") or "/"),
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

    counts = {section_id: 0 for section_id in SECTION_ORDER}
    for item in corrections:
        counts[str(item["section_id"])] += 1

    sections = []
    for index, section_id in enumerate(SECTION_ORDER, start=1):
        label, question, guidance = SECTION_META[section_id]
        value = section_values[section_id]
        sections.append({
            "id": section_id,
            "step": index,
            "label": label,
            "question": question,
            "guidance": guidance,
            "answer": value["answer"],
            "facts": _copy(value["facts"]),
            "items": _copy(value["items"]),
            "source_pointers": list(value["source_pointers"]),
            "example": value["example"],
            "status": "needs-attention" if counts[section_id] else "ready",
            "correction_count": counts[section_id],
        })

    unknown = [
        str(item.get("pointer") or "/")
        for item in diagnostics
        if item.get("code") == "unknown-key"
    ]
    valid = bool(validation_doc.get("valid"))
    return {
        "kind": DELIVERY_PLAN_AUTHORING_KIND,
        "schema_version": DELIVERY_PLAN_AUTHORING_SCHEMA_VERSION,
        "family": family,
        "applicable": applicable,
        "object_label": object_label,
        "name": raw.get("slug"),
        "title": raw.get("title") or raw.get("slug") or object_label.title(),
        "status": "ready-to-review" if valid else "needs-attention",
        "summary": (
            f"This {object_label} answers all seven delivery decisions and is ready to review."
            if valid else
            f"This {object_label} needs {len(corrections)} correction"
            f"{'s' if len(corrections) != 1 else ''} before it can be saved."
        ),
        "sections": sections,
        "corrections": corrections,
        "review_before_save": {
            "scope": section_values["scope"]["answer"],
            "flow": section_values["flow"]["answer"],
            "quality": section_values["quality"]["answer"],
            "decisions": section_values["decisions"]["answer"],
            "recovery": section_values["recovery"]["answer"],
            "stops": section_values["stops"]["answer"],
            "limits": section_values["limits"]["answer"],
        },
        "review_sections": [
            {
                "id": section_id,
                "label": SECTION_META[section_id][0],
                "answer": section_values[section_id]["answer"],
                "status": (
                    "needs-attention"
                    if counts[section_id] else "ready"
                ),
            }
            for section_id in SECTION_ORDER
        ],
        "examples": [
            {
                "id": "simple",
                "label": "Simple delivery",
                "summary": "Scope the work, do it once, review it, then finish or stop.",
            },
            {
                "id": "repair",
                "label": "Delivery with repair",
                "summary": "Add one finite repair route before asking the plan owner for help.",
            },
            {
                "id": "advanced",
                "label": "Detailed governed delivery",
                "summary": "Keep nested flows, bounded repetition, discussion, and exact conditions in Technical details.",
            },
        ],
        "advanced_details": {
            "label": "Technical details",
            "hierarchical_workflows": bool(graph_doc.get("features", {}).get("nested_subflows"))
            if isinstance(graph_doc.get("features"), dict) else False,
            "bounded_loops": bool(graph_doc.get("features", {}).get("bounded_loops"))
            if isinstance(graph_doc.get("features"), dict) else False,
            "debate_cells": bool(graph_doc.get("features", {}).get("debates"))
            if isinstance(graph_doc.get("features"), dict) else False,
            "exact_conditions_editable": True,
            "graph_editable": True,
            "json_import_export": True,
            "source_document_preserved": True,
            "round_trip_lossless": bool(round_trip_doc.get("lossless")),
            "semantic_identity_preserved": bool(round_trip_doc.get("semantic_hash_preserved")),
            "layout_identity_preserved": bool(round_trip_doc.get("layout_hash_preserved")),
        },
        "edit_safety": {
            "targeted_edits_preserve_unedited_fields": True,
            "unknown_fields": unknown,
            "unknown_fields_preserved": bool(unknown),
            "invalid_save_refused": True,
            "exact_export_available": True,
        },
        "source_models": [
            "delivery-workbench-program-studio-document",
            "delivery-workbench-program-studio-graph",
            "delivery-workbench-program-studio-round-trip",
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
