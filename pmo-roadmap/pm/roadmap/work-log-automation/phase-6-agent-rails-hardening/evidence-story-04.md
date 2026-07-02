# Evidence - WLA-6-04

- **Story:** WLA-6-04 - Add evidence capture tooling and content linting
- **Status:** done
- **Date:** 2026-07-02

## What shipped

- `dw_pmo/evidence.py` + `dw evidence capture <project> <phase> <story>
  -- <command…>`: appends a machine-parseable
  `### Captured run — <UTC ts>` block (command, cwd, exit code,
  `git write-tree` index tree, fenced combined output, configurable
  byte cap with `[PMO_EVIDENCE_OUTPUT_TRUNCATED]` marker). Nonzero
  exits are recorded honestly and mirrored as the CLI exit code; the
  capture touches only the evidence file (created on first capture).
- Content lints: `dw check` now ERRORs on done-story evidence that
  still carries the generator placeholder or has an empty body, and on
  broken `assets/` references (the documented convention for
  screenshots/binaries: relative paths next to the evidence file,
  existence-checked). Done stories with narrative-only evidence (no
  captured run) are named in an aggregated warning surfaced via
  `dw context` — legal, but visible.
- Mechanical tests-ran discharge: `dw contract new --tests-capture
  <evidence-path>[#ts]` resolves a passing captured run from the
  STAGED evidence, stamps a `**Tests-ran capture:**` fact, and
  pre-checks the "Tests ran." box; the gate re-verifies at commit time
  (rule `contract-tests-capture-mismatch` on unstaged evidence,
  missing run, or nonzero exit).
- CLI plumbing: everything after a standalone `--` is passed through
  opaquely to the captured command (argparse REMAINDER would otherwise
  swallow flags — caught live during this story's smoke test and
  regression-covered).
- Docs: framework README evidence-capture section + porcelain rule id;
  PMO-CONTRACT.md rule 3 now points to the mechanical discharge.

The commit that ships this story is itself the proof of the discharge
path: its contract was generated with `--tests-capture` referencing the
first captured run below, so the "Tests ran." rule was verified by the
gate against this very file — the first mechanically-discharged rule in
the repo, and the first of the two Phase 6 evidence files the exit
criteria require to carry captured runs.

## Proof — captured runs (appended by `dw evidence capture`)

The blocks below were appended by the tool itself, unedited: the full
42-test unit suite (capture rendering, exit codes, truncation, lints,
discharge tamper matrix) and the 23-scenario gate parity suite
(including S22 discharge and S23 tampered-reference refusal).
Integration beyond these: `roadmap-cli.sh` gained the
capture/placeholder/asset lint section, `work-log-mvp.sh` and
`adoption-discovery.sh` pass unchanged, and `dw check
work-log-automation` stays green with the new lints active — proving
no existing evidence regressed.

### Captured run — 2026-07-02T16:05:08Z

