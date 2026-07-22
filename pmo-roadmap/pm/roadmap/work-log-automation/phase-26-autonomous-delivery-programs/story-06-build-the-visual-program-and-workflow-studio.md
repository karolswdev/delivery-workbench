# WLA-26-06 — Build the visual program and workflow studio

- **Project:** work-log-automation
- **Phase:** 26
- **Status:** backlog
  <!-- status vocabulary: roadmap-builder.md §2.3 -->
- **Depends on:** WLA-26-02, WLA-26-03, WLA-26-04, WLA-26-05
- **Unblocks:** WLA-26-11, WLA-26-12
- **Owner:** unassigned

## Problem

The organization is only a product if people can see and shape it. Configuration
files make policy portable and reviewable; a rich web studio must make the same
roadmap scope, roles, nested workflows, loops, gates, councils, budgets, and
authority legible without creating a second policy engine. Advanced constructs
need direct-manipulation affordances, not a JSON-only escape hatch.

## Scope

- **In:** Workbench Program Studio; program/workflow/organization inventory;
  roadmap-scope picker; rule table and candidate explanation; nested graph
  canvas with subflow drill-down, loop containers and role swimlanes; team/
  verifier/council inspector; rubric/verdict/gate builder; capabilities,
  budgets, stop/escalation policy; Design/Simulate/Validate/JSON/Authority views;
  guarded preview→diff→apply; accessible desktop/mobile behavior.
- **Out:** browser-owned validation/scheduling; arbitrary code editor or shell;
  credentials/provider executables; saving as consent; generic BPMN parity.

## Acceptance criteria

- [ ] Every contract field is authorable either directly in the studio or in
  lossless JSON/config view; graph↔config round trips preserve semantic and
  layout hashes exactly.
- [ ] Nested subflows, loop boundaries/max rounds/exit/exhaustion, fan-out/in,
  implementer/verifier separation, councils, meta-verifier and architect gates,
  artifacts, verdicts, capabilities, budgets and stop routes are visually
  distinct and keyboard accessible.
- [ ] Live shared-compiler diagnostics link to the exact graph/inspector field;
  simulation animates candidate assignment and bounded green/red/debate/repair/
  exhaustion routes with worst-case envelopes before any grant exists.
- [ ] Saving/deleting uses a stale-safe preview/fingerprint/apply flow, writes
  only the declared tracked policy, and starts no program, agent, check,
  observer, notification, or integration act.
- [ ] Authority preview visibly separates requested work/verdict capabilities
  from evidence/certification/commit/push/story/phase capabilities and renders
  advisory/checkpointed/continuous differences without granting them.
- [ ] UI smoke covers nested, debate-active, verifier-failed, budget-exhausted,
  phase-transition and complete organizations across supported desktop/mobile
  viewports with no clipping or inaccessible inspector state.

## Test plan

- **Unit:** Workbench view-model/API and JS interaction assertions in the core
  and explorer suites.
- **Integration:** `workbench-explorer.sh`, `workbench-ui-smoke.sh`, compiler
  parity, save/apply stale red paths, and graph/JSON golden round trips.
- **Manual / device:** inspect nested/council/loop/authority views at desktop and
  narrow mobile widths; capture evidence assets.

## Notes / open questions

The studio can borrow familiar workflow notation, but the contract—not BPMN or
the browser—owns which loops, roles, and authority are legal.
