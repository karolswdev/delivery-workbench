# Evidence - WLA-28-01

- **Story:** WLA-28-01 - Contract the repository-fact boundary
- **Status:** done
- **Date:** 2026-07-26

## One boundary owns repository-derived facts

[`dw_pmo/repofacts.py`](../../../../lib/dw_pmo/repofacts.py) is the versioned
`delivery-workbench-repository-facts@1` boundary. It serves eight facts and
classifies each one, with the reason recorded next to it:

| Class | Facts | Reuse rule |
|---|---|---|
| process-immutable | `git_dir`, `repository_id` | Resolve once per root, reuse for the process. Where the repository *is* cannot change under a running process. |
| derivation-scoped | `head_sha`, `index_tree`, `current_branch`, `remote_url`, `remote_ref`, `worktree_status` | Reuse only inside one derivation; any mutation invalidates. |

The classification is total and enforced: `fact_class` raises on an unknown
fact rather than defaulting, and `contract_document()` must serve the whole
census. The split is asserted directly against the two named sets, so moving a
fact between classes is a deliberate, visible edit.

## The invalidation rule is code, not prose

`repofacts.Derivation` expresses the rule the phase's hard constraint states.
It computes each scoped fact at most once, keys facts by target so
`origin/main` and `origin/other` cannot collide, drops everything on
`invalidate()`, and **refuses** to hold a process-immutable fact — that belongs
to the process-level resolver, not to a derivation.

No caching and no caller changes ship in this story. That is deliberate: the
rule lands before anything reuses a fact, so WLA-28-02 and WLA-28-03 can be
reviewed against a stated rule instead of a guess.

## The guard bites, and it corrected the phase's own assumptions

`RepositoryFactsContractTest` fails if any module outside the boundary
resolves the git directory privately. Proven by planting a resolver in
`board.py`, which failed the guard by name before the file was restored.

On its first run the guard corrected two assumptions written into the phase
status at open:

1. The phase counted **four** private resolutions. There are **five** spawning
   sites — `gitio.in_rewrite_state` was missed. This is the argument for
   writing the guard before the migration rather than after.
2. `signals.py` resolves the git directory privately **without** a subprocess,
   assuming `root/.git` is a directory. It never appeared in the profile
   because it is cheap, but it is wrong wherever `.git` is a file. A test
   creates a real linked worktree and pins both halves: the boundary resolves
   it correctly (finding the path under `worktrees/`), and `signals._git_dir`
   raises. That is a latent correctness bug found by performance work,
   recorded and pinned for WLA-28-02 rather than quietly repaired here.

The ledger is asserted in both directions — the guard fails on a new
undeclared resolver, and equally fails if the ledger names a site that no
longer offends. It cannot rot into a permanent exemption.

## Regression and floor proof

The full core suite runs **510 tests, OK** (499 before this story; the 11 new
cases are additions, nothing was weakened or removed). The module is exercised
on the declared **3.9 floor** with `/usr/bin/python3` 3.9.6, alongside
compileall, docs and canon lint, the source/vendor mirror `cmp`, rider docs
check, `update.sh --check`, `dw check`, and a whitespace check.

## Acceptance mapping

- One module owns the facts and is the only place resolving the git directory
  → `repofacts.py`; guard test proves no undeclared module does.
- Every fact classified with a reason → census test over all eight facts.
- Invalidation rule expressed in code → `Derivation` plus its four cases.
- Fitness test fails on a private resolver → planted `board.py` violation.
- No observable behavior change → 510/510 green, no test weakened.
- Documented where architecture material lives → `docs/architecture.md` §1.

## Proof

### Captured run — 2026-07-26T18:16:14Z

- **Command:** `bash -lc set -e
python3 -m unittest pmo-roadmap/tests/dw-core-tests.py
python3 -m unittest -v pmo-roadmap/tests/dw-core-tests.py -k RepositoryFactsContractTest
/usr/bin/python3 -c "import sys; sys.path.insert(0,'pmo-roadmap/lib'); import dw_pmo.repofacts as rf; print('floor 3.9 ok:', rf.contract_document()['kind'])"
python3 -m compileall -q pmo-roadmap/lib/dw_pmo
bash pmo-roadmap/tests/docs-lint.sh
bash pmo-roadmap/tests/canon-lint.sh
cmp pmo-roadmap/lib/dw_pmo/repofacts.py .githooks/dw_pmo/repofacts.py
.githooks/dw rider docs --check
bash pmo-roadmap/update.sh . --check
pmo-roadmap/bin/dw check work-log-automation
git diff --check`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 73324219348bc07d12a85f17f8ebdd9966bac96f

