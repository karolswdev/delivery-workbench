# Visual orchestration contract

**Status:** Phase 24 delivered the bounded inward loop; Phase 25 extends the
same grant/ledger spine through outward facts, standing-rule nudges, durable
typed requests, and the wheel-installed outward-loop exam. Without changing
vanilla Delivery Workbench or making bounded runs mandatory, Phase 26 delivers
an optional higher-level autonomous capability—multi-phase programs,
hierarchical workflows, independent verifiers, bounded councils and
loops—without retroactively broadening any existing run grant. Its separate
fresh-wheel program and no-program exams pin that composition and default
invariant.
**Product claim:** Delivery Workbench **can coordinate** a bounded multi-agent
delivery run when an operator has configured an exact orchestration score and
authorized a grant over that score. It does not claim that every repository
or story should be orchestrated. Scores, bounded runs, and programs are opt-in
layers: ordinary roadmap, evidence, briefing, deliberate-step, gate, and
Workbench flows require none of them, and a bounded run does not imply a
program.

## Why this layer exists now

Phase 22 supplied one deterministic observation. Phase 23 supplied a
single-use, state-bound action lease with a closed executable table, bounded
receipt, replay claim, and packaged proof. Before those contracts existed, an
orchestrator would have copied recommendations, guessed freshness, and hidden
consent inside a loop. The prerequisites now exist.

The missing capability is not “run the next command forever.” It is a control
plane that can describe and coordinate:

- which agents participate, including parallel research agents;
- what each agent may read, change, and request from its harness;
- which context and prior artifacts each node receives;
- output names, locations, formats, schemas, size limits, and citation rules;
- deterministic checks and their exact argv or built-in predicate;
- dependencies, concurrency limits, budgets, timeouts, and retry ceilings;
- success, failure, repair, escalation, approval, cancellation, and terminal
  routes; and
- where a human must inspect or attest before the run can continue.

That configuration belongs in a rich visual editor and a versioned,
diffable artifact. Runtime authority belongs in a separate, explicit grant.

## The product in one picture

```mermaid
flowchart LR
  E[Visual score editor] --> V[Pure compiler + validator]
  J[(pm/orchestration/*.json)] --> V
  V --> P[Exact score preview\nhash + capabilities + graph]
  P --> A{Operator authorizes\nthis exact score?}
  A -->|no| X[Nothing starts]
  A -->|yes| G[Revocable run grant]
  G --> C[Deterministic conductor]
  C --> S[dw status / dw step]
  C --> D[Agent-driver interface]
  D --> R[Research agents]
  D --> W[Worker / review agents]
  C --> K[Checks + output validators]
  C --> H[Human checkpoints]
  C --> L[(Append-only run ledger)]
  H --> Q[Certification / commit remain explicit]
```

The editor never executes. The compiler never executes. A saved score never
executes. Only an unexpired run grant can let the conductor schedule nodes,
and every scheduled node receives its own claim and receipt.

## Terminology

| Term | Meaning |
|---|---|
| **Score** | The tracked declarative orchestration manifest: graph, roles, inputs, outputs, checks, policies, and limits. |
| **Compilation** | Pure normalization and validation of a score into a deterministic graph plus capability summary. |
| **Grant** | A local, revocable authorization bound to the score hash, repository observation, story, capabilities, budgets, and expiry. |
| **Run** | One projection of ledger events for one grant. A run is local operational state, not roadmap truth. |
| **Node** | One typed unit: agent, check, rail step, approval, or synthesis/collection boundary. |
| **Work packet** | Structured, bounded input handed to an agent driver; never a shell command. |
| **Artifact** | A declared node output with a type, convention, hash, and validation result. |
| **Checkpoint** | A state where the conductor stops until a named human decision is recorded. |
| **Driver** | An adapter between the conductor and an agent harness. The harness owns model execution and sandbox enforcement. |

## Durable score: `delivery-workbench-orchestration@1`

