# Evidence - WLA-27-08

- **Story:** WLA-27-08 - Make every everyday word agree
- **Status:** done
- **Date:** 2026-07-25

## One shared everyday presentation

The new pure
[`presentation.py`](../../../../lib/dw_pmo/presentation.py) module owns the
versioned `delivery-workbench-presentation@1` document, the ten exact preferred
concept names and definitions, task-first CLI help, and the shared presenters
for status, roadmap-step review/results, bounded and program live delivery,
start review, action review, and notifications. Each presentation declares
that it starts no work, writes no state, selects no next work, and grants no
permission.

CLI, Workbench, rider, and notification adapters now render those presentation
documents over canonical facts. They do not reinterpret eligibility,
permission, review, cost, or next-work policy. The existing exact status, step,
run, program, notification, JSON, MCP, HTTP, event, and persisted documents
remain unchanged. `/api/presentation` and `/api/presentation/status` are new
pure HTTP wrappers; `/api/status` retains byte-for-byte core parity.

## Complete surface census and drift enforcement

The versioned
[`product-language-surfaces-v1.json`](../../../../tests/product-language-surfaces-v1.json)
manifest accounts for every WLA-27-01 inventory entry: fifteen everyday or
mixed surfaces are migrated and three architecture/reference surfaces remain
explicitly technical/audit. Every entry names its source and proof; there is no
silent or unclassified remainder.

The expanded executable product-language check verifies:

- the runtime catalog against the reviewed language contract;
- the complete eighteen-surface disposition census;
- reserved engineering-language exclusion in eight marked everyday source
  regions;
- seven repeatable real-presenter snapshots spanning every concept;
- presentation purity flags and canonical adapter wiring;
- Workbench catalog/fallback parity and the explicit technical boundary; and
- exact source/vendor mirror presence.

## Task-first human paths with lossless inspection

Human CLI help and output, Workbench arrival/setup/live views, notification
messages, all four agent riders, README onboarding, and product docs now use
`delivery plan`, `team`, `work`, `review`, `decision`, `blocker`,
`permission`, `progress`, `cost`, and `next step` consistently. Ordinary task
and outcome come first. Exact commands, paths, identities, hashes, tokens,
states, pending-request identities, source facts, and raw documents remain
copyable beneath the explicit **Technical details** label.

The new [everyday delivery guide](../../../../../docs/everyday-delivery.md)
teaches the WLA-27-02 task path end to end: arrival, setup, delivery-plan
review, team/review, live progress, blocker/decision handling, recovery,
proof/completion, and technical inspection. Architecture and interoperability
guides remain linked and retain exact engineering language.

## Regression, device, and distribution proof

- The complete core suite passes all 492 tests in 898.309 seconds, including
  exact core/MCP/HTTP/CLI parity and pending-decision identity under the
  technical boundary.
- The captured focused presenter/setup/status suite passes 26 tests; roadmap
  CLI, HTTP explorer, all 153 Telegram tests (nine optional Pillow cases
  skipped), docs/link checks, syntax checks, rider parity, and update/mirror
  checks pass.
- The browser harness renders all 88 canonical desktop/mobile viewports,
  including arrival, setup review, status, bounded/program live delivery,
  actions, decisions, refusals, permission/cost, receipts, and technical
  inspection. Direct inspection of retained 1440x900 and 390x844 setup-review
  captures confirmed the task hierarchy, readiness, no-start disclosure,
  readable controls, and intentional mobile navigation/choice scrolling
  without clipped task content.
- Fresh wheel and source distributions build and install on Python 3.9. The
  packaged CLI/MCP/HTTP/Workbench/SSE exams keep dormant no-program behavior,
  deliberate steps, bounded orchestration, outward signals, crash recovery,
  and autonomous three-story/two-phase delivery green. The autonomous exam
  replays and streams 203 events with nine conductor and eighteen
  delivery-boundary crash recoveries and no duplicate starts.
- The certification command exits zero only after package smoke, roadmap
  health, and `git diff --check`; its exact command and bounded output follow.

## Captured proof

### Captured run — 2026-07-26T01:18:33Z

