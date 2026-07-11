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

- [ ] `dw story status <…> on-hold --reason "<why>"` writes the
  reason as decoration the reader can see (`status_note`) and
  `normalize_status` reads through; `on-hold` without a reason is
  refused; `paused` gates as its synonym (WLA-17-01).
- [ ] `dw phase pause <n> --reason` / `dw phase resume <n>` flip the
  phase header and README index row; a paused phase reads
  `paused: true` with its note in context (WLA-17-02).
- [ ] `dw next` never proposes a story that is blocked or on-hold,
  never proposes from a paused phase, and its nothing-actionable
  exit names the parked counts; `dw holds` lists every parked
  story and paused phase with reason (WLA-17-03).
- [ ] `dw board` renders phase × status columns for this repo AND
  for the flagship tree (HoldSpeak) without error — parked work
  visibly parked (WLA-17-04).
- [ ] The workbench `#/board` shows swimlanes per phase, status
  columns including on-hold, paused phases dimmed with their
  reason (WLA-17-05).
- [ ] Dragging a card between columns runs the guarded
  preview→apply mutation with a reason prompt for parked columns;
  a drop into done without evidence is refused (WLA-17-06).

## Story status

| ID | Story | Status | Story file | Evidence |
|---|---|---|---|---|
| WLA-17-01 | on-hold enters the write vocabulary; every park carries a reason | backlog | [story-01-hold-vocabulary](./story-01-hold-vocabulary.md) | - |
| WLA-17-02 | Pause and resume a phase | backlog | [story-02-phase-pause](./story-02-phase-pause.md) | - |
| WLA-17-03 | next tells the truth about parked work; dw holds is the ledger | backlog | [story-03-holds-ledger](./story-03-holds-ledger.md) | - |
| WLA-17-04 | dw board — the kanban in the terminal | backlog | [story-04-terminal-board](./story-04-terminal-board.md) | - |
| WLA-17-05 | The board on the workbench | backlog | [story-05-workbench-board](./story-05-workbench-board.md) | - |
| WLA-17-06 | Guarded moves on the board | backlog | [story-06-board-moves](./story-06-board-moves.md) | - |

## Where we are

Phase scaffolded 2026-07-11 from the owner's direction ("sometimes
teams pause things to pivot… what if we also built a visual layer,
like a kanban board, divided by phase?") and the flagship specimen
(HoldSpeak phases 91/92/93 holding their ordering in prose the
machinery cannot read). Six stories written; nothing started.

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
