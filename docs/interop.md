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
| Shared human presentation | `delivery-workbench-presentation` v1 | `presentation.build_*_presentation`; presentation-only and never a replacement for its exact source model |
| Status briefing | `delivery-workbench-status` v1 | `status.build_status` |
| Delivery setup | `delivery-workbench-delivery-setup` v1 | `delivery_setup.build_delivery_setup` |
| Deliberate-step preview | `delivery-workbench-step` v1 | `step.build_step` |
| Deliberate-step result | `delivery-workbench-step-result` v1 | `step.apply_step` |
| Orchestration score | `delivery-workbench-orchestration` v1 | `orchestration.validate_score` |
| Compiled orchestration | `delivery-workbench-compiled-orchestration` v1 | `orchestration.compile_score` |
| Orchestration validation | `delivery-workbench-orchestration-validation` v1 | `orchestration.validate_score` |
| Orchestration simulation | `delivery-workbench-orchestration-simulation` v1 | `orchestration.simulate_score` |
| Program policy | `delivery-workbench-program` v1 | `programs.validate_program` |
| Compiled program policy | `delivery-workbench-compiled-program` v1 | `programs.compile_program` |
| Workflow policy | `delivery-workbench-workflow` v1 | `program_workflow.validate_workflow` |
| Compiled workflow | `delivery-workbench-compiled-workflow` v1 | `program_workflow.compile_workflow` |
| Workflow inventory | `delivery-workbench-workflow-list` v1 | `program_workflow.workflow_inventory` |
| Workflow validation | `delivery-workbench-workflow-validation` v1 | `program_workflow.validate_workflow` |
| Workflow simulation | `delivery-workbench-workflow-simulation` v1 | `program_workflow.simulate_workflow` |
| Organization policy | `delivery-workbench-organization` v1 | `program_organization.validate_organization` |
| Compiled organization | `delivery-workbench-compiled-organization` v1 | `program_organization.compile_organization` |
| Organization inventory | `delivery-workbench-organization-list` v1 | `program_organization.organization_inventory` |
| Organization validation | `delivery-workbench-organization-validation` v1 | `program_organization.validate_organization` |
| Organization simulation | `delivery-workbench-organization-simulation` v1 | `program_organization.simulate_organization` |
| Pure team assignment | `delivery-workbench-team-assignment` v1 | `program_organization.assign_organization_team` |
| Pure assignment replacement | `delivery-workbench-assignment-replacement` v1 | `program_organization.plan_assignment_replacement` |
| Rubric policy | `delivery-workbench-rubric` v1 | `program_verdict.validate_rubric` |
| Compiled rubric | `delivery-workbench-compiled-rubric` v1 | `program_verdict.compile_rubric` |
| Rubric inventory | `delivery-workbench-rubric-list` v1 | `program_verdict.rubric_inventory` |
| Rubric validation | `delivery-workbench-rubric-validation` v1 | `program_verdict.validate_rubric` |
| Mechanical receipt | `delivery-workbench-mechanical-receipt` v1 | `program_verdict` trusted receipt input |
| Mechanical fact | `delivery-workbench-mechanical-fact` v1 | `program_verdict.build_mechanical_fact` |
| Verdict assignment | `delivery-workbench-verdict-assignment` v1 | `program_verdict.build_verdict_assignment` |
| Governed verdict | `delivery-workbench-verdict` v1 | `program_verdict.issue_agent_verdict` |
| Quality gate | `delivery-workbench-quality-gate` v1 | `program_verdict.evaluate_quality_gate` |
| Quality proof | `delivery-workbench-quality-proof` v1 | `program_verdict.evaluate_quality_gate` |
| Program inventory | `delivery-workbench-program-list` v1 | `programs.program_inventory` |
| Program validation | `delivery-workbench-program-validation` v1 | `programs.validate_program` |
| Program simulation | `delivery-workbench-program-simulation` v1 | `programs.simulate_program` |
| Pure program plan | `delivery-workbench-program-plan` v1 | `programs.build_program_plan` |
| Program start plan | `delivery-workbench-program-start-plan` v1 | `program_run.build_program_start_plan` |
| Program grant | `delivery-workbench-program-grant` v1 | `program_run.start_program` |
| Program event | `delivery-workbench-program-event` v1 | `program_run` ledger |
| Program projection | `delivery-workbench-program-projection` v1 | `program_run.replay_program` |
| Program claim preview | `delivery-workbench-program-claim-preview` v1 | `program_run.build_program_claim_preview` |
| Program completion preview | `delivery-workbench-program-completion-preview` v1 | `program_run.build_program_completion_preview` |
| Program control preview | `delivery-workbench-program-control-preview` v1 | `program_run.build_program_control_preview` |
| Program child grant | `delivery-workbench-program-child-grant` v1 | `program_run.derive_child_grant` |
| Program run inventory | `delivery-workbench-program-run-list` v1 | `program_run.program_run_inventory` |
| Program act preview | `delivery-workbench-program-act-preview` v1 | `program_surface.build_program_act_preview` |
| Program control-room view | `delivery-workbench-program-view` v1 | `program_surface.build_program_view` |
| Program summary inventory | `delivery-workbench-program-summary-list` v1 | `program_surface.program_summary_inventory` |
| Public program tick | `delivery-workbench-program-surface-tick` v1 | `program_surface.tick_program_surface` |
| Public program supervision | `delivery-workbench-program-surface-supervision` v1 | `program_surface.supervise_program_surface` |
| Verified program tail | `delivery-workbench-program-tail` v1 | `program_surface.tail_program_events` |
| Explicit program stream | `delivery-workbench-program-stream` v1 | `program_surface.read_program_stream` |
| Deliberation plan | `delivery-workbench-deliberation-plan` v1 | `program_deliberation.compile_deliberation_plan` |
| Deliberation event | `delivery-workbench-deliberation-event` v1 | `program_deliberation` event chain |
| Deliberation projection | `delivery-workbench-deliberation-projection` v1 | `program_deliberation.replay_deliberation` |
| Deliberation simulation | `delivery-workbench-deliberation-simulation` v1 | `program_deliberation.simulate_deliberation` |
| Council round verdict | `delivery-workbench-council-verdict` v1 | `program_deliberation` |
| Meta-verifier verdict | `delivery-workbench-meta-verdict` v1 | `program_deliberation` |
| Architecture verdict | `delivery-workbench-architecture-verdict` v1 | `program_deliberation` |
| Council decision | `delivery-workbench-decision` v1 | `program_deliberation.validate_council_decision` |
| Program Studio overview | `delivery-workbench-program-studio` v1 | `program_studio.build_program_studio` |
| Program Studio document | `delivery-workbench-program-studio-document` v1 | `program_studio.build_studio_document` |
| Program Studio graph | `delivery-workbench-program-studio-graph` v1 | `program_studio.build_studio_graph` |
| Program Studio authority preview | `delivery-workbench-program-studio-authority-preview` v1 | `program_studio.build_authority_preview` |
| Program Studio round trip | `delivery-workbench-program-studio-round-trip` v1 | `program_studio.graph_config_round_trip` |
| Delivery-plan authoring view | `delivery-workbench-delivery-plan-authoring` v1 | `plan_authoring.build_delivery_plan_authoring` |
| Team-and-review application view | `delivery-workbench-team-review` v1 | `team_review.build_team_review` / `team_review.build_live_team_review` |
| Live delivery progress view | `delivery-workbench-live-progress` v1 | `live_progress.build_run_live_progress` / `live_progress.build_program_live_progress` |
| Bounded delivery actions view | `delivery-workbench-bounded-actions` v1 | `bounded_actions.build_run_bounded_actions` / `bounded_actions.build_program_bounded_actions` |
| Program Studio mutation preview | `delivery-workbench-program-studio-mutation-preview` v1 | `program_studio.studio_mutation_preview` |
| Program Studio mutation result | `delivery-workbench-program-studio-mutation-result` v1 | `program_studio.apply_studio_mutation` |
| Program frontier | `delivery-workbench-program-frontier` v1 | `program_conductor.derive_program_frontier` |
| Program conductor tick | `delivery-workbench-program-tick` v1 | `program_conductor.tick_program` |
| Program conductor supervision | `delivery-workbench-program-supervision` v1 | `program_conductor.supervise_program` |
| Program conductor receipt | `delivery-workbench-program-conductor-receipt` v1 | `program_conductor.replay_program_conductor` |
| Typed program request result | `delivery-workbench-program-request-result` v1 | `program_conductor.respond_program_request` |
| Program artifact receipt | `delivery-workbench-program-artifact-receipt` v1 | `program_conductor.ProgramDriverManager` |
| Program driver operation | `delivery-workbench-program-driver-operation` v1 | `program_conductor.ProgramDriverManager` |
| Orchestration run plan | `delivery-workbench-run-plan` v1 | `orchestration_run.build_run_plan` |
| Orchestration run grant | `delivery-workbench-run-grant` v1 | `orchestration_run.start_run` |
| Orchestration run event | `delivery-workbench-run-event` v1 | `orchestration_run` ledger |
| Orchestration run projection | `delivery-workbench-run` v1 | `orchestration_run.replay_run` |
| Orchestration run-act preview | `delivery-workbench-run-act-preview` v1 | `orchestration_surface.build_run_act_preview` |
| Orchestration Run view | `delivery-workbench-run-view` v1 | `orchestration_surface.build_run_view` |
| Explicit bounded run stream | `delivery-workbench-run-stream` v1 | `orchestration_surface.read_run_stream` |
| Mission-control run summary | `delivery-workbench-run-summary-list` v1 | `orchestration_surface.run_summary_inventory` |
| Driver capability | `delivery-workbench-driver-capability` v1 | `orchestration_driver.driver_capability` |
| Agent work packet | `delivery-workbench-work-packet` v1 | `orchestration_driver.build_work_packet` |
| Driver receipt | `delivery-workbench-driver-receipt` v1 | `orchestration_driver.DriverManager` |
| Validated artifact receipt | `delivery-workbench-artifact-receipt` v1 | `orchestration_driver.validate_and_store_outputs` |
| Conductor decision | `delivery-workbench-conductor-decision` v1 | `orchestration_conductor.schedule_decision` |
| Conductor tick | `delivery-workbench-conductor-tick` v1 | `orchestration_conductor.tick_run` |
| Conductor supervision | `delivery-workbench-conductor-supervision` v1 | `orchestration_conductor.supervise_run` |
| Exact check receipt | `delivery-workbench-check-receipt` v1 | `orchestration_conductor.CheckManager` |
| Rail-step receipt | `delivery-workbench-rail-receipt` v1 | `orchestration_conductor.RailManager` |
| Roadmap context | `delivery-workbench-roadmap-context` v1 | `api.build_context_payload` |
| Workbench envelope | `delivery-workbench-workbench-response` v1 | `workbench.envelope` (wraps every HTTP response) |
| Board | `delivery-workbench-board` v1 | `board.board_model` |
| Mission-control state feed | `feed_schema` 1 | [mission-control.md §1](./mission-control.md) |
| Rail events | taxonomy v1.1 (append-only JSONL) | [mission-control.md §3](./mission-control.md) |

