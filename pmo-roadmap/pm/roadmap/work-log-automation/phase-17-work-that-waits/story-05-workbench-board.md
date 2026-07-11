# WLA-17-05 - The board on the workbench

- **Project:** work-log-automation
- **Phase:** 17
- **Status:** backlog
- **Depends on:** WLA-17-04
- **Unblocks:** WLA-17-06
- **Owner:** unassigned

## Problem

The workbench web view has browse, health, trace, edit, and mission
control — but no at-a-glance answer to "where does everything
stand?". The owner's ask: a kanban board, divided by phase. The board
model exists after WLA-17-04; this story gives it glass.

## Scope

- **In:** `workbench.py` — `GET /api/projects/<slug>/board` serving
  `board_model` through the same envelope. `workbench/app.js` —
  `#/board/<slug>` view (nav from overview + project view): one
  swimlane per open phase (pointer phase first), six status
  columns, cards showing story id / title / evidence tick / hold
  note; paused swimlanes dimmed with the reason banner; closed
  phases collapsed rows (click to expand); read-only in this
  story. `workbench/style.css` — board layout (columns scroll
  inside the lane, the page never scrolls sideways), status colors
  reusing the existing badge palette.
- **Out:** drag/mutations (WLA-17-06); new polling machinery (manual
  refresh like other views); mission-control session pins on cards.

## Acceptance criteria

- [ ] `/api/projects/<slug>/board` returns the WLA-17-04 model in
  the standard envelope; route logic covered by a handle_api test.
- [ ] `#/board` renders swimlane-per-phase with all six columns;
  a paused phase is visibly dimmed and shows its reason; closed
  phases are collapsed with done counts.
- [ ] Cards link to the existing story view; hold notes visible on
  the card (not only tooltip) for blocked/on-hold.
- [ ] Snapshot-mode screenshot of the board on this repo's roadmap
  captured into evidence assets.
- [ ] `/usr/bin/python3 pmo-roadmap/tests/dw-core-tests.py` green.

## Test plan

- **Unit:** handle_api board route (status, envelope, 404 unknown
  project).
- **Integration:** serve + curl the endpoint on this repo.
- **Manual / device:** browser screenshot (snapshot mode) into
  evidence assets.

## Notes / open questions

- Keep the DOM light for 90-phase trees: closed lanes render as a
  single row until expanded; no per-card event listeners (one
  delegated handler).
