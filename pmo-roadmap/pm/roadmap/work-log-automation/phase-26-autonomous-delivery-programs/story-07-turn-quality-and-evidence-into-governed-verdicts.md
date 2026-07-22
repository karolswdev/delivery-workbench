# WLA-26-07 — Turn quality and evidence into governed verdicts

- **Project:** work-log-automation
- **Phase:** 26
- **Status:** done
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

- **In:** typed mechanical receipts; individual verifier, independent-panel,
  deliberative-council, meta-verifier and architect verdict/decision schemas;
  rubrics/criteria/severity; claim/evidence/citation lineage; exact resolved
  harness/provider/model/auth-domain provenance; pass/fail/needs-repair/
  abstain/escalate; quorum/veto/all/any/threshold composition; dissent;
  council obligations and accepted debt; freshness and supersession; pure gate
  evaluation and proof packets; evidence materialization preview.
- **Out:** hidden model scores as truth; verifier-written tests/check commands;
  mutable rubrics after grant; marking a story done or integrating by itself;
  storing private reasoning or third-party content bodies.

## Acceptance criteria

- [x] Mechanical predicates cover check receipts, artifact/schema/citation
  conformance, diff scope, roadmap/contract health, signal state, history, and
  exact verification commands; agent prose can never satisfy these types.
- [x] Agent verdicts bind role/identity, rubric/version, exact work/evidence/
  repository/program/round facts, criterion-level outcomes, bounded rationale,
  citations, dissent/abstention, resolved adapter/harness/provider/router/model/
  auth-domain fingerprints and signature/hash; any changed binding or stale
  fact invalidates them.
- [x] Policy distinguishes a non-deliberating review panel from a council:
  panels deterministically compose independent verdicts, while council verdicts
  require completed bounded discussion/decision lineage and cannot be
  counterfeited by votes alone.
- [x] Policy can require one independent verifier, N-of-M panel quorum,
  unanimous council, veto roles, random or full meta-audit, and/or architect
  approval; composition is deterministic and explains every contributing/
  non-contributing verdict, participant and execution binding.
- [x] Every council decision carries rationale, citations, alternatives,
  accepted risks, dissent and an explicit bounded obligations list covering
  backlog/technical-debt/risk/research/follow-up with blocking, ownership,
  target/trigger and acceptance metadata; the decision itself starts/writes
  nothing and obligations cannot be silently dropped.
- [x] Decision provenance says whether the outcome was computed by a rule,
  selected by one preassigned `decider_seat`, or routed to an external
  checkpoint; judge identity binds its stable seat address, assignment
  generation and complete execution provenance, and the judge cannot choose an
  outcome outside the mechanically allowed set.
- [x] Failed/needs-repair verdicts route only to declared bounded repair or
  escalation; a later verdict supersedes rather than erases history, and a
  verifier cannot change the implementation or its own rubric in place.
- [x] Pure evaluation emits pass/fail/pending/refused proof packets with exact
  receipts/verdict lineage, freshness, unresolved dissent, remediation and
  evidence preview while writing/starting nothing.
- [x] Red tests cover forged mechanical evidence, self-verification, rubric
  drift, missing citations, stale diff, colluding identity, quorum loss,
  panel/council confusion, conflicting verdicts, meta-overturn, architect veto,
  changed provider/model resolution, omitted obligations and content leakage.

## Test plan

- **Unit:** fact, verdict, panel, council-decision, obligation, composition,
  execution-provenance, freshness, lineage and refusal tests.
- **Integration:** fixture implementer/verifier/panel/deliberative-council/
  meta-verifier produces a proof packet through one repair/supersession cycle;
  source, vendored runtime, and fresh-wheel exports remain equivalent.
- **Surface boundary:** live CLI/MCP/HTTP/Workbench program-state parity and the
  device-level rendering of facts, judgments, dissent, deciders, and
  obligations are WLA-26-11 acceptance, not a second quality evaluator here.

## Notes / open questions

A policy may legitimately authorize agent judgment to advance work. The honesty
requirement is provenance and explicit trust—not pretending that judgment was a
deterministic test.
