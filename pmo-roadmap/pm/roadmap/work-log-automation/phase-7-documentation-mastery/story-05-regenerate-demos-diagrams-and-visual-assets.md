# WLA-7-05 - Regenerate demos diagrams and visual assets

- **Project:** work-log-automation
- **Phase:** 7
- **Status:** done
- **Depends on:** WLA-7-01, WLA-7-02
- **Unblocks:** WLA-7-07
- **Owner:** unassigned

## Problem

The VHS demos predate the workbench and contract v2; the READMEs have
no visual proof of the workbench at all; and the repo has no social
preview. Assets are documentation: they must show the framework as it
is, regenerate reproducibly, and be verified like everything else.

## Scope

- **In:** Refresh both VHS tapes against current output and add a
  workbench tape (or animated capture) showing explore → health →
  trace → guarded edit; curated README screenshots from the existing
  headless-Firefox harness; Mermaid diagrams referenced by
  WLA-7-02's architecture guide; a social-preview image; alt text on
  every asset; and reproducibility (each asset names the script that
  regenerates it).
- **Out:** Brand design systems, video hosting, marketing pages.

## Acceptance criteria

- [ ] Every rendered demo/screenshot in the docs is regenerated from
  current sources by a checked-in script (captured run).
- [ ] The workbench appears in the root README with real screenshots.
- [ ] All Mermaid sources render on GitHub (no syntax fallbacks).
- [ ] Every image has alt text; the demo-prep scripts stay in the CI
  smoke.
- [ ] The repo has a social preview set and committed under assets.

## Test plan

- **Unit:** n/a.
- **Integration:** demo-prep + screenshot scripts run in the suite.
- **Manual / device:** view every asset on rendered GitHub pages.
