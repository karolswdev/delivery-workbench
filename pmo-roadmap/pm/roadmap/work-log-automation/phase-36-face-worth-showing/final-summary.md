# Phase 36 Final Summary

**Status:** complete.
**Date:** 2026-08-02.

# Phase 36 — Final summary

**Closed:** 2026-08-02. All 5 stories (WLA-36-01 through WLA-36-05) done.

Phase 36 replaced the workbench's scaffold-grade visual layer with a real
design language, opened on the owner's direct verdict and course-corrected
mid-phase on the owner's directive that operator-oss is the inspiration:
its own mission-control skin became the visual source of truth, with the
owner-designated Linear reference as the discipline bar. Designed and
executed by Sol (GPT-5.6) under operator orchestration, with the operator
reviewing rendered screenshots in both themes before every story flipped.

## Outcome vs exit criteria

- **Token system enforced** — met. 126 role-named tokens; a stylesheet
  fitness guard (with planted regressions proving it bites) rejects hex
  outside the token block, mono outside the designated code/ops-label
  classes, and spacing off the 8px grid.
- **Operator-reviewed matrix, misalignments fixed** — met. The operator
  reviewed renders at every story and named defects (green-flooded
  delivery-setup, decorative tri-color mode-card borders, clipped
  needs-you count); the closing sweep fixed those and everything else it
  found, with mechanical one-pixel alignment assertions now measuring the
  topbar, board columns, memory fact grid, and Studio panes.
- **Both themes, both viewports** — met. Dark-native mission-control
  default plus the warm-paper light override pass the full 352-render
  exam at 1440x900 and 390x844.
- **Full battery green, README regenerated** — met. Core 727/727, both
  packaged exams, explorer, accessibility contract, language lint;
  README screenshots regenerated from the redesigned dark UI.

## What shipped

- **WLA-36-01 Design tokens and type**: the operator-oss palette verbatim
  (near-black surfaces, blue-tinted hairlines, electric-blue accent,
  coral/amber/green/blue semantic signals with washes and glows, warm-paper
  light theme), Space Grotesk + JetBrains Mono vendored (SIL OFL, served
  locally, wheel-enrolled), the 400/500/700 weight system, 8px grid, and
  the deliberate dark-default theme-pin flip.
- **WLA-36-02 Shell and navigation**: quiet wordmark, one mono project
  crumb, omni ⌘K trigger, the coral needs-you pill and designed popover,
  icon-demoted density/refresh, restyled palette, one-line footer, one
  28px topbar baseline.
- **WLA-36-03 Board and cards**: one card anatomy with semantic rails and
  at most one soft-wash badge (badge zoo gone and pinned gone), quiet
  overline headers, soft-wash needs-you column, accent-blue primaries,
  clean header band, 'Ready. ready' duplication fixed at source.
- **WLA-36-04 Panels and detail surfaces**: component-level restyle so
  every panel inherits — shared header grid, aligned fact rows, semantic
  pills, designed authority badges (mechanical vs judgment distinct),
  code inside designed frames, quiet empty/refusal states.
- **WLA-36-05 Alignment sweep and visual exam**: operator-named and
  sweep-found defects fixed (green confined to done-semantics everywhere,
  decorative borders removed, chip geometry corrected), the two
  mechanical guards landed, full battery re-baselined, README screenshots
  regenerated.

## Evidence

Every story has a paired evidence file whose captured runs include the
full 352-render browser exam. Core suite: 727 tests, zero failures
throughout. Browser assertions grew 454 → 476 core / 152 program with
ten board-card, eight panel-system, and the alignment/fitness guards.

## Deliberately deferred

- Release remains the owner's landing-phase decision (phases 32-36
  unreleased on main).
- The workbench demo film and social preview still show the old skin;
  regenerating them is a release-ritual step.
