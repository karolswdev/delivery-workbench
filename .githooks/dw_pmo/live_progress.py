"""Plain-language live delivery progress over canonical run facts.

This module does not schedule, dispatch, recover, decide, or mutate.  The
bounded-run and program surfaces pass in facts that their authoritative
replayers and conductors already derived.  These builders only group those
facts around seven operator questions and retain exact identities in a
technical-details section.
"""

from __future__ import annotations

import re

from .test_baseline import build_failure_projection


LIVE_PROGRESS_KIND = "delivery-workbench-live-progress"
LIVE_PROGRESS_SCHEMA_VERSION = 1

QUESTION_ORDER = (
    "delivery",
    "team",
    "passed",
    "blocked",
    "decision",
    "remaining-change-spend",
    "next",
)

_TERMINAL_COMPLETE = {"complete", "succeeded", "awaiting-certification"}
_TERMINAL_STOPPED = {
    "paused", "revoked", "cancelled", "expired", "exhausted", "advisory",
}
_REVIEW_ACTIONS = {
    "check", "verdict", "story-verification", "verdict-issuance",
    "architecture-boundary", "architecture-gate", "architect-verdict",
    "architect-verdict-issuance", "meta-verdict", "meta-verdict-issuance",
    "council-decision", "debate-judgment",
}
_MECHANICAL_ACTIONS = {"check", "story-verification"}
_REPAIR_ACTIONS = {"repair", "retry", "rework"}

_BUDGET_LABELS = {
    "max_phases": ("phases", "phases"),
    "max_stories": ("work items", "items"),
    "max_child_runs": ("bounded child deliveries", "deliveries"),
    "max_concurrency": ("work at once", "items"),
    "max_agent_starts": ("work starts", "starts"),
    "max_provider_starts": ("provider starts", "starts"),
    "max_model_starts": ("model starts", "starts"),
    "max_check_starts": ("check starts", "starts"),
    "max_loop_rounds": ("repeated work rounds", "rounds"),
    "max_debate_rounds": ("discussion rounds", "rounds"),
    "max_councils": ("governed discussions", "discussions"),
    "max_repairs_per_story": ("repairs per work item", "rounds"),
    "max_verdicts": ("review judgments", "judgments"),
    "max_obligations": ("recorded follow-ups", "follow-ups"),
    "max_obligation_materializations": ("materialized follow-ups", "follow-ups"),
    "max_obligation_dispositions": ("resolved follow-ups", "follow-ups"),
    "max_integrations": ("integrations", "integrations"),
    "max_commits": ("commits", "commits"),
    "max_pushes": ("pushes", "pushes"),
    "max_artifact_bytes": ("saved output", "bytes"),
    "max_tokens": ("model tokens", "tokens"),
    "max_observed_cost_microunits": (
        "observed cost", "micro-units",
    ),
    "max_wall_seconds": ("elapsed time", "seconds"),
    "max_nudges": ("follow-up signals", "signals"),
    "max_actions": ("delivery actions", "actions"),
    "max_claims": ("work claims", "claims"),
    "max_driver_calls": ("worker calls", "calls"),
    "max_receipts": ("recorded outcomes", "outcomes"),
    "max_repairs": ("repair rounds", "rounds"),
    "max_review_rounds": ("review rounds", "rounds"),
    "max_external_calls": ("external calls", "calls"),
}
_PRIMARY_BUDGETS = {
    "max_concurrency", "max_stories", "max_agent_starts",
    "max_check_starts", "max_repairs_per_story", "max_pushes",
    "max_artifact_bytes", "max_tokens", "max_observed_cost_microunits",
    "max_wall_seconds", "max_nudges",
}


def _objects(value: object) -> list[dict[str, object]]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, dict)]


def _strings(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value if isinstance(item, str)]


def _words(value: object) -> str:
    text = re.sub(r"[_./:-]+", " ", str(value or "")).strip()
    return " ".join(part for part in text.split() if part)


def _title(value: object, fallback: str = "Delivery work") -> str:
    text = _words(value)
    return text[:1].upper() + text[1:] if text else fallback


def _sentence(value: object, fallback: str = "") -> str:
    text = " ".join(str(value or fallback).split()).strip()
    if not text:
        return ""
    return text[:1].upper() + text[1:] + (
        "" if text.endswith((".", "!", "?")) else "."
    )


def _budget_rows(budgets: object) -> list[dict[str, object]]:
    if not isinstance(budgets, dict):
        return []
    rows: list[dict[str, object]] = []
    for name, raw in budgets.items():
        if not isinstance(raw, dict):
            continue
        used_raw = raw.get("used")
        limit_raw = raw.get("limit")
        remaining_raw = raw.get("remaining")
        used = int(used_raw) if used_raw is not None else None
        limit = int(limit_raw) if limit_raw is not None else None
        remaining = (
            int(remaining_raw) if remaining_raw is not None
            else max(0, limit - used)
            if limit is not None and used is not None else None
        )
        label, unit = _BUDGET_LABELS.get(
            str(name), (_words(str(name).removeprefix("max_")), "units")
        )
        rows.append({
            "id": str(name),
            "label": label,
            "used": used,
            "limit": limit,
            "remaining": remaining,
            "unit": unit,
            "status": (
                "unknown" if used is None or remaining is None
                else "none-left" if remaining <= 0 else "available"
            ),
            "primary": str(name) in _PRIMARY_BUDGETS,
        })
    return rows


def _answer(
    answer_id: str,
    question: str,
    answer: str,
    status: str,
    source_model: str,
    source_path: str,
) -> dict[str, object]:
    return {
        "id": answer_id,
        "question": question,
        "answer": answer,
        "status": status,
        "source": {"model": source_model, "path": source_path},
    }


def _status(
    group: str,
    label: str,
    exact_state: str,
    meaning: str,
) -> dict[str, object]:
    return {
        "group": group,
        "label": label,
        "exact_state": exact_state,
        "meaning": meaning,
    }


