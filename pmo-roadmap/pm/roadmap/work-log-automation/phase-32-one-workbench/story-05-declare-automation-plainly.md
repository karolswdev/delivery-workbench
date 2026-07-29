# WLA-32-05 - Declare automation in plain words

- **Project:** work-log-automation
- **Phase:** 32
- **Status:** backlog
- **Depends on:** WLA-32-02
- **Unblocks:** WLA-32-06
- **Owner:** unassigned

## Problem

Program Studio makes people understand its graph and JSON before they can describe the work they want done. The ordinary path should ask about the delivery, the team, the independent review, the decision points, the repair path, the stops, and the finite limits in that order. People still need access to the exact declaration, but it should not lead the conversation.

## Scope

- **In:** Rework Program Studio in `pmo-roadmap/workbench/app.js` and `pmo-roadmap/workbench/style.css` so the five existing tabs lead with task-shaped forms based on `pmo-roadmap/docs/plan-authoring.md`. Put the graph and raw JSON under a Technical details fold with a clear way back to the plain form. Show the review criteria referenced from `pmo-roadmap/pm/rubrics/` as readable, read-only content in the browser. Keep edits to `pmo-roadmap/pm/programs/*.json`, `pmo-roadmap/pm/workflows/`, and `pmo-roadmap/pm/organizations/` behind the existing `/api/program-studio/preview` then `/apply` boundary, including preservation of fields the form does not understand.
- **Out:** Rubric authoring, rubric engine changes, driver or credential management, new program authority, and changes to the preview or token model.

## Localization hints

- **Affected files:**
  - `pmo-roadmap/workbench/app.js`
  - `pmo-roadmap/workbench/style.css`
  - `pmo-roadmap/lib/dw_pmo/workbench.py`

## Acceptance criteria

- [ ] Opening Program Studio starts with plain questions about what will be delivered and who will do the work; the flow then covers independent review, decision points, repair, stop conditions, and finite spending or work limits in the order prescribed by `pmo-roadmap/docs/plan-authoring.md`.
- [ ] A person can complete the ordinary planning flow without reading or editing a graph or JSON document.
- [ ] Every ordinary form has a Technical details route that shows the exact graph and JSON, and that route has a visible control that returns to the same place in the plain form without discarding edits.
- [ ] When a program refers to review criteria under `pmo-roadmap/pm/rubrics/`, the browser shows those criteria in readable, read-only form and identifies missing references plainly.
- [ ] Saving a Studio change first shows the files and changes to be applied, and apply accepts only the exact single-use token from that preview.
- [ ] A stale, reused, or mismatched apply token is refused, the declaration files stay unchanged, and the page explains that a fresh preview is required.
- [ ] Previewing and applying a change preserves declaration fields that the plain form does not recognize.
- [ ] The ordinary panels use everyday words; exact declaration terms remain available under Technical details.

## Test plan

- **Unit:** `/usr/bin/python3 pmo-roadmap/tests/dw-core-tests.py`
- **Integration:** `bash pmo-roadmap/tests/workbench-explorer.sh`
- **Manual / device:** `bash pmo-roadmap/tests/workbench-ui-smoke.sh`; inspect the Program Studio screenshots at 1440x900 and 390x844, follow the plain form into Technical details and back, open a referenced rubric, and confirm a stale-token refusal leaves the source files unchanged.

## Notes / open questions

Rubrics stay read-only in this phase. The form should preserve advanced declarations it cannot edit rather than flattening or deleting them. During implementation, decide whether a missing rubric gets an inline explanation or a dedicated empty state; either choice must name the broken reference and a safe next step.

Program Studio lives around the `#/program-studio/` routes in app.js; reuse the existing preview/apply handlers in workbench.py rather than adding a second write path.
