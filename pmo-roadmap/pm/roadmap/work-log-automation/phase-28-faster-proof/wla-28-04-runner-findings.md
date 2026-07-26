# WLA-28-04 runner findings (not story evidence)

This story is **parked on-hold**, so these runs are not paired evidence — the
file is deliberately not named `evidence-story-04.md`. It records what the
sharded runner did across several captures, including the two failures that
caused the park. Authoritative: the final capture, whose sharded run 1 passed
523 tests and whose sharded run 2 failed on a wall-clock ceiling under a
loaded desk.


- **Story:** WLA-28-04 - Prove work in parallel
- **Status:** done
- **Date:** 2026-07-26

## Proof

### Captured run — 2026-07-26T19:12:27Z

- **Command:** `bash -lc set -e
echo '=== sharded run 1 ==='
python3 pmo-roadmap/tests/run-core-tests.py
echo '=== sharded run 2 (stability) ==='
python3 pmo-roadmap/tests/run-core-tests.py
echo '=== sharded with a different shard count ==='
python3 pmo-roadmap/tests/run-core-tests.py --shards 4
echo '=== serial run (agreement) ==='
python3 pmo-roadmap/tests/run-core-tests.py --serial
echo '=== runner unit cases ==='
python3 -m unittest -v pmo-roadmap/tests/dw-core-tests.py -k ShardRunnerTest
echo '=== floor 3.9 ==='
/usr/bin/python3 -m py_compile pmo-roadmap/tests/run-core-tests.py
/usr/bin/python3 pmo-roadmap/tests/run-core-tests.py --list
bash pmo-roadmap/tests/docs-lint.sh
bash pmo-roadmap/tests/canon-lint.sh
bash pmo-roadmap/update.sh . --check
pmo-roadmap/bin/dw check work-log-automation
git diff --check`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 2aefb1fb83111d3d74c6d8fb0dc51da3b83a42bd

