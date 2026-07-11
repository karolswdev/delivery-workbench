# Phase 20 - The group grows hands — screenshots, buttons, and per-person consent

**Last updated:** 2026-07-11.

## Goal

The Telegram interface becomes a first-class group surface: the pane
becomes a picture (on demand and live), the buttons become a
configurable toolbar and question-steering keyboards, and consent in
a group belongs to a person, not a room — the second ccgram
absorption (upstream v4.3.11; the first, at v4.3.5, is
docs/absorption-ccgram.md), every feature riding the existing
consent spine. Owner direction (2026-07-11): "make our integration
with Telegram a lot more robust based on groups with interactive
features such as sending screenshots over, using the Telegram API to
build those button-based interfaces… ccgram is MIT — feel free to
use those assets."

## Scope

- **In:** `integrations/telegram/dw_telegram/` — a new
  `screenshot.py` import-pure leaf (ANSI SGR → PNG via Pillow when
  present, honest text fallback when absent; bundled JetBrains Mono
  OFL font only); transport verbs `send_photo` and
  `edit_message_media` (+ ScriptedTransport doubles); `/screen`
  with a refresh button; `/live` image mode (hash-gated
  `editMessageMedia`, timeout auto-stop, text mode preserved);
  owner-of-record captured at `/pair` and enforced on
  consent-bearing commands and callback taps in group chats;
  config-driven toolbar grids (JSON in `telegram.json` — the 3.9
  floor has no tomllib) with key/text/builtin action types and a
  CLOSED builtin table; `setMyCommands` registration; nav keyboards
  (up/down/enter/esc/refresh) on pushed question cards; fitness
  census extensions; docs (absorption ledger v2, mission-control
  contract amendments).
- **Out:** any weakening of the consent spine (arming, pane
  ownership, proposal taps, the seven send locks are untouched
  floors); re-tightening the flowing-conversation stance (§0 stands
  — the binding is the arming); voice/Whisper, LLM summaries/TTS,
  web dashboard mini-app (refusals stand, absorption map rows
  16-18); herdr/other multiplexers (row 19 stands — tmux is the one
  multiplexer); CJK/Symbola fonts (16 MB / 3 MB — deferred until a
  real CJK pane shows tofu); webhook mode (long-poll stands);
  Pillow as a hard dependency (it is optional everywhere, CI
  installs it only for the renderer tests).

## Exit criteria (evidence required)

- [ ] `screenshot.py` renders a captured pane (16/256/RGB ANSI,
  box-drawing) to PNG bytes with Pillow present and reports
  capability honestly without it; it is an import-pure leaf;
  `/screen` sends a photo with a working refresh button inside a
  live binding, and falls back to the `/peek` text capture with a
  stated reason when Pillow is absent (WLA-20-01).
- [ ] `/live` serves an auto-refreshing PICTURE when Pillow is
  present — `editMessageMedia` edits gated by the existing content
  hash, auto-stop preserved — and the text live view without it;
  no-change ticks make zero API calls, exactly as today
  (WLA-20-02).
- [ ] In a group chat, a consent-bearing command or button tap from
  a non-owner is refused by name and the owner is unaffected; reads
  stay chat-scoped; a legacy paired state without an owner-of-record
  keeps today's behavior and `/status` says so; the row-15
  transmutation is recorded as a decision (WLA-20-03).
- [ ] The toolbar renders from config (grid, style, key/text/builtin
  actions), unknown harnesses fall back to the claude grid,
  malformed config entries are skipped with a warning and never
  raise, the builtin table is closed (a config cannot invent one),
  and the slash-command menu is registered with Telegram at serve
  start (WLA-20-04).
- [ ] A pushed agent question carries a nav keyboard that drives the
  bound session's TUI prompt through the driver — armed and
  pane-ownership floors intact — and taps from an unarmed or
  unbound context are refused (WLA-20-05).
- [ ] The fitness suite pins the new shape: `screenshot.py` and
  `toolbarcfg.py` are leaves, photo/media verbs live only in the
  transport, the send-keys census is unchanged, and the planted
  self-test still bites; the absorption ledger names every new
  row absorb/transmute/refuse at v4.3.11; the mission-control
  contract documents the new surfaces (WLA-20-06).

## Story status

