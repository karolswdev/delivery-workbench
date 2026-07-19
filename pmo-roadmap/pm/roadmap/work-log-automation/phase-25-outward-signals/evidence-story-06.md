# Evidence - WLA-25-06

- **Story:** WLA-25-06 - Notify the operator durably
- **Status:** done
- **Date:** 2026-07-19

## Proof

Operator notifications are now durable facts with a consented delivery
path and a typed response port:

- **Derived, never invented.** `lib/dw_pmo/notifications.py` computes
  every notification as a pure function of the run ledgers and signal
  chains: `checkpoint-pending` (with a typed request port),
  `awaiting-certification`, `run-blocked`, `nudge-budget-exhausted`,
  and — behind the operator-local `branch_signals` opt-in settled by
  the contract — `branch-signal` for red observed branches no run owns.
  Only two small append-only stores exist (`acks.jsonl`,
  `deliveries.jsonl` under `.git/pmo-notifications/`); there is no
  cache to delete and derivation is restart-stable by construction.
- **One model, four surfaces.** `dw notifications list|ack|delivered`,
  MCP `dw_notifications` + guarded `dw_notifications_ack`, HTTP
  `GET /api/notifications` + receipted `POST /api/notifications/ack`
  (the read-only fitness census grew deliberately from 7 to 8 POST
  routes), and a Run view card that rides the WLA-25-05 live tail with
  per-item ack buttons.
- **Typed checkpoint responses.** A `checkpoint-pending` notification
  carries a correlation id and the closed decision vocabulary
  (approve|reject — the run contract's schema for the score-declared
  approval node). The new owner-gated Telegram `/decision <correlation>
  approve|reject` command resolves the correlation against the current
  derivation (stale or unknown ids refuse with no decision applied) and
  then crosses the ordinary exact-token `run checkpoint` boundary via
  the rails CLI seam — the phone supplies the decision content, the
  rails supply the authority. Persistent refusal receipts for typed
  responses arrive with WLA-25-08's outstanding-request records.
- **Consented, fail-safe delivery.** `run.py notify` is a bounded push
  pass mirroring `dw signals observe`: it sends unread, undelivered
  facts to the paired chat (the Phase-20 consented destination; unpaired
  exits 2 and facts stay local), records every attempt outcome through
  `dw notifications delivered`, and stops at the 3-attempt ceiling. The
  outbound body is content-safe by test: facts, references, the ack id,
  and the `/decision` instruction — never a token, an apply command, or
  a third-party body.

Seven new tests: two core (derive/ack/correlate with the exact-token
decision round-trip; delivery ceiling + CLI/MCP/HTTP parity + HTTP ack +
branch-signal opt-in) raising the core suite 323 → 325 on both floors,
and five Telegram tests (owner decision applies through the rails,
stale/usage refusals, stranger refusal in a group, the push pass sending
and recording, and the unpaired no-op) raising the interface suite
147 → 152.

Both runs below are authoritative, in order:

- **2026-07-19T14:27:12Z (exit 0)** — the live demo on the installed
  rails: a granted run pauses at a score-declared human checkpoint; the
  derived notification prints its content-safe outbound preview (with
  the `/decision` instruction and no token or `--expect` anywhere); the
  decision applies through the exact-token boundary; the pending set
  re-derives empty (stale correlations refuse); the terminal
  `awaiting-certification` notification acks idempotently; and three
  recorded delivery failures hit the retry ceiling.
- **2026-07-19T14:27:33Z (exit 0)** — the authoritative battery: 325
  core tests on both Python floors, the 152-test Telegram interface
  suite, the 10 fitness tests, docs lint/snippets, canon lint, agent
  surface, the MCP server suite, the 32-render UI smoke, roadmap check,
  rider parity, vendored-rails check, structural doc pins, and diff
  hygiene.

## Manual review

- Confirmed the herdr-remote lesson held in the implementation: no
  transport-equals-authority path exists — the Telegram surface never
  carries a token or applies anything remotely; every decision crosses
  the local exact-token boundary, and the push pass is send-only to the
  already-consented paired chat.
