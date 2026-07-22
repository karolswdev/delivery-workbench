# WLA-26-09 — Conduct and recover hierarchical multi-phase programs

- **Project:** work-log-automation
- **Phase:** 26
- **Status:** backlog
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
  strict child grants; fan-out/in; bounded loop/debate/council/verifier/meta/
  architect scheduling; artifact/verdict/gate reconciliation; outward signal/
  nudge integration; retry/repair/escalation; program supervision; claim-before-
  dispatch, poll/reconcile-before-retry, ledger replay and recovery.
- **Out:** a second scheduler per surface; hidden background daemon; infinite
  loops; parallel integration of multiple stories; automatic graph/rubric/
  authority changes; conflict resolution.

## Acceptance criteria

- [ ] One tick replays state, reconciles existing claims/outward facts, selects
  a stable eligible set within concurrency/resource/budget bounds, claims each
  exact next act, dispatches or polls it, records outcomes/routes, and stops.
- [ ] Hierarchical lineage addresses program→phase→story→workflow/subflow→loop
  round→node/role/attempt so every artifact, verdict, nudge and failure route is
  attributable and replay-stable without flattening away organizational meaning.
- [ ] The conductor enforces implementer/verifier separation and declared
  council/meta/architect order; failed or dissenting verdicts can only retry,
  repair, re-debate, escalate, pause or abort along finite compiled routes.
- [ ] Bounded supervision merely repeats the same tick until a declared
  terminal/poll/checkpoint/budget/time ceiling; it cannot auto-start, elevate
  authority, swallow refusal, or spin when no progress is possible.
- [ ] Planted crashes before/after every claim/dispatch/receipt boundary recover
  with zero duplicate agent/check/nudge/debate speaker/verdict/gate/story-start
  events and with external operations reconciled before retry.
- [ ] Unknown/blocked activity, unavailable required role, quorum loss, repair
  exhaustion, architect veto, stale facts and budget exhaustion stop distinctly;
  none causes the scheduler to skip the story or phase silently.

## Test plan

- **Unit:** scheduler eligibility, hierarchy, loop, route, claim, recovery and
  bounded-supervisor tests on both Python floors.
- **Integration:** fixture program spans at least two stories, nested fan-out,
  verifier repair, debate/meta-audit and phase architect review across multiple
  process restarts.
- **Manual / device:** inspect replay explanation at active, debate, repair,
  phase-boundary and stopped states.

## Notes / open questions

Only one story may own the integration lane in Phase 26. Read-only research,
debate and verification may run concurrently when their declared resource and
context rules permit it.
