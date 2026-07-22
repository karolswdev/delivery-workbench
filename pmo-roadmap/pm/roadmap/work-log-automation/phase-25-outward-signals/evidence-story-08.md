# Evidence - WLA-25-08

- **Story:** WLA-25-08 - Keep pending decisions alive across the pause
- **Status:** done
- **Date:** 2026-07-22

## Proof

The request port is now a durable ledger lifecycle rather than a transient UI
state:

- The existing hash-chained opening fact deterministically creates the
  `req-…` identity. Replay reconstructs the outstanding set at every ledger
  prefix; pause/resume and three restart passes preserve the original id and
  append at most one republish in each control generation.
- `request_republished`, `request_decided`, and content-free
  `request_refused` facts cover the rest of the lifecycle. Wrong correlation,
  wrong response enum, expiry, and terminal crash-prefix cleanup are all
  recorded without consuming a still-valid request or dispatching work.
- `dw run request` / `dw_run_request` / `POST /api/runs/request` share one
  exact-token core. The checkpoint alias is checkpoint-only, including when a
  valid nudge correlation coexists. Telegram routes the same typed response
  through that local boundary and never receives the token.
- CLI `run show`, the Workbench Run view, and the shared view model expose
  age, origin, schema, and outstanding count. The inspect-only decision tree
  binds decided history to the response event's `prev_hash`—the exact ledger
  head the human authorized. Read-time age is not signed token material.

Eight focused regressions raise the core suite 329 → 337. The captured battery
below passed all 337 tests on the local Python and the Python 3.9 floor, all
152 runnable Telegram tests (nine optional Pillow renders skipped), docs and
canon lint/snippets, MCP protocol and mutation parity, CLI/MCP/HTTP
orchestration interop, Workbench API/explorer plus 32 desktop/mobile renders,
the Python-3.9-built wheel and its guided/deliberate/multi-agent packaged exit
exams, plugin and generated-agent parity, vendored-rails parity, roadmap check,
and diff hygiene.

### Captured run — 2026-07-22T06:01:31Z

- **Command:** `bash -o pipefail -c
set -e
python3 pmo-roadmap/tests/dw-core-tests.py
/usr/bin/python3 pmo-roadmap/tests/dw-core-tests.py
python3 pmo-roadmap/tests/telegram-interface-tests.py
bash pmo-roadmap/tests/docs-lint.sh
bash pmo-roadmap/tests/docs-snippet-smoke.sh
bash pmo-roadmap/tests/canon-lint.sh
bash pmo-roadmap/tests/mcp-server.sh
bash pmo-roadmap/tests/orchestration-interop.sh
bash pmo-roadmap/tests/workbench-explorer.sh
bash pmo-roadmap/tests/workbench-ui-smoke.sh
bash pmo-roadmap/tests/package-smoke.sh
bash pmo-roadmap/tests/plugin-validate.sh
bash pmo-roadmap/tests/agent-surface.sh
./pmo-roadmap/update.sh . --check
./.githooks/dw check work-log-automation
git diff --check
`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 7a49eb40c984273371525d3b783e393223c21cdd

