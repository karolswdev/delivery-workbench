# Delivery Workbench — MCP Surface Contract

What the `dw-mcp` server exposes to agents, exactly how, and — most
importantly — what it refuses to expose. This is the design contract
for WLA-10-02/03 (implementation) and WLA-10-04 (wiring); the
inventory and exclusions below are tested properties, not
aspirations. MCP is one of three interoperable transports — the full
surface inventory across CLI, HTTP, and MCP lives in
[interop.md](./interop.md).

## Why a server, and why this thin

Agents already operate the rails headlessly through `.githooks/dw`
— the exit-code contracts and `--json`/`--porcelain` outputs were
built for exactly that. What shelling out loses is structure:
schemas live in prose, refusals arrive as prefixed strings, and
every agent reimplements the parsing. MCP is the native tool
surface for agents, so the rails grow one.

The Phase 6 invariant applies with full force: **there is no second
implementation of any rule.** `dw-mcp` is a thin JSON adapter over
the same `dw_pmo` core functions the CLI calls — every tool below
names its core function, and the parity tests assert that MCP
verdicts equal CLI verdicts on identical repository state. Any
conditional in the server that consults roadmap semantics instead
of calling the core is a defect by definition.

## The exclusions (the load-bearing part)

Two operations are deliberately absent and must never appear:

- **No certification tool.** Flipping `- [ ]` to `- [x]` in
  `.tmp/CONTRACT.md` is an act of attestation — "I verified this
  rule holds." A `dw_certify` tool would mechanize the one step
  whose entire value is that it cannot be mechanized; the contract
  would become a formality the way clicked-through EULAs are.
  Agents certify the way humans do: by deliberately editing the
  contract file after honestly verifying each rule.
- **No commit tool.** `git commit` is where the gate runs; the
  server will not wrap, trigger, or shortcut it. (Also excluded:
  writing `.tmp/BUNDLE-OK.md` — bundle consent is part of the same
  attestation family.)

The exclusion is enforced as a tested property of `tools/list`
output, not just prose (WLA-10-03).

Also out of scope in v1: phase/story scaffolding tools (CLI
ceremony is proportionate there), the workbench's guarded editor
(it has its own localhost surface), and work-log operations.

## Tool inventory

Every tool returns both human-greppable `content` text and
`structuredContent` for machine consumption. Errors set
`isError: true` with the CLI's refusal message as text — refusal
semantics are shared with the CLI by construction. The deliberate-step apply
receipt is the exception by design: expected operational refusals are versioned
result data (`outcome: refused`, `started: false`), not protocol/tool errors.

`dw_status` is intentionally different from a refusal: a briefing whose
`verdict` is `attention` is successful tool data. The caller needs its
blocking reason and repair action, so the adapter never converts that verdict
to `isError`.

### Orientation (read-only)

| Tool | Core function | Input schema (all fields optional unless noted) |
|---|---|---|
| `dw_status` | `status.build_status` | `{project?: string}` — result: the stamped `delivery-workbench-status` v1 object, including exactly one guided `next_action` |
| `dw_knowledge_map` | `repository_map.read_symbol_map` | `{}` — result: the index-tree-bound derived symbol, module, test, and named-gap map; refuses missing or stale cache and never refreshes or authorizes |
| `dw_knowledge_ground` | `grounding.ground_project_story` | `{project: string, story: string}` (required) — result: advisory verified/new/unknown localization from a fresh map and bounded tracked-blob text fallback; read-only, never authorizes, and refuses stale knowledge |
| `dw_step` | `step.build_step` | `{project?: string}` — pure `delivery-workbench-step` v1 preview of one state-bound action; never executes |
| `dw_context` | `api.build_context_payload` | `{project?: string, compact?: boolean}` |
| `dw_next` | `api.next_story` | `{project?: string}` — result: the story object or `{next: null}` |
| `dw_check` | `validate.check_project` + advisory grounding lint | `{project?: string}` — result: `{ok: boolean, issues: string[], warnings?: string[]}`; grounding warnings never change `ok` |
| `dw_doctor` | `doctor.run_doctor` | `{}` — result: `{healthy: boolean, checks: [{name, ok, detail}]}` |

### Browse (read-only)

