---
description: Prove, flip, and ship the current story through the PMO gate.
---

Close out the story the user names (or the current in-progress story
from `.githooks/dw next`). Evidence first, then the flip, then the
gated commit.

1. Prove the work with real runs — for each documented verification
   command:
   `.githooks/dw evidence capture <project> <phase> <story> -- <command>`
   Nonzero exits are recorded honestly; fix and re-capture until the
   run that matters passes. Add narrative context to the evidence file
   around the captured blocks; screenshots/binaries go in `assets/`
   next to it.
2. Flip it: `.githooks/dw story status <project> <phase> <story> done`
   (it refuses without evidence and updates the phase table
   transactionally).
3. Update the phase's "Where we are" pickup snapshot and any canon doc
   the story touches — the gate requires master docs in the same
   commit.
4. Stage everything, then run /dw-contract (generate → verify → certify;
   use `--tests-capture` for the captured run from step 1).
5. `git commit` with a clear message. The gate verifies the flip ships
   its evidence; trailers and the contract archive are automatic.
   Exactly one story flips per commit — bundle only with
   `.tmp/BUNDLE-OK.md` and a one-line rationale.
6. Run `.githooks/dw check` and report the outcome with the commit sha.
