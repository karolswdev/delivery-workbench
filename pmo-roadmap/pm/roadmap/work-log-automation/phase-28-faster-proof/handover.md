# Phase 28 handover

What the next person needs to know that the code does not say out loud.

## Where the rules live

`dw_pmo/repofacts.py` is the only place that resolves the git directory. Before
adding any reuse of a git-derived fact, read its census: each fact is declared
**process-immutable** (where the repository *is* — safe to resolve once per
root, for the life of the process) or **derivation-scoped** (what it
*contains* — safe only inside one observation).

The rule that matters: **speed may never buy itself with staleness.** If you
find yourself wanting to keep a `HEAD`, tree, branch, remote ref, or status
value across a write, stop. Those reads are how `program_freshness_issues` and
the divergence checks fail closed.

## Guards that will shout at you

| Guard | Fires when |
|---|---|
| `RepositoryFactsContractTest` | a module outside the boundary resolves the git directory privately |
| `ProofCostBudgetTest` | a conductor tick exceeds 75 git spawns, or `--git-dir` runs more than once |
| `DerivationReadsTest` | one observation asks git the same question twice |
| `ShardRunnerTest` | sharded discovery stops matching a serial run |

Each has a planted-regression case, so you can see it fail on purpose before
trusting it.

## Running the suite

```
python3 pmo-roadmap/tests/run-core-tests.py            # sharded, what CI runs
python3 pmo-roadmap/tests/run-core-tests.py --serial   # one process, debugging
python3 pmo-roadmap/tests/run-core-tests.py --list     # show the assignment
```

The `python-floor` CI job deliberately stays serial. Keep it that way — it is
the control proving the suite still works unsharded, and it would hide a
sharding bug if it were changed to match.

## Traps this phase hit, so you do not

- **`unittest.defaultTestLoader` is shared state.** It carries
  `testNamePatterns` from any `-k` filter. Using it for discovery silently
  shrank the runner to one unit. Always construct a private `TestLoader()`.
- **Never parse human test output for counts.** Test output can itself contain
  `Ran 1 test in 0.0s` from a mocked runner, which undercounted 513 as 456.
  Shards report JSON, and a shard with no summary is a failure, not a zero.
- **`supervise_program` has two ceilings.** `max_ticks` is what tests mean;
  `max_seconds` defaults to 300 and no test asserts it. Eighteen call sites now
  pass an unreachable value so a loaded machine cannot decide an outcome. If
  you add a `supervise_program` call to a test, do the same.
- **One test is timing-sensitive on purpose.**
  `test_cancellation_interrupts_a_live_contained_check` polls 100 x 20ms for a
  live child process. That budget *is* the assertion. It runs alone in the
  serial tail; do not move it into the shards and do not relax it.
- **`repofacts` builds on `gitio`,** so `gitio.in_rewrite_state` imports the
  boundary inside the function. A module-level import there is circular.
- **Cost hints in the runner are hints.** A stale one changes balance, never
  which tests run. Do not treat them as a contract.

## The obvious next win, and its price

`build_program_plan` accounts for ~687 spawns in the slowest test: branch,
HEAD, and tree, once per call, across 229 calls. Each call is a separate
derivation, so there is nothing safe to cache. Reducing it means changing
signatures so callers pass facts they have already observed — explicit,
reviewable, and a wider diff than this phase wanted. That is the recommended
shape if someone picks it up; a hidden cache is not.

## Still unreleased

Phases 25, 26, 27, and 28 are all on `main` and unreleased. `v1.14.0` remains
the published version on PyPI and the tap. None of this phase changed a
machine contract, so a release carries it without migration.
