# WLA-36-05 - Alignment sweep and visual exam

- **Project:** work-log-automation
- **Phase:** 36
- **Status:** done
- **Depends on:** WLA-36-02, WLA-36-03, WLA-36-04
- **Unblocks:** phase close
- **Owner:** unassigned

## Problem

The owner's core complaint is misalignment. After the redesign lands, every surface gets measured - not eyeballed - and the exam learns to catch regressions of the new standard.

## Scope

- **In:** A systematic alignment pass over all 352 exam renders (operator-reviewed), fixes for every found defect, and new mechanical guards: a stylesheet fitness check (only tokens, no stray hex; mono only via the designated classes) plus browser assertions that measure shared-grid alignment on representative surfaces. Full exam battery re-baselined.
- **Out:** New surfaces or features.

## Acceptance criteria

- [ ] The operator reviews the full 352-render matrix and every found misalignment is fixed; the review is recorded in evidence with before/after shots for the worst offenders.
- [ ] A stylesheet fitness test enforces the token system: no hex values outside the token block, mono only through the designated code classes, spacing values on the 8px scale (documented exceptions listed in the test).
- [ ] Browser assertions measure alignment mechanically on at least the topbar, board columns, memory pane, and one Studio surface (shared left edges, consistent control heights).
- [ ] The full core suite, both packaged exams, the 352-render browser exam, accessibility contract, and language lint are green.
- [ ] README screenshots are regenerated from the redesigned UI.

## Test plan

- **Unit:** covered by the verification command below.
- **Integration:** `/bin/sh -c '/usr/bin/python3 pmo-roadmap/tests/run-core-tests.py && bash pmo-roadmap/tests/workbench-ui-smoke.sh'`
- **Manual / device:** operator reviews rendered screenshots before the story flips done.

## Notes / open questions

This story closes the phase; final-summary.md ships with the last flip.
