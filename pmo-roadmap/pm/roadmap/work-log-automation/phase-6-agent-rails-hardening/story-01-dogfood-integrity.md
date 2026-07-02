# WLA-6-01 - Restore dogfood integrity and land the working tree through the rails

- **Project:** work-log-automation
- **Phase:** 6
- **Status:** done
- **Depends on:** none
- **Unblocks:** WLA-6-02, WLA-6-03, WLA-6-04, WLA-6-05, WLA-6-06, WLA-6-07, WLA-6-08
- **Owner:** unassigned

## Problem

The framework does not currently enforce itself on its own repository. The
repo has six commits, none gated: `core.hooksPath` is unset, `.githooks/`
does not exist at the repo root, no `.tmp/CONTRACT.md` has ever been
written, and no work-log entry exists. Meanwhile the working tree holds the
proof layer for phases 0-5 uncommitted: all 19 evidence files, all four
final summaries, the entire phase-4 and phase-5 directories, `bin/dw`
itself, `tests/roadmap-cli.sh`, and the updated `validation.yml`. The
advertised traceability chain (story -> evidence -> commit -> work-log
entry) has never resolved end-to-end anywhere, including here.

This is the single most credibility-damaging gap found in the 2026-07-02
architecture review: an evidence-first commit-gate framework whose own
history violates its own operating cadence. Every later Phase 6 story must
ship through working rails, so this lands first.

## Scope

- **In:** Install the framework on this repository (`.githooks/`,
  `core.hooksPath`, `.tmp/` gitignore entry); enable work logging via
  `.githooks/pre-commit.config` with a repo-local
  `PMO_WORK_LOG_DIR` decision documented; land the current working tree as
  a sequence of story-scoped, contract-gated commits (one shipped story per
  commit, `.tmp/BUNDLE-OK.md` with written rationale where bundling is
  unavoidable); reference story IDs in commit messages; add a
  `dw check work-log-automation` step to `.github/workflows/validation.yml`
  and commit the currently-uncommitted CI changes; commit the
  `__pycache__`/`*.pyc` gitignore fix.
- **Out:** Rewriting the six existing commits; any behavior change to
  hooks, CLI, templates, or contract semantics (WLA-6-02 through
  WLA-6-06); backfilling work-log entries for pre-Phase-6 history.

## Acceptance criteria

- [ ] `git config core.hooksPath` returns `.githooks` in this repo and
  `.githooks/` contains the framework hooks and helpers.
- [ ] `git status --porcelain` is empty after the landing sequence: every
  phase 0-5 artifact, `bin/dw`, its tests, and CI updates are committed.
- [ ] Every landing commit passed the pre-commit gate with a fresh contract;
  the consented work-log entries exist and are cited (path + commit SHA) in
  the evidence file as proof the gate actually ran.
- [ ] At least one story in `dw context work-log-automation --trace` resolves
  the full chain: README -> phase status -> story -> evidence -> commit ->
  work-log entry.
- [ ] `.github/workflows/validation.yml` runs
  `pmo-roadmap/bin/dw check work-log-automation` and CI is green.
- [ ] The evidence file records the commit-by-commit landing plan, including
  every `BUNDLE-OK.md` rationale used, so the batching is auditable rather
  than silent.

## Test plan

- **Unit:** n/a.
- **Integration / Cypress:** `pmo-roadmap/tests/work-log-mvp.sh` and
  `pmo-roadmap/tests/roadmap-cli.sh` pass before and after landing;
  `dw check work-log-automation` exits 0 in CI.
- **Manual / device:** `work-log-read --list` shows entries for the landing
  day; inspect one entry's `index_tree` against `git cat-file` output for
  the corresponding commit.

## Notes / open questions

The landing sequence will exercise the gate on real history and will likely
surface the known gate bugs (orphan-evidence deletions, bundling friction).
Do not fix them inline; record each friction point in the evidence file as
input to WLA-6-02. Decide during execution whether the work log for this
repo lives in the default `~/.work/log` or a repo-adjacent directory; record
the decision in the phase status.
