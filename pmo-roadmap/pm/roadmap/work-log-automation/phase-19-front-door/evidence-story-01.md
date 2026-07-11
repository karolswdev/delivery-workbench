# Evidence - WLA-19-01

- **Story:** WLA-19-01 - The package states its case — metadata and community polish
- **Status:** done
- **Date:** 2026-07-11

## Proof

Three captured runs, all green, each proving one leg:

1. **19:31:23Z — the core suite** (208 tests OK): the metadata
   edits regress nothing; this is the run the commit contract's
   `--tests-capture` cites.
2. **19:31:44Z — `tests/package-smoke.sh`**: the distribution
   contract still holds end-to-end — sdist + wheel build, isolated
   install, bootstrap to doctor-green — with the new
   `setuptools>=77` build requirement on the 3.9-floor interpreter.
3. **19:32:05Z — the metadata proof**: a fresh wheel's METADATA
   shows `Metadata-Version: 2.4`, `License-Expression: MIT`,
   `License-File: LICENSE`, `Author-email: Karol Sane
   <karolsane@gmail.com>`, and all five Project-URLs (Homepage,
   Documentation, Repository, Changelog, Issues); LICENSE line 3
   reads "Karol Sane"; the README carries the three badges
   (validation workflow, PyPI version, MIT license).

Decision recorded in the story: the audit suggested the
`License :: OSI Approved :: MIT License` classifier, but the first
build warned that setuptools deprecates license classifiers and the
license TOML table (support ends 2027-02-18), so the story shipped
the SPDX expression instead — `license = "MIT"` +
`license-files = ["LICENSE"]`, `requires = ["setuptools>=77"]`.
The only remaining build warnings are the pre-existing benign
`*.pyc` MANIFEST notices.

### Captured run — 2026-07-11T19:31:23Z

