"""The Telegram interface core: one paired owner, three consent rings.

Every inbound update lands here. An unpaired chat gets silence
beyond the pairing prompt. The paired chat gets the read surface
(state, events, sessions, questions, previews), and every steering
act — story verbs, text relay, harness launch, project lifecycle —
becomes a proposal with an explicit preview that executes only on
the approval tap, through the seams the contract names: the
allow-listed story argv (§4 ring 2), the armed tmux driver
(ring 3), and the path-allow-listed lifecycle.

The core is transport- and subprocess-agnostic so CI can prove all
of it against a scripted transport and fixture rails repos.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from . import INTERFACE_VERSION
from .config import Config
from .consent import ARM_DEFAULT_MINUTES, Arming, ProposalBook
from .lifecycle import LifecycleClient
from .pairing import redeem
from .rails import RailsClient
from .render import (
    clip,
    render_events,
    render_question,
    render_sessions,
    render_state,
)
from .runtime import RuntimeState, utc_now
from .tmuxdrive import TmuxDriver, Unarmed

HELP_TEXT = """Mission control (v{version})
Read: /state /events [n] /sessions /questions /peek <tmux-target> /status
Steer (proposal → approval tap): /flip <project> <phase> <story> <status>
  /newstory <project> <phase> <title…>  /reply <session-key> <answer…>
  /launch <claude|codex|pi> <path> [name]
Projects: /open <path>  /install <path>
  /newproject <path> <slug> <prefix> <name…>
