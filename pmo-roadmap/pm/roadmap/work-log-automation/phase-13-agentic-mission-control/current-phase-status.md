# Phase 13 - Mission control: the Desk conveyor and the live roadmap

**Last updated:** 2026-07-03.

## Goal

Make the roadmap visible and steerable from outside the terminal:
a stable machine-readable state feed, live agent-session-to-story
correlation ("Claude is on WLA-12-03, blocked, asking a question"),
and an event stream worth showing (gate verdicts, refusals,
captures, flips) — the Delivery Workbench half of a joint
mission-control experience. The HoldSpeak half — the Desk conveyor
primitive that renders phases as a moving line with stories as
items passing through stations, web and iOS, the DELIGHT-feeling
half — ships as a counterpart phase in the HoldSpeak repo and
consumes only what this phase exposes.

## Scope

- **In:** The mission-control design contract (feed schema,
  correlation model, event taxonomy, and the exact seam the
  HoldSpeak counterpart phase builds against); a versioned
  `dw state --json` roadmap feed; session-to-story correlation
  built on HoldSpeak's existing agent-session registry; an
  append-only event log of rail happenings; an end-to-end proof
  with a real Desk driving a real approval through the Phase 12
  actuator — including the gate refusing one; and a Telegram
  mission-control client (`KarolDeliveryWorkbenchBot`) consuming
  the same substrate — state, agent Q&A relay, approval-gated
  steering, read-only tmux previews (WLA-13-06).
- **Out:** HoldSpeak UI code, the conveyor's visual/gamified
  design, and any Desk object type (all counterpart-phase work in
  the HoldSpeak repo); actuator verbs beyond Phase 12's two;
  machine certification of contracts (canon: never); credentials
  in the repo (bot tokens live in untracked `~/.config` files or
  env vars — the repo is public and history is forever); the parked
  candidates (multi-project dashboard, announcement post, HTTP/SSE
  MCP transport) stay parked.

## Exit criteria (evidence required)

- [ ] The mission-control contract exists; the feed schema, the
  correlation model, and the event taxonomy are pinned, and the
  HoldSpeak counterpart phase is specced against them (WLA-13-01).
- [ ] `dw state --json` emits the versioned feed, schema-pinned by
  tests, consumed by at least one real external reader
  (WLA-13-02).
- [ ] A live agent session in a rails repo resolves to its
  in-progress story with its blocked/awaiting state, proven
  against HoldSpeak's real session registry (WLA-13-03).
- [ ] Gate verdicts, refusals, captures, and flips appear in the
  event log as they happen, with the consent stance recorded
  (WLA-13-04).
- [ ] A real Desk renders real phase state, an approval from it
  flips a story through the Phase 12 actuator, and a gate refusal
  surfaces as a first-class event — all evidence-captured
  (WLA-13-05).
- [ ] The Telegram bot reports state and events, relays an agent
  question and its answer, executes an approved flip, relays a
  gate refusal into chat, and refuses to steer an unarmed session
  — all evidence-captured (WLA-13-06).

## Story status

| ID | Story | Status | Story file | Evidence |
|---|---|---|---|---|
| WLA-13-01 | Design the mission-control contract | backlog | [story-01-design-the-mission-control-contract](./story-01-design-the-mission-control-contract.md) | - |
| WLA-13-02 | Ship the roadmap state feed | backlog | [story-02-ship-the-roadmap-state-feed](./story-02-ship-the-roadmap-state-feed.md) | - |
| WLA-13-03 | Correlate live agent sessions to stories | backlog | [story-03-correlate-live-agent-sessions-to-stories](./story-03-correlate-live-agent-sessions-to-stories.md) | - |
| WLA-13-04 | Emit the events worth showing | backlog | [story-04-emit-the-events-worth-showing](./story-04-emit-the-events-worth-showing.md) | - |
| WLA-13-05 | Prove mission control end-to-end with the Desk | backlog | [story-05-prove-mission-control-end-to-end-with-the-desk](./story-05-prove-mission-control-end-to-end-with-the-desk.md) | - |
| WLA-13-06 | Prove mission control from Telegram | backlog | [story-06-telegram-mission-control](./story-06-telegram-mission-control.md) | - |

## Where we are

Scaffolded 2026-07-03, mid-Phase-12, by the owner's call: the
conveyor vision arrived during WLA-12-01 and was deliberately
parked here instead of widening the largest phase this repo has
run. Not actionable until Phase 12 lands the substrate this phase
rides on: the HoldSpeak pack (12-02), the actuator (12-03), and
`.hs/` Desk presence (12-07). WLA-13-01 sharpens every later
story before any of them starts — the specs below Story 01 are
scaffold-grade on purpose and say so.

## Active risks

| Risk | Likelihood | Mitigation | Stop signal |
|---|---|---|---|
| Phase 12 substrate shifts under these specs | medium | Stories 02-05 stay scaffold-grade until 13-01 re-pins them post-Phase-12 | A Phase 12 story lands something 13-01 assumed differently |
| Two repos, one experience: contract drift between DW feed and Desk consumer | medium | 13-01 pins the schema; counterpart phase declares the feed version it consumes | Desk renders wrong/stale state from a valid feed |
| Session registry is HoldSpeak-owned and 0.x | medium | Correlator treats it read-only; version pinned like the pack | Registry shape change breaks correlation |
| Event log becomes surveillance instead of visibility | low | 13-04 records the consent stance; events describe rails, not people | Any event exposing content the operator didn't opt into |

## Decisions made (this phase)

- 2026-07-03 - Phase scaffolded with `dw phase create` - keeps roadmap structure consistent - CLI.
- 2026-07-03 - Scaffolded mid-Phase-12 rather than widening Phase 12; Phase 12 scope untouched - Karol.
- 2026-07-03 - Split ownership: DW exposes state/events/verbs, HoldSpeak owns the conveyor UI (web + iOS) as a counterpart phase in its own repo - Karol + agent.
- 2026-07-03 - Steering stays within Phase 12's actuator envelope: two verbs, propose-approve-execute, gate always final, certification human, always - canon.
- 2026-07-04 - Telegram joins the phase as a second mission-control client (WLA-13-06), same substrate as the Desk; bot identity `KarolDeliveryWorkbenchBot` - Karol.
- 2026-07-04 - Bot credentials never enter the repo, bogus or real: token provisioned at `~/.config/delivery-workbench/telegram.json` (untracked, chmod 600), env override; CI greps the repo clean - Karol + agent.
- 2026-07-04 - tmux `send-keys` steering is the program's sharpest edge: per-session visible expiring arming, proposal-preview-approval per act, default off; WLA-13-01 designs the envelope before any implementation - Karol + agent.

## Decisions deferred

- Feed transport (file, `dw state` invocation, or served endpoint) - decide in WLA-13-01 - default is the cheapest thing the Desk can poll.
- Whether the journal continues into Phase 13 or Phase 12's stands alone - decide in WLA-13-01 - default is continue; the worked example gets richer.
- Version target (v2.0.0 vs v1.10.0) - decide at phase close by what the feed's stability promise turned out to be.
- Event log persistence (append-only file vs sqlite) - decide in WLA-13-04 with real volume data.
