# Evidence - WLA-30-01

- **Story:** WLA-30-01 - Contract the front-door journey
- **Status:** done
- **Date:** 2026-07-27

## Proof

Delivered as `pmo-roadmap/lib/dw_pmo/setup_proposal.py` — the versioned
`delivery-workbench-setup-proposal@1` contract (closed fields, bounds on
every string and list, JSON-pointer refusals, mandatory false inertness
fields, provenance on every item, tracked vs local content split, a
six-state journey with one revision edge, canonical byte-stable JSON,
and a duplicate-key-refusing loader) — with the contract document at
`docs/setup-proposal.md` and 16 unit tests in
`pmo-roadmap/tests/setup_proposal_tests.py`, wired into the core suite
the same way the grounding and knowledge tests are. Implementation by
Sol (GPT-5.6) under orchestration; reviewed line by line before capture.

Three captured runs prove the story, all authoritative:

1. The **live demo** (first run below) builds a real greenfield
   proposal, proves canonical byte-stability across dump/load/dump,
   walks the full journey forward plus the reviewed-to-draft revision
   edge, exercises six refusals by name, and ends with the purity check
   (validation creates no files).
2. The **unit battery** (second run) — 16 tests covering acceptance,
   refusal, provenance, credential rejection, journey transitions, and
   module purity.
3. The **full core suite** (final run) — the whole regression battery
   including the newly wired contract tests, green on the shipping
   interpreter.

Honest iteration: the first full-suite capture below exited 1 on one
pre-existing failure unrelated to this story — the WLA-27-03
CLI/in-process status parity test, which caught the doctor python3
check mixing the PATH binary's path with the running interpreter's
version (visible only on a desk where the suite runs under
/usr/bin/python3 with Homebrew python3 on PATH; reproduced on a clean
HEAD worktree before any story-01 change). Fixed as the separate rider
commit "Report the PATH python3's own version in doctor checks"; the
final full-suite capture after that fix is the authoritative battery.
Its output is truncated by the capture's output bound (recorded
phase-29 friction); the machine-verified exit code 0 in the capture
header is the authoritative fact.

### Captured run — 2026-07-27T22:57:54Z

- **Command:** `/usr/bin/python3 /private/tmp/claude-501/-Users-karol-dev-code-delivery-workbench/c4dc647a-d1b5-41ba-83af-e7d70e987de9/scratchpad/demo-setup-proposal.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** a53d832b5aaeca2f599e3988e0db4c2cecdb38d9

```text
ACCEPTED greenfield proposal: 1871 canonical bytes
BYTE-STABLE across dump/load/dump: yes
JOURNEY forward walk: uninitialized -> rails-ready -> draft -> reviewed -> configured -> grant-previewed
JOURNEY revision edge reviewed->draft: draft
REFUSED unknown top-level field:       /surprise: unknown field
REFUSED unsupported schema:            /schema: unsupported setup proposal schema
REFUSED inertness starts_work=true:    /starts_work: must be false
REFUSED credential-shaped driver key:  /local_content/driver_bindings/sol-implementer: may not contain credential, token, password, secret, or API-key fields
REFUSED missing provenance:            /project/provenance: field is required
REFUSED journey jump draft->grant-previewed: /state: transition from draft to grant-previewed is not permitted
PURITY: validation created no files in an empty cwd
demo: ok
```

### Captured run — 2026-07-27T22:57:54Z

- **Command:** `/usr/bin/python3 pmo-roadmap/tests/setup_proposal_tests.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** a53d832b5aaeca2f599e3988e0db4c2cecdb38d9

```text
test_all_provenance_vocabularies_are_accepted (__main__.SetupProposalContractTest) ... ok
test_canonical_serialization_is_byte_stable_across_round_trip (__main__.SetupProposalContractTest) ... ok
test_closed_fields_refuse_at_top_level_and_nested_paths (__main__.SetupProposalContractTest) ... ok
test_driver_binding_rejects_credential_pattern_at_any_key (__main__.SetupProposalContractTest) ... ok
test_duplicate_json_keys_and_non_finite_numbers_refuse (__main__.SetupProposalContractTest) ... ok
test_each_inertness_field_is_required_and_exactly_false (__main__.SetupProposalContractTest) ... ok
test_missing_and_unknown_provenance_refuse (__main__.SetupProposalContractTest) ... ok
test_optional_embedded_policy_documents_are_opaque_but_bounded_objects (__main__.SetupProposalContractTest) ... ok
test_string_list_and_opaque_document_bounds_refuse (__main__.SetupProposalContractTest) ... ok
test_unresolved_questions_are_explicit_bounded_provenanced_items (__main__.SetupProposalContractTest) ... ok
test_unsupported_schema_and_missing_project_identity_refuse (__main__.SetupProposalContractTest) ... ok
test_load_and_validate_create_no_files (__main__.SetupProposalFitnessTest) ... ok
test_module_is_pure_stdlib_offline_and_non_spawning (__main__.SetupProposalFitnessTest) ... ok
test_every_other_transition_refuses (__main__.SetupProposalJourneyTest) ... ok
test_fixture_walks_all_six_named_states (__main__.SetupProposalJourneyTest) ... ok
test_validation_never_moves_state_implicitly (__main__.SetupProposalJourneyTest) ... ok

----------------------------------------------------------------------
Ran 16 tests in 0.008s

OK
```

