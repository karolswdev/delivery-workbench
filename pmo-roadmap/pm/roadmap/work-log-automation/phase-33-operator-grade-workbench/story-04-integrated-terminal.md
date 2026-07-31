# WLA-33-04 - Integrated terminal

- **Project:** work-log-automation
- **Phase:** 33
- **Status:** backlog
- **Depends on:** WLA-33-00, WLA-33-01
- **Unblocks:** WLA-33-09
- **Owner:** unassigned

## Problem

Running a command means switching to a separate terminal. Operator
embeds a real terminal in the workspace so you can run tests, inspect
files, or use the dw CLI without leaving the browser.

## Scope

- **In:** Add a terminal panel to the workspace. The workbench Python
  server gets a lightweight PTY route using the stdlib `pty` module,
  exposing a shell session scoped to the repository root. The browser
  panel connects via a WebSocket or chunked-transfer stream and renders
  a basic terminal (xterm.js or a minimal custom renderer). The terminal
  is per-project and persists across panel toggles within a session.
  Bound to localhost only — no remote shell exposure.
- **Out:** Full terminal emulation with color/cursor support in v1 (basic
  line-by-line output is acceptable). Remote access. Running commands on
  behalf of the user without their input. Any change to the authority
  model.

## Localization hints

- **Affected files:**
  - `pmo-roadmap/workbench/app.js` (new terminal-panel module)
  - `pmo-roadmap/workbench/style.css`
  - `pmo-roadmap/lib/dw_pmo/workbench.py` (PTY route)
  - `pmo-roadmap/tests/workbench-ui-smoke.sh`

## Acceptance criteria

- [ ] A terminal panel can be toggled open from the workspace with a
  keyboard shortcut and a button.
- [ ] The terminal provides a real shell session at the repo root.
- [ ] Commands typed in the terminal execute and their output renders
  in the panel.
- [ ] The terminal is bound to localhost only — evidence shows the PTY
  route rejects non-localhost connections.
- [ ] The terminal persists across panel toggles (closing and reopening
  does not lose the shell session).
- [ ] If a full PTY proves unsafe within the authority model, a
  command-runner fallback (predefined dw commands only) is acceptable —
  the decision is recorded here.
