# Phase 26 continuation handover

**Snapshot:** 2026-07-22, after WLA-26-08  
**Branch:** `main`  
**HEAD:** `50b8645` (`Complete WLA-26-08: grant finite program authority`)  
**Roadmap state:** Phase 26 open, 8/12; WLA-26-09 is next  
**Worktree at handover creation:** clean; `main` was 12 commits ahead of
`origin/main`; nothing from this sequence was pushed

This is a continuation snapshot, not a replacement for
[current-phase-status](./current-phase-status.md) or
[the program contract](../../../../../docs/programs.md). If they disagree,
inspect later commits and treat the current canon and evidence as authoritative.

## Product direction to preserve

Delivery Workbench is becoming capable of running a governed autonomous
delivery organization across multiple stories and phases. A program may assign
specialist implementers, independent verifiers, panels, deliberative councils,
meta-verifiers and master architects; run bounded debate, repair and escalation
loops; carry decision obligations; and advance exact delivery and roadmap rails
under finite authority.

Autonomy remains optional:

- vanilla Delivery Workbench without program configuration is a complete,
  healthy mode;
- Phase 24/25 bounded score/run orchestration remains a separate opt-in mode;
- opening the Workbench, Program Studio, saving policy, installing or updating
  never starts a program, creates authority, launches a process or makes a
  network request;
- advisory, checkpointed and continuous programs use the same explicit grant
  machinery, with different ceilings and stop behavior;
- only a separately reviewed, finite, expiring and revocable grant permits
  autonomous work.

Do not reinterpret “can be autonomous” as “is automatic by default.”

## What is complete

WLA-26-01 through WLA-26-08 are done and evidence-backed:

1. Program trust, compatibility and schema contract.
2. Pure multi-phase selection and deterministic role assignment.
3. Reusable hierarchical workflows with statically bounded loops/subflows.
4. Organization topology, execution profiles and separation of duties.
5. Authority-neutral debate/council/meta-verification replay cores.
6. Program Studio with lossless graph/config round trips and no start effects.
7. Mechanical facts, agent/panel verdicts, council decisions and obligations.
8. Exact program-start consent, immutable grant, finite budgets, exclusive
   claims, strict child authority, controls, freshness and hash-chain replay.

The main WLA-26-08 implementation is
`pmo-roadmap/lib/dw_pmo/program_run.py`; the installed/vendored copy is
`.githooks/dw_pmo/program_run.py`. Its public boundary includes:

- `build_program_start_plan` and `start_program`;
- `replay_program`, `program_freshness_issues` and `program_run_inventory`;
- `build_program_claim_preview` and `apply_program_claim`;
- `build_program_completion_preview` and `apply_program_completion`;
- `build_program_control_preview` and `apply_program_control`;
- `derive_child_grant` and `validate_child_grant`.

Authority is stored only beneath
`.git/pmo-programs/runs/<program-run-id>/` as immutable `plan.json`, immutable
`grant.json` and authoritative hash-chained `ledger.jsonl`. Projections and
child grants are derived, not trusted caches.

The current authority core deliberately does **not** dispatch workflow work,
run drivers, integrate results, mutate the roadmap or expose program control
surfaces. Those boundaries belong to WLA-26-09 through WLA-26-11.

## Council and decider semantics

A council is governed deliberation among declared seats over a shared matter.
It is distinct from a review panel, whose reviewers issue independent verdicts
without deliberating with one another.

Final outcome authority is declared before the council starts:

- `rule`: a closed majority/weighted/unanimous rule computes the result;
  `decider_seat` is null. A chair may record or summarize but cannot override.
- `judge`: one preassigned `decider_seat` chooses only among charter-allowed
  outcomes after quorum, veto, evidence and budget constraints are applied.
- `checkpoint`: a separately authorized human/external principal answers a
  typed request; no agent may impersonate that port.
- A rule council may declare a judge-only tie route. That seat is the decider
  only when the tie route is actually taken.

The decider is identified by stable hierarchical seat address plus assignment
generation/hash, not display name or model label. The frozen decision proof
also binds logical profile, principal, registered harness/adapter and version,
router/provider, model vendor/family/id/revision-or-honest-alias, auth-domain
fingerprint, workspace and session. Claude CLI/Sonnet, Pi/OpenRouter/Kimi or
another registered binding can fill a seat, but changing the resolved binding
requires explicit reassignment/new authority. A participant cannot self-elect,
silently substitute, delegate the final decision or invent a route.

