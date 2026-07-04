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
3. **The tmux driver** — the sharpest edge. `/reply` (Q&A relay
   back into an agent session) and anything else that types into a
   terminal requires the target tmux session to be **armed**:
   `/arm <session> [minutes]` (default 15, capped at 60), visible
   via `/armed`, revoked by `/disarm`, auto-expiring at the moment
   of use. An unarmed session cannot be steered — the refusal is
   engineered in the driver, beneath the chat layer, and
   test-proven. `/launch <claude|codex|pi> <path>` starts a named
   tmux session for any supported harness; it starts unarmed like
   everything else.

The bootstrap exception, named honestly: approving `/newproject`
certifies the *bootstrap contract* of the freshly scaffolded repo —
a commit with no stories, no evidence, and no history, where the
preview says exactly that and the dw gate re-verifies every stamped
fact downstream. Story-work certification is never delegated to the
interface; the two allow-listed story verbs cannot commit at all.

## Testing

`pmo-roadmap/tests/telegram-interface-tests.py` proves the whole
surface against a scripted transport and fixture rails repos — the
rails legs (state, events, the crown-case refusal, the real
project-create) run the real dw CLI; Telegram and tmux are the only
fakes, each behind a declared seam. No live network in CI. The live
phone leg (screenshots under the story's evidence `assets/`) is the
one manual item.
