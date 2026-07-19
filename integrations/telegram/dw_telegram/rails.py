"""The rails seam: read the three consumables, write the two verbs.

Reads (§5): the state feed, the event log, and the correlation
document — always through the dw CLI (`dw state --json`,
`dw events --json`, `dw sessions --json`), never by scraping
`pm/roadmap` or importing dw internals. The client declares the
schemas it was proven against and refuses politely on others.

Writes (§4 ring 2): the Phase 12 actuator seam, re-stated here the
way the HoldSpeak connector states it — exactly two ``dw story``
argv shapes are expressible, argv is built by code from the stored,
approved payload (never from message text at egress time), and the
built argv is checked against the allow-listed prefixes before it
runs. The dw gate downstream keeps final say; its refusal banner is
returned verbatim so chat sees exactly what the rails said.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path

from . import FEED_SCHEMA_PROVEN, SESSIONS_SCHEMA_PROVEN

DW_TIMEOUT_SECONDS = 120


def subprocess_runner(argv: list[str], cwd: str | None = None):
    return subprocess.run(
        argv,
        cwd=cwd,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        timeout=DW_TIMEOUT_SECONDS,
    )


class RailsClient:
    def __init__(
        self,
        *,
        dw_cli: list[str] | None = None,
        registry_path: Path | None = None,
        runner=None,
    ) -> None:
        self._dw_cli = dw_cli
        self._registry_path = registry_path
        self._run = runner or subprocess_runner

    def dw_base(self, repo: Path) -> list[str] | None:
        """The repo's own rails first, installed dw second — the
        recorded Phase 12 decision, unchanged."""
        if self._dw_cli:
            return [*self._dw_cli, "--root", str(repo)]
        repo_dw = repo / ".githooks" / "dw"
        if repo_dw.is_file() and os.access(repo_dw, os.X_OK):
            return [str(repo_dw)]
        path_dw = shutil.which("dw")
        if path_dw:
            return [path_dw, "--root", str(repo)]
        return None

    def _json_doc(
        self, repo: Path, argv_tail: list[str]
    ) -> tuple[object, str]:
        base = self.dw_base(repo)
        if base is None:
            return None, f"no dw CLI for {repo}"
        try:
            completed = self._run([*base, *argv_tail], str(repo))
        except (OSError, subprocess.TimeoutExpired) as exc:
            return None, f"dw failed to run: {exc}"
        if completed.returncode != 0:
            detail = (completed.stderr or completed.stdout or "").strip()
            return None, f"dw exited {completed.returncode}: {detail[:300]}"
        try:
            return json.loads(completed.stdout), "ok"
        except (json.JSONDecodeError, ValueError):
            return None, "dw did not return JSON"

    def notifications(self, repo: Path) -> tuple[dict | None, str]:
        """The derived operator-notification inventory (pure read)."""
        return self._json_doc(repo, ["notifications", "list", "--json"])

    def notification_delivered(
        self, repo: Path, notification_id: str, failed: str | None = None
    ) -> tuple[dict | None, str]:
        tail = ["notifications", "delivered", notification_id]
        if failed:
            tail += ["--failed", failed]
        return self._json_doc(repo, tail)

    def checkpoint_decide(
        self, repo: Path, run_id: str, decision: str
    ) -> tuple[dict | None, str]:
        """Preview then apply one checkpoint decision through the
        exact-token boundary. The phone supplies the decision content;
        the rails supply the authority."""
        preview, why = self._json_doc(
            repo,
            ["run", "preview", run_id, "checkpoint",
             "--decision", decision, "--json"],
        )
        if preview is None:
            return None, why
        if not preview.get("applicable"):
            issues = "; ".join(preview.get("issues", [])) or "not applicable"
            return None, f"checkpoint preview refused: {issues}"
        return self._json_doc(
            repo,
            ["run", "checkpoint", run_id, decision,
             "--expect", str(preview.get("act_token", "")), "--json"],
        )

    def read_feed(self, repo: Path) -> tuple[dict | None, str]:
        doc, reason = self._json_doc(repo, ["state", "--json"])
        if doc is None:
            return None, reason
        if not isinstance(doc, dict) or doc.get("feed_schema") != FEED_SCHEMA_PROVEN:
            return None, (
                f"feed_schema {doc.get('feed_schema')!r} is not the schema "
                f"this interface was proven against ({FEED_SCHEMA_PROVEN})"
                if isinstance(doc, dict)
                else "feed document is not an object"
            )
        return doc, "ok"

    def read_events(
        self, repo: Path, tail: int = 10
    ) -> tuple[list | None, str]:
        doc, reason = self._json_doc(
            repo, ["events", "--json", "--tail", str(tail)]
        )
        if doc is None:
            return None, reason
        if not isinstance(doc, list):
            return None, "events document is not a list"
        return doc, "ok"

    def read_sessions(self, repo: Path) -> tuple[dict | None, str]:
        tail = ["sessions", "--json"]
        if self._registry_path is not None:
            tail += ["--registry", str(self._registry_path)]
        doc, reason = self._json_doc(repo, tail)
        if doc is None:
            return None, reason
        if (
            not isinstance(doc, dict)
            or doc.get("sessions_schema") != SESSIONS_SCHEMA_PROVEN
        ):
            return None, (
                "sessions document is not the schema this interface "
                f"was proven against ({SESSIONS_SCHEMA_PROVEN})"
            )
        return doc, "ok"

    # -- the write half: the Phase 12 seam ---------------------------

    def build_story_argv(self, repo: Path, payload: dict) -> list[str]:
        """argv from the stored payload; two verbs, or ValueError."""
        base = self.dw_base(repo)
        if base is None:
            raise ValueError(f"no dw CLI for {repo}")
        verb = str(payload.get("verb") or "")
        if verb == "status":
            argv = [
                *base, "story", "status",
                str(payload["project"]), str(payload["phase"]),
                str(payload["story"]), str(payload["status"]),
            ]
        elif verb == "create":
            argv = [
                *base, "story", "create",
                str(payload["project"]), str(payload["phase"]),
                str(payload["title"]),
            ]
        else:
            raise ValueError(f"verb {verb!r} is not an allow-listed story verb")
        allowed = (
            (*base, "story", "status"),
            (*base, "story", "create"),
        )
        if not any(
            tuple(argv[: len(prefix)]) == prefix for prefix in allowed
        ):
            raise ValueError("built argv escaped the allow-list")
        return argv

    def run_story_verb(
        self, repo: Path, payload: dict
    ) -> tuple[bool, str]:
        """Execute an approved story payload. Returns (ok, output) —
        on refusal the output is the rails' banner, verbatim."""
        argv = self.build_story_argv(repo, payload)
        try:
            completed = self._run(argv, str(repo))
        except (OSError, subprocess.TimeoutExpired) as exc:
            return False, f"dw failed to run: {exc}"
        output = "\n".join(
            part
            for part in (
                (completed.stdout or "").strip(),
                (completed.stderr or "").strip(),
            )
            if part
        )
        return completed.returncode == 0, output
