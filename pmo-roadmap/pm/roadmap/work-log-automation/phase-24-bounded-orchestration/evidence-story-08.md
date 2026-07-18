# Evidence - WLA-24-08

- **Story:** WLA-24-08 - Prove a packaged multi-agent orchestration
- **Status:** done
- **Date:** 2026-07-18

## Proof

### Captured run — 2026-07-18T08:22:20Z

- **Command:** `bash -o pipefail -c
set -e

run_tail() {
  "$@" 2>&1 | tail -n 12
}

python3 --version
/usr/bin/python3 --version
.tmp/phase23-py39-optional/bin/python -m pip show Pillow | rg "^(Name|Version):"
.tmp/phase23-holdspeak-v040/bin/python -m pip show holdspeak numpy | rg "^(Name|Version):"

python3 -m py_compile pmo-roadmap/bin/dw pmo-roadmap/bin/dw-workbench pmo-roadmap/bin/dw-mcp pmo-roadmap/tests/orchestration-packaged-exam.py
python3 -m compileall -q pmo-roadmap/lib/dw_pmo
/usr/bin/python3 -m py_compile pmo-roadmap/bin/dw pmo-roadmap/bin/dw-workbench pmo-roadmap/bin/dw-mcp pmo-roadmap/tests/orchestration-packaged-exam.py
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
run_tail bash pmo-roadmap/tests/orchestration-interop.sh
run_tail bash pmo-roadmap/tests/contributor-flow.sh
run_tail bash pmo-roadmap/tests/plugin-validate.sh
run_tail bash pmo-roadmap/tests/work-log-mvp.sh
run_tail bash pmo-roadmap/tests/deliberate-step-loop.sh
run_tail bash pmo-roadmap/tests/guided-status-loop.sh

bash pmo-roadmap/tests/package-smoke.sh 2>&1 | tail -n 110
run_tail env DW_CODEX_DRIVER_LIVE=1 bash pmo-roadmap/tests/codex-driver-smoke.sh
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

shell_files=(
  pmo-roadmap/bin/work-log-read
  pmo-roadmap/bin/work-log-summarize
  pmo-roadmap/bootstrap/adopt-project.sh
  pmo-roadmap/bootstrap/new-project.sh
  pmo-roadmap/bootstrap/session-intake.sh
  pmo-roadmap/hooks/pre-commit
  pmo-roadmap/hooks/commit-msg
  pmo-roadmap/hooks/post-commit
  pmo-roadmap/install.sh
  pmo-roadmap/update.sh
  pmo-roadmap/tests/adoption-discovery.sh
  pmo-roadmap/tests/agent-surface.sh
  pmo-roadmap/tests/canon-lint.sh
  pmo-roadmap/tests/gate-parity.sh
  pmo-roadmap/tests/roadmap-cli.sh
  pmo-roadmap/tests/work-log-mvp.sh
  pmo-roadmap/tests/workbench-explorer.sh
  pmo-roadmap/tests/workbench-ui-smoke.sh
  pmo-roadmap/tests/plugin-validate.sh
  pmo-roadmap/tests/mcp-server.sh
  pmo-roadmap/tests/step-interop.sh
  pmo-roadmap/tests/orchestration-interop.sh
  pmo-roadmap/tests/codex-driver-smoke.sh
  pmo-roadmap/tests/contributor-flow.sh
  pmo-roadmap/tests/guided-status-loop.sh
  pmo-roadmap/tests/deliberate-step-loop.sh
  pmo-roadmap/tests/package-smoke.sh
  pmo-roadmap/tests/brew-formula-smoke.sh
  pmo-roadmap/tests/upgrade-path.sh
  pmo-roadmap/tests/verify-range.sh
  pmo-roadmap/tests/docs-lint.sh
  pmo-roadmap/tests/docs-snippet-smoke.sh
  demos/scripts/prepare-onboarding-demo.sh
  demos/scripts/prepare-commit-demo.sh
  demos/scripts/capture-workbench-demo.sh
  demos/scripts/render-social-preview.sh
)
bash -n "${shell_files[@]}"
shellcheck -e SC2317 "${shell_files[@]}"

if git grep -nE "[0-9]{6,}:[A-Za-z0-9_-]{30,}" -- ":!*.png" ":!*.gif"; then
  echo "ERROR: bot-token-shaped string tracked in the repo" >&2
  exit 1
fi
if git ls-files | grep -E "(^|/)telegram\.json$"; then
  echo "ERROR: operator telegram config tracked in the repo" >&2
  exit 1
fi
if git ls-files | grep -E "(^|/)(telegram-state\.json|agent-events\.jsonl|\.env|.*\.pem|id_rsa)$"; then
  echo "ERROR: a secret-shaped file is tracked in the repo" >&2
  exit 1
fi
echo "credential grep-clean: ok"

if brew list --formula delivery-workbench >/dev/null 2>&1; then
  echo "homebrew smoke: abstained locally because the operator formula is installed; clean-machine macOS CI remains wired"
else
  run_tail bash pmo-roadmap/tests/brew-formula-smoke.sh
fi

git diff --check
git diff --cached --check
`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** b54379be612d19cdfd7393a8efaf0deae56eb69b

