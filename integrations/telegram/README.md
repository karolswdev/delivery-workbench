# The Telegram interface

Mission control in a pocket (WLA-13-06, implementing
[docs/mission-control.md](../../docs/mission-control.md) §4). The
interface consumes exactly what the Desk consumes — the state feed,
the correlation document, and the event log, via the dw CLI — and
speaks at the Delivery Workbench level of abstraction: phases,
stories, gates, refusals. It never parses terminal content; the one
verbatim surface is the explicitly requested read-only
`capture-pane` preview.

## Configuration (operator-authored, never in this repo)

The bot identity and token are operator configuration at
`~/.config/delivery-workbench/telegram.json` (chmod 600), or the
token alone via the `TELEGRAM_BOT_TOKEN` environment variable,
which takes precedence. No token — bot, pairing, or otherwise — and
no chat ID ever appears in this repository; CI greps it clean.

```json
{
  "bot_token": "(operator-supplied)",
  "workspace_roots": ["~/dev"],
  "default_repo": "~/dev/some-rails-repo",
  "state_path": "~/.config/delivery-workbench/telegram-state.json",
  "registry_path": null,
  "dw_cli": null
}
```

- `workspace_roots` — the lifecycle allow-list: `/open`, `/install`,
  and `/newproject` refuse any path outside these roots.
- `state_path` — runtime state (pairing binding, armed sessions,
  active repo), written chmod 600; defaults beside the config.
- `registry_path` — override for the HoldSpeak agent-session
  registry (the default is the desk's own).
- `dw_cli` — explicit dw argv prefix; by default the target repo's
  vendored `.githooks/dw` runs first, the installed `dw` second.

## Run it

```
python3 integrations/telegram/run.py pair    # one-time pairing token, this terminal only
python3 integrations/telegram/run.py serve   # long-poll the Bot API
```

## Owner binding is by pairing, never hardcoded identity

`run.py pair` prints a single-use token (5-minute TTL) on the
operator's machine and stores only its hash. Send `/pair <token>`
in chat; the binding lands in runtime state. Wrong, expired, and
reused tokens are refused; re-pairing revokes the previous binding;
an unpaired chat gets silence beyond the pairing prompt.

## Topics are projects, and conversation flows

Add the bot to a Telegram group with topics enabled and one
forum topic becomes one rails repo: `/bind` (no argument lists the
allow-listed repos to pick from; `/bind <path>` ties this topic to
that repo). Commands in a bound topic need no repo argument —
`/state`, `/flip`, `/events` all act on the topic's repo — and a
question from an agent working that repo routes home to its topic.
The flat single-chat mode is unchanged: with no topics, `/open`
still sets one active repo.

Inside a bound topic, `/steer <session-key>` binds a live agent
session — **that binding is the arming** (the owner decision of
2026-07-04: consent gates entry, not every utterance). After it,
you just type: your words relay straight to the agent's pane, no
tap per message, agent questions land back in the topic. The
binding refreshes on activity and expires when idle; `/unsteer`
stops it, and pane-ownership verification still runs beneath every
keystroke. Rails verbs (`/flip`, `/newstory`), project lifecycle,
and session launches keep their approval tap — the boundaries the
gate cares about. Design: docs/absorption-ccgram.md §0+§3.

## The three consent rings (contract §4)

1. **Read** — `/state`, `/events`, `/sessions`, `/questions`,
   `/peek` (verbatim, read-only), owner-only.
2. **Rails verbs** — `/flip` and `/newstory` are proposals with
   explicit previews; execution happens only on the approval tap,
   through the two allow-listed `dw story` argv shapes (the
   Phase 12 actuator seam), and the dw gate keeps final say — an
   approved done-flip without evidence is refused and the banner is
   relayed into chat verbatim. Project lifecycle (`/open`,
   `/install`, `/newproject`) is additionally path-allow-listed;
   "create" means scaffolded repo → rails installed → doctor green
   → first gated commit, or the failure is reported at the exact
   step it happened.
3. **The tmux driver** — the sharpest edge. Anything that types
   into a terminal requires the target tmux session to be
   **armed** (default TTL 15 minutes, capped at 60), visible via
   `/armed`, revoked by `/disarm`, auto-expiring at the moment of
   use. For `/reply`, the approval tap doubles as the arming grant
   when the session isn't armed yet — the proposal preview says so
   explicitly, so answering an agent is one tap, not a ceremony.
   `/arm <session> [minutes]` still exists for pre-arming. Text
   that never passed through a grant is refused in the driver,
   beneath the chat layer, test-proven.
   `/launch <claude|codex|pi> <path>` starts a named tmux session
   for any supported harness; it starts unarmed like everything
   else.

The bootstrap exception, named honestly: approving `/newproject`
certifies the *bootstrap contract* of the freshly scaffolded repo —
a commit with no stories, no evidence, and no history, where the
preview says exactly that and the dw gate re-verifies every stamped
fact downstream. Story-work certification is never delegated to the
interface; the two allow-listed story verbs cannot commit at all.

## Instant push: the dw hook seam

`dw hook install` (claude and codex) wires the agent CLIs to
append whitelisted events — SessionStart, Notification, Stop,
SessionEnd; never message or transcript content — to
`~/.config/delivery-workbench/agent-events.jsonl`. The serve loop
drains that stream every second by persisted byte offset, so a
blocked agent reaches your phone in about a second instead of a
poll cycle; the 15-second sessions poll remains as reconciliation.
`dw hook status` shows the wiring; `dw hook uninstall` removes
exactly our entries and nothing else; `DW_HOOK_QUIET=1` in a
process's environment silences its hooks (the nested-session
guard). Config override: `agent_events_path`; hook-side override:
`DW_AGENT_EVENTS`. Design: docs/absorption-ccgram.md §1.

## Testing

`pmo-roadmap/tests/telegram-interface-tests.py` proves the whole
surface against a scripted transport and fixture rails repos — the
rails legs (state, events, the crown-case refusal, the real
project-create) run the real dw CLI; Telegram and tmux are the only
fakes, each behind a declared seam. No live network in CI. The live
phone leg (screenshots under the story's evidence `assets/`) is the
one manual item.
