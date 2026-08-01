# Phase 34 - Multi-agent command center

**Last updated:** 2026-07-31.

## Goal

Close the human-agent interaction loop. DW has the governance substrate
(evidence, ledgers, authority rings, guarded mutations) but Operator
showed what immediacy looks like: a global attention router, per-turn
telemetry, inline ask-and-resume, fleet-wide visibility, and execution
that survives the browser. This phase brings Operator's interaction
density to DW without weakening its consent model.

## Why now

Phase 33 gave the workbench panels, components, and a multi-panel
layout. But the panels are presentation shells compared to what
Operator fills them with: durable transcripts, turn-level cost tracking,
a "Needs you" inbox that routes across projects, and an ask-answer
cycle that keeps the agent running while the human thinks. Three
independent deep analyses of Operator's codebase (commit 174820d8)
confirmed: DW already has the harder governance layer, but it doesn't
yet own the live runtime — execution is tick-driven and sequential,
there's no parallel worker supervisor, and the terminal/services/diff
panels need real backends.

## The promise

An operator opens the workbench and sees, without clicking anything:
how many agents need them, which project, which question, how long
it's been waiting. They click one, read the question in context of
the agent's transcript, answer it, and the agent resumes — all inside
the browser. A side panel shows what each session cost, which model
ran, cache hit rate, and whether the produced artifacts were accepted.
Closing the laptop changes nothing; reopening catches up instantly.
All of this layered on top of DW's existing evidence, certification,
and commit gates — not replacing them.

## Hard constraint

The browser remains a client of the canonical preview/apply functions —
never a scheduler. The ask-answer cycle goes through DW's existing
typed-request and decision-port machinery, not an unrestricted chat
box. SSE streams are read-only observations of ledger state. No new
mutation kind bypasses preview/token/apply. The SQLite analytics
layer is a disposable projection that can be rebuilt from the
authoritative Markdown roadmap and append-only ledger. Merge never
uses `--no-verify`.

## Scope

- **In:** Global always-on SSE event stream, orthogonal state model
  (roadmap/execution/attention/authority), "Needs you" inbox with
  browser notifications, inline typed ask-and-resume on existing
  request ports, reconnect-safe server-side execution, durable
  supervisor process for parallel agents, normalized streaming driver
  events, session-level telemetry projection (per-turn tokens/cache/
  cost in integer microunits), session-to-outcome links, command
  palette, revisioned reusable project context, agent-suggested task
  inbox, guarded diff review/merge flow through preview/token/apply,
  real PTY with authenticated WebSocket, actual service supervisor
  with process groups and crash backoff, and the test surfaces that
  prove it.
- **Out:** replacing the Markdown/ledger authority model with a
  database, adding unrestricted chat, multi-user authentication,
  hosted deployment, new grant or capability kinds, changes to the
  commit gate, cross-repository fleet view (deferred to a later phase
  pending a repo registry).

## Exit criteria (evidence required)

- [ ] A global always-on SSE stream delivers coarse lifecycle events for all active work — not per-view, fleet-wide (WLA-34-01).
- [ ] The workbench separates roadmap status, execution state, attention state, and required authority as four orthogonal axes (WLA-34-02).
- [ ] A "Needs you" inbox shows a global count, ordered oldest-first, with one-click jump and browser notification (WLA-34-03).
- [ ] An agent's typed request renders inline in the session transcript with answer controls; answering resumes the parked child and records the decision in the ledger (WLA-34-04).
- [ ] Execution continues server-side when the browser disconnects; reconnecting catches up via snapshot-then-tail without losing events (WLA-34-05).
- [ ] A session telemetry panel shows per-turn tokens, cache reads/writes, cost in microunits, resolved model, and measurement status — derived from the run ledger (WLA-34-06).
- [ ] Session-to-outcome links are queryable: which session produced which artifact, evidence, check result, and story transition (WLA-34-07).
- [ ] A command palette (Ctrl+K) jumps to any project, story, run, session, or waiting request (WLA-34-08).
- [ ] Revisioned reusable project context is hash-bound per session, with agent-draft and operator-accept lifecycle (WLA-34-09).
- [ ] Agent-suggested tasks appear in a suggestion inbox with provenance, and acceptance creates a roadmap story retaining the suggestion origin (WLA-34-10).
- [ ] The full test suite passes on the complete system (WLA-34-11).