```text
=== sharded run 1 ===
run-core-tests: 513 units across 8 shards
  shard 0:  61 tests in   97.8s  ok
  shard 1:  67 tests in   91.0s  ok
  shard 2:   1 tests in   95.2s  ok
  shard 3:  67 tests in  105.5s  ok
  shard 4:  69 tests in  101.0s  ok
  shard 5:  62 tests in  104.1s  ok
  shard 6:  67 tests in  108.1s  ok
  shard 7:  62 tests in  108.2s  ok
run-core-tests: 456 tests in 108.2s (OK)
=== sharded run 2 (stability) ===
run-core-tests: 513 units across 8 shards
  shard 0:  61 tests in  110.6s  ok
  shard 1:  67 tests in  103.1s  ok
  shard 2:   1 tests in  107.7s  ok
  shard 3:  67 tests in  117.7s  ok
  shard 4:  69 tests in  114.8s  ok
  shard 5:  62 tests in  118.3s  ok
  shard 6:  67 tests in  121.5s  ok
  shard 7:  62 tests in  123.1s  ok
run-core-tests: 456 tests in 123.1s (OK)
=== sharded with a different shard count ===
run-core-tests: 513 units across 4 shards
  shard 0: 126 tests in  195.1s  ok
  shard 1: 129 tests in  199.3s  ok
  shard 2:   1 tests in  192.0s  ok
  shard 3: 129 tests in  211.8s  ok
run-core-tests: 385 tests in 211.8s (OK)
=== serial run (agreement) ===
test_codex_flag_opt_out_respected (__main__.AgentHooksTest) ... dw hook: codex_hooks is explicitly false in /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.unv1e6zv/config.toml; respecting the opt-out
ok
test_emit_never_raises_on_garbage (__main__.AgentHooksTest) ... ok
test_emit_quiet_guard_and_unknown_event (__main__.AgentHooksTest) ... ok
test_emit_whitelists_and_never_leaks_content (__main__.AgentHooksTest) ... ok
test_install_is_idempotent (__main__.AgentHooksTest) ... ok
test_status_reports_per_event (__main__.AgentHooksTest) ... ok
test_uninstall_is_surgical (__main__.AgentHooksTest) ... ok
test_measurements_never_confuse_zero_unbounded_unknown_or_na (__main__.BoundedActionsProjectionTest) ... ok
test_program_request_and_remote_guidance_never_mint_authority (__main__.BoundedActionsProjectionTest) ... ok
test_run_decisions_blockers_permission_and_actions_are_closed (__main__.BoundedActionsProjectionTest) ... ok
test_front_door_names_scope_three_modes_effects_and_permissions (__main__.DeliverySetupTest) ... ok
test_human_cli_and_http_render_the_same_choice_and_readiness (__main__.DeliverySetupTest) ... ok
test_missing_or_invalid_inputs_name_the_delivery_decision_and_correction (__main__.DeliverySetupTest) ... ok
test_setup_and_cancel_model_are_repeatable_and_write_nothing (__main__.DeliverySetupTest) ... ok
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
test_phase_advance_is_one_guarded_summary_pointer_and_header_plan (__main__.DwCoreTest) ... ok
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
test_workbench_step_front_door_keeps_review_and_act_separate (__main__.DwCoreTest) ... ok
test_workbench_story_route_serves_story_detail (__main__.DwCoreTest) ... ok
test_worklog_absent_root_is_optional_not_error (__main__.DwCoreTest) ... ok
test_worklog_endpoint_containment_and_omission (__main__.DwCoreTest) ... ok
test_write_containment (__main__.DwCoreTest) ... ok
test_append_only_and_never_raises (__main__.EventsTest) ... ok
test_content_audit_rogue_keys_dropped (__main__.EventsTest) ... ok
test_gate_refusal_carries_its_rule (__main__.EventsTest) ... ok
test_rail_moments_emit (__main__.EventsTest) ... ok
test_cli_help_uses_the_shared_task_language (__main__.EverydayPresentationTest) ... ok
test_real_presenters_match_versioned_human_snapshots (__main__.EverydayPresentationTest) ... ok
test_runtime_catalog_matches_the_reviewed_contract (__main__.EverydayPresentationTest) ... ok
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
test_repair_and_recovery_use_only_canonical_run_facts (__main__.LiveProgressProjectionTest) ... ok
test_browse_refusals_match_core (__main__.MCPServerTest) ... ok
test_browse_tools_agree_with_core (__main__.MCPServerTest) ... ok
test_browse_tools_are_read_only (__main__.MCPServerTest) ... ok
test_check_and_next_agree_with_core (__main__.MCPServerTest) ... ok
test_core_refusal_becomes_tool_error (__main__.MCPServerTest) ... ok
test_initialize_pins_protocol_version (__main__.MCPServerTest) ... ok
test_mutation_tools_require_their_params (__main__.MCPServerTest) ... ok
test_no_rails_is_a_discoverable_refusal (__main__.MCPServerTest) ... ok
test_notifications_get_no_reply_and_unknown_methods_error (__main__.MCPServerTest) ... ok
test_status_agrees_with_core_and_attention_is_data (__main__.MCPServerTest) ... ok
test_step_tools_are_exact_core_adapters (__main__.MCPServerTest) ... ok
test_story_status_flip_writes_what_the_core_writes (__main__.MCPServerTest) ... ok
test_story_status_refusal_matches_core (__main__.MCPServerTest) ... ok
test_tools_list_matches_contract_and_excludes_attestation (__main__.MCPServerTest) ... ok
test_unknown_tool_and_unknown_params (__main__.MCPServerTest) ... ok
test_cli_invalid_score_returns_pointer_diagnostics_and_exit_one (__main__.OrchestrationCompilerTest) ... ok
test_cli_list_show_validate_and_simulate_share_core_documents (__main__.OrchestrationCompilerTest) ... ok
test_duplicate_json_keys_nonfinite_numbers_and_escaped_symlinks_refuse (__main__.OrchestrationCompilerTest) ... ok
test_exact_keys_duplicate_ids_and_dangling_references_refuse (__main__.OrchestrationCompilerTest) ... ok
test_impossible_capabilities_and_forbidden_rail_authority_refuse (__main__.OrchestrationCompilerTest) ... ok
test_minimal_and_custom_role_round_trip (__main__.OrchestrationCompilerTest) ... ok
test_nudge_rules_compile_simulate_and_refuse_exactly (__main__.OrchestrationCompilerTest) ... ok
test_output_producer_type_and_order_checks_refuse (__main__.OrchestrationCompilerTest) ... ok
test_representative_preset_compiles_and_simulates_parallel_fan_in (__main__.OrchestrationCompilerTest) ... ok
test_resource_locks_and_concurrency_make_simulation_deterministic (__main__.OrchestrationCompilerTest) ... ok
test_semantic_hash_ignores_object_key_order_and_layout_only (__main__.OrchestrationCompilerTest) ... ok
test_success_cycles_and_unbounded_failure_policies_refuse (__main__.OrchestrationCompilerTest) ... ok
test_unsafe_paths_shell_strings_and_undeclared_runners_refuse (__main__.OrchestrationCompilerTest) ... ok
test_activity_transitions_are_ledgered_once_per_change (__main__.OrchestrationConductorTest) ... ok
test_adapters_reject_score_semantics_driver_config_and_argv (__main__.OrchestrationConductorTest) ... ok
test_builtin_file_schema_diff_and_rail_checks_share_receipts (__main__.OrchestrationConductorTest) ... ok
test_cancellation_interrupts_a_live_contained_check (__main__.OrchestrationConductorTest) ... ok
test_cancellation_precedes_interrupt_and_expiry_starts_nothing (__main__.OrchestrationConductorTest) ... ok
test_checkpoint_alias_cannot_decide_a_live_nudge_request (__main__.OrchestrationConductorTest) ... ok
test_cli_and_mcp_controls_require_fresh_preview_tokens (__main__.OrchestrationConductorTest) ... ok
test_cli_run_tail_matches_the_ledger (__main__.OrchestrationConductorTest) ... ok
test_crash_after_check_recovers_without_rerunning_command (__main__.OrchestrationConductorTest) ... ok
test_crash_after_driver_start_recovers_without_duplicate_launch (__main__.OrchestrationConductorTest) ... ok
test_exact_command_check_is_contained_and_write_scope_fails (__main__.OrchestrationConductorTest) ... ok
test_failed_nudge_attempt_runs_its_named_approval_policy (__main__.OrchestrationConductorTest) ... ok
test_failed_repair_follows_its_abort_policy (__main__.OrchestrationConductorTest) ... ok
test_failure_pause_and_named_approval_are_ledger_states (__main__.OrchestrationConductorTest) ... ok
test_full_fanout_check_repair_retry_and_terminal_handoff (__main__.OrchestrationConductorTest) ... ok
test_installed_cli_tick_and_bounded_supervision_share_the_core (__main__.OrchestrationConductorTest) ... ok
test_invalid_artifact_retries_then_exhausts_without_fan_in (__main__.OrchestrationConductorTest) ... ok
test_ledger_tail_is_exact_derivable_and_content_safe (__main__.OrchestrationConductorTest) ... ok
test_mission_control_run_summary_is_content_safe (__main__.OrchestrationConductorTest) ... ok
test_notifications_delivery_ceiling_parity_and_branch_opt_in (__main__.OrchestrationConductorTest) ... ok
test_notifications_derive_ack_and_correlate (__main__.OrchestrationConductorTest) ... ok
test_nudge_authority_rides_the_plan_and_grant (__main__.OrchestrationConductorTest) ... ok
test_nudge_budget_exhaustion_is_a_recorded_blocked_stop (__main__.OrchestrationConductorTest) ... ok
test_nudge_crash_after_delivery_recovers_without_duplicate (__main__.OrchestrationConductorTest) ... ok
test_nudge_receptivity_gates_live_sessions (__main__.OrchestrationConductorTest) ... ok
test_nudge_refusals_are_distinct_recorded_and_deduped (__main__.OrchestrationConductorTest) ... ok
test_nudge_wakes_awaiting_certification_and_delivers_at_most_once (__main__.OrchestrationConductorTest) ... ok
test_nudged_reattempt_supersedes_its_stored_artifact (__main__.OrchestrationConductorTest) ... ok
test_outstanding_request_republishes_once_per_restart_generation (__main__.OrchestrationConductorTest) ... ok
test_pure_schedule_is_stable_and_respects_resource_groups (__main__.OrchestrationConductorTest) ... ok
test_rail_uses_fresh_step_lease_and_stale_action_never_starts (__main__.OrchestrationConductorTest) ... ok
test_request_expiry_is_a_recorded_refusal_and_notification (__main__.OrchestrationConductorTest) ... ok
test_request_preview_and_apply_are_exact_across_interop_surfaces (__main__.OrchestrationConductorTest) ... ok
test_run_act_token_binds_action_reason_decision_and_state (__main__.OrchestrationConductorTest) ... ok
test_run_interop_compiler_plan_projection_and_preview_are_exact (__main__.OrchestrationConductorTest) ... ok
test_run_stream_is_explicit_bounded_and_injection_safe (__main__.OrchestrationConductorTest) ... ok
test_run_view_exposes_request_age_schema_and_inspect_only_lineage (__main__.OrchestrationConductorTest) ... ok
test_run_view_is_pure_rich_and_excludes_private_semantics (__main__.OrchestrationConductorTest) ... ok
test_run_view_static_contract_has_consent_privacy_and_no_poller (__main__.OrchestrationConductorTest) ... ok
test_sse_stream_replays_after_disconnect_and_carries_no_authority (__main__.OrchestrationConduc
[PMO_EVIDENCE_OUTPUT_TRUNCATED]
```

