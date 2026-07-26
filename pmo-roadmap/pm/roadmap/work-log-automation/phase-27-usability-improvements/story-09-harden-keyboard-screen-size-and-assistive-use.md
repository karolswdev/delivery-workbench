# WLA-27-09 - Harden keyboard, screen-size, and assistive use

- **Project:** work-log-automation
- **Phase:** 27
- **Status:** done
- **Depends on:** WLA-27-03, WLA-27-04, WLA-27-05, WLA-27-06, WLA-27-07
- **Unblocks:** WLA-27-10
- **Owner:** unassigned

## Problem

Plain words do not make a task usable if its controls require a pointer, its
structure is invisible to assistive technology, live updates steal focus, or
the decisive action disappears on a narrow screen. Accessibility and
responsive behavior must be part of the core journeys rather than closeout
polish.

This story hardens every redesigned task across input methods, viewport sizes,
semantic structure, focus, and live updates.

## Scope

- **In:** semantic headings/regions/lists/tables/forms; meaningful control
  names and descriptions; keyboard navigation and activation; visible focus;
  dialog/drawer focus management; status and error association; non-color-only
  state; live-update behavior; reduced-motion-safe transitions; zoom/narrow
  and wide layouts; long identifiers and translated plain-language copy;
  automated DOM/interaction assertions plus recorded manual review.
- **Out:** a visual rebrand, broad browser support beyond the repository's
  declared matrix, localization implementation, formal third-party
  certification, or unrelated legacy pages not touched by Phase 27 journeys.

## Acceptance criteria

- [x] Arrival, setup, plan authoring, team/review design, live progress,
  decision/recovery, stop/revoke, and technical-inspection journeys complete
  using only the keyboard with a visible and logical focus order.
- [x] Headings, regions, relationships, forms, errors, progress, blockers, and
  state changes have meaningful programmatic structure and labels; icon,
  position, motion, or color is never the only carrier of meaning.
- [x] Dialogs, drawers, menus, disclosures, and confirmations place and restore
  focus predictably, support dismissal where safe, and do not trap or discard
  in-progress input.
- [x] SSE/live refresh, replay, and background progress do not steal focus or
  flood announcements; material changes remain discoverable on demand.
- [x] Narrow and wide fixtures keep primary facts and safe actions visible
  without horizontal-page scrolling, overlap, clipping, or pointer-only
  affordances; long exact identifiers remain inspectable.
- [x] Automated semantic/keyboard/viewport checks and a recorded assistive-use
  review cover every canonical journey, with failures tied to the owning
  story/screen rather than waived at phase close.

## Test plan

- **Unit:** test focus helpers, disclosure state, live-update announcement
  rules, semantic labels, and layout-state classes.
- **Integration:** extend `pmo-roadmap/tests/workbench-ui-smoke.sh` and browser
  fixtures with keyboard, focus, semantic DOM, zoom/narrow, long-content, and
  live-refresh assertions.
- **Manual / device:** record keyboard-only and assistive-technology passes for
  every WLA-27-02 journey at representative narrow and wide viewports.

## Notes / open questions

Manual review findings are evidence, not permission to replace deterministic
checks with an undocumented "looks good." Any intentionally unsupported
interaction must have a reachable equivalent.

Implemented one keyboard, focus, semantic, live-update, and responsive contract
across all thirteen canonical journeys. Firefox Marionette now performs real
key actions and wide/narrow DOM audits; the exact screenshot harness retains
1440×900 and 390×844 proof. Reviews restore their exact opener, redraws
preserve focus, changed ledger heads are announced once, state is not
color-only, and long technical content wraps or scrolls inside its owner.
