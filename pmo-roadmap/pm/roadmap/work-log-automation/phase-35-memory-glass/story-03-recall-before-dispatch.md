# WLA-35-03 - Recall before dispatch

- **Project:** work-log-automation
- **Phase:** 35
- **Status:** done
- **Depends on:** WLA-35-02
- **Unblocks:** WLA-35-04, WLA-35-05, WLA-35-07, WLA-35-08
- **Owner:** unassigned

## Problem

Recall is worthless if runs can start without it. Both bounded orchestration and autonomous programs must persist a recall receipt before the first actionable dispatch, and every agent work packet must carry an audience-specific view of that frozen recall.

## Scope

- **In:** `dw_pmo.orchestration_conductor` and `dw_pmo.program_conductor` build and persist recall before first agent claim; `memory-recall-built` / `memory-recall-attached` ledger events; recall document attached to work packets alongside the knowledge packet.
- **Out:** Writeback (WLA-35-04), read surfaces (WLA-35-05).

## Acceptance criteria

- [ ] Both conductors build and persist recall before the first agent claim can dispatch.
- [ ] `memory-recall-built` and `memory-recall-attached` events land in the existing hash-chained ledgers, identifying recall ID, source revision, audience, byte count, included item count, and exclusion count.
- [ ] The recall document rides alongside `delivery-workbench-knowledge-packet@1` in the work packet without replacing or reinterpreting it.
- [ ] A missing, malformed, tampered, or stale recall blocks agent dispatch with a typed action-needed state — never a silent empty context; a genuinely hint-free run receives an explicit valid empty recall.
- [ ] Restart and claim recovery reuse the same persisted recall identifier — no different rebuilt packet, no duplicate agent start.
- [ ] Ordinary non-program roadmap commands and repository opening still create no knowledge state, processes, observers, notifications, or network activity.

## Test plan

- **Unit:** covered by the verification command below.
- **Integration:** `/bin/sh -c '/usr/bin/python3 pmo-roadmap/tests/orchestration-packaged-exam.py && /usr/bin/python3 pmo-roadmap/tests/autonomous-program-packaged-exam.py'`
- **Manual / device:** n/a unless named in the acceptance criteria.

## Notes / open questions

Recall is frozen at dispatch: sibling agents share one persisted source revision with audience slices; check and rail nodes get only the run-level reference.
