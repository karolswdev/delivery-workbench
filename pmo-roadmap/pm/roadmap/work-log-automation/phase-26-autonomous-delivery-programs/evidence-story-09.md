# Evidence - WLA-26-09

- **Story:** WLA-26-09 - Conduct and recover hierarchical multi-phase programs
- **Status:** done
- **Date:** 2026-07-23

## Proof

### One replay-first conductor and authority ledger

- `program_conductor.py` adds pure `derive_program_frontier`, one finite
  `tick_program`, and a bounded `supervise_program`. A tick locks the run,
  replays and freshness-checks the immutable program grant and sole
  hash-chained `program_run` ledger, verifies ledger-bound conductor/artifact
  receipts, reconciles an active external operation before retry, derives one
  exact act, claims it, dispatches or records it, and stops.
- `claim_dispatched` records deterministic operation id, idempotency key,
  packet/child-grant hash, adapter/version, and provider/model/auth execution
  binding before an external start. A missing session after that fact stops as
  `external-operation-uncertain`; it is never permission for a second start.
  Driver sessions are reconciliation journals, not authority.
- Stable addresses retain program, phase, story, workflow/subflow, loop/round,
  council/seat, node/role, and attempt. Every child grant is a strict
  non-delegable intersection of grant, scope, assignment, node, remaining
  budget, repository/roadmap facts, and expiry.
- Immutable receipt replay recovers active claims after planted failures
  before/after claim, dispatch, external start, check observation, decision,
  loop round, architecture boundary/verdict/gate, outward fact, nudge delivery,
  and scope proof. Missing, changed, forked, or unhashed receipts stop instead
  of becoming mutable scheduler state.

### Hierarchical work, deliberation, loops, and architecture

- The conductor executes isolated implementer work, deterministic
  fan-out/fan-in, registered built-in checks, mechanical facts, mandatory
  independent rubric verification, and finite claimed repair/reverification.
  It enforces principal/workspace/session separation and preserves exact
  provider/model/auth identity in packets and receipts.
- Debate nodes freeze one finite pure deliberation plan in the first claimed
  round. Replay reconstructs proposal, critique, rebuttal, and judgment from
  conductor receipts rather than creating a second council ledger. Raw seat
  output, the council decision, meta-verdict, each obligation, and an optional
  typed checkpoint remain separate claims. Rule mode has no agent decider;
  judge mode binds only the preassigned seat and execution identity.
- Structural-loop rounds are separately claimed. Each immutable receipt binds
  the compiled check/verdict/decision/artifact-validity observation, producer
  action and receipt, valid carried-artifact hashes, nested round lineage,
  finite maximum, and exact success/continue/exhaustion route. A red source
  remains an input to loop policy rather than inventing an unrelated route.
- A configured final-story phase gate activates only its preassigned
  read-only master architect. Boundary snapshot, architect output, typed
  verdict, and quality-gate proof are distinct claims. Approval reaches only
  the integration checkpoint; veto/checkpoint/abort remain explicit routes.
- The version-pinned `pi-exec` adapter uses closed no-shell argv, scrubbed
  harness-owned environment, non-session print mode, and exact version/model
  resolution. Tracked policy cannot supply executables, arbitrary flags,
  credentials, or commands.

### Content-safe outward loop and causal recovery

- Program policy accepts an optional closed list of at most 20 standing nudge
  rules. Each names one supported SCM signal, exact program binding, uniquely
  expanded non-loop agent target, finite per-signal and total bounds, and an
  optional bounded expectation. Validation requires `program:select`,
  `nudge:deliver`, sufficient `max_nudges`, and worst-case child/agent/provider/
  model/artifact capacity.
- A grant with standing rules requires one resolving exact remote-tracking ref.
  The conductor never observes the network. It reads only the already-observed,
  hash-verified Phase 25 local signal channel for that remote/branch; a newer
  resolved/green fact prevents an older failure from matching.
- A separately claimed outward-fact receipt contains only rule/hash, signal
  kind, signal event hash/sequence, and channel hash—never raw forge text, URL,
  review body, log, credential, or notification payload. A separate nudge
  claim binds that receipt, idle receptivity, exact already-run target lineage,
  next attempt, and finite ceilings.
- A delivered nudge is replayed before newer facts and reaches the target at
  most once. The target packet and receipt bind the nudge receipt. Replay then
  reruns only work made causally stale: activation-dependent DAG nodes,
  independent verification, and any older architecture boundary. It stops as
  `nudge-governance-replay-required` rather than silently reopening a completed
  council or structural-loop outcome.

