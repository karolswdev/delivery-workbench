# Evidence - WLA-9-04

- **Story:** WLA-9-04 - Author a Homebrew formula on a local tap
- **Status:** done
- **Date:** 2026-07-03

## Proof

Deliverables:

- `Formula/delivery-workbench.rb` — tracked in-repo as the source of
  truth for the future public tap. Strategy: unzip the pure-python
  wheel into `libexec` and write a thin interpreter shim — no pip,
  no venv, no network at install time. Skipping
  `Language::Python::Virtualenv` is a recorded waiver: the runtime
  is stdlib-only, so there are no resources to vendor, and the
  simpler install is fully auditable. The tracked url targets the
  GitHub release artifact (sha256 placeholder stamped at
  publication); `brew style` clean after adopting
  `formula_opt_bin`.
- `tests/brew-formula-smoke.sh` — Homebrew ≥6 refuses path installs,
  so the smoke creates a throwaway local tap (`brew tap-new
  --no-git pmo-smoke/local`), rewrites url/sha256 to the locally
  built wheel, installs from the tap, proves `dw --version` truth,
  bootstraps a fixture repo to doctor-green with the brew-installed
  `dw`, re-proves the defer-to-repo rule, then uninstalls and
  untaps. Skips cleanly where brew is absent; wired into CI on the
  macOS leg only (ubuntu runners carry linuxbrew, which would
  attempt a slow real install).
- README "Install without cloning" section covering both channels,
  honestly marked as from-local-build until publication; formula
  version added to the parity test family.

`brew audit` proper requires a published tap with a reachable url —
recorded as part of the publication follow-up; `brew style` (the
locally runnable subset) is clean.

### Captured run — 2026-07-03T16:55:58Z

- **Command:** `bash -c set -e -o pipefail; bash pmo-roadmap/tests/brew-formula-smoke.sh 2>&1 | grep "^brew-formula-smoke"; python3 pmo-roadmap/tests/dw-core-tests.py DwCoreTest 2>&1 | tail -3; bash pmo-roadmap/tests/docs-lint.sh 2>&1 | tail -1`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 218f2d771afbb556640b77eddeeda765502e7dfe

```text
brew-formula-smoke.sh: built delivery_workbench-1.5.0-py3-none-any.whl
brew-formula-smoke.sh: brew style: clean
brew-formula-smoke.sh: ok
Ran 60 tests in 0.439s

OK
docs-lint.sh: ok (0s)
```