## Story status

| ID | Story | Status | Story file | Evidence |
|---|---|---|---|---|
| WLA-34-01 | Global event stream | backlog | [story-01](./story-01-global-event-stream.md) | [evidence-story-01](./evidence-story-01.md) |
| WLA-34-02 | Orthogonal state model | backlog | [story-02](./story-02-orthogonal-state.md) | [evidence-story-02](./evidence-story-02.md) |
| WLA-34-03 | Needs-you inbox | backlog | [story-03](./story-03-needs-you-inbox.md) | [evidence-story-03](./evidence-story-03.md) |
| WLA-34-04 | Inline ask-and-resume | backlog | [story-04](./story-04-inline-ask-resume.md) | [evidence-story-04](./evidence-story-04.md) |
| WLA-34-05 | Reconnect-safe execution | backlog | [story-05](./story-05-reconnect-safe.md) | [evidence-story-05](./evidence-story-05.md) |
| WLA-34-06 | Session telemetry | backlog | [story-06](./story-06-session-telemetry.md) | [evidence-story-06](./evidence-story-06.md) |
| WLA-34-07 | Session-to-outcome links | backlog | [story-07](./story-07-session-outcomes.md) | [evidence-story-07](./evidence-story-07.md) |
| WLA-34-08 | Command palette | backlog | [story-08](./story-08-command-palette.md) | [evidence-story-08](./evidence-story-08.md) |
| WLA-34-09 | Revisioned project context | backlog | [story-09](./story-09-project-context.md) | [evidence-story-09](./evidence-story-09.md) |
| WLA-34-10 | Agent suggestion inbox | backlog | [story-10](./story-10-suggestion-inbox.md) | [evidence-story-10](./evidence-story-10.md) |
| WLA-34-11 | Prove it works | done | [story-11](./story-11-prove-it-works.md) | [evidence-story-11](./evidence-story-11.md) |

## Sequencing

Foundation: WLA-34-01 (global SSE) and WLA-34-02 (state model) enable
everything else — they define the event vocabulary and state axes the
whole phase speaks. Then the interaction core: WLA-34-03 (needs-you
inbox) and WLA-34-04 (ask-and-resume) — these close the human-agent
loop that is the phase's central promise. WLA-34-05 (reconnect safety)
makes the loop durable. Then the telemetry arc: WLA-34-06 (session
telemetry) and WLA-34-07 (session-to-outcome). Then the UX layer:
WLA-34-08 (command palette), WLA-34-09 (project context), WLA-34-10
(suggestion inbox). WLA-34-11 closes the phase as the exam.

## Where we are

Phase scaffolded 2026-07-31 with eleven stories, informed by deep
analysis of Operator's codebase (commit 174820d8) by three independent
sol agents studying the data model, agent orchestration, and UX
patterns. Ready for story authoring and implementation.

## Active risks

