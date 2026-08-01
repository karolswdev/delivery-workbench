"""The MCP stdio server: a thin JSON adapter over the dw core.

Implements the surface contract (docs/mcp.md): newline-delimited
JSON-RPC 2.0 over stdio, protocol version pinned, tools-only
capability, strictly serial loop, python stdlib only. Every tool
calls the same ``dw_pmo`` core function the CLI calls — there is no
rule logic here, and any conditional that consults roadmap semantics
instead of the core is a defect (Phase 6 invariant).

Deliberately absent, by contract: certification, commits, and bundle
consent. Attestation is not a tool call.

``DwError`` from the core becomes a tool-level error carrying the
same refusal text the CLI prints; malformed input becomes a JSON-RPC
error and never kills the loop.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from .model import DwError

PROTOCOL_VERSION = "2025-06-18"
SERVER_NAME = "delivery-workbench"

# JSON-RPC error codes.
PARSE_ERROR = -32700
INVALID_REQUEST = -32600
METHOD_NOT_FOUND = -32601
INVALID_PARAMS = -32602
INTERNAL_ERROR = -32603


def _missing_rails_message(root: Path) -> str:
    return (
        f"no Delivery Workbench rails at {root} (missing pm/roadmap or .githooks/dw). "
        "Adopt the repository first: dw install <repo> --skip-bootstrap "
        "(see docs/distribution.md)."
    )


def _has_rails(root: Path) -> bool:
    from .paths import roadmap_dir

    try:
        roadmap_dir(root)
    except DwError:
        return False
    return True


# ── tool implementations (thin adapters; core does the thinking) ────

def _tool_status(root: Path, args: dict) -> tuple[str, dict]:
    from .status import build_status, render_status

    payload = build_status(root, args.get("project"))
    return render_status(payload).rstrip("\n"), payload


def _tool_knowledge_map(root: Path, args: dict) -> tuple[str, dict]:
    from .repository_map import read_symbol_map

    payload = read_symbol_map(root)
    return json.dumps(payload, sort_keys=True, separators=(",", ":")), payload


def _tool_knowledge_ground(root: Path, args: dict) -> tuple[str, dict]:
    from .grounding import ground_project_story
    from .parse import get_project

    project = get_project(root, str(args["project"]))
    payload = ground_project_story(root, project, str(args["story"]))
    return json.dumps(payload, sort_keys=True, separators=(",", ":")), payload


def _tool_knowledge_lessons(root: Path, args: dict) -> tuple[str, dict]:
    from .knowledge import build_lesson_inventory

    payload = build_lesson_inventory(root)
    return json.dumps(payload, sort_keys=True, separators=(",", ":")), payload


def _tool_knowledge_recall(root: Path, args: dict) -> tuple[str, dict]:
    from .memory_read import build_memory_recall_projection, render_memory_projection

    payload = build_memory_recall_projection(
        root, run=args.get("run"), program=args.get("program")
    )
    return render_memory_projection(payload), payload


def _tool_knowledge_writebacks(root: Path, args: dict) -> tuple[str, dict]:
    from .memory_read import build_memory_writeback_projection, render_memory_projection

    payload = build_memory_writeback_projection(
        root,
        run=args.get("run"),
        program=args.get("program"),
        story=args.get("story"),
        state=args.get("state"),
    )
    return render_memory_projection(payload), payload


def _tool_step(root: Path, args: dict) -> tuple[str, dict]:
    from .step import build_step, render_step

    payload = build_step(root, args.get("project"))
    return render_step(payload).rstrip("\n"), payload


def _tool_step_apply(root: Path, args: dict) -> tuple[str, dict]:
    from .step import apply_step

    payload, _exit_code = apply_step(
        root,
        args.get("project"),
        str(args["expect"]),
    )
    return json.dumps(payload, sort_keys=True), payload


def _tool_setup_preview(root: Path, args: dict) -> tuple[str, dict]:
    from .setup_lease import canonical_setup_preview, preview_setup

    payload = preview_setup(root, Path(str(args["proposal_file"])))
    return canonical_setup_preview(payload), payload


def _tool_setup_apply(root: Path, args: dict) -> tuple[str, dict]:
    from .setup_lease import apply_setup

    payload = apply_setup(root, str(args["proposal"]), str(args["expect"]))
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False), payload


def _tool_context(root: Path, args: dict) -> tuple[str, dict]:
    from .api import build_context_payload
    from .parse import discover_projects, get_project

    project = args.get("project")
    projects = [get_project(root, project)] if project else discover_projects(root)
    payload = build_context_payload(root, projects)
    if args.get("compact"):
        text = json.dumps(payload, sort_keys=True)
    else:
        text = json.dumps(payload, indent=2, sort_keys=True)
    return text, payload


def _tool_next(root: Path, args: dict) -> tuple[str, dict]:
    from .api import next_story, parked_headline, parked_summary
    from .parse import get_project

    project = get_project(root, args.get("project"))
    found = next_story(project, root)
    if found is None:
        parked = parked_summary(project, root)
        headline = parked_headline(parked)
        tail = f"; parked: {headline} — see dw holds" if headline else ""
        return (
            f"dw next: nothing actionable (no in-progress, ready, or backlog stories){tail}",
            {"next_story": None, "parked": parked},
        )
    text = f"{found['story_id']}\t{found['status']}\t{found['phase_path']}\t{found['title']}"
    return text, {"next_story": found}


def _tool_check(root: Path, args: dict) -> tuple[str, dict]:
    from .grounding import grounding_warnings
    from .parse import discover_projects, get_project
    from .riderdocs import rider_docs_issues
    from .validate import check_project

    project = args.get("project")
    projects = [get_project(root, project)] if project else discover_projects(root)
    issues: list[str] = []
    warnings: list[str] = []
    for proj in projects:
        issues.extend(check_project(proj, root))
        warnings.extend(grounding_warnings(proj, root))
    # Repo-level: rendered agent surfaces must match canon (WLA-12-04).
    issues.extend(rider_docs_issues(root))
    lines = [f"ERROR {issue}" for issue in issues]
    lines.extend(f"WARNING {warning}" for warning in warnings)
    if not issues:
        lines.append("dw check: ok")
    structured = {"ok": not issues, "issues": issues}
    if warnings:
        structured["warnings"] = warnings
    return "\n".join(lines), structured


def _tool_doctor(root: Path, args: dict) -> tuple[str, dict]:
    from .doctor import render_doctor, run_doctor

    checks = run_doctor(root)
    structured = {
        "healthy": all(check.ok for check in checks),
        "checks": [
            {"ok": check.ok, "name": check.name, "detail": check.detail}
            for check in checks
        ],
    }
    return render_doctor(checks).rstrip("\n"), structured


def _tool_verify(root: Path, args: dict) -> tuple[str, dict]:
    from .verify import render_verify, run_verify

    result = run_verify(
        root,
        range_spec=args.get("range"),
        all_history=bool(args.get("all")),
        epoch=args.get("epoch"),
    )
    structured = {
        "ok": result.ok,
        "verified": result.verified,
        "pre_epoch_skipped": result.pre_epoch_skipped,
        "out_of_scope": result.out_of_scope,
        "epoch": result.epoch,
        "error": result.error,
        "violations": [
            {"sha": v.sha, "rule": v.rule, "message": v.message}
            for v in result.violations
        ],
    }
    if result.error:
        raise DwError(f"dw verify: error: {result.error}", 2)
    return render_verify(result).rstrip("\n"), structured


def _tool_gate(root: Path, args: dict) -> tuple[str, dict]:
    from .gate import render_gate_failure, render_gate_porcelain, run_gate

    result = run_gate(root)
    structured = {
        "ok": result.ok,
        "tier": result.tier,
        "expected_boxes": result.expected_boxes,
        "checked_boxes": result.checked_boxes,
        "declared_stories": list(result.declared_stories),
        "shipped_stories": list(result.shipped_stories),
        "contract_digest": result.contract_digest,
        "failure": None
        if result.ok
        else {
            "rule": result.failure.rule,
            "message": result.failure.message,
            "remediation": result.failure.remediation,
        },
    }
    if result.ok:
        text = (
            f"dw gate: pass ({result.checked_boxes}/{result.expected_boxes} checkboxes, "
            f"{len(result.shipped_stories)} story flip(s))"
        )
    else:
        text = render_gate_failure(result).rstrip("\n")
    _ = render_gate_porcelain  # parity partner; text mirrors the CLI renderers
    return text, structured


def _tool_board(root: Path, args: dict) -> tuple[str, dict]:
    from .board import board_model, render_board
    from .parse import get_phase, get_project

    project = get_project(root, args.get("project"))
    model = board_model(project, root)
    phase_selector = args.get("phase")
    if phase_selector is not None and str(phase_selector).strip():
        phase = get_phase(project, str(phase_selector))
        model["phases"] = [lane for lane in model["phases"] if lane["number"] == phase.number]
    return render_board(model), model


def _tool_holds(root: Path, args: dict) -> tuple[str, dict]:
    from .api import parked_lines, parked_summary
    from .parse import get_project

    project = get_project(root, args.get("project"))
    parked = parked_summary(project, root)
    lines = parked_lines(parked)
    text = "\n".join(lines) if lines else (
        "dw holds: nothing parked (no blocked or on-hold stories, no paused phases)"
    )
    return text, parked


def _tool_story_show(root: Path, args: dict) -> tuple[str, dict]:
    from .api import story_detail
    from .parse import get_phase, get_project

    project = get_project(root, args["project"])
    phase = get_phase(project, str(args["phase"]))
    detail = story_detail(project, phase, str(args["story"]), root)
    text = (
        f"{detail['story_id']}\t{detail['status_token']}\t{detail['paths']['story']}"
        f"\tevidence={'yes' if detail['evidence_exists'] else 'no'}"
    )
    return text, detail


def _tool_story_status(root: Path, args: dict) -> tuple[str, dict]:
    from .mutations import apply_plan, plan_story_status
    from .parse import get_phase, get_project

    project = get_project(root, args["project"])
    phase = get_phase(project, str(args["phase"]))
    plan = plan_story_status(
        root, project, phase, str(args["story"]), args["status"],
        reason=str(args.get("reason", "") or ""),
    )
    apply_plan(plan, validate_after=False)
    summary = dict(plan.summary)
    text = f"{summary['story_id']}\t{summary['status']}\t{summary['story_path']}"
    return text, summary


def _tool_evidence_capture(root: Path, args: dict) -> tuple[str, dict]:
    from .evidence import run_capture
    from .parse import get_phase, get_project

    command = args["command"]
    if not isinstance(command, list) or not command or not all(
        isinstance(part, str) for part in command
    ):
        raise DwError("command must be a non-empty array of strings")
    project = get_project(root, args["project"])
    phase = get_phase(project, str(args["phase"]))
    exit_code, evidence_path, timestamp = run_capture(
        root, project, phase, str(args["story"]), list(command)
    )
    try:
        shown = str(evidence_path.relative_to(root))
    except ValueError:
        shown = str(evidence_path)
    text = f"{shown}\t{exit_code}\t{timestamp}"
    return text, {
        "evidence_path": shown,
        "exit_code": exit_code,
        "timestamp": timestamp,
        "tests_capture_ref": f"{shown}#{timestamp}",
    }


def _tool_contract_new(root: Path, args: dict) -> tuple[str, dict]:
    from .contract import parse_contract_facts, write_contract
    from .paths import read_text

    story_ids: list[str] = []
    for raw in args.get("story") or []:
        story_ids.extend(part.strip() for part in raw.split(",") if part.strip())
    path = write_contract(
        root,
        story_ids=story_ids or None,
        consent=args.get("consent", "no"),
        reasons=list(args.get("reasons") or []) or None,
        force=bool(args.get("force")),
        tests_capture=args.get("tests_capture"),
        tier=args.get("tier", "auto"),
    )
    facts = parse_contract_facts(read_text(path)) or {}
    text = (
        f".tmp/CONTRACT.md\t{facts.get('index_tree', 'unknown')}\t{facts.get('story', 'none')}\n"
        "Facts stamped. Certification is a deliberate act: verify each rule, then edit "
        ".tmp/CONTRACT.md and flip every '- [ ]' to '- [x]' yourself — no tool does this. "
        "Restaging invalidates the contract (regenerate with force=true)."
    )
    structured = {
        "contract_path": ".tmp/CONTRACT.md",
        "index_tree": facts.get("index_tree"),
        "story": facts.get("story"),
        "tier": facts.get("tier"),
        "certification": "manual-edit-only",
    }
    return text, structured


def _json_tool(payload: dict) -> tuple[str, dict]:
    return json.dumps(payload, sort_keys=True), payload


def _tool_notifications(root: Path, _args: dict) -> tuple[str, dict]:
    from .notifications import build_notifications

    return _json_tool(build_notifications(root))


def _tool_notifications_ack(root: Path, args: dict) -> tuple[str, dict]:
    from datetime import datetime, timezone

    from .notifications import acknowledge_notification

    now_ts = datetime.now(timezone.utc).replace(microsecond=0).strftime("%Y-%m-%dT%H:%M:%SZ")
    return _json_tool(
        acknowledge_notification(root, str(args["notification_id"]), now_ts)
    )


def _tool_orchestration_list(root: Path, _args: dict) -> tuple[str, dict]:
    from .orchestration import score_inventory

    return _json_tool(score_inventory(root))


def _tool_signals(root: Path, args: dict) -> tuple[str, dict]:
    from .signals import build_signals_inventory

    return _json_tool(
        build_signals_inventory(
            root, remote=args.get("remote"), branch=args.get("branch")
        )
    )


def _tool_orchestration_show(root: Path, args: dict) -> tuple[str, dict]:
    from .orchestration import compile_score_path, find_score_path

    return _json_tool(compile_score_path(find_score_path(root, str(args["score"]))))


def _tool_orchestration_simulate(root: Path, args: dict) -> tuple[str, dict]:
    from .orchestration import find_score_path, load_score, simulate_score

    return _json_tool(simulate_score(load_score(find_score_path(root, str(args["score"])))))


def _tool_run_plan(root: Path, args: dict) -> tuple[str, dict]:
    from .orchestration_run import build_run_plan

    return _json_tool(build_run_plan(
        root,
        str(args["score"]),
        str(args.get("project") or "") or None,
        str(args["story"]),
        issued_at=args.get("issued_at"),
        expires_at=args.get("expires_at"),
        standing_nudges=args.get("standing_nudges"),
        signal_channel=args.get("signal_channel"),
    ))


def _tool_run_list(root: Path, _args: dict) -> tuple[str, dict]:
    from .orchestration_run import run_inventory

    return _json_tool(run_inventory(root))


def _tool_run_show(root: Path, args: dict) -> tuple[str, dict]:
    from .orchestration_run import replay_run

    return _json_tool(replay_run(root, str(args["run_id"])))


def _tool_run_view(root: Path, args: dict) -> tuple[str, dict]:
    from .orchestration_surface import build_run_view

    return _json_tool(build_run_view(root, str(args["run_id"])))


def _tool_run_preview(root: Path, args: dict) -> tuple[str, dict]:
    from .orchestration_surface import build_run_act_preview

    return _json_tool(build_run_act_preview(
        root,
        str(args["run_id"]),
        str(args["action"]),
        reason=str(args.get("reason") or ""),
        decision=str(args.get("decision") or ""),
        correlation_id=str(args.get("correlation_id") or ""),
    ))


def _tool_run_start(root: Path, args: dict) -> tuple[str, dict]:
    from .orchestration_surface import start_run_by_id

    return _json_tool(start_run_by_id(
        root,
        str(args["score"]),
        str(args.get("project") or "") or None,
        str(args["story"]),
        str(args["issued_at"]),
        str(args["expires_at"]),
        str(args["expect"]),
        approved=bool(args.get("approve")),
        approved_by=str(args.get("operator") or ""),
        standing_nudges=args.get("standing_nudges"),
        signal_channel=args.get("signal_channel"),
    ))


def _apply_run_tool(root: Path, args: dict, action: str) -> tuple[str, dict]:
    from .orchestration_surface import apply_run_act

    return _json_tool(apply_run_act(
        root,
        str(args["run_id"]),
        action,
        str(args["expect"]),
        reason=str(args.get("reason") or ""),
        decision=str(args.get("decision") or ""),
        correlation_id=str(args.get("correlation_id") or ""),
    ))


def _tool_run_tick(root: Path, args: dict) -> tuple[str, dict]:
    return _apply_run_tool(root, args, "tick")


def _tool_run_pause(root: Path, args: dict) -> tuple[str, dict]:
    return _apply_run_tool(root, args, "pause")


def _tool_run_resume(root: Path, args: dict) -> tuple[str, dict]:
    return _apply_run_tool(root, args, "resume")


def _tool_run_revoke(root: Path, args: dict) -> tuple[str, dict]:
    return _apply_run_tool(root, args, "revoke")


def _tool_run_cancel(root: Path, args: dict) -> tuple[str, dict]:
    return _apply_run_tool(root, args, "cancel")


def _tool_run_checkpoint(root: Path, args: dict) -> tuple[str, dict]:
    return _apply_run_tool(root, args, "checkpoint")


def _tool_run_request(root: Path, args: dict) -> tuple[str, dict]:
    return _apply_run_tool(root, args, "request")


def _tool_run_stream(root: Path, args: dict) -> tuple[str, dict]:
    from .orchestration_surface import read_run_stream

    return _json_tool(read_run_stream(
        root,
        str(args["run_id"]),
        str(args["executor"]),
        str(args["execution_id"]),
        str(args["stream"]),
        max_bytes=int(args.get("max_bytes", 20_000)),
    ))


def _tool_program_list(root: Path, _args: dict) -> tuple[str, dict]:
    from .program_surface import program_summary_inventory

    return _json_tool(program_summary_inventory(root))


def _tool_program_show(root: Path, args: dict) -> tuple[str, dict]:
    from .program_surface import build_program_view

    return _json_tool(build_program_view(root, str(args["run_id"])))


def _tool_program_validate(root: Path, args: dict) -> tuple[str, dict]:
    from .programs import find_program_path, validate_program_path

    return _json_tool(
        validate_program_path(root, find_program_path(root, str(args["program"])))
    )


def _tool_program_simulate(root: Path, args: dict) -> tuple[str, dict]:
    from .programs import simulate_program

    return _json_tool(simulate_program(root, str(args["program"])))


def _program_budget_args(value: object) -> dict[str, int] | None:
    if value is None:
        return None
    if not isinstance(value, dict):
        raise DwError("program budgets must be an object")
    budgets: dict[str, int] = {}
    for key, amount in value.items():
        if (
            not isinstance(key, str)
            or not key
            or not isinstance(amount, int)
            or isinstance(amount, bool)
        ):
            raise DwError(
                "program budgets must map string names to integer ceilings"
            )
        budgets[key] = amount
    return budgets


def _tool_program_plan(root: Path, args: dict) -> tuple[str, dict]:
    from .program_run import build_program_start_plan

    return _json_tool(build_program_start_plan(
        root,
        str(args["program"]),
        mode=str(args["mode"]),
        operator=str(args["operator"]),
        approval_reason=str(args["reason"]),
        intent_id=str(args["intent_id"]),
        capabilities=(
            list(args["capabilities"])
            if "capabilities" in args else None
        ),
        budgets=_program_budget_args(args.get("budgets")),
        issued_at=str(args["issued_at"]),
        expires_at=str(args["expires_at"]),
        remote=str(args.get("remote") or "") or None,
        remote_ref=str(args.get("remote_ref") or "") or None,
    ))


def _tool_program_start(root: Path, args: dict) -> tuple[str, dict]:
    from .program_surface import start_program_by_id

    if args.get("approve") is not True:
        raise DwError("program start requires approve=true")
    return _json_tool(start_program_by_id(
        root,
        str(args["program"]),
        mode=str(args["mode"]),
        operator=str(args["operator"]),
        approval_reason=str(args["reason"]),
        intent_id=str(args["intent_id"]),
        capabilities=(
            list(args["capabilities"])
            if "capabilities" in args else None
        ),
        budgets=_program_budget_args(args.get("budgets")),
        issued_at=str(args["issued_at"]),
        expires_at=str(args["expires_at"]),
        remote=str(args.get("remote") or "") or None,
        remote_ref=str(args.get("remote_ref") or "") or None,
        expect=str(args["expect"]),
    ))


def _tool_program_preview(root: Path, args: dict) -> tuple[str, dict]:
    from .program_surface import build_program_act_preview

    return _json_tool(build_program_act_preview(
        root,
        str(args["run_id"]),
        str(args["action"]),
        reason=str(args.get("reason") or ""),
        decision=str(args.get("decision") or ""),
        request_id=str(args.get("request_id") or ""),
        max_ticks=int(args.get("max_ticks", 100)),
        max_seconds=int(args.get("max_seconds", 300)),
    ))


def _apply_program_tool(
    root: Path,
    args: dict,
    action: str,
) -> tuple[str, dict]:
    from .program_surface import apply_program_act

    return _json_tool(apply_program_act(
        root,
        str(args["run_id"]),
        action,
        str(args["expect"]),
        reason=str(args.get("reason") or ""),
        decision=str(args.get("decision") or ""),
        request_id=str(args.get("request_id") or ""),
        max_ticks=int(args.get("max_ticks", 100)),
        max_seconds=int(args.get("max_seconds", 300)),
    ))


def _tool_program_tick(root: Path, args: dict) -> tuple[str, dict]:
    return _apply_program_tool(root, args, "tick")


def _tool_program_supervise(root: Path, args: dict) -> tuple[str, dict]:
    return _apply_program_tool(root, args, "supervise")


def _tool_program_request(root: Path, args: dict) -> tuple[str, dict]:
    return _apply_program_tool(root, args, "request")


def _tool_program_pause(root: Path, args: dict) -> tuple[str, dict]:
    return _apply_program_tool(root, args, "pause")


def _tool_program_resume(root: Path, args: dict) -> tuple[str, dict]:
    return _apply_program_tool(root, args, "resume")


def _tool_program_revoke(root: Path, args: dict) -> tuple[str, dict]:
    return _apply_program_tool(root, args, "revoke")


def _tool_program_cancel(root: Path, args: dict) -> tuple[str, dict]:
    return _apply_program_tool(root, args, "cancel")


def _tool_program_tail(root: Path, args: dict) -> tuple[str, dict]:
    from .program_surface import tail_program_events

    return _json_tool(tail_program_events(
        root,
        str(args["run_id"]),
        int(args.get("after", 0)),
        int(args.get("limit", 1_000)),
    ))


def _tool_program_stream(root: Path, args: dict) -> tuple[str, dict]:
    from .program_surface import read_program_stream

    return _json_tool(read_program_stream(
        root,
        str(args["run_id"]),
        str(args["session_id"]),
        str(args["stream"]),
        max_bytes=int(args.get("max_bytes", 20_000)),
    ))


_PROJECT_PROP = {"type": "string", "description": "Project slug (optional when the repo has exactly one project)"}
_RUN_ID_PROP = {"type": "string", "description": "Local orchestration run id"}
_RUN_EXPECT_PROP = {
    "type": "string",
    "description": "Exact act_token from a fresh matching dw_run_preview",
}
_PROGRAM_RUN_ID_PROP = {
    "type": "string",
    "description": "Local autonomous program run id",
}
_PROGRAM_EXPECT_PROP = {
    "type": "string",
    "description": "Exact act_token from a fresh matching dw_program_preview",
}

TOOLS: dict[str, dict] = {
    "dw_status": {
        "description": (
            "One versioned, read-only briefing over rails, roadmap, workspace, "
            "current work, and the next safe action. Attention is valid data, "
            "not a tool error. Adapter over dw_pmo.status.build_status."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {"project": _PROJECT_PROP},
            "additionalProperties": False,
        },
        "handler": _tool_status,
    },
    "dw_knowledge_map": {
        "description": (
            "Read the advisory symbol and structure map only when it matches "
            "the current index tree. Returns named Python and non-Python "
            "coverage gaps and never starts or authorizes work. Adapter over "
            "dw_pmo.repository_map.read_symbol_map."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {},
            "additionalProperties": False,
        },
        "handler": _tool_knowledge_map,
    },
    "dw_knowledge_ground": {
        "description": (
            "Read and classify one story's advisory localization hints against "
            "the fresh symbol map and bounded tracked-blob text fallback. Never "
            "starts or authorizes work. Adapter over "
            "dw_pmo.grounding.ground_project_story."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "project": _PROJECT_PROP,
                "story": {
                    "type": "string",
                    "description": "Story ID or story filename",
                },
            },
            "required": ["project", "story"],
            "additionalProperties": False,
        },
        "handler": _tool_knowledge_ground,
    },
    "dw_knowledge_lessons": {
        "description": (
            "List append-only machine lessons with run, HEAD, timestamp, and "
            "supersession provenance. Lessons are advisory and never authorize "
            "work. Adapter over dw_pmo.knowledge.build_lesson_inventory."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {},
            "additionalProperties": False,
        },
        "handler": _tool_knowledge_lessons,
    },
    "dw_knowledge_recall": {
        "description": (
            "Read one frozen bounded-run or program memory history. Returns "
            "typed missing, stale, malformed, or tampered refusals and never "
            "recomputes recall. Adapter over "
            "dw_pmo.memory_read.build_memory_recall_projection."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "run": {"type": "string", "description": "Bounded run id"},
                "program": {"type": "string", "description": "Program run id"},
            },
            "oneOf": [
                {"required": ["run"]},
                {"required": ["program"]},
            ],
            "additionalProperties": False,
        },
        "handler": _tool_knowledge_recall,
    },
    "dw_knowledge_writebacks": {
        "description": (
            "List terminal memory writebacks with optional run, program, story, "
            "and state filters after verifying receipts and earned ledgers. "
            "Adapter over dw_pmo.memory_read.build_memory_writeback_projection."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "run": {"type": "string", "description": "Bounded run id"},
                "program": {"type": "string", "description": "Program run id"},
                "story": {"type": "string", "description": "Story id"},
                "state": {
                    "type": "string",
                    "description": "Memory or terminal outcome state",
                },
            },
            "additionalProperties": False,
        },
        "handler": _tool_knowledge_writebacks,
    },
    "dw_step": {
        "description": (
            "Pure preview of exactly one state-bound, allowlisted status action; "
            "returns delivery-workbench-step@1 and never executes. Adapter over "
            "dw_pmo.step.build_step."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {"project": _PROJECT_PROP},
            "additionalProperties": False,
        },
        "handler": _tool_step,
    },
    "dw_step_apply": {
        "description": (
            "Apply exactly one current step lease and return the bounded, versioned "
            "result; accepts no command or argv and never certifies or commits. "
            "Adapter over dw_pmo.step.apply_step."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "project": _PROJECT_PROP,
                "expect": {
                    "type": "string",
                    "description": "Exact sha256 token from a fresh dw_step preview",
                },
            },
            "required": ["expect"],
            "additionalProperties": False,
        },
        "handler": _tool_step_apply,
    },
    "dw_setup_preview": {
        "description": (
            "Validate one inert setup proposal and preview every tracked and local "
            "write with hashes plus one exact single-use setup lease. Writes no "
            "tracked content and starts no work. Adapter over dw_pmo.setup_lease.preview_setup."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "proposal_file": {
                    "type": "string",
                    "description": "Path to a delivery-workbench-setup-proposal@1 JSON file",
                }
            },
            "required": ["proposal_file"],
            "additionalProperties": False,
        },
        "handler": _tool_setup_preview,
    },
    "dw_setup_apply": {
        "description": (
            "Apply one pending setup proposal atomically under its exact setup token. "
            "Accepts only proposal identity and expect; creates no grant, run, "
            "certification, or commit. Adapter over dw_pmo.setup_lease.apply_setup."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "proposal": {"type": "string", "description": "Exact setup proposal id from preview"},
                "expect": {"type": "string", "description": "Exact setup-sha256 token from preview"},
            },
            "required": ["proposal", "expect"],
            "additionalProperties": False,
        },
        "handler": _tool_setup_apply,
    },
    "dw_context": {
        "description": (
            "Machine-readable roadmap context: issues, warnings, next story, "
            "per-story trace paths. Adapter over dw_pmo.api.build_context_payload."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "project": _PROJECT_PROP,
                "compact": {"type": "boolean", "description": "Single-line JSON text output"},
            },
            "additionalProperties": False,
        },
        "handler": _tool_context,
    },
    "dw_next": {
        "description": (
            "The next actionable story (in-progress, then ready, then backlog). "
            "Adapter over dw_pmo.api.next_story."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {"project": _PROJECT_PROP},
            "additionalProperties": False,
        },
        "handler": _tool_next,
    },
    "dw_check": {
        "description": (
            "Structural and evidence-content lint over the roadmap. "
            "Adapter over dw_pmo.validate.check_project."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {"project": _PROJECT_PROP},
            "additionalProperties": False,
        },
        "handler": _tool_check,
    },
    "dw_doctor": {
        "description": (
            "Verify the rails are wired in this clone (hooksPath, hooks, core, "
            "agent docs). Adapter over dw_pmo.doctor.run_doctor."
        ),
        "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False},
        "handler": _tool_doctor,
    },
    "dw_verify": {
        "description": (
            "Re-derive the gate's structural rules over pushed history "
            "(docs/remote-verification.md). Adapter over dw_pmo.verify.run_verify."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "range": {"type": "string", "description": "Commit range <base>..<head>"},
                "all": {"type": "boolean", "description": "Full epoch-to-HEAD sweep"},
                "epoch": {"type": "string", "description": "Rev where remote rules begin"},
            },
            "additionalProperties": False,
        },
        "handler": _tool_verify,
    },
    "dw_gate": {
        "description": (
            "Preflight the commit gate against the current stage; never consumes "
            "the contract. Adapter over dw_pmo.gate.run_gate."
        ),
        "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False},
        "handler": _tool_gate,
    },
    "dw_board": {
        "description": (
            "The kanban board, read-only: swimlane per phase, six status "
            "columns, cards carrying receipts (paths) and links; stamped "
            "kind + schema_version. Adapter over dw_pmo.board.board_model."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "project": _PROJECT_PROP,
                "phase": {"type": ["string", "integer"], "description": "Optional: one phase's lane only"},
            },
            "additionalProperties": False,
        },
        "handler": _tool_board,
    },
    "dw_holds": {
        "description": (
            "The ledger of parked work, read-only: blocked/on-hold stories "
            "and paused phases, each with its recorded why and its "
            "paths/links. Adapter over dw_pmo.api.parked_summary."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {"project": _PROJECT_PROP},
            "additionalProperties": False,
        },
        "handler": _tool_holds,
    },
    "dw_story_show": {
        "description": (
            "Browse one story whole, read-only: header context, normalized "
            "status + note, story and evidence bodies, parsed captured "
            "runs, paths and links. Adapter over dw_pmo.api.story_detail."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "project": {"type": "string", "description": "Project slug"},
                "phase": {"type": ["string", "integer"], "description": "Phase number or folder name"},
                "story": {"type": ["string", "integer"], "description": "Story id, number, or filename"},
            },
            "required": ["project", "phase", "story"],
            "additionalProperties": False,
        },
        "handler": _tool_story_show,
    },
    "dw_story_status": {
        "description": (
            "Transactionally update a story's header status and the phase table "
            "(refuses done without evidence, exactly like the CLI). Adapter over "
            "dw_pmo.mutations.plan_story_status + apply_plan."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "project": {"type": "string", "description": "Project slug"},
                "phase": {"type": ["string", "integer"], "description": "Phase number or folder name"},
                "story": {"type": ["string", "integer"], "description": "Story id, number, or filename"},
                "status": {
                    "type": "string",
                    "description": "backlog | ready | in-progress | blocked | on-hold | done (done-synonyms complete/closed/shipped; hold-synonym paused)",
                },
                "reason": {
                    "type": "string",
                    "description": "why this status — required for on-hold/paused (recorded in the status cell as decoration); refused with done",
                },
            },
            "required": ["project", "phase", "story", "status"],
            "additionalProperties": False,
        },
        "handler": _tool_story_status,
    },
    "dw_evidence_capture": {
        "description": (
            "Run a command and record it (command, exit code, index tree, output) "
            "into the story's evidence file — evidence comes from real runs. "
            "Adapter over dw_pmo.evidence.run_capture."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "project": {"type": "string", "description": "Project slug"},
                "phase": {"type": ["string", "integer"], "description": "Phase number or folder name"},
                "story": {"type": ["string", "integer"], "description": "Story id, number, or filename"},
                "command": {
                    "type": "array",
                    "items": {"type": "string"},
                    "minItems": 1,
                    "description": "Command argv to execute (no shell)",
                },
            },
            "required": ["project", "phase", "story", "command"],
            "additionalProperties": False,
        },
        "handler": _tool_evidence_capture,
    },
    "dw_contract_new": {
        "description": (
            "Generate .tmp/CONTRACT.md with stamped, gate-verified facts. "
            "Certification stays a deliberate manual edit — no tool flips the "
            "boxes. Adapter over dw_pmo.contract.build_contract/write_contract."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "story": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Story IDs to declare (default: auto-detect flipped stories)",
                },
                "consent": {"type": "string", "enum": ["yes", "no"], "description": "Work-log consent"},
                "reasons": {"type": "array", "items": {"type": "string"}, "description": "Work-log reasons"},
                "tests_capture": {
                    "type": "string",
                    "description": "Evidence capture reference <path>[#timestamp] to discharge the Tests-ran rule mechanically",
                },
                "tier": {"type": "string", "enum": ["auto", "full", "short"], "description": "Contract tier"},
                "force": {"type": "boolean", "description": "Replace an existing contract"},
            },
            "additionalProperties": False,
        },
        "handler": _tool_contract_new,
    },
    "dw_orchestration_list": {
        "description": "Pure score inventory. Adapter over orchestration.score_inventory.",
        "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False},
        "handler": _tool_orchestration_list,
    },
    "dw_notifications": {
        "description": "Pure derived operator notifications with unread and delivery state. Adapter over notifications.build_notifications.",
        "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False},
        "handler": _tool_notifications,
    },
    "dw_notifications_ack": {
        "description": "Acknowledge one derived notification; idempotent and receipted in the local ack log.",
        "inputSchema": {
            "type": "object",
            "properties": {"notification_id": {"type": "string"}},
            "required": ["notification_id"],
            "additionalProperties": False,
        },
        "handler": _tool_notifications_ack,
    },
    "dw_signals": {
        "description": "Pure outward-signal inventory with derived status; observation stays a CLI act. Adapter over signals.build_signals_inventory.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "remote": {"type": "string", "description": "Filter by remote name"},
                "branch": {"type": "string", "description": "Filter by branch name"},
            },
            "additionalProperties": False,
        },
        "handler": _tool_signals,
    },
    "dw_orchestration_show": {
        "description": "Compile one score through the shared exact compiler; starts nothing.",
        "inputSchema": {
            "type": "object",
            "properties": {"score": {"type": "string", "description": "Score slug or filename stem"}},
            "required": ["score"],
            "additionalProperties": False,
        },
        "handler": _tool_orchestration_show,
    },
    "dw_orchestration_simulate": {
        "description": "Pure deterministic score simulation; writes no run state or events.",
        "inputSchema": {
            "type": "object",
            "properties": {"score": {"type": "string", "description": "Score slug or filename stem"}},
            "required": ["score"],
            "additionalProperties": False,
        },
        "handler": _tool_orchestration_simulate,
    },
    "dw_program_list": {
        "description": (
            "Pure healthy-empty program policy and local grant inventory; "
            "starts no store, process, observer, notification, or stream."
        ),
        "inputSchema": {
            "type": "object", "properties": {},
            "additionalProperties": False,
        },
        "handler": _tool_program_list,
    },
    "dw_program_show": {
        "description": (
            "Canonical content-safe program control-room projection over the "
            "grant ledger, conductor receipts, delivery receipts, team, "
            "verdicts, obligations, budgets, and exact next/refusal."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {"run_id": _PROGRAM_RUN_ID_PROP},
            "required": ["run_id"],
            "additionalProperties": False,
        },
        "handler": _tool_program_show,
    },
    "dw_program_validate": {
        "description": "Pure shared-compiler validation of one tracked program.",
        "inputSchema": {
            "type": "object",
            "properties": {"program": {"type": "string"}},
            "required": ["program"],
            "additionalProperties": False,
        },
        "handler": _tool_program_validate,
    },
    "dw_program_simulate": {
        "description": (
            "Pure deterministic roadmap selection, workflow, team, and "
            "worst-case simulation; creates no grant."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {"program": {"type": "string"}},
            "required": ["program"],
            "additionalProperties": False,
        },
        "handler": _tool_program_simulate,
    },
    "dw_program_plan": {
        "description": (
            "Pure exact finite grant preview over tracked program policy and "
            "current repository, roadmap, roster, and execution fingerprints."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "program": {"type": "string"},
                "mode": {
                    "type": "string",
                    "enum": ["advisory", "checkpointed", "continuous"],
                },
                "operator": {"type": "string"},
                "reason": {"type": "string"},
                "intent_id": {"type": "string"},
                "capabilities": {
                    "type": "array", "items": {"type": "string"},
                },
                "budgets": {
                    "type": "object",
                    "additionalProperties": {"type": "integer"},
                },
                "issued_at": {"type": "string"},
                "expires_at": {"type": "string"},
                "remote": {"type": "string"},
                "remote_ref": {"type": "string"},
            },
            "required": [
                "program", "mode", "operator", "reason", "intent_id",
                "issued_at", "expires_at",
            ],
            "additionalProperties": False,
        },
        "handler": _tool_program_plan,
    },
    "dw_program_start": {
        "description": (
            "Rebuild and consume one exact program grant by ids, reviewed "
            "scalars, explicit approval, and start token; starts no child."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "program": {"type": "string"},
                "mode": {
                    "type": "string",
                    "enum": ["advisory", "checkpointed", "continuous"],
                },
                "operator": {"type": "string"},
                "reason": {"type": "string"},
                "intent_id": {"type": "string"},
                "capabilities": {
                    "type": "array", "items": {"type": "string"},
                },
                "budgets": {
                    "type": "object",
                    "additionalProperties": {"type": "integer"},
                },
                "issued_at": {"type": "string"},
                "expires_at": {"type": "string"},
                "remote": {"type": "string"},
                "remote_ref": {"type": "string"},
                "approve": {"type": "boolean"},
                "expect": {"type": "string"},
            },
            "required": [
                "program", "mode", "operator", "reason", "intent_id",
                "issued_at", "expires_at", "approve", "expect",
            ],
            "additionalProperties": False,
        },
        "handler": _tool_program_start,
    },
    "dw_program_preview": {
        "description": (
            "Pure action+closed-parameters+ledger-bound preview required "
            "before every public program operation."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "run_id": _PROGRAM_RUN_ID_PROP,
                "action": {
                    "type": "string",
                    "enum": [
                        "tick", "supervise", "request", "pause", "resume",
                        "revoke", "cancel",
                    ],
                },
                "reason": {"type": "string"},
                "decision": {
                    "type": "string", "enum": ["", "approve", "reject"],
                },
                "request_id": {"type": "string"},
                "max_ticks": {
                    "type": "integer", "minimum": 1, "maximum": 10000,
                },
                "max_seconds": {
                    "type": "integer", "minimum": 1, "maximum": 86400,
                },
            },
            "required": ["run_id", "action"],
            "additionalProperties": False,
        },
        "handler": _tool_program_preview,
    },
    "dw_program_tick": {
        "description": (
            "Apply one fresh program tick through the existing conductor or "
            "exact delivery lane; may start only already-granted bounded work."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "run_id": _PROGRAM_RUN_ID_PROP,
                "expect": _PROGRAM_EXPECT_PROP,
            },
            "required": ["run_id", "expect"],
            "additionalProperties": False,
        },
        "handler": _tool_program_tick,
    },
    "dw_program_supervise": {
        "description": (
            "Explicit finite repetition of the same public program tick; "
            "returns every tick and stops on checkpoint, no progress, terminal, "
            "refusal, budget, or duration."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "run_id": _PROGRAM_RUN_ID_PROP,
                "expect": _PROGRAM_EXPECT_PROP,
                "max_ticks": {
                    "type": "integer", "minimum": 1, "maximum": 10000,
                },
                "max_seconds": {
                    "type": "integer", "minimum": 1, "maximum": 86400,
                },
            },
            "required": ["run_id", "expect", "max_ticks", "max_seconds"],
            "additionalProperties": False,
        },
        "handler": _tool_program_supervise,
    },
    "dw_program_request": {
        "description": (
            "Apply one fresh closed approve/reject response to an exact "
            "outstanding typed program request."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "run_id": _PROGRAM_RUN_ID_PROP,
                "request_id": {"type": "string"},
                "decision": {
                    "type": "string", "enum": ["approve", "reject"],
                },
                "reason": {"type": "string"},
                "expect": _PROGRAM_EXPECT_PROP,
            },
            "required": [
                "run_id", "request_id", "decision", "reason", "expect",
            ],
            "additionalProperties": False,
        },
        "handler": _tool_program_request,
    },
    "dw_program_pause": {
        "description": "Apply one freshly previewed program pause.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "run_id": _PROGRAM_RUN_ID_PROP,
                "reason": {"type": "string"},
                "expect": _PROGRAM_EXPECT_PROP,
            },
            "required": ["run_id", "reason", "expect"],
            "additionalProperties": False,
        },
        "handler": _tool_program_pause,
    },
    "dw_program_resume": {
        "description": (
            "Apply one freshly previewed resume after all grant facts are "
            "re-observed."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "run_id": _PROGRAM_RUN_ID_PROP,
                "reason": {"type": "string"},
                "expect": _PROGRAM_EXPECT_PROP,
            },
            "required": ["run_id", "reason", "expect"],
            "additionalProperties": False,
        },
        "handler": _tool_program_resume,
    },
    "dw_program_revoke": {
        "description": "Apply one freshly previewed permanent program revocation.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "run_id": _PROGRAM_RUN_ID_PROP,
                "reason": {"type": "string"},
                "expect": _PROGRAM_EXPECT_PROP,
            },
            "required": ["run_id", "reason", "expect"],
            "additionalProperties": False,
        },
        "handler": _tool_program_revoke,
    },
    "dw_program_cancel": {
        "description": (
            "Apply one freshly previewed cancellation before bounded child "
            "interruption."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "run_id": _PROGRAM_RUN_ID_PROP,
                "reason": {"type": "string"},
                "expect": _PROGRAM_EXPECT_PROP,
            },
            "required": ["run_id", "reason", "expect"],
            "additionalProperties": False,
        },
        "handler": _tool_program_cancel,
    },
    "dw_program_tail": {
        "description": (
            "Pure verified program ledger cursor replay; returns no mutation "
            "token, prompt, transcript, source, or artifact content."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "run_id": _PROGRAM_RUN_ID_PROP,
                "after": {"type": "integer", "minimum": 0},
                "limit": {
                    "type": "integer", "minimum": 1, "maximum": 1000,
                },
            },
            "required": ["run_id"],
            "additionalProperties": False,
        },
        "handler": _tool_program_tail,
    },
    "dw_program_stream": {
        "description": (
            "Explicitly open one bounded program-agent stdout/stderr stream; "
            "list views never include its content."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "run_id": _PROGRAM_RUN_ID_PROP,
                "session_id": {"type": "string"},
                "stream": {
                    "type": "string", "enum": ["stdout", "stderr"],
                },
                "max_bytes": {
                    "type": "integer", "minimum": 1, "maximum": 100000,
                },
            },
            "required": ["run_id", "session_id", "stream"],
            "additionalProperties": False,
        },
        "handler": _tool_program_stream,
    },
    "dw_run_plan": {
        "description": (
            "Pure grant/start preview rebuilt from local score and rail facts; accepts identifiers "
            "and timestamps, never score semantics, prompts, driver config, or argv."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "score": {"type": "string"}, "project": _PROJECT_PROP,
                "story": {"type": "string"},
                "issued_at": {"type": "string", "description": "Exact ISO-8601 issuance for parity/replay"},
                "expires_at": {"type": "string", "description": "Exact ISO-8601 grant expiry"},
                "standing_nudges": {"type": "array", "items": {"type": "string"}, "description": "Standing nudge matchers: signal or signal=target"},
                "signal_channel": {"type": "string", "description": "Outward signal channel to bind: remote/branch"},
            },
            "required": ["score", "story"],
            "additionalProperties": False,
        },
        "handler": _tool_run_plan,
    },
    "dw_run_list": {
        "description": "Replay all local run ledgers; returns projections and no prompt/source/output content.",
        "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False},
        "handler": _tool_run_list,
    },
    "dw_run_show": {
        "description": "Replay one authoritative hash-chained run projection; pure.",
        "inputSchema": {
            "type": "object", "properties": {"run_id": _RUN_ID_PROP},
            "required": ["run_id"], "additionalProperties": False,
        },
        "handler": _tool_run_show,
    },
    "dw_run_view": {
        "description": "Content-safe live graph, attempts, sessions, checks, artifacts, budgets, routes, controls, and ledger timeline; pure.",
        "inputSchema": {
            "type": "object", "properties": {"run_id": _RUN_ID_PROP},
            "required": ["run_id"], "additionalProperties": False,
        },
        "handler": _tool_run_view,
    },
    "dw_run_preview": {
        "description": "Pure action+parameters+ledger-bound preview required before every run control act.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "run_id": _RUN_ID_PROP,
                "action": {"type": "string", "enum": ["tick", "pause", "resume", "revoke", "cancel", "checkpoint", "request"]},
                "reason": {"type": "string"},
                "decision": {"type": "string"},
                "correlation_id": {"type": "string"},
            },
            "required": ["run_id", "action"],
            "additionalProperties": False,
        },
        "handler": _tool_run_preview,
    },
    "dw_run_start": {
        "description": "Consume one exact run plan by identifiers and token; creates a grant but dispatches no node.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "score": {"type": "string"}, "project": _PROJECT_PROP,
                "story": {"type": "string"}, "issued_at": {"type": "string"},
                "expires_at": {"type": "string"}, "expect": {"type": "string"},
                "approve": {"type": "boolean"}, "operator": {"type": "string"},
                "standing_nudges": {"type": "array", "items": {"type": "string"}, "description": "Standing nudge matchers bound into the grant"},
                "signal_channel": {"type": "string", "description": "Outward signal channel bound into the grant"},
            },
            "required": ["score", "story", "issued_at", "expires_at", "expect", "approve", "operator"],
            "additionalProperties": False,
        },
        "handler": _tool_run_start,
    },
    "dw_run_tick": {
        "description": "Apply one freshly previewed deterministic conductor tick; this act may start bounded work.",
        "inputSchema": {
            "type": "object", "properties": {"run_id": _RUN_ID_PROP, "expect": _RUN_EXPECT_PROP},
            "required": ["run_id", "expect"], "additionalProperties": False,
        },
        "handler": _tool_run_tick,
    },
    "dw_run_pause": {
        "description": "Apply one freshly previewed pause with its exact bounded reason.",
        "inputSchema": {
            "type": "object", "properties": {"run_id": _RUN_ID_PROP, "expect": _RUN_EXPECT_PROP, "reason": {"type": "string"}},
            "required": ["run_id", "expect", "reason"], "additionalProperties": False,
        },
        "handler": _tool_run_pause,
    },
    "dw_run_resume": {
        "description": "Apply one freshly previewed resume after grant facts are re-observed.",
        "inputSchema": {
            "type": "object", "properties": {"run_id": _RUN_ID_PROP, "expect": _RUN_EXPECT_PROP},
            "required": ["run_id", "expect"], "additionalProperties": False,
        },
        "handler": _tool_run_resume,
    },
    "dw_run_revoke": {
        "description": "Apply one freshly previewed permanent grant revocation with reason.",
        "inputSchema": {
            "type": "object", "properties": {"run_id": _RUN_ID_PROP, "expect": _RUN_EXPECT_PROP, "reason": {"type": "string"}},
            "required": ["run_id", "expect", "reason"], "additionalProperties": False,
        },
        "handler": _tool_run_revoke,
    },
    "dw_run_cancel": {
        "description": "Apply one freshly previewed cancellation; ledger cancellation precedes interruption.",
        "inputSchema": {
            "type": "object", "properties": {"run_id": _RUN_ID_PROP, "expect": _RUN_EXPECT_PROP, "reason": {"type": "string"}},
            "required": ["run_id", "expect", "reason"], "additionalProperties": False,
        },
        "handler": _tool_run_cancel,
    },
    "dw_run_checkpoint": {
        "description": "Apply one freshly previewed approve/reject decision to the exact pending checkpoint.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "run_id": _RUN_ID_PROP, "expect": _RUN_EXPECT_PROP,
                "decision": {"type": "string"},
                "correlation_id": {"type": "string"},
            },
            "required": ["run_id", "expect", "decision"],
            "additionalProperties": False,
        },
        "handler": _tool_run_checkpoint,
    },
    "dw_run_request": {
        "description": "Apply one freshly previewed typed response to the exact correlated outstanding request; malformed responses are ledgered refusals.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "run_id": _RUN_ID_PROP, "expect": _RUN_EXPECT_PROP,
                "correlation_id": {"type": "string"},
                "decision": {"type": "string"},
            },
            "required": ["run_id", "expect", "correlation_id", "decision"],
            "additionalProperties": False,
        },
        "handler": _tool_run_request,
    },
    "dw_run_stream": {
        "description": "Explicitly open one bounded agent/check stdout or stderr log; never lists packets, prompts, source, or artifact content.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "run_id": _RUN_ID_PROP,
                "executor": {"type": "string", "enum": ["agent", "check"]},
                "execution_id": {"type": "string"},
                "stream": {"type": "string", "enum": ["stdout", "stderr"]},
                "max_bytes": {"type": "integer", "minimum": 1, "maximum": 100000},
            },
            "required": ["run_id", "executor", "execution_id", "stream"],
            "additionalProperties": False,
        },
        "handler": _tool_run_stream,
    },
}


def tool_definitions() -> list[dict]:
    return [
        {
            "name": name,
            "description": spec["description"],
            "inputSchema": spec["inputSchema"],
        }
        for name, spec in TOOLS.items()
    ]


def _schema_type_matches(value: object, expected: object) -> bool:
    names = expected if isinstance(expected, list) else [expected]
    for name in names:
        if name == "string" and isinstance(value, str):
            return True
        if name == "boolean" and isinstance(value, bool):
            return True
        if name == "integer" and isinstance(value, int) and not isinstance(value, bool):
            return True
        if name == "number" and isinstance(value, (int, float)) and not isinstance(value, bool):
            return True
        if name == "array" and isinstance(value, list):
            return True
        if name == "object" and isinstance(value, dict):
            return True
        if name == "null" and value is None:
            return True
    return False


def _validate_args(schema: dict, args: dict) -> str | None:
    """Validate the closed, shallow MCP input schemas used by this server."""
    if not isinstance(args, dict):
        return "arguments must be an object"
    props = schema.get("properties", {})
    if not schema.get("additionalProperties", True):
        unknown = [key for key in args if key not in props]
        if unknown:
            return f"unknown parameter(s): {', '.join(sorted(unknown))}"
    missing = [key for key in schema.get("required", []) if key not in args]
    if missing:
        return f"missing required parameter(s): {', '.join(missing)}"
    for key, value in args.items():
        field = props.get(key, {})
        expected = field.get("type")
        if expected is not None and not _schema_type_matches(value, expected):
            return f"parameter {key} has the wrong type"
        if "enum" in field and value not in field["enum"]:
            return f"parameter {key} is not an allowed value"
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            if "minimum" in field and value < field["minimum"]:
                return f"parameter {key} is below its minimum"
            if "maximum" in field and value > field["maximum"]:
                return f"parameter {key} exceeds its maximum"
        if isinstance(value, list):
            if len(value) < int(field.get("minItems", 0)):
                return f"parameter {key} has too few items"
            item_type = field.get("items", {}).get("type")
            if item_type is not None and any(
                not _schema_type_matches(item, item_type) for item in value
            ):
                return f"parameter {key} has an item with the wrong type"
    return None


def call_tool(root: Path, name: str, args: dict) -> dict:
    """Dispatch one tools/call; returns the MCP result object."""
    spec = TOOLS.get(name)
    if spec is None:
        return {
            "content": [{"type": "text", "text": f"unknown tool: {name}"}],
            "isError": True,
        }
    problem = _validate_args(spec["inputSchema"], args)
    if problem is not None:
        return {
            "content": [{"type": "text", "text": f"{name}: {problem}"}],
            "isError": True,
        }
    if not _has_rails(root):
        return {
            "content": [{"type": "text", "text": _missing_rails_message(root)}],
            "isError": True,
        }
    try:
        text, structured = spec["handler"](root, args)
    except DwError as exc:
        return {
            "content": [{"type": "text", "text": f"dw: {exc.args[0]}"}],
            "isError": True,
        }
    return {
        "content": [{"type": "text", "text": text}],
        "structuredContent": structured,
    }


# ── JSON-RPC loop ────────────────────────────────────────────────────

def _response(req_id, result=None, error=None) -> dict:
    msg: dict = {"jsonrpc": "2.0", "id": req_id}
    if error is not None:
        msg["error"] = error
    else:
        msg["result"] = result
    return msg


def handle_message(root: Path, message: dict) -> dict | None:
    """One request → one response dict; notifications → None."""
    req_id = message.get("id")
    method = message.get("method")

    if method is None or message.get("jsonrpc") != "2.0":
        if req_id is None:
            return None
        return _response(req_id, error={"code": INVALID_REQUEST, "message": "invalid request"})

    if method.startswith("notifications/"):
        return None  # accepted, ignored (tools-only server)

    if method == "initialize":
        requested = (message.get("params") or {}).get("protocolVersion")
        version = requested if requested == PROTOCOL_VERSION else PROTOCOL_VERSION
        from dw_pmo import __version__

        return _response(
            req_id,
            result={
                "protocolVersion": version,
                "capabilities": {"tools": {}},
                "serverInfo": {"name": SERVER_NAME, "version": __version__},
            },
        )

    if method == "ping":
        return _response(req_id, result={})

    if method == "tools/list":
        return _response(req_id, result={"tools": tool_definitions()})

    if method == "tools/call":
        params = message.get("params") or {}
        name = params.get("name")
        if not isinstance(name, str):
            return _response(
                req_id, error={"code": INVALID_PARAMS, "message": "tools/call requires a tool name"}
            )
        args = params.get("arguments") or {}
        if not isinstance(args, dict):
            return _response(
                req_id, error={"code": INVALID_PARAMS, "message": "arguments must be an object"}
            )
        return _response(req_id, result=call_tool(root, name, args))

    return _response(req_id, error={"code": METHOD_NOT_FOUND, "message": f"method not found: {method}"})


def serve(root: Path, stdin=None, stdout=None) -> int:
    """Serial ndjson loop; returns when stdin closes."""
    stdin = stdin if stdin is not None else sys.stdin
    stdout = stdout if stdout is not None else sys.stdout
    for line in stdin:
        line = line.strip()
        if not line:
            continue
        try:
            message = json.loads(line)
        except (ValueError, UnicodeDecodeError):
            reply = _response(None, error={"code": PARSE_ERROR, "message": "parse error"})
            print(json.dumps(reply), file=stdout, flush=True)
            continue
        try:
            reply = handle_message(root, message)
        except Exception as exc:  # the loop must survive anything
            reply = _response(
                message.get("id"),
                error={"code": INTERNAL_ERROR, "message": f"internal error: {exc}"},
            )
        if reply is not None:
            print(json.dumps(reply), file=stdout, flush=True)
    return 0
