# Phase 29 - Serving ourselves

**Last updated:** 2026-07-26.

## Goal

Delivery Workbench's program engine learns the repository it works in and
delivers real work in this repository. A deterministic repository-knowledge
layer cuts the localization tax every dispatched agent pays, stories are
grounded against verified symbols before work starts, verdicts judge only the
failures a change introduced, authors and reviewers stop sharing one model's
blind spots, every delivery writes its lessons back — and the phase closes
only when a real autonomous program, not a fixture, has delivered a story in
this repository end to end.

## Why now (comparative study, 2026-07-26)

A study of `krishagarwal314/autodev-studio` (a three-day-old but thoughtful
autonomous-SDLC prototype) found that its list of missing maturity-tier
capabilities — durable orchestration, typed verdicts, immutable provenance,
checkpoints, streaming, notifications — is what phases 24-27 already built.
What it has and we lack is the layer that makes agents cheap and grounded:

- **Persistent repository knowledge.** Its core thesis is reducing the
  "localization tax": build repository knowledge once (structure, symbol
  maps, features), retrieve targeted context per task, and write delivery
  lessons back so each delivery makes the next cheaper. Our agent packets
  carry no repository intelligence at all; every dispatched agent rediscovers
  the codebase from zero.
- **Deterministic grounding after generative planning.** Its PM's guessed
  symbols and files are verified against a static symbol map and `git grep`
  before any dev agent sees them. Our stories carry no verified localization.
- **Baseline failure subtraction.** It runs tests before and after a change
  and judges only newly introduced failures — the pattern that makes
  evidence-gated delivery workable on imperfect repositories.
- **Cross-provider review.** Author and reviewer deliberately use different
  model families to decorrelate blind spots. Our organization layer models
  separation of duties but cannot yet express provider diversity.
- **Honest unknown telemetry.** Usage a backend does not report stays
  unknown, never zero.

Its fatal flaw is the inverse of ours: its gates do not gate (quality
failures still open the PR), while our gates have never been exercised —
`.git` in this repository shows **zero program runs ever** and exactly one
bounded run, revoked at its first checkpoint. This phase fixes both sides:
adopt the grounding layer, and prove the engine on ourselves.

## Scope

- **In:** one versioned contract for repository knowledge and its two storage
  classes; a deterministic stdlib-only symbol and structure map with
  index-tree-keyed freshness; story localization hints and mechanical
  grounding; bounded knowledge packets served into the existing agent-packet
  seam; baseline-failure capture and introduced-failure verdict semantics;
  a provider-diversity rule in the organization layer; delivery write-back
  of lessons as bounded, provenance-stamped records; one real checkpointed
  program run in this repository delivering a real story.
- **Out:** any LLM call, embedding model, or network activity inside the
  knowledge core; changing gate, grant, ledger, certification, or refusal
  semantics; a conversational intake surface (a later phase); cross-repository
  knowledge; hosted or shared knowledge sync; a release or version bump;
  weakening any verdict so a program "passes" — introduced failures block,
  full stop.

## Hard constraint

Knowledge may inform; it may never authorize. No knowledge fact, packet,
lesson, or grounding verdict mints authority, satisfies a gate rule, or
substitutes for evidence. The knowledge core is deterministic, stdlib-only,
and offline; deleting every derived knowledge file changes no authoritative
answer. And unlike the studied prototype, quality failure blocks delivery:
an introduced test failure or an unsatisfied review rule can never advance
work by exhausting a budget — it stops at a checkpoint or refusal.

## Exit criteria (evidence required)

- [ ] One documented, versioned contract owns repository knowledge, splits it
  into derived facts (disposable, re-derivable) and earned records
  (append-only, provenance-stamped), and a fitness test keeps LLM, network,
  and nondeterminism out of the knowledge core (WLA-29-01).
- [ ] A deterministic symbol and structure map covers this repository, keyed
  to the repofacts index tree, refreshed incrementally, and served read-only
  across CLI and MCP (WLA-29-02).
- [ ] Stories can carry advisory localization hints, and a mechanical
  grounding pass verifies every hint against the symbol map and `git grep`,
  classifying each as verified, new, or unknown-with-suggestions
  (WLA-29-03).
- [ ] Program and run agent packets carry a bounded, hash-bound knowledge
  packet — verified locations, snippets, related tests, relevant lessons —
  and driver usage telemetry reports unknown as unknown, never zero
  (WLA-29-04).
- [ ] Baseline test failures are captured as a ledgered fact before dispatch,
  verdicts distinguish introduced from pre-existing failures, introduced
  failures block, and pre-existing failures become typed obligations
  (WLA-29-05).
- [ ] The organization layer can require and enforce provider-family
  diversity between implementer and independent reviewer roles, refusing
  unsatisfiable assignments (WLA-29-06).
- [ ] Completed deliveries append bounded, provenance-stamped delivery
  records and lessons to the earned-knowledge store, and later knowledge
  packets retrieve them (WLA-29-07).
