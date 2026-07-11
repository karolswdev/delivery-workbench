# WLA-17-02 - Pause and resume a phase

- **Project:** work-log-automation
- **Phase:** 17
- **Status:** backlog
- **Depends on:** WLA-17-01
- **Unblocks:** WLA-17-03, WLA-17-04, WLA-17-05
- **Owner:** unassigned

## Problem

Pivots park whole phases, not single stories. The flagship's phase 92
says "PRE-CLOSE IMPLEMENTATION (0/10). Phase 91 remains active" — an
ordering constraint written in prose, invisible to `dw next`, which
would happily propose HS-92-01 the moment 91 closes. A phase needs a
machine-readable paused state with a reason, and a way back.

## Scope

- **In:** `mutations.py` — `plan_phase_pause(root, project, phase,
  reason)` rewrites the phase status file's `**Status:**` header to
  `paused (<reason> — since <date>)` and the project README's phase
  index row status to match; `plan_phase_resume` restores
  `in-progress`. Both refuse on a closed phase (final-summary
  present). `parse.py` — `phase_header_status(path)` reads the
  phase file's `**Status:**` line (bullet or bare, the flagship
  shape); `phase_is_paused` = its normalization is `paused`.
  `api.py` — phase items in context gain `paused` + `pause_note`;
  `_project_summary` counts paused phases. CLI `dw phase pause
  <project> <phase> --reason` / `dw phase resume <project>
  <phase>`; workbench mutation kinds `pause_phase` / `resume_phase`
  (same preview→apply flow); events emitted (`phase_paused`,
  `phase_resumed`).
- **Out:** `next`/`holds` consumption of the flag (WLA-17-03); board
  rendering (WLA-17-04/05); auto-resume or dependency triggers
  ("resume when phase N closes" stays prose inside the reason).

## Acceptance criteria

- [ ] `dw phase pause work-log-automation <n> --reason "pivot"` sets
  the phase header and README row; `dw context` reads
  `paused: true`, `pause_note` carrying the reason; `dw phase
  resume` restores an active phase.
- [ ] Pause without `--reason` is refused; pausing a closed phase
  (final-summary.md exists) is refused by name.
- [ ] A paused phase still counts as *open* (never "closed") in
  every existing view; `dw check` raises no new issues on a paused
  phase.
- [ ] Workbench preview→apply can pause and resume with diffs shown;
  fingerprint staleness rules apply unchanged.
- [ ] `/usr/bin/python3 pmo-roadmap/tests/dw-core-tests.py` green.

## Test plan

- **Unit:** pause/resume plan content, refusals (no reason, closed
  phase), header round-trip on both bullet and bare `**Status:**`
  shapes, context fields.
- **Integration:** workbench handle_mutation preview/apply for the
  two new kinds.
- **Manual / device:** n/a.

## Notes / open questions

- Resume restores `in-progress` rather than recomputing from
  stories — the phase index vocabulary is loose by design and
  `normalize_status` reads it either way.
