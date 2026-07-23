# WLA-26-09 — Conduct and recover hierarchical multi-phase programs

- **Project:** work-log-automation
- **Phase:** 26
- **Status:** done
  <!-- status vocabulary: roadmap-builder.md §2.3 -->
- **Depends on:** WLA-26-02, WLA-26-03, WLA-26-04, WLA-26-05, WLA-26-07, WLA-26-08
- **Unblocks:** WLA-26-10, WLA-26-11, WLA-26-12
- **Owner:** unassigned

## Problem

The autonomous organization becomes real when one durable conductor can move
from roadmap selection through nested specialist work, verifier/council loops,
quality decisions and phase-level architecture review, then repeat across
stories and phases. It must recover from process death at every boundary
without duplicating expensive work or destructive acts, and it must never hide
a hard story by selecting an easier one.

## Scope

- **In:** one deterministic `tick_program`; hierarchical scheduler and stable
  addresses; story/phase selection; workflow instantiation; role assignment and
  strict child grants; versioned driver-plugin discovery and exact execution-
  port resolution for CLI/API harnesses (including Codex, Claude and pi/
  OpenRouter fixtures); fan-out/in; bounded loop/debate/panel/council/verifier/
  decider/meta/architect scheduling; artifact/verdict/decision/obligation/gate
  reconciliation; outward signal/nudge integration; retry/repair/escalation;
  program supervision; claim-before-dispatch, poll/reconcile-before-retry,
  ledger replay and recovery.
- **Out:** a second scheduler per surface; hidden background daemon; infinite
  loops; parallel integration of multiple stories; automatic graph/rubric/
  authority changes; conflict resolution.

## Acceptance criteria

- [x] One tick replays state, reconciles existing claims/outward facts, derives
  a stable eligible frontier within concurrency/resource/budget bounds, claims
  at most one exact next act, dispatches or polls it, records its outcome/
  route, and stops.
- [x] Hierarchical lineage addresses program→phase→story→workflow/subflow→loop
  round→council/seat→node/role/attempt so every artifact, verdict, decision,
  obligation, nudge and failure route is attributable and replay-stable without
  flattening away organizational meaning.
- [x] The conductor enforces implementer/verifier separation and declared
  panel/council/decider/meta/architect order; a rule-decided council has no
  override agent, a judge-mode council dispatches only its preassigned
  `decider_seat`, and failed or dissenting verdicts can only retry, repair,
  re-debate, escalate, pause or abort along finite compiled routes.
- [x] Named driver adapters expose closed versioned configuration and safe argv
  rendering for their harness; resolution records requested/reported model,
  provider/router and opaque auth-domain fingerprints, refuses unavailable or
  version-skewed exact bindings, and never accepts arbitrary tracked commands,
  flags or credentials. The resolved model participates in roster/grant
  freshness.
- [x] Council obligations are appended idempotently to the program ledger;
  blocking items stop advancement and non-blocking items remain in the durable
  frontier across story/phase transition, replacement and restart until an
  authorized terminal disposition is recorded.
- [x] Bounded supervision merely repeats the same tick until a declared
  terminal/poll/checkpoint/budget/time ceiling; it cannot auto-start, elevate
  authority, swallow refusal, or spin when no progress is possible.
- [x] Planted crashes before/after every conductor claim/dispatch/receipt
  boundary recover with zero duplicate agent/check/nudge/debate speaker/
  verdict/gate/loop/scope-completion acts and with external operations
  reconciled before retry. Integration and roadmap story/phase rail
  idempotency remain WLA-26-10 acceptance.
- [x] Unknown/blocked activity, unavailable required role, quorum loss, repair
  exhaustion, missing/changed provider-model binding, decider loss, architect
  veto, stale facts, open blocking obligation and budget exhaustion stop
  distinctly; none causes the scheduler to skip the story or phase silently.
- [x] Product-facing documentation—not only roadmap evidence—keeps the root
  and framework READMEs, solution overview, architecture, interop/schema
  inventory, autonomous-program contract, orchestration boundary, and
  Unreleased changelog synchronized with the delivered conductor, its public
  surface status, authority limits, recovery guarantees, and remaining
  fail-closed work; documentation validation passes.

## Test plan

- **Unit:** scheduler eligibility, hierarchy, loop, route, claim, recovery and
  bounded-supervisor tests on both Python floors.
- **Integration:** fixture program spans at least two stories, nested fan-out,
  verifier repair, a heterogeneous provider/model council with explicit
  decider, obligation carry-forward, meta-audit and phase architect review
  across multiple process restarts.
- **Manual / device:** inspect replay explanation at active, debate, repair,
  phase-boundary and stopped states.

## Notes / open questions

Only one story may own the integration lane in Phase 26. Read-only research,
debate and verification may run concurrently when their declared resource and
context rules permit it.

## Implementation checkpoint — 2026-07-23

The restart-safe vertical slice is implemented in `program_conductor.py` and
keeps `program_run.py` as the sole authority ledger. It now provides one
locked deterministic tick plus a bounded supervisor, stable hierarchical
selection/assignment/node/role/attempt addresses, strict child grants embedded
in work packets, durable claim-before-dispatch records, fixture start/poll/
reconcile, immutable hash-bound artifacts and receipts, implementer then
independent verifier, finite claimed repair/reverification, deterministic
fan-out/fan-in collection, and closed built-in checks converted through the
mechanical-fact core. The registered Pi/OpenRouter port pins an exact Pi CLI
semver and renders closed credential-free argv.