### Captured run — 2026-07-26T19:54:18Z

- **Command:** `bash -lc set -e
echo '=== sharded run 1 ==='
python3 pmo-roadmap/tests/run-core-tests.py
echo '=== sharded run 2 (stability, same assignment) ==='
python3 pmo-roadmap/tests/run-core-tests.py
echo '=== sharded, different shard count (3) ==='
python3 pmo-roadmap/tests/run-core-tests.py --shards 3
echo '=== serial run (agreement) ==='
python3 pmo-roadmap/tests/run-core-tests.py --serial
echo '=== runner unit cases ==='
python3 -m unittest -v pmo-roadmap/tests/dw-core-tests.py -k ShardRunnerTest
echo '=== coverage identity: units vs module load ==='
python3 -c "
import importlib.util, sys, unittest
spec=importlib.util.spec_from_file_location('r','pmo-roadmap/tests/run-core-tests.py')
r=importlib.util.module_from_spec(spec); spec.loader.exec_module(r)
units=r.discover_units(); m=sys.modules['dw_core_tests_shard']; loader=unittest.TestLoader()
def flat(s):
    for x in s:
        if isinstance(x, unittest.TestSuite): yield from flat(x)
        else: yield x.id()
ids=[]
for u in units: ids.extend(flat(loader.loadTestsFromNames([u], m)))
full=list(flat(loader.loadTestsFromModule(m)))
assert sorted(ids)==sorted(full), 'sharded discovery differs from module load'
assert len(ids)==len(set(ids)), 'a test would run more than once'
print('coverage identical:', len(ids), 'tests,', len(units), 'units, no duplicates')
"
echo '=== floor 3.9 ==='
/usr/bin/python3 -m py_compile pmo-roadmap/tests/run-core-tests.py
/usr/bin/python3 pmo-roadmap/tests/run-core-tests.py --list
bash pmo-roadmap/tests/docs-lint.sh
bash pmo-roadmap/tests/canon-lint.sh
bash pmo-roadmap/update.sh . --check
pmo-roadmap/bin/dw check work-log-automation
git diff --check`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** 2aefb1fb83111d3d74c6d8fb0dc51da3b83a42bd

