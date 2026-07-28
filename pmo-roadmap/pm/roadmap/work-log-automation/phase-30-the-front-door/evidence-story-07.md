# Evidence - WLA-30-07

- **Story:** WLA-30-07 - Scaffold a governed program
- **Status:** done
- **Date:** 2026-07-27

## Proof

`dw program scaffold --answers <file>` is a deterministic compiler
(`dw_pmo/program_scaffold.py`) from a closed typed answers object
(`delivery-workbench-program-scaffold-answers@1`: identity, scope
selector, implementer and verifier profile names, verification
expectations with at most one exact regression argv, size hints,
autonomy mode capped at checkpointed) to a complete governed bundle
embedded in an unsaved setup proposal: one program, one workflow, a
two-seat organization, check-bound rubrics whose mechanical fact ids
exactly match their producing check node ids (the attempt-7 lesson,
structural now), a local driver-binding fragment, one explicit repair
route, and a certified-handoff terminal. Safe by construction: the
capability request is five bits (program:select, agent:dispatch,
check:execute, workspace:write, verdict:issue) — commit, push, merge,
release, deploy, publish, arbitrary shell, and arbitrary network are
absent, versus the nine-capability hand-written Phase 29 bundle.
Budgets are formulas over story count, phase count, checks, complexity
weight, fan-out, repair rounds, and autonomy factor — no copied
constants — refusing at `/size` when a derivation would exceed a
contract limit. Refusal beats best-effort: same-family seats, missing
verifier, unknown checks, and underivable budgets all refuse with
JSON-pointer diagnostics. Every emitted bundle passes WLA-30-06
whole-bundle validation and pure simulation as an internal
post-condition (via new in-memory `bundle_documents` support in
`programs.py` — no temp files), and scaffolding writes nothing.
Golden fixtures: greenfield build, existing-project maintenance,
cross-provider cell, and a checked-in single-provider refusal.
Implementation by Sol (GPT-5.6) under orchestration in an isolated
worktree; ported to main and re-verified there.

Honest iteration: the first full-suite capture below exited 1 on the
real-repository symbol-map test — the orchestrator had staged the
worktree port's conflict-resolved test file before fixing a missing
close-paren, so the index briefly held an unparsable blob and the
derived map dropped its test links. Restaging the fixed file cleared
it; the final capture is the authoritative battery.

Captured runs, with the final battery authoritative: the **live demo** (this
repository's real roster: byte-identical double run, the
five-capability checkpointed bundle summarized, 12 of 24 budgets
responding to a size change, the same-seat refusal by name, and pm/
untouched), the **unit battery** (11 tests), and the **full core
suite** via `tests/run-core-tests.py` (final capture, machine-verified
exit code).

### Captured run — 2026-07-28T00:44:48Z

- **Command:** `bash /private/tmp/claude-501/-Users-karol-dev-code-delivery-workbench/c4dc647a-d1b5-41ba-83af-e7d70e987de9/scratchpad/demo-program-scaffold.sh`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 3683117d529dda2d30a22e32cb99ae4be814571e

```text
== deterministic: two runs, identical bytes ==
byte-identical across runs

== the generated bundle, summarized ==
proposal schema: delivery-workbench-setup-proposal@1 | state: draft
mode ceiling: checkpointed
requested capabilities: ['agent:dispatch', 'check:execute', 'program:select', 'verdict:issue', 'workspace:write']
excluded authority absent: commit/push/merge/release/deploy/publish
budget sample: {'max_agent_starts': 8, 'max_artifact_bytes': 24320000, 'max_check_starts': 4, 'max_child_runs': 8, 'max_commits': 1}

== budgets derive from size (small vs large differ) ==
budgets that changed with size: 12 of 24

== refusal over best-effort: same provider family on both seats ==
REFUSED: dw: /profiles/verifier: must name an independent verifier profile

== nothing was written by scaffolding ==
pm/ untouched: scaffold output lives only in the proposal

demo: ok
```

### Captured run — 2026-07-28T00:44:49Z

