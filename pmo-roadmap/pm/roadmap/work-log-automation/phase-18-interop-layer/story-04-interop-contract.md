# WLA-18-04 - The interop contract, versioned and pinned

- **Project:** work-log-automation
- **Phase:** 18
- **Status:** done
- **Depends on:** WLA-18-01, WLA-18-02, WLA-18-03
- **Unblocks:** (phase close)
- **Owner:** unassigned

## Problem

The read surface now spans three transports (CLI `--json`, workbench
HTTP, MCP) and several models (context, state feed, board, holds,
story detail, trace, missioncontrol). Nothing names the whole of it
in one place, so a consumer discovers surfaces by reading source —
and a new surface can ship undocumented. A powerful interop layer is
a *named* one.

## Scope

- **In:** `docs/interop.md` — the read-surface contract: one table
  per transport (CLI verbs with `--json`, workbench GET routes, MCP
  tools), each row naming the underlying core function, the model it
  returns, and its schema stamp; the versioning stance (stamps bump
  deliberately; additive changes don't); the read-only guarantee and
  where the write path lives (preview→apply + the gate, by
  reference). Cross-links from docs/mission-control.md (feed) and
  docs/mcp.md. A parity test that enumerates the workbench GET
  routes from `handle_api`'s source and the MCP tool names from the
  registry and asserts each appears in docs/interop.md — a new
  surface cannot ship silently undocumented.
- **Out:** new surfaces (this story documents and pins); OpenAPI
  generation (the doc is the contract; trigger: an external consumer
  asking for machine-readable specs).

## Acceptance criteria

- [ ] `docs/interop.md` names every CLI `--json` verb, every
  workbench GET route, and every MCP tool, each with core function
  + model + schema stamp; readable as the one entry point for a
  consumer.
- [ ] The parity test derives the route and tool inventories from
  code and fails if any is missing from the doc — proven by a
  planted omission in the test's own self-check.
- [ ] docs-lint (link/anchor rules) green over the new doc;
  cross-references from mcp.md and mission-control.md land.
- [ ] `/usr/bin/python3 pmo-roadmap/tests/dw-core-tests.py` green.

## Test plan

- **Unit:** the inventory parity test (+ its planted-omission
  self-check).
- **Integration:** docs-lint.sh, canon-lint.sh.
- **Manual / device:** read-through as a would-be consumer:
  from interop.md alone, fetch the board, follow a card's link to
  a story, and read its evidence — recorded in evidence.

## Notes / open questions

- The doc's scope is READ. The write story (mutations, gate,
  certification) is deliberately elsewhere and referenced, not
  restated — one canon per concern.
