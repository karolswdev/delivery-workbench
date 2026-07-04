# Evidence - WLA-14-04

- **Story:** WLA-14-04 - Topics are projects, and conversation flows
- **Status:** done
- **Date:** 2026-07-04

## Proof

### Captured run — 2026-07-04T19:46:30Z

- **Command:** `bash -c echo "== batteries (both pythons + core) =="
python3 pmo-roadmap/tests/telegram-interface-tests.py 2>&1 | tail -3 | head -1
/usr/bin/python3 pmo-roadmap/tests/telegram-interface-tests.py 2>&1 | tail -3 | head -1
python3 pmo-roadmap/tests/dw-core-tests.py 2>&1 | grep -E "^(OK|Ran)" | tail -2
bash pmo-roadmap/tests/docs-lint.sh 2>&1 | tail -1
echo
echo "== the topic tests, named =="
python3 pmo-roadmap/tests/telegram-interface-tests.py TopicRouterTest TopicScopingTest FlowingConversationTest 2>&1 | grep -E "test_|^OK|^Ran" | tail -20`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** b8c2f2606274031ede45f9f6b276d5936cd84d9f

```text
== batteries (both pythons + core) ==
Ran 79 tests in 5.856s
Ran 79 tests in 5.392s
Ran 160 tests in 13.016s
OK
docs-lint.sh: ok (0s)

== the topic tests, named ==
test_bindings_persist_across_restart (__main__.TopicRouterTest.test_bindings_persist_across_restart) ... ok
test_flat_chat_is_the_none_topic (__main__.TopicRouterTest.test_flat_chat_is_the_none_topic) ... ok
test_repo_bind_scope_and_reverse (__main__.TopicRouterTest.test_repo_bind_scope_and_reverse) ... ok
test_session_binding_expires_but_activity_refreshes (__main__.TopicRouterTest.test_session_binding_expires_but_activity_refreshes) ... ok
test_unbind_repo_cascades_to_session (__main__.TopicRouterTest.test_unbind_repo_cascades_to_session) ... ok
test_bind_then_commands_scope_to_the_topic (__main__.TopicScopingTest.test_bind_then_commands_scope_to_the_topic) ... ok
test_flat_chat_still_uses_active_repo (__main__.TopicScopingTest.test_flat_chat_still_uses_active_repo) ... ok
test_replies_land_in_the_originating_topic (__main__.TopicScopingTest.test_replies_land_in_the_originating_topic) ... ok
test_unbound_topic_has_no_repo (__main__.TopicScopingTest.test_unbound_topic_has_no_repo) ... ok
test_a_question_routes_home_to_its_repo_topic (__main__.FlowingConversationTest.test_a_question_routes_home_to_its_repo_topic) ... ok
test_plain_text_without_a_binding_is_refused_gently (__main__.FlowingConversationTest.test_plain_text_without_a_binding_is_refused_gently) ... ok
test_steer_then_plain_text_flows_no_tap (__main__.FlowingConversationTest.test_steer_then_plain_text_flows_no_tap) ... ok
test_unsteer_stops_the_flow (__main__.FlowingConversationTest.test_unsteer_stops_the_flow) ... ok
Ran 13 tests in 0.672s
OK
```
