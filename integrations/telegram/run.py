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
from dw_telegram.pairing import PAIRING_TTL_SECONDS, new_pairing_token
from dw_telegram.runtime import RuntimeState, utc_now
from dw_telegram.transport import HttpTransport


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
        interface = TelegramInterface(
            config, state, HttpTransport(config.bot_token)
        )
        print("telegram interface: serving (Ctrl-C stops)", file=sys.stderr)
        try:
            interface.run_forever()
        except KeyboardInterrupt:
            return 130
        return 0
    print(f"usage: run.py [pair|serve] (got {verb!r})", file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
