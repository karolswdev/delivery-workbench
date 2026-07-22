# WLA-26-01 — Contract autonomous delivery programs and trust

- **Project:** work-log-automation
- **Phase:** 26
- **Status:** done
  <!-- status vocabulary: roadmap-builder.md §2.3 -->
- **Depends on:** none
- **Unblocks:** WLA-26-02 through WLA-26-12
- **Owner:** unassigned

## Problem

Phase 24 can execute one bounded score and Phase 25 can hear/nudge its outside
world, but neither describes a durable organization operating a roadmap across
stories and phases. The owner wants configurable implementers, independent
verifiers, verifier-of-verifier and master-architect roles, plus advanced
debate/review/repair loops that can push the project completely autonomously.
Before runtime code, the product needs one exact language and trust model for
that larger promise.

That promise is an optional capability, not a replacement product. A repository
must remain fully healthy and useful with only vanilla Delivery Workbench, and
one bounded Phase 24/25 score/run must remain possible without creating or
joining a program. The contract must protect those defaults before it defines
the more powerful layer.

## Scope

- **In:** `docs/programs.md`; versioned `delivery-workbench-program@1` and
  hierarchical workflow contract (including its relationship to
  `delivery-workbench-orchestration@1`); a progressive capability ladder from
  vanilla → bounded run → advisory program → checkpointed program → continuous
  program; no-program and bounded-run compatibility behavior; opt-in discovery,
  install/update, and Workbench UI rules; roadmap scope; workflow bindings;
  organization/role topology; typed loops, verdicts and gates; program states,
  events, claims, budgets, capabilities, child runs, integration acts, privacy,
  storage, interop, threat table, refusal taxonomy, and exit proof standard.
- **Out:** compiler/runtime/UI implementation; any migration that requires a
  program for existing commands or Workbench flows; ambient activation; a
  hosted service; provider selection or credentials; unbounded recursion;
  merge/release/deploy authority.

## Acceptance criteria

- [x] The contract distinguishes tracked program/workflow/organization policy,
  local driver resolution, and a separate finite program grant; opening,
  compiling, simulating, or saving policy starts nothing.
- [x] Vanilla roadmap/evidence/briefing/deliberate-step/gate/Workbench behavior
  remains a complete, behavior-compatible no-program mode: absent program
  configuration is healthy, and install/update starts no program state,
  process, observer, notification, network call, or setup ceremony.
- [x] `delivery-workbench-orchestration@1` remains an independently opt-in
  one-score/one-run contract with terminal handoff; a score, run, template, or
  existing bounded grant is never auto-wrapped in or interpreted as a program.
- [x] Multi-phase scope, deterministic work/team assignment, hierarchical
  subflows, fan-out/fan-in, bounded loop/exhaustion semantics, and optional
  human checkpoints are complete enough to simulate every legal route.
- [x] Continuous story completion requires an independent verifier assignment;
  implementer, verifier, meta-verifier, council, and master-architect duties and
  separation rules are explicit.
- [x] Mechanical facts, individual agent judgments, council/quorum judgments,
  dissent, and meta-verification are different typed verdicts; none can
  impersonate another.
- [x] Advisory/checkpointed/continuous modes, capability lattice, per-scope and
  per-loop budgets, objective/agent-authorized certification, integration,
  story/phase advancement, expiry/revocation, and permanent exclusions are
  defined with exact fail checks.
- [x] A threat table covers ambient authority, self-verification, prompt/rubric
  mutation, infinite loops, colluding councils, hidden dissent, stale verdicts,
  phase skipping, duplicate destructive acts, content leakage, and UI/runtime
  drift, plus default-mode creep and mandatory program setup; docs/canon
  structural tests pin the decisions.

## Test plan

- **Unit:** structural assertions in `pmo-roadmap/tests/dw-core-tests.py` plus
  `pmo-roadmap/tests/docs-lint.sh` and `canon-lint.sh`.
- **Integration:** no program runtime integration; cross-link and generated/
  vendor parity suites must remain green, and the contract defines the separate
  fresh no-program regression lane required before Phase 26 can close.
- **Manual / device:** read the whole contract as one operator-facing authority
  preview; confirm a reader can tell who may do what, why, how often, and when
  the organization must stop.

## Notes / open questions

The choice is settled: Phase 24's score stays frozen as one bounded-run kind.
Phase 26 adds separate program, workflow, organization, and rubric kinds that
compile into one immutable bundle; a program may call a score only through an
explicit bounded child-run leaf and strict subset grant.
