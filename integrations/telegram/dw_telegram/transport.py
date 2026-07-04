"""Transports: the live Bot API and the scripted test double.

The interface core never touches the network itself — it speaks to
a transport with three verbs (poll updates, send a message with
optional approval buttons, answer a callback tap). CI runs entirely
on ``ScriptedTransport``; the HTTP transport is exercised on the
operator's machine, where the token lives. Errors from urllib embed
the request URL, which embeds the token — every exception path here
redacts before re-raising, so the token cannot leak into logs.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from pathlib import Path

API_HOST = "https://api.telegram.org"
POLL_TIMEOUT_SECONDS = 50


class TransportError(RuntimeError):
    """A transport failure with any token content redacted.
    `retry_after` carries Telegram's flood-control pause when the
    API named one, so the send layer can wait instead of dropping."""

    def __init__(self, message: str, retry_after: float | None = None):
        super().__init__(message)
        self.retry_after = retry_after


class HttpTransport:
    def __init__(self, token: str) -> None:
        self._token = token
        self._offset: int | None = None

    def _call(self, method: str, payload: dict) -> dict:
        url = f"{API_HOST}/bot{self._token}/{method}"
        request = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
        )
        try:
            with urllib.request.urlopen(
                request, timeout=POLL_TIMEOUT_SECONDS + 10
            ) as response:
                doc = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            try:
                body = exc.read().decode("utf-8", "replace")[:300]
            except Exception:
                body = ""
            retry_after = None
            if exc.code == 429:
                try:
                    retry_after = float(
                        json.loads(body)["parameters"]["retry_after"]
                    )
                except Exception:
                    retry_after = 5.0
            raise TransportError(
                f"telegram {method} failed: HTTP {exc.code} {body}",
                retry_after=retry_after,
            ) from None
        except Exception as exc:
            raise TransportError(
                f"telegram {method} failed: {type(exc).__name__}"
            ) from None
        if not doc.get("ok"):
            raise TransportError(
                f"telegram {method} refused: {str(doc.get('description'))[:200]}"
            )
        return doc.get("result")

    def get_me(self) -> dict:
        """Identity check at startup — proves the token works and
        names the bot. The username is public; the token never
        appears in output or errors."""
        return self._call("getMe", {}) or {}

    def get_updates(self) -> list[dict]:
        payload: dict = {
            "timeout": POLL_TIMEOUT_SECONDS,
            "allowed_updates": ["message", "callback_query"],
        }
        if self._offset is not None:
            payload["offset"] = self._offset
        updates = self._call("getUpdates", payload) or []
        for update in updates:
            if isinstance(update.get("update_id"), int):
                self._offset = update["update_id"] + 1
        return updates

    def send(
        self,
        chat_id: int,
        text: str,
        buttons: list[list[tuple[str, str]]] | None = None,
        entities: list[dict] | None = None,
        thread_id: int | None = None,
    ) -> int | None:
        payload: dict = {"chat_id": chat_id, "text": text}
        if thread_id is not None:
            payload["message_thread_id"] = thread_id
        if entities:
            payload["entities"] = entities
        if buttons:
            payload["reply_markup"] = {
                "inline_keyboard": [
                    [
                        {"text": label, "callback_data": data}
                        for label, data in row
                    ]
                    for row in buttons
                ]
            }
        result = self._call("sendMessage", payload)
        message_id = (result or {}).get("message_id")
        return message_id if isinstance(message_id, int) else None

    def edit(
        self,
        chat_id: int,
        message_id: int,
        text: str,
        buttons: list[list[tuple[str, str]]] | None = None,
        entities: list[dict] | None = None,
    ) -> None:
        payload: dict = {
            "chat_id": chat_id,
            "message_id": message_id,
            "text": text,
        }
        if entities:
            payload["entities"] = entities
        if buttons:
            payload["reply_markup"] = {
                "inline_keyboard": [
                    [
                        {"text": label, "callback_data": data}
                        for label, data in row
                    ]
                    for row in buttons
                ]
            }
        self._call("editMessageText", payload)

    def answer_callback(self, callback_id: str, text: str = "") -> None:
        self._call(
            "answerCallbackQuery",
            {"callback_query_id": callback_id, "text": text[:180]},
        )

    def send_document(
        self,
        chat_id: int,
        path: str,
        caption: str = "",
        thread_id: int | None = None,
    ) -> None:
        """Upload a file. Multipart, so it bypasses the JSON `_call`
        path; errors are still redacted of the token."""
        import mimetypes
        import uuid

        boundary = uuid.uuid4().hex
        fields = [("chat_id", str(chat_id))]
        if caption:
            fields.append(("caption", caption[:1024]))
        if thread_id is not None:
            fields.append(("message_thread_id", str(thread_id)))
        try:
            with open(path, "rb") as handle:
                file_bytes = handle.read()
        except OSError as exc:
            raise TransportError(f"cannot read file: {exc}") from None
        parts: list[bytes] = []
        for name, value in fields:
            parts.append(
                (
                    f"--{boundary}\r\n"
                    f'Content-Disposition: form-data; name="{name}"\r\n\r\n'
                    f"{value}\r\n"
                ).encode("utf-8")
            )
        filename = Path(path).name
        content_type = (
            mimetypes.guess_type(filename)[0] or "application/octet-stream"
        )
        parts.append(
            (
                f"--{boundary}\r\n"
                f'Content-Disposition: form-data; name="document"; '
                f'filename="{filename}"\r\n'
                f"Content-Type: {content_type}\r\n\r\n"
            ).encode("utf-8")
        )
        body = b"".join(parts) + file_bytes + f"\r\n--{boundary}--\r\n".encode()
        url = f"{API_HOST}/bot{self._token}/sendDocument"
        request = urllib.request.Request(
            url,
            data=body,
            headers={
                "Content-Type": f"multipart/form-data; boundary={boundary}"
            },
        )
        try:
            with urllib.request.urlopen(request, timeout=120) as response:
                doc = json.loads(response.read().decode("utf-8"))
        except Exception as exc:
            raise TransportError(
                f"telegram sendDocument failed: {type(exc).__name__}"
            ) from None
        if not doc.get("ok"):
            raise TransportError(
                f"telegram sendDocument refused: "
                f"{str(doc.get('description'))[:200]}"
            )


class ScriptedTransport:
    """The CI transport: updates fed by the test, sends recorded.
    `feed_stream` interleaves sends and edits chronologically so
    tests can assert what the chat actually looked like. Failure
    injection: set `reject_entities=True` to refuse the entity
    phase (forcing the plain fallback), or `flood_after=(n, s)` to
    raise flood control after n sends."""

    def __init__(self, updates: list[dict] | None = None) -> None:
        self.queue: list[dict] = list(updates or [])
        self.sent: list[dict] = []
        self.edited: list[dict] = []
        self.feed_stream: list[dict] = []
        self.answered: list[dict] = []
        self.documents: list[dict] = []
        self.reject_entities = False
        self.flood_after: tuple[int, float] | None = None
        self._next_id = 100

    def feed(self, update: dict) -> None:
        self.queue.append(update)

    def get_updates(self) -> list[dict]:
        batch, self.queue = self.queue, []
        return batch

    def send(self, chat_id, text, buttons=None, entities=None, thread_id=None) -> int:
        if self.reject_entities and entities:
            raise TransportError("scripted: entities rejected")
        if self.flood_after is not None:
            count, pause = self.flood_after
            if len(self.sent) >= count:
                self.flood_after = None
                raise TransportError("scripted: flood", retry_after=pause)
        record = {
            "chat_id": chat_id,
            "text": text,
            "buttons": buttons,
            "entities": entities,
            "thread_id": thread_id,
            "message_id": self._next_id,
        }
        self._next_id += 1
        self.sent.append(record)
        self.feed_stream.append({**record, "op": "send"})
        return record["message_id"]

    def edit(self, chat_id, message_id, text, buttons=None, entities=None) -> None:
        record = {
            "chat_id": chat_id,
            "message_id": message_id,
            "text": text,
            "buttons": buttons,
            "entities": entities,
        }
        self.edited.append(record)
        self.feed_stream.append({**record, "op": "edit"})

    def answer_callback(self, callback_id: str, text: str = "") -> None:
        self.answered.append({"id": callback_id, "text": text})

    def send_document(self, chat_id, path, caption="", thread_id=None) -> None:
        self.documents.append(
            {
                "chat_id": chat_id,
                "path": path,
                "caption": caption,
                "thread_id": thread_id,
            }
        )
