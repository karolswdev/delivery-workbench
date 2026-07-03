# Evidence - WLA-10-04

- **Story:** WLA-10-04 - Vendor and wire the server for repos agents and the plugin
- **Status:** done
- **Date:** 2026-07-03

## Proof

Deliverables: `install.sh` and `update.sh` vendor `bin/dw-mcp` →
`.githooks/dw-mcp`; install writes the `.mcp.json` seam
(append-only: creates when absent, appends without clobbering
existing servers, refuses unparseable files — all three behaviors
regression-tested in adoption-discovery.sh); the package payload
and formula carry the server by construction (`bin/` grafts whole,
asserted in package-smoke); upgrade-path proves old rails gain
`dw-mcp` on refresh; the managed CLAUDE.md block,
CLAUDE-snippet template, and plugin SKILL.md teach the surface;
`docs/distribution.md`'s payload table names the binary; and this
repository dogfoods its own `.mcp.json` entry.

Scope amendment, recorded in the story and phase status: the plugin
does NOT declare the server — a plugin-declared MCP server would
spawn in every project including rail-less ones and cannot robustly
target a repo-vendored binary; the repo-scoped `.mcp.json` is the
native mechanism and honors the vendored-rails invariant.

The captured run: all four affected suites green (adoption seam
cases, packaged install, upgrade delivery, full MCP smoke), the
dogfooded `.mcp.json` shown, and the full unit suite green.


### Captured run — 2026-07-03T20:03:25Z

- **Command:** `bash -c set -e -o pipefail; echo "== vendored + seam on a fresh install (from adoption-discovery suite) =="; bash pmo-roadmap/tests/adoption-discovery.sh 2>&1 | tail -1; echo "== packaged install carries the server =="; bash pmo-roadmap/tests/package-smoke.sh 2>&1 | tail -1; echo "== upgrades deliver it to old rails =="; bash pmo-roadmap/tests/upgrade-path.sh 2>&1 | tail -1; echo "== full server smoke against installed fixture =="; bash pmo-roadmap/tests/mcp-server.sh 2>&1 | tail -1; echo "== this repo dogfoods the wiring =="; cat .mcp.json; test -x .githooks/dw-mcp && echo ".githooks/dw-mcp executable"; python3 pmo-roadmap/tests/dw-core-tests.py 2>&1 | tail -1`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 2946304e2910e6c49b70fcd73f2f0479e3b9416c

```text
== vendored + seam on a fresh install (from adoption-discovery suite) ==
adoption-discovery.sh: ok
== packaged install carries the server ==
package-smoke.sh: ok
== upgrades deliver it to old rails ==
upgrade-path.sh: ok
== full server smoke against installed fixture ==
mcp-server.sh: ok
== this repo dogfoods the wiring ==
{
  "mcpServers": {
    "delivery-workbench": {
      "type": "stdio",
      "command": ".githooks/dw-mcp",
      "args": []
    }
  }
}
.githooks/dw-mcp executable
OK
```
