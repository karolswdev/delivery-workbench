"""Topics are projects (WLA-14-04, absorption map §0+§3).

ccgram's spatial insight, transmuted: their unit of work is a tmux
window, ours is a rails repo. One forum topic binds to one repo;
inside it, commands scope to that repo with no argument, and a
session bound into the topic converses freely (the §0 stance:
consent gates entry, not every utterance).

`TopicRouter` is the bidirectional map, backed by runtime state:
`(chat, thread) → repo` for scoping, `(chat, thread) → session`
for the live steering binding. The binding is the arming — it
carries an activity-refreshed expiry, is visible, and is revoked
in one act. Pane-ownership verification still runs beneath every
keystroke; this only changes WHERE the arming grant comes from.

The router itself is thin and deterministic; the interface owns
the taps and the relay.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path

from .runtime import RuntimeState, iso, parse_iso


def _same_repo(a: str, b: str) -> bool:
    """Compare repo paths tolerant of symlinks (macOS /var vs
    /private/var) — the registry's repo_root and a bound path may
    spell the same directory differently."""
    if a == b:
        return True
    try:
        return Path(a).resolve() == Path(b).resolve()
    except OSError:
        return False

# The session binding refreshes on activity rather than counting
# down from a grant — a live conversation should not expire mid-turn.
BINDING_IDLE_MINUTES = 30


def topic_key(chat_id: int, thread_id: int | None) -> str:
    """The stable key for a (chat, topic) pair. thread_id None is the
    flat chat — a single implicit topic, so flat mode is just the
    degenerate forum with one room."""
    return f"{chat_id}:{thread_id if thread_id is not None else '-'}"


class TopicRouter:
    def __init__(self, state: RuntimeState) -> None:
        self._state = state

    # -- repo binding (scoping) --------------------------------------

    def bind_repo(self, chat_id: int, thread_id: int | None, repo: str) -> None:
        self._state.topic_repos[topic_key(chat_id, thread_id)] = repo
        self._state.save()

    def repo_for(self, chat_id: int, thread_id: int | None) -> str | None:
        return self._state.topic_repos.get(topic_key(chat_id, thread_id))

    def unbind_repo(self, chat_id: int, thread_id: int | None) -> bool:
        key = topic_key(chat_id, thread_id)
        present = key in self._state.topic_repos
        if present:
            del self._state.topic_repos[key]
            self.unbind_session(chat_id, thread_id)  # session can't outlive repo
            self._state.save()
        return present

    def topic_for_repo(self, chat_id: int, repo: str) -> int | None:
        """Reverse lookup: which topic in this chat holds this repo?
        A pushed question routes home to it. None → not bound here."""
        for key, bound in self._state.topic_repos.items():
            if not _same_repo(bound, repo):
                continue
            prefix = f"{chat_id}:"
            if key.startswith(prefix):
                tail = key[len(prefix):]
                return None if tail == "-" else int(tail)
        return None

    # -- session binding (flowing conversation = the arming) ---------

    def bind_session(
        self,
        chat_id: int,
        thread_id: int | None,
        session_key: str,
        target: str,
        tmux_session: str,
        now: datetime,
        harness: str | None = None,
    ) -> None:
        self._state.topic_sessions[topic_key(chat_id, thread_id)] = {
            "session_key": session_key,
            "target": target,
            "tmux_session": tmux_session,
            "harness": harness,
            "expires_at": iso(now + timedelta(minutes=BINDING_IDLE_MINUTES)),
        }
        self._state.save()

    def bound_session(
        self, chat_id: int, thread_id: int | None, now: datetime
    ) -> dict | None:
        """The live session binding, or None if absent/expired. A live
        read refreshes the idle clock — activity keeps it open."""
        key = topic_key(chat_id, thread_id)
        binding = self._state.topic_sessions.get(key)
        if not binding:
            return None
        expires = parse_iso(binding.get("expires_at"))
        if expires is None or now > expires:
            del self._state.topic_sessions[key]
            self._state.save()
            return None
        binding["expires_at"] = iso(now + timedelta(minutes=BINDING_IDLE_MINUTES))
        self._state.save()
        return binding

    def unbind_session(self, chat_id: int, thread_id: int | None) -> bool:
        key = topic_key(chat_id, thread_id)
        present = key in self._state.topic_sessions
        if present:
            del self._state.topic_sessions[key]
            self._state.save()
        return present
