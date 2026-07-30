"""Safe, shared interop/read models for bounded orchestration runs.

Transports are deliberately boring: they pass score/run identifiers and
fresh tokens into this module.  They never accept score documents, prompts,
provider configuration, check commands, or scheduler decisions.  The same
functions therefore back CLI, MCP, HTTP, the Workbench Run view, and the
mission-control summary without giving any adapter a second rule engine.
"""

from __future__ import annotations

import hashlib
import json
import re
import time
from datetime import datetime
from pathlib import Path

from .bounded_actions import build_run_bounded_actions
from .live_progress import build_run_live_progress
from .model import DwError
from .orchestration import canonical_json
from .orchestration_conductor import TERMINAL_STATES, schedule_decision, tick_run
from .orchestration_driver import artifact_inventory, load_driver_config
from .orchestration_run import (
    RUN_SCHEMA_VERSION,
    _grant_freshness_issues,
    _load_run_documents,
    _read_events,
    _run_dir,
    _sha,
    build_run_plan,
    decide_checkpoint,
    decide_outstanding_request,
    replay_run,
    run_inventory,
    start_run,
    transition_run,
)


RUN_ACT_PREVIEW_KIND = "delivery-workbench-run-act-preview"
RUN_VIEW_KIND = "delivery-workbench-run-view"
RUN_SUMMARY_KIND = "delivery-workbench-run-summary-list"
RUN_STREAM_KIND = "delivery-workbench-run-stream"
RUN_SUPERVISION_SURFACE_KIND = "delivery-workbench-run-surface-supervision"
RUN_SURFACE_SCHEMA_VERSION = 1

_ACTIONS = {
    "tick", "supervise", "pause", "resume", "revoke", "cancel",
    "checkpoint", "request",
}
_SAFE_EXECUTION_ID = re.compile(r"^(?:session|check)-[A-Za-z0-9_.:-]{1,127}$")
_MAX_STREAM_READ = 100_000


def start_run_by_id(
    root: Path,
    score: str,
    project: str | None,
    story: str,
    issued_at: str,
    expires_at: str,
    expect: str,
    *,
    approved: bool,
    approved_by: str,
    standing_nudges: object = None,
    signal_channel: str | None = None,
    now: datetime | None = None,
) -> dict[str, object]:
    """Rebuild and consume one plan without accepting caller-owned semantics."""
    plan = build_run_plan(
        root,
        score,
        project,
        story,
        issued_at=issued_at,
        expires_at=expires_at,
        standing_nudges=standing_nudges,
        signal_channel=signal_channel,
    )
    return start_run(
        root,
        plan,
        expect,
        approved=approved,
        approved_by=approved_by,
        now=now,
    )


