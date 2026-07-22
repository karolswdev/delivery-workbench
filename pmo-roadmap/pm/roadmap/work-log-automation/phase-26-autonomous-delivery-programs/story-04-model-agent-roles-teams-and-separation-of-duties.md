# WLA-26-04 — Model agent roles, teams, and separation of duties

- **Project:** work-log-automation
- **Phase:** 26
- **Status:** backlog
  <!-- status vocabulary: roadmap-builder.md §2.3 -->
- **Depends on:** WLA-26-01, WLA-26-02
- **Unblocks:** WLA-26-05, WLA-26-06, WLA-26-07, WLA-26-08, WLA-26-09
- **Owner:** unassigned

## Problem

A graph of anonymous “agents” is not an organization. Autonomous quality
depends on named duties, different information/capability lanes, stable
assignment, and real separation between the person/model that produced work
and the one that judges it. The program needs to express teams such as
implementer, independent verifier, meta-verifier, master architect, researcher,
critic, judge, reviewer, and repairer without hard-coding providers.

## Scope

- **In:** versioned organization/team definitions; logical roles; required and
  optional assignments; capability/workspace/context/artifact visibility;
  independence and conflict-of-duty constraints; pool/cardinality/concurrency;
  stable local profile resolution; replacement, fallback, quorum, veto, and
  escalation policies; assignment receipts and explanation.
- **Out:** credentials or executable paths in tracked policy; employment-style
  identity; claims that two aliases backed by one session are independent;
  dynamic role invention by agents.

## Acceptance criteria

- [ ] Every continuous story route resolves one implementer and a distinct
  verifier identity/profile before work starts; a single session/attempt cannot
  satisfy both duties and the compiler refuses impossible independence.
- [ ] Roles declare capabilities, workspace mode, allowed context/artifacts,
  output/verdict schemas, concurrency/resource groups, and which other roles
  they may request or judge; child grants are subsets of both program authority
  and role policy.
- [ ] Assignment is deterministic from tracked logical pools plus operator-local
  driver availability, explains selection/fallback, and records exact role,
  profile, adapter capability fingerprint, and independence facts without
  storing secrets.
- [ ] Replacement after unavailable/lost/failed agents follows a declared
  finite policy, never silently grants more capability, and preserves lineage
  so a replacement verifier cannot hide earlier dissent.
- [ ] Fixtures prove implementer/verifier separation, council cardinality,
  architect visibility, restricted critic context, resource conflicts,
  unavailable pools, colliding identities, and capability downgrade/refusal.

## Test plan

- **Unit:** organization compile/assignment/conformance tests in
  `dw-core-tests.py`.
- **Integration:** fixture driver roster resolves a multi-role team and proves
  packet/workspace/artifact visibility boundaries across a restart.
- **Manual / device:** inspect the team/independence explanation; no device work.

## Notes / open questions

“Independent” is a configured technical property—distinct claimed execution
identity, context lane, and duty—not a claim that two models are statistically
independent. The UI and ledger must use that precise language.
