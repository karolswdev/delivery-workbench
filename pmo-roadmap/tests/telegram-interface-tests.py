#!/usr/bin/env python3
"""Tests for the Telegram interface (WLA-13-06).

Everything runs against a scripted transport and fixture rails
repos — no live network, no live tmux, no real registry. The rails
legs (state, events, the crown-case gate refusal) run the real dw
CLI against real fixture repos; tmux and Telegram are the two
things faked, each behind the seam the production code declares.

Covers the story's test plan: message rendering from feed fixtures;
the consent state machine (proposal → approval → execution, single
use, expiry, arming expiry); the pairing state machine (TTL,
single-use, revocation, unpaired-chat refusals); the tmux driver's
unarmed refusal and per-harness launch argv; the lifecycle
allow-list refusal and the full create step sequence; and the crown
case — an approved dishonest done-flip refused by the rails with
the banner relayed into chat.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import types
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

TESTS_DIR = Path(__file__).resolve().parent
REPO_ROOT = TESTS_DIR.parent.parent
BIN_DW = TESTS_DIR.parent / "bin" / "dw"

sys.path.insert(0, str(REPO_ROOT / "integrations" / "telegram"))

from dw_telegram.config import Config, ConfigError, load_config
from dw_telegram.consent import Arming, ProposalBook
from dw_telegram.interface import TelegramInterface
from dw_telegram.lifecycle import LifecycleClient, within_roots
from dw_telegram.pairing import new_pairing_token, redeem
from dw_telegram.rails import RailsClient
from dw_telegram.runtime import RuntimeState, utc_now
from dw_telegram.tmuxdrive import TmuxDriver, Unarmed
from dw_telegram.transport import HttpTransport, ScriptedTransport, TransportError

# ---------------------------------------------------------------- fixtures

README = """# Demo - Roadmap

**Last updated:** 2026-07-04.
**Current phase:** [phase-1-alpha](./phase-1-alpha/current-phase-status.md).
**Status:** active.

## Phase index

| Phase | Goal (one line) | Status | Folder |
|---|---|---|---|
| 1 | Ship the alpha | active | [phase-1-alpha](./phase-1-alpha/) |

## Project metadata

- **Slug:** `demo`
- **Story ID prefix:** DM
"""

STATUS_FILE = """# Phase 1 - Alpha

**Last updated:** 2026-07-04.

## Story status

| ID | Story | Status | Story file | Evidence |
|---|---|---|---|---|
| DM-1-01 | First thing | done | [story-01-first](./story-01-first.md) | [evidence-story-01](./evidence-story-01.md) |
| DM-1-02 | Second thing | in-progress | [story-02-second](./story-02-second.md) | - |
"""

STORY_TMPL = """# {sid} - {title}

- **Project:** demo
- **Phase:** 1
- **Status:** {status}
- **Owner:** unassigned

## Problem

Fixture story.
"""

EVIDENCE_01 = """# Evidence - DM-1-01

- **Story:** DM-1-01 - First thing
- **Status:** done
- **Date:** 2026-07-04

## Proof