def _act_applicability(
    root: Path,
    projection: dict[str, object],
    action: str,
    reason: str,
    decision: str,
    correlation_id: str = "",
) -> list[str]:
    state = str(projection["state"])
    issues: list[str] = []
    if action not in _ACTIONS:
        raise DwError(f"unsupported run act: {action}")
    if action in {"pause", "revoke", "cancel"} and not reason:
        issues.append(f"run {action} requires a reason")
    if action in {"tick", "supervise", "resume", "checkpoint", "request"} and reason:
        issues.append(f"run {action} does not accept a reason")
    if len(reason) > 200 or "\n" in reason or "\0" in reason:
        issues.append("run act reason must be a bounded single line")
    if action not in {"checkpoint", "request"} and decision:
        issues.append(f"run {action} does not accept a checkpoint decision")
    if action not in {"checkpoint", "request"} and correlation_id:
        issues.append(f"run {action} does not accept a request correlation id")

    if action in {"tick", "supervise"}:
        if (
            state in TERMINAL_STATES
            and state != "awaiting-certification"
            and projection["outstanding_requests"]
        ):
            # Recover a crash after terminal authority was ledgered but before
            # its outstanding requests were expired. This tick dispatches no
            # work; the conductor's first act is request maintenance.
            pass
        elif state == "awaiting-certification":
            # A tick here observes external commits and evaluates the
            # score's declared nudge rules — the sanctioned wake. With no
            # rules declared there is nothing a tick could do.
            _run_path, _grant, compiled = _load_run_documents(
                root, str(projection["run_id"])
            )
            if not compiled["score"].get("nudges"):
                issues.append(f"cannot {action} a run in state {state}")
        elif state == "awaiting-approval" and projection["outstanding_requests"]:
            # A restart maintenance tick republishes/ages requests but cannot
            # dispatch while a human decision is outstanding.
            pass
        elif state != "active":
            issues.append(f"cannot {action} a run in state {state}")
        elif not projection["dispatch_allowed"]:
            issues.append("run grant does not currently permit dispatch")
    elif action == "pause":
        pausable = (
            (state == "active" and projection["dispatch_allowed"])
            or (state == "awaiting-approval" and projection["outstanding_requests"])
        )
        if not pausable:
            issues.append(f"cannot pause a run in state {state}")
    elif action == "resume":
        resumable = (
            state == "paused"
            and (not projection["expired"] or projection["outstanding_requests"])
        )
        if not resumable:
            issues.append(f"cannot resume a run in state {state}")
        else:
            _run_path, grant, _compiled = _load_run_documents(
                root, str(projection["run_id"])
            )
            issues.extend(_grant_freshness_issues(root, grant, projection))
    elif action in {"revoke", "cancel"}:
        if state not in {"active", "paused", "awaiting-approval"}:
            issues.append(f"cannot {action} a run in state {state}")
    elif action in {"checkpoint", "request"}:
        requests = list(projection["outstanding_requests"])
        if action == "checkpoint":
            requests = [item for item in requests if item["kind"] == "checkpoint"]
        if not requests:
            issues.append("run has no matching outstanding request")
        elif not correlation_id:
            issues.append("request response requires a correlation id")
        else:
            matching = next(
                (
                    item for item in requests
                    if item["correlation_id"] == correlation_id
                ),
                None,
            )
            # A mismatch remains applicable: applying the exact preview
            # records a correlation-mismatch refusal without consuming the
            # live request. A matching request must be in a decidable state.
            if matching is not None:
                if matching["kind"] == "checkpoint" and state != "awaiting-approval":
                    issues.append("checkpoint request is not currently decidable")
                if matching["kind"] == "nudge" and state not in {
                    "active", "awaiting-certification",
                }:
                    issues.append("nudge request is not currently decidable")
    return issues


def build_run_act_preview(
    root: Path,
    run_id: str,
    action: str,
    *,
    reason: str = "",
    decision: str = "",
    correlation_id: str = "",
    max_ticks: int = 100,
    max_seconds: int = 300,
    now: datetime | None = None,
) -> dict[str, object]:
    """Build a pure action+parameter+ledger-bound confirmation document."""
    action = str(action or "").strip().lower()
    reason = str(reason or "").strip()
    decision = str(decision or "").strip().lower()
    if action == "supervise":
        if (
            isinstance(max_ticks, bool)
            or not isinstance(max_ticks, int)
            or not 1 <= max_ticks <= 10_000
        ):
            raise DwError("run max_ticks must be between 1 and 10000")
        if (
            isinstance(max_seconds, bool)
            or not isinstance(max_seconds, int)
            or not 1 <= max_seconds <= 86_400
        ):
            raise DwError("run max_seconds must be between 1 and 86400")
    projection = replay_run(root, run_id, now=now)
    correlation_id = str(correlation_id or "").strip()
    if action == "checkpoint" and not correlation_id:
        pending = projection.get("pending_checkpoint")
        if isinstance(pending, dict):
            correlation_id = str(pending.get("correlation_id") or "")
    issues = _act_applicability(
        root, projection, action, reason, decision, correlation_id
    )
    pending = projection.get("pending_checkpoint")
    pending_summary = None
    if isinstance(pending, dict):
        pending_summary = {
            key: pending.get(key)
            for key in (
                "node_id", "checkpoint", "mode", "terminal", "reason",
                "correlation_id",
            )
        }
    eligible_requests = list(projection["outstanding_requests"])
    if action == "checkpoint":
        eligible_requests = [
            item for item in eligible_requests if item["kind"] == "checkpoint"
        ]
    request = next(
        (
            item for item in eligible_requests
            if item["correlation_id"] == correlation_id
        ),
        None,
    )
    request_summary = None if request is None else {
        key: request.get(key)
        for key in (
            "correlation_id", "kind", "origin", "origin_node",
            "schema_summary", "opened_at", "expires_at",
        )
    }
    unsigned: dict[str, object] = {
        "kind": RUN_ACT_PREVIEW_KIND,
        "schema_version": RUN_SURFACE_SCHEMA_VERSION,
        "run_id": run_id,
        "action": action,
        "applicable": not issues,
        "issues": issues,
        "state": projection["state"],
        "generation": projection["control_generation"],
        "control_generation": projection["control_generation"],
        "ledger_head": projection["ledger_head"],
        "reason": reason,
        "decision": decision,
        "correlation_id": correlation_id,
        "max_ticks": max_ticks,
        "max_seconds": max_seconds,
        "pending_checkpoint": pending_summary,
        "outstanding_request": request_summary,
        "response_outcome": (
            "correlation-mismatch" if action in {"checkpoint", "request"}
            and request is None else "invalid-response"
            if action in {"checkpoint", "request"}
            and request is not None
            and decision not in request["response_schema"]["decision"]
            else "decision"
        ),
        "starts_work": action in {"tick", "supervise"} and projection["state"] == "active",
        "writes_events": False,
    }
    return {**unsigned, "act_token": _sha(unsigned)}


