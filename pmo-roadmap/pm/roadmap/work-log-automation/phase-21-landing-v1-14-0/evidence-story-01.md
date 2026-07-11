# Evidence - WLA-21-01

- **Story:** WLA-21-01 - Release v1.14.0
- **Status:** done
- **Date:** 2026-07-11

## Proof

One captured run (the contract's `--tests-capture`) carrying the
whole pre-tag verification at 1.14.0:

- **Full battery**: core 208 OK, telegram interface 147 OK,
  fitness 10 OK, docs-lint ok, plugin-validate ok.
- **Version surfaces in lockstep**: `dw --version` answers 1.14.0;
  source and vendored `__version__` byte-equal; plugin manifest;
  formula url at v1.14.0 (sha256 at the zero placeholder until the
  served wheel is verified); CHANGELOG section dated.
- **Both distribution smokes ok** — package (sdist + wheel +
  isolated install + doctor-green bootstrap) and brew (the desk's
  brew copy at 1.13.0 was uninstalled first per the WLA-19-03
  lesson, now recorded in the story notes; reinstalled from the
  tap post-publication).

Publication follows under the standing authorization; the
confirmations (PyPI JSON, cold pip install, brew, CI) are recorded
in the formula-stamp rider commit, as with the last six releases.

### Captured run — 2026-07-11T21:20:24Z

- **Command:** `bash -c echo "== full battery at 1.14.0 =="
/usr/bin/python3 pmo-roadmap/tests/dw-core-tests.py 2>&1 | grep -E "^(OK|FAILED|Ran)"
/usr/bin/python3 pmo-roadmap/tests/telegram-interface-tests.py 2>&1 | grep -E "^(OK|FAILED|Ran)"
/usr/bin/python3 pmo-roadmap/tests/telegram-fitness-tests.py 2>&1 | grep -E "^(OK|FAILED|Ran)"
bash pmo-roadmap/tests/docs-lint.sh 2>&1 | tail -1
bash pmo-roadmap/tests/plugin-validate.sh 2>&1 | tail -1
echo
echo "== version surfaces =="
.githooks/dw --version
grep -n "__version__" pmo-roadmap/lib/dw_pmo/__init__.py .githooks/dw_pmo/__init__.py
grep -n "\"version\"" plugin/.claude-plugin/plugin.json
grep -n "v1.14.0" Formula/delivery-workbench.rb
grep -n "^## v1.14.0" CHANGELOG.md
echo
echo "== distribution smokes =="
bash pmo-roadmap/tests/package-smoke.sh 2>&1 | tail -1
bash pmo-roadmap/tests/brew-formula-smoke.sh 2>&1 | tail -1`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 5f8976333b94c71b17c0834d0fc85823049ff2f5

```text
== full battery at 1.14.0 ==
Ran 208 tests in 113.114s
OK
Ran 147 tests in 47.589s
OK (skipped=10)
Ran 10 tests in 1.058s
OK
docs-lint.sh: ok (3s)
plugin-validate.sh: ok

== version surfaces ==
dw 1.14.0
pmo-roadmap/lib/dw_pmo/__init__.py:152:__version__ = "1.14.0"
.githooks/dw_pmo/__init__.py:152:__version__ = "1.14.0"
3:  "version": "1.14.0",
14:  url "https://github.com/karolswdev/delivery-workbench/releases/download/v1.14.0/delivery_workbench-1.14.0-py3-none-any.whl",
10:## v1.14.0 — 2026-07-11

== distribution smokes ==
package-smoke.sh: ok
brew-formula-smoke.sh: ok
```