```text
Python 3.14.6
Python 3.9.6
Name: pillow
Version: 11.3.0
Name: holdspeak
Version: 0.4.0
Name: numpy
Version: 2.5.1
test_render_grammar (__main__.VerifyTest.test_render_grammar) ... ok
test_smuggled_flip_names_missing_trailer_and_evidence (__main__.VerifyTest.test_smuggled_flip_names_missing_trailer_and_evidence) ... ok

----------------------------------------------------------------------
Ran 297 tests in 110.930s

OK
dw hook: claude — 4 installed, 0 already present in /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.m8ouzcid/settings.json
dw hook: claude — 0 installed, 4 already present in /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.m8ouzcid/settings.json
dw hook: claude — 4 installed, 0 already present in /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.hfwcnugy/settings.json
dw hook: claude — 4 installed, 0 already present in /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.oh78wzsf/settings.json
dw hook: claude — 4 removed from /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.oh78wzsf/settings.json
test_render_grammar (__main__.VerifyTest) ... ok
test_smuggled_flip_names_missing_trailer_and_evidence (__main__.VerifyTest) ... ok

----------------------------------------------------------------------
Ran 297 tests in 103.809s

OK
dw hook: claude — 4 installed, 0 already present in /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.pawk7duw/settings.json
dw hook: claude — 0 installed, 4 already present in /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.pawk7duw/settings.json
dw hook: claude — 4 installed, 0 already present in /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test._etgjr5x/settings.json
dw hook: claude — 4 installed, 0 already present in /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.q95rnob5/settings.json
dw hook: claude — 4 removed from /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.q95rnob5/settings.json
canon-lint.sh: ok
ERROR pmo-roadmap/pm/roadmap/work-log-automation/phase-24-bounded-orchestration/final-summary.md:113: broken link: ./evidence-story-08.md
ERROR pmo-roadmap/pm/roadmap/work-log-automation/phase-24-bounded-orchestration/final-summary.md:178: broken link: ./evidence-story-08.md
```

### Captured run — 2026-07-18T08:27:00Z

- **Command:** `bash -o pipefail -c
set -e

run_tail() {
  "$@" 2>&1 | tail -n 12
}

python3 --version
/usr/bin/python3 --version
.tmp/phase23-py39-optional/bin/python -m pip show Pillow | rg "^(Name|Version):"
.tmp/phase23-holdspeak-v040/bin/python -m pip show holdspeak numpy | rg "^(Name|Version):"

python3 -m py_compile pmo-roadmap/bin/dw pmo-roadmap/bin/dw-workbench pmo-roadmap/bin/dw-mcp pmo-roadmap/tests/orchestration-packaged-exam.py
python3 -m compileall -q pmo-roadmap/lib/dw_pmo
/usr/bin/python3 -m py_compile pmo-roadmap/bin/dw pmo-roadmap/bin/dw-workbench pmo-roadmap/bin/dw-mcp pmo-roadmap/tests/orchestration-packaged-exam.py
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
run_tail bash pmo-roadmap/tests/orchestration-interop.sh
run_tail bash pmo-roadmap/tests/contributor-flow.sh
run_tail bash pmo-roadmap/tests/plugin-validate.sh
run_tail bash pmo-roadmap/tests/work-log-mvp.sh
run_tail bash pmo-roadmap/tests/deliberate-step-loop.sh
run_tail bash pmo-roadmap/tests/guided-status-loop.sh

bash pmo-roadmap/tests/package-smoke.sh 2>&1 | tail -n 110
run_tail env DW_CODEX_DRIVER_LIVE=1 bash pmo-roadmap/tests/codex-driver-smoke.sh
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

shell_files=(
  pmo-roadmap/bin/work-log-read
  pmo-roadmap/bin/work-log-summarize
  pmo-roadmap/bootstrap/adopt-project.sh
  pmo-roadmap/bootstrap/new-project.sh
  pmo-roadmap/bootstrap/session-intake.sh
  pmo-roadmap/hooks/pre-commit
  pmo-roadmap/hooks/commit-msg
  pmo-roadmap/hooks/post-commit
  pmo-roadmap/install.sh
  pmo-roadmap/update.sh
  pmo-roadmap/tests/adoption-discovery.sh
  pmo-roadmap/tests/agent-surface.sh
  pmo-roadmap/tests/canon-lint.sh
  pmo-roadmap/tests/gate-parity.sh
  pmo-roadmap/tests/roadmap-cli.sh
  pmo-roadmap/tests/work-log-mvp.sh
  pmo-roadmap/tests/workbench-explorer.sh
  pmo-roadmap/tests/workbench-ui-smoke.sh
  pmo-roadmap/tests/plugin-validate.sh
  pmo-roadmap/tests/mcp-server.sh
  pmo-roadmap/tests/step-interop.sh
  pmo-roadmap/tests/orchestration-interop.sh
  pmo-roadmap/tests/codex-driver-smoke.sh
  pmo-roadmap/tests/contributor-flow.sh
  pmo-roadmap/tests/guided-status-loop.sh
  pmo-roadmap/tests/deliberate-step-loop.sh
  pmo-roadmap/tests/package-smoke.sh
  pmo-roadmap/tests/brew-formula-smoke.sh
  pmo-roadmap/tests/upgrade-path.sh
  pmo-roadmap/tests/verify-range.sh
  pmo-roadmap/tests/docs-lint.sh
  pmo-roadmap/tests/docs-snippet-smoke.sh
  demos/scripts/prepare-onboarding-demo.sh
  demos/scripts/prepare-commit-demo.sh
  demos/scripts/capture-workbench-demo.sh
  demos/scripts/render-social-preview.sh
)
bash -n "${shell_files[@]}"
shellcheck -e SC2317 "${shell_files[@]}"

if git grep -nE "[0-9]{6,}:[A-Za-z0-9_-]{30,}" -- ":!*.png" ":!*.gif"; then
  echo "ERROR: bot-token-shaped string tracked in the repo" >&2
  exit 1
fi
if git ls-files | grep -E "(^|/)telegram\.json$"; then
  echo "ERROR: operator telegram config tracked in the repo" >&2
  exit 1
fi
if git ls-files | grep -E "(^|/)(telegram-state\.json|agent-events\.jsonl|\.env|.*\.pem|id_rsa)$"; then
  echo "ERROR: a secret-shaped file is tracked in the repo" >&2
  exit 1
fi
echo "credential grep-clean: ok"

if brew list --formula delivery-workbench >/dev/null 2>&1; then
  echo "homebrew smoke: abstained locally because the operator formula is installed; clean-machine macOS CI remains wired"
else
  run_tail bash pmo-roadmap/tests/brew-formula-smoke.sh
fi

git diff --check
git diff --cached --check
`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** 563d7ab4ef6f6952244fc9398bcfeb20c98baf56