| Tool | Core function | Input schema (all fields optional unless noted) |
|---|---|---|
| `dw_board` | `board.board_model` | `{project?: string, phase?: string\|number}` — result: the stamped board model (`kind: delivery-workbench-board`, `schema_version: 1`); cards carry `paths` (story/evidence/phase-status receipts) and `links` (workbench story/trace routes); text is the rendered board |
| `dw_holds` | `api.parked_summary` | `{project?: string}` — result: `{paused_phases, parked_stories, counts}`, every entry with its `note`, `paths`, and `links`; text mirrors the CLI's greppable `PAUSED`/`BLOCKED`/`ON-HOLD` lines |
| `dw_story_show` | `api.story_detail` | `{project: string, phase: string\|number, story: string\|number}` (required) — result: one story whole (header context, `status_token`/`status_note`, story + evidence markdown, parsed `captured_runs`, `paths`, `links`); absences are honest empties |

### Verification (read-only)

| Tool | Core function | Input schema |
|---|---|---|
| `dw_verify` | `verify.run_verify` | `{range?: string, all?: boolean, epoch?: string}` — result mirrors `--porcelain`: `{ok, verified, pre_epoch_skipped, out_of_scope, epoch, violations: [{sha, rule, message}]}` |
| `dw_gate` | `gate.run_gate` | `{}` — result mirrors `dw gate --porcelain` (pass/fail, tier, boxes, shipped stories, failing rule + remediation) — preflight only; never consumes the contract |

### Bounded orchestration (read-only and preview)

These tools accept only selectors, run ids, timestamps, and bounded preview
parameters. They do not accept score documents, prompts, provider/check
commands, driver configuration, scheduling choices, or credentials.

| Tool | Core function | Input schema |
|---|---|---|
| `dw_orchestration_list` | `orchestration.score_inventory` | `{}` |
| `dw_notifications` | `notifications.build_notifications` | `{}`; pure derived operator notifications with unread/delivery state |
| `dw_notifications_ack` | `notifications.acknowledge_notification` | `{notification_id}`; idempotent receipted ack |
| `dw_signals` | `signals.build_signals_inventory` | `{remote?, branch?}`; pure outward-signal inventory with read-time derived status; the observe pass stays a CLI act |
| `dw_orchestration_show` | `orchestration.compile_score_path` | `{score}` |
| `dw_orchestration_simulate` | `orchestration.simulate_score` | `{score}`; pure, starts nothing |
| `dw_run_plan` | `orchestration_run.build_run_plan` | `{score, story, project?, issued_at?, expires_at?, standing_nudges?, signal_channel?}`; exact pure grant preview including nudge authority |
| `dw_run_list` | `orchestration_run.run_inventory` | `{}`; content-safe projections only |
| `dw_run_show` | `orchestration_run.replay_run` | `{run_id}` |
| `dw_run_view` | `orchestration_surface.build_run_view` | `{run_id}`; live graph, attempts, sessions/check receipts, artifact metadata/lineage, budgets, routes, controls, and ledger timeline |
| `dw_run_preview` | `orchestration_surface.build_run_act_preview` | `{run_id, action, reason?, correlation_id?, decision?}`; binds the exact action, parameters, request correlation, and current ledger head in one `act_token` |

### Autonomous programs (read-only and preview)

These tools adapt the same canonical `program_surface` documents as CLI JSON,
HTTP envelope `data`, Workbench bootstrap, and SSE replay. Inventory/view/tail
reads start no program store, process, observer, notification, poller, or
stream, and return no mutation token. The preview tool is the only source of a
public program `act_token`.

