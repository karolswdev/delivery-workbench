# Evidence - WLA-25-09

- **Story:** WLA-25-09 - Prove the outward loop end to end
- **Status:** done
- **Date:** 2026-07-22

## Proof

The Python-floor wheel exit exam composes the entire outward loop in one fresh
consumer repository and a local bare Git forge. It proves:

- a granted run reaches terminal handoff; only the fixture operator certifies,
  commits, and pushes;
- the observer records the pushed commit as a clean, same-repository,
  same-branch fast-forward fact and rebinds the still-exact story/run without
  acquiring forge or tree authority;
- red CI delivers one standing-rule nudge, a planted crash after receipt/claim
  but before driver start restarts with exactly one repair start, and green CI
  clears the failure;
- a changes-requested signal delivers the second nudge, failed review repair
  follows its named approval policy, three installed-CLI restarts republish the
  outstanding request exactly once, stale correlation refuses without
  consuming it, and the correct typed decision crosses the exact HTTP request
  boundary;
- CLI, SSE, and ledger replay match exactly; notification projections agree
  across CLI/MCP/HTTP; delivery and acknowledgement are receipted; and the
  authority-free observer, stream, and every red path leave the fixture forge,
  operator tree, and workspaces unchanged.

The final packaged report was:

```json
{"certification":"operator-only","duplicate_nudges":0,"duplicate_starts":0,"external_rebind":true,"nudges":2,"observer_side_effects":0,"request_republishes":1,"state":"awaiting-certification","stream_matches_ledger":true,"wheel_version":"dw 1.14.0"}
```

The exam also proves the precise refusals for no standing grant, exhausted
nudge budget, blocked/unknown sessions, replay deduplication, stale
correlation, revoked request expiry, and an authority-free stream. Three
composition gaps found by the first red captures are fixed and regression
tested: a clean operator push can rebind a still-exact run, a nudge-woken run
can reach terminal handoff again, and a failed nudge-started repair executes
its declared failure policy instead of becoming dormant.

The authenticated Claude Code specimen in
[WLA-25-07 evidence](./evidence-story-07.md) supplies the separate live harness
round-trip: the real non-interactive driver ran once, received a fixture
CI-failed nudge through the neutral seam, reran with `@nudge` context, and
re-terminaled under the same bounded grant. Fixture output remains the CI
oracle.

## Owner-waived phone supplement

The deterministic package exam exercises notification delivery,
acknowledgement, restart-safe republish, and a typed decision through the same
generic request core used by Telegram. A separate owner-bound phone specimen
was requested as a confidence supplement. A clean local run
`run-7a3e3368b678ccf99d4b32db` opened a real outstanding checkpoint request,
but no owner-bound `/pair` receipt arrived. On 2026-07-22 the owner explicitly
waived that device leg and directed Phase 25 to close. The run was revoked with
reason `owner waived phone specimen for Phase 25 close`; replay shows state
`revoked`, control generation 1, no outstanding request, and the historical
request status `expired`.

This is deliberately recorded as **unperformed, not passed**. It changes no
claim about Telegram transport or per-person consent; those remain supported by
the deterministic interface/conformance suites and their earlier evidence.

## Verification matrix

- Core suite: 338/338 on the local interpreter and 338/338 on the declared
  `/usr/bin/python3` 3.9 floor.
- Python 3.9 package smoke: sdist/wheel build, fresh install, guided exit,
  deliberate-step exit, Phase-24 orchestration exam, and the new Phase-25
  outward-loop exam all passed.
- Telegram: 152 interface tests and 10/10 architecture-fitness tests; the
  expected optional Pillow/`tomllib` skips remained skips on Python 3.9.
- Workbench: explorer smoke and 32 desktop/mobile viewport renders passed.
- Docs lint (432 Markdown files), docs snippets, canon lint, orchestration/MCP/
  step interop, agent surface, plugin validation, adoption, gate parity,
  roadmap CLI, work-log MVP, contributor flow, upgrade path, range verification,
  vendored-rail parity, roadmap check, and diff hygiene passed.
- Homebrew smoke correctly abstained because the operator already has the
  formula installed; no user installation was removed. Clean-machine macOS CI
  remains wired for that environment-specific proof.

### Captured run — 2026-07-22T14:58:37Z

- **Command:** `bash -o pipefail -c
set -e
python3 pmo-roadmap/tests/dw-core-tests.py
/usr/bin/python3 pmo-roadmap/tests/dw-core-tests.py
bash pmo-roadmap/tests/package-smoke.sh
python3 pmo-roadmap/tests/telegram-interface-tests.py
python3 pmo-roadmap/tests/telegram-fitness-tests.py
bash pmo-roadmap/tests/docs-lint.sh
bash pmo-roadmap/tests/docs-snippet-smoke.sh
bash pmo-roadmap/tests/canon-lint.sh
bash pmo-roadmap/tests/orchestration-interop.sh
bash pmo-roadmap/tests/step-interop.sh
bash pmo-roadmap/tests/mcp-server.sh
bash pmo-roadmap/tests/workbench-explorer.sh
bash pmo-roadmap/tests/workbench-ui-smoke.sh
bash pmo-roadmap/tests/agent-surface.sh
bash pmo-roadmap/tests/plugin-validate.sh
./pmo-roadmap/update.sh . --check
./.githooks/dw check work-log-automation
git diff --check
`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** aa2d974fc009a1d7faea1b204386043ea9ccbef1

