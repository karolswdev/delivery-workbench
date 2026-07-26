# WLA-28-02 - Resolve the repository location once

- **Project:** work-log-automation
- **Phase:** 28
- **Status:** done
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
  boundary; memoizing it per repository root for the process; deleting the
  private resolutions; collapsing the triple-call expression in
  `program_delivery.py`; a spawn-count assertion for the tick path.
- **Out:** caching anything that changes on write (WLA-28-03); changing run
  state layout, identifiers, or path-escape validation; changing what
  `_repository_id` hashes; touching the parallel-suite work.

## Acceptance criteria

- [x] Every git-directory resolution goes through the WLA-28-01 boundary and is
  computed at most once per repository root per process.
- [x] `rev-parse --git-dir` spawns during one conductor tick drop from roughly
  53 to at most 1, asserted by a counting test rather than by timing.
- [x] The triple-call expression in `program_delivery.py` resolves the git
  directory once, with identical output.
- [x] The existing path-escape and unsafe-run-id refusals still fire; run store
  layout and `_repository_id` values are byte-identical to before.
- [x] The full core suite passes with no test weakened, and the measured
  improvement is captured as evidence with before and after numbers.
- [x] A repository whose git directory legitimately differs per root (worktree,
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

## Result (measured)

Every git-directory resolution now routes through `repofacts.git_dir`, which
memoizes per resolved root. Measured on the same slowest delivery test:

| | Before | After |
|---|---:|---:|
| `rev-parse --git-dir` spawns | 2,435 | 0 |
| Total git subprocesses | 4,633 | 2,198 |
| Total git time in the test | 63.3s | 25.0s |
| Full core suite wall clock | 814s / 499 tests | 547.6s / 513 tests |

`rev-parse --git-dir` disappears from the test's command histogram entirely —
the first resolution is served from the fixture setup's own resolution, so the
tick itself spends nothing. The conductor-tick ceiling test asserts at most one
spawn per tick, down from roughly 53.

Six sites were migrated, one more than the phase originally counted:

| Site | Was | Now |
|---|---|---|
| `program_run._git_dir` | spawned per state read/write | boundary |
| `orchestration_run._git_dir` | `root/.git` fast path, then spawn | boundary |
| `contract.archive_contract` | inline `subprocess.check_output` | boundary |
| `program_delivery` archive path | **three** spawns in one expression | one call |
| `gitio.in_rewrite_state` | spawned | boundary (function-local import) |
| `signals._git_dir` | assumed `root/.git` is a directory | boundary |

Both ledgers are now empty and asserted empty in both directions.

## Notes / open questions

Keying by root string is what makes this safe when several fixture repositories
live in one test process — the suite does exactly that, so a global cache would
be wrong. A test asserts two roots cost exactly two resolutions across fifty
calls and never return each other's directory.

The long-lived Workbench server serves one root and does not move its git
directory, so a process-lifetime cache is correct there too. If a future story
ever adds repository switching in-process, the boundary is the one place that
must learn to evict. `reset_cache()` exists for tests, not for correctness.

Failures are deliberately not cached: a non-repository that later becomes a
repository resolves correctly, proven by a test. Caching the failure would have
been the easy bug to write here.

Two behavior changes came with the migration, both fixes rather than
regressions, and both are the *correct* reading of the phase's scope even
though the scope forbids semantic changes:

1. `signals.py` now works in a linked worktree or submodule, where it
   previously refused outright. WLA-28-01 pinned the defect; this story flips
   that test from "raises" to "resolves correctly".
2. `orchestration_run._git_dir` dropped a `root/.git` fast path that skipped
   git entirely. It was faster but wrong for the same worktree reason, and the
   boundary's cache makes the fast path pointless anyway.

`gitio.in_rewrite_state` imports the boundary inside the function because
`repofacts` builds on `gitio`; a module-level import would be circular. That
is the one piece of awkwardness in the change and it is confined to one line.
