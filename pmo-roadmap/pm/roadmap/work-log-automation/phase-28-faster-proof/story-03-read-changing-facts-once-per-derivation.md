# WLA-28-03 - Read changing facts once per derivation

- **Project:** work-log-automation
- **Phase:** 28
- **Status:** done
- **Depends on:** WLA-28-01, WLA-28-02
- **Unblocks:** WLA-28-05
- **Owner:** unassigned

## Problem

After the git directory is resolved once, the next tier of waste is facts that
do change, but far less often than they are read. Inside one slow test:

| Calls | Time | Command |
|---:|---:|---|
| 638 | 8.5s | `rev-parse --verify HEAD` |
| 513 | 7.5s | `write-tree` |
| 427 | 5.9s | `symbolic-ref` (current branch) |
| 196 | 2.6s | `remote get-url origin` |

That is roughly 1,774 spawns and 24.5s in a single test, for facts that are
constant across one derivation — one frontier computation, one freshness
check, one plan build — and change only when something writes.

This is the story where speed is most likely to buy itself with staleness, so
it is deliberately separated from WLA-28-02. `program_freshness_issues` and the
divergence checks exist to fail closed; a snapshot that outlives a write would
silently defeat them.

## Scope

- **In:** a derivation-scoped snapshot of `HEAD`, index tree, current branch,
  remote refs, and working-tree status served by the WLA-28-01 boundary;
  explicit invalidation on every mutation; adoption in the conductor,
  delivery, and freshness paths; planted-regression tests per refusal.
- **Out:** caching any of these facts beyond one derivation; process-lifetime
  caching of anything that changes on write; changing what freshness,
  divergence, or dirty-tree checks consider a failure; changing gate rules.

## Design change (2026-07-26): narrowed by measurement

The story was written assuming a derivation-scoped snapshot reused across a
computation and invalidated on write. Attributing the spawns killed that
design before it was built:

| Spawns | Caller |
|---:|---|
| 687 | `programs.py:build_program_plan` (branch + HEAD + tree, once per build) |
| 760 | `program_run:_repository_facts` |
| 588 | `program_run:_remote_observation` |

The `_repository_facts` block is reached almost entirely through
`program_freshness_issues` and the divergence checks, whose **entire purpose is
to re-observe and detect change**. There are only five call sites, and each is
a deliberate fresh look. A snapshot spanning them would not be an optimisation;
it would be the staleness bug the phase's hard constraint forbids, and it would
silently disarm the fail-closed refusals.

`build_program_plan` reads each fact exactly once per call. The 229 calls are
229 separate derivations, so sharing across them raises the same question and
carries the same risk.

So the story keeps its title and drops its mechanism. "Read changing facts once
per derivation" is implemented literally — **one observation asks git each
question once** — and nothing is retained between observations. No cache, no
invalidation rule to get wrong, no refusal to re-arm.

The measured redundancy that fit this definition: `_repository_facts` computed
HEAD for its own `head` key, then called `_remote_observation`, which computed
HEAD again. A repository with a remote configured spawned
`rev-parse --verify HEAD` **twice to answer one question**. The observed head is
now passed into the remote leg.

| | Before | After |
|---|---:|---:|
| `rev-parse --verify HEAD` in the slow test | 638 | 448 |
| Total git subprocesses in that test | 2,198 | 2,008 |
| Against the phase baseline | 4,633 | **2,008 (-57%)** |

The durable deliverable is the guard, not the 190 spawns: a test asserts no
command runs twice for a single observation, and it bites (three
`rev-parse --verify` calls before the fix, two after).

## Acceptance criteria

- [x] Facts that change on write are read at most once **per observation**,
  which is the derivation boundary this codebase actually has.
- [x] Nothing is retained between observations: a commit landing between two
  observations is seen by the second, asserted directly.
- [x] Freshness, remote-divergence, dirty-tree, stale-artifact, and
  commit-hook refusals all still fire — no reuse spans them, because no reuse
  exists outside a single observation.
- [x] No existing refusal test was weakened, skipped, or retimed.
- [x] Spawn counts recorded before and after.
- [x] No fact is shared across repository roots or across runs — there is no
  store to share.
- [x] **Rejected and recorded:** a cross-derivation snapshot with an
  invalidation rule. The measurement showed its target is re-observation
  itself.

## Test plan

- **Unit:** snapshot returns consistent values within a derivation; a write
  invalidates it; distinct roots never share one.
- **Integration:** each fail-closed refusal is exercised with a planted stale
  snapshot and must still refuse; full conductor, delivery, and gate suites
  green.
- **Manual:** review each adoption site and confirm the derivation boundary is
  where a reader would expect it to be.

## Notes / open questions

The honest test for this story is not "is it faster" but "does every refusal
still fire". If a planted regression cannot be made to fail, the invalidation
is not actually being tested and the story is not done.

If any single path proves hard to scope safely, the right answer is to leave
that path uncached and record it — partial adoption with a stated reason beats
a clever cache nobody can reason about.