- **Command:** `bash -o pipefail -c 
set -e
python3 pmo-roadmap/tests/product-language-contract.py
python3 pmo-roadmap/tests/dw-core-tests.py EverydayPresentationTest DeliverySetupTest StatusBriefingTest
bash pmo-roadmap/tests/roadmap-cli.sh
python3 pmo-roadmap/tests/telegram-interface-tests.py
bash pmo-roadmap/tests/workbench-explorer.sh
bash pmo-roadmap/tests/workbench-ui-smoke.sh
bash pmo-roadmap/tests/docs-lint.sh
node --check pmo-roadmap/workbench/app.js
python3 -m py_compile pmo-roadmap/lib/dw_pmo/presentation.py pmo-roadmap/lib/dw_pmo/status.py pmo-roadmap/lib/dw_pmo/step.py pmo-roadmap/lib/dw_pmo/notifications.py pmo-roadmap/lib/dw_pmo/delivery_setup.py pmo-roadmap/lib/dw_pmo/workbench.py
cmp pmo-roadmap/lib/dw_pmo/presentation.py .githooks/dw_pmo/presentation.py
cmp pmo-roadmap/lib/dw_pmo/status.py .githooks/dw_pmo/status.py
cmp pmo-roadmap/bin/dw .githooks/dw
cmp pmo-roadmap/workbench/app.js .githooks/workbench/app.js
cmp pmo-roadmap/workbench/index.html .githooks/workbench/index.html
cmp pmo-roadmap/workbench/style.css .githooks/workbench/style.css
.githooks/dw rider docs --check
bash pmo-roadmap/update.sh . --check
bash pmo-roadmap/tests/package-smoke.sh
.githooks/dw check work-log-automation
git diff --check
`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 2dbc94019263e8423d99c3d2d9b005397b673e76

```text
product-language-contract: ok (10 concepts, 18 surfaces, 15 migrated, 18 reserved terms, 13 fixtures, 7 snapshots, 8 source regions)
test_cli_help_uses_the_shared_task_language (__main__.EverydayPresentationTest.test_cli_help_uses_the_shared_task_language) ... ok
test_real_presenters_match_versioned_human_snapshots (__main__.EverydayPresentationTest.test_real_presenters_match_versioned_human_snapshots) ... ok
test_runtime_catalog_matches_the_reviewed_contract (__main__.EverydayPresentationTest.test_runtime_catalog_matches_the_reviewed_contract) ... ok
test_front_door_names_scope_three_modes_effects_and_permissions (__main__.DeliverySetupTest.test_front_door_names_scope_three_modes_effects_and_permissions) ... ok
test_human_cli_and_http_render_the_same_choice_and_readiness (__main__.DeliverySetupTest.test_human_cli_and_http_render_the_same_choice_and_readiness) ... ok
test_missing_or_invalid_inputs_name_the_delivery_decision_and_correction (__main__.DeliverySetupTest.test_missing_or_invalid_inputs_name_the_delivery_decision_and_correction) ... ok
test_setup_and_cancel_model_are_repeatable_and_write_nothing (__main__.DeliverySetupTest.test_setup_and_cancel_model_are_repeatable_and_write_nothing) ... ok
test_action_targets_next_story_phase_not_a_closed_pointer (__main__.StatusBriefingTest.test_action_targets_next_story_phase_not_a_closed_pointer) ... ok
test_attention_precedence_for_rails_roadmap_and_rewrite (__main__.StatusBriefingTest.test_attention_precedence_for_rails_roadmap_and_rewrite) ... ok
test_captured_evidence_recommends_the_guarded_done_transition (__main__.StatusBriefingTest.test_captured_evidence_recommends_the_guarded_done_transition) ... ok
test_dirty_active_work_continues_but_unowned_work_is_reviewed (__main__.StatusBriefingTest.test_dirty_active_work_continues_but_unowned_work_is_reviewed) ... ok
test_empty_roadmap_directory_is_attention_not_ready (__main__.StatusBriefingTest.test_empty_roadmap_directory_is_attention_not_ready) ... ok
test_http_status_presentation_wraps_but_does_not_replace_exact_status (__main__.StatusBriefingTest.test_http_status_presentation_wraps_but_does_not_replace_exact_status) ... ok
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

----------------------------------------------------------------------
Ran 26 tests in 17.316s

OK
roadmap-cli.sh: ok
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
test_program_response_is_carried_to_the_local_exact_boundary (__main__.NotificationDecisionTest.test_program_response_is_carried_to_the_local_exact_boundary) ... ok
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
test_command_menu_registers_and_opts_out (__main__.ToolbarUpgradeTest.test_command_menu_registers_and_opts_out) ... 
[PMO_EVIDENCE_OUTPUT_TRUNCATED]
```
