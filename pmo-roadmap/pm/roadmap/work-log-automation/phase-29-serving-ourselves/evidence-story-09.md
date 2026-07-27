# Evidence - WLA-29-09

- **Story:** WLA-29-09 - Keep the hook path healthy under worktrees
- **Status:** done
- **Date:** 2026-07-27

## Proof

### Captured run — 2026-07-27T08:05:11Z

- **Command:** `sh -c python3 -B pmo-roadmap/tests/dw-core-tests.py GateTest.test_doctor_detections_and_health StatusBriefingTest 2>&1 | tail -3 && git config core.hooksPath "$PWD/.githooks" && .githooks/dw doctor 2>&1 | grep "core.hooksPath" && .githooks/dw doctor --fix-hooks 2>&1 | grep "core.hooksPath" && git config core.hooksPath`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** dd5d99cf5135a46d7cfb889dd31fd603176722e1

```text
Ran 21 tests in 8.829s

OK
ok   core.hooksPath: /Users/karol/dev/code/delivery-workbench/.githooks — resolves to this clone's .githooks; run `.githooks/dw doctor --fix-hooks` to normalize to the relative form
ok   core.hooksPath: .githooks
.githooks
```
