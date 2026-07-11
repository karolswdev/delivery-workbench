# Phase 17 - Work that waits — holds, pivots, and the board

**Last updated:** 2026-07-11.

## Goal

Parked work becomes first-class. Real projects pause things: a story
waits on an external dependency, a whole phase yields to a pivot
(the flagship's phase 92 — "Phase 91 remains active" — holds ten
stories fake-`in-progress` because the vocabulary has no way to say
*waiting*). This phase gives holds a voice: `on-hold` joins the write
vocabulary and every park carries a reason; a phase can pause and
resume; `dw next` names what it skipped; `dw holds` is the ledger of
everything waiting; and a kanban board — terminal and workbench —
shows the whole picture, columns by status, swimlanes by phase.

## Scope

- **In:** `model.py` (HOLD_STATUSES, vocabulary + normalization
  keywords), `mutations.py` (`--reason` decoration on story status,
  phase pause/resume plans), `parse.py` (status-note extraction),
  `api.py` (`next_story` skipping parked work + honest counts, holds
  ledger, phase pause fields in context), `validate.py` (parked
  semantics in activity checks; a bare `blocked`/`on-hold` warns),
  CLI (`dw story status --reason`, `dw phase pause|resume`,
  `dw holds`, `dw board`), MCP parity (`dw_story_status` reason,
  enum text), workbench server + UI (`#/board` view, editor reason
  field, guarded drag moves through preview→apply), docs
  (roadmap-builder §2.3, agent docs block) and their parity tests.
- **Out:** ANY gate loosening — `gate.py`, `verify.py`,
  `contract.py` semantics unchanged (on-hold is an *open* status;
  done rules untouched); rewriting consumer histories; scheduling
  or reminder machinery (a hold records *why*, not *when to nag*);
  feed schema changes.

## Exit criteria (evidence required)

- [x] `dw story status <…> on-hold --reason "<why>"` writes the
  reason as decoration the reader can see (`status_note`) and
  `normalize_status` reads through; `on-hold` without a reason is
  refused; `paused` gates as its synonym (WLA-17-01 —
  [evidence](./evidence-story-01.md): 188 tests green + live CLI
  walk on a scratch tree).
- [x] `dw phase pause <n> --reason` / `dw phase resume <n>` flip the
  phase header and README index row; a paused phase reads
  `paused: true` with its note in context (WLA-17-02 —
  [evidence](./evidence-story-02.md): 192 tests green + live
  pause→resume walk with all four refusals).
- [x] `dw next` never proposes a story that is blocked or on-hold,
  never proposes from a paused phase, and its nothing-actionable
  exit names the parked counts; `dw holds` lists every parked
  story and paused phase with reason (WLA-17-03 —
  [evidence](./evidence-story-03.md): 194 tests green + live walk;
  the flagship read surfaced HS-25-07, a real forgotten hold).
