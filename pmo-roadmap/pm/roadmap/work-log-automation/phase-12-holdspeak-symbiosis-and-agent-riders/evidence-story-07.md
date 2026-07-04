# Evidence - WLA-12-07

- **Story:** WLA-12-07 - Desk presence, doctor awareness, and release
- **Status:** done
- **Date:** 2026-07-03

## Proof

Three captured runs plus screenshots under `assets/`:

1. **A failed Desk capture (05:13:14Z), kept in:** Firefox headless
   on macOS silently ignores relative `--screenshot` paths; the API
   and `.hs/` halves of that run were already correct. Absolute
   paths fixed it.
2. **Desk presence + doctor (05:16:11Z):** the real HoldSpeak web
   runtime (started headless for the proof, left running for the
   owner), the `delivery-workbench` project created and patched
   through the documented projects API with the rails one-liner —
   asserted to carry "Phase 12" and the next story — the
   `.hs/context.md` block live-rendered from the roadmap, and
   `dw doctor` reporting all five `rider:` lines on this repo
   (claude wired, codex/pi honestly "not installed", holdspeak
   packs installed and current, `.hs` block current).
   `assets/desk-canvas.png` shows the actual Desk (including
   HoldSpeak's own "1 blocked" agent badge);
   `assets/desk-projects-presence.png` shows the archive view with
   the Projects tab. That tab is client-side state a headless
   screenshot cannot click — the API JSON in this capture is the
   exact data it renders; recorded plainly, not papered over.
3. **Suite (05:16:19Z):** 144 core tests including the doctor
   rider states (wired / absent / broken-flips-to-finding) and the
   `.hs` block lifecycle (operator content preserved, refresh
   idempotent, deliberately outside the byte-drift rule) — the
   authoritative tests-ran capture. `mcp-server.sh` and
   `agent-surface.sh` green on the touched surfaces.

Enacted this story: the pre-decided split — release and phase
close move to WLA-12-09 (the story file carries the amendment;
this evidence is the record). README now cross-links
`docs/riders.md` and the journal; `docs/riders.md` gained the
presence/doctor how-to.

### Captured run — 2026-07-04T05:13:14Z

- **Command:** `bash -c 
set -e
BASE=http://127.0.0.1:56178
echo "== the Desk project record, live from the projects API =="
curl -s "$BASE/api/projects" | python3 -m json.tool | grep -E "\"name\"|\"description\"|\"id\"" | head -4
echo
echo "== .hs/context.md (HoldSpeak project-context seam) =="
sed -n "3,12p" .hs/context.md
echo
echo "== screenshot of the real Desk =="
profile=$(mktemp -d)
"/Applications/Firefox.app/Contents/MacOS/firefox" --headless --no-remote --profile "$profile" --screenshot "pmo-roadmap/pm/roadmap/work-log-automation/phase-12-holdspeak-symbiosis-and-agent-riders/assets/desk-project-presence.png" --window-size=1400,900 "$BASE/" >/dev/null 2>&1 &
ffpid=$!
waited=0
while [ ! -s "pmo-roadmap/pm/roadmap/work-log-automation/phase-12-holdspeak-symbiosis-and-agent-riders/assets/desk-project-presence.png" ] && [ "$waited" -lt 30 ]; do sleep 1; waited=$((waited+1)); done
sleep 1; kill "$ffpid" 2>/dev/null || true; wait "$ffpid" 2>/dev/null || true; rm -rf "$profile"
SIZE=$(wc -c < "pmo-roadmap/pm/roadmap/work-log-automation/phase-12-holdspeak-symbiosis-and-agent-riders/assets/desk-project-presence.png" | tr -d " ")
echo "desk screenshot: assets/desk-project-presence.png ($SIZE bytes)"
[ "$SIZE" -gt 20000 ] || { echo "screenshot too small — unrendered"; exit 1; }
`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** eb53c7e17f6656a9775fbdc69a35ff4a84851b89

```text
== the Desk project record, live from the projects API ==
            "id": "proj-ad4bf4f2b078",
            "name": "delivery-workbench",
            "description": "Rails: Phase 12 \u2014 HoldSpeak symbiosis (7/8 done) \u00b7 next: WLA-12-07\tin-progress\tphase-12-holdspeak-symbiosis-and-agent-riders\tDesk presence, doctor awareness, and release \u00b7 .hs/context.md wired",

== .hs/context.md (HoldSpeak project-context seam) ==
## Delivery Workbench roadmap state

This block is rendered from the rails by `dw rider docs`; edit outside the markers only.

### work-log-automation

- Current phase: 12 (phase-12-holdspeak-symbiosis-and-agent-riders)
- Next story: WLA-12-07 — Desk presence, doctor awareness, and release [in-progress]
- Open roadmap warnings: 2


== screenshot of the real Desk ==
bash: line 16: pmo-roadmap/pm/roadmap/work-log-automation/phase-12-holdspeak-symbiosis-and-agent-riders/assets/desk-project-presence.png: No such file or directory
desk screenshot: assets/desk-project-presence.png ( bytes)
bash: line 18: [: : integer expression expected
screenshot too small — unrendered
```

### Captured run — 2026-07-04T05:16:11Z

- **Command:** `bash -c 
set -e
BASE=http://127.0.0.1:56178
echo "== Desk presence: the project record, live from the projects API =="
/usr/bin/curl -s "$BASE/api/projects" | python3 -c "
import json, sys
p = json.load(sys.stdin)[\"projects\"][0]
print(\"name:\", p[\"name\"])
print(\"description:\", p[\"description\"][:160])
assert \"Phase 12\" in p[\"description\"] and \"WLA-12-07\" in p[\"description\"]
print(\"PASS: rails state on the Desk project record\")"
echo
echo "== .hs/context.md — the seam HoldSpeak reads for dictation/detection =="
sed -n "5,12p" .hs/context.md
echo
echo "== screenshots (assets/) =="
ls -la pmo-roadmap/pm/roadmap/work-log-automation/phase-12-holdspeak-symbiosis-and-agent-riders/assets/
echo "(the Projects tab is client-side state a headless screenshot cannot click;"
echo " the API JSON above is the data that tab renders — routes/projects.py)"
echo
echo "== dw doctor: rider awareness on this repo =="
.githooks/dw doctor | grep "rider:"
`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** eb53c7e17f6656a9775fbdc69a35ff4a84851b89

```text
== Desk presence: the project record, live from the projects API ==
name: delivery-workbench
description: Rails: Phase 12 — HoldSpeak symbiosis (7/8 done) · next: WLA-12-07	in-progress	phase-12-holdspeak-symbiosis-and-agent-riders	Desk presence, doctor awareness, an
PASS: rails state on the Desk project record

== .hs/context.md — the seam HoldSpeak reads for dictation/detection ==
This block is rendered from the rails by `dw rider docs`; edit outside the markers only.

### work-log-automation

- Current phase: 12 (phase-12-holdspeak-symbiosis-and-agent-riders)
- Next story: WLA-12-07 — Desk presence, doctor awareness, and release [in-progress]
- Open roadmap warnings: 2


== screenshots (assets/) ==
total 600
drwxr-xr-x   4 karol  staff     128 Jul  3 23:16 .
drwxr-xr-x  21 karol  staff     672 Jul  3 23:13 ..
-rw-r--r--@  1 karol  staff  157781 Jul  3 23:16 desk-canvas.png
-rw-r--r--@  1 karol  staff  143832 Jul  3 23:15 desk-projects-presence.png
(the Projects tab is client-side state a headless screenshot cannot click;
 the API JSON above is the data that tab renders — routes/projects.py)

== dw doctor: rider awareness on this repo ==
ok   rider:claude: wired, matches canon
ok   rider:codex: not installed (optional)
ok   rider:pi: not installed (optional)
ok   rider:holdspeak: packs installed and current: delivery_workbench_actuator_pack.py, delivery_workbench_pack.py
ok   rider:hs-context: .hs/context.md roadmap block current
```

### Captured run — 2026-07-04T05:16:19Z

- **Command:** `python3 pmo-roadmap/tests/dw-core-tests.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** eb53c7e17f6656a9775fbdc69a35ff4a84851b89

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
Ran 144 tests in 11.321s

OK
```
