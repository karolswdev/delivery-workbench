# Phase 10 Final Summary

**Status:** complete.
**Date:** 2026-07-03.

Phase 10 gave agents a first-class programmatic surface without
surrendering an inch of the gate: `dw-mcp`, a stdlib-only MCP stdio
server, exposes the dw core as structured JSON tools with
CLI-identical guardrails — and with the refusals that matter most
enforced as tested properties. A real Claude Code session drove a
story from backlog to done over MCP tools alone, and the one
"error" it hit was the rails telling it the truth.

## Outcome vs exit criteria

All five exit criteria closed with evidence:

1. **Surface contract** — `docs/mcp.md` fixes nine tools mapped
   one-to-one onto named core functions (no second implementation
   of any rule), the pinned protocol subset (stdio ndjson JSON-RPC,
   2025-06-18, tools-only, serial, stdlib-only), and the exclusion
   list: certification, commits, and bundle consent are never tool
   calls (evidence-story-01).
2. **Real stdio exchange with CLI parity** — initialize →
   tools/list → tools/call round-trips against an installed
   fixture; malformed frames survive; verdicts equal the CLI's on
   identical state; outside adopted repos tool calls return a
   discoverable install hint (evidence-story-02,
   `tests/mcp-server.sh`, 7 in-process protocol cases).
3. **Mutations with identical guardrails** — a fixture story walked
   backlog → in-progress → capture → done over MCP only, byte-
   identical (timestamps normalized) to a CLI-driven twin; the
   done-without-evidence refusal carries the core's own message;
   after everything the server did, the contract's boxes were
   unchecked and the gate still blocked an uncertified commit
   (evidence-story-03).
4. **Wired everywhere rails go** — install/update vendor `dw-mcp`;
   the `.mcp.json` seam is append-only with three proven behaviors
   (create / append-without-clobber / refuse-unparseable); package
   and formula carry the server; upgrades deliver it to old rails;
   the managed block and plugin skill teach it; this repository
   dogfoods its own entry. Recorded scope amendment: the plugin
   does not declare the server — repo-scoped `.mcp.json` is the
   native mechanism (evidence-story-04).
5. **Live client proof and v1.7.0** — a genuine nested Claude Code
   session (`--mcp-config --strict-mcp-config`) completed the full
   loop via MCP tools only; `claude mcp list` discovers the
   dogfooded server; every version surface reports 1.7.0 under the
   parity tests; both distribution smokes and the full battery are
   green at the release commit (evidence-story-05).

## What shipped

- `docs/mcp.md`; `lib/dw_pmo/mcpserver.py`; `bin/dw-mcp`;
  installer/updater vendoring with the `.mcp.json` seam; managed
  block, snippet, and SKILL.md teaching the surface; CHANGELOG
  v1.7.0.
- Tests: `tests/mcp-server.sh` (protocol, mutations, exclusion,
  gate-still-blocks, MCP/CLI byte-parity), `MCPServerTest` (10
  cases; unit suite 117 → 128 across the phase), seam regression
  cases in adoption-discovery, delivery assertions in package-smoke
  and upgrade-path, CI wiring incl. the floor compile of `dw-mcp`.

## Deliberately deferred

Phase/story scaffolding tools over MCP (CLI ceremony is
proportionate; trigger: demand from real agent sessions), HTTP/SSE
transport (trigger: a hosted-collaboration phase), MCP
resources/prompts capabilities, PyPI activation (still one
registration away).

Future work starts by opening a new phase with `dw phase create`
and letting the rails do what they were built to do.
