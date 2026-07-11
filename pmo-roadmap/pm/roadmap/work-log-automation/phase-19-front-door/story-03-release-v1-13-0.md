# WLA-19-03 - Release v1.13.0

- **Project:** work-log-automation
- **Phase:** 19
- **Status:** done
- **Depends on:** WLA-19-01, WLA-19-02
- **Unblocks:** (optional)
- **Owner:** unassigned

## Problem

Phases 16 (receipts-first reading), 17 (holds, pivots, the board),
and 18 (the interop layer) are closed on main but unreleased — the
CHANGELOG's Unreleased section already tells their story. With the
readiness and README stories landed, everything a stranger meets is
current; v1.13.0 publishes it on every channel with the same
machinery as the last five releases.

## Scope

- **In:** Bump `dw_pmo.__version__` to 1.13.0 with the vendored
  `.githooks` copy, plugin manifest, and formula url in lockstep
  (formula sha256 reset to placeholder until publication);
  CHANGELOG Unreleased section becomes the dated v1.13.0 section;
  parity family and full battery green at 1.13.0; both distribution
  smokes re-run; annotated `v1.13.0` tag on the release commit;
  phase close with final summary in the same commit as this story's
  flip. Publication follows the standing authorization
  (2026-07-03): push main and the tag, GitHub Release with
  hash-verified artifacts (PyPI publishes via the release workflow
  and the `pipit` trusted publisher), stamp the published wheel's
  sha256 into the formula, mirror the public tap, cold-install
  confirm.
- **Out:** new capabilities; announcement posts; touching the
  release machinery itself.

## Acceptance criteria

- [ ] Every version surface reports 1.13.0 under the parity tests —
  including the two the audit flagged as unguarded: the formula
  url/sha256 and the README (which after WLA-19-02 has no version
  literal to lag).
- [ ] Full battery and both distribution smokes green at the
  release commit; `dw verify --all` passes at the tag.
- [ ] The release workflow publishes to PyPI without manual steps;
  PyPI JSON lists 1.13.0.
- [ ] Formula stamped with the served wheel's sha256; tap mirrored;
  a cold `pip install` from a neutral directory reports 1.13.0.
- [ ] Phase 19 final summary closes the phase in this commit.

## Test plan

- **Unit:** parity family at 1.13.0.
- **Integration:** full `pmo-roadmap/tests/` battery;
  `tests/package-smoke.sh`; `tests/brew-formula-smoke.sh`.
- **Manual / device:** post-publication install checks (pip and
  brew report 1.13.0); CI green on the release head.

## Notes / open questions

The tap repo has no surviving local clone — clone
github.com/karolswdev/homebrew-tap fresh. The trusted publisher
environment name is `pipit` and must not be "fixed".
