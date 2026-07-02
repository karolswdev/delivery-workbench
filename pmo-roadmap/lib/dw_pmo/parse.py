"""Read-only discovery and parsing of the roadmap tree."""

from __future__ import annotations

import re
from pathlib import Path

from .model import PHASE_RE, STORY_RE, Phase, Project, StoryRow, die
from .paths import read_text, rel, roadmap_dir, strip_code


def infer_prefix(project: Path) -> str:
    readme = project / "README.md"
    if readme.exists():
        for line in read_text(readme).splitlines():
            m = re.match(r"- \*\*Story ID prefix:\*\*\s*(.+)$", line)
            if m:
                prefix = strip_code(m.group(1)).strip()
                if prefix:
                    return re.sub(r"[^A-Z0-9]", "", prefix.upper()) or "PRJ"
    parts = [p[0] for p in re.split(r"[^A-Za-z0-9]+", project.name) if p]
    return ("".join(parts) or project.name[:3] or "PRJ").upper()


def discover_projects(root: Path) -> list[Project]:
    projects: list[Project] = []
    for path in sorted(roadmap_dir(root).iterdir()):
        if not path.is_dir():
            continue
        projects.append(Project(path.name, path, infer_prefix(path)))
    return projects


def get_project(root: Path, slug: str | None) -> Project:
    projects = discover_projects(root)
    if slug:
        for project in projects:
            if project.slug == slug:
                return project
        die(f"roadmap project not found: {slug}")
    if len(projects) == 1:
        return projects[0]
    if not projects:
        die("no roadmap projects found")
    die("multiple roadmap projects found; pass a project slug")


def discover_phases(project: Project) -> list[Phase]:
    phases: list[Phase] = []
    for path in sorted(project.path.iterdir()):
        if not path.is_dir():
            continue
        m = PHASE_RE.match(path.name)
        if not m:
            continue
        phases.append(Phase(int(m.group(1)), m.group(2), path))
    return sorted(phases, key=lambda p: p.number)


def get_phase(project: Project, selector: str) -> Phase:
    phases = discover_phases(project)
    for phase in phases:
        if str(phase.number) == selector or phase.path.name == selector:
            return phase
    die(f"phase not found in {project.slug}: {selector}")


def split_table_row(line: str) -> list[str]:
    stripped = line.strip()
    if not stripped.startswith("|") or not stripped.endswith("|"):
        return []
    return [cell.strip() for cell in stripped.strip("|").split("|")]


def parse_story_rows(status_file: Path) -> list[StoryRow]:
    if not status_file.exists():
        return []
    rows: list[StoryRow] = []
    in_table = False
    for line in read_text(status_file).splitlines():
        if line.startswith("| ID | Story | Status | Story file | Evidence |"):
            in_table = True
            continue
        if not in_table:
            continue
        if line.startswith("|---"):
            continue
        if not line.startswith("|"):
            break
        cells = split_table_row(line)
        if len(cells) != 5:
            continue
        rows.append(StoryRow(*cells))
    return rows


def link_target(link: str) -> str:
    m = re.search(r"\]\(([^)]+)\)", link)
    return m.group(1) if m else link


def story_num_from_file(link_or_path: str) -> int | None:
    target = Path(link_target(link_or_path)).name
    m = STORY_RE.match(target)
    return int(m.group(1)) if m else None


def header_status(path: Path) -> str | None:
    if not path.exists():
        return None
    for line in read_text(path).splitlines():
        m = re.match(r"- \*\*Status:\*\*\s*(.+)$", line)
        if m:
            return m.group(1).strip()
    return None


def story_title(path: Path) -> str:
    if not path.exists():
        return path.stem
    lines = read_text(path).splitlines()
    if not lines:
        return path.stem
    first = lines[0].lstrip("#").strip()
    if " - " in first:
        return first.split(" - ", 1)[1]
    if " — " in first:
        return first.split(" — ", 1)[1]
    return first


def parse_current_phase_target(project: Project) -> str:
    readme = project.path / "README.md"
    if not readme.exists():
        return ""
    for line in read_text(readme).splitlines():
        m = re.match(r"^\*\*Current phase:\*\*\s*(.+)$", line)
        if not m:
            continue
        raw = m.group(1).strip().rstrip(".")
        target = link_target(raw)
        if target == raw and raw.lower() in {"complete", "n/a", "none"}:
            return ""
        return target
    return ""


def current_phase_status_path(project: Project) -> Path | None:
    target = parse_current_phase_target(project)
    if not target:
        return None
    return (project.path / target).resolve()


def find_story(project: Project, phase: Phase, selector: str) -> tuple[StoryRow, int, Path]:
    rows = parse_story_rows(phase.path / "current-phase-status.md")
    for row in rows:
        story_num = story_num_from_file(row.story_file)
        story_target = link_target(row.story_file)
        story_path = (phase.path / story_target).resolve()
        selectors = {
            row.story_id,
            str(story_num) if story_num is not None else "",
            f"{story_num:02d}" if story_num is not None else "",
            Path(story_target).name,
            Path(story_target).stem,
        }
        if selector in selectors:
            if story_num is None:
                die(f"could not infer story number for {row.story_id}")
            return row, story_num, story_path
    die(f"story not found in {project.slug} phase {phase.number}: {selector}")


def supplemental_canon(root: Path, project: Project) -> list[dict[str, str]]:
    items: list[dict[str, str]] = []
    for scope, base in (("roadmap-root", roadmap_dir(root)), ("project", project.path)):
        for path in sorted(base.iterdir()):
            if path.is_dir():
                continue
            if path.name == "README.md":
                continue
            if path.suffix.lower() not in {".md", ".markdown"}:
                continue
            if path.name.startswith("story-") or path.name.startswith("evidence-story-"):
                continue
            kind = "supplemental"
            lower = path.name.lower()
            if lower in {"pmo-contract.md", "roadmap-builder.md"}:
                kind = "framework-canon"
            elif "master" in lower or "execution" in lower:
                kind = "orchestrator"
            elif "handover" in lower or "handoff" in lower:
                kind = "handover"
            elif "audit" in lower:
                kind = "audit"
            elif "vision" in lower:
                kind = "vision"
            items.append({"scope": scope, "kind": kind, "path": rel(path, root)})
    return items


def hook_snapshot(root: Path) -> dict[str, object]:
    hooks = root / ".githooks"
    pre = hooks / "pre-commit"
    post = hooks / "post-commit"
    pre_text = read_text(pre) if pre.exists() else ""
    return {
        "hooks_path": rel(hooks, root),
        "pre_commit_exists": pre.exists(),
        "post_commit_exists": post.exists(),
        "config_exists": (hooks / "pre-commit.config").exists(),
        "local_exists": (hooks / "pre-commit.local").exists(),
        "has_config_seam": "pre-commit.config" in pre_text,
        "has_local_seam": "pre-commit.local" in pre_text,
        "has_work_log_capture": "PMO_WORK_LOG_ENABLED" in pre_text and "pmo-work-log" in pre_text,
        "appears_older_snapshot": pre.exists() and (
            "pre-commit.config" not in pre_text or "pre-commit.local" not in pre_text or "PMO_WORK_LOG_ENABLED" not in pre_text
        ),
    }