| Risk | Likelihood | Mitigation | Stop signal |
|---|---|---|---|
| Global SSE stresses the single-threaded Python server | high | Cap subscribers; reuse the existing SSE adapter; evidence must show 5 concurrent streams without degradation | Memory or CPU grows unbounded with 3+ open tabs |
| Ask-and-resume breaks the typed-request authority model | medium | Route answers through existing decision ports; never accept free-text outside typed responses; WLA-34-11 re-runs permission tests | A test finds an answer accepted without a matching typed-request ID |
| SQLite analytics projection drifts from ledger truth | medium | Projection is rebuildable; add a rebuild command; test projection matches ledger-derived facts | A projected fact contradicts the ledger |
| Reconnect-safe execution requires driver/adapter layer changes | high | Scope initially to orchestration runs (already durable via ledger replay); mission-control terminal sessions are a separate scope | The reconnect guarantee claims to cover something it doesn't |
| Real PTY requires WebSocket which stdlib HTTP server lacks | high | Use a sidecar process (like Operator's pty-server.js) with authenticated WebSocket upgrade; proxy through the existing server | The PTY exposes an unauthenticated shell on a reachable port |
| Parallel supervisor process adds operational complexity | medium | Make the supervisor optional — DW still works without it, tick-by-tick; the supervisor is an acceleration, not a requirement | The supervisor's crash takes down ordinary DW operations |

## Decisions made (this phase)

- 2026-07-31 - Phase informed by three independent sol-agent analyses of Operator's codebase (commit 174820d8): data model (schemas, cost tracking, session lineage, reconnect safety), agent orchestration (driver abstraction, parallel sessions, worktree isolation, PTY, services, merge flow), and UX patterns (SSE architecture, kanban, needs-you signaling, diff review, insights).
- 2026-07-31 - The SQLite analytics layer is a disposable projection, not the source of truth. The Markdown roadmap and append-only ledger remain authoritative. Rebuildable from ledger.
- 2026-07-31 - Ask-and-resume goes through DW's existing typed-request and decision-port machinery, not an unrestricted chat box.
- 2026-07-31 - Cost is stored as integer microunits with measurement status (reported/estimated/unknown), never as floating-point dollars. Never turn missing metrics into zero.
- 2026-07-31 - Merge never uses `--no-verify`. Every merge goes through evidence capture, contract certification, and the DW commit gate.
- 2026-07-31 - The parallel supervisor is optional infrastructure, not a replacement for tick-driven execution.
- 2026-07-31 - Reconnect safety is scoped to already-durable orchestration runs initially.

## Decisions deferred

- Whether to add a cross-repository fleet view — requires a registry of DW-managed repos; decide after WLA-34-01 proves the single-repo global stream.
- Whether to add portfolio-level dependency edges between stories — decide in WLA-34-10 based on whether the suggestion inbox needs them.
- Whether the command palette supports natural-language queries — decide in WLA-34-08; default is structured search only.
- Whether the PTY sidecar should use tmux-like persistent sessions or ephemeral per-connection shells — decide in implementation based on complexity.

## Operator analysis sources

Three sol agents studied Operator OSS at commit 174820d8 (2026-07-30):

1. **Data model agent** — SQLite schema (projects, tasks, sessions, messages, summaries, usage, dependencies, services), cost tracking (Claude SDK-reported vs Codex estimated, per-turn microunit storage), session lineage (/clear generation model, snapshot-then-tail reconnect), reconnect safety (server-side turns, startup recovery), project context (mutable singleton with AI-draft refresh lifecycle), agent suggestions (suggest_task tool, provenance-free acceptance).

2. **Agent orchestration agent** — AgentDriver interface (normalized StreamEvent union: session/model/assistant/tool/ask/usage/done), parallel execution model (per-task atomic turn ownership, FIFO follow-up queue, no global worker pool), worktree isolation (branch-per-task, atomic-ref merge, fallback-to-main weakness, --no-verify weakness), PTY sidecar (node-pty + WebSocket, no reconnect, no auth), service supervisor (process-group SIGTERM/SIGKILL, port allocation, orphan reaping, no crash backoff), diff/merge/conflict/PR flow.

3. **UX patterns agent** — Next.js 15/React 19 stack, two-level SSE (per-task transcript + global lifecycle coarse stream), orthogonal state axes (workflow/execution/attention), "Needs you" global inbox (oldest-first, browser notification, one-click jump, answer-by-request-ID), kanban (7 columns including derived Suggested and Needs-input, native drag, no keyboard drag), hand-rendered unified diff (no library, content-visibility for large files), insights (hand-built SVG sparklines, 180-day daily aggregates, estimated cost with ~ prefix), lifecycle separation (turn end ≠ task done, merged ≠ certified).
