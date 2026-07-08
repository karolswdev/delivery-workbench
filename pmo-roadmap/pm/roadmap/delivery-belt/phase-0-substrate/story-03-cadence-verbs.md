# DW-0-03 — Cadence verbs: `dw story start|done`, `dw phase close`

- **Project:** delivery-belt
- **Phase:** 0
- **Status:** backlog
- **Depends on:** DW-0-01
- **Unblocks:** DW-0-04
- **Owner:** unassigned

## Problem

Every shipping commit performs the same mechanical edits across three files
(story Status line, status-table row, two Last-updated lines) by hand-typed
text surgery — the RFC's "six prose surfaces per shipping commit". The
mechanical half becomes verbs; the prose half (Where we are, evidence
content, final summaries) stays authored.

## Scope

- **In:** `dw story start <ID>` (backlog/ready → in-progress),
  `dw story done <ID>`, `dw phase close <project> <phase-number>`, all with
  `--root`. Mechanical edits only: the story `- **Status:**` line; the
  story's status-table row cell (+ evidence-link cell on `done`); the date
  token in the phase file's and project README's `**Last updated:**` lines
  (surrounding prose byte-preserved). Refusals mirroring the hook:
  `story done` refuses if `evidence-story-{n}.md` is absent;
  `phase close` refuses unless `final-summary.md` exists and every story is
  done/cut, then sets the README index row's status cell to `done`. Every
  verb prints the prose surfaces still owed (Where we are, README headline,
  canon docs) so the cadence is completed, not silently half-done.
- **Out:** writing prose; creating evidence/summary files; git operations;
  updating the README current-phase pointer (close prints the reminder
  instead — the pointer's target is a human sequencing decision).

## Acceptance criteria

- [ ] `dw story start DW-0-03` on a fixture flips the header to
      `in-progress`, updates the table row, bumps both Last-updated dates,
      and leaves every other byte of those files unchanged (asserted by
      diff).
- [ ] `dw story done` with the evidence file present flips header + row,
      sets the row's evidence cell to a relative link, bumps dates; without
      the evidence file it refuses with the hook's rule named and exits 1,
      files untouched.
- [ ] `dw phase close` refuses without `final-summary.md` (exit 1); with it
      and all stories terminal, the README phase-index row status cell
      becomes `done` and nothing else in the row changes.
- [ ] An unknown story ID exits 1 naming the projects/IDs it searched.
- [ ] Verbs never touch a file outside the story's project directory.

## Test plan

- **Unit:** `tests/dw-cli.sh` verb sections (fixture diffs asserted
  byte-precisely with `git diff` in the temp repo).
- **Integration / Cypress:** this phase's own paperwork updated via the
  verbs for DW-0-04's ship (the proposal's exit criterion), recorded in
  evidence.
- **Manual / device:** n/a.

## Notes / open questions

- Date source is the system clock (the verbs stamp "today"); acceptable for
  a local CLI whose output is reviewed in the diff.
- Table-cell edits target the §2.2 template column order (`| ID | Story |
  Status | Story file | Evidence |`). Legacy tables that deviate get a
  refusal naming the row, never a guessed edit.
