# Evidence - WLA-27-03

- **Story:** WLA-27-03 - Give first-time users a delivery-shaped front door
- **Status:** done
- **Date:** 2026-07-24

## Proof

The new pure
[`delivery_setup.py`](../../../../lib/dw_pmo/delivery_setup.py) application
view composes the unchanged status, delivery-plan inventory, and Program
Studio models into one `delivery-workbench-delivery-setup@1` document. It
names the selected project, phase/current work, and exactly three choices:
ordinary roadmap work, one bounded delivery, and an optional delivery program.
Each choice carries readiness, one correction when needed, what setup creates,
what could change only later, what stays disabled, and the separate permission
still required. No choice creates authority. Missing program policy remains
healthy; an invalid optional draft affects only that optional choice while
ordinary delivery stays ready.

Workbench now leads with **Your roadmap is ready**, current work, **Open
current work**, and **Review delivery options**. The former repository,
contract, gate, command, and one-step briefing remains available under
**Technical details**. The setup route begins with project/phase delivery
scope, compares all three modes without preselection, focuses the reviewed
choice, and gives **Compare options** and **Leave for now** exits. A program
choice seeds only an unsaved in-memory scope; its technical editor says
**review draft save**, and the existing stale-safe preview still requires
**save this delivery-plan draft** before one tracked policy can change.
Starting work remains a later, separate reviewed act.

Bounded preflight now leads with delivery readiness, work/order, team, review,
permission, limits/stops, and one **Review separate start** next step. An
invalid plan leads with **Affected decision** and one corrective **Next step**.
Exact pointers, codes, hashes, capability/profile names, scheduling simulation,
lineage, and failure routes remain losslessly reachable only after opening
**Technical details**.

Human `dw status` adds a compact setup pointer, and
`dw setup [project] [--technical]` renders the same three choice labels and
readiness as `GET /api/delivery-setup`. Existing `dw status --json`, MCP
status, and source machine documents are byte-unchanged. The interop, product
language, journey, root/framework docs, and versioned surface/source fixtures
now name that presentation-only seam.

## No-side-effect and distribution proof

`DeliverySetupTest` exercises fresh, configured, incomplete, invalid, and ready
facts, source/HTTP equality, human CLI guidance, repeated reads, and every
declared false effect. The Workbench explorer repeats the setup GET without
changing the roadmap tree and proves the source and installed human CLI.
The browser contract statically excludes POST, local storage, event streams,
and polling from the setup renderer.

The complete viewport harness rendered 62 canonical views: the delivery choice
and reviewed-program/technical-detail states plus every existing data state at
1440x900 and 390x844. The narrow setup keeps a single-line scrollable global
bar, delivery scope/current work in the first task region, and horizontally
snappable choice cards with the next card visibly discoverable. Buttons,
selects, number input, cards, disclosure, compare, continue, and leave paths
all retain native keyboard operation and visible focus.

The fresh Python 3.9 wheel package suite passed end to end. Its autonomous exam
completed three stories across two phases with 203 replayed ledger events,
nine conductor crash recoveries, eighteen delivery-boundary crash recoveries,
three pushes, independent council/meta/architect proof, and the full refusal
matrix. The separate dormant consumer then reported the exact
`roadmap|bounded|program` setup choices through installed HTTP and human CLI
while program, notification, workflow, organization, observer/process,
network, and roadmap-write effects remained absent.

Before evidence capture, the complete core regression passed:
`python3 pmo-roadmap/tests/dw-core-tests.py` — 477 tests in 826.335 seconds,
`OK`. Product-language, all thirteen usability journeys, interop, Workbench
explorer, docs/snippets/canon, source/install alignment, and the 62-view
desktop/mobile harness were independently green.

## Manual wide/narrow review

- The overview now answers readiness and current work before exposing any
  repository protocol. Both primary actions are adjacent, and optional setup
  is explicitly not required.
- The wide setup shows scope plus all three comparable choices without a
  default selection. The reviewed effects and remaining permission sit
  together below them.
- At 390×844, the readiness header wraps inside its card, scope and current
  work fit the viewport, and the first choice plus a sliver of the next card
  make horizontal comparison apparent. No long header widens the page.