def _consume_run_supervision_token(
    root: Path,
    run_id: str,
    preview: dict[str, object],
) -> None:
    """Atomically consume one supervision token even when its pass makes no progress."""
    token = str(preview["act_token"])
    directory = _run_dir(root, run_id) / "supervision-tokens"
    directory.mkdir(mode=0o700, parents=True, exist_ok=True)
    receipt = directory / f"{hashlib.sha256(token.encode('utf-8')).hexdigest()}.json"
    document = {
        "kind": "delivery-workbench-run-supervision-token-use",
        "schema_version": RUN_SURFACE_SCHEMA_VERSION,
        "run_id": run_id,
        "action": preview["action"],
        "ledger_head": preview["ledger_head"],
        "generation": preview["generation"],
        "max_ticks": preview["max_ticks"],
        "max_seconds": preview["max_seconds"],
        "token_hash": hashlib.sha256(token.encode("utf-8")).hexdigest(),
    }
    try:
        with receipt.open("x", encoding="utf-8") as handle:
            handle.write(canonical_json(document) + "\n")
        receipt.chmod(0o600)
    except FileExistsError as exc:
        raise DwError(
            "run supervision token already used; no work started and no event was appended"
        ) from exc


def _supervise_run_surface(
    root: Path,
    run_id: str,
    *,
    ledger_head: str,
    max_ticks: int,
    max_seconds: int,
    now: datetime | None = None,
) -> dict[str, object]:
    """Repeat only canonical run ticks inside one finite approved envelope."""
    started = time.monotonic()
    expected_head = ledger_head
    ticks: list[dict[str, object]] = []
    stop = "tick-ceiling"
    for _index in range(max_ticks):
        if time.monotonic() - started >= max_seconds:
            stop = "time-ceiling"
            break
        tick = tick_run(root, run_id, expect=expected_head, now=now)
        ticks.append(tick)
        expected_head = str(tick["after_head"])
        if tick["terminal"]:
            stop = "terminal"
            break
        if tick["state"] in {"paused", "awaiting-approval"}:
            stop = "checkpoint"
            break
        if not tick["progressed"]:
            stop = "no-progress"
            break
    last = ticks[-1] if ticks else None
    return {
        "kind": RUN_SUPERVISION_SURFACE_KIND,
        "schema_version": RUN_SURFACE_SCHEMA_VERSION,
        "run_id": run_id,
        "ticks": ticks,
        "tick_count": len(ticks),
        "stop": stop,
        "state": last["state"] if last else "not-started",
        "terminal": bool(last and last["terminal"]),
        "checkpoint": bool(
            last and last["state"] in {"paused", "awaiting-approval"}
        ),
        "progressed": any(bool(item["progressed"]) for item in ticks),
        "before_head": ledger_head,
        "after_head": expected_head,
        "max_ticks": max_ticks,
        "max_seconds": max_seconds,
        "bounded": True,
        "content_safe": True,
    }


