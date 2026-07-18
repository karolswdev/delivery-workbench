# Phase 24 - The conductor's score — visual orchestration

**Last updated:** 2026-07-17.

## Goal

Delivery Workbench can coordinate a bounded multi-agent delivery run from an
exact, visually authored score and explicit revocable grant: research agents,
dependencies, context, output conventions, checks, failure routes, budgets,
recovery, and human checkpoints—without becoming a generic shell runner or
quietly acquiring certification and commit authority.

## Scope

- **In:** tracked `delivery-workbench-orchestration@1` scores; pure compile,
  validation, and simulation; a rich graph editor; roles including parallel
  research/synthesis/implementation/review/repair; typed inputs and output
  conventions; exact checks; success/failure edges; time/attempt/artifact/
  concurrency budgets; explicit run grants; append-only run ledger and
  receipts; deterministic scheduling; agent-driver and isolated-worktree
  seams; cancellation/restart; CLI, MCP, HTTP, Workbench, and packaged proof.
- **Out:** scores as authority; LLM-invented commands/routes/checks; secret or
  provider executable storage in the repository; unbounded graph cycles;
  shared writable workspaces; automatic conflict resolution; automatic
  evidence judgment, contract certification, commit, push, release, or
  deployment; a hosted service holding local repository authority.

## Exit criteria (evidence required)

- [x] One exact, versioned score model can express agent roles/profiles,
  dependencies, context inputs, typed output conventions, exact checks,
  failure routes, budgets, concurrency, and approval/terminal nodes; its pure
  compiler rejects malformed, cyclic, unbounded, escaped, or capability-
  inconsistent graphs (WLA-24-01/02).
- [x] The Workbench provides a rich visual score editor—graph canvas, node/
  edge palette, full inspector, live errors, capability/output lineage,
  scheduling simulation, JSON view, and guarded preview→diff→apply—with
  lossless graph/JSON round trips and no browser-owned policy (WLA-24-03).
- [x] A separate, explicit grant binds score hash, repository/story facts,
  capabilities, budgets, expiry, and revocation; an append-only ledger plus
  exclusive claims makes run/node projection auditable and dispatch at-most-
  once across restart (WLA-24-04).
- [ ] Provider-neutral drivers receive structured work packets rather than
  commands; read-only research can fan out, synthesis consumes validated
  artifacts, writers use isolated worktrees, unsupported capabilities refuse,
  and outputs must meet declared schemas/conventions before fan-in
  (WLA-24-05).
- [ ] A deterministic conductor schedules eligible nodes, consumes fresh
  `dw step` leases only for declared rail nodes, enforces exact check/failure/
  retry/cancellation policy and all budgets, recovers without duplicate work,
  and stops at named human checkpoints (WLA-24-06).
- [ ] CLI, MCP, HTTP, and Workbench expose byte-equivalent score/run models and
  exact-token acts; the visual Run view makes agents, checks, artifacts,
  attempts, failures, budgets, approvals, cancellation, and terminal handoff
  legible without accepting provider or shell argv (WLA-24-07).
- [ ] A wheel-installed fresh consumer visually configures and executes a
  parallel-research→synthesis→implementation→check/repair score through
  restart and red paths, then stops at `awaiting-certification`; the fixture
  operator alone certifies/commits and the full matrix/history stays green
  (WLA-24-08).

## Story status

| ID | Story | Status | Story file | Evidence |
|---|---|---|---|---|
| WLA-24-01 | Contract the visual score and orchestration authority | done | [story-01-orchestration-contract](./story-01-orchestration-contract.md) | [evidence-story-01](./evidence-story-01.md) |
| WLA-24-02 | Compile and validate exact orchestration rules | done | [story-02-orchestration-manifest-core](./story-02-orchestration-manifest-core.md) | [evidence-story-02](./evidence-story-02.md) |
| WLA-24-03 | Build the rich visual orchestration editor | done | [story-03-visual-orchestration-editor](./story-03-visual-orchestration-editor.md) | [evidence-story-03](./evidence-story-03.md) |
| WLA-24-04 | Authorize runs with grants and an append-only ledger | done | [story-04-run-grants-ledger](./story-04-run-grants-ledger.md) | [evidence-story-04](./evidence-story-04.md) |
| WLA-24-05 | Drive research and worker agents in isolated workspaces | backlog | [story-05-agent-drivers-workspaces](./story-05-agent-drivers-workspaces.md) | - |
| WLA-24-06 | Schedule nodes, checks, failure routes, and recovery | backlog | [story-06-conductor-runtime](./story-06-conductor-runtime.md) | - |
| WLA-24-07 | Expose and monitor runs across every surface | backlog | [story-07-run-control-interop](./story-07-run-control-interop.md) | - |
| WLA-24-08 | Prove a packaged multi-agent orchestration | backlog | [story-08-packaged-orchestration-exam](./story-08-packaged-orchestration-exam.md) | - |