- OWED (recorded like the Phase-20 phone legs): the live phone walk —
  receive a real checkpoint-pending message on the desk bot, reply
  `/decision … approve`, and watch the Run view update — captured as
  screenshots into this phase's evidence assets when Karol next walks
  the phone leg.

### Captured run — 2026-07-19T14:27:12Z

- **Command:** `bash -o pipefail -c 
set -e
python3 - <<PYDEMO
import json, subprocess, sys, tempfile
from pathlib import Path

repo_src = Path(".").resolve()
tmp = Path(tempfile.mkdtemp(prefix="dw-notify-demo."))
repo = tmp / "repo"; repo.mkdir()

def sh(*argv, cwd=repo, ok=True):
    r = subprocess.run([str(a) for a in argv], cwd=str(cwd), text=True,
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if ok and r.returncode != 0:
        raise SystemExit("command failed: %s\n%s" % (argv, r.stderr))
    return r

sh("git", "init", "-q", "-b", "main")
sh("git", "config", "user.name", "Demo")
sh("git", "config", "user.email", "demo@example.test")
sh(repo_src / "pmo-roadmap" / "bootstrap" / "new-project.sh", repo, "sample", "Sample", "SMP")
sh(repo_src / "pmo-roadmap" / "install.sh", repo, "--skip-bootstrap")
dw = repo / ".githooks" / "dw"
sh(dw, "story", "status", "sample", "0", "SMP-0-01", "in-progress")
sh(dw, "rider", "docs")
score = {"kind": "delivery-workbench-orchestration", "schema_version": 1,
  "slug": "notify-loop", "title": "Notify Loop", "project": "sample",
  "defaults": {"max_concurrency": 2, "max_wall_seconds": 3600, "max_agent_starts": 10,
               "max_check_starts": 10, "default_timeout_seconds": 60,
               "max_artifact_bytes": 1000000, "max_nudges": 3},
  "nodes": [
    {"id": "worker", "type": "agent", "role": "implementation", "profile": "worker-write",
     "prompt": "Do the granted work.", "capabilities": ["repository-read", "repository-write"],
     "workspace": "isolated-worktree"},
    {"id": "human-gate", "type": "approval", "needs": ["worker"],
     "prompt": "Review the worker result before continuing."}]}
(repo / "pm" / "orchestration").mkdir(parents=True, exist_ok=True)
(repo / "pm" / "orchestration" / "notify-loop.json").write_text(json.dumps(score, indent=2) + "\n")
sh("git", "add", "."); sh("git", "-c", "core.hooksPath=/dev/null", "commit", "-q", "-m", "score")
store = repo / ".git" / "pmo-orchestration"; store.mkdir(exist_ok=True)
(store / "drivers.json").write_text(json.dumps({"kind": "delivery-workbench-driver-config",
  "schema_version": 1, "workspace_root": None, "profiles": {
    "worker-write": {"adapter": "fixture", "capabilities": ["repository-read", "repository-write"],
                     "workspace_modes": ["isolated-worktree"]}}}, indent=2) + "\n")

plan_out = sh(dw, "run", "plan", "notify-loop", "--project", "sample", "--story", "SMP-0-01", "--json")
plan = json.loads(plan_out.stdout)
plan_file = tmp / "plan.json"; plan_file.write_text(plan_out.stdout)
started = json.loads(sh(dw, "run", "start", "--plan", plan_file, "--expect", plan["start_token"],
                        "--approve", "--operator", "notify-demo", "--json").stdout)
run_id = started["run_id"]

def tick():
    preview = json.loads(sh(dw, "run", "preview", run_id, "tick", "--json").stdout)
    return json.loads(sh(dw, "run", "tick", run_id, "--expect", preview["act_token"], "--json").stdout)

for _ in range(10):
    result = tick()
    if result["state"] == "awaiting-approval":
        break
assert result["state"] == "awaiting-approval"
print("run paused at the human checkpoint")

doc = json.loads(sh(dw, "notifications", "list", "--json").stdout)
pending = [n for n in doc["notifications"] if n["kind"] == "checkpoint-pending"]
assert len(pending) == 1 and pending[0]["unread"]
correlation = pending[0]["request"]["correlation_id"]
outbound = pending[0]["outbound"]
assert "/decision " + correlation in outbound
assert "sha256:" not in outbound and "--expect" not in outbound
print("checkpoint-pending notification derived; outbound preview:")
print("  " + outbound.replace("\\n", "\\n  "))

preview = json.loads(sh(dw, "run", "preview", run_id, "checkpoint", "--decision", "approve", "--json").stdout)
decided = json.loads(sh(dw, "run", "checkpoint", run_id, "approve", "--expect", preview["act_token"], "--json").stdout)
print("typed response applied through the exact-token boundary; state:", decided["state"])

doc = json.loads(sh(dw, "notifications", "list", "--json").stdout)
assert not [n for n in doc["notifications"] if n["kind"] == "checkpoint-pending"]
print("stale correlation now refuses: pending set re-derives empty")

for _ in range(10):
    result = tick()
    if result["terminal"]:
        break
doc = json.loads(sh(dw, "notifications", "list", "--json").stdout)
awaiting = [n for n in doc["notifications"] if n["kind"] == "awaiting-certification"]
assert len(awaiting) == 1
nid = awaiting[0]["id"]
first = json.loads(sh(dw, "notifications", "ack", nid).stdout)
second = json.loads(sh(dw, "notifications", "ack", nid).stdout)
assert first["changed"] is True and second["changed"] is False
print("ack is idempotent and receipted")

sh(dw, "notifications", "delivered", nid, "--failed", "transport-error")
sh(dw, "notifications", "delivered", nid, "--failed", "transport-error")
sh(dw, "notifications", "delivered", nid, "--failed", "transport-error")
doc = json.loads(sh(dw, "notifications", "list", "--json").stdout)
entry = next(n for n in doc["notifications"] if n["id"] == nid)
assert entry["delivery_attempts"] == 3 and not entry["delivered"]
print("delivery failures recorded; retry ceiling holds at 3")

listing = sh(dw, "notifications", "list", ok=False)
print("DEMO COMPLETE: facts derive, previews travel, authority stays local")
PYDEMO
`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 28c7077f51745ec0e6023ba3d8190ca25e6c7b45

