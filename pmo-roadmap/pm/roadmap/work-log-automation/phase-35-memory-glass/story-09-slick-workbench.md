# WLA-35-09 - Slick workbench

- **Project:** work-log-automation
- **Phase:** 35
- **Status:** backlog
- **Depends on:** WLA-35-06, WLA-35-07, WLA-35-08
- **Unblocks:** WLA-35-10
- **Owner:** unassigned

## Problem

The memory surfaces deserve a workbench that feels fast and considered everywhere: perceived latency, density, transitions, reconnect feedback, narrow-screen readability, and dark-mode quality — improving the vanilla JS/CSS architecture, not replacing it.

## Scope

- **In:** Skeleton-first route rendering; shared CSS transition tokens honoring `prefers-reduced-motion`; compact/comfortable density settings; reconnect state announcements; dark-mode journeys over the new surfaces; bounded layouts and copy actions for long hashes.
- **Out:** Frameworks, build tools, CSS libraries, WebSockets — the stack stays vanilla and dependency-free.

## Acceptance criteria

- [ ] Normal routes render a stable shell and `dw-skeleton` state immediately, then fill panels incrementally; the non-snapshot application path contains no synchronous XHR.
- [ ] Short panel, route, and disclosure transitions use shared CSS tokens; `prefers-reduced-motion: reduce` disables every nonessential transition and animation.
- [ ] Compact and comfortable density settings persist in local storage; both modes preserve keyboard order, minimum target sizes, and readable memory provenance at 390px.
- [ ] Dark-mode browser journeys cover the Memory pane, decision timeline, needs-you state, focus rings, status pills, skeletons, empty states, and error states at wide and narrow viewports.
- [ ] Global SSE reconnects announce disconnected, retrying, caught-up, and restored states; a 503 subscriber-cap response shows retry guidance instead of leaving the workspace silently stale.
- [ ] Long hashes and receipt IDs have bounded layouts and copy actions; form errors use `aria-describedby`; no page develops horizontal body scrolling.

## Test plan

- **Unit:** covered by the verification command below.
- **Integration:** `bash pmo-roadmap/tests/workbench-ui-smoke.sh`
- **Manual / device:** n/a unless named in the acceptance criteria.

## Notes / open questions

Judge weak spots from the actual code; keep light default + dark `prefers-color-scheme` override intact (two core tests pin it).
