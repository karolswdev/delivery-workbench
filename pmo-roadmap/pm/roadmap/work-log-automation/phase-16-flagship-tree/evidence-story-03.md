# Evidence - WLA-16-03

- **Story:** WLA-16-03 - The README pointer drives current phase; next-story skips closed phases
- **Status:** done
- **Date:** 2026-07-07

## Proof

### Captured run — 2026-07-08T01:17:10Z

- **Command:** `python3 pmo-roadmap/tests/dw-core-tests.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** f9493b40bcf6e653a9b542123f2ed0995a2a977d

```text
test_codex_flag_opt_out_respected (__main__.AgentHooksTest.test_codex_flag_opt_out_respected) ... dw hook: codex_hooks is explicitly false in /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.wv2bmlzu/config.toml; respecting the opt-out
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
test_evidence_content_lints (__main__.DwCoreTest.test_evidence_content_lints) ... ok
test_find_story_selectors (__main__.DwCoreTest.test_find_story_selectors) ... ok
test_formula_version_single_source (__main__.DwCoreTest.test_formula_version_single_source) ... ok
test_guard_lets_remediation_through (__main__.DwCoreTest.test_guard_lets_remediation_through) ... ok
test_handoff_summary_text (__main__.DwCoreTest.test_handoff_summary_text) ... ok
test_health_classifier_kinds (__main__.DwCoreTest.test_health_classifier_kinds) ... ok
test_health_report_shape_and_guard (__main__.DwCoreTest.test_health_report_shape_and_guard) ... ok
test_hook_seam_explanations (__main__.DwCoreTest.test_hook_seam_explanations) ... ok
test_host_header_allowlist (__main__.DwCoreTest.test_host_header_allowlist) ... ok
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
test_noop_mutation_is_explicitly_idempotent (__main__.DwCoreTest.test_noop_mutation_is_explicitly_idempotent) ... ok
test_parse_adoption_report (__main__.DwCoreTest.test_parse_adoption_report) ... ok
test_parse_adoption_report_malformed (__main__.DwCoreTest.test_parse_adoption_report_malformed) ... ok
test_parser_discovery (__main__.DwCoreTest.test_parser_discovery) ... ok
test_phase_create_and_close (__main__.DwCoreTest.test_phase_create_and_close) ... ok
test_plugin_commands_match_installer_commands (__main__.DwCoreTest.test_plugin_commands_match_installer_commands) ... ok
test_plugin_skill_parity_with_managed_block (__main__.DwCoreTest.test_plugin_skill_parity_with_managed_block) ... ok
test_plugin_version_single_source (__main__.DwCoreTest.test_plugin_version_single_source) ... ok
test_preview_is_pure_and_idempotent (__main__.DwCoreTest.test_preview_is_pure_and_idempotent) ... ok
test_projected_issues_sees_the_future (__main__.DwCoreTest.test_projected_issues_sees_the_future) ... ok
test_pyproject_version_single_source_and_entry_point (__main__.DwCoreTest.test_pyproject_version_single_source_and_entry_point) ... ok
test_run_adoption_preview_and_apply (__main__.DwCoreTest.test_run_adoption_preview_and_apply) ... ok
test_serve_fails_closed_without_roadmap (__main__.DwCoreTest.test_serve_fails_closed_without_roadmap) ... ok
test_stale_target_refused_without_partial_write (__main__.DwCoreTest.test_stale_target_refused_without_partial_write) ... ok
test_status_vocabulary_validation (__main__.DwCoreTest.test_status_vocabulary_validation) ... ok
test_story_scaffold_matches_documented_template (__main__.DwCoreTest.test_story_scaffold_matches_documented_template) ... ok
test_story_timeline_chain_and_shipped (__main__.DwCoreTest.test_story_timeline_chain_and_shipped) ... ok
test_story_timeline_never_claims_unshipped (__main__.DwCoreTest.test_story_timeline_never_claims_unshipped) ... ok
test_story_timeline_work_log_only (__main__.DwCoreTest.test_story_timeline_work_log_only) ... ok
test_story_title_empty_file (__main__.DwCoreTest.test_story_title_empty_file) ... ok
test_story_vocabulary_doc_parity (__main__.DwCoreTest.test_story_vocabulary_doc_parity)
roadmap-builder §2.3 declares the vocabulary; the constants must match. ... ok
test_work_log_trace_fallback (__main__.DwCoreTest.test_work_log_trace_fallback) ... ok
test_workbench_api_view_models (__main__.DwCoreTest.test_workbench_api_view_models) ... ok
test_workbench_file_endpoint_containment (__main__.DwCoreTest.test_workbench_file_endpoint_containment) ... ok
test_workbench_is_read_only (__main__.DwCoreTest.test_workbench_is_read_only) ... ok
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
test_normalize_status_pinned_mappings (__main__.FlagshipDialectTest.test_normalize_status_pinned_mappings) ... /Users/karol/dev/reusable-processes/pmo-roadmap/lib/dw_pmo/model.py:69: DeprecationWarning: 'maxsplit' is passed as positional argument
  s = re.split(r"[(—–:;,.!]", s, 1)[0].strip()
