#!/usr/bin/env python3
"""Run the Telegram interface on the operator's machine.

    python3 integrations/telegram/run.py pair    # print a one-time pairing token
    python3 integrations/telegram/run.py serve   # start the interface

``pair`` prints the short-TTL token to this terminal and nowhere
else; send it in chat as ``/pair <token>`` within its TTL. ``serve``
reads the operator config (``~/.config/delivery-workbench/telegram.json``
or ``TELEGRAM_BOT_TOKEN``) and long-polls the Bot API. No token, chat
id, or pairing token is ever printed by either verb.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from dw_telegram.config import ConfigError, load_config
from dw_telegram.interface import TelegramInterface
from dw_telegram.msgqueue import MessageQueue
from dw_telegram.pairing import PAIRING_TTL_SECONDS, new_pairing_token
from dw_telegram.rails import RailsClient
from dw_telegram.runtime import RuntimeState, utc_now
from dw_telegram.transport import HttpTransport, TransportError


def main(argv: list[str]) -> int:
    verb = argv[0] if argv else "serve"
    try:
        config = load_config()
    except ConfigError as exc:
        print(f"telegram interface: {exc}", file=sys.stderr)
        return 2
    state = RuntimeState(config.resolved_state_path())

    if verb == "pair":
        token = new_pairing_token(state, utc_now())
        print(
            f"pairing token (valid {PAIRING_TTL_SECONDS // 60} min, "
            f"single use):\n\n  /pair {token}\n"
        )
        return 0
    if verb == "serve":
        transport = HttpTransport(config.bot_token)
        try:
            me = transport.get_me()  # fail fast and loud on a bad token
        except TransportError as exc:
            print(f"telegram interface: {exc}", file=sys.stderr)
            return 2
        interface = TelegramInterface(config, state, transport)
        registered = interface.register_command_menu()
        print(
            f"telegram interface: serving as @{me.get('username')} "
            f"(command menu {'registered' if registered else 'off'}; "
            "Ctrl-C stops)",
            file=sys.stderr,
        )
        try:
            interface.run_forever()
        except KeyboardInterrupt:
            return 130
        return 0
    if verb == "notify":
        # One bounded push pass (docs/signals.md): send unread,
        # undelivered notification facts to the paired chat, record
        # every attempt outcome, and exit. Send-only — the paired chat
        # is already the consented destination; facts persist locally
        # whether or not this pass runs.
        if state.paired_chat is None:
            print(
                "telegram interface: not paired; notification facts stay local",
                file=sys.stderr,
            )
            return 2
        repo = None
        if len(argv) > 1:
            repo = Path(argv[1]).expanduser()
        elif config.default_repo is not None:
            repo = config.default_repo
        if repo is None or not repo.is_dir():
            print(
                "telegram interface: notify needs a rails repo "
                "(run.py notify <repo> or set default_repo)",
                file=sys.stderr,
            )
            return 2
        rails = RailsClient(dw_cli=config.dw_cli)
        doc, why = rails.notifications(repo)
        if doc is None:
            print(f"telegram interface: {why}", file=sys.stderr)
            return 1
        pending = [
            item for item in doc.get("notifications", [])
            if item.get("unread")
            and not item.get("delivered")
            and int(item.get("delivery_attempts", 0)) < 3
        ]
        if not pending:
            print("telegram interface: nothing to push", file=sys.stderr)
            return 0
        queue = MessageQueue(HttpTransport(config.bot_token))
        sent = 0
        for item in pending:
            try:
                queue.enqueue(state.paired_chat, str(item.get("outbound", "")))
                queue.flush()
                rails.notification_delivered(repo, str(item["id"]))
                sent += 1
            except TransportError:
                rails.notification_delivered(
                    repo, str(item["id"]), failed="transport-error"
                )
        print(f"telegram interface: pushed {sent}/{len(pending)} notification(s)")
        return 0 if sent == len(pending) else 1
    print(f"usage: run.py [pair|serve|notify] (got {verb!r})", file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
