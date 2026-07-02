# Evidence - WLA-5-09

- **Story:** WLA-5-09 - Harden permissions and local runtime model
- **Status:** done
- **Date:** 2026-07-02

## What shipped

- **Startup fails closed:** the server refuses a nonexistent root, a
  root without a `pm/roadmap` tree, and a busy port — each with a
  clear message naming the remediation (`pass --port`, run
  `dw adopt`/new-project). At startup it prints the served root, the
  URL, and the write policy ("writes happen only via /api/mutations
  preview→apply inside pm/roadmap; never commits").
- **Default-deny at the HTTP layer:** non-local `Host` headers get 403
  (DNS-rebinding guard, bracketed-IPv6-aware parsing), `OPTIONS`
  preflights get 405, and no CORS header is ever emitted (asserted).
  `X-Content-Type-Options: nosniff` on every JSON response. Requests
  log to stderr (`--quiet` to silence) — the suite asserts the access
  log recorded its own 403 and 409 refusals. SIGTERM shuts down
  cleanly and frees the port (proved by rebinding it).
- **A real containment finding, fixed at the core:** the security test
  discovered that a hostile `slug` (`../../escape`) passed
  `ensure_under` when the resolved path stayed *inside* `pm/roadmap`
  while escaping the target phase — cross-project writes were
  constructible. `validate_slug` now enforces the slugify alphabet
  (`[a-z0-9-]` only, in the core, so the CLI benefits too); full-tree
  escapes were already fatal via resolved-path containment.
- **No git surface, provably:** the fixture is now a git repo and the
  suite asserts `git ls-files` is empty after every preview and apply
  cycle — nothing was ever staged, and no endpoint exists that could
  commit.
- **The installation decision (as the story's note required, after
  the boundary was proven):** `install.sh`/`update.sh` now distribute
  `bin/dw-workbench` → `.githooks/dw-workbench` and the static UI →
  `.githooks/workbench/`; `workbench_dir()` resolves both source and
  installed layouts, and the integration suite installs into a fresh
  repo and drives the installed binary end to end. The managed
  CLAUDE.md agent-docs block now names the command.

## Acceptance proof

Unit (78-test core suite): the Host allowlist (local forms pass,
external/LAN/0.0.0.0 refused), slug-injection refusals for both
create kinds, and serve()'s fail-closed refusals with message
assertions. Integration (both OSes): git-index purity, OPTIONS/evil-
Host/CORS default-deny, startup refusal messages, port-conflict
remediation text, access-log content, SIGTERM port reuse, and the
installed-layout end-to-end drive. The captured runs below show the
suite green and the real refusal banners (bare root, hostile slug).

## Proof — captured runs (appended by `dw evidence capture`)

### Captured run — 2026-07-02T21:49:14Z

- **Command:** `pmo-roadmap/tests/workbench-explorer.sh`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 27123b7b0ce7625c067844bab8d14427032d5d80

```text
dw-workbench: serving /private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/pmo-workbench-test.il36ux/repo
dw-workbench: http://127.0.0.1:18917/ (localhost only; Ctrl-C to stop)
dw-workbench: writes happen only via /api/mutations preview→apply inside pm/roadmap; never commits
dw-workbench: shutting down
dw-workbench: serving /private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/pmo-workbench-test.il36ux/installed
dw-workbench: http://127.0.0.1:18918/ (localhost only; Ctrl-C to stop)
dw-workbench: writes happen only via /api/mutations preview→apply inside pm/roadmap; never commits
wor
[PMO_EVIDENCE_OUTPUT_TRUNCATED]
```

### Captured run — 2026-07-02T21:49:18Z

- **Command:** `sh -c 
BARE=$(mktemp -d)
echo "=== refusal: root without a roadmap ==="
pmo-roadmap/bin/dw-workbench --root "$BARE" 2>&1; echo "exit=$?"
echo "=== refusal: hostile slug via API (unit-level) ==="
python3 -c "
import sys; sys.path.insert(0,\"pmo-roadmap/lib\")
from pathlib import Path
from dw_pmo import workbench as wb
status, p = wb.handle_mutation(Path(\".\").resolve(), \"/api/mutations/preview\",
  {\"kind\":\"create_phase\",\"project\":\"work-log-automation\",\"number\":\"99\",\"title\":\"X\",\"slug\":\"../../evil\"})
print(status, p[\"issues\"][0])"
rm -rf "$BARE"`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 27123b7b0ce7625c067844bab8d14427032d5d80

```text
=== refusal: root without a roadmap ===
dw-workbench: no pm/roadmap tree under /private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/tmp.oTlbIv1WyY — the workbench serves exactly one roadmap-bearing repo root; pass --root or run dw adopt / new-project first
exit=1
=== refusal: hostile slug via API (unit-level) ===
400 invalid slug '../../evil': lowercase letters, digits, and hyphens only
```
