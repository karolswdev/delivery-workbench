# Phase 23 - The handrail — one deliberate step

**Last updated:** 2026-07-16.

## Goal

Let a human or agent deliberately apply exactly one current, allowlisted recommendation without copy/paste, stale intent, arbitrary execution, certification, or commit automation.

## Scope

- **In:** a stamped, pure one-step preview over the Phase-22 status action;
  a state token binding the complete observed briefing; a closed executable
  action table; explicit one-step apply with stale-intent refusal; bounded
  execution receipts and events; CLI, MCP, HTTP, workbench, and generated-
  rider surfaces; fresh packaged-consumer proof.
- **Out:** automatic multi-step loops; arbitrary command or shell-string
  execution; certification or commit automation; choosing projects,
  evidence commands, phase content, or test commands for the operator;
  bypassing existing mutation, contract, gate, or consent checks; hosted
  orchestration and remote CI/forge readiness.

## Exit criteria (evidence required)

- [x] `dw step [project] [--json]` previews one stamped, deterministic,
  read-only action lease; `--apply --expect <token>` executes at most one
  allowlisted current argv and refuses stale or prohibited intent before
  starting a child process (WLA-23-01).
- [x] Applied steps produce one bounded, versioned receipt and append one
  content-safe rail event that correlates before/after action and outcome
  without pretending a failed command succeeded (WLA-23-02).
- [x] MCP and HTTP expose the same preview/receipt models and explicit token
  contract while retaining their certification/commit exclusions and
  adapter-parity pins (WLA-23-03).
- [x] The workbench and generated agent riders make the preview→deliberate-
  apply boundary legible, with no generic shell field and no hidden loop
  (WLA-23-04).
- [ ] A wheel-installed fresh consumer advances a real story through
  successive explicit steps, proves stale-token and prohibited-commit red
  paths, and leaves the full regression matrix green (WLA-23-05).

## Story status

| ID | Story | Status | Story file | Evidence |
|---|---|---|---|---|
| WLA-23-01 | dw step — preview and apply one allowlisted action | done | [story-01-step-core-cli](./story-01-step-core-cli.md) | [evidence-story-01](./evidence-story-01.md) |
| WLA-23-02 | Step receipts — stable result and event correlation | done | [story-02-step-receipts](./story-02-step-receipts.md) | [evidence-story-02](./evidence-story-02.md) |
| WLA-23-03 | One step across MCP and HTTP | done | [story-03-step-interop](./story-03-step-interop.md) | [evidence-story-03](./evidence-story-03.md) |
| WLA-23-04 | Workbench and riders expose the handrail | done | [story-04-step-front-door](./story-04-step-front-door.md) | [evidence-story-04](./evidence-story-04.md) |
| WLA-23-05 | Fresh-consumer deliberate-step exit exam | backlog | [story-05-step-exit-exam](./story-05-step-exit-exam.md) | - |

## Where we are

Phase OPEN 4/5. WLA-23-04 made the act boundary legible where users and agents
already orient. The Workbench separates the recommendation from review and
confirmation, POSTs only project+token, refreshes after one receipt or stale
conflict, and offers no apply control for prohibited/manual/certification/
commit states. The managed brief, packaged fallback, workflow commands, and
Claude/Codex/pi/plugin renderings now require a fresh exact lease and stop
after one action; drift is a test error. Desktop/mobile visual and static
fitness coverage pin the control. WLA-23-05 is next: prove the entire sequence
from a wheel-installed fresh consumer, with separate authorization for every
step and the full regression matrix green.

## Active risks

| Risk | Likelihood | Mitigation | Stop signal |
|---|---|---|---|
| A convenience command becomes arbitrary remote execution | high | Commands originate only in the status core and must match a closed action-id/argv-shape table | Any caller supplies argv or a shell string |
| An old preview acts on new state | high | Hash the complete canonical status object; re-read and require the exact token immediately before spawn | The same token survives any relevant state change |
| “One step” quietly becomes an agent loop | medium | One invocation starts at most one child and returns; callers must preview/authorize every next transition | The core follows `status_after` automatically |
| Convenience weakens consent | high | `certify-contract`, `commit`, selection, and manual repairs are never applicable even when status names them | Step edits checkboxes, commits, or invents a choice |
| Transport adapters fork policy | medium | One core plan/apply model; exact payload parity and closed inventory tests | MCP, HTTP, or UI owns an action decision |

## Decisions made (this phase)

- 2026-07-15 - Phase scaffolded with `dw phase create` - keeps roadmap structure consistent - CLI.
- 2026-07-15 - Name the surface `dw step` - it advances exactly one observed recommendation and then stops; `status` remains a pure noun/read surface - user follow-up and Phase-22 boundary.
- 2026-07-15 - Applying requires the opaque token from a fresh preview, not only an action id - the story or command can change while the id stays the same - stale-intent threat model.
- 2026-07-15 - Commit and contract certification are permanently prohibited step actions - explicit invocation of a convenience surface is not consent to ship or attest - consent spine.
- 2026-07-15 - Keep JSON apply unavailable until a versioned receipt exists - a transport-shaped success string would become accidental API debt - WLA-23-02 boundary.
- 2026-07-16 - Claim every applicable token atomically under `.git/pmo-step-claims/` before spawn and feed the claim generation into future tokens - read-only actions otherwise leave the original lease replayable - replay threat model.
- 2026-07-16 - Emit `step_execution` only after a child starts and allow only action/outcome/exit/token hashes/next action - correlation is useful, command and output content are not telemetry - event consent stance.
- 2026-07-16 - Keep operational apply refusal as the same versioned result over every adapter (HTTP 409 envelope; normal MCP result) - callers need `started: false` and the current observation without parsing transport errors - interop contract.
- 2026-07-16 - Limit remote apply inputs to `project` plus exact `expect`; never accept command or argv - adapters cannot expand the core capability accidentally - consent floor.
- 2026-07-16 - Put review and apply in separate Workbench controls and refresh after every result - seeing a recommendation is not consent, and one receipt must never become a UI loop - front-door trust boundary.
- 2026-07-16 - Teach every generated rider to use only the preview's exact fresh command/token and stop after one action - interoperability includes operating discipline, not only payload parity - agent usability.

## Decisions deferred

- Whether a later operator-owned mode may waive the preview token for
  interactive terminals - trigger only after real friction evidence - default
  is one explicit preview token for humans and agents alike.
- Remote/hosted loops - trigger after local one-step receipts prove adequate -
  default is no daemon and no automatic continuation.
