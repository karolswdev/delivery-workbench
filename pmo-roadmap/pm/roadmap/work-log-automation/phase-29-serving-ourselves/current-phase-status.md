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
| WLA-29-01 | Contract repository knowledge | done | [story-01-contract-repository-knowledge](./story-01-contract-repository-knowledge.md) | [evidence-story-01](./evidence-story-01.md) |
| WLA-29-02 | Build the symbol and structure map | done | [story-02-build-the-symbol-and-structure-map](./story-02-build-the-symbol-and-structure-map.md) | [evidence-story-02](./evidence-story-02.md) |
| WLA-29-03 | Ground the work before it starts | done | [story-03-ground-the-work-before-it-starts](./story-03-ground-the-work-before-it-starts.md) | [evidence-story-03](./evidence-story-03.md) |
| WLA-29-04 | Serve knowledge packets to agents | done | [story-04-serve-knowledge-packets-to-agents](./story-04-serve-knowledge-packets-to-agents.md) | [evidence-story-04](./evidence-story-04.md) |
| WLA-29-05 | Judge only the failures we introduced | done | [story-05-judge-only-the-failures-we-introduced](./story-05-judge-only-the-failures-we-introduced.md) | [evidence-story-05](./evidence-story-05.md) |
| WLA-29-06 | Decorrelate the author and the reviewer | done | [story-06-decorrelate-the-author-and-the-reviewer](./story-06-decorrelate-the-author-and-the-reviewer.md) | [evidence-story-06](./evidence-story-06.md) |
| WLA-29-07 | Write the delivery back | backlog | [story-07-write-the-delivery-back](./story-07-write-the-delivery-back.md) | — |
| WLA-29-08 | Serve ourselves for real | backlog | [story-08-serve-ourselves-for-real](./story-08-serve-ourselves-for-real.md) | — |

## Where we are

Phase scaffolded 2026-07-26 from the autodev-studio comparative study and the
operational audit that found the program engine architecturally complete,
fixture-proven, and never once run for real. WLA-29-01 is ready: the contract
lands before any extraction, retrieval, or caching exists, in the pattern
phase 28 proved (the rule ships before anything reuses a fact).

WLA-29-01 shipped the contract:
`delivery-workbench-repository-knowledge@1` in `dw_pmo/knowledge.py`, with
`docs/repository-knowledge.md` as its prose register. The split is structural:
derived facts live under `.git/pmo-knowledge/derived/`, carry the repofacts
index tree they were computed from, and refuse on any other current tree
(`StaleDerivedFact`), with an explicit recompute path; earned records
(`delivery-record`, `lesson`) live under `.git/pmo-knowledge/earned/` as
hash-chained append-only JSONL with closed scalar-only field sets, per-field
caps, and mandatory provenance (origin, UTC timestamp, head SHA), validated on
append and re-validated on read. Every stored document stamps an explicit
false authority marker. The fitness guards hold both directions: gate,
contract, grant, and verdict paths cannot read knowledge stores (a planted
read is rejected), and the knowledge core imports nothing networked,
non-stdlib, or spawning, with no clock or randomness in derived-fact
computation. Nothing calls the module yet — 17 new tests, the core suite grew
to 547, all green, vendored copy byte-identical.

WLA-29-02 built the map on that contract. `symbol_map.py` extracts symbols
(module/class/function/method with qualified names and line spans), the
module inventory, and a static test-to-symbol map with a documented
resolution rule, all through stdlib `ast`; `repository_map.py` stores the
result as a derived fact through `DerivedFactStore`. Two repository facts
were added to the repofacts contract with their classification recorded
(`tracked_files`, `blob_content`, both derivation-scoped), which is how
extraction enumerates blobs without private git access. Over this repository:
147 Python files, 4,388 symbols, and 624 named gaps — every non-Python file
says "out of structural coverage; use git grep" rather than disappearing.
Incremental refresh re-parses only changed blobs (proven one-file-edit →
one parse), extraction is byte-deterministic, stale reads refuse, and
`dw knowledge map` / `dw knowledge refresh` / MCP `dw_knowledge_map` return
one canonical model with parity tested. Core suite 547 → 559, all green.

