# Evidence - WLA-26-11

- **Story:** WLA-26-11 - Operate the autonomous organization across every
  surface
- **Status:** done
- **Date:** 2026-07-23

## Proof

### One canonical program model across every adapter

- `program_surface.py` adds the shared
  `delivery-workbench-program-surface@1` projection over the existing pure
  planner, program authority ledger, conductor, and delivery protocol. It owns
  inventory, control-room detail, tail, explicit bounded stream reads, grant
  plan/start, exact act preview/apply, one-act tick, and bounded supervision.
  It creates no second policy compiler, scheduler, state store, or authority
  path.
- CLI JSON, MCP `structuredContent`, HTTP `data`, Workbench bootstrap, and SSE
  replay frame that same canonical payload. Integration tests create one real
  grant/ledger and compare the normalized documents at one observation head;
  tails and SSE preserve the same verified event hashes and cursor semantics.
- The CLI exposes `program list|show|validate|simulate|plan|start|preview|tick|
  supervise|request|pause|resume|revoke|cancel|tail|stream`. MCP exposes 16
  version-pinned tools with closed schemas. HTTP exposes additive
  `/api/programs/*` reads, previews, acts, SSE, and stream endpoints using
  strict scalar allowlists.
- Reads contain no exact act token or mutation authority. Program tail is
  bounded, SSE is a verified replay with an explicit cursor, and stdout/stderr
  is an explicit bounded open against a named session and stream.

### Dormant compatibility and exact public acts

- With no configured program, inventory is a healthy empty
  `delivery-workbench-program-inventory@1` document. It explicitly reports
  that no store, work, process, poller, stream, grant, or notification was
  created or started. Opening the ordinary CLI, MCP server, HTTP server,
  Workbench, or Program Studio does not activate program machinery.
- Public mutation accepts only identifiers, bounded scalar ceilings/reasons,
  a closed typed decision, and a fresh exact token. Policy documents, role
  assignment, prompts, rubrics, checks, capabilities, credentials, arbitrary
  commands, and retry overrides are absent from the applying schemas and
  rejected if supplied.
- Every act preview binds the program, grant hash, ledger head, assignment
  generation, current state, derived operation, capability, budget, and closed
  parameters. Apply independently re-derives that binding while holding the
  authority-owning conductor, delivery, or ledger lock.
- A barrier-driven real concurrency test makes two public tick clients race
  from the same observed head. Exactly one client records the single receipt;
  the loser receives a stale-binding refusal. This proves adapter-level
  preview/apply cannot turn a stale observation into two successful claims.
- `supervise` is an explicit local finite loop over the same one-act tick. It
  exposes every tick and stops on checkpoint, no progress, terminal state,
  budget, tick ceiling, or duration ceiling. No browser, SSE route, or
  notification creates a hidden supervisor.

### Explanatory control room and portable execution policy

- The responsive Workbench program inventory exposes healthy dormant state,
  pure authority previews, and explicit start. A selected program control room
  explains why the roadmap story/phase, workflow, team, and next act are
  current; exact role and execution provenance; independence; councils,
  perspectives, decider source, and rounds; nested activity and child runs;
  artifacts, mechanical facts, governed verdicts, dissent and obligations;
  gates, delivery, budgets, capabilities, refusals, and the verified timeline.
- The browser opens SSE only after navigating to an explicit program run,
  closes it on route exit, performs no hidden authority polling, and opens
  output only through a labeled bounded stream action. Accessible labels,
  mobile stacking, wrapped identifiers, and content-safe renderers preserve
  the same information at desktop and mobile sizes.
- Program Studio projects portable exact/constrained logical execution
  profiles through the locally registered harness, adapter, router/provider,
  model, principal/auth-domain and workspace availability. It shows fallback
  and replacement policy, provider/model/principal diversity, council
  perspectives, rule-versus-judge authority, veto and obligation policy, and
  stable fingerprints without credentials, arbitrary argv, or activation.
- The browser matrix renders 58 desktop/mobile states. Existing Studio
  specimens cover planning, team assignment, nested execution, debate,
  verifier repair, meta-overturn, phase transition, budget stop, and complete;
  real program-ledger fixtures add active and revoked control-room states.

### Typed notifications and transport separation

- Notifications are derived only from a verified canonical program view and
  cover intervention required, disagreement, decider loss, provider loss,
  architect veto, new/blocking/overdue obligation, budget exhaustion,
  integration refusal, and program completion.
- Outbound content is bounded and content-safe; it contains neither ledger
  act tokens nor credentials, prompts, command lines, raw logs, or private
  reasoning. Delivery and acknowledgement remain notification transport, not
  program authority.
- A phone/client response is a closed approve/reject request result with a
  bounded reason. Correlation resolves the exact open program request, but a
  fresh act preview and token are created only at the local apply boundary.
  Expiry, replay, and stale-head behavior remain explicit refusals.

### Packaging, documentation, and compatibility

