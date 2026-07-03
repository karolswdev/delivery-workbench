# Phase 10 - Agent Interface

**Last updated:** 2026-07-03.

## Goal

Give agents a first-class programmatic surface: a stdlib-only MCP stdio server exposing the dw core as structured JSON tools — orientation, verification, and guarded mutations, never certification — vendored and wired like every other rail, proven against a real client session, and shipped as v1.7.0.

## Scope

- **In:** An MCP surface contract (`docs/mcp.md`) with the tool
  inventory, schemas, and the exclusion list; a stdlib-only stdio
  JSON-RPC server (`lib/dw_pmo/mcpserver.py` + `bin/dw-mcp`) as a
  thin adapter over the same core the CLI calls; orientation,
  verification, and guarded-mutation tools with CLI-parity tests;
  vendoring through install/update/package/formula with a
  non-clobbering `.mcp.json` seam and plugin `mcpServers`
  declaration; an end-to-end client-session proof and the v1.7.0
  release.
- **Out:** Certification or commit tools (the gate's rubber stamp
  is never a tool call), HTTP/SSE transports, MCP
  resources/prompts capabilities, scaffolding tools (phase/story
  create stay CLI ceremony in v1), PyPI activation.

## Exit criteria (evidence required)

- [ ] `docs/mcp.md` fixes the tool inventory, schemas, protocol
  subset, and exclusions; every tool names the core function it
  adapts (no second implementation of any rule).
- [ ] A real stdio exchange (initialize → tools/list → tools/call)
  round-trips against a fixture repo, with tool verdicts proven
  equal to the CLI's on the same state.
- [ ] A fixture story travels backlog → done entirely over MCP
  tools with files byte-identical to the CLI path, while the
  certify/commit exclusion holds and the gate still blocks
  uncertified commits.
- [ ] Fresh installs, upgrades from old rails, and both
  distribution channels deliver a working `dw-mcp`; `.mcp.json`
  wiring never clobbers existing configuration.
- [ ] A live client session completes the loop via MCP only, and
  v1.7.0 ships with version parity, green battery, and the
  annotated tag.

## Story status

| ID | Story | Status | Story file | Evidence |
|---|---|---|---|---|
| WLA-10-01 | Define the MCP surface contract | done | [story-01-define-the-mcp-surface-contract](./story-01-define-the-mcp-surface-contract.md) | [evidence-story-01](./evidence-story-01.md) |
| WLA-10-02 | Implement the stdio MCP server skeleton with orientation tools | done | [story-02-implement-the-stdio-mcp-server-skeleton-with-orientation-tools](./story-02-implement-the-stdio-mcp-server-skeleton-with-orientation-tools.md) | [evidence-story-02](./evidence-story-02.md) |
| WLA-10-03 | Expose guarded mutation tools | done | [story-03-expose-guarded-mutation-tools](./story-03-expose-guarded-mutation-tools.md) | [evidence-story-03](./evidence-story-03.md) |
| WLA-10-04 | Vendor and wire the server for repos agents and the plugin | done | [story-04-vendor-and-wire-the-server-for-repos-agents-and-the-plugin](./story-04-vendor-and-wire-the-server-for-repos-agents-and-the-plugin.md) | [evidence-story-04](./evidence-story-04.md) |
| WLA-10-05 | Prove the surface end-to-end and release v1.7.0 | backlog | [story-05-prove-the-surface-end-to-end-and-release-v1-7-0](./story-05-prove-the-surface-end-to-end-and-release-v1-7-0.md) | - |

## Where we are

WLA-10-04 shipped: dw-mcp is vendored by install.sh and update.sh,
ships in the package payload and formula by construction (bin/ is
grafted whole), the append-only `.mcp.json` seam is proven in three
behaviors (create / append-without-clobber / refuse-unparseable),
upgrades deliver the server to old rails, the managed block and
plugin skill teach the surface, and this repository dogfoods its
own `.mcp.json`. Remaining: WLA-10-05 — the live client proof and
the v1.7.0 release.

## Active risks

| Risk | Likelihood | Mitigation | Stop signal |
|---|---|---|---|
| The server accretes rule logic and becomes a second gate | medium | Thin-adapter rule in the contract; parity tests assert MCP verdicts == CLI verdicts on identical state | Any conditional in mcpserver.py that consults roadmap semantics instead of calling the core |
| A certify/commit tool sneaks in as convenience | low | Exclusion is a tested property of tools/list, not just prose | Any tool whose effect includes checking a contract box or creating a commit |
| Hand-rolled protocol drifts from MCP spec against real clients | medium | Pin the protocol version; WLA-10-05 proves against a live client before release | A real client cannot complete initialize → tools/call |
| stdlib-only framing bugs (partial reads, large payloads) | medium | In-process frame tests incl. malformed input; serial loop keeps state simple | Server dies on a malformed frame or truncates large evidence output |

## Decisions made (this phase)

- 2026-07-03 - Phase scaffolded with `dw phase create` - keeps roadmap structure consistent - CLI.
- 2026-07-03 - Tools only, stdio only, stdlib only in v1 - smallest honest surface; resources/prompts/HTTP wait for demand - phase design (to be locked in WLA-10-01).
- 2026-07-03 - No certification or commit tools, ever, on this surface - attestation is a deliberate act; mechanizing it would hollow out the contract's meaning - locked in WLA-10-01 (`docs/mcp.md`), enforced by test in WLA-10-03.
- 2026-07-03 - The plugin does not declare the MCP server; the repo-scoped `.mcp.json` written by install.sh is the wiring - a plugin-declared server would spawn in rail-less projects and cannot robustly target a repo-vendored binary - WLA-10-04 scope amendment.

## Decisions deferred

- Phase/story scaffolding tools over MCP - trigger: demand from real agent sessions - default is CLI ceremony.
- HTTP/SSE transport for remote agents - trigger: a hosted-collaboration phase - default is stdio.
