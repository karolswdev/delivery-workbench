# WLA-9-02 - Package the framework for pipx

- **Project:** work-log-automation
- **Phase:** 9
- **Status:** backlog
- **Depends on:** WLA-9-01
- **Unblocks:** WLA-9-03, WLA-9-04
- **Owner:** unassigned

## Problem

"Clone the framework repo to adopt a different repo" is the largest
single adoption tax left. A pipx-installable package that carries
the bootstrap commands and the vendorable payload turns adoption
into `pipx install …` + two commands, without touching the
vendored-rails architecture.

## Scope

- **In:** `pyproject.toml` at the repo root per the design contract:
  package `delivery-workbench`, import package `dw_pmo` (sourced
  from `pmo-roadmap/lib/`), version single-sourced from
  `dw_pmo.__version__`, stdlib-only runtime (no install_requires),
  python floor matching CI's 3.9 leg. Console entry points from the
  design doc (global `dw` that defers to a repo's `.githooks/dw`
  when present, plus the install/update/adopt bootstrap surface).
  The payload (hooks, bin, templates, workbench assets, bootstrap
  scripts) ships as package data; `install.sh`/`update.sh` (or their
  packaged equivalents) resolve it from the installed package as
  well as from a checkout. Build proven locally without network
  isolation surprises (`--no-build-isolation` with system
  setuptools, or `pipx run build` — whichever the design doc
  chose). A test `pmo-roadmap/tests/package-smoke.sh`: build sdist +
  wheel, `pipx install` from the local artifact, run the packaged
  bootstrap against a fixture repo, `dw doctor` green there, and
  the defer-to-repo rule proven inside the fixture.
- **Out:** PyPI publication, Homebrew (WLA-9-04), changes to the
  vendored-rails model, deleting the checkout-based path (it must
  keep working — CI and self-hosting depend on it).

## Acceptance criteria

- [ ] `pipx install <local artifact>` yields working global
  commands; the packaged bootstrap adopts a fixture repo to
  doctor-green without this repository checkout present.
- [ ] Inside a repo with vendored rails, the global `dw` defers to
  `.githooks/dw` (version honesty proven when the two differ).
- [ ] `dw --version`, the plugin manifest, CHANGELOG, and
  `pyproject.toml` all agree — extend the existing version-parity
  unit test to cover the new file.
- [ ] Checkout-based `install.sh` path still passes its suites
  (gate-parity, adoption-discovery).

## Test plan

- **Unit:** version-parity extension in `dw-core-tests.py`.
- **Integration:** `pmo-roadmap/tests/package-smoke.sh`; existing
  install-path suites unchanged and green.
- **Manual / device:** `pipx install`, adopt a scratch repo, ship a
  gated commit there.

## Notes / open questions

- Homebrew python3.14 + pipx are present; the `build` module is not
  — the suite must not assume network access at build time.
- Keep `pyproject.toml` out of the sdist-payload confusion: the
  payload is package data under `dw_pmo` (or a sibling data dir),
  not a second copy of the repo.