def apply_run_act(
    root: Path,
    run_id: str,
    action: str,
    expect: str,
    *,
    reason: str = "",
    decision: str = "",
    correlation_id: str = "",
    max_ticks: int = 100,
    max_seconds: int = 300,
    now: datetime | None = None,
) -> dict[str, object]:
    """Apply exactly the fresh preview; no caller-supplied runtime semantics."""
    preview = build_run_act_preview(
        root, run_id, action, reason=reason, decision=decision,
        correlation_id=correlation_id, max_ticks=max_ticks,
        max_seconds=max_seconds, now=now
    )
    if str(expect or "") != preview["act_token"]:
        raise DwError(
            "stale or altered run act token refused; no work started and no event was appended"
        )
    if not preview["applicable"]:
        raise DwError("run act is not applicable: " + "; ".join(preview["issues"]))
    ledger_head = str(preview["ledger_head"])
    if action == "tick":
        return tick_run(root, run_id, expect=ledger_head, now=now)
    if action == "supervise":
        _consume_run_supervision_token(root, run_id, preview)
        return _supervise_run_surface(
            root,
            run_id,
            ledger_head=ledger_head,
            max_ticks=max_ticks,
            max_seconds=max_seconds,
            now=now,
        )
    if action == "checkpoint":
        if correlation_id:
            return decide_outstanding_request(
                root, run_id, correlation_id, decision, ledger_head, now=now,
                expected_kind="checkpoint",
            )
        return decide_checkpoint(root, run_id, decision, ledger_head, now=now)
    if action == "request":
        return decide_outstanding_request(
            root, run_id, correlation_id, decision, ledger_head, now=now
        )
    return transition_run(
        root, run_id, action, ledger_head, reason=reason, now=now
    )


def _read_records(directory: Path, pattern: str, label: str) -> list[dict[str, object]]:
    if not directory.is_dir():
        return []
    records: list[dict[str, object]] = []
    for path in sorted(directory.glob(pattern), key=lambda item: item.name):
        if not path.is_file() or path.is_symlink():
            continue
        try:
            value = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise DwError(f"cannot read {label} record {path.name}: {exc}") from exc
        if not isinstance(value, dict):
            raise DwError(f"{label} record {path.name} must be an object")
        records.append(value)
    return records


def _driver_sessions(run_dir: Path) -> list[dict[str, object]]:
    sessions: list[dict[str, object]] = []
    for record in _read_records(run_dir / "driver-sessions", "session-*.json", "driver session"):
        receipt = record.get("receipt")
        if not isinstance(receipt, dict):
            continue
        sessions.append({
            key: receipt.get(key)
            for key in (
                "run_id", "node_id", "attempt", "claim_id", "profile",
                "adapter", "session_id", "state", "activity", "started",
                "exit_code", "reason", "started_at", "updated_at",
                "stdout_bytes", "stderr_bytes",
            )
        })
    return sessions


def _check_sessions(run_dir: Path) -> list[dict[str, object]]:
    sessions: list[dict[str, object]] = []
    for record in _read_records(run_dir / "check-sessions", "*.json", "check session"):
        if not str(record.get("execution_id", "")).startswith("check-"):
            continue
        sessions.append({
            key: record.get(key)
            for key in (
                "run_id", "node_id", "attempt", "claim_id", "execution_id",
                "runner_kind", "runner_hash", "workspace_identity", "state",
                "started", "reason", "expected_exit_code", "actual_exit_code",
                "timeout_seconds", "stdout_bytes", "stderr_bytes",
                "stdout_truncated", "stderr_truncated", "changed_paths",
                "started_at", "finished_at",
            )
        })
    return sessions


def _rail_sessions(run_dir: Path) -> list[dict[str, object]]:
    sessions: list[dict[str, object]] = []
    for record in _read_records(run_dir / "rail-sessions", "*.json", "rail session"):
        sessions.append({
            key: record.get(key)
            for key in (
                "run_id", "node_id", "attempt", "claim_id", "execution_id",
                "action", "state", "reason", "started", "outcome",
                "exit_code", "before", "after", "next_action",
            )
            if key in record
        })
    return sessions