def _run_node_group(node: dict[str, object]) -> str:
    exact = str(node.get("state") or "waiting")
    node_type = str(node.get("type") or "")
    repair = (
        node.get("activation") == "failure"
        or "repair" in str(node.get("role") or "").lower()
        or "repair" in str(node.get("id") or "").lower()
    )
    if exact == "succeeded":
        return "complete"
    if repair and exact in {"active", "eligible", "routing", "failed"}:
        return "repair"
    if node_type in {"check", "approval"} and exact in {
        "active", "eligible", "awaiting-approval",
    }:
        return "review"
    if exact == "active":
        return "active"
    if exact == "blocked" and node.get("blocked_reason") == "dependencies":
        return "waiting"
    if exact in {"failed", "blocked", "routing"}:
        return "blocked"
    return "waiting"


def _run_status(
    projection: dict[str, object],
    nodes: list[dict[str, object]],
    decision: dict[str, object],
) -> dict[str, object]:
    exact = str(projection.get("state") or "unknown")
    scheduled = _objects(decision.get("scheduled"))
    active = _objects(projection.get("active_claims"))
    lost = any(
        isinstance(item.get("last_receipt"), dict)
        and item["last_receipt"].get("state") == "lost"  # type: ignore[index]
        for item in active
    )
    if lost:
        return _status(
            "recovering", "Recovering", exact,
            "Recorded work is being reconciled before anything can be repeated.",
        )
    if exact in _TERMINAL_COMPLETE:
        label = "Ready for final review" if exact == "awaiting-certification" else "Complete"
        return _status(
            "complete", label, exact,
            "All work in this bounded delivery has reached its saved end state.",
        )
    if exact in _TERMINAL_STOPPED:
        return _status(
            "stopped", _title(exact), exact,
            "No delivery work advances while this saved stop state remains.",
        )
    if exact == "blocked":
        return _status(
            "blocked", "Blocked", exact,
            "The saved delivery rules do not allow more work to start.",
        )
    if exact == "awaiting-approval":
        return _status(
            "review", "Decision needed", exact,
            "A named delivery decision is required before work can continue.",
        )
    active_nodes = {
        str(item.get("node_id")) for item in active
    }
    active_groups = [
        _run_node_group(node)
        for node in nodes
        if str(node.get("id")) in active_nodes
    ]
    if "repair" in active_groups:
        return _status(
            "repair", "Repair in progress", exact,
            "A saved review outcome routed the work through repair.",
        )
    if "review" in active_groups:
        return _status(
            "review", "Review in progress", exact,
            "Checks or review are currently active.",
        )
    if active:
        return _status(
            "active", "Work in progress", exact,
            "One or more recorded work items are active.",
        )
    if (
        _objects(decision.get("action_needed"))
        or _objects(decision.get("resolution_needed"))
    ):
        return _status(
            "repair", "Repair outcome ready", exact,
            "A saved failure route is recording or applying its repair outcome.",
        )
    scheduled_ids = {
        str(item.get("node_id")) for item in scheduled
    }
    scheduled_groups = [
        _run_node_group(node)
        for node in nodes
        if str(node.get("id")) in scheduled_ids
    ]
    if "repair" in scheduled_groups:
        return _status(
            "repair", "Repair ready", exact,
            "The saved failure route identifies repair as the next work.",
        )
    if "review" in scheduled_groups:
        return _status(
            "review", "Review ready", exact,
            "The saved work order identifies review as the next step.",
        )
    if scheduled:
        return _status(
            "waiting", "Ready for the next work", exact,
            "The next work is known and has not started yet.",
        )
    return _status(
        "waiting", "Waiting", exact,
        "No work is active and no different next action has been selected.",
    )


def _run_next_step(
    projection: dict[str, object],
    decision: dict[str, object],
    node_by_id: dict[str, dict[str, object]],
) -> dict[str, object]:
    requests = _objects(projection.get("outstanding_requests"))
    if requests:
        request = requests[0]
        target = str(
            request.get("origin_node")
            or request.get("checkpoint")
            or request.get("origin")
            or "delivery decision"
        )
        return {
            "kind": "decision",
            "label": f"Decide {_words(target)}",
            "detail": "Work waits for the recorded decision and its allowed response.",
            "target": target,
            "action": None,
            "canonical": True,
            "source": {
                "model": "delivery-workbench-run",
                "path": "/outstanding_requests/0",
            },
        }
    active = _objects(projection.get("active_claims"))
    if active:
        item = active[0]
        target = str(item.get("node_id") or "active work")
        return {
            "kind": "wait",
            "label": f"Let {_words(target)} finish",
            "detail": "The recorded active attempt must finish or be reconciled before another step is chosen.",
            "target": target,
            "action": None,
            "canonical": True,
            "source": {
                "model": "delivery-workbench-run",
                "path": "/active_claims/0",
            },
        }
    exact = str(projection.get("state") or "unknown")
    if exact in _TERMINAL_COMPLETE:
        detail = (
            "The bounded work is ready for separate final inspection."
            if exact == "awaiting-certification"
            else "This bounded delivery has no further work step."
        )
        return {
            "kind": "complete",
            "label": "No more bounded work",
            "detail": detail,
            "target": None,
            "action": None,
            "canonical": True,
            "source": {
                "model": "delivery-workbench-run",
                "path": "/state",
            },
        }
    if exact in _TERMINAL_STOPPED or exact == "blocked":
        return {
            "kind": "stopped",
            "label": "No work advances",
            "detail": f"The saved delivery state is {_words(exact)}.",
            "target": None,
            "action": None,
            "canonical": True,
            "source": {
                "model": "delivery-workbench-run",
                "path": "/state",
            },
        }
    scheduled = _objects(decision.get("scheduled"))
    if scheduled:
        item = scheduled[0]
        target = str(item.get("node_id") or "")
        node = node_by_id.get(target, {})
        kind = str(item.get("kind") or "claim")
        if kind == "checkpoint":
            label = f"Ask for {_words(target)} review"
            step_kind = "decision"
        elif _run_node_group(node) == "repair":
            label = f"Start {_words(target)} repair"
            step_kind = "repair"
        elif str(node.get("type")) == "check":
            label = f"Run {_words(target)} check"
            step_kind = "review"
        else:
            label = f"Start {_words(target)}"
            step_kind = "work"
        return {
            "kind": step_kind,
            "label": label,
            "detail": "This is the first step selected by the saved work order.",
            "target": target,
            "action": "tick",
            "canonical": True,
            "source": {
                "model": "delivery-workbench-conductor-decision",
                "path": "/scheduled/0",
            },
        }
    action_needed = _objects(decision.get("action_needed"))
    if action_needed:
        target = str(action_needed[0].get("node_id") or "failed work")
        return {
            "kind": "repair",
            "label": f"Apply the saved outcome for {_words(target)}",
            "detail": "The recorded result must follow its saved repair or stop route.",
            "target": target,
            "action": "tick",
            "canonical": True,
            "source": {
                "model": "delivery-workbench-conductor-decision",
                "path": "/action_needed/0",
            },
        }
    resolution_needed = _objects(decision.get("resolution_needed"))
    if resolution_needed:
        target = str(resolution_needed[0].get("target") or "repair")
        return {
            "kind": "repair",
            "label": f"Record the outcome of {_words(target)}",
            "detail": "The saved failure route is waiting for its recorded repair outcome.",
            "target": target,
            "action": "tick",
            "canonical": True,
            "source": {
                "model": "delivery-workbench-conductor-decision",
                "path": "/resolution_needed/0",
            },
        }
    if bool(decision.get("terminal_needed")):
        return {
            "kind": "complete",
            "label": "Record the bounded delivery handoff",
            "detail": "The saved work order has no unfinished success work.",
            "target": None,
            "action": "tick",
            "canonical": True,
            "source": {
                "model": "delivery-workbench-conductor-decision",
                "path": "/terminal_needed",
            },
        }
    return {
        "kind": "wait",
        "label": "Wait for a recorded state change",
        "detail": "No additional step is selected at this saved state.",
        "target": None,
        "action": None,
        "canonical": True,
        "source": {
            "model": "delivery-workbench-conductor-decision",
            "path": "/scheduled",
        },
    }


