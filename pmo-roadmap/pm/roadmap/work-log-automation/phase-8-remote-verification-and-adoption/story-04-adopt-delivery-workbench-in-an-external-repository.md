# WLA-8-04 - Adopt Delivery Workbench in an external repository

- **Project:** work-log-automation
- **Phase:** 8
- **Status:** in-progress
- **Depends on:** none
- **Unblocks:** WLA-8-05
- **Owner:** unassigned

## Problem

The framework has only ever shipped itself. Self-hosting proves the
mechanics but hides adoption friction: pre-existing history, foreign
layouts, a CLAUDE.md that already says things, contributors who never
read the canon. Until the three-command adoption path is exercised on
a repository we did not design around it, "adoptable" is a claim, not
a fact.

## Scope

- **In:** Run the full documented adoption path
  (`install.sh` → `adopt-project.sh` → `dw adopt --apply`) on a real
  external repository with meaningful history (an existing local
  project or a realistic clone fixture with genuine history —
  chosen at execution time and named in the evidence). Then work one
  real story end-to-end there: status flip, evidence capture,
  contract, gated commit. Keep a timestamped friction log
  (`adoption-friction.md` beside this story's evidence) recording
  every surprise, wrong default, unclear message, or manual fix-up,
  each tagged severity (blocker / papercut / docs).
- **Out:** Fixing the friction (WLA-8-05), publishing the external
  repository, multi-contributor trials.

## Acceptance criteria

- [ ] The external repo reaches `dw doctor` green and `dw check` ok
  through the documented commands alone (deviations become friction
  entries).
- [ ] One story ships through the gate in the external repo, with
  its contract archived and trailers stamped.
- [ ] `dw verify` (from WLA-8-02, if landed) passes over the commits
  produced there; if it has not landed, note it and skip.
- [ ] The friction log exists with severity-tagged entries (or an
  explicit "no friction" claim backed by the transcript).

## Test plan

- **Unit:** n/a (field exercise).
- **Integration:** `dw doctor`, `dw check`, `dw gate --porcelain` in
  the external repo, captured as evidence.
- **Manual / device:** the adoption transcript itself.

## Notes / open questions

- Candidate repo is chosen at execution time; prefer one with real
  commit history over a synthetic fixture, falling back to the
  clone fixture prepared in Phase 7 if none is suitable.