- [x] `dw board` renders phase × status columns for this repo AND
  for the flagship tree (HoldSpeak) without error — parked work
  visibly parked (WLA-17-04 — [evidence](./evidence-story-04.md):
  198 tests green; the flagship's ~90 phases render in 163 lines,
  83 closed lanes folded, phase 92's pivot visible).
- [x] The workbench `#/board` shows swimlanes per phase, status
  columns including on-hold, paused phases dimmed with their
  reason (WLA-17-05 — [evidence](./evidence-story-05.md): 199 tests
  green, 14-render viewport smoke, live screenshots in assets/).
- [ ] Dragging a card between columns runs the guarded
  preview→apply mutation with a reason prompt for parked columns;
  a drop into done without evidence is refused (WLA-17-06).

## Story status

| ID | Story | Status | Story file | Evidence |
|---|---|---|---|---|
| WLA-17-01 | on-hold enters the write vocabulary; every park carries a reason | done | [story-01-hold-vocabulary](./story-01-hold-vocabulary.md) | [evidence-story-01](./evidence-story-01.md) |
| WLA-17-02 | Pause and resume a phase | done | [story-02-phase-pause](./story-02-phase-pause.md) | [evidence-story-02](./evidence-story-02.md) |
| WLA-17-03 | next tells the truth about parked work; dw holds is the ledger | done | [story-03-holds-ledger](./story-03-holds-ledger.md) | [evidence-story-03](./evidence-story-03.md) |
| WLA-17-04 | dw board — the kanban in the terminal | done | [story-04-terminal-board](./story-04-terminal-board.md) | [evidence-story-04](./evidence-story-04.md) |
| WLA-17-05 | The board on the workbench | done | [story-05-workbench-board](./story-05-workbench-board.md) | [evidence-story-05](./evidence-story-05.md) |
| WLA-17-06 | Guarded moves on the board | backlog | [story-06-board-moves](./story-06-board-moves.md) | - |

## Where we are

WLA-17-05 done (2026-07-11): the board has glass —
`/api/projects/<slug>/board` + `#/board`, swimlane per open phase
(pointer leading), six columns with counts, cards carrying ✓
receipts and hold reasons, paused lanes dimmed with the ⏸ banner,
closed lanes folded behind one-line `<details>` receipts; topbar +
project-view links; the viewport smoke grew to 7 views × 2 sizes;
live screenshots in assets/. Earlier: WLA-17-04 (`dw board` in the
terminal; the flagship renders in 0.1s, phase 92's pivot legible),
WLA-17-03 (honest `next` + `dw holds`; HS-25-07 surfaced),
WLA-17-02 (phase pause/resume), WLA-17-01 (the hold vocabulary).
199 core tests green. Next: WLA-17-06 (guarded moves on the board)
— the last story, then the phase closes.

Note for operators on this self-hosting repo: `.githooks/` is the
installed snapshot and syncs at release time; between releases the
source CLI (`pmo-roadmap/bin/dw`, what CI runs) is authoritative for
`check` — the installed copy may report CLAUDE.md canon drift until
the next sync.

## Active risks

| Risk | Likelihood | Mitigation | Stop signal |
|---|---|---|---|
| Hold vocabulary leaks looseness into the gate | low | on-hold is an open status; gate/verify diffs stay empty; gate-parity green | any gate test edit in this phase's diffs |
| Reason decoration breaks legacy parsers/consumers | medium | decoration rides the existing cell-tail convention `normalize_status` already reads through; feed schema pinned | a feed or sessions test needing a shape edit |
| Board drag mutates without the guarded flow | low | drag maps 1:1 onto the existing preview→apply endpoints; no new write path | any board write bypassing /api/mutations |
| Kanban view collapses on 90-phase trees | medium | swimlanes render open phases first, closed phases collapsed behind a count | flagship board unusable or slow |

## Decisions made (this phase)

- 2026-07-11 - Phase scaffolded with `dw phase create` - keeps roadmap structure consistent - CLI.
- 2026-07-11 - `blocked` (can't proceed) and `on-hold` (won't proceed for now) stay distinct statuses - a pivot is a choice, an impediment is not, and the board should show which is which - owner direction.
- 2026-07-11 - A hold's reason lives as decoration in the status cell (and story header), not in a new column or file - the 5-column table stays canonical, `normalize_status` (phase 16) already reads through decoration, legacy trees stay parseable - design.
- 2026-07-11 - `on-hold` requires a reason at write time; legacy bare `blocked` only warns - new vocabulary can carry new obligations without breaking old trees - design.

## Decisions deferred

- A `cut` status in the write vocabulary (carried from phase 16) - trigger: a consumer asking to cut a story through the CLI - default: read-side recognition only.
- Hold expiry / "wake me when" scheduling - trigger: a real consumer needing time-based resurfacing - default: reasons are prose; `dw holds` is the review surface.
- Drag-to-reorder within a column (priority) - trigger: consumer demand - default: table order is priority order.
