# Workbench accessibility contract

Delivery Workbench treats keyboard, narrow-screen, and assistive use as part of
the same delivery contract as correctness. The contract covers all 13 Phase 27
whole-task journeys; it is not a claim of conformance for unrelated downstream
content rendered from a repository.

## Keyboard contract

- The first Tab reveals **Skip to main content**. Activating it focuses the
  current page heading.
- A route change focuses the destination heading. Re-reading saved facts keeps
  focus on the control the operator used.
- Tabs use Left/Right/Home/End. Delivery choices and plan sections also support
  arrow-key movement, while Enter and Space retain their native activation.
- Native `details` disclosures keep focus on their summary.
- Reviews, confirmations, explicit streams, and action previews are labelled
  non-modal dialogs. Focus moves into the review, Escape closes it, and focus
  returns to the exact opener. Closing a review never applies its action or
  discards the in-memory draft.
- Graph nodes remain selectable and movable by keyboard; pointer dragging is an
  additional interaction, not the only one.

## Focus and dynamic updates

API refresh, polling, and server-sent event redraws capture a stable control
identity and restore it after rendering. They do not move focus to new activity.
Only a changed ledger head is announced. Duplicate poll/SSE versions and stable
connection retries are suppressed so an assistive user does not hear the same
state repeatedly.

Route changes are different from background updates: they announce the new page
name and deliberately focus its heading. `aria-busy` marks the main region while
the route is loading.

## Assistive semantics

The shell exposes separately named primary navigation, breadcrumb navigation,
main content, route status, and material live-update status. Each view has one
page heading. Rendered sections, forms, tables, progress indicators, validation
errors, tabs, tab panels, dialogs, graphs, and disclosures receive names from
their visible headings or labels.

State is never color-only. Ready, completed, warning, blocked, failed, revoked,
and unavailable states retain visible text, border shape, and a status symbol.
Progress includes a numeric value and value text. Technical identifiers remain
selectable text rather than being available only through a tooltip.

## Viewport contract

The supported review sizes are 1440×900 and 390×844. At narrow width:

- the primary navigation, tabs, choice cards, tables, and graph canvases scroll
  inside their own bounded containers;
- form and fact grids collapse to one column where needed;
- buttons remain keyboard reachable and coarse-pointer targets are at least
  44 pixels high;
- hashes, paths, IDs, and other long tokens wrap or scroll locally; and
- the document itself has no horizontal page scroll.

Reduced-motion preferences remove repeating pulses and animated transitions.
Forced-colors mode keeps focus, warning, dialog, and status boundaries visible.

## Automated proof

`pmo-roadmap/tests/workbench-accessibility-contract.py` validates coverage,
state/capture traceability, source markers, and planted negative cases.
`pmo-roadmap/tests/workbench-accessibility.py` uses Firefox’s built-in
Marionette WebDriver endpoint to perform real key actions, inspect focus
round-trips, suppress duplicate live updates, and audit the rendered DOM at both
viewports. It uses no third-party browser package.

The browser exam runs inside:

```sh
pmo-roadmap/tests/workbench-ui-smoke.sh
```

When Firefox is unavailable, the existing UI smoke test records a browser skip;
the static contract and non-browser tests still run. Local and release review
should run with Firefox before accepting Workbench UI changes.

## Manual review record

The reviewed matrix is
[`pmo-roadmap/tests/accessibility-journeys-v1.json`](../pmo-roadmap/tests/accessibility-journeys-v1.json).
For each of the 13 journeys it records:

- the keyboard path and focus-return behavior;
- expected headings, regions, forms, errors, progress, blockers, and states;
- wide and narrow layout observations;
- live-update behavior; and
- the wide, narrow, and assistive semantic review result.

The record is dated and keyed to the canonical state and capture IDs. The
contract checker refuses missing journeys, mismatched states, changed viewport
dimensions, incomplete review notes, or a non-passing result.
