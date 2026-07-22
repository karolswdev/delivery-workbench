# WLA-26-04 — Model agent roles, teams, and separation of duties

- **Project:** work-log-automation
- **Phase:** 26
- **Status:** done
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

- [x] Every continuous story route resolves one implementer and a distinct
  verifier identity/profile before work starts; a single session/attempt cannot
  satisfy both duties and the compiler refuses impossible independence.
- [x] Roles declare capabilities, workspace mode, allowed context/artifacts,
  output/verdict schemas, concurrency/resource groups, and which other roles
  they may request or judge; child grants are subsets of both program authority
  and role policy.
- [x] Assignment is deterministic from tracked logical pools plus operator-local
  driver availability, explains selection/fallback, and records exact role,
  profile, adapter capability fingerprint, and independence facts without
  storing secrets.
- [x] Replacement after unavailable/lost/failed agents follows a declared
  finite policy, never silently grants more capability, and preserves lineage
  so a replacement verifier cannot hide earlier dissent.
- [x] Fixtures prove implementer/verifier separation, council cardinality,
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

## Delivered

- Added one pure, closed organization compiler and `dw organization
  list|validate|simulate` surface over an optional tracked registry. An absent
  registry remains healthy and creates no state.
- Made role duties explicit across program/driver capability ceilings,
  workspace, context and artifact visibility, output/verdict schemas,
  cardinality, concurrency/resources, request/judgment edges, independence,
  councils, and finite replacement policy.
- Extended the local driver roster with non-secret principal identity,
  availability, adapter version, concurrency, principal fingerprint, and exact
  adapter-capability fingerprint; aliases sharing a principal cannot masquerade
  as independent.
- Integrated workflow role lanes with organization and program ceilings, then
  emitted deterministic role-slot receipts, verifier preassignment and session
  separation facts, candidate/fallback explanations, council quorum, and
  resource-compatible waves in the pure program plan.
- Added finite replacement previews that preserve assignment/verdict lineage,
  retain dissent, invalidate outstanding work, hold capability constant, and
  take the declared exhaustion route.
- Shipped the optional `autonomous-story-cell` template without creating
  consumer organization policy during install/update.
