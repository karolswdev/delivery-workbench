"""Shared, content-safe public surface for autonomous delivery programs.

CLI, MCP, HTTP, the Workbench control room, and SSE all adapt these documents.
The module owns no policy or execution semantics: it composes the existing
program compiler, grant ledger, conductor, and delivery rails.  Public acts
accept identifiers, closed decisions, bounded reasons, and one fresh token;
they never accept runtime policy, prompts, assignments, capabilities, driver
configuration, commands, or retry routes.
"""

from __future__ import annotations

from datetime import datetime
import hashlib
import json
from pathlib import Path
import re
import time

from .bounded_actions import build_program_bounded_actions
from .live_progress import build_program_live_progress
from .model import DwError
from .orchestration import canonical_json
from .program_conductor import (
    RECONCILIATION_STOPS,
    TERMINAL_AUTHORITY_STATES,
    derive_program_frontier,
    replay_program_conductor,
    respond_program_request,
    tick_program,
)
from .program_delivery import (
    build_program_delivery_preview,
    replay_program_delivery,
    start_program_delivery,
    tick_program_delivery,
)
from .program_run import (
    _run_dir,
    _sha,
    apply_program_control,
    build_program_control_preview,
    build_program_start_plan,
    program_run_inventory,
    replay_program,
    start_program,
)
from .programs import program_inventory
from .team_review import build_live_team_review


PROGRAM_SURFACE_SCHEMA_VERSION = 1
PROGRAM_ACT_PREVIEW_KIND = "delivery-workbench-program-act-preview"
PROGRAM_VIEW_KIND = "delivery-workbench-program-view"
PROGRAM_SUMMARY_KIND = "delivery-workbench-program-summary-list"
PROGRAM_TICK_SURFACE_KIND = "delivery-workbench-program-surface-tick"
PROGRAM_SUPERVISION_SURFACE_KIND = (
    "delivery-workbench-program-surface-supervision"
)
PROGRAM_TAIL_KIND = "delivery-workbench-program-tail"
PROGRAM_STREAM_KIND = "delivery-workbench-program-stream"

PROGRAM_ACTIONS = {
    "tick", "supervise", "request", "pause", "resume", "revoke", "cancel",
}
_CONTROL_ACTIONS = {"pause", "resume", "revoke", "cancel"}
_REASON_ACTIONS = {"request", "pause", "resume", "revoke", "cancel"}
_RUN_ID_RE = re.compile(r"^program-[0-9a-f]{24}$")
_DELIVERY_ID_RE = re.compile(r"^delivery-[0-9a-f]{24}$")
_SESSION_ID_RE = re.compile(r"^session-[0-9a-f]{24}$")
_MAX_TAIL_EVENTS = 1_000
_MAX_STREAM_READ = 100_000


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise DwError(message)


def _bounded_reason(value: object, *, required: bool) -> str:
    reason = str(value or "").strip()
    if required:
        _require(bool(reason), "program act requires a reason")
    else:
        _require(not reason, "program act does not accept a reason")
    _require(
        len(reason.encode("utf-8")) <= 1_000
        and "\x00" not in reason
        and "\n" not in reason
        and "\r" not in reason,
        "program act reason must be a bounded single line",
    )
    return reason


def start_program_by_id(
    root: Path,
    program: str,
    *,
    mode: str,
    operator: object,
    approval_reason: str,
    intent_id: str,
    capabilities: list[str] | None,
    budgets: dict[str, int] | None,
    issued_at: str,
    expires_at: str,
    remote: str | None,
    remote_ref: str | None,
    expect: str,
    now: str | datetime | None = None,
) -> dict[str, object]:
    """Rebuild and consume one grant plan from ids and reviewed scalar facts."""
    plan = build_program_start_plan(
        root,
        program,
        mode=mode,
        operator=operator,
        approval_reason=approval_reason,
        intent_id=intent_id,
        capabilities=capabilities,
        budgets=budgets,
        issued_at=issued_at,
        expires_at=expires_at,
        remote=remote,
        remote_ref=remote_ref,
    )
    _require(
        str(expect or "") == plan["start_token"],
        "stale or altered program start token refused; no grant was created",
    )
    return start_program(
        root,
        plan,
        start_token=str(plan["start_token"]),
        now=now,
    )


def _delivery_frontiers(
    root: Path,
    run_id: str,
    *,
    now: str | datetime | None = None,
) -> list[dict[str, object]]:
    base = _run_dir(root.resolve(), run_id) / "delivery"
    if base.is_symlink():
        raise DwError("refusing symlinked program delivery store")
    if not base.is_dir():
        return []
    frontiers: list[dict[str, object]] = []
    for path in sorted(base.iterdir(), key=lambda item: item.name):
        if (
            not path.is_dir()
            or path.is_symlink()
            or not _DELIVERY_ID_RE.fullmatch(path.name)
        ):
            continue
        frontiers.append(
            replay_program_delivery(root, run_id, path.name, now=now)
        )
    return frontiers


def _public_action(action: object) -> dict[str, object] | None:
    if not isinstance(action, dict):
        return None
    return {
        key: action.get(key)
        for key in (
            "action_id", "kind", "address", "phase", "story",
            "workflow_address", "node", "role", "role_address", "attempt",
        )
        if key in action
    }


