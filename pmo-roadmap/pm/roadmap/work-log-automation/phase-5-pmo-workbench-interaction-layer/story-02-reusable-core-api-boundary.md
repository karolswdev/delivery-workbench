# WLA-5-02 - Extract reusable PMO core API boundary

- **Project:** work-log-automation
- **Phase:** 5
- **Status:** ready
- **Depends on:** WLA-5-01
- **Unblocks:** WLA-5-03, WLA-5-04, WLA-5-05, WLA-5-06, WLA-5-07, WLA-5-08
- **Owner:** unassigned

## Problem

`pmo-roadmap/bin/dw` currently owns the parser, validator, trace, and mutation
logic. A workbench UI or local API that reimplements that logic would create
two behavioral surfaces and eventually two sources of truth. The core must be
extracted into a reusable library before any rich UI or server can be trusted.

## Scope

- **In:** `pmo-roadmap/lib/dw_pmo/` package, typed/domain dataclasses,
  parser/context extraction, validator extraction, trace extraction, mutation
  preview/apply primitives, CLI adapter migration, and compatibility tests.
- **Out:** UI components, HTTP server, new mutation types beyond Phase 4
  behavior, or changing the existing CLI contract without a compatibility shim.

## Acceptance criteria

- [ ] `pmo-roadmap/lib/dw_pmo/` exists with modules for model, paths, parse,
  validate, trace, mutations, render, and API envelopes or an equivalent
  cohesive structure documented in the story evidence.
- [ ] `pmo-roadmap/bin/dw` imports the shared core and keeps the Phase 4 command
  behavior intact.
- [ ] Core mutation APIs can produce a preview object without writing files.
- [ ] Core apply APIs write only PMO-owned paths, reuse rollback behavior, and
  return changed files plus validation results.
- [ ] Existing `pmo-roadmap/tests/roadmap-cli.sh` passes unchanged or with only
  assertions that strengthen the public contract.
- [ ] New core-level tests cover parser fixtures, validation fixtures, mutation
  preview idempotence, stale target handling, and trace fallback behavior.

## Test plan

- **Unit:** Core parser/validator/mutation tests for canonical and drift
  fixtures.
- **Integration / Cypress:** `pmo-roadmap/tests/roadmap-cli.sh` and
  `pmo-roadmap/bin/dw context work-log-automation --trace --compact`.
- **Manual / device:** Inspect `dw --help` and representative command output to
  confirm the CLI surface still reads the same.

## Notes / open questions

The extraction should be boring and mechanical. Any redesign of PMO semantics
belongs in a separate story and must not block preserving existing CLI behavior.