```text
=== sharded run 1 ===

======================================================================
shard 1 output
======================================================================
.............................F.............................
======================================================================
shard 1 output
======================================================================
out
........
======================================================================
FAIL: test_builtin_file_schema_diff_and_rail_checks_share_receipts (dw_core_tests_shard.OrchestrationConductorTest)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/Users/karol/dev/code/delivery-workbench/pmo-roadmap/tests/dw-core-tests.py", line 7888, in test_builtin_file_schema_diff_and_rail_checks_share_receipts
    self.assertEqual(diff_final["state"], "awaiting-certification")
AssertionError: 'blocked' != 'awaiting-certification'
- blocked
+ awaiting-certification


----------------------------------------------------------------------
Ran 67 tests in 71.970s

FAILED (failures=1)
dw hook: claude — 4 installed, 0 already present in /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.t8xhqe2w/settings.json
dw hook: claude — 4 removed from /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.t8xhqe2w/settings.json
##shard-summary {"ran": 67, "failures": 1, "errors": 0, "skipped": 0}

run-core-tests: 516 units across 8 shards + 1 serial
  shard 0:  61 tests in  575.4s  ok
  shard 1:  67 tests in  565.9s  FAIL
  shard 2:  63 tests in  579.6s  ok
  shard 3:  67 tests in  580.0s  ok
  shard 4:  71 tests in  585.4s  ok
  shard 5:  68 tests in  581.5s  ok
  shard 6:  63 tests in  583.8s  ok
  shard 7:  62 tests in  585.0s  ok
  shard 8:   1 tests in    1.9s  ok
run-core-tests: 523 tests in 587.3s (FAILED)
```

### Captured run — 2026-07-26T20:09:14Z