Scores are tracked at `pm/orchestration/<slug>.json`. JSON is deliberate:
the stdlib Python 3.9 core can parse it exactly, the browser can round-trip it
without a second parser, canonical serialization is hashable, and Git still
shows the operator the complete diff. Markdown remains the roadmap source of
truth; the score is executable delivery policy, not another roadmap.

A representative score is below. The shipped ordinary preset is
[`research-build-review.json`](../pmo-roadmap/templates/orchestration/research-build-review.json);
`dw_pmo.orchestration` is the exact schema and semantic owner. Install seeds
that file into `pm/orchestration/` without overwriting an operator's copy.

```json
{
  "kind": "delivery-workbench-orchestration",
  "schema_version": 1,
  "slug": "research-build-review",
  "title": "Research, implement, verify, and hand back",
  "project": "myapp",
  "defaults": {
    "max_concurrency": 3,
    "max_wall_seconds": 7200,
    "max_agent_starts": 8,
    "max_check_starts": 20,
    "default_timeout_seconds": 1200,
    "max_artifact_bytes": 1000000
  },
  "nodes": [
    {
      "id": "research-api",
      "type": "agent",
      "role": "research",
      "profile": "research-readonly",
      "needs": [],
      "capabilities": ["repository-read", "network"],
      "workspace": "read-only",
      "inputs": ["story", "status", "docs/**"],
      "outputs": [{
        "name": "api-findings",
        "format": "markdown",
        "path": "artifacts/api-findings.md",
        "required_sections": ["Findings", "Sources", "Risks"],
        "citations": "required",
        "max_bytes": 30000
      }],
      "timeout_seconds": 1200,
      "on_failure": {"action": "pause"}
    },
    {
      "id": "research-risks",
      "type": "agent",
      "role": "research",
      "profile": "research-readonly",
      "needs": [],
      "capabilities": ["repository-read"],
      "workspace": "read-only",
      "inputs": ["story", "architecture"],
      "outputs": [{
        "name": "risk-register",
        "format": "json",
        "path": "artifacts/risks.json",
        "schema": "schemas/risk-register-v1.json",
        "max_bytes": 20000
      }],
      "timeout_seconds": 900,
      "on_failure": {"action": "retry", "max_attempts": 2}
    },
    {
      "id": "synthesize",
      "type": "agent",
      "role": "synthesis",
      "profile": "reasoning-readonly",
      "needs": ["research-api", "research-risks"],
      "capabilities": ["repository-read"],
      "workspace": "read-only",
      "inputs": [
        {"artifact": "api-findings", "format": "markdown"},
        {"artifact": "risk-register", "format": "json"}
      ],
      "outputs": [{
        "name": "implementation-brief",
        "format": "markdown",
        "path": "artifacts/implementation-brief.md",
        "required_sections": ["Scope", "Decisions", "Acceptance checks"]
      }],
      "on_failure": {"action": "approval", "checkpoint": "research-review"}
    },
    {
      "id": "implement",
      "type": "agent",
      "role": "implementation",
      "profile": "worker-write",
      "needs": ["synthesize"],
      "resource_groups": ["working-tree"],
      "capabilities": ["repository-read", "repository-write"],
      "workspace": "isolated-worktree",
      "inputs": [
        "story",
        {"artifact": "implementation-brief", "format": "markdown"}
      ],
      "outputs": [{
        "name": "implementation-diff",
        "format": "git-diff",
        "path": "workspace",
        "allowed_paths": ["src/**", "tests/**", "docs/**"],
        "max_bytes": 500000
      }],
      "on_failure": {"action": "route", "node": "repair", "max_visits": 1}
    },
    {
      "id": "tests",
      "type": "check",
      "needs": ["implement"],
      "runner": {
        "kind": "command",
        "argv": ["python3", "-m", "pytest", "-q"],
        "cwd": "workspace",
        "timeout_seconds": 1200,
        "output_bytes": 30000,
        "writes": []
      },
      "expect": {"exit_code": 0},
      "on_failure": {"action": "route", "node": "repair", "max_visits": 1}
    },
    {
      "id": "repair",
      "type": "agent",
      "activation": "failure",
      "role": "repair",
      "profile": "worker-write",
      "needs": ["implement"],
      "resource_groups": ["working-tree"],
      "capabilities": ["repository-read", "repository-write"],
      "workspace": "isolated-worktree",
      "inputs": [
        "story",
        {"artifact": "implementation-brief", "format": "markdown"}
      ],
      "outputs": [{
        "name": "repair-diff",
        "format": "git-diff",
        "path": "workspace",
        "allowed_paths": ["src/**", "tests/**", "docs/**"],
        "max_bytes": 500000
      }],
      "on_failure": {"action": "abort"}
    },
    {
      "id": "human-handoff",
      "type": "approval",
      "needs": ["tests"],
      "prompt": "Review the diff, evidence, and contract before certification.",
      "options": ["approve", "reject"],
      "terminal": "awaiting-certification"
    }
  ]
}
```

