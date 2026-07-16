# The interop contract — every read surface, named

Delivery Workbench exposes one read layer over three transports.
Every surface below derives live from the Markdown roadmap through
the same `dw_pmo` core — no second parser, no cache — and every
surface is **read-only**: the write path is exactly the guarded
preview→apply mutation flow plus the commit gate
(see [mcp.md](./mcp.md) for the mutation stance and
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
| Roadmap context | `delivery-workbench-roadmap-context` v1 | `api.build_context_payload` |
| Workbench envelope | `delivery-workbench-workbench-response` v1 | `workbench.envelope` (wraps every HTTP response) |
| Board | `delivery-workbench-board` v1 | `board.board_model` |
| Mission-control state feed | `feed_schema` 1 | [mission-control.md §1](./mission-control.md) |
| Rail events | taxonomy v1.1 (append-only JSONL) | [mission-control.md §3](./mission-control.md) |

## CLI (`dw`), machine-readable verbs

| Verb | Core function | Returns |
|---|---|---|
| `dw status [project] --json` | `status.build_status` | the stamped briefing; exit 0 `ready`, 1 `attention` |
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

## Workbench HTTP (GET, localhost/tailnet)

Served by `dw-workbench`; every response rides the stamped envelope.
Mutations exist only at `POST /api/mutations/preview` and
`POST /api/mutations/apply` (documented with the editor, not here).

| Route | Core function | Returns |
|---|---|---|
| `/api/status?project=<slug>` | `status.build_status` | the stamped briefing in `data`; `attention` remains HTTP 200 data |
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
this is the inventory. Read-only: `dw_status`, `dw_context`, `dw_next`,
`dw_check`, `dw_doctor`, `dw_board`, `dw_holds`, `dw_story_show`,
`dw_verify`, `dw_gate`. Guarded mutations: `dw_story_status`,
`dw_evidence_capture`, `dw_contract_new`. Certification is never a
tool call.

## The pin

A test (`test_interop_doc_names_every_surface`) derives the route
inventory from `workbench.handle_api`'s source and the tool
inventory from the MCP registry, and fails if any surface is missing
from this document — a new surface cannot ship undocumented.
The same test pins the status stamp and CLI verb; adapter parity tests compare
CLI JSON, MCP `structuredContent`, and HTTP envelope `data` without rewriting
the core object.
