# Evidence - WLA-22-02

- **Story:** WLA-22-02 - dw status — one deterministic core and CLI
- **Status:** done
- **Date:** 2026-07-15

## Proof

### Captured run — 2026-07-16T01:08:52Z

- **Command:** `bash -o pipefail -c python3 pmo-roadmap/tests/dw-core-tests.py 2>&1 | tail -n 10 && bash pmo-roadmap/tests/roadmap-cli.sh && bash pmo-roadmap/tests/adoption-discovery.sh && bash pmo-roadmap/tests/docs-lint.sh && bash pmo-roadmap/tests/canon-lint.sh && pmo-roadmap/update.sh . --check && .githooks/dw check work-log-automation && git diff --check`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 85da3eade3a27bbb5000a1a61c0386ec9f3f05df

```text

----------------------------------------------------------------------
Ran 218 tests in 19.655s

OK
dw hook: claude — 4 installed, 0 already present in /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.z2wf4zlv/settings.json
dw hook: claude — 0 installed, 4 already present in /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.z2wf4zlv/settings.json
dw hook: claude — 4 installed, 0 already present in /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.x8ff9b08/settings.json
dw hook: claude — 4 installed, 0 already present in /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.gt85ith_/settings.json
dw hook: claude — 4 removed from /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.gt85ith_/settings.json
roadmap-cli.sh: ok
adoption-discovery.sh: ok
docs-lint: ok (361 markdown files)
docs-lint.sh: ok (1s)
canon-lint.sh: ok
update.sh: up to date (vendored rails match source v1.14.0)
dw check: ok
```