- [ ] A real checkpointed autonomous program — live adapters, not fixtures —
  delivers at least one real story in this repository end to end, through
  knowledge packets, baseline subtraction, and the diversity rule, ending at
  the human certification seam; friction is recorded as stories or
  obligations (WLA-29-08).

## Story status

| ID | Story | Status | Story file | Evidence |
|---|---|---|---|---|
| WLA-29-01 | Contract repository knowledge | ready | [story-01-contract-repository-knowledge](./story-01-contract-repository-knowledge.md) | — |
| WLA-29-02 | Build the symbol and structure map | backlog | [story-02-build-the-symbol-and-structure-map](./story-02-build-the-symbol-and-structure-map.md) | — |
| WLA-29-03 | Ground the work before it starts | backlog | [story-03-ground-the-work-before-it-starts](./story-03-ground-the-work-before-it-starts.md) | — |
| WLA-29-04 | Serve knowledge packets to agents | backlog | [story-04-serve-knowledge-packets-to-agents](./story-04-serve-knowledge-packets-to-agents.md) | — |
| WLA-29-05 | Judge only the failures we introduced | backlog | [story-05-judge-only-the-failures-we-introduced](./story-05-judge-only-the-failures-we-introduced.md) | — |
| WLA-29-06 | Decorrelate the author and the reviewer | backlog | [story-06-decorrelate-the-author-and-the-reviewer](./story-06-decorrelate-the-author-and-the-reviewer.md) | — |
| WLA-29-07 | Write the delivery back | backlog | [story-07-write-the-delivery-back](./story-07-write-the-delivery-back.md) | — |
| WLA-29-08 | Serve ourselves for real | backlog | [story-08-serve-ourselves-for-real](./story-08-serve-ourselves-for-real.md) | — |

## Where we are

Phase scaffolded 2026-07-26 from the autodev-studio comparative study and the
operational audit that found the program engine architecturally complete,
fixture-proven, and never once run for real. WLA-29-01 is ready: the contract
lands before any extraction, retrieval, or caching exists, in the pattern
phase 28 proved (the rule ships before anything reuses a fact).

## Active risks

| Risk | Likelihood | Mitigation | Stop signal |
|---|---|---|---|
| Knowledge quietly becomes authority — a packet, lesson, or grounding verdict is treated as consent or evidence | medium | The contract states the exclusion; fitness tests assert no knowledge module imports authority surfaces and no gate/grant path reads knowledge stores | Any gate, grant, or verdict test needs a knowledge fixture to pass |
| The symbol map goes stale and grounds stories against a repository that no longer exists | medium | Freshness is keyed to the repofacts index tree from phase 28; a stale map refuses to ground rather than answering | A grounding answer is served from a map whose index tree differs from the current derivation |
| Baseline subtraction is used to excuse regressions | low | Only failures present in the pre-dispatch baseline are subtractable; the baseline is a ledgered fact, not an agent claim; introduced failures block unconditionally | Any path where a post-change failure advances work without appearing in the baseline fact |
| The real program run (WLA-29-08) stalls on live-adapter friction and the phase closes on fixtures instead | medium | The story's acceptance criteria name live adapters explicitly; friction becomes recorded stories or obligations, not silent scope cuts | Anyone proposes closing WLA-29-08 with a fixture adapter in the evidence |
| Lesson write-back becomes an unbounded prose channel | low | Earned records have bounded, typed fields with per-field length caps and run-id provenance, in the signals content-boundary style | A lesson field accepts free-form content with no cap or provenance |

## Decisions made (this phase)

- 2026-07-26 - Phase scaffolded from the autodev-studio comparative study and
  the zero-real-runs operational finding - the features adopted are the ones
  the study named as genuinely missing, and the proof story is real, not
  fixture - owner direction: delivery-workbench must be capable of serving
  ourselves.
- 2026-07-26 - Knowledge informs, never authorizes - recorded as the hard
  constraint before any knowledge code exists - matches the configuration-is-
  not-authority spine.
- 2026-07-26 - The knowledge core is deterministic and stdlib-only; LLM
  interpretation of the repository, where wanted, is agent output routed
  through typed write-back, never core behavior - keeps the no-LLM floor the
  project has held since Phase 0.
- 2026-07-26 - Introduced failures block, unconditionally - the studied
  prototype's proceed-on-exhausted-budget behavior is explicitly rejected -
  owner direction.

## Decisions deferred

- Conversational intake (a Scope-Chat-shaped front door that drafts phases and
  stories through the guarded mutation surface) - trigger: after WLA-29-08
  proves the engine on real work - default is not in this phase.
- Whether earned knowledge (lessons, delivery records) should be tracked in
  the repository rather than `.git`-local so it travels with clones - trigger:
  first time a second machine or contributor needs the lessons - default is
  `.git`-local like signals.
- Embedding-based retrieval beyond deterministic lexical scoring - trigger:
  measured retrieval misses on real program runs - default is no; it would
  break the stdlib-only, offline floor.
- Cross-repository knowledge and portfolio scheduling - unchanged from the
  Phase 26 deferral - trigger remains one repository crossing multiple phases
  autonomously.
