# WLA-26-01 — Contract autonomous delivery programs and trust

- **Project:** work-log-automation
- **Phase:** 26
- **Status:** in-progress
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

## Scope

- **In:** `docs/programs.md`; versioned `delivery-workbench-program@1` and
  hierarchical workflow contract (including its relationship to
  `delivery-workbench-orchestration@1`); roadmap scope; workflow bindings;
  organization/role topology; typed loops, verdicts and gates; program states,
  events, claims, budgets, capabilities, child runs, integration acts, privacy,
  storage, interop, threat table, refusal taxonomy, and exit proof standard.
- **Out:** compiler/runtime/UI implementation; a hosted service; provider
  selection or credentials; unbounded recursion; merge/release/deploy authority.

## Acceptance criteria

- [ ] The contract distinguishes tracked program/workflow/organization policy,
  local driver resolution, and a separate finite program grant; opening,
  compiling, simulating, or saving policy starts nothing.
- [ ] Multi-phase scope, deterministic work/team assignment, hierarchical
  subflows, fan-out/fan-in, bounded loop/exhaustion semantics, and optional
  human checkpoints are complete enough to simulate every legal route.
- [ ] Continuous story completion requires an independent verifier assignment;
  implementer, verifier, meta-verifier, council, and master-architect duties and
  separation rules are explicit.
- [ ] Mechanical facts, individual agent judgments, council/quorum judgments,
  dissent, and meta-verification are different typed verdicts; none can
  impersonate another.
- [ ] Advisory/checkpointed/continuous modes, capability lattice, per-scope and
  per-loop budgets, objective/agent-authorized certification, integration,
  story/phase advancement, expiry/revocation, and permanent exclusions are
  defined with exact fail checks.
- [ ] A threat table covers ambient authority, self-verification, prompt/rubric
  mutation, infinite loops, colluding councils, hidden dissent, stale verdicts,
  phase skipping, duplicate destructive acts, content leakage, and UI/runtime
  drift; docs/canon structural tests pin the decisions.

## Test plan

- **Unit:** structural assertions in `pmo-roadmap/tests/dw-core-tests.py` plus
  `pmo-roadmap/tests/docs-lint.sh` and `canon-lint.sh`.
- **Integration:** no runtime integration; cross-link and generated/vendor
  parity suites must remain green.
- **Manual / device:** read the whole contract as one operator-facing authority
  preview; confirm a reader can tell who may do what, why, how often, and when
  the organization must stop.

## Notes / open questions

The contract may choose a new hierarchical workflow kind or a compatible v2 of
the score, but it must not overload the existing v1 DAG with implicit runtime
semantics. That choice is settled here before compiler work.
