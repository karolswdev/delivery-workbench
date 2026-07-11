# Evidence - WLA-19-03

- **Story:** WLA-19-03 - Release v1.13.0
- **Status:** done
- **Date:** 2026-07-11

## Proof

Four captured runs; the 19:39:05Z failure is an honest iteration,
the other three are authoritative:

1. **19:38:21Z — the full battery + version-surface walk at
   1.13.0** (the contract's `--tests-capture` run): core suite 208
   OK (includes the parity family), telegram interface 108 OK
   (1 skip), telegram fitness 8 OK, docs-lint ok,
   plugin-validate ok; then every version surface read back at
   1.13.0 — `dw --version`, source and vendored `__version__`,
   the plugin manifest, the formula url (sha256 reset to the zero
   placeholder until publication), and the CHANGELOG section
   header.
2. **19:38:48Z — `tests/package-smoke.sh`**: sdist + wheel build
   and isolated install at 1.13.0, doctor-green bootstrap.
3. **19:39:05Z — brew smoke, REFUSED** (exit 1): the desk still
   had the brew package installed (at 1.8.0); the smoke rightly
   refuses to run beside it. Uninstalled, re-ran.
4. **19:39:23Z — `tests/brew-formula-smoke.sh`**: green — the
   1.13.0 formula installs from a locally built wheel and
   `dw --version` answers 1.13.0.

Publication (standing authorization, 2026-07-03) follows this
commit: annotated `v1.13.0` tag, push, GitHub Release with
hash-verified artifacts, PyPI via the release workflow's trusted
publisher, then the formula sha256 stamp and tap mirror as the
usual rider commit — the post-publication confirmations are
recorded there.

### Captured run — 2026-07-11T19:38:21Z

- **Command:** `bash -c echo "== full battery at 1.13.0 =="
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
grep -n "v1.13.0" Formula/delivery-workbench.rb
grep -n "^## v1.13.0" CHANGELOG.md`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 98878a10a341182c11865b1146a86ef45ae5bfe8

```text
== full battery at 1.13.0 ==
Ran 208 tests in 13.635s
OK
Ran 108 tests in 6.609s
OK (skipped=1)
Ran 8 tests in 0.111s
OK
docs-lint.sh: ok (0s)
plugin-validate.sh: ok

== version surfaces ==
dw 1.13.0
pmo-roadmap/lib/dw_pmo/__init__.py:152:__version__ = "1.13.0"
.githooks/dw_pmo/__init__.py:152:__version__ = "1.13.0"
3:  "version": "1.13.0",
14:  url "https://github.com/karolswdev/delivery-workbench/releases/download/v1.13.0/delivery_workbench-1.13.0-py3-none-any.whl",
10:## v1.13.0 — 2026-07-11
```

### Captured run — 2026-07-11T19:38:48Z

- **Command:** `bash pmo-roadmap/tests/package-smoke.sh`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 98878a10a341182c11865b1146a86ef45ae5bfe8

```text
package-smoke.sh: skipping unhealthy interpreter: python3
package-smoke.sh: building with: /usr/bin/python3 (Python 3.9.6)
* Creating isolated environment: venv+pip...
* Installing packages in isolated environment:
  - setuptools>=77
* Getting build dependencies for sdist...
warning: no previously-included files matching '*.pyc' found anywhere in distribution
* Building sdist...
warning: no previously-included files matching '*.pyc' found anywhere in distribution
* Building wheel from sdist
* Creating isolated environment: venv+pip...
* Installing packages in isolated environment:
  - setuptools>=77
* Getting build dependencies for wheel...
warning: no previously-included files matching '__pycache__/*' found anywhere in distribution
warning: no previously-included files matching '*.pyc' found anywhere in distribution
* Building wheel...
warning: no previously-included files matching '__pycache__/*' found anywhere in distribution
warning: no previously-included files matching '*.pyc' found anywhere in distribution
package-smoke.sh: built delivery_workbench-1.13.0-py3-none-any.whl and delivery_workbench-1.13.0.tar.gz
package-smoke.sh: pipx cannot create environments here; falling back to venv+pip
WARNING: You are using pip version 21.2.4; however, version 26.0.1 is available.
You should consider upgrading via the '/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/pmo-package-smoke.DEazLm/appenv/bin/python -m pip install --upgrade pip' command.
package-smoke.sh: installed via venv+pip
package-smoke.sh: ok
```

### Captured run — 2026-07-11T19:39:05Z

- **Command:** `bash pmo-roadmap/tests/brew-formula-smoke.sh`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** 98878a10a341182c11865b1146a86ef45ae5bfe8

```text
brew-formula-smoke.sh: delivery-workbench already installed; uninstall it before running the smoke
```

### Captured run — 2026-07-11T19:39:23Z

- **Command:** `bash pmo-roadmap/tests/brew-formula-smoke.sh`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 98878a10a341182c11865b1146a86ef45ae5bfe8

```text
* Creating isolated environment: venv+pip...
* Installing packages in isolated environment:
  - setuptools>=77
* Getting build dependencies for wheel...
warning: no previously-included files matching '*.pyc' found anywhere in distribution
* Building wheel...
warning: no previously-included files matching '*.pyc' found anywhere in distribution
brew-formula-smoke.sh: built delivery_workbench-1.13.0-py3-none-any.whl
brew-formula-smoke.sh: brew style: clean
brew-formula-smoke.sh: ok
```