def _tick_operation(
    root: Path,
    run_id: str,
    *,
    now: str | datetime | None = None,
) -> tuple[dict[str, object], list[str]]:
    authority = replay_program(root, run_id, now=now)
    issues: list[str] = []
    if authority["state"] != "running":
        return {
            "lane": "none",
            "state": authority["state"],
            "next_action": None,
            "delivery_id": None,
        }, [f"cannot tick program authority in state {authority['state']}"]

    deliveries = _delivery_frontiers(root, run_id, now=now)
    active = [item for item in deliveries if not item["complete"]]
    if len(active) > 1:
        return {
            "lane": "none",
            "state": "delivery-conflict",
            "next_action": None,
            "delivery_id": None,
        }, ["program has multiple incomplete delivery intents"]
    if active:
        delivery = active[0]
        return {
            "lane": "delivery",
            "state": delivery["state"],
            "delivery_id": delivery["delivery_id"],
            "next_action": _public_action(delivery["next_action"]),
            "completed_actions": len(delivery["completed_action_ids"]),
        }, []

    conductor = replay_program_conductor(root, run_id, now=now)
    frontier = derive_program_frontier(root, run_id, now=now)
    if (
        frontier.get("state") == "story-certified"
        and frontier.get("stop") == "integration-required"
    ):
        preview = build_program_delivery_preview(root, run_id, now=now)
        issues.extend(
            str(item.get("message") or item.get("code"))
            for item in preview["issues"]
            if isinstance(item, dict)
        )
        return {
            "lane": "delivery-plan",
            "state": frontier["state"],
            "delivery_id": None,
            "next_action": {
                "kind": "delivery-plan",
                "phase": preview["binding"]["phase"],
                "story": preview["binding"]["story"],
                "action_count": len(preview["actions"]),
            },
            "delivery_plan_hash": _sha({
                key: item
                for key, item in preview.items()
                if key != "delivery_token"
            }),
        }, issues

    next_actions = list(frontier.get("next_actions", []))
    return {
        "lane": "conductor",
        "state": frontier["state"],
        "delivery_id": None,
        "next_action": _public_action(next_actions[0]) if next_actions else None,
        "active_claim_ids": [
            item["claim_id"]
            for item in conductor["active_conductor_claims"]
        ],
        "stop": frontier.get("stop"),
    }, []


def build_program_act_preview(
    root: Path,
    run_id: str,
    action: str,
    *,
    reason: str = "",
    decision: str = "",
    request_id: str = "",
    max_ticks: int = 100,
    max_seconds: int = 300,
    now: str | datetime | None = None,
) -> dict[str, object]:
    """Build a pure action+parameter+ledger-bound confirmation document."""
    action = str(action or "").strip().lower()
    _require(action in PROGRAM_ACTIONS, f"unsupported program act: {action}")
    reason = _bounded_reason(reason, required=action in _REASON_ACTIONS)
    decision = str(decision or "").strip().lower()
    request_id = str(request_id or "").strip()
    authority = replay_program(root, run_id, now=now)
    issues: list[str] = []
    operation: dict[str, object] | None = None

    if action in {"tick", "supervise"}:
        _require(not decision and not request_id, f"program {action} accepts no decision")
        _require(
            isinstance(max_ticks, int)
            and not isinstance(max_ticks, bool)
            and 1 <= max_ticks <= 10_000,
            "program max_ticks must be between 1 and 10000",
        )
        _require(
            isinstance(max_seconds, int)
            and not isinstance(max_seconds, bool)
            and 1 <= max_seconds <= 86_400,
            "program max_seconds must be between 1 and 86400",
        )
        operation, operation_issues = _tick_operation(
            root, run_id, now=now
        )
        issues.extend(operation_issues)
    elif action in _CONTROL_ACTIONS:
        _require(not decision and not request_id, f"program {action} accepts no decision")
        control = build_program_control_preview(
            root,
            run_id,
            action=action,
            decision="approve",
            reason=reason,
            now=now,
        )
        issues.extend(
            str(item.get("message") or item.get("code"))
            for item in control["issues"]
            if isinstance(item, dict)
        )
        operation = {
            "lane": "control",
            "state": authority["state"],
            "effect": control["effect"],
            "next_action": None,
            "delivery_id": None,
        }
    else:
        _require(action == "request", "unsupported program act")
        _require(
            bool(request_id) and request_id.startswith("claim-"),
            "program request requires one request id",
        )
        _require(
            decision in {"approve", "reject"},
            "program request decision must be approve or reject",
        )
        matches = [
            item
            for item in authority["outstanding_requests"]
            if item.get("claim_id") == request_id
        ]
        if len(matches) != 1:
            issues.append("program request is stale, unknown, or no longer outstanding")
            request = None
        else:
            request = matches[0]
        operation = {
            "lane": "request",
            "state": authority["state"],
            "request": request,
            "next_action": None,
            "delivery_id": None,
        }

    unsigned: dict[str, object] = {
        "kind": PROGRAM_ACT_PREVIEW_KIND,
        "schema_version": PROGRAM_SURFACE_SCHEMA_VERSION,
        "run_id": run_id,
        "action": action,
        "applicable": not issues,
        "issues": issues,
        "state": authority["state"],
        "grant_hash": authority["grant_hash"],
        "generation": authority["generation"],
        "ledger_head": authority["ledger_head"],
        "reason": reason,
        "decision": decision,
        "request_id": request_id,
        "max_ticks": max_ticks,
        "max_seconds": max_seconds,
        "operation": operation,
        "starts_work": action in {"tick", "supervise"},
        "writes_events": False,
    }
    return {**unsigned, "act_token": _sha(unsigned)}


