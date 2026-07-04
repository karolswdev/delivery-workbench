# Evidence - WLA-13-02

- **Story:** WLA-13-02 - Ship the roadmap state feed
- **Status:** done
- **Date:** 2026-07-03

## Proof

Three captured runs:

1. **The feed live (05:55:02Z):** bare `dw state` prints the
   one-line pulse; `--json` emits feed_schema 1 with the full
   belt data (14 phases, 80 stories on this repo); `--write`
   drops the identical document to a file.
2. **The real consumers (05:55:24Z):** both HoldSpeak packs
   converted from `dw context --compact` scraping to the feed —
   they now check `feed_schema` before trusting a byte and fail
   politely on a version they weren't proven against — bumped to
   0.1.1, re-installed, discovered on the desk, and the full
   23-test pack suite green after conversion.
3. **Suite (05:55:34Z):** 147 core tests including the three
   schema-pinning tests whose frozen key sets ARE the stability
   promise — the authoritative tests-ran capture.

Amendment recorded in docs/mission-control.md §1 in this commit,
per the contract's own rule: the per-project `phases` array
(number, title, status, stories_done, stories_total) joined the
schema before freezing — the conveyor renders phases as the belt
and the actuator validates against story-less phases; neither
works from `current_phase` alone.

### Captured run — 2026-07-04T05:55:02Z

- **Command:** `bash -c 
set -e
echo "== the feed, live from this repo =="
.githooks/dw state
echo
.githooks/dw state --json | python3 -c "
import json, sys
d = json.load(sys.stdin)
p = d[\"projects\"][0]
cp = p[\"current_phase\"]
print(\"feed_schema:\", d[\"feed_schema\"])
print(\"current phase:\", cp[\"number\"], cp[\"status\"], f\"{cp[\"stories_done\"]}/{cp[\"stories_total\"]}\")
print(\"phases on the belt:\", len(p[\"phases\"]), \"| stories:\", len(p[\"stories\"]))"
echo
echo "== --write drops the same document =="
.githooks/dw state --write /tmp/dw-state-proof.json
python3 -c "import json; d=json.load(open(\"/tmp/dw-state-proof.json\")); print(\"written document schema:\", d[\"feed_schema\"])"
rm /tmp/dw-state-proof.json
`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 859696466bf5859bf0db14c659808472f276fb4b

```text
== the feed, live from this repo ==
work-log-automation	phase 13 [open] 1/6	next WLA-13-02 [in-progress]	warnings:1

feed_schema: 1
current phase: 13 open 1/6
phases on the belt: 14 | stories: 80

== --write drops the same document ==
/tmp/dw-state-proof.json
written document schema: 1
```

### Captured run — 2026-07-04T05:55:24Z

- **Command:** `bash -c 
echo "== packs 0.1.1 (feed consumers) re-installed and discovered on the desk =="
/Users/karol/dev/tools/HoldSpeak/.venv/bin/python -c "
from holdspeak.plugin_pack_loader import DEFAULT_USER_PACK_DIR, discover_user_packs
packs, errors = discover_user_packs(DEFAULT_USER_PACK_DIR)
found = sorted((p.manifest.id, p.manifest.version) for p in packs)
print(found, \"errors:\", list(errors))
assert found == [(\"delivery_workbench\", \"0.1.1\"), (\"delivery_workbench_actuator\", \"0.1.1\")] and not errors
print(\"PASS: both feed-consuming packs live on the desk\")"
echo
echo "== pack suite (both packs now consume dw state --json) =="
/Users/karol/dev/tools/HoldSpeak/.venv/bin/python pmo-roadmap/tests/holdspeak-pack-tests.py 2>&1 | tail -2
`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 859696466bf5859bf0db14c659808472f276fb4b

```text
== packs 0.1.1 (feed consumers) re-installed and discovered on the desk ==
[('delivery_workbench', '0.1.1'), ('delivery_workbench_actuator', '0.1.1')] errors: []
PASS: both feed-consuming packs live on the desk

== pack suite (both packs now consume dw state --json) ==

OK
```

### Captured run — 2026-07-04T05:55:34Z

- **Command:** `python3 pmo-roadmap/tests/dw-core-tests.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 859696466bf5859bf0db14c659808472f276fb4b

```text
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
test_render_grammar (__main__.VerifyTest.test_render_grammar) ... ok
test_smuggled_flip_names_missing_trailer_and_evidence (__main__.VerifyTest.test_smuggled_flip_names_missing_trailer_and_evidence) ... ok

----------------------------------------------------------------------
Ran 147 tests in 10.833s

OK
```
