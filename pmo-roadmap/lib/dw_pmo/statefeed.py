"""The mission-control state feed (WLA-13-02).

`dw state --json` emits a versioned, schema-stable subset of
roadmap state for external consumers — the Desk conveyor, the
Telegram interface, the HoldSpeak packs. `dw context --compact`
remains the CLI-facing view and may change shape; this feed may
not, without a `FEED_SCHEMA` bump. The schema is pinned by tests
(`dw-core-tests.py`) that fail on unannounced shape changes, and
the contract lives in docs/mission-control.md §1.

One deliberate addition over the contract's first sketch, amended
there in the same commit: a per-project `phases` array. The Desk
conveyor renders phases as the belt, and the actuator pack
validates create-targets against phases that may hold no stories
yet — neither works from `current_phase` alone.
"""

from __future__ import annotations

import json
from pathlib import Path

from .api import next_story
from .gitio import write_tree
from .model import DONE_STATUSES, Project, normalize_status
from .parse import (
    discover_phases,
    discover_projects,
    parse_story_rows,
    story_num_from_file,
)
from .paths import read_text
from .validate import project_warnings

FEED_SCHEMA = 1


def _phase_title(phase) -> str:
    status_file = phase.path / "current-phase-status.md"
    if status_file.exists():
        for line in read_text(status_file).splitlines():
            if line.startswith("# "):
                return line[2:].strip()
    return phase.path.name


def _project_state(project: Project, root: Path) -> dict:
    phases_out: list[dict] = []
    stories_out: list[dict] = []
    current_phase: dict | None = None
    found = next_story(project, root)
    for phase in discover_phases(project):
        rows = parse_story_rows(phase.path / "current-phase-status.md")
        done = 0
        for row in rows:
            story_num = story_num_from_file(row.story_file)
            evidence = (
                phase.path / f"evidence-story-{story_num:02d}.md"
                if story_num
                else None
            )
            if normalize_status(row.status) in DONE_STATUSES:
                done += 1
            stories_out.append(
                {
                    "story_id": row.story_id,
                    "title": row.title,
                    "status": row.status,
                    "phase": phase.number,
                    "evidence_exists": bool(evidence and evidence.exists()),
                }
            )
        phase_state = {
            "number": phase.number,
            "title": _phase_title(phase),
            "status": (
                "closed"
                if (phase.path / "final-summary.md").exists()
                else "open"
            ),
            "stories_done": done,
            "stories_total": len(rows),
        }
        phases_out.append(phase_state)
        if found and found.get("phase") == phase.number:
            current_phase = phase_state
    if current_phase is None and phases_out:
        open_phases = [p for p in phases_out if p["status"] == "open"]
        current_phase = (open_phases or phases_out)[-1]
    return {
        "slug": project.slug,
        "prefix": project.prefix,
        "current_phase": current_phase,
        "next_story": (
            {
                "story_id": found["story_id"],
                "title": found["title"],
                "status": found["status"],
            }
            if found
            else None
        ),
        "phases": phases_out,
        "stories": stories_out,
        "warnings": len(project_warnings(project, root)),
    }


def build_state_feed(root: Path) -> dict:
    return {
        "feed_schema": FEED_SCHEMA,
        "generated_at_tree": write_tree(root) or "unknown",
        "projects": [
            _project_state(project, root)
            for project in discover_projects(root)
        ],
    }


def render_state_feed(root: Path) -> str:
    return json.dumps(build_state_feed(root), indent=2, sort_keys=True)
