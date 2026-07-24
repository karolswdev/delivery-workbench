# Evidence - WLA-27-02

- **Story:** WLA-27-02 - Define whole-task journeys and usability proof
- **Status:** done
- **Date:** 2026-07-24

## Proof

The reviewed
[whole-task journey guide](../../../../../docs/usability-journeys.md) and four
versioned fixture documents define thirteen journeys, fifteen reachable
states, three explicit operating tiers, the seven Phase 26 operator questions,
and bidirectional ownership for WLA-27-03 through WLA-27-10. Every journey
fixes its start, ordinary question, canonical visible facts, bounded actions,
one success next step, one safe refusal/recovery next step, and the exact
**Technical details** state and return path. `vanilla` remains the healthy
default; `bounded-run` and `program` are separate optional choices whose starts
require their existing explicit boundaries.

The deterministic
[`usability-journey-contract.py`](../../../../tests/usability-journey-contract.py)
checker validates exact shapes, unique inventories, application-language
concepts, reserved-term hygiene, all source models against `docs/interop.md`,
action effects against five existing mutation boundaries plus explicit
no-authority read-only inspection, tier-change confirmation, question and
screen coverage, exact next steps, safe exits, technical-detail reachability,
downstream reuse, docs/README/CI wiring, and the complete baseline. Its six
planted mutations prove rejection of an incomplete starting state, missing
safe exit, invented authority, inaccessible details, ambiguous next step, and
silent tier upgrade.

Reachability reuses the shipped Workbench harness instead of inventing a
parallel UI fixture model. Each state maps canonical model paths to an
existing `capture_id`; the checker requires both its desktop and mobile render,
and the captured integration run rebuilt and rendered all 60 views from the
production core/read models. The same run passed 46 selected status, bounded
authority, Program Studio, and live-program surface tests. No production UI,
workflow, authority, or machine-contract source changed in this story.

The recorded pre-redesign baseline covers every journey at 1440x900 and
390x844: 88 visible steps, 38 user decisions, 81 exposed engineering-term
entries, 13 dead ends, and 26 context switches. These are descriptive,
reproducible comparison categories, not a generated usability score.

### Captured run — 2026-07-24T07:59:36Z

- **Command:** `bash -o pipefail -c set -e
/usr/bin/python3 --version
/usr/bin/python3 -m py_compile pmo-roadmap/tests/usability-journey-contract.py
/usr/bin/python3 pmo-roadmap/tests/usability-journey-contract.py
python3 pmo-roadmap/tests/usability-journey-contract.py
python3 pmo-roadmap/tests/product-language-contract.py
python3 pmo-roadmap/tests/dw-core-tests.py -q StatusBriefingTest OrchestrationRunAuthorityTest ProgramSurfaceTest ProgramStudioTest
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
- **Exit code:** 0
- **Index-tree:** 25d3a243dca61ce0f596d133a43913c1c050019d

```text
Python 3.9.6
usability-journey-contract: ok (13 journeys, 15 reachable states, 6 red fixtures; baseline 88 steps, 38 decisions, 81 engineering terms, 13 dead ends, 26 context switches)
usability-journey-contract: ok (13 journeys, 15 reachable states, 6 red fixtures; baseline 88 steps, 38 decisions, 81 engineering terms, 13 dead ends, 26 context switches)
product-language-contract: ok (10 concepts, 18 surfaces, 18 reserved terms, 10 fixtures)
dw-workbench: 127.0.0.1 "GET /api/programs/program-5c9012b954bbde46ff1664c4/events?from=0&follow=0 HTTP/1.1" 200 -
----------------------------------------------------------------------
Ran 46 tests in 44.449s

OK
dw-workbench: shutting down
dw-workbench: serving /private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/pmo-ui-smoke.euC4IS/repo
dw-workbench: http://127.0.0.1:21678/ (localhost or your own .ts.net tailnet; Ctrl-C to stop)
dw-workbench: writes require a guarded preview→apply content boundary or an exact step/run/program token; never stages, certifies, or commits
workbench-ui-smoke.sh: ok (60 viewport renders: 23 data views + empty Studio + program planning/active/certified/revoked + attention + ambiguity, desktop+mobile)
dw-workbench: shutting down
dw-workbench: serving /private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/pmo-ui-smoke.euC4IS/dw-program-test.p9lfbr3s/repo
dw-workbench: http://127.0.0.1:24360/ (localhost or your own .ts.net tailnet; Ctrl-C to stop)
dw-workbench: writes require a guarded preview→apply content boundary or an exact step/run/program token; never stages, certifies, or commits
docs-lint: ok (461 markdown files)
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

## Manual wide/narrow review

All 60 final captures were also retained locally under ignored
`.tmp/wla27-final-baseline` while the findings were checked against
`baseline-v1.json`.

- Healthy ordinary work is reachable, but contract, gate, workspace, and
  deliberate-step language leads the arrival view; on narrow screens the
  project and safe action move below stacked protocol cards.
- Empty Program Studio is technically healthy, but the large program editor
  visually outweighs the optionality explanation and can look like required
  setup.
- Plan and team design lead with graph node, topology, role, and exact
  capability structures. Narrow layouts make the graph, active editor field,
  and outcome difficult to keep in view together.
- Preflight leads with semantic/document hashes, exact capability requests,
  profiles, budget field names, and scheduling waves rather than one delivery
  readiness answer.
- Live, failed-review, and human-decision states are reconstructable from
  exact cards and graphs, but generated identifiers, event integrity,
  authority state, and counters precede ownership, consequence, and next
  action—most strongly on mobile.
- Remaining permission and cost are precise but distributed across a raw
  workflow binding and many counters. Stop/revoke consequences likewise
  require moving between live state, exact preview, and stopped state.
- The completion specimen simultaneously presents `running`,
  `story-certified`, and `integration-required`, so the current application
  does not lead with whether one work item or the whole delivery is complete.
- Exact data is reachable through `JSON`, but that tab is not yet the explicit
  **Technical details** boundary and does not preserve the ordinary task
  context on return.

### Captured run — 2026-07-24T08:08:35Z

- **Command:** `bash -o pipefail -c set -e
/usr/bin/python3 pmo-roadmap/tests/usability-journey-contract.py
python3 pmo-roadmap/tests/usability-journey-contract.py
python3 pmo-roadmap/tests/product-language-contract.py
pmo-roadmap/tests/docs-lint.sh
pmo-roadmap/tests/canon-lint.sh
.githooks/dw check work-log-automation
.githooks/dw rider docs --check
pmo-roadmap/update.sh . --check
git diff --check
git diff --cached --check`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 6e2005d8ea7101c83134b0980e26cf310636f423

```text
usability-journey-contract: ok (13 journeys, 15 reachable states, 6 red fixtures; baseline 88 steps, 38 decisions, 81 engineering terms, 13 dead ends, 26 context switches)
usability-journey-contract: ok (13 journeys, 15 reachable states, 6 red fixtures; baseline 88 steps, 38 decisions, 81 engineering terms, 13 dead ends, 26 context switches)
product-language-contract: ok (10 concepts, 18 surfaces, 18 reserved terms, 10 fixtures)
docs-lint: ok (462 markdown files)
docs-lint.sh: ok (0s)
canon-lint.sh: ok
dw check: ok
dw rider docs: all rendered surfaces match canon
update.sh: up to date (vendored rails match source v1.14.0)
```
