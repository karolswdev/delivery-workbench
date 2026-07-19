# Evidence - WLA-25-01

- **Story:** WLA-25-01 - Contract the outward signal and nudge authority
- **Status:** done
- **Date:** 2026-07-18

## Proof

The reviewed contract in `docs/signals.md` fixes the outward layer's
meanings before any component acquires behavior: the product claim
(Delivery Workbench **can observe** outward facts and **can nudge** under
an explicit grant), the `delivery-workbench-signal@1` fact model with
hash-chained storage under `.git/pmo-signals/` and read-time derived-status
precedence, the six-state activity vocabulary with its pure receptivity
table (`blocked`/`unknown` refuse under every intent), the four-layer nudge
model (score rule → grant authority with budgets and exact-match standing
rules → receptivity → at-most-once ledger receipt), authority rings 0-5,
typed request ports with exactly-once republish on resume, the
no-authority SSE tail, preview-only notifications under Phase-20 consent,
permanent content exclusions, a thirteen-row threat table, and the Phase-25
proof standard. Both contract-owed decisions are settled on record: nudge
targets are declared route targets only, and run-less branch signals notify
per-project opt-in. `docs/orchestration.md` cross-links the new contract,
and the phase plan stands at nine ordered, bounded stories.

The **authoritative run is 2026-07-19T03:19:51Z (exit 0)** — the full
battery (297 core tests on both Python floors, docs lint and snippets,
canon lint, agent surface, roadmap check, rider parity, vendored-rails
check, structural contract pins, story-table count, diff hygiene). The two
earlier captures are honest iterations: 03:09:50Z failed on two structural
pins whose phrases wrap across source lines (pins shortened to within-line
fragments, contract text unchanged), and 03:14:23Z failed on `dw check`
because this evidence file already existed while the story was still
`in-progress` (resolved by flipping the story done before the final run,
matching the Phase-24 order).

## Manual review

- Walked the contracted scenario end to end: operator integrates and
  pushes → fixture CI fails → `pr-check` signal appends to the chain →
  derived status flips to `ci-failed` → the score's `ci-failed` rule
  matches its declared repair target → the grant's standing rule covers
  the exact (kind, target) pair → receptivity finds the session
  `waiting_input` → one structured packet delivers with one ledger
  receipt → repair reruns → `checkpoint-pending` notifies over Telegram
  as a preview → the typed response crosses the local exact-token
  boundary. Every step maps to one contracted fact, act, or refusal, and
  every refusal in the taxonomy has a threat-table row.
- Confirmed the observer stays pure (`starts_work: false`), packets can
  never carry argv/tokens/secrets/third-party bodies, `blocked` refuses
  even operator-initiated nudges, the stream carries no authority, and
  ring 5 (certification, commit, push, merge, release) is untouched.

### Captured run — 2026-07-19T03:09:50Z

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
rg -q "can observe" docs/signals.md
rg -q "can nudge" docs/signals.md
rg -q "^## Durable signal model" docs/signals.md
rg -q "^## Derived status precedence" docs/signals.md
rg -q "^## Activity states and receptivity" docs/signals.md
rg -q "^## Nudge model" docs/signals.md
rg -q "^## Authority model" docs/signals.md
rg -q "^## Request ports and outstanding requests" docs/signals.md
rg -q "^## Threat model and fail checks" docs/signals.md
rg -q "declared route targets only" docs/signals.md
rg -q "at-most-once per signal per rule" docs/signals.md
rg -q "never inject without a grant, a budget, and a receipt" docs/signals.md
rg -q "including a manual operator" docs/signals.md
rg -q "signals.md" docs/orchestration.md
test "$(rg -c "^\| WLA-25-" pmo-roadmap/pm/roadmap/work-log-automation/phase-25-outward-signals/current-phase-status.md)" -eq 9
git diff --check
git diff --cached --check
`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** 625e1ffe57d27105b9c5989f4fa2db39cd36aec9

```text
dw hook: codex_hooks is explicitly false in /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.kl3hpcw8/config.toml; respecting the opt-out
----------------------------------------------------------------------
Ran 297 tests in 110.256s

OK
dw hook: claude — 4 installed, 0 already present in /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.wdaunhgh/settings.json
dw hook: claude — 0 installed, 4 already present in /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.wdaunhgh/settings.json
dw hook: claude — 4 installed, 0 already present in /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.g6xvjdv0/settings.json
dw hook: claude — 4 installed, 0 already present in /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.0w_98_2i/settings.json
dw hook: claude — 4 removed from /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.0w_98_2i/settings.json
dw hook: codex_hooks is explicitly false in /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.9pejodw7/config.toml; respecting the opt-out
----------------------------------------------------------------------
Ran 297 tests in 108.527s

OK
dw hook: claude — 4 installed, 0 already present in /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.6ae4qtuk/settings.json
dw hook: claude — 0 installed, 4 already present in /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.6ae4qtuk/settings.json
dw hook: claude — 4 installed, 0 already present in /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.obkts_vw/settings.json
dw hook: claude — 4 installed, 0 already present in /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.axws86sz/settings.json
dw hook: claude — 4 removed from /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.axws86sz/settings.json
docs-lint: ok (409 markdown files)
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