## Where we are

Phase OPEN 4/8. WLA-24-04 has delivered the separate execution-authority ring.
A pure run plan binds the compiled score to local repository/HEAD/status/story
facts, requested profiles/capabilities/workspaces, every finite budget, expiry,
and permanent exclusions. Exact-token approval atomically publishes immutable
plan/score/grant documents and a hash-chained ledger; replay ignores disposable
cache state and fails closed on tamper, truncation, or forks. Cross-process
start/node claims, idempotency, freshness, expiry, budgets, and immediate
pause/resume/revoke/cancel transitions are test-proven on both Python floors
and in the wheel. WLA-24-05 is next: drive provider-neutral research and
worker packets through capability-checked, isolated workspaces.

## Active risks

| Risk | Likelihood | Mitigation | Stop signal |
|---|---|---|---|
| Visual flexibility becomes an arbitrary workflow language | high | Five typed nodes, acyclic success graph, bounded retry/repair policy, pure compiler | Editor can save an unbounded cycle or hidden runtime field |
| A tracked score is mistaken for execution consent | high | Separate hash-bound, expiring, revocable grant with capability/budget preview | Saving or opening a score starts work |
| Agent prompts smuggle shell/provider authority | high | Work packets are structured; logical profiles resolve only in operator-local driver config | Score contains a provider executable, secret, or agent-supplied command |
| Research or parallel writers escape their lane | high | Capability match, read-only research artifacts, isolated writer worktrees, resource locks, output/path checks | Two writable nodes share a cwd or undeclared output reaches fan-in |
| Failure handling becomes infinite or dishonest | high | Compile-time finite ceilings; required checks cannot skip; explicit retry/route/approval/pause/abort receipts | Run advances after a failed required check without a recorded route |
| Crash/retry duplicates expensive or destructive work | high | Exclusive claims before dispatch; append-only ledger; poll-before-retry recovery | Restart launches a second copy of a claimed node |
| “Orchestration complete” bypasses consent spine | high | Terminal handoff is `awaiting-certification`; certification/commit remain explicit | Score or driver checks boxes, commits, pushes, or releases |

## Decisions made (this phase)

- 2026-07-17 - Phase scaffolded with `dw phase create` - keeps roadmap structure consistent - CLI.
- 2026-07-17 - Say Delivery Workbench **can coordinate**, not that it will - orchestration is an explicitly configured product capability, not a promise to automate every project - owner correction.
- 2026-07-17 - Make the rich visual editor the product center and a canonical JSON score its lossless backing - exact roles, research fan-out, dependencies, prompts/context, outputs, checks, fail routes, budgets, approvals, and terminals must all be inspectable - owner direction.
- 2026-07-17 - Separate score from grant - tracked configuration is reviewable intent; execution needs a fresh, revocable authorization over the exact compiled hash and capabilities - consent spine.
- 2026-07-17 - Keep agent execution in provider drivers and harness sandboxes - Delivery Workbench coordinates structured packets, workspaces, receipts, and policy rather than becoming a provider-specific shell runner - architecture boundary.
- 2026-07-17 - Permit exact command checks only as tokenized argv in an authorized score with cwd/time/output/write bounds - real projects need pytest/npm/build checks, while shell strings and agent-invented commands remain out - fail-check requirement.
- 2026-07-17 - Hash runtime semantics separately from editor layout while hashing the complete normalized document for stale-safe saves - canvas movement cannot change authority, but no layout edit is silently lost - WLA-24-02.
- 2026-07-17 - Treat failure-only repair nodes as explicitly activated and bounded route targets - the success graph stays acyclic and simulation cannot accidentally schedule repair work on the green path - WLA-24-02.
- 2026-07-17 - Make a run plan reviewable but non-authoritative, then consume its complete score/repository/status/story binding only through one explicit local approval - configuration remains distinct from consent - WLA-24-04.
- 2026-07-17 - Treat the hash-chained ledger as authority and `projection.json` as disposable - crash recovery and audit do not depend on a mutable cache - WLA-24-04.
- 2026-07-17 - Stop future dispatch immediately on pause, revoke, cancellation, expiry, stale repository facts, or budget exhaustion while still allowing in-flight claims to record bounded terminal outcomes - revocation is operational, not decorative - WLA-24-04.

## Decisions deferred

- Cross-machine hosted control plane - trigger after the local score/grant/run
  contract survives the packaged exit exam - default is local execution
  authority with remote-friendly thin adapters.
- Automatic certification, commit, push, release, or deployment - trigger only
  under a separately designed approval authority - default is a terminal
  `awaiting-certification` handoff.
- Arbitrary cyclic graphs and automatic merge/conflict resolution - trigger
  after bounded DAG plus retry/repair routes prove insufficient - default is
  finite scheduling and reviewed integration.
