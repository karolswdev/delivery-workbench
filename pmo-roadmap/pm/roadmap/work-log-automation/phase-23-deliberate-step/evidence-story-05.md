# Evidence - WLA-23-05

- **Story:** WLA-23-05 - Fresh-consumer deliberate-step exit exam
- **Status:** done
- **Date:** 2026-07-16

## Proof

### Captured run — 2026-07-16T15:24:47Z

- **Command:** `bash -o pipefail -c
set -e
run_tail() { "$@" 2>&1 | tail -n 10; }

python3 --version
/usr/bin/python3 --version
.tmp/phase23-py39-optional/bin/python -m pip show Pillow | rg '^(Name|Version):'
.tmp/phase23-holdspeak-v040/bin/python -m pip show holdspeak numpy | rg '^(Name|Version):'

python3 -m py_compile pmo-roadmap/bin/dw pmo-roadmap/bin/dw-workbench pmo-roadmap/bin/dw-mcp
python3 -m compileall -q pmo-roadmap/lib/dw_pmo
/usr/bin/python3 -m py_compile pmo-roadmap/bin/dw pmo-roadmap/bin/dw-workbench pmo-roadmap/bin/dw-mcp
/usr/bin/python3 -m compileall -q pmo-roadmap/lib/dw_pmo
run_tail python3 pmo-roadmap/tests/dw-core-tests.py
run_tail /usr/bin/python3 pmo-roadmap/tests/dw-core-tests.py

run_tail bash pmo-roadmap/tests/canon-lint.sh
run_tail bash pmo-roadmap/tests/docs-lint.sh
run_tail bash pmo-roadmap/tests/docs-snippet-smoke.sh
run_tail bash pmo-roadmap/tests/adoption-discovery.sh
run_tail bash pmo-roadmap/tests/agent-surface.sh
run_tail bash pmo-roadmap/tests/gate-parity.sh
run_tail bash pmo-roadmap/tests/roadmap-cli.sh
run_tail bash pmo-roadmap/tests/workbench-explorer.sh
run_tail bash pmo-roadmap/tests/workbench-ui-smoke.sh
run_tail bash pmo-roadmap/tests/mcp-server.sh
run_tail bash pmo-roadmap/tests/step-interop.sh
run_tail bash pmo-roadmap/tests/contributor-flow.sh
run_tail bash pmo-roadmap/tests/plugin-validate.sh
run_tail bash pmo-roadmap/tests/work-log-mvp.sh

bash pmo-roadmap/tests/package-smoke.sh 2>&1 | tail -n 70
run_tail bash pmo-roadmap/tests/upgrade-path.sh
run_tail bash pmo-roadmap/tests/verify-range.sh

.tmp/phase23-py39-optional/bin/python -m compileall -q integrations/telegram
run_tail .tmp/phase23-py39-optional/bin/python pmo-roadmap/tests/telegram-interface-tests.py
run_tail .tmp/phase23-py39-optional/bin/python pmo-roadmap/tests/telegram-fitness-tests.py
run_tail .tmp/phase23-holdspeak-v040/bin/python pmo-roadmap/tests/holdspeak-pack-tests.py

run_tail bash demos/scripts/prepare-onboarding-demo.sh
run_tail bash demos/scripts/prepare-commit-demo.sh
run_tail bash demos/scripts/capture-workbench-demo.sh --smoke
run_tail bash demos/scripts/render-social-preview.sh --smoke

node --check pmo-roadmap/workbench/app.js
node --check .githooks/workbench/app.js
pmo-roadmap/update.sh . --check
.githooks/dw rider docs --check
run_tail .githooks/dw check work-log-automation
run_tail .githooks/dw verify --all

bash -n   pmo-roadmap/bin/work-log-read   pmo-roadmap/bin/work-log-summarize   pmo-roadmap/bootstrap/adopt-project.sh   pmo-roadmap/bootstrap/new-project.sh   pmo-roadmap/bootstrap/session-intake.sh   pmo-roadmap/hooks/pre-commit   pmo-roadmap/hooks/commit-msg   pmo-roadmap/hooks/post-commit   pmo-roadmap/install.sh   pmo-roadmap/update.sh   pmo-roadmap/tests/adoption-discovery.sh   pmo-roadmap/tests/agent-surface.sh   pmo-roadmap/tests/canon-lint.sh   pmo-roadmap/tests/gate-parity.sh   pmo-roadmap/tests/roadmap-cli.sh   pmo-roadmap/tests/work-log-mvp.sh   pmo-roadmap/tests/workbench-explorer.sh   pmo-roadmap/tests/workbench-ui-smoke.sh   pmo-roadmap/tests/plugin-validate.sh   pmo-roadmap/tests/mcp-server.sh   pmo-roadmap/tests/step-interop.sh   pmo-roadmap/tests/contributor-flow.sh   pmo-roadmap/tests/guided-status-loop.sh   pmo-roadmap/tests/deliberate-step-loop.sh   pmo-roadmap/tests/package-smoke.sh   pmo-roadmap/tests/brew-formula-smoke.sh   pmo-roadmap/tests/upgrade-path.sh   pmo-roadmap/tests/verify-range.sh   pmo-roadmap/tests/docs-lint.sh   pmo-roadmap/tests/docs-snippet-smoke.sh   demos/scripts/prepare-onboarding-demo.sh   demos/scripts/prepare-commit-demo.sh   demos/scripts/capture-workbench-demo.sh   demos/scripts/render-social-preview.sh

shellcheck -e SC2317   pmo-roadmap/install.sh   pmo-roadmap/update.sh   pmo-roadmap/hooks/pre-commit   pmo-roadmap/hooks/commit-msg   pmo-roadmap/hooks/post-commit   pmo-roadmap/bin/work-log-read   pmo-roadmap/bin/work-log-summarize   pmo-roadmap/bootstrap/adopt-project.sh   pmo-roadmap/bootstrap/new-project.sh   pmo-roadmap/bootstrap/session-intake.sh   pmo-roadmap/tests/adoption-discovery.sh   pmo-roadmap/tests/agent-surface.sh   pmo-roadmap/tests/canon-lint.sh   pmo-roadmap/tests/gate-parity.sh   pmo-roadmap/tests/roadmap-cli.sh   pmo-roadmap/tests/work-log-mvp.sh   pmo-roadmap/tests/workbench-explorer.sh   pmo-roadmap/tests/workbench-ui-smoke.sh   pmo-roadmap/tests/plugin-validate.sh   pmo-roadmap/tests/mcp-server.sh   pmo-roadmap/tests/step-interop.sh   pmo-roadmap/tests/contributor-flow.sh   pmo-roadmap/tests/guided-status-loop.sh   pmo-roadmap/tests/deliberate-step-loop.sh   pmo-roadmap/tests/package-smoke.sh   pmo-roadmap/tests/brew-formula-smoke.sh   pmo-roadmap/tests/upgrade-path.sh   pmo-roadmap/tests/verify-range.sh   pmo-roadmap/tests/docs-lint.sh   pmo-roadmap/tests/docs-snippet-smoke.sh   demos/scripts/prepare-onboarding-demo.sh   demos/scripts/prepare-commit-demo.sh   demos/scripts/capture-workbench-demo.sh   demos/scripts/render-social-preview.sh

if git grep -nE '[0-9]{6,}:[A-Za-z0-9_-]{30,}' -- ':!*.png' ':!*.gif'; then
  echo 'ERROR: bot-token-shaped string tracked in the repo' >&2
  exit 1
fi
if git ls-files | grep -E '(^|/)telegram\.json$'; then
  echo 'ERROR: operator telegram config tracked in the repo' >&2
  exit 1
fi
if git ls-files | grep -E '(^|/)(telegram-state\.json|agent-events\.jsonl|\.env|.*\.pem|id_rsa)$'; then
  echo 'ERROR: a secret-shaped file is tracked in the repo' >&2
  exit 1
fi
echo 'credential grep-clean: ok'

if brew list --formula delivery-workbench >/dev/null 2>&1; then
  echo 'homebrew smoke: abstained locally because the operator formula is installed; clean-machine macOS CI remains wired'
else
  run_tail bash pmo-roadmap/tests/brew-formula-smoke.sh
fi

git diff --check
git diff --cached --check
`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** d2b8b96a8446acbc9c9ada81e83d68f7efc2479a

