# Evidence — WLA-33-01

## Summary

Workspace home delivered. The monolithic 6727-line `app.js` was split
into 12 independently loadable modules. The board remains the home view
with the briefing strip above, inline story creation, and guarded
drag-to-move — all now rendering through the WLA-33-00 component library.

## Module split

| Module | Lines | Content |
|---|---|---|
| `core.js` | 724 | DOM refs, utilities, focus management, API helpers, presentation catalog |
| `board.js` | 481 | Board cards, lanes, overview strip, drag/move/create/park flows |
| `views.js` | 433 | Project, phase, story, file, health, trace, worklog, mission control |
| `editor.js` | 1017 | Structured editor, adoption review, ideation flow |
| `orchestration.js` | ~700 | Orchestration score editor, design, validation |
| `runs.js` | ~1800 | Run/program control rooms, SSE live tails, bounded actions |
| `studio.js` | 1616 | Program Studio, delivery setup, plan/workflow/team editors |
| `app.js` | 100 | Router dispatch and DOM event wiring only |

Plus 4 utility modules from WLA-33-00: `components.js`, `interactions.js`,
`layout.js`, `design.js`.

**Load order:** components → interactions → layout → design → core → board →
views → editor → orchestration → runs → studio → app (router).

All functions remain globals for backward compatibility. No IIFE wrappers,
no build step, no framework dependency.

## Test results

Full core test suite passed with zero failures after the split.
All 12 JS files pass `node --check` syntax validation.
Zero duplicate function definitions across all modules.
