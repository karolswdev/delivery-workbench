# Evidence - WLA-26-06

- **Story:** WLA-26-06 - Build the visual program and workflow studio
- **Status:** done
- **Date:** 2026-07-22

## Proof

### Implementation and review

- `program_studio.py` builds the optional inventory and document model from the
  same program, workflow, organization, planning, and deliberation compilers
  used outside the browser. Source, vendored runtime, and wheel exports remain
  byte-equivalent; an absent `pm/programs/`, `pm/workflows/`, or
  `pm/organizations/` tree is a healthy empty inventory.
- Workbench exposes read-only inventory/detail endpoints plus explicit guarded
  preview and apply endpoints. The ordinary `#/` route is unchanged;
  `#/program-studio` is an additive destination with a neutral no-program state,
  no background polling, no grant, no work start, and no setup demand.
- Design renders workflow role lanes, nested subflows, fan-out/fan-in, bounded
  loop/debate containers, artifact/verdict/gate routes, and organization teams,
  verifier separation, councils, meta-verifiers, and architects. Keyboard node
  movement/selection, nested drill-down, inspectors, and responsive graph
  scrolling preserve access on desktop and narrow mobile viewports.
- Program views expose exact roadmap scope, binding candidates, phase architect
  gates, budgets, stops, and capabilities. Simulate covers candidate assignment,
  nested execution, active debate, verifier failure, budget exhaustion, phase
  transition, and completion using compiler-derived state and finite envelopes.
- Validate links every shared-compiler diagnostic to the corresponding node,
  inspector control, or exact JSON pointer. JSON remains a complete authoring
  surface. Embedded config plus document, semantic, and layout hashes prove
  lossless graph/config round trips and keep node placement authority-neutral.
- Authority preview distinctly groups work/verdict requests and the separately
  named evidence, integration, certification, Git, and roadmap rails for
  advisory, checkpointed, and continuous modes. It describes potential grant
  boundaries but creates no grant or runtime state.
- Saving and deleting require previewed content, diff, source fingerprint, and
  operation fingerprint. Apply revalidates the exact plan, rejects stale or
  escaping paths, writes only one declared tracked policy atomically, and rolls
  back on failure. Runtime-effect assertions remain false throughout.

### Acceptance mapping

- Complete authoring and round trip: all three policy families expose graph and
  full JSON views; golden tests preserve exact config, semantic, document, and
  layout hashes through graph→config→graph conversion.
- Visual grammar and accessibility: nested workflow, bounded loop/debate,
  separation-of-duties organization, council/meta/architect, artifact, verdict,
  budget, capability, and stop constructs have distinct nodes/routes plus
  keyboard and mobile inspector access.
- Shared validation and simulation: exact diagnostic focus targets and seven
  deterministic scenario projections expose candidate selection, finite bounds,
  green/red/debate/repair/exhaustion/phase routes before authority exists.
- Guarded mutation: preview/apply parity, stale fingerprint refusal, one-file
  containment, path-escape refusal, atomic rollback, and no-runtime-effect
  assertions cover save and delete.
- Vanilla compatibility: empty API/UI golden cases preserve the Workbench front
  door, create no policy directories or state, and introduce no poller, warning,
  blocking setup, or changed default route.
- Authority honesty: previews separate all sensitive rails, render each mode,
  and explicitly prove that viewing, editing, and saving grant nothing.
- Viewport proof: the smoke matrix rendered 52 desktop/mobile combinations,
  including empty, nested, debate-active, verifier-failed, budget-exhausted,
  phase-transition, complete, Validate, JSON, and Authority states without
  clipping or an unreachable inspector.

### Verification summary

- Core suite: 395/395 on Python 3.14 and 395/395 on the Python 3.9 floor.
- Focused Studio suite: 8/8 on both interpreter floors.
- Fresh wheel package smoke: passed on Python 3.9, including source/vendored/
  installed parity, empty inventory, round trip, preview, and no ambient policy.
- Workbench explorer and the 52-viewport UI smoke matrix passed; nested and
  authority desktop/mobile captures were also inspected manually.
- Canon, documentation, snippet, roadmap, rider, update-parity, syntax, and diff
  checks passed.

### Captured run — 2026-07-22T21:50:31Z

- **Command:** `bash -o pipefail -c set -e
python3 pmo-roadmap/tests/dw-core-tests.py -q -k ProgramStudioTest
/usr/bin/python3 pmo-roadmap/tests/dw-core-tests.py -q -k ProgramStudioTest
bash pmo-roadmap/tests/workbench-explorer.sh
bash pmo-roadmap/tests/workbench-ui-smoke.sh
bash pmo-roadmap/tests/canon-lint.sh
bash pmo-roadmap/tests/docs-lint.sh
bash pmo-roadmap/tests/docs-snippet-smoke.sh
./.githooks/dw check work-log-automation
./.githooks/dw rider docs --check
pmo-roadmap/update.sh . --check
git diff --check
git diff --cached --check`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** b9aef53375af3674b2a89bff4f5901a6f5f6189d

```text
----------------------------------------------------------------------
Ran 8 tests in 0.109s

OK
----------------------------------------------------------------------
Ran 8 tests in 0.127s

OK
dw-workbench: serving /private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/pmo-workbench-test.xwB95o/repo
dw-workbench: http://127.0.0.1:18791/ (localhost or your own .ts.net tailnet; Ctrl-C to stop)
dw-workbench: writes require a guarded preview→apply content boundary or an exact step/run token; never stages, certifies, or commits
dw-workbench: shutting down
dw-workbench: serving /private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/pmo-workbench-test.xwB95o/installed
dw-workbench: http://127.0.0.1:18792/ (localhost or your own .ts.net tailnet; Ctrl-C to stop)
dw-workbench: writes require a guarded preview→apply content boundary or an exact step/run token; never stages, certifies, or commits
workbench-explorer.sh: ok
dw-workbench: shutting down
dw-workbench: serving /private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/pmo-workbench-test.xwB95o/repo
dw-workbench: http://127.0.0.1:18791/ (localhost or your own .ts.net tailnet; Ctrl-C to stop)
dw-workbench: writes require a guarded preview→apply content boundary or an exact step/run token; never stages, certifies, or commits
workbench-ui-smoke.sh: ok (52 viewport renders: 23 data views + empty Studio + attention + ambiguity, desktop+mobile)
dw-workbench: shutting down
dw-workbench: serving /private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/pmo-ui-smoke.w5sokU/repo
dw-workbench: http://127.0.0.1:21092/ (localhost or your own .ts.net tailnet; Ctrl-C to stop)
dw-workbench: writes require a guarded preview→apply content boundary or an exact step/run token; never stages, certifies, or commits
canon-lint.sh: ok
docs-lint: ok (439 markdown files)
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
dw check: ok
dw rider docs: all rendered surfaces match canon
update.sh: up to date (vendored rails match source v1.14.0)
```
