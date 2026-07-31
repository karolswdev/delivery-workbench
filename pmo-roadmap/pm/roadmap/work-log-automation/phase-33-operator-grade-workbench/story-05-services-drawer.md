# WLA-33-05 - Services drawer

- **Project:** work-log-automation
- **Phase:** 33
- **Status:** backlog
- **Depends on:** WLA-33-00, WLA-33-04
- **Unblocks:** WLA-33-09
- **Owner:** unassigned

## Problem

When an agent starts a dev server, runs a test watcher, or kicks off a
build, those processes are invisible in the workbench. You have to find
the terminal tab where they're running. Operator shows a services drawer
with live logs, status, and restart controls for managed processes.

## Scope

- **In:** Add a services/processes drawer to the workspace. The workbench
  server tracks child processes started through `dw evidence capture` or
  the terminal panel, showing their name, PID, status (running/stopped/
  errored), and live log output. The drawer supports start/stop/restart
  for known service processes. Port assignments are visible. The drawer
  is collapsible and does not take over the workspace.
- **Out:** Process orchestration or supervision beyond what already runs.
  Docker/container management. Automatic process discovery outside of
  dw-managed commands. Remote process management.

## Localization hints

- **Affected files:**
  - `pmo-roadmap/workbench/app.js` (new services-drawer module)
  - `pmo-roadmap/workbench/style.css`
  - `pmo-roadmap/lib/dw_pmo/workbench.py` (process tracking route)
  - `pmo-roadmap/tests/workbench-ui-smoke.sh`

## Acceptance criteria

- [ ] A services drawer is accessible from the workspace showing all
  tracked processes with name, status, and port.
- [ ] Live log output from a running process streams into the drawer.
- [ ] Stop and restart controls work for tracked processes.
- [ ] The drawer is collapsible and does not interfere with the board
  or session panels.
- [ ] A process that exits is shown as stopped with its exit code.
