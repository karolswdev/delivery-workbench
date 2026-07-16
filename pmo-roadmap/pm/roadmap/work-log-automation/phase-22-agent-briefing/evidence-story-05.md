# Evidence - WLA-22-05

- **Story:** WLA-22-05 - Prove the guided loop in a fresh consumer
- **Status:** done
- **Date:** 2026-07-15

## Proof

### Captured run — 2026-07-16T02:00:25Z

- **Command:** `bash -o pipefail -c
set -e
run_tail() { "$@" 2>&1 | tail -n 4; }
run_tail /usr/bin/python3 pmo-roadmap/tests/dw-core-tests.py
run_tail pmo-roadmap/tests/canon-lint.sh
run_tail pmo-roadmap/tests/docs-lint.sh
run_tail pmo-roadmap/tests/docs-snippet-smoke.sh
run_tail pmo-roadmap/tests/adoption-discovery.sh
run_tail pmo-roadmap/tests/agent-surface.sh
run_tail pmo-roadmap/tests/gate-parity.sh
run_tail pmo-roadmap/tests/roadmap-cli.sh
run_tail pmo-roadmap/tests/workbench-explorer.sh
run_tail pmo-roadmap/tests/workbench-ui-smoke.sh
run_tail pmo-roadmap/tests/mcp-server.sh
run_tail pmo-roadmap/tests/contributor-flow.sh
run_tail pmo-roadmap/tests/plugin-validate.sh
run_tail pmo-roadmap/tests/work-log-mvp.sh
pmo-roadmap/tests/package-smoke.sh 2>&1 | tail -n 28
run_tail pmo-roadmap/tests/upgrade-path.sh
run_tail pmo-roadmap/tests/verify-range.sh
run_tail python3 pmo-roadmap/tests/telegram-interface-tests.py
run_tail python3 pmo-roadmap/tests/telegram-fitness-tests.py
run_tail pmo-roadmap/bin/dw check work-log-automation
run_tail pmo-roadmap/bin/dw verify --all
bash -n pmo-roadmap/tests/guided-status-loop.sh pmo-roadmap/tests/package-smoke.sh
shellcheck pmo-roadmap/tests/guided-status-loop.sh pmo-roadmap/tests/package-smoke.sh
git diff --check
`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 3e113e27195b2426f2cd146542025e23c39b73d8

```text
dw hook: claude — 0 installed, 4 already present in /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.wiiynzkz/settings.json
dw hook: claude — 4 installed, 0 already present in /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.b4lakzzg/settings.json
dw hook: claude — 4 installed, 0 already present in /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.vu6irnfc/settings.json
dw hook: claude — 4 removed from /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.vu6irnfc/settings.json
canon-lint.sh: ok
docs-lint: ok (364 markdown files)
docs-lint.sh: ok (0s)
ok: pmo-roadmap/README.md snippet 'intake-no-prompt' ran as printed
ok: pmo-roadmap/README.md snippet 'adopt-close-loop' ran as printed
docs-lint snippets: ok
docs-snippet-smoke.sh: ok
adoption-discovery.sh: ok
agent-surface.sh: ok
gate-parity.sh: ok
roadmap-cli.sh: ok
dw-workbench: shutting down
dw-workbench: serving /private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/pmo-workbench-test.DE7QvV/repo
dw-workbench: http://127.0.0.1:18392/ (localhost or your own .ts.net tailnet; Ctrl-C to stop)
dw-workbench: writes happen only via /api/mutations preview→apply inside pm/roadmap; never commits
dw-workbench: shutting down
dw-workbench: serving /private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/pmo-ui-smoke.EdtJsO/repo
dw-workbench: http://127.0.0.1:21512/ (localhost or your own .ts.net tailnet; Ctrl-C to stop)
dw-workbench: writes happen only via /api/mutations preview→apply inside pm/roadmap; never commits
mutation walk: ok (done-without-evidence refused; contract stamped, certification manual)
gate still blocks uncertified commits: ok
MCP/CLI byte-parity (timestamps normalized): ok
mcp-server.sh: ok
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
pmo-roadmap post-commit: contract archived to .git/pmo-contract-archive/71542d7cf40e6523d8a07a8c5bf429e46d1c8c6d
red 2: fixup squash displaces trailers mid-body and dw verify names trailer-missing
contributor-flow.sh: ok
plugin manifests: ok (version 1.14.0, 4 commands, 1 skill)
claude plugin validate: ok
plugin-validate.sh: ok
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
pmo-roadmap post-commit: contract archived to .git/pmo-contract-archive/fa5acca448b4b377264616f2c50dd400919b9076
pmo-roadmap post-commit: work log appended to /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T//pmo-work-log-test.hACTAA/work-log/2026-07-15/demo-111031837-work-summary.log
work-log-mvp.sh: ok
* Building wheel...
warning: no previously-included files matching '__pycache__/*' found anywhere in distribution
warning: no previously-included files matching '*.pyc' found anywhere in distribution
package-smoke.sh: built delivery_workbench-1.14.0-py3-none-any.whl and delivery_workbench-1.14.0.tar.gz
package-smoke.sh: pipx cannot create environments here; falling back to venv+pip
WARNING: You are using pip version 21.2.4; however, version 26.0.1 is available.
You should consider upgrading via the '/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/pmo-package-smoke.ihQ80o/appenv/bin/python -m pip install --upgrade pip' command.
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
commit     497458625226         trailers+archive+verify=ok
guided-status-loop.sh: ok (packaged CLI/MCP/HTTP recommendation sequence)
package-smoke.sh: ok
  Commit proceeding.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
pmo-roadmap post-commit: contract archived to .git/pmo-contract-archive/94cb986a236fa0af7a124fbd68ddd55efa0eb2e6
upgrade-path.sh: ok
  Commit proceeding.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
pmo-roadmap post-commit: contract archived to .git/pmo-contract-archive/831f7b7a212475999f59e9d18c6194adc95522b6
verify-range.sh: ok
----------------------------------------------------------------------
Ran 147 tests in 9.410s

OK (skipped=9)
----------------------------------------------------------------------
Ran 10 tests in 0.124s

OK
dw check: ok
dw verify: ok (123 commits verified, 17 pre-epoch skipped)
```

