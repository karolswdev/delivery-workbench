# WLA-25-08 - Keep pending decisions alive across the pause

- **Project:** work-log-automation
- **Phase:** 25
- **Status:** backlog
- **Depends on:** WLA-25-01
- **Unblocks:** WLA-25-06, WLA-25-09
- **Owner:** unassigned

## Problem

Phase 24 proved crash recovery for *work*: claimed nodes resume without
duplicate starts. Pending *decisions* are weaker: a checkpoint that was
awaiting a human when the conductor stopped is rediscovered only by
re-deriving the projection, and nothing re-announces it — the decision
silently waits for someone to look. microsoft/agent-framework-go treats
outstanding human requests as first-class checkpoint state: a workflow
snapshot includes its pending external requests, and resume republishes
them, typed and correlated. Adopting that discipline makes pause/resume
honest for humans, not just for agents, and gives WLA-25-06 the seam it
delivers notifications through.

## Scope

- **In:** pending checkpoint decisions (and pending nudge previews
  awaiting manual application) persisted as explicit outstanding-request
  records in run state — typed per the score's request/response schemas,
  correlation-id-bound, hash-chained with the ledger; `run resume` and
  conductor restart republish every outstanding request exactly once
  (a `request-republished` ledger event with the original correlation
  id, consumed by the notification layer); `run show`/`run view`/the
  Workbench list outstanding requests as a first-class section with age
  and origin; checkpoint lineage made explicit — each checkpoint event
  records its parent decision point, so `run view` can render the
  decision history as a tree (read-only time-travel: inspect the state
  a past decision saw; forking a run from a past checkpoint remains
  out); expiry semantics — an outstanding request older than the
  grant's expiry converts to a recorded `expired` refusal, never a
  live decision.
- **Out:** fork-from-checkpoint execution (inspect-only in this phase);
  any change to who may decide (operator, exact token, ring-4 — all
  unchanged); new decision kinds beyond those the score already
  declares.

## Acceptance criteria

- [ ] Stopping the conductor (crash or pause) with a checkpoint pending
  and resuming republishes exactly one `request-republished` event with
  the original correlation id; a decision submitted against the
  pre-restart id still applies, and a duplicate republish cannot occur,
  proven across three consecutive restarts.
- [ ] Outstanding requests are derivable from the ledger alone: a
  replay test reconstructs the pending set at every ledger position and
  matches the live projection.
- [ ] Typed validation holds at the seam: a response that fails the
  declared schema or correlation id is a recorded refusal that leaves
  the request outstanding.
- [ ] The Workbench and `run show` render outstanding requests with age,
  origin node, and schema summary; an operator can find every waiting
  decision without scrolling the ledger.
- [ ] Checkpoint lineage renders as a decision tree in `run view`, and
  inspecting a historical decision shows the exact facts preview the
  decider saw (already ledgered), read-only.
- [ ] Grant expiry converts outstanding requests to recorded `expired`
  refusals during the next tick or resume, and the notification layer
  observes that transition.

## Test plan

- **Unit:** outstanding-request reducer, republish idempotency,
  schema/correlation validation, expiry conversion.
- **Integration:** fixture run with planted crashes at
  pending-checkpoint boundaries; ledger-replay equivalence; Workbench
  render states.
- **Manual / device:** pause a run at a checkpoint, restart the machine
  session, resume, and answer the republished request from the Run view.

## Notes / open questions

The MAF-go checkpoint model also carries in-flight *messages*; our
equivalent (undelivered nudge packets) is deliberately excluded — an
undelivered nudge is refused and re-derived from its signal fact rather
than persisted as a queued message, keeping the ledger the only truth.
