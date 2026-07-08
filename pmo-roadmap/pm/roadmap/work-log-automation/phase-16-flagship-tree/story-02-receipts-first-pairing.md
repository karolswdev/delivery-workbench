# WLA-16-02 - Receipts-first evidence pairing + retired rows + file-derived stories

- **Project:** work-log-automation
- **Phase:** 16
- **Status:** done
- **Depends on:** WLA-16-01
- **Unblocks:** WLA-16-04
- **Owner:** unassigned

## Problem

`check_project` pairs evidence against the story TABLE alone: an
evidence file whose story exists on disk but not in a parseable row is
an "orphan"; a done row whose Evidence cell holds prose (the legacy
notes-column dialect) is a "broken evidence link" even when
`evidence-story-NN.md` sits right there. Struck-through rows
(`~~HS-1-01~~`, story-file cell `—`) — the legacy convention for a cut
story — read as broken links. The receipts are on disk; the checker
only believes the prose.

## Scope

- **In:** `validate.py` — story numbers collected from BOTH table
  rows and on-disk `story-NN-*.md` files; orphan-evidence fires only
  when neither exists; premature-evidence consults the story FILE
  header (normalized) when there is no row. Retired rows (struck
  `~~ID~~` or normalized status in `{cut, cancelled, superseded}`):
  no broken-story-link, no evidence demands, excluded from
  "all stories done" (which becomes "all rows terminal and at least
  one done"). A done row whose Evidence cell is not a markdown link
  is accepted when `evidence-story-NN.md` exists (content lints run
  against it); a broken actual link stays an error.
  `statefeed.py` — when a phase has story files that no parsed row
  covers, derive story entries from the files (id from the H1,
  status from the header, normalized) so coverage is receipts-first;
  `project_warnings` gains one per-phase warning naming how many
  stories are file-derived (legible, not silent).
- **Out:** normalization itself (WLA-16-01); pointer/next-story
  (WLA-16-03); any gate/mutation change; inventing evidence demands
  for file-derived stories beyond what rows already get.

## Acceptance criteria

- [ ] Fixture: a phase with a 4-column decorated table, evidence
  files for its done stories, one prose Evidence cell, one struck
  row, and one table-less phase holding done story files + evidence
  — `dw check` reports zero errors on it.
- [ ] The same fixture with one planted real desync of each kind
  (evidence file with no story anywhere; evidence for a story whose
  file header says in-progress; a done row with neither link nor
  receipt file) reports exactly those, with the existing message
  vocabulary (classification table in `validate.py` still matches).
- [ ] `dw state --json` on the table-less phase lists its stories
  (file-derived) with correct statuses, and the project's warnings
  count includes the file-derived notice.
- [ ] Existing validation fixtures pass unmodified.
- [ ] `python3 pmo-roadmap/tests/dw-core-tests.py` green.

## Test plan

- **Unit:** new `dw-core-tests.py` cases per the fixture above.
- **Integration:** `pmo-roadmap/tests/package-smoke.sh`.
- **Manual / device:** n/a.

## Notes / open questions

- File-derived stories are a READ affordance for legacy trees; the
  methodology still requires the table for new work, and the gate
  still enforces it on staged diffs.