## Exit-exam assertions

The package-smoke leg reused the CLI installed from its just-built Python
3.9 wheel. Its nested fresh consumer asserted the complete sequence below;
each row is the byte-equal CLI JSON, MCP `structuredContent`, and HTTP
envelope `data` object observed before the action was executed:

```text
ready     review-workspace
ready     generate-contract
ready     certify-contract     (manual; command=null)
ready     commit               (live gate pass)
ready     start-story
ready     continue-story
attention repair-roadmap       (planted done-without-evidence red path)
ready     continue-story
ready     continue-story       (real work present)
attention finish-story         (captured evidence; guarded done argv)
ready     review-workspace
ready     generate-contract
ready     certify-contract     (manual; command=null)
ready     generate-contract    (restaged index made contract stale)
ready     certify-contract     (manual; command=null)
ready     commit               (live gate pass)
ready     start-story          (clean tree; follow-up remains)
```

Every parity read snapshotted tracked-file hashes, NUL-safe Git porcelain,
and `.git/pmo-events.jsonl` before and after; all were byte-identical. The
fixture commit `497458625226…` carried `PMO-Story` and
`PMO-Contract-Digest` trailers, had a checked contract archived under its
full commit SHA, passed `dw verify --all`, and was disposable with the
temporary consumer. No fixture state or external repository was changed.

## Full matrix observed on this checkout

| Obligation | Result |
|---|---|
| Core and declared floor | 221/221 on the local interpreter and 221/221 on `/usr/bin/python3` 3.9.6; compile and bytecode checks passed |
| Status red paths | guarded done without evidence refused; planted missing evidence returned blocking `repair-roadmap`; stale contract returned `generate-contract --force`; neither returned `commit` |
| CLI / MCP / HTTP | exact status-object parity at every guided transition; MCP protocol and mutation walk green; 13-tool inventory remains pinned |
| Browser | explorer/API integration green; 18 Firefox renders (seven views plus attention and ambiguity, desktop and mobile) green; the Phase-22 front-door images were visually inspected |
| Shell and docs | every shipped shell parsed; ShellCheck green; canon, links/anchors/images, executable snippets, adoption, agent lifecycle, roadmap CLI, gate parity, contribution, plugin, and work-log suites green |
| Distribution and history | sdist + wheel built on Python 3.9; packaged install/update and defer-to-repo green; v1.5.0→current upgrade green; range fixtures green; pre-close history verified 123 commits with 17 pre-epoch skips |
| Telegram | 147 interface tests green in Python 3.9 with Pillow; one Python-3.11-only `tomllib` lock abstained on the declared floor; 10/10 architecture-fitness tests green |
| HoldSpeak | 23/23 passed under Python 3.13 with pinned HoldSpeak v0.4.0 installed `--no-deps` plus NumPy, matching the CI job |
| Homebrew | local smoke deliberately refused because the user's formula is already installed; no uninstall was performed; the clean-machine macOS CI leg remains wired |

The full captured battery exited 0. The Homebrew line is an explicit local
environment limitation, not a green claim. Release narrative is prepared in
`CHANGELOG.md` under **Unreleased**; v1.14.0 remains unchanged and no tag,
push, release, package upload, or formula mutation was performed.
