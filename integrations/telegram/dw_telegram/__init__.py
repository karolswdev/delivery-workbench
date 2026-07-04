"""The Telegram interface — mission control in a pocket (WLA-13-06).

Implements docs/mission-control.md §4 in full: the same feed,
correlation, and event log the Desk consumes (§5 — via the dw CLI,
never private scraping), rendered for chat; agent Q&A relayed off
the correlation document; story flips through the Phase 12
allow-listed argv seam; a tmux driver for claude/codex/pi behind
per-session, visible, expiring arming; project lifecycle
path-allow-listed to the operator's workspace roots. Owner binding
is by pairing, never hardcoded identity.

The component name is "the Telegram interface". The concrete bot
identity and token are operator configuration in
``~/.config/delivery-workbench/telegram.json`` (or
``TELEGRAM_BOT_TOKEN``) and never appear in this repository.

Stdlib only, like the core. CI proves everything against a scripted
transport and fixture rails repos — no live network, ever.
"""

from __future__ import annotations

INTERFACE_VERSION = "0.1.0"

# The substrate schemas this client was proven against (§5: every
# client declares them; drift is a compatibility note, not a break).
FEED_SCHEMA_PROVEN = 1
SESSIONS_SCHEMA_PROVEN = 1
