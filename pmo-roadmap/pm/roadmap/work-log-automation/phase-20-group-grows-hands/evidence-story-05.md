# Evidence - WLA-20-05

- **Story:** WLA-20-05 - Questions answer with buttons
- **Status:** done
- **Date:** 2026-07-11

## Proof

Two captured runs, both green:

1. **20:37:15Z — WITHOUT Pillow** (the contract's
   `--tests-capture`): 147 interface tests OK (140 → 147: the
   seven QuestionNavTest legs) + fitness 8 OK. The legs: a bound
   AND armed session's question carries exactly the five-button
   keyboard, routed to its home topic; an unbound question keeps
   today's card (no keyboard) and so does an unarmed one; arrow
   taps produce exactly one named-key send through the driver;
   Enter edits the card to say what was sent; 📸 delivers the
   story-01 capture flow; and the two refusal corners hold — a
   forged tap without a binding and a tap on an unarmed binding
   both refuse with ZERO keystrokes and ZERO arming (the
   "never arms" invariant, asserted against state).
2. **20:37:24Z — WITH Pillow** (proof venv): 147 OK, one
   pre-existing skip — the same flows with the renderer live.

The keyboard is deliberately dumb (it never parses the menu — 📸
shows the truth, arrows move, Enter commits) and deliberately
strict (eligibility = the two grants that already exist, bound +
armed; the proposal path with one-tap arming remains the only way
consent enters). Taps inherit the story-03 owner check upstream of
all of this.

### Captured run — 2026-07-11T20:37:15Z

- **Command:** `bash -c /usr/bin/python3 pmo-roadmap/tests/telegram-interface-tests.py 2>&1 | tail -3
/usr/bin/python3 pmo-roadmap/tests/telegram-fitness-tests.py 2>&1 | tail -3`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 2661686fd9059eda773c035896b2b6ea60f8844c

```text
Ran 147 tests in 8.706s

OK (skipped=10)
Ran 8 tests in 0.142s

OK
```

### Captured run — 2026-07-11T20:37:24Z

