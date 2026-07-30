# Phase 32 - One workbench

**Last updated:** 2026-07-29.

## Goal

Turn the web view into the all-in-one front door: a kanban home, plain words everywhere, guided ideation from rough idea to phase plan, automation you can declare and consent to in readable terms, mission control for autonomous work, and a design worth showing.

## Why now

The workbench already does a lot — board, guarded roadmap edits, run and program control rooms, Program Studio — but it reads like the inside of the machine, not like a product. Seven jargon-labelled navigation entries, authority details buried under folds, an ideation flow that hands back to the terminal halfway, and a visual layer nobody would screenshot with pride. v1.15.0 proved the engine on film; this phase makes the cockpit worthy of it.

## The promise

A person who has never read the docs opens the workbench and can, without learning a single internal term: see their project as a board and move work on it, turn a rough idea into a drafted phase plan, declare a team and an automation policy in plain words, grant a clearly-worded permission, watch autonomous work live, and stop it with one obvious control. Every exact detail stays one "Technical details" fold away. Nothing gains new authority: every mutation keeps its existing preview → exact token → apply boundary.

## Hard constraint

The browser stays a client of the canonical preview/apply functions — never a scheduler. No start-on-open, no auto-tick from SSE, no generic certify/commit controls, no capability or budget elevation at runtime, no `--no-verify` anywhere. Simplification changes wording, layout, and flow — never the authority model.

## Scope

- **In:** `pmo-roadmap/workbench/` (app.js, style.css, index.html), `pmo-roadmap/lib/dw_pmo/workbench.py` (routes, wording, the `/api/runs/start` schema fix, a preview-bound bounded-run supervise contract), navigation and information architecture, product-language enforcement, board upgrades (including wiring the existing pause/resume phase mutations), the in-browser ideation flow over the existing setup preview/apply routes, Program Studio task-shaped simplification, start-consent panels, a unified live-work view, and the smoke/accessibility/language test surfaces that prove it all.
- **Out:** any new authority or capability (no new mutation kinds beyond what the core already exposes), hosted/multi-user deployment and authentication, WebSocket or message-bus transport rework, driver/credential management UI, a generic terminal, rubric *engine* changes (readable display only), and changes to gate, contract, or grant semantics.

## Exit criteria (evidence required)

- [ ] A design-token layer exists and every route renders through it, proven by the refreshed wide + 390px screenshot matrix (WLA-32-01).
- [ ] The navigation is at most five plain-language destinations with a working project selector, and no product-language-contract technical term appears outside a Technical details fold on the ordinary panels (WLA-32-02, WLA-32-08).
- [ ] The board is the home route and supports create, move, park-with-reason, and phase pause/resume without leaving it (WLA-32-03).
- [ ] A rough idea can become a previewed, applied phase plan entirely in the browser through the existing setup preview/apply boundary (WLA-32-04).
- [ ] Program Studio leads with task-shaped plain-language forms; graph and JSON live under Technical details (WLA-32-05).
- [ ] Run and program start panels present capabilities, budgets, expiry, stop conditions, push destination, and permanent exclusions as headline consent material, and `/api/runs/start` accepts the standing-nudge fields it reads (WLA-32-06).
- [ ] One live-work view lists every run and program with its next step, outstanding decisions, and visually distinct pause/revoke/cancel controls, including finite preview-bound supervision for bounded runs (WLA-32-07).
- [ ] The UI smoke, accessibility, and new language-lint suites pass and are captured as evidence (WLA-32-08).

## Story status

| ID | Story | Status | Story file | Evidence |
|---|---|---|---|---|
| WLA-32-01 | One calm design language | done | [story-01-design-language](./story-01-design-language.md) | [evidence-story-01](./evidence-story-01.md) |
| WLA-32-02 | A front door in plain words | done | [story-02-plain-front-door](./story-02-plain-front-door.md) | [evidence-story-02](./evidence-story-02.md) |
| WLA-32-03 | The board runs the project | done | [story-03-board-runs-the-project](./story-03-board-runs-the-project.md) | [evidence-story-03](./evidence-story-03.md) |
| WLA-32-04 | From rough idea to phase plan | done | [story-04-idea-to-phase-plan](./story-04-idea-to-phase-plan.md) | [evidence-story-04](./evidence-story-04.md) |
| WLA-32-05 | Declare automation in plain words | done | [story-05-declare-automation-plainly](./story-05-declare-automation-plainly.md) | [evidence-story-05](./evidence-story-05.md) |
| WLA-32-06 | Consent you can read | done | [story-06-consent-you-can-read](./story-06-consent-you-can-read.md) | [evidence-story-06](./evidence-story-06.md) |
| WLA-32-07 | Mission control for live work | done | [story-07-mission-control-live-work](./story-07-mission-control-live-work.md) | [evidence-story-07](./evidence-story-07.md) |
| WLA-32-08 | Prove it reads and looks right | backlog | [story-08-prove-it-reads-and-looks-right](./story-08-prove-it-reads-and-looks-right.md) | - |

## Sequencing

Foundation first: WLA-32-01 (design tokens) and WLA-32-02 (information architecture) set the visual and verbal frame every later story renders inside. Then the two everyday pillars, WLA-32-03 (board) and WLA-32-04 (ideation). Then the autonomy arc: WLA-32-05 (declare), WLA-32-06 (consent), WLA-32-07 (watch and steer). WLA-32-08 closes the phase as the exam over everything.

## Where we are

Phase scaffolded 2026-07-29 from four grounding surveys: the web-layer map (routes, seams, jargon inventory), the full CLI/MCP capability surface and its web gaps, the phase-authoring conventions, and a deep-dive of the runs/programs execution layer with its safety rails. All eight stories are backlog; WLA-32-01 is first up. No blockers.

## Active risks

| Risk | Likelihood | Mitigation | Stop signal |
|---|---|---|---|
| Simplification quietly weakens an authority boundary | low | Hard constraint above; every mutation keeps preview → exact token → apply; WLA-32-08 re-runs the permission-model tests | Any test or review finds a mutation reachable without a fresh exact token |
| app.js (5,077 lines) becomes unmaintainable mid-rewrite | medium | Stories restyle and reorganize views incrementally; no big-bang rewrite; each story leaves the suite green | A story cannot land without touching more than its named views |
| Plain wording drifts from what the system actually does | medium | Wording changes must map 1:1 to the product-language contract; exact terms stay under Technical details, never deleted | A label describes an action the underlying command does not perform |
| Screenshot/accessibility suites silently skip (no Firefox) | medium | WLA-32-08 evidence must show the browser-dependent paths actually ran | Evidence contains a skip marker for the rendering exam |

## Decisions made (this phase)

- 2026-07-29 - Phase scaffolded with `dw phase create` / `dw story create` - keeps roadmap structure consistent - CLI.
- 2026-07-29 - The phase changes wording, layout, and flow only; the authority model (grants, tokens, exclusions) is untouched - simplification must not become a security regression - operator.
- 2026-07-29 - Board becomes the home route; the current overview content moves into it or one fold below it - the board is the view users actually think in - operator.

## Decisions deferred

- Whether bounded-run supervision gets a web contract or stays CLI-only - decide in WLA-32-07 planning - default is a finite, preview-bound web contract mirroring program supervision.
- Whether a rubric Studio family is added or rubrics stay read-only in the browser - decide in WLA-32-05 - default is readable display only, authoring stays in files.
- SSE fan-out efficiency (shared ledger watcher instead of per-subscriber replay) - trigger if live views feel slow with several open tabs - default is keep the current adapter.
