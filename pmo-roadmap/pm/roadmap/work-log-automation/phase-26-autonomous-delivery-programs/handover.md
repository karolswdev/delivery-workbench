# Phase 26 continuation handover

**Snapshot:** 2026-07-23, after WLA-26-11
**Branch:** `agent/wla-26-09-conductor`
**Roadmap state:** Phase 26 open, 11/12; WLA-26-12 is next
**Delivery state:** WLA-26-09/10 are published on the draft PR branch; this
checkpoint adds the WLA-26-11 implementation, tests, documentation, evidence,
and roadmap closeout.

This is a continuation snapshot, not a replacement for
[current-phase-status](./current-phase-status.md),
[story-11](./story-11-operate-the-autonomous-organization-across-every-surface.md),
or [evidence-story-11](./evidence-story-11.md).

## Completed through WLA-26-11

Phase 26 remains an explicitly configured layer above ordinary Delivery
Workbench and one-score/one-run bounded orchestration. No program is inferred
from install, update, Workbench open, Program Studio, a Phase 24 score, a
signal observer, or an existing bounded run.

The delivered sequence now includes:

1. WLA-26-01 — autonomous-program trust and compatibility contract;
2. WLA-26-02 — pure roadmap-scope selection and assignment;
3. WLA-26-03 — reusable finite hierarchical workflows;
4. WLA-26-04 — organizations, roles, provenance, and separation;
5. WLA-26-05 — bounded councils and meta-verification;
6. WLA-26-06 — lossless Program Studio authoring;
7. WLA-26-07 — governed rubric verdicts, quality gates, decisions, and
   obligations;
8. WLA-26-08 — finite local program grants, exclusive claims, child
   intersections, replay, and controls; and
9. WLA-26-09 — the restart-safe hierarchical conductor, including outward
   facts/nudges, cross-story/phase selection, obligation gates, and exact scope
   completion; and
10. WLA-26-10 — exact separately claimed evidence, integration, contract,
    certification, commit, push, obligation, story, and phase delivery rails;
    and
11. WLA-26-11 — one byte-equivalent program surface across CLI, MCP, HTTP,
    SSE, Workbench control room, typed notifications, and bounded streams.

The embedded core and public surfaces can now plan, start, explain, operate,
observe, and integrate a governed autonomous program without introducing a
second scheduler or authority path. WLA-26-12 alone remains and owns the
installed multi-phase exit exam.

## WLA-26-09 delivered runtime

`program_conductor.py` composes the existing pure planner, workflow,
organization, verdict, deliberation, signal, driver, and program-authority
cores. It does not introduce another authority store:

- `derive_program_frontier` is pure and explains the next exact act or stop;
- `tick_program` locks, replays, freshness-checks, reconciles, claims at most
  one act, dispatches or records it, and returns;
- `supervise_program` only repeats that same tick within finite tick and
  wall-time bounds; and
- `program_run` remains the sole hash-chained authority ledger.

The conductor covers isolated agent work, deterministic collection, registered
checks, mechanical facts, independent verification, finite repair, bounded
debate/council/meta-review, durable obligations, typed structural-loop rounds,
and final-story master-architect gates. Claim, dispatch, output, decision,
verdict, obligation, loop, and gate receipts retain exact hierarchical lineage
and immutable hashes.

`claim_dispatched` is recorded before external start. Restart reconciles the
same deterministic operation/idempotency key; a missing session after dispatch
is `external-operation-uncertain`, not permission to start again. Closed
fixture and version-pinned Pi adapters prove exact argv, model/provider/auth
binding, scrubbed credential handling, and version-skew refusal.

## Outward facts and standing nudges

Program policy may declare a closed finite `nudges` list. Each rule binds one
of `ci-failed`, `changes-requested`, or `merge-conflict` to one exact program
binding and uniquely expanded agent target outside a structural-loop round.
It has finite `max_per_signal` and `max_total` ceilings and requires
`program:select`, `nudge:deliver`, sufficient global nudge capacity, and
worst-case target start/artifact capacity.

Program start requires one resolving exact remote-tracking ref when rules
exist and freezes its Phase 25 signal-channel branch. The conductor never polls
the network. Before selection it may consume only an already-observed,
hash-verified local fact:

