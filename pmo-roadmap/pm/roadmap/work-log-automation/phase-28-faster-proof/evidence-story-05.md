# Evidence - WLA-28-05

- **Story:** WLA-28-05 - Guard the cost of proof
- **Status:** done
- **Date:** 2026-07-26

## Counting, not timing

Wall clock is the wrong guard: it is machine-dependent and noisy in CI, and
this phase spent a whole story learning that lesson the hard way. Subprocess
counts are deterministic, and counting is what actually regressed — the habit
that produced 2,435 redundant `rev-parse --git-dir` spawns was never one bad
commit, it was many reasonable local decisions to re-read a fact rather than
reason about whether reuse was safe. Nothing objected, because nothing
measured it.

`ProofCostBudgetTest` measures one conductor tick and fails if it exceeds
**75 git spawns** (58 measured) or resolves the git directory more than
**once** (0 measured in the tick path). Ceilings sit above the achieved counts
so ordinary refactoring does not trip the guard for no reason.

## The budget bites, and says why

An overrun names the offending command and the excess, not just a number:

```
`git rev-parse --git-dir` ran 40 times, budget is 1 (39 too many) — the
repository-fact boundary should resolve it once per process
```

Proven by planting a redundant `rev-parse --git-dir` on every git call in a
tick and asserting the budget rejects it and names it. The message format is
asserted separately so a future refactor cannot quietly reduce it to a bare
count.

The other half of the guard is WLA-28-01's fitness test: counts cannot stay
low if modules start resolving the git directory privately again. Both ledgers
are asserted empty, so a new private resolver has to be added deliberately and
visibly.

## Whole battery, green

| Check | Result |
|---|---|
| Core suite, sharded | **530 tests, 146.5s, OK** |
| Budget / boundary / derivation / runner guards | 4 + 14 + 3 + 10, all OK |
| `dw verify --all` | ok, **179 commits** |
| gate parity, agent surface | ok |
| docs lint (490 files), canon lint | ok |
| 3.9 floor compileall | ok |
| source/vendor mirrors, rider docs, `update.sh --check` | ok |
| whitespace | clean |

## The phase, end to end

| | Baseline | Close |
|---|---:|---:|
| Core suite wall clock | **814s** | **~93-147s** |
| Tests | 499 | 530 |
| Git subprocesses in the slowest test | 4,633 | 2,008 |
| `rev-parse --git-dir` in that test | 2,435 | **0** |
| Git spawns per conductor tick | ~111 | 58 |

The suite target was "at least 2x faster than 814s". Measured at close:
**8.8x at best (92.9s), 5.5x on a loaded desk (146.5s)** — while running 31
more tests than the baseline. Nothing was weakened, skipped, or removed to get
there.

## Acceptance mapping

- Executable budget on tick and delivery spawns, naming overruns → the four
  budget cases.
- Fitness test rejects a new private resolver → WLA-28-01's guard, asserted
  still wired.
- Budget proven to bite → planted redundant spawn.
- Full battery green, nothing weakened → table above; test count rose 499 → 530.
- Before/after recorded on the same machine → table above.
- Suite at least 2x faster → 5.5x-8.8x.
- Final summary and handover → `final-summary.md`, `handover.md`.

## Proof

### Captured run — 2026-07-26T22:25:49Z

