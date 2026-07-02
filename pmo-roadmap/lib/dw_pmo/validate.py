"""Structural validation and drift warnings for roadmap projects."""

from __future__ import annotations

import re
from pathlib import Path

from .model import DONE_STATUSES, EVIDENCE_PLACEHOLDER, OPEN_STATUSES, Project
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
from .paths import read_text, rel
from .evidence import CAPTURE_HEADING_RE

_ASSET_REF_RE = re.compile(r"\]\(((?:\./)?assets/[^)]+)\)")
_HEADER_BULLET_RE = re.compile(r"^- \*\*(Story|Status|Date):\*\*")


def _evidence_body_is_empty(text: str) -> bool:
    """True when nothing but scaffold (headings, header bullets) remains."""
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if _HEADER_BULLET_RE.match(stripped):
            continue
        return False
    return True


def evidence_content_issues(evidence_path: Path, phase_path: Path, root: Path) -> list[str]:
    """ERROR-level content lints for a done story's evidence file."""
    issues: list[str] = []
    try:
        text = read_text(evidence_path)
    except OSError:
        return [f"{rel(evidence_path, root)}: evidence file could not be read"]
    if EVIDENCE_PLACEHOLDER in text:
        issues.append(f"{rel(evidence_path, root)}: evidence still contains the generator placeholder")
    elif _evidence_body_is_empty(text):
        issues.append(f"{rel(evidence_path, root)}: evidence body is empty (no proof content)")
    for m in _ASSET_REF_RE.finditer(text):
        target = m.group(1)
        if not (phase_path / target).exists():
            issues.append(f"{rel(evidence_path, root)}: broken asset reference: {target}")
    return issues


def project_warnings(project: Project, root: Path) -> list[str]:
    warnings: list[str] = []
    active = []
    uncaptured: list[str] = []
    for phase in discover_phases(project):
        rows = parse_story_rows(phase.path / "current-phase-status.md")
        if any(row.status in OPEN_STATUSES for row in rows):
            active.append(phase.path.name)
        for row in rows:
            if row.status not in DONE_STATUSES:
                continue
            target = link_target(row.evidence)
            if not target or target in {"-", "—"}:
                continue
            path = (phase.path / target).resolve()
            if not path.exists():
                continue
            try:
                text = read_text(path)
            except OSError:
                continue
            if not any(CAPTURE_HEADING_RE.match(line) for line in text.splitlines()):
                uncaptured.append(rel(path, root))
    if len(active) > 1:
        warnings.append(f"multiple open phases detected: {', '.join(active)}")
    if uncaptured:
        shown = ", ".join(uncaptured[:8])
        more = f" (+{len(uncaptured) - 8} more)" if len(uncaptured) > 8 else ""
        warnings.append(f"narrative-only evidence (no captured runs): {shown}{more}")
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
                evidence_file: Path | None = None
                if row.evidence in {"-", "—", ""}:
                    issues.append(f"{status_file.relative_to(root)}: done story {row.story_id} has no evidence link")
                elif evidence_target and evidence_target not in {"-", "—"}:
                    evidence_path = (phase.path / evidence_target).resolve()
                    if not evidence_path.exists():
                        issues.append(f"{status_file.relative_to(root)}: broken evidence link for {row.story_id}: {evidence_target}")
                    else:
                        evidence_file = evidence_path
                elif story_num is not None and not (phase.path / f"evidence-story-{story_num:02d}.md").exists():
                    issues.append(f"{status_file.relative_to(root)}: done story {row.story_id} missing evidence-story-{story_num:02d}.md")
                if evidence_file is not None:
                    issues.extend(evidence_content_issues(evidence_file, phase.path, root))
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
