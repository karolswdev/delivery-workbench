# Phase 28 - Faster Proof

**Last updated:** 2026-07-26.

## Goal

Cut the cost of proving work. Repository facts are resolved once and re-read
exactly when they can have changed, redundant `git` subprocesses disappear, and
the proof suite runs in parallel — without weakening any freshness, authority,
or fail-closed guarantee.

## Why now (measured, 2026-07-26)

Profiling the core suite on the desk produced the facts this phase acts on:

- The suite runs 499 tests in **814s**, and **80% of that comes from the
  slowest 52 tests (10% of the suite)** — all program conductor, delivery, and
  orchestration cases.
- The slowest single test spawns **4,633 `git` subprocesses costing 63.3s of
  its 67s** (94%).
- **2,435 of those calls are `git rev-parse --git-dir`** — 32.7s spent
  re-asking where `.git` is, a fact that cannot change while the process runs.
  `program_run.py` resolves it on every read or write of run state, roughly
  **53 spawns per conductor tick**.
- `program_delivery.py` calls `rev-parse --git-dir` **three times in one
  expression** where two are always redundant.
- Four private git-directory resolutions were counted at phase open
  (`program_run`, `orchestration_run`, `signals`, plus an inline resolution in
  `contract.py`). WLA-28-01's fitness guard corrected this to **five** spawning
  sites — `gitio.in_rewrite_state` was missed — plus `signals.py`, which
  resolves privately without spawning.
- A scratch experiment memoizing one resolver cut the slowest test
  **80.6s to 40.6s (2.0x)** and the whole suite **814s to 619s**, with all 499
  tests still passing.
- Everyday commands are not affected: a real `dw status` issues only **4** git
  calls. The waste is specific to the program tick loop, so it also costs real
  autonomous program runs, not only tests.

## Scope

- **In:** one contracted boundary for repository-derived facts and its
  caching/invalidation rules; replacing the private git-directory resolvers;
  removing redundant subprocess spawns in the program, delivery,
  orchestration, and signals paths; a per-derivation snapshot for facts that
  change on write; parallel execution of the core proof suite; an executable
  cost budget that fails on regression.
- **Out:** changing gate rules, authority, grant, ledger, evidence,
  certification, replay, or refusal semantics; changing machine-contract
  fields, event kinds, or persisted identifiers; rewriting tests to assert
  less; replacing `git` with an in-process implementation; adding a test
  dependency beyond the standard library or moving off the Python floor; a
  version bump, release, or package publication.

## Hard constraint

Speed may never buy itself with staleness. A fact may be cached for the
process only if it cannot change while the process runs (the git directory,
the repository identity). Facts that change on write — `HEAD`, the index
tree, the current branch, remote refs, working-tree status — may be reused
only inside one derivation and must be invalidated by any mutation. Every
existing fail-closed refusal must still fire, proven by planted regressions.

## Exit criteria (evidence required)

- [x] One documented, executable contract owns repository-derived facts and
  states, per fact, whether it is process-immutable or derivation-scoped; no
  module resolves the git directory privately (WLA-28-01).
- [ ] The git directory is resolved at most once per repository per process;
  `rev-parse --git-dir` spawns per conductor tick drop from ~53 to at most 1,
  and the triple-call expression is gone (WLA-28-02).
- [ ] Facts that change on write are read once per derivation and re-read
  after any mutation; freshness, divergence, and dirty-tree refusals still
  fire on planted regressions (WLA-28-03).
- [ ] The core proof suite runs sharded across processes on the declared
  Python floor with standard-library tooling only, deterministically and with
  no cross-shard temp state (WLA-28-04).
- [ ] An executable budget caps `git` spawns per tick and fails the suite if a
  new private resolver or redundant spawn appears; the full battery is green
  and the suite is at least 2x faster on the same machine (WLA-28-05).

## Story status

| ID | Story | Status | Story file | Evidence |
|---|---|---|---|---|
| WLA-28-01 | Contract the repository-fact boundary | done | [story-01-contract-the-repository-fact-boundary](./story-01-contract-the-repository-fact-boundary.md) | [evidence-story-01](./evidence-story-01.md) |
| WLA-28-02 | Resolve the repository location once | backlog | [story-02-resolve-the-repository-location-once](./story-02-resolve-the-repository-location-once.md) | - |
| WLA-28-03 | Read changing facts once per derivation | backlog | [story-03-read-changing-facts-once-per-derivation](./story-03-read-changing-facts-once-per-derivation.md) | - |
| WLA-28-04 | Prove work in parallel | backlog | [story-04-prove-work-in-parallel](./story-04-prove-work-in-parallel.md) | - |
| WLA-28-05 | Guard the cost of proof | backlog | [story-05-guard-the-cost-of-proof](./story-05-guard-the-cost-of-proof.md) | - |

## Where we are

Phase opened 2026-07-26 with profiling evidence in hand. WLA-28-01 shipped the
boundary the other four stories depend on: `delivery-workbench-repository-facts@1`
in `dw_pmo/repofacts.py`, eight facts classified, the invalidation rule
expressed as `repofacts.Derivation`, and a fitness guard that fails on any new
private git-directory resolution. No caching and no caller changes shipped with
it, deliberately — the rule lands before anything reuses a fact.

The guard immediately corrected two of the phase's own assumptions: there are
five spawning sites rather than four (`gitio.in_rewrite_state` was missed), and
`signals.py` resolves the git directory privately without spawning, in a way
that is wrong for linked worktrees. Both are recorded and pinned by tests for
WLA-28-02 to resolve.

WLA-28-02 is next: route every site through the boundary, memoize the
process-immutable resolution, and collapse the triple-call expression.

## Active risks

| Risk | Likelihood | Mitigation | Stop signal |
|---|---|---|---|
| A cache serves a stale fact and a fail-closed refusal stops firing | medium | Cache only process-immutable facts globally; scope changing facts to one derivation; planted-regression tests per refusal | Any existing refusal test needs weakening to pass |
| Parallel shards share temp or global state and go flaky | medium | Each test already owns its temp repo; shard by class, assert no shared paths, run repeatedly to detect order dependence | The same test passes serially and fails sharded |
| Speed work quietly changes machine contracts | low | Scope forbids field/event/identifier changes; existing parity and schema tests stay untouched | A contract or parity test needs editing |
| The suite gets faster by proving less | low | Test count and assertions may not drop; the budget story pins spawn counts, not only wall clock | Test count falls without a recorded reason |

## Decisions made (this phase)

- 2026-07-26 - Phase scaffolded from measured profiling rather than suspicion -
  the four targets are the ones the profile named - profiler output recorded in
  this status.
- 2026-07-26 - Speed may not weaken freshness; the hard constraint above binds
  every story - a stale gate is worse than a slow one - owner direction.
- 2026-07-26 - The fitness guard ships before the migration, with a declared
  shrinking ledger of remaining sites rather than a silent exemption - it
  caught a missed site on its first run - WLA-28-01.
- 2026-07-26 - `signals.py`'s worktree defect is pinned by a test and left for
  WLA-28-02 rather than repaired inside the contract story - keeps the
  boundary commit free of behavior change - WLA-28-01.

## Decisions deferred

- Whether to extend sharding to the shell and integration suites - trigger once
  WLA-28-04 proves core suite sharding is stable - default is core suite only.
- Whether the cost budget becomes a CI-enforced threshold or a local advisory -
  trigger at WLA-28-05 - default is fail the suite, matching existing fitness
  tests.
