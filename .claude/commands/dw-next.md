---
description: Orient in the Delivery Workbench roadmap and pick up the next story.
---

Orient yourself in this repository's Delivery Workbench roadmap and
report what to work on next. Do not change anything yet.

1. Run `.githooks/dw doctor` — if anything FAILs, report it and stop.
2. Run `.githooks/dw next --json`. Exit 0 means a story was found;
   exit 2 means nothing is actionable (report that and stop).
3. Run `.githooks/dw check` and `.githooks/dw context --compact`; read
   the current phase's `current-phase-status.md` "Where we are" section
   and the story file itself.
4. Report: the story ID and title, its acceptance criteria, any lint
   issues or warnings that affect it, and your plan to complete it.

If the user confirms, flip it in-progress before working:
`.githooks/dw story status <project> <phase> <story> in-progress`