def build_run_live_progress(
    projection: dict[str, object],
    decision: dict[str, object],
    graph_nodes: list[dict[str, object]],
    artifacts: list[dict[str, object]],
    events: list[dict[str, object]],
) -> dict[str, object]:
    """Group one bounded run without deriving any new execution choice."""
    nodes = [dict(item) for item in graph_nodes]
    node_by_id = {str(item.get("id")): item for item in nodes}
    scheduled = _objects(decision.get("scheduled"))
    status = _run_status(projection, nodes, decision)
    groups = {
        name: [
            {
                "title": _title(item.get("id")),
                "summary": _sentence(
                    item.get("blocked_reason"),
                    f"{_title(item.get('type'))} is {_words(item.get('state'))}",
                ),
                "attempt": int(item.get("attempt", 0)),
                "technical_ref": str(item.get("id") or ""),
                "exact_state": str(item.get("state") or "waiting"),
            }
            for item in nodes
            if _run_node_group(item) == name
        ]
        for name in (
            "active", "waiting", "review", "repair", "blocked", "complete",
        )
    }
    completed = groups["complete"]
    failed_claims = [
        item
        for item in _objects(projection.get("completed_claims"))
        if str(item.get("outcome")) != "succeeded"
    ]
    check_nodes = [
        item for item in nodes if str(item.get("type")) == "check"
    ]
    approval_nodes = [
        item for item in nodes if str(item.get("type")) == "approval"
    ]
    repair_nodes = [
        item for item in nodes
        if item.get("activation") == "failure"
        or "repair" in str(item.get("role") or "").lower()
        or "repair" in str(item.get("id") or "").lower()
    ]
    passed = [
        _title(item.get("id"))
        for item in nodes
        if str(item.get("state")) == "succeeded"
    ]
    blocked = groups["blocked"]
    requests = _objects(projection.get("outstanding_requests"))
    next_step = _run_next_step(projection, decision, node_by_id)
    owner_roles = list(dict.fromkeys(
        _title(item.get("role"))
        for item in nodes
        if str(item.get("type")) == "agent" and item.get("role")
    ))
    reviewer_roles = list(dict.fromkeys(
        _title(item.get("role") or item.get("id"))
        for item in nodes
        if str(item.get("type")) in {"check", "approval"}
    ))
    budgets = _budget_rows(_usage_budget_overlay(
        projection.get("budgets"), _objects(projection.get("node_receipts"))
    ))
    capabilities = [_words(item) for item in _strings(projection.get("capabilities"))]
    exclusions = [_words(item) for item in _strings(
        projection.get("permanent_exclusions")
    )]
    story = projection.get("story")
    story_doc = story if isinstance(story, dict) else {}
    story_id = str(story_doc.get("id") or "bounded delivery")
    story_title = str(story_doc.get("title") or story_id)
    team_answer = (
        f"Work: {', '.join(owner_roles)}. Review: {', '.join(reviewer_roles)}."
        if owner_roles or reviewer_roles
        else "No doing or reviewing responsibility is named for this bounded work."
    )
    passed_answer = (
        f"Passed: {', '.join(passed)}."
        if passed
        else "No declared work item has passed yet."
    )
    blocked_answer = (
        f"Blocked: {', '.join(item['title'] for item in blocked)}."
        if blocked
        else "No declared work item is blocked."
    )
    decision_answer = (
        f"A decision is needed for {_words(requests[0].get('origin_node') or requests[0].get('origin'))}."
        if requests
        else "No person needs to decide anything right now."
    )
    allowed = ", ".join(capabilities) if capabilities else "no additional change types"
    remaining_summary = "; ".join(
        f"{item['remaining']} {item['label']}"
        for item in budgets
    ) or "no counted execution limit"
    limits_answer = (
        f"It may still use {allowed}. Remaining limits: {remaining_summary}. "
        "Money cost is not recorded by this delivery."
    )
    activity = [
        {
            "id": f"work-{index + 1}",
            "title": _title(node.get("id")),
            "status": _run_node_group(node),
            "summary": (
                f"Passed on attempt {node.get('attempt')}."
                if node.get("state") == "succeeded"
                else _sentence(
                    node.get("blocked_reason"),
                    f"{_title(node.get('type'))} is {_words(node.get('state'))}",
                )
            ),
            "outcomes": [
                str(item.get("outcome"))
                for item in _objects(projection.get("completed_claims"))
                if str(item.get("node_id")) == str(node.get("id"))
            ],
            "technical_refs": [str(node.get("id") or "")],
        }
        for index, node in enumerate(nodes)
        if str(node.get("state")) != "dormant"
        or node.get("activation") != "failure"
    ]
    active_claims = _objects(projection.get("active_claims"))
    recovering = status["group"] == "recovering"
    return {
        "kind": LIVE_PROGRESS_KIND,
        "schema_version": LIVE_PROGRESS_SCHEMA_VERSION,
        "context": "bounded-run",
        "title": story_title,
        "subtitle": f"{story_id} · bounded delivery",
        "status": status,
        "answers": [
            _answer(
                "delivery", "What are we delivering?",
                f"{story_id}: {story_title}.", "known",
                "delivery-workbench-run", "/story",
            ),
            _answer(
                "team", "Who is doing and reviewing it?", team_answer,
                "known" if owner_roles or reviewer_roles else "not-declared",
                "delivery-workbench-run-view", "/graph/nodes",
            ),
            _answer(
                "passed", "What passed?", passed_answer,
                "passed" if passed else "none-yet",
                "delivery-workbench-conductor-decision", "/node_states",
            ),
            _answer(
                "blocked", "What is blocked?", blocked_answer,
                "blocked" if blocked else "clear",
                "delivery-workbench-conductor-decision", "/blocked",
            ),
            _answer(
                "decision", "Who needs to decide?", decision_answer,
                "needed" if requests else "not-needed",
                "delivery-workbench-run", "/outstanding_requests",
            ),
            _answer(
                "remaining-change-spend",
                "What may delivery still change or spend?",
                limits_answer, "bounded",
                "delivery-workbench-run", "/capabilities",
            ),
            _answer(
                "next", "What happens next?",
                f"{next_step['label']}. {next_step['detail']}",
                str(next_step["kind"]),
                str(next_step["source"]["model"]),  # type: ignore[index]
                str(next_step["source"]["path"]),  # type: ignore[index]
            ),
        ],
        "delivery": {
            "work_id": story_id,
            "title": story_title,
            "project": projection.get("project"),
            "scope": "One bounded work item and its declared work order.",
        },
        "progress": {
            "basis": "declared-work-items",
            "known_total": len(nodes),
            "completed": len(completed),
            "percent": round(100 * len(completed) / len(nodes)) if nodes else 0,
            "groups": groups,
        },
        "team": {
            "owners": [
                {"name": item, "assignment": "responsibility-only"}
                for item in owner_roles
            ],
            "reviewers": [
                {"name": item, "assignment": "declared-review"}
                for item in reviewer_roles
            ],
            "summary": team_answer,
            "identity_note": (
                "This bounded work names responsibilities, not a person, until an active work record names the execution."
            ),
        },
        "review": {
            "mechanical": [
                {
                    "title": _title(item.get("id")),
                    "status": _run_node_group(item),
                    "exact_state": item.get("state"),
                }
                for item in check_nodes
            ],
            "agent_judgment": [],
            "dissent": [],
            "repair": [
                {
                    "title": _title(item.get("id")),
                    "status": _run_node_group(item),
                    "exact_state": item.get("state"),
                }
                for item in repair_nodes
            ],
            "final_governed_decisions": [
                {
                    "title": _title(item.get("id")),
                    "status": _run_node_group(item),
                    "exact_state": item.get("state"),
                }
                for item in approval_nodes
            ],
            "failed_evidence": [
                {
                    "work": _title(item.get("node_id")),
                    "outcome": item.get("outcome"),
                    "attempt": item.get("attempt"),
                }
                for item in failed_claims
            ],
        },
        "blocker": {
            "status": "blocked" if blocked else "clear",
            "summary": blocked_answer,
            "items": blocked,
        },
        "decision": {
            "status": "needed" if requests else "not-needed",
            "summary": decision_answer,
            "items": [
                {
                    "title": _title(
                        item.get("origin_node") or item.get("origin")
                    ),
                    "options": _strings(
                        item.get("response_schema", {}).get("decision")
                        if isinstance(item.get("response_schema"), dict)
                        else []
                    ),
                    "technical_ref": item.get("correlation_id"),
                }
                for item in requests
            ],
        },
        "limits": {
            "permission": {
                "status": (
                    "available"
                    if projection.get("dispatch_allowed")
                    else "not-currently-available"
                ),
                "may_still_use": capabilities,
                "will_not_use": exclusions,
                "summary": f"Allowed change types: {allowed}.",
            },
            "cost": {
                "status": "not-recorded",
                "summary": "Money cost is not recorded; counted execution limits are shown separately.",
            },
            "counts": budgets,
            "expires_at": projection.get("expires_at"),
        },
        "next_step": next_step,
        "activity": activity,
        "recovery": {
            "status": "recovering" if recovering else "verified",
            "summary": (
                "Recorded active work is being reconciled; it has not been declared lost or restarted."
                if recovering
                else "The saved history was checked before this view was built."
            ),
            "completed_work_preserved": len(
                _objects(projection.get("completed_claims"))
            ),
            "active_work_tracked": len(active_claims),
            "active_technical_refs": [
                str(item.get("claim_id")) for item in active_claims
            ],
            "duplicate_protection": (
                "A work identity and its recorded outcomes are replayed once; conflicting duplication stops replay."
            ),
            "stale_snapshot": (
                "If live updates disconnect, the last verified view remains visible and refresh checks the full saved history again."
            ),
        },
        "technical_details": {
            "run_id": projection.get("run_id"),
            "exact_state": projection.get("state"),
            "control_generation": projection.get("control_generation"),
            "ledger_head": projection.get("ledger_head"),
            "ledger_events": projection.get("ledger_events"),
            "scheduled": scheduled,
            "eligible": decision.get("eligible", []),
            "blocked": decision.get("blocked", []),
            "event_hashes": [
                item.get("event_hash") for item in events
            ],
            "artifact_hashes": [
                {
                    "name": item.get("name"),
                    "sha256": item.get("sha256"),
                }
                for item in artifacts
            ],
            "source_models": [
                "delivery-workbench-run",
                "delivery-workbench-conductor-decision",
                "delivery-workbench-run-event",
            ],
        },
        "starts_work": False,
        "writes_events": False,
        "selects_next_work": False,
        "decides_recovery": False,
        "grants_authority": False,
    }


