# Evidence - WLA-26-01

- **Story:** WLA-26-01 - Contract autonomous delivery programs and trust
- **Status:** done
- **Date:** 2026-07-22

## Proof

The reviewed contract in `docs/programs.md` fixes the optional program layer
before runtime work begins. It preserves vanilla Delivery Workbench and one
bounded score/run as complete independent modes, introduces four closed policy
kinds that compile into one immutable bundle, defines deterministic
`roadmap-frontier-v1` selection, and makes general cycles impossible while
supporting typed finite subflow, repair, review, debate, and audit loops.

The trust model assigns the verifier before implementation and proves
independence on locally resolved principal/workspace identity rather than
display names. Mechanical facts, individual judgments, council judgments, and
meta-verdicts are separate types. Fifteen capabilities are independent granted
bits, all continuous budgets are finite, thirty-two refusal codes are closed,
and the threat table covers default-mode creep through duplicate destructive
acts and UI/runtime drift. Six structural core tests pin those decisions.

The authoritative captured run below passed **344/344 core tests on both
Python floors**, docs links and executable snippets, canon, agent surfaces,
roadmap health, rider parity, vendored-rail parity, and diff hygiene.

## Manual review

- Walked a no-program install and ordinary status/next/step/evidence/gate/
  Workbench route: the contract requires compatible behavior and zero program
  store, process, observer, stream, notification, network, or setup effects.
- Walked one bounded Phase 24 score: it reaches its terminal handoff and cannot
  acquire a scope, next-story selection, program grant, or continuation unless
  an explicit program references it as a strict-subset child leaf.
- Walked a continuous two-phase route: pure plan selects the earliest frontier,
  assigns implementer and independent verifier, exact grant starts work, failed
  verification enters one finite repair loop, fresh verification and optional
  council/meta/architect gates pass, then evidence, integration, certification,
  commit, push, story completion, and phase advancement consume separate
  capabilities and receipts.
- Walked crash, stale verdict, unresolved dissent, architect veto, exhausted
  round budget, integration conflict, remote divergence, and revocation paths:
  each maps to one closed refusal/terminal route and none can silently skip work
  or repeat an uncertain destructive act.

## Captured runs

### Captured run — 2026-07-22T17:47:25Z

- **Command:** `bash -o pipefail -c set -e
python3 pmo-roadmap/tests/dw-core-tests.py -q
/usr/bin/python3 pmo-roadmap/tests/dw-core-tests.py -q
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
- **Index-tree:** 95316bf58a4f9ff9308c5a3b408dbf194ce9d07f

```text
dw hook: codex_hooks is explicitly false in /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.k5l1a3yf/config.toml; respecting the opt-out
dw-workbench: 127.0.0.1 "GET /api/runs/run-6c431c650ef14f454e4d34bd/events?follow=0 HTTP/1.1" 200 -
dw-workbench: 127.0.0.1 "GET /api/runs/run-6c431c650ef14f454e4d34bd/events?follow=0 HTTP/1.1" 200 -
dw-workbench: 127.0.0.1 "POST /api/runs/run-6c431c650ef14f454e4d34bd/events HTTP/1.1" 405 -
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
Ran 344 tests in 175.360s

OK
dw hook: claude — 4 installed, 0 already present in /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.y88949ef/settings.json
dw hook: claude — 0 installed, 4 already present in /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.y88949ef/settings.json
dw hook: claude — 4 installed, 0 already present in /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.sg_zb06p/settings.json
dw hook: claude — 4 installed, 0 already present in /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.q2srkz63/settings.json
dw hook: claude — 4 removed from /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.q2srkz63/settings.json
dw hook: codex_hooks is explicitly false in /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.pov_bo1h/config.toml; respecting the opt-out
dw-workbench: 127.0.0.1 "GET /api/runs/run-9e7b56c1ddeb8594337583c2/events?follow=0 HTTP/1.1" 200 -
dw-workbench: 127.0.0.1 "GET /api/runs/run-9e7b56c1ddeb8594337583c2/events?follow=0 HTTP/1.1" 200 -
dw-workbench: 127.0.0.1 "POST /api/runs/run-9e7b56c1ddeb8594337583c2/events HTTP/1.1" 405 -
dw-workbench: 127.0.0.1 "GET /api/signals/events?remote=origin&branch=sse-x&follow=0 HTTP/1.1" 200 -
dw-workbench: 127.0.0.1 "GET /api/runs/run-000000000000000000000000/events?follow=0 HTTP/1.1" 400 -
----------------------------------------------------------------------
Ran 344 tests in 166.085s

OK
dw hook: claude — 4 installed, 0 already present in /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.s3y7g3uw/settings.json
dw hook: claude — 0 installed, 4 already present in /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.s3y7g3uw/settings.json
dw hook: claude — 4 installed, 0 already present in /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.aogw296z/settings.json
dw hook: claude — 4 installed, 0 already present in /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.494a_p0g/settings.json
dw hook: claude — 4 removed from /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.494a_p0g/settings.json
docs-lint: ok (433 markdown files)
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

### Captured run — 2026-07-22T17:55:49Z

- **Command:** `bash -o pipefail -c set -e
python3 pmo-roadmap/tests/dw-core-tests.py ProgramContractTest -q
bash pmo-roadmap/tests/docs-lint.sh
bash pmo-roadmap/tests/canon-lint.sh
./.githooks/dw check work-log-automation
./.githooks/dw rider docs --check
pmo-roadmap/update.sh . --check
git diff --check
git diff --cached --check`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** f2be7a81231c0ae46a0c6cfe09c5b4add56246b8

```text
----------------------------------------------------------------------
Ran 6 tests in 0.001s

OK
docs-lint: ok (434 markdown files)
docs-lint.sh: ok (0s)
canon-lint.sh: ok
dw check: ok
dw rider docs: all rendered surfaces match canon
update.sh: up to date (vendored rails match source v1.14.0)
```
