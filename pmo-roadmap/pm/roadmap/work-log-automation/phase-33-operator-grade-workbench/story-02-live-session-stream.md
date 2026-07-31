# WLA-33-02 - Live session stream

- **Project:** work-log-automation
- **Phase:** 33
- **Status:** backlog
- **Depends on:** WLA-33-01
- **Unblocks:** WLA-33-03, WLA-33-09
- **Owner:** unassigned

## Problem

When an agent is working a story, the only way to watch it is in the
terminal where it runs. The workbench shows story status but not what
the agent is doing right now. Operator streams tool calls, edits, and
questions in real time inside the workspace — you see the work happen.

## Scope

- **In:** Add a session panel that opens when clicking a story card.
  The panel streams live agent activity via the existing SSE adapter:
  tool calls, file edits, questions waiting for input, and evidence
  captures. Show which agent is on which story (from the sessions
  endpoint). Display a transcript of the session with timestamps and
  collapsible tool-call detail. When no agent is active on a story,
  show the story's evidence and last activity instead.
- **Out:** A generic terminal (that's WLA-33-04). Sending input to the
  agent from the browser (the session binding from mission control
  handles that separately). Changes to the SSE adapter or event schema.

## Localization hints

- **Affected files:**
  - `pmo-roadmap/workbench/app.js` (new session-panel module)
  - `pmo-roadmap/workbench/style.css`
  - `pmo-roadmap/lib/dw_pmo/workbench.py` (session-list route if needed)
  - `pmo-roadmap/tests/workbench-ui-smoke.sh`

## Acceptance criteria

- [ ] Clicking a story card on the board opens a session panel alongside
  the board (side-by-side, not a modal).
- [ ] When an agent session is active on the story, tool calls and file
  edits stream into the panel in real time.
- [ ] Questions waiting for input are visually distinct (highlighted,
  with a "needs you" indicator on the board card).
- [ ] When no agent is active, the panel shows the story body, evidence
  summary, and last captured run.
- [ ] The panel can be closed without losing board state.
- [ ] A 10-minute streaming session does not degrade browser performance
  (evidence: memory stable within 20% of baseline).