### Captured run — 2026-07-27T22:58:10Z

- **Command:** `/usr/bin/python3 pmo-roadmap/tests/dw-core-tests.py`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** a53d832b5aaeca2f599e3988e0db4c2cecdb38d9

```text
test_codex_flag_opt_out_respected (__main__.AgentHooksTest) ... dw hook: codex_hooks is explicitly false in /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.6qakrnd0/config.toml; respecting the opt-out
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
test_human_cli_and_http_render_the_same_choice_and_readiness (__main__.DeliverySetupTest) ... FAIL
test_missing_or_invalid_inputs_name_the_delivery_decision_and_correction (__main__.DeliverySetupTest) ... ok
test_setup_and_cancel_model_are_repeatable_and_write_nothing (__main__.DeliverySetupTest) ... ok
test_no_fact_is_read_twice_inside_one_observation (__main__.DerivationReadsTest) ... ok
test_one_observation_reads_head_once_even_with_a_remote (__main__.DerivationReadsTest) ... ok
test_separate_observations_still_re_read_everything (__main__.DerivationReadsTest) ... ok
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
test_fix_hooks_path_is_noop_on_relative_and_refuses_foreign (__main__.GateTest) ... ok
test_fix_hooks_path_normalizes_same_clone_absolute (__main__.GateTest) ... ok
test_forced_full_tier_config (__main__.GateTest) ... ok
test_head_mismatch_after_history_moves (__main__.GateTest) ... ok
test_hooks_path_foreign_absolute_still_fails (__main__.GateTest) ... ok
test_hooks_path_same_clone_absolute_is_healthy_with_hint (__main__.GateTest) ... ok
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
test_check_warnings_are_greppable_and_do_not_change_exit_code (grounding_tests.GroundingIntegrationTest) ... ok
test_cli_and_mcp_are_byte_identical_and_read_only (grounding_tests.GroundingIntegrationTest) ... ok
test_fixture_story_classifies_verified_new_and_misspelled_with_evidence (grounding_tests.GroundingIntegrationTest) ... ok
test_gap_text_match_prevents_explicit_new_classification (grounding_tests.GroundingIntegrationTest) ... ok
test_stale_map_refuses_instead_of_answering (grounding_tests.GroundingIntegrationTest) ... ok
test_story_table_parser_is_unchanged_by_optional_story_section (grounding_tests.GroundingIntegrationTest) ... ok
test_commented_template_example_is_not_parsed_as_real_hints (grounding_tests.GroundingUnitTest) ... ok
test_parser_requires_nested_lists_and_preserves_explicit_new_marker (grounding_tests.GroundingUnitTest) ... ok
test_suggestions_are_bounded_by_name_distance (grounding_tests.GroundingUnitTest) ... ok
test_absent_and_explicit_zero_are_distinct_end_to_end_values (knowledge_packet_tests.HonestUsageTest) ... ok
test_budget_drops_whole_lowest_scored_items_and_names_them (knowledge_packet_tests.KnowledgePacketTest) ... ok
test_hint_free_packet_is_explicit_and_does_not_guess (knowledge_packet_tests.KnowledgePacketTest) ... ok
test_same_inputs_are_byte_identical_with_stable_ties (knowledge_packet_tests.KnowledgePacketTest) ... ok
test_stale_grounding_is_a_typed_refusal_not_empty_packet (knowledge_packet_tests.KnowledgePacketTest) ... ok
test_delivery_shape_is_only_ledger_identifiers_and_counts (knowledge_writeback_tests.KnowledgeWritebackTest) ... ok
test_lesson_inventory_lists_provenance_and_supersession (knowledge_writeback_tests.KnowledgeWritebackTest) ... ok
test_only_success_terminal_persists_and_cap_is_per_run (knowledge_writeback_tests.KnowledgeWritebackTest) ... ok
test_second_packet_prefers_superseding_lesson_and_keeps_chain (knowledge_writeback_tests.KnowledgeWritebackTest) ... ok
test_terminal_retry_deduplicates_exact_records (knowledge_writeback_tests.KnowledgeWritebackTest) ... ok
test_typed_output_is_closed_and_bounded (knowledge_writeback_tests.KnowledgeWritebackTest) ... ok
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
test_nudge
[PMO_EVIDENCE_OUTPUT_TRUNCATED]
```

