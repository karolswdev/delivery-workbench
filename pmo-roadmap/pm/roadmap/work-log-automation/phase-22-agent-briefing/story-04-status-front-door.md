# WLA-22-04 - The workbench and agent brief open on the answer

- **Project:** work-log-automation
- **Phase:** 22
- **Status:** done
- **Depends on:** WLA-22-03
- **Unblocks:** WLA-22-05
- **Owner:** unassigned

## Problem

Even after the aggregate model exists, the two highest-traffic front
doors can still make users reconstruct it: the browser overview starts
with project cards, and the generated agent brief asks for three
orientation commands. The answer should be visible first without hiding
the specialist views behind it.

## Scope

- **In:** a responsive status/next-action panel on the workbench overview;
  honest attention, manual-action, multi-project, workspace, and gate
  states; canonical agent-doc wording that begins with `dw status` and
  keeps specialist commands; regenerated Claude/Codex/pi/plugin surfaces;
  parity and viewport tests.
- **Out:** buttons that execute status actions; a new workbench write
  route; removing `context`, `next`, `check`, `doctor`, or the board.

## Acceptance criteria

- [x] Desktop and mobile overview render verdict, selected project,
  workspace summary, and the first action with an argv-safe command or
  explicit manual act; no horizontal overflow or raw JSON dump.
- [x] Attention and ambiguity are at least as prominent as ready state;
  the panel never presents a commit button or executes a recommendation.
- [x] The canonical agent brief instructs every rider to call status once
  before work, explains its exit contract, and points to specialist
  surfaces for depth.
- [x] Regeneration is idempotent and all committed agent copies match the
  one canon; existing users' unmanaged prose remains untouched.
- [x] UI smoke covers the new panel at both viewport sizes and the
  workbench remains read-only under its fitness guard.

## Test plan

- **Unit:** render helpers for ready/attention/manual/multi-project shapes;
  agent-doc and plugin parity.
- **Integration:** workbench HTTP/UI smoke and agent-surface lifecycle.
- **Manual / device:** browser walk at desktop and narrow mobile width;
  run a fresh Claude/Codex/pi rider's first instruction.

## Notes / open questions

The status panel is the foyer, not a replacement for the rooms. Project,
board, health, mission-control, trace, and editor routes remain directly
addressable.

The foyer fetches `/api/status` beside the project list and renders only
escaped fields: four compact facts, one reason, and either individually
escaped argv tokens or an explicit manual-act notice. It has no action
button. The renderer contract and 18 Firefox captures cover ready,
broken-rail attention, and ambiguous multi-project states at 1440×900 and
390×844. The shared brief and `/dw-next` canon now begin with status; Claude,
AGENTS/Codex, pi, and plugin render/parity fixtures prove regeneration and
preservation of unmanaged prose.
