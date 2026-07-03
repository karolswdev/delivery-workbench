# Evidence - WLA-9-05

- **Story:** WLA-9-05 - Release v1.6.0
- **Status:** done
- **Date:** 2026-07-03

## Proof

Release v1.6.0: `dw_pmo.__version__` bumped (the single source),
plugin manifest and formula artifact url bumped in lockstep,
pyproject stays dynamic by construction, and the CHANGELOG opens
with the v1.6.0 section covering Phase 8 (remote verification and
adoption) and Phase 9 (distribution) with links to both final
summaries. The parity test family enforces all of it — any surface
lagging the single source turns the unit suite red.

The captured run shows every surface reporting 1.6.0, the full
117-test suite green, both smokes rebuilding and passing against
the 1.6.0 artifacts (isolated install, packaged bootstrap to
doctor-green, defer rule; brew local-tap install, style clean), and
`dw verify --all` clean over the history at the release point. The
annotated `v1.6.0` tag is created on the release commit immediately
after it exists (tags cannot point at unborn commits, so the tag
itself is proven by `git tag -l`/`git show v1.6.0` post-commit, as
the story's test plan specifies); pushing commits, the tag, and
publishing artifacts remain user actions.

### Captured run — 2026-07-03T17:00:12Z

- **Command:** `bash -c set -e -o pipefail; echo "== every version surface reports 1.6.0 =="; .githooks/dw --version; grep -o "\"version\": \"1.6.0\"" plugin/.claude-plugin/plugin.json; grep -o "delivery_workbench-1.6.0-py3-none-any.whl" Formula/delivery-workbench.rb | head -1; grep -o "^## v1.6.0" CHANGELOG.md; grep -o "attr = \"dw_pmo.__version__\"" pyproject.toml; echo; echo "== full unit suite (parity family included) =="; python3 pmo-roadmap/tests/dw-core-tests.py 2>&1 | tail -3; echo "== 1.6.0 artifacts through both smokes =="; bash pmo-roadmap/tests/package-smoke.sh 2>&1 | grep "built\|: ok"; bash pmo-roadmap/tests/brew-formula-smoke.sh 2>&1 | grep "built\|style\|: ok"; echo; echo "== history verifies at the release point =="; .githooks/dw verify --all`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** f8e2ca9e3ee724684be2e05a3f388212e1c7f053

```text
== every version surface reports 1.6.0 ==
dw 1.6.0
"version": "1.6.0"
delivery_workbench-1.6.0-py3-none-any.whl
## v1.6.0
attr = "dw_pmo.__version__"

== full unit suite (parity family included) ==
Ran 117 tests in 12.048s

OK
== 1.6.0 artifacts through both smokes ==
package-smoke.sh: built delivery_workbench-1.6.0-py3-none-any.whl and delivery_workbench-1.6.0.tar.gz
package-smoke.sh: ok
brew-formula-smoke.sh: built delivery_workbench-1.6.0-py3-none-any.whl
brew-formula-smoke.sh: brew style: clean
brew-formula-smoke.sh: ok

== history verifies at the release point ==
dw verify: ok (37 commits verified, 17 pre-epoch skipped)
```