- Source and vendored packages contain the same shared surface and adapters;
  fresh-wheel smoke asserts the packaged module, import surface, MCP inventory,
  HTTP routes, and CLI help.
- Root/framework READMEs, solution overview, architecture, orchestration,
  interop, MCP, autonomous-program contract, Unreleased changelog, story,
  status, evidence, and handover now describe the public operations and leave
  only WLA-26-12's installed multi-phase exam.
- Existing vanilla, bounded-run, conductor, delivery, notification, and
  Workbench behavior remains covered alongside the new additive program paths.

## Verification summary

- `ProgramSurfaceTest`: 7/7 public parity, dormant-state, strict-input,
  bounded-supervision, race, request, and notification tests.
- `ProgramConductorTest`: 20/20 replay, checkpoint, structural-loop,
  independent-verification, delivery handoff, and versioned-adapter tests.
- Python 3.9 public surface plus Program Studio: 16/16.
- MCP, Program Studio, notification, interop, and Workbench route contract
  selection: 29/29.
- Full core suite: 472/472 on Python 3.14 and 472/472 on the Python 3.9 floor.
- Fresh-wheel Python 3.9 packaging passed: sdist and wheel build/install,
  packaged module/import/CLI/MCP/HTTP checks, guided and deliberate-step loops,
  multi-agent orchestration with zero duplicate restarts, and outward
  orchestration with zero duplicate starts/nudges.
- Workbench explorer passed; the expanded browser smoke rendered 58
  desktop/mobile views including real active and revoked program ledgers.
- Python compilation on both floors, canon lint, all Markdown, executable
  documentation snippets, agent surfaces, roadmap validation, rendered rider,
  source/vendored update parity, the exact CI ShellCheck set, and diff checks
  passed.

## Captured validation - 2026-07-23

```text
$ python3 pmo-roadmap/tests/dw-core-tests.py -q ProgramSurfaceTest
Ran 7 tests in 14.640s
OK

$ /usr/bin/python3 pmo-roadmap/tests/dw-core-tests.py -q \
    ProgramSurfaceTest ProgramStudioTest
Ran 16 tests in 13.644s
OK

$ python3 pmo-roadmap/tests/dw-core-tests.py -q ProgramConductorTest
Ran 20 tests in 390.423s
OK

$ python3 pmo-roadmap/tests/dw-core-tests.py -q MCPServerTest \
    ProgramStudioTest \
    OrchestrationConductorTest.test_notifications_derive_ack_and_correlate \
    OrchestrationConductorTest.test_notifications_delivery_ceiling_parity_and_branch_opt_in \
    OrchestrationConductorTest.test_request_expiry_is_a_recorded_refusal_and_notification \
    DwCoreTest.test_missioncontrol_readonly_fitness_guard \
    DwCoreTest.test_interop_doc_names_every_surface
Ran 29 tests in 5.703s
OK

$ python3 pmo-roadmap/tests/dw-core-tests.py -q
Ran 472 tests in 794.819s
OK

$ /usr/bin/python3 pmo-roadmap/tests/dw-core-tests.py -q
Ran 472 tests in 740.368s
OK

$ pmo-roadmap/tests/package-smoke.sh
package-smoke.sh: built delivery_workbench-1.14.0-py3-none-any.whl and
delivery_workbench-1.14.0.tar.gz
guided-status-loop.sh: ok
deliberate-step-loop.sh: ok
packaged multi-agent orchestration: duplicate_restarts=0, verify_all=ok
packaged outward exam: duplicate_starts=0, duplicate_nudges=0
package-smoke.sh: ok

$ pmo-roadmap/tests/workbench-explorer.sh
workbench-explorer.sh: ok

$ pmo-roadmap/tests/workbench-ui-smoke.sh
workbench-ui-smoke.sh: ok (58 viewport renders: 23 data views + empty Studio
+ program planning/active/revoked + attention + ambiguity, desktop+mobile)

$ pmo-roadmap/tests/docs-lint.sh
docs-lint: ok (445 markdown files)
docs-lint.sh: ok

$ pmo-roadmap/tests/canon-lint.sh
canon-lint.sh: ok

$ pmo-roadmap/tests/docs-snippet-smoke.sh
docs-snippet-smoke.sh: ok

$ pmo-roadmap/tests/agent-surface.sh
agent-surface.sh: ok

$ .githooks/dw check work-log-automation
dw check: ok

$ .githooks/dw rider docs --check
dw rider docs: all rendered surfaces match canon

$ pmo-roadmap/update.sh . --check
update.sh: up to date (vendored rails match source v1.14.0)

$ python3 -m compileall -q pmo-roadmap/lib/dw_pmo .githooks/dw_pmo
(no output)

$ /usr/bin/python3 -m compileall -q \
    pmo-roadmap/lib/dw_pmo .githooks/dw_pmo
(no output)

$ shellcheck -e SC2317 <the exact validation.yml shell-file set>
(no output)

$ git diff --check
(no output)
```
