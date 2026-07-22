# Evidence - WLA-26-02

- **Story:** WLA-26-02 - Select work across a governed roadmap scope
- **Status:** done
- **Date:** 2026-07-22

## Proof

The delivered `dw program list|validate|simulate|plan` surface is a pure,
optional compiler/planner over one explicit local roadmap scope. An absent
`pm/programs/` directory returns a healthy empty inventory. Configured programs
resolve a closed program/workflow/organization/rubric family, reject invalid or
ambiguous scope and bindings, and separate layout-bearing document hashes from
layout-independent executable hashes.

`roadmap-frontier-v1` inventories every project story, explains out-of-scope,
done, held, blocked, dependency-bound, active, paused/closed-phase, and
frontier-stopped candidates, resumes one eligible active story, or selects the
first eligible story in the earliest incomplete scoped phase. The plan binds
branch, HEAD, index tree, Git operation, roadmap health/file hashes, policy and
reference hashes, workflow/rubric versions, requested policy ceilings, and the
local driver roster. Stable hash assignment produces a required implementer
and a different read-only verifier principal/workspace, with optional
meta-verifier, architect, and council policy visible in the derivation.

Every read document stamps `starts_work: false`; plans and simulations also
stamp policy, roadmap, run-state, and grant creation false. Twelve planner
tests cover the two-phase happy path, CLI/core byte parity, stable repeat
planning, layout/authority separation, scope exhaustion, multiple active work,
holds/blocks/dependencies, unknown and dangling references, ambiguous rules,
unsupported status, required-verifier and council failures, and the healthy
no-program case. The authoritative run below passed **356/356 core tests on
both Python floors**, the fresh-wheel package exam, docs and snippets, canon,
agent surfaces, roadmap health, rider and vendored parity, and diff hygiene.

## Manual review

- Inspected a two-phase plan with one completed story, one active story, one
  held story, one dependency-bound future story, and one blocked out-of-scope
  story. The active story was resumed and every other candidate carried a
  distinct reason.
- Inspected assignment derivation: declared pools were filtered by duty,
  driver capabilities, workspace mode, profile principal, and workspace
  domain before stable weighted hash ranking. The selected writer and verifier
  differed on both principal profile and workspace domain; optional
  meta-verifier and master-architect slots remained explicit.
- Moved layout data in the program, workflow, organization, and rubric. Source
  document hashes changed while semantic/reference/policy bundle hashes did
  not, preserving the visual-builder boundary.
- Repeated the plan at one observation and compared canonical bytes and the
  repository snapshot. No `.git/pmo-programs` store, grant, run state, policy,
  roadmap write, process, observer, or work start appeared.
- Installed the built wheel into a fresh empty repository and confirmed
  `program list` reported a healthy empty inventory while the established
  guided status, deliberate-step, orchestration, and outward-signal exams
  remained green.

## Captured runs

### Captured run — 2026-07-22T18:26:03Z

- **Command:** `bash -o pipefail -c set -e
python3 pmo-roadmap/tests/dw-core-tests.py -q
/usr/bin/python3 pmo-roadmap/tests/dw-core-tests.py -q
bash pmo-roadmap/tests/package-smoke.sh
bash pmo-roadmap/tests/docs-lint.sh
bash pmo-roadmap/tests/docs-snippet-smoke.sh
bash pmo-roadmap/tests/canon-lint.sh
bash pmo-roadmap/tests/agent-surface.sh
./.githooks/dw check work-log-automation
./.githooks/dw rider docs --check
pmo-roadmap/update.sh . --check
git diff --check
git diff --cached --check`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 453dbb99e70fd4da1c6e40faecc806075b82d3ad

