# WLA-23-05 - Fresh-consumer deliberate-step exit exam

- **Project:** work-log-automation
- **Phase:** 23
- **Status:** backlog
- **Depends on:** WLA-23-04
- **Unblocks:** phase close and next release decision
- **Owner:** unassigned

## Problem

Component tests cannot prove that repeated explicit one-step authorization is
usable, stale-safe, and incapable of crossing the consent boundary in a
wheel-installed consumer.

## Scope

- **In:** packaged install/update fixture; successive preview/token/apply
  transitions; stale same-id and prohibited commit red paths; transport/UI
  parity; full regression and release-readiness closeout.
- **Out:** publishing/tagging without a separate owner request; multi-step
  automation.

## Acceptance criteria

- [ ] A fresh consumer advances one real story by authorizing every step
  separately and never reconstructing the underlying action argv.
- [ ] A relevant state change invalidates the token even when the action id
  stays constant; runner/event counts remain zero.
- [ ] Certification and commit remain manual through every surface.
- [ ] Full distribution, Python-floor, UI, agent, optional integration, docs,
  and history suites are green with a phase final summary.

## Test plan

- **Unit:** full core suite.
- **Integration:** dedicated package exit exam plus complete CI matrix.
- **Manual / device:** inspect fresh-consumer receipts and final commit chain.

## Notes / open questions

Record unresolved decisions here before implementation starts.
