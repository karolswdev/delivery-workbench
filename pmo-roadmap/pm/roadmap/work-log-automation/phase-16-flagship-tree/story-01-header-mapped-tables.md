# WLA-16-01 - Header-mapped story tables + status normalization

- **Project:** work-log-automation
- **Phase:** 16
- **Status:** backlog
- **Depends on:** none
- **Unblocks:** WLA-16-02, WLA-16-03
- **Owner:** unassigned

## Problem

`parse_story_rows` recognizes exactly one byte sequence
(`| ID | Story | Status | Story file | Evidence |`) and exactly five
cells; anything else parses to zero rows. The flagship consumer's
recent phases use a 4-column table (`| ID | Story | Status | Story
file |`) with decorated status cells (`**done** (2026-07-07 — …)`), so
`dw state` reads them as 0/0 and `dw check` calls every evidence file
an orphan. Status comparisons are raw string equality, so a decorated
`done` never equals `done`.

## Scope

- **In:** `parse.py` — detect a story table by its header cells
  (case-insensitive match on `ID`, `Story`, `Status`, `Story file`;
  `Evidence` optional), map columns by index from that header, keep
  the canonical header as a fast path with byte-identical results.
  `model.py` — `normalize_status(raw)`: strip markdown emphasis,
  match a known status keyword at token boundaries (longest-first:
  `in-progress`/`in progress`, `not-started`/`not started`,
  `backlog`, `ready`, `blocked`, `paused`, `done`, `complete`,
  `closed`, `shipped`, `cut`, `cancelled`, `superseded`, `planned`,
  `planning`, `scaffolded`); no keyword → the first
  decoration-stripped token, lowercased. Read-side consumers switch
  membership tests to the normalized value: `validate.py`,
  `api.py` (`next_story`, `project_context` filter/active),
  `statefeed.py` (done counting), `workbench.py` (open detection +
  status chip counts), `sessions.py` (`_IN_PROGRESS`).
- **Out:** any change to `mutations.py` / `gate.py` / `verify.py` /
  `contract.py` (the write vocabulary stays `STORY_STATUSES`,
  exact); evidence pairing semantics (WLA-16-02); pointer logic
  (WLA-16-03).

## Acceptance criteria

- [ ] Existing `dw-core-tests.py` parser/validation fixtures pass
  unmodified (canonical tables parse byte-identically).
- [ ] A 4-column header-mapped fixture table parses to the same
  StoryRow set as its 5-column equivalent (evidence cell empty).
- [ ] `normalize_status` maps: `**done** (2026-07-07 — …)` → `done`;
  `CLOSED ✅ (6/6)` → `closed`; `in-progress (3/6)` → `in-progress`;
  `not-started` → `not-started`; `host-complete (…)` →
  `host-complete` (NOT `complete`); `paused` → `paused`; plain
  `done` → `done` — pinned in tests.
- [ ] A decorated-status story header vs a plain table cell (or vice
  versa) no longer raises a status-mismatch error when they
  normalize equal; a genuinely different pair still does.
- [ ] `python3 pmo-roadmap/tests/dw-core-tests.py` green;
  `pmo-roadmap/tests/gate-parity.sh` green (gate untouched).

## Test plan

- **Unit:** new `dw-core-tests.py` cases: header-mapped table parse,
  normalization table, mismatch suppression/preservation.
- **Integration:** `pmo-roadmap/tests/gate-parity.sh`,
  `pmo-roadmap/tests/package-smoke.sh` (CI set).
- **Manual / device:** n/a.

## Notes / open questions

- Normalization is deliberately not exposed as a write vocabulary:
  `dw story status` still rejects anything outside
  `STORY_STATUSES`. The reader meets history where it is; the writer
  keeps history clean from here.
