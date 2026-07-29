---
name: dw-contract
description: Generate and honestly certify the commit contract for the staged work.
---

Author the PMO commit contract for the currently staged work.

## Delivery task

Review the intended files and their proof, then prepare the final commit check.
Never claim a rule passed without verifying it.

## Technical details

1. Confirm staging is final (`git status`, `git diff --cached --stat`).
   The contract stamps the staged index tree — restaging afterwards
   invalidates it.
2. Generate it:
   `.githooks/dw contract new [--story <ID>] [--consent yes --reasons "…"] [--tests-capture <evidence-path>[#ts]]`
   Use `--tests-capture` whenever a passing captured run exists in the
   staged evidence — it discharges the "Tests ran." rule mechanically.
3. Read `.tmp/CONTRACT.md`. For each remaining `- [ ]` box, actually
   verify the rule against the staged diff (evidence on disk, master
   docs updated in this commit, no bypasses, pairing, atomicity). Only
   then flip it to `- [x]`. Never flip a box you have not verified —
   the archived contract and digest trailer make this certification
   permanent.
4. Preflight with `.githooks/dw gate` (non-consuming). If it fails,
   the banner names the rule and the fix.
5. Report the contract summary (story, consent, discharged rules) and
   that the commit is ready.