Schema v1 is closed by level: unknown top-level, default, node, output,
artifact-input, runner, expectation, failure-policy, and layout keys are
diagnostics rather than ignored behavior. The compiler normalizes every
finite default and stamps two hashes:

- `semantic_hash` covers every runtime rule and excludes only top-level
  editor layout;
- `document_hash` covers the normalized score including layout, so a save can
  still be stale-safe and lossless; and
- validation errors carry `pointer`, `code`, `message`, and `remediation`.

The pure CLI surface is `dw orchestration list|show|validate|simulate`.
`simulate` reports deterministic waves, locks, fan-out/fan-in, capability and
profile inventory, output lineage, checkpoints, failure branches, budgets,
and terminal meanings; it explicitly reports `starts_work: false` and
`writes_events: false`.

Since Phase 25 a score may also declare an optional top-level `nudges`
section — bounded rules binding one outward signal kind (`ci-failed`,
`changes-requested`, `merge-conflict`, `waiting-input-timeout`) to one
declared agent node with finite per-signal and per-rule ceilings and an
optional bounded expectation string. Rules feed the semantic hash, appear
in simulation, and execute only under a grant that carries matching
standing nudge rules and a `max_nudges` budget (score `defaults`). The
full contract is [signals.md](./signals.md).

### Score invariants

- Node ids are unique, stable, and selector-safe.
- `needs`, explicit failure routes, and nudge targets resolve to existing
  nodes; a nudge target must be an agent node, and naming a
  failure-activated node in a nudge rule makes it reachable exactly like
  a failure route does.
- The success graph is acyclic. Bounded retries and repair visits are policy,
  never implicit graph cycles.
- Every executable node declares timeout and output bounds, directly or via
  score defaults.
- Parallel eligibility is deterministic; ties resolve by score order then id.
- Required outputs have one producer. Consumers can reference only declared
  artifacts from completed dependencies.
- No prompt, artifact name, path, check, or failure route is synthesized by
  the conductor.
- A score may request capabilities; it cannot grant them. Driver discovery
  and the run grant must both satisfy the request.
- Secrets, API tokens, provider executables, and machine-specific paths never
  belong in the tracked score.

## Node types

| Type | Purpose | Execution owner | Important refusal |
|---|---|---|---|
| `agent` | Research, synthesis, implementation, review, documentation, or repair | Configured agent harness through a driver | Missing profile/capability, undeclared output, or unavailable isolation |
| `check` | Deterministic command or built-in predicate | Local check runner | Shell string, unbounded output/time, escaped cwd, undeclared writes |
| `rail` | One status/step transition named by action id | Existing `dw step` core | Stale lease, action not allowed by score+grant, certification, or commit |
| `approval` | Explicit inspect/choose/attest boundary | Human/operator surface | No approval identity/receipt, expired grant, changed preview |
| `collect` | Validate and expose a set of already-produced artifacts | Pure compiler/validator | Missing, oversized, malformed, or convention-violating artifact |

