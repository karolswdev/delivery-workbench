# Phase 36 - A face worth showing

**Last updated:** 2026-08-02.

## Goal

Replace the scaffold-grade visual layer with a Linear-grade design language, adopted token-for-token from the popular-web-designs reference: dark-native luminance model, a real type scale on a real grid, disciplined components, and zero misalignments — across every workbench surface, both themes, wide and narrow.

## Scope

- **In:** A Linear-grade design language adopted token-for-token from the owner-designated reference (`~/dev/hermes-agent/skills/creative/popular-web-designs/templates/linear.app.md`): dark-native luminance model, Inter-first type scale (400/510/590, cv01+ss03), 8px grid, translucent-white border tiers, single indigo accent; applied across shell, board, and every panel; closed by a measured alignment sweep with new mechanical guards.
- **Out:** Information-architecture changes, new features, new routes, runtime font fetching, dependencies, frameworks.

## Exit criteria (evidence required)

- [ ] Every UI surface renders on the token system — no ad hoc hex, mono only for code/hashes/terminal — enforced by a stylesheet fitness test.
- [ ] The operator has reviewed the full 352-render matrix of the redesigned UI and every found misalignment is fixed (evidence carries before/after shots).
- [ ] Dark-native default + Linear-light override both pass the full browser exam at 1440x900 and 390x844.
- [ ] Full core suite, packaged exams, accessibility contract, and language lint green; README screenshots regenerated.

## Story status

| ID | Story | Status | Story file | Evidence |
|---|---|---|---|---|
| WLA-36-01 | Design tokens and type | backlog | [story-01-design-tokens-and-type](./story-01-design-tokens-and-type.md) | - |
| WLA-36-02 | Shell and navigation | backlog | [story-02-shell-and-navigation](./story-02-shell-and-navigation.md) | - |
| WLA-36-03 | Board and cards | backlog | [story-03-board-and-cards](./story-03-board-and-cards.md) | - |
| WLA-36-04 | Panels and detail surfaces | backlog | [story-04-panels-and-detail-surfaces](./story-04-panels-and-detail-surfaces.md) | - |
| WLA-36-05 | Alignment sweep and visual exam | backlog | [story-05-alignment-sweep-and-visual-exam](./story-05-alignment-sweep-and-visual-exam.md) | - |

## Where we are

Phase opened 2026-08-02 on the owner's direct verdict: the UI layer is scaffold-grade (mono-everything, no grid, badge zoo, dashed empty states) and must be rebuilt to the standard of the designated reference. Stories planned; implementation not started.

## Active risks

| Risk | Likelihood | Mitigation | Stop signal |
|---|---|---|---|
| Scope is underspecified | medium | Add concrete stories before implementation | A story cannot name testable acceptance criteria |

## Decisions made (this phase)

- 2026-08-02 - Phase scaffolded with `dw phase create` - keeps roadmap structure consistent - CLI.
- 2026-08-02 - Design reference is Linear, adopted token-for-token from the owner-designated catalog (`popular-web-designs`); dev-dashboard guidance in the catalog concurs - owner directive.
- 2026-08-02 - Dark becomes the native default theme (Linear is dark-native; the owner's taste on record); light remains first-class as the prefers-color-scheme override; the two pinned color-scheme core tests flip DELIBERATELY in WLA-36-01 - design.
- 2026-08-02 - No runtime font fetching: Inter via local-font stack with system fallbacks; the workbench stays offline and dependency-free - constraint.

## Decisions deferred

- Detailed story breakdown - trigger before implementation begins - default is no code changes without stories.
