# Phase 21 - The landing — v1.14.0 ships the group's hands

**Last updated:** 2026-07-11.

## Goal

Phase 20's interactive surface — screenshots, buttons, per-person
consent — reaches every channel as v1.14.0, with the same machinery
as the last six releases. Owner direction (2026-07-11): "Land it."

## Scope

- **In:** the CHANGELOG's v1.14.0 section telling phase 20's story;
  version bump across every surface (source + vendored
  `__version__`, plugin manifest, formula url with the sha256 reset
  to placeholder); full battery + both distribution smokes at
  1.14.0; annotated tag; GitHub Release with hash-verified
  artifacts; PyPI via the release workflow; formula stamp + tap
  mirror + cold-install confirmations; the desk's bot served so the
  owed phase-20 phone leg is one tap away.
- **Out:** new capabilities; the phone-leg screenshots themselves
  (they need the owner's hands — recorded as owed in phase 20's
  evidence, they land there when taken); announcement/docs-site
  work (the next strategic phase, decided separately).

## Exit criteria (evidence required)

- [x] v1.14.0 is live on every channel: every version surface in
  lockstep under the parity tests, full battery + both smokes green
  at the release commit, annotated tag, GitHub Release with sha256s
  in the notes, PyPI at 1.14.0 via the trusted publisher, formula
  stamped with the served wheel's hash, tap mirrored, cold pip
  install and brew both reporting 1.14.0, CI green (WLA-21-01 —
  [evidence](./evidence-story-01.md): the pre-tag battery +
  surfaces + smokes captured; post-publication confirmations in
  the stamp rider commit).

## Story status

| ID | Story | Status | Story file | Evidence |
|---|---|---|---|---|
| WLA-21-01 | Release v1.14.0 | done | [story-01-release-v1-14-0](./story-01-release-v1-14-0.md) | [evidence-story-01](./evidence-story-01.md) |

## Where we are

Phase CLOSED 1/1 (2026-07-11, same night as phases 19 and 20) —
see [final-summary](./final-summary.md). v1.14.0 carries the
group's hands to every channel; the phone leg stays owed in
phase 20's evidence with the bot served for it.

## Active risks

| Risk | Likelihood | Mitigation | Stop signal |
|---|---|---|---|
| The two unguarded surfaces lag the bump (formula url/sha256) | low | the release story names them; the README version literal was removed in WLA-19-02 | a released surface reads 1.13.0 |
| Telegram job's Pillow install masks a floor regression | low | the suite also runs (and is captured) without Pillow; python-floor job unchanged | renderer legs green but fallback legs red |

## Decisions made (this phase)

- 2026-07-11 - Phase scaffolded with `dw phase create` - keeps roadmap structure consistent - CLI.
- 2026-07-11 - Release does not wait for the phone-leg screenshots - phase 20 closed with the walk owed and the machinery test-proven; the bot is served at landing so the walk is one tap away - sequencing.

## Decisions deferred

- The next strategic phase (outward: docs site + announcement vs
  inward: iOS conveyor + remote transport) - trigger: owner's call
  after the landing - recommendation on record: outward.