Agent `role` is descriptive and editor-visible, not hard-coded policy. The
first-class role presets are `research`, `synthesis`, `implementation`,
`review`, `verification`, `documentation`, and `repair`; a score can name a
custom role without minting capabilities.

## Rich visual score editor

The Workbench provides a dedicated orchestration route with four coupled views:

1. **Design:** an SVG/canvas graph with node palette, typed ports, dependency
   and failure edges, grouping, zoom, keyboard navigation, and a property
   inspector. Research-agent fan-out and synthesis fan-in are visible shapes,
   not hidden JSON conventions.
2. **Validate:** the pure compiler's normalized graph, capability inventory,
   output lineage, concurrency projection, unreachable-node and cycle errors,
   unbounded retry/time/cost errors, and a dry scheduling trace.
3. **JSON:** the complete canonical document, losslessly synchronized with the
   graph and still validated only by the shared compiler.
4. **Run:** the exact score hash and grant, live node states, agent/session
   correlation, checks, output validation, attempts, budgets, checkpoints,
   cancellation, and terminal handoff.

The inspector configures the complete rule surface:

- agent role/profile, prompt template, context selectors, capabilities,
  workspace mode, timeout, and retry ceiling;
- inputs and typed outputs, including path/name conventions, format/schema,
  required headings, citations, allowed paths, and byte bounds;
- command checks as tokenized argv, built-in file/schema/diff/rail checks,
  expected result, timeout, output cap, and declared write behavior;
- success dependencies and explicit failure routes (`retry`, `route`,
  `approval`, `pause`, or `abort`), all bounded;
- score/run budgets, concurrency/resource groups, and approval checkpoints;
  and
- terminal meaning such as `complete`, `blocked`, `cancelled`, or
  `awaiting-certification`.

All four views are delivered. Run replays the authoritative ledger through the
shared core and renders live graph state, attempts, agent/check/rail sessions,
artifact metadata and lineage, finite budgets, failure routes, checkpoints,
terminal meaning, and the content-safe ledger timeline. It never reconstructs
policy in the browser and never polls. Every grant or control is a separate
preview→confirm act; a state, action, reason, or decision change invalidates
the exact token before work or an event can start. Graph and JSON round-trip losslessly.
Saving uses preview→diff→apply through a dedicated contained score mutation;
the browser never owns validation policy. A score with compiler errors cannot
be saved or authorized. Presets are ordinary scores copied into the editor,
not magic runtime branches.

## Authority model

The orchestration layer adds one explicit authority ring; it does not blur
the existing ones.

| Ring | Act | Authority |
|---|---|---|
| 0 | Read score, compile, simulate, inspect status/runs | None; pure reads |
| 1 | Save score | Guarded content preview plus exact fingerprint apply |
| 2 | Start/resume run | Operator grant over score hash, repo/status facts, story, capabilities, budgets, and expiry |
| 3 | Start agent/check/rail node | Active grant + scheduler eligibility + exclusive node claim + driver/check/step refusal checks |
| 4 | Approve checkpoint or capability elevation | Fresh human decision over an exact checkpoint preview |
| 5 | Certify contract and commit | Existing explicit operator act; never inferred from score or run completion |

A tracked score is no more authority than a CI workflow sitting on disk. A
grant is the act boundary. Editing a score invalidates an unstarted grant; an
active run remains bound to its original immutable compiled score and cannot
silently adopt the edit.

## Run grant

The delivered authorization core uses `delivery-workbench-run-plan@1`,
`delivery-workbench-run-grant@1`, `delivery-workbench-run-event@1`, and the
replayed `delivery-workbench-run@1` projection. The grant contains:

- a token-derived, single-use run id plus score slug and both canonical score
  hashes;