```text
Python 3.14.6
Python 3.9.6
Name: pillow
Version: 11.3.0
Name: holdspeak
Version: 0.4.0
Name: numpy
Version: 2.5.1
test_render_grammar (__main__.VerifyTest.test_render_grammar) ... ok
test_smuggled_flip_names_missing_trailer_and_evidence (__main__.VerifyTest.test_smuggled_flip_names_missing_trailer_and_evidence) ... ok

----------------------------------------------------------------------
Ran 297 tests in 110.808s

OK
dw hook: claude — 4 installed, 0 already present in /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.dcg8c3bk/settings.json
dw hook: claude — 0 installed, 4 already present in /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.dcg8c3bk/settings.json
dw hook: claude — 4 installed, 0 already present in /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.dl82vp1l/settings.json
dw hook: claude — 4 installed, 0 already present in /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.to3d54dr/settings.json
dw hook: claude — 4 removed from /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.to3d54dr/settings.json
AssertionError: {'kin[1396 chars]ed': 1, 'limit': 7200}}, 'active_claims': [], [476 chars]alse} != {'kin[1396 chars]ed': 0, 'limit': 7200}}, 'active_claims': [], [476 chars]alse}
Diff is 2612 characters long. Set self.maxDiff to None to see it.

----------------------------------------------------------------------
Ran 297 tests in 104.970s

FAILED (failures=1)
dw hook: claude — 4 installed, 0 already present in /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.chjnjp9s/settings.json
dw hook: claude — 0 installed, 4 already present in /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.chjnjp9s/settings.json
dw hook: claude — 4 installed, 0 already present in /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.i0qa48uy/settings.json
dw hook: claude — 4 installed, 0 already present in /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.bj3a36xg/settings.json
dw hook: claude — 4 removed from /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.bj3a36xg/settings.json
```

### Captured run — 2026-07-18T08:34:31Z

- **Command:** `bash -o pipefail -c set -e

run_tail() {
  "$@" 2>&1 | tail -n 12
}

python3 --version
/usr/bin/python3 --version
.tmp/phase23-py39-optional/bin/python -m pip show Pillow | rg "^(Name|Version):"
.tmp/phase23-holdspeak-v040/bin/python -m pip show holdspeak numpy | rg "^(Name|Version):"

python3 -m py_compile pmo-roadmap/bin/dw pmo-roadmap/bin/dw-workbench pmo-roadmap/bin/dw-mcp pmo-roadmap/tests/orchestration-packaged-exam.py
python3 -m compileall -q pmo-roadmap/lib/dw_pmo
/usr/bin/python3 -m py_compile pmo-roadmap/bin/dw pmo-roadmap/bin/dw-workbench pmo-roadmap/bin/dw-mcp pmo-roadmap/tests/orchestration-packaged-exam.py
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
run_tail bash pmo-roadmap/tests/orchestration-interop.sh
run_tail bash pmo-roadmap/tests/contributor-flow.sh
run_tail bash pmo-roadmap/tests/plugin-validate.sh
run_tail bash pmo-roadmap/tests/work-log-mvp.sh
run_tail bash pmo-roadmap/tests/deliberate-step-loop.sh
run_tail bash pmo-roadmap/tests/guided-status-loop.sh

bash pmo-roadmap/tests/package-smoke.sh 2>&1 | tail -n 110
run_tail env DW_CODEX_DRIVER_LIVE=1 bash pmo-roadmap/tests/codex-driver-smoke.sh
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

shell_files=(
  pmo-roadmap/bin/work-log-read
  pmo-roadmap/bin/work-log-summarize
  pmo-roadmap/bootstrap/adopt-project.sh
  pmo-roadmap/bootstrap/new-project.sh
  pmo-roadmap/bootstrap/session-intake.sh
  pmo-roadmap/hooks/pre-commit
  pmo-roadmap/hooks/commit-msg
  pmo-roadmap/hooks/post-commit
  pmo-roadmap/install.sh
  pmo-roadmap/update.sh
  pmo-roadmap/tests/adoption-discovery.sh
  pmo-roadmap/tests/agent-surface.sh
  pmo-roadmap/tests/canon-lint.sh
  pmo-roadmap/tests/gate-parity.sh
  pmo-roadmap/tests/roadmap-cli.sh
  pmo-roadmap/tests/work-log-mvp.sh
  pmo-roadmap/tests/workbench-explorer.sh
  pmo-roadmap/tests/workbench-ui-smoke.sh
  pmo-roadmap/tests/plugin-validate.sh
  pmo-roadmap/tests/mcp-server.sh
  pmo-roadmap/tests/step-interop.sh
  pmo-roadmap/tests/orchestration-interop.sh
  pmo-roadmap/tests/codex-driver-smoke.sh
  pmo-roadmap/tests/contributor-flow.sh
  pmo-roadmap/tests/guided-status-loop.sh
  pmo-roadmap/tests/deliberate-step-loop.sh
  pmo-roadmap/tests/package-smoke.sh
  pmo-roadmap/tests/brew-formula-smoke.sh
  pmo-roadmap/tests/upgrade-path.sh
  pmo-roadmap/tests/verify-range.sh
  pmo-roadmap/tests/docs-lint.sh
  pmo-roadmap/tests/docs-snippet-smoke.sh
  demos/scripts/prepare-onboarding-demo.sh
  demos/scripts/prepare-commit-demo.sh
  demos/scripts/capture-workbench-demo.sh
  demos/scripts/render-social-preview.sh
)
bash -n "${shell_files[@]}"
shellcheck -e SC2317 "${shell_files[@]}"

if git grep -nE "[0-9]{6,}:[A-Za-z0-9_-]{30,}" -- ":!*.png" ":!*.gif"; then
  echo "ERROR: bot-token-shaped string tracked in the repo" >&2
  exit 1
fi
if git ls-files | grep -E "(^|/)telegram\.json$"; then
  echo "ERROR: operator telegram config tracked in the repo" >&2
  exit 1
fi
if git ls-files | grep -E "(^|/)(telegram-state\.json|agent-events\.jsonl|\.env|.*\.pem|id_rsa)$"; then
  echo "ERROR: a secret-shaped file is tracked in the repo" >&2
  exit 1
fi
echo "credential grep-clean: ok"

if brew list --formula delivery-workbench >/dev/null 2>&1; then
  echo "homebrew smoke: abstained locally because the operator formula is installed; clean-machine macOS CI remains wired"
else
  run_tail bash pmo-roadmap/tests/brew-formula-smoke.sh
fi

git diff --check
git diff --cached --check
`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** 1e5992a367096642dfadab7d7cec0b14dbfeeba8