| Tool | Core function | Input schema |
|---|---|---|
| `dw_program_list` | `program_surface.program_summary_inventory` | `{}`; healthy empty policy/run inventory in ordinary mode |
| `dw_program_show` | `program_surface.build_program_view` | `{run_id}`; content-safe why/current lineage, organization and exact execution fingerprints, activity, quality/dissent, gates, obligations, deliveries, budgets, controls, and verified timeline |
| `dw_program_validate` | `programs.validate_program_path` | `{program}`; pure tracked-policy validation |
| `dw_program_simulate` | `programs.simulate_program` | `{program}`; pure deterministic scope, workflow, team, and worst-case simulation |
| `dw_program_plan` | `program_run.build_program_start_plan` | `{program, mode, operator, reason, intent_id, issued_at, expires_at, capabilities?, budgets?, remote?, remote_ref?}`; pure exact finite-grant preview |
| `dw_program_preview` | `program_surface.build_program_act_preview` | `{run_id, action, reason?, decision?, request_id?, max_ticks?, max_seconds?}`; binds one closed operation and its finite ceilings to the current ledger head |
| `dw_program_tail` | `program_surface.tail_program_events` | `{run_id, after?, limit?}`; verified bounded ledger suffix with no prompt, transcript, source, artifact content, or token |

### Autonomous programs (exact-token acts)

Each tool consumes an `act_token` from a fresh matching
`dw_program_preview`, except start, which consumes the `start_token` from the
matching pure plan. Inputs are closed and `additionalProperties: false`; no act
accepts policy, assignments, prompts, rubrics, checks, driver configuration,
credentials, commands, or retry overrides.

| Tool | Core function | Input schema |
|---|---|---|
| `dw_program_start` | `program_surface.start_program_by_id` | `{program, mode, operator, reason, intent_id, issued_at, expires_at, approve, expect, capabilities?, budgets?, remote?, remote_ref?}`; rebuilds and consumes one exact grant, starts no child |
| `dw_program_tick` | `program_surface.apply_program_act` | `{run_id, expect}`; one conductor, delivery-plan, or delivery tick under the existing grant |
| `dw_program_supervise` | `program_surface.apply_program_act` | `{run_id, expect, max_ticks, max_seconds}`; explicit finite repetition that returns every tick and stops at no-progress/checkpoint/refusal/budget/duration/terminal |
| `dw_program_request` | `program_surface.apply_program_act` | `{run_id, request_id, decision: "approve"\|"reject", reason, expect}`; one typed response to one exact outstanding request |
| `dw_program_pause` | `program_surface.apply_program_act` | `{run_id, reason, expect}` |
| `dw_program_resume` | `program_surface.apply_program_act` | `{run_id, reason, expect}`; re-observes grant facts |
| `dw_program_revoke` | `program_surface.apply_program_act` | `{run_id, reason, expect}`; permanent for that grant |
| `dw_program_cancel` | `program_surface.apply_program_act` | `{run_id, reason, expect}`; cancellation is ledgered before bounded interruption |
| `dw_program_stream` | `program_surface.read_program_stream` | `{run_id, session_id, stream: "stdout"\|"stderr", max_bytes?}`; explicit independently bounded open only; list/view/tail never include its content |

### Bounded orchestration (exact-token acts)

Every act is separate from preview. A ledger, action, reason, or checkpoint
decision change makes the token unusable. Expected state races are tool
errors with the shared refusal text; nothing is automatically re-previewed.

| Tool | Core function | Input schema |
|---|---|---|
| `dw_run_start` | `orchestration_surface.start_run_by_id` | `{score, story, project?, issued_at, expires_at, expect, approve, operator}`; rebuilds the exact plan and creates a grant, but dispatches nothing |
| `dw_run_tick` | `orchestration_surface.apply_run_act` | `{run_id, expect}`; one tick preview token; may start only score-authorized bounded work |
| `dw_run_pause` | `orchestration_surface.apply_run_act` | `{run_id, expect, reason}` |
| `dw_run_resume` | `orchestration_surface.apply_run_act` | `{run_id, expect}`; re-observes grant facts |
| `dw_run_revoke` | `orchestration_surface.apply_run_act` | `{run_id, expect, reason}`; permanent for that grant |
| `dw_run_cancel` | `orchestration_surface.apply_run_act` | `{run_id, expect, reason}`; cancellation is ledgered before interruption |
| `dw_run_request` | `orchestration_surface.apply_run_act` | `{run_id, expect, correlation_id, decision}`; one response validated against the outstanding request's closed schema |
| `dw_run_checkpoint` | `orchestration_surface.apply_run_act` | `{run_id, expect, decision, correlation_id?}`; checkpoint-only compatibility alias |
| `dw_run_stream` | `orchestration_surface.read_run_stream` | `{run_id, executor: "agent"|"check", execution_id, stream: "stdout"|"stderr", max_bytes?}`; explicit, independently bounded open only |