```text
test_codex_flag_opt_out_respected (__main__.AgentHooksTest.test_codex_flag_opt_out_respected) ... dw hook: codex_hooks is explicitly false in /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.yyvnzkje/config.toml; respecting the opt-out
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
test_nudge_rules_compile_simulate_and_refuse_exactly (__main__.OrchestrationCompilerTest.test_nudge_rules_compile_simulate_and_refuse_exactly) ... ok
test_output_producer_type_and_order_checks_refuse (__main__.OrchestrationCompilerTest.test_output_producer_type_and_order_checks_refuse) ... ok
test_representative_preset_compiles_and_simulates_parallel_fan_in (__main__.OrchestrationCompilerTest.test_representative_preset_compiles_and_simulates_parallel_fan_in) ... ok
test_resource_locks_and_concurrency_make_simulation_deterministic (__main__.OrchestrationCompilerTest.test_resource_locks_and_concurrency_make_simulation_deterministic) ... ok
test_semantic_hash_ignores_object_key_order_and_layout_only (__main__.OrchestrationCompilerTest.test_semantic_hash_ignores_object_key_order_and_layout_only) ... ok
test_success_cycles_and_unbounded_failure_policies_refuse (__main__.OrchestrationCompilerTest.test_success_cycles_and_unbounded_failure_policies_refuse) ... ok
test_unsafe_paths_shell_strings_and_undeclared_runners_refuse (__main__.OrchestrationCompilerTest.test_unsafe_paths_shell_strings_and_undeclared_runners_refuse) ... ok
test_activity_transitions_are_ledgered_once_per_change (__main__.OrchestrationConductorTest.test_activity_transitions_are_ledgered_once_per_change) ... ok
test_adapters_reject_score_semantics_driver_config_and_argv (__main__.OrchestrationConductorTest.test_adapters_reject_score_semantics_driver_config_and_argv) ... ok
test_builtin_file_schema_diff_and_rail_checks_share_receipts (__main__.OrchestrationConductorTest.test_builtin_file_schema_diff_and_rail_checks_share_receipts) ... ok
test_cancellation_interrupts_a_live_contained_check (__main__.OrchestrationConductorTest.test_cancellation_interrupts_a_live_contained_check) ... ok
test_cancellation_precedes_interrupt_and_expiry_starts_nothing (__main__.OrchestrationConductorTest.test_cancellation_precedes_interrupt_and_expiry_starts_nothing) ... ok
test_checkpoint_alias_cannot_decide_a_live_nudge_request (__main__.OrchestrationConductorTest.test_checkpoint_alias_cannot_decide_a_live_nudge_request) ... ok
test_cli_and_mcp_controls_require_fresh_preview_tokens (__main__.OrchestrationConductorTest.test_cli_and_mcp_controls_require_fresh_preview_tokens) ... ok
test_cli_run_tail_matches_the_ledger (__main__.OrchestrationConductorTest.test_cli_run_tail_matches_the_ledger) ... ok
test_crash_after_check_recovers_without_rerunning_command (__main__.OrchestrationConductorTest.test_crash_after_check_recovers_without_rerunning_command) ... ok
test_crash_after_driver_start_recovers_without_duplicate_launch (__main__.OrchestrationConductorTest.test_crash_after_driver_start_recovers_without_duplicate_launch) ... ok
test_exact_command_check_is_contained_and_write_scope_fails (__main__.OrchestrationConductorTest.test_exact_command_check_is_contained_and_write_scope_fails) ... ok
test_failed_nudge_attempt_runs_its_named_approval_policy (__main__.OrchestrationConductorTest.test_failed_nudge_attempt_runs_its_named_approval_policy) ... ok
test_failed_repair_follows_its_abort_policy (__main__.OrchestrationConductorTest.test_failed_repair_follows_its_abort_policy) ... ok
test_failure_pause_and_named_approval_are_ledger_states (__main__.OrchestrationConductorTest.test_failure_pause_and_named_approval_are_ledger_states) ... ok
test_full_fanout_check_repair_retry_and_terminal_handoff (__main__.OrchestrationConductorTest.test_full_fanout_check_repair_retry_and_terminal_handoff) ... ok
test_installed_cli_tick_and_bounded_supervision_share_the_core (__main__.OrchestrationConductorTest.test_installed_cli_tick_and_bounded_supervision_share_the_core) ... ok
test_invalid_artifact_retries_then_exhausts_without_fan_in (__main__.OrchestrationConductorTest.test_invalid_artifact_retries_then_exhausts_without_fan_in) ... ok
test_ledger_tail_is_exact_derivable_and_content_safe (__main__.OrchestrationConductorTest.test_ledger_tail_is_exact_derivable_and_content_safe) ... ok
test_mission_control_run_summary_is_content_safe (__main__.OrchestrationConductorTest.test_mission_control_run_summary_is_content_safe) ... ok
test_notifications_delivery_ceiling_parity_and_branch_opt_in (__main__.OrchestrationConductorTest.test_notifications_delivery_ceiling_parity_and_branch_opt_in) ... ok
test_notifications_derive_ack_and_correlate (__main__.OrchestrationConductorTest.test_notifications_derive_ack_and_correlate) ... ok
test_nudge_authority_rides_the_plan_and_grant (__main__.OrchestrationConductorTest.test_nudge_authority_rides_the_plan_and_grant) ... ok
test_nudge_budget_exhaustion_is_a_recorded_blocked_stop (__main__.OrchestrationConductorTest.test_nudge_budget_exhaustion_is_a_recorded_blocked_stop) ... ok
test_nudge_crash_after_delivery_recovers_without_duplicate (__main__.OrchestrationConductorTest.test_nudge_crash_after_delivery_recovers_without_duplicate) ... ok
test_nudge_receptivity_gates_live_sessions (__main__.OrchestrationConductorTest.test_nudge_receptivity_gates_live_sessions) ... ok
test_nudge_refusals_are_distinct_recorded_and_deduped (__main__.OrchestrationConductorTest.test_nudge_refusals_are_distinct_recorded_and_deduped) ... ok
test_nudge_wakes_awaiting_certification_and_delivers_at_most_once (__main__.OrchestrationConductorTest.test_nudge_wakes_awaiting_certification_and_delivers_at_most_once) ... ok
test_nudged_reattempt_supersedes_its_stored_artifact (__main__.OrchestrationConductorTest.test_nudged_reattempt_supersedes_its_stored_artifact) ... ok
test_outstanding_request_republishes_once_per_restart_generation (__main__.OrchestrationConductorTest.test_outstanding_request_republishes_once_per_restart_generation) ... ok
test_pure_schedule_is_stable_and_respects_resource_groups (__main__.OrchestrationConductorTest.test_pure_schedule_is_stable_and_respects_resource_groups) ... ok
test_rail_uses_fresh_step_lease_and_stale_action_never_starts (__main__.OrchestrationConductorTest.test_rail_uses_fresh_step_lease_and_stale_action_never_starts) ... ok
test_request_expiry_is_a_recorded_refusal_and_notification (__main__.OrchestrationConductorTest.test_request_expiry_is_a_recorded_refusal_and_notification) ... ok
test_request_preview_and_apply_are_exact_across_interop_surfaces (__main__.OrchestrationConductorTest.test_request_preview_and_apply_are_exact_across_interop_surfaces) ... ok
test_run_act_token_binds_action_reason_decision_and_state (__main__.OrchestrationConductorTest.test_run_act_token_binds_action_reason_decision_and_state) ... ok
test_run_interop_compiler_plan_projection_and_preview_are_exact (__main__.OrchestrationConductorTest.test_run_interop_compiler_plan_projection_and_preview_are_exact) ... ok
test_run_stream_is_explicit_bounded_and_injection_safe (__main__.OrchestrationConductorTest.test_run_stream_is_explicit_bounded_and_injection_safe) ... ok
test_run_view_exposes_request_age_schema_and_inspect_only_lineage (__main__.OrchestrationConductorTest.test_run_view_exposes_request_age_schema_and_inspect_only_lineage) ... ok
test_run_view_is_pure_rich_and_excludes_private_semantics (__main__.OrchestrationConductorTest.test_run_view_is_pure_rich_and_excludes_private_semantics) ... ok
test_run_view_static_contract_has_consent_privacy_and_no_poller (__main__.OrchestrationConductorTest.test_run_view_static_contract_has_consent_privacy_and_no_poller) ... ok
test_sse_stream_replays_after_disconnect_and_carries_no_authority (__main__.OrchestrationConductorTest.test_sse_stream_replays_after_disconnect_and_carries_no_authority) ... dw-workbench: 127.0.0.1 "GET /api/runs/run-c3069de933e36ba0697da6c0/events?follow=0 HTTP/1.1" 200 -
dw-workbench: 127.0.0.1 "GET /api/runs/run-c3069de933e36ba0697da6c0/events?follow=0 HTTP/1.1" 200 -
dw-workbench: 127.0.0.1 "POST /api/runs/run-c3069de933e36ba0697da6c0/events HTTP/1.1" 405 -
dw-workbench: 127.0.0.1 "GET /api/signals/events?remote=origin&branch=sse-x&follow=0 HTTP/1.1" 200 -
dw-workbench: 127.0.0.1 "GET /api/runs/run-000000000000000000000000/events?follow=0 HTTP/1.1" 400 -
ok
test_stale_tick_preview_refuses_before_dispatch_or_event (__main__.OrchestrationConductorTest.test_stale_tick_preview_refuses_before_dispatch_or_event) ... ok
test_terminal_request_cleanup_recovers_a_crash_prefix (__main__.OrchestrationConductorTest.test_terminal_request_cleanup_recovers_a_crash_prefix) ... ok
test_tick_result_is_returned_unmodified_by_cli_mcp_and_http (__main__.OrchestrationConductorTest.test_tick_result_is_returned_unmodified_by_cli_mcp_and_http)
Applying adapters wrap the one core document; none reinterprets it. ... ok
test_typed_request_refusals_are_ledgered_and_leave_request_live (__main__.OrchestrationConductorTest.test_typed_request_refusals_are_ledgered_and_leave_request_live) ... ok
test_uncovered_nudge_is_a_typed_request_before_manual_delivery (__main__.OrchestrationConductorTest.test_uncovered_nudge_is_a_typed_request_before_manual_delivery) ... ok
test_unsupported_authority_and_start_budget_stop (__main__.OrchestrationConductorTest.test_unsupported_authority_and_start_budget_stop) ... ok
test_activity_follows_the_scripted_plan_and_terminal_mapping (__main__.OrchestrationDriverTest.test_activity_follows_the_scripted_plan_and_terminal_mapping) ... ok
test_adapter_inventing_activity_states_is_a_conformance_error (__main__.OrchestrationDriverTest.test_adapter_inventing_activity_states_is_a_conformance_error) ... ok
test_claude_adapter_claims_no_rich_activity (__main__.OrchestrationDriverTest.test_claude_adapter_claims_no_rich_activity) ... ok
test_claude_adapter_is_least_privilege_by_construction (__main__.OrchestrationDriverTest.test_claude_adapter_is_least_privilege_by_construction) ... ok
test_claude_adapter_version_pin_refuses_content_free (__main__.OrchestrationDriverTest.test_claude_adapter_version_pin_refuses_content_free) ... ok
test_codex_adapter_claims_no_rich_activity (__main__.OrchestrationDriverTest.test_codex_adapter_claims_no_rich_activity) ... ok
test_config_and_capability_documents_are_closed_and_credential_free (__main__.OrchestrationDriverTest.test_config_and_capability_documents_are_closed_and_credential_free) ... ok
test_lost_maps_to_unknown_and_default_running_activity_is_active (__main__.OrchestrationDriverTest.test_lost_maps_to_unknown_and_default_running_activity_is_active) ... ok
test_malformed_json_and_oversized_artifact_fail_deterministically (__main__.OrchestrationDriverTest.test_malformed_json_and_oversized_artifact_fail_deterministically) ... ok
test_missing_citation_fails_collect_even_after_driver_success (__main__.OrchestrationDriverTest.test_missing_citation_fails_collect_even_after_driver_success) ... ok
test_packet_is_bounded_structured_and_contains_no_provider_command (__main__.OrchestrationDriverTest.test_packet_is_bounded_structured_and_contains_no_provider_command) ... ok
test_parallel_research_validates_before_synthesis_fan_in (__main__.OrchestrationDriverTest.test_parallel_research_validates_before_synthesis_fan_in) ... ok
test_pause_between_packet_and_start_refuses_without_adapter_launch (__main__.OrchestrationDriverTest.test_pause_between_packet_and_start_refuses_without_adapter_launch) ... ok
test_start_poll_interrupt_collect_idempotency_and_recovery_states (__main__.OrchestrationDriverTest.test_start_poll_interrupt_collect_idempotency_and_recovery_states) ... ok
test_timeout_nonzero_lost_stream_and_interrupt_states_are_truthful (__main__.OrchestrationDriverTest.test_timeout_nonzero_lost_stream_and_interrupt_states_are_truthful) ... ok
test_undeclared_diff_path_and_output_are_refused (__main__.OrchestrationDriverTest.test_undeclared_diff_path_and_output_are_refused) ... ok
test_unsupported_profile_request_refuses_before_adapter_start (__main__.OrchestrationDriverTest.test_unsupported_profile_request_refuses_before_adapter_start) ... ok
test_writers_get_distinct_worktrees_diff_scope_and_no_implicit_integration (__main__.OrchestrationDriverTest.test_writers_get_distinct_worktrees_diff_scope_and_no_implicit_integration) ... ok
test_apply_failure_rolls_back_the_original_bytes (__main__.OrchestrationEditorTest.test_apply_failure_rolls_back_the_original_bytes) ... ok
test_delete_is_a_separate_preview_apply_act (__main__.OrchestrationEditorTest.test_delete_is_a_separate_preview_apply_act) ... ok
test_http_inventory_and_document_use_the_shared_compiler_purely (__main__.OrchestrationEditorTest.test_http_inventory_and_document_use_the_shared_compiler_purely) ... ok
test_invalid_unknown_field_blocks_apply_without_silent_drop (__main__.OrchestrationEditorTest.test_invalid_unknown_field_blocks_apply_without_silent_drop) ... ok
test_save_preview_diff_apply_and_reload_are_exact (__main__.OrchestrationEditorTest.test_save_preview_diff_apply_and_reload_are_exact) ... ok
test_score_routes_reject_injection_and_outside_symlink (__main__.OrchestrationEditorTest.test_score_routes_reject_injection_and_outside_symlink) ... ok
test_stale_save_and_delete_previews_refuse (__main__.OrchestrationEditorTest.test_stale_save_and_delete_previews_refuse) ... ok
test_visual_editor_static_contract_names_every_rule_surface (__main__.OrchestrationEditorTest.test_visual_editor_static_contract_names_every_rule_surface) ... ok
test_claim_release_idempotency_and_all_budget_counters (__main__.OrchestrationRunAuthorityTest.test_claim_release_idempotency_and_all_budget_counters) ... ok
test_expiry_and_store_escape_prevent_future_dispatch (__main__.OrchestrationRunAuthorityTest.test_expiry_and_store_escape_prevent_future_dispatch) ... ok
test_installed_cli_plan_start_show_list_pause_resume (__main__.OrchestrationRunAuthorityTest.test_installed_cli_plan_start_show_list_pause_resume) ... ok
test_ledger_detail_is_closed_and_content_safe (__main__.OrchestrationRunAuthorityTest.test_ledger_detail_is_closed_and_content_safe) ... ok
test_pause_resume_revoke_cancel_are_exact_terminal_transitions (__main__.OrchestrationRunAuthorityTest.test_pause_resume_revoke_cancel_are_exact_terminal_transitions) ... ok
test_plan_is_pure_and_binds_score_status_story_authority_and_expiry (__main__.OrchestrationRunAuthorityTest.test_plan_is_pure_and_binds_score_status_story_authority_and_expiry) ... ok
test_projection_ignores_cache_and_corrupt_ledger_fails_closed (__main__.OrchestrationRunAuthorityTest.test_projection_ignores_cache_and_corrupt_ledger_fails_closed) ... ok
test_repository_or_story_drift_stales_dispatch_but_not_audit_replay (__main__.OrchestrationRunAuthorityTest.test_repository_or_story_drift_stales_dispatch_but_not_audit_replay) ... ok
test_start_requires_exact_approval_and_writes_one_atomic_run (__main__.OrchestrationRunAuthorityTest.test_start_requires_exact_approval_and_writes_one_atomic_run) ... ok
test_tampered_or_stale_plan_refuses_without_run_state (__main__.OrchestrationRunAuthorityTest.test_tampered_or_stale_plan_refuses_without_run_state) ... ok
test_two_processes_cannot_claim_the_same_node_attempt (__main__.OrchestrationRunAuthorityTest.test_two_processes_cannot_claim_the_same_node_attempt) ... ok
test_two_processes_cannot_start_the_same_plan (__main__.OrchestrationRunAuthorityTest.test_two_processes_cannot_start_the_same_plan) ... ok
test_agents_md_gets_the_agents_variant (__main__.RiderDocsTest.test_agents_md_gets_the_agents_variant) ... ok
test_agents_transformations_actually_fire (__main__.RiderDocsTest.test_agents_transformations_actually_fire) ... ok
test_codex_and_pi_share_agents_md_without_conflict (__main__.RiderDocsTest.test_codex_and_pi_share_agents_md_without_conflict) ... ok
test_codex_installer_is_idempotent (__main__.RiderDocsTest.test_codex_installer_is_idempotent) ... ok
test_codex_skill_drift_is_a_check_error (__main__.RiderDocsTest.test_codex_skill_drift_is_a_check_error) ... ok
test_codex_skill_renders_frontmatter_and_body (__main__.RiderDocsTest.test_codex_skill_renders_frontmatter_and_body) ... ok
test_doctor_riders_wired_absent_and_broken (__main__.RiderDocsTest.test_doctor_riders_wired_absent_and_broken) ... ok
test_embedded_specs_match_source_canon (__main__.RiderDocsTest.test_embedded_specs_match_source_canon) ... ok
test_every_rider_opens_with_status_then_uses_fresh_step_leases (__main__.RiderDocsTest.test_every_rider_opens_with_status_then_uses_fresh_step_leases) ... ok
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
test_chain_fails_closed_on_corruption_fork_and_truncation (__main__.SignalsTest.test_chain_fails_closed_on_corruption_fork_and_truncation) ... ok
test_changed_facts_append_and_status_rederives (__main__.SignalsTest.test_changed_facts_append_and_status_rederives) ... ok
test_github_remote_parsing_and_provider_refusals (__main__.SignalsTest.test_github_remote_parsing_and_provider_refusals) ... /opt/homebrew/Cellar/python@3.14/3.14.6/Frameworks/Python.framework/Versions/3.14/lib/python3.14/tempfile.py:484: ResourceWarning: Implicitly cleaning up <HTTPError 401: 'refused'>
  _warnings.warn(self.warn_message, ResourceWarning)
/opt/homebrew/Cellar/python@3.14/3.14.6/Frameworks/Python.framework/Versions/3.14/lib/python3.14/tempfile.py:484: ResourceWarning: Implicitly cleaning up <HTTPError 403: 'refused'>
  _warnings.warn(self.warn_message, ResourceWarning)
/opt/homebrew/Cellar/python@3.14/3.14.6/Frameworks/Python.framework/Versions/3.14/lib/python3.14/tempfile.py:484: ResourceWarning: Implicitly cleaning up <HTTPError 429: 'refused'>
  _warnings.warn(self.warn_message, ResourceWarning)
/opt/homebrew/Cellar/python@3.14/3.14.6/Frameworks/Python.framework/Versions/3.14/lib/python3.14/tempfile.py:484: ResourceWarning: Implicitly cleaning up <HTTPError 500: 'refused'>
  _warnings.warn(self.warn_message, ResourceWarning)
/opt/homebrew/Cellar/python@3.14/3.14.6/Frameworks/Python.framework/Versions/3.14/lib/python3.14/tempfile.py:484: ResourceWarning: Implicitly cleaning up <HTTPError 304: 'refused'>
  _warnings.warn(self.warn_message, ResourceWarning)
ok
test_inventory_agrees_across_cli_mcp_and_http (__main__.SignalsTest.test_inventory_agrees_across_cli_mcp_and_http) ... ok
test_observe_is_pure_appends_facts_and_stamps_no_work (__main__.SignalsTest.test_observe_is_pure_appends_facts_and_stamps_no_work) ... ok
test_projection_cache_is_disposable (__main__.SignalsTest.test_projection_cache_is_disposable) ... ok
test_receptivity_table_is_exhaustive_and_refuses_blocked (__main__.SignalsTest.test_receptivity_table_is_exhaustive_and_refuses_blocked) ... ok
test_refusals_are_content_free_recorded_and_deduped (__main__.SignalsTest.test_refusals_are_content_free_recorded_and_deduped) ... ok
test_semantic_dedup_appends_nothing_when_unchanged (__main__.SignalsTest.test_semantic_dedup_appends_nothing_when_unchanged) ... ok
test_status_precedence_matches_the_contract (__main__.SignalsTest.test_status_precedence_matches_the_contract) ... ok
test_third_party_content_never_persists (__main__.SignalsTest.test_third_party_content_never_persists) ... ok
test_feed_reflects_real_state (__main__.StateFeedTest.test_feed_reflects_real_state) ... ok
test_schema_is_pinned (__main__.StateFeedTest.test_schema_is_pinned) ... ok
test_write_emits_the_same_document (__main__.StateFeedTest.test_write_emits_the_same_document) ... ok
test_action_targets_next_story_phase_not_a_closed_pointer (__main__.StatusBriefingTest.test_action_targets_next_story_phase_not_a_closed_pointer) ... ok
test_attention_precedence_for_rails_roadmap_and_rewrite (__main__.StatusBriefingTest.test_attention_precedence_for_rails_roadmap_and_rewrite) ... ok
test_captured_evidence_recommends_the_guarded_done_transition (__main__.StatusBriefingTest.test_captured_evidence_recommends_the_guarded_done_transition) ... ok
test_dirty_active_work_continues_but_unowned_work_is_reviewed (__main__.StatusBriefingTest.test_dirty_active_work_continues_but_unowned_work_is_reviewed) ... ok
test_empty_roadmap_directory_is_attention_not_ready (__main__.StatusBriefingTest.test_empty_roadmap_directory_is_attention_not_ready) ... ok
test_human_render_leads_with_verdict_and_next (__main__.StatusBriefingTest.test_human_render_leads_with_verdict_and_next) ... ok
test_mixed_stage_precedes_contract_and_status_is_pure (__main__.StatusBriefingTest.test_mixed_stage_precedes_contract_and_status_is_pure) ... ok
test_multiple_projects_are_never_guessed (__main__.StatusBriefingTest.test_multiple_projects_are_never_guessed) ... ok
test_path_lists_are_bounded_but_counts_are_complete (__main__.StatusBriefingTest.test_path_lists_are_bounded_but_counts_are_complete) ... ok
test_schema_is_pinned_and_clean_repo_starts_next_story (__main__.StatusBriefingTest.test_schema_is_pinned_and_clean_repo_starts_next_story) ... ok
test_stage_contract_certification_gate_and_staleness_sequence (__main__.StatusBriefingTest.test_stage_contract_certification_gate_and_staleness_sequence) ... ok
test_step_allowlist_positive_and_negative_matrix (__main__.StatusBriefingTest.test_step_allowlist_positive_and_negative_matrix) ... ok
test_step_closes_over_action_id_and_entire_argv_shape (__main__.StatusBriefingTest.test_step_closes_over_action_id_and_entire_argv_shape) ... ok
test_step_interruption_and_start_failure_are_truthful (__main__.StatusBriefingTest.test_step_interruption_and_start_failure_are_truthful) ... ok
test_step_preview_is_schema_pinned_pure_and_state_bound (__main__.StatusBriefingTest.test_step_preview_is_schema_pinned_pure_and_state_bound) ... ok
test_step_runs_exactly_one_allowlisted_child_and_mirrors_exit (__main__.StatusBriefingTest.test_step_runs_exactly_one_allowlisted_child_and_mirrors_exit) ... ok
test_step_stale_token_refuses_before_runner_even_for_same_action (__main__.StatusBriefingTest.test_step_stale_token_refuses_before_runner_even_for_same_action) ... ok
test_step_success_is_bounded_and_old_lease_cannot_replay (__main__.StatusBriefingTest.test_step_success_is_bounded_and_old_lease_cannot_replay) ... ok
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
test_render_grammar (__main__.VerifyTest.test_render_grammar) ... ok
test_smuggled_flip_names_missing_trailer_and_evidence (__main__.VerifyTest.test_smuggled_flip_names_missing_trailer_and_evidence) ... ok

----------------------------------------------------------------------
Ran 338 tests in 188.171s

OK
dw hook: claude — 4 installed, 0 already present in /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.oapd2b04/settings.json
dw hook: claude — 0 installed, 4 already present in /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.oapd2b04/settings.json
dw hook: claude — 4 installed, 0 already present in /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.aapt7e79/settings.json
dw hook: claude — 4 installed, 0 already present in /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.6iam07a3/settings.json
dw hook: claude — 4 removed from /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.6iam07a3/settings.json
test_codex_flag_opt_out_respected (__main__.AgentHooksTest) ... dw hook: codex_hooks is explicitly false in /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.sjlze1m3/config.toml; respecting the opt-out
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
test_workbench_step_front_door_keeps_review_and_act_separate (__main__.DwCoreTest) ... ok
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
test_sse_stream_replays_after_disconnect_and_carries_no_authority (__main__.OrchestrationConductorTest) ... dw-workbench: 127.0.0.1 "GET /api/runs/run-1e6d10b01762161449a04e02/events?follow=0 HTTP/1.1" 200 -
dw-workbench: 127.0.0.1 "GET /api/runs/run-1e6d10b01762161449a04e02/events?follow=0 HTTP/1.1" 200 -
dw-workbench: 127.0.0.1 "POST /api/runs/run-1e6d10b01762161449a04e02/events HTTP/1.1" 405 -
dw-workbench: 127.0.0.1 "GET /api/signals/events?remote=origin&branch=sse-x&follow=0 HTTP/1.1" 200 -
dw-workbench: 127.0.0.1 "GET /api/runs/run-000000000000000000000000/events?follow=0 HTTP/1.1" 400 -
ok
test_stale_tick_preview_refuses_before_dispatch_or_event (__main__.OrchestrationConductorTest) ... ok
test_terminal_request_cleanup_recovers_a_crash_prefix (__main__.OrchestrationConductorTest) ... ok
test_tick_result_is_returned_unmodified_by_cli_mcp_and_http (__main__.OrchestrationConductorTest)
Applying adapters wrap the one core document; none reinterprets it. ... ok
test_typed_request_refusals_are_ledgered_and_leave_request_live (__main__.OrchestrationConductorTest) ... ok
test_uncovered_nudge_is_a_typed_request_before_manual_delivery (__main__.OrchestrationConductorTest) ... ok
test_unsupported_authority_and_start_budget_stop (__main__.OrchestrationConductorTest) ... ok
test_activity_follows_the_scripted_plan_and_terminal_mapping (__main__.OrchestrationDriverTest) ... ok
test_adapter_inventing_activity_states_is_a_conformance_error (__main__.OrchestrationDriverTest) ... ok
test_claude_adapter_claims_no_rich_activity (__main__.OrchestrationDriverTest) ... ok
test_claude_adapter_is_least_privilege_by_construction (__main__.OrchestrationDriverTest) ... ok
test_claude_adapter_version_pin_refuses_content_free (__main__.OrchestrationDriverTest) ... ok
test_codex_adapter_claims_no_rich_activity (__main__.OrchestrationDriverTest) ... ok
test_config_and_capability_documents_are_closed_and_credential_free (__main__.OrchestrationDriverTest) ... ok
test_lost_maps_to_unknown_and_default_running_activity_is_active (__main__.OrchestrationDriverTest) ... ok
test_malformed_json_and_oversized_artifact_fail_deterministically (__main__.OrchestrationDriverTest) ... ok
test_missing_citation_fails_collect_even_after_driver_success (__main__.OrchestrationDriverTest) ... ok
test_packet_is_bounded_structured_and_contains_no_provider_command (__main__.OrchestrationDriverTest) ... ok
test_parallel_research_validates_before_synthesis_fan_in (__main__.OrchestrationDriverTest) ... ok
test_pause_between_packet_and_start_refuses_without_adapter_launch (__main__.OrchestrationDriverTest) ... ok
test_start_poll_interrupt_collect_idempotency_and_recovery_states (__main__.OrchestrationDriverTest) ... ok
test_timeout_nonzero_lost_stream_and_interrupt_states_are_truthful (__main__.OrchestrationDriverTest) ... ok
test_undeclared_diff_path_and_output_are_refused (__main__.OrchestrationDriverTest) ... ok
test_unsupported_profile_request_refuses_before_adapter_start (__main__.OrchestrationDriverTest) ... ok
test_writers_get_distinct_worktrees_diff_scope_and_no_implicit_integration (__main__.OrchestrationDriverTest) ... ok
test_apply_failure_rolls_back_the_original_bytes (__main__.OrchestrationEditorTest) ... ok
test_delete_is_a_separate_preview_apply_act (__main__.OrchestrationEditorTest) ... ok
test_http_inventory_and_document_use_the_shared_compiler_purely (__main__.OrchestrationEditorTest) ... ok
test_invalid_unknown_field_blocks_apply_without_silent_drop (__main__.OrchestrationEditorTest) ... ok
test_save_preview_diff_apply_and_reload_are_exact (__main__.OrchestrationEditorTest) ... ok
test_score_routes_reject_injection_and_outside_symlink (__main__.OrchestrationEditorTest) ... ok
test_stale_save_and_delete_previews_refuse (__main__.OrchestrationEditorTest) ... ok
test_visual_editor_static_contract_names_every_rule_surface (__main__.OrchestrationEditorTest) ... ok
test_claim_release_idempotency_and_all_budget_counters (__main__.OrchestrationRunAuthorityTest) ... ok
test_expiry_and_store_escape_prevent_future_dispatch (__main__.OrchestrationRunAuthorityTest) ... ok
test_installed_cli_plan_start_show_list_pause_resume (__main__.OrchestrationRunAuthorityTest) ... ok
test_ledger_detail_is_closed_and_content_safe (__main__.OrchestrationRunAuthorityTest) ... ok
test_pause_resume_revoke_cancel_are_exact_terminal_transitions (__main__.OrchestrationRunAuthorityTest) ... ok
test_plan_is_pure_and_binds_score_status_story_authority_and_expiry (__main__.OrchestrationRunAuthorityTest) ... ok
test_projection_ignores_cache_and_corrupt_ledger_fails_closed (__main__.OrchestrationRunAuthorityTest) ... ok
test_repository_or_story_drift_stales_dispatch_but_not_audit_replay (__main__.OrchestrationRunAuthorityTest) ... ok
test_start_requires_exact_approval_and_writes_one_atomic_run (__main__.OrchestrationRunAuthorityTest) ... ok
test_tampered_or_stale_plan_refuses_without_run_state (__main__.OrchestrationRunAuthorityTest) ... ok
test_two_processes_cannot_claim_the_same_node_attempt (__main__.OrchestrationRunAuthorityTest) ... ok
test_two_processes_cannot_start_the_same_plan (__main__.OrchestrationRunAuthorityTest) ... ok
test_agents_md_gets_the_agents_variant (__main__.RiderDocsTest) ... ok
test_agents_transformations_actually_fire (__main__.RiderDocsTest) ... ok
test_codex_and_pi_share_agents_md_without_conflict (__main__.RiderDocsTest) ... ok
test_codex_installer_is_idempotent (__main__.RiderDocsTest) ... ok
test_codex_skill_drift_is_a_check_error (__main__.RiderDocsTest) ... ok
test_codex_skill_renders_frontmatter_and_body (__main__.RiderDocsTest) ... ok
test_doctor_riders_wired_absent_and_broken (__main__.RiderDocsTest) ... ok
test_embedded_specs_match_source_canon (__main__.RiderDocsTest) ... ok
test_every_rider_opens_with_status_then_uses_fresh_step_leases (__main__.RiderDocsTest) ... ok
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
test_chain_fails_closed_on_corruption_fork_and_truncation (__main__.SignalsTest) ... ok
test_changed_facts_append_and_status_rederives (__main__.SignalsTest) ... ok
test_github_remote_parsing_and_provider_refusals (__main__.SignalsTest) ... ok
test_inventory_agrees_across_cli_mcp_and_http (__main__.SignalsTest) ... ok
test_observe_is_pure_appends_facts_and_stamps_no_work (__main__.SignalsTest) ... ok
test_projection_cache_is_disposable (__main__.SignalsTest) ... ok
test_receptivity_table_is_exhaustive_and_refuses_blocked (__main__.SignalsTest) ... ok
test_refusals_are_content_free_recorded_and_deduped (__main__.SignalsTest) ... ok
test_semantic_dedup_appends_nothing_when_unchanged (__main__.SignalsTest) ... ok
test_status_precedence_matches_the_contract (__main__.SignalsTest) ... ok
test_third_party_content_never_persists (__main__.SignalsTest) ... ok
test_feed_reflects_real_state (__main__.StateFeedTest) ... ok
test_schema_is_pinned (__main__.StateFeedTest) ... ok
test_write_emits_the_same_document (__main__.StateFeedTest) ... ok
test_action_targets_next_story_phase_not_a_closed_pointer (__main__.StatusBriefingTest) ... ok
test_attention_precedence_for_rails_roadmap_and_rewrite (__main__.StatusBriefingTest) ... ok
test_captured_evidence_recommends_the_guarded_done_transition (__main__.StatusBriefingTest) ... ok
test_dirty_active_work_continues_but_unowned_work_is_reviewed (__main__.StatusBriefingTest) ... ok
test_empty_roadmap_directory_is_attention_not_ready (__main__.StatusBriefingTest) ... ok
test_human_render_leads_with_verdict_and_next (__main__.StatusBriefingTest) ... ok
test_mixed_stage_precedes_contract_and_status_is_pure (__main__.StatusBriefingTest) ... ok
test_multiple_projects_are_never_guessed (__main__.StatusBriefingTest) ... ok
test_path_lists_are_bounded_but_counts_are_complete (__main__.StatusBriefingTest) ... ok
test_schema_is_pinned_and_clean_repo_starts_next_story (__main__.StatusBriefingTest) ... ok
test_stage_contract_certification_gate_and_staleness_sequence (__main__.StatusBriefingTest) ... ok
test_step_allowlist_positive_and_negative_matrix (__main__.StatusBriefingTest) ... ok
test_step_closes_over_action_id_and_entire_argv_shape (__main__.StatusBriefingTest) ... ok
test_step_interruption_and_start_failure_are_truthful (__main__.StatusBriefingTest) ... ok
test_step_preview_is_schema_pinned_pure_and_state_bound (__main__.StatusBriefingTest) ... ok
test_step_runs_exactly_one_allowlisted_child_and_mirrors_exit (__main__.StatusBriefingTest) ... ok
test_step_stale_token_refuses_before_runner_even_for_same_action (__main__.StatusBriefingTest) ... ok
test_step_success_is_bounded_and_old_lease_cannot_replay (__main__.StatusBriefingTest) ... ok
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
Ran 338 tests in 205.411s

OK
dw hook: claude — 4 installed, 0 already present in /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.x6qigba7/settings.json
dw hook: claude — 0 installed, 4 already present in /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.x6qigba7/settings.json
dw hook: claude — 4 installed, 0 already present in /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.02hkhcwb/settings.json
dw hook: claude — 4 installed, 0 already present in /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.jf6sl8w1/settings.json
dw hook: claude — 4 removed from /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.jf6sl8w1/settings.json
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
package-smoke.sh: built delivery_workbench-1.14.0-py3-none-any.whl and delivery_workbench-1.14.0.tar.gz
package-smoke.sh: pipx cannot create environments here; falling back to venv+pip
WARNING: You are using pip version 21.2.4; however, version 26.0.1 is available.
You should consider upgrading via the '/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/pmo-package-smoke.2n6BMv/appenv/bin/python -m pip install --upgrade pip' command.
package-smoke.sh: installed via venv+pip
ready     review-workspace   absent     not-applicable
ready     generate-contract  absent     fail
ready     certify-contract   unchecked  fail
ready     commit             passing    pass
ready     start-story        absent     not-applicable
ready     continue-story     absent     not-applicable
attention repair-roadmap     absent     not-applicable
ready     continue-story     absent     not-applicable
ready     continue-story     absent     not-applicable
attention finish-story       absent     not-applicable
ready     review-workspace   absent     not-applicable
ready     generate-contract  absent     fail
ready     certify-contract   unchecked  fail
ready     generate-contract  stale      fail
ready     certify-contract   unchecked  fail
ready     commit             passing    pass
ready     start-story        absent     not-applicable
commit     3a30b20c0f90         trailers+archive+verify=ok
guided-status-loop.sh: ok (packaged CLI/MCP/HTTP recommendation sequence)
authorize 01 cli  review-workspace   -> review-workspace
authorize 02 mcp  generate-contract  -> certify-contract
refuse   bootstrap certification started=0 step_events=+0
refuse   bootstrap commit       started=0 step_events=+0
authorize 03 http start-story        -> continue-story
refuse   same-id stale token    started=0 step_events=+0
authorize 04 mcp  continue-story     -> continue-story
authorize 05 cli  finish-story       -> review-workspace
authorize 06 http review-workspace   -> review-workspace
authorize 07 cli  generate-contract  -> certify-contract
refuse   story certification    started=0 step_events=+0
refuse   story commit           started=0 step_events=+0
bootstrap  c227e01121c4         certification+commit=manual
commit     0c064a0be58c         trailers+archive+verify=ok
handoff    start-story        authorizations=7
deliberate-step-loop.sh: ok (fresh token per action; no argv reconstruction or consent shortcut)
{"artifact_count": 5, "checks": 2, "compiler_red_cases": 6, "duplicate_restarts": 0, "exam": "packaged multi-agent orchestration", "operator_commit": "12e6c6984a47d7c67d7a164383d043edc3d1cca9", "parallel_research": 2, "repair_visits": 1, "run_id": "run-8c184218231315cba8f3fa12", "runtime_red_cases": 5, "state": "awaiting-certification", "verify_all": "ok"}
{"certification": "operator-only", "duplicate_nudges": 0, "duplicate_starts": 0, "external_rebind": true, "kind": "delivery-workbench-packaged-outward-exam", "nudges": 2, "observer_side_effects": 0, "operator_push": "6e20f6a84ced4b5f25998d6e36985fa95f5f60e8", "refusals": {"blocked-session": "non-receptive", "budget": "nudge-budget-exhausted", "revoked-request": "expired", "stale-correlation": "correlation-mismatch", "unknown-session": "non-receptive", "without-standing-grant": "no-standing-rule"}, "request_republishes": 1, "run_id": "run-4778435e23f757464c2342ae", "schema_version": 1, "state": "awaiting-certification", "stream_matches_ledger": true, "wheel_version": "dw 1.14.0"}
package-smoke.sh: ok
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
test_image_live_expires_and_unlive_stops (__main__.ImageLiveViewTest.test_image_live_expires_and_unlive_stops) ... skipped 'Pillow not installed'
test_image_live_is_read_only (__main__.ImageLiveViewTest.test_image_live_is_read_only) ... skipped 'Pillow not installed'
test_live_posts_a_photo_and_edits_media_on_change_only (__main__.ImageLiveViewTest.test_live_posts_a_photo_and_edits_media_on_change_only) ... skipped 'Pillow not installed'
test_live_text_forces_text_mode_despite_renderer (__main__.ImageLiveViewTest.test_live_text_forces_text_mode_despite_renderer) ... skipped 'Pillow not installed'
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
test_decision_applies_through_the_rails_for_the_owner (__main__.NotificationDecisionTest.test_decision_applies_through_the_rails_for_the_owner) ... ok
test_decision_from_a_stranger_is_refused (__main__.NotificationDecisionTest.test_decision_from_a_stranger_is_refused) ... ok
test_decision_refuses_stale_correlation_and_bad_usage (__main__.NotificationDecisionTest.test_decision_refuses_stale_correlation_and_bad_usage) ... ok
test_push_pass_sends_outbound_and_records_delivery (__main__.NotificationDecisionTest.test_push_pass_sends_outbound_and_records_delivery) ... ok
test_push_pass_without_pairing_sends_nothing (__main__.NotificationDecisionTest.test_push_pass_without_pairing_sends_nothing) ... ok
test_expired_token_refused (__main__.PairingTest.test_expired_token_refused) ... ok
test_no_outstanding_token_refused (__main__.PairingTest.test_no_outstanding_token_refused) ... ok
test_pair_then_reuse_refused (__main__.PairingTest.test_pair_then_reuse_refused) ... ok
test_repair_revokes_previous_binding (__main__.PairingTest.test_repair_revokes_previous_binding) ... ok
test_state_file_is_owner_only (__main__.PairingTest.test_state_file_is_owner_only) ... ok
test_token_from_separate_pair_process_is_honored (__main__.PairingTest.test_token_from_separate_pair_process_is_honored) ... ok
test_token_stored_hashed_not_cleartext (__main__.PairingTest.test_token_stored_hashed_not_cleartext) ... ok
test_unpaired_chat_gets_prompt_then_silence (__main__.PairingTest.test_unpaired_chat_gets_prompt_then_silence) ... ok
test_wrong_token_refused (__main__.PairingTest.test_wrong_token_refused) ... ok
test_consent_command_refused_for_stranger_owner_fine (__main__.PerPersonConsentTest.test_consent_command_refused_for_stranger_owner_fine) ... ok
test_every_tap_refused_for_stranger (__main__.PerPersonConsentTest.test_every_tap_refused_for_stranger) ... ok
test_owner_recorded_status_says_so (__main__.PerPersonConsentTest.test_owner_recorded_status_says_so) ... ok
test_pair_records_owner_and_it_round_trips (__main__.PerPersonConsentTest.test_pair_records_owner_and_it_round_trips) ... ok
test_reads_stay_chat_scoped (__main__.PerPersonConsentTest.test_reads_stay_chat_scoped) ... ok
test_relay_refused_for_stranger_flows_for_owner (__main__.PerPersonConsentTest.test_relay_refused_for_stranger_flows_for_owner) ... ok
test_status_warns_on_legacy_pairing (__main__.PerPersonConsentTest.test_status_warns_on_legacy_pairing) ... ok
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
test_bound_and_armed_question_carries_the_keyboard (__main__.QuestionNavTest.test_bound_and_armed_question_carries_the_keyboard) ... ok
test_forged_tap_without_binding_refuses_and_never_arms (__main__.QuestionNavTest.test_forged_tap_without_binding_refuses_and_never_arms) ... ok
test_nav_taps_drive_the_prompt_and_enter_notes_it (__main__.QuestionNavTest.test_nav_taps_drive_the_prompt_and_enter_notes_it) ... ok
test_peek_delivers_the_screen_flow (__main__.QuestionNavTest.test_peek_delivers_the_screen_flow) ... ok
test_tap_on_unarmed_binding_refuses_and_never_arms (__main__.QuestionNavTest.test_tap_on_unarmed_binding_refuses_and_never_arms) ... ok
test_unarmed_question_keeps_todays_card (__main__.QuestionNavTest.test_unarmed_question_keeps_todays_card) ... ok
test_unbound_question_keeps_todays_card (__main__.QuestionNavTest.test_unbound_question_keeps_todays_card) ... ok
test_events_render_real_log (__main__.ReadSurfaceTest.test_events_render_real_log) ... ok
test_peek_is_read_only_capture (__main__.ReadSurfaceTest.test_peek_is_read_only_capture) ... ok
test_sessions_render_correlation (__main__.ReadSurfaceTest.test_sessions_render_correlation) ... ok
test_state_renders_real_feed (__main__.ReadSurfaceTest.test_state_renders_real_feed) ... ok
test_steer_a_dead_session_offers_capability_recovery (__main__.RecoveryTest.test_steer_a_dead_session_offers_capability_recovery) ... ok
test_story_argv_allow_list_is_two_verbs (__main__.SchemaComplianceTest.test_story_argv_allow_list_is_two_verbs) ... ok
test_unproven_feed_schema_refused_politely (__main__.SchemaComplianceTest.test_unproven_feed_schema_refused_politely) ... ok
test_unproven_sessions_schema_refused_politely (__main__.SchemaComplianceTest.test_unproven_sessions_schema_refused_politely) ... ok
test_fallback_without_renderer_states_reason (__main__.ScreenCommandTest.test_fallback_without_renderer_states_reason) ... ok
test_refresh_edits_the_same_photo_message (__main__.ScreenCommandTest.test_refresh_edits_the_same_photo_message) ... skipped 'Pillow not installed'
test_screen_is_read_only (__main__.ScreenCommandTest.test_screen_is_read_only) ... ok
test_screen_sends_photo_with_refresh_button (__main__.ScreenCommandTest.test_screen_sends_photo_with_refresh_button) ... skipped 'Pillow not installed'
test_screen_unbound_and_argless_states_usage (__main__.ScreenCommandTest.test_screen_unbound_and_argless_states_usage) ... ok
test_ansi_matrix_renders_to_png (__main__.ScreenshotRendererTest.test_ansi_matrix_renders_to_png) ... skipped 'Pillow not installed'
test_forced_unavailable_returns_none_with_reason (__main__.ScreenshotRendererTest.test_forced_unavailable_returns_none_with_reason) ... ok
test_garbage_sgr_never_raises (__main__.ScreenshotRendererTest.test_garbage_sgr_never_raises) ... skipped 'Pillow not installed'
test_live_mode_is_lighter_than_full (__main__.ScreenshotRendererTest.test_live_mode_is_lighter_than_full) ... skipped 'Pillow not installed'
test_strip_non_sgr_keeps_colors (__main__.ScreenshotRendererTest.test_strip_non_sgr_keeps_colors) ... ok
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
test_builtin_table_is_closed (__main__.ToolbarConfigTest.test_builtin_table_is_closed) ... ok
test_buttons_route_keys_to_kb_and_the_rest_to_tb (__main__.ToolbarConfigTest.test_buttons_route_keys_to_kb_and_the_rest_to_tb) ... ok
test_config_reshapes_grid_and_adds_text_action (__main__.ToolbarConfigTest.test_config_reshapes_grid_and_adds_text_action) ... ok
test_default_grids_per_harness_and_fallback (__main__.ToolbarConfigTest.test_default_grids_per_harness_and_fallback) ... ok
test_loader_never_raises_on_garbage (__main__.ToolbarConfigTest.test_loader_never_raises_on_garbage) ... ok
test_toolbar_only_offered_when_bound (__main__.ToolbarTest.test_toolbar_only_offered_when_bound) ... ok
test_toolbar_press_fires_a_key_no_extra_tap (__main__.ToolbarTest.test_toolbar_press_fires_a_key_no_extra_tap) ... ok
test_toolbar_press_without_binding_refused (__main__.ToolbarTest.test_toolbar_press_without_binding_refused) ... ok
test_builtin_screen_tap_produces_the_screen_flow (__main__.ToolbarUpgradeTest.test_builtin_screen_tap_produces_the_screen_flow) ... ok
test_command_menu_registers_and_opts_out (__main__.ToolbarUpgradeTest.test_command_menu_registers_and_opts_out) ... ok
test_dismiss_edits_the_card_and_unknown_action_refused (__main__.ToolbarUpgradeTest.test_dismiss_edits_the_card_and_unknown_action_refused) ... ok
test_tap_without_binding_refused (__main__.ToolbarUpgradeTest.test_tap_without_binding_refused) ... ok
test_text_action_types_through_the_driver (__main__.ToolbarUpgradeTest.test_text_action_types_through_the_driver) ... ok
test_toolbar_renders_the_harness_grid (__main__.ToolbarUpgradeTest.test_toolbar_renders_the_harness_grid) ... ok
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
Ran 152 tests in 11.883s

OK (skipped=9)
test_bot_api_strings_live_only_in_the_transport (__main__.ConsentFloorTest.test_bot_api_strings_live_only_in_the_transport) ... ok
test_keystroke_methods_are_defined_only_in_the_driver (__main__.ConsentFloorTest.test_keystroke_methods_are_defined_only_in_the_driver) ... ok
test_send_keys_lives_only_in_the_driver (__main__.ConsentFloorTest.test_send_keys_lives_only_in_the_driver) ... ok
test_consent_floor_catches_planted_send_keys (__main__.FitnessSelfTest.test_consent_floor_catches_planted_send_keys) ... ok
test_layering_catches_a_planted_transport_import (__main__.FitnessSelfTest.test_layering_catches_a_planted_transport_import) ... ok
test_layering_catches_a_planted_violation_in_a_new_leaf (__main__.FitnessSelfTest.test_layering_catches_a_planted_violation_in_a_new_leaf) ... ok
test_leaves_stay_leaves (__main__.ImportLayeringTest.test_leaves_stay_leaves) ... ok
test_no_import_cycles (__main__.ImportLayeringTest.test_no_import_cycles) ... ok
test_rails_seam_is_reached_only_through_the_interface (__main__.ImportLayeringTest.test_rails_seam_is_reached_only_through_the_interface) ... ok
test_transport_is_a_pure_leaf (__main__.ImportLayeringTest.test_transport_is_a_pure_leaf) ... ok

----------------------------------------------------------------------
Ran 10 tests in 0.126s

OK
docs-lint: ok (432 markdown files)
docs-lint.sh: ok (0s)
ok: CONTRIBUTING.md snippet 'contributor-setup' ran as printed
ok: CONTRIBUTING.md snippet 'contributor-gated-commit' ran as printed
ok: pmo-roadmap/README.md snippet 'install' ran as printed
ok: pmo-roadmap/README.md snippet 'update' ran as printed
ok: pmo-roadmap/README.md snippet 'new-project' ran as printed
ok: pmo-roadmap/README.md snippet 'adopt-three-step' ran as printed
ok: pmo-roadmap/README.md snippet 'intake-no-prompt' ran as printed
ok: pmo-roadmap/README.md snippet 'adopt-close-loop' ran as printed
docs-lint snippets: ok
docs-snippet-smoke.sh: ok
canon-lint.sh: ok
orchestration interop: exact CLI/MCP/HTTP lifecycle reached awaiting-certification
orchestration-interop.sh: ok
dw-workbench: shutting down
dw-workbench: serving /private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-orchestration-interop.h7d7cu/repo
dw-workbench: http://127.0.0.1:24391/ (localhost or your own .ts.net tailnet; Ctrl-C to stop)
dw-workbench: writes require /api/mutations preview→apply or an exact /api/step/apply token; never stages, certifies, or commits
preview parity: CLI = MCP = HTTP
result parity:  CLI = MCP = HTTP
replay/injection: refused without another child
certification/commit: previewable, never applicable
step-interop.sh: ok
protocol exchange: ok (9 replies)
no-rails refusal: ok
mutation walk: ok (done-without-evidence refused; contract stamped, certification manual)
gate still blocks uncertified commits: ok
MCP/CLI byte-parity (timestamps normalized): ok
mcp-server.sh: ok
dw-workbench: serving /private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/pmo-workbench-test.ubqGhl/repo
dw-workbench: http://127.0.0.1:18348/ (localhost or your own .ts.net tailnet; Ctrl-C to stop)
dw-workbench: writes require /api/mutations preview→apply or an exact /api/step/apply token; never stages, certifies, or commits
dw-workbench: shutting down
dw-workbench: serving /private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/pmo-workbench-test.ubqGhl/installed
dw-workbench: http://127.0.0.1:18349/ (localhost or your own .ts.net tailnet; Ctrl-C to stop)
dw-workbench: writes require /api/mutations preview→apply or an exact /api/step/apply token; never stages, certifies, or commits
workbench-explorer.sh: ok
dw-workbench: shutting down
dw-workbench: serving /private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/pmo-workbench-test.ubqGhl/repo
dw-workbench: http://127.0.0.1:18348/ (localhost or your own .ts.net tailnet; Ctrl-C to stop)
dw-workbench: writes require /api/mutations preview→apply or an exact /api/step/apply token; never stages, certifies, or commits
workbench-ui-smoke.sh: ok (32 viewport renders: 14 views + attention + ambiguity, desktop+mobile)
dw-workbench: shutting down
dw-workbench: serving /private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/pmo-ui-smoke.9FBAYo/repo
dw-workbench: http://127.0.0.1:22294/ (localhost or your own .ts.net tailnet; Ctrl-C to stop)
dw-workbench: writes require /api/mutations preview→apply or an exact /api/step/apply token; never stages, certifies, or commits
agent-surface.sh: ok
plugin manifests: ok (version 1.14.0, 4 commands, 1 skill)
claude plugin validate: ok
plugin-validate.sh: ok
update.sh: up to date (vendored rails match source v1.14.0)
dw check: ok
```

### Captured run — 2026-07-22T15:10:10Z

- **Command:** `./.githooks/dw verify --all`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** aa2d974fc009a1d7faea1b204386043ea9ccbef1

```text
dw verify: ok (146 commits verified, 17 pre-epoch skipped)
```
