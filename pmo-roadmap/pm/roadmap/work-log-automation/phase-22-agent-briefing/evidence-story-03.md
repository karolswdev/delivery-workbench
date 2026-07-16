# Evidence - WLA-22-03

- **Story:** WLA-22-03 - One model everywhere — MCP and HTTP parity
- **Status:** done
- **Date:** 2026-07-15

## Proof

### Captured run — 2026-07-16T01:20:31Z

- **Command:** `bash -o pipefail -c python3 pmo-roadmap/tests/dw-core-tests.py 2>&1 | tail -n 10 && bash pmo-roadmap/tests/mcp-server.sh && bash pmo-roadmap/tests/workbench-explorer.sh && bash pmo-roadmap/tests/adoption-discovery.sh && bash pmo-roadmap/tests/upgrade-path.sh && bash pmo-roadmap/tests/package-smoke.sh && bash pmo-roadmap/tests/docs-lint.sh && bash pmo-roadmap/tests/canon-lint.sh && pmo-roadmap/update.sh . --check && .githooks/dw check work-log-automation && git diff --check`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 346c48915b454d6413a0ef35f6bbfe3c810b48b4

```text

----------------------------------------------------------------------
Ran 219 tests in 19.808s

OK
dw hook: claude — 4 installed, 0 already present in /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.mumwosqa/settings.json
dw hook: claude — 0 installed, 4 already present in /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.mumwosqa/settings.json
dw hook: claude — 4 installed, 0 already present in /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.3ezla2c2/settings.json
dw hook: claude — 4 installed, 0 already present in /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.pxvryypz/settings.json
dw hook: claude — 4 removed from /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.pxvryypz/settings.json
protocol exchange: ok (9 replies)
no-rails refusal: ok
mutation walk: ok (done-without-evidence refused; contract stamped, certification manual)
gate still blocks uncertified commits: ok
MCP/CLI byte-parity (timestamps normalized): ok
mcp-server.sh: ok
dw-workbench: serving /private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/pmo-workbench-test.jRiwIt/repo
dw-workbench: http://127.0.0.1:18909/ (localhost or your own .ts.net tailnet; Ctrl-C to stop)
dw-workbench: writes happen only via /api/mutations preview→apply inside pm/roadmap; never commits
dw-workbench: shutting down
dw-workbench: serving /private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/pmo-workbench-test.jRiwIt/installed
dw-workbench: http://127.0.0.1:18910/ (localhost or your own .ts.net tailnet; Ctrl-C to stop)
dw-workbench: writes happen only via /api/mutations preview→apply inside pm/roadmap; never commits
workbench-explorer.sh: ok
dw-workbench: shutting down
dw-workbench: serving /private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/pmo-workbench-test.jRiwIt/repo
dw-workbench: http://127.0.0.1:18909/ (localhost or your own .ts.net tailnet; Ctrl-C to stop)
dw-workbench: writes happen only via /api/mutations preview→apply inside pm/roadmap; never commits
adoption-discovery.sh: ok
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✓ The system accepted your understanding of the project management framework.
  Contract acknowledged (7/7 checkboxes).
  Commit proceeding.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
pmo-roadmap post-commit: contract archived to .git/pmo-contract-archive/fe200c70ded703dbab061b5e0c1874d9b910ae6f
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✓ The system accepted your understanding of the project management framework.
  Contract acknowledged (7/7 checkboxes).
  Stories shipped this commit: 1 (evidence verified by dw gate).
  Commit proceeding.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
pmo-roadmap post-commit: contract archived to .git/pmo-contract-archive/21c2fdf35b1fb5f8823a1a86cf55b6bdf84ce780
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✓ The system accepted your understanding of the project management framework.
  Contract acknowledged (7/7 checkboxes).
  Commit proceeding.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
pmo-roadmap post-commit: contract archived to .git/pmo-contract-archive/70463626ce6b345fa89f0755a2f50ae226528120
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✓ The system accepted your understanding of the project management framework.
  Contract acknowledged (7/7 checkboxes).
  Stories shipped this commit: 1 (evidence verified by dw gate).
  Commit proceeding.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
pmo-roadmap post-commit: contract archived to .git/pmo-contract-archive/237bc58d03f430ab105f501861091be65f5ad983
upgrade-path.sh: ok
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
You should consider upgrading via the '/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/pmo-package-smoke.sPqbB7/appenv/bin/python -m pip install --upgrade pip' command.
package-smoke.sh: installed via venv+pip
package-smoke.sh: ok
docs-lint: ok (362 markdown files)
docs-lint.sh: ok (1s)
canon-lint.sh: ok
update.sh: up to date (vendored rails match source v1.14.0)
dw check: ok
```
