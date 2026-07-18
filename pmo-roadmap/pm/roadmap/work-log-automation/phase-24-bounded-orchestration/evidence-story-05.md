# Evidence - WLA-24-05

- **Story:** WLA-24-05 - Drive research and worker agents in isolated workspaces
- **Status:** done
- **Date:** 2026-07-17

## Proof

### Result interpretation

- The first capture proves both 273-test Python runtime suites, a wheel/sdist
  install in a fresh environment, and an authenticated read-only `codex exec`
  session. That session returned declared artifact `live-findings` with content
  hash `sha256:ee2270d22c9ab508ff4082d4943469e893b427346c72a854e46d1f1b5736fe5c`,
  passed section/citation/size/containment checks, appended three ledger events,
  and left the operator tree clean. Its final exit 127 is the captured typo in
  the subsequent docs-script path; none of those completed proofs failed.
- The second capture uses the real docs/canon/agent scripts and proves all four
  surfaces. Its final exit 1 is the expected structural refusal while evidence
  existed and WLA-24-05 had not yet been transitioned from `in-progress` to
  `done`.
- The third capture follows that explicit lifecycle transition and closes with
  `dw check`, rendered-rider parity, source/vendor parity, and both worktree and
  index whitespace checks green. The fixture suite separately covers two
  concurrent research agents, validation-gated synthesis, isolated writer
  worktrees and locks, scoped diff receipts, idempotent recovery, pause/stale
  refusal, timeout/nonzero/lost/oversized/malformed outcomes, and truthful
  interrupt capabilities.

### Captured run — 2026-07-18T05:35:55Z

- **Command:** `bash -o pipefail -c set -e
python3 pmo-roadmap/tests/dw-core-tests.py -q
/usr/bin/python3 pmo-roadmap/tests/dw-core-tests.py -q
bash pmo-roadmap/tests/package-smoke.sh
DW_CODEX_DRIVER_LIVE=1 bash pmo-roadmap/tests/codex-driver-smoke.sh
bash pmo-roadmap/roadmap-cli.sh docs-lint
bash pmo-roadmap/roadmap-cli.sh docs-snippet
bash pmo-roadmap/roadmap-cli.sh canon
bash pmo-roadmap/roadmap-cli.sh agent --check
python3 -m py_compile pmo-roadmap/lib/dw_pmo/orchestration_run.py pmo-roadmap/lib/dw_pmo/orchestration_driver.py
/usr/bin/python3 -m py_compile pmo-roadmap/lib/dw_pmo/orchestration_run.py pmo-roadmap/lib/dw_pmo/orchestration_driver.py
bash -n pmo-roadmap/tests/codex-driver-smoke.sh
.githooks/dw check
.githooks/dw rider docs --check
pmo-roadmap/update.sh . --check
git diff --check
git diff --cached --check`
- **Cwd:** .
- **Exit code:** 127
- **Index-tree:** 27a7886952df4275f6f216df9d2f76956185b0dc

