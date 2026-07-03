# Evidence - WLA-9-02

- **Story:** WLA-9-02 - Package the framework for pipx
- **Status:** done
- **Date:** 2026-07-03

## Proof

Deliverables:

- `pyproject.toml` — distribution `delivery-workbench`, import
  package `dw_pmo` from `pmo-roadmap/lib`, version dynamic from
  `dw_pmo.__version__`, `dependencies = []` (stdlib-only runtime),
  python ≥ 3.9, one console script `dw = dw_pmo.launcher:main`.
- `setup.py` — a single `build_py` hook assembling
  `dw_pmo/_payload/` from the source tree (12-source inventory per
  `docs/distribution.md`); `MANIFEST.in` makes sdist→wheel identical
  to repo→wheel. Wheel inspected: 55 payload files including
  `install.sh`, hooks, `bin/dw`, `lib/dw_pmo/verify.py`, templates,
  workbench assets, bootstrap scripts.
- `lib/dw_pmo/launcher.py` — the global `dw`: bootstrap verbs
  (install/update/adopt-project/new-project/intake) dispatch to the
  payload scripts; inside an adopted repo it execs `.githooks/dw`
  unconditionally with a staleness note when versions differ;
  outside repos it delegates to the packaged `bin/dw`.
- Tests: `tests/package-smoke.sh` (interpreter health probe → build
  sdist+wheel → isolated install → version truth → packaged
  bootstrap of a fixture to doctor-green from outside the checkout →
  defer-to-repo proof via a marker script); `LauncherTest` (3 cases)
  and a pyproject parity test in dw-core-tests.py (suite 112 → 116);
  CI gains a `package-smoke` job and the shellcheck/syntax lists
  pick up both new suites (verify-range.sh had been missing —
  retroactively added).

Environment notes recorded honestly: this machine's brew python
3.14 has a broken `pyexpat` (missing `_XML_SetAllocTrackerActivationThreshold`
against `/usr/lib/libexpat.1.dylib`), which breaks venv+ensurepip and
therefore pipx entirely — an environment defect, not a package one.
The smoke's health probe skips it, builds with `/usr/bin/python3`
(3.9.6 — exactly the package floor), and falls back to venv+pip,
which exercises the same wheel and entry point. CI's healthy runners
take the pipx path.

### Captured run — 2026-07-03T16:46:01Z

- **Command:** `bash -c set -e -o pipefail; bash pmo-roadmap/tests/package-smoke.sh 2>&1 | grep "^package-smoke"; python3 pmo-roadmap/tests/dw-core-tests.py 2>&1 | tail -3`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 0bd3b518d5cbec878c538d6c2339b83300175482

```text
package-smoke.sh: skipping unhealthy interpreter: python3
package-smoke.sh: building with: /usr/bin/python3 (Python 3.9.6)
package-smoke.sh: built delivery_workbench-1.5.0-py3-none-any.whl and delivery_workbench-1.5.0.tar.gz
package-smoke.sh: pipx cannot create environments here; falling back to venv+pip
package-smoke.sh: installed via venv+pip
package-smoke.sh: ok
Ran 116 tests in 12.020s

OK
```