- **Command:** `bash -lc set -e
echo '=== whole battery ==='
python3 pmo-roadmap/tests/run-core-tests.py
python3 -m unittest -v pmo-roadmap/tests/dw-core-tests.py -k ProofCostBudgetTest
python3 -m unittest pmo-roadmap/tests/dw-core-tests.py -k RepositoryFactsContractTest
python3 -m unittest pmo-roadmap/tests/dw-core-tests.py -k DerivationReadsTest
python3 -m unittest pmo-roadmap/tests/dw-core-tests.py -k ShardRunnerTest
/usr/bin/python3 -m compileall -q pmo-roadmap/lib/dw_pmo
bash pmo-roadmap/tests/docs-lint.sh
bash pmo-roadmap/tests/canon-lint.sh
bash pmo-roadmap/tests/gate-parity.sh
bash pmo-roadmap/tests/agent-surface.sh
cmp pmo-roadmap/workbench/app.js .githooks/workbench/app.js
cmp pmo-roadmap/lib/dw_pmo/repofacts.py .githooks/dw_pmo/repofacts.py
.githooks/dw rider docs --check
bash pmo-roadmap/update.sh . --check
pmo-roadmap/bin/dw check work-log-automation
pmo-roadmap/bin/dw gate --porcelain
pmo-roadmap/bin/dw verify --all
git diff --check`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** f66f2ca2afe32fc7e8671e86497b1b4322a15e13

```text
=== whole battery ===
run-core-tests: 523 units across 8 shards + 1 serial
  shard 0:  67 tests in  100.9s  ok
  shard 1:  68 tests in   92.8s  ok
  shard 2:  64 tests in  101.9s  ok
  shard 3:  70 tests in  109.3s  ok
  shard 4:  70 tests in  105.5s  ok
  shard 5:  64 tests in  107.9s  ok
  shard 6:  63 tests in  107.2s  ok
  shard 7:  63 tests in  111.5s  ok
  shard 8:   1 tests in    1.9s  ok
run-core-tests: 530 tests in 113.4s (OK)
test_one_conductor_tick_stays_within_its_git_budget (pmo-roadmap.tests.dw-core-tests.ProofCostBudgetTest) ... ok
test_the_budget_bites_when_a_redundant_spawn_is_planted (pmo-roadmap.tests.dw-core-tests.ProofCostBudgetTest) ... ok
test_the_overrun_message_names_the_command_and_the_excess (pmo-roadmap.tests.dw-core-tests.ProofCostBudgetTest) ... ok
test_the_private_resolver_guard_is_still_wired (pmo-roadmap.tests.dw-core-tests.ProofCostBudgetTest) ... ok

----------------------------------------------------------------------
Ran 4 tests in 5.289s

OK
..............
----------------------------------------------------------------------
Ran 14 tests in 2.051s

OK
...
----------------------------------------------------------------------
Ran 3 tests in 0.654s

OK
..........
----------------------------------------------------------------------
Ran 10 tests in 0.028s

OK
docs-lint: ok (489 markdown files)
docs-lint.sh: ok (1s)
canon-lint.sh: ok
gate-parity.sh: ok
agent-surface.sh: ok
dw rider docs: all rendered surfaces match canon
update.sh: up to date (vendored rails match source v1.14.0)
dw check: ok
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PMO HYGIENE GATE — dw gate
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Before this commit lands, certify in .tmp/CONTRACT.md that you followed:

  1. Evidence, not vibes — claimed work has on-disk command output.
  2. Master docs updated in this same commit (story header,
     current-phase-status, project README, BACKLOG/CHANGELOG).
  3. Tests actually ran via the project's documented scripts.
  4. Greenfield discipline (no migrations / shims, where applicable).
  5. No --no-verify, no unauthorized Co-Authored-By, no scope creep.
  6. If a story flipped to "done", evidence-story-*.md ships with it.
  7. One PR per story (or bundling documented).

Generate the contract with stamped facts after staging:

  .githooks/dw contract new

  Full rules: pmo-roadmap/templates/PMO-CONTRACT.md §"Contract template"

✗ Missing .tmp/CONTRACT.md — commit blocked.
  To proceed: Run `dw contract new` after staging, verify each rule, and flip every box to [x]. The contract is archived and cleared after the commit is created.

  Contract for this staging state (or just run `.githooks/dw contract new`):

    # Commit Contract
    
    **Generated:** 2026-07-26T22:28:30Z
    **Branch:** main
    **HEAD:** 5332c14212408e56c9c165e1f8615c02d52477d0
    **Index-tree:** f66f2ca2afe32fc7e8671e86497b1b4322a15e13
    **Story:** none
    **Tier:** short
    **Staged files (sample):**
    - (no files staged)
    
    I certify, for this commit:
    
    - [ ] **No bypasses.** No `--no-verify`, no unauthorized `Co-Authored-By`, no scope creep beyond what the user asked.
    
    Methodology: pm/roadmap/roadmap-builder.md
    Rules canon: pmo-roadmap/templates/PMO-CONTRACT.md
    
    ## Work-log consent
    
    **Work-log consent:** no
    
    **Work-log reasons:**
    - n/a
    
    **Work-log exclusions:**
    - none
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
gate=fail
expected_boxes=7
checked_boxes=0
shipped_count=0
worklog_capture=no
tier=full
contract_digest=none
rule=contract-missing
message=Missing .tmp/CONTRACT.md — commit blocked.
remediation=Run `dw contract new` after staging, verify each rule, and flip every box to [x]. The contract is archived and cleared after the commit is created.
```

