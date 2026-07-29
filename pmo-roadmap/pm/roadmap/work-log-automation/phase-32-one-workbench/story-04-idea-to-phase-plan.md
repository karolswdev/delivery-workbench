# WLA-32-04 - From rough idea to phase plan

- **Project:** work-log-automation
- **Phase:** 32
- **Status:** backlog
- **Depends on:** WLA-32-02
- **Unblocks:** WLA-32-08
- **Owner:** unassigned

## Problem

The browser can show a detailed setup proposal, but its accept and reject
marks live only in the current browser session and the normal path ends with
terminal commands. A person should be able to turn rough text into a
corrected phase plan and apply it without leaving the workbench, while every
draft remains inert until the guarded apply step.

## Scope

- **In:** Build one guided flow in `pmo-roadmap/workbench/app.js` that takes
  rough idea text, presents an editable draft of phases, stories, acceptance
  criteria, and source notes, carries review decisions into corrections,
  then previews and applies the result through the existing
  `/api/setup/preview` and `/api/setup/apply` routes in
  `pmo-roadmap/lib/dw_pmo/workbench.py`. Reuse the current adoption review
  and its proposal shape instead of creating a second review model. Keep the
  terminal commands under Technical details as a fallback. Cover the full
  flow in `pmo-roadmap/tests/workbench-explorer.sh`,
  `pmo-roadmap/tests/workbench-ui-smoke.sh`,
  `pmo-roadmap/tests/workbench-accessibility.py`, and
  `pmo-roadmap/tests/dw-core-tests.py`.
- **Out:** Starting a story, run, or program; granting permission; changing
  setup lease semantics; a browser scheduler; free-form file editing; making
  `dw program scaffold --answers <file>` the required browser path; removal
  of the terminal setup workflow.

## Localization hints

- **Affected files:**
  - `pmo-roadmap/workbench/app.js`
  - `pmo-roadmap/lib/dw_pmo/workbench.py`
  - `pmo-roadmap/tests/dw-core-tests.py`
  - `pmo-roadmap/tests/workbench-explorer.sh`

## Acceptance criteria

- [ ] A user can enter rough idea text and reach a structured browser draft
  containing at least one editable phase, its stories, independently
  editable acceptance criteria, and source notes without using a terminal.
- [ ] Accept and reject decisions made during review affect the draft: an
  accepted item remains in the preview, while a rejected item must be
  corrected or removed before preview. Reloading or moving between steps
  does not silently discard those decisions.
- [ ] The review step shows the complete proposed setup in plain words and
  offers one canonical next step to preview it. Exact proposal data and the
  terminal fallback appear only under Technical details, with a return path
  to the same review position.
- [ ] Preview uses the existing setup preview route and shows the exact plan
  before apply. Editing the draft after preview invalidates that preview and
  requires a fresh one.
- [ ] Apply uses the matching one-use setup lease. Missing, stale, changed,
  or reused leases are refused with a plain explanation, and the canonical
  files remain unchanged.
- [ ] Opening the flow, typing an idea, structuring it, and recording review
  decisions writes no project files, starts no work, and grants no
  permission. A successful apply creates configuration only; it does not
  start a story, run, or program.
- [ ] The full journey and every refusal can be completed by keyboard at
  1440x900 and 390x844, with focus moved to each new step and returned from
  Technical details, no horizontal page overflow, and no color-only review
  state.

## Test plan

- **Unit:** `python3 pmo-roadmap/tests/dw-core-tests.py`
- **Integration:** `bash pmo-roadmap/tests/workbench-explorer.sh`
- **Browser:** `bash pmo-roadmap/tests/workbench-ui-smoke.sh`
- **Accessibility:** `python3 pmo-roadmap/tests/workbench-accessibility.py`
- **Manual / device:** In a disposable unconfigured repository, enter a rough
  idea, edit the generated phase and stories, accept one item, reject and
  correct another, preview, edit once more to invalidate the preview, then
  preview and apply. Repeat the journey at 390x844 and confirm that no files,
  work, or permissions exist before apply and that the lease cannot be
  reused afterward.

## Notes / open questions

Decide during implementation whether the first structured draft is assembled
in the client or by a thin server adapter around the existing inert proposal
builder. Either choice must produce the same proposal shape the setup routes
already accept, must work without giving the browser scheduling authority,
and must leave the draft inert. For a small addition to an existing project,
the same flow may finish through the existing guarded phase and story
creation actions, but setup preview and apply remain the required adoption
path.

The current adoption review is the `#/edit/adoption_review` route; the setup preview/apply handlers and their one-use lease already exist in workbench.py. Keep proposal building separate from those handlers so drafting cannot acquire apply authority.