```text
dw hook: codex_hooks is explicitly false in /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.ipok6cx4/config.toml; respecting the opt-out
................................................................................................................................................................................................................................................dw-workbench: 127.0.0.1 "GET /api/runs/run-368c65394f6c96309535469f/events?follow=0 HTTP/1.1" 200 -
dw-workbench: 127.0.0.1 "GET /api/runs/run-368c65394f6c96309535469f/events?follow=0 HTTP/1.1" 200 -
dw-workbench: 127.0.0.1 "POST /api/runs/run-368c65394f6c96309535469f/events HTTP/1.1" 405 -
dw-workbench: 127.0.0.1 "GET /api/signals/events?remote=origin&branch=sse-x&follow=0 HTTP/1.1" 200 -
dw-workbench: 127.0.0.1 "GET /api/runs/run-000000000000000000000000/events?follow=0 HTTP/1.1" 400 -
......................................................................................................................................................dw-workbench: 127.0.0.1 "GET /api/programs/program-aed83526268eb0290b7d3367/events?from=0&follow=0 HTTP/1.1" 200 -
........................................................................................................................
----------------------------------------------------------------------
Ran 510 tests in 800.926s

OK
dw hook: claude — 4 installed, 0 already present in /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.gns_lueo/settings.json
dw hook: claude — 0 installed, 4 already present in /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.gns_lueo/settings.json
dw hook: claude — 4 installed, 0 already present in /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.yu5xnt8w/settings.json
dw hook: claude — 4 installed, 0 already present in /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.k3xb703h/settings.json
dw hook: claude — 4 removed from /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.k3xb703h/settings.json
test_a_derivation_refuses_to_hold_a_process_immutable_fact (pmo-roadmap.tests.dw-core-tests.RepositoryFactsContractTest) ... ok
test_contract_document_is_versioned_and_total (pmo-roadmap.tests.dw-core-tests.RepositoryFactsContractTest) ... ok
test_derivation_computes_once_and_a_mutation_invalidates (pmo-roadmap.tests.dw-core-tests.RepositoryFactsContractTest) ... ok
test_derivation_keys_facts_so_distinct_targets_do_not_collide (pmo-roadmap.tests.dw-core-tests.RepositoryFactsContractTest) ... ok
test_every_served_fact_declares_a_valid_class_and_reason (pmo-roadmap.tests.dw-core-tests.RepositoryFactsContractTest) ... ok
test_git_dir_resolves_and_refuses_a_non_repository (pmo-roadmap.tests.dw-core-tests.RepositoryFactsContractTest) ... ok
test_no_new_module_resolves_the_git_directory_privately (pmo-roadmap.tests.dw-core-tests.RepositoryFactsContractTest) ... ok
test_the_boundary_resolves_a_linked_worktree_where_git_is_a_file (pmo-roadmap.tests.dw-core-tests.RepositoryFactsContractTest) ... ok
test_the_pending_ledger_names_only_real_remaining_sites (pmo-roadmap.tests.dw-core-tests.RepositoryFactsContractTest) ... ok
test_the_split_is_exactly_where_the_phase_says_it_is (pmo-roadmap.tests.dw-core-tests.RepositoryFactsContractTest) ... ok
test_unknown_facts_are_refused_rather_than_defaulted (pmo-roadmap.tests.dw-core-tests.RepositoryFactsContractTest) ... ok

----------------------------------------------------------------------
Ran 11 tests in 0.184s

OK
floor 3.9 ok: delivery-workbench-repository-facts
docs-lint: ok (483 markdown files)
docs-lint.sh: ok (0s)
canon-lint.sh: ok
dw rider docs: all rendered surfaces match canon
update.sh: up to date (vendored rails match source v1.14.0)
dw check: ok
```