- fixture proof line
"""


def make_rails_repo(base: Path) -> Path:
    repo = base / "demo-repo"
    phase = repo / "pm" / "roadmap" / "demo" / "phase-1-alpha"
    phase.mkdir(parents=True)
    (repo / "pm" / "roadmap" / "demo" / "README.md").write_text(README)
    (phase / "current-phase-status.md").write_text(STATUS_FILE)
    (phase / "story-01-first.md").write_text(
        STORY_TMPL.format(sid="DM-1-01", title="First thing", status="done")
    )
    (phase / "story-02-second.md").write_text(
        STORY_TMPL.format(
            sid="DM-1-02", title="Second thing", status="in-progress"
        )
    )
    (phase / "evidence-story-01.md").write_text(EVIDENCE_01)
    # Rails markers so the correlator counts this as a rails repo.
    hooks = repo / ".githooks"
    hooks.mkdir()
    dw_stub = hooks / "dw"
    dw_stub.write_text("#!/usr/bin/env python3\n")
    dw_stub.chmod(0o755)
    subprocess.run(
        ["git", "init", "-q", str(repo)],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    return repo


def make_registry(base: Path, repo: Path, *, awaiting=True) -> Path:
    now = utc_now().strftime("%Y-%m-%dT%H:%M:%SZ")
    registry = base / "agent_sessions.json"
    registry.write_text(
        json.dumps(
            {
                "version": 1,
                "sessions": {
                    "claude:sess-1": {
                        "agent": "claude",
                        "session_id": "sess-1",
                        "model": "test-model",
                        "repo_root": str(repo),
                        "project_name": "demo",
                        "awaiting_response": awaiting,
                        "last_assistant_text": "Should I delete the flag?",
                        "tmux_session": "desk",
                        "tmux_window": 0,
                        "tmux_pane": "%7",
                        "updated_at": now,
                    },
                    # A session started in a plain terminal: no tmux
                    # address, therefore honest but unsteerable.
                    "claude:bare-term": {
                        "agent": "claude",
                        "session_id": "bare-term",
                        "repo_root": str(repo),
                        "project_name": "demo",
                        "awaiting_response": awaiting,
                        "last_assistant_text": "Ship it?",
                        "updated_at": now,
                    },
                },
            }
        )
    )
    return registry


class FakeClock:
    def __init__(self) -> None:
        self.now = datetime(2026, 7, 4, 12, 0, 0, tzinfo=timezone.utc)

    def __call__(self) -> datetime:
        return self.now

    def advance(self, **kwargs) -> None:
        self.now += timedelta(**kwargs)


class RecordingRunner:
    """A subprocess seam double: records argv, returns success."""

    def __init__(self, hook=None) -> None:
        self.calls: list[list[str]] = []
        self.hook = hook

    def __call__(self, argv, cwd=None):
        self.calls.append(list(argv))
        if self.hook:
            result = self.hook(argv, cwd)
            if result is not None:
                return result
        return types.SimpleNamespace(returncode=0, stdout="", stderr="")




def topic_message(chat: int, text: str, thread: int) -> dict:
    return {"message": {"chat": {"id": chat}, "text": text,
                        "message_thread_id": thread}}


def message(chat: int, text: str) -> dict:
    return {"message": {"chat": {"id": chat}, "text": text}}


def callback(chat: int, data: str, cb="cb-1") -> dict:
    return {
        "callback_query": {
            "id": cb,
            "data": data,
            "message": {"chat": {"id": chat}},
        }
    }


OWNER = 4242  # fixture chat id, not a real identity


class InterfaceCase(unittest.TestCase):
    """Shared harness: fixture repo, paired interface, fakes."""

    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp(prefix="dw-telegram-test."))
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)
        self.repo = make_rails_repo(self.tmp)
        self.registry = make_registry(self.tmp, self.repo)
        self.clock = FakeClock()
        self.transport = ScriptedTransport()

        def tmux_hook(argv, cwd):
            # The driver verifies pane ownership before typing; the
            # fixture pane %7 belongs to tmux session "desk".
            if argv[1] == "display-message":
                return types.SimpleNamespace(
                    returncode=0, stdout="desk\n", stderr=""
                )
            return None

        self.tmux_runner = RecordingRunner(tmux_hook)
        self.config = Config(
            bot_token="unit-test-token",
            workspace_roots=[self.tmp],
            default_repo=self.repo,
            state_path=self.tmp / "state.json",
            registry_path=self.registry,
            dw_cli=[sys.executable, str(BIN_DW)],
        )
        self.state = RuntimeState(self.config.resolved_state_path())
        arming = Arming(self.state)
        self.iface = TelegramInterface(
            self.config,
            self.state,
            self.transport,
            driver=TmuxDriver(arming, runner=self.tmux_runner, sleeper=lambda _s: None),
            clock=self.clock,
        )

    def pair(self, chat: int = OWNER) -> None:
        token = new_pairing_token(self.state, self.clock())
        self.iface.handle_update(message(chat, f"/pair {token}"))
        self.transport.sent.clear()

    def sent_texts(self) -> list[str]:
        # The chat as the user saw it: sends and in-place edits,
        # chronological (the queue merges and the cards edit).
        return [item["text"] for item in self.transport.feed_stream]

    def last_text(self) -> str:
        self.assertTrue(self.transport.feed_stream, "expected a chat message")
        return self.transport.feed_stream[-1]["text"]

    def last_proposal_id(self) -> str:
        buttons = self.transport.sent[-1]["buttons"]
        self.assertTrue(buttons, "expected approval buttons")
        data = buttons[0][0][1]
        self.assertTrue(data.startswith("ap:"))
        return data.split(":", 1)[1]

    def approve_last(self, chat: int = OWNER) -> None:
        self.iface.handle_update(
            callback(chat, f"ap:{self.last_proposal_id()}")
        )


# ---------------------------------------------------------------- pairing


class PairingTest(InterfaceCase):
    def test_unpaired_chat_gets_prompt_then_silence(self) -> None:
        self.iface.handle_update(message(OWNER, "/start"))
        self.assertIn("pairing", self.last_text().lower())
        self.transport.sent.clear()
        for text in ("/state", "/flip demo 1 DM-1-02 done", "hello"):
            self.iface.handle_update(message(OWNER, text))
        self.assertEqual(self.transport.sent, [], "unpaired chats get silence")

    def test_no_outstanding_token_refused(self) -> None:
        self.iface.handle_update(message(OWNER, "/pair anything"))
        self.assertIn("No pairing token is outstanding", self.last_text())
        self.assertIsNone(self.state.paired_chat)

    def test_wrong_token_refused(self) -> None:
        new_pairing_token(self.state, self.clock())
        self.iface.handle_update(message(OWNER, "/pair wrong-token"))
        self.assertIn("Wrong pairing token", self.last_text())
        self.assertIsNone(self.state.paired_chat)

    def test_expired_token_refused(self) -> None:
        token = new_pairing_token(self.state, self.clock())
        self.clock.advance(minutes=6)
        self.iface.handle_update(message(OWNER, f"/pair {token}"))
        self.assertIn("expired", self.last_text())
        self.assertIsNone(self.state.paired_chat)

    def test_pair_then_reuse_refused(self) -> None:
        token = new_pairing_token(self.state, self.clock())
        self.iface.handle_update(message(OWNER, f"/pair {token}"))
        self.assertEqual(self.state.paired_chat, OWNER)
        self.iface.handle_update(message(999, f"/pair {token}"))
        self.assertIn("already used", self.last_text())
        self.assertEqual(self.state.paired_chat, OWNER)

    def test_repair_revokes_previous_binding(self) -> None:
        self.pair(OWNER)
        token = new_pairing_token(self.state, self.clock())
        self.iface.handle_update(message(999, f"/pair {token}"))
        self.assertEqual(self.state.paired_chat, 999)
        self.transport.sent.clear()
        self.iface.handle_update(message(OWNER, "/state"))
        self.assertEqual(
            self.transport.sent, [], "revoked chat is unpaired again"
        )

    def test_state_file_is_owner_only(self) -> None:
        new_pairing_token(self.state, self.clock())
        mode = (self.config.resolved_state_path()).stat().st_mode & 0o777
        self.assertEqual(mode, 0o600)

    def test_token_stored_hashed_not_cleartext(self) -> None:
        token = new_pairing_token(self.state, self.clock())
        raw = (self.config.resolved_state_path()).read_text()
        self.assertNotIn(token, raw)

    def test_token_from_separate_pair_process_is_honored(self) -> None:
        # The pair CLI and the server are separate processes sharing
        # the state file; a token generated AFTER the server loaded
        # its state must still redeem (the server reloads on pairing).
        other = RuntimeState(self.config.resolved_state_path())
        token = new_pairing_token(other, self.clock())
        self.iface.handle_update(message(OWNER, f"/pair {token}"))
        self.assertTrue(
            any("Paired" in text for text in self.sent_texts()),
            self.sent_texts(),
        )
        self.assertEqual(self.state.paired_chat, OWNER)


# ---------------------------------------------------------------- consent


class ConsentTest(InterfaceCase):
    def setUp(self) -> None:
        super().setUp()
        self.pair()

    def propose_flip(self) -> str:
        self.iface.handle_update(
            message(OWNER, "/flip demo 1 DM-1-02 in-progress")
        )
        return self.last_proposal_id()

    def test_reject_executes_nothing(self) -> None:
        proposal_id = self.propose_flip()
        self.iface.handle_update(callback(OWNER, f"rj:{proposal_id}"))
        self.assertIn("rejected", self.last_text())
        self.iface.handle_update(callback(OWNER, f"ap:{proposal_id}"))
        self.assertIn("nothing executed", self.last_text())

    def test_proposal_is_single_use(self) -> None:
        proposal_id = self.propose_flip()
        self.iface.handle_update(callback(OWNER, f"ap:{proposal_id}"))
        first = self.last_text()
        self.assertIn("done:", first)
        self.iface.handle_update(callback(OWNER, f"ap:{proposal_id}"))
        self.assertIn("nothing executed", self.last_text())

    def test_proposal_expires(self) -> None:
        proposal_id = self.propose_flip()
        self.clock.advance(minutes=16)
        self.iface.handle_update(callback(OWNER, f"ap:{proposal_id}"))
        self.assertIn("nothing executed", self.last_text())

    def test_unpaired_callback_refused(self) -> None:
        proposal_id = self.propose_flip()
        self.iface.handle_update(callback(999, f"ap:{proposal_id}"))
        self.assertEqual(self.transport.answered[-1]["text"], "not paired")
        # And the proposal is still executable by the owner — the
        # stranger's tap neither executed nor consumed it.
        self.iface.handle_update(callback(OWNER, f"ap:{proposal_id}"))
        self.assertIn("done:", self.last_text())


# ---------------------------------------------------------------- rails read


class ReadSurfaceTest(InterfaceCase):
    def setUp(self) -> None:
        super().setUp()
        self.pair()

    def test_state_renders_real_feed(self) -> None:
        self.iface.handle_update(message(OWNER, "/state"))
        text = self.last_text()
        self.assertIn("demo", text)
        self.assertIn("phase 1", text)
        self.assertIn("DM-1-02", text)

    def test_events_render_real_log(self) -> None:
        # A real story flip through the real CLI emits story_status.
        rails = RailsClient(dw_cli=self.config.dw_cli)
        ok, out = rails.run_story_verb(
            self.repo,
            {
                "verb": "status", "project": "demo", "phase": "1",
                "story": "DM-1-02", "status": "blocked",
            },
        )
        self.assertTrue(ok, out)
        self.iface.handle_update(message(OWNER, "/events"))
        text = self.last_text()
        self.assertIn("story_status", text)
        self.assertIn("DM-1-02", text)

    def test_sessions_render_correlation(self) -> None:
        self.iface.handle_update(message(OWNER, "/sessions"))
        text = self.last_text()
        self.assertIn("claude:sess-1", text)
        self.assertIn("DM-1-02", text)  # on_story via the fixture repo
        self.assertIn("awaiting a response", text)

    def test_peek_is_read_only_capture(self) -> None:
        self.iface.handle_update(message(OWNER, "/peek desk"))
        self.assertEqual(
            self.tmux_runner.calls,
            [["tmux", "capture-pane", "-p", "-t", "desk"]],
        )


# ---------------------------------------------------------------- Q&A relay


class QARelayTest(InterfaceCase):
    def setUp(self) -> None:
        super().setUp()
        self.pair()

    def test_question_surfaces_with_story_correlation(self) -> None:
        self.iface.poll_tick()
        text = self.last_text()
        self.assertIn("Claude on DM-1-02 is asking:", text)
        self.assertIn("Should I delete the flag?", text)
        sent_before = len(self.transport.sent)
        self.iface.poll_tick()  # same question is not re-pushed
        self.assertEqual(len(self.transport.sent), sent_before)

    def test_reply_reaches_the_right_pane_when_armed(self) -> None:
        self.iface.handle_update(message(OWNER, "/arm desk"))
        self.iface.handle_update(
            message(OWNER, "/reply claude:sess-1 yes, delete it")
        )
        self.assertIn("Relay into", self.last_text())
        self.approve_last()
        self.assertIn("relayed", self.last_text())
        sends = [c for c in self.tmux_runner.calls if c[1] == "send-keys"]
        self.assertEqual(
            sends,
            [
                ["tmux", "send-keys", "-t", "%7", "-l", "yes, delete it"],
                ["tmux", "send-keys", "-t", "%7", "Enter"],
            ],
            "the driver targets the registry pane, literally",
        )

    def test_reply_approval_is_the_arming_grant(self) -> None:
        # No prior /arm: the proposal preview names the arming, and
        # the approval tap grants it — one explicit act, not two.
        self.iface.handle_update(
            message(OWNER, "/reply claude:sess-1 yes, delete it")
        )
        self.assertIn("Approving also arms 'desk'", self.last_text())
        self.approve_last()
        self.assertIn("relayed (armed 'desk' for 15 min)", self.last_text())
        self.assertTrue(
            [c for c in self.tmux_runner.calls if c[1] == "send-keys"]
        )
        self.iface.handle_update(message(OWNER, "/armed"))
        self.assertIn("desk armed until", self.last_text())

    def test_recycled_pane_id_is_refused(self) -> None:
        # Live-found (2026-07-04): pane ids are only unique per tmux
        # server. A stale registry entry pointed at %0, which the
        # current server had reassigned to the bot's own console —
        # the relay typed into the wrong pane and reported success.
        # The driver must prove pane ownership before one keystroke.
        def hijacked(argv, cwd):
            if argv[1] == "display-message":
                return types.SimpleNamespace(
                    returncode=0, stdout="dw-telegram\n", stderr=""
                )
            return None

        runner = RecordingRunner(hijacked)
        self.iface.driver = TmuxDriver(
            Arming(self.state), runner=runner
        )
        self.iface.handle_update(message(OWNER, "/arm desk"))
        self.iface.handle_update(
            message(OWNER, "/reply claude:sess-1 hello?")
        )
        self.approve_last()
        text = self.last_text()
        self.assertIn("belongs to tmux session 'dw-telegram'", text)
        self.assertIn("nothing was typed", text)
        self.assertEqual(
            [c for c in runner.calls if c[1] == "send-keys"], []
        )

    def test_dead_pane_is_refused(self) -> None:
        def dead(argv, cwd):
            if argv[1] == "display-message":
                return types.SimpleNamespace(
                    returncode=1, stdout="", stderr="can't find pane %7"
                )
            return None

        runner = RecordingRunner(dead)
        self.iface.driver = TmuxDriver(
            Arming(self.state), runner=runner
        )
        self.iface.handle_update(message(OWNER, "/arm desk"))
        self.iface.handle_update(
            message(OWNER, "/reply claude:sess-1 hello?")
        )
        self.approve_last()
        self.assertIn("does not exist", self.last_text())
        self.assertEqual(
            [c for c in runner.calls if c[1] == "send-keys"], []
        )

    def test_no_keystroke_without_a_grant(self) -> None:
        # The driver boundary is intact: text that never passed
        # through an arming grant (no /arm, no approved reply) is
        # refused below the chat layer.
        with self.assertRaises(Unarmed):
            self.iface.driver.send_text(
                "desk", "%7", "sneaky", self.clock()
            )
        self.assertEqual(
            [c for c in self.tmux_runner.calls if c[1] == "send-keys"],
            [],
            "not one keystroke without a grant",
        )

    def test_arming_expires(self) -> None:
        self.iface.handle_update(message(OWNER, "/arm desk 15"))
        self.clock.advance(minutes=16)
        self.iface.handle_update(message(OWNER, "/armed"))
        self.assertIn("nothing is armed", self.last_text())
        # A late reply needs (and gets) a fresh grant via its tap.
        self.iface.handle_update(
            message(OWNER, "/reply claude:sess-1 late answer")
        )
        self.assertIn("Approving also arms", self.last_text())

    def test_reply_to_a_session_outside_tmux_explains_itself(self) -> None:
        self.iface.handle_update(
            message(OWNER, "/reply claude:bare-term go ahead")
        )
        text = self.last_text()
        self.assertIn("not running inside tmux", text)
        self.assertIn("/launch", text)
        self.assertIsNone(self.transport.sent[-1]["buttons"])

    def test_unsteerable_sessions_are_marked(self) -> None:
        self.iface.handle_update(message(OWNER, "/sessions"))
        self.assertIn("[not steerable — no tmux]", self.last_text())
        self.iface.handle_update(message(OWNER, "/questions"))
        bare = [
            t for t in self.sent_texts() if "Ship it?" in t
        ]
        self.assertTrue(bare)
        self.assertIn("answer it at the desk", bare[-1])
        self.assertNotIn("/reply claude:bare-term", bare[-1])

    def test_disarm_and_status(self) -> None:
        self.iface.handle_update(message(OWNER, "/arm desk"))
        self.iface.handle_update(message(OWNER, "/armed"))
        self.assertIn("desk armed until", self.last_text())
        self.iface.handle_update(message(OWNER, "/disarm desk"))
        self.iface.handle_update(message(OWNER, "/armed"))
        self.assertIn("nothing is armed", self.last_text())


# ---------------------------------------------------------------- the crown


class CrownCaseTest(InterfaceCase):
    def setUp(self) -> None:
        super().setUp()
        self.pair()

    def test_approved_dishonest_done_flip_is_refused_with_banner(self) -> None:
        self.iface.handle_update(message(OWNER, "/flip demo 1 DM-1-02 done"))
        self.assertIn("Flip DM-1-02", self.last_text())
        self.approve_last()
        text = self.last_text()
        self.assertIn("the rails refused:", text)
        self.assertIn(
            "refusing to mark story done without evidence", text,
            "the dw banner rides into chat verbatim",
        )

    def test_honest_flip_executes(self) -> None:
        self.iface.handle_update(
            message(OWNER, "/flip demo 1 DM-1-02 blocked")
        )
        self.approve_last()
        self.assertIn("done:", self.last_text())
        status = (
            self.repo
            / "pm/roadmap/demo/phase-1-alpha/current-phase-status.md"
        ).read_text()
        self.assertIn("| blocked |", status)

    def test_unknown_story_never_becomes_a_proposal(self) -> None:
        self.iface.handle_update(message(OWNER, "/flip demo 1 DM-9-99 done"))
        self.assertIn("not on the demo roadmap", self.last_text())
        self.assertIsNone(self.transport.sent[-1]["buttons"])


# ---------------------------------------------------------------- driver


class DriverTest(InterfaceCase):
    def setUp(self) -> None:
        super().setUp()
        self.pair()

    def test_launch_all_supported_harnesses(self) -> None:
        for harness in ("claude", "codex", "pi"):
            self.iface.handle_update(
                message(OWNER, f"/launch {harness} {self.repo} run-{harness}")
            )
            self.approve_last()
            self.assertIn(f"launched {harness}", self.last_text())
        launches = [
            c for c in self.tmux_runner.calls if c[1] == "new-session"
        ]
        self.assertEqual(
            [c[-1] for c in launches], ["claude", "codex", "pi"]
        )
        for call in launches:
            self.assertEqual(call[2], "-d", "sessions launch detached")

    def test_unsupported_harness_refused(self) -> None:
        self.iface.handle_update(
            message(OWNER, f"/launch bash {self.repo}")
        )
        self.approve_last()
        self.assertIn("not supported", self.last_text())

    def test_launched_session_starts_unarmed(self) -> None:
        self.iface.handle_update(
            message(OWNER, f"/launch claude {self.repo} fresh")
        )
        self.approve_last()
        driver = self.iface.driver
        with self.assertRaises(Unarmed):
            driver.send_text("fresh", "fresh", "hello", self.clock())


# ---------------------------------------------------------------- lifecycle


class LifecycleTest(InterfaceCase):
    def setUp(self) -> None:
        super().setUp()
        self.pair()

    def test_create_outside_roots_refused_before_proposal(self) -> None:
        outside = Path(tempfile.mkdtemp(prefix="dw-outside."))
        self.addCleanup(shutil.rmtree, outside, ignore_errors=True)
        self.iface.handle_update(
            message(OWNER, f"/newproject {outside}/x proj PX Project X")
        )
        self.assertIn("outside the allow-listed workspace roots", self.last_text())
        self.assertIsNone(self.transport.sent[-1]["buttons"])

    def test_open_requires_rails_repo_within_roots(self) -> None:
        bare = self.tmp / "bare"
        bare.mkdir()
        self.iface.handle_update(message(OWNER, f"/open {bare}"))
        self.assertIn("not a rails repo", self.last_text())
        self.iface.handle_update(message(OWNER, f"/open {self.repo}"))
        self.assertIn("active rails repo", self.last_text())

    def test_create_step_sequence_with_scripted_runner(self) -> None:
        target = self.tmp / "fresh-project"

        def hook(argv, cwd):
            if "contract" in argv:
                contract = target / ".tmp" / "CONTRACT.md"
                contract.parent.mkdir(parents=True, exist_ok=True)
                contract.write_text("- [ ] No bypasses.\n")
            if argv[-1] == "init" or (argv[0] == "git" and argv[1] == "init"):
                target.mkdir(exist_ok=True)
            return None

        runner = RecordingRunner(hook)
        lifecycle = LifecycleClient(
            self.config,
            RailsClient(dw_cli=self.config.dw_cli),
            runner=runner,
        )
        steps, reason = lifecycle.plan_create(
            target, "fresh", "FR", "Fresh Project"
        )
        self.assertIsNotNone(steps, reason)
        ok, report = lifecycle.execute(target, steps)
        self.assertTrue(ok, report)
        labels = [line.lstrip("✓✗ ").split(":")[0] for line in report]
        self.assertEqual(
            labels,
            [
                "git init", "install rails", "roadmap skeleton", "doctor",
                "stage", "contract", "certify bootstrap contract",
                "first gated commit",
            ],
        )
        self.assertIn(
            "- [x] No bypasses.",
            (target / ".tmp" / "CONTRACT.md").read_text(),
        )

    def test_create_for_real_lands_on_the_rails(self) -> None:
        """The full leg, no fakes: scaffold → rails → doctor →
        first gated commit, gate hooks live."""
        gitconfig = self.tmp / "gitconfig"
        gitconfig.write_text(
            "[user]\n\tname = Fixture Owner\n\temail = fixture@example.test\n"
        )
        old = {
            key: os.environ.get(key)
            for key in ("GIT_CONFIG_GLOBAL", "GIT_CONFIG_SYSTEM")
        }
        os.environ["GIT_CONFIG_GLOBAL"] = str(gitconfig)
        os.environ["GIT_CONFIG_SYSTEM"] = os.devnull

        def restore() -> None:
            for key, value in old.items():
                if value is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = value

        self.addCleanup(restore)

        target = self.tmp / "real-project"
        lifecycle = LifecycleClient(
            self.config, RailsClient(dw_cli=self.config.dw_cli)
        )
        steps, reason = lifecycle.plan_create(
            target, "real", "RL", "Real Project"
        )
        self.assertIsNotNone(steps, reason)
        ok, report = lifecycle.execute(target, steps)
        self.assertTrue(ok, "\n".join(report))
        head = subprocess.run(
            ["git", "-C", str(target), "log", "--oneline"],
            stdout=subprocess.PIPE,
            text=True,
            check=True,
        ).stdout
        self.assertIn("Adopt Delivery Workbench rails", head)
        self.assertTrue((target / "pm" / "roadmap" / "real").is_dir())
        self.assertTrue((target / ".githooks" / "dw").is_file())


# ---------------------------------------------------------------- hygiene


class TokenHygieneTest(unittest.TestCase):
    def test_env_token_overrides_missing_config(self) -> None:
        tmp = Path(tempfile.mkdtemp(prefix="dw-cfg."))
        self.addCleanup(shutil.rmtree, tmp, ignore_errors=True)
        config = load_config(
            tmp / "absent.json", env={"TELEGRAM_BOT_TOKEN": "unit-test-token"}
        )
        self.assertEqual(config.bot_token, "unit-test-token")

    def test_missing_token_error_names_path_not_content(self) -> None:
        tmp = Path(tempfile.mkdtemp(prefix="dw-cfg."))
        self.addCleanup(shutil.rmtree, tmp, ignore_errors=True)
        with self.assertRaises(ConfigError) as caught:
            load_config(tmp / "absent.json", env={})
        self.assertIn("absent.json", str(caught.exception))

    def test_transport_errors_never_carry_the_token(self) -> None:
        import urllib.request

        transport = HttpTransport("SECRET-TOKEN-VALUE")
        original = urllib.request.urlopen

        def explode(*_args, **_kwargs):
            raise OSError("connect https://api.telegram.org/botSECRET-TOKEN-VALUE/x")

        urllib.request.urlopen = explode
        try:
            with self.assertRaises(TransportError) as caught:
                transport.send(1, "hello")
        finally:
            urllib.request.urlopen = original
        self.assertNotIn("SECRET-TOKEN-VALUE", str(caught.exception))


# ---------------------------------------------------------------- schemas


class SchemaComplianceTest(unittest.TestCase):
    def test_unproven_feed_schema_refused_politely(self) -> None:
        def runner(argv, cwd=None):
            return types.SimpleNamespace(
                returncode=0,
                stdout=json.dumps({"feed_schema": 2, "projects": []}),
                stderr="",
            )

        rails = RailsClient(dw_cli=["dw"], runner=runner)
        doc, reason = rails.read_feed(Path("/anywhere"))
        self.assertIsNone(doc)
        self.assertIn("proven against", reason)

    def test_unproven_sessions_schema_refused_politely(self) -> None:
        def runner(argv, cwd=None):
            return types.SimpleNamespace(
                returncode=0,
                stdout=json.dumps({"sessions_schema": 99, "sessions": []}),
                stderr="",
            )

        rails = RailsClient(dw_cli=["dw"], runner=runner)
        doc, reason = rails.read_sessions(Path("/anywhere"))
        self.assertIsNone(doc)
        self.assertIn("proven against", reason)

    def test_story_argv_allow_list_is_two_verbs(self) -> None:
        rails = RailsClient(dw_cli=["dw"])
        with self.assertRaises(ValueError):
            rails.build_story_argv(
                Path("/r"), {"verb": "delete", "project": "x"}
            )
        argv = rails.build_story_argv(
            Path("/r"),
            {
                "verb": "status", "project": "p", "phase": 1,
                "story": "S-1-01", "status": "done",
            },
        )
        self.assertEqual(argv[:4], ["dw", "--root", "/r", "story"])




# ---------------------------------------------------------- hook drain


from dw_telegram.agentevents import decide_pushes, read_new_events


class AgentEventsReaderTest(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="dw-events-test."))
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)
        self.path = self.tmp / "agent-events.jsonl"

    def append(self, text):
        with self.path.open("a") as fh:
            fh.write(text)

    def test_reads_incrementally_by_offset(self):
        self.append('{"event": "Stop", "agent": "claude"}\n')
        events, offset = read_new_events(self.path, 0)
        self.assertEqual([e["event"] for e in events], ["Stop"])
        events2, offset2 = read_new_events(self.path, offset)
        self.assertEqual(events2, [])
        self.append('{"event": "Notification"}\n')
        events3, _ = read_new_events(self.path, offset2)
        self.assertEqual([e["event"] for e in events3], ["Notification"])

    def test_partial_tail_waits_for_its_newline(self):
        self.append('{"event": "Stop"}\n{"event": "Notif')
        events, offset = read_new_events(self.path, 0)
        self.assertEqual(len(events), 1)
        self.append('ication"}\n')
        events2, _ = read_new_events(self.path, offset)
        self.assertEqual([e["event"] for e in events2], ["Notification"])

    def test_truncation_resets_honestly(self):
        self.append('{"event": "Stop"}\n' * 5)
        _, offset = read_new_events(self.path, 0)
        self.path.write_text('{"event": "SessionStart"}\n')
        events, _ = read_new_events(self.path, offset)
        self.assertEqual([e["event"] for e in events], ["SessionStart"])

    def test_malformed_lines_are_skipped_not_fatal(self):
        self.append('not json\n{"event": "Notification"}\n[1,2]\n')
        events, _ = read_new_events(self.path, 0)
        self.assertEqual([e["event"] for e in events], ["Notification"])

    def test_missing_file_is_empty(self):
        events, offset = read_new_events(self.path, 999)
        self.assertEqual((events, offset), ([], 0))

    def test_decide_pushes_only_notifications_coalesced(self):
        events = [
            {"event": "Stop", "session_id": "a"},
            {"event": "Notification", "session_id": "a", "ts": "1"},
            {"event": "Notification", "session_id": "a", "ts": "2"},
            {"event": "Notification", "session_id": "b", "ts": "3"},
            {"event": "SessionEnd", "session_id": "b"},
        ]
        pushes = decide_pushes(events)
        self.assertEqual(
            [(p["session_id"], p["ts"]) for p in pushes],
            [("a", "2"), ("b", "3")],
            "latest per session, order preserved, nothing else pushes",
        )


class HookDrainTest(InterfaceCase):
    def setUp(self):
        super().setUp()
        self.pair()
        self.events_path = self.tmp / "agent-events.jsonl"
        self.config.agent_events_path = self.events_path

    def emit(self, event, session="hook-sess-1"):
        with self.events_path.open("a") as fh:
            fh.write(json.dumps({
                "ts": "2026-07-04T20:00:00Z", "agent": "claude",
                "event": event, "session_id": session, "cwd": str(self.repo),
            }) + "\n")

    def test_notification_pushes_in_the_same_drain(self):
        self.emit("Notification")
        pushed = self.iface.drain_agent_events()
        self.assertEqual(pushed, 1)
        texts = self.sent_texts()
        self.assertTrue(any("needs attention" in t for t in texts), texts)
        # poll_tick ran right after: the fixture registry question rode along
        self.assertTrue(
            any("is asking:" in t for t in texts),
            "the correlated question enriches the push",
        )

    def test_stop_records_but_does_not_push(self):
        self.emit("Stop")
        self.assertEqual(self.iface.drain_agent_events(), 0)
        self.assertEqual(self.transport.sent, [])

    def test_restart_never_repushes(self):
        self.emit("Notification")
        self.iface.drain_agent_events()
        sent_before = len(self.transport.sent)
        fresh_state = RuntimeState(self.config.resolved_state_path())
        self.assertEqual(
            fresh_state.events_offset, self.state.events_offset,
            "the offset persisted",
        )
        arming = Arming(fresh_state)
        fresh = TelegramInterface(
            self.config, fresh_state, self.transport,
            driver=TmuxDriver(arming, runner=self.tmux_runner, sleeper=lambda _s: None),
            clock=self.clock,
        )
        self.assertEqual(fresh.drain_agent_events(), 0)
        self.assertEqual(len(self.transport.sent), sent_before)

    def test_unpaired_drain_is_silent_and_consumes_nothing(self):
        self.state.paired_chat = None
        self.emit("Notification")
        self.assertEqual(self.iface.drain_agent_events(), 0)
        self.assertEqual(self.state.events_offset, 0,
                         "unpaired leaves the stream for later")



# ------------------------------------------------------- message layer


from dw_telegram.entities import chunk, to_entities
from dw_telegram.msgqueue import MessageQueue, OutMessage, plan_batch


class EntitiesTest(unittest.TestCase):
    def test_hostile_characters_need_no_escaping(self):
        hostile = "a_b*c[d](e)~f`g>h#i+j-k=l|m{n}o.p!q"
        plain, entities = to_entities(hostile)
        self.assertEqual(plain, hostile)
        self.assertEqual(entities, [])

    def test_bold_code_pre_become_entities(self):
        plain, entities = to_entities(
            "**bold** then `code` then:\n```\npre block\n```"
        )
        self.assertEqual(plain, "bold then code then:\npre block")
        self.assertEqual(
            [(e["type"], e["offset"], e["length"]) for e in entities],
            [("bold", 0, 4), ("code", 10, 4), ("pre", 21, 9)],
        )

    def test_offsets_are_utf16_after_emoji(self):
        plain, entities = to_entities("🙋 **bold**")
        # the emoji is TWO utf-16 units; a char count would say 2, not 3
        self.assertEqual(entities, [{"type": "bold", "offset": 3, "length": 4}])
        self.assertEqual(plain, "🙋 bold")

    def test_chunk_prefers_line_boundaries_and_rescopes(self):
        text = "\n".join(f"line {i}" for i in range(400))
        plain, entities = to_entities("**" + text[:6] + "**" + text[6:])
        pieces = chunk(plain, entities, limit=1000)
        self.assertGreater(len(pieces), 1)
        self.assertEqual("".join(piece for piece, _ in pieces), plain)
        for piece, _ in pieces[:-1]:
            self.assertTrue(piece.endswith("\n"), "cuts at line boundaries")
        self.assertEqual(pieces[0][1][0]["offset"], 0, "entity rescoped")


class PlanBatchTest(unittest.TestCase):
    def test_adjacent_texts_merge_statuses_coalesce(self):
        pending = [
            OutMessage(1, "first"),
            OutMessage(1, "second"),
            OutMessage(1, "working… 10%", kind="status"),
            OutMessage(1, "third with buttons", buttons=[[("A", "a")]]),
            OutMessage(1, "working… 90%", kind="status"),
            OutMessage(1, "fourth"),
        ]
        actions = plan_batch(pending)
        self.assertEqual(
            [(a.op, a.text) for a in actions],
            [
                ("send", "first\n\nsecond"),
                ("send", "third with buttons"),
                ("send", "fourth"),
                ("edit_status", "working… 90%"),
            ],
            "merge adjacent, never merge buttons, only the latest status",
        )

    def test_merge_respects_the_cap(self):
        big = "x" * 3000
        actions = plan_batch([OutMessage(1, big), OutMessage(1, big)])
        self.assertEqual(len(actions), 2, "over the cap stays separate")


class MessageQueueTest(unittest.TestCase):
    def setUp(self):
        self.transport = ScriptedTransport()
        self.naps = []
        self.queue = MessageQueue(self.transport, sleeper=self.naps.append)

    def test_burst_arrives_ordered_and_merged(self):
        for i in range(4):
            self.queue.enqueue(1, f"msg {i}")
        self.queue.flush()
        self.assertEqual(len(self.transport.sent), 1)
        self.assertEqual(
            self.transport.sent[0]["text"], "msg 0\n\nmsg 1\n\nmsg 2\n\nmsg 3"
        )

    def test_entity_rejection_falls_back_to_plain(self):
        self.transport.reject_entities = True
        self.queue.enqueue(1, "**bold** stays readable")
        self.queue.flush()
        self.assertEqual(len(self.transport.sent), 1)
        sent = self.transport.sent[0]
        self.assertEqual(sent["text"], "bold stays readable")
        self.assertIsNone(sent["entities"], "second phase shipped plain")

    def test_flood_control_pauses_and_retries(self):
        self.transport.flood_after = (0, 7.0)
        self.queue.enqueue(1, "patient message")
        self.queue.flush()
        self.assertEqual(self.naps, [7.0], "the retry_after pause was honored")
        self.assertEqual(len(self.transport.sent), 1, "delivered after the pause")

    def test_status_edits_in_place(self):
        self.queue.enqueue(1, "working… 10%", kind="status")
        self.queue.flush()
        self.queue.enqueue(1, "working… 90%", kind="status")
        self.queue.flush()
        self.assertEqual(len(self.transport.sent), 1, "one bubble")
        self.assertEqual(len(self.transport.edited), 1)
        self.assertEqual(self.transport.edited[0]["text"], "working… 90%")

    def test_oversize_text_chunks_at_send_layer(self):
        self.queue.enqueue(1, "\n".join(f"row {i}" for i in range(900)))
        self.queue.flush()
        self.assertGreater(len(self.transport.sent), 1)
        rebuilt = "".join(s["text"] for s in self.transport.sent)
        self.assertIn("row 899", rebuilt, "nothing truncated, only split")


class CardLifecycleTest(InterfaceCase):
    def setUp(self):
        super().setUp()
        self.pair()

    def _callback_with_message_id(self, data, message_id):
        return {
            "callback_query": {
                "id": "cb-x", "data": data,
                "message": {"chat": {"id": OWNER}, "message_id": message_id},
            }
        }

    def test_one_card_edits_through_its_lifecycle(self):
        self.iface.handle_update(
            message(OWNER, "/flip demo 1 DM-1-02 blocked")
        )
        card = self.transport.sent[-1]
        self.assertIsNotNone(card["buttons"])
        proposal_id = card["buttons"][0][0][1].split(":", 1)[1]
        self.iface.handle_update(
            self._callback_with_message_id(
                f"ap:{proposal_id}", card["message_id"]
            )
        )
        edits = [
            e for e in self.transport.edited
            if e["message_id"] == card["message_id"]
        ]
        self.assertEqual(len(edits), 1, "the card itself was edited")
        self.assertIn("✓ done:", edits[0]["text"])
        self.assertIn("Flip DM-1-02", edits[0]["text"], "preview retained")

    def test_rejection_edits_the_card_too(self):
        self.iface.handle_update(
            message(OWNER, "/flip demo 1 DM-1-02 blocked")
        )
        card = self.transport.sent[-1]
        proposal_id = card["buttons"][0][0][1].split(":", 1)[1]
        self.iface.handle_update(
            self._callback_with_message_id(
                f"rj:{proposal_id}", card["message_id"]
            )
        )
        self.assertIn("rejected", self.transport.edited[-1]["text"])



# ----------------------------------------------------- topics = projects


from dw_telegram.topics import TopicRouter, topic_key


class TopicRouterTest(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="dw-topics-test."))
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)
        self.state = RuntimeState(self.tmp / "state.json")
        self.router = TopicRouter(self.state)
        self.clock = FakeClock()

    def test_repo_bind_scope_and_reverse(self):
        self.router.bind_repo(1, 10, "/repos/a")
        self.router.bind_repo(1, 20, "/repos/b")
        self.assertEqual(self.router.repo_for(1, 10), "/repos/a")
        self.assertEqual(self.router.repo_for(1, 20), "/repos/b")
        self.assertIsNone(self.router.repo_for(1, 99))
        self.assertEqual(self.router.topic_for_repo(1, "/repos/b"), 20)
        self.assertIsNone(self.router.topic_for_repo(1, "/nope"))

    def test_flat_chat_is_the_none_topic(self):
        self.router.bind_repo(1, None, "/repos/flat")
        self.assertEqual(self.router.repo_for(1, None), "/repos/flat")
        self.assertEqual(topic_key(1, None), "1:-")

    def test_unbind_repo_cascades_to_session(self):
        self.router.bind_repo(1, 10, "/repos/a")
        self.router.bind_session(1, 10, "claude:s", "%1", "desk", self.clock())
        self.router.unbind_repo(1, 10)
        self.assertIsNone(self.router.bound_session(1, 10, self.clock()))

    def test_session_binding_expires_but_activity_refreshes(self):
        self.router.bind_session(1, 10, "claude:s", "%1", "desk", self.clock())
        self.clock.advance(minutes=25)
        # a read within the window refreshes the idle clock
        self.assertIsNotNone(self.router.bound_session(1, 10, self.clock()))
        self.clock.advance(minutes=25)
        self.assertIsNotNone(self.router.bound_session(1, 10, self.clock()))
        self.clock.advance(minutes=31)
        self.assertIsNone(self.router.bound_session(1, 10, self.clock()))

    def test_bindings_persist_across_restart(self):
        self.router.bind_repo(1, 10, "/repos/a")
        self.router.bind_session(1, 10, "claude:s", "%1", "desk", self.clock())
        reloaded = RuntimeState(self.tmp / "state.json")
        router2 = TopicRouter(reloaded)
        self.assertEqual(router2.repo_for(1, 10), "/repos/a")
        self.assertIsNotNone(router2.bound_session(1, 10, self.clock()))


class TopicScopingTest(InterfaceCase):
    def setUp(self):
        super().setUp()
        self.config.default_repo = None  # force topic scoping to matter
        self.pair()

    def test_bind_then_commands_scope_to_the_topic(self):
        self.iface.handle_update(
            topic_message(OWNER, f"/bind {self.repo}", 77)
        )
        self.assertIn("is now", self.last_text())
        # /state in the bound topic needs no repo arg and hits that repo
        self.iface.handle_update(topic_message(OWNER, "/state", 77))
        text = self.last_text()
        self.assertIn("demo", text)
        self.assertIn("DM-1-02", text)

    def test_replies_land_in_the_originating_topic(self):
        self.iface.handle_update(topic_message(OWNER, f"/bind {self.repo}", 77))
        self.iface.handle_update(topic_message(OWNER, "/state", 77))
        self.assertEqual(self.transport.sent[-1]["thread_id"], 77)

    def test_unbound_topic_has_no_repo(self):
        self.iface.handle_update(topic_message(OWNER, "/state", 88))
        self.assertIn("no rails repo here", self.last_text())

    def test_flat_chat_still_uses_active_repo(self):
        self.iface.handle_update(message(OWNER, f"/open {self.repo}"))
        self.iface.handle_update(message(OWNER, "/state"))
        self.assertIn("demo", self.last_text())
        self.assertIsNone(self.transport.sent[-1]["thread_id"])


class FlowingConversationTest(InterfaceCase):
    def setUp(self):
        super().setUp()
        self.pair()
        self.iface.handle_update(topic_message(OWNER, f"/bind {self.repo}", 5))

    def test_steer_then_plain_text_flows_no_tap(self):
        self.iface.handle_update(
            topic_message(OWNER, "/steer claude:sess-1", 5)
        )
        self.assertIn("steering", self.last_text())
        self.tmux_runner.calls.clear()
        self.iface.handle_update(
            topic_message(OWNER, "yes, delete the flag", 5)
        )
        sends = [c for c in self.tmux_runner.calls if c[1] == "send-keys"]
        self.assertEqual(
            sends,
            [
                ["tmux", "send-keys", "-t", "%7", "-l", "yes, delete the flag"],
                ["tmux", "send-keys", "-t", "%7", "Enter"],
            ],
            "plain text relays to the bound pane with no proposal",
        )
        # and no proposal card was ever offered
        self.assertFalse(
            any(s["buttons"] for s in self.transport.sent[-2:]),
            "conversation flows without a tap",
        )

    def test_plain_text_without_a_binding_is_refused_gently(self):
        self.iface.handle_update(topic_message(OWNER, "just chatting", 5))
        self.assertIn("no session bound", self.last_text())
        self.assertEqual(
            [c for c in self.tmux_runner.calls if c[1] == "send-keys"], []
        )

    def test_unsteer_stops_the_flow(self):
        self.iface.handle_update(topic_message(OWNER, "/steer claude:sess-1", 5))
        self.iface.handle_update(topic_message(OWNER, "/unsteer", 5))
        self.assertIn("stopped steering", self.last_text())
        self.tmux_runner.calls.clear()
        self.iface.handle_update(topic_message(OWNER, "hello?", 5))
        self.assertIn("no session bound", self.last_text())
        self.assertEqual(
            [c for c in self.tmux_runner.calls if c[1] == "send-keys"], []
        )

    def test_a_question_routes_home_to_its_repo_topic(self):
        # the fixture registry session is in self.repo, bound to topic 5
        self.iface.poll_tick()
        homed = [
            s for s in self.transport.sent
            if "is asking:" in s["text"] and s["thread_id"] == 5
        ]
        self.assertTrue(homed, "the question landed in the repo's topic")



# --------------------------------------------------- driver's manners


from dw_telegram.tmuxdrive import HARNESS, content_hash


class DriverMannersTest(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="dw-driver-test."))
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)
        self.state = RuntimeState(self.tmp / "state.json")
        self.arming = Arming(self.state)
        self.clock = FakeClock()
        self.naps = []
        self.runner = RecordingRunner(
            lambda argv, cwd: types.SimpleNamespace(
                returncode=0, stdout="desk\n", stderr="")
            if argv[1] == "display-message" else None
        )
        self.driver = TmuxDriver(
            self.arming, runner=self.runner, sleeper=self.naps.append
        )
        self.arming.arm("desk", self.clock())

    def test_literal_then_settle_then_enter_separately(self):
        ok, _ = self.driver.send_text("desk", "%1", "hello", self.clock(),
                                      harness="claude")
        self.assertTrue(ok)
        sends = [c for c in self.runner.calls if c[1] == "send-keys"]
        self.assertEqual(
            sends,
            [
                ["tmux", "send-keys", "-t", "%1", "-l", "hello"],
                ["tmux", "send-keys", "-t", "%1", "Enter"],
            ],
        )
        self.assertEqual(self.naps, [0.5], "claude's settle pause between them")

    def test_settle_is_per_harness_from_the_table(self):
        self.driver.send_text("desk", "%1", "x", self.clock(), harness="codex")
        self.assertEqual(self.naps, [0.3], "codex settle from the capability table")

    def test_send_key_is_a_single_named_key(self):
        ok, _ = self.driver.send_key("desk", "%1", "Escape", self.clock())
        self.assertTrue(ok)
        self.assertIn(["tmux", "send-keys", "-t", "%1", "Escape"], self.runner.calls)

    def test_recovery_verbs_follow_capability(self):
        self.assertEqual(HARNESS["claude"].recovery_verbs, ("resume", "fresh"))
        self.assertEqual(HARNESS["pi"].recovery_verbs, ("fresh",))

    def test_resume_launch_only_when_supported(self):
        ok, msg = self.driver.launch("claude", "s1", "/tmp", resume=True)
        self.assertTrue(ok)
        newsess = [c for c in self.runner.calls if c[1] == "new-session"]
        self.assertEqual(newsess[-1][-1], "claude --resume")
        ok2, msg2 = self.driver.launch("pi", "s2", "/tmp", resume=True)
        self.assertFalse(ok2)
        self.assertIn("no resume", msg2)

    def test_content_hash_gates(self):
        self.assertEqual(content_hash("same"), content_hash("same"))
        self.assertNotEqual(content_hash("a"), content_hash("b"))


class LiveViewTest(InterfaceCase):
    def setUp(self):
        super().setUp()
        self.pair()
        self.frames = ["frame one", "frame one", "frame two"]
        def cap(argv, cwd):
            if argv[1] == "capture-pane":
                text = self.frames.pop(0) if self.frames else "frame two"
                return types.SimpleNamespace(returncode=0, stdout=text, stderr="")
            if argv[1] == "display-message":
                return types.SimpleNamespace(returncode=0, stdout="desk\n", stderr="")
            return None
        self.tmux_runner.hook = cap

    def test_live_view_edits_only_on_change(self):
        self.iface.handle_update(message(OWNER, "/live %7"))
        first = self.transport.sent[-1]
        self.assertIn("live, read-only", first["text"])
        # second frame identical → no edit
        self.iface.refresh_live_views()
        self.assertEqual(len(self.transport.edited), 0, "no change, no edit")
        # third frame differs → one edit
        self.iface.refresh_live_views()
        self.assertEqual(len(self.transport.edited), 1)
        self.assertIn("frame two", self.transport.edited[-1]["text"])

    def test_live_view_is_read_only(self):
        self.iface.handle_update(message(OWNER, "/live %7"))
        self.iface.refresh_live_views()
        self.assertEqual(
            [c for c in self.tmux_runner.calls if c[1] == "send-keys"], [],
            "a live view never sends a keystroke",
        )

    def test_live_view_expires(self):
        self.iface.handle_update(message(OWNER, "/live %7"))
        self.clock.advance(minutes=6)
        self.iface.refresh_live_views()
        self.assertEqual(self.iface._live_views, {}, "expired view dropped")


class ToolbarTest(InterfaceCase):
    def setUp(self):
        super().setUp()
        self.pair()
        self.iface.handle_update(topic_message(OWNER, f"/bind {self.repo}", 3))
        self.iface.handle_update(topic_message(OWNER, "/steer claude:sess-1", 3))

    def _kb(self, data, thread):
        return {"callback_query": {
            "id": "cb-kb", "data": data,
            "message": {"chat": {"id": OWNER}, "message_id": 1,
                        "message_thread_id": thread}}}

    def test_toolbar_only_offered_when_bound(self):
        self.iface.handle_update(topic_message(OWNER, "/toolbar", 3))
        self.assertIsNotNone(self.transport.sent[-1]["buttons"])
        # an unbound topic gets a refusal, no buttons
        self.iface.handle_update(topic_message(OWNER, "/toolbar", 999))
        self.assertIn("no session bound", self.last_text())
        self.assertIsNone(self.transport.sent[-1]["buttons"])

    def test_toolbar_press_fires_a_key_no_extra_tap(self):
        self.tmux_runner.calls.clear()
        self.iface.handle_update(self._kb("kb:Escape", 3))
        keys = [c for c in self.tmux_runner.calls if c[1] == "send-keys"]
        self.assertEqual(keys, [["tmux", "send-keys", "-t", "%7", "Escape"]])
        self.assertEqual(self.transport.answered[-1]["text"], "Escape")

    def test_toolbar_press_without_binding_refused(self):
        self.iface.handle_update(topic_message(OWNER, "/unsteer", 3))
        self.tmux_runner.calls.clear()
        self.iface.handle_update(self._kb("kb:Enter", 3))
        self.assertIn("no live binding", self.transport.answered[-1]["text"])
        self.assertEqual(
            [c for c in self.tmux_runner.calls if c[1] == "send-keys"], [])


class RecoveryTest(InterfaceCase):
    def setUp(self):
        super().setUp()
        self.pair()
        self.iface.handle_update(message(OWNER, f"/open {self.repo}"))

    def test_steer_a_dead_session_offers_capability_recovery(self):
        # display-message returns a DIFFERENT session → the pane is stale
        def stale(argv, cwd):
            if argv[1] == "display-message":
                return types.SimpleNamespace(
                    returncode=1, stdout="", stderr="no such pane")
            return None
        self.tmux_runner.hook = stale
        self.iface.handle_update(message(OWNER, "/steer claude:sess-1"))
        text = self.last_text()
        self.assertIn("looks gone", text)
        self.assertIn("resume, fresh", text)  # claude supports resume

if __name__ == "__main__":
    unittest.main(verbosity=2)
