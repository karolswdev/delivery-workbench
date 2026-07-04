# WLA-13-06 - Prove mission control from Telegram

- **Project:** work-log-automation
- **Phase:** 13
- **Status:** backlog
- **Depends on:** WLA-13-02, WLA-13-03, WLA-13-04
- **Unblocks:** phase close (with WLA-13-05)
- **Owner:** unassigned

*Scaffold-grade spec (2026-07-04): direction is firm, details are
not. WLA-13-01 re-pins this story before it starts.*

## Problem

The Desk conveyor (WLA-13-05) is mission control at the desk; the
owner is not always at the desk. A Telegram bot is the same
mission control in a pocket: it consumes the same feed,
correlation, and events the Desk does, speaks at the Delivery
Workbench level of abstraction (phases, stories, gates — never
raw terminal noise), relays the questions agents are blocked on
and carries the answers back, and can steer live claude/codex/pi
terminal sessions — with a way to see exactly what is happening
when the abstract view isn't enough. Without this story, "steer
from anywhere" is a demo idea; with it, it is a consented,
allow-listed, evidenced property.

## Scope

- **In:** The Telegram interface — the component name; the
  concrete bot identity and token are operator configuration in
  `~/.config/delivery-workbench/telegram.json`, never in this repo
  — that (a) reports mission-control state on demand and on events —
  current phase, story statuses, next actionable, gate verdicts
  and refusals — rendered for chat; (b) relays agent Q&A using the
  session↔story correlation (WLA-13-03): "Claude on WLA-12-03 is
  asking: …" with the reply routed back to the right session;
  (c) steers, under the strictest consent envelope in the program:
  every steering act is a proposal message with an explicit
  preview, executes only on an in-chat approval tap, and is
  restricted to (1) the two allow-listed `dw story` verbs via the
  Phase 12 actuator seam and (2) text relay into an explicitly
  armed tmux session via `send-keys` — arming is per-session,
  visible, and expires; (d) shows live previews via read-only
  `tmux capture-pane` snapshots on request; (e) drives project
  lifecycle: open, install, or create Delivery-Workbench-backed
  git projects on request — `dw`-scaffolded repo, rails installed,
  doctor green, first gated commit — each act a proposal with a
  preview and an approval tap, path-allow-listed to the operator's
  workspace roots; (f) acts as the CLI driver for ALL supported
  agent harnesses through tmux: launching and driving claude,
  codex, and pi sessions in named tmux sessions, every session
  under the same visible, expiring arming envelope, so the whole
  story loop can be conducted from the phone while the terminal
  stays the single place where anything actually runs. Chat
  identity allow-list: the bot answers its owner, nobody else.
- **Out:** Committing any credential to this repo — the bot token
  lives in `~/.config/delivery-workbench/telegram.json` (untracked,
  chmod 600; already provisioned) or `TELEGRAM_BOT_TOKEN`, and the
  repo carries neither real nor placeholder tokens, ever; group
  chats and multi-user access control (owner-only first); any
  parsing of terminal content beyond verbatim capture-pane relay;
  new actuator verbs.

## Acceptance criteria

- [ ] The bot reports real roadmap state and real events for this
  repo in chat, from the WLA-13-02/04 feed and log — no private
  scraping.
- [ ] An agent question surfaces in Telegram with its story
  correlation, and a reply from chat reaches the right live
  session (evidence: both sides captured).
- [ ] A story flip proposed in chat executes only after the
  approval tap, through the Phase 12 actuator seam — and the
  crown case holds: an approved dishonest done-flip is refused by
  the dw gate, with the banner relayed back into the chat.
- [ ] Steering into a tmux session requires prior, visible,
  expiring arming; an unarmed session cannot be steered (test
  proves the refusal); `capture-pane` previews are read-only;
  the driver works against every supported harness (claude,
  codex, pi) in the fixture proof.
- [ ] A project created from chat arrives fully on the rails:
  approved proposal → scaffolded git repo under an allow-listed
  workspace root → rails installed → `dw doctor` green → first
  gated commit; refused outside the allow-listed roots.
- [ ] No token or chat ID appears anywhere in the repo (grep-clean
  in CI); the config path and env override are documented.

## Test plan

- **Unit:** message rendering from feed fixtures; consent state
  machine (proposal → approval → execution, arming expiry);
  owner-allow-list refusals.
- **Integration:** bot logic against a fixture rails repo with a
  scripted Telegram transport (no live network in CI).
- **Manual / device:** the live loop from a phone — state, a
  relayed question and answer, an approved flip, a gate refusal in
  chat, a capture-pane preview — screenshots under evidence
  `assets/`.

## Notes / open questions

- tmux `send-keys` is raw input injection into a terminal running
  with the owner's rights — the single sharpest edge in the
  program. WLA-13-01 designs its consent envelope (arming
  semantics, expiry, what is loggable) before any implementation;
  the default posture is everything off.
- Whether the bot process lives in this repo or rides HoldSpeak's
  relay seams - decide in WLA-13-01 with the counterpart phase in
  view.