1. one `outward-fact` claim records only rule/hash, signal kind, event
   hash/sequence, and channel hash;
2. one `nudge` claim binds that fact, exact already-run target lineage, next
   attempt, idle receptivity, expectation, and finite ceilings;
3. the target packet and result bind the nudge receipt; and
4. dependent DAG work, independent verification, and any stale architecture
   boundary receive causal new attempts.

Raw forge prose, URLs, logs, review bodies, credentials, and notification
payloads never enter the ledger or nudge packet. A newer green/resolved fact
ends the match. A completed council or structural-loop outcome is not silently
rewritten; replay stops as `nudge-governance-replay-required`.

## Scope transitions and obligations

The WLA-26-08 start plan now freezes the deterministic union of all seats and
checkpoint ports reachable across the entire granted scope, not only the first
selected story. When WLA-26-10 later records fresh, separately authorized
completion facts, the next conductor tick can safely select the next exact
binding, story, workflow, team, and phase without acquiring a new principal,
provider/model/auth binding, or port.

Non-blocking obligations remain in the content-safe frontier across selection,
phase change, and restart. An open blocking obligation stops before selection
as `blocking-obligation-open`. When the pure planner reports the entire scope
done, one exact `program-scope-proof` claim stores one immutable receipt and
records one `program_scope_completed` event. Crash after that receipt recovers
the same terminal `complete` result.

## WLA-26-10 delivered runtime

`program_delivery.py` composes existing authority, evidence, contract, gate,
verify, and roadmap-mutation cores without adding a second ledger:

- `build_program_delivery_preview` is pure and binds the immutable program
  grant/ledger, current claim, proof packet, mechanical and governed verdicts,
  story/phase state, candidate artifact, repository/index/tree, contract,
  optional remote, and every separately requested act;
- `start_program_delivery` freezes
  `delivery-workbench-program-delivery-plan@1`; tick/replay/supervise reserve
  one dependent claim at a time, reconcile its outward effect, and store one
  ledger-bound `delivery-workbench-program-delivery-receipt@1`;
- the candidate diff is simulated in temporary Git object/index stores and is
  applied exactly with fixed `git apply --index --binary`; changed base,
  artifact, allowed paths, result tree, index, or worktree refuses before
  advancement, with no three-way or conflict-resolution route;
- evidence and canonical story/phase mutations are planned as exact guarded
  content; contract generation sees the complete staged candidate tree,
  objective/governed certification maps every assertion to current proof, and
  the real gate, hooks, commit, and one-commit range verification execute
  without bypass; and
- optional push resolves only the grant-bound remote URL, head and branch,
  re-observes the exact lease, requires fast-forward, uses no force option, and
  records/rebinds the resulting tracking fact.

Blocking obligations refuse delivery before any partial advance. Non-blocking
items remain durable without forced roadmap mutation. Separate materialization
may create exactly one traced, deduplicated roadmap story through the canonical
story-create plan; separate disposition records completion, supersession,
escalation, or an accountable exact waiver while retaining the original
decision and obligation.

The fixture proof executes two story commits and one phase transition against
a local bare remote. Crashes after first-story effects and second-story
receipts reconcile to the same evidence, archive, commits, remote ref, status,
phase summary, pointer, and next-story start. Hook failure, planted remote
divergence, dirty/stale/tampered state, blocking debt, missing objective
capability, duplicate materialization, and unauthorized waiver all stop
without a force or partial-advancement escape.

## WLA-26-11 delivered operations

`program_surface.py` is the shared public projection over the pure planner,
program authority ledger, conductor, and delivery protocol:

- inventory, detail, tail, and explicit bounded stream reads are pure verified
  observations; an absent program directory is healthy and creates nothing;
- grant planning/start, exact action preview/apply, one-act tick, and bounded
  supervision retain one canonical payload across CLI JSON, MCP
  `structuredContent`, HTTP `data`, Workbench bootstrap, and SSE replay;
- exact previews bind the grant, ledger head, generation, state, derived
  operation, capability, budget, and closed parameters. Apply rechecks that
  binding while holding the authority-owning lock, so concurrent surface
  clients cannot both act from one stale frontier; and