```text
Python 3.14.6
Python 3.9.6
Name: pillow
Version: 11.3.0
Name: holdspeak
Version: 0.4.0
Name: numpy
Version: 2.5.1
test_render_grammar (__main__.VerifyTest.test_render_grammar) ... ok
test_smuggled_flip_names_missing_trailer_and_evidence (__main__.VerifyTest.test_smuggled_flip_names_missing_trailer_and_evidence) ... ok

----------------------------------------------------------------------
Ran 297 tests in 119.284s

OK
dw hook: claude — 4 installed, 0 already present in /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.71eqqe8p/settings.json
dw hook: claude — 0 installed, 4 already present in /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.71eqqe8p/settings.json
dw hook: claude — 4 installed, 0 already present in /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.vpxbx8ns/settings.json
dw hook: claude — 4 installed, 0 already present in /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.1y2pvdmq/settings.json
dw hook: claude — 4 removed from /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.1y2pvdmq/settings.json
test_render_grammar (__main__.VerifyTest) ... ok
test_smuggled_flip_names_missing_trailer_and_evidence (__main__.VerifyTest) ... ok

----------------------------------------------------------------------
Ran 297 tests in 123.462s

OK
dw hook: claude — 4 installed, 0 already present in /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.pa500vvs/settings.json
dw hook: claude — 0 installed, 4 already present in /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.pa500vvs/settings.json
dw hook: claude — 4 installed, 0 already present in /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.ebrs512z/settings.json
dw hook: claude — 4 installed, 0 already present in /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.9te2q5hi/settings.json
dw hook: claude — 4 removed from /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.9te2q5hi/settings.json
canon-lint.sh: ok
docs-lint: ok (398 markdown files)
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
adoption-discovery.sh: ok
agent-surface.sh: ok
gate-parity.sh: ok
roadmap-cli.sh: ok
dw-workbench: serving /private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/pmo-workbench-test.jpAPkx/repo
dw-workbench: http://127.0.0.1:19368/ (localhost or your own .ts.net tailnet; Ctrl-C to stop)
dw-workbench: writes require /api/mutations preview→apply or an exact /api/step/apply token; never stages, certifies, or commits
dw-workbench: shutting down
dw-workbench: serving /private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/pmo-workbench-test.jpAPkx/installed
dw-workbench: http://127.0.0.1:19369/ (localhost or your own .ts.net tailnet; Ctrl-C to stop)
dw-workbench: writes require /api/mutations preview→apply or an exact /api/step/apply token; never stages, certifies, or commits
workbench-explorer.sh: ok
dw-workbench: shutting down
dw-workbench: serving /private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/pmo-workbench-test.jpAPkx/repo
dw-workbench: http://127.0.0.1:19368/ (localhost or your own .ts.net tailnet; Ctrl-C to stop)
dw-workbench: writes require /api/mutations preview→apply or an exact /api/step/apply token; never stages, certifies, or commits
workbench-ui-smoke.sh: ok (32 viewport renders: 14 views + attention + ambiguity, desktop+mobile)
dw-workbench: shutting down
dw-workbench: serving /private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/pmo-ui-smoke.ZHEk8u/repo
dw-workbench: http://127.0.0.1:21108/ (localhost or your own .ts.net tailnet; Ctrl-C to stop)
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
orchestration interop: exact CLI/MCP/HTTP lifecycle reached awaiting-certification
orchestration-interop.sh: ok
dw-workbench: shutting down
dw-workbench: serving /private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-orchestration-interop.Jq1qiB/repo
dw-workbench: http://127.0.0.1:24619/ (localhost or your own .ts.net tailnet; Ctrl-C to stop)
dw-workbench: writes require /api/mutations preview→apply or an exact /api/step/apply token; never stages, certifies, or commits
red 1a: the maintainer's own gate refuses the two-flip squash
pmo-roadmap post-commit: contract archived to .git/pmo-contract-archive/b4988252cf03fb0d12e9ae0156c878d7281824e4
red 1b: forced two-flip squash lands and dw verify names atomicity
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✓ The system accepted your understanding of the project management framework.
  Contract acknowledged (7/7 checkboxes).
  Stories shipped this commit: 1 (evidence verified by dw gate).
  Commit proceeding.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
pmo-roadmap post-commit: contract archived to .git/pmo-contract-archive/eeb00769b12e2ea532cd2fdb6b2e11b034bfc733
red 2: fixup squash displaces trailers mid-body and dw verify names trailer-missing
contributor-flow.sh: ok
plugin manifests: ok (version 1.14.0, 4 commands, 1 skill)
claude plugin validate: ok
plugin-validate.sh: ok
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
pmo-roadmap post-commit: contract archived to .git/pmo-contract-archive/e927010cc4d90e6fd407b3b5d94a636660c3c491
pmo-roadmap post-commit: work log appended to /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T//pmo-work-log-test.0tbISS/work-log/2026-07-18/demo-1404983084-work-summary.log
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✓ The system accepted your understanding of the project management framework.
  Contract acknowledged (1/1 checkboxes).
  Work log payload captured for post-commit finalization.
  Commit proceeding.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
pmo-roadmap post-commit: contract archived to .git/pmo-contract-archive/f47066636d5879fbff9f49c060890e2155480756
pmo-roadmap post-commit: work log appended to /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T//pmo-work-log-test.0tbISS/work-log/2026-07-18/demo-1404983084-work-summary.log
work-log-mvp.sh: ok
authorize 03 http start-story        -> continue-story
refuse   same-id stale token    started=0 step_events=+0
authorize 04 mcp  continue-story     -> continue-story
authorize 05 cli  finish-story       -> review-workspace
authorize 06 http review-workspace   -> review-workspace
authorize 07 cli  generate-contract  -> certify-contract
refuse   story certification    started=0 step_events=+0
refuse   story commit           started=0 step_events=+0
bootstrap  95b75081d083         certification+commit=manual
commit     fff100eb90ab         trailers+archive+verify=ok
handoff    start-story        authorizations=7
deliberate-step-loop.sh: ok (fresh token per action; no argv reconstruction or consent shortcut)
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
commit     47894a89a165         trailers+archive+verify=ok
guided-status-loop.sh: ok (packaged CLI/MCP/HTTP recommendation sequence)
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
You should consider upgrading via the '/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/pmo-package-smoke.x7Lwwv/appenv/bin/python -m pip install --upgrade pip' command.
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
commit     722a03f66c18         trailers+archive+verify=ok
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
bootstrap  d91cc1b04dc1         certification+commit=manual
commit     eb8b1c4efef7         trailers+archive+verify=ok
handoff    start-story        authorizations=7
deliberate-step-loop.sh: ok (fresh token per action; no argv reconstruction or consent shortcut)
{"artifact_count": 5, "checks": 2, "compiler_red_cases": 6, "duplicate_restarts": 0, "exam": "packaged multi-agent orchestration", "operator_commit": "04281d10cbebd4a14f819856b53b259cef3df149", "parallel_research": 2, "repair_visits": 1, "run_id": "run-3e43280b198471519eb1ca9b", "runtime_red_cases": 5, "state": "awaiting-certification", "verify_all": "ok"}
package-smoke.sh: ok
{"adapter": "codex-exec", "artifact": "live-findings", "artifact_hash": "sha256:12d6631ce855b70cac9bfcc0eddd15f4887244963c946b289bc64fc69482637e", "checks": ["declared", "contained", "bytes", "markdown-sections", "citations"], "ledger_events": 3, "operator_tree_clean": true, "session_id": "session-c3aa036d655a2fd96d45644a", "state": "succeeded"}
codex-driver-smoke.sh: ok (authenticated read-only codex exec adapter)
  Contract acknowledged (7/7 checkboxes).
  Commit proceeding.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
pmo-roadmap post-commit: contract archived to .git/pmo-contract-archive/fc1320cb8d816e3d1165f28077adb407ec328921
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✓ The system accepted your understanding of the project management framework.
  Contract acknowledged (7/7 checkboxes).
  Stories shipped this commit: 1 (evidence verified by dw gate).
  Commit proceeding.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
pmo-roadmap post-commit: contract archived to .git/pmo-contract-archive/479f60d4fc9aeb110833c981013bb8d6e85a11dd
upgrade-path.sh: ok
  Contract acknowledged (7/7 checkboxes).
  Stories shipped this commit: 2 (evidence verified by dw gate).
  Commit proceeding.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
pmo-roadmap post-commit: contract archived to .git/pmo-contract-archive/1ede343809cd1dac3c08d7c9ba569b1a9a66edc7
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✓ The system accepted your understanding of the project management framework.
  Contract acknowledged (7/7 checkboxes).
  Commit proceeding.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
pmo-roadmap post-commit: contract archived to .git/pmo-contract-archive/c1ca0dc0d336dab85ec49c5c7760f1d5ff69f2c8
verify-range.sh: ok
test_repo_bind_scope_and_reverse (__main__.TopicRouterTest) ... ok
test_session_binding_expires_but_activity_refreshes (__main__.TopicRouterTest) ... ok
test_unbind_repo_cascades_to_session (__main__.TopicRouterTest) ... ok
test_bind_then_commands_scope_to_the_topic (__main__.TopicScopingTest) ... ok
test_flat_chat_still_uses_active_repo (__main__.TopicScopingTest) ... ok
test_replies_land_in_the_originating_topic (__main__.TopicScopingTest) ... ok
test_unbound_topic_has_no_repo (__main__.TopicScopingTest) ... ok

----------------------------------------------------------------------
Ran 147 tests in 10.762s

OK (skipped=1)
test_consent_floor_catches_planted_send_keys (__main__.FitnessSelfTest) ... ok
test_layering_catches_a_planted_transport_import (__main__.FitnessSelfTest) ... ok
test_layering_catches_a_planted_violation_in_a_new_leaf (__main__.FitnessSelfTest) ... ok
test_leaves_stay_leaves (__main__.ImportLayeringTest) ... ok
test_no_import_cycles (__main__.ImportLayeringTest) ... ok
test_rails_seam_is_reached_only_through_the_interface (__main__.ImportLayeringTest) ... ok
test_transport_is_a_pure_leaf (__main__.ImportLayeringTest) ... ok

----------------------------------------------------------------------
Ran 10 tests in 0.152s

OK
test_synthesized_artifact_carries_the_summary (__main__.PackHostIntegrationTest.test_synthesized_artifact_carries_the_summary) ... ok
test_broken_dw_is_failure_shape (__main__.PackUnitTest.test_broken_dw_is_failure_shape) ... ok
test_empty_transcript_is_failure_shape (__main__.PackUnitTest.test_empty_transcript_is_failure_shape) ... ok
test_hallucinated_story_id_is_demoted_to_drift (__main__.PackUnitTest.test_hallucinated_story_id_is_demoted_to_drift) ... ok
test_no_roadmap_resolvable_fails_before_llm (__main__.PackUnitTest.test_no_roadmap_resolvable_fails_before_llm) ... ok
test_success_grounds_real_story_ids (__main__.PackUnitTest.test_success_grounds_real_story_ids) ... ok
test_unparseable_response_is_failure_shape (__main__.PackUnitTest.test_unparseable_response_is_failure_shape) ... ok

----------------------------------------------------------------------
Ran 23 tests in 11.281s

OK
Prepared onboarding demo repo:
  /tmp/delivery-workbench-onboarding-demo
Prepared commit-gate demo repo:
  /tmp/delivery-workbench-commit-demo
Work-log root:
  /tmp/delivery-workbench-work-log
capture-workbench-demo.sh: ok
  /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T//dw-workbench-demo.CgPcHi/rendered/workbench-tour.gif
  /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T//dw-workbench-demo.CgPcHi/assets/workbench-overview.png
  /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T//dw-workbench-demo.CgPcHi/assets/workbench-trace.png
  /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T//dw-workbench-demo.CgPcHi/assets/workbench-editor.png
dw-workbench: shutting down
dw-workbench: serving /private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-workbench-demo.CgPcHi/repo
dw-workbench: http://127.0.0.1:23522/ (localhost or your own .ts.net tailnet; Ctrl-C to stop)
dw-workbench: writes require /api/mutations preview→apply or an exact /api/step/apply token; never stages, certifies, or commits
render-social-preview.sh: ok
  /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T//dw-social-preview.vN1hxT/assets/social-preview.png
update.sh: up to date (vendored rails match source v1.14.0)
dw rider docs: all rendered surfaces match canon
ERROR pmo-roadmap/pm/roadmap/work-log-automation/phase-24-bounded-orchestration/evidence-story-08.md: evidence exists but matching story is not done
```

