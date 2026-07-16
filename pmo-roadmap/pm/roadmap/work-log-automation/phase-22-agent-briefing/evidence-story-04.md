# Evidence - WLA-22-04

- **Story:** WLA-22-04 - The workbench and agent brief open on the answer
- **Status:** done
- **Date:** 2026-07-15

## Proof

### Captured run — 2026-07-16T01:31:40Z

- **Command:** `bash -o pipefail -c python3 pmo-roadmap/tests/dw-core-tests.py 2>&1 | tail -n 10 && bash pmo-roadmap/tests/agent-surface.sh && bash pmo-roadmap/tests/workbench-explorer.sh && bash pmo-roadmap/tests/workbench-ui-smoke.sh && bash pmo-roadmap/tests/plugin-validate.sh && bash pmo-roadmap/tests/docs-lint.sh && bash pmo-roadmap/tests/canon-lint.sh && .githooks/dw rider docs --check && pmo-roadmap/update.sh . --check && .githooks/dw check work-log-automation && git diff --check`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 22208c273dde6b6e7709cf6e6f182532c28d3530

```text

----------------------------------------------------------------------
Ran 220 tests in 19.930s

OK
dw hook: claude — 4 installed, 0 already present in /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.l6lf39wi/settings.json
dw hook: claude — 0 installed, 4 already present in /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.l6lf39wi/settings.json
dw hook: claude — 4 installed, 0 already present in /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.k1amu8yh/settings.json
dw hook: claude — 4 installed, 0 already present in /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.1cohuuzk/settings.json
dw hook: claude — 4 removed from /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.1cohuuzk/settings.json
agent-surface.sh: ok
dw-workbench: serving /private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/pmo-workbench-test.Efm49g/repo
dw-workbench: http://127.0.0.1:19382/ (localhost or your own .ts.net tailnet; Ctrl-C to stop)
dw-workbench: writes happen only via /api/mutations preview→apply inside pm/roadmap; never commits
dw-workbench: shutting down
dw-workbench: serving /private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/pmo-workbench-test.Efm49g/installed
dw-workbench: http://127.0.0.1:19383/ (localhost or your own .ts.net tailnet; Ctrl-C to stop)
dw-workbench: writes happen only via /api/mutations preview→apply inside pm/roadmap; never commits
workbench-explorer.sh: ok
dw-workbench: shutting down
dw-workbench: serving /private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/pmo-workbench-test.Efm49g/repo
dw-workbench: http://127.0.0.1:19382/ (localhost or your own .ts.net tailnet; Ctrl-C to stop)
dw-workbench: writes happen only via /api/mutations preview→apply inside pm/roadmap; never commits
workbench-ui-smoke.sh: ok (18 viewport renders: 7 views + attention + ambiguity, desktop+mobile)
dw-workbench: shutting down
dw-workbench: serving /private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/pmo-ui-smoke.777SsZ/repo
dw-workbench: http://127.0.0.1:21966/ (localhost or your own .ts.net tailnet; Ctrl-C to stop)
dw-workbench: writes happen only via /api/mutations preview→apply inside pm/roadmap; never commits
plugin manifests: ok (version 1.14.0, 4 commands, 1 skill)
claude plugin validate: ok
plugin-validate.sh: ok
docs-lint: ok (363 markdown files)
docs-lint.sh: ok (0s)
canon-lint.sh: ok
dw rider docs: all rendered surfaces match canon
update.sh: up to date (vendored rails match source v1.14.0)
dw check: ok
```
