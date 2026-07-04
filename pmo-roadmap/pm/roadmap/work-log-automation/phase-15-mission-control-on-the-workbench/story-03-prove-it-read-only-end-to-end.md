# WLA-15-03 - Prove it read-only, end to end

- **Project:** work-log-automation
- **Phase:** 15
- **Status:** backlog
- **Depends on:** WLA-15-01, WLA-15-02.
- **Unblocks:** phase close.
- **Owner:** unassigned

## Problem

A read-only surface earns its "read-only" claim only when a test
proves no write path exists, and the belt earns "mission control"
only when it renders this repo's real state in a real browser. This
story is both proofs, plus whatever the phase-close version decision
names.

## Scope

- **In:** (a) The read-only guarantee, test-enforced: the
  mission-control routes expose no mutation, and the assertion fails
  on a planted write handler (a fitness-style guard, the Phase 14
  precedent). (b) The live demonstration against this repo: the belt
  rendering the actual roadmap, a real correlated session if one is
  live, the event ticker showing recent gate activity —
  screenshot(s) under evidence `assets/`. (c) Full battery,
  workbench tests, docs-lint, and the release checklist per the
  phase-close decision.
- **Out:** New capability (this story integrates and proves).

## Acceptance criteria

- [ ] The no-write-path guard fails on a planted mutation route and
  passes on the real tree; wired into CI.
- [ ] A screenshot of the live belt in the workbench browser is in
  evidence assets.
- [ ] Full battery + workbench tests + docs-lint green; release
  checklist per the phase-close decision.

## Test plan

- **Unit:** the read-only fitness guard.
- **Integration:** the workbench explorer/smoke over all
  mission-control routes.
- **Manual / device:** the live-browser screenshot above.