### Captured run — 2026-07-18T08:45:47Z

- **Command:** `bash pmo-roadmap/tests/package-smoke.sh`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** b54d884c0fec6b9aba6b1af891654b6b7cfbd9a5

```text
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
You should consider upgrading via the '/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/pmo-package-smoke.weHhr7/appenv/bin/python -m pip install --upgrade pip' command.
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
commit     84a615d444a4         trailers+archive+verify=ok
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
bootstrap  bf71c75787c1         certification+commit=manual
commit     2cb5eae351e8         trailers+archive+verify=ok
handoff    start-story        authorizations=7
deliberate-step-loop.sh: ok (fresh token per action; no argv reconstruction or consent shortcut)
{"artifact_count": 5, "checks": 2, "compiler_red_cases": 6, "duplicate_restarts": 0, "exam": "packaged multi-agent orchestration", "operator_commit": "3cb77d9620d5d91b861baceaf11763867f8c9fd5", "parallel_research": 2, "repair_visits": 1, "run_id": "run-d0714dc821b83796fd70552b", "runtime_red_cases": 5, "state": "awaiting-certification", "verify_all": "ok"}
package-smoke.sh: ok
```

### Captured run — 2026-07-18T08:50:50Z

- **Command:** `bash -o pipefail -c set -e
run_tail() { "$@" 2>&1 | tail -n 12; }

run_tail .githooks/dw check work-log-automation
run_tail .githooks/dw verify --all
run_tail bash pmo-roadmap/tests/canon-lint.sh
run_tail bash pmo-roadmap/tests/docs-lint.sh
run_tail bash pmo-roadmap/tests/docs-snippet-smoke.sh

python3 -m py_compile pmo-roadmap/tests/orchestration-packaged-exam.py
/usr/bin/python3 -m py_compile pmo-roadmap/tests/orchestration-packaged-exam.py
for i in 1 2 3 4 5; do
  python3 pmo-roadmap/tests/dw-core-tests.py OrchestrationConductorTest.test_run_interop_compiler_plan_projection_and_preview_are_exact >/dev/null
  /usr/bin/python3 pmo-roadmap/tests/dw-core-tests.py OrchestrationConductorTest.test_run_interop_compiler_plan_projection_and_preview_are_exact >/dev/null
done
echo "adapter parity clock-boundary stress: ok (5/5 each interpreter)"

node --check pmo-roadmap/workbench/app.js
node --check .githooks/workbench/app.js
pmo-roadmap/update.sh . --check
.githooks/dw rider docs --check

shell_files=(
  pmo-roadmap/install.sh
  pmo-roadmap/update.sh
  pmo-roadmap/hooks/pre-commit
  pmo-roadmap/hooks/commit-msg
  pmo-roadmap/hooks/post-commit
  pmo-roadmap/tests/package-smoke.sh
  pmo-roadmap/tests/orchestration-interop.sh
  pmo-roadmap/tests/codex-driver-smoke.sh
  pmo-roadmap/tests/workbench-ui-smoke.sh
  pmo-roadmap/tests/mcp-server.sh
  pmo-roadmap/tests/step-interop.sh
  demos/scripts/prepare-onboarding-demo.sh
  demos/scripts/prepare-commit-demo.sh
  demos/scripts/capture-workbench-demo.sh
  demos/scripts/render-social-preview.sh
)
bash -n "${shell_files[@]}"
shellcheck -e SC2317 "${shell_files[@]}"

if git grep -nE "[0-9]{6,}:[A-Za-z0-9_-]{30,}" -- ":!*.png" ":!*.gif"; then
  exit 1
fi
if git ls-files | grep -E "(^|/)(telegram\.json|telegram-state\.json|agent-events\.jsonl|\.env|.*\.pem|id_rsa)$"; then
  exit 1
fi
echo "credential grep-clean: ok"

if brew list --formula delivery-workbench >/dev/null 2>&1; then
  echo "homebrew smoke: abstained locally because the operator formula is installed; clean-machine macOS CI remains wired"
else
  run_tail bash pmo-roadmap/tests/brew-formula-smoke.sh
fi

git diff --check
git diff --cached --check
`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** 34daeb72e0799e2a124c132e16a76e9afa02cee0

