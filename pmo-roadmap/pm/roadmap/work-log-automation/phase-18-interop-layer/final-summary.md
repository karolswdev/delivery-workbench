# Phase 18 Final Summary

**Status:** complete.
**Date:** 2026-07-11.

## Outcome vs exit criteria

Four for four, all evidenced, same day as the board itself. Phase 17
made the picture; this phase made every element on it a door:

1. **Self-describing cards** (WLA-18-01) — every board card, lane,
   parked story, and paused phase carries `paths` (repo-relative
   story/evidence/phase-status receipts; the evidence address is
   stable before the file exists, `evidence_exists` tells the
   occupancy truth) and `links` (workbench story/trace routes). One
   helper mints every link shape; the board model is stamped
   `delivery-workbench-board` v1; a no-rot test resolves every
   emitted link through `handle_api` and demands 200. Proven live:
   a consumer holding only board JSON walked card → story +
   evidence → trace over HTTP with zero tree knowledge.
2. **One story, whole** (WLA-18-02) — `api.story_detail` is the one
   core (header context, normalized status + why, bodies, parsed
   captured runs, paths/links, honest absences); the workbench
   story route refactored onto it additively; `dw story show
   [--json]` browses it with every `find_story` selector form.
3. **The MCP read surface** (WLA-18-03) — `dw_board`, `dw_holds`,
   `dw_story_show`: thin adapters over the same cores, byte-equal
   structuredContent, the CLI's exact refusals, a read-only census
   (no browse handler may reach plan_/apply). The shared
   `parked_lines` renderer keeps CLI and MCP text from drifting.
4. **The contract** (WLA-18-04) — `docs/interop.md` names the whole
   read surface: five stamped models, eleven CLI machine verbs,
   thirteen workbench GET routes, twelve MCP tools, the versioning
   stance, and the read-only guarantee with write paths referenced
   elsewhere. The pin derives inventories from `handle_api` source
   and the MCP registry and proves it bites with a planted
   omission — no surface ships undocumented again.

Core tests 199 → 208; mcp-server, docs lints, snippet smoke,
gate-parity, package-smoke all green throughout.

## What shipped

`board.py` (link/path minting + the stamp), `api.py`
(`story_detail`, `parked_lines`, receipts on `parked_summary`),
`workbench.py` (story route on the shared core), CLI (`dw story
show`, `holds` refactor), `mcpserver.py` (three browse tools),
`docs/interop.md` (new), docs/mcp.md Browse table + cross-links,
the CLAUDE block + snapshot synced per the canon rule.

## Deliberately deferred

- Remote/authenticated transport (localhost/tailnet stands).
- Push (webhooks/SSE) for board changes — pull is the contract.
- OpenAPI/machine-readable specs — trigger: an external consumer
  asking; the doc + stamps are the contract today.