- Opening the reviewed program state shows creation, later change, disabled
  behavior, remaining permission, safe exits, and the collapsed technical
  boundary. Opening/closing that boundary and leaving return without writes.
- Invalid bounded/program fixtures name the delivery decision and correction
  before any raw internal pointer. Unavailable ordinary/program continuation
  is disabled; the bounded correction may still open the delivery-plan editor.

The first captured chain below passed every product and 62-view viewport check,
then failed its final roadmap check because this evidence file existed while
the story was still `in-progress`. That block is retained as fail-closed rail
evidence. After linking the evidence, checking acceptance, and completing the
story transition, the second captured chain passed the same focused
model/parity guards plus roadmap, rider, docs, syntax, and source/install
alignment.

### Captured run — 2026-07-24T09:43:53Z

- **Command:** `bash -o pipefail -c set -e
python3 pmo-roadmap/tests/dw-core-tests.py DeliverySetupTest
python3 pmo-roadmap/tests/product-language-contract.py
python3 pmo-roadmap/tests/usability-journey-contract.py
pmo-roadmap/tests/workbench-explorer.sh
pmo-roadmap/tests/workbench-ui-smoke.sh
pmo-roadmap/tests/docs-lint.sh
pmo-roadmap/tests/docs-snippet-smoke.sh
pmo-roadmap/tests/canon-lint.sh
.githooks/dw check work-log-automation
.githooks/dw rider docs --check
pmo-roadmap/update.sh . --check
git diff --check
git diff --cached --check`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** 527f11887365ce88d74a8951843c0b0b8dad1650

```text
test_front_door_names_scope_three_modes_effects_and_permissions (__main__.DeliverySetupTest.test_front_door_names_scope_three_modes_effects_and_permissions) ... ok
test_human_cli_and_http_render_the_same_choice_and_readiness (__main__.DeliverySetupTest.test_human_cli_and_http_render_the_same_choice_and_readiness) ... ok
test_missing_or_invalid_inputs_name_the_delivery_decision_and_correction (__main__.DeliverySetupTest.test_missing_or_invalid_inputs_name_the_delivery_decision_and_correction) ... ok
test_setup_and_cancel_model_are_repeatable_and_write_nothing (__main__.DeliverySetupTest.test_setup_and_cancel_model_are_repeatable_and_write_nothing) ... ok

----------------------------------------------------------------------
Ran 4 tests in 6.258s

OK
product-language-contract: ok (10 concepts, 18 surfaces, 18 reserved terms, 10 fixtures)
usability-journey-contract: ok (13 journeys, 15 reachable states, 6 red fixtures; baseline 88 steps, 38 decisions, 81 engineering terms, 13 dead ends, 26 context switches)
dw-workbench: serving /private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/pmo-workbench-test.zxfzyc/repo
dw-workbench: http://127.0.0.1:19742/ (localhost or your own .ts.net tailnet; Ctrl-C to stop)
dw-workbench: writes require a guarded preview→apply content boundary or an exact step/run/program token; never stages, certifies, or commits
dw-workbench: shutting down
dw-workbench: serving /private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/pmo-workbench-test.zxfzyc/installed
dw-workbench: http://127.0.0.1:19743/ (localhost or your own .ts.net tailnet; Ctrl-C to stop)
dw-workbench: writes require a guarded preview→apply content boundary or an exact step/run/program token; never stages, certifies, or commits
workbench-explorer.sh: ok
dw-workbench: shutting down
dw-workbench: serving /private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/pmo-workbench-test.zxfzyc/repo
dw-workbench: http://127.0.0.1:19742/ (localhost or your own .ts.net tailnet; Ctrl-C to stop)
dw-workbench: writes require a guarded preview→apply content boundary or an exact step/run/program token; never stages, certifies, or commits
dw-workbench: shutting down
dw-workbench: serving /private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/pmo-ui-smoke.zX3ZKa/repo
dw-workbench: http://127.0.0.1:21547/ (localhost or your own .ts.net tailnet; Ctrl-C to stop)
dw-workbench: writes require a guarded preview→apply content boundary or an exact step/run/program token; never stages, certifies, or commits
workbench-ui-smoke.sh: ok (62 viewport renders: 23 data views + delivery setup/review + program planning/active/certified/revoked + attention + ambiguity, desktop+mobile)
dw-workbench: shutting down
dw-workbench: serving /private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/pmo-ui-smoke.zX3ZKa/dw-program-test.1ofc9lki/repo
dw-workbench: http://127.0.0.1:24229/ (localhost or your own .ts.net tailnet; Ctrl-C to stop)
dw-workbench: writes require a guarded preview→apply content boundary or an exact step/run/program token; never stages, certifies, or commits
docs-lint: ok (464 markdown files)
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
ERROR pmo-roadmap/pm/roadmap/work-log-automation/phase-27-usability-improvements/evidence-story-03.md: evidence exists but matching story is not done
```

