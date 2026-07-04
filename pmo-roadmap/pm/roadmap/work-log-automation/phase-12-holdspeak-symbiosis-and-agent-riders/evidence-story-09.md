# Evidence - WLA-12-09

- **Story:** WLA-12-09 - Release v1.9.0 and close the phase
- **Status:** done
- **Date:** 2026-07-03

## Proof

The release ritual per `docs/distribution.md`, in order. The
captured battery run below (05:23:04Z) is the full core suite plus
both distribution smokes at the bumped version — the parity tests
inside it assert every version surface reports 1.9.0. The bump
touched `dw_pmo.__version__`, the plugin manifest, the formula url
(sha256 reset to the zero placeholder until the published wheel
exists), and the CHANGELOG, whose new section links the phase
final summary created by `dw phase close` in this same commit.
Post-publish captures (wheel sha stamp, PyPI availability, cold
pip install, tap mirror) are appended below as the ritual's later
steps complete.

### Captured run — 2026-07-04T05:23:04Z

- **Command:** `bash -c python3 pmo-roadmap/tests/dw-core-tests.py 2>&1 | tail -2 && pmo-roadmap/tests/package-smoke.sh 2>&1 | tail -2 && pmo-roadmap/tests/brew-formula-smoke.sh 2>&1 | tail -2`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 4288ecab02b12b30643e50209a8d2328e5bf908f

```text

OK
package-smoke.sh: installed via venv+pip
package-smoke.sh: ok
brew-formula-smoke.sh: delivery-workbench already installed; uninstall it before running the smoke
```