- local repository identity, branch, HEAD/index tree, selected project,
  phase/story file hashes, and initial status hash;
- requested profiles, capabilities, and workspace modes;
- maximum concurrency, wall time, agent/check starts, attempts, and artifact
  bytes;
- issued/expiry timestamps and revocation generation; and
- the operator's explicit approval identity/time plus permanent exclusions.

`dw run plan` is pure and reports `starts_work: false`; `dw run start` accepts
the complete plan, its exact `start_token`, an explicit approval, and a bounded
operator identity. It re-plans from current facts before atomically publishing
an immutable plan/compiled-score/grant plus the initial ledger event. The grant
lives under `.git/pmo-orchestration/runs/<run-id>/grant.json`. It is local
authority, not a portable bearer secret. Replay, tamper, expiry, revocation,
exhausted budgets, changed repository/status/story facts, or ambiguity all
stop dispatch before another node is claimed.

## Run state and deterministic scheduling

```mermaid
stateDiagram-v2
  [*] --> draft
  draft --> ready: score compiles
  ready --> running: exact grant approved
  running --> waiting_agent: agent started
  waiting_agent --> running: typed outputs accepted
  running --> waiting_approval: checkpoint / elevation
  waiting_approval --> running: fresh approval
  running --> paused: explicit pause / recoverable refusal
  paused --> running: resume grant still valid
  running --> blocked: terminal check or policy failure
  running --> awaiting_certification: score terminal reached
  running --> cancelled: revoke / cancel
  running --> expired: time or budget exhausted
  waiting_agent --> interrupted: driver lost / cancellation timeout
  awaiting_certification --> awaiting_certification: external commit observed (no shipped claim)
  awaiting_certification --> running: covered outward nudge (bounded repair only)
```

An external operator commit is always observation first. The ledger records
its relation plus a closed repository/status/story fact checkpoint. It may
refresh dispatch freshness only when it is a clean fast-forward on the
grant's same repository and branch while the bound story remains unchanged
and `in-progress`; the event is then explicitly marked `rebindable`. Dirty,
diverged, rewritten, cross-branch, or roadmap-changing commits remain visible
but cannot refresh authority. This is not certification or push authority—it
only lets an already granted standing nudge run its bounded repair against
the operator's new fact boundary.

A terminal approval node is a historical handoff, not an outstanding human
request. If a covered nudge wakes the run, a repaired or re-routed run may
reach that terminal handoff again. Only nonterminal checkpoints enter
`awaiting-approval`, derive a request correlation, and wait for a typed
decision.

The conductor derives the current projection from an append-only ledger. One
reconciliation tick:

1. locks the run and replays/validates its ledger;
2. re-observes repository/status/session/driver facts;
3. handles completed, failed, lost, or cancelled work;
4. validates newly declared artifacts and checks budgets;
5. chooses eligible nodes deterministically;
6. claims each node before dispatch, up to the granted concurrency; and
7. appends dispatch/refusal/checkpoint receipts, then returns.

The long-running conductor is only repeated ticks with a stop signal and
backoff. The tick remains directly callable and idempotent for tests,
recovery, CLI operation, and hosted schedulers. It never follows an unrecorded
decision.

This runtime is delivered as one shared core: `schedule_decision` is pure;
`dw run preview <run> tick` produces its exact consent document and
`dw run tick <run> --expect <act-token>` performs one
reconciliation/dispatch boundary; and
`dw run supervise <run> --max-ticks N --interval S` is finite repetition over
that same tick for an explicitly requested CLI supervisor.
`dw run request <run> <correlation> <decision> --expect <act-token>` is the
generic preview-bound typed response; `dw run checkpoint` remains its
checkpoint-only compatibility alias. Pending requests are replayed from the
ledger, shown with age/origin/schema, and republished once per restart/resume
generation without changing their correlation. A tick first polls or recovers existing
claims, then records configured failure routes, then schedules in immutable
score order. A repair receipt binds source attempt, visit, repair node and
repair attempt; successful repair re-enables exactly the failed source, while
retry/visit/start budgets turn exhaustion into a recorded `blocked` stop.

