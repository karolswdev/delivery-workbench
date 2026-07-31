# WLA-33-06 - Insights dashboard

- **Project:** work-log-automation
- **Phase:** 33
- **Status:** backlog
- **Depends on:** WLA-33-00, WLA-33-01
- **Unblocks:** WLA-33-09
- **Owner:** unassigned

## Problem

There is no at-a-glance view of what the project cost, how much work
shipped, or what the agents have been doing over time. Operator shows
per-day spend, token usage, tasks shipped, and lines merged — all
computed locally without phoning home.

## Scope

- **In:** Add an insights panel to the workspace. Compute locally from
  data the CLI already has: stories shipped per phase, evidence captures
  with timestamps, lines changed (from git log), and commit history.
  Show a timeline of activity (stories completed, evidence captured),
  a breakdown by phase, and a summary strip (total stories, total
  commits, total evidence captures). If the events or sessions data
  includes token counts or cost estimates, surface those too. Filter
  by project and time range. All data stays local — no external
  telemetry, no network calls.
- **Out:** Token-level cost estimation if the data doesn't already exist
  in the CLI output (don't invent cost data). Real-time spend tracking
  (that would require agent-side instrumentation). External analytics
  integrations.

## Localization hints

- **Affected files:**
  - `pmo-roadmap/workbench/app.js` (new insights-panel module)
  - `pmo-roadmap/workbench/style.css`
  - `pmo-roadmap/lib/dw_pmo/workbench.py` (insights data route)
  - `pmo-roadmap/tests/workbench-ui-smoke.sh`

## Acceptance criteria

- [ ] An insights panel is accessible from the workspace toolbar.
- [ ] It shows stories shipped, evidence captures, and commit count
  over a selectable time range.
- [ ] A per-phase breakdown is visible.
- [ ] All data is derived from local git history and roadmap files —
  no network calls are made (evidence: no outbound requests during
  the insights render).
- [ ] The panel renders within 2 seconds on a repository with 200+
  commits.
