# Phase 26 continuation handover

**Snapshot:** 2026-07-23, after WLA-26-10
**Branch:** `agent/wla-26-09-conductor`
**Roadmap state:** Phase 26 open, 10/12; WLA-26-11 is next
**Delivery state:** WLA-26-09 is published on the draft PR branch; this
checkpoint adds the WLA-26-10 implementation, tests, documentation, evidence,
and roadmap closeout.

This is a continuation snapshot, not a replacement for
[current-phase-status](./current-phase-status.md),
[story-10](./story-10-integrate-work-and-advance-exact-roadmap-rails.md),
or [evidence-story-10](./evidence-story-10.md).

## Completed through WLA-26-10

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
    certification, commit, push, obligation, story, and phase delivery rails.

The embedded core can now conduct and integrate a governed autonomous program.
WLA-26-11 owns public CLI/MCP/HTTP/Workbench program operations and the live
control room; WLA-26-12 owns the installed multi-phase exit exam.

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

## Immediate next story: WLA-26-11

Read
[story-11](./story-11-operate-the-autonomous-organization-across-every-surface.md)
before implementation. The shared embedded planner/conductor/delivery APIs are
now present; WLA-26-11 should expose them byte-equivalently through CLI, MCP,
HTTP, and the Workbench control room rather than reimplementing state or
authority per surface.

Keep these boundaries:

- previews/list/status/explain remain pure and create no program state;
- every mutating public operation uses the same exact grant, claim, capability,
  budget, freshness, idempotency, and receipt core;
- the control room must explain current story/team/workflow/verdict/obligation/
  loop/budget/authority and active recovery state, not infer it from prose;
- no surface may add generic shell, provider-secret, certification, commit,
  push, roadmap, merge, release, deploy, or publication authority;
- vanilla and Phase 24/25 bounded-run surfaces remain complete independent
  modes with no ambient program activation; and
- WLA-26-12 still owns the fresh-wheel, no-human, multi-phase exit exam.

## Source map

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
- `pmo-roadmap/tests/dw-core-tests.py` — 20 conductor tests plus planner,
  authority, deliberation, and wider regressions.
- [docs/programs.md](../../../../../docs/programs.md) — normative program,
  delivery authority, recovery, refusal, and remaining public-surface
  contract.

## Validation baseline

WLA-26-10 adds six focused delivery/recovery/refusal tests on both supported
Python floors. The full core suite passes 464/464 on Python 3.14 and 464/464
on Python 3.9. Fresh-wheel package smoke, canon/docs/snippets, agent surfaces,
roadmap, rendered rider, source/vendored parity, compilation, and diff checks
complete the green closeout matrix captured in
[evidence-story-10](./evidence-story-10.md).

Useful commands:

```bash
python3 pmo-roadmap/tests/dw-core-tests.py -q ProgramDeliveryTest
/usr/bin/python3 pmo-roadmap/tests/dw-core-tests.py -q ProgramDeliveryTest
python3 pmo-roadmap/tests/dw-core-tests.py -q
/usr/bin/python3 pmo-roadmap/tests/dw-core-tests.py -q
pmo-roadmap/tests/package-smoke.sh
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
- WLA-26-10 source and vendored code, tests, root/framework READMEs, solution
  overview, architecture, interop/program contracts, changelog, story, status,
  evidence, and this handover belong to one delivery checkpoint.
- Preserve unrelated user changes if a later session finds additional dirty
  paths, and recheck branch/upstream/PR state before publication.

## First actions for the next session

1. Read this handover, current phase status, WLA-26-11, WLA-26-10 evidence, and
   the public-surface/control-room sections of `docs/programs.md`.
2. Confirm `git status -sb`, recent commits, and source/vendored parity; do not
   assume the snapshot is still current.
3. Keep WLA-26-09/10 green and use their exact program claims/receipts as the
   sole authority boundary for all public operations.
4. Contract WLA-26-11 byte-equivalent CLI/MCP/HTTP documents and control-room
   explanations before adding surface handlers or UI state.
5. Preserve both Python floors, fresh-wheel packaging, no-program vanilla
   behavior, and project-facing documentation from the first WLA-26-11 slice.
