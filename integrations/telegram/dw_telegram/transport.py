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

API_HOST = "https://api.telegram.org"
POLL_TIMEOUT_SECONDS = 50


class TransportError(RuntimeError):
    """A transport failure with any token content redacted."""


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
            raise TransportError(
                f"telegram {method} failed: HTTP {exc.code} {body}"
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
    ) -> None:
        payload: dict = {"chat_id": chat_id, "text": text}
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
        self._call("sendMessage", payload)

    def answer_callback(self, callback_id: str, text: str = "") -> None:
        self._call(
            "answerCallbackQuery",
            {"callback_query_id": callback_id, "text": text[:180]},
        )


class ScriptedTransport:
    """The CI transport: updates fed by the test, sends recorded."""

    def __init__(self, updates: list[dict] | None = None) -> None:
        self.queue: list[dict] = list(updates or [])
        self.sent: list[dict] = []
        self.answered: list[dict] = []

    def feed(self, update: dict) -> None:
        self.queue.append(update)

    def get_updates(self) -> list[dict]:
        batch, self.queue = self.queue, []
        return batch

    def send(self, chat_id, text, buttons=None) -> None:
        self.sent.append(
            {"chat_id": chat_id, "text": text, "buttons": buttons}
        )

    def answer_callback(self, callback_id: str, text: str = "") -> None:
        self.answered.append({"id": callback_id, "text": text})