## Agents, research, and isolated workspaces

The delivered driver protocol is provider-neutral: capability discovery,
`start`, `poll`, `interrupt`, and `collect`. A hash-bound structured work packet carries run/node ids,
role, bounded prompt/context, declared inputs/outputs, workspace identity,
capability request, deadlines, and a bounded repository-knowledge section.
The knowledge section contains verified locations, whole-symbol snippets,
mapped tests, relevant earned lessons when present, labeled unverified hints,
and named budget exclusions. Hint-free stories say so; stale map or grounding
refuses packet assembly. It carries no provider executable or shell argv, and
knowledge informs without authorizing any action.

Operator-local `.git/pmo-orchestration/drivers.json` configuration maps logical
profiles such as `research-readonly` or `worker-write` to installed adapters,
capabilities, workspace modes, named router/provider, model vendor/family/id,
revision-or-alias policy, opaque auth domain, and optional local executable
choice. Public capability documents expose only the auth-domain fingerprint,
never credentials. The complete resolved execution binding participates in
the capability and roster fingerprint, so changing a provider or configured
model makes an old assignment/grant stale. Configuration rejects credential/
token/password/secret fields; authentication stays with the harness. The
adapter reports supported capabilities and its actual sandbox/
interrupt claims; a mismatch returns a content-free non-started refusal.
Network access, model choice, filesystem sandboxing, and tool approval remain
enforceable by the harness/adapter, not falsely claimed by Delivery Workbench.

Read-only research agents can fan out in parallel against one immutable tree
and write only declared run artifacts. Write-capable agents receive isolated
Git worktrees and resource locks. A synthesis node consumes research artifacts
only after their output contracts pass. Concurrent write work never shares a
working directory, and integrating a worktree diff is a separate reviewed
transition—not an implicit side effect of agent completion.

`FixtureDriver` is the deterministic test oracle: its sessions and
idempotency receipts persist across manager restart and can model running,
succeeded, failed, cancelled, lost, nonzero, timeout, malformed, and oversized
states without a provider. `CodexExecDriver` is the first real adapter. It uses
the stable non-interactive `codex exec` surface with an explicit read-only or
workspace-write sandbox, no interactive approval, ephemeral session rollout,
a shell environment that inherits no host secrets, bounded stdout/stderr, and
host-captured final output. `ClaudeCodeExecDriver` (Phase 25) is the second
real adapter, over non-interactive `claude -p`: the workspace mode maps to a
closed tool allowlist (no shell tool in either mode), the environment is
scrubbed to a small allowlist with authentication left entirely to the
harness, and capability discovery pins the tested `claude` major version —
outside the pin the adapter refuses content-free instead of degrading.
Both real adapters are live-smoked only when authenticated; deterministic CI
never depends on a model response.

## Checks, outputs, and failure policy

Check nodes are either built-in predicates or exact tokenized argv from the
reviewed score. There is no shell-string mode, interpolation, command emitted
by an agent, unbounded cwd, or inherited secret environment. Command checks
run in either the successful isolated predecessor workspace or a separate
grant-HEAD check worktree—never the operator tree—with timeout, stream caps,
a minimal environment, and bounded before/after filesystem snapshots. Any
writes outside declared paths fail the check. Built-in file, JSON-schema,
diff-scope, and rail-status checks use the same persistent receipt contract.

Output validation is deterministic before downstream scheduling:

- existence, kind, path containment, byte bound, and hash;
- JSON schema subset or required Markdown sections;
- citation requirement for research outputs;
- Git diff scope for implementation outputs; and
- one-producer/type-compatible lineage for every artifact reference.

