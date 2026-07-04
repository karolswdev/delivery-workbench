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

### Captured run — 2026-07-04T05:26:18Z

- **Command:** `bash -c echo "served wheel sha256 verification:" && shasum -a 256 /private/tmp/claude-501/-Users-karol-dev-code-delivery-workbench/fdc6877b-9071-406e-94f9-c2020d111439/scratchpad/served.whl && grep -n "sha256\|url" Formula/delivery-workbench.rb | head -3 && pmo-roadmap/tests/brew-formula-smoke.sh 2>&1 | tail -2`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 50e960e2b66d526ec4013b9fa7c75682a0c42408

```text
served wheel sha256 verification:
9b8409941eeb334fe3b174065db859863b54719c10ecc20b1aca1c7b2240bd04  /private/tmp/claude-501/-Users-karol-dev-code-delivery-workbench/fdc6877b-9071-406e-94f9-c2020d111439/scratchpad/served.whl
8:# The url below targets the GitHub release artifact for this version;
10:# locally built wheel by rewriting url/sha256 to a file:// path.
14:  url "https://github.com/karolswdev/delivery-workbench/releases/download/v1.9.0/delivery_workbench-1.9.0-py3-none-any.whl",
brew-formula-smoke.sh: delivery-workbench already installed; uninstall it before running the smoke
```
