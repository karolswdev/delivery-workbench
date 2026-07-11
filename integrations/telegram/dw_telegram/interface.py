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
from .agentevents import decide_pushes, read_new_events, render_push
from .config import Config
from .consent import ARM_DEFAULT_MINUTES, Arming, ProposalBook
from .lifecycle import LifecycleClient
from .msgqueue import MessageQueue
from .pairing import redeem
from .rails import RailsClient
from .render import (
    render_events,
    render_question,
    render_sessions,
    render_state,
)
from .runtime import RuntimeState, utc_now
from .tmuxdrive import TmuxDriver, Unarmed
from .topics import TopicRouter

HELP_TEXT = """Mission control (v{version})
Topics are projects: /bind [path] ties this topic to a repo (commands
  here then need no repo arg); /unbind releases it.
Converse: /steer <session-key> binds a session — then just type, and
  your words reach the pane (no tap per message); /unsteer stops.
  /toolbar posts Esc/Enter/arrows for the bound session.
Watch: /live [target] auto-refreshes a pane read-only — as a picture
  where rendering is available (/live text [target] keeps the text
  view); /unlive stops.
  /screen [target] sends the pane as a picture (colors and all) with
  a refresh button; falls back to text where rendering is unavailable.
Files: /send <glob|path|substring> — a clean repo file, behind seven
  locks (secrets, gitignore, state files all refuse).
Read: /state /events [n] /sessions /questions /peek <tmux-target> /status
Steer (proposal → approval tap): /flip <project> <phase> <story> <status>
  /newstory <project> <phase> <title…>  /reply <session-key> <answer…>
  /launch <claude|codex|pi> <path> [name]
Projects: /open <path>  /install <path>
  /newproject <path> <slug> <prefix> <name…>
Arming: /arm <tmux-session> [minutes] /disarm <s> /armed
Certification stays human and the dw gate keeps final say."""

PAIRING_PROMPT = (
    "This interface is bound by pairing. Generate a token on the "
    "operator machine and send: /pair <token>"
)