| ID | Story | Status | Story file | Evidence |
|---|---|---|---|---|
| WLA-20-01 | The pane becomes a picture — the screenshot engine | backlog | [story-01-screenshot-engine](./story-01-screenshot-engine.md) | - |
| WLA-20-02 | The live view learns to show, not tell | backlog | [story-02-live-image-view](./story-02-live-image-view.md) | - |
| WLA-20-03 | Consent belongs to a person — groups get faces | backlog | [story-03-per-person-consent](./story-03-per-person-consent.md) | - |
| WLA-20-04 | The toolbar grows up — grids, builtins, and the command menu | backlog | [story-04-toolbar-grows-up](./story-04-toolbar-grows-up.md) | - |
| WLA-20-05 | Questions answer with buttons | backlog | [story-05-question-nav-buttons](./story-05-question-nav-buttons.md) | - |
| WLA-20-06 | The exit exam — fitness, ledger, and the contract amended | backlog | [story-06-exit-exam](./story-06-exit-exam.md) | - |

## Where we are

Scaffolded from a capability-map discovery of the current
integration plus a source read of upstream ccgram v4.3.11 (cloned,
MIT). The map's findings that shaped the cut: the button/callback
plumbing already exists end-to-end (proposal cards, the basic
toolbar); NO image path exists (no sendPhoto/editMessageMedia/
renderer — absorption row 11 parked "image later if wanted", now
wanted); NO per-user authorization exists (a paired group grants
every member full owner power — chat_id is checked, from.id never);
no setMyCommands. Implementation order is the story order: the
screenshot leaf first (01), the surfaces that consume it (02), then
consent (03) BEFORE the new interactive surfaces (04, 05) so they
are born owner-checked, exam last (06).

## Active risks

| Risk | Likelihood | Mitigation | Stop signal |
|---|---|---|---|
| A button becomes a second door into the terminal | medium | every key/text action routes through TmuxDriver (fitness: send-keys census); builtin table closed | send-keys or a keystroke method outside tmuxdrive.py |
| Per-person consent breaks the desk's existing private-chat pairing | medium | owner-of-record enforcement applies only where group ambiguity exists; legacy state keeps today's behavior; interface tests pin both | a private-chat flow demanding a re-pair |
| Pillow becomes a hard dependency by accident | medium | capability probe + text fallback tested WITHOUT Pillow in the suite; CI installs Pillow only for renderer tests | an import of PIL at module top-level outside the probe |
| Image live view floods the Bot API | low | the existing content-hash gate carries over; editMessageMedia only on change; auto-stop timeout | an edit tick with an unchanged hash |
| Absorbing 4.3.11 code drags in ccgram's stack (PTB, structlog) | low | transmute, don't vendor: rewrite onto urllib transport + stdlib; only the renderer algorithm and font asset carry over | a new third-party import outside the optional PIL probe |

## Decisions made (this phase)

- 2026-07-11 - Phase scaffolded with `dw phase create` - keeps roadmap structure consistent - CLI.
- 2026-07-11 - Row 15's refusal (user-ID allowlist) is TRANSMUTED, not repealed: no config allowlist appears; the pairing act itself names the owner-of-record (`from.id` of the `/pair` message), and group-context consent checks against that one identity - the owner's new "groups-based" direction makes person-granularity necessary; pairing remains the single consent act - owner charter + capability map §2.
- 2026-07-11 - Bundle JetBrains Mono only (274 KB, OFL); Noto CJK (16 MB) and Symbola (3 MB) deferred - repo heft; tofu is honest until a real CJK pane needs more - asset audit.
- 2026-07-11 - Toolbar config is JSON inside telegram.json, not TOML - the 3.9 test floor has no tomllib and the config file already exists chmod-600 - platform floor.
- 2026-07-11 - Pillow is optional everywhere: module-level probe, text fallback, capability stated in /status - the integration keeps the stdlib-only spirit; the wheel is untouched (integrations/ never ships in it) - distribution stance.

## Decisions deferred

- Sessions dashboard with kill/new buttons (ccgram) - trigger: real
  multi-session pain on the desk - default: `/sessions` text stays.
- Directory-browser bind menu (ccgram db: callbacks) - trigger:
  `/bind` candidate list outgrowing a screenful - default: the
  numbered list stands.
- Auto-screenshot on TUI-prompt detection (push a picture with the
  question) - trigger: WLA-20-05 proving insufficient without it -
  default: nav keyboard + on-demand refresh.
- Webhook transport - trigger: long-poll latency actually hurting -
  default: getUpdates long-poll.
