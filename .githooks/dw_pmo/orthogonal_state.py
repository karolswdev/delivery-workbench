"""Orthogonal state projection (WLA-34-02).

Four independent axes derived from existing data sources:

  workflow   -- the roadmap status (backlog, ready, in-progress, etc.)
  execution  -- running | idle | stopped | unknown
  attention  -- none | waiting-for-input | decision-pending | blocked
  authority  -- none | ring-1 | ring-2 | ring-3 | ring-4 | ring-5

This module is a DERIVED VIEW. It reads from the roadmap, run ledgers,
session registry, notifications, and step recommendations. It never
creates new state or writes anything.
"""

from __future__ import annotations

from pathlib import Path

from .board import board_model
from .model import DwError, normalize_status
from .parse import discover_phases, get_project, parse_story_rows


def _derive_execution(
    story_id: str,
    run_entries: list[dict],
    program_entries: list[dict],
    session_pins: dict[str, list],
) -> str:
    """Derive execution state for one story from runs, programs, and sessions.

    running  -- an active run/program references this story AND has active
                claims, or a session is pinned to it and not stale
    idle     -- a run/program references this story but has no active claims
                and no running session
    stopped  -- no run/program references this story
    unknown  -- data cannot be read
    """
    has_reference = False
    has_active = False

    for entry in run_entries:
        run = entry.get("run")
        if not run or not entry.get("valid"):
            continue
        run_story = run.get("story", {})
        if isinstance(run_story, dict) and run_story.get("id") == story_id:
            has_reference = True
            state = str(run.get("state", ""))
            if state in {"active", "awaiting-approval", "awaiting-certification"}:
                active_claims = run.get("active_claims", [])
                if active_claims:
                    has_active = True

    for entry in program_entries:
        if not entry.get("valid"):
            continue
        operational = str(entry.get("operational_state", ""))
        if operational in {"active", "running"}:
            has_active = True
            has_reference = True
        elif entry.get("active_claims", 0) > 0:
            has_active = True
            has_reference = True

    # Session pins: if a live session is pinned to this story, it is running
    if story_id in session_pins:
        for session in session_pins[story_id]:
            if not session.get("stale"):
                has_reference = True
                has_active = True

    if has_active:
        return "running"
    if has_reference:
        return "idle"
    return "stopped"


def _derive_attention(
    story_id: str,
    workflow: str,
    run_entries: list[dict],
    notifications: list[dict],
) -> tuple[str, dict | None]:
    """Derive attention state and optional detail from notifications and runs.

    none              -- nothing needs the operator
    waiting-for-input -- a typed request is pending (checkpoint or nudge)
    decision-pending  -- a run decision is outstanding but not input-typed
    blocked           -- the story or a referencing run is blocked
    """
    detail = None

    # Check notifications for pending requests that reference this story
    for notification in notifications:
        kind = str(notification.get("kind", ""))
        if kind in {
            "checkpoint-pending", "request-pending", "request-republished",
            "program-intervention-required",
        }:
            request = notification.get("request", {})
            if isinstance(request, dict):
                correlation = str(request.get("correlation_id", ""))
                detail = {
                    "request_id": notification.get("id", ""),
                    "kind": kind,
                    "correlation_id": correlation,
                    "node": str(notification.get("node", "")),
                }
                return "waiting-for-input", detail

    # Check run entries for outstanding requests bound to this story
    for entry in run_entries:
        run = entry.get("run")
        if not run or not entry.get("valid"):
            continue
        run_story = run.get("story", {})
        if isinstance(run_story, dict) and run_story.get("id") == story_id:
            writeback = run.get("memory_writeback")
            if isinstance(writeback, dict) and writeback.get("status") == "action-needed":
                return "blocked", {
                    "kind": "memory-writeback-action-needed",
                    "terminal_event_ref": str(
                        writeback.get("terminal_event_ref", "")
                    ),
                    "reason": str(writeback.get("reason", "")),
                }

            outstanding = run.get("outstanding_requests", [])
            if outstanding:
                req = outstanding[0]
                detail = {
                    "request_id": str(req.get("correlation_id", "")),
                    "kind": str(req.get("kind", "")),
                    "correlation_id": str(req.get("correlation_id", "")),
                    "opened_at": str(req.get("opened_at", "")),
                }
                return "waiting-for-input", detail

            state = str(run.get("state", ""))
            if state == "awaiting-approval":
                return "decision-pending", None

    # Blocked from roadmap status
    if workflow == "blocked":
        return "blocked", None

    return "none", None