- **Command:** `bash -lc set -e
uptime
echo '=== sharded run 1 ==='
python3 pmo-roadmap/tests/run-core-tests.py
echo '=== sharded run 2 (stability) ==='
python3 pmo-roadmap/tests/run-core-tests.py
echo '=== sharded, different shard count (3) ==='
python3 pmo-roadmap/tests/run-core-tests.py --shards 3
echo '=== serial run (agreement) ==='
python3 pmo-roadmap/tests/run-core-tests.py --serial
echo '=== runner unit cases ==='
python3 -m unittest -v pmo-roadmap/tests/dw-core-tests.py -k ShardRunnerTest
echo '=== coverage identity: units vs module load ==='
python3 -c "
import importlib.util, sys, unittest
spec=importlib.util.spec_from_file_location('r','pmo-roadmap/tests/run-core-tests.py')
r=importlib.util.module_from_spec(spec); spec.loader.exec_module(r)
units=r.discover_units(); m=sys.modules['dw_core_tests_shard']; loader=unittest.TestLoader()
def flat(s):
    for x in s:
        if isinstance(x, unittest.TestSuite): yield from flat(x)
        else: yield x.id()
ids=[]
for u in units: ids.extend(flat(loader.loadTestsFromNames([u], m)))
full=list(flat(loader.loadTestsFromModule(m)))
assert sorted(ids)==sorted(full), 'sharded discovery differs from a module load'
assert len(ids)==len(set(ids)), 'a test would run more than once'
print('coverage identical:', len(ids), 'tests from', len(units), 'units, no duplicates')
"
echo '=== floor 3.9 ==='
/usr/bin/python3 -m py_compile pmo-roadmap/tests/run-core-tests.py
/usr/bin/python3 pmo-roadmap/tests/run-core-tests.py --list
bash pmo-roadmap/tests/docs-lint.sh
bash pmo-roadmap/tests/canon-lint.sh
bash pmo-roadmap/update.sh . --check
pmo-roadmap/bin/dw check work-log-automation
git diff --check`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** 2aefb1fb83111d3d74c6d8fb0dc51da3b83a42bd