- `supervise` only repeats the same public tick for explicit finite tick and
  duration ceilings, exposing every result and stopping on checkpoint,
  terminal state, no progress, budget, or duration.

The CLI now exposes `program list|show|validate|simulate|plan|start|preview|
tick|supervise|request|pause|resume|revoke|cancel|tail|stream`. MCP exposes the
same 16 operations through strict version-pinned tools. HTTP adds exact
`/api/programs/*` reads, previews, acts, SSE, and bounded streams with scalar
allowlists and no arbitrary policy, prompt, command, capability, credential,
or retry inputs at act time.

The responsive Workbench control room explains intent, workflow, organization,
seat/provider/model/auth provenance, independence, councils/deciders, nested
activity, artifacts, facts/verdicts/dissent, rounds, gates, obligations,
delivery, budgets, capabilities, next actions, refusals, and the verified
timeline. It opens SSE only on an explicit run route, closes it on route exit,
never polls for authority, and opens output streams only on demand. Program
Studio projects portable exact/constrained execution profiles against local
registered adapter availability and fingerprints without credentials or
arbitrary commands.

Notifications are content-safe derivations of the same verified surface and
cover intervention, disagreement, decider/provider loss, architect veto, new/
blocking/overdue obligations, budget exhaustion, integration refusal, and
completion. A response remains a closed approve/reject request document; the
transport receives no act token and cannot become authority.

## Immediate next story: WLA-26-12

Read
[story-12](./story-12-prove-a-fully-autonomous-multi-phase-program.md) before
implementation. The embedded authority/conductor/delivery core and its shared
public operations are now present; WLA-26-12 should prove those exact packaged
surfaces in the installed no-human, multi-phase exit exam rather than creating
another runtime or test-only path.

Keep these boundaries:

- exercise more than one phase and story from a fresh wheel with no source-tree
  imports or hidden human response;
- include specialist implementation, independent verification, one bounded
  debate and repair loop, meta-verifier and master-architect participation,
  evidence/integration/commit/push, exact story/phase advancement, and planted
  crash recovery;
- prove the complete stale/divergent/exhausted/revoked/under-authorized/
  obligation/refusal matrix through the same installed public operations;
- run a separate fresh no-program consumer proving healthy vanilla behavior
  and the absence of ambient program stores, streams, pollers, processes, or
  notifications;
- no surface may add generic shell, provider-secret, certification, commit,
  push, roadmap, merge, release, deploy, or publication authority;
- vanilla and Phase 24/25 bounded-run surfaces remain complete independent
  modes with no ambient program activation; and
- keep the Python 3.9 floor, current interpreter, source/vendored parity, and
  project-facing docs green through phase closeout.

## Source map

- `pmo-roadmap/lib/dw_pmo/program_surface.py` — canonical inventory, control
  room view, tail/stream reads, exact public previews/applies, tick, and bounded
  supervision.
- `pmo-roadmap/bin/dw`, `mcpserver.py`, and `workbench.py` — strict CLI, MCP,
  HTTP, SSE, and Workbench transport framing over the shared surface.
- `pmo-roadmap/workbench/` — responsive planning inventory and live program
  control room; explicit run-route SSE and bounded on-demand output streams.
- `pmo-roadmap/lib/dw_pmo/notifications.py` — verified program notification
  derivation, typed request responses, and local exact-act correlation.
- `pmo-roadmap/lib/dw_pmo/program_studio.py` — portable execution-port policy
  plus safe local availability, diversity, fallback, and fingerprint
  projection.
- `pmo-roadmap/lib/dw_pmo/program_conductor.py` — replay-first frontier, tick,
  receipts, drivers, work/council/loop/gate/outward/scope behavior.
- `pmo-roadmap/lib/dw_pmo/program_delivery.py` — pure delivery preview,
  immutable plan/receipt replay, exact candidate-tree integration,
  evidence/contract/certification/commit/push/roadmap rails, and obligation
  materialization/disposition.
- `pmo-roadmap/lib/dw_pmo/program_run.py` — start/grant/ledger/claim/
  completion/control authority, scope-wide roster/ports, terminal scope event.
