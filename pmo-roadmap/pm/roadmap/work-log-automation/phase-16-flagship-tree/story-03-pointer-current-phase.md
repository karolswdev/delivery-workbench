# WLA-16-03 - The README pointer drives current phase; next-story skips closed phases

- **Project:** work-log-automation
- **Phase:** 16
- **Status:** done
- **Depends on:** WLA-16-01
- **Unblocks:** WLA-16-04
- **Owner:** unassigned

## Problem

`_project_state` picks `current_phase` from wherever `next_story`
lands, and `next_story` scans all phases oldest-first for the first
`in-progress`/`ready`/`backlog` row — including phases already closed
with a `final-summary.md`. On the flagship tree this elects phase 17
of 86 as "current" (a closed phase with two hardware-gated backlog
rows) while the project README's `**Current phase:**` pointer — the
methodology's own current-phase receipt, already parsed by
`parse_current_phase_target` — names phase 85. Nothing in a closed
phase is actionable; the pointer is authoritative when it resolves.

## Scope

- **In:** `api.next_story` — skip phases whose `final-summary.md`
  exists; within each status tier, prefer the phase the README
  pointer names before the oldest-first scan. `statefeed._project_state`
  — `current_phase` is the pointer's phase when the pointer resolves
  to an existing phase dir; else the phase `next_story` landed in;
  else last open; else last. Tests for both, including the
  pointer-names-a-closed-phase case (report it as current with its
  `closed` status — the truth, not a guess).
- **Out:** the stale-pointer error (already exists in
  `check_project`); any mutation of the pointer (`dw phase close`
  behavior unchanged); feed schema shape.

## Acceptance criteria

- [ ] `dw next` on a fixture with a backlog row inside a closed
  phase and an in-progress row in a later open phase proposes the
  later story; a tree whose ONLY open rows sit in closed phases
  reports nothing actionable (exit 2).
- [ ] `dw state --json`: `current_phase` equals the README pointer's
  phase when it resolves (open or closed); the fallback chain
  (next-story phase → last open → last) is exercised by fixtures
  when the pointer is absent or unresolvable.
- [ ] Existing next-story/statefeed fixtures pass unmodified except
  where they encoded the closed-phase scan (each such edit named in
  evidence with its reason).
- [ ] `python3 pmo-roadmap/tests/dw-core-tests.py` green;
  `pmo-roadmap/tests/telegram-interface-tests.py` green (a feed
  consumer, must see no shape change).

## Test plan

- **Unit:** new `dw-core-tests.py` cases per the criteria.
- **Integration:** `pmo-roadmap/tests/telegram-interface-tests.py`,
  `pmo-roadmap/tests/workbench-explorer.sh`.
- **Manual / device:** n/a.

## Notes / open questions

- The pointer names ONE phase; multi-open-phase trees keep their
  existing "multiple open phases" warning — the pointer does not
  silence it.