- **Command:** `/usr/bin/python3 pmo-roadmap/tests/dw-core-tests.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 613e296704d766b33ff83d02d6df7ab902f7c580

```text
test_codex_flag_opt_out_respected (__main__.AgentHooksTest) ... dw hook: codex_hooks is explicitly false in /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.if1avdgr/config.toml; respecting the opt-out
ok
test_emit_never_raises_on_garbage (__main__.AgentHooksTest) ... ok
test_emit_quiet_guard_and_unknown_event (__main__.AgentHooksTest) ... ok
test_emit_whitelists_and_never_leaks_content (__main__.AgentHooksTest) ... ok
test_install_is_idempotent (__main__.AgentHooksTest) ... ok
test_status_reports_per_event (__main__.AgentHooksTest) ... ok
test_uninstall_is_surgical (__main__.AgentHooksTest) ... ok
test_anchor_only_checked_for_markdown_targets (__main__.DocsLintTest) ... ok
test_duplicate_headings_get_numeric_suffixes (__main__.DocsLintTest) ... ok
test_every_defect_class_is_caught (__main__.DocsLintTest) ... ok
test_github_slug_rules (__main__.DocsLintTest) ... ok
test_headings_inside_fences_are_not_anchors (__main__.DocsLintTest) ... ok
test_ignore_pragmas (__main__.DocsLintTest) ... ok
test_links_inside_code_are_not_linted (__main__.DocsLintTest) ... ok
test_snippet_extraction_names_attrs_and_body (__main__.DocsLintTest) ... ok
test_snippet_marker_without_fence_is_an_error (__main__.DocsLintTest) ... ok
test_valid_links_anchors_and_images_pass (__main__.DocsLintTest) ... ok
test_agent_docs_block_lifecycle (__main__.DwCoreTest) ... ok
test_apply_cycle_and_stale_refusal (__main__.DwCoreTest) ... ok
test_apply_refuses_tampered_intent (__main__.DwCoreTest) ... ok
test_apply_returns_changes_and_validation (__main__.DwCoreTest) ... ok
test_apply_rolls_back_on_write_failure (__main__.DwCoreTest) ... ok
test_bare_park_warns_never_errors (__main__.DwCoreTest) ... ok
test_board_and_holds_carry_receipts_and_links (__main__.DwCoreTest) ... ok
test_board_bucketing_pinned (__main__.DwCoreTest) ... ok
test_board_model_columns_and_receipts (__main__.DwCoreTest) ... ok
test_board_render_paused_folds_and_truncation (__main__.DwCoreTest) ... ok
test_board_retired_rows_counted_not_shown (__main__.DwCoreTest) ... ok
test_builder_final_summary_spec_matches_generator (__main__.DwCoreTest) ... ok
test_canon_cited_rule_ids_exist_in_gate (__main__.DwCoreTest) ... ok
test_canon_fence_boxes_match_contract_template (__main__.DwCoreTest) ... ok
test_capture_appends_and_records (__main__.DwCoreTest) ... ok
test_capture_never_hands_stdin_to_the_child (__main__.DwCoreTest) ... ok
test_capture_truncation_marker (__main__.DwCoreTest) ... ok
test_captured_run_parse_survives_multiline_commands (__main__.DwCoreTest) ... ok
test_changelog_release_matches_version (__main__.DwCoreTest) ... ok
test_check_broken (__main__.DwCoreTest) ... ok
test_check_clean (__main__.DwCoreTest) ... ok
test_check_flags_placeholder_evidence_for_done_story (__main__.DwCoreTest) ... ok
test_done_requires_evidence (__main__.DwCoreTest) ... ok
test_dw_version_flag_single_source (__main__.DwCoreTest) ... ok
test_emitted_links_resolve_against_the_api (__main__.DwCoreTest) ... ok
test_evidence_content_lints (__main__.DwCoreTest) ... ok
test_find_story_selectors (__main__.DwCoreTest) ... ok
test_formula_version_single_source (__main__.DwCoreTest) ... ok
test_guard_lets_remediation_through (__main__.DwCoreTest) ... ok
test_handoff_summary_text (__main__.DwCoreTest) ... ok
test_health_classifier_kinds (__main__.DwCoreTest) ... ok
test_health_report_shape_and_guard (__main__.DwCoreTest) ... ok
test_hold_reason_round_trip (__main__.DwCoreTest) ... ok
test_hook_seam_explanations (__main__.DwCoreTest) ... ok
test_host_header_allowlist (__main__.DwCoreTest) ... ok
test_interop_doc_names_every_surface (__main__.DwCoreTest)
docs/interop.md is the read-surface contract; a new route, ... ok
test_missioncontrol_has_no_mutation_route (__main__.DwCoreTest) ... ok
test_missioncontrol_live_layer_pins_only_on_story (__main__.DwCoreTest) ... ok
test_missioncontrol_payload_carries_the_live_layer (__main__.DwCoreTest) ... ok
test_missioncontrol_readonly_fitness_guard (__main__.DwCoreTest) ... ok
test_missioncontrol_readonly_guard_catches_a_planted_write (__main__.DwCoreTest) ... ok
test_missioncontrol_route_serves_the_three_documents (__main__.DwCoreTest) ... ok
test_missioncontrol_tail_clamps (__main__.DwCoreTest) ... ok
test_mutation_fingerprint_binds_content (__main__.DwCoreTest) ... ok
test_mutation_preview_guarded_by_validation_issues (__main__.DwCoreTest) ... ok
test_mutation_preview_maps_one_to_one_and_writes_nothing (__main__.DwCoreTest) ... ok
test_mutation_preview_refusals (__main__.DwCoreTest) ... ok
test_mutation_slug_injection_refused (__main__.DwCoreTest) ... ok
test_narrative_only_warning (__main__.DwCoreTest) ... ok
test_next_skips_parked_stories_and_paused_phases (__main__.DwCoreTest) ... ok
test_noop_mutation_is_explicitly_idempotent (__main__.DwCoreTest) ... ok
test_park_without_reason_refused (__main__.DwCoreTest) ... ok
test_parse_adoption_report (__main__.DwCoreTest) ... ok
test_parse_adoption_report_malformed (__main__.DwCoreTest) ... ok
test_parser_discovery (__main__.DwCoreTest) ... ok
test_phase_create_and_close (__main__.DwCoreTest) ... ok
test_phase_pause_and_resume_refusals (__main__.DwCoreTest) ... ok
test_phase_pause_and_resume_round_trip (__main__.DwCoreTest) ... ok
test_phase_pause_inserts_bare_status_under_h1 (__main__.DwCoreTest) ... ok
test_plain_statuses_write_byte_identical (__main__.DwCoreTest) ... ok
test_plugin_commands_match_installer_commands (__main__.DwCoreTest) ... ok
test_plugin_skill_parity_with_managed_block (__main__.DwCoreTest) ... ok
test_plugin_version_single_source (__main__.DwCoreTest) ... ok
test_preview_is_pure_and_idempotent (__main__.DwCoreTest) ... ok
test_projected_issues_sees_the_future (__main__.DwCoreTest) ... ok
test_pyproject_version_single_source_and_entry_point (__main__.DwCoreTest) ... ok
test_reason_composes_with_open_statuses_and_refuses_done (__main__.DwCoreTest) ... ok
test_run_adoption_preview_and_apply (__main__.DwCoreTest) ... ok
test_serve_fails_closed_without_roadmap (__main__.DwCoreTest) ... ok
test_stale_target_refused_without_partial_write (__main__.DwCoreTest) ... ok
test_status_note_extraction (__main__.DwCoreTest) ... ok
test_status_vocabulary_validation (__main__.DwCoreTest) ... ok
test_story_detail_carries_captured_runs (__main__.DwCoreTest) ... ok
test_story_detail_whole_and_absences (__main__.DwCoreTest) ... ok
test_story_scaffold_matches_documented_template (__main__.DwCoreTest) ... ok
test_story_timeline_chain_and_shipped (__main__.DwCoreTest) ... ok
test_story_timeline_never_claims_unshipped (__main__.DwCoreTest) ... ok
test_story_timeline_work_log_only (__main__.DwCoreTest) ... ok
test_story_title_empty_file (__main__.DwCoreTest) ... ok
test_story_vocabulary_doc_parity (__main__.DwCoreTest)
roadmap-builder §2.3 declares the vocabulary; the constants must match. ... ok
test_work_log_trace_fallback (__main__.DwCoreTest) ... ok
test_workbench_api_view_models (__main__.DwCoreTest) ... ok
test_workbench_board_route (__main__.DwCoreTest) ... ok
test_workbench_file_endpoint_containment (__main__.DwCoreTest) ... ok
test_workbench_is_read_only (__main__.DwCoreTest) ... ok
test_workbench_pause_and_resume_mutations (__main__.DwCoreTest) ... ok
test_workbench_story_route_serves_story_detail (__main__.DwCoreTest) ... ok
test_worklog_absent_root_is_optional_not_error (__main__.DwCoreTest) ... ok
test_worklog_endpoint_containment_and_omission (__main__.DwCoreTest) ... ok
test_write_containment (__main__.DwCoreTest) ... ok
test_append_only_and_never_raises (__main__.EventsTest) ... ok
test_content_audit_rogue_keys_dropped (__main__.EventsTest) ... ok
test_gate_refusal_carries_its_rule (__main__.EventsTest) ... ok
test_rail_moments_emit (__main__.EventsTest) ... ok
test_canonical_header_maps_identically (__main__.FlagshipDialectTest) ... ok
test_decorated_done_counts_in_state_feed (__main__.FlagshipDialectTest) ... ok
test_decorated_statuses_do_not_mismatch (__main__.FlagshipDialectTest) ... ok
test_done_row_with_no_receipt_still_errors (__main__.FlagshipDialectTest) ... ok
test_file_only_evidence_vouched_by_header (__main__.FlagshipDialectTest) ... ok
test_flagship_fixture_reads_clean (__main__.FlagshipDialectTest) ... ok
test_four_column_decorated_table_parses (__main__.FlagshipDialectTest) ... ok
test_genuine_mismatch_still_reported (__main__.FlagshipDialectTest) ... ok
test_next_story_none_when_only_closed_phases_have_open_rows (__main__.FlagshipDialectTest) ... ok
test_next_story_skips_closed_phases (__main__.FlagshipDialectTest) ... ok
test_normalize_status_pinned_mappings (__main__.FlagshipDialectTest) ... ok
test_planted_desyncs_still_fire (__main__.FlagshipDialectTest) ... ok
test_pointer_absent_falls_back_to_next_story_phase (__main__.FlagshipDialectTest) ... ok
test_pointer_names_current_phase_even_closed (__main__.FlagshipDialectTest) ... ok
test_struck_row_makes_no_demands (__main__.FlagshipDialectTest) ... ok
test_tableless_phase_reads_from_files (__main__.FlagshipDialectTest) ... ok
test_added_orphan_evidence_blocked (__main__.GateTest) ... ok
test_atomicity_and_bundle_ok (__main__.GateTest) ... ok
test_branch_mismatch (__main__.GateTest) ... ok
test_capital_x_boxes_count (__main__.GateTest) ... ok
test_digest_and_trailers (__main__.GateTest) ... ok
test_doctor_detections_and_health (__main__.GateTest) ... ok
test_evidence_deletion_orphaning_done_story_blocked (__main__.GateTest) ... ok
test_evidence_deletion_with_regressed_story_passes (__main__.GateTest) ... ok
test_expected_boxes_config_fallback_beats_env (__main__.GateTest) ... ok
test_facts_missing_on_v1_style_contract (__main__.GateTest) ... ok
test_forced_full_tier_config (__main__.GateTest) ... ok
test_head_mismatch_after_history_moves (__main__.GateTest) ... ok
test_index_tree_mismatch_and_touch_bypass_dead (__main__.GateTest) ... ok
test_invented_staged_sample_refused (__main__.GateTest) ... ok
test_missing_unchecked_and_count_fallback (__main__.GateTest) ... ok
test_modified_evidence_of_done_story_passes (__main__.GateTest) ... ok
test_orphan_evidence_deletion_passes (__main__.GateTest) ... ok
test_paths_with_spaces (__main__.GateTest) ... ok
test_porcelain_verbatim (__main__.GateTest) ... ok
test_rename_of_done_story_is_not_a_flip (__main__.GateTest) ... ok
test_rules_doc_titles_extension_and_tampering (__main__.GateTest) ... ok
test_short_tier_blocked_for_roadmap_commits (__main__.GateTest) ... ok
test_short_tier_docs_only_passes (__main__.GateTest) ... ok
test_story_declaration_enforced_for_flips (__main__.GateTest) ... ok
test_story_timeline_with_git_and_work_log (__main__.GateTest) ... ok
test_synonym_status_counts_as_flip (__main__.GateTest) ... ok
test_tests_capture_discharge_and_tamper (__main__.GateTest) ... ok
test_unpadded_numbers_pair_both_ways (__main__.GateTest) ... ok
test_work_log_dir_precedence (__main__.GateTest) ... ok
test_worklog_preconditions (__main__.GateTest) ... ok
test_payload_dir_resolves_checkout_layout (__main__.LauncherTest) ... ok
test_repo_dw_found_only_in_adopted_repos (__main__.LauncherTest) ... ok
test_vendored_version_parses_init (__main__.LauncherTest) ... ok
test_browse_refusals_match_core (__main__.MCPServerTest) ... ok
test_browse_tools_agree_with_core (__main__.MCPServerTest) ... ok
test_browse_tools_are_read_only (__main__.MCPServerTest) ... ok
test_check_and_next_agree_with_core (__main__.MCPServerTest) ... ok
test_core_refusal_becomes_tool_error (__main__.MCPServerTest) ... ok
test_initialize_pins_protocol_version (__main__.MCPServerTest) ... ok
test_mutation_tools_require_their_params (__main__.MCPServerTest) ... ok
test_no_rails_is_a_discoverable_refusal (__main__.MCPServerTest) ... ok
test_notifications_get_no_reply_and_unknown_methods_error (__main__.MCPServerTest) ... ok
test_story_status_flip_writes_what_the_core_writes (__main__.MCPServerTest) ... ok
test_story_status_refusal_matches_core (__main__.MCPServerTest) ... ok
test_tools_list_matches_contract_and_excludes_attestation (__main__.MCPServerTest) ... ok
test_unknown_tool_and_unknown_params (__main__.MCPServerTest) ... ok
test_agents_md_gets_the_agents_variant (__main__.RiderDocsTest) ... ok
test_agents_transformations_actually_fire (__main__.RiderDocsTest) ... ok
test_codex_and_pi_share_agents_md_without_conflict (__main__.RiderDocsTest) ... ok
test_codex_installer_is_idempotent (__main__.RiderDocsTest) ... ok
test_codex_skill_drift_is_a_check_error (__main__.RiderDocsTest) ... ok
test_codex_skill_renders_frontmatter_and_body (__main__.RiderDocsTest) ... ok
test_doctor_riders_wired_absent_and_broken (__main__.RiderDocsTest) ... ok
test_embedded_specs_match_source_canon (__main__.RiderDocsTest) ... ok
test_hand_edited_copy_is_a_check_error (__main__.RiderDocsTest) ... ok
test_hand_edited_doc_block_is_a_check_error (__main__.RiderDocsTest) ... ok
test_hs_context_block_lifecycle (__main__.RiderDocsTest) ... ok
test_pi_installer_is_idempotent (__main__.RiderDocsTest) ... ok
test_pi_prompt_drift_is_a_check_error (__main__.RiderDocsTest) ... ok
test_pi_prompt_is_verbatim_canon_and_pure (__main__.RiderDocsTest) ... ok
test_real_tree_matches_canon (__main__.RiderDocsTest) ... ok
test_regeneration_is_idempotent (__main__.RiderDocsTest) ... ok
test_all_outcomes (__main__.SessionsTest) ... ok
test_registry_failure_shapes (__main__.SessionsTest) ... ok
test_feed_reflects_real_state (__main__.StateFeedTest) ... ok
test_schema_is_pinned (__main__.StateFeedTest) ... ok
test_write_emits_the_same_document (__main__.StateFeedTest) ... ok
test_bundled_double_flip_with_trailer_passes (__main__.VerifyTest) ... ok
test_clean_flip_with_trailers_passes (__main__.VerifyTest) ... ok
test_double_flip_without_bundle_fails_atomicity (__main__.VerifyTest) ... ok
test_errors_exit_via_error_field (__main__.VerifyTest) ... ok
test_every_rederivable_rule_id_is_a_gate_rule_or_remote_only (__main__.VerifyTest) ... ok
test_evidence_deletion_orphans_done_story (__main__.VerifyTest) ... ok
test_flip_not_declared_in_story_trailer (__main__.VerifyTest) ... ok
test_malformed_digest_and_story_id (__main__.VerifyTest) ... ok
test_merge_commits_are_out_of_scope (__main__.VerifyTest) ... ok
test_non_roadmap_commits_are_out_of_scope (__main__.VerifyTest) ... ok
test_orphan_evidence_added_without_flip (__main__.VerifyTest) ... ok
test_pre_epoch_commits_are_skipped_not_flagged (__main__.VerifyTest) ... ok
test_render_grammar (__main__.VerifyTest) ... ok
test_smuggled_flip_names_missing_trailer_and_evidence (__main__.VerifyTest) ... ok

