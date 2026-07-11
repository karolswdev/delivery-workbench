# Evidence - WLA-17-06

- **Story:** WLA-17-06 - Guarded moves on the board
- **Status:** done
- **Date:** 2026-07-11

## Proof

The board acts, and it acts through the one guarded write path.
Dragging a card to a column (or the ⇄ affordance on every card, for
keyboards and touch) opens the move panel, which constructs exactly
the editor's `update_story_status` intent and walks the existing
preview → fingerprint-bound apply flow — no new server endpoint
exists. Client mirrors of the server rules gate the preview button
(a park demands its reason, a done-drop on an evidence-less story is
refused with the editor's message); the server stays the authority.
Drops on paused/closed lanes refuse with a notice; cross-phase drops
refuse (a story moves between columns of its own phase). Apply
re-reads the board from Markdown. Editor parity in the same commit:
`on-hold` joined the editor's status vocabulary with a reason field
and the matching client-side refusal. The snapshot affordance
(`?snapshot=1&automove=<story>:<column>`) mirrors the editor's
`autopreview` so headless capture can see the panel.

Screenshot: [board-move-panel.png](./assets/board-move-panel.png) —
the panel open on "move DM-1-01: ready → on-hold" with the required
reason field, above the live lane.

Two captured runs below, both authoritative:

1. **16:39:41Z** — the full core suite: 199 tests, exit 0 (the
   server-side rules the drag mirrors were pinned in WLA-17-01/02;
   no new server surface exists to test).
2. **16:39:53Z** — the live HTTP walk on a scratch roadmap through
   the real server: ready→in-progress previewed (200) and applied
   (200) with the row shown flipped; on-hold without reason refused
   400 naming --reason; with the reason applied 200 and the cell
   wearing `on-hold (pivot to the launch — since 2026-07-11)`;
   done-drop without evidence refused 400 by the same rule as the
   CLI; and the stale-fingerprint path — preview, drive-by edit
   underneath, apply — refused 409 with nothing written (the row
   shown unchanged after).

Also green this session (not captured): workbench-explorer.sh,
gate-parity.sh, package-smoke.sh, workbench-ui-smoke.sh (14
renders).

### Captured run — 2026-07-11T16:39:41Z

- **Command:** `/usr/bin/python3 pmo-roadmap/tests/dw-core-tests.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 2160428f401a3ceb181f02a0d89a27d22f13959e

```text
test_codex_flag_opt_out_respected (__main__.AgentHooksTest) ... dw hook: codex_hooks is explicitly false in /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test._i1q9pp5/config.toml; respecting the opt-out
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
Ran 199 tests in 12.433s

OK
dw hook: claude — 4 installed, 0 already present in /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test._f3k9dg2/settings.json
dw hook: claude — 0 installed, 4 already present in /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test._f3k9dg2/settings.json
dw hook: claude — 4 installed, 0 already present in /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.tnguhvlr/settings.json
dw hook: claude — 4 installed, 0 already present in /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.nih5lshb/settings.json
dw hook: claude — 4 removed from /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.nih5lshb/settings.json
```

### Captured run — 2026-07-11T16:39:53Z

- **Command:** `/private/tmp/claude-501/-Users-karol-dev-code-delivery-workbench/475abfb9-3a84-4a46-9535-cd63c3b7d3fd/scratchpad/wla-17-06-demo.sh`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 2160428f401a3ceb181f02a0d89a27d22f13959e

```text
== 1. the move a drag constructs: ready -> in-progress, preview then apply ==
preview http=200 fingerprint=sha256:d9d97691decf36274…
apply http=200
| DM-1-01 | First thing | in-progress | [story-01-first](./story-01-first.md) | - |

== 2. a drop into on-hold without a reason: the server refuses ==
preview http=400 error=a hold needs its why; pass --reason when parking a story on-hold/paused

== 3. with the reason: applied, the cell wears the why ==
apply http=200
| DM-1-01 | First thing | on-hold (pivot to the launch — since 2026-07-11) | [story-01-first](./story-01-first.md) | - |

== 4. a drop into done without evidence: refused by the same rule as the CLI ==
preview http=400 error=refusing to mark story done without evidence; pass --evidence-body or --evidence-from-file

== 5. the stale-fingerprint path: preview, mutate underneath, apply -> 409, nothing written ==
preview http=200
apply http=409 (expected 409) error=stale preview: source files changed after the preview was taken
| DM-1-01 | First thing | on-hold (pivot to the launch — since 2026-07-11) | [story-01-first](./story-01-first.md) | - |
dw-workbench: shutting down
dw-workbench: serving /private/tmp/dw-moves-demo.SI57NU
dw-workbench: http://127.0.0.1:23253/ (localhost or your own .ts.net tailnet; Ctrl-C to stop)
dw-workbench: writes happen only via /api/mutations preview→apply inside pm/roadmap; never commits
```