def _surface_tick(
    root: Path,
    run_id: str,
    *,
    now: str | datetime | None = None,
    expected_binding: dict[str, object] | None = None,
    expected_operation: dict[str, object] | None = None,
) -> dict[str, object]:
    operation, issues = _tick_operation(root, run_id, now=now)
    _require(not issues, "program tick is not applicable: " + "; ".join(issues))
    if expected_operation is not None:
        _require(
            operation == expected_operation,
            "program act token is stale at the execution frontier",
        )
    lane = str(operation["lane"])
    raw: dict[str, object]
    if lane == "delivery-plan":
        preview = build_program_delivery_preview(root, run_id, now=now)
        if expected_binding is not None:
            binding = preview["binding"]
            _require(
                isinstance(binding, dict)
                and all(
                    binding.get(key) == expected_binding.get(key)
                    for key in ("grant_hash", "ledger_head", "generation")
                ),
                "program act token is stale at the delivery-plan boundary",
            )
        _require(
            bool(preview["applicable"]),
            "program delivery plan is not applicable",
        )
        frontier = start_program_delivery(
            root,
            preview,
            delivery_token=str(preview["delivery_token"]),
        )
        raw = {
            "kind": "delivery-plan",
            "delivery_id": frontier["delivery_id"],
            "state": frontier["state"],
            "progressed": True,
            "action": operation["next_action"],
            "receipt": None,
            "remaining": len(preview["actions"]),
        }
    elif lane == "delivery":
        raw = tick_program_delivery(
            root,
            run_id,
            str(operation["delivery_id"]),
            now=now,
            _expected_binding=expected_binding,
        )
    elif lane == "conductor":
        raw = tick_program(
            root,
            run_id,
            now=now,
            _expected_binding=expected_binding,
        )
    else:
        raise DwError("program tick has no authorized execution lane")

    authority = replay_program(root, run_id, now=now)
    try:
        frontier = derive_program_frontier(root, run_id, now=now)
    except DwError as exc:
        frontier = {
            "state": "stopped",
            "terminal": False,
            "checkpoint": False,
            "stop": "frontier-invalid",
            "next_actions": [],
            "lineage": None,
            "refusal": exc.message,
        }
    progressed = bool(raw.get("progressed", True))
    stop = raw.get("stop") or frontier.get("stop")
    checkpoint = bool(frontier.get("checkpoint"))
    # The conductor intentionally hands certified work to the exact delivery
    # adapter.  On this public surface that is an internal lane transition,
    # not a human checkpoint and not a reason for supervise to stop.
    if (
        lane == "conductor"
        and raw.get("stop") == "integration-required"
        and authority["state"] == "running"
    ):
        delivery_preview = build_program_delivery_preview(
            root, run_id, now=now
        )
        if delivery_preview["applicable"]:
            checkpoint = False
            stop = None
    if lane in {"delivery-plan", "delivery"}:
        incomplete_deliveries = [
            item
            for item in _delivery_frontiers(root, run_id, now=now)
            if not item["complete"]
        ]
        if incomplete_deliveries:
            checkpoint = False
            stop = None
    terminal = (
        authority["state"] in TERMINAL_AUTHORITY_STATES
        or bool(frontier.get("terminal"))
    )
    return {
        "kind": PROGRAM_TICK_SURFACE_KIND,
        "schema_version": PROGRAM_SURFACE_SCHEMA_VERSION,
        "run_id": run_id,
        "lane": lane,
        "state": frontier.get("state", authority["state"]),
        "authority_state": authority["state"],
        "progressed": progressed,
        "terminal": terminal,
        "checkpoint": checkpoint,
        "stop": stop,
        "action": raw.get("action"),
        "delivery_id": raw.get("delivery_id") or operation.get("delivery_id"),
        "receipt": raw.get("receipt"),
        "ledger_head": authority["ledger_head"],
        "frontier": {
            "lineage": frontier.get("lineage"),
            "next_action_count": len(frontier.get("next_actions", [])),
            "refusal": frontier.get("refusal"),
        },
        "content_safe": True,
    }


def _supervise_program_surface(
    root: Path,
    run_id: str,
    *,
    max_ticks: int,
    max_seconds: int,
    now: str | datetime | None = None,
    expected_binding: dict[str, object] | None = None,
    expected_operation: dict[str, object] | None = None,
) -> dict[str, object]:
    started = time.monotonic()
    ticks: list[dict[str, object]] = []
    stop = "tick-ceiling"
    for _index in range(max_ticks):
        if time.monotonic() - started >= max_seconds:
            stop = "time-ceiling"
            break
        tick = _surface_tick(
            root,
            run_id,
            now=now,
            expected_binding=expected_binding if not ticks else None,
            expected_operation=expected_operation if not ticks else None,
        )
        ticks.append(tick)
        if tick["terminal"]:
            stop = "terminal"
            break
        if tick["checkpoint"]:
            stop = "checkpoint"
            break
        if tick["stop"] in RECONCILIATION_STOPS:
            stop = str(tick["stop"])
            break
        if tick["stop"] is not None:
            stop = str(tick["stop"])
            break
        if not tick["progressed"]:
            stop = "no-progress"
            break
    last = ticks[-1] if ticks else None
    return {
        "kind": PROGRAM_SUPERVISION_SURFACE_KIND,
        "schema_version": PROGRAM_SURFACE_SCHEMA_VERSION,
        "run_id": run_id,
        "ticks": ticks,
        "tick_count": len(ticks),
        "stop": stop,
        "state": last["state"] if last else "not-started",
        "terminal": bool(last and last["terminal"]),
        "checkpoint": bool(last and last["checkpoint"]),
        "progressed": any(bool(item["progressed"]) for item in ticks),
        "max_ticks": max_ticks,
        "max_seconds": max_seconds,
        "bounded": True,
        "content_safe": True,
    }