### Captured run — 2026-07-19T03:14:23Z

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
rg -q "can observe" docs/signals.md
rg -q "can nudge" docs/signals.md
rg -q "^## Durable signal model" docs/signals.md
rg -q "^## Derived status precedence" docs/signals.md
rg -q "^## Activity states and receptivity" docs/signals.md
rg -q "^## Nudge model" docs/signals.md
rg -q "^## Authority model" docs/signals.md
rg -q "^## Request ports and outstanding requests" docs/signals.md
rg -q "^## Threat model and fail checks" docs/signals.md
rg -q "declared route targets only" docs/signals.md
rg -q "at-most-once per signal" docs/signals.md
rg -q "never inject without a grant" docs/signals.md
rg -q "including a manual operator" docs/signals.md
rg -q "signals.md" docs/orchestration.md
test "$(rg -c "^\| WLA-25-" pmo-roadmap/pm/roadmap/work-log-automation/phase-25-outward-signals/current-phase-status.md)" -eq 9
git diff --check
git diff --cached --check
`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** 625e1ffe57d27105b9c5989f4fa2db39cd36aec9

```text
dw hook: codex_hooks is explicitly false in /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.smxbwotb/config.toml; respecting the opt-out
----------------------------------------------------------------------
Ran 297 tests in 118.263s

OK
dw hook: claude — 4 installed, 0 already present in /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.h6khp3u3/settings.json
dw hook: claude — 0 installed, 4 already present in /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.h6khp3u3/settings.json
dw hook: claude — 4 installed, 0 already present in /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.6yoa8hxe/settings.json
dw hook: claude — 4 installed, 0 already present in /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.2laj3o17/settings.json
dw hook: claude — 4 removed from /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.2laj3o17/settings.json
dw hook: codex_hooks is explicitly false in /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.0py1wd88/config.toml; respecting the opt-out
----------------------------------------------------------------------
Ran 297 tests in 110.428s

OK
dw hook: claude — 4 installed, 0 already present in /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.mu6ik936/settings.json
dw hook: claude — 0 installed, 4 already present in /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.mu6ik936/settings.json
dw hook: claude — 4 installed, 0 already present in /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.bkscwolg/settings.json
dw hook: claude — 4 installed, 0 already present in /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.us52xpo3/settings.json
dw hook: claude — 4 removed from /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.us52xpo3/settings.json
docs-lint: ok (410 markdown files)
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
ERROR pmo-roadmap/pm/roadmap/work-log-automation/phase-25-outward-signals/evidence-story-01.md: evidence exists but matching story is not done
```

### Captured run — 2026-07-19T03:19:51Z

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
rg -q "can observe" docs/signals.md
rg -q "can nudge" docs/signals.md
rg -q "^## Durable signal model" docs/signals.md
rg -q "^## Derived status precedence" docs/signals.md
rg -q "^## Activity states and receptivity" docs/signals.md
rg -q "^## Nudge model" docs/signals.md
rg -q "^## Authority model" docs/signals.md
rg -q "^## Request ports and outstanding requests" docs/signals.md
rg -q "^## Threat model and fail checks" docs/signals.md
rg -q "declared route targets only" docs/signals.md
rg -q "at-most-once per signal" docs/signals.md
rg -q "never inject without a grant" docs/signals.md
rg -q "including a manual operator" docs/signals.md
rg -q "signals.md" docs/orchestration.md
test "$(rg -c "^\| WLA-25-" pmo-roadmap/pm/roadmap/work-log-automation/phase-25-outward-signals/current-phase-status.md)" -eq 9
git diff --check
git diff --cached --check
`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 625e1ffe57d27105b9c5989f4fa2db39cd36aec9

```text
dw hook: codex_hooks is explicitly false in /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.hsfe8j6s/config.toml; respecting the opt-out
----------------------------------------------------------------------
Ran 297 tests in 112.508s

OK
dw hook: claude — 4 installed, 0 already present in /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.o7vyf4_y/settings.json
dw hook: claude — 0 installed, 4 already present in /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.o7vyf4_y/settings.json
dw hook: claude — 4 installed, 0 already present in /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.zfy3r6ik/settings.json
dw hook: claude — 4 installed, 0 already present in /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.oindq7f5/settings.json
dw hook: claude — 4 removed from /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.oindq7f5/settings.json
dw hook: codex_hooks is explicitly false in /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.dot6bruc/config.toml; respecting the opt-out
----------------------------------------------------------------------
Ran 297 tests in 111.038s

OK
dw hook: claude — 4 installed, 0 already present in /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.suk3x33x/settings.json
dw hook: claude — 0 installed, 4 already present in /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.suk3x33x/settings.json
dw hook: claude — 4 installed, 0 already present in /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.sckzske1/settings.json
dw hook: claude — 4 installed, 0 already present in /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.s8drnowc/settings.json
dw hook: claude — 4 removed from /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.s8drnowc/settings.json
docs-lint: ok (410 markdown files)
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
canon-lint.sh: ok
agent-surface.sh: ok
dw check: ok
dw rider docs: all rendered surfaces match canon
update.sh: up to date (vendored rails match source v1.14.0)
```
