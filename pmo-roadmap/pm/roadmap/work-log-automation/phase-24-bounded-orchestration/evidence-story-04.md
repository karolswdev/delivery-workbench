# Evidence - WLA-24-04

- **Story:** WLA-24-04 - Authorize runs with grants and an append-only ledger
- **Status:** done
- **Date:** 2026-07-17

## Proof

`dw_pmo.orchestration_run` now supplies the local consent and audit layer that
the visual score deliberately lacks. A pure plan expands the complete grant
before approval; an exact single-use token plus explicit operator identity
atomically captures immutable plan/compiled-score/grant documents and the
first hash-chained event. Every later control or claim is serialized across
processes, compares a fresh ledger head, replays the complete chain, and
refuses on stale repository/status/story facts, expiry, revocation, tamper,
idempotency reuse, or a finite budget.

### Captured run — 2026-07-18T05:01:24Z

- **Command:** `bash -o pipefail -c set -e
python3 pmo-roadmap/tests/dw-core-tests.py -q
/usr/bin/python3 pmo-roadmap/tests/dw-core-tests.py -q
bash pmo-roadmap/tests/package-smoke.sh
bash pmo-roadmap/tests/roadmap-cli.sh
bash pmo-roadmap/tests/docs-lint.sh
bash pmo-roadmap/tests/docs-snippet-smoke.sh
bash pmo-roadmap/tests/canon-lint.sh
bash pmo-roadmap/tests/agent-surface.sh
python3 -m py_compile pmo-roadmap/bin/dw pmo-roadmap/lib/dw_pmo/orchestration_run.py
/usr/bin/python3 -m py_compile pmo-roadmap/bin/dw pmo-roadmap/lib/dw_pmo/orchestration_run.py
.githooks/dw run --help
.githooks/dw check work-log-automation
.githooks/dw rider docs --check
pmo-roadmap/update.sh . --check
git diff --check
git diff --cached --check`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** e72e154c5e2faad3c287f613b0cd98cd4d8e7cce

```text
dw hook: codex_hooks is explicitly false in /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.3o4i86wn/config.toml; respecting the opt-out
----------------------------------------------------------------------
Ran 262 tests in 45.143s

OK
dw hook: claude — 4 installed, 0 already present in /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.6ffdkgwq/settings.json
dw hook: claude — 0 installed, 4 already present in /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.6ffdkgwq/settings.json
dw hook: claude — 4 installed, 0 already present in /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.mparrisy/settings.json
dw hook: claude — 4 installed, 0 already present in /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.kvhhtr4r/settings.json
dw hook: claude — 4 removed from /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.kvhhtr4r/settings.json
dw hook: codex_hooks is explicitly false in /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.j8bxw6ix/config.toml; respecting the opt-out
----------------------------------------------------------------------
Ran 262 tests in 42.436s

OK
dw hook: claude — 4 installed, 0 already present in /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.gyosez_a/settings.json
dw hook: claude — 0 installed, 4 already present in /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.gyosez_a/settings.json
dw hook: claude — 4 installed, 0 already present in /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.p09th6xu/settings.json
dw hook: claude — 4 installed, 0 already present in /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.p79bue10/settings.json
dw hook: claude — 4 removed from /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.p79bue10/settings.json
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
You should consider upgrading via the '/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/pmo-package-smoke.gRsFuS/appenv/bin/python -m pip install --upgrade pip' command.
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
commit     e4ffe27365f1         trailers+archive+verify=ok
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
bootstrap  1b12f3151930         certification+commit=manual
commit     c14ae6fbf779         trailers+archive+verify=ok
handoff    start-story        authorizations=7
deliberate-step-loop.sh: ok (fresh token per action; no argv reconstruction or consent shortcut)
package-smoke.sh: ok
roadmap-cli.sh: ok
docs-lint: ok (392 markdown files)
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
usage: dw run [-h] {plan,start,list,show,pause,resume,revoke,cancel} ...

positional arguments:
  {plan,start,list,show,pause,resume,revoke,cancel}
    plan                pure preview over an exact score, story, repository
                        state, grant, and expiry
    start               atomically create one grant from an exact fresh plan
                        and explicit approval
    list                list projections replayed from local run ledgers
    show                replay and show one authoritative run projection
    pause               append one exact pause transition
    resume              append one exact resume transition
    revoke              append one exact revoke transition
    cancel              append one exact cancel transition

options:
  -h, --help            show this help message and exit
dw check: ok
dw rider docs: all rendered surfaces match canon
update.sh: up to date (vendored rails match source v1.14.0)
```

## Manual diagnostic review

- Inspected the human `dw run plan` rendering and confirmed the exact semantic
  hash, branch/HEAD, in-progress story, expiry, profiles, capabilities,
  workspace modes, every finite budget, permanent exclusions, and start token
  are visible before approval; the same document states `starts-work false`.
- Inspected a started run directory and confirmed `plan.json`, `score.json`,
  and `grant.json` are immutable, `ledger.jsonl` begins with one chained
  `run_started` event, and `projection.json` can be deleted or forged without
  changing replay.
- Raced two processes over the same start token and two more over the same
  node-attempt/idempotency claim. Exactly one process won each race; the loser
  appended nothing. Pause blocked a new claim immediately while the prior
  in-flight claim could still record a bounded cancellation outcome.
- Planted an unknown plan field, capability expansion, changed score/HEAD,
  symlinked store, expired grant, reused token/key, oversized artifact charge,
  forked chain, and truncated final line. Each failed closed without a second
  run, claim, or transition.