## CLI (`dw`), machine-readable verbs

| Verb | Core function | Returns |
|---|---|---|
| `dw status [project] --json` | `status.build_status` | the stamped briefing; exit 0 `ready`, 1 `attention` |
| `dw knowledge map [--json]` | `repository_map.read_symbol_map` | the cached symbol, module, test, and named-gap map only when its index tree is current; otherwise refuses |
| `dw knowledge ground <project> <story> [--json]` | `grounding.ground_project_story` | advisory verified/new/unknown localization results from a fresh map plus bounded tracked-blob text fallback; read-only and refuses stale knowledge |
| `dw knowledge lessons [--json]` | `knowledge.build_lesson_inventory` | append-only machine lessons with run, HEAD, timestamp, location-resolution, age, and supersession provenance; advisory only |
| `dw knowledge refresh [--json]` | `repository_map.refresh_symbol_map` | an explicit incremental refresh of the disposable derived map; reads tracked blobs and changes no authoritative state |
| `dw setup [project] [--technical]` | `delivery_setup.build_delivery_setup` | human guidance over the same three delivery choices and readiness used by Workbench; intentionally no JSON mode, write, grant, or start |
| `dw step [project] --json` | `step.build_step` | pure state-bound preview; add `--apply --expect <token>` for exactly one closed-table action and the stamped result |
| `dw orchestration list --json` | `orchestration.score_inventory` | contained `pm/orchestration/*.json` inventory with validation and stable hashes |
| `dw orchestration show <score> --json` | `orchestration.compile_score` | normalized runtime score, layout, analysis, semantic hash, and document hash |
| `dw orchestration validate <score> --json` | `orchestration.validate_score` | exact-key verdict plus JSON-pointer diagnostics/remediation; exit 1 invalid |
| `dw orchestration simulate <score> --json` | `orchestration.simulate_score` | pure scheduling waves, locks, lineage, branches, budgets, checkpoints, and terminals |
| `dw organization list --json` | `program_organization.organization_inventory` | healthy empty inventory or direct-contained organization validation/hash summaries; pure |
| `dw organization validate <organization> --json` | `program_organization.validate_organization` | closed role/capability/visibility/cardinality/independence/council/replacement policy plus logical feasibility diagnostics; exit 1 invalid |
| `dw organization simulate <organization> --json` | `program_organization.simulate_organization` | logical assignment witnesses, packet policies, council aggregation/audit/budgets, and resource-compatible concurrency waves; pure |
| `dw workflow list --json` | `program_workflow.workflow_inventory` | healthy empty inventory or contained source-aware template validation plus finite envelope/hash summaries; pure |
| `dw workflow validate <workflow> --json` | `program_workflow.validate_workflow` | closed parameters/nodes/routes, exact nested version/hash and bounded-score references, recursion/cycle/capability/envelope diagnostics; exit 1 invalid |
| `dw workflow simulate <workflow> --json` | `program_workflow.simulate_workflow` | namespaced hierarchy, fan waves, typed route outcomes, concrete bounded rounds, debate byte/token/route proof, per-node/route/worst-case envelopes, source provenance, and capability consumers; pure |
| `dw rubric list --json` | `program_verdict.rubric_inventory` | healthy empty inventory or direct-contained rubric validation/hash summaries; pure |
| `dw rubric validate <rubric> --json` | `program_verdict.validate_rubric` | exact criteria, evidence/citation, aggregation/veto and freshness policy with source-aware diagnostics; exit 1 invalid |
| `dw program list --json` | `programs.program_inventory` | healthy empty inventory when no program is configured; otherwise contained policy validation/hashes; pure |
| `dw program validate <program> --json` | `programs.validate_program` | exact-key policy/reference/scope/binding verdict plus source-aware diagnostics; exit 1 invalid |
| `dw program simulate <program> --json` | `programs.simulate_program` | every roadmap candidate reason plus deterministic workflow/team/role assignment; explicitly no work/state/grant |
| `dw program plan <program> --json` | `programs.build_program_plan` | without `--mode`: repository/roadmap snapshot, selected story, workflow/team/roles, policy/roster hashes, and complete derivation; pure |
| `dw program plan <program> --mode <mode> … --json` | `program_run.build_program_start_plan` | pure exact finite-grant preview with a single-use `start_token`; creates no grant or child |
| `dw program start --plan <file> --expect <token> --approve --json` | `program_surface.start_program_by_id` | rebuilds the reviewed plan from its ids and bounded scalar request, then issues exactly one local grant; starts no child |
| `dw program show <run> --json` | `program_surface.build_program_view` | canonical content-safe control-room projection with the shared live-progress and bounded-actions views plus exact lineage, organization, activity, quality/dissent, gates, obligations, deliveries, limits, controls, and verified timeline |
| `dw program preview <run> <action> --json` | `program_surface.build_program_act_preview` | pure action/closed-parameters/ledger-bound preview and exact `act_token` |
| `dw program tick <run> --expect <act-token> --json` | `program_surface.apply_program_act` | exactly one conductor, delivery-plan, or delivery tick through the existing grant and ledger |
| `dw program supervise <run> --max-ticks <n> --max-seconds <s> --expect <act-token> --json` | `program_surface.apply_program_act` | explicit finite repetition of the same public tick; returns every tick and stops on no-progress, checkpoint, refusal, budget, duration, or terminal state |
| `dw program request <run> <request> approve\|reject --reason <text> --expect <act-token> --json` | `program_surface.apply_program_act` | one closed typed response to one exact outstanding request |
| `dw program pause <run> --reason <text> --expect <act-token> --json` | `program_surface.apply_program_act` | one freshly previewed pause |
| `dw program resume <run> --reason <text> --expect <act-token> --json` | `program_surface.apply_program_act` | one freshly previewed resume after grant facts are re-observed |
| `dw program revoke <run> --reason <text> --expect <act-token> --json` | `program_surface.apply_program_act` | one permanent, ledgered revocation |
| `dw program cancel <run> --reason <text> --expect <act-token> --json` | `program_surface.apply_program_act` | one ledgered cancellation before bounded interruption |
| `dw program tail <run> [--after N] [--follow]` | `program_surface.tail_program_events` | verified canonical ledger suffix; `--json` returns the stamped bounded tail and is intentionally incompatible with follow |
| `dw program stream <run> <session> stdout\|stderr --json` | `program_surface.read_program_stream` | one explicitly opened content-safe log, independently bounded to 100,000 bytes |
| `dw notifications list --json` | `notifications.build_notifications` | derived operator notifications (pending/republished/expired requests, terminals, blocked stops, opt-in branch signals) with affected work, exact response guidance, unread, and delivery state; pure (exit 2 when none) |
| `dw notifications ack <id>` | `notifications.acknowledge_notification` | idempotent, receipted acknowledgement in the local ack log |
| `dw notifications delivered <id> [--channel C] [--failed reason]` | `notifications.record_delivery` | one recorded delivery-attempt outcome for a channel consumer (ceiling-bounded retries) |
| `dw signals list [--remote R] [--branch B] --json` | `signals.build_signals_inventory` | observed channels with hash-chained facts and read-time derived status; pure (exit 2 when none) |
| `dw signals observe [--remote R] [--branch B] [--provider github\|fixture] --json` | `signals.observe_signals` | one bounded observe pass: semantic-diffed appends and content-free refusals; stamps `starts_work: false` |
| `dw run plan <score> --project <slug> --story <id> --json` | `orchestration_run.build_run_plan` | pure exact score/repository/status/story/capability/budget/expiry binding plus single-use start token |
| `dw run start --plan <file> --expect <token> --approve --operator <id> --json` | `orchestration_run.start_run` | immutable local grant and initial hash-chained projection; no node dispatch |
| `dw run list|show [<run>] --json` | `orchestration_run.run_inventory/replay_run` | authoritative ledger-derived projections, including outstanding requests and their history; disposable cache is ignored |
| `dw run view <run> --json` | `orchestration_surface.build_run_view` | pure content-safe live-progress and bounded-actions views plus exact graph, attempts, sessions/checks, artifact lineage, limits, routes, outstanding requests, inspect-only decision lineage, controls, and ledger |
| `dw run preview <run> <act> --json` | `orchestration_surface.build_run_act_preview` | pure action+parameters+correlation+ledger-bound consent document and exact `act_token` |
| `dw run pause|resume|revoke|cancel <run> --expect <act-token> --json` | `orchestration_surface.apply_run_act` | one exact preview-confirm lifecycle transition that immediately gates future dispatch |
| `dw run tick <run> --expect <act-token> --json` | `orchestration_surface.apply_run_act` → `orchestration_conductor.tick_run` | one explicitly confirmed replay/reconcile/route/schedule boundary with exact receipts and no hidden continuation |
| `dw run supervise <run> --max-ticks <n> --interval <s> --json` | `orchestration_conductor.supervise_run` | bounded repetition over `tick_run`, stopping at terminal/pause/approval/no-progress |
| `dw run request <run> <correlation> <decision> --expect <act-token> --json` | `orchestration_surface.apply_run_act` → `orchestration_run.decide_outstanding_request` | one fresh typed response over the exact outstanding request; schema/correlation refusals are ledgered and leave the request live |
| `dw run checkpoint <run> approve|reject [--correlation <id>] --expect <act-token> --json` | generic request boundary → `orchestration_run.decide_checkpoint` | compatibility alias for the exact pending checkpoint request |
| `dw run stream <run> agent|check <execution> stdout|stderr --json` | `orchestration_surface.read_run_stream` | one explicitly opened log, independently bounded to 100,000 bytes; never a list/feed/event field |
| `dw run tail <run> [--after N] [--follow]` | `orchestration_surface.tail_run_events` | the verified hash-chained ledger suffix after a cursor, one canonical event JSON per line; pure read, no tokens or content bodies |
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

