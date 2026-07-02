# Evidence - WLA-6-08

- **Story:** WLA-6-08 - Harden CI, parity, and portability testing
- **Status:** done
- **Date:** 2026-07-02

## What shipped

- **Negative-path coverage with named rules.** The parity suite gained
  an `expect_rule` helper: every failing scenario now asserts the exact
  gate rule id in porcelain output (evidence-missing,
  contract-unchecked, contract-missing, atomicity,
  evidence-deletion-orphans-story, orphan-evidence,
  contract-missing-box, contract-sample-mismatch, contract-unknown-box
  — joining the previously asserted index-tree/tier/tests-capture
  rules), and the documented remediations unblock in-suite (e.g. the
  synonym-flip scenario now pairs the evidence and passes). The
  remaining rule family is asserted per-rule in the 55-test unit suite.
- **The `pre-commit.local` seam survives `update.sh`** and still blocks
  afterward — proven in parity S14's extension (acceptance #5).
- **CI matrix and hygiene** (`validation.yml` rewritten): the full
  integration set runs on `ubuntu-latest` AND `macos-latest`
  (fail-fast off); a dedicated shellcheck job lints every shipped
  script; a python-floor job runs the core suite on the declared 3.9
  floor via setup-python; `permissions: contents: read`; a concurrency
  group with cancel-in-progress; push filtered to `main` so PR branches
  run once; `actions/checkout` bumped to v5 (clearing the Node 20
  deprecation annotation).
- **shellcheck is clean over all 19 shipped scripts** (0 findings,
  shellcheck 0.11): SC2295 inner-expansion quoting fixed across the
  installer and bootstrap scripts, seam variables and
  sourced-consumer functions carry reasoned `disable` directives, a
  dead test variable was removed, literal `done` arguments quoted, and
  intentional-literal patterns (`~/.claude` grep, awk programs,
  markdown backticks) documented inline.
- **A real portability bug found and fixed while hardening:** the
  bash 5.2 `patsub_replacement` fix from WLA-6-07 (quoting replacement
  strings) turned out to insert literal quotes on bash 3.2 — scaffolds
  rendered `"DEMO"-0-01` and the placeholder-row substitution silently
  stopped matching on macOS. The portable resolution:
  `shopt -u patsub_replacement 2>/dev/null || true` in all three
  bootstrap scripts with unquoted replacements, verified on bash 3.2
  locally and bash 5.2 in CI. This is exactly the class of divergence
  the new two-OS matrix exists to catch on every push.
- Docs: the framework README conventions now declare the python3 ≥ 3.9
  floor and the two-OS CI posture; the root README validation section
  includes the shellcheck sweep.

## Proof — captured runs (appended by `dw evidence capture`)

### Captured run — 2026-07-02T18:16:57Z

- **Command:** `sh -c shellcheck pmo-roadmap/install.sh pmo-roadmap/update.sh pmo-roadmap/hooks/pre-commit pmo-roadmap/hooks/commit-msg pmo-roadmap/hooks/post-commit pmo-roadmap/bin/work-log-read pmo-roadmap/bin/work-log-summarize pmo-roadmap/bootstrap/*.sh pmo-roadmap/tests/*.sh demos/scripts/*.sh && echo "shellcheck: all shipped shell clean (0 findings)"`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 636d202e451c80d4634b46a9538ace7901c0ca5b

```text
shellcheck: all shipped shell clean (0 findings)
```

### Captured run — 2026-07-02T18:17:08Z

- **Command:** `pmo-roadmap/tests/gate-parity.sh`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 636d202e451c80d4634b46a9538ace7901c0ca5b

```text
gate-parity.sh: ok
```

### Captured run — 2026-07-02T18:17:32Z

- **Command:** `python3 pmo-roadmap/tests/dw-core-tests.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 636d202e451c80d4634b46a9538ace7901c0ca5b

```text
test_agent_docs_block_lifecycle (__main__.DwCoreTest.test_agent_docs_block_lifecycle) ... ok
test_apply_returns_changes_and_validation (__main__.DwCoreTest.test_apply_returns_changes_and_validation) ... ok
test_capture_appends_and_records (__main__.DwCoreTest.test_capture_appends_and_records) ... ok
test_capture_truncation_marker (__main__.DwCoreTest.test_capture_truncation_marker) ... ok
test_check_broken (__main__.DwCoreTest.test_check_broken) ... ok
test_check_clean (__main__.DwCoreTest.test_
[PMO_EVIDENCE_OUTPUT_TRUNCATED]
```