def _program_status(
    authority: dict[str, object],
    frontier: dict[str, object],
    roles: list[dict[str, object]],
    deliveries: list[dict[str, object]],
) -> dict[str, object]:
    exact = str(authority.get("state") or "unknown")
    operational = str(frontier.get("state") or "unknown")
    if (
        operational == "reconciling"
        or any(item.get("state") == "reconciling" for item in deliveries)
    ):
        return _status(
            "recovering", "Recovering", exact,
            "Recorded work is being reconciled before a new action can start.",
        )
    if exact == "complete":
        return _status(
            "complete", "Complete", exact,
            "The entire saved delivery scope reached its completed state.",
        )
    if exact in _TERMINAL_STOPPED:
        return _status(
            "stopped", _title(exact), exact,
            "No delivery work advances while this saved stop state remains.",
        )
    if frontier.get("checkpoint") or exact == "checkpoint":
        return _status(
            "review", "Review checkpoint", exact,
            "The saved delivery is waiting at a declared review boundary.",
        )
    if operational == "stopped" or frontier.get("stop"):
        return _status(
            "blocked", "Blocked", exact,
            "A saved stop or unresolved blocker prevents the next work.",
        )
    if authority.get("outstanding_requests"):
        return _status(
            "review", "Decision needed", exact,
            "A recorded request needs a decision before delivery continues.",
        )
    active_roles = [
        item for item in roles if item.get("activity") == "active"
    ]
    if any(
        str(item.get("duty")) == "repairer"
        or "repair" in str(item.get("role") or "").lower()
        for item in active_roles
    ):
        return _status(
            "repair", "Repair in progress", exact,
            "A saved review outcome routed work through repair.",
        )
    if any(
        str(item.get("duty")) in {
            "verifier", "reviewer", "meta-verifier", "master-architect",
            "critic", "judge",
        }
        for item in active_roles
    ):
        return _status(
            "review", "Review in progress", exact,
            "Independent review or a governed decision is active.",
        )
    if authority.get("active_claims"):
        return _status(
            "active", "Work in progress", exact,
            "One or more recorded delivery activities are active.",
        )
    next_actions = _objects(frontier.get("next_actions"))
    if next_actions and str(next_actions[0].get("kind")) in _REVIEW_ACTIONS:
        return _status(
            "review", "Review ready", exact,
            "The next saved delivery action is a check or review.",
        )
    return _status(
        "waiting", "Ready for the next work", exact,
        "The saved delivery order identifies what may happen next.",
    )


