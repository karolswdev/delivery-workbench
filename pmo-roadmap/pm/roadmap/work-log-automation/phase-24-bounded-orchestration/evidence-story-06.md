# Evidence - WLA-24-06

- **Story:** WLA-24-06 - Schedule nodes, checks, failure routes, and recovery
- **Status:** done
- **Date:** 2026-07-18

## Proof

### Result interpretation

- The same staged tree passed 287 tests on the current interpreter and Python
  3.9.6. The 14 conductor scenarios on each runtime cover pure stable ordering,
  concurrency/resource exclusion, parallel research→validated synthesis,
  implementation→failed check→repair→exact source retry, repair/retry
  exhaustion, unsupported authority, agent/check budgets, expiry, pause,
  approval/rejection, abort, cancellation, terminal handoff, and external
  commit observation.
- Planted crashes after claim, provider start, artifact collection, and check
  completion recover from the ledger plus persistent executor receipt without
  a second launch. A cross-process cancellation test records `run_cancelled`
  before terminating a live check process group, releases the claim truthfully,
  and schedules nothing else.
- Command checks execute exact score argv without a shell in contained
  grant-HEAD/predecessor worktrees. Bounded snapshots catch undeclared writes
  without dirtying the operator tree; file, JSON-schema, diff-scope, and
  rail-status built-ins share the receipt contract. Fresh declared rail acts
  consume `dw step`; stale acts and permanent certification/commit exclusions
  remain non-started.
- Package smoke built wheel and sdist, installed a fresh consumer, found the
  conductor module, imported `schedule_decision`/`tick_run`/`supervise_run`,
  and retained the existing deliberate-step packaged exam. Documentation,
  snippets, canon, generated agent surfaces, dual-runtime compilation, and
  source/vendor parity all closed green.

### Captured run — 2026-07-18T06:27:47Z

- **Command:** `bash -o pipefail -c set -e
python3 pmo-roadmap/tests/dw-core-tests.py -q
/usr/bin/python3 pmo-roadmap/tests/dw-core-tests.py -q
bash pmo-roadmap/tests/package-smoke.sh
bash pmo-roadmap/tests/docs-lint.sh
bash pmo-roadmap/tests/docs-snippet-smoke.sh
bash pmo-roadmap/tests/canon-lint.sh
bash pmo-roadmap/tests/agent-surface.sh
python3 -m py_compile pmo-roadmap/lib/dw_pmo/orchestration_run.py pmo-roadmap/lib/dw_pmo/orchestration_driver.py pmo-roadmap/lib/dw_pmo/orchestration_conductor.py pmo-roadmap/bin/dw
/usr/bin/python3 -m py_compile pmo-roadmap/lib/dw_pmo/orchestration_run.py pmo-roadmap/lib/dw_pmo/orchestration_driver.py pmo-roadmap/lib/dw_pmo/orchestration_conductor.py pmo-roadmap/bin/dw
pmo-roadmap/update.sh . --check
.githooks/dw rider docs --check
git diff --check
git diff --cached --check`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 91c50f8aab0bc3a0c3d4414fa46fe2530cdcb5b7

```text
dw hook: codex_hooks is explicitly false in /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.pahy8pc4/config.toml; respecting the opt-out
----------------------------------------------------------------------
Ran 287 tests in 105.325s

OK
dw hook: claude — 4 installed, 0 already present in /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.33lhse3j/settings.json
dw hook: claude — 0 installed, 4 already present in /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.33lhse3j/settings.json
dw hook: claude — 4 installed, 0 already present in /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.owhuxspu/settings.json
dw hook: claude — 4 installed, 0 already present in /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.mcktzagi/settings.json
dw hook: claude — 4 removed from /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.mcktzagi/settings.json
dw hook: codex_hooks is explicitly false in /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.f36_66rp/config.toml; respecting the opt-out
----------------------------------------------------------------------
Ran 287 tests in 95.094s

OK
dw hook: claude — 4 installed, 0 already present in /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.y5abk3ws/settings.json
dw hook: claude — 0 installed, 4 already present in /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.y5abk3ws/settings.json
dw hook: claude — 4 installed, 0 already present in /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.tgta5ouf/settings.json
dw hook: claude — 4 installed, 0 already present in /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.itxz3njz/settings.json
dw hook: claude — 4 removed from /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.itxz3njz/settings.json
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
You should consider upgrading via the '/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/pmo-package-smoke.6q8AVu/appenv/bin/python -m pip install --upgrade pip' command.
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
commit     c3efe1272b0b         trailers+archive+verify=ok
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
bootstrap  385282234ee8         certification+commit=manual
commit     f790f38369bb         trailers+archive+verify=ok
handoff    start-story        authorizations=7
deliberate-step-loop.sh: ok (fresh token per action; no argv reconstruction or consent shortcut)
package-smoke.sh: ok
docs-lint: ok (394 markdown files)
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
agent-surface.sh: ok
update.sh: up to date (vendored rails match source v1.14.0)
dw rider docs: all rendered surfaces match canon
```

### Captured run — 2026-07-18T06:33:18Z

- **Command:** `bash -o pipefail -c set -e
.githooks/dw check
.githooks/dw rider docs --check
pmo-roadmap/update.sh . --check
git diff --check
git diff --cached --check`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 7067695c0fc78c6d681c644640f726f6b4780fe9

```text
dw check: ok
dw rider docs: all rendered surfaces match canon
update.sh: up to date (vendored rails match source v1.14.0)
```
