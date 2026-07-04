"""The tmux driver — the sharpest edge, behind the arming boundary.

`send-keys` is raw input injection into a terminal running with the
owner's rights; no allow-list can bound free text. So the arming
*is* the consent boundary (§4 ring 3) and it is enforced here, at
the lowest layer that can still refuse: ``send_text`` checks the
arming store at the moment of use and raises ``Unarmed`` rather
than emitting a single keystroke into an unarmed session. Previews
(``capture_pane``) are read-only by construction — ``-p`` prints,
nothing is sent. Launching a harness creates a *named* session that
starts life unarmed like everything else.

Addressing: the correlation document's ``tmux`` fields name the
agent's own session/window/pane — the driver targets that pane,
never "whatever is focused".
"""

from __future__ import annotations

import subprocess
from datetime import datetime

from .consent import Arming

TMUX_TIMEOUT_SECONDS = 15

# The supported agent harnesses and the command each launches. The
# name is the whole contract — flags and prompts are typed by the
# owner into the armed session, not baked in here.
HARNESS_COMMANDS = {
    "claude": "claude",
    "codex": "codex",
    "pi": "pi",
}


class Unarmed(RuntimeError):
    """Steering was attempted into a session that is not armed."""


def subprocess_runner(argv: list[str], cwd: str | None = None):
    return subprocess.run(
        argv,
        cwd=cwd,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        timeout=TMUX_TIMEOUT_SECONDS,
    )


class TmuxDriver:
    def __init__(self, arming: Arming, runner=None) -> None:
        self._arming = arming
        self._run = runner or subprocess_runner

    def capture_pane(self, target: str) -> tuple[bool, str]:
        """Read-only snapshot of a pane (or a session's active pane)."""
        try:
            completed = self._run(
                ["tmux", "capture-pane", "-p", "-t", target]
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            return False, f"tmux failed: {exc}"
        if completed.returncode != 0:
            return False, (completed.stderr or "").strip() or "tmux refused"
        return True, completed.stdout or ""

    def send_text(
        self, session: str, target: str, text: str, now: datetime
    ) -> tuple[bool, str]:
        """Relay text + Enter into an ARMED session's pane.

        ``session`` is the tmux session name the owner armed;
        ``target`` is the precise pane within it. ``-l`` keeps the
        text literal — no key-name interpretation.
        """
        if not self._arming.is_armed(session, now):
            raise Unarmed(
                f"session {session!r} is not armed; arm it first "
                "(arming is per-session and expires)"
            )
        # Pane ids are only unique per tmux *server*: a recycled id
        # from a dead server can point at an unrelated pane — typing
        # into it would be exactly the "whatever is focused" failure
        # the contract forbids. Prove the target belongs to the armed
        # session before one keystroke leaves.
        try:
            owner = self._run(
                ["tmux", "display-message", "-p", "-t", target,
                 "#{session_name}"]
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            return False, f"tmux failed: {exc}"
        if owner.returncode != 0:
            return False, (
                f"target pane {target!r} does not exist — the session "
                "has likely ended (its registry entry was stale)"
            )
        actual = (owner.stdout or "").strip()
        if actual != session:
            return False, (
                f"refusing: pane {target!r} belongs to tmux session "
                f"{actual!r}, not the armed {session!r} — the registry "
                "address is stale, nothing was typed"
            )
        for argv in (
            ["tmux", "send-keys", "-t", target, "-l", text],
            ["tmux", "send-keys", "-t", target, "Enter"],
        ):
            try:
                completed = self._run(argv)
            except (OSError, subprocess.TimeoutExpired) as exc:
                return False, f"tmux failed: {exc}"
            if completed.returncode != 0:
                return False, (
                    (completed.stderr or "").strip() or "tmux refused"
                )
        return True, "sent"

    def launch(
        self, harness: str, session: str, cwd: str
    ) -> tuple[bool, str]:
        """Start a supported harness in a new named tmux session."""
        command = HARNESS_COMMANDS.get(harness)
        if command is None:
            return False, (
                f"harness {harness!r} is not supported "
                f"({', '.join(sorted(HARNESS_COMMANDS))})"
            )
        try:
            completed = self._run(
                [
                    "tmux", "new-session", "-d",
                    "-s", session, "-c", cwd, command,
                ]
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            return False, f"tmux failed: {exc}"
        if completed.returncode != 0:
            return False, (completed.stderr or "").strip() or "tmux refused"
        return True, f"launched {harness} in tmux session {session!r} (unarmed)"