### Captured run — 2026-07-27T23:12:37Z

- **Command:** `/usr/bin/python3 pmo-roadmap/tests/dw-core-tests.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 55b44d0899a4c007669a9e1be442b3c2147b30d3

```text
test_codex_flag_opt_out_respected (__main__.AgentHooksTest) ... dw hook: codex_hooks is explicitly false in /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.iuujksne/config.toml; respecting the opt-out
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
test_no_fact_is_read_twice_inside_one_observation (__main__.DerivationReadsTest) ... ok
test_one_observation_reads_head_once_even_with_a_remote (__main__.DerivationReadsTest) ... ok
test_separate_observations_still_re_read_everything (__main__.DerivationReadsTest) ... ok
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
test_fix_hooks_path_is_noop_on_relative_and_refuses_foreign (__main__.GateTest) ... ok
test_fix_hooks_path_normalizes_same_clone_absolute (__main__.GateTest) ... ok
test_forced_full_tier_config (__main__.GateTest) ... ok
test_head_mismatch_after_history_moves (__main__.GateTest) ... ok
test_hooks_path_foreign_absolute_still_fails (__main__.GateTest) ... ok
test_hooks_path_same_clone_absolute_is_healthy_with_hint (__main__.GateTest) ... ok
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
test_check_warnings_are_greppable_and_do_not_change_exit_code (grounding_tests.GroundingIntegrationTest) ... ok
test_cli_and_mcp_are_byte_identical_and_read_only (grounding_tests.GroundingIntegrationTest) ... ok
test_fixture_story_classifies_verified_new_and_misspelled_with_evidence (grounding_tests.GroundingIntegrationTest) ... ok
test_gap_text_match_prevents_explicit_new_classification (grounding_tests.GroundingIntegrationTest) ... ok
test_stale_map_refuses_instead_of_answering (grounding_tests.GroundingIntegrationTest) ... ok
test_story_table_parser_is_unchanged_by_optional_story_section (grounding_tests.GroundingIntegrationTest) ... ok
test_commented_template_example_is_not_parsed_as_real_hints (grounding_tests.GroundingUnitTest) ... ok
test_parser_requires_nested_lists_and_preserves_explicit_new_marker (grounding_tests.GroundingUnitTest) ... ok
test_suggestions_are_bounded_by_name_distance (grounding_tests.GroundingUnitTest) ... ok
test_absent_and_explicit_zero_are_distinct_end_to_end_values (knowledge_packet_tests.HonestUsageTest) ... ok
test_budget_drops_whole_lowest_scored_items_and_names_them (knowledge_packet_tests.KnowledgePacketTest) ... ok
test_hint_free_packet_is_explicit_and_does_not_guess (knowledge_packet_tests.KnowledgePacketTest) ... ok
test_same_inputs_are_byte_identical_with_stable_ties (knowledge_packet_tests.KnowledgePacketTest) ... ok
test_stale_grounding_is_a_typed_refusal_not_empty_packet (knowledge_packet_tests.KnowledgePacketTest) ... ok
test_delivery_shape_is_only_ledger_identifiers_and_counts (knowledge_writeback_tests.KnowledgeWritebackTest) ... ok
test_lesson_inventory_lists_provenance_and_supersession (knowledge_writeback_tests.KnowledgeWritebackTest) ... ok
test_only_success_terminal_persists_and_cap_is_per_run (knowledge_writeback_tests.KnowledgeWritebackTest) ... ok
test_second_packet_prefers_superseding_lesson_and_keeps_chain (knowledge_writeback_tests.KnowledgeWritebackTest) ... ok
test_terminal_retry_deduplicates_exact_records (knowledge_writeback_tests.KnowledgeWritebackTest) ... ok
test_typed_output_is_closed_and_bounded (knowledge_writeback_tests.KnowledgeWritebackTest) ... ok
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
test_nudge_r
[PMO_EVIDENCE_OUTPUT_TRUNCATED]
```
