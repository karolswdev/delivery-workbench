# Phase 33 - Operator-grade workbench

**Last updated:** 2026-07-31.

## Goal

Rebuild the web view from a document browser into a workspace you actually
want open all day — the way Operator makes parallel agent sessions feel
like one calm desk. Kanban home, live session streams, diff review, cost
and progress insights, an integrated terminal, and a control surface that
hides the cockpit until you ask for it. Keep DW's evidence-first integrity
underneath: every mutation still goes through preview, exact token, apply.

## Why now

Phase 32 made the workbench readable and gave it a design language, but it
is still fundamentally a text-heavy document viewer with buttons. Operator
showed what a workspace for agent-driven work looks like: dense, live,
and focused on the work — not on the tool. DW has the engine; it needs
the cockpit to match. A newcomer should install, open the browser, and
feel like they can drive.

## The promise

A person opens the workbench and sees a workspace, not a wall of text.
Their stories are cards on a board. Clicking one opens a live session view
where they can watch an agent work, see its tool calls, review the diff,
and merge — without leaving the browser. A sidebar shows what things cost
and what shipped. A terminal is a keypress away. The advanced machinery
(orchestration scores, programs, grants) stays one fold away, not in
the face.

## Hard constraint

The browser stays a client of the canonical preview/apply functions —
never a scheduler. No start-on-open, no auto-tick from SSE, no generic
certify/commit controls, no capability or budget elevation at runtime,
no `--no-verify` anywhere. The UI redesign changes layout, density, and
interaction — never the authority model.

## Scope

- **In:** `pmo-roadmap/workbench/` (app.js, style.css, index.html),
  `pmo-roadmap/lib/dw_pmo/workbench.py` (routes, API surface),
  navigation and layout architecture, workspace-style multi-panel views,
  live session streaming, diff rendering, terminal embedding, insights
  computation, progressive disclosure of advanced features, and the test
  surfaces that prove it.
- **Out:** new authority or mutation kinds, hosted/multi-user deployment
  and authentication, WebSocket or message-bus transport rework,
  driver/credential management, changes to gate/contract/grant semantics,
  the orchestration and program engines themselves.

## Exit criteria (evidence required)

- [ ] A component library and design system exists, with a framework decision recorded, and the existing board migrated to new components with no regression (WLA-33-00).
- [ ] The workbench opens to a workspace layout: a kanban board of stories with status columns, drag-to-move, and inline create — not a text page with a board link (WLA-33-01).
- [ ] Clicking a story card opens a session panel showing the live agent transcript — tool calls, edits, questions — streamed in real time via SSE (WLA-33-02).
- [ ] The session panel includes a diff review view: side-by-side or unified changes with accept/reject controls that ride the existing preview/apply boundary (WLA-33-03).
- [ ] An integrated terminal panel is available per-project, providing a real shell session inside the workspace without leaving the browser (WLA-33-04).
- [ ] A services/processes drawer shows managed dev/test processes with live log tailing and status indicators (WLA-33-05).
- [ ] An insights panel shows per-project and per-story cost, tokens used, evidence captured, and stories shipped — computed locally, no external telemetry (WLA-33-06).
- [ ] Advanced features (orchestration, programs, grants, scores) are accessible from a discoverable but non-default path — not in the main navigation, but reachable in one click from the workspace (WLA-33-07).
- [ ] The layout is dense and multi-panel: session transcript, diff, terminal, and insights can coexist on screen without modal takeovers, adapting to viewport width (WLA-33-08).
- [ ] The full UI smoke, accessibility, and language-lint suites pass on the new layout, with wide and 390px screenshot coverage in both themes (WLA-33-09).

## Story status

