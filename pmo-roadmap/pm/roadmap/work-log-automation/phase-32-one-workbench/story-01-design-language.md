# WLA-32-01 - One calm design language

- **Project:** work-log-automation
- **Phase:** 32
- **Status:** backlog
- **Depends on:** none
- **Unblocks:** WLA-32-02
- **Owner:** unassigned

## Problem

The workbench has grown route by route, and its cards, tables, controls,
folds, and status labels no longer look like parts of one product. The
current stylesheet already handles accessibility modes, but it lacks a
small set of shared visual rules that later Phase 32 work can build on.

## Scope

- **In:** Add CSS custom properties for type, spacing, color roles,
  radii, and elevation at the top of
  `pmo-roadmap/workbench/style.css`. Give light and dark themes explicit
  role values, then migrate the existing route styles to those tokens so
  cards, tables, buttons, folds, and status pills share one visual
  language. Refresh the wide and mobile screenshot coverage in
  `pmo-roadmap/tests/workbench-ui-smoke.sh` for both themes.
- **Out:** Route, navigation, wording, data, and mutation changes in
  `pmo-roadmap/workbench/app.js` or
  `pmo-roadmap/lib/dw_pmo/workbench.py`; a new CSS framework; removal of
  the existing reduced-motion or forced-colors behavior.

## Localization hints

- **Affected files:**
  - `pmo-roadmap/workbench/style.css`
  - `pmo-roadmap/tests/workbench-ui-smoke.sh`

## Acceptance criteria

- [ ] The top of `pmo-roadmap/workbench/style.css` defines a documented
  type scale, spacing scale, semantic color roles, radii, and elevation,
  with complete values for light and dark themes.
- [ ] Every route uses the shared card, table, button, fold, and status-pill
  treatment; the 1440x900 and 390x844 screenshot matrix shows no route
  retaining a conflicting one-off treatment.
- [ ] The refreshed screenshot matrix covers every route in both light and
  dark themes, and each image has readable text, visible focus and status
  cues, and no horizontal page overflow.
- [ ] Existing links, forms, folds, and guarded actions still behave the
  same after the style migration, as shown by the explorer and browser
  smoke suites.
- [ ] With reduced motion requested, transitions and animations remain
  suppressed; with forced colors active, controls, focus, and status stay
  distinguishable without relying on the theme palette.
- [ ] The keyboard and region exam passes at both supported viewport widths.

## Test plan

- **Unit:** `python3 pmo-roadmap/tests/dw-core-tests.py`
- **Integration:** `bash pmo-roadmap/tests/workbench-explorer.sh`
- **Browser:** `bash pmo-roadmap/tests/workbench-ui-smoke.sh`
- **Accessibility:** `python3 pmo-roadmap/tests/workbench-accessibility.py`
- **Manual / device:** Open the screenshot matrix produced by
  `bash pmo-roadmap/tests/workbench-ui-smoke.sh`; compare every route at
  1440x900 and 390x844 in light and dark themes, then repeat one route with
  reduced motion and forced colors enabled.

## Notes / open questions

Keep the token set small enough to review in one screen. Route-specific
layout values can remain where they express a real layout need, but shared
component color, spacing, shape, and depth should come from the token layer.
The screenshot refresh is evidence of consistency, not permission to alter
what any route does.
