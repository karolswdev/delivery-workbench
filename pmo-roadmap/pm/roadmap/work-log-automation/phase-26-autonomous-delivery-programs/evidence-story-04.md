# Evidence - WLA-26-04

- **Story:** WLA-26-04 - Model agent roles, teams, and separation of duties
- **Status:** done
- **Date:** 2026-07-22

## Proof

### Implementation and review

- `program_organization.py` is one pure compiler for tracked logical agents,
  pools, teams, exact role slots, capability/workspace/context/artifact packet
  policy, schemas, concurrency/resources, independence, councils, and finite
  replacement. Unknown or missing structural fields refuse with source-aware
  diagnostics.
- `dw organization list|validate|simulate` shares that core. Repeated reads are
  byte-stable and create no policy, principal, session, grant, or run state; an
  absent `pm/organizations/` directory is healthy.
- Each continuous team statically requires one singleton implementer and one
  required verifier that names the implementer as an independence prerequisite
  and judgment subject. Logical-pool feasibility is proven before local driver
  discovery.
- Local driver profiles now expose only non-secret availability, principal,
  adapter/version, concurrency, isolation, capability, principal fingerprint,
  and adapter-capability fingerprint. Review confirmed no command, model,
  credential, token, password, prompt, or executable enters an assignment.
- Program planning intersects workflow role lanes with program, role,
  logical-agent, and driver ceilings. The assignment receipt fixes each
  role/slot, packet visibility, effective child ceiling, candidate/exclusion,
  session-binding key, and principal/workspace/session separation fact before
  dispatch.
- Colliding logical aliases that resolve to one principal, one workspace
  domain, or insufficient concurrency refuse. A read-only verifier profile
  with repository-write capability also refuses rather than relying on a
  prompt to abstain from writing.
- Council proof expands role cardinality into distinct assigned principals,
  checks quorum, and serializes shared resource groups into deterministic
  waves. The fixture gives critics proposal-only context while the master
  architect receives the declared roadmap/evidence view.
- Replacement preview accepts only closed declared reasons, chooses only a
  declared fallback candidate, increments generation, creates a new session
  binding, preserves the complete earlier lineage/dissent, invalidates stale
  work and verdicts, keeps capability unchanged, and takes the exact exhaustion
  route after the finite count.
- The wheel contains `autonomous-story-cell.json`, but package install/update
  leaves `pm/organizations/` absent. Package smoke explicitly copies the
  example before installed-CLI validation and simulation.

### Acceptance mapping

- Required implementer/verifier and session-level separation: planner fixture,
  logical feasibility, local-principal collision, and separation-fact cases.
- Closed role/child policy: workflow-lane capability, workspace, context,
  artifact, schema, resource, and program-authority intersection cases.
- Deterministic explained assignment: stable repeated plan, unavailable primary
  fallback, roster/adapter fingerprint, and no-secret serialization cases.
- Finite honest replacement: successful generation-two replacement plus
  preserved lineage/dissent, invalidation, unchanged ceiling, and exhausted
  route cases.
- Requested refusal matrix: council cardinality, architect visibility,
  restricted critic context, resource conflicts, unavailable pools, colliding
  identities, and capability downgrade/smuggling cases.

### Captured run — 2026-07-22T19:56:57Z

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
- **Index-tree:** 7b7526fe2183d3f059ddb76c1ada8a28d1387300