| ID | Story | Status | Story file | Evidence |
|---|---|---|---|---|
| WLA-33-00 | Design system and component foundation | done | [story-00-design-system](./story-00-design-system.md) | [evidence-story-00](./evidence-story-00.md) |
| WLA-33-01 | Workspace home | done | [story-01-workspace-home](./story-01-workspace-home.md) | [evidence-story-01](./evidence-story-01.md) |
| WLA-33-02 | Live session stream | done | [story-02-live-session-stream](./story-02-live-session-stream.md) | [evidence-story-02](./evidence-story-02.md) |
| WLA-33-03 | Diff review panel | done | [story-03-diff-review-panel](./story-03-diff-review-panel.md) | [evidence-story-03](./evidence-story-03.md) |
| WLA-33-04 | Integrated terminal | done | [story-04-integrated-terminal](./story-04-integrated-terminal.md) | [evidence-story-04](./evidence-story-04.md) |
| WLA-33-05 | Services drawer | done | [story-05-services-drawer](./story-05-services-drawer.md) | [evidence-story-05](./evidence-story-05.md) |
| WLA-33-06 | Insights dashboard | done | [story-06-insights-dashboard](./story-06-insights-dashboard.md) | [evidence-story-06](./evidence-story-06.md) |
| WLA-33-07 | Progressive disclosure | done | [story-07-progressive-disclosure](./story-07-progressive-disclosure.md) | [evidence-story-07](./evidence-story-07.md) |
| WLA-33-08 | Multi-panel layout | done | [story-08-multi-panel-layout](./story-08-multi-panel-layout.md) | [evidence-story-08](./evidence-story-08.md) |
| WLA-33-09 | Prove it works and looks right | done | [story-09-prove-it-works](./story-09-prove-it-works.md) | [evidence-story-09](./evidence-story-09.md) |

## Sequencing

Design system first: WLA-33-00 (components, framework, interaction
primitives, layout grid) is the foundation everything else builds on.
Then the workspace shell: WLA-33-01 (board as home) and WLA-33-08
(multi-panel layout engine). Then the live-work core: WLA-33-02
(session stream) and WLA-33-03 (diff review) — the heart of the
Operator feel. Then the supporting panels: WLA-33-04 (terminal),
WLA-33-05 (services), WLA-33-06 (insights). WLA-33-07 (progressive
disclosure) sweeps the advanced features into their fold. WLA-33-09
closes the phase as the exam.

## Where we are

Phase scaffolded 2026-07-31 with nine stories. Ready for implementation.

## Active risks

| Risk | Likelihood | Mitigation | Stop signal |
|---|---|---|---|
| Monolithic app.js (5K lines) resists incremental panel additions | high | WLA-33-01 splits into a module-per-panel structure before adding new panels | A story cannot add its panel without rewriting unrelated views |
| Live session streaming adds latency or memory pressure | medium | SSE adapter already exists from Phase 25; reuse it; cap buffer size; evidence must show a 30-minute session without degradation | Memory grows unbounded during a tailing session |
| Terminal-in-browser requires a PTY server the workbench doesn't have | high | Scope WLA-33-04 to a new lightweight PTY route in workbench.py using the stdlib pty module; fallback is a command-runner panel (not a full shell) | The PTY server cannot be made safe within the workbench's authority model |
| Diff rendering at scale (large files, many changes) | medium | Use a line-level diff with truncation; no syntax highlighting in v1 | Diff panel freezes on a 5000-line change |
| Simplification quietly weakens an authority boundary | low | Hard constraint above; every mutation keeps preview/token/apply; WLA-33-09 re-runs the permission-model tests | Any test or review finds a mutation reachable without a fresh exact token |

## Decisions made (this phase)

- 2026-07-31 - Phase scaffolded with `dw phase create` - keeps roadmap structure consistent - CLI.
- 2026-07-31 - The reference point is Operator (iishyfishyy/operator-oss): workspace-style multi-panel layout, live session visibility, diff review, insights, integrated terminal — adapted to DW's evidence-first model - operator.
- 2026-07-31 - The authority model (grants, tokens, exclusions) is untouched; the UI redesign changes layout, density, and interaction only - operator.

## Decisions deferred

- Whether the terminal is a full PTY or a command-runner panel — decide in WLA-33-04 based on what the authority model allows.
- Whether to migrate from vanilla JS to a framework (Preact, Lit) — decide in WLA-33-01 based on whether the module split is sufficient.
- Whether insights include token-level cost estimation or just story/evidence counts — decide in WLA-33-06 based on what data the CLI already exposes.
