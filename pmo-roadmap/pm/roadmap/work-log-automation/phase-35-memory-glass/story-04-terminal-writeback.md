# WLA-35-04 - Terminal writeback

- **Project:** work-log-automation
- **Phase:** 35
- **Status:** done
- **Depends on:** WLA-35-01, WLA-35-03
- **Unblocks:** WLA-35-05, WLA-35-08
- **Owner:** unassigned

## Problem

Lessons today flow only from certified handoffs. Every terminal state — success or failure — carries information future runs need. Writeback must distill bounded facts at safe terminal boundaries, with unsuccessful outcomes recorded as candidate observations, never as confirmed solutions.

## Scope

- **In:** `dw_pmo.knowledge_writeback` extended so all terminal states produce bounded `delivery-workbench-memory-writeback@1` receipts; exactly-once writeback at terminal transitions with crash-replay dedup.
- **Out:** UI display (WLA-35-06), compounding proof (WLA-35-08).

## Acceptance criteria

- [ ] Successful, failed, cancelled, revoked, lost, timed-out, and exhausted runs all produce bounded writeback receipts.
- [ ] A writeback records terminal state, story IDs, subject hash, recalled memory IDs, decision references, evidence and check references, changed-file identifiers, failure signatures, accepted lesson hashes, and discarded lesson counts — never raw prompts, transcripts, tool output, credentials, or model thinking.
- [ ] Certified lessons continue through `persist_certified_handoff(...)` and `observe_lesson_integration(...)`; candidate observations from unsuccessful runs stay distinct and cannot become confirmed without a later provenance-bound observation.
- [ ] Program and bounded-run terminal transitions call the writeback adapter exactly once; replay after a crash deduplicates the exact receipt and lesson records.
- [ ] Supersession stays append-only: corrections append a new earned record retaining full ancestry; nothing rewrites or deletes an earned record.
- [ ] A writeback failure is visible in the run projection and needs-you surface but cannot retroactively change the run's verdict, certification, or terminal state.

## Test plan

- **Unit:** covered by the verification command below.
- **Integration:** `/usr/bin/python3 pmo-roadmap/tests/knowledge_writeback_tests.py`
- **Manual / device:** n/a unless named in the acceptance criteria.

## Notes / open questions

Writeback stores outcomes, not transcripts.
