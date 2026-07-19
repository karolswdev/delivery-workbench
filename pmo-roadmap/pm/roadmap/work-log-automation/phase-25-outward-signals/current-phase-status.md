# Phase 25 - The listening conductor — outward signals and bounded nudges

**Last updated:** 2026-07-19.

## Goal

Delivery Workbench hears the world outside the run — CI, reviews, merge
state, agent activity — records it as durable facts, and under an explicit
grant nudges the right agent back to work: observed, bounded, ledgered,
revocable. The third absorption phase: Agent Orchestrator's observation
loops and microsoft/agent-framework-go's typed human-in-the-loop
discipline, re-interpreted under the consent spine.

## Scope

- **In:** the `delivery-workbench-signal@1` outward-fact contract; an
  authority-free SCM observer (GitHub adapter + fixture provider, ETag
  guards, semantic diff, hash-chained signal facts, read-time derived
  status); driver activity states (`active | idle | waiting_input |
  blocked | exited | unknown`) with a receptivity table; a granted
  auto-nudge engine (score-declared rules, grant-held budgets and
  exact-match standing rules, at-most-once ledgered delivery); an SSE
  ledger/signal tail with cursor replay; durable operator notifications
  over the consented Telegram surface with typed checkpoint request
  ports; outstanding decisions surviving pause/resume with republish;
  a Claude Code non-interactive driver; a packaged fresh-wheel exam
  plus live specimen.
- **Out:** auto-merge or any forge mutation; injection into `blocked`
  or `unknown` sessions; automatic certification, commit, push,
  release, or deployment; cross-repository nudging; hosted or
  cross-machine observers; secrets or third-party content bodies in
  durable facts; fork-from-checkpoint execution (inspect-only);
  non-GitHub forge adapters.

## Exit criteria (evidence required)

- [x] One versioned signal contract separates the authority-free
  observer from the granted nudge engine, defines facts, derived-status
  precedence, activity vocabulary, nudge/receipt semantics, standing
  rules, typed checkpoint ports, and permanent exclusions, with a
  threat table naming exact fail checks (WLA-25-01).
- [x] The SCM observer records deduplicated, hash-chained,
  content-excluded signal facts and byte-equivalent derived status
  across CLI/MCP/HTTP while provably starting nothing (WLA-25-02).
- [x] Drivers report the contracted activity states honestly
  (fixture: all; codex exec: `active`/`exited`/`unknown`), and the pure
  receptivity table refuses injection into `blocked`/`unknown` under
  every intent (WLA-25-03).
- [x] Auto-nudges happen only under score rule + grant budget +
  standing-rule match, deliver at-most-once per signal across restart,
  respect receptivity, and exhaust into a recorded blocked stop —
  each refusal class distinct and receipted (WLA-25-04).
- [x] The SSE tail replays the ledger exactly from any cursor, carries
  no authority and no excluded content, and drives the live Run view
  without polling (WLA-25-05).
- [x] Notification facts persist append-only with unread/ack, deliver
  over per-person-consented Telegram carrying previews and typed-port
  correlation only — never tokens or apply commands — and fail safe
  when the channel is down (WLA-25-06).
- [ ] A least-privilege non-interactive Claude Code driver passes the
  full conformance suite with harness-owned auth and a recorded live
  specimen, CI green on fixtures alone (WLA-25-07).
- [ ] Outstanding checkpoint decisions survive crash/pause and resume
  with exactly-once typed republish, ledger-derivable pending sets,
  visible age/origin, and expiry-to-refusal semantics (WLA-25-08).
- [ ] A wheel-installed fresh consumer walks the whole outward loop —
  push, red CI, auto-nudge, repair, review signal, checkpoint through
  restart, phone-side typed decision, notifications — with every new
  red path refused exactly, at-most-once held under a planted crash,
  operator-only certification, and a separate live specimen
  (WLA-25-09).

## Story status

