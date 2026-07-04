# WLA-15-01 - Design and the belt panel

- **Project:** work-log-automation
- **Phase:** 15
- **Status:** ready
- **Depends on:** Phase 13 (the feed/sessions/events substrate),
  Phase 14 (the message-layer patterns to echo where useful).
- **Unblocks:** WLA-15-02, WLA-15-03.
- **Owner:** unassigned

## Problem

Mission control renders on three surfaces — the CLI, the phone, and
the HoldSpeak Desk — but not on the workbench's own local browser
(`dw-workbench`, `dw_pmo/workbench.py`), which is where a developer
already sits to read the roadmap. The belt should be there too. And
it belongs there in its simplest form: the web view is read-only by
charter (it never stages or commits), so mission control here is the
picture without the hands. No approval taps, no arming, no steering —
just the live belt at your desk, which is exactly the surface where
steering would be wrong anyway.

## Scope

- **In:** A mission-control panel in the `dw-workbench` server: a
  new read-only route (e.g. `/missioncontrol`) and a belt view that
  consumes the same three documents every other client does — via
  the in-process API (`dw_pmo.statefeed`, `.sessions`, `.events`),
  not by re-parsing `pm/roadmap`. Phases render as the belt, the
  current phase's stories as the items, the next actionable story
  distinct, warnings visible. Served on localhost only, like the
  rest of the workbench. The design (a short section in
  `docs/mission-control.md` or a workbench note) pins: the route,
  the read-only stance (no write path reachable from this panel,
  proven by a test), and the refresh model (§below).
- **Out:** Any steering — flips, arming, file sends (those live on
  the phone and Desk where the consent machinery is). No new schema;
  this is a fourth consumer of the frozen feed.

## Acceptance criteria

- [ ] The workbench serves a read-only mission-control belt for the
  repo it is rooted at, built from the feed — phases, stories, next
  actionable, warnings.
- [ ] The panel has no reachable write path: a test asserts the
  route set exposes no mutation (the workbench's guarded-edit flow
  is separate and unchanged).
- [ ] It matches the workbench's existing visual language (reuse its
  CSS/tokens, not a bolt-on).
- [ ] Workbench-explorer tests and docs-lint pass.

## Test plan

- **Unit:** the panel's render from a feed fixture; the
  no-write-path assertion.
- **Integration:** `pmo-roadmap/tests/workbench-explorer.sh` (or its
  smoke) exercises the new route.
- **Manual / device:** a screenshot of the belt in the local
  browser, under evidence `assets/`.

## Notes / open questions

- Refresh model: the workbench is server-rendered; decide between a
  meta-refresh, a small poll (the ccgram single-flight pattern), or
  an SSE tick. Cheapest honest option first.
