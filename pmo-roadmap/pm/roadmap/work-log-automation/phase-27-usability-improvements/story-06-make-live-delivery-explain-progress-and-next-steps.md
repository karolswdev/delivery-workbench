# WLA-27-06 - Make live delivery explain progress and next steps

- **Project:** work-log-automation
- **Phase:** 27
- **Status:** backlog
- **Depends on:** WLA-27-03, WLA-27-04, WLA-27-05
- **Unblocks:** WLA-27-07 through WLA-27-10
- **Owner:** unassigned

## Problem

The live program surface exposes exact state and a rich event stream, but an
operator should not have to reconstruct the delivery story from protocol
events. The normal view must make progress, ownership, review results,
blockers, and the next step obvious while retaining complete technical
inspectability.

This story redesigns live operation around the seven questions in the Phase 26
handoff and derives every answer from the existing canonical state.

## Scope

- **In:** live Workbench summary and navigation; delivery scope/progress;
  active, waiting, review, repair, blocked, and complete work; current owner and
  reviewer; passed/failed evidence summaries; decisions and blockers; remaining
  permission/cost; one canonical next-step explanation; readable activity
  grouped separately from the exact audit timeline; replay/recovery and stale
  connection states; responsive fixtures.
- **Out:** changing conductor selection, eligibility, dispatch, evidence,
  review, delivery, replay, or recovery logic; inventing a UI-only next action;
  hiding exact events; decision controls owned by WLA-27-07; hosted monitoring.

## Acceptance criteria

- [ ] The default live view directly answers what is being delivered, who is
  doing and reviewing it, what passed, what is blocked, who must decide, what
  permission/cost remains, and what happens next.
- [ ] Work is grouped by understandable delivery state with exact story/run
  identity available on demand; waiting, idle, complete, stopped, revoked,
  failed, and recovering states cannot be confused.
- [ ] Review outcomes distinguish mechanical checks, agent judgment, dissent,
  repair, and final governed decisions without overstating what any one result
  proves.
- [ ] The displayed next step and blocker are projections of canonical
  conductor/status facts; the renderer contains no alternate selection,
  authority, or recovery policy.
- [ ] A readable activity view groups related work and outcomes, while the
  exact ordered/hash-linked events and provenance remain accessible in the
  technical/audit view.
- [ ] Disconnect, replay, crash recovery, duplicate delivery receipts, and
  stale snapshots produce honest state and recovery guidance without
  suggesting that work was lost or repeated when the ledger proves otherwise.

## Test plan

- **Unit:** cover application-view summaries and next-step explanations for
  active, review, repair, blocked, stopped, revoked, recovering, and complete
  fixtures.
- **Integration:** extend HTTP/SSE/Workbench parity and recovery tests so every
  visible answer traces to canonical state and exact events remain unchanged.
- **Manual / device:** run the live-progress journeys at wide and narrow
  viewports, including audit inspection, disconnect, reconnect, and recovery.

## Notes / open questions

Readable grouping may summarize many events, but it must never delete, reorder,
or reinterpret the audit record. Counts and progress labels must define their
denominators and unknown states.
