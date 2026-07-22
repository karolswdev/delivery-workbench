# WLA-26-05 — Run debates, councils, and meta-verification

- **Project:** work-log-automation
- **Phase:** 26
- **Status:** done
  <!-- status vocabulary: roadmap-builder.md §2.3 -->
- **Depends on:** WLA-26-03, WLA-26-04
- **Unblocks:** WLA-26-06, WLA-26-07, WLA-26-09, WLA-26-12
- **Owner:** unassigned

## Problem

Some decisions deserve more than one builder and one yes/no reviewer. The owner
explicitly wants debate corners, verifier-of-verifier checks, and master
architects who can challenge direction. Those patterns must be first-class,
bounded, and replayable—not a prompt asking several agents to “talk until they
agree.”

## Scope

- **In:** typed propose→critique→rebut→judge debate subflow; independent or
  adversarial review panels; council membership/cardinality; round topics and
  artifacts; quorum, weighted vote, unanimous, judge, veto, and tie policies;
  preserved dissent; verifier-of-verifier sampling/full audit; architect review
  at story/phase boundaries; repair/escalation routes; per-council budgets and
  receipts.
- **Out:** free-form chat rooms; open-ended deliberation; hidden chain-of-thought
  capture; agent-created membership/rules; majority vote presented as objective
  fact; a master architect with undeclared integration authority.

## Acceptance criteria

- [x] Debate rounds exchange only declared bounded artifacts (proposal,
  critique, rebuttal, verdict and citations); no private reasoning or transport
  transcript becomes required durable state.
- [x] Compile/simulation proves maximum rounds, speakers, starts, artifacts,
  time, token/output bytes, quorum, tie/exhaustion route, and which verdict can
  advance or request repair.
- [x] Council projection and ledger preserve every typed vote/verdict, evidence
  reference, dissent, abstention, replacement, judge rationale, and resulting
  route without exposing excluded prompt/content bodies.
- [x] A meta-verifier receives the exact verifier rubric, evidence and verdict
  lineage, cannot modify implementation, and emits a typed uphold/overturn/
  escalate result that never erases the original verdict.
- [x] A master-architect role can inspect declared cross-story/phase artifacts,
  issue a governed architecture verdict or repair/escalation request, and has no
  implicit commit/push/roadmap authority.
- [x] Fixture scenarios cover consensus, preserved minority dissent, tie,
  quorum loss, verifier overturn, architect-requested repair, budget exhaustion,
  crash between rounds, and deterministic replay with no duplicate speaker.

## Test plan

- **Unit:** debate/council/meta-verdict compiler and projection tests.
- **Integration:** fixture-driver council executes at least two rounds and one
  meta-verifier audit through restart, with exact artifact/receipt lineage.
- **Manual / device:** inspect council/debate rendering in WLA-26-06; no phone
  dependency.

## Notes / open questions

The product records concise declared artifacts and verdict rationale, not hidden
reasoning traces. “Debate” is a workflow protocol with evidence, not a demand
for chain-of-thought.

## Delivered

- Added an authority-neutral `program_deliberation` compiler/simulator and
  hash-chained replay engine over one already-compiled workflow, assigned
  organization, council, exact rubric, subject, evidence, and optional
  architect boundary.
- Made debate routes and byte/token/time bounds explicit, and extended council
  policy with majority, weighted, unanimous, or judge aggregation; role
  weights; vetoes; none/sample/full meta-audit; and finite per-council ceilings.
- Implemented deterministic propose→critique→rebuttal→judge claims, typed
  artifact/vote/verdict receipts, distinct-principal quorum, abstention,
  preserved dissent, tie/checkpoint, repair, redeliberation, and exhaustion.
- Added independent read-only meta-verifier packets/results that retain the
  original verdict, plus story/phase master-architect packets that explicitly
  lack implementation, integration, Git, and roadmap authority.
- Proved exact retry/restart behavior, including a planted crash between two
  rounds with no duplicate speaker, and preserved replacement/dissent lineage.
- Shipped source, vendored, and wheel exports while keeping install/update and
  ordinary/no-program usage free of policy, grants, stores, processes, or work.
