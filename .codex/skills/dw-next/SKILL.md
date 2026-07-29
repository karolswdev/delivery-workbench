---
name: dw-next
description: Start from the Delivery Workbench status briefing and pick up the next story.
---

Orient yourself in this repository's Delivery Workbench roadmap and
report what to work on next. Do not change anything yet.

## Delivery task

Report readiness, current work, any blocker, progress, and the source-backed
next step. Ask for a missing delivery-scope decision instead of guessing.

## Technical details

1. Run `.githooks/dw status --json` and read its JSON even if it exits 1.
   Exit 0 means `ready`; exit 1 means `attention`, which is valid data. If
   its action is blocking, report the named repair and stop. If it requires
   project selection, ask rather than guessing, then rerun with that slug.
2. Read `next_action`; this command is report-only, so do not execute a
   mutation yet. Use `.githooks/dw next --json` for the focused story object
   (exit 2 means nothing is actionable).
3. Run `.githooks/dw check` and `.githooks/dw context --compact`; read
   the current phase's `current-phase-status.md` "Where we are" section
   and the story file itself.
4. Report: the status verdict and recommendation, story ID and title, its acceptance criteria, any lint
   issues or warnings that affect it, and your plan to complete it.

If the user confirms, run `.githooks/dw step [project] --json` and review the
fresh lease. Require `applicable: true` and action `start-story`, then invoke
that document's exact `apply_command`; never reconstruct or modify its argv.
Stop after its one receipt and report the newly observed action. If the lease
is stale, manual, prohibited, or names anything else, do not apply it. Never
continue into a step loop.
