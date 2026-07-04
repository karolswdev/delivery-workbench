# WLA-13-04 - Emit the events worth showing

- **Project:** work-log-automation
- **Phase:** 13
- **Status:** done
- **Depends on:** WLA-13-01
- **Unblocks:** WLA-13-05
- **Owner:** unassigned

*Re-pinned by WLA-13-01 (2026-07-04): implement against
[docs/mission-control.md](../../../../../docs/mission-control.md) §3 (seven events, `.git/pmo-events.jsonl`, content-audit test).*

## Problem

The conveyor's delight lives in moments, not snapshots: a story
sliding into the done station, a gate refusal flashing the rule it
named, an evidence capture landing. The rails already produce all
of these — in hook banners and evidence files — but nothing emits
them as consumable events, so any UI would have to poll and diff
the whole state to notice that something just happened.

## Scope

- **In:** An append-only event log of rail happenings — status
  flips, evidence captures, contract certifications, gate passes
  and refusals (with rule id) — written at the moment the
  machinery already observes them (hooks, capture, status
  mutation); shape and persistence per the WLA-13-01 taxonomy and
  the deferred persistence decision; the consent stance recorded
  in the design doc and enforced: events describe the rails, never
  transcript or diff content.
- **Out:** Push transport / subscriptions (consumers poll the log
  this phase); notification UX (Desk-side); analytics over the
  log.

## Acceptance criteria

- [ ] Each taxonomy event appears in the log when its rail moment
  happens, test-proven per event type, including a gate refusal
  carrying its rule id.
- [ ] The log is append-only and survives an aborted commit the
  way the contract archive does.
- [ ] A content audit test proves no event carries transcript or
  diff payloads.
- [ ] Full battery passes.

## Test plan

- **Unit:** event emission per rail moment; content audit.
- **Integration:** a full story loop in a fixture emits the
  expected event sequence.
- **Manual / device:** the log tailed live during a real story
  loop, captured as evidence.

## Notes / open questions

- Persistence (append-only file vs sqlite) - deferred to this
  story with real volume data, per the phase status.