```text
dw check: ok
dw verify: ok (136 commits verified, 17 pre-epoch skipped)
canon-lint.sh: ok
docs-lint: ok (398 markdown files)
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
test_run_interop_compiler_plan_projection_and_preview_are_exact (__main__.OrchestrationConductorTest.test_run_interop_compiler_plan_projection_and_preview_are_exact) ... ok

----------------------------------------------------------------------
Ran 1 test in 1.999s

OK
test_run_interop_compiler_plan_projection_and_preview_are_exact (__main__.OrchestrationConductorTest) ... ok

----------------------------------------------------------------------
Ran 1 test in 1.915s

OK
test_run_interop_compiler_plan_projection_and_preview_are_exact (__main__.OrchestrationConductorTest.test_run_interop_compiler_plan_projection_and_preview_are_exact) ... ok

----------------------------------------------------------------------
Ran 1 test in 2.007s

OK
test_run_interop_compiler_plan_projection_and_preview_are_exact (__main__.OrchestrationConductorTest) ... ok

----------------------------------------------------------------------
Ran 1 test in 1.923s

OK
test_run_interop_compiler_plan_projection_and_preview_are_exact (__main__.OrchestrationConductorTest.test_run_interop_compiler_plan_projection_and_preview_are_exact) ... ok

----------------------------------------------------------------------
Ran 1 test in 2.027s

OK
test_run_interop_compiler_plan_projection_and_preview_are_exact (__main__.OrchestrationConductorTest) ... ok

----------------------------------------------------------------------
Ran 1 test in 1.914s

OK
test_run_interop_compiler_plan_projection_and_preview_are_exact (__main__.OrchestrationConductorTest.test_run_interop_compiler_plan_projection_and_preview_are_exact) ... ok

----------------------------------------------------------------------
Ran 1 test in 2.030s

OK
test_run_interop_compiler_plan_projection_and_preview_are_exact (__main__.OrchestrationConductorTest) ... ok

----------------------------------------------------------------------
Ran 1 test in 1.908s

OK
test_run_interop_compiler_plan_projection_and_preview_are_exact (__main__.OrchestrationConductorTest.test_run_interop_compiler_plan_projection_and_preview_are_exact) ... ok

----------------------------------------------------------------------
Ran 1 test in 2.081s

OK
test_run_interop_compiler_plan_projection_and_preview_are_exact (__main__.OrchestrationConductorTest) ... ok

----------------------------------------------------------------------
Ran 1 test in 1.952s

OK
adapter parity clock-boundary stress: ok (5/5 each interpreter)
update.sh: up to date (vendored rails match source v1.14.0)
dw rider docs: all rendered surfaces match canon

In pmo-roadmap/tests/workbench-ui-smoke.sh line 236:
      $CAPTURE_PATTERN)
      ^--------------^ SC2254 (warning): Quote expansions in case patterns to match literally rather than as a glob.

For more information:
  https://www.shellcheck.net/wiki/SC2254 -- Quote expansions in case patterns...
```

