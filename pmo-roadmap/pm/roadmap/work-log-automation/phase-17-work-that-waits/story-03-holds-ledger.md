# WLA-17-03 - next tells the truth about parked work; dw holds is the ledger

- **Project:** work-log-automation
- **Phase:** 17
- **Status:** backlog
- **Depends on:** WLA-17-01, WLA-17-02
- **Unblocks:** WLA-17-04, WLA-17-05
- **Owner:** unassigned

## Problem

`dw next` already skips blocked stories — silently. With on-hold and
paused phases in the vocabulary, silence becomes dishonesty: "nothing
actionable" is a different situation when three stories and a phase
are deliberately waiting. Parked work needs one review surface, or
holds become the place where work goes to be forgotten.

## Scope

- **In:** `api.py` — `next_story` skips stories in paused phases and
  on-hold stories (normalized); a `parked_summary(project)` helper
  returns paused phases + blocked/on-hold stories with notes;
  `project_context` carries it. CLI — `dw next` exit-2 message
  names the parked counts ("nothing actionable (2 blocked, 1
  on-hold, 1 phase paused — dw holds)"); new `dw holds [project]
  [--json]` prints one greppable line per hold (`BLOCKED <id>
  <note>` / `ON-HOLD <id> <note>` / `PAUSED phase-<n> <note>`),
  exit 0 with holds, exit 2 when nothing is parked. MCP: `dw_next`
  text gains the same tail; context already carries the ledger.
  `validate.py` — warning (never an error) for a parked story with
  no visible reason.
- **Out:** board rendering (WLA-17-04/05); any change to what
  counts as actionable beyond parked-skipping; time-based nagging.

## Acceptance criteria

- [ ] A fixture with an in-progress story inside a paused phase:
  `dw next` proposes a story from an unpaused phase instead; with
  everything parked it exits 2 naming the counts.
- [ ] `dw holds` lists every blocked/on-hold story and paused phase
  with its note and location; `--json` returns the same as a
  machine object; empty ledger exits 2.
- [ ] A blocked or on-hold story without a reason surfaces a
  `dw check` warning naming the story (existing trees keep passing
  — warning, not error).
- [ ] `dw context` includes the parked summary; MCP `dw_next`
  reflects the honest tail.
- [ ] `/usr/bin/python3 pmo-roadmap/tests/dw-core-tests.py` green.

## Test plan

- **Unit:** next-skips-parked (story and phase level), exit-2
  message counts, holds ledger content/exit codes, bare-park
  warning.
- **Integration:** MCP tool text via mcpserver tests if present.
- **Manual / device:** run against the flagship tree: `dw holds`
  reads phases 91/92/93 honestly.

## Notes / open questions

- `dw holds` is read-only; releasing a hold is `dw story status …
  ready` / `dw phase resume` — no new write path.
