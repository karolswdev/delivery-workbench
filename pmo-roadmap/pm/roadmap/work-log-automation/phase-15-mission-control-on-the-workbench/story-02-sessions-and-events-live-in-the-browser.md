# WLA-15-02 - Sessions and events, live in the browser

- **Project:** work-log-automation
- **Phase:** 15
- **Status:** backlog
- **Depends on:** WLA-15-01.
- **Unblocks:** WLA-15-03.
- **Owner:** unassigned

## Problem

The belt without the live layer is the roadmap you already have. The
correlation document says which agent is on which story and whether
it is blocked; the event log narrates the rails with gate verdicts
and rule ids. Rendering both in the workbench turns a static roadmap
page into the same mission control the phone and Desk show — at the
desk, in the browser already open.

## Scope

- **In:** The panel gains the live layer: `dw sessions` correlations
  pinned to their story rows (on_story loudest when awaiting a
  human, the honest buckets otherwise, stale marked not dropped),
  and a `dw events` ticker with `gate_refusal` first-class carrying
  its rule id verbatim. Read-only, localhost, content-free per the
  §3 consent stance (no transcript content — the events already
  carry none).
- **Out:** Steering of any kind.

## Acceptance criteria

- [ ] Sessions render pinned per correlation outcome; awaiting is the
  loudest signal; stale is visible.
- [ ] An events ticker renders with a `gate_refusal` and its rule id.
- [ ] The refresh model from 15-01 keeps the layer live without a
  full page reload thrash (single-flight or SSE, decided in 01).

## Test plan

- **Unit:** session pinning and event rendering from fixtures.
- **Integration:** the workbench smoke exercises the live routes.
- **Manual / device:** rides WLA-15-03.