# The slash menu registered with Telegram (setMyCommands) so clients
# offer completion. Read surfaces and entry points only — the
# steering verbs demand arguments a menu tap cannot supply, and
# leaving them out keeps the menu honest about what one tap can do.
COMMAND_MENU = [
    ("/status", "interface, repo, owner, screenshots, live views"),
    ("/state", "the roadmap: phases, stories, next actionable"),
    ("/sessions", "which live agent is on which story"),
    ("/events", "what happened on the rails"),
    ("/questions", "agents waiting for an answer"),
    ("/bind", "tie this topic to a repo"),
    ("/steer", "bind a live session — then just type"),
    ("/screen", "the pane as a picture, refresh button included"),
    ("/live", "auto-refreshing pane view (picture where possible)"),
    ("/toolbar", "buttons for the bound session"),
    ("/send", "a repo file, behind seven locks"),
    ("/help", "the full verb list"),
]


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
        self.queue = MessageQueue(transport)
        self.topics = TopicRouter(state)
        from .toolbarcfg import load_toolbar

        self.toolbar_cfg, self.toolbar_warnings = load_toolbar(
            config.toolbar
        )
        self._notified_questions: set[tuple[str, str]] = set()
        self._reply_thread: int | None = None  # topic of the update in flight
        self._sender_id: int | None = None  # from.id of the update in flight
        # Active live views: key -> {target, message_id, thread, last_hash,
        # expires}. Refreshed by the drain loop, hash-gated.
        self._live_views: dict[str, dict] = {}
        import threading

        self._lock = threading.RLock()  # drain thread vs update loop

    # -- plumbing -----------------------------------------------------

    def _now(self) -> datetime:
        return self.clock()

    # Commands that steer, mutate, arm, or move bytes off the machine.
    # In a chat with more than one human, only the owner-of-record may
    # use them; reads stay chat-scoped (§0: consent gates entry, and
    # the entry belongs to a person).
    CONSENT_COMMANDS = frozenset({
        "/steer", "/unsteer", "/reply", "/flip", "/newstory", "/launch",
        "/install", "/newproject", "/arm", "/disarm", "/open", "/send",
        "/bind", "/unbind",
    })
    OWNER_REFUSAL = "✕ refused: consent belongs to the paired owner"

    def _not_owner(self) -> bool:
        """True when the update in flight is NOT from the
        owner-of-record. Legacy states (paired before the owner was
        recorded) keep chat-granularity behavior — /status says so."""
        owner = self.state.owner_user_id
        if owner is None:
            return False
        return self._sender_id != owner

    def _say(self, chat_id: int, text: str, buttons=None, thread_id=...) -> None:
        # Renderers keep full content; the queue's send layer merges,
        # formats via entities, and chunks (absorption map §2). By
        # default a reply lands in the topic the update came from.
        thread = self._reply_thread if thread_id is ... else thread_id
        self.queue.enqueue(chat_id, text, buttons=buttons, thread_id=thread)

    def _active_repo(self, chat_id: int | None = None) -> Path | None:
        # Topic-scoped first (§3): a bound topic means that repo, no
        # argument. Flat chat and unbound topics fall back to the
        # active/default repo — flat mode unchanged.
        if chat_id is not None:
            bound = self.topics.repo_for(chat_id, self._reply_thread)
            if bound:
                return Path(bound)
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
                thread = message.get("message_thread_id")
                sender = (message.get("from") or {}).get("id")
                self._sender_id = sender if isinstance(sender, int) else None
                self._reply_thread = thread if isinstance(thread, int) else None
                if isinstance(chat, int) and text:
                    self._handle_message(chat, text)
            elif isinstance(callback, dict):
                cb_message = callback.get("message") or {}
                chat = (cb_message.get("chat") or {}).get("id")
                message_id = cb_message.get("message_id")
                thread = cb_message.get("message_thread_id")
                sender = (callback.get("from") or {}).get("id")
                self._sender_id = sender if isinstance(sender, int) else None
                self._reply_thread = thread if isinstance(thread, int) else None
                data = str(callback.get("data") or "")
                callback_id = str(callback.get("id") or "")
                if isinstance(chat, int):
                    self._handle_callback(
                        chat,
                        data,
                        callback_id,
                        message_id if isinstance(message_id, int) else None,
                    )
        except Exception as exc:  # never kill the loop; never leak internals
            chat = self.state.paired_chat
            if chat is not None:
                self._say(chat, f"internal error: {type(exc).__name__}")
        finally:
            self._reply_thread = None
            self._sender_id = None
            self.queue.flush()

    def drain_agent_events(self) -> int:
        """Drain the dw hook stream and push instantly (§1 of the
        absorption map): a Notification event reaches the paired
        chat in the same drain it was appended, then poll_tick runs
        immediately to enrich with the correlated question. The
        byte offset persists in runtime state — a restart never
        re-pushes. Returns the number of pushes made."""
        with self._lock:
            chat = self.state.paired_chat
            if chat is None:
                return 0
            path = self.config.resolved_agent_events_path()
            events, new_offset = read_new_events(
                path, self.state.events_offset
            )
            if new_offset != self.state.events_offset:
                self.state.events_offset = new_offset
                self.state.save()
            if not events:
                return 0
            pushes = decide_pushes(events)
            for event in pushes:
                self._say(chat, render_push(event))
            if pushes:
                self.poll_tick()  # enrich instantly from the correlation
            self.queue.flush()
            return len(pushes)

    def refresh_live_views(self) -> None:
        """Re-capture each active live view and edit its message in
        place only when the pane content changed (§4: content-hash
        gating — no change, no edit, no API call). Read-only: never a
        keystroke. Expired views are dropped."""
        from . import screenshot
        from .tmuxdrive import content_hash

        now = self._now()
        for key in list(self._live_views):
            view = self._live_views[key]
            expires = view.get("expires")
            if expires is not None and now.timestamp() > expires:
                del self._live_views[key]
                continue
            image_mode = view.get("mode") == "image"
            ok, output = self.driver.capture_pane(
                view["target"], ansi=image_mode
            )
            if not ok:
                continue
            digest = content_hash(output)
            if digest == view.get("last_hash"):
                continue  # the gate: no change, no render, no API call
            view["last_hash"] = digest
            from .transport import TransportError

            try:
                if image_mode:
                    png = screenshot.text_to_image(output, live=True)
                    if png is None:
                        continue
                    self.transport.edit_message_media(
                        self.state.paired_chat,
                        view["message_id"],
                        png,
                        caption=f"{view['target']} — live, read-only",
                    )
                else:
                    body = (
                        f"── {view['target']} (live, read-only) ──\n{output}"
                    )
                    self.transport.edit(
                        self.state.paired_chat, view["message_id"], body
                    )
            except TransportError:
                pass

    def poll_tick(self) -> None:
        """Push newly awaiting agent questions — routed home to the
        topic bound to the session's repo when there is one (§3),
        otherwise to the flat chat / active topic."""
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
            session_repo = str(session.get("repo_root") or "")
            home = (
                self.topics.topic_for_repo(chat, session_repo)
                if session_repo
                else None
            )
            self._say(
                chat,
                render_question(session),
                buttons=self._question_nav_buttons(chat, home, session),
                thread_id=home,
            )
        self.queue.flush()

    NAV_KEYBOARD = [
        [("↑", "qn:Up"), ("↓", "qn:Down"), ("📸", "qn:peek")],
        [("⏎ Enter", "qn:Enter"), ("⎋ Esc", "qn:Escape")],
    ]

    def _question_nav_buttons(
        self, chat: int, home: int | None, session: dict
    ) -> list | None:
        """The nav keyboard rides a question card only when its
        session is BOUND in the home topic AND ARMED — the two
        grants that already exist. Anything less keeps today's
        card: the proposal path with its one-tap arming, because a
        nav tap never arms."""
        binding = self.topics.bound_session(chat, home, self._now())
        if binding is None:
            return None
        if binding.get("session_key") != session.get("key"):
            return None
        if not self.arming.is_armed(
            str(binding.get("tmux_session") or ""), self._now()
        ):
            return None
        return self.NAV_KEYBOARD

    # -- messages -------------------------------------------------------

    def _handle_message(self, chat_id: int, text: str) -> None:
        stripped = text.strip()
        parts = stripped.split()
        if not parts:
            return
        command = parts[0].split("@")[0].lower()
        args = parts[1:]

        if self.state.paired_chat != chat_id:
            # Unpaired chats: the pairing prompt and nothing else.
            if command == "/pair" and args:
                ok, message = redeem(
                    self.state, chat_id, args[0], self._now(),
                    user_id=self._sender_id,
                )
                self._say(chat_id, message)
                if ok:
                    self._say(chat_id, HELP_TEXT.format(version=INTERFACE_VERSION))
            elif command in {"/start", "/pair"}:
                self._say(chat_id, PAIRING_PROMPT)
            return

        # Flowing conversation (§0): plain text — not a command — in a
        # topic with a live session binding relays straight to the
        # pane. The binding IS the arming; no per-message tap. Pane
        # ownership is still verified beneath, per keystroke.
        if not command.startswith("/"):
            if self._relay_if_bound(chat_id, stripped):
                return
            self._say(
                chat_id,
                "no session bound to this topic — /steer <session-key> "
                "to converse, or start a command with /.",
            )
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
            "/bind": self._cmd_bind,
            "/unbind": self._cmd_unbind,
            "/steer": self._cmd_steer,
            "/unsteer": self._cmd_unsteer,
            "/live": self._cmd_live,
            "/unlive": self._cmd_unlive,
            "/screen": self._cmd_screen,
            "/toolbar": self._cmd_toolbar,
            "/send": self._cmd_send,
            "/install": self._cmd_install,
            "/newproject": self._cmd_newproject,
            "/launch": self._cmd_launch,
            "/pair": self._cmd_repair,
        }.get(command)
        if handler is None:
            self._say(chat_id, f"unknown command {command}; /help lists them")
            return
        if command in self.CONSENT_COMMANDS and self._not_owner():
            self._say(chat_id, self.OWNER_REFUSAL)
            return
        handler(chat_id, args)

    def _relay_if_bound(self, chat_id: int, text: str) -> bool:
        """Relay free text to a topic's bound session, or False if
        this topic has no live binding."""
        binding = self.topics.bound_session(
            chat_id, self._reply_thread, self._now()
        )
        if binding is None:
            return False
        if self._not_owner():
            # The flow stays flowing for the OWNER; a second human
            # typing into a steered topic is exactly who this stops.
            self._say(chat_id, self.OWNER_REFUSAL)
            return True
        session = binding["tmux_session"]
        now = self._now()
        if not self.arming.is_armed(session, now):
            # The topic binding is the grant; keep the driver's own
            # arming store in step so its ownership check passes.
            self.arming.arm(session, now)
        try:
            ok, output = self.driver.send_text(
                session, binding["target"], text, now,
                harness=binding.get("harness"),
            )
        except Unarmed as exc:
            self._say(chat_id, f"✕ {exc}")
            return True
        if not ok:
            self._say(chat_id, f"✕ relay failed: {output}")
        return True

    def _cmd_repair(self, chat_id: int, args: list[str]) -> None:
        if not args:
            self._say(chat_id, "usage: /pair <token>")
            return
        _ok, message = redeem(self.state, chat_id, args[0], self._now())
        self._say(chat_id, message)

    def _cmd_help(self, chat_id: int, _args: list[str]) -> None:
        self._say(chat_id, HELP_TEXT.format(version=INTERFACE_VERSION))

    def _cmd_status(self, chat_id: int, _args: list[str]) -> None:
        from . import screenshot

        repo = self._active_repo(chat_id)
        armed = self.arming.status(self._now())
        lines = [
            f"interface v{INTERFACE_VERSION}, paired",
            f"active repo: {repo or 'none (use /open <path>)'}",
            "owner: recorded"
            if self.state.owner_user_id is not None
            else (
                "owner: NOT recorded (legacy pairing — every member "
                "of this chat can steer; /pair again to bind consent "
                "to a person)"
            ),
            "screenshots: png"
            if screenshot.AVAILABLE
            else f"screenshots: text only ({screenshot.unavailable_reason()})",
            "live views: "
            + (
                ", ".join(
                    f"{v['target']} ({v.get('mode', 'text')})"
                    for v in self._live_views.values()
                )
                or "none"
            ),
        ]
        if self.toolbar_warnings:
            lines.append(
                "toolbar config warnings:\n  "
                + "\n  ".join(self.toolbar_warnings)
            )
        lines += [
            "armed sessions: "
            + (
                ", ".join(f"{s} (until {t})" for s, t in armed)
                if armed
                else "none — everything off by default"
            ),
        ]
        self._say(chat_id, "\n".join(lines))

    def _repo_or_complain(self, chat_id: int) -> Path | None:
        repo = self._active_repo(chat_id)
        if repo is None:
            self._say(
                chat_id,
                "no rails repo here; /bind in a topic or /open <path>",
            )
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
            self._say(
                chat_id,
                f"{key} is not running inside tmux, so there is no pane "
                "to type into — it can only be answered at the desk. "
                "Steerable sessions show a tmux address in /sessions; "
                "/launch <claude|codex|pi> <path> starts one.",
            )
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
        if session.get("stale"):
            arming_part += (
                "\n⚠ This session's registry entry is stale (no update "
                "in 30+ min) — it may have ended; the driver will "
                "verify the pane before typing."
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

    def _cmd_bind(self, chat_id: int, args: list[str]) -> None:
        """Bind this topic to a rails repo (§3). No path: list the
        allow-listed rails repos to pick from."""
        if not args:
            options = self._biddable_repos()
            if not options:
                self._say(
                    chat_id,
                    "no rails repos under the allow-listed workspace "
                    "roots; check workspace_roots in the config.",
                )
                return
            self._say(
                chat_id,
                "bind this topic to a repo:\n"
                + "\n".join(f"  /bind {p}" for p in options),
            )
            return
        path = Path(args[0]).expanduser()
        ok, reason = self.lifecycle.check_open(path)
        if not ok:
            self._say(chat_id, f"refused: {reason}")
            return
        self.topics.bind_repo(
            chat_id, self._reply_thread, str(path.resolve())
        )
        where = "this topic" if self._reply_thread is not None else "this chat"
        self._say(
            chat_id,
            f"◆ {where} is now {path.name} ({path.resolve()}). "
            "Commands here scope to it; /steer a session to converse.",
        )

    def _cmd_unbind(self, chat_id: int, _args: list[str]) -> None:
        was = self.topics.unbind_repo(chat_id, self._reply_thread)
        self._say(
            chat_id,
            "unbound; this topic is no longer tied to a repo"
            if was
            else "this topic was not bound",
        )

    def _biddable_repos(self) -> list[str]:
        found: list[str] = []
        for root in self.config.workspace_roots:
            try:
                for child in sorted(root.iterdir()):
                    if (child / "pm" / "roadmap").is_dir() and (
                        child / ".githooks" / "dw"
                    ).is_file():
                        found.append(str(child))
            except OSError:
                continue
        return found

    def _cmd_steer(self, chat_id: int, args: list[str]) -> None:
        """Bind a session into this topic — the arming (§0). After
        this, plain text flows to the pane, no per-message tap."""
        if not args:
            self._say(chat_id, "usage: /steer <session-key>")
            return
        key = args[0]
        repo = self._repo_or_complain(chat_id)
        if repo is None:
            return
        doc, reason = self.rails.read_sessions(repo)
        if doc is None:
            self._say(chat_id, f"sessions unavailable: {reason}")
            return
        session = next(
            (s for s in doc.get("sessions") or [] if s.get("key") == key),
            None,
        )
        if session is None:
            self._say(chat_id, f"no live session {key!r}; /sessions lists them")
            return
        tmux = session.get("tmux") or {}
        if not tmux.get("session"):
            self._say(
                chat_id,
                f"{key} is not inside tmux — it can't be steered "
                "(no pane to type into).",
            )
            return
        target = self._pane_target(tmux)
        # Capability-aware recovery (§4): if the pane is gone, offer
        # what the harness supports rather than binding a corpse.
        owner_ok, _ = self.driver._verify_owner(str(tmux["session"]), target)
        if not owner_ok:
            from .tmuxdrive import HARNESS

            descriptor = HARNESS.get(str(session.get("agent") or ""))
            verbs = descriptor.recovery_verbs if descriptor else ("fresh",)
            self._say(
                chat_id,
                f"session {key} looks gone (its pane is stale). "
                f"Recovery options for {session.get('agent')}: "
                f"{', '.join(verbs)} — use /launch to start one.",
            )
            return
        self.topics.bind_session(
            chat_id, self._reply_thread, key, target,
            str(tmux["session"]), self._now(),
            harness=str(session.get("agent") or ""),
        )
        self.arming.arm(str(tmux["session"]), self._now())
        self._say(
            chat_id,
            f"⚡ steering {session.get('agent')} session {key} — "
            "type to converse; the binding refreshes on activity and "
            "expires when idle. /unsteer stops it.",
        )

    def _cmd_unsteer(self, chat_id: int, _args: list[str]) -> None:
        binding = self.topics.bound_session(
            chat_id, self._reply_thread, self._now()
        )
        was = self.topics.unbind_session(chat_id, self._reply_thread)
        if was and binding:
            self.arming.disarm(binding.get("tmux_session", ""))
        self._say(
            chat_id,
            "stopped steering this topic" if was else "no session was bound here",
        )

    # -- live view and toolbar (§4) -----------------------------------

    LIVE_TTL_SECONDS = 300  # a live view auto-expires after 5 min

    def _cmd_live(self, chat_id: int, args: list[str]) -> None:
        """Auto-refreshing read-only view of a pane. Prefers the
        bound session's pane; a bare target works too. Shows a
        PICTURE where the renderer is available; `/live text
        [target]` keeps the text view on purpose."""
        from . import screenshot

        force_text = bool(args) and args[0].lower() == "text"
        rest = args[1:] if force_text else args
        target = rest[0] if rest else None
        if target is None:
            binding = self.topics.bound_session(
                chat_id, self._reply_thread, self._now()
            )
            if binding is None:
                self._say(chat_id, "usage: /live [text] <tmux-target> (or /steer first)")
                return
            target = binding["target"]
        image_mode = screenshot.AVAILABLE and not force_text
        ok, output = self.driver.capture_pane(target, ansi=image_mode)
        if not ok:
            self._say(chat_id, f"live view unavailable: {output}")
            return
        from .tmuxdrive import content_hash

        message_id = None
        if image_mode:
            png = screenshot.text_to_image(output, live=True)
            if png is None:
                image_mode = False  # renderer said no: text, honestly
            else:
                from .transport import TransportError

                try:
                    message_id = self.transport.send_photo(
                        chat_id,
                        png,
                        caption=f"{target} — live, read-only",
                        thread_id=self._reply_thread,
                    )
                except TransportError as exc:
                    self._say(chat_id, f"live view unavailable: {exc}")
                    return
        if not image_mode:
            body = f"── {target} (live, read-only) ──\n{output}"
            message_id = self.transport.send(
                chat_id, body, thread_id=self._reply_thread
            )
        if message_id is None:
            return
        self._live_views[f"{chat_id}:{target}"] = {
            "target": target,
            "message_id": message_id,
            "thread": self._reply_thread,
            "mode": "image" if image_mode else "text",
            "last_hash": content_hash(output),
            "expires": self._now().timestamp() + self.LIVE_TTL_SECONDS,
        }

    def _screen_target(self, chat_id: int, args: list[str]) -> str | None:
        """Resolve /screen's target exactly as /live does: explicit
        argument, else the topic's bound session pane."""
        if args:
            return args[0]
        binding = self.topics.bound_session(
            chat_id, self._reply_thread, self._now()
        )
        return binding["target"] if binding else None

    def _cmd_screen(self, chat_id: int, args: list[str]) -> None:
        """One shot of the pane as a picture, with a refresh button.
        Read-only: capture → render → sendPhoto. Where Pillow is
        absent the text capture goes out instead, reason stated."""
        target = self._screen_target(chat_id, args)
        if target is None:
            self._say(chat_id, "usage: /screen <tmux-target> (or /steer first)")
            return
        self._send_screen(chat_id, target)

    def _send_screen(
        self, chat_id: int, target: str, message_id: int | None = None
    ) -> bool:
        """Capture and deliver one screenshot; edits the existing
        photo message in place when `message_id` is given (the
        refresh button's path). Returns True when a picture (or its
        stated fallback) went out."""
        from . import screenshot
        from .transport import TransportError

        ok, output = self.driver.capture_pane(
            target, ansi=screenshot.AVAILABLE
        )
        if not ok:
            self._say(chat_id, f"screenshot unavailable: {output}")
            return False
        png = screenshot.text_to_image(output)
        if png is None:
            reason = screenshot.unavailable_reason() or "renderer unavailable"
            self._say(
                chat_id,
                f"rendering unavailable ({reason}) — text capture "
                f"instead:\n── {target} (read-only) ──\n{output}",
            )
            return True
        caption = f"{target} — {self._now().strftime('%H:%M:%S')} UTC"
        buttons = [[("🔄 refresh", f"ss:{target}")]]
        try:
            if message_id is not None:
                self.transport.edit_message_media(
                    chat_id, message_id, png, caption=caption,
                    buttons=buttons,
                )
            else:
                self.transport.send_photo(
                    chat_id, png, caption=caption, buttons=buttons,
                    thread_id=self._reply_thread,
                )
        except TransportError as exc:
            self._say(chat_id, f"screenshot send failed: {exc}")
            return False
        return True

    def _cmd_unlive(self, chat_id: int, args: list[str]) -> None:
        removed = [
            key for key in list(self._live_views)
            if key.startswith(f"{chat_id}:")
            and (not args or self._live_views[key]["target"] == args[0])
        ]
        for key in removed:
            del self._live_views[key]
        self._say(
            chat_id,
            f"stopped {len(removed)} live view(s)"
            if removed
            else "no live views here",
        )

    def _cmd_toolbar(self, chat_id: int, _args: list[str]) -> None:
        """Post the steering toolbar for the topic's bound session.
        Buttons fire directly while the binding is live — the binding
        is the grant, no tap-per-tap (§4). The grid is data: built-in
        per-harness layouts, reshaped by the operator's config
        (toolbarcfg; the builtin table is closed)."""
        binding = self.topics.bound_session(
            chat_id, self._reply_thread, self._now()
        )
        if binding is None:
            self._say(
                chat_id,
                "no session bound here; /steer <session-key> first",
            )
            return
        harness = str(binding.get("session_key") or "").split(":")[0]
        note = (
            f" ({len(self.toolbar_warnings)} config warning(s) — /status)"
            if self.toolbar_warnings
            else ""
        )
        self._say(
            chat_id,
            f"toolbar for {binding['session_key']} (buttons act while "
            f"steering):{note}",
            buttons=self.toolbar_cfg.buttons_for(harness),
        )

    def _handle_toolbar_action(
        self, chat_id: int, action_id: str, callback_id: str,
        message_id: int | None,
    ) -> None:
        """A tb: tap — text/builtin actions resolved through the
        CURRENT config at tap time. Keys ride kb:, one door."""
        action = self.toolbar_cfg.action(action_id)
        if action is None:
            self.transport.answer_callback(
                callback_id, f"no such toolbar action {action_id!r}"
            )
            return
        binding = self.topics.bound_session(
            chat_id, self._reply_thread, self._now()
        )
        if binding is None:
            self.transport.answer_callback(
                callback_id, "no live binding — /steer first"
            )
            return
        if action.kind == "builtin":
            if action.payload == "screen":
                ok = self._send_screen(chat_id, binding["target"])
                self.transport.answer_callback(
                    callback_id, "screenshot" if ok else "capture failed"
                )
            elif action.payload == "live":
                self._cmd_live(chat_id, [])
                self.transport.answer_callback(callback_id, "live view up")
            else:  # dismiss — the closed table has exactly three
                self._card_update(chat_id, message_id, "toolbar dismissed")
                self.transport.answer_callback(callback_id, "dismissed")
            return
        # text action: the binding is the grant, same as the relay
        session = binding["tmux_session"]
        if not self.arming.is_armed(session, self._now()):
            self.arming.arm(session, self._now())
        try:
            ok, output = self.driver.send_text(
                session, binding["target"], action.payload, self._now()
            )
        except Unarmed as exc:
            self.transport.answer_callback(callback_id, str(exc)[:180])
            return
        self.transport.answer_callback(
            callback_id,
            action.payload if ok else f"failed: {output}"[:180],
        )

    def _handle_question_nav(
        self, chat_id: int, key: str, callback_id: str,
        message_id: int | None,
    ) -> None:
        """A qn: tap drives the TUI prompt the question came from.
        Deliberately dumb: it never claims to know what the menu
        says — 📸 shows the truth, arrows move, Enter commits. And
        deliberately strict: a nav tap NEVER arms; an unarmed or
        unbound session refuses (the proposal path with its one-tap
        arming is how consent enters)."""
        binding = self.topics.bound_session(
            chat_id, self._reply_thread, self._now()
        )
        if binding is None:
            self.transport.answer_callback(
                callback_id, "no live binding — /steer first"
            )
            return
        if key == "peek":
            ok = self._send_screen(chat_id, binding["target"])
            self.transport.answer_callback(
                callback_id, "captured" if ok else "capture failed"
            )
            return
        if key not in {"Up", "Down", "Enter", "Escape"}:
            self.transport.answer_callback(callback_id, "")
            return
        session = binding["tmux_session"]
        try:
            ok, output = self.driver.send_key(
                session, binding["target"], key, self._now()
            )
        except Unarmed:
            self.transport.answer_callback(
                callback_id,
                "session unarmed — a nav tap never arms; approve a "
                "reply or /arm first",
            )
            return
        if ok and key in {"Enter", "Escape"}:
            self._card_update(
                chat_id,
                message_id,
                f"{key} sent to {binding['session_key']} — /questions "
                "to re-check what it is waiting on now",
            )
        self.transport.answer_callback(
            callback_id, key if ok else f"failed: {output}"[:180]
        )

    def register_command_menu(self) -> bool:
        """Register the slash menu with Telegram (setMyCommands) so
        the client offers completion. Config `command_menu: false`
        opts out. Returns True when registered."""
        if not self.config.command_menu:
            return False
        from .transport import TransportError

        try:
            self.transport.set_my_commands(COMMAND_MENU)
        except TransportError:
            return False  # cosmetic surface: never block serving
        return True

    # -- the file leg: /send behind seven locks (§5) ------------------

    def _cmd_send(self, chat_id: int, args: list[str]) -> None:
        """Send a repo file to chat, behind seven locks. A clean exact
        match sends straight through; an ambiguous match lists the
        candidates; a hazard is refused by the lock that caught it."""
        if not args:
            self._say(chat_id, "usage: /send <glob|path|substring>")
            return
        repo = self._repo_or_complain(chat_id)
        if repo is None:
            return
        from .sendfiles import resolve_matches, validate_sendable
        from .transport import TransportError

        matches = resolve_matches(args[0], repo)
        if not matches:
            self._say(chat_id, f"no file matches {args[0]!r} in {repo.name}")
            return
        if len(matches) > 1:
            listing = "\n".join(
                f"  /send {p.relative_to(repo.resolve())}" for p in matches[:20]
            )
            self._say(
                chat_id,
                f"{len(matches)} files match — pick one:\n{listing}",
            )
            return
        path = matches[0]
        refusal = validate_sendable(path, repo)
        if refusal is not None:
            self._say(chat_id, f"✕ refused: {refusal}")
            return
        rel = path.relative_to(repo.resolve())
        size_kb = max(1, path.stat().st_size // 1024)
        caption = f"{rel} — {repo.name} — {size_kb} KB"
        try:
            self.transport.send_document(
                chat_id, str(path), caption, thread_id=self._reply_thread
            )
        except TransportError as exc:
            self._say(chat_id, f"✕ send failed: {exc}")
            return
        self._say(chat_id, f"✓ sent {rel}")

    def _pane_target(self, tmux: dict) -> str:
        pane = tmux.get("pane")
        if str(pane or "").startswith("%"):
            return str(pane)
        if tmux.get("window") is not None and pane is not None:
            return f"{tmux['session']}:{tmux.get('window')}.{pane}"
        return str(tmux["session"])

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

    def _handle_toolbar_key(
        self, chat_id: int, key: str, callback_id: str
    ) -> None:
        """A toolbar press: fire one key into the topic's bound
        session (the binding is the grant), or refresh its live view.
        Ownership is verified in the driver, per press."""
        binding = self.topics.bound_session(
            chat_id, self._reply_thread, self._now()
        )
        if binding is None:
            self.transport.answer_callback(
                callback_id, "no live binding — /steer first"
            )
            return
        if key == "refresh":
            self.refresh_live_views()
            self.transport.answer_callback(callback_id, "refreshed")
            return
        session = binding["tmux_session"]
        if not self.arming.is_armed(session, self._now()):
            self.arming.arm(session, self._now())
        try:
            ok, output = self.driver.send_key(
                session, binding["target"], key, self._now()
            )
        except Unarmed as exc:
            self.transport.answer_callback(callback_id, str(exc)[:180])
            return
        self.transport.answer_callback(
            callback_id, key if ok else f"failed: {output}"[:180]
        )

    def _card_update(
        self, chat_id: int, message_id: int | None, text: str
    ) -> None:
        """Edit the proposal card in place through its lifecycle —
        one card in the history, not a trail (absorption map §2).
        Falls back to a plain send when the edit is impossible."""
        from .transport import TransportError

        if message_id is not None:
            try:
                self.transport.edit(chat_id, message_id, text)
                return
            except TransportError:
                pass
        self._say(chat_id, text)

    def _handle_callback(
        self,
        chat_id: int,
        data: str,
        callback_id: str,
        message_id: int | None = None,
    ) -> None:
        if self.state.paired_chat != chat_id:
            self.transport.answer_callback(callback_id, "not paired")
            return
        if self._not_owner():
            # Every tap is consent-bearing: approvals execute,
            # toolbar keys reach a terminal, refreshes cost API
            # calls. One identity holds them all.
            self.transport.answer_callback(
                callback_id, "consent belongs to the paired owner"
            )
            return
        action, _, rest = data.partition(":")
        if action == "kb":
            self._handle_toolbar_key(chat_id, rest, callback_id)
            return
        if action == "tb":
            self._handle_toolbar_action(chat_id, rest, callback_id, message_id)
            return
        if action == "qn":
            self._handle_question_nav(chat_id, rest, callback_id, message_id)
            return
        if action == "ss":
            # Screenshot refresh: re-capture and edit the same photo
            # message in place — read-only, no keystroke involved.
            refreshed = self._send_screen(chat_id, rest, message_id)
            self.transport.answer_callback(
                callback_id, "refreshed" if refreshed else "capture failed"
            )
            return
        proposal_id = rest
        if action == "rj":
            self.proposals.discard(proposal_id)
            self.transport.answer_callback(callback_id, "rejected")
            self._card_update(
                chat_id, message_id, f"✕ proposal {proposal_id} rejected"
            )
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
        outcome = self._execute(chat_id, proposal)
        self._card_update(
            chat_id, message_id, f"{proposal.preview}\n\n{outcome}"
        )

    def _execute(self, chat_id: int, proposal) -> str:
        """Execute an approved proposal; the outcome text lands on
        the card via edit-in-place (never a second message)."""
        payload = proposal.payload
        if proposal.kind == "story":
            ok, output = self.rails.run_story_verb(
                Path(payload["repo"]), payload
            )
            return (
                f"✓ done:\n{output}"
                if ok
                else f"✕ the rails refused:\n{output}"
            )
        if proposal.kind == "reply":
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
                return f"✕ refused: {exc}"
            return (
                f"✓ relayed{armed_note}"
                if ok
                else f"✕ relay failed: {output}"
            )
        if proposal.kind == "launch":
            ok, output = self.driver.launch(
                payload["harness"], payload["session"], payload["cwd"]
            )
            return f"✓ {output}" if ok else f"✕ launch failed: {output}"
        if proposal.kind == "lifecycle":
            ok, report = self.lifecycle.execute(
                Path(payload["path"]), payload["steps"]
            )
            summary = "\n".join(report)
            return (
                f"✓ on the rails:\n{summary}"
                if ok
                else f"✕ stopped honestly:\n{summary}"
            )
        return f"unknown proposal kind {proposal.kind!r}"

    # -- the loop ---------------------------------------------------------

    def run_forever(self) -> None:
        """Long-poll until interrupted. A daemon thread drains the
        dw hook stream every second so pushes are instant even while
        the long poll blocks; a transient transport failure backs
        off and retries — only Ctrl-C (or a kill) stops serving."""
        import sys
        import threading
        import time

        from .transport import TransportError

        def _drain_loop() -> None:
            while True:
                time.sleep(1)
                try:
                    with self._lock:
                        self.drain_agent_events()
                        if self._live_views:
                            self.refresh_live_views()
                except Exception:
                    pass  # the drain must never kill the interface

        threading.Thread(target=_drain_loop, daemon=True).start()

        backoff = 2
        while True:
            try:
                for update in self.transport.get_updates():
                    with self._lock:
                        self.handle_update(update)
                with self._lock:
                    self.poll_tick()
                backoff = 2
            except TransportError as exc:
                print(
                    f"telegram interface: {exc}; retrying in {backoff}s",
                    file=sys.stderr,
                )
                time.sleep(backoff)
                backoff = min(backoff * 2, 60)
