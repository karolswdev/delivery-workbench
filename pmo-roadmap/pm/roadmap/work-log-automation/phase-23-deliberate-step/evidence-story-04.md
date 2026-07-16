# Evidence - WLA-23-04

- **Story:** WLA-23-04 - Workbench and riders expose the handrail
- **Status:** done
- **Date:** 2026-07-16

## Proof

### Captured run — 2026-07-16T15:05:35Z

- **Command:** `bash -c set -e
python3 pmo-roadmap/tests/dw-core-tests.py -q
/usr/bin/python3 pmo-roadmap/tests/dw-core-tests.py -q
node --check pmo-roadmap/workbench/app.js
node --check .githooks/workbench/app.js
bash pmo-roadmap/tests/workbench-explorer.sh
bash pmo-roadmap/tests/workbench-ui-smoke.sh
bash pmo-roadmap/tests/step-interop.sh
bash pmo-roadmap/tests/mcp-server.sh
bash pmo-roadmap/tests/agent-surface.sh
bash pmo-roadmap/tests/plugin-validate.sh
bash pmo-roadmap/tests/package-smoke.sh
bash pmo-roadmap/tests/docs-lint.sh
bash pmo-roadmap/tests/docs-snippet-smoke.sh
bash pmo-roadmap/tests/canon-lint.sh
shellcheck -e SC2317 pmo-roadmap/tests/workbench-ui-smoke.sh pmo-roadmap/tests/step-interop.sh
.githooks/dw rider docs --check
pmo-roadmap/update.sh . --check
.githooks/dw check work-log-automation
git diff --check`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 04a242f2dc932775b6278423b1162f2cedfd9275

