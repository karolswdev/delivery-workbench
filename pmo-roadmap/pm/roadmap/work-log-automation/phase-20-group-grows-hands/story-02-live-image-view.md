# WLA-20-02 - The live view learns to show, not tell

- **Project:** work-log-automation
- **Phase:** 20
- **Status:** done
- **Depends on:** WLA-20-01
- **Unblocks:** (optional)
- **Owner:** unassigned

## Problem

`/live` already edits one message in place on a content-hash gate —
but it shows a text rendering of a colored, box-drawn TUI. With the
screenshot engine in place, the live view can serve the actual
picture, exactly as ccgram's live view does (editMessageMedia,
hash-gated, auto-stop), completing absorption row 11's parked
"image later if wanted."

## Scope

- **In:** `/live` gains image mode: when `RENDER_AVAILABLE` and the
  first render succeeds, the live message is a photo and each
  changed tick edits it via `edit_message_media`; the EXISTING
  content-hash gate decides "changed" (no new polling loop, no new
  cadence); the existing auto-stop timeout and `/unlive` carry over
  unchanged; text mode remains the Pillow-absent path and the
  explicit `/live text <target>` escape hatch. `/status` names the
  active live mode.
- **Out:** cadence changes (the tick stays as-is); multi-pane grids
  (ccgram web dashboard is refused); streaming/video.

## Acceptance criteria

- [ ] With Pillow: `/live` posts one photo message; a changed pane
  hash produces exactly one `edit_message_media` call; an unchanged
  hash produces ZERO API calls (pinned exactly as the text mode's
  existing no-change test).
- [ ] Auto-stop and `/unlive` end the loop in image mode exactly as
  in text mode; the final state is stated in the message.
- [ ] Without Pillow: `/live` behaves byte-identically to today —
  the existing text-mode tests pin it exactly, now with the render
  probe forced off in their setUp (CI installs Pillow since
  WLA-20-01, so the force-off is what keeps them the no-Pillow
  pins; assertions untouched).
- [ ] `/live text <target>` forces text mode even with Pillow
  present.
- [ ] Full telegram suites green.

## Test plan

- **Unit:** mode selection (probe on/off, explicit text).
- **Integration:** image live tick sequence via ScriptedTransport
  (photo → media edit on change → silence on no-change → stop);
  regression run of the existing text live tests.
- **Manual / device:** live image view against a real pane on the
  desk.

## Notes / open questions

The hash gates on captured TEXT (pre-render), so an unchanged pane
never renders a PNG either — the render cost rides behind the same
gate.