def apply_program_act(
    root: Path,
    run_id: str,
    action: str,
    expect: str,
    *,
    reason: str = "",
    decision: str = "",
    request_id: str = "",
    max_ticks: int = 100,
    max_seconds: int = 300,
    now: str | datetime | None = None,
) -> dict[str, object]:
    """Apply exactly one fresh preview without caller-owned runtime semantics."""
    preview = build_program_act_preview(
        root,
        run_id,
        action,
        reason=reason,
        decision=decision,
        request_id=request_id,
        max_ticks=max_ticks,
        max_seconds=max_seconds,
        now=now,
    )
    _require(
        str(expect or "") == preview["act_token"],
        "stale or altered program act token refused; no work started and no event was appended",
    )
    _require(
        bool(preview["applicable"]),
        "program act is not applicable: " + "; ".join(preview["issues"]),
    )
    expected_binding = {
        key: preview[key]
        for key in ("grant_hash", "ledger_head", "generation", "state")
    }
    expected_operation = preview.get("operation")
    _require(
        isinstance(expected_operation, dict),
        "program act preview has no exact operation binding",
    )
    action = str(action).strip().lower()
    if action == "tick":
        return _surface_tick(
            root,
            run_id,
            now=now,
            expected_binding=expected_binding,
            expected_operation=expected_operation,
        )
    if action == "supervise":
        return _supervise_program_surface(
            root,
            run_id,
            max_ticks=max_ticks,
            max_seconds=max_seconds,
            now=now,
            expected_binding=expected_binding,
            expected_operation=expected_operation,
        )
    if action == "request":
        return respond_program_request(
            root,
            run_id,
            request_id,
            decision,
            reason=reason,
            now=now,
            _expected_binding=expected_binding,
        )
    control = build_program_control_preview(
        root,
        run_id,
        action=action,
        decision="approve",
        reason=reason,
        now=now,
    )
    binding = control["binding"]
    _require(
        isinstance(binding, dict)
        and all(
            binding.get(key) == expected_binding.get(key)
            for key in ("grant_hash", "ledger_head", "generation", "state")
        ),
        "program act token is stale at the control boundary",
    )
    return apply_program_control(
        root,
        control,
        control_token=str(control["control_token"]),
        now=now,
    )


def _safe_artifact(value: object) -> dict[str, object] | None:
    if not isinstance(value, dict):
        return None
    return {
        key: value.get(key)
        for key in (
            "artifact_id", "action_id", "address", "attempt", "name",
            "artifact_kind", "bytes", "sha256", "ref", "valid", "checks",
        )
        if key in value
    }


def _safe_receipt(value: dict[str, object]) -> dict[str, object]:
    payload = value.get("payload")
    safe_payload: dict[str, object] = {}
    if isinstance(payload, dict):
        for key in (
            "binding", "phase", "story", "status", "reason", "why",
            "team", "workflow", "assignment_hash", "roster_hash",
            "separation", "repair_round", "round", "stage", "council_id",
            "protocol_id", "loop_address", "loop_lineage", "max_rounds",
            "result", "route", "request_id", "port", "decision",
            "generation", "ledger_head", "child_grant_hash", "test_failures",
        ):
            if key in payload:
                safe_payload[key] = payload[key]
    return {
        "action_id": value.get("action_id"),
        "address": value.get("address"),
        "action_kind": value.get("action_kind"),
        "phase": value.get("phase"),
        "story": value.get("story"),
        "workflow_address": value.get("workflow_address"),
        "node": value.get("node"),
        "role": value.get("role"),
        "role_address": value.get("role_address"),
        "attempt": value.get("attempt"),
        "claim_id": value.get("claim_id"),
        "outcome": value.get("outcome"),
        "result": value.get("result"),
        "route": value.get("route"),
        "operation": value.get("operation"),
        "artifacts": [
            item
            for item in (
                _safe_artifact(artifact)
                for artifact in value.get("artifacts", [])
            )
            if item is not None
        ],
        "verdict": value.get("verdict"),
        "decision": value.get("decision"),
        "obligation_ids": list(value.get("obligation_ids", [])),
        "payload": safe_payload,
        "issued_at": value.get("issued_at"),
        "receipt_hash": value.get("receipt_hash"),
    }