```text
run paused at the human checkpoint
checkpoint-pending notification derived; outbound preview:
  delivery-workbench: checkpoint-pending
  run: run-805818592e2020c7bd6ecbc1
  where: human-gate
  a named human checkpoint is waiting for a decision
  to decide, reply: /decision ntf-4c8dd967a327d84abb27821e approve|reject
  the decision applies only through the local exact-token checkpoint boundary
  ack: ntf-4c8dd967a327d84abb27821e
typed response applied through the exact-token boundary; state: active
stale correlation now refuses: pending set re-derives empty
ack is idempotent and receipted
delivery failures recorded; retry ceiling holds at 3
DEMO COMPLETE: facts derive, previews travel, authority stays local
```

### Captured run — 2026-07-19T14:27:33Z

- **Command:** `bash -o pipefail -c 
set -e
python3 pmo-roadmap/tests/dw-core-tests.py -q
/usr/bin/python3 pmo-roadmap/tests/dw-core-tests.py -q
/usr/bin/python3 pmo-roadmap/tests/telegram-interface-tests.py
/usr/bin/python3 pmo-roadmap/tests/telegram-fitness-tests.py
bash pmo-roadmap/tests/docs-lint.sh
bash pmo-roadmap/tests/docs-snippet-smoke.sh
bash pmo-roadmap/tests/canon-lint.sh
bash pmo-roadmap/tests/agent-surface.sh
bash pmo-roadmap/tests/mcp-server.sh
bash pmo-roadmap/tests/workbench-ui-smoke.sh
.githooks/dw check work-log-automation
.githooks/dw rider docs --check
pmo-roadmap/update.sh . --check
rg -q "dw notifications list" docs/interop.md
rg -q "api/notifications" docs/interop.md
rg -q "dw_notifications" docs/mcp.md
rg -q "dw_notifications" CLAUDE.md
rg -q "WLA-25-06" docs/signals.md
git diff --check
git diff --cached --check
`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 28c7077f51745ec0e6023ba3d8190ca25e6c7b45

