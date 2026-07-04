# Phase 15 - Mission control on the workbench

**Last updated:** 2026-07-04.

## Goal

The local dw-workbench browser grows a mission-control belt: the same feed, correlation, and events the phone and Desk render, now in the read-only roadmap view — no steering (that stays where the consent machinery lives), just the live picture at your desk.

## Scope

- **In:** A read-only mission-control belt in the local `dw-workbench`
  browser — the fourth consumer of the frozen feed/sessions/events,
  built from the in-process API, never re-parsing the roadmap.
  Phases as the belt, stories as items, live session correlations and
  a gate-refusal event ticker, matching the workbench's own visual
  language. Localhost only. A read-only fitness guard proves no write
  path is reachable from the panel.
- **Out:** Any steering (flips, arming, file sends stay on the phone
  and Desk, where the consent machinery lives); any new schema.

## Exit criteria (evidence required)

- [ ] The workbench serves the belt read-only, built from the feed,
  matching its own styling (WLA-15-01).
- [ ] Sessions pinned and a gate-refusal event ticker render live,
  refresh without a full reload (WLA-15-02).
- [ ] A no-write-path guard fails on a planted mutation and passes on
  the real tree, in CI; a live-browser screenshot in evidence
  (WLA-15-03).

## Story status

| ID | Story | Status | Story file | Evidence |
|---|---|---|---|---|
| WLA-15-01 | Design and the belt panel | done | [story-01-design-and-the-belt-panel](./story-01-design-and-the-belt-panel.md) | [evidence-story-01](./evidence-story-01.md) |
| WLA-15-02 | Sessions and events, live in the browser | done | [story-02-sessions-and-events-live-in-the-browser](./story-02-sessions-and-events-live-in-the-browser.md) | [evidence-story-02](./evidence-story-02.md) |
| WLA-15-03 | Prove it read-only, end to end | backlog | [story-03-prove-it-read-only-end-to-end](./story-03-prove-it-read-only-end-to-end.md) | - |

## Where we are

This phase has been scaffolded and is ready for story planning.

## Active risks

| Risk | Likelihood | Mitigation | Stop signal |
|---|---|---|---|
| Scope is underspecified | medium | Add concrete stories before implementation | A story cannot name testable acceptance criteria |

## Decisions made (this phase)

- 2026-07-04 - Phase scaffolded with `dw phase create` - keeps roadmap structure consistent - CLI.

## Decisions deferred

- Detailed story breakdown - trigger before implementation begins - default is no code changes without stories.
