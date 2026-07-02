# Evidence - WLA-6-06

- **Story:** WLA-6-06 - Right-size ceremony and unify template canon
- **Status:** done
- **Date:** 2026-07-02

## What shipped

- **Tiered contracts, decided by the gate.** `dw contract new --tier
  auto` (the default) picks the short form — stamped facts plus only
  the **No bypasses.** box — for commits that do not touch the roadmap
  tree; anything roadmap-shaped (which includes every story flip) gets
  the full rule set, and a hand-tampered `**Tier:** short` on a roadmap
  commit is refused (`contract-tier-mismatch`). `--tests-capture`
  implies the full tier. `PMO_CONTRACT_TIER=full` in
  `pre-commit.config` restores full ceremony everywhere, honored by
  generator and gate alike. Documented in PMO-CONTRACT.md §"Contract
  tiers"; porcelain gains a `tier=` line.
- **One status vocabulary, doc-and-constant parity-tested.**
  roadmap-builder §2.3 now carries the canonical declaration
  (`backlog | ready | in-progress | blocked | done`, done-synonyms
  `complete | closed | shipped`); PMO-CONTRACT rule 2 and the `.tmpl`
  files reference it instead of restating subsets; `STORY_STATUSES` in
  `dw_pmo.model` is the machine side, split from the looser
  phase-index vocabulary (`planned`/`not-started`), and a unit test
  parses the doc line and asserts equality with the constant. Project
  status got the same treatment in §2.1.
- **De-personalized canon, enforced by lint.** Private memory
  instructions (`~/.claude`, `feedback_*` keys), machine paths
  (`~/dev/reusable-processes`), and the Pantrybot worked examples are
  gone from every canonical surface — the examples moved intact to
  `templates/examples/` (roadmap-builder worked example + the
  project-extension example), which install never distributes. The new
  `tests/canon-lint.sh` greps all canonical surfaces for the forbidden
  patterns in CI, and caught two leftovers in `install.sh` on its
  first run.
- **Template reconciliation + lighter closure.** `story.md.tmpl` /
  `phase-status.md.tmpl` and builder §2 now agree section-for-section
  (the project-specific design-handoff lines left the canon with the
  example); "Integration / Cypress" became "Integration" in the tmpl,
  the builder, and `dw`'s embedded scaffold; `final-summary.md` slimmed
  from eight sections to four (outcome vs exit criteria, evidence
  index, surprises, handoff); evidence §2.4 now recommends captured
  runs and the `assets/` convention.

## Acceptance proof

Tier behavior is proven at three layers, all CI-run: unit tests
(auto-short for docs-only, forced-full via config, tampered-tier
refusal, `--tests-capture` tier bump), parity scenarios S24-S26
(short-form docs-only commit passes through the real shim; short-form
with a staged story is blocked; forced-full config), and the
agent-surface banner assertion (the inline template in a blocked
docs-only commit is the short form with live facts). Vocabulary parity
is `test_story_vocabulary_doc_parity`; canon cleanliness is
`canon-lint.sh` (green below). The framework README's dependency,
installer, and validation sections were re-verified against the actual
post-Phase-6 toolchain.

## Proof — captured runs (appended by `dw evidence capture`)

### Captured run — 2026-07-02T16:43:22Z

- **Command:** `pmo-roadmap/tests/gate-parity.sh`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** de8b953c88e83d43369c6a571fb2cca4f6b69d4b

```text
gate-parity.sh: ok
```

### Captured run — 2026-07-02T16:43:42Z

- **Command:** `pmo-roadmap/tests/canon-lint.sh`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** de8b953c88e83d43369c6a571fb2cca4f6b69d4b

```text
canon-lint.sh: ok
```

### Captured run — 2026-07-02T16:43:43Z

- **Command:** `python3 pmo-roadmap/tests/dw-core-tests.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** de8b953c88e83d43369c6a571fb2cca4f6b69d4b

```text
test_agent_docs_block_lifecycle (__main__.DwCoreTest.test_agent_docs_block_lifecycle) ... ok
test_apply_returns_changes_and_validation (__main__.DwCoreTest.test_apply_returns_changes_and_validation) ... ok
test_capture_appends_and_records (__main__.DwCoreTest.test_capture_appends_and_records) ... ok
test_capture_truncation_marker (__main__.DwCoreTest.test_capture_truncation_marker) ... ok
test_che
[PMO_EVIDENCE_OUTPUT_TRUNCATED]
```