| ID | Story | Status | Story file | Evidence |
|---|---|---|---|---|
| WLA-25-01 | Contract the outward signal and nudge authority | done | [story-01-signal-nudge-contract](./story-01-signal-nudge-contract.md) | [evidence-story-01](./evidence-story-01.md) |
| WLA-25-02 | Observe SCM facts without acting | done | [story-02-scm-observer](./story-02-scm-observer.md) | [evidence-story-02](./evidence-story-02.md) |
| WLA-25-03 | Teach drivers to report activity states | done | [story-03-driver-activity-states](./story-03-driver-activity-states.md) | [evidence-story-03](./evidence-story-03.md) |
| WLA-25-04 | Nudge agents under grant authority | done | [story-04-bounded-nudge-engine](./story-04-bounded-nudge-engine.md) | [evidence-story-04](./evidence-story-04.md) |
| WLA-25-05 | Stream the ledger live | done | [story-05-ledger-live-stream](./story-05-ledger-live-stream.md) | [evidence-story-05](./evidence-story-05.md) |
| WLA-25-06 | Notify the operator durably | done | [story-06-operator-notifications](./story-06-operator-notifications.md) | [evidence-story-06](./evidence-story-06.md) |
| WLA-25-07 | Drive Claude Code through the neutral seam | backlog | [story-07-claude-code-driver](./story-07-claude-code-driver.md) | - |
| WLA-25-08 | Keep pending decisions alive across the pause | backlog | [story-08-typed-checkpoint-resume](./story-08-typed-checkpoint-resume.md) | - |
| WLA-25-09 | Prove the outward loop end to end | backlog | [story-09-packaged-outward-exam](./story-09-packaged-outward-exam.md) | - |

## Where we are

Phase open 6/9. WLA-25-01 is done: `docs/signals.md` contracts the whole
outward layer — the `delivery-workbench-signal@1` fact model, read-time
derived-status precedence, the six-state activity vocabulary with its
receptivity table, the four-layer nudge model (score rule → grant
authority → receptivity → ledger receipt), authority rings 0-5, typed
request ports with republish-on-resume, the no-authority live stream,
preview-only notifications, storage/privacy boundaries, a thirteen-row
threat table, and the Phase-25 proof standard — cross-linked from
`docs/orchestration.md` and pinned by structural assertions inside the
captured battery (2×297 core tests on both Python floors, docs
lint/snippets, canon lint, agent surface, roadmap check, rider parity,
update check, diff hygiene). Both deferred contract questions are
settled on record: nudge targets are declared route targets only, and
run-less branch signals notify per-project opt-in. The phase plan
stands at nine ordered stories from the two 2026-07-18 source studies
(AgentWrapper/agent-orchestrator; microsoft/agent-framework-go).

WLA-25-02 is done: `lib/dw_pmo/signals.py` delivers the authority-free
observer — provider port with fixture oracle and least-privilege GitHub
adapter, hash-chained facts under `.git/pmo-signals/` in the run-ledger
discipline, semantic dedup, content exclusion by construction, read-time
derived status, and content-free degraded-forge refusals — surfaced
byte-identically as `dw signals list`, MCP `dw_signals`, and Workbench
`GET /api/signals`, with the bounded `dw signals observe` pass staying a
CLI act stamped `starts_work: false`. Ten new tests raise the core suite
to 307; the live demo walked failing/green/conflicted/closed scenarios,
parity, fail-closed corruption, and refusal dedup on the installed CLI.

WLA-25-03 is done: driver receipts carry an exact-key `activity` field
from the contracted six-state vocabulary, adapters declare bounded
activity plans that the manager conformance-checks (invented states,
`exited`-while-running, non-lists, oversized plans, and missing keys all
refuse), terminal states map honestly (`lost` → `unknown`, otherwise
`exited`), the conductor ledgers `activity_observed` once per change
with replay-idempotent dedup, the projection/run view/Workbench surface
`last_activity` and per-session activity with no new authority, and
`signals.receptivity` is the pure exhaustive table — `blocked` and
`unknown` refuse under every intent including manual. FixtureDriver
scripts every state deterministically across restart; codex exec is
pinned to its honest subset by source assertion. Core suite 313 on both
floors; the live demo walked a granted run's deduped transition ledger
to `awaiting-certification`.

