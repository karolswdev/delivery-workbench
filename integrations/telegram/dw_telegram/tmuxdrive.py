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

import hashlib
import subprocess
import time
from dataclasses import dataclass
from datetime import datetime

from .consent import Arming

TMUX_TIMEOUT_SECONDS = 15


@dataclass(frozen=True)
class Harness:
    """A supported agent CLI, described as DATA — no `if harness ==`
    anywhere (absorption map §4, ccgram's ProviderCapabilities). The
    name is the whole launch contract; flags and prompts are typed
    into the armed session by the owner, not baked here.

    ``settle_seconds`` is the pause between the literal text and the
    submit keystroke. Claude's TUI treats a same-batch Enter as a
    newline, not a submit — the pause is the fix, proven in ccgram
    (multiplexer/tmux.py). ``supports_resume`` gates the recovery
    offer for a dead session."""

    name: str
    command: str
    settle_seconds: float
    supports_resume: bool

    @property
    def recovery_verbs(self) -> tuple[str, ...]:
        return ("resume", "fresh") if self.supports_resume else ("fresh",)


# Verified needs, modeled honestly: claude's TUI demonstrably needs
# the settle pause; codex behaves the same in practice; both resume.
# pi is launch-and-relay with no verified resume, so it offers fresh
# only rather than overclaiming a verb we have not proven.
HARNESS = {
    "claude": Harness("claude", "claude", 0.5, supports_resume=True),
    "codex": Harness("codex", "codex", 0.3, supports_resume=True),
    "pi": Harness("pi", "pi", 0.3, supports_resume=False),
}


def content_hash(text: str) -> str:
    """Stable digest of a pane snapshot — the live view edits only
    when this changes (no change, no edit, no API call)."""
    return hashlib.sha256(text.encode("utf-8", "replace")).hexdigest()


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
    def __init__(self, arming: Arming, runner=None, sleeper=time.sleep) -> None:
        self._arming = arming
        self._run = runner or subprocess_runner
        self._sleep = sleeper  # injectable so tests assert the settle

    def capture_pane(self, target: str, ansi: bool = False) -> tuple[bool, str]:
        """Read-only snapshot of a pane (or a session's active pane).
        ``ansi=True`` keeps escape sequences (`-e`) so a renderer can
        reproduce the colors; plain text remains the default."""
        argv = ["tmux", "capture-pane", "-p"]
        if ansi:
            argv.append("-e")
        argv += ["-t", target]
        try:
            completed = self._run(argv)
        except (OSError, subprocess.TimeoutExpired) as exc:
            return False, f"tmux failed: {exc}"
        if completed.returncode != 0:
            return False, (completed.stderr or "").strip() or "tmux refused"
        return True, completed.stdout or ""

    def send_text(
        self,
        session: str,
        target: str,
        text: str,
        now: datetime,
        harness: str | None = None,
    ) -> tuple[bool, str]:
        """Relay text into an ARMED session's pane, then submit.

        ``session`` is the tmux session name the owner armed;
        ``target`` is the precise pane within it. ``-l`` keeps the
        text literal — no key-name interpretation. The literal text
        and the submitting Enter are sent as SEPARATE keystrokes with
        a per-harness settle pause between them, because a TUI treats
        a same-batch Enter as a newline rather than a submit (the
        ccgram lesson, §4).
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
        ok, detail = self._verify_owner(session, target)
        if not ok:
            return False, detail
        # Literal text first.
        try:
            completed = self._run(
                ["tmux", "send-keys", "-t", target, "-l", text]
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            return False, f"tmux failed: {exc}"
        if completed.returncode != 0:
            return False, (completed.stderr or "").strip() or "tmux refused"
        # Settle, then submit as its own keystroke (per-harness pause).
        descriptor = HARNESS.get(harness or "")
        self._sleep(descriptor.settle_seconds if descriptor else 0.5)
        try:
            completed = self._run(["tmux", "send-keys", "-t", target, "Enter"])
        except (OSError, subprocess.TimeoutExpired) as exc:
            return False, f"tmux failed: {exc}"
        if completed.returncode != 0:
            return False, (completed.stderr or "").strip() or "tmux refused"
        return True, "sent"

    def send_key(self, session: str, target: str, key: str, now: datetime) -> tuple[bool, str]:
        """Send one named key (Escape, Enter, Up…) into an armed,
        ownership-verified pane — the toolbar's primitive. Same floor
        as send_text: unarmed refuses, a stale pane refuses."""
        if not self._arming.is_armed(session, now):
            raise Unarmed(f"session {session!r} is not armed")
        ok, detail = self._verify_owner(session, target)
        if not ok:
            return False, detail
        try:
            completed = self._run(["tmux", "send-keys", "-t", target, key])
        except (OSError, subprocess.TimeoutExpired) as exc:
            return False, f"tmux failed: {exc}"
        if completed.returncode != 0:
            return False, (completed.stderr or "").strip() or "tmux refused"
        return True, "sent"

    def _verify_owner(self, session: str, target: str) -> tuple[bool, str]:
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
        return True, "ok"

    def launch(
        self, harness: str, session: str, cwd: str, resume: bool = False
    ) -> tuple[bool, str]:
        """Start a supported harness in a new named tmux session. With
        ``resume`` and a harness that supports it, append its resume
        flag (capability-driven recovery, §4)."""
        descriptor = HARNESS.get(harness)
        if descriptor is None:
            return False, (
                f"harness {harness!r} is not supported "
                f"({', '.join(sorted(HARNESS))})"
            )
        command = descriptor.command
        if resume:
            if not descriptor.supports_resume:
                return False, (
                    f"{harness} has no resume; launch fresh instead"
                )
            command = f"{command} --resume"
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
        verb = "resumed" if resume else "launched"
        return True, f"{verb} {harness} in tmux session {session!r} (unarmed)"
