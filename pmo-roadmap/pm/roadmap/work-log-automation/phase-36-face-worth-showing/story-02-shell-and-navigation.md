# WLA-36-02 - Shell and navigation

- **Project:** work-log-automation
- **Phase:** 36
- **Status:** backlog
- **Depends on:** WLA-36-01
- **Unblocks:** WLA-36-03, WLA-36-04
- **Owner:** unassigned

## Problem

The topbar is seven unrelated widgets on no grid: a logo that looks text-selected, duplicate breadcrumbs ('Project: sample' AND 'work / sample'), a floating yellow 'Needs you', a naked 'Comfortable' button, a timestamp, and an oversized refresh button. The needs-you dropdown is an unstyled popover.

## Scope

- **In:** A designed application shell: one aligned header on panel-dark with the Linear nav pattern (wordmark, quiet 510-weight nav links, ONE project/breadcrumb affordance, needs-you as a proper pill with count, density+refresh demoted to quiet icon/ghost buttons, command-palette hint), a designed needs-you popover (elevated surface, layered shadow stack, real list rows), a footer reduced to a single quiet status line, and the command palette restyled as the signature Linear surface.
- **Out:** Board/panel content (stories 03-04).

## Acceptance criteria

- [ ] Every topbar element sits on one baseline grid with consistent heights, gaps, and paddings; nothing looks selected, floats, or duplicates another element's meaning.
- [ ] Project identity appears exactly once in the header; navigation links use the 510-weight quiet style with a clear active state.
- [ ] Needs-you is a designed pill + popover: elevated surface, border tier, shadow stack, aligned rows with title/meta hierarchy, keyboard and screen-reader behavior preserved.
- [ ] The command palette matches the reference pattern (elevated surface, 12px radius, layered shadow, 16px input, 13px/510 results, 12px metadata).
- [ ] The footer is one quiet single-line status bar; the served-from path moves behind a fold or title attribute.
- [ ] Browser exam, accessibility contract, and language lint green at both viewports and themes.

## Test plan

- **Unit:** covered by the verification command below.
- **Integration:** `bash pmo-roadmap/tests/workbench-ui-smoke.sh`
- **Manual / device:** operator reviews rendered screenshots before the story flips done.

## Notes / open questions

Do not add navigation entries; the two-primary/five-advanced inventory is pinned by tests and stays.
