# Phase 17 Final Summary

**Status:** complete.
**Date:** 2026-07-11.

## Outcome vs exit criteria

Six for six, all evidenced, one sitting. Work that waits is now
first-class across the whole stack:

1. **The hold vocabulary** (WLA-17-01) — `on-hold` (synonym
   `paused`) joined the write vocabulary as an *open* status,
   distinct from `blocked`: an impediment is not a choice. Every
   park carries a mandatory `--reason`, written as cell/header
   decoration (`on-hold (<why> — since <date>)`) that
   `normalize_status` reads through and the new `status_note`
   recovers. `done` refuses a reason — a decorated done would evade
   the gate's exact flip detection. CLI, MCP, and workbench
   mutation bodies all carry it; §2.3 declares three vocabulary
   groups and the parity test pins them.
2. **Phase pause/resume** (WLA-17-02) — `dw phase pause --reason` /
   `resume` write the phase header (bullet/bare shape preserved,
   the flagship's bare shape inserted when absent) and the README
   index row together; `pause_phase`/`resume_phase` ride the
   workbench preview→apply editor; the rail event taxonomy grew
   `phase_paused`/`phase_resumed`.
3. **Honest next + the ledger** (WLA-17-03) — `next` skips paused
   phases and parked stories but names the counts; `dw holds
   [--json]` prints one greppable line per hold; context carries
   `parked`; a bare park warns, never errors. The flagship read
   surfaced HS-25-07 — blocked, reasonless, forgotten since phase
   25 of a 93-phase project — the exact failure mode this phase
   ends.
4. **The terminal board** (WLA-17-04) — `dw board`: swimlane per
   phase, six status columns, ✓ receipts, hold reasons footnoted,
   honest folds everywhere (+N more, retired counted, table-less
   phases named). The flagship's ~90 phases render in 0.1s; phase
   92's prose-hidden pivot reads as ten identical bare in-progress
   cards.
5. **The board on glass** (WLA-17-05) — `/api/projects/<slug>/board`
   + `#/board`: pointer lane leading, paused lanes dimmed behind
   their ⏸ reason banner, closed lanes folded into one-line
   receipts; screenshots in assets/; the viewport smoke grew to 7
   views × 2 sizes.
6. **Guarded moves** (WLA-17-06) — drag a card (or ⇄) and the board
   constructs the editor's own `update_story_status` intent through
   the existing preview → fingerprint-bound apply flow. No new
   write path; park-needs-reason, done-needs-evidence, paused/
   closed-lane refusals, and the stale-fingerprint 409 all proven
   over real HTTP.

## What shipped

`model.py` (HOLD_STATUSES, PARKED_STATUSES, normalization keywords,
`status_note`), `mutations.py` (reason decoration; pause/resume
plans), `parse.py` (`phase_header_status`, `phase_is_paused`),
`api.py` (parked-aware `next_story`, `parked_summary`/`headline`,
phase pause fields, story `status_token`/`status_note`), the new
`board.py`, `validate.py` (bare-park warning), `events.py` (two new
taxonomy entries), CLI (`--reason`, `phase pause|resume`, `holds`,
`board`), MCP (`dw_story_status` reason + honest `dw_next`),
workbench server (board route, two mutation kinds, reason
passthrough) and UI (board view, guarded moves, editor reason
field), docs (§2.3, CLAUDE snippet + regenerated block,
mission-control §3), tests 183 → 199.

## Deliberately deferred

- A `cut` write status (read-side recognition only, carried again).
- Hold expiry / "wake me when" scheduling — reasons are prose;
  `dw holds` is the review surface.
- Drag-to-reorder within a column — table order is priority order.
- Cross-phase moves from the board — a story moves between columns
  of its own phase.
- Offering `dw phase pause` upstream to the flagship's 92/93 (the
  machinery now exists; adopting it is the consumer's decision).