### Cross-story/phase continuation, obligations, and completion

- Program start freezes the deterministic union of seats and checkpoint ports
  reachable by every binding in the granted scope. A later story or phase
  therefore cannot introduce a provider, model, auth domain, principal, or
  decision port absent from the reviewed grant.
- After separately authorized WLA-26-10 facts make the current story complete,
  replay filters old workflow receipts, re-runs the pure planner, and selects
  the next exact story, binding, workflow, team, and phase. The WLA-26-09
  conductor performs no integration, evidence, certification, commit, push,
  story status, or phase mutation itself.
- Non-blocking council obligations remain in the content-safe replay frontier
  across story/phase selection and restart. Any open blocking obligation stops
  selection distinctly as `blocking-obligation-open`.
- When the pure planner reports the whole granted scope complete, the
  conductor reserves one exact `program-scope-proof`, stores one immutable
  receipt, and records one `program_scope_completed` event. A crash after the
  proof recovers the same claim and terminal `complete` state without a second
  proof or event.

### Compatibility and documentation

- No-program vanilla use and Phase 24/25 bounded runs retain their existing
  schemas, grants, public commands, and default behavior. Program runtime
  remains an embedded shared-core API: WLA-26-10 owns delivery rails and
  WLA-26-11 owns CLI/MCP/HTTP/Workbench live controls.
- Source and vendored packages are byte-synchronized. Project-facing
  `README.md`, framework README, solution overview, architecture, interop
  inventory, autonomous-program contract, orchestration boundary, and
  Unreleased changelog all document the final WLA-26-09 behavior and remaining
  fail-closed boundaries.

## Verification summary

- Focused planner/conductor/authority/deliberation matrix: 65/65 on Python
  3.14 and 65/65 on the Python 3.9 floor. `ProgramConductorTest` contributes
  20 recovery and refusal scenarios.
- Full core suite: 457/457 on Python 3.14 and 457/457 on Python 3.9.
- Fresh-wheel packaging passed on Python 3.9: sdist and wheel build/install,
  packaged guided status loop, deliberate multi-surface consent loop,
  multi-agent orchestration exam with zero duplicate restarts, and outward-loop
  exam with zero duplicate starts/nudges.
- Python compilation, canon lint, Markdown links/anchors/images, executable
  documentation snippets, agent-surface parity, source/vendored update parity,
  roadmap validation, rendered rider parity, and diff checks passed.

## Captured validation - 2026-07-23

```text
$ python3 pmo-roadmap/tests/dw-core-tests.py -q ProgramConductorTest
Ran 20 tests in 413.882s
OK

$ python3 pmo-roadmap/tests/dw-core-tests.py -q \
    ProgramPlannerTest ProgramConductorTest \
    ProgramRunAuthorityTest ProgramDeliberationTest
Ran 65 tests in 513.673s
OK

$ /usr/bin/python3 pmo-roadmap/tests/dw-core-tests.py -q \
    ProgramPlannerTest ProgramConductorTest \
    ProgramRunAuthorityTest ProgramDeliberationTest
Ran 65 tests in 489.587s
OK

$ python3 pmo-roadmap/tests/dw-core-tests.py -q
Ran 457 tests in 706.205s
OK

$ /usr/bin/python3 pmo-roadmap/tests/dw-core-tests.py -q
Ran 457 tests in 538.938s
OK

$ pmo-roadmap/tests/package-smoke.sh
package-smoke.sh: built delivery_workbench-1.14.0-py3-none-any.whl
package-smoke.sh: built delivery_workbench-1.14.0.tar.gz
guided-status-loop.sh: ok
deliberate-step-loop.sh: ok
packaged multi-agent orchestration: duplicate_restarts=0, verify_all=ok
packaged outward exam: duplicate_starts=0, duplicate_nudges=0
package-smoke.sh: ok

$ pmo-roadmap/tests/canon-lint.sh
canon-lint.sh: ok

$ pmo-roadmap/tests/docs-lint.sh
docs-lint: ok

$ pmo-roadmap/tests/docs-snippet-smoke.sh
docs-snippet-smoke.sh: ok

$ pmo-roadmap/tests/agent-surface.sh
agent-surface.sh: ok

$ pmo-roadmap/update.sh . --check
update.sh: up to date (vendored rails match source v1.14.0)

$ .githooks/dw check work-log-automation
dw check: ok

$ .githooks/dw rider docs --check
dw rider docs: all rendered surfaces match canon

$ git diff --check
(no output)
```