Arming (ring 3): /arm <tmux-session> [minutes] /disarm <s> /armed
Certification stays human and the dw gate keeps final say."""

PAIRING_PROMPT = (
    "This interface is bound by pairing. Generate a token on the "
    "operator machine and send: /pair <token>"
)


class TelegramInterface:
    def __init__(
        self,
        config: Config,
        state: RuntimeState,
        transport,
        *,
        rails: RailsClient | None = None,
        driver: TmuxDriver | None = None,
        lifecycle: LifecycleClient | None = None,
        clock=None,
    ) -> None:
        self.config = config
        self.state = state
        self.transport = transport
        self.clock = clock or utc_now
        self.rails = rails or RailsClient(
            dw_cli=config.dw_cli, registry_path=config.registry_path
        )
        self.arming = Arming(state)
        self.driver = driver or TmuxDriver(self.arming)
        self.lifecycle = lifecycle or LifecycleClient(config, self.rails)
        self.proposals = ProposalBook()
        self._notified_questions: set[tuple[str, str]] = set()

    # -- plumbing -----------------------------------------------------

    def _now(self) -> datetime:
        return self.clock()

    def _say(self, chat_id: int, text: str, buttons=None) -> None:
        self.transport.send(chat_id, clip(text), buttons)

    def _active_repo(self) -> Path | None:
        if self.state.active_repo:
            return Path(self.state.active_repo)
        return self.config.default_repo

    def _propose(
        self, chat_id: int, kind: str, preview: str, payload: dict
    ) -> None:
        proposal = self.proposals.add(kind, preview, payload, self._now())
        self._say(
            chat_id,
            f"Proposal {proposal.id}:\n{preview}",
            buttons=[[
                ("Approve", f"ap:{proposal.id}"),
                ("Reject", f"rj:{proposal.id}"),
            ]],
        )

    # -- entry points ---------------------------------------------------

    def handle_update(self, update: dict) -> None:
        try:
            message = update.get("message")
            callback = update.get("callback_query")
            if isinstance(message, dict):
                chat = (message.get("chat") or {}).get("id")
                text = str(message.get("text") or "")
                if isinstance(chat, int) and text:
                    self._handle_message(chat, text)
            elif isinstance(callback, dict):
                chat = (
                    (callback.get("message") or {}).get("chat") or {}
                ).get("id")
                data = str(callback.get("data") or "")
                callback_id = str(callback.get("id") or "")
                if isinstance(chat, int):
                    self._handle_callback(chat, data, callback_id)
        except Exception as exc:  # never kill the loop; never leak internals
            chat = self.state.paired_chat
            if chat is not None:
                self._say(chat, f"internal error: {type(exc).__name__}")

    def poll_tick(self) -> None:
        """Push newly awaiting agent questions to the paired chat."""
        chat = self.state.paired_chat
        repo = self._active_repo()
        if chat is None or repo is None:
            return
        doc, _reason = self.rails.read_sessions(repo)
        if doc is None or doc.get("registry") != "ok":
            return
        for session in doc.get("sessions") or []:
            if not session.get("awaiting_response"):
                continue
            key = (
                str(session.get("key")),
                str(session.get("last_assistant_text") or "")[:200],
            )
            if key in self._notified_questions:
                continue
            self._notified_questions.add(key)
            self._say(chat, render_question(session))

    # -- messages -------------------------------------------------------

    def _handle_message(self, chat_id: int, text: str) -> None:
        parts = text.strip().split()
        if not parts:
            return
        command = parts[0].split("@")[0].lower()
        args = parts[1:]

        if self.state.paired_chat != chat_id:
            # Unpaired chats: the pairing prompt and nothing else.
            if command == "/pair" and args:
                ok, message = redeem(
                    self.state, chat_id, args[0], self._now()
                )
                self._say(chat_id, message)
                if ok:
                    self._say(chat_id, HELP_TEXT.format(version=INTERFACE_VERSION))
            elif command in {"/start", "/pair"}:
                self._say(chat_id, PAIRING_PROMPT)
            return

        handler = {
            "/start": self._cmd_help, "/help": self._cmd_help,
            "/status": self._cmd_status,
            "/state": self._cmd_state,
            "/events": self._cmd_events,
            "/sessions": self._cmd_sessions,
            "/questions": self._cmd_questions,
            "/peek": self._cmd_peek,
            "/reply": self._cmd_reply,
            "/flip": self._cmd_flip,
            "/newstory": self._cmd_newstory,
            "/arm": self._cmd_arm,
            "/disarm": self._cmd_disarm,
            "/armed": self._cmd_armed,
            "/open": self._cmd_open,
            "/install": self._cmd_install,
            "/newproject": self._cmd_newproject,
            "/launch": self._cmd_launch,
            "/pair": self._cmd_repair,
        }.get(command)
        if handler is None:
            self._say(chat_id, f"unknown command {command}; /help lists them")
            return
        handler(chat_id, args)

    def _cmd_repair(self, chat_id: int, args: list[str]) -> None:
        if not args:
            self._say(chat_id, "usage: /pair <token>")
            return
        _ok, message = redeem(self.state, chat_id, args[0], self._now())
        self._say(chat_id, message)

    def _cmd_help(self, chat_id: int, _args: list[str]) -> None:
        self._say(chat_id, HELP_TEXT.format(version=INTERFACE_VERSION))

    def _cmd_status(self, chat_id: int, _args: list[str]) -> None:
        repo = self._active_repo()
        armed = self.arming.status(self._now())
        lines = [
            f"interface v{INTERFACE_VERSION}, paired",
            f"active repo: {repo or 'none (use /open <path>)'}",
            "armed sessions: "
            + (
                ", ".join(f"{s} (until {t})" for s, t in armed)
                if armed
                else "none — everything off by default"
            ),
        ]
        self._say(chat_id, "\n".join(lines))

    def _repo_or_complain(self, chat_id: int) -> Path | None:
        repo = self._active_repo()
        if repo is None:
            self._say(chat_id, "no active rails repo; /open <path> first")
        return repo

    def _cmd_state(self, chat_id: int, _args: list[str]) -> None:
        repo = self._repo_or_complain(chat_id)
        if repo is None:
            return
        feed, reason = self.rails.read_feed(repo)
        self._say(
            chat_id,
            render_state(feed) if feed else f"state unavailable: {reason}",
        )

    def _cmd_events(self, chat_id: int, args: list[str]) -> None:
        repo = self._repo_or_complain(chat_id)
        if repo is None:
            return
        try:
            tail = max(1, min(int(args[0]), 50)) if args else 10
        except ValueError:
            tail = 10
        events, reason = self.rails.read_events(repo, tail=tail)
        self._say(
            chat_id,
            render_events(events)
            if events is not None
            else f"events unavailable: {reason}",
        )

    def _read_sessions(self, chat_id: int) -> dict | None:
        repo = self._repo_or_complain(chat_id)
        if repo is None:
            return None
        doc, reason = self.rails.read_sessions(repo)
        if doc is None:
            self._say(chat_id, f"sessions unavailable: {reason}")
        return doc

    def _cmd_sessions(self, chat_id: int, _args: list[str]) -> None:
        doc = self._read_sessions(chat_id)
        if doc is not None:
            self._say(chat_id, render_sessions(doc))

    def _cmd_questions(self, chat_id: int, _args: list[str]) -> None:
        doc = self._read_sessions(chat_id)
        if doc is None:
            return
        awaiting = [
            s
            for s in doc.get("sessions") or []
            if s.get("awaiting_response")
        ]
        if not awaiting:
            self._say(chat_id, "no agent is awaiting a response")
            return
        for session in awaiting:
            self._say(chat_id, render_question(session))

    def _cmd_peek(self, chat_id: int, args: list[str]) -> None:
        if not args:
            self._say(chat_id, "usage: /peek <tmux-target>")
            return
        ok, output = self.driver.capture_pane(args[0])
        self._say(
            chat_id,
            f"── {args[0]} (read-only) ──\n{output}"
            if ok
            else f"preview unavailable: {output}",
        )

    # -- steering: everything below is proposal → approval ---------------

    def _cmd_reply(self, chat_id: int, args: list[str]) -> None:
        if len(args) < 2:
            self._say(chat_id, "usage: /reply <session-key> <answer…>")
            return
        key, answer = args[0], " ".join(args[1:])
        doc = self._read_sessions(chat_id)
        if doc is None:
            return
        session = next(
            (
                s
                for s in doc.get("sessions") or []
                if s.get("key") == key
            ),
            None,
        )
        if session is None:
            self._say(chat_id, f"no live session {key!r}; /sessions lists them")
            return
        tmux = session.get("tmux") or {}
        if not tmux.get("session"):
            self._say(chat_id, f"session {key!r} has no tmux address to steer")
            return
        pane = tmux.get("pane")
        target = (
            str(pane)
            if str(pane or "").startswith("%")
            else f"{tmux['session']}:{tmux.get('window')}.{pane}"
            if tmux.get("window") is not None and pane is not None
            else str(tmux["session"])
        )
        stories = session.get("stories") or []
        story_part = f" (on {stories[0]['story_id']})" if stories else ""
        armed = self.arming.is_armed(str(tmux["session"]), self._now())
        arming_part = (
            ""
            if armed
            else f"\nApproving also arms {tmux['session']!r} for "
            "15 minutes (visible via /armed, revocable via /disarm)."
        )
        self._propose(
            chat_id,
            "reply",
            f"Relay into {session.get('agent')} session {key}{story_part}, "
            f"tmux {target}:\n“{answer}”{arming_part}",
            {
                "session": str(tmux["session"]),
                "target": target,
                "text": answer,
            },
        )

    def _cmd_flip(self, chat_id: int, args: list[str]) -> None:
        if len(args) != 4:
            self._say(
                chat_id, "usage: /flip <project> <phase> <story> <status>"
            )
            return
        repo = self._repo_or_complain(chat_id)
        if repo is None:
            return
        project, phase, story_id, status = args
        feed, reason = self.rails.read_feed(repo)
        if feed is None:
            self._say(chat_id, f"state unavailable: {reason}")
            return
        proj = next(
            (
                p
                for p in feed.get("projects") or []
                if p.get("slug") == project
            ),
            None,
        )
        if proj is None:
            self._say(chat_id, f"project {project!r} is not on the roadmap")
            return
        story = next(
            (
                s
                for s in proj.get("stories") or []
                if s.get("story_id") == story_id
            ),
            None,
        )
        if story is None:
            self._say(
                chat_id, f"story {story_id!r} is not on the {project} roadmap"
            )
            return
        self._propose(
            chat_id,
            "story",
            f"Flip {story_id} ({story.get('title')}) from "
            f"[{story.get('status')}] to [{status}] in {project} at {repo}.\n"
            f"The dw gate still applies — a done-flip without evidence "
            f"will be refused.",
            {
                "repo": str(repo),
                "verb": "status",
                "project": project,
                "phase": phase,
                "story": story_id,
                "status": status,
            },
        )

    def _cmd_newstory(self, chat_id: int, args: list[str]) -> None:
        if len(args) < 3:
            self._say(chat_id, "usage: /newstory <project> <phase> <title…>")
            return
        repo = self._repo_or_complain(chat_id)
        if repo is None:
            return
        project, phase, title = args[0], args[1], " ".join(args[2:])
        self._propose(
            chat_id,
            "story",
            f"Create a new story {title!r} in {project} phase {phase} "
            f"at {repo}.",
            {
                "repo": str(repo),
                "verb": "create",
                "project": project,
                "phase": phase,
                "title": title,
            },
        )

    def _cmd_arm(self, chat_id: int, args: list[str]) -> None:
        if not args:
            self._say(chat_id, "usage: /arm <tmux-session> [minutes]")
            return
        try:
            minutes = int(args[1]) if len(args) > 1 else ARM_DEFAULT_MINUTES
        except ValueError:
            minutes = ARM_DEFAULT_MINUTES
        expires = self.arming.arm(args[0], self._now(), minutes)
        self._say(
            chat_id,
            f"armed {args[0]!r} until {expires.strftime('%H:%M:%SZ')} — "
            f"/disarm {args[0]} revokes it",
        )

    def _cmd_disarm(self, chat_id: int, args: list[str]) -> None:
        if not args:
            self._say(chat_id, "usage: /disarm <tmux-session>")
            return
        was = self.arming.disarm(args[0])
        self._say(
            chat_id,
            f"disarmed {args[0]!r}" if was else f"{args[0]!r} was not armed",
        )

    def _cmd_armed(self, chat_id: int, _args: list[str]) -> None:
        armed = self.arming.status(self._now())
        self._say(
            chat_id,
            "\n".join(f"{s} armed until {t}" for s, t in armed)
            if armed
            else "nothing is armed",
        )

    def _cmd_open(self, chat_id: int, args: list[str]) -> None:
        if not args:
            self._say(chat_id, "usage: /open <path>")
            return
        path = Path(args[0]).expanduser()
        ok, reason = self.lifecycle.check_open(path)
        if not ok:
            self._say(chat_id, f"refused: {reason}")
            return
        self.state.active_repo = str(path.resolve())
        self.state.save()
        self._say(chat_id, f"active rails repo: {self.state.active_repo}")

    def _cmd_install(self, chat_id: int, args: list[str]) -> None:
        if not args:
            self._say(chat_id, "usage: /install <path>")
            return
        path = Path(args[0]).expanduser()
        steps, reason = self.lifecycle.plan_install(path)
        if steps is None:
            self._say(chat_id, f"refused: {reason}")
            return
        self._propose(
            chat_id,
            "lifecycle",
            f"Install the rails onto {path} and require doctor green.",
            {"path": str(path), "steps": steps},
        )

    def _cmd_newproject(self, chat_id: int, args: list[str]) -> None:
        if len(args) < 4:
            self._say(
                chat_id,
                "usage: /newproject <path> <slug> <prefix> <name…>",
            )
            return
        path = Path(args[0]).expanduser()
        slug, prefix, name = args[1], args[2], " ".join(args[3:])
        steps, reason = self.lifecycle.plan_create(path, slug, prefix, name)
        if steps is None:
            self._say(chat_id, f"refused: {reason}")
            return
        self._propose(
            chat_id,
            "lifecycle",
            f"Create {name!r} ({slug}, prefix {prefix}) at {path}: "
            "git init → rails install → roadmap skeleton → doctor green → "
            "first gated commit. Approval certifies the bootstrap "
            "contract as your recorded consent; the dw gate re-verifies "
            "every fact.",
            {"path": str(path), "steps": steps},
        )

    def _cmd_launch(self, chat_id: int, args: list[str]) -> None:
        if len(args) < 2:
            self._say(
                chat_id, "usage: /launch <claude|codex|pi> <path> [name]"
            )
            return
        harness, path = args[0].lower(), Path(args[1]).expanduser()
        name = args[2] if len(args) > 2 else f"dw-{harness}"
        if not path.is_dir():
            self._say(chat_id, f"refused: {path} does not exist")
            return
        self._propose(
            chat_id,
            "launch",
            f"Launch {harness} in a new tmux session {name!r} at {path}. "
            f"The session starts unarmed; /arm {name} before steering it.",
            {"harness": harness, "session": name, "cwd": str(path)},
        )

    # -- callbacks: the approval taps -------------------------------------

    def _handle_callback(
        self, chat_id: int, data: str, callback_id: str
    ) -> None:
        if self.state.paired_chat != chat_id:
            self.transport.answer_callback(callback_id, "not paired")
            return
        action, _, proposal_id = data.partition(":")
        if action == "rj":
            self.proposals.discard(proposal_id)
            self.transport.answer_callback(callback_id, "rejected")
            self._say(chat_id, f"proposal {proposal_id} rejected")
            return
        if action != "ap":
            self.transport.answer_callback(callback_id, "")
            return
        proposal = self.proposals.take(proposal_id, self._now())
        if proposal is None:
            self.transport.answer_callback(
                callback_id, "unknown or expired proposal"
            )
            self._say(
                chat_id,
                f"proposal {proposal_id} is unknown, already decided, "
                "or expired — nothing executed",
            )
            return
        self.transport.answer_callback(callback_id, "approved")
        self._execute(chat_id, proposal)

    def _execute(self, chat_id: int, proposal) -> None:
        payload = proposal.payload
        if proposal.kind == "story":
            ok, output = self.rails.run_story_verb(
                Path(payload["repo"]), payload
            )
            self._say(
                chat_id,
                f"done:\n{output}" if ok else f"the rails refused:\n{output}",
            )
        elif proposal.kind == "reply":
            # The approval tap IS the arming grant when the session is
            # not yet armed — the preview said so explicitly. The
            # driver still refuses anything that skipped this grant.
            session = payload["session"]
            now = self._now()
            armed_note = ""
            if not self.arming.is_armed(session, now):
                self.arming.arm(session, now)
                armed_note = f" (armed {session!r} for 15 min)"
            try:
                ok, output = self.driver.send_text(
                    session, payload["target"], payload["text"], now
                )
            except Unarmed as exc:
                self._say(chat_id, f"refused: {exc}")
                return
            self._say(
                chat_id,
                f"relayed{armed_note}" if ok else f"relay failed: {output}",
            )
        elif proposal.kind == "launch":
            ok, output = self.driver.launch(
                payload["harness"], payload["session"], payload["cwd"]
            )
            self._say(chat_id, output if ok else f"launch failed: {output}")
        elif proposal.kind == "lifecycle":
            ok, report = self.lifecycle.execute(
                Path(payload["path"]), payload["steps"]
            )
            summary = "\n".join(report)
            self._say(
                chat_id,
                f"on the rails:\n{summary}"
                if ok
                else f"stopped honestly:\n{summary}",
            )
        else:
            self._say(chat_id, f"unknown proposal kind {proposal.kind!r}")

    # -- the loop ---------------------------------------------------------

    def run_forever(self) -> None:
        """Long-poll until interrupted. A transient transport failure
        backs off and retries — a network blip must not take the
        interface offline; only Ctrl-C (or a kill) stops serving."""
        import sys
        import time

        from .transport import TransportError

        backoff = 2
        while True:
            try:
                for update in self.transport.get_updates():
                    self.handle_update(update)
                self.poll_tick()
                backoff = 2
            except TransportError as exc:
                print(
                    f"telegram interface: {exc}; retrying in {backoff}s",
                    file=sys.stderr,
                )
                time.sleep(backoff)
                backoff = min(backoff * 2, 60)
