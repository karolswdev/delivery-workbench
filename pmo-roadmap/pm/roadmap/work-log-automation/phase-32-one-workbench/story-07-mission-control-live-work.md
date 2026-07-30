# WLA-32-07 - Mission control for live work

- **Project:** work-log-automation
- **Phase:** 32
- **Status:** done
- **Depends on:** WLA-32-06
- **Unblocks:** WLA-32-08
- **Owner:** unassigned

## Problem

Live work is split between bounded-run and program control rooms, so a blocked decision can stay hidden until someone opens the right run. The workbench needs one Live view that says what is running, what happens next, and where a person must act. It must remain a client of the existing ledgers and guarded actions, not become a scheduler.

## Scope

- **In:** Add one Live view in `pmo-roadmap/workbench/app.js` and `pmo-roadmap/workbench/style.css` that combines the bounded-run and program inventories. Build its detail panels from the canonical run and program views, including status, next step, blockers, requests, budgets, notifications, and timeline. Surface outstanding decisions across all live work. Add a finite, preview-bound bounded-run supervision route in `pmo-roadmap/lib/dw_pmo/workbench.py`, with ceilings bound into the token and stop rules matching program supervision. Keep `/api/runs/<id>/events` and `/api/programs/<id>/events` as invalidation signals that trigger a canonical refetch. Use existing bounded stream opens for stdout and stderr details.
- **Out:** A background scheduler, start-on-open, automatic work triggered by live events, blind retries, arbitrary command entry, runtime authority increases, generic delivery buttons, merge, force-push, release, deploy, or changes to the run and program ledgers.

## Localization hints

- **Affected files:**
  - `pmo-roadmap/workbench/app.js`
  - `pmo-roadmap/workbench/style.css`
  - `pmo-roadmap/lib/dw_pmo/workbench.py`
  - `pmo-roadmap/lib/dw_pmo/orchestration_surface.py`
  - `pmo-roadmap/lib/dw_pmo/program_surface.py`

## Acceptance criteria

- [ ] One Live destination lists every bounded run and program with its kind, current status, canonical next step, and whether a decision or blocker needs attention.
- [ ] Outstanding decisions, blockers, and unacknowledged notifications are visible in the combined list without opening each control room, and each item links to the exact place where it can be handled.
- [ ] Each detail panel has one canonical next step, one readable refusal or recovery outcome, and a Technical details route with a clear return to the ordinary view.
- [ ] Pause is described as resumable, revoke as permanent loss of permission, and cancel as revocation plus bounded interruption; the three controls look distinct and show their consequence before confirmation.
- [ ] Resume is available only for paused work. Revoked or cancelled work cannot be resumed, and the refusal explains why.
- [ ] Bounded-run supervision requires a preview and exact single-use token that binds the maximum ticks, maximum seconds, current ledger head, generation, and action.
- [ ] Bounded-run supervision accepts only finite ceilings within the published limits, performs no more work than the approved ceilings, and stops at a checkpoint, terminal state, or no-progress result.
- [ ] A stale or mismatched supervision token is refused without advancing the run, and an uncertain transport result tells the person to reload history instead of retrying automatically.
- [ ] Live-event messages only mark the view for canonical refetch. They never start, tick, supervise, retry, approve, or otherwise mutate work.
- [ ] After a dropped event connection or failed refetch, the view marks its data as stale and offers an explicit refresh; it does not hide the last known state or retry a mutation.
- [ ] Output opens only on an explicit request, remains capped at 100 KB per stream read, and cannot be used to submit an arbitrary command.

## Test plan

- **Unit:** `/usr/bin/python3 pmo-roadmap/tests/dw-core-tests.py`
- **Integration:** `bash pmo-roadmap/tests/workbench-explorer.sh`
- **Manual / device:** `bash pmo-roadmap/tests/workbench-ui-smoke.sh`; inspect the combined Live view at 1440x900 and 390x844 for active, awaiting-decision, paused, revoked, cancelled, blocked, stale, and complete states. Disconnect the event stream, confirm the stale marker and explicit refresh, and exercise a stale supervision token without advancing the run.

## Notes / open questions

Use the existing run and program states as facts; the combined view may group them in plain language but must not invent a third state machine. The default decision is to add the finite bounded-run web supervision contract in this story. Its HTTP shape should mirror program supervision closely enough that the permission tests can compare both paths.

Reuse the canonical run/program views, summary inventories, cursor tail reads, and bounded stream reads. Program supervision already has preview-bound ceiling and frontier checks; the bounded-run web contract should follow that shape rather than the current direct CLI call.
