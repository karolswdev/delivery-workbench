# Evidence - WLA-28-03

- **Story:** WLA-28-03 - Read changing facts once per derivation
- **Status:** done
- **Date:** 2026-07-26

## The design this story shipped is not the one it was written with

WLA-28-03 was written assuming a derivation-scoped snapshot, reused across a
computation and invalidated on write. Attributing the remaining spawns to their
callers killed that design before it was built:

| Spawns | Caller |
|---:|---|
| 687 | `programs.py:build_program_plan` |
| 760 | `program_run:_repository_facts` |
| 588 | `program_run:_remote_observation` |

`_repository_facts` has only five call sites, and they are reached almost
entirely through `program_freshness_issues` and the divergence checks — whose
**entire purpose is to re-observe and detect change**. A snapshot spanning
them would not be an optimisation; it would be the staleness bug the phase's
hard constraint forbids, and it would quietly disarm the fail-closed refusals
that exist to catch a moved HEAD or a dirty tree. `build_program_plan` already
reads each fact exactly once per call; its 229 calls are 229 separate
derivations.

So the story keeps its title and drops its mechanism. "Read changing facts once
per derivation" is implemented literally — **one observation asks git each
question once** — and nothing is retained between observations. There is no
cache, therefore no invalidation rule to get wrong and no refusal to re-arm.

## What was actually redundant

`_repository_facts` computed HEAD for its own `head` key, then called
`_remote_observation`, which computed HEAD **again**. Any repository with a
remote configured spawned `rev-parse --verify HEAD` twice to answer one
question. The observed head is now passed into the remote leg; a caller that
does not supply it still gets a fresh read.

| | Before | After |
|---|---:|---:|
| `rev-parse --verify HEAD` in the slow test | 638 | 448 |
| Total git subprocesses in that test | 2,198 | 2,008 |
| Against the phase baseline | 4,633 | **2,008 (-57%)** |

## The guard is the deliverable, not the 190 spawns

Three cases pin the rule:

- no command runs twice for a single observation;
- one observation reads HEAD once even with a remote configured;
- **separate observations still re-read everything** — a commit landing
  between two observations changes both `head` and `index_tree` in the second,
  which is the guarantee that keeps re-observation honest.

The guard bites: reverting the one-line fix makes the observation spawn
`rev-parse --verify` three times instead of two, and the test fails by name.

## Regression proof

526 tests OK (499 at phase baseline; 27 added across the phase, none weakened
or removed), sharded in 92.9s. `dw verify --all` re-derives the structural
rules over **178 commits**. Gate parity, docs and canon lint, compileall on the
3.9 floor, the source/vendor mirror `cmp`, rider docs check, `update.sh
--check`, `dw check`, and a whitespace check all pass.

## Acceptance mapping

- Read at most once per observation -> no-double-read guard.
- Nothing retained between observations -> the commit-between-observations
  case.
- Every fail-closed refusal still fires -> no reuse spans observations; full
  conductor, delivery, and gate suites green; `dw verify --all` ok.
- No refusal test weakened, skipped, or retimed -> test count rose, not fell.
- Before/after spawn counts recorded -> table above.
- Cross-derivation snapshot rejected and recorded -> design-change section in
  the story.

## Proof

### Captured run — 2026-07-26T22:18:21Z

- **Command:** `bash -lc set -e
python3 pmo-roadmap/tests/run-core-tests.py
python3 -m unittest -v pmo-roadmap/tests/dw-core-tests.py -k DerivationReadsTest
/usr/bin/python3 -m compileall -q pmo-roadmap/lib/dw_pmo
bash pmo-roadmap/tests/docs-lint.sh
bash pmo-roadmap/tests/canon-lint.sh
bash pmo-roadmap/tests/gate-parity.sh
cmp pmo-roadmap/lib/dw_pmo/program_run.py .githooks/dw_pmo/program_run.py
.githooks/dw rider docs --check
bash pmo-roadmap/update.sh . --check
pmo-roadmap/bin/dw check work-log-automation
pmo-roadmap/bin/dw verify --all
git diff --check`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 1108ecd97a462611f9c446fa918315c76e118b24

```text
run-core-tests: 519 units across 8 shards + 1 serial
  shard 0:  67 tests in   80.0s  ok
  shard 1:  68 tests in   76.2s  ok
  shard 2:  63 tests in   82.9s  ok
  shard 3:  67 tests in   86.2s  ok
  shard 4:  69 tests in   84.7s  ok
  shard 5:  63 tests in   87.4s  ok
  shard 6:  63 tests in   86.7s  ok
  shard 7:  65 tests in   91.0s  ok
  shard 8:   1 tests in    1.9s  ok
run-core-tests: 526 tests in 92.9s (OK)
test_no_fact_is_read_twice_inside_one_observation (pmo-roadmap.tests.dw-core-tests.DerivationReadsTest) ... ok
test_one_observation_reads_head_once_even_with_a_remote (pmo-roadmap.tests.dw-core-tests.DerivationReadsTest) ... ok
test_separate_observations_still_re_read_everything (pmo-roadmap.tests.dw-core-tests.DerivationReadsTest) ... ok

----------------------------------------------------------------------
Ran 3 tests in 0.735s

OK
docs-lint: ok (486 markdown files)
docs-lint.sh: ok (0s)
canon-lint.sh: ok
gate-parity.sh: ok
dw rider docs: all rendered surfaces match canon
update.sh: up to date (vendored rails match source v1.14.0)
dw check: ok
dw verify: ok (178 commits verified, 17 pre-epoch skipped)
```
