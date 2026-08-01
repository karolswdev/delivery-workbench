# WLA-35-05 - Memory read surfaces

- **Project:** work-log-automation
- **Phase:** 35
- **Status:** done
- **Depends on:** WLA-35-03, WLA-35-04
- **Unblocks:** WLA-35-06, WLA-35-07
- **Owner:** unassigned

## Problem

Recall and writeback live in ledgers and earned stores no operator should have to replay by hand. One byte-consistent read model must serve CLI, MCP, and HTTP so both humans and agents can inspect what a run recalled, what it wrote back, and where every item came from.

## Scope

- **In:** `dw knowledge recall --run/--program`, `dw knowledge writebacks` with filters; MCP tools `dw_knowledge_recall` and `dw_knowledge_writebacks`; read-only HTTP endpoints `GET /api/runs/{run_id}/memory`, `GET /api/programs/{program}/memory`, `GET /api/memory/records/{record_hash}`.
- **Out:** Any mutation form; UI rendering (WLA-35-06/07).

## Acceptance criteria

- [ ] `dw knowledge recall --run <run-id>` and `--program <program-run-id>` work, plus `dw knowledge writebacks` with run, program, story, and state filters.
- [ ] MCP tools `dw_knowledge_recall` and `dw_knowledge_writebacks` exist; their success and refusal payloads are byte-identical to the CLI projections.
- [ ] The three read-only HTTP endpoints exist and group `recalled`, `used-as-basis`, `written-back`, `superseded`, and `excluded` entries while preserving record hashes and ledger coordinates.
- [ ] Missing, stale, malformed, and tampered sources return typed refusals; no endpoint silently omits a broken source and presents a partial history as complete.
- [ ] The endpoints remain localhost-only, have no mutation form, and never trigger recomputation, refresh, dispatch, or writeback as a side effect of reading.
- [ ] The interop parity inventories (dw-core-tests POST-route guards and docs/interop.md) are updated deliberately for any route additions.

## Test plan

- **Unit:** covered by the verification command below.
- **Integration:** `/bin/sh -c 'bash pmo-roadmap/tests/mcp-server.sh && bash pmo-roadmap/tests/workbench-explorer.sh'`
- **Manual / device:** n/a unless named in the acceptance criteria.

## Notes / open questions

Corrections and supersession continue through guarded append-only operations — no unguarded edit-memory endpoint.
