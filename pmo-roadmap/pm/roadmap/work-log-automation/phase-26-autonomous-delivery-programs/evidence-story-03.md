# Evidence - WLA-26-03

- **Story:** WLA-26-03 - Compile reusable hierarchical workflows and bounded loops
- **Status:** done
- **Date:** 2026-07-22

## Proof

### Implementation and review

- `dw workflow list`, `validate`, and `simulate` use one pure compiler over
  tracked direct-contained JSON policy; an absent `pm/workflows/` is valid and
  repeated simulation creates no repository or runtime state.
- The compiler closes eleven node kinds and emits stable namespaced node,
  artifact, and role addresses, exact source/subflow provenance, deterministic
  fan-out/fan-in waves, typed routes, and per-node plus whole-workflow finite
  envelopes.
- Bindings accept only declared typed literals, parent parameters, context, or
  node-input artifacts. They cannot substitute structural fields such as node
  kinds, commands, capabilities, paths, routes, checks, limits, or providers.
- Red-path fixtures refuse missing or mismatched subflow hashes, recursive
  hierarchy, dependency and backward-route cycles, non-result predicates,
  missing loop bounds/exhaustion routes, excessive nesting or symbolic size,
  capability smuggling, and workflow envelopes beyond program budgets.
- Review confirmed that layout-only edits change document hashes but preserve
  semantic and bound-instance hashes, including inside nested subflows.
- Phase 24 orchestration remains an explicit `bounded_run` leaf whose immutable
  score hash and budgets are pinned. No legacy score is inferred, rewritten,
  or activated by program planning.
- The wheel contains exactly the optional `docs-only`,
  `research-build-verify`, and `architect-debate-delivery` templates. Install
  and update do not create consumer workflow policy; package smoke copies each
  example explicitly before installed-CLI validation and simulation.
- The architect template exercises a bounded propose/critique/rebuttal/judge
  debate, nested delivery subflow, and finite audit loop; the research template
  names a separate verifier and explicit bounded Phase 24 score.

### Acceptance mapping

- Typed non-structural binding: `ProgramWorkflowTest` binding and structural
  substitution refusal cases.
- Exact subflow provenance and lineage: nested compilation, hash mismatch,
  recursion, namespaced role/artifact, and nested-layout hash cases.
- Finite loops and envelopes: loop/debate predicate, ceiling, exhaustion,
  resource-lock, and budget-intersection cases.
- Legible pure simulation and refusal routes: CLI inventory/template round-trip
  and package-installed simulation cases.
- Phase 24 compatibility: explicit bounded-score leaf and package regression
  exam.
- Three shipped organizations: wheel-content and installed-template smoke.

### Captured run — 2026-07-22T19:14:27Z

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
- **Index-tree:** b05db4ad23839807dc8046ac055154c7d030e1fe

