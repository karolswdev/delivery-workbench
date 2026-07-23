# Phase 26 continuation handover

**Snapshot:** 2026-07-23, after WLA-26-09
**Branch:** `main`
**Starting HEAD:** `90e9b28` (`Document Phase 26 conductor handover`)
**Roadmap state:** Phase 26 open, 9/12; WLA-26-10 is next
**Worktree at snapshot:** contains the uncommitted WLA-26-09 implementation,
tests, project documentation, story evidence, and roadmap closeout; `main` is
13 commits ahead of `origin/main`; nothing from this sequence was pushed

This is a continuation snapshot, not a replacement for
[current-phase-status](./current-phase-status.md),
[story-09](./story-09-conduct-and-recover-hierarchical-multi-phase-programs.md),
or [evidence-story-09](./evidence-story-09.md).

## Completed through WLA-26-09

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
   completion.

The product is not yet autonomously integrating or advancing roadmap files.
WLA-26-10 owns those separately authorized delivery rails. WLA-26-11 owns
public live controls, and WLA-26-12 owns the installed multi-phase exit exam.

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

## Immediate next story: WLA-26-10

Read
[story-10](./story-10-integrate-work-and-advance-exact-roadmap-rails.md)
before implementation. Compose new rails around the existing program claim and
conductor contracts; do not add a generic shell runner, direct Markdown
mutation, or a second delivery ledger.

The useful dependency order is:

1. pure integration preview over exact run/claim/proof/verdict/story/phase,
   repository/index/diff, evidence, contract, and optional remote facts;
2. exact isolated-diff apply with allowed paths, expected base/result trees,
   freshness, no partial write, and no automatic conflict resolution;
3. separately claimed evidence materialization and PMO contract generation;
4. explicit objective-versus-governed certification mapping with honest
   machine/program provenance;
5. separately claimed gated commit and optional fast-forward push to the bound
   remote/ref;
6. canonical roadmap story completion, next-story start, and phase transition
   through existing preview/fingerprint/apply cores; and
7. obligation materialization/disposition with stable decision/obligation ids,
   separate capability, deduplication, and retained audit history.

Exercise at least two stories and one phase transition in a clean fixture repo
with a local bare remote. Plant crashes after every evidence, integration,
contract, certification, commit, push, story, and phase receipt. Reconcile
existing durable state before retry and prove no duplicate blocks, status
flips, summaries, commits, or pushes.

## Non-negotiable WLA-26-10 boundaries

- A green check, verifier, council, meta-verifier, or architect result grants
  no delivery act by implication.
- Evidence, integration, objective certification, governed certification,
  contract generation, commit, push, story completion, story start, phase
  advancement, obligation materialization, and obligation disposition remain
  separately claimed capabilities and receipts.
- A blocking obligation prevents story/phase advancement. A non-blocking item
  remains ledger-visible; it becomes roadmap work only through separate,
  deduplicated authority.
- Machine certification may assert only canonically declared fully mechanical
  facts. Subjective certification remains an accountable rubric-backed
  judgment; neither may claim a human acted when one did not.
- Commit binds exact parent, staged tree, message/trailers, contract digest,
  proof, and gate result. Push binds the exact commit, remote/ref, URL
  fingerprint, observed head, and fast-forward lease. No force push.
- Merge, rebase/conflict auto-resolution, release, deploy, publication,
  arbitrary shell/network, policy edits, authority minting, and
  cross-repository writes remain impossible in Phase 26.
- The WLA-26-09 conductor may consume WLA-26-10 receipts/facts on replay but
  must not perform an unclaimed shortcut around them.

## Source map

- `pmo-roadmap/lib/dw_pmo/program_conductor.py` — replay-first frontier, tick,
  receipts, drivers, work/council/loop/gate/outward/scope behavior.
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
  `steps.py`, and guarded roadmap mutation helpers — existing rails to compose
  in WLA-26-10, not duplicate.
- `.githooks/dw_pmo/` — vendored package; keep byte-equivalent via
  `pmo-roadmap/update.sh .`.
- `pmo-roadmap/tests/dw-core-tests.py` — 20 conductor tests plus planner,
  authority, deliberation, and wider regressions.
- [docs/programs.md](../../../../../docs/programs.md) — normative program
  contract and exact WLA-26-09/WLA-26-10 boundary.

## Validation baseline

WLA-26-09 closes with:

- focused planner/conductor/authority/deliberation matrix: 65/65 on Python
  3.14 and 65/65 on Python 3.9;
- full core suite: 457/457 on Python 3.14 and 457/457 on Python 3.9;
- fresh-wheel Python 3.9 package smoke, including guided, deliberate,
  multi-agent, and outward-loop exams;
- canon, all Markdown, executable snippets, agent surfaces, roadmap, rendered
  rider, source/vendored update parity, compile, and diff checks.

Exact assertions, commands, timings, and package outcomes are in
[evidence-story-09](./evidence-story-09.md).

Useful commands:

```bash
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

- Last committed checkpoint is still `90e9b28`; WLA-26-09 is intentionally
  uncommitted in this snapshot.
- Source and vendored code, tests, root/framework READMEs, solution overview,
  architecture, interop, program/orchestration contracts, changelog, story,
  status, evidence, and this handover are all part of the active worktree.
- No push was performed. Recheck branch/upstream state before any publication;
  the snapshot observed `main...origin/main [ahead 13]`.
- Preserve unrelated user changes if a later session finds additional dirty
  paths.

## First actions for the next session

1. Read this handover, current phase status, WLA-26-10, WLA-26-09 evidence, and
   the integration/advancement section of `docs/programs.md`.
2. Confirm `git status -sb`, recent commits, and source/vendored parity; do not
   assume the snapshot is still current.
3. Keep WLA-26-09 green and use its exact program claims/receipts as the only
   authority boundary for new rails.
4. Contract WLA-26-10 previews and receipt schemas in docs/tests before adding
   repository or roadmap mutation.
5. Preserve both Python floors, fresh-wheel packaging, no-program vanilla
   behavior, and project-facing documentation from the first WLA-26-10 slice.
