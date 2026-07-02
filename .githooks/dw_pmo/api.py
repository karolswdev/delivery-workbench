"""Machine-readable context envelopes shared by the CLI and workbench."""

from __future__ import annotations

from pathlib import Path

from .model import OPEN_STATUSES, Phase, Project, StoryRow
from .parse import (
    discover_phases,
    get_phase,
    header_status,
    hook_snapshot,
    link_target,
    parse_current_phase_target,
    parse_story_rows,
    story_num_from_file,
    supplemental_canon,
)
from .paths import rel, roadmap_dir
from .trace import recent_commits, work_log_entries
from .validate import check_project, project_warnings


def next_story(project: Project, root: Path) -> dict[str, object] | None:
    preferred = ("in-progress", "ready", "backlog")
    for status in preferred:
        for phase in discover_phases(project):
            for row in parse_story_rows(phase.path / "current-phase-status.md"):
                if row.status == status:
                    story_target = link_target(row.story_file)
                    return {
                        "story_id": row.story_id,
                        "title": row.title,
                        "status": row.status,
                        "phase": phase.number,
                        "phase_path": phase.path.name,
                        "story_path": rel((phase.path / story_target).resolve(), root),
                    }
    return None


def story_context(row: StoryRow, phase: Phase, project: Project, root: Path, include_trace: bool = False) -> dict[str, object]:
    story_target = link_target(row.story_file)
    story_path = (phase.path / story_target).resolve()
    story_num = story_num_from_file(row.story_file)
    evidence_target = link_target(row.evidence)
    if row.evidence in {"-", "—", ""} and story_num is not None:
        evidence_path = phase.path / f"evidence-story-{story_num:02d}.md"
        evidence_link = ""
    elif evidence_target and evidence_target not in {"-", "—"}:
        evidence_path = (phase.path / evidence_target).resolve()
        evidence_link = evidence_target
    else:
        evidence_path = None
        evidence_link = ""

    header = header_status(story_path)
    paths = [
        project.path / "README.md",
        phase.path / "current-phase-status.md",
        story_path,
    ]
    if evidence_path:
        paths.append(evidence_path)
    final_summary = phase.path / "final-summary.md"
    if final_summary.exists():
        paths.append(final_summary)

    item = {
        "story_id": row.story_id,
        "title": row.title,
        "status": row.status,
        "header_status": header,
        "story_file": story_target,
        "story_path": rel(story_path, root),
        "story_exists": story_path.exists(),
        "evidence": row.evidence,
        "evidence_file": evidence_link,
        "evidence_path": rel(evidence_path, root) if evidence_path else "",
        "evidence_exists": bool(evidence_path and evidence_path.exists()),
        "trace": {
            "readme": rel(project.path / "README.md", root),
            "phase_status": rel(phase.path / "current-phase-status.md", root),
            "story": rel(story_path, root),
            "evidence": rel(evidence_path, root) if evidence_path else "",
            "final_summary": rel(final_summary, root),
        },
    }
    if include_trace:
        item["recent_commits"] = recent_commits(root, paths)
        item["work_log_entries"] = work_log_entries(root, project, row)
    return item


def project_context(
    project: Project,
    root: Path,
    phase_selector: str | None = None,
    status_filter: str | None = None,
    include_trace: bool = False,
) -> dict[str, object]:
    phases = discover_phases(project)
    if phase_selector:
        phases = [get_phase(project, phase_selector)]

    phase_items: list[dict[str, object]] = []
    for phase in phases:
        all_rows = parse_story_rows(phase.path / "current-phase-status.md")
        rows = []
        for row in all_rows:
            if status_filter and row.status != status_filter:
                continue
            rows.append(story_context(row, phase, project, root, include_trace))
        phase_items.append(
            {
                "number": phase.number,
                "slug": phase.slug,
                "path": rel(phase.path, root),
                "status_file": rel(phase.path / "current-phase-status.md", root),
                "status_file_exists": (phase.path / "current-phase-status.md").exists(),
                "final_summary": rel(phase.path / "final-summary.md", root),
                "final_summary_exists": (phase.path / "final-summary.md").exists(),
                "active": any(row.status in OPEN_STATUSES for row in all_rows),
                "stories": rows,
            }
        )

    return {
        "slug": project.slug,
        "prefix": project.prefix,
        "path": rel(project.path, root),
        "readme": rel(project.path / "README.md", root),
        "readme_exists": (project.path / "README.md").exists(),
        "current_phase_target": parse_current_phase_target(project),
        "next_story": next_story(project, root),
        "issues": check_project(project, root),
        "warnings": project_warnings(project, root),
        "supplemental_canon": supplemental_canon(root, project),
        "hook_snapshot": hook_snapshot(root),
        "work_logs": work_log_entries(root, project),
        "phases": phase_items,
    }


def build_context_payload(
    root: Path,
    projects: list[Project],
    phase_selector: str | None = None,
    status_filter: str | None = None,
    include_trace: bool = False,
) -> dict[str, object]:
    return {
        "kind": "delivery-workbench-roadmap-context",
        "schema_version": 1,
        "root": str(root),
        "roadmap_dir": rel(roadmap_dir(root), root),
        "projects": [
            project_context(project, root, phase_selector, status_filter, include_trace)
            for project in projects
        ],
    }