Retry remains an immutable score failure policy exercised by a confirmed
tick; it is not a manual retry tool. Authority elevation requires a new grant.
Certification, commit, push, release, and deploy remain permanently absent.

### Guarded mutations

| Tool | Core function | Input schema |
|---|---|---|
| `dw_step_apply` | `step.apply_step` | `{expect: string, project?: string}` — consumes one exact preview token, starts at most its closed-table child, and returns `delivery-workbench-step-result` v1; no command/argv field, certification, commit, or continuation |
| `dw_story_status` | `mutations.plan_story_status` + `mutations.apply_plan` | `{project: string, phase: string|number, story: string|number, status: string}` (required) — same transactional header+table write, same refusal of done-without-evidence |
| `dw_evidence_capture` | `evidence.run_capture` | `{project, phase, story, command: string[], cwd?: string}` (required except cwd) — command is an argv array, executed exactly as `dw evidence capture -- …`; output recorded with the shared renderer and its truncation bounds |
| `dw_contract_new` | `contract.build_contract` + `contract.write_contract` | `{story?: string[], consent?: "yes"|"no", reasons?: string[], tests_capture?: string, tier?: "auto"|"full"|"short", force?: boolean}` — result text states plainly: certification happens by editing `.tmp/CONTRACT.md`, and no tool does it |

`dw_evidence_capture` runs a caller-supplied command. That is the
same power `dw evidence capture` already grants any shell user, and
it is the point: evidence must come from real runs, not typed-in
claims. MCP clients front tool calls with their own permission
prompts; the server neither adds nor subtracts from that gate.

## Protocol subset

- **Transport:** stdio; newline-delimited JSON-RPC 2.0 messages
  (one message per line, UTF-8), per the MCP stdio transport.
- **Protocol version:** pinned to `2025-06-18`; `initialize`
  echoes the client's requested version when it matches, otherwise
  responds with the pinned version (client decides whether to
  proceed, per spec).
- **Methods:** `initialize`, `notifications/initialized`
  (accepted, ignored), `tools/list`, `tools/call`, `ping`.
  Everything else → JSON-RPC `-32601` (method not found).
  Unknown tool name → tool error; invalid params against a tool's
  schema → `-32602`.
- **Capabilities advertised:** `{"tools": {}}` — no resources, no
  prompts, no notifications in v1.
- **Loop:** strictly serial (read → dispatch → respond). dw
  operations are subsecond; the CLI is serial too. A malformed
  line yields a `-32700` parse error response and the loop
  continues — bad input never kills the server.
- **Implementation:** python stdlib only (`json`, `sys`,
  `argparse`, existing core imports). No MCP SDK — the subset
  above is small, the repo's floor is python 3.9, and the
  `python-floor` CI job proves the constraint stays honest.

## Binding to a repository

`dw-mcp` binds to one repository per process: root discovery from
cwd (or `--root`), exactly like `bin/dw`. Launched outside an
adopted repository (no rails, no roadmap), `initialize` succeeds
but every tool call returns a tool error naming the missing rails
and the install command — a discoverable failure, not a dead
socket. The vendored copy under `.githooks/dw-mcp` is the one
agents should run, for the same defer-to-repo reason the global
CLI defers: the server that answers must be the rails that gate
(WLA-10-04 wires `.mcp.json` accordingly).

## Proof obligations

- Every tool's verdict equals the CLI's on identical fixture state
  (`dw-core-tests.py` parity cases, WLA-10-02/03).
- `dw_step` and `dw_step_apply` return the exact same core preview/result as
  CLI and HTTP, reject caller-supplied argv, consume one lease, and preserve
  the certification/commit exclusions (`tests/step-interop.sh`, WLA-23-03).
- A fixture story walks backlog → done over MCP with files
  byte-identical to the CLI path (WLA-10-03).
- `tools/list` never contains a certify/commit/bundle tool
  (WLA-10-03, asserted against this document's exclusion list).
- A real client completes initialize → tools/list → tools/call
  (`tests/mcp-server.sh` subprocess smoke, WLA-10-02; live client
  session, WLA-10-05).