```text
test_codex_flag_opt_out_respected (__main__.AgentHooksTest.test_codex_flag_opt_out_respected) ... dw hook: codex_hooks is explicitly false in /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.hs8jeafe/config.toml; respecting the opt-out
ok
test_emit_never_raises_on_garbage (__main__.AgentHooksTest.test_emit_never_raises_on_garbage) ... ok
test_emit_quiet_guard_and_unknown_event (__main__.AgentHooksTest.test_emit_quiet_guard_and_unknown_event) ... ok
test_emit_whitelists_and_never_leaks_content (__main__.AgentHooksTest.test_emit_whitelists_and_never_leaks_content) ... ok
test_install_is_idempotent (__main__.AgentHooksTest.test_install_is_idempotent) ... ok
test_status_reports_per_event (__main__.AgentHooksTest.test_status_reports_per_event) ... ok
test_uninstall_is_surgical (__main__.AgentHooksTest.test_uninstall_is_surgical) ... ok
test_anchor_only_checked_for_markdown_targets (__main__.DocsLintTest.test_anchor_only_checked_for_markdown_targets) ... ok
test_duplicate_headings_get_numeric_suffixes (__main__.DocsLintTest.test_duplicate_headings_get_numeric_suffixes) ... ok
test_every_defect_class_is_caught (__main__.DocsLintTest.test_every_defect_class_is_caught) ... ok
test_github_slug_rules (__main__.DocsLintTest.test_github_slug_rules) ... ok
test_headings_inside_fences_are_not_anchors (__main__.DocsLintTest.test_headings_inside_fences_are_not_anchors) ... ok
test_ignore_pragmas (__main__.DocsLintTest.test_ignore_pragmas) ... ok
test_links_inside_code_are_not_linted (__main__.DocsLintTest.test_links_inside_code_are_not_linted) ... ok
test_snippet_extraction_names_attrs_and_body (__main__.DocsLintTest.test_snippet_extraction_names_attrs_and_body) ... ok
test_snippet_marker_without_fence_is_an_error (__main__.DocsLintTest.test_snippet_marker_without_fence_is_an_error) ... ok
test_valid_links_anchors_and_images_pass (__main__.DocsLintTest.test_valid_links_anchors_and_images_pass) ... ok
test_agent_docs_block_lifecycle (__main__.DwCoreTest.test_agent_docs_block_lifecycle) ... ok
test_apply_cycle_and_stale_refusal (__main__.DwCoreTest.test_apply_cycle_and_stale_refusal) ... ok
test_apply_refuses_tampered_intent (__main__.DwCoreTest.test_apply_refuses_tampered_intent) ... ok
test_apply_returns_changes_and_validation (__main__.DwCoreTest.test_apply_returns_changes_and_validation) ... ok
test_apply_rolls_back_on_write_failure (__main__.DwCoreTest.test_apply_rolls_back_on_write_failure) ... ok
test_bare_park_warns_never_errors (__main__.DwCoreTest.test_bare_park_warns_never_errors) ... ok
test_board_and_holds_carry_receipts_and_links (__main__.DwCoreTest.test_board_and_holds_carry_receipts_and_links) ... ok
test_board_bucketing_pinned (__main__.DwCoreTest.test_board_bucketing_pinned) ... ok
test_board_model_columns_and_receipts (__main__.DwCoreTest.test_board_model_columns_and_receipts) ... ok
test_board_render_paused_folds_and_truncation (__main__.DwCoreTest.test_board_render_paused_folds_and_truncation) ... ok
test_board_retired_rows_counted_not_shown (__main__.DwCoreTest.test_board_retired_rows_counted_not_shown) ... ok
test_builder_final_summary_spec_matches_generator (__main__.DwCoreTest.test_builder_final_summary_spec_matches_generator) ... ok
test_canon_cited_rule_ids_exist_in_gate (__main__.DwCoreTest.test_canon_cited_rule_ids_exist_in_gate) ... ok
test_canon_fence_boxes_match_contract_template (__main__.DwCoreTest.test_canon_fence_boxes_match_contract_template) ... ok
test_capture_appends_and_records (__main__.DwCoreTest.test_capture_appends_and_records) ... ok
test_capture_never_hands_stdin_to_the_child (__main__.DwCoreTest.test_capture_never_hands_stdin_to_the_child) ... ok
test_capture_truncation_marker (__main__.DwCoreTest.test_capture_truncation_marker) ... ok
test_captured_run_parse_survives_multiline_commands (__main__.DwCoreTest.test_captured_run_parse_survives_multiline_commands) ... ok
test_changelog_release_matches_version (__main__.DwCoreTest.test_changelog_release_matches_version) ... ok
test_check_broken (__main__.DwCoreTest.test_check_broken) ... ok
test_check_clean (__main__.DwCoreTest.test_check_clean) ... ok
test_check_flags_placeholder_evidence_for_done_story (__main__.DwCoreTest.test_check_flags_placeholder_evidence_for_done_story) ... ok
test_done_requires_evidence (__main__.DwCoreTest.test_done_requires_evidence) ... ok
test_dw_version_flag_single_source (__main__.DwCoreTest.test_dw_version_flag_single_source) ... ok
test_emitted_links_resolve_against_the_api (__main__.DwCoreTest.test_emitted_links_resolve_against_the_api) ... ok
test_evidence_content_lints (__main__.DwCoreTest.test_evidence_content_lints) ... ok
test_find_story_selectors (__main__.DwCoreTest.test_find_story_selectors) ... ok
test_formula_version_single_source (__main__.DwCoreTest.test_formula_version_single_source) ... ok
test_guard_lets_remediation_through (__main__.DwCoreTest.test_guard_lets_remediation_through) ... ok
test_handoff_summary_text (__main__.DwCoreTest.test_handoff_summary_text) ... ok
test_health_classifier_kinds (__main__.DwCoreTest.test_health_classifier_kinds) ... ok
test_health_report_shape_and_guard (__main__.DwCoreTest.test_health_report_shape_and_guard) ... ok
test_hold_reason_round_trip (__main__.DwCoreTest.test_hold_reason_round_trip) ... ok
test_hook_seam_explanations (__main__.DwCoreTest.test_hook_seam_explanations) ... ok
test_host_header_allowlist (__main__.DwCoreTest.test_host_header_allowlist) ... ok
test_interop_doc_names_every_surface (__main__.DwCoreTest.test_interop_doc_names_every_surface)
docs/interop.md is the read-surface contract; a new route, ... ok
test_missioncontrol_has_no_mutation_route (__main__.DwCoreTest.test_missioncontrol_has_no_mutation_route) ... ok
test_missioncontrol_live_layer_pins_only_on_story (__main__.DwCoreTest.test_missioncontrol_live_layer_pins_only_on_story) ... ok
test_missioncontrol_payload_carries_the_live_layer (__main__.DwCoreTest.test_missioncontrol_payload_carries_the_live_layer) ... ok
test_missioncontrol_readonly_fitness_guard (__main__.DwCoreTest.test_missioncontrol_readonly_fitness_guard) ... ok
test_missioncontrol_readonly_guard_catches_a_planted_write (__main__.DwCoreTest.test_missioncontrol_readonly_guard_catches_a_planted_write) ... ok
test_missioncontrol_route_serves_the_three_documents (__main__.DwCoreTest.test_missioncontrol_route_serves_the_three_documents) ... ok
test_missioncontrol_tail_clamps (__main__.DwCoreTest.test_missioncontrol_tail_clamps) ... ok
test_mutation_fingerprint_binds_content (__main__.DwCoreTest.test_mutation_fingerprint_binds_content) ... ok
test_mutation_preview_guarded_by_validation_issues (__main__.DwCoreTest.test_mutation_preview_guarded_by_validation_issues) ... ok
test_mutation_preview_maps_one_to_one_and_writes_nothing (__main__.DwCoreTest.test_mutation_preview_maps_one_to_one_and_writes_nothing) ... ok
test_mutation_preview_refusals (__main__.DwCoreTest.test_mutation_preview_refusals) ... ok
test_mutation_slug_injection_refused (__main__.DwCoreTest.test_mutation_slug_injection_refused) ... ok
test_narrative_only_warning (__main__.DwCoreTest.test_narrative_only_warning) ... ok
test_next_skips_parked_stories_and_paused_phases (__main__.DwCoreTest.test_next_skips_parked_stories_and_paused_phases) ... ok
test_noop_mutation_is_explicitly_idempotent (__main__.DwCoreTest.test_noop_mutation_is_explicitly_idempotent) ... ok
test_park_without_reason_refused (__main__.DwCoreTest.test_park_without_reason_refused) ... ok
test_parse_adoption_report (__main__.DwCoreTest.test_parse_adoption_report) ... ok
test_parse_adoption_report_malformed (__main__.DwCoreTest.test_parse_adoption_report_malformed) ... ok
test_parser_discovery (__main__.DwCoreTest.test_parser_discovery) ... ok
test_phase_create_and_close (__main__.DwCoreTest.test_phase_create_and_close) ... ok
test_phase_pause_and_resume_refusals (__main__.DwCoreTest.test_phase_pause_and_resume_refusals) ... ok
test_phase_pause_and_resume_round_trip (__main__.DwCoreTest.test_phase_pause_and_resume_round_trip) ... ok
test_phase_pause_inserts_bare_status_under_h1 (__main__.DwCoreTest.test_phase_pause_inserts_bare_status_under_h1) ... ok
test_plain_statuses_write_byte_identical (__main__.DwCoreTest.test_plain_statuses_write_byte_identical) ... ok
test_plugin_commands_match_installer_commands (__main__.DwCoreTest.test_plugin_commands_match_installer_commands) ... ok
test_plugin_skill_parity_with_managed_block (__main__.DwCoreTest.test_plugin_skill_parity_with_managed_block) ... ok
test_plugin_version_single_source (__main__.DwCoreTest.test_plugin_version_single_source) ... ok
test_preview_is_pure_and_idempotent (__main__.DwCoreTest.test_preview_is_pure_and_idempotent) ... ok
test_projected_issues_sees_the_future (__main__.DwCoreTest.test_projected_issues_sees_the_future) ... ok
test_pyproject_version_single_source_and_entry_point (__main__.DwCoreTest.test_pyproject_version_single_source_and_entry_point) ... ok
test_reason_composes_with_open_statuses_and_refuses_done (__main__.DwCoreTest.test_reason_composes_with_open_statuses_and_refuses_done) ... ok
test_run_adoption_preview_and_apply (__main__.DwCoreTest.test_run_adoption_preview_and_apply) ... ok
test_serve_fails_closed_without_roadmap (__main__.DwCoreTest.test_serve_fails_closed_without_roadmap) ... ok
test_stale_target_refused_without_partial_write (__main__.DwCoreTest.test_stale_target_refused_without_partial_write) ... ok
test_status_note_extraction (__main__.DwCoreTest.test_status_note_extraction) ... ok
test_status_vocabulary_validation (__main__.DwCoreTest.test_status_vocabulary_validation) ... ok
test_story_detail_carries_captured_runs (__main__.DwCoreTest.test_story_detail_carries_captured_runs) ... ok
test_story_detail_whole_and_absences (__main__.DwCoreTest.test_story_detail_whole_and_absences) ... ok
test_story_scaffold_matches_documented_template (__main__.DwCoreTest.test_story_scaffold_matches_documented_template) ... ok
test_story_timeline_chain_and_shipped (__main__.DwCoreTest.test_story_timeline_chain_and_shipped) ... ok
test_story_timeline_never_claims_unshipped (__main__.DwCoreTest.test_story_timeline_never_claims_unshipped) ... ok
test_story_timeline_work_log_only (__main__.DwCoreTest.test_story_timeline_work_log_only) ... ok
test_story_title_empty_file (__main__.DwCoreTest.test_story_title_empty_file) ... ok
test_story_vocabulary_doc_parity (__main__.DwCoreTest.test_story_vocabulary_doc_parity)
roadmap-builder §2.3 declares the vocabulary; the constants must match. ... ok
test_work_log_trace_fallback (__main__.DwCoreTest.test_work_log_trace_fallback) ... ok
test_workbench_api_view_models (__main__.DwCoreTest.test_workbench_api_view_models) ... ok
test_workbench_board_route (__main__.DwCoreTest.test_workbench_board_route) ... ok
test_workbench_file_endpoint_containment (__main__.DwCoreTest.test_workbench_file_endpoint_containment) ... ok
test_workbench_is_read_only (__main__.DwCoreTest.test_workbench_is_read_only) ... ok
test_workbench_pause_and_resume_mutations (__main__.DwCoreTest.test_workbench_pause_and_resume_mutations) ... ok
test_workbench_step_front_door_keeps_review_and_act_separate (__main__.DwCoreTest.test_workbench_step_front_door_keeps_review_and_act_separate) ... ok
test_workbench_story_route_serves_story_detail (__main__.DwCoreTest.test_workbench_story_route_serves_story_detail) ... ok
test_worklog_absent_root_is_optional_not_error (__main__.DwCoreTest.test_worklog_absent_root_is_optional_not_error) ... ok
test_worklog_endpoint_containment_and_omission (__main__.DwCoreTest.test_worklog_endpoint_containment_and_omission) ... ok
test_write_containment (__main__.DwCoreTest.test_write_containment) ... ok
test_append_only_and_never_raises (__main__.EventsTest.test_append_only_and_never_raises) ... ok
test_content_audit_rogue_keys_dropped (__main__.EventsTest.test_content_audit_rogue_keys_dropped) ... ok
test_gate_refusal_carries_its_rule (__main__.EventsTest.test_gate_refusal_carries_its_rule) ... ok
test_rail_moments_emit (__main__.EventsTest.test_rail_moments_emit) ... ok
test_canonical_header_maps_identically (__main__.FlagshipDialectTest.test_canonical_header_maps_identically) ... ok
test_decorated_done_counts_in_state_feed (__main__.FlagshipDialectTest.test_decorated_done_counts_in_state_feed) ... ok
test_decorated_statuses_do_not_mismatch (__main__.FlagshipDialectTest.test_decorated_statuses_do_not_mismatch) ... ok
test_done_row_with_no_receipt_still_errors (__main__.FlagshipDialectTest.test_done_row_with_no_receipt_still_errors) ... ok
test_file_only_evidence_vouched_by_header (__main__.FlagshipDialectTest.test_file_only_evidence_vouched_by_header) ... ok
test_flagship_fixture_reads_clean (__main__.FlagshipDialectTest.test_flagship_fixture_reads_clean) ... ok
test_four_column_decorated_table_parses (__main__.FlagshipDialectTest.test_four_column_decorated_table_parses) ... ok
test_genuine_mismatch_still_reported (__main__.FlagshipDialectTest.test_genuine_mismatch_still_reported) ... ok
test_next_story_none_when_only_closed_phases_have_open_rows (__main__.FlagshipDialectTest.test_next_story_none_when_only_closed_phases_have_open_rows) ... ok
test_next_story_skips_closed_phases (__main__.FlagshipDialectTest.test_next_story_skips_closed_phases) ... ok
test_normalize_status_pinned_mappings (__main__.FlagshipDialectTest.test_normalize_status_pinned_mappings) ... ok
test_planted_desyncs_still_fire (__main__.FlagshipDialectTest.test_planted_desyncs_still_fire) ... ok
test_pointer_absent_falls_back_to_next_story_phase (__main__.FlagshipDialectTest.test_pointer_absent_falls_back_to_next_story_phase) ... ok
test_pointer_names_current_phase_even_closed (__main__.FlagshipDialectTest.test_pointer_names_current_phase_even_closed) ... ok
test_struck_row_makes_no_demands (__main__.FlagshipDialectTest.test_struck_row_makes_no_demands) ... ok
test_tableless_phase_reads_from_files (__main__.FlagshipDialectTest.test_tableless_phase_reads_from_files) ... ok
test_added_orphan_evidence_blocked (__main__.GateTest.test_added_orphan_evidence_blocked) ... ok
test_atomicity_and_bundle_ok (__main__.GateTest.test_atomicity_and_bundle_ok) ... ok
test_branch_mismatch (__main__.GateTest.test_branch_mismatch) ... ok
test_capital_x_boxes_count (__main__.GateTest.test_capital_x_boxes_count) ... ok
test_digest_and_trailers (__main__.GateTest.test_digest_and_trailers) ... ok
test_doctor_detections_and_health (__main__.GateTest.test_doctor_detections_and_health) ... ok
test_evidence_deletion_orphaning_done_story_blocked (__main__.GateTest.test_evidence_deletion_orphaning_done_story_blocked) ... ok
test_evidence_deletion_with_regressed_story_passes (__main__.GateTest.test_evidence_deletion_with_regressed_story_passes) ... ok
test_expected_boxes_config_fallback_beats_env (__main__.GateTest.test_expected_boxes_config_fallback_beats_env) ... ok
test_facts_missing_on_v1_style_contract (__main__.GateTest.test_facts_missing_on_v1_style_contract) ... ok
test_forced_full_tier_config (__main__.GateTest.test_forced_full_tier_config) ... ok
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
test_short_tier_blocked_for_roadmap_commits (__main__.GateTest.test_short_tier_blocked_for_roadmap_commits) ... ok
test_short_tier_docs_only_passes (__main__.GateTest.test_short_tier_docs_only_passes) ... ok
test_story_declaration_enforced_for_flips (__main__.GateTest.test_story_declaration_enforced_for_flips) ... ok
test_story_timeline_with_git_and_work_log (__main__.GateTest.test_story_timeline_with_git_and_work_log) ... ok
test_synonym_status_counts_as_flip (__main__.GateTest.test_synonym_status_counts_as_flip) ... ok
test_tests_capture_discharge_and_tamper (__main__.GateTest.test_tests_capture_discharge_and_tamper) ... ok
test_unpadded_numbers_pair_both_ways (__main__.GateTest.test_unpadded_numbers_pair_both_ways) ... ok
test_work_log_dir_precedence (__main__.GateTest.test_work_log_dir_precedence) ... ok
test_worklog_preconditions (__main__.GateTest.test_worklog_preconditions) ... ok
test_payload_dir_resolves_checkout_layout (__main__.LauncherTest.test_payload_dir_resolves_checkout_layout) ... ok
test_repo_dw_found_only_in_adopted_repos (__main__.LauncherTest.test_repo_dw_found_only_in_adopted_repos) ... ok
test_vendored_version_parses_init (__main__.LauncherTest.test_vendored_version_parses_init) ... ok
test_browse_refusals_match_core (__main__.MCPServerTest.test_browse_refusals_match_core) ... ok
test_browse_tools_agree_with_core (__main__.MCPServerTest.test_browse_tools_agree_with_core) ... ok
test_browse_tools_are_read_only (__main__.MCPServerTest.test_browse_tools_are_read_only) ... ok
test_check_and_next_agree_with_core (__main__.MCPServerTest.test_check_and_next_agree_with_core) ... ok
test_core_refusal_becomes_tool_error (__main__.MCPServerTest.test_core_refusal_becomes_tool_error) ... ok
test_initialize_pins_protocol_version (__main__.MCPServerTest.test_initialize_pins_protocol_version) ... ok
test_mutation_tools_require_their_params (__main__.MCPServerTest.test_mutation_tools_require_their_params) ... ok
test_no_rails_is_a_discoverable_refusal (__main__.MCPServerTest.test_no_rails_is_a_discoverable_refusal) ... ok
test_notifications_get_no_reply_and_unknown_methods_error (__main__.MCPServerTest.test_notifications_get_no_reply_and_unknown_methods_error) ... ok
test_status_agrees_with_core_and_attention_is_data (__main__.MCPServerTest.test_status_agrees_with_core_and_attention_is_data) ... ok
test_step_tools_are_exact_core_adapters (__main__.MCPServerTest.test_step_tools_are_exact_core_adapters) ... ok
test_story_status_flip_writes_what_the_core_writes (__main__.MCPServerTest.test_story_status_flip_writes_what_the_core_writes) ... ok
test_story_status_refusal_matches_core (__main__.MCPServerTest.test_story_status_refusal_matches_core) ... ok
test_tools_list_matches_contract_and_excludes_attestation (__main__.MCPServerTest.test_tools_list_matches_contract_and_excludes_attestation) ... ok
test_unknown_tool_and_unknown_params (__main__.MCPServerTest.test_unknown_tool_and_unknown_params) ... ok
test_cli_invalid_score_returns_pointer_diagnostics_and_exit_one (__main__.OrchestrationCompilerTest.test_cli_invalid_score_returns_pointer_diagnostics_and_exit_one) ... ok
test_cli_list_show_validate_and_simulate_share_core_documents (__main__.OrchestrationCompilerTest.test_cli_list_show_validate_and_simulate_share_core_documents) ... ok
test_duplicate_json_keys_nonfinite_numbers_and_escaped_symlinks_refuse (__main__.OrchestrationCompilerTest.test_duplicate_json_keys_nonfinite_numbers_and_escaped_symlinks_refuse) ... ok
test_exact_keys_duplicate_ids_and_dangling_references_refuse (__main__.OrchestrationCompilerTest.test_exact_keys_duplicate_ids_and_dangling_references_refuse) ... ok
test_impossible_capabilities_and_forbidden_rail_authority_refuse (__main__.OrchestrationCompilerTest.test_impossible_capabilities_and_forbidden_rail_authority_refuse) ... ok
test_minimal_and_custom_role_round_trip (__main__.OrchestrationCompilerTest.test_minimal_and_custom_role_round_trip) ... ok
test_nudge_rule
[PMO_EVIDENCE_OUTPUT_TRUNCATED]
```
