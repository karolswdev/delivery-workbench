# WLA-24-01 - Contract the visual score and orchestration authority

- **Project:** work-log-automation
- **Phase:** 24
- **Status:** done
- **Depends on:** none
- **Unblocks:** WLA-24-02 through WLA-24-08
- **Owner:** unassigned

## Problem

Phase 23 proves one explicit stale-safe action, but orchestration introduces a
larger authority surface: graphs, parallel agents, prompts/context, checks,
outputs, retries, failure routing, workspaces, and long-lived recovery. Coding
a loop before contracting those meanings would recreate the exact hidden
authority and consent ambiguity that `dw status` and `dw step` removed.

## Scope

- **In:** `docs/orchestration.md`; product claim; exact score artifact and node
  taxonomy; rich-editor rule surface; output/check/failure conventions; score
  versus grant authority; run state machine; scheduler/driver/workspace/
  recovery boundaries; storage and privacy; CLI/MCP/HTTP/Workbench seams;
  threat model; Phase-24 exit proof; complete stories/dependencies/risks.
- **Out:** executable manifest parser, editor code, run state, agent launch,
  command checks, or transport endpoints; provider selection; hosted service;
  certification/commit automation.

## Acceptance criteria

- [x] The contract says Delivery Workbench **can coordinate** a configured
  run, uses capability rather than automatic-operation language throughout,
  and distinguishes a tracked score from the separate authority to execute it.
- [x] One representative `delivery-workbench-orchestration@1` score and
  explicit invariants cover research fan-out/fan-in, roles/profiles,
  dependencies, capabilities, context, typed outputs, exact checks, success/
  failure routes, retries, budgets, concurrency, approvals, and terminals.
- [x] The rich visual editor is specified as Design/Validate/Run views with a
  complete inspector, graph/JSON lossless round trip, pure compilation,
  scheduling simulation, and guarded preview→diff→apply save path.
- [x] Authority rings, grant facts, run states, deterministic tick semantics,
  provider-neutral work packets, isolated workspaces, output validation,
  append-only receipts, cancellation, crash recovery, and privacy exclusions
  are unambiguous enough for exact tests.
- [x] The threat table contains fail checks for score drift, invented
  commands/routes, capability mismatch, parallel writes, unbounded retry,
  skipped checks, duplicate dispatch, stale rail actions, remote expansion,
  and certification/commit confusion.
- [x] Phase status and all seven dependent implementation/exit stories have
  ordered dependencies, bounded scope, testable acceptance criteria, and a
  wheel-installed multi-agent exit exam; docs/roadmap validation passes with
  captured evidence.

## Test plan

- **Unit:** structural doc assertions pin product claim, score/node/grant/run
  terms, editor fields, and permanent exclusions until executable tests own
  them.
- **Integration:** docs lint/snippets, roadmap self-check, rider/generated
  parity, and diff hygiene.
- **Manual / device:** walk the representative research→synthesis→implement→
  check→approval score and verify that every visible editor rule maps to one
  persisted field and one stated runtime refusal.

## Notes / open questions

This story deliberately makes visual configuration part of the core product,
not a late dashboard story. The compiler remains the policy owner; the editor
is a lossless authoring surface over it.

Exact command checks are allowed only as score-owned argv arrays under an
explicit grant, with contained cwd, timeout, output cap, cancellation, and
declared write behavior. Agent-emitted commands and shell strings remain
prohibited.

The score lives in tracked `pm/orchestration/*.json`; run grants, ledgers, and
artifacts live under `.git/pmo-orchestration/`. Secrets and machine-specific
provider mappings live only in operator configuration.

Completed with the architecture contract, eight-story phase plan, structural
assertions, full core test matrix, documentation validation, generated-surface
parity, and roadmap self-check captured in `evidence-story-01.md`. Executable
score compilation begins in WLA-24-02; this story makes no runtime claim.