```text
dw hook: codex_hooks is explicitly false in /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.l2yus8vx/config.toml; respecting the opt-out
----------------------------------------------------------------------
Ran 230 tests in 24.303s

OK
dw hook: claude — 4 installed, 0 already present in /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.xvd2o1xg/settings.json
dw hook: claude — 0 installed, 4 already present in /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.xvd2o1xg/settings.json
dw hook: claude — 4 installed, 0 already present in /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test._njxkoye/settings.json
dw hook: claude — 4 installed, 0 already present in /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.59v9zal9/settings.json
dw hook: claude — 4 removed from /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.59v9zal9/settings.json
dw hook: codex_hooks is explicitly false in /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.86ffs99o/config.toml; respecting the opt-out
----------------------------------------------------------------------
Ran 230 tests in 22.922s

OK
dw hook: claude — 4 installed, 0 already present in /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.f86jozdu/settings.json
dw hook: claude — 0 installed, 4 already present in /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.f86jozdu/settings.json
dw hook: claude — 4 installed, 0 already present in /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.xhvki059/settings.json
dw hook: claude — 4 installed, 0 already present in /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.u54g6pen/settings.json
dw hook: claude — 4 removed from /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.u54g6pen/settings.json
dw-workbench: serving /private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/pmo-workbench-test.4189Sn/repo
dw-workbench: http://127.0.0.1:19879/ (localhost or your own .ts.net tailnet; Ctrl-C to stop)
dw-workbench: writes require /api/mutations preview→apply or an exact /api/step/apply token; never stages, certifies, or commits
dw-workbench: shutting down
dw-workbench: serving /private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/pmo-workbench-test.4189Sn/installed
dw-workbench: http://127.0.0.1:19880/ (localhost or your own .ts.net tailnet; Ctrl-C to stop)
dw-workbench: writes require /api/mutations preview→apply or an exact /api/step/apply token; never stages, certifies, or commits
workbench-explorer.sh: ok
dw-workbench: shutting down
dw-workbench: serving /private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/pmo-workbench-test.4189Sn/repo
dw-workbench: http://127.0.0.1:19879/ (localhost or your own .ts.net tailnet; Ctrl-C to stop)
dw-workbench: writes require /api/mutations preview→apply or an exact /api/step/apply token; never stages, certifies, or commits
workbench-ui-smoke.sh: ok (20 viewport renders: 8 views + attention + ambiguity, desktop+mobile)
dw-workbench: shutting down
dw-workbench: serving /private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/pmo-ui-smoke.cfahSB/repo
dw-workbench: http://127.0.0.1:22043/ (localhost or your own .ts.net tailnet; Ctrl-C to stop)
dw-workbench: writes require /api/mutations preview→apply or an exact /api/step/apply token; never stages, certifies, or commits
preview parity: CLI = MCP = HTTP
result parity:  CLI = MCP = HTTP
replay/injection: refused without another child
certification/commit: previewable, never applicable
step-interop.sh: ok
protocol exchange: ok (9 replies)
no-rails refusal: ok
mutation walk: ok (done-without-evidence refused; contract stamped, certification manual)
gate still blocks uncertified commits: ok
MCP/CLI byte-parity (timestamps normalized): ok
mcp-server.sh: ok
agent-surface.sh: ok
plugin manifests: ok (version 1.14.0, 4 commands, 1 skill)
claude plugin validate: ok
plugin-validate.sh: ok
package-smoke.sh: skipping unhealthy interpreter: python3
package-smoke.sh: building with: /usr/bin/python3 (Python 3.9.6)
* Creating isolated environment: venv+pip...
* Installing packages in isolated environment:
  - setuptools>=77
* Getting build dependencies for sdist...
warning: no previously-included files matching '*.pyc' found anywhere in distribution
* Building sdist...
warning: no previously-included files matching '*.pyc' found anywhere in distribution
* Building wheel from sdist
* Creating isolated environment: venv+pip...
* Installing packages in isolated environment:
  - setuptools>=77
* Getting build dependencies for wheel...
warning: no previously-included files matching '__pycache__/*' found anywhere in distribution
warning: no previously-included files matching '*.pyc' found anywhere in distribution
* Building wheel...
warning: no previously-included files matching '__pycache__/*' found anywhere in distribution
warning: no previously-included files matching '*.pyc' found anywhere in distribution
package-smoke.sh: built delivery_workbench-1.14.0-py3-none-any.whl and delivery_workbench-1.14.0.tar.gz
package-smoke.sh: pipx cannot create environments here; falling back to venv+pip
WARNING: You are using pip version 21.2.4; however, version 26.0.1 is available.
You should consider upgrading via the '/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/pmo-package-smoke.ZTJDbJ/appenv/bin/python -m pip install --upgrade pip' command.
package-smoke.sh: installed via venv+pip
ready     review-workspace   absent     not-applicable
ready     generate-contract  absent     fail
ready     certify-contract   unchecked  fail
ready     commit             passing    pass
ready     start-story        absent     not-applicable
ready     continue-story     absent     not-applicable
attention repair-roadmap     absent     not-applicable
ready     continue-story     absent     not-applicable
ready     continue-story     absent     not-applicable
attention finish-story       absent     not-applicable
ready     review-workspace   absent     not-applicable
ready     generate-contract  absent     fail
ready     certify-contract   unchecked  fail
ready     generate-contract  stale      fail
ready     certify-contract   unchecked  fail
ready     commit             passing    pass
ready     start-story        absent     not-applicable
commit     f548f8e6b114         trailers+archive+verify=ok
guided-status-loop.sh: ok (packaged CLI/MCP/HTTP recommendation sequence)
package-smoke.sh: ok
docs-lint: ok (376 markdown files)
docs-lint.sh: ok (0s)
ok: CONTRIBUTING.md snippet 'contributor-setup' ran as printed
ok: CONTRIBUTING.md snippet 'contributor-gated-commit' ran as printed
ok: pmo-roadmap/README.md snippet 'install' ran as printed
ok: pmo-roadmap/README.md snippet 'update' ran as printed
ok: pmo-roadmap/README.md snippet 'new-project' ran as printed
ok: pmo-roadmap/README.md snippet 'adopt-three-step' ran as printed
ok: pmo-roadmap/README.md snippet 'intake-no-prompt' ran as printed
ok: pmo-roadmap/README.md snippet 'adopt-close-loop' ran as printed
docs-lint snippets: ok
docs-snippet-smoke.sh: ok
canon-lint.sh: ok
dw rider docs: all rendered surfaces match canon
update.sh: up to date (vendored rails match source v1.14.0)
dw check: ok
```
