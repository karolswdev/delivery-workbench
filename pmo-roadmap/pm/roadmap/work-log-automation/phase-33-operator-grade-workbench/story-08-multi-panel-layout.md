# WLA-33-08 - Multi-panel layout

- **Project:** work-log-automation
- **Phase:** 33
- **Status:** backlog
- **Depends on:** WLA-33-00, WLA-33-01
- **Unblocks:** WLA-33-02, WLA-33-03, WLA-33-04, WLA-33-05, WLA-33-06, WLA-33-09
- **Owner:** unassigned

## Problem

The current workbench is a single-panel view: one route fills the screen,
and switching means leaving what you were looking at. Operator lets you
see the session transcript, diff, terminal, and status simultaneously —
the workspace is dense because the work needs density.

## Scope

- **In:** Build a multi-panel layout engine for the workspace. Panels
  (board, session, diff, terminal, services, insights) can be opened
  side-by-side or stacked. Resizable dividers between panels. A sensible
  default arrangement (board left, session/diff right, terminal bottom).
  Panels remember their open/closed state across page loads (localStorage).
  On narrow viewports (< 768px), panels stack vertically with swipe or
  tab navigation — no horizontal overflow. Keyboard shortcuts to toggle
  each panel.
- **Out:** Draggable/detachable panels (fixed positions in v1). Saving
  named layouts. Multi-monitor support.

## Localization hints

- **Affected files:**
  - `pmo-roadmap/workbench/app.js` (layout engine module)
  - `pmo-roadmap/workbench/style.css` (grid/flexbox layout, panel sizing)
  - `pmo-roadmap/workbench/index.html` (panel container structure)
  - `pmo-roadmap/tests/workbench-ui-smoke.sh`
  - `pmo-roadmap/tests/workbench-accessibility.py`

## Acceptance criteria

- [ ] At least three panels can be visible simultaneously on a 1440px+
  viewport without scrolling or overlap.
- [ ] Dividers between panels are draggable to resize.
- [ ] Panel open/closed state persists across page reloads.
- [ ] On a 390px viewport, panels stack vertically with a tab bar or
  swipe to switch — no horizontal scrollbar.
- [ ] Keyboard shortcuts exist for toggling each panel (documented in
  the workspace with a help overlay or tooltip).
- [ ] The layout does not break when all panels are closed or when only
  one panel is open.
