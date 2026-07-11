# Phase 20 Final Summary

**Status:** complete (6/6).
**Date:** 2026-07-11.

## Outcome vs exit criteria

All six exit criteria met, each with captured evidence:

1. **The screenshot engine** (WLA-20-01): `screenshot.py` as an
   import-pure leaf — SGR state machine (16/256/RGB, reverse),
   non-SGR stripping with an upstream defect fixed en route
   (three-byte charset designators half-stripped by ccgram's
   regex), one bundled OFL font, Pillow optional with the fallback
   stated. `/screen` with in-place 🔄 refresh. Suite green WITH
   and WITHOUT Pillow; `assets/screen-demo.png` is the engine's
   own output.
2. **The image live view** (WLA-20-02): `/live` serves photos
   behind the SAME content-hash gate — no change, no render, no
   API call, pinned. `/live text` on purpose; phase-14 text
   behavior pinned under a forced-off probe.
3. **Per-person consent** (WLA-20-03): the `/pair` redeemer is the
   owner-of-record; fourteen consent commands, every tap, and the
   relay answer to that identity; reads chat-scoped; legacy states
   keep today's behavior with a `/status` warning; the executed
   truth table includes the strict anonymous-refusal corner.
4. **The toolbar as data** (WLA-20-04): per-harness JSON grids,
   key/text/builtin with the builtin table CLOSED (a twelve-shape
   garbage fuzz and a live minting refusal prove the loader),
   tb: taps resolve at tap time, `setMyCommands` at serve start
   with opt-out.
5. **Question nav keyboards** (WLA-20-05): bound + armed only,
   never arming (both refusal corners pinned at zero keystrokes,
   zero arming); Enter notes itself on the card; 📸 delivers the
   story-01 flow.
6. **The exit exam** (WLA-20-06): fitness 8 → 10 (quoted Bot API
   census pinned to transport.py; planted self-test bites in a NEW
   leaf), the absorption ledger's second-absorption section
   (rows 21–30, upstream v4.3.11), the mission-control contract's
   three §4 amendments, the README paragraph. Full battery green:
   core 208, interface 147, fitness 10, docs-lint, plugin.

## What shipped

The second ccgram absorption, from the owner's direction: robust
groups, screenshots over the wire, button-based interfaces. Test
count 108 → 147 across the phase. The consent spine did not move:
every new surface enters through pairing (now with a face), the
binding-is-arming stance (§0, untouched), the driver's one door
with per-keystroke ownership, and the closed builtin table. The
transport stayed a pure leaf; Pillow stayed optional everywhere
(a CI test amenity, never a dependency; the published wheel is
untouched — integrations/ never ships in it).

Notable finds: upstream's charset-designator regex defect (fixed,
test-pinned); the pre-existing group-authority gap (any member of
a paired group held full owner power — closed by WLA-20-03).

## Deliberately deferred

- Directory-browser bind menu, sessions dashboard buttons,
  auto-screenshot on prompt detection, webhook transport (phase
  decisions, triggers recorded).
- CJK/Symbola fonts (16 MB / 3 MB) until a real pane shows tofu.
- The live phone leg screenshots (owed in evidence-story-06; the
  machinery is test-proven).

## Audit trail

| Story | Evidence |
|---|---|
| WLA-20-01 | [evidence-story-01](./evidence-story-01.md) |
| WLA-20-02 | [evidence-story-02](./evidence-story-02.md) |
| WLA-20-03 | [evidence-story-03](./evidence-story-03.md) |
| WLA-20-04 | [evidence-story-04](./evidence-story-04.md) |
| WLA-20-05 | [evidence-story-05](./evidence-story-05.md) |
| WLA-20-06 | [evidence-story-06](./evidence-story-06.md) |