- `pmo-roadmap/lib/dw_pmo/programs.py` — program schema/compiler/planner,
  standing-nudge validation and worst-case envelopes.
- `pmo-roadmap/lib/dw_pmo/signals.py` — shared current-fact matcher over the
  hash-chained Phase 25 signal projection.
- `pmo-roadmap/lib/dw_pmo/program_verdict.py` — mechanical facts, governed
  verdicts, quality gates.
- `pmo-roadmap/lib/dw_pmo/program_deliberation.py` — pure council protocol and
  decisions.
- `pmo-roadmap/lib/dw_pmo/evidence.py`, `contract.py`, `gate.py`, `verify.py`,
  `steps.py`, and guarded roadmap mutation helpers — canonical rails composed
  by delivery, including honest machine/program contract certification and
  one guarded phase summary/pointer/header transition.
- `.githooks/dw_pmo/` — vendored package; keep byte-equivalent via
  `pmo-roadmap/update.sh .`.
- `pmo-roadmap/tests/dw-core-tests.py` — seven public-surface/parity/race tests,
  20 conductor tests, Studio/notification checks, plus planner, authority,
  deliberation, delivery, and wider regressions.
- [docs/programs.md](../../../../../docs/programs.md) — normative program,
  delivery authority, recovery, refusal, public-surface, and control-room
  contract.

## Validation baseline

WLA-26-11 adds seven focused public-surface/parity/race/request tests, expands
the exact MCP/HTTP/CLI and Studio/notification contracts, and renders 58
desktop/mobile browser states including real active and revoked program
ledgers. The full two-floor core suite, fresh-wheel package smoke, Workbench
explorer/UI smoke, canon/docs/snippets, agent surfaces, roadmap, rendered
rider, source/vendored parity, compilation, ShellCheck, and diff checks form
the green closeout matrix captured in
[evidence-story-11](./evidence-story-11.md).

Useful commands:

```bash
python3 pmo-roadmap/tests/dw-core-tests.py -q ProgramSurfaceTest
/usr/bin/python3 pmo-roadmap/tests/dw-core-tests.py -q ProgramSurfaceTest
python3 pmo-roadmap/tests/dw-core-tests.py -q
/usr/bin/python3 pmo-roadmap/tests/dw-core-tests.py -q
pmo-roadmap/tests/package-smoke.sh
pmo-roadmap/tests/workbench-explorer.sh
pmo-roadmap/tests/workbench-ui-smoke.sh
pmo-roadmap/tests/canon-lint.sh
pmo-roadmap/tests/docs-lint.sh
pmo-roadmap/tests/docs-snippet-smoke.sh
pmo-roadmap/tests/agent-surface.sh
pmo-roadmap/update.sh . --check
.githooks/dw check work-log-automation
.githooks/dw rider docs --check
git diff --check
```

## Repository and continuation notes

- WLA-26-09 is commit `6f52011` on
  `agent/wla-26-09-conductor`; the branch tracks its same-named origin and
  draft PR.
- WLA-26-10 is commit `43aba10`, followed by its ShellCheck hardening commit
  `4feb2d4`, on the same branch and draft PR.
- WLA-26-11 source and vendored code, tests, Workbench assets, root/framework
  READMEs, solution overview, architecture, interop/MCP/program contracts,
  changelog, story, status, evidence, and this handover belong to one delivery
  checkpoint.
- Preserve unrelated user changes if a later session finds additional dirty
  paths, and recheck branch/upstream/PR state before publication.

## First actions for the next session

1. Read this handover, current phase status, WLA-26-12, WLA-26-11 evidence,
   and the installed-exam/public-surface sections of `docs/programs.md`.
2. Confirm `git status -sb`, recent commits, and source/vendored parity; do not
   assume the snapshot is still current.
3. Keep WLA-26-09/10/11 green and use their exact installed program
   claims/receipts and shared public surface as the sole authority boundary.
4. Build WLA-26-12 as a fresh-wheel external exam over the shipped adapters;
   do not import the source tree or add test-only runtime authority.
5. Preserve both Python floors, no-program vanilla behavior, complete refusal
   proof, crash idempotency, and project-facing documentation through phase
   closeout.
