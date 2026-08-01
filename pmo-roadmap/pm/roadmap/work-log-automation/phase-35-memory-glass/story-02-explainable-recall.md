# WLA-35-02 - Explainable recall

- **Project:** work-log-automation
- **Phase:** 35
- **Status:** backlog
- **Depends on:** WLA-35-01
- **Unblocks:** WLA-35-03
- **Owner:** unassigned

## Problem

Agents start work with a grounding packet, but nothing ranks prior lessons, evidence digests, outcomes, and decisions for the story at hand. Recall must be deterministic, bounded, and explainable — every included item says why it matched; every excluded item says why it was dropped.

## Scope

- **In:** New pure module `pmo-roadmap/lib/dw_pmo/memory_recall.py` with `build_memory_recall(...)`; deterministic lexical/structural ranking; bounded budget with whole-item drops and typed exclusions.
- **Out:** Conductor wiring (WLA-35-03), UI (WLA-35-06). No embeddings, no model calls, no background indexer.

## Acceptance criteria

- [ ] `build_memory_recall(...)` is pure: it does not read Git, files, clocks, environment variables, randomness, or the network.
- [ ] Queries are built from acceptance criteria, grounded files and symbols, test names, failure signatures, story identifiers, and declared orchestration tags; ranking is deterministic and exposes `score`, `match_reasons`, and `source_kind`.
- [ ] Recall items support at least `grounding`, `repository-snippet`, `test-reference`, `evidence-digest`, `lesson`, `terminal-outcome`, and `decision` source kinds.
- [ ] Each item carries a stable source reference, confidence, delivery state, source revision, and short factual summary; the document records source heads for the repository index, earned-record chains, and referenced ledgers.
- [ ] The default budget is bounded and deterministic; whole items are dropped rather than truncated, and `exclusions[]` records byte-budget, stale-source, superseded, low-score, and audience-filter reasons.
- [ ] Existing knowledge-packet behavior remains byte-identical when the recall builder is not invoked.

## Test plan

- **Unit:** covered by the verification command below.
- **Integration:** `/usr/bin/python3 pmo-roadmap/tests/knowledge_packet_tests.py`
- **Manual / device:** n/a unless named in the acceptance criteria.

## Notes / open questions

Same inputs must produce byte-identical recall. Evidence digests reference the paired evidence file; they never replace it.