def _node_document(
    node: dict[str, object], state: dict[str, object]
) -> dict[str, object]:
    outputs = []
    for output in node.get("outputs", []):
        if not isinstance(output, dict):
            continue
        outputs.append({
            key: output.get(key)
            for key in (
                "name", "format", "path", "schema", "required_sections",
                "citations", "max_bytes", "allowed_paths",
            )
            if key in output
        })
    runner = node.get("runner") if isinstance(node.get("runner"), dict) else None
    runner_summary = None
    if runner is not None:
        runner_summary = {
            key: runner.get(key)
            for key in (
                "kind", "name", "path", "schema", "allowed_paths",
                "timeout_seconds", "output_bytes", "writes",
            )
            if key in runner
        }
        runner_summary["runner_hash"] = _sha(runner)
    return {
        "id": node["id"],
        "type": node["type"],
        "title": node.get("title") or node["id"],
        "activation": node.get("activation", "success"),
        "needs": list(node.get("needs", [])),
        "resource_groups": list(node.get("resource_groups", [])),
        "role": node.get("role"),
        "profile": node.get("profile"),
        "workspace": node.get("workspace"),
        "capabilities": list(node.get("capabilities", [])),
        "runner": runner_summary,
        "rail_action": node.get("action") if node.get("type") == "rail" else None,
        "terminal": node.get("terminal") if node.get("type") == "approval" else None,
        "options": list(node.get("options", [])) if node.get("type") == "approval" else [],
        "on_failure": node.get("on_failure"),
        "outputs": outputs,
        "state": state.get("state", "unknown"),
        "attempt": state.get("attempt", 0),
        "blocked_reason": state.get("blocked_reason"),
    }


def _control_catalog(
    root: Path, projection: dict[str, object]
) -> list[dict[str, object]]:
    controls: list[dict[str, object]] = []
    candidates = [
        ("tick", False, "", True, ""),
        ("supervise", False, "", True, ""),
        ("pause", True, "", False, ""),
        ("resume", False, "", False, ""),
        ("revoke", True, "", False, ""),
        ("cancel", True, "", False, ""),
    ]
    for request in projection["outstanding_requests"]:
        for option in request["response_schema"]["decision"]:
            candidates.append((
                "request", False, str(option), False,
                str(request["correlation_id"]),
            ))
    for action, reason_required, decision, starts_work, correlation_id in candidates:
        reason = "operator reason required" if reason_required else ""
        issues = _act_applicability(
            root, projection, action, reason, decision, correlation_id
        )
        # The placeholder satisfies shape validation only; the UI must collect
        # the real reason and request a new exact preview before confirming.
        if reason_required:
            issues = [issue for issue in issues if "requires a reason" not in issue]
        controls.append({
            "action": action,
            "decision": decision,
            "correlation_id": correlation_id,
            "available": not issues,
            "issues": issues,
            "reason_required": reason_required,
            "preview_required": True,
            "starts_work": (
                starts_work and projection["state"] == "active"
            ),
        })
    controls.extend([
        {
            "action": "retry",
            "decision": "",
            "available": False,
            "issues": ["retry is governed only by the immutable score failure policy"],
            "reason_required": False,
            "preview_required": False,
            "starts_work": False,
        },
        {
            "action": "elevate",
            "decision": "",
            "available": False,
            "issues": ["authority elevation requires a new grant and is never a run act"],
            "reason_required": False,
            "preview_required": False,
            "starts_work": False,
        },
    ])
    return controls


def _decision_tree(history: list[dict[str, object]]) -> dict[str, object]:
    children: dict[str, list[str]] = {
        str(item["correlation_id"]): [] for item in history
    }
    roots: list[str] = []
    for item in history:
        correlation = str(item["correlation_id"])
        parent = str(item.get("parent_correlation_id") or "")
        if parent and parent in children:
            children[parent].append(correlation)
        else:
            roots.append(correlation)
    nodes = []
    for item in history:
        correlation = str(item["correlation_id"])
        nodes.append({
            key: item.get(key)
            for key in (
                "correlation_id", "parent_correlation_id", "kind", "origin",
                "origin_node", "status", "opened_seq", "opened_at",
                "decision", "decision_seq", "schema_summary", "preview",
            )
        } | {"children": children[correlation]})
    return {"roots": roots, "nodes": nodes, "inspect_only": True}