ok
test_planted_desyncs_still_fire (__main__.FlagshipDialectTest.test_planted_desyncs_still_fire) ... ok
test_pointer_absent_falls_back_to_next_story_phase (__main__.FlagshipDialectTest.test_pointer_absent_falls_back_to_next_story_phase) ... ok
test_pointer_names_current_phase_even_closed (__main__.FlagshipDialectTest.test_pointer_names_current_phase_even_closed) ... ok
test_struck_row_makes_no_demands (__main__.FlagshipDialectTest.test_struck_row_makes_no_demands) ... /Users/karol/dev/reusable-processes/pmo-roadmap/lib/dw_pmo/model.py:69: DeprecationWarning: 'maxsplit' is passed as positional argument
  s = re.split(r"[(—–:;,.!]", s, 1)[0].strip()
/Users/karol/dev/reusable-processes/pmo-roadmap/lib/dw_pmo/model.py:69: DeprecationWarning: 'maxsplit' is passed as positional argument
  s = re.split(r"[(—–:;,.!]", s, 1)[0].strip()
ok
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
test_check_and_next_agree_with_core (__main__.MCPServerTest.test_check_and_next_agree_with_core) ... ok
test_core_refusal_becomes_tool_error (__main__.MCPServerTest.test_core_refusal_becomes_tool_error) ... ok
test_initialize_pins_protocol_version (__main__.MCPServerTest.test_initialize_pins_protocol_version) ... ok
test_mutation_tools_require_their_params (__main__.MCPServerTest.test_mutation_tools_require_their_params) ... ok
test_no_rails_is_a_discoverable_refusal (__main__.MCPServerTest.test_no_rails_is_a_discoverable_refusal) ... ok
test_notifications_get_no_reply_and_unknown_methods_error (__main__.MCPServerTest.test_notifications_get_no_reply_and_unknown_methods_error) ... ok
test_story_status_flip_writes_what_the_core_writes (__main__.MCPServerTest.test_story_status_flip_writes_what_the_core_writes) ... ok
test_story_status_refusal_matches_core (__main__.MCPServerTest.test_story_status_refusal_matches_core) ... ok
test_tools_list_matches_contract_and_excludes_attestation (__main__.MCPServerTest.test_tools_list_matches_contract_and_excludes_attestation) ... ok
test_unknown_tool_and_unknown_params (__main__.MCPServerTest.test_unknown_tool_and_unknown_params) ... ok
test_agents_md_gets_the_agents_variant (__main__.RiderDocsTest.test_agents_md_gets_the_agents_variant) ... ok
test_agents_transformations_actually_fire (__main__.RiderDocsTest.test_agents_transformations_actually_fire) ... ok
test_codex_and_pi_share_agents_md_without_conflict (__main__.RiderDocsTest.test_codex_and_pi_share_agents_md_without_conflict) ... ok
test_codex_installer_is_idempotent (__main__.RiderDocsTest.test_codex_installer_is_idempotent) ... ok
test_codex_skill_drift_is_a_check_error (__main__.RiderDocsTest.test_codex_skill_drift_is_a_check_error) ... ok
test_codex_skill_renders_frontmatter_and_body (__main__.RiderDocsTest.test_codex_skill_renders_frontmatter_and_body) ... ok
test_doctor_riders_wired_absent_and_broken (__main__.RiderDocsTest.test_doctor_riders_wired_absent_and_broken) ... ok
test_embedded_specs_match_source_canon (__main__.RiderDocsTest.test_embedded_specs_match_source_canon) ... ok
test_hand_edited_copy_is_a_check_error (__main__.RiderDocsTest.test_hand_edited_copy_is_a_check_error) ... ok
test_hand_edited_doc_block_is_a_check_error (__main__.RiderDocsTest.test_hand_edited_doc_block_is_a_check_error) ... ok
test_hs_context_block_lifecycle (__main__.RiderDocsTest.test_hs_context_block_lifecycle) ... ok
test_pi_installer_is_idempotent (__main__.RiderDocsTest.test_pi_installer_is_idempotent) ... ok
test_pi_prompt_drift_is_a_check_error (__main__.RiderDocsTest.test_pi_prompt_drift_is_a_check_error) ... ok
test_pi_prompt_is_verbatim_canon_and_pure (__main__.RiderDocsTest.test_pi_prompt_is_verbatim_canon_and_pure) ... ok
test_real_tree_matches_canon (__main__.RiderDocsTest.test_real_tree_matches_canon) ... ok
test_regeneration_is_idempotent (__main__.RiderDocsTest.test_regeneration_is_idempotent) ... ok
test_all_outcomes (__main__.SessionsTest.test_all_outcomes) ... ok
test_registry_failure_shapes (__main__.SessionsTest.test_registry_failure_shapes) ... ok
test_feed_reflects_real_state (__main__.StateFeedTest.test_feed_reflects_real_state) ... ok
test_schema_is_pinned (__main__.StateFeedTest.test_schema_is_pinned) ... ok
test_write_emits_the_same_document (__main__.StateFeedTest.test_write_emits_the_same_document) ... ok
test_bundled_double_flip_with_trailer_passes (__main__.VerifyTest.test_bundled_double_flip_with_trailer_passes) ... ok
test_clean_flip_with_trailers_passes (__main__.VerifyTest.test_clean_flip_with_trailers_passes) ... ok
test_double_flip_without_bundle_fails_atomicity (__main__.VerifyTest.test_double_flip_without_bundle_fails_atomicity) ... ok
test_errors_exit_via_error_field (__main__.VerifyTest.test_errors_exit_via_error_field) ... ok
test_every_rederivable_rule_id_is_a_gate_rule_or_remote_only (__main__.VerifyTest.test_every_rederivable_rule_id_is_a_gate_rule_or_remote_only) ... ok
test_evidence_deletion_orphans_done_story (__main__.VerifyTest.test_evidence_deletion_orphans_done_story) ... ok
test_flip_not_declared_in_story_trailer (__main__.VerifyTest.test_flip_not_declared_in_story_trailer) ... ok
test_malformed_digest_and_story_id (__main__.VerifyTest.test_malformed_digest_and_story_id) ... ok
test_merge_commits_are_out_of_scope (__main__.VerifyTest.test_merge_commits_are_out_of_scope) ... ok
test_non_roadmap_commits_are_out_of_scope (__main__.VerifyTest.test_non_roadmap_commits_are_out_of_scope) ... ok
test_orphan_evidence_added_without_flip (__main__.VerifyTest.test_orphan_evidence_added_without_flip) ... ok
test_pre_epoch_commits_are_skipped_not_flagged (__main__.VerifyTest.test_pre_epoch_commits_are_skipped_not_flagged) ... ok
test_render_gram
[PMO_EVIDENCE_OUTPUT_TRUNCATED]
```

### Captured run — 2026-07-08T01:17:19Z

- **Command:** `python3 pmo-roadmap/tests/telegram-interface-tests.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** f9493b40bcf6e653a9b542123f2ed0995a2a977d