# Map step action ids to authority rings. These are ordered from least
# to most authority required:
#   ring-1: read-only orientation (continue-story, review-holds)
#   ring-2: safe status transitions (start-story)
#   ring-3: evidence and operational (finish-story, repair-roadmap)
#   ring-4: contract generation (generate-contract)
#   ring-5: certification and commit (manual only, never automated)
_ACTION_RING_MAP = {
    "continue-story": "ring-1",
    "review-holds": "ring-1",
    "review-unstaged": "ring-1",
    "review-workspace": "ring-1",
    "resolve-rewrite": "ring-1",
    "start-story": "ring-2",
    "plan-work": "ring-2",
    "repair-rails": "ring-2",
    "repair-roadmap": "ring-3",
    "finish-story": "ring-3",
    "generate-contract": "ring-4",
    "commit": "ring-5",
    "certify-contract": "ring-5",
}


def _derive_authority(step_data: dict | None) -> str:
    """Derive authority ring from the current step recommendation.

    none    -- no step action recommended or not applicable
    ring-N  -- the action requires ring-N authority
    """
    if step_data is None:
        return "none"

    action = step_data.get("action", {})
    if not isinstance(action, dict):
        return "none"

    action_id = str(action.get("id", ""))
    if not action_id:
        return "none"

    # Manual actions always require highest authority
    if action.get("kind") == "manual":
        return "ring-5"

    return _ACTION_RING_MAP.get(action_id, "none")


def build_orthogonal_state(root: Path, slug: str) -> dict[str, object]:
    """Build the four-axis state projection for every story in a project.

    This is a derived view: it reads from existing data sources and
    never writes. Safe for repos with no active runs (everything shows
    execution=stopped, attention=none, authority=none).
    """
    project = get_project(root, slug)

    # Gather run data (safe: returns empty when no runs exist)
    try:
        from .orchestration_run import run_inventory
        runs = run_inventory(root).get("runs", [])
    except (DwError, Exception):
        runs = []

    # Gather program data (safe: returns empty when no programs exist)
    try:
        from .program_surface import program_summary_inventory
        programs = program_summary_inventory(root).get("runs", [])
    except (DwError, Exception):
        programs = []

    # Gather session pins (safe: returns empty when no sessions exist)
    try:
        from .sessions import correlate_sessions
        from .workbench import mission_control_live_layer
        sessions_doc = correlate_sessions()
        pins, _off_belt = mission_control_live_layer(sessions_doc)
    except (DwError, Exception):
        pins = {}

    # Gather notifications (safe: returns empty when none exist)
    try:
        from .notifications import build_notifications
        all_notifications = build_notifications(root).get("notifications", [])
    except (DwError, Exception):
        all_notifications = []

    # Gather step data (best-effort; may fail for multi-project repos)
    try:
        from .step import build_step
        step_data = build_step(root, slug)
    except (DwError, Exception):
        step_data = None

    # Filter notifications relevant to story-bound runs
    story_run_ids: dict[str, set[str]] = {}
    for entry in runs:
        run = entry.get("run")
        if not run or not entry.get("valid"):
            continue
        run_story = run.get("story", {})
        if isinstance(run_story, dict):
            sid = str(run_story.get("id", ""))
            if sid:
                story_run_ids.setdefault(sid, set()).add(str(run.get("run_id", "")))

    stories: list[dict[str, object]] = []
    for phase in discover_phases(project):
        status_file = phase.path / "current-phase-status.md"
        for row in parse_story_rows(status_file):
            workflow = normalize_status(row.status)
            story_id = row.story_id

            # Filter runs that reference this story
            story_runs = [
                entry for entry in runs
                if entry.get("valid")
                and isinstance(entry.get("run", {}).get("story"), dict)
                and entry["run"]["story"].get("id") == story_id
            ]

            # Filter notifications for runs bound to this story
            bound_run_ids = story_run_ids.get(story_id, set())
            story_notifications = [
                n for n in all_notifications
                if n.get("unread")
                and (
                    str(n.get("run_id", "")) in bound_run_ids
                    or not n.get("run_id")
                )
            ]

            execution = _derive_execution(
                story_id, story_runs, programs, pins,
            )
            attention, attention_detail = _derive_attention(
                story_id, workflow, story_runs, story_notifications,
            )
            authority = _derive_authority(step_data)

            entry = {
                "story_id": story_id,
                "workflow": workflow,
                "execution": execution,
                "attention": attention,
                "authority": authority,
            }
            if attention_detail:
                entry["attention_detail"] = attention_detail

            stories.append(entry)

    return {
        "kind": "delivery-workbench-orthogonal-state",
        "schema_version": 1,
        "project": slug,
        "stories": stories,
    }
