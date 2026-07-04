# WLA-13-03 - Correlate live agent sessions to stories

- **Project:** work-log-automation
- **Phase:** 13
- **Status:** done
- **Depends on:** WLA-13-01, WLA-13-02
- **Unblocks:** WLA-13-05
- **Owner:** unassigned

*Re-pinned by WLA-13-01 (2026-07-04): implement against
[docs/mission-control.md](../../../../../docs/mission-control.md) §2 (registry read-only, four outcomes, 30-minute staleness TTL, pinned field list).*

## Problem

HoldSpeak's agent hook already reports each live session's cwd,
session id, model, and whether the agent is waiting on a human
(`awaiting_response`, queryable from the iOS companion today).
Delivery Workbench knows which story is in-progress in any rails
repo. Nobody joins the two, so "Claude is on WLA-12-03, blocked,
asking you a question" — the sentence that makes the conveyor a
mission-control surface rather than a status page — cannot be
computed anywhere.

## Scope

- **In:** A correlator that reads HoldSpeak's session registry
  (read-only, version-pinned like the Phase 12 pack), resolves
  each session's cwd to a rails repo and its in-progress story,
  and enriches the WLA-13-02 feed with per-session
  who/where/what/blocked entries; the ambiguity rules from the
  WLA-13-01 design (no rails repo, multiple in-progress,
  worktrees) implemented and tested.
- **Out:** Writing anything into HoldSpeak state; reading
  transcript content (the correlator sees rails and registry
  metadata, nothing an operator didn't opt into via the hook).

## Acceptance criteria

- [ ] A live session in a rails fixture repo resolves to its
  in-progress story, including the awaiting/blocked flag, proven
  against HoldSpeak's real registry format.
- [ ] Every WLA-13-01 ambiguity case has a test and a defined,
  honest output (unknown beats guessed).
- [ ] Full battery passes.

## Test plan

- **Unit:** correlation rules over fixture registries.
- **Integration:** real agent session in a fixture rails repo,
  captured as evidence.
- **Manual / device:** correlation visible from the feed while a
  real session runs in this repo.

## Notes / open questions

- Registry access path (file read vs HoldSpeak API) - decide in
  WLA-13-01 against the pinned HoldSpeak version.
