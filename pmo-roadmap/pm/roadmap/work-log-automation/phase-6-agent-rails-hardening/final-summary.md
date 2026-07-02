# Phase 6 Final Summary

**Status:** complete.
**Date:** 2026-07-02.

## Outcome vs exit criteria

All ten exit criteria closed with evidence (see
[current-phase-status](./current-phase-status.md) for the pointers):
the repo enforces itself end-to-end (hooks, trailers, archive, work
logs — pre-contract-v2 Phase 6 commits carry story IDs but no digest
trailers, recorded as expected history in evidence-story-03), the
full trace chain resolves, the gate is single-sourced with the
drift-bug family fixed and parity-proven, index-tree freshness killed
the touch bypass, evidence content is linted with captured runs in
five real Phase 6 evidence files, the agent surface completes a
lifecycle from CLAUDE.md alone with doctor healthy, contract tiers are
gate-decided, the canon is de-personalized under CI lint,
three-command adoption lands doctor-healthy, and CI runs the full
suite on ubuntu + macos with shellcheck, a python-3.9 floor job, and
least-privilege hygiene.

## Evidence index

| ID | Story | Evidence | Landing commits |
|---|---|---|---|
| WLA-6-01 | Dogfood integrity | [evidence-story-01](./evidence-story-01.md) | 690dcec..a00b150 |
| WLA-6-02 | Single dw gate engine | [evidence-story-02](./evidence-story-02.md) | e23a958 |
| WLA-6-03 | Verified contract v2 | [evidence-story-03](./evidence-story-03.md) | faa7de6, 23f8fec |
| WLA-6-04 | Evidence capture + lints | [evidence-story-04](./evidence-story-04.md) | 88d64c4 |
| WLA-6-05 | Agent surface | [evidence-story-05](./evidence-story-05.md) | c86bdb8 |
| WLA-6-06 | Ceremony + canon | [evidence-story-06](./evidence-story-06.md) | 2ee38b2, 5e2137f |
| WLA-6-07 | Onboarding bridge | [evidence-story-07](./evidence-story-07.md) | b0c74d7, 45d3c65, 5a6e6f8 |
| WLA-6-08 | CI + portability | [evidence-story-08](./evidence-story-08.md) | this commit |

## Surprises and lessons

- The framework's own history was its harshest reviewer: landing the
  backlog through the gate produced the friction log that drove the
  whole phase.
- Verification beats certification everywhere it was tried: index-tree
  freshness, title-matched boxes, captured runs, and stamped facts each
  removed an honor-system surface without adding agent friction.
- Portability bugs hide in pairs: fixing bash 5.2 patsub_replacement
  broke bash 3.2; only the two-OS matrix catches that class reliably.
- Ship the linter early — canon-lint and shellcheck each caught real
  regressions on their first run.

## Handoff to phase 5 (resumed)

- Now available: dw_pmo core with gate/contract/evidence/adopt/doctor
  APIs, preview→apply-with-fingerprint mutations, machine-readable
  porcelain, and a two-OS CI matrix — the foundation WLA-5-03..10's
  workbench UI builds on without a second source of truth.
- Contract/canon changes: contract v2 tiers, mechanical tests-ran
  discharge, slimmed final summaries (this file is the first),
  de-personalized templates, single status vocabulary.
- Read first: pm/roadmap README "Active extension",
  phase-5 current-phase-status "Where we are", and
  evidence-story-01's friction log for the remaining deferred items
  (committed contract-archive mirror, work-log retention, hosted mode).
