# WLA-18-03 - The MCP read surface: board, holds, story

- **Project:** work-log-automation
- **Phase:** 18
- **Status:** done
- **Depends on:** WLA-18-01, WLA-18-02
- **Unblocks:** WLA-18-04
- **Owner:** unassigned

## Problem

Agents are the heaviest interop consumers, and the MCP server has
nine tools with zero browse surface: no board, no holds, no story.
An MCP-capable agent that wants the kanban or a story's evidence
must shell out — exactly what the server exists to prevent.

## Scope

- **In:** `mcpserver.py` — three read-only tools, adapters over the
  same core functions the CLI `--json` verbs call:
  `dw_board(project?, phase?)` → the WLA-18-01 stamped model;
  `dw_holds(project?)` → `parked_summary` (text mirrors the CLI's
  greppable lines); `dw_story_show(project, phase, story)` →
  `story_detail`. Docs parity: the managed CLAUDE.md block and
  docs/mcp.md name the grown tool set (orientation gains the three;
  certification stance restated unchanged). Tests: tool wiring
  (name → handler → shape), refusal parity (unknown project/story
  errors match the CLI), and the read-only census (no new tool
  touches plan_*/apply).
- **Out:** any mutation tool; transport changes; the contract doc
  itself (WLA-18-04).

## Acceptance criteria

- [ ] `dw_board`, `dw_holds`, `dw_story_show` are served, return
  the same structured objects as `dw board --json`,
  `dw holds --json`, `dw story show --json` — asserted by tests
  comparing both paths on one fixture.
- [ ] Refusals are identical to the CLI's (unknown project, unknown
  story — same messages via DwError).
- [ ] A census test pins the new tools as read-only (no
  plan_/apply_ calls reachable from their handlers).
- [ ] CLAUDE.md managed block + docs/mcp.md name the tools (and the
  .githooks snapshot rides the same commit — the canon rule).
- [ ] `/usr/bin/python3 pmo-roadmap/tests/dw-core-tests.py` green;
  `pmo-roadmap/tests/mcp-server.sh` green.

## Test plan

- **Unit:** MCPServerTest additions per tool; CLI↔MCP parity on a
  fixture; read-only census.
- **Integration:** mcp-server.sh (live stdio round-trip).
- **Manual / device:** n/a.

## Notes / open questions

- Tool descriptions follow the existing house pattern: name the
  adapter ("Adapter over dw_pmo.board.board_model") so the one-core
  guarantee is visible in the schema itself.