```text
14:09  up 3 days,  3:34, 7 users, load averages: 6.38 10.68 13.18
=== sharded run 1 ===
run-core-tests: 516 units across 8 shards + 46 serial
  shard 0:  61 tests in   90.5s  ok
  shard 1:  62 tests in   78.2s  ok
  shard 2:  57 tests in   85.1s  ok
  shard 3:  61 tests in   93.4s  ok
  shard 4:  63 tests in   94.8s  ok
  shard 5:  57 tests in   94.6s  ok
  shard 6:  57 tests in   95.1s  ok
  shard 7:  59 tests in   99.5s  ok
  shard 8:  46 tests in   94.3s  ok
run-core-tests: 523 tests in 193.8s (OK)
=== sharded run 2 (stability) ===
run-core-tests: 516 units across 8 shards + 46 serial
  shard 0:  61 tests in  241.5s  ok
  shard 1:  62 tests in  213.3s  ok
  shard 2:  57 tests in  231.4s  ok
  shard 3:  61 tests in  254.9s  ok
  shard 4:  63 tests in  254.3s  ok
  shard 5:  57 tests in  253.9s  ok
  shard 6:  57 tests in  254.1s  ok
  shard 7:  59 tests in  260.4s  ok
  shard 8:  46 tests in  137.5s  ok
run-core-tests: 523 tests in 397.9s (OK)
=== sharded, different shard count (3) ===
run-core-tests: 516 units across 3 shards + 46 serial
  shard 0: 158 tests in  359.2s  ok
  shard 1: 156 tests in  357.9s  ok
  shard 2: 163 tests in  355.8s  ok
  shard 3:  46 tests in  152.9s  ok
run-core-tests: 523 tests in 512.2s (OK)
=== serial run (agreement) ===
test_codex_flag_opt_out_respected (__main__.AgentHooksTest) ... dw hook: codex_hooks is explicitly false in /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.wg14ozff/config.toml; respecting the opt-out
ok
test_emit_never_raises_on_garbage (__main__.AgentHooksTest) ... ok
test_emit_quiet_guard_and_unknown_event (__main__.AgentHooksTest) ... ok
test_emit_whitelists_and_never_leaks_content (__main__.AgentHooksTest) ... ok
test_install_is_idempotent (__main__.AgentHooksTest) ... ok
test_status_reports_per_event (__main__.AgentHooksTest) ... ok
test_uninstall_is_surgical (__main__.AgentHooksTest) ... ok
test_measurements_never_confuse_zero_unbounded_unknown_or_na (__main__.BoundedActionsProjectionTest) ... ok
test_program_request_and_remote_guidance_never_mint_authority (__main__.BoundedActionsProjectionTest) ... ok
test_run_decisions_blockers_permission_and_actions_are_closed (__main__.BoundedActionsProjectionTest) ... ok
test_front_door_names_scope_three_modes_effects_and_permissions (__main__.DeliverySetupTest) ... ok
test_human_cli_and_http_render_the_same_choice_and_readiness (__main__.DeliverySetupTest) ... ok
test_missing_or_invalid_inputs_name_the_delivery_decision_and_correction (__main__.DeliverySetupTest) ... ok
test_setup_and_cancel_model_are_repeatable_and_write_nothing (__main__.DeliverySetupTest) ... ok
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
test_phase_advance_is_one_guarded_summary_pointer_and_header_plan (__main__.DwCoreTest) ... ok
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
test_workbench_step_front_door_keeps_review_and_act_separate (__main__.DwCoreTest) ... ok
test_workbench_story_route_serves_story_detail (__main__.DwCoreTest) ... ok
test_worklog_absent_root_is_optional_not_error (__main__.DwCoreTest) ... ok
test_worklog_endpoint_containment_and_omission (__main__.DwCoreTest) ... ok
test_write_containment (__main__.DwCoreTest) ... ok
test_append_only_and_never_raises (__main__.EventsTest) ... ok
test_content_audit_rogue_keys_dropped (__main__.EventsTest) ... ok
test_gate_refusal_carries_its_rule (__main__.EventsTest) ... ok
test_rail_moments_emit (__main__.EventsTest) ... ok
test_cli_help_uses_the_shared_task_language (__main__.EverydayPresentationTest) ... ok
test_real_presenters_match_versioned_human_snapshots (__main__.EverydayPresentationTest) ... ok
test_runtime_catalog_matches_the_reviewed_contract (__main__.EverydayPresentationTest) ... ok
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
test_repair_and_recovery_use_only_canonical_run_facts (__main__.LiveProgressProjectionTest) ... ok
test_browse_refusals_match_core (__main__.MCPServerTest) ... ok
test_browse_tools_agree_with_core (__main__.MCPServerTest) ... ok
test_browse_tools_are_read_only (__main__.MCPServerTest) ... ok
test_check_and_next_agree_with_core (__main__.MCPServerTest) ... ok
test_core_refusal_becomes_tool_error (__main__.MCPServerTest) ... ok
test_initialize_pins_protocol_version (__main__.MCPServerTest) ... ok
test_mutation_tools_require_their_params (__main__.MCPServerTest) ... ok
test_no_rails_is_a_discoverable_refusal (__main__.MCPServerTest) ... ok
test_notifications_get_no_reply_and_unknown_methods_error (__main__.MCPServerTest) ... ok
test_status_agrees_with_core_and_attention_is_data (__main__.MCPServerTest) ... ok
test_step_tools_are_exact_core_adapters (__main__.MCPServerTest) ... ok
test_story_status_flip_writes_what_the_core_writes (__main__.MCPServerTest) ... ok
test_story_status_refusal_matches_core (__main__.MCPServerTest) ... ok
test_tools_list_matches_contract_and_excludes_attestation (__main__.MCPServerTest) ... ok
test_unknown_tool_and_unknown_params (__main__.MCPServerTest) ... ok
test_cli_invalid_score_returns_pointer_diagnostics_and_exit_one (__main__.OrchestrationCompilerTest) ... ok
test_cli_list_show_validate_and_simulate_share_core_documents (__main__.OrchestrationCompilerTest) ... ok
test_duplicate_json_keys_nonfinite_numbers_and_escaped_symlinks_refuse (__main__.OrchestrationCompilerTest) ... ok
test_exact_keys_duplicate_ids_and_dangling_references_refuse (__main__.OrchestrationCompilerTest) ... ok
test_impossible_capabilities_and_forbidden_rail_authority_refuse (__main__.OrchestrationCompilerTest) ... ok
test_minimal_and_custom_role_round_trip (__main__.OrchestrationCompilerTest) ... ok
test_nudge_rules_compile_simulate_and_refuse_exactly (__main__.OrchestrationCompilerTest) ... ok
test_output_producer_type_and_order_checks_refuse (__main__.OrchestrationCompilerTest) ... ok
test_representative_preset_compiles_and_simulates_parallel_fan_in (__main__.OrchestrationCompilerTest) ... ok
test_resource_locks_and_concurrency_make_simulation_deterministic (__main__.OrchestrationCompilerTest) ... ok
test_semantic_hash_ignores_object_key_order_and_layout_only (__main__.OrchestrationCompilerTest) ... ok
test_success_cycles_and_unbounded_failure_policies_refuse (__main__.OrchestrationCompilerTest) ... ok
test_unsafe_paths_shell_strings_and_undeclared_runners_refuse (__main__.OrchestrationCompilerTest) ... ok
test_activity_transitions_are_ledgered_once_per_change (__main__.OrchestrationConductorTest) ... ok
test_adapters_reject_score_semantics_driver_config_and_argv (__main__.OrchestrationConductorTest) ... ok
test_builtin_file_schema_diff_and_rail_checks_share_receipts (__main__.OrchestrationConductorTest) ... ok
test_cancellation_interrupts_a_live_contained_check (__main__.OrchestrationConductorTest) ... ok
test_cancellation_precedes_interrupt_and_expiry_starts_nothing (__main__.OrchestrationConductorTest) ... ok
test_checkpoint_alias_cannot_decide_a_live_nudge_request (__main__.OrchestrationConductorTest) ... ok
test_cli_and_mcp_controls_require_fresh_preview_tokens (__main__.OrchestrationConductorTest) ... ok
test_cli_run_tail_matches_the_ledger (__main__.OrchestrationConductorTest) ... ok
test_crash_after_check_recovers_without_rerunning_command (__main__.OrchestrationConductorTest) ... ok
test_crash_after_driver_start_recovers_without_duplicate_launch (__main__.OrchestrationConductorTest) ... ok
test_exact_command_check_is_contained_and_write_scope_fails (__main__.OrchestrationConductorTest) ... ok
test_failed_nudge_attempt_runs_its_named_approval_policy (__main__.OrchestrationConductorTest) ... ok
test_failed_repair_follows_its_abort_policy (__main__.OrchestrationConductorTest) ... ok
test_failure_pause_and_named_approval_are_ledger_states (__main__.OrchestrationConductorTest) ... ok
test_full_fanout_check_repair_retry_and_terminal_handoff (__main__.OrchestrationConductorTest) ... ok
test_installed_cli_tick_and_bounded_supervision_share_the_core (__main__.OrchestrationConductorTest) ... ok
test_invalid_artifact_retries_then_exhausts_without_fan_in (__main__.OrchestrationConductorTest) ... ok
test_ledger_tail_is_exact_derivable_and_content_safe (__main__.OrchestrationConductorTest) ... ok
test_mission_control_run_summary_is_content_safe (__main__.OrchestrationConductorTest) ... ok
test_notifications_delivery_ceiling_parity_and_branch_opt_in (__main__.OrchestrationConductorTest) ... ok
test_notifications_derive_ack_and_correlate (__main__.OrchestrationConductorTest) ... ok
test_nudge_authority_rides_the_plan_and_grant (__main__.OrchestrationConductorTest) ... ok
test_nudge_budget_exhaustion_is_a_recorded_blocked_stop (__main__.OrchestrationConductorTest) ... ok
test_nudge_crash_after_delivery_recovers_without_duplicate (__main__.OrchestrationConductorTest) ... ok
test_nudge_receptivity_gates_live_sessions (__main__.OrchestrationConductorTest) ... ok
test_nudge_refusals_are_distinct_recorded_and_deduped (__main__.OrchestrationConductorTest) ... ok
test_nudge_wakes_awaiting_certification_and_delivers_at_most_once (__main__.OrchestrationConductorTest) ... ok
test_nudged_reattempt_supersedes_its_stored_artifact (__main__.OrchestrationConductorTest) ... ok
test_outstanding_request_republishes_once_per_restart_generation (__main__.OrchestrationConductorTest) ... ok
test_pure_schedule_is_stable_and_respects_resource_groups (__main__.OrchestrationConductorTest) ... ok
test_rail_uses_fresh_step_lease_and_stale_action_never_starts (__main__.OrchestrationConductorTest) ... ok
test_request_expiry_is_a_recorded_refusal_and_notification (__main__.OrchestrationConductorTest) ... ok
test_request_preview_and_apply_are_exact_across_interop_surfaces (__main__.OrchestrationConductorTest) ... ok
test_run_act_token_binds_action_reason_decision_and_state (__main__.OrchestrationConductorTest) ... ok
test_run_interop_compiler_plan_projection_and_preview_are_exact (__main__.OrchestrationConductorTest) ... ok
test_run_stream_is_explicit_bounded_and_injection_safe (__main__.OrchestrationConductorTest) ... ok
test_run_view_exposes_request_age_schema_and_inspect_only_lineage (__main__.OrchestrationConductorTest) ... ok
test_run_view_is_pure_rich_and_excludes_private_semantics (__main__.OrchestrationConductorTest) ... ok
test_run_view_static_contract_ha
[PMO_EVIDENCE_OUTPUT_TRUNCATED]
```

