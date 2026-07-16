# Phase 22 - The briefing — one answer before agents act

**Last updated:** 2026-07-15.

## Goal

Give every human and agent one deterministic, versioned answer for
repository readiness, current work, and the next safe action, shared
across every supported surface. Delivery Workbench already has strong
individual rails; this phase turns them into one legible entry point.

## Scope

- **In:** a dated solution map; a versioned status-briefing contract;
  a pure core that composes clone wiring, roadmap validity, Git
  workspace/contract state, current work, holds, and an ordered next
  action; `dw status [project] [--json]`; byte-equal MCP and HTTP
  adapters; a workbench front-door view; the canonical agent brief;
  schema, purity, parity, viewport, and fresh-consumer tests.
- **Out:** executing the recommended action automatically; changing
  gate, evidence, consent, or certification policy; hosted telemetry;
  fetching CI or forge state; choosing among multiple projects or
  ambiguous active stories on the operator's behalf; a new database or
  daemon.

## Exit criteria (evidence required)

- [x] The repository has one current, evidence-linked solution
  overview and a status-briefing contract that defines readiness,
  schema, action precedence, and non-goals (WLA-22-01).
- [ ] `dw status [project] [--json]` returns a stamped, deterministic,
  read-only model over rails health, roadmap health, workspace state,
  selected work, gate state, and the next safe action; red paths never
  claim readiness (WLA-22-02).
- [ ] `dw_status` and `GET /api/status` return the same core model as
  the CLI, and the interop inventory/schema pins fail on drift
  (WLA-22-03).
- [ ] The workbench overview and generated agent brief begin with the
  briefing and its next action without removing any specialist surface
  (WLA-22-04).
- [ ] A fresh packaged consumer is driven from unknown state through a
  complete evidence-backed story and gated commit using the briefing's
  recommendation at each transition; all distribution and UI checks
  remain green (WLA-22-05).

## Story status

| ID | Story | Status | Story file | Evidence |
|---|---|---|---|---|
| WLA-22-01 | Map the solution and contract the briefing | done | [story-01-solution-map-and-briefing-contract](./story-01-solution-map-and-briefing-contract.md) | [evidence-story-01](./evidence-story-01.md) |
| WLA-22-02 | dw status — one deterministic core and CLI | ready | [story-02-status-core-and-cli](./story-02-status-core-and-cli.md) | - |
| WLA-22-03 | One model everywhere — MCP and HTTP parity | ready | [story-03-status-interop](./story-03-status-interop.md) | - |
| WLA-22-04 | The workbench and agent brief open on the answer | backlog | [story-04-status-front-door](./story-04-status-front-door.md) | - |
| WLA-22-05 | Prove the guided loop in a fresh consumer | backlog | [story-05-guided-loop-exit-exam](./story-05-guided-loop-exit-exam.md) | - |

## Where we are

Phase OPEN 1/5. WLA-22-01 is done: the dated solution overview maps the
whole product and its proof, the roadmap front door is current again,
and `docs/status-briefing.md` freezes the v1 readiness/action contract
before implementation. Its captured run is 208 core tests plus docs,
canon, roadmap, and diff checks green. WLA-22-02 is next: build the pure
status core and CLI against that contract.

## Active risks

| Risk | Likelihood | Mitigation | Stop signal |
|---|---|---|---|
| The briefing becomes a second implementation of existing rules | medium | Compose `doctor`, validation, `next`, holds, gate inspection, and Git plumbing; adapters contain no semantics | A status-only conditional reinterprets a story or gate rule |
| A concise answer hides ambiguity and sends an agent into the wrong project | medium | Unknown beats guessed; multiple possible projects yield `select-project`, never an implicit choice | The model chooses one of several plausible projects |
| A recommended commit is unsafe because the index or contract moved | high | Inspect the live index and gate without emitting events; unstaged work outranks commit; only a passing gate may recommend `git commit` | `commit` appears while the gate would refuse |
| Machine consumers couple to prose | medium | Stamp the model, pin exact key sets, use argv arrays and action ids; prose is a renderer only | A client must scrape the human summary |
| Status reads mutate telemetry or the roadmap | low | Purity checksum tests and a no-event gate-inspection seam | Repeated status calls change any file or event log |
| The overview becomes another stale front door | medium | Link claims to executable proof and make freshness-sensitive facts a dated snapshot; phase 22 updates the roadmap's own stale summary | Undated release/count claims appear as timeless truth |

## Decisions made (this phase)

- 2026-07-15 - Phase scaffolded with `dw phase create` - keeps roadmap structure consistent - CLI.
- 2026-07-15 - Name the entry point `dw status`, the model `delivery-workbench-status`, and the agent tool `dw_status` - the most discoverable word should own the aggregate answer; `dw story status` remains the scoped mutation - audit finding.
- 2026-07-15 - The briefing is read-only and recommends exactly one next action but never executes it - orientation may guide consent, never impersonate it - trust boundary.
- 2026-07-15 - `ready` means the rails and roadmap are safe to work on, not that the tree is clean or work is finished - dirty/staged/contract states are normal workflow states with different next actions - workflow model.
- 2026-07-15 - Unknown beats guessed - no implicit project selection when more than one candidate exists, and no invented test command - mission-control precedent.
- 2026-07-15 - Action commands are argv arrays, not shell strings; deliberate human acts such as contract certification have `kind: manual` and no pretend command - interoperability and consent spine.

## Decisions deferred

- Remote CI/forge readiness in the briefing - trigger: a stable provider-neutral receipt source - default: local and pushed-history facts only.
- Installed-vs-latest package discovery over the network - trigger: an update service with an offline contract - default: `dw update --check` remains explicit.
- Auto-execution of recommended actions - not planned; the briefing stays a read surface and existing mutation/consent paths retain authority.
- Status history or analytics - trigger: a concrete operator question that the append-only rail event taxonomy cannot answer - default: no new persistence.
