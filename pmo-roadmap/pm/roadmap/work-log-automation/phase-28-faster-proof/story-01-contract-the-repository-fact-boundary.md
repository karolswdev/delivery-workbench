# WLA-28-01 - Contract the repository-fact boundary

- **Project:** work-log-automation
- **Phase:** 28
- **Status:** ready
- **Depends on:** -
- **Unblocks:** WLA-28-02, WLA-28-03, WLA-28-05
- **Owner:** unassigned

## Problem

Repository-derived facts are read ad hoc. Four places resolve the git
directory privately (`program_run`, `orchestration_run`, `signals`, and an
inline resolution in `contract.py`), and callers re-derive `HEAD`, the index
tree, the current branch, and remote refs wherever they happen to need them.
Nothing states which of these facts can change while a process runs, so no
caller can safely reuse one, and the only safe habit is to spawn `git` again.

That habit is what makes the program tick loop expensive: roughly 53
`rev-parse --git-dir` spawns per tick for a value that is fixed for the life of
the process.

The fix has to start with a contract, not a cache. Until the code says which
facts are process-immutable and which are derivation-scoped, any memoization is
a guess and a future staleness bug.

## Scope

- **In:** one module owning repository-derived facts; a documented, versioned
  classification of each fact as process-immutable or derivation-scoped; the
  invalidation rule for derivation-scoped facts; a fitness test asserting no
  module resolves the git directory privately; documentation of the boundary
  alongside the existing architecture material.
- **Out:** changing any caller yet (WLA-28-02 and WLA-28-03 do that); changing
  what any fact means or how it is computed; caching anything that changes on
  write; replacing `git` invocation with an in-process implementation.

## Acceptance criteria

- [ ] One module owns repository-derived facts and is the only place that
  resolves the git directory; the four private resolutions are named in the
  contract as the sites to be replaced.
- [ ] Every fact the boundary serves is classified explicitly as
  process-immutable (git directory, repository identity) or
  derivation-scoped (`HEAD`, index tree, current branch, remote refs,
  working-tree status), with the reason recorded.
- [ ] The invalidation rule for derivation-scoped facts is stated in the
  contract and expressed in code, not only in prose.
- [ ] A fitness test fails if any module outside the boundary resolves the git
  directory itself, in the style of the existing architecture fitness tests.
- [ ] The boundary changes no observable behavior: the full core suite passes
  unchanged, with no test edited to assert less.
- [ ] The classification is documented where the architecture material lives
  and is discoverable from the phase status.

## Test plan

- **Unit:** classification is complete and total (every served fact has a
  class); the immutable/derivation-scoped split is asserted directly.
- **Integration:** full core suite green with the boundary in place and no
  caller changes; planted private resolver is rejected by the fitness test.
- **Manual:** read the contract and confirm each of the four named private
  resolution sites appears with its replacement target.

## Notes / open questions

The contract is the load-bearing artifact of this phase. Stories 02 and 03 are
mechanical once the classification exists; without it they are unsafe.

Deliberately no caching ships in this story — only the boundary and its rules.
That keeps the first commit's risk near zero and makes the later speed commits
easy to review against a stated rule.
