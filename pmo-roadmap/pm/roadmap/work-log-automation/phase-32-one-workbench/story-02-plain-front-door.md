# WLA-32-02 - A front door in plain words

- **Project:** work-log-automation
- **Phase:** 32
- **Status:** backlog
- **Depends on:** WLA-32-01
- **Unblocks:** WLA-32-03, WLA-32-04
- **Owner:** unassigned

## Problem

The workbench opens with seven navigation choices written around the
system's internal structure, and a repository with several projects silently
redirects to the first one. A new user has to learn the machinery before they
can choose a project or understand what to do next.

## Scope

- **In:** Replace the seven links in `pmo-roadmap/workbench/index.html` and
  their route presentation in `pmo-roadmap/workbench/app.js` with at most
  five plain destinations. Decide the final names against
  `pmo-roadmap/docs/product-language-contract-v1.json` and the 13 journeys
  in `pmo-roadmap/docs/usability-journeys.md`; "Board", "Plan",
  "Automation", "Live", and "Health" are the starting proposal, not a
  fixed answer. Add a project selector that keeps the chosen project while
  the user moves between routes. Rewrite ordinary-panel copy so everyday
  words come first, exact terms appear only in a labelled "Technical
  details" fold, and each panel presents one canonical next step. Update
  `pmo-roadmap/tests/workbench-explorer.sh`,
  `pmo-roadmap/tests/workbench-ui-smoke.sh`, and
  `pmo-roadmap/tests/workbench-accessibility.py` to cover the new front
  door.
- **Out:** Changes to the meaning of any command or mutation; removal of
  exact technical information; authentication or project-level access
  control; the board-home and in-browser planning work owned by WLA-32-03
  and WLA-32-04.

## Localization hints

- **Affected files:**
  - `pmo-roadmap/workbench/index.html`
  - `pmo-roadmap/workbench/app.js`
  - `pmo-roadmap/lib/dw_pmo/workbench.py`
  - `pmo-roadmap/tests/workbench-explorer.sh`
  - `pmo-roadmap/tests/workbench-ui-smoke.sh`
  - `pmo-roadmap/tests/workbench-accessibility.py`

## Acceptance criteria

- [ ] The shell shows no more than five destinations, and each name uses an
  everyday concept from the product language contract or a tested synonym
  that a first-time user can explain.
- [ ] When more than one project exists, the user can choose one before
  entering its routes; the workbench does not silently choose the first
  project.
- [ ] The selected project remains selected while the user follows links,
  reloads a route, and returns from Technical details. An unavailable
  project produces a plain explanation and a route back to the selector
  instead of redirecting to another project.
- [ ] No term from the contract's technical column appears in an ordinary
  panel. When an exact term is needed, it appears inside a fold labelled
  "Technical details", with an obvious way to close it and return focus to
  the control that opened it.
- [ ] Each ordinary panel leads with one primary next step. The 13 journeys
  in `pmo-roadmap/docs/usability-journeys.md` each have one canonical route
  forward plus a Technical details route and return path.
- [ ] The destination list, project selector, folds, and primary actions are
  fully operable by keyboard, retain non-color focus cues, and fit at
  390x844 without horizontal page overflow.

## Test plan

- **Unit:** `python3 pmo-roadmap/tests/dw-core-tests.py`
- **Integration:** `bash pmo-roadmap/tests/workbench-explorer.sh`
- **Browser:** `bash pmo-roadmap/tests/workbench-ui-smoke.sh`
- **Accessibility:** `python3 pmo-roadmap/tests/workbench-accessibility.py`
- **Manual / device:** Start the workbench in a fixture with at least two
  projects, choose the second project, visit every destination, reload, and
  return from each Technical details fold at 1440x900 and 390x844. Compare
  every ordinary panel against
  `pmo-roadmap/docs/product-language-contract-v1.json`.

## Notes / open questions

Choose the final destination names during implementation with the language
contract and journey tests open. Five labels are a ceiling, not a target.
Exact language still matters for audit and support, so this story moves it
under Technical details rather than deleting or paraphrasing it beyond
recognition.