def _program_next_step(
    authority: dict[str, object],
    frontier: dict[str, object],
    next_action: dict[str, object] | None,
    deliveries: list[dict[str, object]],
) -> dict[str, object]:
    delivery_recovery = next(
        (
            item for item in deliveries
            if item.get("state") == "reconciling"
        ),
        None,
    )
    if str(frontier.get("state")) == "reconciling" or delivery_recovery:
        target = (
            str(delivery_recovery.get("active_claim_ids", ["recorded work"])[0])
            if isinstance(delivery_recovery, dict)
            and delivery_recovery.get("active_claim_ids")
            else str(
                _objects(authority.get("active_claims"))[0].get("claim_id")
                if _objects(authority.get("active_claims"))
                else "recorded work"
            )
        )
        return {
            "kind": "recovering",
            "label": "Reconcile recorded work",
            "detail": "The existing work identity must resolve before a new action can start.",
            "target": target,
            "action": None,
            "canonical": True,
            "source": {
                "model": "delivery-workbench-program-frontier",
                "path": "/state",
            },
        }
    requests = _objects(authority.get("outstanding_requests"))
    if requests:
        request = requests[0]
        target = str(request.get("port") or request.get("claim_id") or "request")
        return {
            "kind": "decision",
            "label": f"Decide {_words(target)}",
            "detail": "Delivery waits for the recorded request to receive an allowed answer.",
            "target": target,
            "action": None,
            "canonical": True,
            "source": {
                "model": "delivery-workbench-program",
                "path": "/outstanding_requests/0",
            },
        }
    if frontier.get("checkpoint") or frontier.get("stop") == "checkpoint":
        lineage = frontier.get("lineage")
        lineage_doc = lineage if isinstance(lineage, dict) else {}
        target = str(
            lineage_doc.get("story")
            or lineage_doc.get("phase")
            or "delivery checkpoint"
        )
        return {
            "kind": "wait",
            "label": "Delivery is waiting at its saved checkpoint",
            "detail": "The declared review boundary has been reached; no different next action is selected here.",
            "target": target,
            "action": None,
            "canonical": True,
            "source": {
                "model": "delivery-workbench-program-frontier",
                "path": "/checkpoint",
            },
        }
    if isinstance(next_action, dict):
        kind = str(next_action.get("kind") or "work")
        target = str(
            next_action.get("story")
            or next_action.get("node")
            or next_action.get("role")
            or next_action.get("address")
            or kind
        )
        if kind in _REPAIR_ACTIONS or "repair" in kind:
            group = "repair"
        elif kind in _REVIEW_ACTIONS:
            group = "review"
        else:
            group = "work"
        return {
            "kind": group,
            "label": f"{_title(kind)}: {_words(target)}",
            "detail": "This is the first action in the saved delivery order.",
            "target": target,
            "action": dict(next_action),
            "canonical": True,
            "source": {
                "model": "delivery-workbench-program-frontier",
                "path": "/next_actions/0",
            },
        }
    exact = str(authority.get("state") or "unknown")
    if exact == "complete":
        return {
            "kind": "complete",
            "label": "No more delivery work",
            "detail": "The entire saved scope is complete.",
            "target": None,
            "action": None,
            "canonical": True,
            "source": {
                "model": "delivery-workbench-program",
                "path": "/state",
            },
        }
    if exact in _TERMINAL_STOPPED or frontier.get("stop"):
        return {
            "kind": "stopped",
            "label": "No work advances",
            "detail": (
                f"The saved delivery is stopped at {_words(frontier.get('stop') or exact)}."
            ),
            "target": None,
            "action": None,
            "canonical": True,
            "source": {
                "model": "delivery-workbench-program-frontier",
                "path": "/stop",
            },
        }
    return {
        "kind": "wait",
        "label": "Wait for a recorded state change",
        "detail": "No additional action is selected at this saved state.",
        "target": None,
        "action": None,
        "canonical": True,
        "source": {
            "model": "delivery-workbench-program-frontier",
            "path": "/next_actions",
        },
    }