def _driver_sessions(root: Path, run_id: str) -> list[dict[str, object]]:
    directory = _run_dir(root.resolve(), run_id) / "conductor" / "driver-sessions"
    if directory.is_symlink():
        raise DwError("refusing symlinked program driver session store")
    if not directory.is_dir():
        return []
    sessions: list[dict[str, object]] = []
    for path in sorted(directory.glob("operation-*.json"), key=lambda item: item.name):
        if not path.is_file() or path.is_symlink():
            continue
        try:
            record = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise DwError(f"cannot read program driver session: {exc}") from exc
        _require(isinstance(record, dict), "program driver session must be an object")
        receipt = record.get("receipt")
        sessions.append({
            "operation_id": record.get("operation_id"),
            "session_id": record.get("session_id"),
            "claim_id": record.get("claim_id"),
            "profile": record.get("profile"),
            "adapter": record.get("adapter"),
            "adapter_version": record.get("adapter_version"),
            "child_grant_hash": record.get("child_grant_hash"),
            "state": (
                receipt.get("state")
                if isinstance(receipt, dict)
                else record.get("status")
            ),
            "activity": (
                receipt.get("activity")
                if isinstance(receipt, dict)
                else None
            ),
            "started_at": (
                receipt.get("started_at")
                if isinstance(receipt, dict)
                else None
            ),
            "updated_at": (
                receipt.get("updated_at")
                if isinstance(receipt, dict)
                else None
            ),
            "stdout_bytes": (
                receipt.get("stdout_bytes")
                if isinstance(receipt, dict)
                else 0
            ),
            "stderr_bytes": (
                receipt.get("stderr_bytes")
                if isinstance(receipt, dict)
                else 0
            ),
        })
    return sessions


def _activity_graph(
    activities: list[dict[str, object]],
    next_action: dict[str, object] | None,
) -> dict[str, object]:
    nodes = [
        {
            "id": item["action_id"],
            "address": item["address"],
            "kind": item["action_kind"],
            "role": item["role"],
            "state": item["outcome"],
            "result": item["result"],
            "parent": None,
        }
        for item in activities
    ]
    if next_action and next_action.get("action_id"):
        nodes.append({
            "id": next_action["action_id"],
            "address": next_action.get("address"),
            "kind": next_action.get("kind"),
            "role": next_action.get("role"),
            "state": "next",
            "result": None,
            "parent": None,
        })
    by_address = {
        str(node["address"]): node
        for node in nodes
        if node.get("address")
    }
    addresses = sorted(by_address, key=lambda item: (len(item), item))
    edges: list[dict[str, str]] = []
    for address in addresses:
        candidates = [
            parent
            for parent in addresses
            if parent != address and address.startswith(parent + "/")
        ]
        if candidates:
            parent = max(candidates, key=len)
            by_address[address]["parent"] = by_address[parent]["id"]
            edges.append({
                "from": str(by_address[parent]["id"]),
                "to": str(by_address[address]["id"]),
                "kind": "contains",
            })
    # Stable causal order remains visible even when hierarchy siblings have no
    # direct containment edge.
    for left, right in zip(nodes, nodes[1:]):
        edges.append({
            "from": str(left["id"]),
            "to": str(right["id"]),
            "kind": "precedes",
        })
    return {"nodes": nodes, "edges": edges, "nested": True}


def _delivery_documents(
    root: Path,
    run_id: str,
    *,
    now: str | datetime | None = None,
) -> list[dict[str, object]]:
    documents: list[dict[str, object]] = []
    for frontier in _delivery_frontiers(root, run_id, now=now):
        next_action = frontier.get("next_action")
        documents.append({
            "delivery_id": frontier["delivery_id"],
            "state": frontier["state"],
            "complete": frontier["complete"],
            "plan_hash": frontier["plan_hash"],
            "completed_action_ids": frontier["completed_action_ids"],
            "active_claim_ids": [
                item["claim_id"] for item in frontier["active_claims"]
            ],
            "next_action": (
                {
                    key: next_action.get(key)
                    for key in (
                        "action_id", "kind", "category", "capability",
                        "phase", "story",
                    )
                }
                if isinstance(next_action, dict)
                else None
            ),
            "receipts": [
                {
                    "action_id": item.get("action_id"),
                    "action_kind": item.get("action_kind"),
                    "capability": item.get("capability"),
                    "phase": item.get("phase"),
                    "story": item.get("story"),
                    "receipt_hash": item.get("receipt_hash"),
                    "result": item.get("result"),
                }
                for item in frontier["receipts"]
            ],
        })
    return documents


def _control_catalog(authority: dict[str, object]) -> list[dict[str, object]]:
    state = str(authority["state"])
    allowed = {
        "tick": state == "running",
        "supervise": state == "running",
        "pause": state in {"running", "checkpoint"},
        "resume": state == "paused",
        "revoke": state in {
            "running", "checkpoint", "paused", "expired", "exhausted",
            "advisory",
        },
        "cancel": state in {
            "running", "checkpoint", "paused", "expired", "exhausted",
        },
    }
    controls = [
        {
            "action": action,
            "available": available,
            "issue": (
                None
                if available
                else (
                    f"{action} is unavailable while program permission "
                    f"is {state}"
                )
            ),
            "reason_required": action in _REASON_ACTIONS,
            "decision": None,
            "request_id": None,
            "preview_required": True,
            "starts_work": action in {"tick", "supervise"},
        }
        for action, available in allowed.items()
    ]
    for request in authority["outstanding_requests"]:
        for decision in ("approve", "reject"):
            controls.append({
                "action": "request",
                "available": request.get("status") == "open",
                "reason_required": True,
                "decision": decision,
                "request_id": request["claim_id"],
                "preview_required": True,
                "starts_work": False,
            })
    controls.extend([
        {
            "action": "retry",
            "available": False,
            "reason_required": False,
            "decision": None,
            "request_id": None,
            "preview_required": False,
            "starts_work": False,
            "issue": "retry is owned only by compiled workflow policy",
        },
        {
            "action": "elevate",
            "available": False,
            "reason_required": False,
            "decision": None,
            "request_id": None,
            "preview_required": False,
            "starts_work": False,
            "issue": "authority changes require a new program grant",
        },
    ])
    return controls


