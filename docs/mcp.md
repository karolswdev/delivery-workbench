# Delivery Workbench — MCP Surface Contract

What the `dw-mcp` server exposes to agents, exactly how, and — most
importantly — what it refuses to expose. This is the design contract
for WLA-10-02/03 (implementation) and WLA-10-04 (wiring); the
inventory and exclusions below are tested properties, not
aspirations. MCP is one of three read transports — the full
read-surface inventory across CLI, HTTP, and MCP lives in
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

Every tool returns both human-greppable `content` text (the same
lines the CLI prints, so transcripts stay auditable) and
`structuredContent` for machine consumption. Errors set
`isError: true` with the CLI's refusal message as text — refusal
semantics are shared with the CLI by construction.

### Orientation (read-only)

| Tool | Core function | Input schema (all fields optional unless noted) |
|---|---|---|
| `dw_context` | `api.build_context_payload` | `{project?: string, compact?: boolean}` |
| `dw_next` | `api.next_story` | `{project?: string}` — result: the story object or `{next: null}` |
| `dw_check` | `validate.check_project` | `{project?: string}` — result: `{ok: boolean, issues: string[]}` |
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

### Guarded mutations

| Tool | Core function | Input schema |
|---|---|---|
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
- A fixture story walks backlog → done over MCP with files
  byte-identical to the CLI path (WLA-10-03).
- `tools/list` never contains a certify/commit/bundle tool
  (WLA-10-03, asserted against this document's exclusion list).
- A real client completes initialize → tools/list → tools/call
  (`tests/mcp-server.sh` subprocess smoke, WLA-10-02; live client
  session, WLA-10-05).