Every council decision carries an explicit obligations array, even when empty.
Blocking obligations stop advancement. Non-blocking backlog, technical debt,
risk, research and follow-up obligations remain durable until completed,
superseded, escalated or explicitly waived. Roadmap materialization and
disposition are separately granted acts.

Keep ordinary `verdict:issue`, `council:decide`, `obligation:record` and
`certification:verdict` as independent capabilities. An agent verdict or green
test does not silently grant certification authority.

## Work remaining

The remaining dependency order is intentional:

1. [WLA-26-09](./story-09-conduct-and-recover-hierarchical-multi-phase-programs.md)
   — conduct and recover the hierarchy.
2. [WLA-26-10](./story-10-integrate-work-and-advance-exact-roadmap-rails.md)
   — apply certified results and exact evidence/Git/roadmap acts.
3. [WLA-26-11](./story-11-operate-the-autonomous-organization-across-every-surface.md)
   — CLI/MCP/HTTP/Workbench control-room parity.
4. [WLA-26-12](./story-12-prove-a-fully-autonomous-multi-phase-program.md)
   — installed-wheel, multi-phase, crash-recovery and vanilla-regression proof.

The product is therefore not yet autonomously advancing roadmaps. It can
compile the organization and grant finite authority for every required act,
but no Phase 26 conductor currently consumes those reservations.

## Immediate next story: WLA-26-09

Build one new program conductor around a deterministic `tick_program`. Do not
extend Phase 24's `delivery-workbench-orchestration@1` semantics or create a
second authority mechanism. The useful implementation shape is:

1. Acquire one program-conductor lock for the run.
2. Replay `program_run` and refuse corrupt, stale or non-runnable authority.
3. Reconcile unresolved claims and outward driver facts before selecting work.
4. Rebuild the deterministic program frontier, workflow instance and exact
   organization assignment from the frozen grant/current permitted facts.
5. Derive the next stable hierarchical act(s) within concurrency, role,
   resource and remaining-budget ceilings.
6. Reserve each act through `build_program_claim_preview` plus
   `apply_program_claim` before dispatch or polling.
7. Invoke only a registered, versioned, closed driver adapter; pass the claim's
   deterministic idempotency key and exact derived child grant.
8. Reconcile/poll the same external operation after uncertainty or restart;
   never infer from a missing local receipt that the operation did not happen.
9. Validate the closed artifact/verdict/decision/obligation result with the
   existing pure core, then complete the exact claim.
10. Return one content-safe tick projection and stop. Bounded supervision may
    repeat this tick, but it may not become an ambient daemon or spin without
    progress.

Stable lineage must retain
`program/phase/story/workflow/subflow/loop-round/council/seat/node/role/attempt`.
Do not flatten this into a generic task queue: replay must explain who acted,
under which role and provider/model assignment, on which round and route.

The first WLA-26-09 vertical slice should be narrow but real:

- new source module, likely `dw_pmo/program_conductor.py`, plus vendored/export
  parity;
- pure next-act derivation for one selected story and compiled workflow;
- claim-before-dispatch through `program_run`;
- one fixture registered adapter with start/poll/reconcile behavior;
- one implementer result followed by an independent verifier result;
- planted crash immediately before and after dispatch and receipt;
- replay proving no duplicate start, claim, verdict or route transition.

Then layer fan-out/fan-in, repair loops, deliberation, rule/judge/checkpoint
decisions, obligation recording, meta-verification, master-architect phase gates,
outward signals and the exact scope-complete transition. Do not jump to Git or
roadmap mutation; those are WLA-26-10 rails.

## Existing cores to compose, not duplicate

- `programs.py`: program compile, scope/frontier plan and authority policy.
- `program_workflow.py`: hierarchy, finite envelopes, node/loop routes.
- `program_organization.py`: stable assignment, roles, replacement and
  separation proof.
- `program_deliberation.py`: bounded council round claims/submissions,
  decision authority, dissent and meta/architect packets.
- `program_verdict.py`: mechanical facts, rubric-bound agent/panel verdicts,
  freshness and quality gates.
