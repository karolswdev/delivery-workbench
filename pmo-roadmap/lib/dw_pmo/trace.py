"""Git history and work-log correlation for roadmap artifacts."""

from __future__ import annotations

import subprocess
from pathlib import Path

from .model import Project, StoryRow
from .paths import read_text, rel, work_log_root


def recent_commits(root: Path, paths: list[Path], limit: int = 5) -> list[dict[str, str]]:
    rel_paths = [rel(path, root) for path in paths if path and path.exists()]
    if not rel_paths:
        return []
    try:
        out = subprocess.check_output(
            ["git", "-C", str(root), "log", f"--max-count={limit}", "--format=%H%x09%cs%x09%s", "--", *rel_paths],
            stderr=subprocess.DEVNULL,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return []
    commits = []
    for line in out.splitlines():
        parts = line.split("\t", 2)
        if len(parts) == 3:
            commits.append({"sha": parts[0], "date": parts[1], "subject": parts[2]})
    return commits


def parse_work_log_entry(path: Path, root: Path, project: Project, story: StoryRow | None = None) -> dict[str, str] | None:
    try:
        text = read_text(path)
    except OSError:
        return None
    if f"project: {project.slug}" not in text and project.slug not in path.name:
        return None
    if story and story.story_id not in text and story.title not in text:
        return None
    commit = ""
    subject = ""
    timestamp = ""
    for line in text.splitlines():
        if line.startswith("timestamp: ") and not timestamp:
            timestamp = line.split(": ", 1)[1]
        elif line.startswith("commit: ") and not commit:
            commit = line.split(": ", 1)[1]
        elif line.startswith("- **Subject:** ") and not subject:
            subject = line.split("- **Subject:** ", 1)[1]
    return {
        "path": str(path),
        "date": path.parent.name,
        "commit": commit,
        "subject": subject,
        "timestamp": timestamp,
    }


def work_log_entries(root: Path, project: Project, story: StoryRow | None = None, limit: int = 10) -> list[dict[str, str]]:
    log_root = work_log_root()
    if not log_root.is_dir():
        return []
    entries: list[dict[str, str]] = []
    for path in sorted(log_root.glob("*/*-work-summary.log"), reverse=True):
        entry = parse_work_log_entry(path, root, project, story)
        if entry:
            entries.append(entry)
        if len(entries) >= limit:
            break
    return entries
