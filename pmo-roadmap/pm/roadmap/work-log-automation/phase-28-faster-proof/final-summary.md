# Phase 28 - Faster Proof: final summary

**Closed:** 2026-07-26. Five stories, five shipped.

## Outcome against the exit criteria

| Exit criterion | Result |
|---|---|
| One executable contract owns repository facts; no private git-dir resolution | `delivery-workbench-repository-facts@1` in `dw_pmo/repofacts.py`; both ledgers empty and asserted empty in both directions |
| Git directory resolved once per process; per-tick spawns ~53 → ≤1 | `rev-parse --git-dir` gone from the tick path entirely |
| Changing facts read once per derivation; refusals still fire | Implemented as one-read-per-observation; nothing retained between observations |
| Core suite sharded, stdlib only, deterministic, no cross-shard state | `tests/run-core-tests.py`; coverage proven identical to a serial load |
| Executable budget caps spawns and fails on regression; suite ≥2x faster | Budget guard bites on a planted spawn; **8.8x** measured |

## The numbers

Measured on the same desk, same suite:

| | Baseline (phase open) | Close |
|---|---:|---:|
| Core suite wall clock | **814s** | **92.9s** |
| Tests | 499 | 526 |
| Git subprocesses in the slowest test | 4,633 | 2,008 |
| `rev-parse --git-dir` in that test | 2,435 | **0** |
| Git spawns per conductor tick | ~111 (incl. ~53 git-dir) | 58 |

**8.8x faster while running 27 more tests.** Nothing was weakened, skipped, or
removed to get there; the test count only rose.

Roughly a third of the win came from not asking git the same question twice,
and the rest from using the cores that were already idle.

## What shipped

- **WLA-28-01** — the repository-fact boundary. Eight facts classified as
  process-immutable or derivation-scoped, with the reason recorded; the
  invalidation rule expressed as `repofacts.Derivation`; a fitness guard that
  fails on any new private git-directory resolution.
- **WLA-28-02** — one resolution per root per process. Six sites migrated,
  `rev-parse --git-dir` eliminated from the tick path, the cache keyed by root
  so one process can serve many repositories.
- **WLA-28-03** — one observation asks git each question once. The planned
  cross-derivation snapshot was **rejected on measurement**.
- **WLA-28-04** — the suite sharded across processes, stdlib only, on the 3.9
  floor, with coverage proven identical to a serial run.
- **WLA-28-05** — an executable budget on spawns per tick, proven to bite.

## Two latent bugs found by performance work

Neither was the point of the phase, and both were real:

1. **`signals.py` did not work in a linked worktree or submodule.** It assumed
   `root/.git` is a directory; where `.git` is a file it refused outright.
   Found by the WLA-28-01 fitness guard, pinned by a test using a real
   `git worktree add`, fixed in WLA-28-02.
2. **`orchestration_run` had the same flaw** in a `root/.git` fast path that
   skipped git entirely — faster, and wrong for the same reason.

## What the guards caught in our own work

Worth recording, because the guards paid for themselves before the phase
closed:

- The fitness guard corrected the phase's own count of private resolvers on
  its first run: five spawning sites, not four.
- The shard runner's tests caught two bugs in the runner: discovery using the
  shared `unittest.defaultTestLoader`, whose `-k` filter silently shrank it
  from 516 units to **1**; and count-parsing that matched a fixture string and
  undercounted 513 tests as **456**.

## Deliberately deferred

- **Cross-derivation fact reuse.** Rejected, not postponed: its target is
  re-observation itself. Revisiting it requires a different mechanism —
  explicit fact injection into `build_program_plan` — not a cache.
- **`build_program_plan`'s 687 spawns.** Each call reads each fact once; the
  229 calls are 229 separate derivations. Reducing them means changing
  signatures so callers pass what they already observed.
- **Sharding the shell, integration, package, and Telegram suites.** The core
  suite only, as scoped. `package-smoke.sh` remains the long pole in CI.
- **A wall-clock threshold in CI.** The budget counts subprocesses, which is
  deterministic; wall clock is machine-dependent and would flake.
- **`supervise_program`'s 300s default.** Left alone. Only the test call sites
  pass an unreachable ceiling; changing the product default was out of scope.

## Honest notes

The phase's plan did not survive contact with measurement, twice, and both
times the measurement won:

- WLA-28-03 lost its mechanism entirely. Caching what
  `program_freshness_issues` reads would have disarmed the fail-closed
  refusals — a faster gate that lies is worse than a slow one.
- WLA-28-04 was parked mid-flight when repeated sharded runs proved unstable,
  then resolved once the cause turned out to be an incidental 300s wall-clock
  guard that no test asserts.

The hard constraint held throughout: nothing is cached that can change while
the process runs, and every fail-closed refusal still fires.