The individual lifecycle spellings are `dw run show`, `dw run pause`,
`dw run resume`, `dw run revoke`, and `dw run cancel`; the grouped rows above
do not imply a combined command.

## Delivered Phase 26 program surface

`program_surface` is the one public projection and exact-act seam over the
existing program compiler, grant, conductor, and delivery cores. CLI JSON, MCP
`structuredContent`, HTTP envelope `data`, Workbench bootstrap, and SSE cursor
replay adapt its canonical documents instead of reconstructing program state.
Reads start no store, process, observer, notification, poller, or stream.

Every public mutation is a preview→exact-token act over the sole program
ledger. Act schemas accept ids, bounded reasons, closed approve/reject
decisions, finite supervision ceilings, reviewed grant scalars, and exact
tokens only. They do not accept policy documents, role assignments, prompts,
rubrics, checks, capabilities at tick time, credentials, commands, or retry
overrides. The conductor still owns agent/check/council/loop work;
`program_delivery` still owns separately claimed integration/Git/roadmap acts.
The surface adds no authority or hidden scheduler.

## Workbench HTTP (localhost/tailnet)

Served by `dw-workbench`; every response rides the stamped envelope.
Roadmap-content mutations use only `POST /api/mutations/preview` and
`POST /api/mutations/apply`. Orchestration-score content has its own
compiler-backed `POST /api/orchestration/preview|apply` pair. The deliberate
step has its own exact-token apply route; none accepts caller-supplied runtime
or provider argv.

