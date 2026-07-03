# Evidence - WLA-10-02

- **Story:** WLA-10-02 - Implement the stdio MCP server skeleton with orientation tools
- **Status:** done
- **Date:** 2026-07-03

## Proof

Deliverables:

- `lib/dw_pmo/mcpserver.py` — the stdio server: newline-delimited
  JSON-RPC 2.0, pinned protocol 2025-06-18, tools-only capability,
  strictly serial loop that survives malformed frames (-32700 and
  continue), JSON-RPC errors for unknown methods (-32601) and bad
  params (-32602). Six orientation/verification tools registered
  (`dw_context`, `dw_next`, `dw_check`, `dw_doctor`, `dw_verify`,
  `dw_gate`), each a thin adapter calling the exact core function
  `docs/mcp.md` names; every result carries greppable text plus
  `structuredContent`. Outside adopted repos: initialize succeeds,
  tool calls return the discoverable no-rails refusal naming the
  install command.
- `bin/dw-mcp` — entry script with the same bootstrap seam as
  `bin/dw`; compiles clean on the 3.9 floor.
- Tests: `MCPServerTest` (7 in-process protocol/parity/error cases;
  unit suite 117 → 124) and `tests/mcp-server.sh` — a real
  subprocess exchange against a freshly installed fixture repo
  (initialize → tools/list incl. the exclusion assertion →
  dw_next/dw_check/dw_verify with CLI parity → -32601 → garbage
  frame survival → unknown-tool error → ping), plus the no-rails
  leg. Wired into CI (integration step + shellcheck/syntax lists +
  floor compile of dw-mcp).

The captured run: fixture smoke green, the 7 protocol cases green,
full 124-test suite green.


### Captured run — 2026-07-03T19:56:11Z

- **Command:** `bash -c set -e -o pipefail; bash pmo-roadmap/tests/mcp-server.sh; python3 pmo-roadmap/tests/dw-core-tests.py MCPServerTest 2>&1 | tail -3; python3 pmo-roadmap/tests/dw-core-tests.py 2>&1 | tail -1`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 2086708d2417327cae9fbf9863b4207312591999

```text
protocol exchange: ok (8 replies)
no-rails refusal: ok
mcp-server.sh: ok
Ran 7 tests in 0.014s

OK
OK
```