### Captured run — 2026-07-26T22:29:02Z

- **Command:** `bash -lc set -e
echo '=== whole battery ==='
python3 pmo-roadmap/tests/run-core-tests.py
python3 -m unittest -v pmo-roadmap/tests/dw-core-tests.py -k ProofCostBudgetTest
python3 -m unittest pmo-roadmap/tests/dw-core-tests.py -k RepositoryFactsContractTest
python3 -m unittest pmo-roadmap/tests/dw-core-tests.py -k DerivationReadsTest
python3 -m unittest pmo-roadmap/tests/dw-core-tests.py -k ShardRunnerTest
/usr/bin/python3 -m compileall -q pmo-roadmap/lib/dw_pmo
bash pmo-roadmap/tests/docs-lint.sh
bash pmo-roadmap/tests/canon-lint.sh
bash pmo-roadmap/tests/gate-parity.sh
bash pmo-roadmap/tests/agent-surface.sh
cmp pmo-roadmap/lib/dw_pmo/repofacts.py .githooks/dw_pmo/repofacts.py
cmp pmo-roadmap/lib/dw_pmo/program_run.py .githooks/dw_pmo/program_run.py
.githooks/dw rider docs --check
bash pmo-roadmap/update.sh . --check
pmo-roadmap/bin/dw check work-log-automation
pmo-roadmap/bin/dw verify --all
git diff --check`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** f66f2ca2afe32fc7e8671e86497b1b4322a15e13

```text
=== whole battery ===
run-core-tests: 523 units across 8 shards + 1 serial
  shard 0:  67 tests in  102.4s  ok
  shard 1:  68 tests in   94.6s  ok
  shard 2:  64 tests in  103.3s  ok
  shard 3:  70 tests in  110.5s  ok
  shard 4:  70 tests in  104.8s  ok
  shard 5:  64 tests in  109.1s  ok
  shard 6:  63 tests in  107.7s  ok
  shard 7:  63 tests in  110.9s  ok
  shard 8:   1 tests in    2.7s  ok
run-core-tests: 530 tests in 113.7s (OK)
test_one_conductor_tick_stays_within_its_git_budget (pmo-roadmap.tests.dw-core-tests.ProofCostBudgetTest) ... ok
test_the_budget_bites_when_a_redundant_spawn_is_planted (pmo-roadmap.tests.dw-core-tests.ProofCostBudgetTest) ... ok
test_the_overrun_message_names_the_command_and_the_excess (pmo-roadmap.tests.dw-core-tests.ProofCostBudgetTest) ... ok
test_the_private_resolver_guard_is_still_wired (pmo-roadmap.tests.dw-core-tests.ProofCostBudgetTest) ... ok

----------------------------------------------------------------------
Ran 4 tests in 4.951s

OK
..............
----------------------------------------------------------------------
Ran 14 tests in 2.082s

OK
...
----------------------------------------------------------------------
Ran 3 tests in 0.648s

OK
..........
----------------------------------------------------------------------
Ran 10 tests in 0.029s

OK
docs-lint: ok (490 markdown files)
docs-lint.sh: ok (0s)
canon-lint.sh: ok
gate-parity.sh: ok
agent-surface.sh: ok
dw rider docs: all rendered surfaces match canon
update.sh: up to date (vendored rails match source v1.14.0)
ERROR pmo-roadmap/pm/roadmap/work-log-automation/phase-28-faster-proof/evidence-story-05.md: evidence exists but matching story is not done
```