----------------------------------------------------------------------
Ran 208 tests in 15.053s

OK
dw hook: claude — 4 installed, 0 already present in /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.p0sxjwgm/settings.json
dw hook: claude — 0 installed, 4 already present in /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.p0sxjwgm/settings.json
dw hook: claude — 4 installed, 0 already present in /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.57ozzt5u/settings.json
dw hook: claude — 4 installed, 0 already present in /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.k5rizr1s/settings.json
dw hook: claude — 4 removed from /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.k5rizr1s/settings.json
```

### Captured run — 2026-07-11T19:31:44Z

- **Command:** `bash pmo-roadmap/tests/package-smoke.sh`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 613e296704d766b33ff83d02d6df7ab902f7c580

```text
package-smoke.sh: skipping unhealthy interpreter: python3
package-smoke.sh: building with: /usr/bin/python3 (Python 3.9.6)
* Creating isolated environment: venv+pip...
* Installing packages in isolated environment:
  - setuptools>=77
* Getting build dependencies for sdist...
warning: no previously-included files matching '*.pyc' found anywhere in distribution
* Building sdist...
warning: no previously-included files matching '*.pyc' found anywhere in distribution
* Building wheel from sdist
* Creating isolated environment: venv+pip...
* Installing packages in isolated environment:
  - setuptools>=77
