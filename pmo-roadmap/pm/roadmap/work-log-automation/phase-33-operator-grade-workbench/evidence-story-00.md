# Evidence — WLA-33-00

## Summary

Design system and component foundation delivered. Framework decision:
vanilla Web Components (Custom Elements v1, no Shadow DOM). Ten
components, five interaction primitives, a workspace layout engine,
and a design reference page at `#/design`. The existing board
migrated to new components. Core test suite: 698 tests, zero failures.

**New files:** `components.js` (627 lines, 10 components), `interactions.js`
(824 lines, 5 primitives), `layout.js` (133 lines), `design.js` (175 lines).

**Modified:** `app.js` (board functions use dw-card, dw-status-pill, dw-button,
dw-badge, dw-fold, dw-toast; `#/design` route added), `style.css` (+550 lines),
`index.html` (loads four new scripts).

### Captured run — 2026-07-31T22:47:44Z

- **Command:** `python3 pmo-roadmap/tests/dw-core-tests.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** e490f2bb879bc5c86d466642772c7ffaf022114d

```text
test_codex_flag_opt_out_respected (__main__.AgentHooksTest.test_codex_flag_opt_out_respected) ... dw hook: codex_hooks is explicitly false in /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test._pwd6kak/config.toml; respecting the opt-out
ok
test_emit_never_raises_on_garbage (__main__.AgentHooksTest.test_emit_never_raises_on_garbage) ... ok
test_emit_quiet_guard_and_unknown_event (__main__.AgentHooksTest.test_emit_quiet_guard_and_unknown_event) ... ok
test_emit_whitelists_and_never_leaks_content (__main__.AgentHooksTest.test_emit_whitelists_and_never_leaks_content) ... ok
test_install_is_idempotent (__main__.AgentHooksTest.test_install_is_idempotent) ... ok
test_status_reports_per_event (__main__.AgentHooksTest.test_status_reports_per_event) ... ok
test_uninstall_is_surgical (__main__.AgentHooksTest.test_uninstall_is_surgical) ... ok
test_measurements_never_confuse_zero_unbounded_unknown_or_na (__main__.BoundedActionsProjectionTest.test_measurements_never_confuse_zero_unbounded_unknown_or_na) ... ok
test_program_request_and_remote_guidance_never_mint_authority (__main__.BoundedActionsProjectionTest.test_program_request_and_remote_guidance_never_mint_authority) ... ok
test_run_decisions_blockers_permission_and_actions_are_closed (__main__.BoundedActionsProjectionTest.test_run_decisions_blockers_permission_and_actions_are_closed) ... ok
test_complete_green_route_is_required (bundle_validation_tests.BundleFactAndBudgetTest.test_complete_green_route_is_required) ... ok
test_fact_check_match_and_phase_29_mismatch_regression (bundle_validation_tests.BundleFactAndBudgetTest.test_fact_check_match_and_phase_29_mismatch_regression) ... ok
test_larger_required_team_changes_the_minimum_budget_envelope (bundle_validation_tests.BundleFactAndBudgetTest.test_larger_required_team_changes_the_minimum_budget_envelope) ... ok
test_team_cardinality_verifier_and_fanout_budgets (bundle_validation_tests.BundleFactAndBudgetTest.test_team_cardinality_verifier_and_fanout_budgets) ... ok
test_cli_mcp_and_http_validate_share_canonical_bytes (bundle_validation_tests.BundlePolicyPurityAndParityTest.test_cli_mcp_and_http_validate_share_canonical_bytes) ... ok
test_tracked_execution_controls_refuse_with_pointers (bundle_validation_tests.BundlePolicyPurityAndParityTest.test_tracked_execution_controls_refuse_with_pointers) ... ok
test_validation_is_byte_stable_and_writes_nothing (bundle_validation_tests.BundlePolicyPurityAndParityTest.test_validation_is_byte_stable_and_writes_nothing) ... ok
test_real_phase_29_bundle_is_preflighted_as_one_linked_object (bundle_validation_tests.BundleRealPhase29IntegrationTest.test_real_phase_29_bundle_is_preflighted_as_one_linked_object) ... ok
test_compiler_conductor_node_sets_are_code_owned_and_checkpoint_refuses (bundle_validation_tests.BundleRosterAndParityTest.test_compiler_conductor_node_sets_are_code_owned_and_checkpoint_refuses) ... ok
test_diversity_satisfiable_unsatisfiable_and_roster_absent (bundle_validation_tests.BundleRosterAndParityTest.test_diversity_satisfiable_unsatisfiable_and_roster_absent) ... ok
test_roster_diagnostics_are_closed_and_credential_safe (bundle_validation_tests.BundleRosterAndParityTest.test_roster_diagnostics_are_closed_and_credential_safe) ... ok
test_unconductable_builtin_check_name_refuses_at_validation (bundle_validation_tests.BundleRosterAndParityTest.test_unconductable_builtin_check_name_refuses_at_validation) ... ok
test_front_door_names_scope_three_modes_effects_and_permissions (__main__.DeliverySetupTest.test_front_door_names_scope_three_modes_effects_and_permissions) ... ok
test_human_cli_and_http_render_the_same_choice_and_readiness (__main__.DeliverySetupTest.test_human_cli_and_http_render_the_same_choice_and_readiness) ... ok
test_missing_or_invalid_inputs_name_the_delivery_decision_and_correction (__main__.DeliverySetupTest.test_missing_or_invalid_inputs_name_the_delivery_decision_and_correction) ... ok
test_setup_and_cancel_model_are_repeatable_and_write_nothing (__main__.DeliverySetupTest.test_setup_and_cancel_model_are_repeatable_and_write_nothing) ... ok
test_no_fact_is_read_twice_inside_one_observation (__main__.DerivationReadsTest.test_no_fact_is_read_twice_inside_one_observation) ... ok
test_one_observation_reads_head_once_even_with_a_remote (__main__.DerivationReadsTest.test_one_observation_reads_head_once_even_with_a_remote) ... ok
test_separate_observations_still_re_read_everything (__main__.DerivationReadsTest.test_separate_observations_still_re_read_everything) ... ok
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
test_board_is_home_and_keeps_every_act_on_canonical_mutations (__main__.DwCoreTest.test_board_is_home_and_keeps_every_act_on_canonical_mutations) ... ok
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
test_phase_advance_is_one_guarded_summary_pointer_and_header_plan (__main__.DwCoreTest.test_phase_advance_is_one_guarded_summary_pointer_and_header_plan) ... ok
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
test_run_start_accepts_notification_fields_and_still_refuses_unknown_properties (__main__.DwCoreTest.test_run_start_accepts_notification_fields_and_still_refuses_unknown_properties) ... ok
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
test_cli_help_uses_the_shared_task_language (__main__.EverydayPresentationTest.test_cli_help_uses_the_shared_task_language) ... ok
test_real_presenters_match_versioned_human_snapshots (__main__.EverydayPresentationTest.test_real_presenters_match_versioned_human_snapshots) ... ok
test_runtime_catalog_matches_the_reviewed_contract (__main__.EverydayPresentationTest.test_runtime_catalog_matches_the_reviewed_contract) ... ok
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
test_fix_hooks_path_is_noop_on_relative_and_refuses_foreign (__main__.GateTest.test_fix_hooks_path_is_noop_on_relative_and_refuses_foreign) ... ok
test_fix_hooks_path_normalizes_same_clone_absolute (__main__.GateTest.test_fix_hooks_path_normalizes_same_clone_absolute) ... ok
test_forced_full_tier_config (__main__.GateTest.test_forced_full_tier_config) ... ok
test_head_mismatch_after_history_moves (__main__.GateTest.test_head_mismatch_after_history_moves) ... ok
test_hooks_p
[PMO_EVIDENCE_OUTPUT_TRUNCATED]
```