Validated bytes are copied into
`.git/pmo-orchestration/runs/<run>/artifacts/<node>/<name>/` beside an exact
`delivery-workbench-artifact-receipt@1`. Downstream packet construction accepts
only one unambiguous receipt whose size/hash/format still matches its content.
Context selectors are contained and explicitly truncated at file/count/packet
caps; artifact inputs are never truncated.

Failure policy is data, not improvised reasoning: bounded retry, route to a
named repair node, request approval, pause, or abort. Required checks and
outputs cannot be silently skipped. A retry gets a new attempt id and receipt;
an old node claim cannot replay.

## Ledger, receipts, and recovery

Runtime state lives under `.git/pmo-orchestration/runs/<run-id>/`:

```text
grant.json                 exact local authority
plan.json                  immutable reviewed start plan
score.json                 immutable compiled score used by this run
ledger.jsonl               hash-chained append-only authoritative run ledger
artifacts/<node>/<name>    bounded declared outputs + metadata
driver-sessions/            persistent provider-neutral session receipts
check-sessions/             exact runner hashes, bounds, outcomes, snapshots
rail-sessions/              fresh dw-step lease/result receipts
workspaces/<node>/           isolated writer workspace identities
projection.json            disposable derived cache
```

Ledger events carry ids, hashes, state transitions, attempts, timestamps,
budgets, driver/check outcomes, and artifact metadata—not prompts, model
transcripts, source content, credentials, or raw check output. Detailed
streams remain bounded local artifacts and appear only on explicit inspection.

Cross-process ledger and whole-tick locks, stale intent-bound acts, single-use start tokens,
and unique node-attempt/idempotency claims make dispatch at-most-once. Driver,
check, and rail executors persist an idempotent local receipt before a retry;
an uncertain started check/rail becomes `lost` rather than running twice. Deleting
or corrupting `projection.json` changes nothing because every read replays the
immutable grant and authoritative hash chain; truncated, corrupt, or forked
ledgers fail closed. Pause, revoke, and cancel stop future dispatch immediately
while already claimed work can still record a bounded terminal outcome. After a crash, restart
replays the ledger and polls claimed driver work; it never assumes an absent
receipt means failure or blindly starts a duplicate. Unknown agent state moves
to `interrupted` or a human recovery checkpoint. Cancellation revokes future
dispatch first, then asks active drivers to interrupt, records every outcome,
and never deletes the audit trail.

## Surfaces and interoperability

One core owns score compilation, grant planning, run projection, tick, and
cancellation. Adapters remain thin:

- CLI: `dw orchestration list|show|validate|simulate`, plus `dw run plan|start|list|show|view|preview|pause|resume|revoke|cancel|tick|supervise|checkpoint|request|stream`;
- MCP: byte-identical score/run reads, previews, exact-token acts, and explicit bounded streams—never caller-supplied score semantics or provider/check argv;
- HTTP: the same documents inside versioned envelopes, with stale acts as 409;
- Workbench: Design, Validate, JSON, and Run views over those HTTP models, with manual refresh and no authorization poller; and
- events/state feed: bounded run summaries for mission-control clients.

Remote or hosted schedulers may call `tick`, but the local runner holding the
grant, repository, driver configuration, and workspaces remains the execution
authority. A Phase 24 implementation does not turn an HTTP score into a
cross-machine bearer capability.

## Threat model and fail checks

| Threat | Required fail check |
|---|---|
| Score edit smuggles new authority into an active run | Run uses immutable compiled score/hash; changed score needs a new grant |
| Model invents commands, outputs, or routes | Only score-declared nodes/argv/artifacts/routes compile; work packets are structured |
| Research agent exfiltrates or writes source | Capability/profile match, read-only workspace, declared artifacts, harness-owned network policy |
| Parallel writers corrupt one tree | Isolated worktrees plus resource locks; no shared writable cwd |
| Retry becomes an infinite loop | Compile-time finite ceilings plus run budgets and visit counters |
| Failed check is waved through | Required checks cannot skip; only explicit failure route or approval receipt advances |
| Crash launches duplicate agent/check | Exclusive claim before dispatch; recovery polls before any retry |
| Stale rail action executes | Fresh `dw step` preview/apply at the rail node boundary |
| Remote caller expands capability | Grant is local/non-portable; adapters accept ids/tokens, never driver or shell argv |
| “Run complete” becomes “safe to commit” | Terminal is `awaiting-certification`; gate certification and commit remain explicit |

