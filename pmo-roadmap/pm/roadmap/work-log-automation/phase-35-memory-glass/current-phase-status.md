# Phase 35 - Memory glass

**Last updated:** 2026-08-01.

## Goal

Make memory a visible, testable part of every bounded run and autonomous program: bounded recall assembled before agents act, transparent decision basis while work is live, distilled provenance-bound writeback when it ends — compounding intelligence across runs while memory stays advisory, local, and dependency-free.

## Scope

- **In:** Three new memory document kinds in the repository-knowledge contract; a pure deterministic recall builder; recall-before-dispatch wiring in both conductors; terminal writeback for every terminal state; one byte-consistent read model over CLI/MCP/HTTP; an AgentGlass-style Memory pane and decision-basis timeline in the workbench; a compounding multi-agent packaged proof; a whole-workbench UX polish pass; the exit exam.
- **Out:** Embeddings, vector stores, model calls, or background indexers in recall; any exposure of private model reasoning; external services, frameworks, or build tools (the runtime stays stdlib Python + vanilla web, `dependencies = []`); any mutation form on memory read endpoints; a second source of truth beside Markdown roadmaps, evidence, Git state, ledgers, and earned records.

## Exit criteria (evidence required)

- [ ] Every run and program persists a recall receipt before the first agent dispatch, and a missing/stale/tampered recall blocks dispatch with a typed refusal (packaged exams).
- [ ] Every terminal state produces an exactly-once, bounded, provenance-bound writeback receipt, with crash-replay dedup (writeback tests + packaged exams).
- [ ] The two-run compounding scenario passes: a related run recalls a prior run's lesson and outcome; an unrelated run excludes them explainably (packaged fixture).
- [ ] Operators can see what an agent recalled, which facts underlay each decision, and what was written back — in the browser, over CLI, and over MCP, byte-consistently (browser exam + parity tests).
- [ ] Memory holds no authority: permission tests prove no memory document can start work, widen a grant, satisfy evidence or certification, or alter a verdict.
- [ ] Full core suite green with no regression from the 698-test Phase 34 baseline; ordinary non-program use stays side-effect free (no-program regression exam).

## Story status

| ID | Story | Status | Story file | Evidence |
|---|---|---|---|---|
| WLA-35-01 | Memory contract | done | [story-01-memory-contract](./story-01-memory-contract.md) | [evidence-story-01](./evidence-story-01.md) |
| WLA-35-02 | Explainable recall | backlog | [story-02-explainable-recall](./story-02-explainable-recall.md) | - |
| WLA-35-03 | Recall before dispatch | backlog | [story-03-recall-before-dispatch](./story-03-recall-before-dispatch.md) | - |
| WLA-35-04 | Terminal writeback | backlog | [story-04-terminal-writeback](./story-04-terminal-writeback.md) | - |
| WLA-35-05 | Memory read surfaces | backlog | [story-05-memory-read-surfaces](./story-05-memory-read-surfaces.md) | - |
| WLA-35-06 | AgentGlass memory pane | backlog | [story-06-agentglass-memory-pane](./story-06-agentglass-memory-pane.md) | - |
| WLA-35-07 | Decision basis timeline | backlog | [story-07-decision-basis-timeline](./story-07-decision-basis-timeline.md) | - |
| WLA-35-08 | Compounding multi-agent memory | backlog | [story-08-compounding-multi-agent-memory](./story-08-compounding-multi-agent-memory.md) | - |
| WLA-35-09 | Slick workbench | backlog | [story-09-slick-workbench](./story-09-slick-workbench.md) | - |
| WLA-35-10 | Prove it works | backlog | [story-10-prove-it-works](./story-10-prove-it-works.md) | - |

## Where we are

WLA-35-01 done (2026-08-01): the memory contract exists — three document kinds in `contract_document()` with false-authority fields, a `terminal-outcome` earned record kind with confirmed/candidate/superseded states, and an extended authority import guard. Knowledge suites 22 → 28 tests. Next: WLA-35-02 (the pure recall builder).

## Active risks

| Risk | Likelihood | Mitigation | Stop signal |
|---|---|---|---|
| Memory quietly acquires authority | medium | False-authority fields on every document; extend the authority import-guard tests first (WLA-35-01) | A gate, grant, verdict, or certification path imports a memory module |
| Recall becomes nondeterministic or unbounded | medium | Pure builder, lexical/structural signals only, byte budgets with typed exclusions | Same inputs produce different recall bytes |
| Parallel agents poison shared memory | medium | Freeze recall at dispatch; serialize writeback at terminal boundaries | A sibling agent's context changes while both are active |
| UI work drifts into a framework rewrite | low | Phase-33 design system and vanilla architecture are the contract | A build step, dependency, or Shadow DOM appears |
| Exam weakened to pass | low | Baseline pinned at 698 core tests; no skipped tests, no relaxed refusals | Test count drops or a refusal assertion loosens |

## Decisions made (this phase)

- 2026-08-01 - Phase designed by Sol (GPT-5.6) from three-source grounding (phase 33/34 final summaries, knowledge/orchestration modules, workbench UI code); executed story-by-story under orchestration - keeps design and execution accountable to the rails - operator.
- 2026-08-01 - One knowledge system, not a parallel memory database: memory lives under the existing repository-knowledge boundary (derived facts, earned records, run/program ledgers); `memory_recall.py` is a projector, not a store - avoids a second source of truth - design.
- 2026-08-01 - Three document kinds carry the phase: `delivery-workbench-memory-recall@1` (frozen pre-dispatch context with items, scores, match reasons, exclusions, source revision), `delivery-workbench-memory-writeback@1` (terminal outcome receipt; outcomes, never transcripts), `delivery-workbench-decision-basis@1` (structured decision audit; facts and rules, never chain of thought). All carry `starts_work`/`authorizes`/`satisfies_gate`/`substitutes_for_evidence` fixed `false` - design.
- 2026-08-01 - Deterministic relevance, no embeddings: exact story/phase/file/symbol/test/failure-signature matches, criteria term overlap, grounded-location overlap, supersession and delivery-state preference, bounded confidence/recency tie-breakers, stable-hash final tie-breaker - same inputs must produce byte-identical recall - design.
- 2026-08-01 - Recall is frozen before dispatch; audience slices (coordinator/implementer/verifier/judge/shared) come from one persisted source revision; writeback serializes at terminal or certified-handoff boundaries - prevents races and memory poisoning - design.
- 2026-08-01 - The memory web API is read-only (`GET /api/runs/{run_id}/memory`, `GET /api/programs/{program}/memory`, `GET /api/memory/records/{record_hash}`); corrections stay guarded and append-only - design.
- 2026-08-01 - Canonical implementation in `pmo-roadmap/lib/dw_pmo/` and `pmo-roadmap/workbench/`; `.githooks/` copies are installed rider payloads kept byte-synced - matches the repo's self-hosting rule - design.

## Decisions deferred

- Whether any memory surface ships in a release - trigger is Karol opening a landing phase - default is unreleased on main.
- Cross-repository memory (recall from other clones' earned records) - trigger is a real second-repo use case - default is single-repository scope.