### Captured run — 2026-07-26T20:59:54Z

- **Command:** `bash -lc set -e
uptime
echo '=== sharded run 1 ==='
python3 pmo-roadmap/tests/run-core-tests.py
echo '=== sharded run 2 (stability) ==='
python3 pmo-roadmap/tests/run-core-tests.py
echo '=== sharded, different shard count (3) ==='
python3 pmo-roadmap/tests/run-core-tests.py --shards 3
echo '=== serial run (agreement) ==='
python3 pmo-roadmap/tests/run-core-tests.py --serial
echo '=== runner unit cases ==='
python3 -m unittest pmo-roadmap/tests/dw-core-tests.py -k ShardRunnerTest
echo '=== coverage identity: units vs module load ==='
python3 -c "
import importlib.util, sys, unittest
spec=importlib.util.spec_from_file_location('r','pmo-roadmap/tests/run-core-tests.py')
r=importlib.util.module_from_spec(spec); spec.loader.exec_module(r)
units=r.discover_units(); m=sys.modules['dw_core_tests_shard']; loader=unittest.TestLoader()
def flat(s):
    for x in s:
        if isinstance(x, unittest.TestSuite): yield from flat(x)
        else: yield x.id()
ids=[]
for u in units: ids.extend(flat(loader.loadTestsFromNames([u], m)))
full=list(flat(loader.loadTestsFromModule(m)))
assert sorted(ids)==sorted(full), 'sharded discovery differs from a module load'
assert len(ids)==len(set(ids)), 'a test would run more than once'
print('coverage identical:', len(ids), 'tests from', len(units), 'units, no duplicates')
"
echo '=== floor 3.9 ==='
/usr/bin/python3 -m py_compile pmo-roadmap/tests/run-core-tests.py
/usr/bin/python3 pmo-roadmap/tests/run-core-tests.py --list
bash pmo-roadmap/tests/docs-lint.sh
bash pmo-roadmap/tests/canon-lint.sh
bash pmo-roadmap/update.sh . --check
pmo-roadmap/bin/dw check work-log-automation
git diff --check`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** 2aefb1fb83111d3d74c6d8fb0dc51da3b83a42bd

