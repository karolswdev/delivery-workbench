# WLA-27-07 - Turn decisions, blockers, permissions, and cost into actions

- **Project:** work-log-automation
- **Phase:** 27
- **Status:** done
- **Depends on:** WLA-27-03, WLA-27-05, WLA-27-06
- **Unblocks:** WLA-27-08, WLA-27-09, WLA-27-10
- **Owner:** unassigned

## Problem

Usability becomes a trust failure if the pleasant summary disappears at the
moment a person must decide, recover, spend, or stop. Current exact request,
grant, budget, refusal, and error models must become understandable actions
without broadening authority or turning a transport response into permission.

This story creates one action language for blocked work, human decisions,
remaining permission and cost, recoverable errors, pause/stop/revoke, and stale
or already-applied requests.

## Scope

- **In:** decision/blocker inbox and detail; closed response sets derived from
  canonical requests; effect/limit summaries before action; remaining
  permission, phase/story/step, time, and cost views; pause, stop, revoke, and
  resume explanations; refusal/error structure describing what happened, what
  did not change, and the next safe step; stale/duplicate/applied/recovered
  states; exact audit details and receipts.
- **Out:** new approval channels, standing-authority semantics, budget types,
  retry policy, transport-equals-authority behavior, automatic responses,
  conflict resolution, or release/deploy controls.

## Acceptance criteria

- [x] Every blocker says what work is affected, why it cannot proceed, who or
  what can resolve it, which choices are currently valid, and what will happen
  after each choice.
- [x] Decision controls are generated from the exact outstanding request and
  closed response set; stale, revoked, already-applied, unauthorized, or
  mismatched responses refuse without an ambiguous retry.
- [x] Before granting or consuming permission, the application states the
  concrete effects allowed, scope, ceilings, expiry/stop conditions, current
  consumption, and what remains forbidden in ordinary language.
- [x] Cost and progress distinguish limits, estimates, actual consumption,
  remaining capacity, and unknown/not-applicable values; zero and unbounded
  cannot be confused.
- [x] Pause, stop, revoke, cancel, reject, retry, and resume are distinct
  actions with consequences shown before confirmation and exact receipts after
  completion.
- [x] Errors and refusals state what happened, what state remained unchanged,
  whether an effect may already have occurred, the safe next step, and how to
  inspect exact technical evidence.
- [x] Notification/remote presentation may carry or draft a response but
  cannot manufacture authority; canonical principal, token, freshness, and
  request checks remain decisive.

## Test plan

- **Unit:** cover decision/effect summaries, permission and cost arithmetic,
  zero/unbounded/unknown states, stale response red paths, and error recovery
  language.
- **Integration:** exercise Workbench and notification flows against the same
  outstanding-request and grant models, including replay-safe duplicate and
  crash-boundary cases.
- **Manual / device:** complete blocked-decision, remaining-limit,
  pause/revoke, and recoverable-error journeys without consulting raw JSON,
  then verify each exact receipt in the audit view.

## Notes / open questions

Friendly wording must not soften refusals or collapse materially different
actions. The confirmation level should be proportionate to the exact effect,
not applied indiscriminately to every read or reversible draft.
