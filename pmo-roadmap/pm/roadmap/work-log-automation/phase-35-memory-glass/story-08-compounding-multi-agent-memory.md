# WLA-35-08 - Compounding multi-agent memory

- **Project:** work-log-automation
- **Phase:** 35
- **Status:** done
- **Depends on:** WLA-35-03, WLA-35-04, WLA-35-07
- **Unblocks:** WLA-35-09, WLA-35-10
- **Owner:** unassigned

## Problem

The thesis of this phase is that memory compounds: a later related run benefits from an earlier one, an unrelated run does not, and parallel agents cannot poison each other's context. This story proves it with packaged fixtures.

## Scope

- **In:** A packaged fixture: run A writes a confirmed lesson and terminal outcome; related run B recalls both; unrelated run C excludes them with an explainable low-score reason. Audience-specific slices for coordinator/implementer/verifier/council from one frozen source revision; serialized writeback.
- **Out:** New orchestration node types; UI work.

## Acceptance criteria

- [ ] The A/B/C packaged fixture exists and passes: B recalls A's lesson and outcome, C excludes them with an explainable low-score exclusion.
- [ ] Coordinator, implementer, verifier, and council participants receive audience-specific recall slices from one persisted source revision; their packets identify the common recall and their filter reason.
- [ ] Council decisions preserve proposal, critique, rebuttal, judgment, and dissent references; a later council can recall the prior conclusion and dissent without treating either as binding precedent.
- [ ] Agents cannot mutate shared long-term memory while sibling nodes are active; the conductor serializes accepted writeback after the safe terminal or certified-handoff boundary.
- [ ] Crash recovery produces zero duplicate dispatches, recall receipts, writebacks, lessons, or delivery observations.
- [ ] Failed and cancelled outcomes are recallable as warnings or failure patterns but never promoted to confirmed lessons without later evidence.

## Test plan

- **Unit:** covered by the verification command below.
- **Integration:** `/usr/bin/python3 pmo-roadmap/tests/autonomous-program-packaged-exam.py`
- **Manual / device:** n/a unless named in the acceptance criteria.

## Notes / open questions

Freeze before dispatch, serialize writeback at terminal boundaries — no mid-run shared-memory mutation.