- **Command:** `/private/tmp/claude-501/-Users-karol-dev-code-delivery-workbench/810a20d6-6a03-40b4-86b4-a69112bb7ad6/scratchpad/pilenv/bin/python pmo-roadmap/tests/telegram-interface-tests.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 2661686fd9059eda773c035896b2b6ea60f8844c

```text
test_decide_pushes_only_notifications_coalesced (__main__.AgentEventsReaderTest) ... ok
test_malformed_lines_are_skipped_not_fatal (__main__.AgentEventsReaderTest) ... ok
test_missing_file_is_empty (__main__.AgentEventsReaderTest) ... ok
test_partial_tail_waits_for_its_newline (__main__.AgentEventsReaderTest) ... ok
test_reads_incrementally_by_offset (__main__.AgentEventsReaderTest) ... ok
test_truncation_resets_honestly (__main__.AgentEventsReaderTest) ... ok
test_one_card_edits_through_its_lifecycle (__main__.CardLifecycleTest) ... ok
test_rejection_edits_the_card_too (__main__.CardLifecycleTest) ... ok
test_proposal_expires (__main__.ConsentTest) ... ok
test_proposal_is_single_use (__main__.ConsentTest) ... ok
test_reject_executes_nothing (__main__.ConsentTest) ... ok
test_unpaired_callback_refused (__main__.ConsentTest) ... ok
test_approved_dishonest_done_flip_is_refused_with_banner (__main__.CrownCaseTest) ... ok
test_honest_flip_executes (__main__.CrownCaseTest) ... ok
test_unknown_story_never_becomes_a_proposal (__main__.CrownCaseTest) ... ok
test_content_hash_gates (__main__.DriverMannersTest) ... ok
test_literal_then_settle_then_enter_separately (__main__.DriverMannersTest) ... ok
test_recovery_verbs_follow_capability (__main__.DriverMannersTest) ... ok
test_resume_launch_only_when_supported (__main__.DriverMannersTest) ... ok
test_send_key_is_a_single_named_key (__main__.DriverMannersTest) ... ok
test_settle_is_per_harness_from_the_table (__main__.DriverMannersTest) ... ok
test_launch_all_supported_harnesses (__main__.DriverTest) ... ok
test_launched_session_starts_unarmed (__main__.DriverTest) ... ok
test_unsupported_harness_refused (__main__.DriverTest) ... ok
test_bold_code_pre_become_entities (__main__.EntitiesTest) ... ok
test_chunk_prefers_line_boundaries_and_rescopes (__main__.EntitiesTest) ... ok
test_hostile_characters_need_no_escaping (__main__.EntitiesTest) ... ok
test_offsets_are_utf16_after_emoji (__main__.EntitiesTest) ... ok
test_a_question_routes_home_to_its_repo_topic (__main__.FlowingConversationTest) ... ok
test_plain_text_without_a_binding_is_refused_gently (__main__.FlowingConversationTest) ... ok
test_steer_then_plain_text_flows_no_tap (__main__.FlowingConversationTest) ... ok
test_unsteer_stops_the_flow (__main__.FlowingConversationTest) ... ok
test_notification_pushes_in_the_same_drain (__main__.HookDrainTest) ... ok
test_restart_never_repushes (__main__.HookDrainTest) ... ok
test_stop_records_but_does_not_push (__main__.HookDrainTest) ... ok
test_unpaired_drain_is_silent_and_consumes_nothing (__main__.HookDrainTest) ... ok
test_image_live_expires_and_unlive_stops (__main__.ImageLiveViewTest) ... ok
test_image_live_is_read_only (__main__.ImageLiveViewTest) ... ok
test_live_posts_a_photo_and_edits_media_on_change_only (__main__.ImageLiveViewTest) ... ok
test_live_text_forces_text_mode_despite_renderer (__main__.ImageLiveViewTest) ... ok
test_create_for_real_lands_on_the_rails (__main__.LifecycleTest)
The full leg, no fakes: scaffold → rails → doctor → ... ok
test_create_outside_roots_refused_before_proposal (__main__.LifecycleTest) ... ok
test_create_step_sequence_with_scripted_runner (__main__.LifecycleTest) ... ok
test_open_requires_rails_repo_within_roots (__main__.LifecycleTest) ... ok
test_live_view_edits_only_on_change (__main__.LiveViewTest) ... ok
test_live_view_expires (__main__.LiveViewTest) ... ok
test_live_view_is_read_only (__main__.LiveViewTest) ... ok
test_burst_arrives_ordered_and_merged (__main__.MessageQueueTest) ... ok
test_entity_rejection_falls_back_to_plain (__main__.MessageQueueTest) ... ok
test_flood_control_pauses_and_retries (__main__.MessageQueueTest) ... ok
test_oversize_text_chunks_at_send_layer (__main__.MessageQueueTest) ... ok
test_status_edits_in_place (__main__.MessageQueueTest) ... ok
test_expired_token_refused (__main__.PairingTest) ... ok
test_no_outstanding_token_refused (__main__.PairingTest) ... ok
test_pair_then_reuse_refused (__main__.PairingTest) ... ok
test_repair_revokes_previous_binding (__main__.PairingTest) ... ok
test_state_file_is_owner_only (__main__.PairingTest) ... ok
test_token_from_separate_pair_process_is_honored (__main__.PairingTest) ... ok
test_token_stored_hashed_not_cleartext (__main__.PairingTest) ... ok
test_unpaired_chat_gets_prompt_then_silence (__main__.PairingTest) ... ok
test_wrong_token_refused (__main__.PairingTest) ... ok
test_consent_command_refused_for_stranger_owner_fine (__main__.PerPersonConsentTest) ... ok
test_every_tap_refused_for_stranger (__main__.PerPersonConsentTest) ... ok
test_owner_recorded_status_says_so (__main__.PerPersonConsentTest) ... ok
test_pair_records_owner_and_it_round_trips (__main__.PerPersonConsentTest) ... ok
test_reads_stay_chat_scoped (__main__.PerPersonConsentTest) ... ok
test_relay_refused_for_stranger_flows_for_owner (__main__.PerPersonConsentTest) ... ok
test_status_warns_on_legacy_pairing (__main__.PerPersonConsentTest) ... ok
test_adjacent_texts_merge_statuses_coalesce (__main__.PlanBatchTest) ... ok
test_merge_respects_the_cap (__main__.PlanBatchTest) ... ok
test_the_whole_pocket_desk_in_one_flow (__main__.PocketDeskExitExamTest) ... ok
test_arming_expires (__main__.QARelayTest) ... ok
test_dead_pane_is_refused (__main__.QARelayTest) ... ok
test_disarm_and_status (__main__.QARelayTest) ... ok
test_no_keystroke_without_a_grant (__main__.QARelayTest) ... ok
test_question_surfaces_with_story_correlation (__main__.QARelayTest) ... ok
test_recycled_pane_id_is_refused (__main__.QARelayTest) ... ok
test_reply_approval_is_the_arming_grant (__main__.QARelayTest) ... ok
test_reply_reaches_the_right_pane_when_armed (__main__.QARelayTest) ... ok
test_reply_to_a_session_outside_tmux_explains_itself (__main__.QARelayTest) ... ok
test_unsteerable_sessions_are_marked (__main__.QARelayTest) ... ok
test_bound_and_armed_question_carries_the_keyboard (__main__.QuestionNavTest) ... ok
test_forged_tap_without_binding_refuses_and_never_arms (__main__.QuestionNavTest) ... ok
test_nav_taps_drive_the_prompt_and_enter_notes_it (__main__.QuestionNavTest) ... ok
test_peek_delivers_the_screen_flow (__main__.QuestionNavTest) ... ok
test_tap_on_unarmed_binding_refuses_and_never_arms (__main__.QuestionNavTest) ... ok
test_unarmed_question_keeps_todays_card (__main__.QuestionNavTest) ... ok
test_unbound_question_keeps_todays_card (__main__.QuestionNavTest) ... ok
test_events_render_real_log (__main__.ReadSurfaceTest) ... ok
test_peek_is_read_only_capture (__main__.ReadSurfaceTest) ... ok
test_sessions_render_correlation (__main__.ReadSurfaceTest) ... ok
test_state_renders_real_feed (__main__.ReadSurfaceTest) ... ok
test_steer_a_dead_session_offers_capability_recovery (__main__.RecoveryTest) ... ok
test_story_argv_allow_list_is_two_verbs (__main__.SchemaComplianceTest) ... ok
test_unproven_feed_schema_refused_politely (__main__.SchemaComplianceTest) ... ok
test_unproven_sessions_schema_refused_politely (__main__.SchemaComplianceTest) ... ok
test_fallback_without_renderer_states_reason (__main__.ScreenCommandTest) ... ok
test_refresh_edits_the_same_photo_message (__main__.ScreenCommandTest) ... ok
test_screen_is_read_only (__main__.ScreenCommandTest) ... ok
test_screen_sends_photo_with_refresh_button (__main__.ScreenCommandTest) ... ok
test_screen_unbound_and_argless_states_usage (__main__.ScreenCommandTest) ... ok
test_ansi_matrix_renders_to_png (__main__.ScreenshotRendererTest) ... ok
test_forced_unavailable_returns_none_with_reason (__main__.ScreenshotRendererTest) ... ok
test_garbage_sgr_never_raises (__main__.ScreenshotRendererTest) ... ok
test_live_mode_is_lighter_than_full (__main__.ScreenshotRendererTest) ... ok
test_strip_non_sgr_keeps_colors (__main__.ScreenshotRendererTest) ... ok
test_ambiguous_match_lists_candidates (__main__.SendCommandTest) ... ok
test_no_match_says_so (__main__.SendCommandTest) ... ok
test_send_a_clean_file_goes_straight_through (__main__.SendCommandTest) ... ok
test_send_a_secret_is_refused_by_name (__main__.SendCommandTest) ... ok
test_send_the_config_by_name_is_refused (__main__.SendCommandTest) ... ok
test_a_clean_file_passes_all_locks (__main__.SendLocksTest) ... ok
test_lock1_traversal (__main__.SendLocksTest) ... ok
test_lock2_hidden (__main__.SendLocksTest) ... ok
test_lock3_secret_pattern (__main__.SendLocksTest) ... ok
test_lock4_size (__main__.SendLocksTest) ... ok
test_lock5_gitignore (__main__.SendLocksTest) ... ok
test_lock6_gitleaks_rule (__main__.SendLocksTest) ... skipped 'the gitleaks lock needs tomllib (py3.11+); it abstains below that'
test_lock7_state_dir (__main__.SendLocksTest) ... ok
test_lock7_state_file_by_name (__main__.SendLocksTest) ... ok
test_resolve_exact_glob_and_substring (__main__.SendLocksTest) ... ok
test_env_token_overrides_missing_config (__main__.TokenHygieneTest) ... ok
test_missing_token_error_names_path_not_content (__main__.TokenHygieneTest) ... ok
test_transport_errors_never_carry_the_token (__main__.TokenHygieneTest) ... ok
test_builtin_table_is_closed (__main__.ToolbarConfigTest) ... ok
test_buttons_route_keys_to_kb_and_the_rest_to_tb (__main__.ToolbarConfigTest) ... ok
test_config_reshapes_grid_and_adds_text_action (__main__.ToolbarConfigTest) ... ok
test_default_grids_per_harness_and_fallback (__main__.ToolbarConfigTest) ... ok
test_loader_never_raises_on_garbage (__main__.ToolbarConfigTest) ... ok
test_toolbar_only_offered_when_bound (__main__.ToolbarTest) ... ok
test_toolbar_press_fires_a_key_no_extra_tap (__main__.ToolbarTest) ... ok
test_toolbar_press_without_binding_refused (__main__.ToolbarTest) ... ok
test_builtin_screen_tap_produces_the_screen_flow (__main__.ToolbarUpgradeTest) ... ok
test_command_menu_registers_and_opts_out (__main__.ToolbarUpgradeTest) ... ok
test_dismiss_edits_the_card_and_unknown_action_refused (__main__.ToolbarUpgradeTest) ... ok
test_tap_without_binding_refused (__main__.ToolbarUpgradeTest) ... ok
test_text_action_types_through_the_driver (__main__.ToolbarUpgradeTest) ... ok
test_toolbar_renders_the_harness_grid (__main__.ToolbarUpgradeTest) ... ok
test_bindings_persist_across_restart (__main__.TopicRouterTest) ... ok
test_flat_chat_is_the_none_topic (__main__.TopicRouterTest) ... ok
test_repo_bind_scope_and_reverse (__main__.TopicRouterTest) ... ok
test_session_binding_expires_but_activity_refreshes (__main__.TopicRouterTest) ... ok
test_unbind_repo_cascades_to_session (__main__.TopicRouterTest) ... ok
test_bind_then_commands_scope_to_the_topic (__main__.TopicScopingTest) ... ok
test_flat_chat_still_uses_active_repo (__main__.TopicScopingTest) ... ok
test_replies_land_in_the_originating_topic (__main__.TopicScopingTest) ... ok
test_unbound_topic_has_no_repo (__main__.TopicScopingTest) ... ok

----------------------------------------------------------------------
Ran 147 tests in 9.363s

OK (skipped=1)
```
