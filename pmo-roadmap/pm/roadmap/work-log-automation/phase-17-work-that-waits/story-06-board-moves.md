# WLA-17-06 - Guarded moves on the board

- **Project:** work-log-automation
- **Phase:** 17
- **Status:** backlog
- **Depends on:** WLA-17-05
- **Unblocks:** (phase close)
- **Owner:** unassigned

## Problem

A board you can only look at sends you back to the CLI for the very
action it suggests. The workbench already has the correct write
discipline — structured intent, preview with diffs, fingerprint-bound
apply, issues guard. Dragging a card is just another way to construct
that same intent; it must never become a second write path.

## Scope

- **In:** `workbench/app.js` — HTML5 drag-and-drop on board cards:
  drop on a status column opens the move panel (existing
  preview→apply components) pre-filled with
  `update_story_status`; dropping into blocked/on-hold requires a
  reason in the panel (client mirrors the server rule from
  WLA-17-01); dropping into done surfaces the evidence-body
  requirement exactly like the editor does; apply refreshes the
  board. Paused/closed swimlanes refuse drops with an explanatory
  notice. Keyboard/no-drag fallback: a "move…" affordance on each
  card opening the same panel.
- **Out:** any new server endpoint (moves go through
  /api/mutations/preview + /api/mutations/apply verbatim);
  drag-to-reorder; multi-select.

## Acceptance criteria

- [ ] Dragging a ready card to in-progress previews the exact
  diffs and applies on confirm; the board reflects the new state
  after apply.
- [ ] Dropping onto on-hold/blocked demands a reason before preview
  is enabled; the applied cell carries the decoration.
- [ ] Dropping a no-evidence story onto done is refused client-side
  with the same message shape as the editor; forcing through the
  panel still hits the server refusal.
- [ ] Drops on paused or closed lanes are refused with a notice
  naming why; nothing is written.
- [ ] Stale-fingerprint path proven: change the file between
  preview and apply → 409 surfaced, nothing written.
- [ ] `/usr/bin/python3 pmo-roadmap/tests/dw-core-tests.py` green.

## Test plan

- **Unit:** the server-side rules the drag mirrors are covered by
  WLA-17-01/02 handle_mutation tests (reason-required parks).
- **Integration:** scripted preview→apply move through the HTTP
  endpoints (curl) on a scratch roadmap.
- **Manual / device:** browser walk: drag ready→in-progress,
  drag→on-hold with reason, refused done-drop; screenshots into
  evidence assets.

## Notes / open questions

- The issues-guard (409 when the project has validation issues)
  applies to board moves exactly as to editor mutations — the
  board surfaces the same acknowledge flow, never bypasses it.
