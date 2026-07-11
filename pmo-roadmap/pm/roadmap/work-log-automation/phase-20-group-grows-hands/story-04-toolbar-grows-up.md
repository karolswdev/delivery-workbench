# WLA-20-04 - The toolbar grows up — grids, builtins, and the command menu

- **Project:** work-log-automation
- **Phase:** 20
- **Status:** done
- **Depends on:** WLA-20-01, WLA-20-03
- **Unblocks:** (optional)
- **Owner:** unassigned

## Problem

The `/toolbar` is one hardcoded grid (Enter/Esc/arrows/refresh).
ccgram's toolbar is configuration: per-provider button grids with
three action types — `key` (a named key through the multiplexer),
`text` (literal text + Enter), `builtin` (a closed set of special
handlers) — and a style knob. Our HARNESS capability table already
models per-agent behavior as data; the toolbar should ride the same
idea. And the bot never registers its commands with Telegram, so
the client offers no command menu at all.

## Scope

- **In:** `integrations/telegram/dw_telegram/toolbarcfg.py` — a new
  import-pure leaf transmuted from ccgram's `toolbar_config.py`:
  built-in per-harness grids (claude/codex/pi keyed by the HARNESS
  names), action types `key`/`text`/`builtin` with a CLOSED builtin
  dispatch set (`screen`, `live`, `dismiss`), styles
  (emoji/text/emoji_text), loader reading an optional `"toolbar"`
  object from `telegram.json` (JSON, not TOML — 3.9 floor), unknown
  harness → claude grid, malformed entries logged-and-skipped,
  loader never raises. `interface.py`: `/toolbar` renders the grid
  for the bound session's harness; `key`/`text` taps route through
  the driver exactly as today (armed + owned floors); `builtin`
  taps dispatch to the story-01 screenshot and existing live/
  dismiss handlers; taps are owner-checked (story 03). Transport:
  `set_my_commands(commands)` verb; serve start registers the
  slash-command menu (config opt-out `"command_menu": false`).
- **Out:** user-defined builtins (the table is closed — a config
  can rearrange, relabel, or drop buttons, never mint capability);
  read_state/mode-cycling buttons (ccgram's provider mode button —
  deferred until a harness needs it); persistent reply keyboards.

## Acceptance criteria

- [ ] Default grids render per harness; unknown harness falls back
  to claude; a config override reshapes the grid; a malformed entry
  is skipped with a warning and the rest of the grid survives; the
  loader never raises on garbage (fuzz-ish test over broken JSON
  shapes).
- [ ] A config naming a non-builtin as `builtin` is refused at load
  (closed table pinned by a test that tries to mint one).
- [ ] `key` and `text` taps reach the pane only through
  `TmuxDriver` (fitness census unchanged) and only armed+owned;
  `builtin: screen` produces the story-01 photo flow.
- [ ] `setMyCommands` is called once at serve start with the
  command set; opt-out config suppresses it; ScriptedTransport
  records it.
- [ ] Full telegram suites green.

## Test plan

- **Unit:** toolbarcfg loader (defaults, override, malformed,
  closed-table refusal).
- **Integration:** /toolbar render + tap dispatch per action type
  via ScriptedTransport; serve-start registration.
- **Manual / device:** desk walk with a custom grid in
  telegram.json.

## Notes / open questions

Emoji labels ship in the built-in grids (📸 ⏎ ⎋ …); style
`text` strips them for clients where emoji render poorly.
