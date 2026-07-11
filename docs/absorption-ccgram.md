# The absorption map: ccgram, transmuted (WLA-14-01)

**Scope:** the design contract for Phase 14. The study subject is
[alexei-led/ccgram](https://github.com/alexei-led/ccgram)
v4.3.5 (commit `4e4fc31`), MIT-licensed, itself carrying the
lineage of six-ddc's original — read in full on 2026-07-04. Ideas
are re-interpreted here, not copied; wherever code (not just an
idea) is ported in a later story, it carries the MIT notice and
this attribution. Claim marks as in
[mission-control.md](./mission-control.md): **verified**
(confirmed in the studied clone, path cited), **decided** (a
choice this document makes and owns). Stories WLA-14-02..07
implement against this document; when reality disagrees, the
story amends this document in the same commit.

ccgram's thesis, which we keep whole: sit on the terminal
multiplexer, never wrap an agent SDK — the desk session stays the
source of truth, and the phone is a window onto it, not a
replacement for it. That is already our thesis; the two systems
disagree only about consent, and that disagreement is the whole
reason this map exists.

## §0. The interaction stance (owner decision, 2026-07-04)

**Consent gates ENTRY, not every utterance.** The Phase 13
interface demanded a proposal tap per relayed reply; the live day
proved the boundary right and the ceremony wrong. The standing
model, binding on every story in this phase:

- **Pairing** admits the owner. Unchanged (§4 ring 1 of the
  mission-control contract).
- **Binding a session into a topic IS the arming** — one
  explicit, visible act, announced in the topic, revocable in one
  tap, expiring on real idleness (activity-refreshed TTL, not a
  stopwatch). While a binding is live, conversation FLOWS: typed
  text relays to the pane, replies land back, the toolbar fires —
  zero intermediate taps.
- **Taps remain at boundaries the gate cares about:** story
  verbs, project lifecycle, session launch and recovery. Rare
  taps that mean something, instead of constant taps that mean
  nothing.
- **The floor never moves:** pane-ownership verification per
  keystroke (the recycled-pane-id lesson), and the dw gate's
  final say over the rails.

This amends mission-control.md §4 ring 3 (amendment recorded
there in this same commit) and retires 13-06's per-reply
proposal.

## The ledger: absorb / transmute / refuse

| # | ccgram idea (verified at) | Verdict | Why / how |
|---|---|---|---|
| 1 | Entity-based formatting — markdown → plain text + offset entities, two-phase fallback (`src/ccgram/entity_formatting.py:147`, `message_sender.py`) | **absorb** | Eliminates the escape-error class entirely; consent-neutral craft. → 14-03 |
| 2 | Hook-driven push: agent hooks append `events.jsonl`, byte-offset reader, truncation-tolerant (`src/ccgram/hook.py`, `event_reader.py:22`) | **absorb** | Instant beats polling; crash-safe by construction. dw grows its own hook seam. → 14-02 |
| 3 | Per-chat FIFO queue: merge, coalesce-to-latest status, flood-control, worker respawn (`src/ccgram/handlers/messaging_pipeline/message_queue.py`) | **absorb** | Ordered, un-spammy delivery under burst; consent-neutral. → 14-03 |
| 4 | `/send` security pipeline: containment, hidden, secret globs, size, gitleaks rules, `git check-ignore`, state-file protection (`src/ccgram/handlers/send/send_security.py:26-163`) | **absorb + extend** | A consent instrument with no happy-path tax; we add our own state files as lock 7. → 14-06 |
| 5 | Pure decision kernel — I/O into a context, transitions as pure functions (`src/ccgram/handlers/polling/window_tick/decide.py:30`) | **absorb** | Our pairing/binding/proposal machines earn mock-free tests. → 14-03 |
| 6 | Cleanup-callback registry — modules self-register teardown by scope (`src/ccgram/topic_state_registry.py:24`) | **absorb** | Kills the forgotten-state-dict bug class as topics arrive. → 14-04 |
| 7 | Capability-flag providers — behavior as data, zero `if provider ==` (`src/ccgram/providers/base.py:103`) | **absorb** | Our HARNESS table grows flags; adding a harness becomes data. → 14-05 |
| 8 | TUI send craft — literal, settle delay, Enter as its own keystroke; per-harness quirks (`src/ccgram/multiplexer/tmux.py:557`) | **absorb** | Submit reliability is interaction quality once conversation flows. → 14-05 |
| 9 | Topic-per-window forum model, bidirectional thread router (`src/ccgram/thread_router.py:136`) | **transmute** | Their unit is a tmux window; ours is the rails repo. One topic = one project; sessions ride inside; topic emoji = rails state. → 14-04 |
| 10 | Directory browser for new sessions (`handlers/text/text_handler.py:257`) | **transmute** | Becomes the path-allow-listed project picker inside the ring-2 lifecycle envelope (`/newproject` proposals included). → 14-04 |
| 11 | Live view — screenshot auto-refresh, `editMessageMedia`, content-hash gating (`handlers/live/live_view.py`) | **transmute** | Absorbed as edit-in-place `/live` with hash gating; stays read-only ring 1 (text first, image later if wanted). → 14-05 |
| 12 | Action toolbar — per-provider inline grid, live-state-seeded toggles (`handlers/toolbar/toolbar_keyboard.py:106`) | **transmute** | Exists only inside a live binding; dies with it; every press through pane-ownership. → 14-05 |
| 13 | Session recovery — resume/continue/fresh on dead windows (`session_lifecycle.py:54`) | **transmute** | Capability-aware one-tap offers (launch is a boundary act). → 14-05 |
| 14 | Interactive-UI nav keyboard (arrows/Space/Tab/Esc) (`handlers/interactive/interactive_ui.py:152`) | **transmute** | Folded into the toolbar story, same binding envelope. → 14-05 |
| 15 | User-ID allowlist + group lock as auth (`config.py:62`) | **refuse** | Pairing stands: no identity we author, revocable by re-pair, hashed at rest. Their model is configuration-as-identity; ours survived a live day. |
| 16 | NL → LLM shell-command suggestion with approval keyboard (`handlers/shell/shell_commands.py:352`) | **refuse** | We relay to agents; we do not synthesize shell. The agent is the place where language becomes commands — behind its own harness and our gate. |
| 17 | LLM completion summaries + TTS voice replies (`llm/summarizer.py`, queue TTS) | **refuse for now** | Content flowing to the paired owner's own chat is permissible in principle (see §0 note below), but summaries add an LLM dependency to the interface for cosmetic gain. Park; revisit on demand. |
| 18 | Web dashboard mini-app (xterm.js) | **refuse** | The Desk conveyor is our dashboard (HoldSpeak Phase 82); one desk is enough. |
| 19 | Vim-mode detection, herdr multiplexer support | **defer** | Note the seams; no present need. tmux stays the one multiplexer. |
| 20 | Architecture fitness tests as CI gates (`tests/.../test_query_layer_only_for_handlers.py`, `make arch-guard`) | **absorb** | Guardrails as tests — the workbench's own religion applied to its own bot. → 14-07 |

**The content decision (§3-adjacent, decided):** rails events
remain content-free — the §3 consent stance is untouched. But the
*conversational stream* (what the owner's own agent says in a
topic the owner bound) is the owner's own content flowing to the
owner's own paired chat: relaying it verbatim is permitted and is
the entire point of flowing conversation. The two streams stay
separate pipes and are never mixed: events narrate the rails,
topics carry the conversation.

## §1. The hook seam (implemented by WLA-14-02)

`dw hook --install/--uninstall/--status` for claude and codex:
idempotent settings edits, a nested-session guard (verified in
the study: `hook.py:821` walks the process tree so spawned
observers don't double-fire — absorb that discipline), hook
processes that never read interface config. Events append to
`~/.config/delivery-workbench/agent-events.jsonl` (flock-locked;
SessionStart / Notification / Stop / SessionEnd at minimum;
rails-adjacent metadata only). The interface drains it by
persisted byte offset (truncation resets honestly; malformed
lines skipped — the `event_reader.py:22` shape) and pushes
instantly; the 15-second poll becomes fallback and
reconciliation. When HoldSpeak's registry is present, correlation
still comes from `dw sessions` — the hook stream is the wake-up,
never a second source of truth.

## §2. The message layer (implemented by WLA-14-03)

Entity offsets instead of escaping; two-phase entity→plain
fallback; splitting only at the send layer; a per-chat FIFO queue
with adjacent-text merge, stale-status coalescing, flood-control
pauses, worker respawn; edit-in-place for every evolving message
(proposal cards, belt status, live view). The pairing, binding,
and proposal state machines are rewritten as pure decision
kernels over explicit contexts — tested without mocks.

## §3. Topics are projects (implemented by WLA-14-04)

Forum-group support beside flat chat; one topic per rails repo,
bound by tap from the allow-listed roots; the bidirectional
`(chat, thread) ↔ repo` router with stale-binding eviction and
name/emoji sync; commands scope to their topic's repo;
cross-topic pushes route home. Inside a topic, binding a session
per §0 opens flowing conversation. The cleanup registry (ledger
#6) manages per-topic state teardown.

## §4. The driver's manners (implemented by WLA-14-05)

Literal / settle / Enter as the driver's shape; the HARNESS table
grows capability flags (submit style, resume support, recovery
verbs) so behavior is data; `/live` auto-refresh by edit-in-place
with content-hash gating, read-only; the toolbar inside live
bindings; capability-aware recovery offers.

## §5. Seven locks on `/send` (implemented by WLA-14-06)

Path containment → hidden-file block → secret patterns → size cap
→ `git check-ignore` → gitleaks-style rules where cheap → the
workbench's own state files unsendable by name (operator config,
runtime state, contract scratch, events). Refusals name the lock.
Clean files send directly — no ceremony on the happy path.

## §6. The exit exam and the fitness discipline (WLA-14-07)

The live day (topics, ~1 s push, a real typed conversation, the
toolbar, `/send` both ways, a flip and the crown case from a
topic), screenshots landing in evidence the same day — plus
layering fitness tests for `integrations/telegram/` wired into
CI: the transport never imports rails, handlers read through the
query surface, and no import path bypasses the pane-ownership
check.

## The second absorption — upstream v4.3.11 (phase 20)

The owner's direction (2026-07-11): robust groups, screenshots
over the wire, button-based interfaces — "ccgram is MIT, feel free
to use those assets." Upstream had moved v4.3.5 → v4.3.11; a fresh
clone was read at the source level. Same discipline as the first
absorption: transmute onto the urllib transport and stdlib, never
vendor the stack (PTB, structlog, asyncio all stayed behind), and
every feature rides the consent spine that already existed.

| # | ccgram idea (v4.3.11 source) | Verdict | What we did (story) |
|---|---|---|---|
| 21 | `screenshot.py` — pane text → PNG, ANSI SGR, three-tier font chain | **absorb/transmute** | `dw_telegram/screenshot.py`, import-pure leaf: SGR machine and 256-color math carry over; async/structlog dropped; ONE font (JetBrains Mono, OFL) — CJK/Symbola deferred as repo heft; Pillow optional with honest text fallback; upstream's charset-designator half-strip fixed (WLA-20-01) |
| 22 | live view — auto-refresh screenshots via `editMessageMedia`, hash-gated, auto-stop | **absorb** (closes row 11's "image later if wanted") | `/live` image mode behind the SAME text-content hash gate — no change, no render, no API call; `/live text` keeps the text view (WLA-20-02) |
| 23 | user-ID allowlist (row 15, refused at 4.3.5) | **transmute** — still no allowlist | `/pair`'s redeemer becomes the owner-of-record; consent commands, every tap, and the relay answer to that one identity in group chats; legacy states keep chat granularity, `/status` says so (WLA-20-03) |
| 24 | `toolbar_config.py` — per-provider grids from TOML, key/text/builtin | **absorb/transmute** | `dw_telegram/toolbarcfg.py` leaf: JSON in `telegram.json` (3.9 floor, no tomllib), per-HARNESS grids, builtin table CLOSED (screen/live/dismiss — a config can never mint capability), tb: taps resolve at tap time (WLA-20-04) |
| 25 | `setMyCommands` slash menu | **absorb** | read-and-entry verbs only; config opt-out; registered at serve start, never blocking (WLA-20-04) |
| 26 | interactive UI — arrows/enter/esc buttons on TUI prompts | **absorb/transmute** | nav keyboard on pushed question cards, bound + armed ONLY, a nav tap never arms; deliberately dumb (📸 shows the truth, no menu parsing) (WLA-20-05) |
| 27 | screenshot control keys under the photo (`kb:` under `ss:`) | **transmute down** | one 🔄 refresh button editing the same message; steering keys stay on the toolbar where the binding is visible |
| 28 | directory browser (`db:` menus) | **defer again** | `/bind`'s numbered list stands until it outgrows a screenful |
| 29 | sessions dashboard (kill/new buttons) | **defer** | `/sessions` text stands until real multi-session pain |
| 30 | voice/Whisper, TTS, web dashboard, herdr | **refusals stand** | rows 16–19 unchanged |

The exit exam grew with the surface (WLA-20-06): `screenshot` and
`toolbarcfg` joined the LEAVES census; the quoted Bot API strings
(`"sendPhoto"`, `"editMessageMedia"`, `"setMyCommands"`, and the
five originals) are pinned to `transport.py` alone; the planted
self-test now also bites inside a NEW leaf; the send-keys census is
unchanged — the driver is still the only door into a terminal.

## The journal

**Decided:** the journal continues into Phase 14 under the same
charter — same voice, same cadence, same honesty bar. Entry 16
opens the phase.
