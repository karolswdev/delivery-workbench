# WLA-12-09 - Release v1.9.0 and close the phase

- **Project:** work-log-automation
- **Phase:** 12
- **Status:** done
- **Depends on:** WLA-12-07
- **Unblocks:** none (closes the phase)
- **Owner:** unassigned

## Problem

Created by the split WLA-12-07's own note pre-decided: cutting a
release inside a feature story has bitten before (phase 11 kept it
separate), and the Desk/doctor halves grew. Everything the phase
built — two HoldSpeak packs, three typing-surface riders, the
canonical brief, doctor awareness, the journal — is on main and
green, but v1.8.0 is still what a `pip install` gets. The phase
is not one product until it ships as one.

## Scope

- **In:** CHANGELOG for v1.9.0 (the phase's story, compressed);
  version bump everywhere the parity tests look; the release
  ritual per `docs/distribution.md` (tag, GitHub Release, PyPI via
  the trusted-publisher workflow, tap formula sha stamp + mirror);
  `pip install delivery-workbench==1.9.0` verified; the final
  journal entry; `dw phase close` with a real audit-style
  final-summary (outcome vs exit criteria, what shipped, what was
  deliberately deferred).
- **Out:** Any feature work; the announcement post (parked
  candidate); Phase 13.

## Acceptance criteria

- [ ] Version parity: every version surface reports 1.9.0 under
  the parity tests; full battery and smokes green at the release
  commit.
- [ ] v1.9.0 live on PyPI, the tap, and GitHub Releases;
  `pip install delivery-workbench==1.9.0` works in a clean venv.
- [ ] The journal has its final entry and the phase closes with
  `dw phase close` and a real final summary in the same commit.

## Test plan

- **Unit:** version-parity tests.
- **Integration:** full battery + package smoke at the release
  commit.
- **Manual / device:** the release ritual itself,
  evidence-captured; post-publish pip install verification.

## Notes / open questions

- Follow `docs/distribution.md` "Cutting a release" exactly; the
  pipit trusted-publisher environment name is load-bearing — never
  "fix" it.
