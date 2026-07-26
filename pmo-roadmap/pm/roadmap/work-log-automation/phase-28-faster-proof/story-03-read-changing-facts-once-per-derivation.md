# WLA-28-03 - Read changing facts once per derivation

- **Project:** work-log-automation
- **Phase:** 28
- **Status:** backlog
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

## Acceptance criteria

- [ ] Facts that change on write are read at most once per derivation and
  reused within it, served by the WLA-28-01 boundary.
- [ ] Any mutation invalidates the snapshot; a derivation that spans a write
  re-reads rather than reusing, asserted directly.
- [ ] Freshness, remote-divergence, dirty-tree, stale-artifact, and
  commit-hook refusals all still fire, each proven by a planted regression that
  fails if the snapshot goes stale.
- [ ] No existing refusal test is weakened, skipped, or retimed to pass.
- [ ] Spawn counts for these four commands per tick drop measurably, recorded
  as before and after evidence.
- [ ] The snapshot is never shared across repository roots or across runs.

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
