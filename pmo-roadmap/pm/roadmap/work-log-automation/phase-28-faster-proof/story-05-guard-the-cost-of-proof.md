# WLA-28-05 - Guard the cost of proof

- **Project:** work-log-automation
- **Phase:** 28
- **Status:** done
- **Depends on:** WLA-28-01, WLA-28-02, WLA-28-03, WLA-28-04
- **Unblocks:** -
- **Owner:** unassigned

## Problem

Performance work that is not guarded rots. The habit that produced 2,435
redundant spawns was not a single bad commit; it was many reasonable local
decisions to re-read a fact rather than reason about whether it was safe to
reuse. Nothing in the suite objected, because nothing measured it.

This story closes the phase by making the cost observable and enforced, and by
proving the whole battery is still honest and now faster.

Wall-clock alone is the wrong guard: it is machine-dependent and noisy in CI.
Counting subprocesses is deterministic and is what actually regressed.

## Scope

- **In:** an executable budget capping `git` spawns for a conductor tick and
  the delivery path; a fitness test rejecting new private git-directory
  resolvers; end-to-end proof that the full battery is green; recorded before
  and after measurements for the phase; the phase final summary and handover.
- **Out:** enforcing a wall-clock threshold in CI; extending budgets to
  surfaces this phase did not touch; further optimization work beyond
  restoring the budget when it fails.

## Acceptance criteria

- [x] An executable budget caps `git` subprocess spawns for one conductor tick
  and for the delivery path, and fails with a message naming the command that
  overran and by how much.
- [x] A fitness test fails if a new private git-directory resolution appears
  outside the WLA-28-01 boundary.
- [x] The budget is proven to bite: a planted redundant spawn fails the suite.
- [x] The full battery is green — core suite, gate, verify, package smoke,
  docs and canon lint, workbench mirrors, rider docs check — with no test
  weakened across the phase.
- [x] Measured before and after numbers for the phase are recorded: suite wall
  clock, slowest-test wall clock, and per-tick spawn counts, on the same
  machine.
- [x] The suite is at least 2x faster than the 814s baseline on the same
  machine.
- [x] Phase final summary and handover record what shipped, what was
  deliberately deferred, and where the budget lives.

## Test plan

- **Unit:** budget accounting counts the right commands and reports overruns
  precisely; the private-resolver fitness check rejects a planted violation.
- **Integration:** whole battery green; sharded and serial runs agree; planted
  redundant spawn fails.
- **Manual:** run the full battery end to end on the desk, capture timings, and
  compare against the recorded 2026-07-26 baseline.

## Notes / open questions

The 2x target is against the 814s serial baseline measured on the desk on
2026-07-26. Stories 02 and 03 alone were measured to reach 619s; sharding is
what carries the rest, so if WLA-28-04 has to be narrowed, this target should
be renegotiated openly rather than quietly dropped.

The budget numbers should be set slightly above the achieved counts, not at
them, so ordinary refactoring does not trip the guard for no reason.
