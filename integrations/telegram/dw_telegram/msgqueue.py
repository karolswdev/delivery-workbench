"""The per-chat message queue (WLA-14-03, absorption map §2).

Ordered delivery under burst, with the ccgram disciplines
absorbed: adjacent plain texts merge under the size cap, stale
statuses coalesce to only-the-latest (edited in place, not
re-sent), flood-control pauses are honored, and a failure to send
one message never drops the ones behind it.

`plan_batch` is the pure decision kernel: pending messages in,
actions out, no I/O — the §2 pattern, tested without mocks. The
queue object is the thin executor around it.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field

from .entities import TELEGRAM_LIMIT, chunk, to_entities

MERGE_LIMIT = 3800  # merged texts stay under Telegram's ceiling
_SEND_RETRIES = 3


@dataclass
class OutMessage:
    chat_id: int
    text: str
    kind: str = "text"  # "text" | "status"
    buttons: list | None = None


@dataclass
class Action:
    """One planned transport act."""

    op: str  # "send" | "edit_status"
    chat_id: int
    text: str
    buttons: list | None = None


def plan_batch(pending: list[OutMessage]) -> list[Action]:
    """The kernel: merge adjacent plain texts per chat, coalesce all
    statuses per chat to the latest (as one edit_status), keep
    button-bearing messages unmerged and in order."""
    actions: list[Action] = []
    latest_status: dict[int, OutMessage] = {}
    for message in pending:
        if message.kind == "status":
            latest_status[message.chat_id] = message
            continue
        previous = actions[-1] if actions else None
        if (
            previous is not None
            and previous.op == "send"
            and previous.chat_id == message.chat_id
            and previous.buttons is None
            and message.buttons is None
            and len(previous.text) + len(message.text) + 2 <= MERGE_LIMIT
        ):
            previous.text = f"{previous.text}\n\n{message.text}"
            continue
        actions.append(
            Action("send", message.chat_id, message.text, message.buttons)
        )
    for chat_id, message in latest_status.items():
        actions.append(Action("edit_status", chat_id, message.text))
    return actions


class MessageQueue:
    """Executor: renders entities, chunks at the send layer, tries
    entities first and plain second, edits the status bubble in
    place, and pauses on flood control instead of dropping."""

    def __init__(self, transport, sleeper=time.sleep) -> None:
        self._transport = transport
        self._sleep = sleeper
        self._pending: list[OutMessage] = []
        self._status_ids: dict[int, int] = {}  # chat -> live status msg

    def enqueue(
        self,
        chat_id: int,
        text: str,
        *,
        kind: str = "text",
        buttons: list | None = None,
    ) -> None:
        self._pending.append(OutMessage(chat_id, text, kind, buttons))

    def flush(self) -> None:
        pending, self._pending = self._pending, []
        for action in plan_batch(pending):
            if action.op == "edit_status":
                self._flush_status(action)
            else:
                self._deliver(action)

    # -- internals ----------------------------------------------------

    def _flush_status(self, action: Action) -> None:
        message_id = self._status_ids.get(action.chat_id)
        if message_id is not None:
            if self._try_edit(action.chat_id, message_id, action.text):
                return
        new_id = self._deliver(action)
        if new_id is not None:
            self._status_ids[action.chat_id] = new_id

    def _try_edit(self, chat_id: int, message_id: int, text: str) -> bool:
        from .transport import TransportError

        plain, entities = to_entities(text)
        for payload_entities in (entities or None, None):
            try:
                self._transport.edit(
                    chat_id, message_id, plain, entities=payload_entities
                )
                return True
            except TransportError:
                continue
        return False

    def _deliver(self, action: Action) -> int | None:
        """Send with entity fallback, chunking, and flood patience.
        Returns the last message id when the transport reports one."""
        from .transport import TransportError

        plain, entities = to_entities(action.text)
        pieces = chunk(plain, entities, TELEGRAM_LIMIT)
        last_id: int | None = None
        for index, (piece, scoped) in enumerate(pieces):
            buttons = action.buttons if index == len(pieces) - 1 else None
            for attempt_entities in (scoped or None, None):
                delivered = False
                for attempt in range(_SEND_RETRIES):
                    try:
                        last_id = self._transport.send(
                            action.chat_id,
                            piece,
                            buttons,
                            entities=attempt_entities,
                        )
                        delivered = True
                        break
                    except TransportError as exc:
                        retry_after = getattr(exc, "retry_after", None)
                        if retry_after:
                            self._sleep(min(float(retry_after), 60.0))
                            continue
                        break  # non-flood failure: try the plain phase
                if delivered:
                    break
        return last_id