```text
dw hook: codex_hooks is explicitly false in /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.8yu_3a45/config.toml; respecting the opt-out
dw-workbench: 127.0.0.1 "GET /api/runs/run-70c491c9718ff048c6d2d625/events?follow=0 HTTP/1.1" 200 -
dw-workbench: 127.0.0.1 "GET /api/runs/run-70c491c9718ff048c6d2d625/events?follow=0 HTTP/1.1" 200 -
dw-workbench: 127.0.0.1 "POST /api/runs/run-70c491c9718ff048c6d2d625/events HTTP/1.1" 405 -
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
Ran 378 tests in 187.246s

OK
dw hook: claude — 4 installed, 0 already present in /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.vky9qwku/settings.json
dw hook: claude — 0 installed, 4 already present in /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.vky9qwku/settings.json
dw hook: claude — 4 installed, 0 already present in /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.i78vg_c1/settings.json
dw hook: claude — 4 installed, 0 already present in /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.2dyb91we/settings.json
dw hook: claude — 4 removed from /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.2dyb91we/settings.json
dw hook: codex_hooks is explicitly false in /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.pyt91u94/config.toml; respecting the opt-out
dw-workbench: 127.0.0.1 "GET /api/runs/run-d83c62dcb79f55378454e167/events?follow=0 HTTP/1.1" 200 -
dw-workbench: 127.0.0.1 "GET /api/runs/run-d83c62dcb79f55378454e167/events?follow=0 HTTP/1.1" 200 -
dw-workbench: 127.0.0.1 "POST /api/runs/run-d83c62dcb79f55378454e167/events HTTP/1.1" 405 -
dw-workbench: 127.0.0.1 "GET /api/signals/events?remote=origin&branch=sse-x&follow=0 HTTP/1.1" 200 -
dw-workbench: 127.0.0.1 "GET /api/runs/run-000000000000000000000000/events?follow=0 HTTP/1.1" 400 -
----------------------------------------------------------------------
Ran 378 tests in 185.020s

OK
dw hook: claude — 4 installed, 0 already present in /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.glw1trlv/settings.json
dw hook: claude — 0 installed, 4 already present in /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.glw1trlv/settings.json
dw hook: claude — 4 installed, 0 already present in /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.3jl9qdnj/settings.json
dw hook: claude — 4 installed, 0 already present in /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.lliyrz4w/settings.json
dw hook: claude — 4 removed from /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.lliyrz4w/settings.json
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
You should consider upgrading via the '/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/pmo-package-smoke.id6Ev4/appenv/bin/python -m pip install --upgrade pip' command.
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
commit     f01ee9842be3         trailers+archive+verify=ok
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
bootstrap  8c0ce6164799         certification+commit=manual
commit     958ebfa84b90         trailers+archive+verify=ok
handoff    start-story        authorizations=7
deliberate-step-loop.sh: ok (fresh token per action; no argv reconstruction or consent shortcut)
{"artifact_count": 5, "checks": 2, "compiler_red_cases": 6, "duplicate_restarts": 0, "exam": "packaged multi-agent orchestration", "operator_commit": "cac20aeb7b33dff306083027c17d0c22a7f61e15", "parallel_research": 2, "repair_visits": 1, "run_id": "run-4ba5fbf2e0bb5c7dbde8b6d1", "runtime_red_cases": 5, "state": "awaiting-certification", "verify_all": "ok"}
{"certification": "operator-only", "duplicate_nudges": 0, "duplicate_starts": 0, "external_rebind": true, "kind": "delivery-workbench-packaged-outward-exam", "nudges": 2, "observer_side_effects": 0, "operator_push": "b191593ede2485cfec6d95df1c1da7cd735cdb31", "refusals": {"blocked-session": "non-receptive", "budget": "nudge-budget-exhausted", "revoked-request": "expired", "stale-correlation": "correlation-mismatch", "unknown-session": "non-receptive", "without-standing-grant": "no-standing-rule"}, "request_republishes": 1, "run_id": "run-fb24d1a8642301524e320fb7", "schema_version": 1, "state": "awaiting-certification", "stream_matches_ledger": true, "wheel_version": "dw 1.14.0"}
package-smoke.sh: ok
docs-lint: ok (436 markdown files)
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

### Captured run — 2026-07-22T20:08:39Z

- **Command:** `bash -o pipefail -c set -e
python3 pmo-roadmap/tests/dw-core-tests.py ProgramContractTest ProgramPlannerTest ProgramOrganizationTest ProgramWorkflowTest -q
/usr/bin/python3 pmo-roadmap/tests/dw-core-tests.py ProgramContractTest ProgramPlannerTest ProgramOrganizationTest ProgramWorkflowTest -q
bash pmo-roadmap/tests/docs-lint.sh
bash pmo-roadmap/tests/canon-lint.sh
./.githooks/dw check work-log-automation
./.githooks/dw rider docs --check
pmo-roadmap/update.sh . --check
git diff --check
git diff --cached --check`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 01d2c0a39479cc92b2d2d19c9a7e91e54730799a

```text
----------------------------------------------------------------------
Ran 40 tests in 4.531s

OK
----------------------------------------------------------------------
Ran 40 tests in 5.224s

OK
docs-lint: ok (437 markdown files)
docs-lint.sh: ok (1s)
canon-lint.sh: ok
dw check: ok
dw rider docs: all rendered surfaces match canon
update.sh: up to date (vendored rails match source v1.14.0)
```
