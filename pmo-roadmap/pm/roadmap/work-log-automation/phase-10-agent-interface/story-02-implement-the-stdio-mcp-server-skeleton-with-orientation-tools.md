# WLA-10-02 - Implement the stdio MCP server skeleton with orientation tools

- **Project:** work-log-automation
- **Phase:** 10
- **Status:** done
- **Depends on:** WLA-10-01
- **Unblocks:** WLA-10-03
- **Owner:** unassigned

## Problem

The contract from WLA-10-01 needs a running server: a stdlib-only
stdio JSON-RPC loop speaking the pinned MCP subset, with the
read-only half of the tool inventory — the part an agent needs to
orient before it changes anything.

## Scope

- **In:** `lib/dw_pmo/mcpserver.py` — request loop (Content-Length
  framing per MCP stdio, or newline-delimited JSON per the design
  doc's decision), `initialize` handshake advertising tools-only
  capability, `tools/list` serving the schemas from the design doc,
  `tools/call` dispatch, `ping`, JSON-RPC error objects for unknown
  methods/tools/invalid params. Orientation and verification tools
  wired to the shared core: `dw_context`, `dw_next`, `dw_check`,
  `dw_doctor`, `dw_verify`, `dw_gate` — every result carrying both
  human-greppable text content and `structuredContent`. A
  `bin/dw-mcp` entry script (same bootstrap seam as `bin/dw`).
  Protocol-level tests in `pmo-roadmap/tests/dw-core-tests.py`
  (drive the loop in-process with synthetic frames) plus a
  subprocess smoke `pmo-roadmap/tests/mcp-server.sh` (spawn
  `dw-mcp`, initialize, list tools, call `dw_next` and `dw_check`
  against a fixture repo, assert JSON).
- **Out:** Mutation tools (WLA-10-03), vendoring/wiring
  (WLA-10-04), any MCP capability beyond tools.

## Acceptance criteria

- [ ] A real client exchange works over stdio: initialize →
  tools/list (exact inventory from the design doc, orientation
  subset) → tools/call round-trips with valid JSON-RPC framing.
- [ ] Tool results match the CLI's verdicts on the same fixture
  (e.g. `dw_check` reports the same issues `dw check` prints;
  `dw_next` agrees with `dw next --json`) — parity asserted in
  tests, not claimed.
- [ ] Unknown method → JSON-RPC -32601; unknown tool and bad params
  → tool-level errors per the design doc; a malformed frame does
  not kill the loop.
- [ ] Stdlib-only holds (compileall on the python floor passes; no
  new imports outside the standard library).

## Test plan

- **Unit:** in-process protocol cases in `dw-core-tests.py`
  (handshake, list, call, error paths, framing).
- **Integration:** `pmo-roadmap/tests/mcp-server.sh` subprocess
  smoke against a fixture repo.
- **Manual / device:** drive it from a live MCP client session
  (deferred to WLA-10-05's end-to-end proof).

## Notes / open questions

- Concurrency: the loop is strictly serial in v1 — dw operations
  are fast and the CLI is serial too; note it in the doc.