def build_run_view(
    root: Path, run_id: str, *, now: datetime | None = None
) -> dict[str, object]:
    """Build the content-safe, read-only explanation/consent model."""
    run_dir, _grant, compiled = _load_run_documents(root, run_id)
    projection = replay_run(root, run_id, now=now)
    artifacts = artifact_inventory(root, run_id)
    decision = schedule_decision(compiled, projection, artifacts)
    blocked = {
        str(item["node_id"]): str(item["reason"])
        for item in decision["blocked"]
    }
    states = {
        str(item["node_id"]): {**item, "blocked_reason": blocked.get(str(item["node_id"]))}
        for item in decision["node_states"]
    }
    pending = projection.get("pending_checkpoint")
    if isinstance(pending, dict):
        node_id = str(pending["node_id"])
        states[node_id] = {
            "node_id": node_id,
            "state": "awaiting-approval",
            "attempt": 0,
            "blocked_reason": str(pending.get("reason") or "checkpoint"),
        }
    graph_nodes = [
        _node_document(node, states.get(str(node["id"]), {}))
        for node in compiled["score"]["nodes"]
    ]
    safe_artifacts = [
        {
            key: artifact.get(key)
            for key in (
                "run_id", "node_id", "attempt", "name", "format", "bytes",
                "sha256", "path", "valid", "checks",
            )
        }
        for artifact in artifacts
    ]
    events = _read_events(run_dir, run_id)
    live_progress = build_run_live_progress(
        projection,
        decision,
        graph_nodes,
        safe_artifacts,
        events,
    )
    controls = _control_catalog(root, projection)
    bounded_actions = build_run_bounded_actions(
        projection,
        decision,
        graph_nodes,
        controls,
        live_progress,
        events,
    )
    terminal = projection["state"] in TERMINAL_STATES
    terminal_meaning = {
        "awaiting-certification": "work is handed back for human inspection, certification, and commit",
        "blocked": "the bounded policy stopped; inspect failure routes and receipts",
        "cancelled": "operator cancellation is final for this grant",
        "revoked": "the grant authority was revoked and cannot resume",
        "complete": "the score declared a complete terminal",
    }.get(str(projection["state"]), "the conductor may advance only through a fresh tick preview")
    return {
        "kind": RUN_VIEW_KIND,
        "schema_version": RUN_SURFACE_SCHEMA_VERSION,
        "run_id": run_id,
        "score": projection["score"],
        "project": projection["project"],
        "story": {
            key: projection["story"].get(key)
            for key in ("id", "title", "status", "phase", "story_path")
        },
        "state": projection["state"],
        "dispatch_allowed": projection["dispatch_allowed"],
        "expired": projection["expired"],
        "expires_at": projection["expires_at"],
        "control_generation": projection["control_generation"],
        "ledger_head": projection["ledger_head"],
        "ledger_events": projection["ledger_events"],
        "live_progress": live_progress,
        "bounded_actions": bounded_actions,
        "graph": {
            "nodes": graph_nodes,
            "layout": compiled.get("layout", {}),
            "eligible": decision["eligible"],
            "scheduled_on_confirm": decision["scheduled"],
            "active_resource_groups": decision["active_resource_groups"],
        },
        "attempts": {
            "active": projection["active_claims"],
            "completed": projection["completed_claims"],
            "receipts": projection["node_receipts"],
        },
        "sessions": {
            "agents": _driver_sessions(run_dir),
            "checks": _check_sessions(run_dir),
            "rails": _rail_sessions(run_dir),
        },
        "artifacts": safe_artifacts,
        "budgets": projection["budgets"],
        "nudges": projection["nudges"],
        "routes": projection["routes"],
        "checkpoints": projection["checkpoints"],
        "pending_checkpoint": projection["pending_checkpoint"],
        "outstanding_requests": projection["outstanding_requests"],
        "decision_tree": _decision_tree(projection["request_history"]),
        "request_refusals": projection["request_refusals"],
        "fact_binding": projection["fact_binding"],
        "external_commits": projection["external_commits"],
        "timeline": events,
        "controls": controls,
        "terminal": terminal,
        "terminal_meaning": terminal_meaning,
        "privacy": {
            "list_documents_exclude": [
                "credentials", "provider argv", "check argv", "prompts",
                "packets", "transcripts", "source content", "artifact content",
            ],
            "streams_require_explicit_open": True,
            "stream_max_bytes": _MAX_STREAM_READ,
        },
        "starts_work": False,
        "writes_events": False,
    }


