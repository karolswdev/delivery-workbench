# WLA-31-02 - Release v1.15.0

- **Project:** work-log-automation
- **Phase:** 31
- **Status:** ready
- **Depends on:** WLA-31-01
- **Unblocks:** (optional)
- **Owner:** unassigned

## Problem

Phases 25 through 30 — orchestration, autonomous programs, the
usability exam, mission control, the knowledge layer, the front
door — are closed on main with CI green and nothing published. The
settling period the owner called on 2026-07-27 is over by the
owner's own word ("let's release all of this good work"). What a
stranger can `pip install` still predates the entire autonomy
layer.

## Scope

- **In:** CHANGELOG v1.15.0 section covering phases 25-31 (linking
  each phase's final summary; written fresh — none of them touched
  the CHANGELOG); bump `dw_pmo.__version__` to 1.15.0 with the
  vendored `.githooks` copy, plugin manifest, and formula url in
  lockstep (sha256 reset to placeholder until publication); parity
  family and full battery green at 1.15.0; both distribution
  smokes; annotated `v1.15.0` tag on the release commit; phase
  close with final summary in the same commit as this story's
  flip. Publication under the standing authorization (2026-07-03)
  renewed for this landing: push main and the tag, GitHub Release
  with hash-verified artifacts, PyPI via the release workflow
  (`pipit` trusted publisher), stamp the served wheel's sha256 into
  the formula, mirror the tap, cold-install confirm.
- **Out:** new capabilities; hosting or embedding the ceremony
  demo (owner's call, separately).

## Acceptance criteria

- [ ] Every version surface reports 1.15.0 under the parity tests,
  including the formula url (sha256 stamped post-publication).
- [ ] Full battery and both distribution smokes green at the
  release commit; `dw verify --all` passes at the tag.
- [ ] The release workflow publishes to PyPI without manual steps;
  PyPI JSON lists 1.15.0; a cold pip install from a neutral
  directory reports 1.15.0.
- [ ] Phase 31 final summary closes the phase in this commit.

## Test plan

- **Unit:** parity family at 1.15.0.
- **Integration:** full battery; `tests/package-smoke.sh`;
  `tests/brew-formula-smoke.sh`.
- **Manual / device:** post-publication install checks; CI green on
  the release head.

## Notes / open questions

Brew smoke refuses while the brew package is installed — uninstall
first, reinstall from the tap at the end (learned in WLA-19-03).
The formula sha256 stamp lands as a follow-up gated commit after
publication, per the v1.14.0 pattern.
