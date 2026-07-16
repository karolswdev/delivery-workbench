# WLA-22-03 - One model everywhere — MCP and HTTP parity

- **Project:** work-log-automation
- **Phase:** 22
- **Status:** ready
- **Depends on:** WLA-22-02
- **Unblocks:** WLA-22-04, WLA-22-05
- **Owner:** unassigned

## Problem

A status command helps terminal users but leaves agents and the browser
reassembling the same facts. The existing interop promise is strongest
when adapters are byte-thin over a single model and tests make drift
impossible.

## Scope

- **In:** `dw_status` (optional project), `GET /api/status?project=`,
  `docs/mcp.md`, `docs/interop.md`, tool/route census pins, CLI/MCP/HTTP
  structured-payload parity, refusal and read-only tests, installed-copy
  parity.
- **Out:** UI rendering and managed-agent prose (WLA-22-04); mutation;
  remote transport/auth changes; schema v2.

## Acceptance criteria

- [ ] MCP and HTTP call the status core directly and contain no readiness
  or action-selection conditionals.
- [ ] Normal and attention fixtures produce the same structured object
  through CLI JSON, MCP `structuredContent`, and HTTP envelope `data`.
- [ ] The tool and GET route are documented, census-pinned, read-only,
  usable with one or many projects, and do not convert attention into a
  tool/protocol error.
- [ ] The MCP tool inventory still excludes certification, commit, and
  bundle operations; status can recommend but cannot execute them.
- [ ] Install/update/package fixtures carry the new module and all three
  adapters.

## Test plan

- **Unit:** adapter/core equality and interop inventory tests.
- **Integration:** extend `mcp-server.sh`, `workbench-explorer.sh`, and
  package smoke with green and attention status legs.
- **Manual / device:** query the real repository over CLI, MCP protocol,
  and a running localhost workbench; normalize only the HTTP envelope's
  generated timestamp and compare `data` exactly.

## Notes / open questions

Attention is data, not a transport failure: an agent most needs the
briefing when something is wrong.