```text
14:59  up 3 days,  4:25, 7 users, load averages: 6.14 5.56 6.85
=== sharded run 1 ===
run-core-tests: 516 units across 8 shards + 46 serial
  shard 0:  61 tests in  185.5s  ok
  shard 1:  62 tests in  160.0s  ok
  shard 2:  57 tests in  177.0s  ok
  shard 3:  61 tests in  202.5s  ok
  shard 4:  63 tests in  197.4s  ok
  shard 5:  57 tests in  206.2s  ok
  shard 6:  57 tests in  206.2s  ok
  shard 7:  59 tests in  211.9s  ok
  shard 8:  46 tests in  567.8s  ok
run-core-tests: 523 tests in 779.7s (OK)
=== sharded run 2 (stability) ===

======================================================================
shard 1 output
======================================================================
..................................F...........................
======================================================================
FAIL: test_rule_council_meta_audits_and_ingests_durable_obligation (dw_core_tests_shard.ProgramConductorTest)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/Users/karol/dev/code/delivery-workbench/pmo-roadmap/tests/dw-core-tests.py", line 13039, in test_rule_council_meta_audits_and_ingests_durable_obligation
    self.assertEqual((result["state"], result["stop"]),
AssertionError: Tuples differ: ('ready', 'time-ceiling') != ('story-certified', 'checkpoint')

First differing element 0:
'ready'
'story-certified'

- ('ready', 'time-ceiling')
+ ('story-certified', 'checkpoint')

----------------------------------------------------------------------
Ran 62 tests in 618.910s

FAILED (failures=1)
dw hook: claude — 4 installed, 0 already present in /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.p01s4q92/settings.json
dw hook: claude — 4 removed from /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.p01s4q92/settings.json
##shard-summary {"ran": 62, "failures": 1, "errors": 0, "skipped": 0}

run-core-tests: 516 units across 8 shards + 46 serial
  shard 0:  61 tests in  746.0s  ok
  shard 1:  62 tests in  621.0s  FAIL
  shard 2:  57 tests in  740.1s  ok
  shard 3:  61 tests in  798.6s  ok
  shard 4:  63 tests in  762.2s  ok
  shard 5:  57 tests in  783.2s  ok
  shard 6:  57 tests in  782.4s  ok
  shard 7:  59 tests in  816.4s  ok
  shard 8:  46 tests in  365.0s  ok
run-core-tests: 523 tests in 1181.6s (FAILED)
```
