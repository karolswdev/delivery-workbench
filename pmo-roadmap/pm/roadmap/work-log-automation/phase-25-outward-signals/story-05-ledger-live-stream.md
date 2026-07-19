# WLA-25-05 - Stream the ledger live

- **Project:** work-log-automation
- **Phase:** 25
- **Status:** backlog
- **Depends on:** WLA-25-01
- **Unblocks:** WLA-25-06, WLA-25-09
- **Owner:** unassigned

## Problem

The Workbench Run view explains a run precisely but statically: seeing
progress means explicit refresh, and any external consumer that wants
liveness must poll `run view` in a loop — the exact pattern the rails
discourage. Agent Orchestrator's answer is a change-data-capture
pipeline: every durable write lands in a change log that a poller tails
and fans out to subscribers over SSE with replay. Delivery Workbench is
already better positioned than AO here — the hash-chained ledger *is* a
change log with integrity guarantees — so liveness is a tail surface
over authority that already exists, not new machinery.

## Scope

- **In:** an SSE endpoint on the existing localhost Workbench/HTTP
  runtime that tails a run's ledger (and, once WLA-25-02 lands, a
  branch's signal chain) from a client-supplied sequence cursor —
  `Last-Event-ID` semantics map to ledger sequence, so reconnects replay
  exactly the missed suffix; events carry the same bounded models the
  read surfaces already return (ids, hashes, states, budgets — never
  prompts, transcripts, or third-party content), following the
  privacy-defaulted telemetry posture absorbed from
  microsoft/agent-framework-go: structure always, content only behind
  the existing explicit bounded-stream opens; the Workbench Run view
  subscribes and updates the graph, attempts, budgets, checkpoints, and
  nudge lineage live, with the explicit-refresh path retained as
  fallback; `dw run stream --follow` gains the same tail over stdout
  for terminal use.
- **Out:** any write or act over the stream (it is read-only by
  construction — no token ever travels server→client that could be
  replayed as consent); cross-machine transport or hosted relays;
  WebSocket terminal attachment; event payloads exceeding the read-model
  privacy boundary.

## Acceptance criteria

- [ ] A subscriber connecting with a cursor receives every ledger event
  after it exactly once, in order; disconnect/reconnect at an arbitrary
  point replays the missed suffix with no gap and no duplicate, proven
  against a fixture run with a scripted mid-run disconnect.
- [ ] Stream events are byte-derivable from the ledger alone: a test
  replays a completed run's ledger and reproduces the exact event
  sequence a live subscriber saw.
- [ ] No stream payload contains prompt text, transcript content,
  artifact bodies, or third-party content; the content-exclusion test
  suite runs against recorded streams.
- [ ] The stream carries no authority: no token, no apply URL, no
  mutation route is reachable from the SSE surface, enforced by test on
  the HTTP router.
- [ ] The Workbench Run view renders live updates for dispatch, check,
  failure-route, nudge, checkpoint, and terminal events without
  polling, and degrades to explicit refresh when the stream is closed.
- [ ] The localhost-only runtime boundary and existing auth posture are
  unchanged, re-verified by the runtime boundary tests.

## Test plan

- **Unit:** cursor replay, event derivation from ledger, payload
  privacy assertions.
- **Integration:** fixture run streamed end to end with disconnects;
  CLI `--follow` parity with the SSE sequence.
- **Manual / device:** watch a live fixture run in the Workbench with
  the network panel open — one SSE connection, no polling requests,
  graph moving as ticks land.

## Notes / open questions

AO tails a SQLite trigger table because its facts live in mutable rows;
our ledger already serializes writes, so the only new component is the
tail cursor. If signal chains (WLA-25-02) and run ledgers stream through
one endpoint, the event envelope needs a source discriminator — decide
in the WLA-25-01 contract.