- **Command:** `python3 pmo-roadmap/tests/dw-core-tests.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 3b6be870a68a2d5860fe1f3789caac19add4c683

```text
test_apply_returns_changes_and_validation (__main__.DwCoreTest.test_apply_returns_changes_and_validation) ... ok
test_capture_appends_and_records (__main__.DwCoreTest.test_capture_appends_and_records) ... ok
test_capture_truncation_marker (__main__.DwCoreTest.test_capture_truncation_marker) ... ok
test_check_broken (__main__.DwCoreTest.test_check_broken) ... ok
test_check_clean (__main__.DwCoreTest.test_check_clean) ... ok
test_check_flags_placeholder_evidence_for_done_story (__main__.DwCoreTest.test_check_flags_placeholder_evidence_for_done_story) ... ok
test_done_requires_evidence (__main__.DwCoreTest.test_done_requires_evidence) ... ok
test_evidence_content_lints (__main__.DwCoreTest.test_evidence_content_lints) ... ok
test_find_story_selectors (__main__.DwCoreTest.test_find_story_selectors) ... ok
test_narrative_only_warning (__main__.DwCoreTest.test_narrative_only_warning) ... ok
test_parser_discovery (__main__.DwCoreTest.test_parser_discovery) ... ok
test_phase_create_and_close (__main__.DwCoreTest.test_phase_create_and_close) ... ok
test_preview_is_pure_and_idempotent (__main__.DwCoreTest.test_preview_is_pure_and_idempotent) ... ok
test_stale_target_refused_without_partial_write (__main__.DwCoreTest.test_stale_target_refused_without_partial_write) ... ok
test_story_title_empty_file (__main__.DwCoreTest.test_story_title_empty_file) ... ok
test_work_log_trace_fallback (__main__.DwCoreTest.test_work_log_trace_fallback) ... ok
test_write_containment (__main__.DwCoreTest.test_write_containment) ... ok
test_added_orphan_evidence_blocked (__main__.GateTest.test_added_orphan_evidence_blocked) ... ok
test_atomicity_and_bundle_ok (__main__.GateTest.test_atomicity_and_bundle_ok) ... ok
test_branch_mismatch (__main__.GateTest.test_branch_mismatch) ... ok
test_capital_x_boxes_count (__main__.GateTest.test_capital_x_boxes_count) ... ok
test_digest_and_trailers (__main__.GateTest.test_digest_and_trailers) ... ok
test_evidence_deletion_orphaning_done_story_blocked (__main__.GateTest.test_evidence_deletion_orphaning_done_story_blocked) ... ok
test_evidence_deletion_with_regressed_story_passes (__main__.GateTest.test_evidence_deletion_with_regressed_story_passes) ... ok
test_expected_boxes_config_fallback_beats_env (__main__.GateTest.test_expected_boxes_config_fallback_beats_env) ... ok
test_facts_missing_on_v1_style_contract (__main__.GateTest.test_facts_missing_on_v1_style_contract) ... ok
test_head_mismatch_after_history_moves (__main__.GateTest.test_head_mismatch_after_history_moves) ... ok
test_index_tree_mismatch_and_touch_bypass_dead (__main__.GateTest.test_index_tree_mismatch_and_touch_bypass_dead) ... ok
test_invented_staged_sample_refused (__main__.GateTest.test_invented_staged_sample_refused) ... ok
test_missing_unchecked_and_count_fallback (__main__.GateTest.test_missing_unchecked_and_count_fallback) ... ok
test_modified_evidence_of_done_story_passes (__main__.GateTest.test_modified_evidence_of_done_story_passes) ... ok
test_orphan_evidence_deletion_passes (__main__.GateTest.test_orphan_evidence_deletion_passes) ... ok
test_paths_with_spaces (__main__.GateTest.test_paths_with_spaces) ... ok
test_porcelain_verbatim (__main__.GateTest.test_porcelain_verbatim) ... ok
test_rename_of_done_story_is_not_a_flip (__main__.GateTest.test_rename_of_done_story_is_not_a_flip) ... ok
test_rules_doc_titles_extension_and_tampering (__main__.GateTest.test_rules_doc_titles_extension_and_tampering) ... ok
test_story_declaration_enforced_for_flips (__main__.GateTest.test_story_declaration_enforced_for_flips) ... ok
test_synonym_status_counts_as_flip (__main__.GateTest.test_synonym_status_counts_as_flip) ... ok
test_tests_capture_discharge_and_tamper (__main__.GateTest.test_tests_capture_discharge_and_tamper) ... ok
test_unpadded_numbers_pair_both_ways (__main__.GateTest.test_unpadded_numbers_pair_both_ways) ... ok
test_work_log_dir_precedence (__main__.GateTest.test_work_log_dir_precedence) ... ok
test_worklog_preconditions (__main__.GateTest.test_worklog_preconditions) ... ok

----------------------------------------------------------------------
Ran 42 tests in 6.390s

OK
```

### Captured run — 2026-07-02T16:05:15Z

- **Command:** `pmo-roadmap/tests/gate-parity.sh`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 3b6be870a68a2d5860fe1f3789caac19add4c683

```text
gate-parity.sh: ok
```
