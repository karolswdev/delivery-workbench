"""Agent suggestion inbox: structured proposals from agent sessions.

Suggestions are stored as individual JSON files under
``pm/suggestions/{project-slug}/`` so they travel with the repository
and are auditable through normal git history.  Each suggestion records
provenance (session, run, rationale) and lifecycle state.
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from .model import DwError

VALID_PRIORITIES = ("normal", "high")
VALID_STATES = ("suggested", "accepted", "dismissed")


def _suggestions_dir(root: Path, project_slug: str) -> Path:
    return root / "pm" / "suggestions" / project_slug


def _suggestion_path(root: Path, project_slug: str, suggestion_id: str) -> Path:
    return _suggestions_dir(root, project_slug) / f"suggestion-{suggestion_id}.json"


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).strftime("%Y-%m-%dT%H:%M:%SZ")


def _read_suggestion(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise DwError(f"cannot read suggestion {path.name}: {exc}") from exc


def _write_suggestion(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(data, indent=2, sort_keys=False) + "\n",
        encoding="utf-8",
    )


class SuggestionStore:
    """Manage agent suggestions per project."""

    def __init__(self, root: Path) -> None:
        self.root = root

    def suggest(
        self,
        project: str,
        title: str,
        description: str,
        priority: str = "normal",
        session_id: Optional[str] = None,
        run_id: Optional[str] = None,
        rationale: str = "",
    ) -> dict:
        """Create a new suggestion and persist it."""
        if not title.strip():
            raise DwError("suggestion title must not be empty")
        if priority not in VALID_PRIORITIES:
            raise DwError(
                f"suggestion priority must be one of {', '.join(VALID_PRIORITIES)}"
            )
        suggestion_id = str(uuid.uuid4())
        data = {
            "id": suggestion_id,
            "title": title.strip(),
            "description": description.strip(),
            "priority": priority,
            "proposed_by_session": session_id or None,
            "proposed_by_run": run_id or None,
            "proposed_at": _now_iso(),
            "state": "suggested",
            "decided_by": None,
            "decided_at": None,
            "materialized_story_id": None,
            "rationale": rationale.strip(),
        }
        path = _suggestion_path(self.root, project, suggestion_id)
        _write_suggestion(path, data)
        return data

    def list(
        self, project: str, state: Optional[str] = None
    ) -> list[dict]:
        """Return suggestions for a project, optionally filtered by state."""
        if state is not None and state not in VALID_STATES:
            raise DwError(
                f"suggestion state filter must be one of {', '.join(VALID_STATES)}"
            )
        sdir = _suggestions_dir(self.root, project)
        if not sdir.is_dir():
            return []
        results: list[dict] = []
        for path in sorted(sdir.glob("suggestion-*.json")):
            try:
                data = _read_suggestion(path)
            except DwError:
                continue  # skip corrupt files
            if state is not None and data.get("state") != state:
                continue
            results.append(data)
        # Newest first
        results.sort(key=lambda s: s.get("proposed_at", ""), reverse=True)
        return results

    def get(self, project: str, suggestion_id: str) -> dict:
        """Return a single suggestion by id."""
        path = _suggestion_path(self.root, project, suggestion_id)
        if not path.is_file():
            raise DwError(f"suggestion not found: {suggestion_id}")
        return _read_suggestion(path)

    def accept(
        self,
        project: str,
        suggestion_id: str,
        decided_by: str = "operator",
        materialized_story_id: Optional[str] = None,
    ) -> dict:
        """Mark a suggestion as accepted."""
        path = _suggestion_path(self.root, project, suggestion_id)
        if not path.is_file():
            raise DwError(f"suggestion not found: {suggestion_id}")
        data = _read_suggestion(path)
        if data.get("state") != "suggested":
            raise DwError(
                f"suggestion {suggestion_id} is already {data.get('state')}; "
                "only suggested items can be accepted"
            )
        data["state"] = "accepted"
        data["decided_by"] = decided_by
        data["decided_at"] = _now_iso()
        if materialized_story_id:
            data["materialized_story_id"] = materialized_story_id
        _write_suggestion(path, data)
        return data

    def dismiss(
        self,
        project: str,
        suggestion_id: str,
        decided_by: str = "operator",
    ) -> dict:
        """Mark a suggestion as dismissed (kept for audit)."""
        path = _suggestion_path(self.root, project, suggestion_id)
        if not path.is_file():
            raise DwError(f"suggestion not found: {suggestion_id}")
        data = _read_suggestion(path)
        if data.get("state") != "suggested":
            raise DwError(
                f"suggestion {suggestion_id} is already {data.get('state')}; "
                "only suggested items can be dismissed"
            )
        data["state"] = "dismissed"
        data["decided_by"] = decided_by
        data["decided_at"] = _now_iso()
        _write_suggestion(path, data)
        return data

    def pending_count(self, project: str) -> int:
        """Count suggestions in the 'suggested' state."""
        return len(self.list(project, state="suggested"))
