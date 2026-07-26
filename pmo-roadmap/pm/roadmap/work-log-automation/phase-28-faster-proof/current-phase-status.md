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
- [x] The git directory is resolved at most once per repository per process;
  `rev-parse --git-dir` spawns per conductor tick drop from ~53 to at most 1,
  and the triple-call expression is gone (WLA-28-02).
- [x] Facts that change on write are read once per **observation** — the
  derivation boundary this codebase actually has — and nothing is retained
  between observations, so freshness, divergence, and dirty-tree refusals all
  still fire. The originally planned cross-derivation snapshot was rejected on
  measurement and the reason recorded (WLA-28-03).
- [x] The core proof suite runs sharded across processes on the declared
  Python floor with standard-library tooling only, deterministically and with
  no cross-shard temp state (WLA-28-04).
- [ ] An executable budget caps `git` spawns per tick and fails the suite if a
  new private resolver or redundant spawn appears; the full battery is green
  and the suite is at least 2x faster on the same machine (WLA-28-05).

## Story status

| ID | Story | Status | Story file | Evidence |
|---|---|---|---|---|
| WLA-28-01 | Contract the repository-fact boundary | done | [story-01-contract-the-repository-fact-boundary](./story-01-contract-the-repository-fact-boundary.md) | [evidence-story-01](./evidence-story-01.md) |
| WLA-28-02 | Resolve the repository location once | done | [story-02-resolve-the-repository-location-once](./story-02-resolve-the-repository-location-once.md) | [evidence-story-02](./evidence-story-02.md) |
| WLA-28-03 | Read changing facts once per derivation | done | [story-03-read-changing-facts-once-per-derivation](./story-03-read-changing-facts-once-per-derivation.md) | [evidence-story-03](./evidence-story-03.md) |
| WLA-28-04 | Prove work in parallel | done | [story-04-prove-work-in-parallel](./story-04-prove-work-in-parallel.md) | [evidence-story-04](./evidence-story-04.md) |
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

WLA-28-02 then routed all six sites through the boundary and memoized the
resolution per root. `rev-parse --git-dir` is gone from the tick path
entirely: 2,435 spawns to **0** in the slowest test, total git subprocesses
4,633 to 2,198, git time 63.3s to 25.0s, and the full suite **814s to 547.6s**
while running 14 more tests than the baseline. Two latent worktree defects were
fixed on the way (`signals.py` and `orchestration_run`'s `root/.git` fast
path), and both ledgers are empty and asserted empty in both directions.

**WLA-28-04 is next; WLA-28-03 is deferred behind it by owner decision.**
Attributing the remaining spawns changed the picture WLA-28-03 was written
against:

| Spawns | Caller |
|---:|---|
| 687 | `programs.py:build_program_plan` (branch + HEAD + tree, once per build, 229 builds) |
| 588 | `program_run:_remote_observation` |
| 760 | `program_run:_repository_facts` |

The largest block sits behind `program_freshness_issues`, whose entire purpose
is to re-observe and detect change. Caching that is exactly the staleness bug
the hard constraint forbids, so the story's original design does not survive
contact with the measurement. WLA-28-04 is independent, carries almost no
correctness risk, and is the larger remaining win, so it goes first and
WLA-28-03 is reconsidered afterwards with a fast suite already in hand.

**WLA-28-04 shipped (2026-07-26), after a deliberate park.**
`tests/run-core-tests.py` shards the suite across processes with the standard
library alone on the 3.9 floor. Coverage is proven identical to a serial module
load (516 units expand to exactly the 523 test ids, zero duplicates), and three
consecutive sharded runs measured **118.6s / 129.4s / 122.5s**, all green —
**4.4x** against 547.6s serial and **6.5x** against the 814s baseline. CI now
runs sharded; the `python-floor` job stays serial as a control.

The park was correct and the diagnosis was cheaper than feared.
`supervise_program` carries a `max_seconds` guard defaulting to 300 that
eighteen call sites inherited and **no test asserts** — on a busy desk a
twelve-tick supervision ran out of seconds and returned `time-ceiling` instead
of certifying. Those sites now pass an unreachable ceiling, so `max_ticks`
alone decides an outcome; no assertion changed. Exactly one case is genuinely
load-sensitive — a live-cancellation test whose 2s poll budget *is* the
assertion — and it runs alone in a serial tail.

The runner's own tests caught two bugs in it, both the failure mode the story
exists to prevent: discovery using the shared `defaultTestLoader` (a `-k`
filter silently shrank it from 516 units to 1), and count-parsing that read a
fixture string and undercounted 513 as 456. Shards now report JSON, and a
shard with no summary is a failure rather than a silent zero.

WLA-28-03 then shipped, narrowed by measurement. Its planned cross-derivation
snapshot was **rejected**: the spawns it targeted sit behind
`program_freshness_issues` and the divergence checks, whose purpose is to
re-observe, so a snapshot spanning them would have disarmed the fail-closed
refusals. Implemented literally instead — one observation asks git each
question once. `_repository_facts` had been computing HEAD and then letting
`_remote_observation` compute it again, so any repository with a remote spawned
`rev-parse --verify HEAD` twice per observation. HEAD reads fell 638 to 448 and
total spawns in the slow test 2,198 to 2,008 — **4,633 to 2,008 (-57%)** against
the phase baseline. The durable deliverable is the guard: no command runs twice
for one observation, and separate observations still re-read everything.

WLA-28-05 is next: pin these numbers as an executable budget and close the
phase.

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
- 2026-07-26 - WLA-28-04 runs before WLA-28-03 - spawn attribution showed
  WLA-28-03's target sits behind `program_freshness_issues`, whose job is to
  re-observe, so its original design conflicts with the hard constraint;
  WLA-28-04 is independent, lower risk, and the larger win - owner decision.

## Decisions deferred

- Whether to extend sharding to the shell and integration suites - trigger once
  WLA-28-04 proves core suite sharding is stable - default is core suite only.
- How to reduce the ~2,035 remaining derivation spawns without weakening
  re-observation - trigger after WLA-28-04 lands - options on record: explicit
  fact injection into `build_program_plan`, a scoped snapshot with proven
  invalidation, or closing WLA-28-03 as deliberately not done.
- Whether the cost budget becomes a CI-enforced threshold or a local advisory -
  trigger at WLA-28-05 - default is fail the suite, matching existing fitness
  tests.
- **How to make the sixteen `supervise_program` tests survive parallel
  execution** - trigger: WLA-28-04 cannot leave on-hold until this is decided -
  options: (a) raise `max_seconds` in those fixtures, which does not weaken
  what they assert but does edit tests this phase's scope protects; (b) run
  them in the serial tail and accept ~1.4x instead of 2.6x; (c) shard only in
  CI, where the machine is dedicated, and keep the desk default serial;
  (d) make the ceilings configurable so tests can scale them by observed load.
  No default - this is an owner decision.