### Captured run — 2026-07-18T08:52:38Z

- **Command:** `bash -o pipefail -c set -e
run_tail() { "$@" 2>&1 | tail -n 12; }

run_tail .githooks/dw check work-log-automation
run_tail .githooks/dw verify --all
run_tail bash pmo-roadmap/tests/canon-lint.sh
run_tail bash pmo-roadmap/tests/docs-lint.sh
run_tail bash pmo-roadmap/tests/docs-snippet-smoke.sh

python3 -m py_compile pmo-roadmap/tests/orchestration-packaged-exam.py
/usr/bin/python3 -m py_compile pmo-roadmap/tests/orchestration-packaged-exam.py
for i in 1 2 3 4 5; do
  python3 pmo-roadmap/tests/dw-core-tests.py OrchestrationConductorTest.test_run_interop_compiler_plan_projection_and_preview_are_exact >/dev/null
  /usr/bin/python3 pmo-roadmap/tests/dw-core-tests.py OrchestrationConductorTest.test_run_interop_compiler_plan_projection_and_preview_are_exact >/dev/null
done
echo "adapter parity clock-boundary stress: ok (5/5 each interpreter)"

node --check pmo-roadmap/workbench/app.js
node --check .githooks/workbench/app.js
pmo-roadmap/update.sh . --check
.githooks/dw rider docs --check

shell_files=(
  pmo-roadmap/install.sh
  pmo-roadmap/update.sh
  pmo-roadmap/hooks/pre-commit
  pmo-roadmap/hooks/commit-msg
  pmo-roadmap/hooks/post-commit
  pmo-roadmap/tests/package-smoke.sh
  pmo-roadmap/tests/orchestration-interop.sh
  pmo-roadmap/tests/codex-driver-smoke.sh
  pmo-roadmap/tests/workbench-ui-smoke.sh
  pmo-roadmap/tests/mcp-server.sh
  pmo-roadmap/tests/step-interop.sh
  demos/scripts/prepare-onboarding-demo.sh
  demos/scripts/prepare-commit-demo.sh
  demos/scripts/capture-workbench-demo.sh
  demos/scripts/render-social-preview.sh
)
bash -n "${shell_files[@]}"
shellcheck -e SC2317 "${shell_files[@]}"

if git grep -nE "[0-9]{6,}:[A-Za-z0-9_-]{30,}" -- ":!*.png" ":!*.gif"; then
  exit 1
fi
if git ls-files | grep -E "(^|/)(telegram\.json|telegram-state\.json|agent-events\.jsonl|\.env|.*\.pem|id_rsa)$"; then
  exit 1
fi
echo "credential grep-clean: ok"

if brew list --formula delivery-workbench >/dev/null 2>&1; then
  echo "homebrew smoke: abstained locally because the operator formula is installed; clean-machine macOS CI remains wired"
else
  run_tail bash pmo-roadmap/tests/brew-formula-smoke.sh
fi

git diff --check
git diff --cached --check
`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** bed1c4f44579df801bb051d896671870df3b35c8

