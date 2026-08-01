# WLA-33-09 - Prove it works and looks right

- **Project:** work-log-automation
- **Phase:** 33
- **Status:** done
- **Depends on:** WLA-33-00, WLA-33-02, WLA-33-03, WLA-33-04, WLA-33-05, WLA-33-06, WLA-33-07, WLA-33-08
- **Unblocks:** none
- **Owner:** unassigned

## Problem

Every prior story changed the workbench layout and interaction. This
story is the exam: prove the whole workspace holds together, nothing
broke, and the authority model is intact.

## Scope

- **In:** Run the full UI smoke suite, the accessibility suite, and
  the language-lint suite against the new workspace layout. Capture
  wide (1440px+) and mobile (390px) screenshot matrices in both themes
  for every panel combination. Run the permission-model test subset
  to prove no mutation is reachable without a fresh exact token. Record
  a walkthrough: open workbench → see board → click story → see session
  stream → open diff → toggle terminal → check insights → find advanced
  features → close panels.
- **Out:** New features. Bug fixes beyond what the suites expose.

## Localization hints

- **Affected files:**
  - `pmo-roadmap/tests/workbench-ui-smoke.sh`
  - `pmo-roadmap/tests/workbench-explorer.sh`
  - `pmo-roadmap/tests/workbench-accessibility.py`
  - `pmo-roadmap/tests/dw-core-tests.py`

## Acceptance criteria

- [x] The UI smoke suite passes with zero failures on the new layout.
- [x] The accessibility suite passes (keyboard navigation, focus
  management, ARIA labels on all interactive elements).
- [x] The language-lint suite passes — no technical jargon outside
  "Technical details" folds in the default workspace.
- [x] Wide and 390px screenshot matrices exist for both themes, covering
  all panel combinations.
- [x] The permission-model tests pass — no mutation without a fresh
  exact token.
- [x] A recorded walkthrough demonstrates the full workspace flow from
  open to close.
