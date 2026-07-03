# WLA-10-04 - Vendor and wire the server for repos agents and the plugin

- **Project:** work-log-automation
- **Phase:** 10
- **Status:** backlog
- **Depends on:** WLA-10-03
- **Unblocks:** WLA-10-05
- **Owner:** unassigned

## Problem

A server nobody's client can find is a demo. The rails' whole
distribution story — vendored per-repo copies, installer/updater,
package payload, plugin — must carry `dw-mcp` the same way it
carries `dw`, and agent-facing configuration must point at the
vendored copy (the same defer-to-repo logic the global launcher
obeys: the server that answers must be the rails that gate).

## Scope

- **In:** `install.sh`/`update.sh` vendor `bin/dw-mcp` →
  `.githooks/dw-mcp` (payload inventory, `docs/distribution.md`
  table, and the doc-parity cross-check updated); install writes a
  `.mcp.json` entry for the vendored server if the file is absent
  or lacks the entry (append-only, never clobbering existing
  servers — same posture as the .gitignore seam); the Claude Code
  plugin declares the server (`plugin/.claude-plugin/plugin.json`
  `mcpServers` → `.githooks/dw-mcp`, so plugin users get the tools
  wherever rails are installed); the managed CLAUDE.md block,
  plugin SKILL.md, and `docs/mcp.md` teach the surface; upgrade
  path: `update.sh --check` content comparison already covers new
  vendored files — assert `dw-mcp` arrives on upgrade in
  `upgrade-path.sh`; this repo's own `.mcp.json` gains the entry
  (self-hosting dogfood).
- **Out:** Marketplace re-publication mechanics beyond the version
  bump (WLA-10-05 handles release), HTTP transport, per-tool
  permission configuration (client-side concern).

## Acceptance criteria

- [ ] A fresh `install.sh` target has `.githooks/dw-mcp`
  executable, a `.mcp.json` pointing at it, and the smoke can
  initialize against it; an existing `.mcp.json` with other
  servers survives install untouched except the added entry.
- [ ] `upgrade-path.sh` proves a v1.5.0-adopted repo gains
  `dw-mcp` and the `.mcp.json` seam on update.
- [ ] Package payload and formula installs carry the server
  (package-smoke asserts the vendored file); the payload
  cross-check in `docs/distribution.md` includes it.
- [ ] Agent docs parity tests pass with the new surface taught in
  the managed block and SKILL.md.

## Test plan

- **Unit:** doc-parity and plugin-parity extensions.
- **Integration:** adoption-discovery/package-smoke/upgrade-path
  extended assertions; `mcp-server.sh` run against an installed
  fixture (not the source tree).
- **Manual / device:** `claude mcp list`-style client discovery in
  this repo (deferred proof lands in WLA-10-05).

## Notes / open questions

- `.mcp.json` merging: stdlib JSON read-modify-write with a
  refusal on unparseable files (never guess at a broken config).