WLA-29-03 made grounding mechanical. Stories may carry an optional advisory
`## Localization hints` section (template updated); `dw_pmo/grounding.py`
classifies every hint as verified (file + line span from the map), new, or
unknown, with the rule stated and enforced: `(new)` is the only way to claim
newness and is accepted only with complete no-match evidence from both the
map and a bounded fallback scan over sanctioned tracked-blob facts — an
unmarked absence, a fallback text match, or an incomplete scan stays
unknown, and the declaring story is excluded so a hint cannot satisfy
itself. Surfaces: `dw knowledge ground`, MCP `dw_knowledge_ground`,
advisory warnings in `dw check` (exit codes untouched), and grounding
results inside program plans only for stories that carry hints (hint-free
plans byte-identical). Stale maps refuse rather than answer. The manual
check grounded WLA-29-04's real hints: 5 verified with locations, the
`(new)` file accepted via exact tracked-path absence, and the `(new)`
symbol honestly kept unknown pending complete no-match evidence. Core
suite 559 → 571, all green.

Deliberate resequencing, 2026-07-26: WLA-29-06 lands next, before
WLA-29-04/05. It has no dependencies, its implementation is complete and
exam-proven in an isolated worktree, and it touches the same driver and
program modules WLA-29-04 must edit — landing it first avoids a pointless
conflict pass. Recorded here as an owner-direction scheduling decision.

WLA-29-06 landed on that schedule. Provider family is now a declared
adapter attribute (`fixture`, `openai`, `anthropic`, `pi`; fixtures can
declare alternate families for tests), and organizations may declare named
`diversity` rules of kind `provider-family` between exactly two roles.
Enforcement runs at initial assignment, candidate search, replacement, and
plan/start diagnostics; an unsatisfiable roster refuses before start with
`provider-diversity-unsatisfied` naming the rule and the missing family,
and an undeclared family fails closed. Organizations without the field are
untouched — diversity is not default-on, and the exemplar organization
deliberately stays without it. Assignment receipts record the
role-to-family pairing; the team and live-review surfaces say "reviewed by
a different model family" in product language with snapshots re-pinned.
The packaged autonomous exam gained both legs (satisfying assignment and
refused variant) and runs complete against the merged tree. Core suite
571 → 573 green; product-language contract ok.

WLA-29-04 gave dispatched agents the repository. `knowledge_packet.py`
builds a pure, deterministic, stdlib-only packet from a story's verified
grounding: whole-symbol snippets at verified locations, mapped tests, and
relevant earned lessons, under a declared byte budget (default 32,768 —
to be validated by the real run in WLA-29-08) with deterministic lexical
scoring, stable tie-breaking, and whole-item degradation that names every
exclusion with its score. Hint-free and ungrounded stories yield packets
that say so; unverified hints appear only labeled unverified; stale maps
or grounding refuse through the existing packet-assembly failure path
(`StaleKnowledgePacket`), never as an empty packet. The section rides both
bounded-run and program packets hash-bound, with legacy replay
compatibility proven. The honest-telemetry pass landed with it: usage a
backend does not report stays unknown through receipts, ledgers, live
progress, bounded actions, and workbench projections, while an explicitly
reported zero stays numeric zero. Core suite 573 → 581, all green.

WLA-29-05 made verdicts judge only what a change introduced. Before first
dispatch the declared test command runs in a persistent, head-bound
baseline worktree and the failing set is recorded as a bounded, immutable
ledger fact (identifiers and counts, head-SHA provenance, never output
prose) that no agent-facing surface can write or amend. Post-change
failures classify as introduced — routed straight to
`route-block-introduced-test-failure`, bypassing retry, repair, loop,
exhaustion, and escalation — or pre-existing, which emit strictly
validated non-blocking `technical-debt` obligations, batched into one
ledger event with one replay and deduplicated per run. Missing, foreign-
head, stale-command, truncated, or unparseable baselines fail closed: all
failures judged introduced. One shared failure projection renders both
sets across gate proof, live progress, and team review, so "green with
pre-existing debt" is never reported as plain green. Programs without a
declared command keep today's whole-result semantics, recorded honestly
as subtraction-unavailable. The diff absorbed a three-lens review
(altitude, simplification, efficiency) plus a matching peer-session
review before landing; two structural suggestions were declined on
architecture (baseline capture stays tick-driven for crash-recovery
replay; event-schema centralization deferred as follow-up). Core suite
581 → 589, all green; packaged exam complete.

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
