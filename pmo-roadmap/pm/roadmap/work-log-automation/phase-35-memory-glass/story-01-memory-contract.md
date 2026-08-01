# WLA-35-01 - Memory contract

- **Project:** work-log-automation
- **Phase:** 35
- **Status:** backlog
- **Depends on:** none
- **Unblocks:** WLA-35-02, WLA-35-04
- **Owner:** unassigned

## Problem

The knowledge layer has packets, derived facts, and earned records, but no contract distinguishing long-term memory, per-run recall, decision basis, and terminal writeback. Without typed, capped, provenance-bound document kinds, memory surfaces built later would improvise shapes and risk acquiring authority they must never have.

## Scope

- **In:** New document kinds `delivery-workbench-memory-recall@1`, `delivery-workbench-memory-writeback@1`, `delivery-workbench-decision-basis@1` in `pmo-roadmap/lib/dw_pmo/knowledge.py` contract_document(); a terminal outcome record kind in EarnedRecordStore.
- **Out:** Recall ranking, conductor wiring, UI — later stories.

## Acceptance criteria

- [ ] `delivery-workbench-memory-recall@1`, `delivery-workbench-memory-writeback@1`, and `delivery-workbench-decision-basis@1` are added to the machine-readable contract returned by `dw_pmo.knowledge.contract_document()`.
- [ ] Every document has a closed field set, deterministic identity, byte and item caps, provenance references, and the four required false-authority fields `starts_work`, `authorizes`, `satisfies_gate`, `substitutes_for_evidence`, all fixed to `false`.
- [ ] `EarnedRecordStore` gains a terminal outcome record kind without weakening sequence, timestamp, hash-chain, exact-field, and field-cap validation.
- [ ] Memory records distinguish `confirmed`, `candidate`, and `superseded`; a failed, cancelled, lost, or timed-out run cannot produce a confirmed lesson merely because an agent claimed one.
- [ ] The knowledge-layer import guard still proves that gates, grants, verdicts, contracts, and certification do not read memory.

## Test plan

- **Unit:** covered by the verification command below.
- **Integration:** `/usr/bin/python3 pmo-roadmap/tests/repository_knowledge_tests.py`
- **Manual / device:** n/a unless named in the acceptance criteria.

## Notes / open questions

Build on DerivedFactStore, EarnedRecordStore, and `delivery-workbench-knowledge-packet@1` — one knowledge system, not a parallel memory database. Document shapes are recorded in this phase's current-phase-status.md decisions.
