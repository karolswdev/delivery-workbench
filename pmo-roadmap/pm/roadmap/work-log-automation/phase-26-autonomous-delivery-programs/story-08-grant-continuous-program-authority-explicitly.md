# WLA-26-08 — Grant continuous program authority explicitly

- **Project:** work-log-automation
- **Phase:** 26
- **Status:** backlog
  <!-- status vocabulary: roadmap-builder.md §2.3 -->
- **Depends on:** WLA-26-01, WLA-26-02, WLA-26-04, WLA-26-07
- **Unblocks:** WLA-26-09, WLA-26-10, WLA-26-11, WLA-26-12
- **Owner:** unassigned

## Problem

A sophisticated workflow still has no right to run itself. Completely
autonomous operation is legitimate only when an operator can review one exact
program, roadmap scope, organization, quality policy, worst-case envelope, and
integration boundary, then issue finite authority that can be inspected and
revoked. Advisory, checkpointed, and continuous must be profiles over the same
ledgered machinery rather than three subtly different products.

Those three are optional program profiles, not global product modes. Vanilla
Delivery Workbench and a bounded score/run select none of them and carry no
program store, program observer, or implicit program authority.

## Scope

- **In:** pure start plan; exact approval; immutable grant binding repository,
  roadmap/program/workflow/organization/rubric hashes and driver capability
  fingerprints; modes; child-run authority ceiling; capabilities for selection,
  work, verdict, evidence, diff integration, objective/agent-authorized
  certification, commit, push, story/phase advancement; budgets for phases,
  stories, rounds, councils, agents, checks, nudges, repairs, verdicts,
  integrations, bytes and wall time; expiry/pause/resume/revoke/cancel;
  append-only program ledger, claims and replay.
- **Out:** policy as consent; perpetual grants; merge/release/deploy/publication;
  provider credentials; caller-supplied commands; capability elevation in place.

## Acceptance criteria

- [ ] Preview states exact scope, candidate/team/workflow derivation, worst-case
  bounds, requested capabilities, exclusions, stop conditions, mode, expiry and
  accountable operator while writing and starting nothing.
- [ ] No program mode is auto-selected and no program grant is implied by
  install/update, shipped templates, the presence or execution of a bounded
  score, opening Workbench, or invoking ordinary `status`, `next`, `step`, or
  gate flows.
- [ ] Advisory authorizes no dispatch or mutation; checkpointed runs only
  between named typed ports; continuous can repeat exact program ticks and
  complete stories/phases with zero human interaction only inside the explicit
  capabilities and finite budgets.
- [ ] Child workflow/run grants are mechanically strict subsets of program,
  role, story, repository and remaining-budget authority; no child can certify,
  integrate, commit, push or advance merely because it can write code or judge.
- [ ] Ledger-first exclusive claims and hash-chained events cover selection,
  assignment, child grants, rounds, verdicts, gates, repairs, integration,
  roadmap transitions, controls and exhaustion; replay is the authority and
  projections are disposable.
- [ ] Every control/decision token binds action, reason/decision, ledger head,
  generation and state; stale/expired/revoked/over-budget/program-drift/
  repository-drift/roadmap-drift attempts refuse before dispatch or mutation.
- [ ] Revocation stops future child and integration claims immediately,
  expires outstanding typed requests, preserves bounded in-flight receipts,
  and cannot be reversed into a broader grant.

## Test plan

- **Unit:** plan/grant/token/budget/claim/replay/control and capability-subset
  tests on both Python floors.
- **Integration:** two processes race start/control/tick claims; expiry and
  revocation interrupt a fixture program without duplicate dispatch.
- **Manual / device:** inspect the visual authority envelope and confirm
  continuous mode makes its destructive ceiling unmistakable.

## Notes / open questions

The phase must make full autonomy possible, not mandatory. The same compiled
program should move between advisory, checkpointed, and continuous only by
issuing a new grant—never by editing a live grant.
