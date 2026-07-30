"""Plain-language bounded actions over canonical delivery facts.

The run and program surfaces pass their already-derived controls, requests,
limits, blockers, and receipts into this module.  The builders explain those
facts; they do not decide applicability, create response options, mint a
token, select work, spend permission, or write an event.
"""

from __future__ import annotations

import math
import re


BOUNDED_ACTIONS_KIND = "delivery-workbench-bounded-actions"
BOUNDED_ACTIONS_SCHEMA_VERSION = 1

_UNBOUNDED = {"unbounded", "unlimited", "infinite", "infinity", "∞"}
_COST_BUDGETS = {
    "max_tokens",
    "max_observed_cost_microunits",
    "max_wall_seconds",
    "max_artifact_bytes",
}
_CONTROL_RECEIPTS = {
    "run_paused": ("pause", "Delivery paused"),
    "run_resumed": ("resume", "Delivery resumed"),
    "run_revoked": ("revoke", "Delivery permission permanently stopped"),
    "run_cancelled": ("cancel", "Bounded delivery cancelled"),
    "request_decided": ("request", "Decision recorded"),
    "request_refused": ("request", "Decision response refused"),
    "node_claimed": ("tick", "Bounded work started"),
    "node_released": ("tick", "Bounded work outcome recorded"),
    "program_paused": ("pause", "Program paused"),
    "program_resumed": ("resume", "Program resumed"),
    "program_revoked": (
        "revoke", "Program permission permanently stopped",
    ),
    "program_cancelled": ("cancel", "Program cancelled"),
    "program_exhausted": ("limit", "Program stopped at a finite limit"),
    "claim_completed": ("tick", "Program work outcome recorded"),
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


def _bounded_text(value: object, fallback: str) -> str:
    text = " ".join(str(value or "").split()).strip()
    return text or fallback


def classify_measurement(
    kind: str,
    value: object = None,
    *,
    unit: str = "units",
    applicable: bool = True,
    unbounded: bool = False,
) -> dict[str, object]:
    """Classify one value without collapsing zero, unknown, or unbounded.

    ``applicable=False`` is an explicit not-applicable value.  ``None`` while
    applicable is unknown, never zero.  Unbounded must be explicit either via
    the flag or one of the recognized exact source spellings.
    """
    state = "unknown"
    normalized: int | float | None = None
    if not applicable:
        state = "not-applicable"
    elif unbounded or (
        isinstance(value, str) and value.strip().lower() in _UNBOUNDED
    ):
        state = "unbounded"
    elif (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(float(value))
    ):
        normalized = value
        state = "zero" if value == 0 else "finite"
    return {
        "kind": kind,
        "state": state,
        "value": normalized,
        "unit": unit,
    }


def _usage_item(
    item_id: str,
    label: str,
    category: str,
    unit: str,
    *,
    actual: object = None,
    limit: object = None,
    remaining: object = None,
    estimate: object = None,
    actual_applicable: bool = True,
    limit_applicable: bool = True,
    remaining_applicable: bool = True,
    estimate_applicable: bool = False,
    primary: bool = True,
) -> dict[str, object]:
    limit_unbounded = (
        isinstance(limit, str) and limit.strip().lower() in _UNBOUNDED
    )
    remaining_unbounded = limit_unbounded and remaining is None
    return {
        "id": item_id,
        "label": label,
        "category": category,
        "primary": primary,
        "measurements": {
            "limit": classify_measurement(
                "limit",
                limit,
                unit=unit,
                applicable=limit_applicable,
                unbounded=limit_unbounded,
            ),
            "estimate": classify_measurement(
                "estimate",
                estimate,
                unit=unit,
                applicable=estimate_applicable,
            ),
            "actual": classify_measurement(
                "actual",
                actual,
                unit=unit,
                applicable=actual_applicable,
            ),
            "remaining": classify_measurement(
                "remaining",
                remaining,
                unit=unit,
                applicable=remaining_applicable,
                unbounded=remaining_unbounded,
            ),
        },
    }


def _usage(
    budgets: object,
    live_progress: dict[str, object],
) -> dict[str, object]:
    rows = _objects((live_progress.get("limits") or {}).get("counts"))
    row_by_id = {str(item.get("id")): item for item in rows}
    items: list[dict[str, object]] = []
    if isinstance(budgets, dict):
        for item_id, raw in budgets.items():
            if not isinstance(raw, dict):
                continue
            display = row_by_id.get(str(item_id), {})
            label = str(display.get("label") or _words(item_id))
            unit = str(display.get("unit") or "units")
            category = (
                "measured-cost"
                if str(item_id) in _COST_BUDGETS
                else "permission-consumption"
            )
            items.append(_usage_item(
                str(item_id),
                label,
                category,
                unit,
                actual=raw.get("used"),
                limit=raw.get("limit"),
                remaining=raw.get("remaining"),
                primary=bool(display.get("primary", True)),
            ))

    progress = live_progress.get("progress")
    progress_doc = progress if isinstance(progress, dict) else {}
    known_total = progress_doc.get("known_total")
    completed = progress_doc.get("completed")
    progress_known = (
        isinstance(known_total, int)
        and not isinstance(known_total, bool)
        and isinstance(completed, int)
        and not isinstance(completed, bool)
    )
    items.insert(0, _usage_item(
        "declared-work-progress",
        "declared work",
        "progress",
        "work items",
        actual=completed if progress_known else None,
        limit=known_total if progress_known else None,
        remaining=(
            max(0, int(known_total) - int(completed))
            if progress_known else None
        ),
    ))
    if not any(item["id"] == "max_observed_cost_microunits" for item in items):
        items.append(_usage_item(
            "money-cost",
            "money cost",
            "measured-cost",
            "money units",
            actual=None,
            limit=None,
            remaining=None,
            actual_applicable=True,
            limit_applicable=False,
            remaining_applicable=False,
        ))
    return {
        "items": items,
        "legend": {
            "limit": "The maximum allowed by the exact permission.",
            "estimate": "A declared forecast, only when the source records one.",
            "actual": "Measured consumption recorded so far.",
            "remaining": "The exact finite limit minus measured use.",
            "zero": "Zero means none; it never means unbounded.",
            "unbounded": (
                "Unbounded appears only when the exact source explicitly says "
                "there is no finite ceiling."
            ),
            "unknown": "Unknown means the source does not record the value.",
            "not-applicable": "Not applicable means this delivery does not use that measure.",
        },
        "adds_incomparable_units": False,
    }


def build_refusal_explanation(
    happened: str,
    unchanged: str,
    *,
    effect_may_have_occurred: bool | None,
    safe_next: str,
    technical_evidence: dict[str, object] | None = None,
) -> dict[str, object]:
    return {
        "what_happened": _bounded_text(happened, "The action was refused."),
        "what_stayed_unchanged": _bounded_text(
            unchanged, "The saved delivery state stayed unchanged."
        ),
        "effect_may_have_occurred": effect_may_have_occurred,
        "effect_answer": (
            "yes"
            if effect_may_have_occurred is True
            else "no"
            if effect_may_have_occurred is False
            else "unknown"
        ),
        "safe_next_step": _bounded_text(
            safe_next, "Reload the saved state before choosing another action."
        ),
        "technical_evidence": technical_evidence or {},
    }


def _decision_effect(decision: str, *, context: str) -> tuple[str, str]:
    normalized = str(decision or "").strip().lower()
    boundary = (
        "program frontier"
        if context == "program"
        else "bounded delivery state"
    )
    if normalized in {"approve", "accept", "yes", "continue"}:
        return (
            "Records approval only for this exact outstanding request.",
            f"The canonical {boundary} is recalculated; only work it then permits may proceed.",
        )
    if normalized in {"reject", "deny", "no", "stop"}:
        return (
            "Records rejection only for this exact outstanding request.",
            f"Affected work stays stopped or follows the saved rejection route; permission is not revoked.",
        )
    return (
        "Records this exact closed response only for the named outstanding request.",
        f"The canonical {boundary} is recalculated from that saved response.",
    )


def build_response_guidance(
    *,
    context: str,
    affected_work: str,
    correlation_id: str,
    decisions: list[str],
) -> dict[str, object]:
    """Build transport-safe response guidance from one exact response set."""
    choices = []
    for decision in decisions:
        effect, after = _decision_effect(decision, context=context)
        choices.append({
            "decision": decision,
            "label": f"{_title(decision)} this request",
            "effect": effect,
            "after": after,
        })
    return {
        "affected_work": affected_work,
        "correlation_id": correlation_id,
        "choices": choices,
        "transport_role": "response-carrier",
        "transport_can_draft_response": True,
        "transport_grants_authority": False,
        "decisive_checks": [
            "the canonical local principal is authorized",
            "the exact request is still outstanding",
            "the response is in the request's closed response set",
            "the local preview token is fresh for the current ledger and generation",
            "the apply boundary accepts the same request and response",
        ],
        "safe_next_step": (
            "Send one listed response or leave the request pending; the local "
            "exact boundary must still accept it."
        ),
        "starts_work": False,
        "writes_events": False,
        "grants_authority": False,
    }


def _action_semantics(
    action: str,
    *,
    context: str,
    decision: str,
    next_step: dict[str, object],
) -> dict[str, object]:
    subject = "program" if context == "program" else "delivery"
    if action == "tick":
        repair = str(next_step.get("kind")) == "repair"
        return {
            "label": (
                "Retry the bounded repair"
                if repair
                else "Continue one reviewed step"
            ),
            "effect": (
                "Starts only the next repair attempt already selected by the "
                "saved delivery plan, within remaining permission and limits."
                if repair
                else "Starts at most the one next step already selected by the "
                "saved delivery state, within remaining permission and limits."
            ),
            "unchanged": (
                "It does not change retry policy, select different work, or "
                "broaden permission."
            ),
            "after": (
                "The resulting receipt is saved and the canonical next step is recalculated."
            ),
            "severity": "start",
            "permanent": False,
        }
    if action == "supervise":
        return {
            "label": "Continue within reviewed ceilings",
            "effect": (
                f"May start successive canonical {subject} steps only until the "
                "reviewed tick, time, checkpoint, stop, or terminal ceiling."
            ),
            "unchanged": (
                "It does not choose another workflow, expand scope, or raise a limit."
            ),
            "after": "An exact receipt and stop reason are shown for the bounded pass.",
            "severity": "start",
            "permanent": False,
        }
    if action == "pause":
        return {
            "label": f"Pause the {subject}",
            "effect": (
                f"Stops new {subject} work from starting while preserving "
                "completed work, current requests, remaining limits, and history."
            ),
            "unchanged": (
                "Pause is reversible; it does not revoke permission or erase prior effects."
            ),
            "after": "A separately reviewed resume is required before new work can start.",
            "severity": "caution",
            "permanent": False,
        }
    if action == "resume":
        return {
            "label": "Resume reviewed work",
            "effect": (
                "Rechecks the saved permission and current facts, then leaves "
                "the delivery eligible only for work its canonical state permits."
            ),
            "unchanged": (
                "Resume does not repeat completed work, expand scope, or start "
                "a step without its separate canonical control."
            ),
            "after": "The current next step is recalculated from the refreshed saved state.",
            "severity": "caution",
            "permanent": False,
        }
    if action == "revoke":
        return {
            "label": f"Permanently stop the {subject}",
            "effect": (
                f"Permanently prevents new {subject} work under this permission "
                "and expires any outstanding request bound to it."
            ),
            "unchanged": "Completed work and the exact history remain available for inspection.",
            "after": "This permission cannot resume; new authority would require a separate grant.",
            "severity": "danger",
            "permanent": True,
        }
    if action == "cancel":
        return {
            "label": f"Cancel and interrupt this bounded {subject}",
            "effect": (
                f"Permanently revokes this {subject} permission, marks it cancelled, "
                "expires its outstanding requests, and interrupts recorded active work within its bounded process boundary."
            ),
            "unchanged": (
                "Completed effects and exact history remain; cancellation does "
                "not certify, merge, release, or revoke any separate authority."
            ),
            "after": (
                "The cancelled delivery cannot resume. Any interruption is bounded "
                "to work recorded under this permission."
            ),
            "severity": "danger",
            "permanent": True,
        }
    if action == "request":
        effect, after = _decision_effect(decision, context=context)
        return {
            "label": f"{_title(decision)} this request",
            "effect": effect,
            "unchanged": (
                "No other request, permission ceiling, or completed work changes."
            ),
            "after": after,
            "severity": (
                "danger"
                if str(decision).lower() in {"reject", "deny", "no", "stop"}
                else "caution"
            ),
            "permanent": False,
        }
    if action == "retry":
        return {
            "label": "Retry is controlled by the delivery plan",
            "effect": (
                "No operator retry is available. Only an attempt already "
                "selected by the saved failure policy can run through continue."
            ),
            "unchanged": "Retry policy, attempts, permission, and delivery state stay unchanged.",
            "after": "Review the failed check and the saved repair route.",
            "severity": "unavailable",
            "permanent": False,
        }
    if action == "elevate":
        return {
            "label": "Request new permission separately",
            "effect": "This control cannot add permission or raise a limit.",
            "unchanged": "Current scope, limits, and forbidden effects stay unchanged.",
            "after": "A new grant must be reviewed through its separate start boundary.",
            "severity": "unavailable",
            "permanent": False,
        }
    return {
        "label": _title(action),
        "effect": "Applies only the exact operation described by its fresh preview.",
        "unchanged": "No other delivery fact or permission changes.",
        "after": "The saved state is replayed and its exact receipt is shown.",
        "severity": "caution",
        "permanent": False,
    }


def _control_issue(control: dict[str, object]) -> str:
    issues = _strings(control.get("issues"))
    issue = str(control.get("issue") or "")
    return "; ".join([*issues, *([issue] if issue else [])]) or (
        "This action is not applicable in the current saved state."
    )


def _actions(
    controls: list[dict[str, object]],
    *,
    context: str,
    live_progress: dict[str, object],
) -> list[dict[str, object]]:
    actions: list[dict[str, object]] = []
    next_step = live_progress.get("next_step")
    next_doc = next_step if isinstance(next_step, dict) else {}
    for index, control in enumerate(controls):
        action = str(control.get("action") or "")
        decision = str(control.get("decision") or "")
        semantics = _action_semantics(
            action,
            context=context,
            decision=decision,
            next_step=next_doc,
        )
        correlation = str(
            control.get("correlation_id")
            or control.get("request_id")
            or ""
        )
        action_id = ":".join(
            part for part in (action, correlation, decision) if part
        ) or f"control-{index + 1}"
        available = bool(control.get("available"))
        issue = "" if available else _control_issue(control)
        entry = {
            "id": action_id,
            "kind": "decision" if action == "request" else "control",
            "action": action,
            "decision": decision or None,
            "correlation_id": correlation or None,
            "label": semantics["label"],
            "available": available,
            "issue": issue or None,
            "reason_required": bool(control.get("reason_required")),
            "preview_required": bool(control.get("preview_required")),
            "confirmation_required": bool(
                available and control.get("preview_required")
            ),
            "may_start_work": bool(control.get("starts_work")),
            "permanent": semantics["permanent"],
            "severity": semantics["severity"],
            "consequences": {
                "effect": semantics["effect"],
                "unchanged": semantics["unchanged"],
                "after": semantics["after"],
            },
            "exact_binding": {
                "action": action,
                "decision": decision or None,
                (
                    "request_id"
                    if context == "program"
                    else "correlation_id"
                ): correlation or None,
                "control_index": index,
            },
            "source": {
                "model": (
                    "delivery-workbench-program-view"
                    if context == "program"
                    else "delivery-workbench-run-view"
                ),
                "path": f"/controls/{index}",
            },
        }
        if not available:
            entry["refusal"] = build_refusal_explanation(
                issue,
                semantics["unchanged"],
                effect_may_have_occurred=False,
                safe_next=str(semantics["after"]),
                technical_evidence=entry["source"],
            )
        actions.append(entry)
    return actions


def _read_actions(
    *,
    context: str,
    has_decision: bool,
    has_failure: bool,
) -> list[dict[str, object]]:
    items = [
        {
            "id": "reload-delivery-state",
            "kind": "read",
            "action": None,
            "read_action": "reload",
            "label": "Reload delivery state",
            "available": True,
            "confirmation_required": False,
            "consequences": {
                "effect": "Replays the canonical saved state and starts no work.",
                "unchanged": "Delivery state, permission, and cost remain unchanged.",
                "after": "The latest verified blockers, actions, limits, and receipts are shown.",
            },
        },
        {
            "id": "review-remaining-limits",
            "kind": "read",
            "action": None,
            "read_action": "limits",
            "label": "Review remaining limits",
            "available": True,
            "confirmation_required": False,
            "consequences": {
                "effect": "Opens current permission, consumption, and cost facts.",
                "unchanged": "No work starts and no limit or permission changes.",
                "after": "Choose an available bounded action or leave state unchanged.",
            },
        },
        {
            "id": "open-technical-details",
            "kind": "read",
            "action": None,
            "read_action": "technical",
            "label": "Open Technical details",
            "available": True,
            "confirmation_required": False,
            "consequences": {
                "effect": "Opens exact identities, controls, hashes, and ordered history.",
                "unchanged": "No delivery state changes.",
                "after": "Return to the same delivery summary when inspection is complete.",
            },
        },
        {
            "id": "return-without-change",
            "kind": "read",
            "action": None,
            "read_action": "leave",
            "label": (
                "Return without stopping"
                if context == "program"
                else "Leave delivery unchanged"
            ),
            "available": True,
            "confirmation_required": False,
            "consequences": {
                "effect": "Closes any local preview and applies nothing.",
                "unchanged": "Current delivery state stays unchanged.",
                "after": "The saved state remains available for later review.",
            },
        },
    ]
    if has_decision:
        items.insert(0, {
            "id": "leave-decision-pending",
            "kind": "read",
            "action": None,
            "read_action": "leave",
            "label": "Decide later",
            "available": True,
            "confirmation_required": False,
            "consequences": {
                "effect": "Leaves this exact request pending and starts no affected work.",
                "unchanged": "The request, affected work, permission, and cost stay unchanged.",
                "after": "Reload the saved state before responding later.",
            },
        })
    if has_failure:
        items.insert(0, {
            "id": "review-failed-check",
            "kind": "read",
            "action": None,
            "read_action": "failure",
            "label": "Review the failed check",
            "available": True,
            "confirmation_required": False,
            "consequences": {
                "effect": "Opens the saved failure and repair explanation.",
                "unchanged": "No replacement work starts and the prior failure remains visible.",
                "after": "Use only the repair step selected by the saved delivery plan.",
            },
        })
    for index, item in enumerate(items):
        item.update({
            "decision": None,
            "correlation_id": None,
            "reason_required": False,
            "preview_required": False,
            "may_start_work": False,
            "permanent": False,
            "severity": "read",
            "exact_binding": None,
            "source": {
                "model": BOUNDED_ACTIONS_KIND,
                "path": f"/read_actions/{index}",
            },
        })
    return items


def _permission(
    *,
    context: str,
    facts: dict[str, object],
    live_progress: dict[str, object],
    usage: dict[str, object],
) -> dict[str, object]:
    limits = live_progress.get("limits")
    limits_doc = limits if isinstance(limits, dict) else {}
    permission = limits_doc.get("permission")
    permission_doc = permission if isinstance(permission, dict) else {}
    scope = facts.get("scope")
    if context == "bounded-run":
        story = facts.get("story")
        story_doc = story if isinstance(story, dict) else {}
        scope = {
            "project": facts.get("project"),
            "story_id": story_doc.get("id"),
            "story_title": story_doc.get("title"),
        }
    stop_conditions = _strings(facts.get("stop_conditions"))
    if context == "bounded-run":
        stop_conditions = [
            "permission expiry",
            "a finite counted limit reaching its ceiling",
            "a terminal or failure route in the saved delivery plan",
            "a separately confirmed pause, revoke, or cancel",
        ]
    elif not stop_conditions:
        stop_conditions = [
            "permission expiry",
            "a finite program limit reaching its ceiling",
            "a saved program frontier stop or checkpoint",
            "a separately confirmed pause, revoke, or cancel",
        ]
    current_use = []
    for item in usage["items"]:
        if item["category"] == "progress":
            continue
        measurements = item["measurements"]
        actual = measurements["actual"]
        remaining = measurements["remaining"]
        current_use.append({
            "id": item["id"],
            "label": item["label"],
            "actual": actual,
            "remaining": remaining,
        })
    return {
        "status": permission_doc.get("status", "unknown"),
        "allowed_effects": list(permission_doc.get("may_still_use") or []),
        "scope": scope,
        "ceilings": [
            item["id"]
            for item in usage["items"]
            if item["category"] != "progress"
            and item["measurements"]["limit"]["state"]
            in {"finite", "zero", "unbounded"}
        ],
        "expires_at": limits_doc.get("expires_at") or facts.get("expires_at"),
        "stop_conditions": [
            _title(item) for item in stop_conditions
        ],
        "current_use": current_use,
        "forbidden_effects": list(
            permission_doc.get("will_not_use")
            or facts.get("permanent_exclusions")
            or []
        ),
        "summary": permission_doc.get(
            "summary", "Permission facts are unavailable."
        ),
        "source": {
            "model": (
                "delivery-workbench-program"
                if context == "program"
                else "delivery-workbench-run"
            ),
            "paths": [
                "/capabilities",
                "/scope" if context == "program" else "/story",
                "/budgets",
                "/expires_at",
                "/permanent_exclusions",
            ],
        },
    }


def _receipt_from_event(
    event: dict[str, object],
    *,
    context: str,
) -> dict[str, object] | None:
    event_name = str(event.get("event") or "")
    if event_name not in _CONTROL_RECEIPTS:
        return None
    action, label = _CONTROL_RECEIPTS[event_name]
    detail = event.get("detail")
    detail_doc = detail if isinstance(detail, dict) else {}
    decision = str(detail_doc.get("decision") or "")
    if event_name == "request_decided" and decision:
        label = f"{_title(decision)} decision recorded"
    if event_name == "request_refused":
        label = "Decision response refused without applying it"
    exact_ref = str(
        event.get("event_hash")
        or detail_doc.get("receipt_hash")
        or ""
    )
    return {
        "id": f"{context}:{event.get('seq', len(exact_ref))}:{event_name}",
        "label": label,
        "action": action,
        "decision": decision or None,
        "outcome": str(
            detail_doc.get("outcome")
            or detail_doc.get("result")
            or detail_doc.get("reason")
            or detail_doc.get("to_state")
            or "recorded"
        ),
        "at": event.get("ts") or event.get("at"),
        "exact_reference": exact_ref or None,
        "source": {
            "model": (
                "delivery-workbench-program-event"
                if context == "program"
                else "delivery-workbench-run-event"
            ),
            "path": f"/timeline/{event.get('seq')}",
        },
    }


def _receipts(
    events: list[dict[str, object]],
    *,
    context: str,
    program_receipts: list[dict[str, object]] | None = None,
) -> list[dict[str, object]]:
    items = [
        item
        for item in (
            _receipt_from_event(event, context=context) for event in events
        )
        if item is not None
    ]
    for receipt in program_receipts or []:
        if str(receipt.get("action_kind")) != "checkpoint-request":
            continue
        decision = receipt.get("decision")
        decision_doc = decision if isinstance(decision, dict) else {}
        option = str(decision_doc.get("option") or receipt.get("result") or "")
        items.append({
            "id": str(receipt.get("receipt_hash") or receipt.get("action_id")),
            "label": f"{_title(option)} decision recorded",
            "action": "request",
            "decision": option or None,
            "outcome": receipt.get("result") or "recorded",
            "at": receipt.get("issued_at"),
            "exact_reference": receipt.get("receipt_hash"),
            "source": {
                "model": "delivery-workbench-program-receipt",
                "path": f"/activities/completed/{receipt.get('action_id')}",
            },
        })
    deduped: dict[str, dict[str, object]] = {}
    for item in items:
        deduped[str(item["id"])] = item
    return list(deduped.values())[-8:][::-1]


def _request_actions(
    actions: list[dict[str, object]],
    correlation_id: str,
) -> list[dict[str, object]]:
    return [
        item
        for item in actions
        if item["action"] == "request"
        and item.get("correlation_id") == correlation_id
    ]


def _choice(action: dict[str, object]) -> dict[str, object]:
    return {
        "action_id": action["id"],
        "label": action["label"],
        "decision": action.get("decision"),
        "available": action["available"],
        "effect": action["consequences"]["effect"],
        "after": action["consequences"]["after"],
    }


def _fallback_choices(actions: list[dict[str, object]]) -> list[dict[str, object]]:
    preferred = [
        item for item in actions
        if item["available"]
        and item.get("action") in {"tick", "pause", "resume", "revoke", "cancel"}
    ]
    if not preferred:
        preferred = [
            item for item in actions
            if item["id"] in {
                "review-failed-check",
                "reload-delivery-state",
                "open-technical-details",
            }
        ]
    return [_choice(item) for item in preferred[:5]]


def _run_inbox(
    projection: dict[str, object],
    decision: dict[str, object],
    graph_nodes: list[dict[str, object]],
    actions: list[dict[str, object]],
) -> list[dict[str, object]]:
    inbox: list[dict[str, object]] = []
    node_by_id = {
        str(item.get("id")): item for item in graph_nodes
    }
    for request in _objects(projection.get("outstanding_requests")):
        correlation = str(request.get("correlation_id") or "")
        choices = _request_actions(actions, correlation)
        affected = _title(
            request.get("origin_node") or request.get("origin"),
            "This bounded delivery",
        )
        inbox.append({
            "id": f"decision:{correlation}",
            "kind": "decision",
            "status": "needs-decision",
            "affected_work": affected,
            "why": _bounded_text(
                request.get("schema_summary"),
                "The saved delivery is waiting for one exact closed response.",
            ),
            "resolver": "The named checkpoint owner through the fresh local request boundary.",
            "valid_choices": [_choice(item) for item in choices],
            "after_no_choice": (
                "The request remains pending and affected work does not advance."
            ),
            "technical_reference": correlation,
            "source": {
                "model": "delivery-workbench-run",
                "path": "/outstanding_requests",
            },
        })
    seen: set[str] = set()
    for blocked in _objects(decision.get("blocked")):
        node_id = str(blocked.get("node_id") or "")
        reason = str(blocked.get("reason") or "unknown blocker")
        if reason == "dependencies" or node_id in seen:
            continue
        seen.add(node_id)
        node = node_by_id.get(node_id, {})
        inbox.append({
            "id": f"blocker:{node_id}",
            "kind": "blocker",
            "status": "blocked",
            "affected_work": _title(node.get("title") or node_id),
            "why": _title(reason),
            "resolver": (
                "The saved failure route, a required external fact, or an "
                "operator using one currently available exact control."
            ),
            "valid_choices": _fallback_choices(actions),
            "after_no_choice": "Affected work remains stopped in the saved state.",
            "technical_reference": node_id,
            "source": {
                "model": "delivery-workbench-conductor-decision",
                "path": "/blocked",
            },
        })
    if projection.get("state") == "blocked" and not any(
        item["kind"] == "blocker" for item in inbox
    ):
        inbox.append({
            "id": "blocker:run-state",
            "kind": "blocker",
            "status": "blocked",
            "affected_work": _title(
                (projection.get("story") or {}).get("title")
                if isinstance(projection.get("story"), dict)
                else "This bounded delivery"
            ),
            "why": "The saved bounded policy reached its blocked terminal state.",
            "resolver": "The saved delivery policy; this grant cannot invent another route.",
            "valid_choices": _fallback_choices(actions),
            "after_no_choice": "The blocked state and completed evidence remain unchanged.",
            "technical_reference": projection.get("ledger_head"),
            "source": {
                "model": "delivery-workbench-run",
                "path": "/state",
            },
        })
    for refusal in _objects(projection.get("request_refusals")):
        reason = str(refusal.get("reason") or "request refusal")
        inbox.append({
            "id": f"refusal:{refusal.get('seq', refusal.get('correlation_id'))}",
            "kind": "refusal",
            "status": "refused",
            "affected_work": _title(
                refusal.get("origin_node") or refusal.get("origin"),
                "The named request",
            ),
            "why": _title(reason),
            "resolver": "Reload the exact request state; do not guess another response.",
            "valid_choices": [
                _choice(item) for item in actions
                if item["id"] in {
                    "reload-delivery-state",
                    "open-technical-details",
                }
            ],
            "after_no_choice": "No decision is applied by this refusal.",
            "technical_reference": (
                refusal.get("response_hash") or refusal.get("correlation_id")
            ),
            "explanation": build_refusal_explanation(
                f"The request response was refused: {_words(reason)}.",
                "The live request and affected delivery state were not changed by the refusal.",
                effect_may_have_occurred=False,
                safe_next="Reload the current requests and respond only to an exact outstanding request.",
                technical_evidence={
                    "model": "delivery-workbench-run",
                    "path": "/request_refusals",
                },
            ),
            "source": {
                "model": "delivery-workbench-run",
                "path": "/request_refusals",
            },
        })
    return inbox


def _program_inbox(
    authority: dict[str, object],
    frontier: dict[str, object],
    actions: list[dict[str, object]],
    refusal: dict[str, object] | None,
) -> list[dict[str, object]]:
    inbox: list[dict[str, object]] = []
    current_story = ""
    selection = authority.get("selection")
    if isinstance(selection, dict):
        story = selection.get("story")
        current_story = str(
            story.get("id") if isinstance(story, dict) else story or ""
        )
    for request in _objects(authority.get("outstanding_requests")):
        request_id = str(request.get("claim_id") or "")
        choices = _request_actions(actions, request_id)
        inbox.append({
            "id": f"decision:{request_id}",
            "kind": "decision",
            "status": "needs-decision",
            "affected_work": _title(
                current_story or request.get("port"),
                "The current program work",
            ),
            "why": (
                f"The saved program is waiting at {_words(request.get('port') or 'checkpoint')}."
            ),
            "resolver": "The granted program operator through the fresh local request boundary.",
            "valid_choices": [_choice(item) for item in choices],
            "after_no_choice": "The request remains pending and affected work does not advance.",
            "technical_reference": request_id,
            "source": {
                "model": "delivery-workbench-program",
                "path": "/outstanding_requests",
            },
        })
    for obligation in _objects(authority.get("blocking_obligations")):
        obligation_id = str(obligation.get("id") or "")
        inbox.append({
            "id": f"blocker:{obligation_id}",
            "kind": "blocker",
            "status": "blocked",
            "affected_work": _title(
                obligation.get("target") or current_story,
                "The current program work",
            ),
            "why": _bounded_text(
                obligation.get("statement") or obligation.get("reason"),
                "A saved blocking obligation is still open.",
            ),
            "resolver": _title(
                obligation.get("accountable_role"),
                "The accountable role named by the saved obligation",
            ),
            "valid_choices": _fallback_choices(actions),
            "after_no_choice": "Program progression remains stopped while the obligation is blocking.",
            "technical_reference": obligation_id,
            "source": {
                "model": "delivery-workbench-program",
                "path": "/blocking_obligations",
            },
        })
    stop = str(frontier.get("stop") or "")
    if stop and stop not in {"integration-required", "scope-complete"}:
        inbox.append({
            "id": f"blocker:frontier:{stop}",
            "kind": "blocker",
            "status": "blocked",
            "affected_work": _title(current_story, "The current program scope"),
            "why": f"The saved program frontier stopped at {_words(stop)}.",
            "resolver": (
                "The saved program rules, a required role or fact, or an "
                "operator using one currently available exact control."
            ),
            "valid_choices": _fallback_choices(actions),
            "after_no_choice": "No new program work advances from this saved stop.",
            "technical_reference": stop,
            "source": {
                "model": "delivery-workbench-program-frontier",
                "path": "/stop",
            },
        })
    if refusal:
        inbox.append({
            "id": f"refusal:{refusal.get('code', 'program')}",
            "kind": "refusal",
            "status": "refused",
            "affected_work": _title(current_story, "The current program scope"),
            "why": str(refusal.get("message") or refusal.get("code") or "Program refusal"),
            "resolver": "Reload exact program evidence; this view will not guess a frontier.",
            "valid_choices": [
                _choice(item) for item in actions
                if item["id"] in {
                    "reload-delivery-state",
                    "open-technical-details",
                }
            ],
            "after_no_choice": "No work starts from an invalid frontier.",
            "technical_reference": refusal.get("ledger_head"),
            "explanation": build_refusal_explanation(
                str(refusal.get("message") or "The program frontier was refused."),
                "The last verified program ledger remains authoritative.",
                effect_may_have_occurred=False,
                safe_next="Inspect the exact ledger and reload after correcting the source fact.",
                technical_evidence={
                    "model": "delivery-workbench-program-view",
                    "path": "/current/refusal",
                },
            ),
            "source": {
                "model": "delivery-workbench-program-view",
                "path": "/current/refusal",
            },
        })
    return inbox


def _base_document(
    *,
    context: str,
    facts: dict[str, object],
    live_progress: dict[str, object],
    controls: list[dict[str, object]],
    inbox_builder,
    events: list[dict[str, object]],
    program_receipts: list[dict[str, object]] | None = None,
) -> dict[str, object]:
    usage = _usage(facts.get("budgets"), live_progress)
    mutating_actions = _actions(
        controls,
        context="program" if context == "program" else "bounded-run",
        live_progress=live_progress,
    )
    has_decision = bool(facts.get("outstanding_requests"))
    has_failure = bool(
        (live_progress.get("review") or {}).get("failed_evidence")
        if isinstance(live_progress.get("review"), dict)
        else False
    ) or str((live_progress.get("next_step") or {}).get("kind")) == "repair"
    read_actions = _read_actions(
        context="program" if context == "program" else "bounded-run",
        has_decision=has_decision,
        has_failure=has_failure,
    )
    actions = [*read_actions, *mutating_actions]
    inbox = inbox_builder(actions)
    return {
        "kind": BOUNDED_ACTIONS_KIND,
        "schema_version": BOUNDED_ACTIONS_SCHEMA_VERSION,
        "context": context,
        "summary": (
            f"{len(inbox)} decision, blocker, or refusal item"
            f"{'s' if len(inbox) != 1 else ''}; "
            f"{sum(1 for item in mutating_actions if item['available'])} "
            "exact bounded actions currently available."
        ),
        "inbox": inbox,
        "permission": _permission(
            context=context,
            facts=facts,
            live_progress=live_progress,
            usage=usage,
        ),
        "usage": usage,
        "actions": actions,
        "receipts": _receipts(
            events,
            context="program" if context == "program" else "bounded-run",
            program_receipts=program_receipts,
        ),
        "error_contract": {
            "required_parts": [
                "what happened",
                "what stayed unchanged",
                "whether an effect may already have occurred",
                "the safe next step",
                "exact technical evidence",
            ],
            "unknown_effect_rule": (
                "If transport ends without an exact refusal or receipt, effect "
                "status is unknown until the saved ledger is reloaded."
            ),
        },
        "transport_boundary": {
            "role": "response-carrier",
            "notification_or_remote_grants_authority": False,
            "decisive_checks": [
                "canonical principal",
                "exact request identity",
                "closed response set",
                "fresh preview token",
                "current ledger and generation",
            ],
        },
        "starts_work": False,
        "writes_events": False,
        "selects_action": False,
        "selects_next_work": False,
        "grants_authority": False,
        "changes_retry_policy": False,
        "sends_notifications": False,
    }


def build_run_bounded_actions(
    projection: dict[str, object],
    decision: dict[str, object],
    graph_nodes: list[dict[str, object]],
    controls: list[dict[str, object]],
    live_progress: dict[str, object],
    events: list[dict[str, object]],
) -> dict[str, object]:
    """Explain exact bounded-run controls without selecting or applying one."""
    return _base_document(
        context="bounded-run",
        facts=projection,
        live_progress=live_progress,
        controls=controls,
        inbox_builder=lambda actions: _run_inbox(
            projection, decision, graph_nodes, actions
        ),
        events=events,
    )


def build_program_bounded_actions(
    authority: dict[str, object],
    frontier: dict[str, object],
    controls: list[dict[str, object]],
    live_progress: dict[str, object],
    events: list[dict[str, object]],
    *,
    refusal: dict[str, object] | None,
    receipts: list[dict[str, object]],
) -> dict[str, object]:
    """Explain exact program controls without selecting or applying one."""
    return _base_document(
        context="program",
        facts=authority,
        live_progress=live_progress,
        controls=controls,
        inbox_builder=lambda actions: _program_inbox(
            authority, frontier, actions, refusal
        ),
        events=events,
        program_receipts=receipts,
    )