```text
dw hook: codex_hooks is explicitly false in /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.hvnw5sp0/config.toml; respecting the opt-out
dw-workbench: 127.0.0.1 "GET /api/runs/run-68d073f33ea39b37eeb664f3/events?follow=0 HTTP/1.1" 200 -
dw-workbench: 127.0.0.1 "GET /api/runs/run-68d073f33ea39b37eeb664f3/events?follow=0 HTTP/1.1" 200 -
dw-workbench: 127.0.0.1 "POST /api/runs/run-68d073f33ea39b37eeb664f3/events HTTP/1.1" 405 -
dw-workbench: 127.0.0.1 "GET /api/signals/events?remote=origin&branch=sse-x&follow=0 HTTP/1.1" 200 -
dw-workbench: 127.0.0.1 "GET /api/runs/run-000000000000000000000000/events?follow=0 HTTP/1.1" 400 -
/opt/homebrew/Cellar/python@3.14/3.14.6/Frameworks/Python.framework/Versions/3.14/lib/python3.14/tempfile.py:484: ResourceWarning: Implicitly cleaning up <HTTPError 401: 'refused'>
  _warnings.warn(self.warn_message, ResourceWarning)
/opt/homebrew/Cellar/python@3.14/3.14.6/Frameworks/Python.framework/Versions/3.14/lib/python3.14/tempfile.py:484: ResourceWarning: Implicitly cleaning up <HTTPError 403: 'refused'>
  _warnings.warn(self.warn_message, ResourceWarning)
/opt/homebrew/Cellar/python@3.14/3.14.6/Frameworks/Python.framework/Versions/3.14/lib/python3.14/tempfile.py:484: ResourceWarning: Implicitly cleaning up <HTTPError 429: 'refused'>
  _warnings.warn(self.warn_message, ResourceWarning)
/opt/homebrew/Cellar/python@3.14/3.14.6/Frameworks/Python.framework/Versions/3.14/lib/python3.14/tempfile.py:484: ResourceWarning: Implicitly cleaning up <HTTPError 500: 'refused'>
  _warnings.warn(self.warn_message, ResourceWarning)
/opt/homebrew/Cellar/python@3.14/3.14.6/Frameworks/Python.framework/Versions/3.14/lib/python3.14/tempfile.py:484: ResourceWarning: Implicitly cleaning up <HTTPError 304: 'refused'>
  _warnings.warn(self.warn_message, ResourceWarning)
----------------------------------------------------------------------
Ran 325 tests in 174.621s

OK
dw hook: claude — 4 installed, 0 already present in /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.x7abgign/settings.json
dw hook: claude — 0 installed, 4 already present in /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.x7abgign/settings.json
dw hook: claude — 4 installed, 0 already present in /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.k71nrbxk/settings.json
dw hook: claude — 4 installed, 0 already present in /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.ri75bav4/settings.json
dw hook: claude — 4 removed from /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.ri75bav4/settings.json
dw hook: codex_hooks is explicitly false in /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.vnn7zjhc/config.toml; respecting the opt-out
dw-workbench: 127.0.0.1 "GET /api/runs/run-e855d537d75f50de46f49940/events?follow=0 HTTP/1.1" 200 -
dw-workbench: 127.0.0.1 "GET /api/runs/run-e855d537d75f50de46f49940/events?follow=0 HTTP/1.1" 200 -
dw-workbench: 127.0.0.1 "POST /api/runs/run-e855d537d75f50de46f49940/events HTTP/1.1" 405 -
dw-workbench: 127.0.0.1 "GET /api/signals/events?remote=origin&branch=sse-x&follow=0 HTTP/1.1" 200 -
dw-workbench: 127.0.0.1 "GET /api/runs/run-000000000000000000000000/events?follow=0 HTTP/1.1" 400 -
----------------------------------------------------------------------
Ran 325 tests in 151.549s

OK
dw hook: claude — 4 installed, 0 already present in /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.v_tqvcye/settings.json
dw hook: claude — 0 installed, 4 already present in /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.v_tqvcye/settings.json
dw hook: claude — 4 installed, 0 already present in /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.o5husd4u/settings.json
dw hook: claude — 4 installed, 0 already present in /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test._mfbwu4w/settings.json
dw hook: claude — 4 removed from /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test._mfbwu4w/settings.json
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
test_image_live_expires_and_unlive_stops (__main__.ImageLiveViewTest) ... skipped 'Pillow not installed'
test_image_live_is_read_only (__main__.ImageLiveViewTest) ... skipped 'Pillow not installed'
test_live_posts_a_photo_and_edits_media_on_change_only (__main__.ImageLiveViewTest) ... skipped 'Pillow not installed'
test_live_text_forces_text_mode_despite_renderer (__main__.ImageLiveViewTest) ... skipped 'Pillow not installed'
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
test_decision_applies_through_the_rails_for_the_owner (__main__.NotificationDecisionTest) ... ok
test_decision_from_a_stranger_is_refused (__main__.NotificationDecisionTest) ... ok
test_decision_refuses_stale_correlation_and_bad_usage (__main__.NotificationDecisionTest) ... ok
test_push_pass_sends_outbound_and_records_delivery (__main__.NotificationDecisionTest) ... ok
test_push_pass_without_pairing_sends_nothing (__main__.NotificationDecisionTest) ... ok
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
test_refresh_edits_the_same_photo_message (__main__.ScreenCommandTest) ... skipped 'Pillow not installed'
test_screen_is_read_only (__main__.ScreenCommandTest) ... ok
test_screen_sends_photo_with_refresh_button (__main__.ScreenCommandTest) ... skipped 'Pillow not installed'
test_screen_unbound_and_argless_states_usage (__main__.ScreenCommandTest) ... ok
test_ansi_matrix_renders_to_png (__main__.ScreenshotRendererTest) ... skipped 'Pillow not installed'
test_forced_unavailable_returns_none_with_reason (__main__.ScreenshotRendererTest) ... ok
test_garbage_sgr_never_raises (__main__.ScreenshotRendererTest) ... skipped 'Pillow not installed'
test_live_mode_is_lighter_than_full (__main__.ScreenshotRendererTest) ... skipped 'Pillow not installed'
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
Ran 152 tests in 12.479s

OK (skipped=10)
test_bot_api_strings_live_only_in_the_transport (__main__.ConsentFloorTest) ... ok
test_keystroke_methods_are_defined_only_in_the_driver (__main__.ConsentFloorTest) ... ok
test_send_keys_lives_only_in_the_driver (__main__.ConsentFloorTest) ... ok
test_consent_floor_catches_planted_send_keys (__main__.FitnessSelfTest) ... ok
test_layering_catches_a_planted_transport_import (__main__.FitnessSelfTest) ... ok
test_layering_catches_a_planted_violation_in_a_new_leaf (__main__.FitnessSelfTest) ... ok
test_leaves_stay_leaves (__main__.ImportLayeringTest) ... ok
test_no_import_cycles (__main__.ImportLayeringTest) ... ok
test_rails_seam_is_reached_only_through_the_interface (__main__.ImportLayeringTest) ... ok
test_transport_is_a_pure_leaf (__main__.ImportLayeringTest) ... ok

----------------------------------------------------------------------
Ran 10 tests in 0.167s

OK
docs-lint: ok (415 markdown files)
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
agent-surface.sh: ok
protocol exchange: ok (9 replies)
no-rails refusal: ok
mutation walk: ok (done-without-evidence refused; contract stamped, certification manual)
gate still blocks uncertified commits: ok
MCP/CLI byte-parity (timestamps normalized): ok
mcp-server.sh: ok
workbench-ui-smoke.sh: ok (32 viewport renders: 14 views + attention + ambiguity, desktop+mobile)
dw-workbench: shutting down
dw-workbench: serving /private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/pmo-ui-smoke.DvGSIR/repo
dw-workbench: http://127.0.0.1:22059/ (localhost or your own .ts.net tailnet; Ctrl-C to stop)
dw-workbench: writes require /api/mutations preview→apply or an exact /api/step/apply token; never stages, certifies, or commits
dw check: ok
dw rider docs: all rendered surfaces match canon
update.sh: up to date (vendored rails match source v1.14.0)
```