def _usage_budget_overlay(
    budgets: object, receipts: list[dict[str, object]]
) -> object:
    if not isinstance(budgets, dict):
        return budgets
    usages = []
    latest_driver_receipts: dict[str, dict[str, object]] = {}
    for receipt in receipts:
        operation = receipt.get("operation")
        usage = operation.get("usage") if isinstance(operation, dict) else None
        if isinstance(usage, dict):
            usages.append(usage)
        elif receipt.get("executor") == "driver":
            latest_driver_receipts[str(receipt.get("claim_id") or "")] = receipt
    for receipt in latest_driver_receipts.values():
        total = receipt.get("total_tokens")
        cost = receipt.get("cost_microunits")
        usages.append({
            "total_tokens": total if isinstance(total, int) else None,
            "cost_microunits": cost if isinstance(cost, int) else None,
        })
    if not usages:
        return budgets
    result = {
        str(name): dict(raw) if isinstance(raw, dict) else raw
        for name, raw in budgets.items()
    }
    for counter, field in (
        ("max_tokens", "total_tokens"),
        ("max_observed_cost_microunits", "cost_microunits"),
    ):
        row = result.get(counter)
        if not isinstance(row, dict):
            continue
        values = [usage.get(field) for usage in usages]
        if any(value is None for value in values):
            row["used"] = None
            row["remaining"] = None
            row["measurement"] = "unknown"
        else:
            used = sum(int(value) for value in values)
            row["used"] = used
            limit = row.get("limit")
            row["remaining"] = (
                max(0, int(limit) - used) if limit is not None else None
            )
            row["measurement"] = "reported"
    return result