Planted crashes after claim, before dispatch, after the dispatch ledger event,
after external start, after check observation, and after receipt recover
without duplicate claims, starts, checks, verdicts, or routes. Deleting a
session after durable dispatch stops as external-operation uncertainty rather
than launching again. Obligation record/disposition and scope-complete events
are now exact-claim-bound; scope completion additionally requires fresh pure
planner proof that the whole granted roadmap scope is complete.

The next restart-safe layer now composes the existing pure deliberation core.
The first separately claimed debate round freezes the exact finite plan in its
immutable receipt; replay deterministically reconstructs every pure claim and
submission from the program-ledger-bound conductor receipts. Proposal,
critique, rebuttal and judgment seats keep council/round/seat/role lineage and
receive exact child grants. Raw judgment is separate from the claimed immutable
council decision: rule mode has no agent decider, judge mode binds only the
preassigned seat and execution identity, and a checkpoint tie opens only the
grant-declared `program-decision-checkpoint` request.

Full meta-audit is dispatched and issued under separate agent/verdict claims.
Each decision obligation is ingested idempotently through its own exact
`obligation-record` claim before an advance route is eligible. A planted crash
after the immutable decision receipt recovers one council claim and one
decision, while the existing dispatch recovery prevents duplicate speakers.

The next layer composes configured `before-phase-complete` master-architect
gates. A gate becomes eligible only for the last unfinished scoped story in
the phase. Planning makes that exact role policy-required with a read-only
phase-visible packet and the intersected `agent:dispatch`/`verdict:issue`
ceiling. The conductor freezes a separately claimed bounded phase snapshot,
dispatches the preassigned architect, issues a typed immutable
`architect-verdict` under a separate verdict claim, and records the pure
quality-gate proof under a final gate claim. Approval reaches only the
integration checkpoint; veto stops before it; checkpoint failure opens only
the declared `phase-boundary` port. Crashes after the boundary, architect and
gate receipts recover without duplicating any of those acts.

The structural-loop layer now composes the finite loop proof already emitted
by `program_workflow`. Each active round gives its child subflow an exact
`loop/<id>/round/<n>/subflow/...` lineage, including nested loop segments.
Only the compiled check/verdict/decision/artifact-validity source can satisfy
the predicate. One separately claimed immutable `loop-round` receipt binds the
scalar observation, producer action/receipt hash, valid carried-artifact
hashes, finite maximum, and exact success/continue/exhaustion route. A red
predicate source is handled by the loop policy rather than the child node's
ordinary failure route. Planted failure after storing that receipt replays one
completed claim and consumes one loop-round budget unit; exhaustion after the
compiled maximum routes distinctly.

The final conductor layer composes outward facts, standing-rule nudges, and
scope transitions without acquiring observer or delivery-rail authority.
Program policy validates a closed finite nudge rule against one exact binding
and expanded non-loop agent target, requires `program:select` plus
`nudge:deliver`, and charges worst-case reruns to grant envelopes. Start
requires one exact resolving remote-tracking ref and freezes every
scope-reachable seat and checkpoint port, not only the initial selection.

Before ordinary selection, replay reads only the already-observed Phase 25
local signal chain. A current matching SCM failure becomes a separately
claimed content-safe outward-fact receipt; a second claim delivers at most one
rule/signal-bounded nudge only after its target agent has already run. The
nudge receipt binds that fact and the exact next target attempt, and causal
replay repeats dependent DAG work, independent verification, and a stale
architecture boundary. Completed council or structural-loop history is never
silently reopened.

Once separately authorized WLA-26-10 facts make a selected story complete, the
next tick selects the next exact story, binding, workflow and phase from the
pure planner. Non-blocking obligations remain in the frontier across those
transitions; a blocking obligation stops before selection. When the planner
reports the entire granted scope complete, the conductor claims one immutable
scope proof and records one terminal completion event. Crash fixtures prove
one outward fact, one nudge delivery/target, durable obligation carry, and one
scope proof/event across restart.

Product-facing documentation is part of this story's deliverable. The root
README, framework README, solution overview, architecture, interop/schema
inventory, program/orchestration contracts, and Unreleased changelog describe
the final WLA-26-09 boundary and distinguish the embedded core from both the
WLA-26-10 delivery rails and WLA-26-11 public runtime surface.

The final combined planner/conductor/authority/deliberation matrix passes
65/65 and the full core suite passes 457/457 on both Python floors.
Fresh-wheel packaging and the guided, deliberate, multi-agent, outward-loop,
canon, documentation, snippet, agent-surface, roadmap, rider, update-parity,
compile, and diff gates are green. Exact results and recovery assertions are
captured in [evidence-story-09](./evidence-story-09.md).

Integration, Git, evidence, certification, and roadmap mutation remain out of
scope here and owned by WLA-26-10. WLA-26-09 merely consumes their fresh
authoritative completion facts on the next replay.