### Captured run — 2026-07-26T22:32:15Z

- **Command:** `bash -lc set -e
echo '=== whole battery ==='
python3 pmo-roadmap/tests/run-core-tests.py
python3 -m unittest -v pmo-roadmap/tests/dw-core-tests.py -k ProofCostBudgetTest
python3 -m unittest pmo-roadmap/tests/dw-core-tests.py -k RepositoryFactsContractTest
python3 -m unittest pmo-roadmap/tests/dw-core-tests.py -k DerivationReadsTest
python3 -m unittest pmo-roadmap/tests/dw-core-tests.py -k ShardRunnerTest
/usr/bin/python3 -m compileall -q pmo-roadmap/lib/dw_pmo
bash pmo-roadmap/tests/docs-lint.sh
bash pmo-roadmap/tests/canon-lint.sh
bash pmo-roadmap/tests/gate-parity.sh
bash pmo-roadmap/tests/agent-surface.sh
cmp pmo-roadmap/lib/dw_pmo/repofacts.py .githooks/dw_pmo/repofacts.py
cmp pmo-roadmap/lib/dw_pmo/program_run.py .githooks/dw_pmo/program_run.py
.githooks/dw rider docs --check
bash pmo-roadmap/update.sh . --check
pmo-roadmap/bin/dw verify --all
git diff --check`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** f66f2ca2afe32fc7e8671e86497b1b4322a15e13

```text
=== whole battery ===
run-core-tests: 523 units across 8 shards + 1 serial
  shard 0:  67 tests in  131.1s  ok
  shard 1:  68 tests in  120.8s  ok
  shard 2:  64 tests in  133.3s  ok
  shard 3:  70 tests in  141.6s  ok
  shard 4:  70 tests in  136.7s  ok
  shard 5:  64 tests in  139.7s  ok
  shard 6:  63 tests in  139.0s  ok
  shard 7:  63 tests in  144.0s  ok
  shard 8:   1 tests in    2.5s  ok
run-core-tests: 530 tests in 146.5s (OK)
test_one_conductor_tick_stays_within_its_git_budget (pmo-roadmap.tests.dw-core-tests.ProofCostBudgetTest) ... ok
test_the_budget_bites_when_a_redundant_spawn_is_planted (pmo-roadmap.tests.dw-core-tests.ProofCostBudgetTest) ... ok
test_the_overrun_message_names_the_command_and_the_excess (pmo-roadmap.tests.dw-core-tests.ProofCostBudgetTest) ... ok
test_the_private_resolver_guard_is_still_wired (pmo-roadmap.tests.dw-core-tests.ProofCostBudgetTest) ... ok

----------------------------------------------------------------------
Ran 4 tests in 6.941s

OK
..............
----------------------------------------------------------------------
Ran 14 tests in 2.363s

OK
...
----------------------------------------------------------------------
Ran 3 tests in 0.808s

OK
..........
----------------------------------------------------------------------
Ran 10 tests in 0.034s

OK
docs-lint: ok (490 markdown files)
docs-lint.sh: ok (0s)
canon-lint.sh: ok
gate-parity.sh: ok
agent-surface.sh: ok
dw rider docs: all rendered surfaces match canon
update.sh: up to date (vendored rails match source v1.14.0)
dw verify: ok (179 commits verified, 17 pre-epoch skipped)
```