```text
test_decide_pushes_only_notifications_coalesced (__main__.AgentEventsReaderTest.test_decide_pushes_only_notifications_coalesced) ... ok
test_malformed_lines_are_skipped_not_fatal (__main__.AgentEventsReaderTest.test_malformed_lines_are_skipped_not_fatal) ... ok
test_missing_file_is_empty (__main__.AgentEventsReaderTest.test_missing_file_is_empty) ... ok
test_partial_tail_waits_for_its_newline (__main__.AgentEventsReaderTest.test_partial_tail_waits_for_its_newline) ... ok
test_reads_incrementally_by_offset (__main__.AgentEventsReaderTest.test_reads_incrementally_by_offset) ... ok
test_truncation_resets_honestly (__main__.AgentEventsReaderTest.test_truncation_resets_honestly) ... ok
test_one_card_edits_through_its_lifecycle (__main__.CardLifecycleTest.test_one_card_edits_through_its_lifecycle) ... ok
test_rejection_edits_the_card_too (__main__.CardLifecycleTest.test_rejection_edits_the_card_too) ... ok
test_proposal_expires (__main__.ConsentTest.test_proposal_expires) ... ok
test_proposal_is_single_use (__main__.ConsentTest.test_proposal_is_single_use) ... ok
test_reject_executes_nothing (__main__.ConsentTest.test_reject_executes_nothing) ... ok
test_unpaired_callback_refused (__main__.ConsentTest.test_unpaired_callback_refused) ... ok
test_approved_dishonest_done_flip_is_refused_with_banner (__main__.CrownCaseTest.test_approved_dishonest_done_flip_is_refused_with_banner) ... ok
test_honest_flip_executes (__main__.CrownCaseTest.test_honest_flip_executes) ... ok
test_unknown_story_never_becomes_a_proposal (__main__.CrownCaseTest.test_unknown_story_never_becomes_a_proposal) ... ok
test_content_hash_gates (__main__.DriverMannersTest.test_content_hash_gates) ... ok
test_literal_then_settle_then_enter_separately (__main__.DriverMannersTest.test_literal_then_settle_then_enter_separately) ... ok
test_recovery_verbs_follow_capability (__main__.DriverMannersTest.test_recovery_verbs_follow_capability) ... ok
test_resume_launch_only_when_supported (__main__.DriverMannersTest.test_resume_launch_only_when_supported) ... ok
test_send_key_is_a_single_named_key (__main__.DriverMannersTest.test_send_key_is_a_single_named_key) ... ok
test_settle_is_per_harness_from_the_table (__main__.DriverMannersTest.test_settle_is_per_harness_from_the_table) ... ok
test_launch_all_supported_harnesses (__main__.DriverTest.test_launch_all_supported_harnesses) ... ok
test_launched_session_starts_unarmed (__main__.DriverTest.test_launched_session_starts_unarmed) ... ok
test_unsupported_harness_refused (__main__.DriverTest.test_unsupported_harness_refused) ... ok
test_bold_code_pre_become_entities (__main__.EntitiesTest.test_bold_code_pre_become_entities) ... ok
test_chunk_prefers_line_boundaries_and_rescopes (__main__.EntitiesTest.test_chunk_prefers_line_boundaries_and_rescopes) ... ok
test_hostile_characters_need_no_escaping (__main__.EntitiesTest.test_hostile_characters_need_no_escaping) ... ok
test_offsets_are_utf16_after_emoji (__main__.EntitiesTest.test_offsets_are_utf16_after_emoji) ... ok
test_a_question_routes_home_to_its_repo_topic (__main__.FlowingConversationTest.test_a_question_routes_home_to_its_repo_topic) ... ok
test_plain_text_without_a_binding_is_refused_gently (__main__.FlowingConversationTest.test_plain_text_without_a_binding_is_refused_gently) ... ok
test_steer_then_plain_text_flows_no_tap (__main__.FlowingConversationTest.test_steer_then_plain_text_flows_no_tap) ... ok
test_unsteer_stops_the_flow (__main__.FlowingConversationTest.test_unsteer_stops_the_flow) ... ok
test_notification_pushes_in_the_same_drain (__main__.HookDrainTest.test_notification_pushes_in_the_same_drain) ... ok
test_restart_never_repushes (__main__.HookDrainTest.test_restart_never_repushes) ... ok
test_stop_records_but_does_not_push (__main__.HookDrainTest.test_stop_records_but_does_not_push) ... ok
test_unpaired_drain_is_silent_and_consumes_nothing (__main__.HookDrainTest.test_unpaired_drain_is_silent_and_consumes_nothing) ... ok
test_create_for_real_lands_on_the_rails (__main__.LifecycleTest.test_create_for_real_lands_on_the_rails)
The full leg, no fakes: scaffold → rails → doctor → ... ok
test_create_outside_roots_refused_before_proposal (__main__.LifecycleTest.test_create_outside_roots_refused_before_proposal) ... ok
test_create_step_sequence_with_scripted_runner (__main__.LifecycleTest.test_create_step_sequence_with_scripted_runner) ... ok
test_open_requires_rails_repo_within_roots (__main__.LifecycleTest.test_open_requires_rails_repo_within_roots) ... ok
test_live_view_edits_only_on_change (__main__.LiveViewTest.test_live_view_edits_only_on_change) ... ok
test_live_view_expires (__main__.LiveViewTest.test_live_view_expires) ... ok
test_live_view_is_read_only (__main__.LiveViewTest.test_live_view_is_read_only) ... ok
test_burst_arrives_ordered_and_merged (__main__.MessageQueueTest.test_burst_arrives_ordered_and_merged) ... ok
test_entity_rejection_falls_back_to_plain (__main__.MessageQueueTest.test_entity_rejection_falls_back_to_plain) ... ok
test_flood_control_pauses_and_retries (__main__.MessageQueueTest.test_flood_control_pauses_and_retries) ... ok
test_oversize_text_chunks_at_send_layer (__main__.MessageQueueTest.test_oversize_text_chunks_at_send_layer) ... ok
test_status_edits_in_place (__main__.MessageQueueTest.test_status_edits_in_place) ... ok
test_expired_token_refused (__main__.PairingTest.test_expired_token_refused) ... ok
test_no_outstanding_token_refused (__main__.PairingTest.test_no_outstanding_token_refused) ... ok
test_pair_then_reuse_refused (__main__.PairingTest.test_pair_then_reuse_refused) ... ok
test_repair_revokes_previous_binding (__main__.PairingTest.test_repair_revokes_previous_binding) ... ok
test_state_file_is_owner_only (__main__.PairingTest.test_state_file_is_owner_only) ... ok
test_token_from_separate_pair_process_is_honored (__main__.PairingTest.test_token_from_separate_pair_process_is_honored) ... ok
test_token_stored_hashed_not_cleartext (__main__.PairingTest.test_token_stored_hashed_not_cleartext) ... ok
test_unpaired_chat_gets_prompt_then_silence (__main__.PairingTest.test_unpaired_chat_gets_prompt_then_silence) ... ok
test_wrong_token_refused (__main__.PairingTest.test_wrong_token_refused) ... ok
test_adjacent_texts_merge_statuses_coalesce (__main__.PlanBatchTest.test_adjacent_texts_merge_statuses_coalesce) ... ok
test_merge_respects_the_cap (__main__.PlanBatchTest.test_merge_respects_the_cap) ... ok
test_the_whole_pocket_desk_in_one_flow (__main__.PocketDeskExitExamTest.test_the_whole_pocket_desk_in_one_flow) ... ok
test_arming_expires (__main__.QARelayTest.test_arming_expires) ... ok
test_dead_pane_is_refused (__main__.QARelayTest.test_dead_pane_is_refused) ... ok
test_disarm_and_status (__main__.QARelayTest.test_disarm_and_status) ... ok
test_no_keystroke_without_a_grant (__main__.QARelayTest.test_no_keystroke_without_a_grant) ... ok
test_question_surfaces_with_story_correlation (__main__.QARelayTest.test_question_surfaces_with_story_correlation) ... ok
test_recycled_pane_id_is_refused (__main__.QARelayTest.test_recycled_pane_id_is_refused) ... ok
test_reply_approval_is_the_arming_grant (__main__.QARelayTest.test_reply_approval_is_the_arming_grant) ... ok
test_reply_reaches_the_right_pane_when_armed (__main__.QARelayTest.test_reply_reaches_the_right_pane_when_armed) ... ok
test_reply_to_a_session_outside_tmux_explains_itself (__main__.QARelayTest.test_reply_to_a_session_outside_tmux_explains_itself) ... ok
test_unsteerable_sessions_are_marked (__main__.QARelayTest.test_unsteerable_sessions_are_marked) ... ok
test_events_render_real_log (__main__.ReadSurfaceTest.test_events_render_real_log) ... ok
test_peek_is_read_only_capture (__main__.ReadSurfaceTest.test_peek_is_read_only_capture) ... ok
test_sessions_render_correlation (__main__.ReadSurfaceTest.test_sessions_render_correlation) ... ok
test_state_renders_real_feed (__main__.ReadSurfaceTest.test_state_renders_real_feed) ... ok
test_steer_a_dead_session_offers_capability_recovery (__main__.RecoveryTest.test_steer_a_dead_session_offers_capability_recovery) ... ok
test_story_argv_allow_list_is_two_verbs (__main__.SchemaComplianceTest.test_story_argv_allow_list_is_two_verbs) ... ok
test_unproven_feed_schema_refused_politely (__main__.SchemaComplianceTest.test_unproven_feed_schema_refused_politely) ... ok
test_unproven_sessions_schema_refused_politely (__main__.SchemaComplianceTest.test_unproven_sessions_schema_refused_politely) ... ok
test_ambiguous_match_lists_candidates (__main__.SendCommandTest.test_ambiguous_match_lists_candidates) ... ok
test_no_match_says_so (__main__.SendCommandTest.test_no_match_says_so) ... ok
test_send_a_clean_file_goes_straight_through (__main__.SendCommandTest.test_send_a_clean_file_goes_straight_through) ... ok
test_send_a_secret_is_refused_by_name (__main__.SendCommandTest.test_send_a_secret_is_refused_by_name) ... ok
test_send_the_config_by_name_is_refused (__main__.SendCommandTest.test_send_the_config_by_name_is_refused) ... ok
test_a_clean_file_passes_all_locks (__main__.SendLocksTest.test_a_clean_file_passes_all_locks) ... ok
test_lock1_traversal (__main__.SendLocksTest.test_lock1_traversal) ... ok
test_lock2_hidden (__main__.SendLocksTest.test_lock2_hidden) ... ok
test_lock3_secret_pattern (__main__.SendLocksTest.test_lock3_secret_pattern) ... ok
test_lock4_size (__main__.SendLocksTest.test_lock4_size) ... ok
test_lock5_gitignore (__main__.SendLocksTest.test_lock5_gitignore) ... ok
test_lock6_gitleaks_rule (__main__.SendLocksTest.test_lock6_gitleaks_rule) ... ok
test_lock7_state_dir (__main__.SendLocksTest.test_lock7_state_dir) ... ok
test_lock7_state_file_by_name (__main__.SendLocksTest.test_lock7_state_file_by_name) ... ok
test_resolve_exact_glob_and_substring (__main__.SendLocksTest.test_resolve_exact_glob_and_substring) ... ok
test_env_token_overrides_missing_config (__main__.TokenHygieneTest.test_env_token_overrides_missing_config) ... ok
test_missing_token_error_names_path_not_content (__main__.TokenHygieneTest.test_missing_token_error_names_path_not_content) ... ok
test_transport_errors_never_carry_the_token (__main__.TokenHygieneTest.test_transport_errors_never_carry_the_token) ... ok
test_toolbar_only_offered_when_bound (__main__.ToolbarTest.test_toolbar_only_offered_when_bound) ... ok
test_toolbar_press_fires_a_key_no_extra_tap (__main__.ToolbarTest.test_toolbar_press_fires_a_key_no_extra_tap) ... ok
test_toolbar_press_without_binding_refused (__main__.ToolbarTest.test_toolbar_press_without_binding_refused) ... ok
test_bindings_persist_across_restart (__main__.TopicRouterTest.test_bindings_persist_across_restart) ... ok
test_flat_chat_is_the_none_topic (__main__.TopicRouterTest.test_flat_chat_is_the_none_topic) ... ok
test_repo_bind_scope_and_reverse (__main__.TopicRouterTest.test_repo_bind_scope_and_reverse) ... ok
test_session_binding_expires_but_activity_refreshes (__main__.TopicRouterTest.test_session_binding_expires_but_activity_refreshes) ... ok
test_unbind_repo_cascades_to_session (__main__.TopicRouterTest.test_unbind_repo_cascades_to_session) ... ok
test_bind_then_commands_scope_to_the_topic (__main__.TopicScopingTest.test_bind_then_commands_scope_to_the_topic) ... ok
test_flat_chat_still_uses_active_repo (__main__.TopicScopingTest.test_flat_chat_still_uses_active_repo) ... ok
test_replies_land_in_the_originating_topic (__main__.TopicScopingTest.test_replies_land_in_the_originating_topic) ... ok
test_unbound_topic_has_no_repo (__main__.TopicScopingTest.test_unbound_topic_has_no_repo) ... ok

----------------------------------------------------------------------
Ran 108 tests in 5.765s

OK
```
