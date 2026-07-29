# Phase 31 - Landing v1.15.0 - the ceremony

**Last updated:** 2026-07-28.

## Goal

Release phases 25-30 as v1.15.0 with a recorded full-pipeline ceremony demo: empty directory to delivered WebSocket Tic Tac Toe in one phase, on film.

## Scope

- **In:** One rendered full-pipeline ceremony demo
  (`demos/rendered/full-pipeline.mp4` plus regenerable sources) and
  the v1.15.0 landing: CHANGELOG for phases 25-31, version bump in
  lockstep across every surface, full battery + distribution
  smokes, tag, GitHub Release, PyPI, formula stamp, tap mirror.
- **Out:** new capabilities; hosting/embedding the demo video
  (owner's call after landing).

## Exit criteria (evidence required)

- [ ] `demos/rendered/full-pipeline.mp4` shows the whole pipeline —
  empty dir, init, intake, setup lease, adopt commit, grant, live
  claude+codex delivery of WebSocket Tic Tac Toe, evidence, gated
  ship, the game played — and is regenerable from checked-in
  sources (WLA-31-01).
- [ ] v1.15.0 is live: PyPI lists it, cold pip install reports it,
  formula stamped and tap mirrored, `dw verify --all` green at the
  tag (WLA-31-02).

## Story status

| ID | Story | Status | Story file | Evidence |
|---|---|---|---|---|
| WLA-31-01 | The ceremony demo | done | [story-01-ceremony-demo](./story-01-ceremony-demo.md) | [evidence-story-01](./evidence-story-01.md) |
| WLA-31-02 | Release v1.15.0 | ready | [story-02-release-v1-15-0](./story-02-release-v1-15-0.md) | - |

## Where we are

WLA-31-01 is done: `demos/rendered/full-pipeline.mp4` (5:21) shows
the whole pipeline live — init, intake, browser review, setup lease,
gated adopt, explicit grant, claude implementing, codex certifying,
certified handoff, operator ship through the gate, and the game
played by two synced WebSocket clients. The ceremony run also fixed
a real scaffold defect (Python-shaped diff-scope allowlist) on the
way. WLA-31-02 (the release) is next.

## Active risks

| Risk | Likelihood | Mitigation | Stop signal |
|---|---|---|---|
| Live agent ticks make the recording unwatchably long | medium | Segmented capture, ffmpeg concat + timelapse of long stretches | A single tick exceeds the segment budget with no visible progress |
| Release-day surface drift (parity, formula, workflow) | low | The v1.14.0 ritual followed verbatim; parity family gates it | Any parity test red at 1.15.0 |

## Decisions made (this phase)

- 2026-07-28 - Phase scaffolded with `dw phase create` - keeps roadmap structure consistent - CLI.
- 2026-07-28 - Owner ended the settling period and authorized the
  landing of phases 25-30 with a full-pipeline demo as part of the
  ceremony - the release should demonstrate, not just describe, the
  autonomy layer - owner + Fable.

## Decisions deferred

- Where the demo video is hosted/embedded - trigger after v1.15.0
  is live - default is it ships only in-repo under `demos/rendered/`.