def build_program_live_progress(
    authority: dict[str, object],
    frontier: dict[str, object],
    *,
    selection: dict[str, object] | None,
    next_action: dict[str, object] | None,
    roles: list[dict[str, object]],
    receipts: list[dict[str, object]],
    artifacts: list[dict[str, object]],
    verdicts: list[dict[str, object]],
    decisions: list[dict[str, object]],
    dissent: list[dict[str, object]],
    gates: list[dict[str, object]],
    deliveries: list[dict[str, object]],
    integrations: list[dict[str, object]],
) -> dict[str, object]:
    """Group one program run without selecting or authorizing an action."""
    status = _program_status(authority, frontier, roles, deliveries)
    next_step = _program_next_step(
        authority, frontier, next_action, deliveries
    )
    scope = authority.get("scope")
    scope_doc = scope if isinstance(scope, dict) else {}
    scope_stories = _strings(scope_doc.get("story_ids"))
    scope_phases = [
        int(item) for item in scope_doc.get("phases", [])
        if isinstance(item, int) and not isinstance(item, bool)
    ] if isinstance(scope_doc.get("phases"), list) else []
    scope_completion = authority.get("scope_completion")
    completion_doc = (
        scope_completion if isinstance(scope_completion, dict) else {}
    )
    completed_stories = _strings(completion_doc.get("completed_stories"))
    completed_stories.extend(
        str(item.get("story"))
        for item in integrations
        if item.get("action_kind") == "story-complete" and item.get("story")
    )
    completed_stories = list(dict.fromkeys(completed_stories))
    selected_story = ""
    if isinstance(selection, dict):
        raw_story = selection.get("story")
        if isinstance(raw_story, dict):
            selected_story = str(raw_story.get("id") or "")
        else:
            selected_story = str(raw_story or "")
    progress_items = []
    for story in scope_stories:
        if story in completed_stories:
            group = "complete"
        elif story == selected_story:
            group = status["group"] if status["group"] in {
                "active", "review", "repair", "blocked", "recovering",
            } else "waiting"
        else:
            group = "waiting"
        progress_items.append({
            "title": _title(story),
            "status": group,
            "technical_ref": story,
        })
    owner_duties = {
        "implementer", "repairer", "researcher",
    }
    review_duties = {
        "verifier", "reviewer", "meta-verifier", "master-architect",
        "critic",
    }
    decision_duties = {"judge"}

    def team_member(item: dict[str, object]) -> dict[str, object]:
        return {
            "name": str(item.get("agent") or _title(item.get("role"))),
            "responsibility": _title(item.get("duty") or item.get("role")),
            "status": str(item.get("activity") or "waiting"),
            "technical_ref": item.get("address"),
        }

    owners = [
        team_member(item)
        for item in roles if str(item.get("duty")) in owner_duties
    ]
    reviewers = [
        team_member(item)
        for item in roles if str(item.get("duty")) in review_duties
    ]
    decision_owners = [
        team_member(item)
        for item in roles if str(item.get("duty")) in decision_duties
    ]
    blocking = _objects(authority.get("blocking_obligations"))
    requests = _objects(authority.get("outstanding_requests"))
    checkpoint = bool(
        frontier.get("checkpoint") or frontier.get("stop") == "checkpoint"
    )
    blocking_stop = bool(frontier.get("stop")) and not checkpoint
    passed_gates = [
        item for item in gates
        if str(item.get("result") or item.get("status")) in {
            "passed", "pass", "succeeded", "approved", "accepted",
        }
    ]
    passed_names = [
        _title(
            item.get("action_kind")
            or item.get("role")
            or item.get("address")
        )
        for item in passed_gates
    ]
    blocker_answer = (
        "Blocked by " + ", ".join(
            _title(item.get("statement") or item.get("id"))
            for item in blocking
        ) + "."
        if blocking
        else (
            f"Blocked at {_words(frontier.get('stop'))}."
            if blocking_stop
            else "No recorded blocker prevents the next delivery action."
        )
    )
    who = [item["name"] for item in decision_owners]
    decision_needed = bool(requests)
    decision_answer = (
        f"{', '.join(who) or 'The recorded decision owner'} must review the current request."
        if decision_needed
        else "No person needs to decide anything right now."
    )
    team_answer = (
        f"Work: {', '.join(str(item['name']) for item in owners) or 'not assigned'}. "
        f"Independent review: {', '.join(str(item['name']) for item in reviewers) or 'not assigned'}."
    )
    raw_failure_sets = next(
        (
            item["payload"]["test_failures"]
            for item in reversed(receipts)
            if isinstance(item.get("payload"), dict)
            and isinstance(item["payload"].get("test_failures"), dict)
        ),
        None,
    )
    failure_sets = (
        build_failure_projection(raw_failure_sets)
        if isinstance(raw_failure_sets, dict) else None
    )
    if isinstance(failure_sets, dict):
        introduced_count = int(failure_sets.get("introduced_count", 0))
        pre_existing_count = int(failure_sets.get("pre_existing_count", 0))
        if introduced_count:
            passed_answer = (
                f"{introduced_count} introduced test failure"
                f"{'s' if introduced_count != 1 else ''}; "
                f"{pre_existing_count} pre-existing."
            )
        elif pre_existing_count:
            passed_answer = (
                f"No introduced failures; {pre_existing_count} pre-existing "
                f"test failure{'s' if pre_existing_count != 1 else ''}."
            )
        else:
            passed_answer = "The declared test command has no failures."
    else:
        passed_answer = (
            f"Passed: {', '.join(passed_names)}."
            if passed_names
            else "No mechanical or judgment review outcome has passed yet."
        )
    budgets = _budget_rows(_usage_budget_overlay(
        authority.get("budgets"), receipts
    ))
    capabilities = [_words(item) for item in _strings(
        authority.get("capabilities")
    )]
    exclusions = [_words(item) for item in _strings(
        authority.get("permanent_exclusions")
    )]
    answer_budget_ids = {
        "max_stories", "max_agent_starts", "max_check_starts",
        "max_pushes", "max_tokens", "max_observed_cost_microunits",
        "max_wall_seconds",
    }
    remaining_summary = "; ".join(
        (
            f"unknown remaining {item['label']}"
            if item["remaining"] is None
            else f"{item['remaining']} {item['label']}"
        )
        for item in budgets
        if item["id"] in answer_budget_ids
    ) or "no counted execution limit"
    allowed = ", ".join(capabilities) if capabilities else "no additional change types"
    limits_answer = (
        f"It may still use {allowed}. Remaining limits: {remaining_summary}."
    )
    budget_by_id = {
        str(item["id"]): item for item in budgets
    }
    cost_parts = []
    token_cost = budget_by_id.get("max_tokens")
    if token_cost is not None:
        cost_parts.append(
            "Model token usage is unknown"
            if token_cost["used"] is None
            else (
                f"{token_cost['used']} of {token_cost['limit']} model tokens used; "
                f"{token_cost['remaining']} remain"
            )
        )
    observed_cost = budget_by_id.get("max_observed_cost_microunits")
    if observed_cost is not None:
        cost_parts.append(
            "Observed money cost is unknown"
            if observed_cost["used"] is None
            else (
                f"{observed_cost['used']} of {observed_cost['limit']} observed cost "
                f"micro-units used; {observed_cost['remaining']} remain"
            )
        )
    cost_summary = (
        ". ".join(cost_parts) + "."
        if cost_parts
        else "Money and token cost are not recorded by this delivery."
    )
    program = authority.get("program")
    program_doc = program if isinstance(program, dict) else {}
    program_title = str(
        program_doc.get("title")
        or program_doc.get("slug")
        or program
        or "Program delivery"
    )
    scope_summary = (
        f"{len(scope_stories)} work item{'s' if len(scope_stories) != 1 else ''}"
        + (
            f" across phase{'s' if len(scope_phases) != 1 else ''} "
            + ", ".join(str(item) for item in scope_phases)
            if scope_phases else ""
        )
    )
    activity_by_address: dict[str, dict[str, object]] = {}
    for index, item in enumerate(receipts):
        address = str(
            item.get("address")
            or item.get("workflow_address")
            or item.get("story")
            or item.get("action_kind")
            or f"activity-{index + 1}"
        )
        group = activity_by_address.setdefault(address, {
            "id": f"activity-{len(activity_by_address) + 1}",
            "title": _title(
                item.get("story") or item.get("role") or item.get("action_kind")
            ),
            "status": "complete",
            "summary": "",
            "outcomes": [],
            "technical_refs": [],
        })
        outcome = str(item.get("result") or "recorded")
        group["outcomes"].append(outcome)  # type: ignore[union-attr]
        group["technical_refs"].append(  # type: ignore[union-attr]
            str(item.get("action_id") or address)
        )
        group["summary"] = (
            f"{len(group['outcomes'])} related outcome"  # type: ignore[arg-type]
            f"{'s' if len(group['outcomes']) != 1 else ''}: "  # type: ignore[arg-type]
            + ", ".join(str(value) for value in group["outcomes"])  # type: ignore[union-attr]
            + "."
        )
    for item in _objects(authority.get("active_claims")):
        subject = item.get("subject")
        subject_doc = subject if isinstance(subject, dict) else {}
        address = str(subject_doc.get("id") or item.get("claim_id"))
        activity_by_address[address] = {
            "id": f"activity-{len(activity_by_address) + 1}",
            "title": _title(
                subject_doc.get("story")
                or subject_doc.get("role")
                or subject_doc.get("kind")
                or address
            ),
            "status": (
                "recovering"
                if status["group"] == "recovering"
                else "active"
            ),
            "summary": (
                "Recorded work is being reconciled."
                if status["group"] == "recovering"
                else "Recorded work is active."
            ),
            "outcomes": [],
            "technical_refs": [str(item.get("claim_id"))],
        }
    mechanical = [
        item for item in gates
        if str(item.get("action_kind")) in _MECHANICAL_ACTIONS
    ]
    judgment = [
        item for item in verdicts
        if str(item.get("action_kind")) not in _MECHANICAL_ACTIONS
    ]
    repair_receipts = [
        item for item in receipts
        if str(item.get("action_kind")) in _REPAIR_ACTIONS
        or "repair" in str(item.get("role") or "").lower()
    ]
    delivery_active_ids = [
        str(claim_id)
        for item in deliveries
        for claim_id in item.get("active_claim_ids", [])
        if isinstance(claim_id, str)
    ]
    completed_delivery_actions = sum(
        len(item.get("completed_action_ids", []))
        for item in deliveries
        if isinstance(item.get("completed_action_ids"), list)
    )
    recovering = status["group"] == "recovering"
    return {
        "kind": LIVE_PROGRESS_KIND,
        "schema_version": LIVE_PROGRESS_SCHEMA_VERSION,
        "context": "program",
        "title": program_title,
        "subtitle": f"{scope_summary} · ongoing delivery",
        "status": status,
        "answers": [
            _answer(
                "delivery", "What are we delivering?",
                f"{program_title}: {scope_summary}.", "known",
                "delivery-workbench-program", "/scope",
            ),
            _answer(
                "team", "Who is doing and reviewing it?", team_answer,
                "known" if owners or reviewers else "not-assigned",
                "delivery-workbench-program-view", "/organization/roles",
            ),
            _answer(
                "passed", "What passed?", passed_answer,
                "passed" if passed_names else "none-yet",
                "delivery-workbench-program-view", "/gates",
            ),
            _answer(
                "blocked", "What is blocked?", blocker_answer,
                "blocked" if blocking or blocking_stop else "clear",
                "delivery-workbench-program", "/blocking_obligations",
            ),
            _answer(
                "decision", "Who needs to decide?", decision_answer,
                "needed" if decision_needed else "not-needed",
                "delivery-workbench-program", "/outstanding_requests",
            ),
            _answer(
                "remaining-change-spend",
                "What may delivery still change or spend?",
                limits_answer, "bounded",
                "delivery-workbench-program", "/capabilities",
            ),
            _answer(
                "next", "What happens next?",
                f"{next_step['label']}. {next_step['detail']}",
                str(next_step["kind"]),
                str(next_step["source"]["model"]),  # type: ignore[index]
                str(next_step["source"]["path"]),  # type: ignore[index]
            ),
        ],
        "delivery": {
            "title": program_title,
            "scope": scope_summary,
            "story_ids": scope_stories,
            "phases": scope_phases,
            "current_story": selected_story or None,
        },
        "progress": {
            "basis": "granted-work-items",
            "known_total": len(scope_stories),
            "completed": len([
                item for item in scope_stories if item in completed_stories
            ]),
            "percent": (
                round(
                    100
                    * len([
                        item for item in scope_stories
                        if item in completed_stories
                    ])
                    / len(scope_stories)
                )
                if scope_stories else 0
            ),
            "items": progress_items,
        },
        "team": {
            "owners": owners,
            "reviewers": reviewers,
            "decision_owners": decision_owners,
            "summary": team_answer,
        },
        "review": {
            **({"test_failures": failure_sets} if isinstance(failure_sets, dict) else {}),
            "mechanical": [
                {
                    "title": _title(item.get("action_kind")),
                    "status": str(item.get("result") or "recorded"),
                    "technical_ref": item.get("action_id"),
                }
                for item in mechanical
            ],
            "agent_judgment": [
                {
                    "title": _title(
                        item.get("role") or item.get("action_kind")
                    ),
                    "status": str(item.get("result") or "recorded"),
                    "technical_ref": item.get("action_id"),
                }
                for item in judgment
            ],
            "dissent": [
                {
                    "title": _title(
                        item.get("role") or item.get("action_kind")
                    ),
                    "status": str(item.get("result") or "recorded"),
                    "technical_ref": item.get("action_id"),
                }
                for item in dissent
            ],
            "repair": [
                {
                    "title": _title(
                        item.get("role") or item.get("action_kind")
                    ),
                    "status": str(item.get("result") or "recorded"),
                    "technical_ref": item.get("action_id"),
                }
                for item in repair_receipts
            ],
            "final_governed_decisions": [
                {
                    "title": _title(
                        item.get("role") or item.get("action_kind")
                    ),
                    "status": str(item.get("result") or "recorded"),
                    "technical_ref": item.get("action_id"),
                }
                for item in decisions
            ],
        },
        "blocker": {
            "status": (
                "blocked" if blocking or blocking_stop else "clear"
            ),
            "summary": blocker_answer,
            "items": [
                {
                    "title": _title(item.get("statement") or item.get("id")),
                    "technical_ref": item.get("id"),
                }
                for item in blocking
            ],
        },
        "decision": {
            "status": "needed" if decision_needed else "not-needed",
            "summary": decision_answer,
            "owners": decision_owners,
            "items": [
                {
                    "title": _title(item.get("port") or item.get("claim_id")),
                    "technical_ref": item.get("claim_id"),
                }
                for item in requests
            ],
        },
        "limits": {
            "permission": {
                "status": (
                    "available"
                    if authority.get("future_claims_allowed")
                    else "not-currently-available"
                ),
                "may_still_use": capabilities,
                "will_not_use": exclusions,
                "summary": f"Allowed change types: {allowed}.",
            },
            "cost": {
                "status": "measured" if cost_parts else "not-recorded",
                "summary": cost_summary,
            },
            "counts": budgets,
            "expires_at": authority.get("expires_at"),
        },
        "next_step": next_step,
        "activity": list(activity_by_address.values()),
        "recovery": {
            "status": "recovering" if recovering else "verified",
            "summary": (
                "Recorded active work is being reconciled; it has not been declared lost or restarted."
                if recovering
                else "The saved history and delivery outcomes were checked before this view was built."
            ),
            "completed_work_preserved": len(
                _objects(authority.get("completed_claims"))
            ),
            "completed_delivery_actions_preserved": completed_delivery_actions,
            "active_work_tracked": len(
                _objects(authority.get("active_claims"))
            ) + len(delivery_active_ids),
            "active_technical_refs": [
                str(item.get("claim_id"))
                for item in _objects(authority.get("active_claims"))
            ] + delivery_active_ids,
            "duplicate_protection": (
                "Each delivery action has at most one accepted recorded outcome; replay refuses conflicting duplicates."
            ),
            "stale_snapshot": (
                "If live updates disconnect, the last verified view remains visible and refresh checks the full saved history again."
            ),
        },
        "technical_details": {
            "run_id": authority.get("run_id"),
            "exact_state": authority.get("state"),
            "operational_state": frontier.get("state"),
            "stop": frontier.get("stop"),
            "generation": authority.get("generation"),
            "ledger_head": authority.get("ledger_head"),
            "event_count": authority.get("event_count"),
            "next_actions": [next_action] if next_action is not None else [],
            "selected_next_action": next_action,
            "delivery_ids": [
                item.get("delivery_id") for item in deliveries
            ],
            "artifact_hashes": [
                {
                    "name": item.get("name"),
                    "hash": item.get("hash") or item.get("sha256"),
                }
                for item in artifacts
            ],
            "source_models": [
                "delivery-workbench-program",
                "delivery-workbench-program-frontier",
                "delivery-workbench-program-delivery-frontier",
                "delivery-workbench-program-event",
            ],
        },
        "starts_work": False,
        "writes_events": False,
        "selects_next_work": False,
        "decides_recovery": False,
        "grants_authority": False,
    }