def run_summary_inventory(
    root: Path, *, now: datetime | None = None
) -> dict[str, object]:
    """Content-free mission-control summary over authoritative projections."""
    try:
        source = run_inventory(root, now=now)
    except DwError as exc:
        # Roadmap parsing and its state feed are also supported in unpacked,
        # not-yet-installed directories.  Such a directory cannot contain a
        # run ledger, so its truthful orchestration inventory is empty.  Keep
        # all other run-store errors visible rather than masking corruption.
        if exc.message != "orchestration runs require a Git repository":
            raise
        source = {"runs": []}
    summaries: list[dict[str, object]] = []
    for item in source["runs"]:
        if not item["valid"]:
            summaries.append({
                "run_id": item["run_id"], "valid": False, "error": item["error"],
            })
            continue
        run = item["run"]
        summaries.append({
            "run_id": run["run_id"],
            "valid": True,
            "state": run["state"],
            "score": run["score"]["slug"],
            "project": run["project"],
            "story": run["story"]["id"],
            "active_claims": len(run["active_claims"]),
            "completed_claims": len(run["completed_claims"]),
            "outstanding_requests": len(run["outstanding_requests"]),
            "ledger_events": run["ledger_events"],
            "ledger_head": run["ledger_head"],
            "expired": run["expired"],
            "expires_at": run["expires_at"],
            "budgets": run["budgets"],
        })
    return {
        "kind": RUN_SUMMARY_KIND,
        "schema_version": RUN_SURFACE_SCHEMA_VERSION,
        "runs": summaries,
        "starts_work": False,
        "writes_events": False,
    }


