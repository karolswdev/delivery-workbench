# WLA-17-04 - dw board — the kanban in the terminal

- **Project:** work-log-automation
- **Phase:** 17
- **Status:** done
- **Depends on:** WLA-17-01, WLA-17-02, WLA-17-03
- **Unblocks:** WLA-17-05
- **Owner:** unassigned

## Problem

The roadmap's state lives in tables inside per-phase files; there is
no single view of "what's where" across a project. Agents and humans
both orient faster on a board: columns by status, swimlanes by
phase, parked work visibly parked. The terminal comes first — it is
the surface every dw user already has.

## Scope

- **In:** a `board_model(project, root)` builder in the core —
  per phase: normalized status buckets (backlog | ready |
  in-progress | blocked | on-hold | done) with story ids, titles,
  notes, evidence flags; phases ordered open-first (pointer phase
  on top), paused phases flagged with note, closed phases reduced
  to a one-line done-count. CLI `dw board [project] [--phase N]
  [--all] [--json]` renders fixed-width columns; `--all` expands
  closed phases; `--json` returns the model. Honest truncation —
  never silently dropping a story (a `+N more` tail).
- **Out:** the web board (WLA-17-05); any mutation; per-story
  ordering semantics beyond table order.

## Acceptance criteria

- [ ] `dw board` on this repo renders every open phase as a
  swimlane with six status columns; closed phases collapse to a
  count line; a paused fixture phase shows its pause marker +
  reason.
- [ ] `dw board --json` returns the model (stable keys: phases[],
  columns[], story ids/titles/notes/evidence) — pinned in a test.
- [ ] Run against the flagship tree (~90 phases): completes fast,
  output legible, no errors; parked/decorated legacy statuses land
  in the right columns via `normalize_status`.
- [ ] Nothing is silently dropped: truncated columns show `+N more`.
- [ ] `/usr/bin/python3 pmo-roadmap/tests/dw-core-tests.py` green.

## Test plan

- **Unit:** board model bucketing (incl. decorated statuses, retired
  rows excluded from open columns), JSON shape, truncation tail.
- **Integration:** CLI smoke on the repo's own roadmap.
- **Manual / device:** `dw board` against ~/dev/tools/HoldSpeak —
  captured in evidence.

## Notes / open questions

- Column set is the write vocabulary plus done; legacy oddities
  (`planned`, `scaffolded`…) bucket via normalization to backlog
  unless done/cut — the exact mapping is pinned in tests.