### Captured run — 2026-07-24T09:49:39Z

- **Command:** `bash -o pipefail -c set -e
python3 pmo-roadmap/tests/dw-core-tests.py DeliverySetupTest
python3 pmo-roadmap/tests/product-language-contract.py
python3 pmo-roadmap/tests/usability-journey-contract.py
pmo-roadmap/tests/workbench-explorer.sh
pmo-roadmap/tests/docs-lint.sh
pmo-roadmap/tests/docs-snippet-smoke.sh
pmo-roadmap/tests/canon-lint.sh
node --check pmo-roadmap/workbench/app.js
python3 -m py_compile pmo-roadmap/lib/dw_pmo/delivery_setup.py pmo-roadmap/lib/dw_pmo/workbench.py pmo-roadmap/tests/autonomous-program-packaged-exam.py
.githooks/dw check work-log-automation
.githooks/dw rider docs --check
pmo-roadmap/update.sh . --check
git diff --check
git diff --cached --check`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 527f11887365ce88d74a8951843c0b0b8dad1650

```text
test_front_door_names_scope_three_modes_effects_and_permissions (__main__.DeliverySetupTest.test_front_door_names_scope_three_modes_effects_and_permissions) ... ok
test_human_cli_and_http_render_the_same_choice_and_readiness (__main__.DeliverySetupTest.test_human_cli_and_http_render_the_same_choice_and_readiness) ... ok
test_missing_or_invalid_inputs_name_the_delivery_decision_and_correction (__main__.DeliverySetupTest.test_missing_or_invalid_inputs_name_the_delivery_decision_and_correction) ... ok
test_setup_and_cancel_model_are_repeatable_and_write_nothing (__main__.DeliverySetupTest.test_setup_and_cancel_model_are_repeatable_and_write_nothing) ... ok

----------------------------------------------------------------------
Ran 4 tests in 6.207s

OK
product-language-contract: ok (10 concepts, 18 surfaces, 18 reserved terms, 10 fixtures)
usability-journey-contract: ok (13 journeys, 15 reachable states, 6 red fixtures; baseline 88 steps, 38 decisions, 81 engineering terms, 13 dead ends, 26 context switches)
dw-workbench: serving /private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/pmo-workbench-test.Uz4PVs/repo
dw-workbench: http://127.0.0.1:18063/ (localhost or your own .ts.net tailnet; Ctrl-C to stop)
dw-workbench: writes require a guarded preview→apply content boundary or an exact step/run/program token; never stages, certifies, or commits
dw-workbench: shutting down
dw-workbench: serving /private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/pmo-workbench-test.Uz4PVs/installed
dw-workbench: http://127.0.0.1:18064/ (localhost or your own .ts.net tailnet; Ctrl-C to stop)
dw-workbench: writes require a guarded preview→apply content boundary or an exact step/run/program token; never stages, certifies, or commits
workbench-explorer.sh: ok
dw-workbench: shutting down
dw-workbench: serving /private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/pmo-workbench-test.Uz4PVs/repo
dw-workbench: http://127.0.0.1:18063/ (localhost or your own .ts.net tailnet; Ctrl-C to stop)
dw-workbench: writes require a guarded preview→apply content boundary or an exact step/run/program token; never stages, certifies, or commits
docs-lint: ok (464 markdown files)
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
dw check: ok
dw rider docs: all rendered surfaces match canon
update.sh: up to date (vendored rails match source v1.14.0)
```
