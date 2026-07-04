# Evidence - WLA-12-06

- **Story:** WLA-12-06 - Prove the pi rider end-to-end
- **Status:** done
- **Date:** 2026-07-03

## Proof

Four captured runs:

1. **A failed install (04:59:45Z), kept in:** the fixture's
   vendored `dw` predated the pi verb — the consumer-upgrade path
   announcing itself. Synced the fixture the way `update.sh` would;
   the failure is the reminder that consumers get new verbs via
   update, not osmosis.
2. **Installer (05:00:05Z):** `dw rider install pi` wires the
   shared AGENTS.md (agents variant) and the four commands as
   `.pi/prompts/*.md` project prompt templates — rendered verbatim
   from canon, because pi's template format is byte-identical to
   the command-spec format. Second run: all `unchanged`. The purity
   check is mechanical in two places: `grep -rniE 'mcp|claude'`
   over `.pi/prompts/` in this capture, and the
   `pi_purity_violations` guard inside the installer itself, which
   refuses to render a spec that ever grows a forbidden fragment.
3. **The loop (05:00:18Z):** the full story loop under real pi
   (`--provider openrouter --model gpt-5.2 -p`, key sourced from
   the operator's shell, never printed) — next → in-progress →
   work → evidence capture → done → contract certified by the
   agent working the story → gated commit. Trailers stamped,
   gate banner in the transcript, `dw verify` re-derives the
   commit from history alone. No MCP, no slash commands, no
   sandbox negotiations: a context file and a shell were enough,
   which was the entire claim under test.
4. **Suite (05:04:06Z):** 142 core tests including the pi
   renderer/installer/purity/drift cases and the shared-AGENTS.md
   coexistence case — the authoritative tests-ran capture.

The shared-file answer, recorded per the story's open question:
one AGENTS.md serves every AGENTS.md-reading harness (there is
only one filename — per-harness forks are impossible by
construction). The agents variant is therefore CLI-first with MCP
as one clearly-optional aside, and the pi-native surfaces carry no
MCP references at all. Installing the codex rider then the pi
rider leaves AGENTS.md `unchanged` on the second install,
test-proven.

### Captured run — 2026-07-04T04:59:45Z

- **Command:** `bash -c 
set -e
cd '/private/tmp/claude-501/-Users-karol-dev-code-delivery-workbench/fdc6877b-9071-406e-94f9-c2020d111439/scratchpad/codex-rider-fixture'
echo '== dw rider install pi (first run) =='
.githooks/dw rider install pi
echo
echo '== second run must change nothing =='
.githooks/dw rider install pi
echo
echo '== mechanical purity check over every pi-native rendered file =='
if grep -rniE 'mcp|claude' .pi/prompts/; then echo 'PURITY VIOLATION'; exit 1; else echo 'clean: no MCP or Claude references in .pi/prompts/'; fi
echo
echo '== AGENTS.md head (shared agents variant) =='
sed -n '1,4p' AGENTS.md
`
- **Cwd:** .
- **Exit code:** 2
- **Index-tree:** 15c0d82d2d2106034d711c6c7adeb034dcb658a0

```text
== dw rider install pi (first run) ==
usage: dw rider install [-h] {codex}
dw rider install: error: argument surface: invalid choice: 'pi' (choose from 'codex')
```

### Captured run — 2026-07-04T05:00:05Z

- **Command:** `bash -c 
set -e
cd '/private/tmp/claude-501/-Users-karol-dev-code-delivery-workbench/fdc6877b-9071-406e-94f9-c2020d111439/scratchpad/codex-rider-fixture'
echo '== dw rider install pi (first run) =='
.githooks/dw rider install pi
echo
echo '== second run must change nothing =='
.githooks/dw rider install pi
echo
echo '== mechanical purity check over every pi-native rendered file =='
if grep -rniE 'mcp|claude' .pi/prompts/; then echo 'PURITY VIOLATION'; exit 1; else echo 'clean: no MCP or Claude references in .pi/prompts/'; fi
echo
echo '== AGENTS.md head (shared agents variant) =='
sed -n '1,4p' AGENTS.md
`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 15c0d82d2d2106034d711c6c7adeb034dcb658a0

```text
== dw rider install pi (first run) ==
AGENTS.md	created
.pi/prompts/dw-adopt.md	created
.pi/prompts/dw-contract.md	created
.pi/prompts/dw-next.md	created
.pi/prompts/dw-story-done.md	created

== second run must change nothing ==
AGENTS.md	unchanged
.pi/prompts/dw-adopt.md	unchanged
.pi/prompts/dw-contract.md	unchanged
.pi/prompts/dw-next.md	unchanged
.pi/prompts/dw-story-done.md	unchanged

== mechanical purity check over every pi-native rendered file ==
clean: no MCP or Claude references in .pi/prompts/

== AGENTS.md head (shared agents variant) ==
<!-- BEGIN DELIVERY WORKBENCH (managed by pmo-roadmap install.sh/update.sh — edits inside are overwritten) -->

## Delivery Workbench (PMO rails)
```

### Captured run — 2026-07-04T05:00:18Z

- **Command:** `zsh -c 
source ~/.zshrc >/dev/null 2>&1
cd '/private/tmp/claude-501/-Users-karol-dev-code-delivery-workbench/fdc6877b-9071-406e-94f9-c2020d111439/scratchpad/codex-rider-fixture'
pi --provider openrouter --model gpt-5.2 -p --no-session 'You are working a Delivery Workbench story on the rails in this repository (the brief is in AGENTS.md — read it first). Execute exactly these steps in order, printing every command output verbatim as you go:
1. .githooks/dw next webshop --json
2. .githooks/dw story status webshop 1 WSH-1-01 in-progress
3. Create cart_api.md containing a "# Cart API" heading and two sentences sketching the endpoints.
4. .githooks/dw evidence capture webshop 1 WSH-1-01 -- test -f cart_api.md
5. .githooks/dw story status webshop 1 WSH-1-01 done
6. git add -A
7. .githooks/dw contract new --story WSH-1-01
8. Read .tmp/CONTRACT.md and honestly verify each rule against what you actually did in steps 1-7, then flip every "- [ ]" to "- [x]" by editing the file.
9. git commit -m "Complete WSH-1-01: cart API sketched"
10. Print the commit output verbatim, then run: git log --oneline -1'
`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 15c0d82d2d2106034d711c6c7adeb034dcb658a0

```text
```bash
.githooks/dw next webshop --json
```

```json
{"phase": 1, "phase_path": "phase-1-checkout-flow", "status": "backlog", "story_id": "WSH-1-01", "story_path": "pm/roadmap/webshop/phase-1-checkout-flow/story-01-build-the-cart-api.md", "title": "Build the cart API"}
```

```bash
.githooks/dw story status webshop 1 WSH-1-01 in-progress
```

```
WSH-1-01	in-progress	pm/roadmap/webshop/phase-1-checkout-flow/story-01-build-the-cart-api.md
```

Created `cart_api.md` with the requested heading and endpoint sketch.

```bash
.githooks/dw evidence capture webshop 1 WSH-1-01 -- test -f cart_api.md
```

```
pm/roadmap/webshop/phase-1-checkout-flow/evidence-story-01.md	0	2026-07-04T05:01:26Z
```

```bash
.githooks/dw story status webshop 1 WSH-1-01 done
```

```
WSH-1-01	done	pm/roadmap/webshop/phase-1-checkout-flow/story-01-build-the-cart-api.md
```

```bash
git add -A
```

```
(no output)
```

```bash
.githooks/dw contract new --story WSH-1-01
```

```
dw contract new: facts stamped. Verify each rule, flip every '- [ ]' to '- [x]', then commit. Restaging invalidates the contract (re-run with --force).
.tmp/CONTRACT.md	e20b52dd2dc3d588afe6c146caa5c8742adcda42	WSH-1-01
```

Read `.tmp/CONTRACT.md`, verified against steps 1–7, and flipped all checkboxes to `- [x]`.

```bash
git commit -m "Complete WSH-1-01: cart API sketched"
```

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✓ The system accepted your understanding of the project management framework.
  Contract acknowledged (7/7 checkboxes).
  Stories shipped this commit: 1 (evidence verified by dw gate).
  Commit proceeding.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
pmo-roadmap post-commit: contract archived to .git/pmo-contract-archive/7ecfe1dda626d24eed4119b9de6dc7faba838e54
[main 7ecfe1d] Complete WSH-1-01: cart API sketched
 29 files changed, 264 insertions(+), 9 deletions(-)
 create mode 100644 .githooks/dw_pmo/__pycache__/riderdocs.cpython-314.pyc
 create mode 100644 .pi/prompts/dw-adopt.md
 create mode 100644 .pi/prompts/dw-contract.md
 create mode 100644 .pi/prompts/dw-next.md
 create mode 100644 .pi/prompts/dw-story-done.md
 create mode 100644 AGENTS.md
 create mode 100644 cart_api.md
 create mode 100644 pm/roadmap/webshop/phase-1-checkout-flow/evidence-story-01.md
```

```bash
git log --oneline -1
```

```
7ecfe1d Complete WSH-1-01: cart API sketched
```
```

### Captured run — 2026-07-04T05:04:06Z

- **Command:** `python3 pmo-roadmap/tests/dw-core-tests.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 15c0d82d2d2106034d711c6c7adeb034dcb658a0

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
test_embedded_specs_match_source_canon (__main__.RiderDocsTest.test_embedded_specs_match_source_canon) ... ok
test_hand_edited_copy_is_a_check_error (__main__.RiderDocsTest.test_hand_edited_copy_is_a_check_error) ... ok
test_hand_edited_doc_block_is_a_check_error (__main__.RiderDocsTest.test_hand_edited_doc_block_is_a_check_error) ... ok
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
Ran 142 tests in 9.314s

OK
```
