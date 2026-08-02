# WLA-35-10 - Prove it works

- **Project:** work-log-automation
- **Phase:** 35
- **Status:** done
- **Depends on:** WLA-35-01, WLA-35-02, WLA-35-03, WLA-35-04, WLA-35-05, WLA-35-06, WLA-35-07, WLA-35-08, WLA-35-09
- **Unblocks:** phase close
- **Owner:** unassigned

## Problem

The exit exam: the full closed loop in a real browser and through the packaged fixtures — recall before dispatch, transparent decision basis live, terminal writeback, and a later run benefiting from that memory — while proving memory stays advisory and ordinary use stays side-effect free.

## Scope

- **In:** Full core suite; packaged orchestration + autonomous-program exams with the two-run compounding scenario; browser exam at 1440x900 and 390x844 in both themes; permission tests; no-program regression exam; recorded browser journey.
- **Out:** New features. This story only proves.

## Acceptance criteria

- [ ] The full core suite passes with no regression from the 698-test Phase 34 baseline, with new tests covering recall, writeback, tamper refusal, replay, multi-agent isolation, and authority exclusion.
- [ ] The packaged orchestration and autonomous-program exams complete the two-run compounding scenario with zero duplicate starts or writebacks after forced restart.
- [ ] The browser exam covers run and program memory at 1440x900 and 390x844 in light and dark themes, including populated, empty, stale, tampered, disconnected, failed-run, and superseded-memory states.
- [ ] A recorded browser journey shows: open workbench, start fixture run, inspect recalled knowledge before agent output, follow a decision to its basis, finish the run, inspect writeback, start the related run, and see the prior lesson recalled.
- [ ] Permission tests prove no memory document can start work, widen a grant, satisfy evidence or certification, alter a verdict, or bypass preview and exact-token mutation guards.
- [ ] The no-program regression exam proves install, update, repository open, status, board browsing, and ordinary story work create no program, recall, writeback, observer, process, notification, or network side effects.

## Test plan

- **Unit:** covered by the verification command below.
- **Integration:** `/bin/sh -c '/usr/bin/python3 pmo-roadmap/tests/dw-core-tests.py && bash pmo-roadmap/tests/workbench-explorer.sh && bash pmo-roadmap/tests/workbench-ui-smoke.sh'`
- **Manual / device:** n/a unless named in the acceptance criteria.

## Notes / open questions

Do not weaken the exam to make it pass: no deleted or skipped tests, no removed Firefox paths, no relaxed refusals, no longer unconditional sleeps.
