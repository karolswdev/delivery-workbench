# WLA-35-06 - AgentGlass memory pane

- **Project:** work-log-automation
- **Phase:** 35
- **Status:** backlog
- **Depends on:** WLA-35-05
- **Unblocks:** WLA-35-07, WLA-35-09
- **Owner:** unassigned

## Problem

This is the glass pane: a Memory pane on live runs, programs, and sessions showing what the agent knew — compact summary first, then expandable provenance, freshness, match reasons, exclusions, and terminal writeback — using the existing custom elements and progressive-disclosure rules.

## Scope

- **In:** New `pmo-roadmap/workbench/memory-panel.js` loaded through the hash-routed shell; links from runs, session panel, outcomes panel, needs-you items, and the command palette; `.githooks/workbench/` payload kept in byte sync.
- **Out:** Decision timeline (WLA-35-07); global polish (WLA-35-09).

## Acceptance criteria

- [ ] `memory-panel.js` exists in the canonical workbench source and loads through the existing hash-routed application shell, with the `.githooks/workbench/` installed payload byte-synced.
- [ ] The pane is reachable from `runs.js`, `session-panel.js`, `outcomes-panel.js`, needs-you items, and the command palette, preserving current route and focus on open and close.
- [ ] The summary shows recall time, freshness, included and excluded counts, source mix, and writeback state; each memory card shows factual summary, confidence, why-recalled, source path or receipt, and supersession state.
- [ ] The pane distinguishes 'available to the agent', 'referenced by a decision', and 'written after completion', and never implies that mere recall caused or authorized an action.
- [ ] Stale, missing, tampered, and empty states have plain-language explanations with a technical-details fold carrying the typed refusal.
- [ ] Wide and 390px layouts remain keyboard navigable, screen-reader labelled, and stable in light and dark themes.

## Test plan

- **Unit:** covered by the verification command below.
- **Integration:** `/usr/bin/python3 pmo-roadmap/tests/workbench-accessibility-contract.py`
- **Manual / device:** n/a unless named in the acceptance criteria.

## Notes / open questions

Use the phase-33 design system (dw-card, dw-fold, dw-skeleton, dw-empty-state…). No new component system.
