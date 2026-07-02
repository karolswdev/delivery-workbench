"""Structural validation and drift warnings for roadmap projects."""

from __future__ import annotations

import re
from pathlib import Path

from .model import DONE_STATUSES, OPEN_STATUSES, Project
from .parse import (
    current_phase_status_path,
    discover_phases,
    header_status,
    hook_snapshot,
    link_target,
    parse_current_phase_target,
    parse_story_rows,
    story_num_from_file,
)
from .paths import rel


def project_warnings(project: Project, root: Path) -> list[str]:
    warnings: list[str] = []
    active = []
    for phase in discover_phases(project):
        rows = parse_story_rows(phase.path / "current-phase-status.md")
        if any(row.status in OPEN_STATUSES for row in rows):
            active.append(phase.path.name)
    if len(active) > 1:
        warnings.append(f"multiple open phases detected: {', '.join(active)}")
    snapshot = hook_snapshot(root)
    if snapshot["appears_older_snapshot"]:
        warnings.append("installed pre-commit hook appears older than current Delivery Workbench seams")
    return warnings


def check_project(project: Project, root: Path) -> list[str]:
    issues: list[str] = []
    current_status = current_phase_status_path(project)
    if current_status and not current_status.exists():
        issues.append(f"{rel(project.path / 'README.md', root)}: current phase pointer is stale: {parse_current_phase_target(project)}")

    for phase in discover_phases(project):
        status_file = phase.path / "current-phase-status.md"
        if not status_file.exists():
            issues.append(f"{rel(phase.path, root)}: missing current-phase-status.md")
            continue
        rows = parse_story_rows(status_file)
        story_nums: set[int] = set()
        done_nums: set[int] = set()
        for row in rows:
            story_target = link_target(row.story_file)
            story_path = (phase.path / story_target).resolve()
            story_num = story_num_from_file(row.story_file)
            if story_num is not None:
                story_nums.add(story_num)
                if row.status in DONE_STATUSES:
                    done_nums.add(story_num)
            if not story_path.exists():
                issues.append(f"{status_file.relative_to(root)}: broken story link for {row.story_id}: {story_target}")
                continue
            status = header_status(story_path)
            if status and status != row.status:
                issues.append(
                    f"{story_path.relative_to(root)}: header status {status!r} differs from phase table {row.status!r}"
                )
            evidence_target = link_target(row.evidence)
            if row.status in DONE_STATUSES:
                if row.evidence in {"-", "—", ""}:
                    issues.append(f"{status_file.relative_to(root)}: done story {row.story_id} has no evidence link")
                elif evidence_target and evidence_target not in {"-", "—"}:
                    evidence_path = (phase.path / evidence_target).resolve()
                    if not evidence_path.exists():
                        issues.append(f"{status_file.relative_to(root)}: broken evidence link for {row.story_id}: {evidence_target}")
                elif story_num is not None and not (phase.path / f"evidence-story-{story_num:02d}.md").exists():
                    issues.append(f"{status_file.relative_to(root)}: done story {row.story_id} missing evidence-story-{story_num:02d}.md")
        for evidence in sorted(phase.path.glob("evidence-story-*.md")):
            m = re.match(r"^evidence-story-(\d+)\.md$", evidence.name)
            if not m:
                continue
            ev_num = int(m.group(1))
            if ev_num not in story_nums:
                issues.append(f"{rel(evidence, root)}: orphan evidence has no matching story row")
            elif ev_num not in done_nums:
                issues.append(f"{rel(evidence, root)}: evidence exists but matching story is not done")
        if rows and all(row.status in DONE_STATUSES for row in rows) and not (phase.path / "final-summary.md").exists():
            issues.append(f"{rel(phase.path, root)}: all stories are done but final-summary.md is missing")
    return issues
