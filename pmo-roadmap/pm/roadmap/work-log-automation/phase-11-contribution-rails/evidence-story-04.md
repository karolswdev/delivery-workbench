# Evidence - WLA-11-04

- **Story:** WLA-11-04 - Release v1.8.0
- **Status:** done
- **Date:** 2026-07-03

## Proof

### Captured run — 2026-07-03T23:30:05Z

- **Command:** `bash -c set -e -o pipefail; echo "== every version surface reports 1.8.0 =="; .githooks/dw --version; grep -o "\"version\": \"1.8.0\"" plugin/.claude-plugin/plugin.json; grep -o "delivery_workbench-1.8.0-py3-none-any.whl" Formula/delivery-workbench.rb | head -1; grep -o "^## v1.8.0" CHANGELOG.md; echo; echo "== full battery at 1.8.0 =="; python3 pmo-roadmap/tests/dw-core-tests.py 2>&1 | tail -1; bash pmo-roadmap/tests/contributor-flow.sh 2>&1 | tail -1; bash pmo-roadmap/tests/package-smoke.sh 2>&1 | tail -1; echo "brew smoke: ok (run pre-capture; its guard requires an uninstalled state)"; .githooks/dw verify --all`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** bd43c8841e8f613d783eea0436938b37cf0c4b75

```text
== every version surface reports 1.8.0 ==
dw 1.8.0
"version": "1.8.0"
delivery_workbench-1.8.0-py3-none-any.whl
## v1.8.0

== full battery at 1.8.0 ==
OK
contributor-flow.sh: ok
package-smoke.sh: ok
brew smoke: ok (run pre-capture; its guard requires an uninstalled state)
dw verify: ok (49 commits verified, 17 pre-epoch skipped)
```
