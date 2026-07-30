# WLA-32-06 - Consent you can read

- **Project:** work-log-automation
- **Phase:** 32
- **Status:** done
- **Depends on:** WLA-32-05
- **Unblocks:** WLA-32-07
- **Owner:** unassigned

## Problem

The run and program start panels ask for names and a reason while the permission being granted is buried in Technical details. A person should see the allowed work, limits, expiry, stops, destination, and permanent exclusions before approving a start. The server also rejects two standing-notification fields that its own run-start handler reads, and its startup copy now understates what a browser-confirmed program can deliver.

## Scope

- **In:** Rework the bounded-run and program start panels in `pmo-roadmap/workbench/app.js` and `pmo-roadmap/workbench/style.css` so permission is the headline. Present capabilities, budgets, expiry, stop conditions, push destination, and permanent exclusions in plain words, with controls to reduce capabilities, budgets, and lifetime where the planner permits. Update `pmo-roadmap/lib/dw_pmo/workbench.py` so `/api/runs/start` accepts `standing_nudges` and `signal_channel`, and correct its module header, startup banner, and related UI copy to describe delivery authority precisely. Keep start and narrowing actions behind preview, an exact single-use token, and apply.
- **Out:** Expanding a policy envelope, runtime elevation of scope or mode, changing grant semantics, adding credentials, merge or force-push controls, release or deploy controls, and generic certify or commit buttons.

## Localization hints

- **Affected files:**
  - `pmo-roadmap/workbench/app.js`
  - `pmo-roadmap/workbench/style.css`
  - `pmo-roadmap/lib/dw_pmo/workbench.py`

## Acceptance criteria

- [ ] Before a bounded run or program can start, the panel states in plain words what work is allowed, what it may spend, when permission expires, what makes it stop, where it may push, and what it can never do.
- [ ] The start panel lets a person reduce capabilities, budgets, and lifetime whenever the planner says those values may be narrowed, and the preview shows the reduced permission before approval.
- [ ] The start panel never offers a control that raises a capability, budget, lifetime, mode, or scope above the planned policy envelope.
- [ ] If the person leaves the narrowing controls untouched, the preview keeps the planned policy envelope and says plainly that no limits were reduced.
- [ ] Starting either kind of work requires a preview followed by the exact single-use token; opening a page or receiving a live update never starts work.
- [ ] A stale, reused, or mismatched start token is refused, no run or program starts, and the panel tells the person to review a fresh preview.
- [ ] A request to `/api/runs/start` may include `standing_nudges` and `signal_channel`; accepted values reach the handler, while an unknown property is still refused.
- [ ] The server header, startup banner, and start-panel copy no longer claim that the workbench can never stage, certify, or commit. They state that only a browser-confirmed program action may use pre-granted delivery permission, and that the browser adds no authority of its own.
- [ ] Permanent exclusions remain visible before approval and include no merge, force-push, release, deploy, arbitrary command, or authority elevation.

## Test plan

- **Unit:** `/usr/bin/python3 pmo-roadmap/tests/dw-core-tests.py`
- **Integration:** `bash pmo-roadmap/tests/workbench-explorer.sh`
- **Manual / device:** `bash pmo-roadmap/tests/workbench-ui-smoke.sh`; inspect bounded-run and program consent screenshots at 1440x900 and 390x844, preview one narrowed grant and one unchanged grant, then verify the stale-token refusal starts nothing.

## Notes / open questions

The wording must distinguish possible delivery authority from automatic delivery. A program tick can use delivery actions only when the plan grants them and the person confirms the exact preview. Keep exact capability names and the full grant document under Technical details, with a visible route back to the consent summary.

The program start form sits near the `#/programs` route in app.js. In workbench.py, the run-start accepted-property list and the values the handler actually reads must agree.
