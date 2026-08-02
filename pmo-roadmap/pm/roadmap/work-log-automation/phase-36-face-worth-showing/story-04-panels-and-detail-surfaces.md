# WLA-36-04 - Panels and detail surfaces

- **Project:** work-log-automation
- **Phase:** 36
- **Status:** backlog
- **Depends on:** WLA-36-01
- **Unblocks:** WLA-36-05
- **Owner:** unassigned

## Problem

Runs, live view, session stream, memory pane, decision timeline, outcomes, insights, editor, terminal, and Program Studio all inherit the scaffold look: mono body text, inconsistent chips, unaligned key-value rows, and raw hash dumps.

## Scope

- **In:** Every non-board surface restyled on the story-01 tokens: panel headers with title hierarchy, key-value grids that actually align, tables with quiet row borders, the memory pane and decision timeline as showcase surfaces (provenance cards on translucent surfaces, honest authority labels as designed badges), terminal and code kept mono INSIDE designed frames, hashes as quiet mono chips with the existing copy affordance.
- **Out:** New features; route or API changes.

## Acceptance criteria

- [ ] Every panel opens with a consistent header pattern (title 510, quiet meta line, actions right-aligned on the grid).
- [ ] Key-value and fact rows align on a shared grid across all panels; no ragged label columns remain.
- [ ] The memory pane and decision timeline read as flagship surfaces: card anatomy from story 03, authority labels as designed badges (mechanical vs judgment visually distinct), match reasons as quiet chips.
- [ ] Terminal, transcripts, code, and diffs stay monospace inside designed frames; all other panel text uses the UI type scale.
- [ ] Live/SSE status, folds, toasts, dialogs, and skeletons restyle onto the token system with reduced-motion respected.
- [ ] Browser exam, accessibility contract, and language lint green at both viewports and themes.

## Test plan

- **Unit:** covered by the verification command below.
- **Integration:** `bash pmo-roadmap/tests/workbench-ui-smoke.sh`
- **Manual / device:** operator reviews rendered screenshots before the story flips done.

## Notes / open questions

Reuse the dw-* components; restyle them once at the component level wherever possible instead of per-surface overrides.