```text
dw hook: codex_hooks is explicitly false in /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.a5mtlwat/config.toml; respecting the opt-out
dw-workbench: 127.0.0.1 "GET /api/runs/run-ad82fdae3fab5848385b00f4/events?follow=0 HTTP/1.1" 200 -
dw-workbench: 127.0.0.1 "GET /api/runs/run-ad82fdae3fab5848385b00f4/events?follow=0 HTTP/1.1" 200 -
dw-workbench: 127.0.0.1 "POST /api/runs/run-ad82fdae3fab5848385b00f4/events HTTP/1.1" 405 -
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
Ran 369 tests in 176.664s

OK
dw hook: claude — 4 installed, 0 already present in /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.c6sh0_xf/settings.json
dw hook: claude — 0 installed, 4 already present in /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.c6sh0_xf/settings.json
dw hook: claude — 4 installed, 0 already present in /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.m98xjg5x/settings.json
dw hook: claude — 4 installed, 0 already present in /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.aorepyf2/settings.json
dw hook: claude — 4 removed from /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.aorepyf2/settings.json
dw hook: codex_hooks is explicitly false in /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test._8803wnf/config.toml; respecting the opt-out
dw-workbench: 127.0.0.1 "GET /api/runs/run-116a63380ece5a63b8269ee6/events?follow=0 HTTP/1.1" 200 -
dw-workbench: 127.0.0.1 "GET /api/runs/run-116a63380ece5a63b8269ee6/events?follow=0 HTTP/1.1" 200 -
dw-workbench: 127.0.0.1 "POST /api/runs/run-116a63380ece5a63b8269ee6/events HTTP/1.1" 405 -
dw-workbench: 127.0.0.1 "GET /api/signals/events?remote=origin&branch=sse-x&follow=0 HTTP/1.1" 200 -
dw-workbench: 127.0.0.1 "GET /api/runs/run-000000000000000000000000/events?follow=0 HTTP/1.1" 400 -
----------------------------------------------------------------------
Ran 369 tests in 169.774s

OK
dw hook: claude — 4 installed, 0 already present in /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.sr3n56g5/settings.json
dw hook: claude — 0 installed, 4 already present in /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.sr3n56g5/settings.json
dw hook: claude — 4 installed, 0 already present in /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.l37adgzc/settings.json
dw hook: claude — 4 installed, 0 already present in /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.nghap8jl/settings.json
dw hook: claude — 4 removed from /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.nghap8jl/settings.json
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
You should consider upgrading via the '/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/pmo-package-smoke.r8UImu/appenv/bin/python -m pip install --upgrade pip' command.
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
commit     5c9e6f805193         trailers+archive+verify=ok
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
bootstrap  2dea5df441b9         certification+commit=manual
commit     3c884b72588b         trailers+archive+verify=ok
handoff    start-story        authorizations=7
deliberate-step-loop.sh: ok (fresh token per action; no argv reconstruction or consent shortcut)
{"artifact_count": 5, "checks": 2, "compiler_red_cases": 6, "duplicate_restarts": 0, "exam": "packaged multi-agent orchestration", "operator_commit": "855ab55e41ff54642c52c2629171d6e65e397a1f", "parallel_research": 2, "repair_visits": 1, "run_id": "run-dbbf981862f6b0b7a3f2cdb6", "runtime_red_cases": 5, "state": "awaiting-certification", "verify_all": "ok"}
{"certification": "operator-only", "duplicate_nudges": 0, "duplicate_starts": 0, "external_rebind": true, "kind": "delivery-workbench-packaged-outward-exam", "nudges": 2, "observer_side_effects": 0, "operator_push": "a4873938f6df80306dc2206b191c7e81f6e756ad", "refusals": {"blocked-session": "non-receptive", "budget": "nudge-budget-exhausted", "revoked-request": "expired", "stale-correlation": "correlation-mismatch", "unknown-session": "non-receptive", "without-standing-grant": "no-standing-rule"}, "request_republishes": 1, "run_id": "run-f8bfbc6ed6c56f9dd00c9672", "schema_version": 1, "state": "awaiting-certification", "stream_matches_ledger": true, "wheel_version": "dw 1.14.0"}
package-smoke.sh: ok
docs-lint: ok (435 markdown files)
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

### Captured run — 2026-07-22T19:23:57Z

- **Command:** `bash -o pipefail -c set -e
python3 pmo-roadmap/tests/dw-core-tests.py ProgramContractTest ProgramPlannerTest ProgramWorkflowTest -q
/usr/bin/python3 pmo-roadmap/tests/dw-core-tests.py ProgramContractTest ProgramPlannerTest ProgramWorkflowTest -q
bash pmo-roadmap/tests/docs-lint.sh
bash pmo-roadmap/tests/canon-lint.sh
./.githooks/dw check work-log-automation
./.githooks/dw rider docs --check
pmo-roadmap/update.sh . --check
git diff --check
git diff --cached --check`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** cb26aecdf14be4d7263c1e2be84b284828be6e00

```text
----------------------------------------------------------------------
Ran 31 tests in 2.996s

OK
----------------------------------------------------------------------
Ran 31 tests in 2.841s

OK
docs-lint: ok (436 markdown files)
docs-lint.sh: ok (0s)
canon-lint.sh: ok
dw check: ok
dw rider docs: all rendered surfaces match canon
update.sh: up to date (vendored rails match source v1.14.0)
```
