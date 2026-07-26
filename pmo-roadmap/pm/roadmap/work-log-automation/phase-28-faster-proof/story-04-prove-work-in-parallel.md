# WLA-28-04 - Prove work in parallel

- **Project:** work-log-automation
- **Phase:** 28
- **Status:** backlog
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

## Notes / open questions

Sharding by class rather than by test keeps expensive nested fixtures
(`ProgramDeliveryTest` builds on `ProgramConductorTest` which builds on
`ProgramRunAuthorityTest`) inside one process, and avoids paying setup more
often than the serial runner does.

The slowest single test takes far longer than the average shard will, so
perfect balance is impossible; distributing the known-slow classes across
different shards first is a reasonable, simple heuristic.