* Getting build dependencies for wheel...
warning: no previously-included files matching '__pycache__/*' found anywhere in distribution
warning: no previously-included files matching '*.pyc' found anywhere in distribution
* Building wheel...
warning: no previously-included files matching '__pycache__/*' found anywhere in distribution
warning: no previously-included files matching '*.pyc' found anywhere in distribution
package-smoke.sh: built delivery_workbench-1.12.0-py3-none-any.whl and delivery_workbench-1.12.0.tar.gz
package-smoke.sh: pipx cannot create environments here; falling back to venv+pip
WARNING: You are using pip version 21.2.4; however, version 26.0.1 is available.
You should consider upgrading via the '/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/pmo-package-smoke.498Zyx/appenv/bin/python -m pip install --upgrade pip' command.
package-smoke.sh: installed via venv+pip
package-smoke.sh: ok
```

### Captured run — 2026-07-11T19:32:05Z

- **Command:** `bash -c set -e; TMP=$(mktemp -d); /usr/bin/python3 -m venv "$TMP/venv"; "$TMP/venv/bin/python" -m pip install --quiet --upgrade pip build; "$TMP/venv/bin/python" -m build --wheel --outdir "$TMP/dist" . >/dev/null 2>&1; WHL=$(ls "$TMP"/dist/*.whl); echo "wheel: $(basename "$WHL")"; unzip -p "$WHL" "*.dist-info/METADATA" | grep -E "^(Metadata-Version|License-Expression|License-File|Author-email|Project-URL)"; echo "--- LICENSE holder ---"; grep -n "Copyright" LICENSE; echo "--- README badges ---"; grep -nE "badge.svg|img.shields.io" README.md`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 613e296704d766b33ff83d02d6df7ab902f7c580

```text
wheel: delivery_workbench-1.12.0-py3-none-any.whl
Metadata-Version: 2.4
Author-email: Karol Sane <karolsane@gmail.com>
License-Expression: MIT
Project-URL: Homepage, https://github.com/karolswdev/delivery-workbench
Project-URL: Documentation, https://github.com/karolswdev/delivery-workbench/tree/main/docs
Project-URL: Repository, https://github.com/karolswdev/delivery-workbench
Project-URL: Changelog, https://github.com/karolswdev/delivery-workbench/blob/main/CHANGELOG.md
Project-URL: Issues, https://github.com/karolswdev/delivery-workbench/issues
License-File: LICENSE
--- LICENSE holder ---
3:Copyright (c) 2026 Karol Sane
--- README badges ---
3:[![validation](https://github.com/karolswdev/delivery-workbench/actions/workflows/validation.yml/badge.svg)](https://github.com/karolswdev/delivery-workbench/actions/workflows/validation.yml)
4:[![PyPI](https://img.shields.io/pypi/v/delivery-workbench)](https://pypi.org/project/delivery-workbench/)
5:[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](./LICENSE)
```
