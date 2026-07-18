# Evidence - WLA-24-01

- **Story:** WLA-24-01 - Contract the visual score and orchestration authority
- **Status:** done
- **Date:** 2026-07-17

## Proof

The reviewed contract in `docs/orchestration.md` fixes the product claim,
canonical score, visual editor, grant, ledger, driver, workspace, scheduling,
failure, recovery, privacy, and terminal-authority boundaries before those
components acquire behavior. The phase plan breaks implementation into seven
ordered, independently provable stories and keeps the compiler/runtime/editor
work visibly outstanding.

### Captured run — 2026-07-18T02:48:39Z

- **Command:** `bash -o pipefail -c
set -e
python3 pmo-roadmap/tests/dw-core-tests.py -q
/usr/bin/python3 pmo-roadmap/tests/dw-core-tests.py -q
bash pmo-roadmap/tests/docs-lint.sh
bash pmo-roadmap/tests/docs-snippet-smoke.sh
bash pmo-roadmap/tests/canon-lint.sh
bash pmo-roadmap/tests/agent-surface.sh
.githooks/dw check work-log-automation
.githooks/dw rider docs --check
pmo-roadmap/update.sh . --check
rg -q 'Delivery Workbench \*\*can coordinate\*\*' docs/orchestration.md
rg -q '^## Rich visual score editor' docs/orchestration.md
rg -q 'parallel research agents' docs/orchestration.md
rg -q 'output conventions' docs/orchestration.md
rg -q 'Failure policy is data' docs/orchestration.md
rg -q '^## Run grant' docs/orchestration.md
rg -q '^## Threat model and fail checks' docs/orchestration.md
test "$(rg -c '^\| WLA-24-' pmo-roadmap/pm/roadmap/work-log-automation/phase-24-bounded-orchestration/current-phase-status.md)" -eq 8
git diff --check
git diff --cached --check
`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** c529b55d81c8c2aeeed41a72d08ef43ad744a39f

```text
dw hook: codex_hooks is explicitly false in /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.m0a1fx9p/config.toml; respecting the opt-out
----------------------------------------------------------------------
Ran 230 tests in 26.108s

OK
dw hook: claude — 4 installed, 0 already present in /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.azfmkg91/settings.json
dw hook: claude — 0 installed, 4 already present in /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.azfmkg91/settings.json
dw hook: claude — 4 installed, 0 already present in /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.6akluzf3/settings.json
dw hook: claude — 4 installed, 0 already present in /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.kjrb4_mi/settings.json
dw hook: claude — 4 removed from /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.kjrb4_mi/settings.json
dw hook: codex_hooks is explicitly false in /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.qjb_hv0o/config.toml; respecting the opt-out
----------------------------------------------------------------------
Ran 230 tests in 24.579s

OK
dw hook: claude — 4 installed, 0 already present in /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.3uo2t34a/settings.json
dw hook: claude — 0 installed, 4 already present in /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.3uo2t34a/settings.json
dw hook: claude — 4 installed, 0 already present in /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.0jyps6x8/settings.json
dw hook: claude — 4 installed, 0 already present in /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.hxms9x43/settings.json
dw hook: claude — 4 removed from /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.hxms9x43/settings.json
docs-lint: ok (389 markdown files)
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

## Manual review

- Walked the representative research fan-out → synthesis → implementation →
  exact check → failure/repair → approval flow and confirmed that every rule
  shown by the proposed editor has a canonical score field and runtime owner.
- Confirmed that saving a score grants no authority, provider and secret
  details stay operator-local, writable agents receive isolated workspaces,
  and successful coordination terminates at `awaiting-certification` rather
  than certifying or committing.