WLA-25-04 is done: the nudge engine is live as the contract's four
layers. Scores declare bounded `nudges` rules (compile-validated,
semantic-hash-covered, simulated); grants carry exact-match standing
rules, a `max_nudges` budget, and the bound signal channel — all stated
in the plan preview and dying with the grant; ticks match chain facts by
event hash and walk the seven-reason refusal taxonomy as deduped
`nudge_refused` events; a covered match appends one `nudge_delivered`
receipt that is the at-most-once marker across restart and the one
sanctioned wake of an `awaiting-certification` run. Idle targets
re-activate as fresh attempts whose packets carry an `@nudge` context
document; live `waiting_input` sessions receive hash-bound packets
through the new `deliver_nudge` driver seam; `active` defers and
`blocked`/`unknown` refuse. Budget exhaustion on an active run is a
recorded blocked stop. The run-act surface now permits `tick` on
`awaiting-certification` exactly when the score declares nudges — the
gap the demo's first capture caught. Suite 320 on both floors plus
interop and the packaged exam; the CLI demo walked
signal→standing-rule→wake→repair→re-terminal with at-most-once held.
Note for later Workbench editor work: nudge rules author through the
editor's JSON view and compiler save path today; a dedicated graphical
inspector panel is future editor scope.

WLA-25-05 is done: the hash-chained ledger is its own change log, and
liveness is now a tail over it. `tail_run_events`/`tail_signal_events`
return the verified suffix after a cursor (corrupt chains fail closed
before streaming); SSE endpoints on the existing localhost runtime
serve the canonical events with ledger-sequence ids and exact
`Last-Event-ID` resume; `dw run tail` prints the same lines; and the
Workbench Run view rides an EventSource that debounce-refreshes the
existing read model, with explicit refresh as the degradation path.
The stream carries no authority and no content bodies — proven by a
live subscriber demo that watched a real run execute, resumed
mid-ledger, and matched the ledger byte for byte (a planted secret
prompt never crossed). Suite 323 on both floors; 32 UI renders green.

WLA-25-06 is done: notifications are pure derivations over the ledgers
and signal chains (checkpoint-pending with typed request ports,
awaiting-certification, run-blocked, nudge-budget-exhausted, and the
opt-in branch-signal kind), with only two append-only local stores
(acks, delivery attempts with a 3-try ceiling). One model serves
`dw notifications`, MCP read + guarded ack, HTTP read + the eighth
deliberate POST route, and a live Run view card. The Telegram side
gains the owner-gated `/decision <correlation> approve|reject` typed
response (stale refuses; authority stays at the local exact-token
checkpoint boundary) and the bounded `run.py notify` push pass to the
paired chat, send-only and fail-safe. The herdr-remote counterexample
held: no token or apply command ever leaves the machine. Suites: core
325, Telegram 152, both floors green. OWED: the live phone leg
screenshots, recorded in evidence-story-06. Next: WLA-25-07, the
Claude Code driver.

## Active risks

| Risk | Likelihood | Mitigation | Stop signal |
|---|---|---|---|
| The observer quietly becomes an actor | high | Observer is pure read with `starts_work: false` stamped and tested; all action lives behind grants | Any observe path mutates forge, tree, run, or agent |
| Auto-nudge becomes an unbounded feedback loop | high | Per-rule/per-run ceilings, at-most-once per signal, exhaustion → recorded blocked stop | A nudge fires twice for one signal or after budget exhaustion |
| Nudges leak authority or content into agent sessions | high | Structured packets only: facts and references; no commands, shell, secrets, or third-party bodies | A packet carries argv, a token, or copied CI/review text |
| Injection into a permission decision | high | Receptivity table refuses `blocked`/`unknown` under every intent, including manual | Any input reaches a session reporting `blocked` |
| The live stream becomes a consent channel | medium | SSE is read-only by construction; no tokens server→client; router tested | Any mutation or token reachable from the stream surface |
| Phone notifications turn into remote control | high | Messages carry previews and typed-port responses; approval still crosses the exact-token boundary locally | An outbound message contains an apply command or consent token |
| Adapter roster growth outpaces honesty | medium | Conformance suite + version-pinned capability discovery + `unknown` over guessing | An adapter reports a state or capability it cannot substantiate |
| Signal facts drift from forge truth | medium | Semantic diff on every sweep; degraded forge access is a recorded refusal, never stale-silent success | Derived status disagrees with the forge for an observed fact |

