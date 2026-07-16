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
2. Preview `.githooks/dw step [project] --json`; require a fresh,
   `applicable: true` `finish-story` lease for the intended story. Invoke only
   its exact `apply_command`, then stop. Never reconstruct the guarded status
   argv or continue automatically. A stale token or missing evidence refuses
   without starting the transition.
3. Update the phase's "Where we are" pickup snapshot and any canon doc
   the story touches — the gate requires master docs in the same
   commit.
4. Stage everything, then run /dw-contract (generate → verify → certify;
   use `--tests-capture` for the captured run from step 1).
5. Run `git commit` yourself with a clear message — `dw step` cannot commit.
   The gate verifies the flip ships
   its evidence; trailers and the contract archive are automatic.
   Exactly one story flips per commit — bundle only with
   `.tmp/BUNDLE-OK.md` and a one-line rationale.
6. Run `.githooks/dw check` and report the outcome with the commit sha.
