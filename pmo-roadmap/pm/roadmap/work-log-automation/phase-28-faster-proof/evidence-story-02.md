# Evidence - WLA-28-02

- **Story:** WLA-28-02 - Resolve the repository location once
- **Status:** done
- **Date:** 2026-07-26

## The repository location is resolved once

`repofacts.git_dir` memoizes per resolved repository root and is now the only
place that asks git where `.git` is. Six sites were migrated — one more than
the phase counted at open, because WLA-28-01's guard found `gitio` too:

| Site | Was | Now |
|---|---|---|
| `program_run._git_dir` | spawned on every run-state read and write | boundary |
| `orchestration_run._git_dir` | `root/.git` fast path, then a spawn | boundary |
| `contract.archive_contract` | inline `subprocess.check_output` | boundary |
| `program_delivery` archive path | **three** spawns in one expression | one call |
| `gitio.in_rewrite_state` | spawned | boundary (function-local import) |
| `signals._git_dir` | assumed `root/.git` is a directory | boundary |

Both ledgers are empty (`() ()` in the captured floor check) and asserted empty
in both directions, so a new private resolver has to be added deliberately and
visibly.

## Measured effect

Same slowest delivery test, same machine, before and after:

| | Before | After |
|---|---:|---:|
| `rev-parse --git-dir` spawns | 2,435 | **0** |
| Total git subprocesses | 4,633 | 2,198 |
| Git time inside the test | 63.3s | 25.0s |
| Full core suite | 814s / 499 tests | **547.6s / 513 tests** |

`rev-parse --git-dir` disappears from the command histogram entirely: the
fixture's own first resolution serves the whole process, so the tick spends
nothing. The suite is 33% faster while running 14 more tests than the
baseline.

## The cache is keyed, not global

The suite builds a fresh fixture repository per test, so one process routinely
serves many repositories. A global slot would hand one repository another's
store — the easy bug to write here. Tests assert:

- two roots cost exactly two resolutions across fifty calls, and never return
  each other's directory;
- a failed resolution is **not** cached as success — a non-repository that
  later becomes a repository resolves correctly;
- one conductor tick resolves the git directory at most once, down from ~53.

## Two behavior changes, both fixes

1. `signals.py` now works in a linked worktree or submodule. It previously
   assumed `root/.git` was a directory and refused outright where `.git` is a
   file. WLA-28-01 pinned that defect with a real `git worktree add` fixture;
   this story flips the assertion from "raises" to "resolves correctly".
2. `orchestration_run._git_dir` dropped a `root/.git` fast path that skipped
   git entirely — faster, but wrong for the same worktree reason, and made
   pointless by the cache.

Neither weakens a refusal. Each module keeps its own error message, so program
authority, orchestration runs, signals, and the contract archive still refuse a
non-repository in their own words.

## Regression proof

513 tests OK (499 at phase baseline, 510 after WLA-28-01; 14 added across the
phase, none weakened or removed). `dw verify --all` re-derives the structural
rules over **175 commits** of pushed history. Gate parity, docs and canon lint,
compileall, the 3.9 floor, source/vendor mirror `cmp`, rider docs check,
`update.sh --check`, `dw check`, and a whitespace check all pass.

## Acceptance mapping

- Every resolution through the boundary, at most once per root → six sites
  migrated; keyed-cache test; empty ledgers asserted both ways.
- Spawns per tick from ~53 to at most 1 → ceiling test, counted not timed.
- Triple-call expression gone → one `repofacts.git_dir(root)` call.
- Path-escape and unsafe-run-id refusals still fire; store layout unchanged →
  full conductor, delivery, and gate suites green; `dw verify --all` ok.
- Distinct roots stay isolated → keyed-cache test.
- Measured improvement recorded → table above.

## Proof

### Captured run — 2026-07-26T18:49:46Z

- **Command:** `bash -lc set -e
python3 -m unittest pmo-roadmap/tests/dw-core-tests.py
python3 -m unittest -v pmo-roadmap/tests/dw-core-tests.py -k RepositoryFactsContractTest
/usr/bin/python3 -c "import sys; sys.path.insert(0,'pmo-roadmap/lib'); import dw_pmo.repofacts as rf; print('floor 3.9 ok; ledgers empty:', rf.PENDING_PRIVATE_RESOLVERS, rf.PRIVATE_NON_SPAWNING_RESOLVERS)"
python3 -m compileall -q pmo-roadmap/lib/dw_pmo
bash pmo-roadmap/tests/docs-lint.sh
bash pmo-roadmap/tests/canon-lint.sh
bash pmo-roadmap/tests/gate-parity.sh
cmp pmo-roadmap/lib/dw_pmo/repofacts.py .githooks/dw_pmo/repofacts.py
cmp pmo-roadmap/lib/dw_pmo/program_run.py .githooks/dw_pmo/program_run.py
.githooks/dw rider docs --check
bash pmo-roadmap/update.sh . --check
pmo-roadmap/bin/dw check work-log-automation
pmo-roadmap/bin/dw verify --all
git diff --check`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** c9a6d8cc343889885a81e507242bfa36a99163e4

