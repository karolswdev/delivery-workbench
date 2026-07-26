# WLA-28-04 - Prove work in parallel

- **Project:** work-log-automation
- **Phase:** 28
- **Status:** on-hold (Sharded runs are not stable on a loaded machine: 16 supervise_program tests carry wall-clock ceilings; awaiting owner decision on how to handle them — since 2026-07-26)
- **Depends on:** -
- **Unblocks:** WLA-28-05
- **Owner:** unassigned

## Problem

The core suite runs 499 tests in one process, one after another, on a machine
with many idle cores. Stories 02 and 03 remove wasted work from the slowest
10% of tests; this story is the only lever that also helps the fast 90%.

The suite is already shaped for parallelism and does not know it: every test
builds its own temporary repository under `mkdtemp` and cleans it up, so there
is no shared fixture to contend over. What is missing is a runner that spreads
classes across processes.

The constraint is that this repository proves itself with the standard library
on a declared Python floor. Reaching for `pytest-xdist` would trade a
dependency and a floor change for the speedup, which the phase scope forbids.

## Scope

- **In:** a standard-library shard runner that distributes test classes across
  processes; a stable, deterministic assignment of classes to shards; aggregate
  reporting that fails the run if any shard fails; wiring the CI core-test step
  and the local entry point to it; a documented way to run the suite serially
  for debugging.
- **Out:** adding any third-party test dependency; changing the Python floor;
  sharding the shell, integration, package, or Telegram suites; rewriting tests
  to be parallel-safe by weakening them; changing test semantics or count.

## Acceptance criteria

- [ ] The core suite runs sharded across processes using only the standard
  library, on the declared Python floor.
- [ ] Shard assignment is deterministic: the same input produces the same
  distribution, and the full test set is covered exactly once with none
  dropped or duplicated.
- [ ] Any shard failure fails the whole run, with the failing test identified
  as clearly as the serial runner identifies it.
- [ ] No cross-shard temp state: each shard's fixtures are isolated and no
  shard depends on another's side effects.
- [ ] Order dependence is ruled out by running the suite repeatedly under
  sharding and comparing results against a serial run.
- [ ] Test count and assertions are unchanged; a serial mode remains available
  and documented for debugging.
- [ ] Wall-clock improvement on the same machine is recorded as evidence.

## Test plan

- **Unit:** shard assignment covers every class exactly once and is stable
  across invocations; failure in one shard propagates to the run's exit code.
- **Integration:** sharded run and serial run report the same test count and
  the same result set; repeated sharded runs are stable across several
  executions.
- **Manual:** run the suite serially and sharded on the desk, compare timings,
  and record both in evidence.

## Status: parked, not done (2026-07-26)

The runner is built, correct, and fast, but the story's stability criterion is
**not** met, so it is parked rather than claimed.

What works and is proven:

- `tests/run-core-tests.py`, standard library only, runs on the 3.9 floor.
- Coverage is provably identical to a serial module load: 516 units expand to
  523 tests, asserted equal to `loadTestsFromModule` with zero duplicates.
- Assignment is deterministic (same inputs, same distribution, independent of
  input order) and balanced (~133 cost per shard across 8).
- A failing shard fails the run; a shard that reports **no** machine-readable
  summary is a failure, never a silent zero.
- Measured wall clock on a quiet desk: **211s sharded vs ~550s serial (2.6x)**;
  best observed 193.8s. Serial agrees at 523 tests.

Why it is parked — repeated sharded runs are **not** stable on a loaded
machine. Two different tests failed across repeats, both for wall-clock
reasons rather than isolation:

1. `OrchestrationConductorTest.test_cancellation_interrupts_a_live_contained_check`
   polls 100 x 20ms for a spawned check process to publish a receipt. A fresh
   interpreter on a saturated box can miss that two-second budget. Handled by
   moving the whole class to the serial tail.
2. `ProgramConductorTest.test_rule_council_meta_audits_and_ingests_durable_obligation`
   failed with `('ready', 'time-ceiling')` instead of
   `('story-certified', 'checkpoint')` — the run exhausted `supervise_program`'s
   wall-clock ceiling before certifying.

The second is the blocking one. **Sixteen tests call `supervise_program` with a
finite `max_seconds`**, and they are precisely the most expensive tests in the
suite. Moving all sixteen to the serial tail would serialize roughly 380s of a
~550s suite and cap the speedup near 1.4x, which defeats the story.

The desk was carrying load averages of 6–13 from unrelated work throughout
these runs, which is the condition that triggers this. A dedicated CI runner is
quieter, and the first sharded run of every capture passed.

The open decision is recorded in the phase status. It needs an owner call
because the obvious fix — raising `max_seconds` in those fixtures — edits
tests, and this phase's scope forbids rewriting tests to accommodate the
runner, even though raising a ceiling would not weaken what those tests assert.

## Notes / open questions

Sharding by class rather than by test keeps expensive nested fixtures
(`ProgramDeliveryTest` builds on `ProgramConductorTest` which builds on
`ProgramRunAuthorityTest`) inside one process, and avoids paying setup more
often than the serial runner does.

The slowest single test takes far longer than the average shard will, so
perfect balance is impossible; distributing the known-slow classes across
different shards first is a reasonable, simple heuristic.
