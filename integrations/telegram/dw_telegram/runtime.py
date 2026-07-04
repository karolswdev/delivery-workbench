"""Runtime state — the interface's memory, outside the repo.

One JSON file (default ``~/.config/delivery-workbench/telegram-state.json``,
chmod 600) holding exactly the things §4 says live in runtime state
and never in configuration we author: the pairing binding (a chat
id, present only after a successful pairing), the outstanding
pairing token's *hash*, the armed-session map, and the active rails
repo. The file is rewritten atomically and re-tightened to 0600 on
every save.
"""

from __future__ import annotations

import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path

STATE_VERSION = 1


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def iso(ts: datetime) -> str:
    return ts.strftime("%Y-%m-%dT%H:%M:%SZ")


def parse_iso(raw: object) -> datetime | None:
    text = str(raw or "").strip()
    if not text:
        return None
    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return None


class RuntimeState:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.paired_chat: int | None = None
        self.pairing: dict | None = None  # {token_sha256, expires_at, used}
        self.armed: dict[str, str] = {}  # tmux session -> expires_at iso
        self.active_repo: str | None = None
        self.events_offset: int = 0  # byte offset into the hook stream
        self.topic_repos: dict[str, str] = {}  # topic-key -> repo path
        self.topic_sessions: dict[str, dict] = {}  # topic-key -> binding
        self._load()

    def reload(self) -> None:
        """Re-read the file. The pairing CLI and the serving process
        are separate processes sharing this file; the server reloads
        before judging a pairing attempt so a token generated while
        it was already running is honored."""
        self._load()

    def _load(self) -> None:
        if not self.path.exists():
            return
        try:
            doc = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError, ValueError):
            return
        if not isinstance(doc, dict) or doc.get("state_version") != STATE_VERSION:
            return
        chat = doc.get("paired_chat")
        self.paired_chat = int(chat) if isinstance(chat, int) else None
        pairing = doc.get("pairing")
        self.pairing = pairing if isinstance(pairing, dict) else None
        armed = doc.get("armed")
        self.armed = (
            {str(k): str(v) for k, v in armed.items()}
            if isinstance(armed, dict)
            else {}
        )
        repo = doc.get("active_repo")
        self.active_repo = str(repo) if repo else None
        offset = doc.get("events_offset")
        self.events_offset = offset if isinstance(offset, int) and offset >= 0 else 0
        repos = doc.get("topic_repos")
        self.topic_repos = (
            {str(k): str(v) for k, v in repos.items()}
            if isinstance(repos, dict)
            else {}
        )
        sessions = doc.get("topic_sessions")
        self.topic_sessions = (
            {str(k): v for k, v in sessions.items() if isinstance(v, dict)}
            if isinstance(sessions, dict)
            else {}
        )

    def save(self) -> None:
        doc = {
            "state_version": STATE_VERSION,
            "paired_chat": self.paired_chat,
            "pairing": self.pairing,
            "armed": self.armed,
            "active_repo": self.active_repo,
            "events_offset": self.events_offset,
            "topic_repos": self.topic_repos,
            "topic_sessions": self.topic_sessions,
        }
        self.path.parent.mkdir(parents=True, exist_ok=True)
        fd, tmp = tempfile.mkstemp(
            dir=str(self.path.parent), prefix=".telegram-state."
        )
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                json.dump(doc, handle, indent=2, sort_keys=True)
                handle.write("\n")
            os.chmod(tmp, 0o600)
            os.replace(tmp, self.path)
        finally:
            if os.path.exists(tmp):
                os.unlink(tmp)
        os.chmod(self.path, 0o600)