def build_program_view(
    root: Path,
    run_id: str,
    *,
    now: str | datetime | None = None,
) -> dict[str, object]:
    """Build the canonical content-safe program control-room projection."""
    authority = replay_program(root, run_id, now=now)
    conductor = replay_program_conductor(root, run_id, now=now)
    refusal: dict[str, object] | None = None
    try:
        frontier = derive_program_frontier(root, run_id, now=now)
    except DwError as exc:
        frontier = {
            "state": "stopped",
            "terminal": False,
            "checkpoint": False,
            "stop": "frontier-invalid",
            "next_actions": [],
            "lineage": None,
            "open_obligations": authority["open_obligations"],
            "open_obligation_ids": [
                item["id"] for item in authority["open_obligations"]
            ],
            "blocking_obligation_ids": [
                item["id"] for item in authority["blocking_obligations"]
            ],
        }
        refusal = {
            "code": "frontier-invalid",
            "message": exc.message[:1_000],
            "state": authority["state"],
            "ledger_head": authority["ledger_head"],
            "retryable": False,
        }
    receipts = [_safe_receipt(item) for item in conductor["receipts"]]
    next_actions = list(frontier.get("next_actions", []))
    next_action = _public_action(next_actions[0]) if next_actions else None
    selections = [
        item["payload"]
        for item in receipts
        if item["action_kind"] == "selection"
    ]
    selection = selections[-1] if selections else authority["selection"]
    roster = authority["roster"]
    active_role_addresses = {
        item.get("subject", {}).get("id")
        for item in authority["active_claims"]
        if isinstance(item.get("subject"), dict)
    }
    roles = []
    for seat in roster["seats"]:
        address = seat["address"]
        role_receipts = [
            item for item in receipts if item["role_address"] == address
        ]
        roles.append({
            "address": address,
            "role": seat["role"],
            "duty": seat["duty"],
            "slot": seat["slot"],
            "agent": seat["agent"],
            "profile": seat["profile"],
            "principal_fingerprint": seat["principal_fingerprint"],
            "assignment_generation": seat["assignment_generation"],
            "workspace_domain": seat["workspace_domain"],
            "session_binding_key": seat["session_binding_key"],
            "execution": seat["execution"],
            "authority_ceiling": seat["authority_ceiling"],
            "activity": (
                "active"
                if any(
                    isinstance(item, str) and item.startswith(str(address))
                    for item in active_role_addresses
                )
                else "complete"
                if role_receipts
                else "waiting"
            ),
            "last_result": (
                role_receipts[-1]["result"] if role_receipts else None
            ),
        })
    artifacts = [
        artifact
        for receipt in receipts
        for artifact in receipt["artifacts"]
    ]
    verdicts = [
        {
            "action_id": item["action_id"],
            "address": item["address"],
            "role": item["role"],
            "role_address": item["role_address"],
            **item["verdict"],
        }
        for item in receipts
        if isinstance(item.get("verdict"), dict)
    ]
    decisions = [
        {
            "action_id": item["action_id"],
            "address": item["address"],
            "role": item["role"],
            "decision": item["decision"],
            "obligation_ids": item["obligation_ids"],
            "result": item["result"],
        }
        for item in receipts
        if isinstance(item.get("decision"), dict)
    ]
    dissent = [
        item
        for item in decisions
        if str(item.get("result")) in {
            "dissent", "quorum-lost", "overturn", "escalate",
        }
    ]
    rounds = [
        item
        for item in receipts
        if item["action_kind"] in {
            "debate-round", "debate-proposal", "debate-critique",
            "debate-rebuttal", "debate-judgment", "meta-verdict",
            "meta-verdict-issuance", "architect-verdict",
            "architect-verdict-issuance", "council-decision",
        }
    ]
    gates = [
        item
        for item in receipts
        if item["action_kind"] in {
            "check", "verdict", "story-verification", "verdict-issuance",
            "architecture-boundary", "architecture-gate",
            "architect-verdict", "architect-verdict-issuance",
        }
    ]
    candidate = next(
        (
            artifact
            for artifact in reversed(artifacts)
            if artifact.get("artifact_kind") == "git-diff"
        ),
        None,
    )
    deliveries = _delivery_documents(root, run_id, now=now)
    integrations = [
        receipt
        for delivery in deliveries
        for receipt in delivery["receipts"]
        if receipt["action_kind"] in {
            "integration", "commit", "push", "story-complete",
            "phase-advance", "story-start",
        }
    ]
    live_progress = build_program_live_progress(
        authority,
        frontier,
        selection=selection if isinstance(selection, dict) else None,
        next_action=next_action,
        roles=roles,
        receipts=receipts,
        artifacts=artifacts,
        verdicts=verdicts,
        decisions=decisions,
        dissent=dissent,
        gates=gates,
        deliveries=deliveries,
        integrations=integrations,
    )
    timeline = tail_program_events(
        root, run_id, after_seq=0, limit=_MAX_TAIL_EVENTS
    )["events"]
    controls = _control_catalog(authority)
    bounded_actions = build_program_bounded_actions(
        authority,
        frontier,
        controls,
        live_progress,
        timeline,
        refusal=refusal,
        receipts=receipts,
    )
    stop = frontier.get("stop")
    terminal_meaning = {
        "complete": "the exact granted roadmap scope completed",
        "revoked": "the grant was revoked and cannot resume",
        "cancelled": "operator cancellation is final for this grant",
        "expired": "the finite grant lifetime ended",
        "exhausted": "a finite grant budget reached its ceiling",
        "advisory": "this grant can explain but cannot dispatch or mutate",
    }.get(
        str(authority["state"]),
        (
            f"the program stopped at {stop}"
            if stop
            else "the next act is derived only from a fresh ledger replay"
        ),
    )
    return {
        "kind": PROGRAM_VIEW_KIND,
        "schema_version": PROGRAM_SURFACE_SCHEMA_VERSION,
        "run_id": run_id,
        "program": authority["program"],
        "mode": authority["mode"],
        "state": authority["state"],
        "operational_state": frontier["state"],
        "generation": authority["generation"],
        "grant_hash": authority["grant_hash"],
        "plan_hash": authority["plan_hash"],
        "ledger_head": authority["ledger_head"],
        "event_count": authority["event_count"],
        "issued_at": authority["issued_at"],
        "expires_at": authority["expires_at"],
        "expired": authority["expired"],
        "scope": authority["scope"],
        "live_progress": live_progress,
        "bounded_actions": bounded_actions,
        "current": {
            "selection": selection,
            "lineage": frontier.get("lineage"),
            "candidate": candidate,
            "team": roster["team"],
            "organization": roster["organization"],
            "next_action": next_action,
            "stop": stop,
            "refusal": refusal,
        },
        "why": {
            "story": (
                selection.get("why") or selection.get("reason")
                if isinstance(selection, dict)
                else None
            ),
            "phase": (
                f"phase {selection.get('phase')} is the earliest eligible scoped frontier"
                if isinstance(selection, dict)
                else "the granted scope has no current roadmap candidate"
            ),
            "workflow": (
                selection.get("workflow")
                if isinstance(selection, dict)
                else None
            ),
            "team": (
                selection.get("team")
                if isinstance(selection, dict)
                else roster["team"]
            ),
            "next": (
                next_action
                if next_action is not None
                else refusal or {"stop": stop, "meaning": terminal_meaning}
            ),
        },
        "organization": {
            "slug": roster["organization"],
            "team": roster["team"],
            "roles": roles,
            "councils": roster["councils"],
            "separation": roster["separation"],
            "roster_hash": roster["roster_hash"],
            "assignment_hash": roster["assignment_hash"],
        },
        "team_review": build_live_team_review(
            {
                "slug": roster["organization"],
                "team": roster["team"],
                "roles": roles,
                "councils": roster["councils"],
                "separation": roster["separation"],
                "roster_hash": roster["roster_hash"],
                "assignment_hash": roster["assignment_hash"],
            },
            decisions,
            dissent,
            gates,
        ),
        "graph": _activity_graph(receipts, next_action),
        "activities": {
            "completed": receipts,
            "active_claims": authority["active_claims"],
            "sessions": _driver_sessions(root, run_id),
        },
        "artifacts": artifacts,
        "verdicts": verdicts,
        "decisions": decisions,
        "rounds": rounds,
        "dissent": dissent,
        "gates": gates,
        "child_runs": [
            item
            for item in receipts
            if item["action_kind"] == "child-grant"
        ],
        "deliveries": deliveries,
        "integrations": integrations,
        "obligations": {
            "all": authority["obligations"],
            "open": authority["open_obligations"],
            "blocking": authority["blocking_obligations"],
            "history": authority["obligation_history"],
        },
        "requests": authority["outstanding_requests"],
        "phase_progress": {
            "scope_phases": authority["scope"].get("phases", []),
            "scope_stories": authority["scope"].get("story_ids", []),
            "selected_phases": authority["selected_phases"],
            "selected_stories": authority["selected_stories"],
            "scope_completion": authority["scope_completion"],
        },
        "budgets": authority["budgets"],
        "stop_conditions": authority["stop_conditions"],
        "cost_accounting": authority["cost_accounting"],
        "capabilities": authority["capabilities"],
        "permanent_exclusions": authority["permanent_exclusions"],
        "timeline": timeline,
        "controls": controls,
        "terminal": authority["state"] in TERMINAL_AUTHORITY_STATES,
        "terminal_meaning": terminal_meaning,
        "privacy": {
            "list_documents_exclude": [
                "credentials", "provider argv", "prompts", "work packets",
                "transcripts", "source content", "artifact content",
            ],
            "streams_require_explicit_open": True,
            "stream_max_bytes": _MAX_STREAM_READ,
            "content_safe": True,
        },
        "starts_work": False,
        "writes_events": False,
    }


