# Phase 9 Final Summary

**Status:** complete.
**Date:** 2026-07-03.

Phase 9 made Delivery Workbench installable without cloning its
repository, without touching the invariant that makes it
trustworthy: per-repo vendored rails remain the only gating
authority, and the unit of distribution is the bootstrap vehicle.
A machine can now `pipx install` or `brew install` the framework,
adopt any repo with two commands, and keep vendored rails fresh
with a staleness check that reads content, not version strings.

## Outcome vs exit criteria

All five exit criteria closed with evidence:

1. **Distribution contract** — `docs/distribution.md` locks the
   vendored-rails invariant, the defer-to-repo rule (global `dw`
   execs `.githooks/dw` unconditionally inside adopted repos), the
   `dw_pmo/_payload/` layout that lets install.sh/update.sh run
   unmodified from checkout or package, and the v1 channels; all 12
   installer copy sources cross-checked into the doc
   (evidence-story-01).
2. **pipx-installable package** — `delivery-workbench` builds as
   sdist + wheel (55-file payload), installs into an isolated env,
   and bootstraps a fixture repo to doctor-green from outside the
   checkout; the defer rule is proven by marker test
   (evidence-story-02, `tests/package-smoke.sh`).
3. **Upgrade path from real v1.5.0 rails** — a fixture adopted from
   the actual tag upgrades to current: `verify.py` arrives, roadmap
   content and config seams stay byte-identical, the mixed-version
   history verifies clean, and the gate ships a story afterward.
   `update.sh --check` became content-based after the fixture proved
   version strings report "fresh" between releases while code moves
   (evidence-story-03, `tests/upgrade-path.sh`).
4. **Homebrew formula from a local tap** — pip-free, venv-free
   install (wheel unzipped into libexec behind an interpreter shim;
   virtualenv machinery waived because the runtime is stdlib-only),
   proven end-to-end from a throwaway tap: install, version truth,
   brew-installed bootstrap, defer rule, clean uninstall
   (evidence-story-04, `tests/brew-formula-smoke.sh`).
5. **v1.6.0** — every version surface agrees under the extended
   parity tests (`dw --version`, plugin manifest, CHANGELOG,
   pyproject dynamic attr, formula artifact url); both smokes pass
   against the 1.6.0 artifacts; the annotated `v1.6.0` tag marks the
   release commit and `dw verify --all` passes at it
   (evidence-story-05).

## What shipped

- `docs/distribution.md`; `pyproject.toml` + `setup.py` payload
  hook + `MANIFEST.in`; `lib/dw_pmo/launcher.py` (the global `dw`);
  `Formula/delivery-workbench.rb`; `update.sh --check`;
  README "Install without cloning" section.
- Tests: `package-smoke.sh`, `upgrade-path.sh`,
  `brew-formula-smoke.sh`, `LauncherTest`, and the extended
  version-parity family (unit suite 111 → 117 across the phase);
  CI gains `package-smoke`, the upgrade-path step, and the macOS
  brew-smoke leg.

## Deliberately deferred

PyPI registration and the public tap repository (user-triggered
publications — the artifacts make each a one-command follow-up;
the formula's sha256 is stamped at publication), bottles/prebuilt
binaries, Windows-native installers. Environment note for this
machine: brew python 3.14 has a broken `pyexpat`, which disables
pipx and venv-with-pip there — the smokes probe interpreter health
and fall back accordingly.

Future work starts by opening a new phase with `dw phase create`
and letting the rails do what they were built to do.