```text
Python 3.14.6
Python 3.9.6
Name: pillow
Version: 11.3.0
Name: holdspeak
Version: 0.4.0
Name: numpy
Version: 2.5.1

----------------------------------------------------------------------
Ran 230 tests in 24.567s

OK
dw hook: claude — 4 installed, 0 already present in /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.ut5ry2pv/settings.json
dw hook: claude — 0 installed, 4 already present in /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.ut5ry2pv/settings.json
dw hook: claude — 4 installed, 0 already present in /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.igbfr7ox/settings.json
dw hook: claude — 4 installed, 0 already present in /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.nb_g6tdf/settings.json
dw hook: claude — 4 removed from /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.nb_g6tdf/settings.json

----------------------------------------------------------------------
Ran 230 tests in 23.304s

OK
dw hook: claude — 4 installed, 0 already present in /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.dqswxlz9/settings.json
dw hook: claude — 0 installed, 4 already present in /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.dqswxlz9/settings.json
dw hook: claude — 4 installed, 0 already present in /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.72ij5d2c/settings.json
dw hook: claude — 4 installed, 0 already present in /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.t82dhxig/settings.json
dw hook: claude — 4 removed from /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.t82dhxig/settings.json
canon-lint.sh: ok
docs-lint: ok (377 markdown files)
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
adoption-discovery.sh: ok
agent-surface.sh: ok
gate-parity.sh: ok
roadmap-cli.sh: ok
dw-workbench: writes require /api/mutations preview→apply or an exact /api/step/apply token; never stages, certifies, or commits
dw-workbench: shutting down
dw-workbench: serving /private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/pmo-workbench-test.P5KDf6/installed
dw-workbench: http://127.0.0.1:19699/ (localhost or your own .ts.net tailnet; Ctrl-C to stop)
dw-workbench: writes require /api/mutations preview→apply or an exact /api/step/apply token; never stages, certifies, or commits
workbench-explorer.sh: ok
dw-workbench: shutting down
dw-workbench: serving /private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/pmo-workbench-test.P5KDf6/repo
dw-workbench: http://127.0.0.1:19698/ (localhost or your own .ts.net tailnet; Ctrl-C to stop)
dw-workbench: writes require /api/mutations preview→apply or an exact /api/step/apply token; never stages, certifies, or commits
workbench-ui-smoke.sh: ok (20 viewport renders: 8 views + attention + ambiguity, desktop+mobile)
dw-workbench: shutting down
dw-workbench: serving /private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/pmo-ui-smoke.zkhepJ/repo
dw-workbench: http://127.0.0.1:21684/ (localhost or your own .ts.net tailnet; Ctrl-C to stop)
dw-workbench: writes require /api/mutations preview→apply or an exact /api/step/apply token; never stages, certifies, or commits
protocol exchange: ok (9 replies)
no-rails refusal: ok
mutation walk: ok (done-without-evidence refused; contract stamped, certification manual)
gate still blocks uncertified commits: ok
MCP/CLI byte-parity (timestamps normalized): ok
mcp-server.sh: ok
preview parity: CLI = MCP = HTTP
result parity:  CLI = MCP = HTTP
replay/injection: refused without another child
certification/commit: previewable, never applicable
step-interop.sh: ok
red 1b: forced two-flip squash lands and dw verify names atomicity
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✓ The system accepted your understanding of the project management framework.
  Contract acknowledged (7/7 checkboxes).
  Stories shipped this commit: 1 (evidence verified by dw gate).
  Commit proceeding.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
pmo-roadmap post-commit: contract archived to .git/pmo-contract-archive/be955d7353ab2cd231506fe383cfd36405460707
red 2: fixup squash displaces trailers mid-body and dw verify names trailer-missing
contributor-flow.sh: ok
plugin manifests: ok (version 1.14.0, 4 commands, 1 skill)
claude plugin validate: ok
plugin-validate.sh: ok
pmo-roadmap post-commit: work log appended to /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T//pmo-work-log-test.EiiozA/work-log/2026-07-16/demo-2145037123-work-summary.log
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✓ The system accepted your understanding of the project management framework.
  Contract acknowledged (1/1 checkboxes).
  Work log payload captured for post-commit finalization.
  Commit proceeding.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
pmo-roadmap post-commit: contract archived to .git/pmo-contract-archive/cfc00cfa020715026c57dc1c6f5cb3f1b4ce40ae
pmo-roadmap post-commit: work log appended to /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T//pmo-work-log-test.EiiozA/work-log/2026-07-16/demo-2145037123-work-summary.log
work-log-mvp.sh: ok
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
You should consider upgrading via the '/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/pmo-package-smoke.C4EJhp/appenv/bin/python -m pip install --upgrade pip' command.
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
commit     b7ebcc947fbd         trailers+archive+verify=ok
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
bootstrap  54410f36caa5         certification+commit=manual
commit     2c4040312749         trailers+archive+verify=ok
handoff    start-story        authorizations=7
deliberate-step-loop.sh: ok (fresh token per action; no argv reconstruction or consent shortcut)
package-smoke.sh: ok
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
pmo-roadmap post-commit: contract archived to .git/pmo-contract-archive/6d6460f20a19ee3db06299714dad2f9b1285df7a
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✓ The system accepted your understanding of the project management framework.
  Contract acknowledged (7/7 checkboxes).
  Stories shipped this commit: 1 (evidence verified by dw gate).
  Commit proceeding.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
pmo-roadmap post-commit: contract archived to .git/pmo-contract-archive/56e381d1c79610c39ffaa2ca2989cfded67e264f
upgrade-path.sh: ok
  Commit proceeding.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
pmo-roadmap post-commit: contract archived to .git/pmo-contract-archive/35cb06307640cfd2a34f4331de5a6f668904659b
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✓ The system accepted your understanding of the project management framework.
  Contract acknowledged (7/7 checkboxes).
  Commit proceeding.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
pmo-roadmap post-commit: contract archived to .git/pmo-contract-archive/aace09c2776f6e422d124db9b8fbb989dc7751ab
verify-range.sh: ok
test_unbind_repo_cascades_to_session (__main__.TopicRouterTest) ... ok
test_bind_then_commands_scope_to_the_topic (__main__.TopicScopingTest) ... ok
test_flat_chat_still_uses_active_repo (__main__.TopicScopingTest) ... ok
test_replies_land_in_the_originating_topic (__main__.TopicScopingTest) ... ok
test_unbound_topic_has_no_repo (__main__.TopicScopingTest) ... ok

----------------------------------------------------------------------
Ran 147 tests in 9.435s

OK (skipped=1)
test_layering_catches_a_planted_violation_in_a_new_leaf (__main__.FitnessSelfTest) ... ok
test_leaves_stay_leaves (__main__.ImportLayeringTest) ... ok
test_no_import_cycles (__main__.ImportLayeringTest) ... ok
test_rails_seam_is_reached_only_through_the_interface (__main__.ImportLayeringTest) ... ok
test_transport_is_a_pure_leaf (__main__.ImportLayeringTest) ... ok

----------------------------------------------------------------------
Ran 10 tests in 0.159s

OK
test_empty_transcript_is_failure_shape (__main__.PackUnitTest.test_empty_transcript_is_failure_shape) ... ok
test_hallucinated_story_id_is_demoted_to_drift (__main__.PackUnitTest.test_hallucinated_story_id_is_demoted_to_drift) ... ok
test_no_roadmap_resolvable_fails_before_llm (__main__.PackUnitTest.test_no_roadmap_resolvable_fails_before_llm) ... ok
test_success_grounds_real_story_ids (__main__.PackUnitTest.test_success_grounds_real_story_ids) ... ok
test_unparseable_response_is_failure_shape (__main__.PackUnitTest.test_unparseable_response_is_failure_shape) ... ok

----------------------------------------------------------------------
Ran 23 tests in 9.866s

OK
Prepared onboarding demo repo:
  /tmp/delivery-workbench-onboarding-demo
Prepared commit-gate demo repo:
  /tmp/delivery-workbench-commit-demo
Work-log root:
  /tmp/delivery-workbench-work-log
capture-workbench-demo.sh: ok
  /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T//dw-workbench-demo.OANWIc/rendered/workbench-tour.gif
  /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T//dw-workbench-demo.OANWIc/assets/workbench-overview.png
  /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T//dw-workbench-demo.OANWIc/assets/workbench-trace.png
  /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T//dw-workbench-demo.OANWIc/assets/workbench-editor.png
dw-workbench: shutting down
dw-workbench: serving /private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-workbench-demo.OANWIc/repo
dw-workbench: http://127.0.0.1:23771/ (localhost or your own .ts.net tailnet; Ctrl-C to stop)
dw-workbench: writes require /api/mutations preview→apply or an exact /api/step/apply token; never stages, certifies, or commits
render-social-preview.sh: ok
  /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T//dw-social-preview.eorBlx/assets/social-preview.png
update.sh: up to date (vendored rails match source v1.14.0)
dw rider docs: all rendered surfaces match canon
dw check: ok
dw verify: ok (128 commits verified, 17 pre-epoch skipped)
credential grep-clean: ok
homebrew smoke: abstained locally because the operator formula is installed; clean-machine macOS CI remains wired
```