- **Command:** `/usr/bin/python3 pmo-roadmap/tests/program_scaffold_tests.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 3683117d529dda2d30a22e32cb99ae4be814571e

```text
test_closed_answers_default_checkpointed_and_pointer_refusals (__main__.ProgramScaffoldAnswersTest) ... ok
test_duplicate_json_keys_refuse (__main__.ProgramScaffoldAnswersTest) ... ok
test_unknown_check_and_argv_refuse (__main__.ProgramScaffoldAnswersTest) ... ok
test_budgets_change_with_shape_and_are_not_phase_29_copy (__main__.ProgramScaffoldCompilerTest) ... ok
test_deterministic_byte_identical_and_no_write (__main__.ProgramScaffoldCompilerTest) ... ok
test_named_profile_refusals_are_not_best_effort (__main__.ProgramScaffoldCompilerTest) ... ok
test_safe_capabilities_local_bindings_and_certified_terminal (__main__.ProgramScaffoldCompilerTest) ... ok
test_cli_emits_canonical_proposal_and_writes_nothing (__main__.ProgramScaffoldGoldenTest) ... ok
test_cross_provider_generated_bundle_is_simpler_than_phase_29 (__main__.ProgramScaffoldGoldenTest) ... ok
test_single_provider_golden_is_a_typed_refusal (__main__.ProgramScaffoldGoldenTest) ... ok
test_three_emitted_goldens_validate_and_simulate (__main__.ProgramScaffoldGoldenTest) ... ok

----------------------------------------------------------------------
Ran 11 tests in 0.602s

OK
```

### Captured run — 2026-07-28T00:45:00Z

- **Command:** `/usr/bin/python3 pmo-roadmap/tests/run-core-tests.py`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** 3683117d529dda2d30a22e32cb99ae4be814571e

```text

======================================================================
shard 5 output
======================================================================
..................................................................................
======================================================================
ERROR: test_real_core_tests_reference_sampled_dw_pmo_symbols (repository_map_tests.RealRepositoryMapTest) (symbol='build_status')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/Users/karol/dev/code/delivery-workbench/pmo-roadmap/tests/repository_map_tests.py", line 293, in test_real_core_tests_reference_sampled_dw_pmo_symbols
    self.assertTrue(expected & test_links[test_file])
KeyError: 'pmo-roadmap/tests/dw-core-tests.py'

======================================================================
ERROR: test_real_core_tests_reference_sampled_dw_pmo_symbols (repository_map_tests.RealRepositoryMapTest) (symbol='run_gate')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/Users/karol/dev/code/delivery-workbench/pmo-roadmap/tests/repository_map_tests.py", line 293, in test_real_core_tests_reference_sampled_dw_pmo_symbols
    self.assertTrue(expected & test_links[test_file])
KeyError: 'pmo-roadmap/tests/dw-core-tests.py'

======================================================================
ERROR: test_real_core_tests_reference_sampled_dw_pmo_symbols (repository_map_tests.RealRepositoryMapTest) (symbol='run_verify')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/Users/karol/dev/code/delivery-workbench/pmo-roadmap/tests/repository_map_tests.py", line 293, in test_real_core_tests_reference_sampled_dw_pmo_symbols
    self.assertTrue(expected & test_links[test_file])
KeyError: 'pmo-roadmap/tests/dw-core-tests.py'

======================================================================
ERROR: test_real_core_tests_reference_sampled_dw_pmo_symbols (repository_map_tests.RealRepositoryMapTest) (symbol='story_detail')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/Users/karol/dev/code/delivery-workbench/pmo-roadmap/tests/repository_map_tests.py", line 293, in test_real_core_tests_reference_sampled_dw_pmo_symbols
    self.assertTrue(expected & test_links[test_file])
KeyError: 'pmo-roadmap/tests/dw-core-tests.py'

----------------------------------------------------------------------
Ran 83 tests in 136.913s

FAILED (errors=4)
##shard-summary {"ran": 83, "failures": 0, "errors": 4, "skipped": 0}

run-core-tests: 666 units across 8 shards + 1 serial
  shard 0:  85 tests in  100.4s  ok
  shard 1:  89 tests in  101.0s  ok
  shard 2:  84 tests in  118.9s  ok
  shard 3:  86 tests in  112.0s  ok
  shard 4:  88 tests in  113.5s  ok
  shard 5:  83 tests in  137.1s  FAIL
  shard 6:  81 tests in  119.7s  ok
  shard 7:  81 tests in  117.8s  ok
  shard 8:   1 tests in    2.7s  ok
run-core-tests: 678 tests in 139.8s (FAILED)
```

### Captured run — 2026-07-28T00:47:48Z

- **Command:** `/usr/bin/python3 pmo-roadmap/tests/run-core-tests.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 27ceadfe02ebe48d31ff9900601a5c0d659d2ca0

```text
run-core-tests: 666 units across 8 shards + 1 serial
  shard 0:  85 tests in   85.5s  ok
  shard 1:  89 tests in   86.0s  ok
  shard 2:  84 tests in  103.1s  ok
  shard 3:  86 tests in   96.2s  ok
  shard 4:  88 tests in   98.8s  ok
  shard 5:  83 tests in  121.4s  ok
  shard 6:  81 tests in  103.7s  ok
  shard 7:  81 tests in  102.4s  ok
  shard 8:   1 tests in    2.3s  ok
run-core-tests: 678 tests in 123.8s (OK)
```
