# WLA-20-01 - The pane becomes a picture — the screenshot engine

- **Project:** work-log-automation
- **Phase:** 20
- **Status:** done
- **Depends on:** none
- **Unblocks:** WLA-20-02, WLA-20-04
- **Owner:** unassigned

## Problem

The phone sees the pane only as text (`/peek`, text `/live`) — ANSI
color, box-drawing UIs, and TUI prompts arrive flattened or mangled.
ccgram solved this years ago: capture the pane, parse the SGR codes,
render a dark-background PNG with a monospace font chain, send it as
a photo. Phase 14 transmuted that DOWN to text-only and parked
"image later if wanted" (absorption map row 11). The owner now wants
it: "sending screenshots over."

## Scope

- **In:** `integrations/telegram/dw_telegram/screenshot.py` — a new
  import-pure leaf transmuted from ccgram v4.3.11's
  `screenshot.py`: SGR parsing (16/256/RGB, bold/reverse), non-SGR
  escape stripping (OSC/CSI), `text_to_image(text) -> bytes | None`,
  a module-level Pillow probe (`RENDER_AVAILABLE`), and the bundled
  `fonts/JetBrainsMono-Regular.ttf` (OFL, 274 KB, license file
  alongside). Transport: `send_photo(chat, png, caption, buttons,
  thread)` and `edit_message_media(chat, message_id, png)` on
  `HttpTransport` (multipart, reusing the sendDocument plumbing) and
  `ScriptedTransport` (`.photos`, `.media_edits`, feed_stream
  entries). Interface: `/screen` inside a live binding (or explicit
  armed target, same resolution as `/peek`) captures via the driver,
  renders, sends a photo with one `ss:` refresh button;
  Pillow-absent path sends the text capture with the reason stated.
  `/status` reports render capability.
- **Out:** `/live` image mode (WLA-20-02); toolbar screenshot
  builtin (WLA-20-04); auto-screenshot on prompts (deferred); CJK
  and Symbola fonts (deferred, recorded); any new capture path (the
  driver's `capture_pane` is the one source).

## Acceptance criteria

- [ ] Renderer unit tests (Pillow present): a fixture with 16-color,
  256-color, RGB, bold and reverse SGR runs renders to a valid PNG
  (magic bytes + non-trivial dimensions); OSC/CSI noise is stripped;
  box-drawing glyphs map to the bundled font without exceptions.
- [ ] Without Pillow (probe forced off): `text_to_image` returns
  None, `/screen` delivers the text capture with the fallback reason,
  and NOTHING raises — proven by tests that run in a PIL-less
  process.
- [ ] `/screen` in a live binding sends a photo whose refresh button
  re-captures and edits the same message (ScriptedTransport asserts
  one photo + one media edit, no new message).
- [ ] Fitness: `screenshot.py` is in LEAVES (zero internal imports);
  photo/media API strings appear only in `transport.py`.
- [ ] Full telegram interface + fitness suites green; core suite
  untouched and green.

## Test plan

- **Unit:** renderer fixtures (ANSI matrix, stripping, fallback);
  transport multipart shape for photo/media.
- **Integration:** `/screen` flow via ScriptedTransport + fake
  driver, refresh callback round-trip; PIL-less subprocess leg.
- **Manual / device:** live `/screen` against a real tmux pane on
  the desk (phone leg recorded as an asset when convenient).

## Notes / open questions

Renderer is transmuted, not vendored: ccgram's structlog/asyncio
usage is dropped; the algorithm (SGR state machine, font metrics,
line layout) carries over under the existing MIT lineage note in
docs/absorption-ccgram.md. Pillow is installed only in the proof
venv and CI's renderer leg, never a package dependency.