def _contained_stream_path(
    root: Path,
    run_id: str,
    executor: str,
    execution_id: str,
    stream: str,
) -> Path:
    if executor not in {"agent", "check"}:
        raise DwError("run stream executor must be agent or check")
    if not _SAFE_EXECUTION_ID.fullmatch(execution_id or ""):
        raise DwError("unsafe run stream execution id")
    if stream not in {"stdout", "stderr"}:
        raise DwError("run stream must be stdout or stderr")
    run_dir = _run_dir(root, run_id)
    if executor == "check":
        if not execution_id.startswith("check-"):
            raise DwError("check stream id must begin with check-")
        directory = run_dir / "check-sessions" / execution_id
    else:
        if not execution_id.startswith("session-"):
            raise DwError("agent stream id must begin with session-")
        record_path = run_dir / "driver-sessions" / f"{execution_id}.json"
        if not record_path.is_file() or record_path.is_symlink():
            raise DwError("agent stream session record is absent")
        try:
            record = json.loads(record_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise DwError(f"cannot read agent stream session: {exc}") from exc
        if record.get("session_id") != execution_id:
            raise DwError("agent stream session identity mismatch")
        directory = Path(str(record.get("staging", "")))
        resolved = directory.resolve()
        config = load_driver_config(root)
        configured = config.get("workspace_root")
        if configured:
            workspace_base = Path(str(configured)).resolve()
        else:
            tag = hashlib.sha256(str(root.resolve()).encode("utf-8")).hexdigest()[:16]
            workspace_base = (
                root.resolve().parent / ".delivery-workbench-workspaces" / tag
            ).resolve()
        expected = (workspace_base / run_id / "sessions" / execution_id).resolve()
        if (
            directory.is_symlink()
            or resolved != expected
            or resolved.name != execution_id
            or resolved.parent.name != "sessions"
            or resolved.parent.parent.name != run_id
        ):
            raise DwError("agent stream staging path is not contained by run/session identity")
        directory = resolved
    if not directory.is_dir() or directory.is_symlink():
        raise DwError("run stream directory is absent or unsafe")
    target = directory / f"{stream}.log"
    if not target.is_file() or target.is_symlink() or target.resolve().parent != directory.resolve():
        raise DwError("run stream is absent or unsafe")
    return target


RUN_TAIL_KIND = "delivery-workbench-run-tail"
SIGNAL_TAIL_KIND = "delivery-workbench-signal-tail"
_MAX_TAIL_EVENTS = 1000


def _tail_lines(path: Path, after_seq: int, limit: int) -> tuple[list[dict[str, object]], int]:
    events: list[dict[str, object]] = []
    head = -1
    for offset, line in enumerate(path.read_bytes().splitlines()):
        head = offset
        if offset <= after_seq or len(events) >= limit:
            continue
        events.append(json.loads(line.decode("utf-8")))
    return events, head


def tail_run_events(
    root: Path, run_id: str, after_seq: int = -1, limit: int = _MAX_TAIL_EVENTS
) -> dict[str, object]:
    """The verified ledger suffix after a cursor.

    Pure read with no authority: every event is the canonical hash-chained
    ledger line (ids, hashes, states, bounded scalar details) — never a
    token, prompt, transcript, or artifact body. Replay validates the
    whole chain before a single line is emitted, so a corrupt ledger
    fails closed instead of streaming.
    """
    if isinstance(after_seq, bool) or not isinstance(after_seq, int) or after_seq < -1:
        raise DwError("tail cursor must be an integer sequence, or -1 for the start")
    limit = max(1, min(int(limit), _MAX_TAIL_EVENTS))
    projection = replay_run(root, run_id)
    run_dir, _grant, _compiled = _load_run_documents(root, run_id)
    events, head = _tail_lines(run_dir / "ledger.jsonl", after_seq, limit)
    return {
        "kind": RUN_TAIL_KIND,
        "schema_version": RUN_SURFACE_SCHEMA_VERSION,
        "run_id": run_id,
        "after": after_seq,
        "head_seq": head,
        "state": projection["state"],
        "events": events,
        "starts_work": False,
        "writes_events": False,
    }


def tail_signal_events(
    root: Path, remote: str, branch: str,
    after_seq: int = -1, limit: int = _MAX_TAIL_EVENTS,
) -> dict[str, object]:
    """The verified signal-chain suffix after a cursor; pure read."""
    from .signals import _channel_dir, replay_channel

    if isinstance(after_seq, bool) or not isinstance(after_seq, int) or after_seq < -1:
        raise DwError("tail cursor must be an integer sequence, or -1 for the start")
    limit = max(1, min(int(limit), _MAX_TAIL_EVENTS))
    projection = replay_channel(root, remote, branch)
    chain = _channel_dir(root, remote, branch) / "signals.jsonl"
    events, head = _tail_lines(chain, after_seq, limit)
    return {
        "kind": SIGNAL_TAIL_KIND,
        "schema_version": RUN_SURFACE_SCHEMA_VERSION,
        "channel": projection["channel"],
        "after": after_seq,
        "head_seq": head,
        "status": projection["status"],
        "events": events,
        "starts_work": False,
        "writes_events": False,
    }


def read_run_stream(
    root: Path,
    run_id: str,
    executor: str,
    execution_id: str,
    stream: str,
    *,
    max_bytes: int = 20_000,
) -> dict[str, object]:
    """Explicitly open one allowlisted log, bounded independently of its source."""
    if isinstance(max_bytes, bool) or not isinstance(max_bytes, int) or not 1 <= max_bytes <= _MAX_STREAM_READ:
        raise DwError(f"stream max_bytes must be from 1 through {_MAX_STREAM_READ}")
    path = _contained_stream_path(root, run_id, executor, execution_id, stream)
    total = path.stat().st_size
    with path.open("rb") as handle:
        data = handle.read(max_bytes)
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65_536), b""):
            digest.update(chunk)
    return {
        "kind": RUN_STREAM_KIND,
        "schema_version": RUN_SURFACE_SCHEMA_VERSION,
        "run_id": run_id,
        "executor": executor,
        "execution_id": execution_id,
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
    """Canonical adapter-parity helper used by the test suite."""
    return canonical_json(value).encode("utf-8")