- `program_run.py`: the only program grant/claim/control/replay authority.
- `orchestration_driver.py`: current registered-driver inventory and execution
  binding seam.
- `orchestration_conductor.py`: useful Phase 24 reference for deterministic
  tick, lock and recovery patterns, but not a program scheduler to mutate.

Prefer editing `pmo-roadmap/lib/dw_pmo/` and then run
`pmo-roadmap/update.sh .` to refresh `.githooks/dw_pmo/`. Keep source,
vendored package exports and installed-wheel behavior identical.

## Persistence and event constraints

Current program-ledger events are only `program_started`, `claim_reserved`,
`claim_completed`, `program_paused`, `program_resumed`, `program_revoked`,
`program_cancelled` and `program_exhausted`. Claim categories already cover
selection, assignment, child/agent/check work, council/debate/loop rounds,
verdict/gate/repair, obligations, evidence/integration/certification, commit,
push, story/phase rails, nudges, notifications and checkpoint requests.

WLA-26-09 may add versioned conductor/artifact/decision receipts and the exact
scope-complete transition, but all authority must originate in a reserved
program claim. Any bounded receipt/artifact storage must remain subordinate to
the immutable grant and authoritative ledger. Do not add a mutable projection
whose deletion or editing changes program meaning.

Program states are authority states, not UI activity labels. Waiting for an
agent, repairing or deliberating should be derived conductor views; do not add
them casually to the grant state machine.

## Non-negotiable refusal boundaries

Stop rather than improvise when any of these is true:

- policy, roster, provider/model/auth, repository or roadmap freshness changed;
- the required role/decider is unavailable or substitution is undeclared;
- verifier independence, council quorum, veto or architect policy fails;
- a compiled route, capability, typed port or finite budget is absent;
- a blocking obligation remains open;
- an external operation is uncertain and cannot be reconciled safely;
- ledger replay is corrupt, forked, truncated, reordered or hash-invalid;
- selection would skip a held/failed/dissenting story for easier work;
- execution would require arbitrary tracked argv, raw credentials, arbitrary
  network destinations, merge/conflict resolution, release, deployment,
  publication or cross-repository writes.

Pause/revoke/cancel and bounded in-flight receipts must remain available under
their existing rules. Revocation generation invalidates future claims and
typed requests; it must not be bypassed by conductor-local state.

## Verification baseline

At `50b8645` the following passed:

- full core suite: 433/433 on Python 3.14;
- full core suite: 433/433 on the Python 3.9 floor;
- focused WLA-26-08 authority tests: 17/17 on both floors;
- broader program slice: 89/89 on both floors;
- fresh-wheel package smoke on Python 3.9, including existing bounded
  orchestration/outward-loop exams and healthy empty program inventory;
- canon lint, docs lint, executable docs snippets, agent-surface parity,
  source/vendored update parity, compile checks, roadmap check and diff check.

Evidence is in [evidence-story-08](./evidence-story-08.md). Re-run the full
matrix after changing shared runtime/driver code; do not rely only on new
focused tests.

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

## Repository and commit notes

- Last three completed stories:
  - `50b8645` — WLA-26-08 finite program authority.
  - `3238199` — WLA-26-07 governed quality decisions.
  - `419bdd2` — WLA-26-06 Program Studio.
- The WLA-26-08 commit changed 26 files and introduced `program_run.py` in
  source and vendored packages plus its evidence document.
- No push was performed. Verify branch/upstream state again before publishing;
  the handover snapshot observed `main...origin/main [ahead 12]`.
- The repository was clean before this handover document was added. Preserve
  unrelated user changes if the next session finds a dirty worktree.

## First actions for the next session

1. Read this handover, `current-phase-status.md`, WLA-26-09 and the program
   grant/recovery sections of `docs/programs.md`.
2. Confirm `git status -sb` and recent commits; do not assume the snapshot is
   still current.
3. Inspect `ProgramRunAuthorityTest` and the Phase 24 conductor recovery tests
   before choosing the new conductor API.
4. Mark WLA-26-09 active only when implementation actually begins.
5. Contract the new tick/receipt schemas in docs and tests before adding
   dispatch side effects.
6. Preserve the optional/vanilla regression lane from the first test, not only
   at phase close.