## Phase 24 proof standard — fulfilled

The wheel-installed fresh-consumer exam proves that Delivery Workbench can:

1. use the visual editor to configure a score with parallel research agents,
   synthesis, implementation, exact output conventions, deterministic checks,
   a repair/failure route, budgets, and a human terminal checkpoint;
2. round-trip graph ↔ JSON without semantic drift and reject planted cycles,
   unbounded retry, missing output, shell string, escaped path, and unsupported
   capability;
3. authorize the exact compiled hash, run through fixture agent drivers in
   isolated workspaces, and expose every state/receipt identically across CLI,
   MCP, HTTP, and the Workbench;
4. survive restart, refuse a duplicate dispatch, cancel cleanly, and stop on
   expiry/budget/check failure; and
5. hand a real evidence-ready diff back at `awaiting-certification`, with no
   automatic checkbox edit or commit, then pass the existing gated history
   chain after the fixture operator completes those acts.

The deterministic fixture-driver exam is the mandatory CI proof. It passed
with two parallel research agents, validated fan-in, isolated implementation,
one fail→repair→recheck route, crash recovery with zero duplicate starts, and
an `awaiting-certification` terminal. A separately provisioned live Codex run
passed the real driver seam without making variable model output the oracle.
The complete record is in the
[Phase 24 final summary](../pmo-roadmap/pm/roadmap/work-log-automation/phase-24-bounded-orchestration/final-summary.md).

## Deliberate authority boundaries and possible later extensions

These are not missing prerequisites for orchestration. The local visual
coordination framework is complete. They are either intentionally excluded
authority or materially different deployment models that need their own
operator decision:

- Arbitrary cyclic graphs; bounded retry/repair policy covers the recoverable
  cases without turning scheduling into an undecidable workflow language.
- Secrets in scores, provider-specific prompt fields, and repository-defined
  driver executables.
- Cross-repository write transactions and automatic merge/conflict resolution.
- Automatic evidence adequacy judgment, contract certification, commit,
  push, release, or deployment.
- A central hosted control plane holding repository authority. The delivered
  CLI/MCP/HTTP contracts already permit remote clients to coordinate a local
  runner; moving the repository consent root to a service would be a separate
  security and operations product decision.

One extension has since been contracted: outward observation and bounded
nudging — CI, review, merge-state, and agent-activity facts recorded as
durable signals and routed back to agents under grant authority — is
specified in the [outward signals contract](./signals.md) (Phase 25).

A second, separately opt-in extension is now contracted and incrementally
implemented in [programs.md](./programs.md): multi-phase programs may compose
bounded child runs, hierarchical workflows, independent verifiers, councils,
and exact delivery rails under their own finite program grant. Its embedded
restart-safe conductor now composes agent/check/repair, deliberation,
obligation, meta-review, typed structural-loop, phase-architect, content-safe
outward-fact/nudge, cross-story/phase-selection, and exact scope-completion
boundaries one replay-derived tick at a time. It reuses Phase 25's
authority-free signal chain but never performs an observe pass; program
standing rules accept only SCM signals, an exact already-run agent target, and
finite grant/rule budgets. Exact integration/Git/roadmap delivery and the
canonical CLI/MCP/HTTP/Workbench program controls are now delivered as
separate program-only adapters over the same ledger. Existing scores and run
grants acquire none of those semantics or capabilities, and the bounded-run
surface remains independently complete.