```text
dw hook: codex_hooks is explicitly false in /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.iwn92s57/config.toml; respecting the opt-out
dw-workbench: 127.0.0.1 "GET /api/runs/run-5c7e717ebdd5a2b12440ce66/events?follow=0 HTTP/1.1" 200 -
dw-workbench: 127.0.0.1 "GET /api/runs/run-5c7e717ebdd5a2b12440ce66/events?follow=0 HTTP/1.1" 200 -
dw-workbench: 127.0.0.1 "POST /api/runs/run-5c7e717ebdd5a2b12440ce66/events HTTP/1.1" 405 -
dw-workbench: 127.0.0.1 "GET /api/signals/events?remote=origin&branch=sse-x&follow=0 HTTP/1.1" 200 -
dw-workbench: 127.0.0.1 "GET /api/runs/run-000000000000000000000000/events?follow=0 HTTP/1.1" 400 -
/opt/homebrew/Cellar/python@3.14/3.14.6/Frameworks/Python.framework/Versions/3.14/lib/python3.14/tempfile.py:484: ResourceWarning: Implicitly cleaning up <HTTPError 401: 'refused'>
  _warnings.warn(self.warn_message, ResourceWarning)
/opt/homebrew/Cellar/python@3.14/3.14.6/Frameworks/Python.framework/Versions/3.14/lib/python3.14/tempfile.py:484: ResourceWarning: Implicitly cleaning up <HTTPError 403: 'refused'>
  _warnings.warn(self.warn_message, ResourceWarning)
/opt/homebrew/Cellar/python@3.14/3.14.6/Frameworks/Python.framework/Versions/3.14/lib/python3.14/tempfile.py:484: ResourceWarning: Implicitly cleaning up <HTTPError 429: 'refused'>
  _warnings.warn(self.warn_message, ResourceWarning)
/opt/homebrew/Cellar/python@3.14/3.14.6/Frameworks/Python.framework/Versions/3.14/lib/python3.14/tempfile.py:484: ResourceWarning: Implicitly cleaning up <HTTPError 500: 'refused'>
  _warnings.warn(self.warn_message, ResourceWarning)
/opt/homebrew/Cellar/python@3.14/3.14.6/Frameworks/Python.framework/Versions/3.14/lib/python3.14/tempfile.py:484: ResourceWarning: Implicitly cleaning up <HTTPError 304: 'refused'>
  _warnings.warn(self.warn_message, ResourceWarning)
----------------------------------------------------------------------
Ran 356 tests in 173.604s

OK
dw hook: claude — 4 installed, 0 already present in /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.lg86jpt4/settings.json
dw hook: claude — 0 installed, 4 already present in /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.lg86jpt4/settings.json
dw hook: claude — 4 installed, 0 already present in /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.iga7fmx8/settings.json
dw hook: claude — 4 installed, 0 already present in /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.j0fm7lrp/settings.json
dw hook: claude — 4 removed from /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.j0fm7lrp/settings.json
dw hook: codex_hooks is explicitly false in /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.8f8wehm8/config.toml; respecting the opt-out
dw-workbench: 127.0.0.1 "GET /api/runs/run-98cea052a3ede5ac8d756e15/events?follow=0 HTTP/1.1" 200 -
dw-workbench: 127.0.0.1 "GET /api/runs/run-98cea052a3ede5ac8d756e15/events?follow=0 HTTP/1.1" 200 -
dw-workbench: 127.0.0.1 "POST /api/runs/run-98cea052a3ede5ac8d756e15/events HTTP/1.1" 405 -
dw-workbench: 127.0.0.1 "GET /api/signals/events?remote=origin&branch=sse-x&follow=0 HTTP/1.1" 200 -
dw-workbench: 127.0.0.1 "GET /api/runs/run-000000000000000000000000/events?follow=0 HTTP/1.1" 400 -
----------------------------------------------------------------------
Ran 356 tests in 167.699s

OK
dw hook: claude — 4 installed, 0 already present in /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.b7_2tjka/settings.json
dw hook: claude — 0 installed, 4 already present in /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.b7_2tjka/settings.json
dw hook: claude — 4 installed, 0 already present in /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.9f2nphkd/settings.json
dw hook: claude — 4 installed, 0 already present in /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.kwsnwojc/settings.json
dw hook: claude — 4 removed from /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.kwsnwojc/settings.json
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
You should consider upgrading via the '/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/pmo-package-smoke.QhTVjz/appenv/bin/python -m pip install --upgrade pip' command.
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
commit     39c77adf1880         trailers+archive+verify=ok
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
bootstrap  99990f6e99f2         certification+commit=manual
commit     cb9c70e9c418         trailers+archive+verify=ok
handoff    start-story        authorizations=7
deliberate-step-loop.sh: ok (fresh token per action; no argv reconstruction or consent shortcut)
{"artifact_count": 5, "checks": 2, "compiler_red_cases": 6, "duplicate_restarts": 0, "exam": "packaged multi-agent orchestration", "operator_commit": "4b1a118b1312a099eb7877115f39a1a161618559", "parallel_research": 2, "repair_visits": 1, "run_id": "run-e91d5e72572684593b9bc6d3", "runtime_red_cases": 5, "state": "awaiting-certification", "verify_all": "ok"}
{"certification": "operator-only", "duplicate_nudges": 0, "duplicate_starts": 0, "external_rebind": true, "kind": "delivery-workbench-packaged-outward-exam", "nudges": 2, "observer_side_effects": 0, "operator_push": "21dba05fc4567b23c8058910c6a8b19320924a80", "refusals": {"blocked-session": "non-receptive", "budget": "nudge-budget-exhausted", "revoked-request": "expired", "stale-correlation": "correlation-mismatch", "unknown-session": "non-receptive", "without-standing-grant": "no-standing-rule"}, "request_republishes": 1, "run_id": "run-af39046438b9d9ef3db9d7b8", "schema_version": 1, "state": "awaiting-certification", "stream_matches_ledger": true, "wheel_version": "dw 1.14.0"}
package-smoke.sh: ok
docs-lint: ok (434 markdown files)
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
dw check: ok
dw rider docs: all rendered surfaces match canon
update.sh: up to date (vendored rails match source v1.14.0)
```

### Captured run — 2026-07-22T18:35:44Z

- **Command:** `bash -o pipefail -c set -e
python3 pmo-roadmap/tests/dw-core-tests.py ProgramContractTest ProgramPlannerTest -q
/usr/bin/python3 pmo-roadmap/tests/dw-core-tests.py ProgramContractTest ProgramPlannerTest -q
bash pmo-roadmap/tests/docs-lint.sh
bash pmo-roadmap/tests/canon-lint.sh
./.githooks/dw check work-log-automation
./.githooks/dw rider docs --check
pmo-roadmap/update.sh . --check
git diff --check
git diff --cached --check`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** cb668b055a779a5871e3bde1437ed9072a9c0d5f

```text
----------------------------------------------------------------------
Ran 18 tests in 2.678s

OK
----------------------------------------------------------------------
Ran 18 tests in 2.514s

OK
docs-lint: ok (435 markdown files)
docs-lint.sh: ok (1s)
canon-lint.sh: ok
dw check: ok
dw rider docs: all rendered surfaces match canon
update.sh: up to date (vendored rails match source v1.14.0)
```
