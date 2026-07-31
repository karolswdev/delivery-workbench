# WLA-33-07 - Progressive disclosure

- **Project:** work-log-automation
- **Phase:** 33
- **Status:** backlog
- **Depends on:** WLA-33-00, WLA-33-01
- **Unblocks:** WLA-33-09
- **Owner:** unassigned

## Problem

The workbench shows everything at once: orchestration scores, program
studios, run control rooms, grants, bounded-run supervision, rubric
policies. A newcomer hits a cockpit when they need a steering wheel.
Operator keeps the primary interface focused on the work and puts
configuration and advanced features behind discoverable but non-default
paths.

## Scope

- **In:** Reorganize the navigation so the default workspace contains
  only: the board, session/diff panels, terminal, services, and
  insights. The advanced features (orchestration editor, program studio,
  run/program control rooms, rubric display) move behind a single
  "Advanced" or "Automation" entry point — still reachable in one click,
  but not cluttering the main navigation. The existing Phase 32
  "Technical details" fold pattern continues for advanced detail within
  any panel. Ensure no functionality is removed — everything is still
  accessible, just not in the face.
- **Out:** Removing any existing feature. Changing what the advanced
  features do. Adding new advanced features. Changing the authority
  model.

## Localization hints

- **Affected files:**
  - `pmo-roadmap/workbench/app.js` (navigation restructure)
  - `pmo-roadmap/workbench/style.css`
  - `pmo-roadmap/tests/workbench-explorer.sh`
  - `pmo-roadmap/tests/workbench-accessibility.py`

## Acceptance criteria

- [ ] The main workspace navigation has at most five entries, none of
  which mention orchestration, programs, grants, or scores.
- [ ] All advanced features are reachable from the workspace in at most
  two clicks.
- [ ] No feature is removed — every route that existed before still
  exists and functions.
- [ ] A first-time user can reach the board, open a story, and see the
  terminal without encountering any advanced terminology.
- [ ] The advanced entry point has a discoverable visual indicator
  (icon, label, or both) that communicates "more tools here" without
  requiring documentation.