```text
dw hook: codex_hooks is explicitly false in /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.dfrkth8h/config.toml; respecting the opt-out
----------------------------------------------------------------------
Ran 273 tests in 67.199s

OK
dw hook: claude — 4 installed, 0 already present in /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.xd2v9syr/settings.json
dw hook: claude — 0 installed, 4 already present in /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.xd2v9syr/settings.json
dw hook: claude — 4 installed, 0 already present in /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.lpwek8l8/settings.json
dw hook: claude — 4 installed, 0 already present in /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.8qopj6l1/settings.json
dw hook: claude — 4 removed from /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.8qopj6l1/settings.json
dw hook: codex_hooks is explicitly false in /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.rbwegz3c/config.toml; respecting the opt-out
----------------------------------------------------------------------
Ran 273 tests in 61.376s

OK
dw hook: claude — 4 installed, 0 already present in /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.ge7safek/settings.json
dw hook: claude — 0 installed, 4 already present in /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.ge7safek/settings.json
dw hook: claude — 4 installed, 0 already present in /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.9dv4qmxu/settings.json
dw hook: claude — 4 installed, 0 already present in /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.48t152yg/settings.json
dw hook: claude — 4 removed from /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.48t152yg/settings.json
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
You should consider upgrading via the '/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/pmo-package-smoke.ItFYBy/appenv/bin/python -m pip install --upgrade pip' command.
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
commit     df17e5794ab0         trailers+archive+verify=ok
guided-status-loop.sh: ok (packaged CLI/MCP/HTTP recommendation sequence)
authorize 01 cli  review-workspace   -> review-workspace
authorize 02 mcp  generate-contract  -> certify-contract
refuse   bootstrap certification started=0 step_events=+0
refuse   bootstrap commit       started=0 step_events=+0
authorize 03 http start-story        -> continue-story
refuse   same-id stale token    started=0 step_events=+0
authorize 04 mcp  continue-story     -> continue-story
authorize 05 cli  finish-story       -> review-workspace
authorize 06 http review-workspace   -> review-workspace
authorize 07 cli  generate-contract  -> certify-contract
refuse   story certification    started=0 step_events=+0
refuse   story commit           started=0 step_events=+0
bootstrap  d47bc9d56c27         certification+commit=manual
commit     2727c4fc181b         trailers+archive+verify=ok
handoff    start-story        authorizations=7
deliberate-step-loop.sh: ok (fresh token per action; no argv reconstruction or consent shortcut)
package-smoke.sh: ok
{"adapter": "codex-exec", "artifact": "live-findings", "artifact_hash": "sha256:ee2270d22c9ab508ff4082d4943469e893b427346c72a854e46d1f1b5736fe5c", "checks": ["declared", "contained", "bytes", "markdown-sections", "citations"], "ledger_events": 3, "operator_tree_clean": true, "session_id": "session-c26c16b248e643a4ce5f4f0b", "state": "succeeded"}
codex-driver-smoke.sh: ok (authenticated read-only codex exec adapter)
bash: pmo-roadmap/roadmap-cli.sh: No such file or directory
```

### Captured run — 2026-07-18T05:39:59Z

- **Command:** `bash -o pipefail -c set -e
bash pmo-roadmap/tests/docs-lint.sh
bash pmo-roadmap/tests/docs-snippet-smoke.sh
bash pmo-roadmap/tests/canon-lint.sh
bash pmo-roadmap/tests/agent-surface.sh
python3 -m py_compile pmo-roadmap/lib/dw_pmo/orchestration_run.py pmo-roadmap/lib/dw_pmo/orchestration_driver.py
/usr/bin/python3 -m py_compile pmo-roadmap/lib/dw_pmo/orchestration_run.py pmo-roadmap/lib/dw_pmo/orchestration_driver.py
bash -n pmo-roadmap/tests/codex-driver-smoke.sh
.githooks/dw check
.githooks/dw rider docs --check
pmo-roadmap/update.sh . --check
git diff --check
git diff --cached --check`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** 27a7886952df4275f6f216df9d2f76956185b0dc

```text
docs-lint: ok (394 markdown files)
docs-lint.sh: ok (1s)
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
agent-surface.sh: ok
ERROR pmo-roadmap/pm/roadmap/work-log-automation/phase-24-bounded-orchestration/evidence-story-05.md: evidence exists but matching story is not done
```

### Captured run — 2026-07-18T05:40:36Z

- **Command:** `bash -o pipefail -c set -e
.githooks/dw check
.githooks/dw rider docs --check
pmo-roadmap/update.sh . --check
git diff --check
git diff --cached --check`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** ce0253a22137806390773f7727509d325b057c40

```text
dw check: ok
dw rider docs: all rendered surfaces match canon
update.sh: up to date (vendored rails match source v1.14.0)
```
