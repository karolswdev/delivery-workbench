# WLA-28-02 - Resolve the repository location once

- **Project:** work-log-automation
- **Phase:** 28
- **Status:** backlog
- **Depends on:** WLA-28-01
- **Unblocks:** WLA-28-05
- **Owner:** unassigned

## Problem

`git rev-parse --git-dir` is the single most expensive thing the program tick
loop does: 2,435 spawns costing 32.7s inside one test, over half of all git
time. The git directory of a checkout cannot change while the process runs, so
every call after the first is pure waste.

`program_run._git_dir` is on the path of every read and write of run state
(`program_store_dir` and `_run_dir` both route through it), which is why the
count scales with ticks rather than with repositories.

`program_delivery.py` makes it plainer still: one expression calls
`rev-parse --git-dir` three times, where the second and third are always
redundant.

A scratch experiment memoizing this one resolver cut the slowest test from
80.6s to 40.6s and the whole suite from 814s to 619s with all 499 tests
passing, so the size of the win is known before the work starts.

## Scope

- **In:** routing every git-directory resolution through the WLA-28-01
  boundary; memoizing it per repository root for the process; deleting the four
  private resolutions; collapsing the triple-call expression in
  `program_delivery.py`; a spawn-count assertion for the tick path.
- **Out:** caching anything that changes on write (WLA-28-03); changing run
  state layout, identifiers, or path-escape validation; changing what
  `_repository_id` hashes; touching the parallel-suite work.

## Acceptance criteria

- [ ] Every git-directory resolution goes through the WLA-28-01 boundary and is
  computed at most once per repository root per process.
- [ ] `rev-parse --git-dir` spawns during one conductor tick drop from roughly
  53 to at most 1, asserted by a counting test rather than by timing.
- [ ] The triple-call expression in `program_delivery.py` resolves the git
  directory once, with identical output.
- [ ] The existing path-escape and unsafe-run-id refusals still fire; run store
  layout and `_repository_id` values are byte-identical to before.
- [ ] The full core suite passes with no test weakened, and the measured
  improvement is captured as evidence with before and after numbers.
- [ ] A repository whose git directory legitimately differs per root (worktree,
  submodule, separate fixture repo) still resolves correctly — the cache is
  keyed by root, not global.

## Test plan

- **Unit:** cache keyed per root returns distinct directories for distinct
  roots; a single root resolves once across many state reads.
- **Integration:** counting test over a full conductor tick asserts the spawn
  ceiling; run store paths and repository ids compared against pre-change
  values; multi-repository fixtures in one process stay isolated.
- **Manual:** capture the slowest delivery test before and after and record
  both timings in evidence.

## Notes / open questions

Keying by root string is what makes this safe when several fixture repositories
live in one test process — the suite does exactly that, so a global cache would
be wrong.

The long-lived Workbench server serves one root and does not move its git
directory, so a process-lifetime cache is correct there too. If a future story
ever adds repository switching in-process, the boundary is the one place that
must learn to evict.
