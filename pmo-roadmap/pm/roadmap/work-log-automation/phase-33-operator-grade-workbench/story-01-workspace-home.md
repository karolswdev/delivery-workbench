# WLA-33-01 - Workspace home

- **Project:** work-log-automation
- **Phase:** 33
- **Status:** backlog
- **Depends on:** none
- **Unblocks:** WLA-33-02, WLA-33-03, WLA-33-04, WLA-33-05, WLA-33-06, WLA-33-07, WLA-33-08
- **Owner:** unassigned

## Problem

The workbench opens to a text-heavy overview page. The board exists but
is a secondary route. A newcomer sees a wall of status lines, not a
workspace. Operator opens to a multi-project dashboard with live status
cards — the work is the first thing you see.

## Scope

- **In:** Restructure the workbench entry point as a workspace layout.
  The kanban board becomes the default view with status columns
  (Backlog / Ready / In progress / Blocked / Done), drag-to-move cards,
  inline story creation, and a project selector. Split `app.js` into a
  module-per-panel structure so subsequent stories can add panels without
  touching unrelated code. The overview briefing (verdict, next step,
  attention items) becomes a compact strip above the board, not a
  separate page.
- **Out:** New panels (session, diff, terminal, insights — those are
  later stories). New mutation kinds. Changes to the authority model.

## Localization hints

- **Affected files:**
  - `pmo-roadmap/workbench/app.js` (split into modules)
  - `pmo-roadmap/workbench/style.css`
  - `pmo-roadmap/workbench/index.html`
  - `pmo-roadmap/tests/workbench-ui-smoke.sh`
  - `pmo-roadmap/tests/workbench-explorer.sh`

## Acceptance criteria

- [ ] The workbench opens to a workspace layout with the kanban board as
  the primary content, not behind a navigation link.
- [ ] The briefing strip (verdict, next step, blockers) is visible above
  the board without scrolling.
- [ ] Stories can be created inline from a board lane.
- [ ] Drag-to-move and status changes go through preview/token/apply.
- [ ] `app.js` is split into at least four modules (board, panels,
  navigation, core) loadable independently.
- [ ] Wide and 390px screenshots in both themes pass visual review.