| Route | Core function | Returns |
|---|---|---|
| `GET /api/presentation` | `presentation.build_presentation_catalog` | shared preferred terms, labels, and the explicit Technical details boundary used by human adapters; pure |
| `GET /api/presentation/status?project=<slug>` | `presentation.build_status_presentation` over `status.build_status` | task-first status presentation with source paths; the exact status remains available separately |
| `/api/status?project=<slug>` | `status.build_status` | the stamped briefing in `data`; `attention` remains HTTP 200 data |
| `GET /api/delivery-setup?project=<slug>` | `delivery_setup.build_delivery_setup` | pure application view over status, delivery-plan inventory, and optional-program inventory: delivery scope, all three choices, effects, remaining permission, corrections, and technical sources |
| `GET /api/step?project=<slug>` | `step.build_step` | the stamped pure preview in `data` |
| `POST /api/step/apply` | `step.apply_step` | exact stamped result in `data`; 409 for a non-started refusal |
| `POST /api/setup/preview` | `setup_lease.preview_setup` | canonical complete tracked/local change set and one typed setup lease in `data`; no tracked write or work start |
| `POST /api/setup/apply` | `setup_lease.apply_setup` | exact proposal id plus setup token only; revalidated journaled all-or-nothing setup in `data` |
| `GET /api/orchestration` | `orchestration.score_inventory` | contained score inventory with validity and hashes; pure |
| `GET /api/orchestration/<score>` | shared compiler | raw score plus validation, compiled model, and simulation; pure |
| `GET /api/orchestration/<score>/compiled` | `orchestration.compile_score_path` | byte-identical compiled score in `data` |
| `GET /api/orchestration/<score>/simulation` | `orchestration.simulate_score` | byte-identical pure simulation in `data` |
| `GET /api/program-studio` | `program_studio.build_program_studio` | healthy optional policy inventory plus shared family/compiler metadata; pure and neutral when empty |
| `GET /api/program-studio/<family>/<name>` | `program_studio.build_studio_document` | selected program/workflow/organization source plus task-shaped delivery-plan authoring and, for organizations, the shared team-and-review application view; validation, graph, simulation, and authority projections remain pure |
| `GET /api/notifications` | `notifications.build_notifications` | the derived notification inventory in `data`; pure |
| `POST /api/notifications/ack` | `notifications.acknowledge_notification` | receipted idempotent acknowledgement of one notification id |
| `GET /api/signals?remote=…&branch=…` | `signals.build_signals_inventory` | observed outward channels and derived status in `data`; pure, never an observe pass |
| `POST /api/orchestration/preview` | `orchestration_edit.build_score_mutation_plan` | normalized save/delete diff, compiler verdict, and state fingerprint; no write/run/event |
| `POST /api/orchestration/apply` | `orchestration_edit.apply_score_mutation` | one fresh atomic score save/delete with read-back verification and rollback; never starts a run |
| `POST /api/program-studio/preview` | `program_studio.build_studio_mutation_plan` | one selected policy save/delete diff, compiler projections and stale fingerprint; no grant/run/agent/check/roadmap effect |
| `POST /api/program-studio/apply` | `program_studio.apply_studio_mutation` | one fresh direct-contained policy save/delete with read-back validation and explicit false runtime effects |
| `GET /api/programs` | `program_surface.program_summary_inventory` | healthy empty policy/run inventory in ordinary mode, otherwise canonical content-safe run summaries; pure |
| `GET /api/programs/<run>` / `GET /api/programs/<run>/view` | `program_surface.build_program_view` | the same canonical control-room document returned by CLI and MCP, including the shared live-progress and bounded-actions application views |
| `GET /api/programs/<run>/act/<action>` / `POST /api/programs/preview` | `program_surface.build_program_act_preview` | pure exact action preview; POST carries bounded reason/decision/request/ceiling fields outside the URL |
| `GET /api/programs/<run>/tail?after=N&limit=N` | `program_surface.tail_program_events` | stamped bounded verified ledger suffix; no token or mutation authority |
| `GET /api/programs/<run>/streams/<session>/<stdout\|stderr>` | `program_surface.read_program_stream` | one explicit independently bounded session log; never included in list/view/event payloads |
| `GET /api/programs/<run>/events` (SSE) | `program_surface.tail_program_events` | `program-ledger` events with `Last-Event-ID`/`from` replay of the exact missed suffix; read-only and never a scheduler |
| `POST /api/programs/plan` | `program_run.build_program_start_plan` | exact pure grant preview from a program id and reviewed scalar bounds |
| `POST /api/programs/start` | `program_surface.start_program_by_id` | rebuilds and consumes one exact approved start token; grant creation dispatches nothing |
| `POST /api/programs/tick` | `program_surface.apply_program_act` | one exact public program tick |
| `POST /api/programs/supervise` | `program_surface.apply_program_act` | explicit finite repetition under the previewed tick/time ceilings |
| `POST /api/programs/request` | `program_surface.apply_program_act` | one exact closed response to one outstanding typed request |
| `POST /api/programs/pause` | `program_surface.apply_program_act` | one exact pause with a bounded reason |
| `POST /api/programs/resume` | `program_surface.apply_program_act` | one exact fresh resume with a bounded reason |
| `POST /api/programs/revoke` | `program_surface.apply_program_act` | one exact permanent revocation with a bounded reason |
| `POST /api/programs/cancel` | `program_surface.apply_program_act` | one exact ledgered cancellation with a bounded reason |
| `GET /api/run-plan?score=…&project=…&story=…` | `orchestration_run.build_run_plan` | exact pure grant/start preview; identifiers and timestamps only |
| `GET /api/runs` | `orchestration_run.run_inventory` | authoritative local projections; no prompts, argv, source, transcripts, or artifact bytes |
| `GET /api/runs/<run>` | `orchestration_run.replay_run` | byte-identical projection in `data` |
| `GET /api/runs/<run>/view` | `orchestration_surface.build_run_view` | pure live-progress and bounded-actions explanation used by Workbench Run; exact consent remains a separate preview |
| `GET /api/runs/<run>/act/<action>` / `POST /api/runs/preview` | `orchestration_surface.build_run_act_preview` | exact pure act preview; POST carries bounded reason/decision/correlation fields and keeps them out of the address bar |
| `POST /api/runs/start` | `orchestration_surface.start_run_by_id` | identifiers/timestamps/token/approval only; grant creation dispatches nothing |
| `POST /api/runs/tick`, `POST /api/runs/pause`, `POST /api/runs/resume`, `POST /api/runs/revoke`, `POST /api/runs/cancel`, `POST /api/runs/request`, `POST /api/runs/checkpoint` | `orchestration_surface.apply_run_act` | exact preview token plus only its bound reason/decision/correlation; stale is HTTP 409; checkpoint is a compatibility alias |
| `GET /api/runs/<run>/streams/<executor>/<execution>/<stream>` | `orchestration_surface.read_run_stream` | explicit bounded stdout/stderr; no packets, prompts, final message, or artifact content |
| `GET /api/runs/<run>/events` (SSE) | `orchestration_surface.tail_run_events` | live hash-chained ledger tail; `Last-Event-ID`/`from` cursor replays the exact missed suffix; read-only — no token or mutation is reachable from the stream |
| `GET /api/signals/events?remote=…&branch=…` (SSE) | `orchestration_surface.tail_signal_events` | live signal-chain tail with the same cursor-replay and no-authority posture |
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
this is the inventory. Read-only: `dw_status`, `dw_knowledge_map`,
`dw_knowledge_ground`, `dw_knowledge_lessons`, `dw_step`, `dw_context`,
`dw_next`, `dw_check`, `dw_doctor`, `dw_board`, `dw_holds`,
`dw_story_show`, `dw_verify`, `dw_gate`, `dw_orchestration_list`,
`dw_signals`, `dw_notifications`, `dw_orchestration_show`,
`dw_orchestration_simulate`, `dw_program_list`, `dw_program_show`,
`dw_program_validate`, `dw_program_simulate`, `dw_program_plan`,
`dw_program_preview`, `dw_program_tail`,
`dw_run_plan`, `dw_run_list`, `dw_run_show`, `dw_run_view`, and
`dw_run_preview`.
Setup lease tools: `dw_setup_preview` validates a reviewed proposal and records only its pending Git-local lease; `dw_setup_apply` accepts only that proposal id and exact typed token, then lands the complete setup atomically. Exact-token actions: `dw_step_apply`, `dw_program_start`, `dw_program_tick`,
`dw_program_supervise`, `dw_program_request`, `dw_program_pause`,
`dw_program_resume`, `dw_program_revoke`, `dw_program_cancel`,
`dw_run_start`, `dw_run_tick`,
`dw_run_pause`, `dw_run_resume`, `dw_run_revoke`, `dw_run_cancel`,
`dw_run_request`, and the checkpoint-compatible `dw_run_checkpoint`. The
explicitly opened and bounded `dw_program_stream` and `dw_run_stream` are
the only program/run tools returning log content. Other guarded mutations:
`dw_story_status`, `dw_evidence_capture`, `dw_contract_new`, and the
receipted idempotent `dw_notifications_ack`.
Certification and commit are never tool calls.

## The pin

A test (`test_interop_doc_names_every_surface`) derives the GET and POST route
inventories from `workbench.handle_api` / `handle_mutation` and the tool
inventory from the MCP registry, and fails if any surface is missing
from this document — a new surface cannot ship undocumented.
The same test pins the model stamps and CLI verbs; adapter parity tests compare
CLI JSON, MCP `structuredContent`, and HTTP envelope `data` without rewriting
the core object.
