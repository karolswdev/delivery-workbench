# WLA-18-01 - Self-describing cards: the board and the ledger carry their receipts

- **Project:** work-log-automation
- **Phase:** 18
- **Status:** backlog
- **Depends on:** none
- **Unblocks:** WLA-18-02, WLA-18-03, WLA-18-04
- **Owner:** unassigned

## Problem

A board card is `story_id/title/status/note/evidence_exists` — a
picture, not a door. A consumer holding `dw board --json` (or the
workbench board response) cannot walk to the story file, the
evidence receipt, or the trace without independently knowing the
roadmap tree layout. Same for `dw holds` entries. Interop starts
with self-description.

## Scope

- **In:** `board.py` — every card gains `paths` (repo-relative:
  `story`, `evidence`, `phase_status`) and `links` (workbench API:
  `story`, `trace`); every lane gains `links.phase`; the model is
  stamped `kind: "delivery-workbench-board"` +
  `schema_version: 1`. One helper derives the links so the shape
  cannot fork. `api.py` — `parked_summary` story entries gain the
  same `paths`/`links`; paused-phase entries gain
  `paths.phase_status` + `links.phase`. A test resolves every
  emitted link against `workbench.handle_api` (no rot by
  construction). The workbench board view keeps rendering from the
  same fields (no UI change required).
- **Out:** new routes (the links point at routes that already
  exist); the story-detail core (WLA-18-02); MCP (WLA-18-03).

## Acceptance criteria

- [ ] `dw board --json` cards carry `paths.story`,
  `paths.evidence`, `paths.phase_status` (repo-relative, correct
  against the tree) and `links.story`, `links.trace`; lanes carry
  `links.phase`; the model carries `kind` + `schema_version: 1` —
  all pinned in tests.
- [ ] `dw holds --json` parked stories and paused phases carry the
  same self-description — pinned.
- [ ] A test walks every link emitted for the fixture project
  through `handle_api` and asserts 200 — links cannot rot.
- [ ] Existing board consumers keep working (UI renders unchanged;
  17's board tests pass with only additive shape edits).
- [ ] `/usr/bin/python3 pmo-roadmap/tests/dw-core-tests.py` green.

## Test plan

- **Unit:** shape pins for cards/lanes/holds; link-resolution walk
  against handle_api; schema stamp.
- **Integration:** `dw board --json` + `dw holds --json` smoke on
  this repo.
- **Manual / device:** n/a.

## Notes / open questions

- `evidence` path is emitted even when the file does not exist yet
  (paired with `evidence_exists` — the consumer sees both the
  address and the truth about occupancy). Absent links render as
  absent paths, never invented.
