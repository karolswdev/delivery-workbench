# Evidence - WLA-14-01

- **Story:** WLA-14-01 - Design: the absorption map
- **Status:** done
- **Date:** 2026-07-04

## Proof

### Captured run — 2026-07-04T18:37:53Z

- **Command:** `bash -c echo "== the map exists and lints =="
bash pmo-roadmap/tests/docs-lint.sh 2>&1 | tail -1
echo
echo "== every cited source verified in the studied clone (v4.3.5 @ 4e4fc31) =="
cd /private/tmp/claude-501/-Users-karol-dev-code-delivery-workbench/4832ba83-41fe-489c-beaf-887e8ed6b611/scratchpad/ccgram
git log -1 --format="clone at: %h %s"
for f in src/ccgram/entity_formatting.py src/ccgram/hook.py src/ccgram/event_reader.py src/ccgram/handlers/messaging_pipeline/message_queue.py src/ccgram/handlers/send/send_security.py src/ccgram/handlers/polling/window_tick/decide.py src/ccgram/topic_state_registry.py src/ccgram/providers/base.py src/ccgram/multiplexer/tmux.py src/ccgram/thread_router.py src/ccgram/handlers/text/text_handler.py src/ccgram/handlers/live/live_view.py src/ccgram/handlers/toolbar/toolbar_keyboard.py src/ccgram/session_lifecycle.py src/ccgram/config.py src/ccgram/handlers/shell/shell_commands.py src/ccgram/handlers/interactive/interactive_ui.py src/ccgram/llm/summarizer.py; do
  test -f "$f" && echo "  ok $f" || { echo "  MISSING $f"; exit 1; }
done
grep -c "MIT License" LICENSE
echo
echo "== key claims spot-checked =="
grep -n "def decide_tick" src/ccgram/handlers/polling/window_tick/decide.py
grep -n "def convert_to_entities" src/ccgram/entity_formatting.py
grep -n "def check_gitleaks_rules" src/ccgram/handlers/send/send_security.py
grep -n "_is_nested_session" src/ccgram/hook.py | head -1`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 7ce70d1a1dc396edf0ac7c27906b9cfdfca7ec3f

```text
== the map exists and lints ==
docs-lint.sh: ok (0s)

== every cited source verified in the studied clone (v4.3.5 @ 4e4fc31) ==
clone at: 4e4fc31 docs: update CHANGELOG.md for v4.3.5
  ok src/ccgram/entity_formatting.py
  ok src/ccgram/hook.py
  ok src/ccgram/event_reader.py
  ok src/ccgram/handlers/messaging_pipeline/message_queue.py
  ok src/ccgram/handlers/send/send_security.py
  ok src/ccgram/handlers/polling/window_tick/decide.py
  ok src/ccgram/topic_state_registry.py
  ok src/ccgram/providers/base.py
  ok src/ccgram/multiplexer/tmux.py
  ok src/ccgram/thread_router.py
  ok src/ccgram/handlers/text/text_handler.py
  ok src/ccgram/handlers/live/live_view.py
  ok src/ccgram/handlers/toolbar/toolbar_keyboard.py
  ok src/ccgram/session_lifecycle.py
  ok src/ccgram/config.py
  ok src/ccgram/handlers/shell/shell_commands.py
  ok src/ccgram/handlers/interactive/interactive_ui.py
  ok src/ccgram/llm/summarizer.py
1

== key claims spot-checked ==
30:def decide_tick(ctx: TickContext) -> TickDecision:
147:def convert_to_entities(text: str) -> tuple[str, list[TelegramEntity]]:
158:def check_gitleaks_rules(path: Path, cwd: Path) -> str | None:
821:def _is_nested_session(pane_tty: str) -> bool:
```