## Exit-exam assertions

The package leg reused the CLI installed from its just-built Python 3.9 wheel
inside a disposable consumer. It compared a fresh preview over CLI, MCP, and
HTTP before every authorization, then supplied only `project` and the opaque
token to the chosen adapter. The harness never executes or reconstructs the
status object's argv.

```text
authorize 01 cli  review-workspace
authorize 02 mcp  generate-contract
refuse      all  bootstrap certification and commit (started=0, events=+0)
authorize 03 http start-story
refuse      all  same-action stale token (started=0, events=+0)
authorize 04 mcp  continue-story
authorize 05 cli  finish-story
authorize 06 http review-workspace
authorize 07 cli  generate-contract
refuse      all  story certification and commit (started=0, events=+0)
handoff          start-story (seven separately authorized actions)
```

The stale fixture changed the real workspace while the next action remained
`continue-story`. That changed the complete-observation token. CLI, MCP, and
HTTP all returned the same refusal document; the runner, claim directory,
tracked state, and `step_execution` event count stayed unchanged. A new token
then advanced normally. Certification and both commits were performed by the
fixture operator outside the step capability. The final story commit carried
the required trailers, archived its checked contract under the full commit
SHA, and passed history verification.

## Full matrix observed on this checkout

| Obligation | Result |
|---|---|
| Core and Python floor | 230/230 passed on Python 3.14.6 and 230/230 on Python 3.9.6; CLI/workbench/MCP compile and package bytecode checks passed |
| Deliberate-step contract | Seven fresh authorizations, same-id stale refusal with zero starts/events, replay and argv injection refusal, and manual-only certification/commit passed |
| Distribution | Python 3.9 built the v1.14.0 sdist and wheel; the wheel-installed guided-status and deliberate-step consumer exams both reached trailered, archived, verified commits |
| CLI / MCP / HTTP | Exact preview/result core-document parity passed; MCP protocol, route/tool inventories, and guarded mutation walk passed |
| Browser and assets | Workbench integration passed; Firefox produced 20 viewport renders (eight views plus attention and ambiguity, desktop and mobile); demo capture and social rendering smokes passed |
| Agent and shell surfaces | Agent rider, plugin, adoption, roadmap, gate, contribution, work-log, Bash parse, ShellCheck, generated-rider drift, and vendored-source drift checks passed |
| Optional integrations | Telegram passed 147 interface tests on Python 3.9 + Pillow and 10 architecture-fitness tests; pinned HoldSpeak v0.4.0 + NumPy passed 23/23 |
| Docs and history | 377 Markdown files plus executable snippets passed; v1.5.0 upgrade and history-range fixtures passed; pre-close `dw verify --all` verified 128 commits and skipped 17 documented pre-epoch commits |
| Homebrew | Local smoke abstained because the operator formula is installed and the test will not uninstall it; the clean-machine macOS CI leg remains wired |

The captured battery exited 0. The Homebrew row is an explicit environment
limitation, not a green local claim. No version bump, tag, package upload,
release, or formula mutation is part of this story.