## Decisions made (this phase)

- 2026-07-18 - Phase scaffolded with `dw phase create` - keeps roadmap structure consistent - CLI.
- 2026-07-18 - Auto-nudging is supported under grant authority - owner correction of the initial "signals in, consent before action" recommendation; the consent moves into the standing rule the operator approves, not into each delivery - owner direction.
- 2026-07-18 - Absorb, do not adopt: AO's observation shapes and MAF-go's typed HITL discipline are re-implemented on the ledger/grant spine rather than imported as daemon authority - the third absorption after HoldSpeak and ccgram - architecture boundary.
- 2026-07-18 - `blocked` and `unknown` sessions never receive injected input, even manually - a session stopped on a permission decision is awaiting a ring-4 approval, and honesty requires refusing what cannot be observed - WLA-25-03.
- 2026-07-18 - Undelivered nudges are refused and re-derived from signal facts, never queued - the ledger stays the only truth; MAF-go's in-flight message persistence is deliberately not copied - WLA-25-08.
- 2026-07-18 - Nudge targets are declared route targets only - a nudge changes when a declared node runs, never whether an undeclared node exists, so `orchestration simulate` can still show every way a run can unfold; an unwired fixer is a score edit plus re-grant - WLA-25-01 (docs/signals.md).
- 2026-07-18 - Red CI / review signals on branches with no associated run notify per-project opt-in - observation everywhere by default would make the quiet channel noisy before it earns trust - WLA-25-01 (docs/signals.md).
- 2026-07-18 - The observe pass is a CLI act; MCP and HTTP expose reads only - a remote client can see every fact and derived status but cannot make the machine poll a forge, keeping the observer's write path (its own store) local-operator-initiated - WLA-25-02.
- 2026-07-19 - `nudge_delivered` is the only event that reverses a terminal state (`awaiting-certification` → `active`) - the wake is granted, budgeted, at-most-once, and receipted, and certification/commit authority is untouched - WLA-25-04.
- 2026-07-19 - Naming a failure-activated node in a nudge rule makes it reachable exactly like a failure route - explicit nudge routing is declared routing, so `orchestration simulate` still shows every way a run can unfold - WLA-25-04.
- 2026-07-19 - The undelivered nudge is never queued: the ledger event is the delivery marker (at-most-once), and a crash between seam call and injection under-delivers rather than double-delivers - WLA-25-04.
- 2026-07-19 - Phone decisions are documents, not buttons: `/decision` carries a correlation id and a closed vocabulary, and the approve/reject still crosses the local exact-token boundary - the herdr-remote study's transport-equals-authority model is the recorded counterexample - WLA-25-06.
- 2026-07-19 - Branch signals notify behind the operator-local `branch_signals` opt-in, and never for a channel a grant already owns - the run-bound channel already nudges; notifying it twice would be noise - WLA-25-06.

## Decisions deferred

- Signal-history export into evidence files - trigger after the
  WLA-25-09 exam findings - default is no export.
- Non-GitHub forge adapters and interactive (PTY) agent harnesses -
  trigger on demand after the seam holds - default is out.
- Declarative screen-state manifests for interactive drivers (herdr
  study, 2026-07-19): data-file rules classifying `waiting_input`/
  `blocked` from terminal state, with which-rule/what-evidence audit
  payloads in the ledger and strict unknown-degrades-to-idle
  conservatism - trigger with the first interactive driver - default is
  the honest `unknown` from WLA-25-03.
- An extension seam (herdr study, 2026-07-19): declare the dw CLI/MCP
  surface as the plugin API with injected run/story env context, publish
  a JSON Schema for the stamped models, adopt a `dw-plugin` topic
  convention, and gate plugin capabilities behind the grant system -
  candidate phase 26 - default is no new seam this phase.
