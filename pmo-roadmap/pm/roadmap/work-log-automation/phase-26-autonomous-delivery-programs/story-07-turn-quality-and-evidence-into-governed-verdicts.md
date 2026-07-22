# WLA-26-07 — Turn quality and evidence into governed verdicts

- **Project:** work-log-automation
- **Phase:** 26
- **Status:** in-progress
  <!-- status vocabulary: roadmap-builder.md §2.3 -->
- **Depends on:** WLA-26-01, WLA-26-04, WLA-26-05
- **Unblocks:** WLA-26-08, WLA-26-09, WLA-26-10, WLA-26-12
- **Owner:** unassigned

## Problem

Tests alone cannot judge architecture, clarity, risk, or whether a story really
solved its problem; model confidence alone cannot prove a file exists or a
command passed. Autonomous delivery needs both hard evidence and governed
expert judgment, with the distinction visible. A verifier must return a typed,
rubric-bound verdict that can be audited, challenged, and combined without
being mistaken for a mechanical fact.

## Scope

- **In:** typed mechanical receipts; individual verifier, council, meta-verifier
  and architect verdict schemas; rubrics/criteria/severity; claim/evidence/
  citation lineage; pass/fail/needs-repair/abstain/escalate; quorum/veto/all/any/
  threshold composition; dissent; freshness and supersession; pure gate
  evaluation and proof packets; evidence materialization preview.
- **Out:** hidden model scores as truth; verifier-written tests/check commands;
  mutable rubrics after grant; marking a story done or integrating by itself;
  storing private reasoning or third-party content bodies.

## Acceptance criteria

- [ ] Mechanical predicates cover check receipts, artifact/schema/citation
  conformance, diff scope, roadmap/contract health, signal state, history, and
  exact verification commands; agent prose can never satisfy these types.
- [ ] Agent verdicts bind role/identity, rubric/version, exact work/evidence/
  repository/program/round facts, criterion-level outcomes, bounded rationale,
  citations, dissent/abstention and signature/hash; stale facts invalidate them.
- [ ] Policy can require one independent verifier, N-of-M quorum, unanimous
  council, veto roles, random or full meta-audit, and/or architect approval;
  composition is deterministic and explains every contributing/non-contributing
  verdict.
- [ ] Failed/needs-repair verdicts route only to declared bounded repair or
  escalation; a later verdict supersedes rather than erases history, and a
  verifier cannot change the implementation or its own rubric in place.
- [ ] Pure evaluation emits pass/fail/pending/refused proof packets with exact
  receipts/verdict lineage, freshness, unresolved dissent, remediation and
  evidence preview while writing/starting nothing.
- [ ] Red tests cover forged mechanical evidence, self-verification, rubric
  drift, missing citations, stale diff, colluding identity, quorum loss,
  conflicting verdicts, meta-overturn, architect veto and content leakage.

## Test plan

- **Unit:** verdict schema, composition, freshness, lineage and refusal tests.
- **Integration:** fixture implementer/verifier/council/meta-verifier produces a
  proof packet through one repair/supersession cycle; CLI/MCP/HTTP parity.
- **Manual / device:** verify UI labels mechanical facts and agent judgments
  differently and never hides dissent.

## Notes / open questions

A policy may legitimately authorize agent judgment to advance work. The honesty
requirement is provenance and explicit trust—not pretending that judgment was a
deterministic test.