```text
dw hook: codex_hooks is explicitly false in /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.imixg0_b/config.toml; respecting the opt-out
................................................................................................................................................................................................................................................dw-workbench: 127.0.0.1 "GET /api/runs/run-b71d196b7d7655d3603660bc/events?follow=0 HTTP/1.1" 200 -
dw-workbench: 127.0.0.1 "GET /api/runs/run-b71d196b7d7655d3603660bc/events?follow=0 HTTP/1.1" 200 -
dw-workbench: 127.0.0.1 "POST /api/runs/run-b71d196b7d7655d3603660bc/events HTTP/1.1" 405 -
dw-workbench: 127.0.0.1 "GET /api/signals/events?remote=origin&branch=sse-x&follow=0 HTTP/1.1" 200 -
dw-workbench: 127.0.0.1 "GET /api/runs/run-000000000000000000000000/events?follow=0 HTTP/1.1" 400 -
......................................................................................................................................................dw-workbench: 127.0.0.1 "GET /api/programs/program-bc22746405f0ffcaffa53e29/events?from=0&follow=0 HTTP/1.1" 200 -
...........................................................................................................................
----------------------------------------------------------------------
Ran 513 tests in 547.636s

OK
dw hook: claude — 4 installed, 0 already present in /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.rxj38qve/settings.json
dw hook: claude — 0 installed, 4 already present in /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.rxj38qve/settings.json
dw hook: claude — 4 installed, 0 already present in /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.rt58g3w5/settings.json
dw hook: claude — 4 installed, 0 already present in /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.412omt80/settings.json
dw hook: claude — 4 removed from /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.412omt80/settings.json
test_a_derivation_refuses_to_hold_a_process_immutable_fact (pmo-roadmap.tests.dw-core-tests.RepositoryFactsContractTest) ... ok
test_a_failed_resolution_is_not_cached_as_success (pmo-roadmap.tests.dw-core-tests.RepositoryFactsContractTest) ... ok
test_contract_document_is_versioned_and_total (pmo-roadmap.tests.dw-core-tests.RepositoryFactsContractTest) ... ok
test_derivation_computes_once_and_a_mutation_invalidates (pmo-roadmap.tests.dw-core-tests.RepositoryFactsContractTest) ... ok
test_derivation_keys_facts_so_distinct_targets_do_not_collide (pmo-roadmap.tests.dw-core-tests.RepositoryFactsContractTest) ... ok
test_every_served_fact_declares_a_valid_class_and_reason (pmo-roadmap.tests.dw-core-tests.RepositoryFactsContractTest) ... ok
test_git_dir_is_resolved_once_per_root_and_keyed_not_global (pmo-roadmap.tests.dw-core-tests.RepositoryFactsContractTest) ... ok
test_git_dir_resolves_and_refuses_a_non_repository (pmo-roadmap.tests.dw-core-tests.RepositoryFactsContractTest) ... ok
test_no_new_module_resolves_the_git_directory_privately (pmo-roadmap.tests.dw-core-tests.RepositoryFactsContractTest) ... ok
test_one_conductor_tick_stays_under_the_git_dir_spawn_ceiling (pmo-roadmap.tests.dw-core-tests.RepositoryFactsContractTest) ... ok
test_the_boundary_resolves_a_linked_worktree_where_git_is_a_file (pmo-roadmap.tests.dw-core-tests.RepositoryFactsContractTest) ... ok
test_the_pending_ledger_names_only_real_remaining_sites (pmo-roadmap.tests.dw-core-tests.RepositoryFactsContractTest) ... ok
test_the_split_is_exactly_where_the_phase_says_it_is (pmo-roadmap.tests.dw-core-tests.RepositoryFactsContractTest) ... ok
test_unknown_facts_are_refused_rather_than_defaulted (pmo-roadmap.tests.dw-core-tests.RepositoryFactsContractTest) ... ok

----------------------------------------------------------------------
Ran 14 tests in 2.320s

OK
floor 3.9 ok; ledgers empty: () ()
docs-lint: ok (484 markdown files)
docs-lint.sh: ok (0s)
canon-lint.sh: ok
gate-parity.sh: ok
dw rider docs: all rendered surfaces match canon
update.sh: up to date (vendored rails match source v1.14.0)
dw check: ok
dw verify: ok (175 commits verified, 17 pre-epoch skipped)
```