def program_summary_inventory(
    root: Path,
    *,
    now: str | datetime | None = None,
) -> dict[str, object]:
    """Return tracked policies plus replayed local grants; absent is healthy."""
    policies = program_inventory(root)
    authority = program_run_inventory(root, now=now)
    runs: list[dict[str, object]] = []
    for item in authority["runs"]:
        if item["state"] == "corrupt":
            runs.append({**item, "valid": False})
            continue
        projection = replay_program(root, str(item["run_id"]), now=now)
        try:
            frontier = derive_program_frontier(
                root, str(item["run_id"]), now=now
            )
            operational_state = frontier["state"]
            stop = frontier.get("stop")
            lineage = frontier.get("lineage")
        except DwError as exc:
            operational_state = "stopped"
            stop = "frontier-invalid"
            lineage = None
            item = {**item, "error": exc.message}
        runs.append({
            **item,
            "valid": "error" not in item,
            "operational_state": operational_state,
            "stop": stop,
            "lineage": lineage,
            "event_count": projection["event_count"],
            "active_claims": len(projection["active_claims"]),
            "outstanding_requests": len(projection["outstanding_requests"]),
            "open_obligations": len(projection["open_obligations"]),
            "blocking_obligations": len(projection["blocking_obligations"]),
            "expires_at": projection["expires_at"],
            "budgets": projection["budgets"],
        })
    return {
        "kind": PROGRAM_SUMMARY_KIND,
        "schema_version": PROGRAM_SURFACE_SCHEMA_VERSION,
        "programs": policies["programs"],
        "runs": runs,
        "healthy": bool(policies["healthy"] and authority["healthy"]),
        "starts_work": False,
        "writes_events": False,
        "creates_grant": False,
        "creates_program_store": False,
        "starts_process": False,
        "starts_stream": False,
        "starts_poller": False,
        "sends_notifications": False,
    }


