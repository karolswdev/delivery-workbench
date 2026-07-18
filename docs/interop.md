# The interop contract — every surface, named

Delivery Workbench exposes one core layer over three transports.
Every surface below derives live from the Markdown roadmap through
the same `dw_pmo` core — no second parser, no cache. Reads are pure. The
write paths are the structured editor's guarded preview→apply flow, guarded
MCP mutations, and the explicit state-bound deliberate step. None can stage,
certify, or commit
(see [mcp.md](./mcp.md), [deliberate-step.md](./deliberate-step.md), and
`pm/roadmap/PMO-CONTRACT.md` for the gate rules; this document
never restates them).

A consumer needs no tree knowledge: board cards, holds entries, and
story detail all carry `paths` (repo-relative receipts) and `links`
(workbench routes), so you can walk card → story → evidence → trace
from any entry point.

## Versioning stance

Stamped models carry `kind` + `schema_version` (or a named schema
field). Additive changes (new keys) do **not** bump a version;
renames and removals do, deliberately, with a CHANGELOG entry.
Unstamped surfaces are documented here and pinned by tests; a stamp
is added when an external consumer asks for one.

| Model | Stamp | Declared in |
|---|---|---|
| Status briefing | `delivery-workbench-status` v1 | `status.build_status` |
| Deliberate-step preview | `delivery-workbench-step` v1 | `step.build_step` |
| Deliberate-step result | `delivery-workbench-step-result` v1 | `step.apply_step` |
| Orchestration score | `delivery-workbench-orchestration` v1 | `orchestration.validate_score` |
| Compiled orchestration | `delivery-workbench-compiled-orchestration` v1 | `orchestration.compile_score` |
| Orchestration validation | `delivery-workbench-orchestration-validation` v1 | `orchestration.validate_score` |
| Orchestration simulation | `delivery-workbench-orchestration-simulation` v1 | `orchestration.simulate_score` |
| Orchestration run plan | `delivery-workbench-run-plan` v1 | `orchestration_run.build_run_plan` |
| Orchestration run grant | `delivery-workbench-run-grant` v1 | `orchestration_run.start_run` |
| Orchestration run event | `delivery-workbench-run-event` v1 | `orchestration_run` ledger |
| Orchestration run projection | `delivery-workbench-run` v1 | `orchestration_run.replay_run` |
| Driver capability | `delivery-workbench-driver-capability` v1 | `orchestration_driver.driver_capability` |
| Agent work packet | `delivery-workbench-work-packet` v1 | `orchestration_driver.build_work_packet` |
| Driver receipt | `delivery-workbench-driver-receipt` v1 | `orchestration_driver.DriverManager` |
| Validated artifact receipt | `delivery-workbench-artifact-receipt` v1 | `orchestration_driver.validate_and_store_outputs` |
| Roadmap context | `delivery-workbench-roadmap-context` v1 | `api.build_context_payload` |
| Workbench envelope | `delivery-workbench-workbench-response` v1 | `workbench.envelope` (wraps every HTTP response) |
| Board | `delivery-workbench-board` v1 | `board.board_model` |
| Mission-control state feed | `feed_schema` 1 | [mission-control.md §1](./mission-control.md) |
| Rail events | taxonomy v1.1 (append-only JSONL) | [mission-control.md §3](./mission-control.md) |

## CLI (`dw`), machine-readable verbs

| Verb | Core function | Returns |
|---|---|---|
| `dw status [project] --json` | `status.build_status` | the stamped briefing; exit 0 `ready`, 1 `attention` |
| `dw step [project] --json` | `step.build_step` | pure state-bound preview; add `--apply --expect <token>` for exactly one closed-table action and the stamped result |
| `dw orchestration list --json` | `orchestration.score_inventory` | contained `pm/orchestration/*.json` inventory with validation and stable hashes |
| `dw orchestration show <score> --json` | `orchestration.compile_score` | normalized runtime score, layout, analysis, semantic hash, and document hash |
| `dw orchestration validate <score> --json` | `orchestration.validate_score` | exact-key verdict plus JSON-pointer diagnostics/remediation; exit 1 invalid |
| `dw orchestration simulate <score> --json` | `orchestration.simulate_score` | pure scheduling waves, locks, lineage, branches, budgets, checkpoints, and terminals |
| `dw run plan <score> --project <slug> --story <id> --json` | `orchestration_run.build_run_plan` | pure exact score/repository/status/story/capability/budget/expiry binding plus single-use start token |
| `dw run start --plan <file> --expect <token> --approve --operator <id> --json` | `orchestration_run.start_run` | immutable local grant and initial hash-chained projection; no node dispatch |
| `dw run list|show [<run>] --json` | `orchestration_run.run_inventory/replay_run` | authoritative ledger-derived projections; disposable cache is ignored |
| `dw run pause|resume|revoke|cancel <run> --expect <ledger-head> --json` | `orchestration_run.transition_run` | one exact append-only lifecycle transition that immediately gates future dispatch |
| `dw context [project] [--compact] [--trace]` | `api.build_context_payload` | the stamped roadmap context |
| `dw state --json` | `statefeed.build_state_feed` | the mission-control feed (`feed_schema` 1) |
| `dw next [project] --json` | `api.next_story` | the next actionable story or `{next_story: null, parked}` |
| `dw board [project] [--phase N] --json` | `board.board_model` | the stamped board model |
| `dw holds [project] --json` | `api.parked_summary` | paused phases + parked stories with notes, paths, links |
| `dw story show <project> <phase> <story> --json` | `api.story_detail` | one story whole: bodies, captured runs, paths, links |
| `dw sessions --json [--registry]` | `sessions.correlate_sessions` | live agent sessions correlated to stories |
| `dw events [--tail N]` | `events.read_events` | rail events, one JSON object per line |
| `dw check [project]` | `validate.check_project` | greppable `ERROR` lines (exit 1 on issues) |
| `dw gate --porcelain` | `gate.run_gate` | the gate verdict, machine-readable |
| `dw verify [range] --porcelain` | `verify.run_verify` | the history audit, machine-readable |

