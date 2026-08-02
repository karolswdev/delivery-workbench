# WLA-36-03 - Board and cards

- **Project:** work-log-automation
- **Phase:** 36
- **Status:** done
- **Depends on:** WLA-36-01
- **Unblocks:** WLA-36-05
- **Owner:** unassigned

## Problem

The board is the home view and it reads as scaffolding: flat grey boxes, a badge zoo (three unrelated pill styles per card), dashed-border empty columns, tracked-out uppercase mono column labels, and no hover or depth model.

## Scope

- **In:** The board redesigned as the flagship surface: Linear-style cards (translucent surface, border tier, 8px radius, title in 510, metadata in 13px tertiary, ONE status system - dot + label, attention accent used sparingly), quiet column headers with counts, designed empty states (no dashed borders; a single quiet line), luminance hover lift, coherent create/park/move affordances, and the phase/flat toggle as a proper segmented control.
- **Out:** Non-board panels (story 04).

## Acceptance criteria

- [ ] Cards follow one anatomy: status dot + title (510) + metadata line (13px tertiary) + at most one accent badge; the three-pill zoo is gone.
- [ ] Column headers are quiet 13px/510 labels with counts; no uppercase mono tracking; empty columns show one quiet muted line, no dashed boxes.
- [ ] Hover and drag states use luminance lift and the border tiers; motion respects reduced-motion.
- [ ] The Flat/By-phase toggle is a designed segmented control; create/park/refusal flows keep their guarded behavior and read as part of the same system.
- [ ] Board renders clean at 1440x900 and 390x844 in both themes with no horizontal scroll and no misaligned edges (verified against fresh screenshots reviewed by the operator).
- [ ] Browser exam, accessibility contract, and language lint green.

## Test plan

- **Unit:** covered by the verification command below.
- **Integration:** `bash pmo-roadmap/tests/workbench-ui-smoke.sh`
- **Manual / device:** operator reviews rendered screenshots before the story flips done.

## Notes / open questions

The four-column Operator layout stays; this is a reskin to a real standard, not an information-architecture change.