def tail_program_events(
    root: Path,
    run_id: str,
    after_seq: int = 0,
    limit: int = _MAX_TAIL_EVENTS,
) -> dict[str, object]:
    """Return a verified canonical ledger suffix after one sequence cursor."""
    _require(
        isinstance(after_seq, int)
        and not isinstance(after_seq, bool)
        and after_seq >= 0,
        "program tail cursor must be a non-negative integer",
    )
    _require(
        isinstance(limit, int) and not isinstance(limit, bool),
        "program tail limit must be an integer",
    )
    limit = max(1, min(limit, _MAX_TAIL_EVENTS))
    projection = replay_program(root, run_id)
    ledger = _run_dir(root.resolve(), run_id) / "ledger.jsonl"
    events: list[dict[str, object]] = []
    try:
        lines = ledger.read_bytes().splitlines()
    except OSError as exc:
        raise DwError(f"cannot read program ledger: {exc}") from exc
    for line in lines:
        try:
            event = json.loads(line.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise DwError(f"cannot decode program ledger event: {exc}") from exc
        if int(event["seq"]) > after_seq and len(events) < limit:
            events.append(event)
    return {
        "kind": PROGRAM_TAIL_KIND,
        "schema_version": PROGRAM_SURFACE_SCHEMA_VERSION,
        "run_id": run_id,
        "after": after_seq,
        "head_seq": projection["event_count"],
        "state": projection["state"],
        "ledger_head": projection["ledger_head"],
        "events": events,
        "starts_work": False,
        "writes_events": False,
    }


def _program_stream_path(
    root: Path,
    run_id: str,
    session_id: str,
    stream: str,
) -> Path:
    _require(
        bool(_RUN_ID_RE.fullmatch(run_id or "")),
        "unsafe program run id",
    )
    _require(
        bool(_SESSION_ID_RE.fullmatch(session_id or "")),
        "unsafe program stream session id",
    )
    _require(
        stream in {"stdout", "stderr"},
        "program stream must be stdout or stderr",
    )
    directory = _run_dir(root.resolve(), run_id) / "conductor" / "driver-sessions"
    record_matches: list[dict[str, object]] = []
    if directory.is_dir() and not directory.is_symlink():
        for path in directory.glob("operation-*.json"):
            if not path.is_file() or path.is_symlink():
                continue
            try:
                value = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError) as exc:
                raise DwError(f"cannot read program stream session: {exc}") from exc
            if isinstance(value, dict) and value.get("session_id") == session_id:
                record_matches.append(value)
    _require(
        len(record_matches) == 1,
        "program stream session is absent or ambiguous",
    )
    expected = (directory / session_id).resolve()
    staging = Path(str(record_matches[0].get("staging", "")))
    _require(
        not staging.is_symlink()
        and staging.resolve() == expected
        and expected.parent == directory.resolve()
        and expected.is_dir(),
        "program stream session path is not contained",
    )
    target = expected / f"{stream}.log"
    _require(
        target.is_file()
        and not target.is_symlink()
        and target.resolve().parent == expected,
        "program stream is absent or unsafe",
    )
    return target


def read_program_stream(
    root: Path,
    run_id: str,
    session_id: str,
    stream: str,
    *,
    max_bytes: int = 20_000,
) -> dict[str, object]:
    """Explicitly open one bounded allowlisted program agent stream."""
    _require(
        isinstance(max_bytes, int)
        and not isinstance(max_bytes, bool)
        and 1 <= max_bytes <= _MAX_STREAM_READ,
        f"program stream max_bytes must be from 1 through {_MAX_STREAM_READ}",
    )
    path = _program_stream_path(root, run_id, session_id, stream)
    total = path.stat().st_size
    with path.open("rb") as handle:
        data = handle.read(max_bytes)
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65_536), b""):
            digest.update(chunk)
    return {
        "kind": PROGRAM_STREAM_KIND,
        "schema_version": PROGRAM_SURFACE_SCHEMA_VERSION,
        "run_id": run_id,
        "executor": "agent",
        "session_id": session_id,
        "stream": stream,
        "bytes": total,
        "included_bytes": len(data),
        "truncated": total > len(data),
        "sha256": "sha256:" + digest.hexdigest(),
        "content": data.decode("utf-8", errors="replace"),
        "starts_work": False,
        "writes_events": False,
    }


def document_bytes(value: object) -> bytes:
    """Canonical adapter-parity helper."""
    return canonical_json(value).encode("utf-8")