## Workbench HTTP (localhost/tailnet)

Served by `dw-workbench`; every response rides the stamped envelope.
Roadmap-content mutations use only `POST /api/mutations/preview` and
`POST /api/mutations/apply`. Orchestration-score content has its own
compiler-backed `POST /api/orchestration/preview|apply` pair. The deliberate
step has its own exact-token apply route; none accepts caller-supplied runtime
or provider argv.

| Route | Core function | Returns |
|---|---|---|
| `/api/status?project=<slug>` | `status.build_status` | the stamped briefing in `data`; `attention` remains HTTP 200 data |
| `GET /api/step?project=<slug>` | `step.build_step` | the stamped pure preview in `data` |
| `POST /api/step/apply` | `step.apply_step` | exact stamped result in `data`; 409 for a non-started refusal |
| `GET /api/orchestration` | `orchestration.score_inventory` | contained score inventory with validity and hashes; pure |
| `GET /api/orchestration/<score>` | shared compiler | raw score plus validation, compiled model, and simulation; pure |
| `POST /api/orchestration/preview` | `orchestration_edit.build_score_mutation_plan` | normalized save/delete diff, compiler verdict, and state fingerprint; no write/run/event |
| `POST /api/orchestration/apply` | `orchestration_edit.apply_score_mutation` | one fresh atomic score save/delete with read-back verification and rollback; never starts a run |
| `POST /api/mutations/preview` | guarded editor plan | content diff + state fingerprint; no write |
| `POST /api/mutations/apply` | guarded editor apply | applies only the matching fresh fingerprint inside `pm/roadmap` |
| `/api/context` | `api.build_context_payload` | the roadmap context |
| `/api/projects` | `workbench._project_summary` | per-project summaries (counts, next story) |
| `/api/projects/<slug>` | `api.project_context` | one project: phases, stories, parked summary |
| `/api/projects/<slug>/board` | `board.board_model` | the stamped board model |
| `/api/projects/<slug>/phases/<n>` | `api.project_context` | one phase + final-summary content |
| `/api/projects/<slug>/phases/<n>/events` | `api.phase_events` | recent commits scoped to the phase |
| `/api/projects/<slug>/stories/<id>` | `api.story_detail` | one story whole |
| `/api/projects/<slug>/trace/<id>` | `api.story_timeline` | the intent-to-proof chain + events |
| `/api/projects/<slug>/handoff/<id>` | `api.handoff_summary` | the agent handoff text |
| `/api/health` | `validate.health_report` | issues/warnings classified, hook snapshot |
| `/api/missioncontrol` | `statefeed` + `sessions` + `events` | the belt: feed, pins, off-belt, events |
| `/api/worklog?path=…` | contained read | one work-log artifact, verbatim |
| `/api/file?path=…` | contained read | one file inside the roadmap tree |

## MCP tools (`dw-mcp`, stdio)

The full tool table with input schemas lives in [mcp.md](./mcp.md);
this is the inventory. Read-only: `dw_status`, `dw_step`, `dw_context`, `dw_next`,
`dw_check`, `dw_doctor`, `dw_board`, `dw_holds`, `dw_story_show`,
`dw_verify`, `dw_gate`. Exact-token action: `dw_step_apply`. Guarded mutations: `dw_story_status`,
`dw_evidence_capture`, `dw_contract_new`. Certification is never a
tool call.

## The pin

A test (`test_interop_doc_names_every_surface`) derives the GET and POST route
inventories from `workbench.handle_api` / `handle_mutation` and the tool
inventory from the MCP registry, and fails if any surface is missing
from this document — a new surface cannot ship undocumented.
The same test pins the model stamps and CLI verbs; adapter parity tests compare
CLI JSON, MCP `structuredContent`, and HTTP envelope `data` without rewriting
the core object.