```text
dw check: ok
dw verify: ok (136 commits verified, 17 pre-epoch skipped)
canon-lint.sh: ok
docs-lint: ok (398 markdown files)
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
test_run_interop_compiler_plan_projection_and_preview_are_exact (__main__.OrchestrationConductorTest.test_run_interop_compiler_plan_projection_and_preview_are_exact) ... ok

----------------------------------------------------------------------
Ran 1 test in 2.000s

OK
test_run_interop_compiler_plan_projection_and_preview_are_exact (__main__.OrchestrationConductorTest) ... ok

----------------------------------------------------------------------
Ran 1 test in 1.999s

OK
test_run_interop_compiler_plan_projection_and_preview_are_exact (__main__.OrchestrationConductorTest.test_run_interop_compiler_plan_projection_and_preview_are_exact) ... ok

----------------------------------------------------------------------
Ran 1 test in 1.996s

OK
test_run_interop_compiler_plan_projection_and_preview_are_exact (__main__.OrchestrationConductorTest) ... ok

----------------------------------------------------------------------
Ran 1 test in 1.940s

OK
test_run_interop_compiler_plan_projection_and_preview_are_exact (__main__.OrchestrationConductorTest.test_run_interop_compiler_plan_projection_and_preview_are_exact) ... ok

----------------------------------------------------------------------
Ran 1 test in 2.026s

OK
test_run_interop_compiler_plan_projection_and_preview_are_exact (__main__.OrchestrationConductorTest) ... ok

----------------------------------------------------------------------
Ran 1 test in 1.888s

OK
test_run_interop_compiler_plan_projection_and_preview_are_exact (__main__.OrchestrationConductorTest.test_run_interop_compiler_plan_projection_and_preview_are_exact) ... ok

----------------------------------------------------------------------
Ran 1 test in 2.060s

OK
test_run_interop_compiler_plan_projection_and_preview_are_exact (__main__.OrchestrationConductorTest) ... ok

----------------------------------------------------------------------
Ran 1 test in 1.880s

OK
test_run_interop_compiler_plan_projection_and_preview_are_exact (__main__.OrchestrationConductorTest.test_run_interop_compiler_plan_projection_and_preview_are_exact) ... ok

----------------------------------------------------------------------
Ran 1 test in 1.999s

OK
test_run_interop_compiler_plan_projection_and_preview_are_exact (__main__.OrchestrationConductorTest) ... ok

----------------------------------------------------------------------
Ran 1 test in 1.905s

OK
adapter parity clock-boundary stress: ok (5/5 each interpreter)
update.sh: up to date (vendored rails match source v1.14.0)
dw rider docs: all rendered surfaces match canon
credential grep-clean: ok
homebrew smoke: abstained locally because the operator formula is installed; clean-machine macOS CI remains wired
```
