# WLA-21-01 - Release v1.14.0

- **Project:** work-log-automation
- **Phase:** 21
- **Status:** backlog
- **Depends on:** none
- **Unblocks:** (optional)
- **Owner:** unassigned

## Problem

Phase 20 (the group grows hands) is closed on main with CI green
and nothing published. The Telegram surface a stranger reads about
in the README — screenshots, the image live view, the toolbar, the
question keyboards, per-person consent in groups — should be the
surface `pip install` serves.

## Scope

- **In:** CHANGELOG v1.14.0 section for phase 20 (written fresh —
  phase 20 closed without touching the CHANGELOG); bump
  `dw_pmo.__version__` to 1.14.0 with the vendored `.githooks`
  copy, plugin manifest, and formula url in lockstep (sha256 reset
  to placeholder until publication); parity family and full
  battery green at 1.14.0; both distribution smokes; annotated
  `v1.14.0` tag on the release commit; phase close with final
  summary in the same commit as this story's flip. Publication
  under the standing authorization (2026-07-03): push main and the
  tag, GitHub Release with hash-verified artifacts, PyPI via the
  release workflow (`pipit` trusted publisher), stamp the served
  wheel's sha256 into the formula, mirror the tap, cold-install
  confirm, brew upgrade the desk. Serve the bot in tmux so the
  owed phase-20 phone leg is one tap away.
- **Out:** new capabilities; the phone-leg screenshots (owner's
  hands; they land in phase 20's evidence assets when taken).

## Acceptance criteria

- [ ] Every version surface reports 1.14.0 under the parity tests,
  including the formula url (sha256 stamped post-publication).
- [ ] Full battery and both distribution smokes green at the
  release commit; `dw verify --all` passes at the tag.
- [ ] The release workflow publishes to PyPI without manual steps;
  PyPI JSON lists 1.14.0; a cold pip install from a neutral
  directory and the desk's brew both report 1.14.0.
- [ ] Phase 21 final summary closes the phase in this commit.

## Test plan

- **Unit:** parity family at 1.14.0.
- **Integration:** full battery; `tests/package-smoke.sh`;
  `tests/brew-formula-smoke.sh`.
- **Manual / device:** post-publication install checks; CI green on
  the release head; the bot serving in tmux `dw-telegram`.

## Notes / open questions

Brew smoke refuses while the brew package is installed — uninstall
first, reinstall from the tap at the end (learned in WLA-19-03).
