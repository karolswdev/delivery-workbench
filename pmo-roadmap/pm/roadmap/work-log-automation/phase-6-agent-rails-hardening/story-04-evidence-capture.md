# WLA-6-04 - Add evidence capture tooling and content linting

- **Project:** work-log-automation
- **Phase:** 6
- **Status:** done
- **Depends on:** WLA-6-02
- **Unblocks:** WLA-6-05
- **Owner:** unassigned

## Problem

Evidence content is entirely uninspected. An empty file passes the gate;
`dw` itself generates the placeholder "Evidence body intentionally left for
the operator to complete before commit," and that placeholder sails through
both the hook and `dw check`. The dogfood roadmap shows exactly the failure
this invites: all 19 evidence files were written retroactively in one bulk
session, phase-0 evidence cites phase-4 tools that did not exist when the
stories were done, and one phase-3 evidence file opens with a pseudo-command
against a destroyed temp directory. The framework's central promise —
evidence, not vibes — currently rests on reviewer diligence alone, and the
"tests actually ran" contract rule is checkable in principle but checked
nowhere.

## Scope

- **In:** `dw evidence capture <project> <story> -- <command>` runs the
  command and appends a deterministic block to the story's evidence file:
  the exact command, working directory, UTC timestamp, exit code,
  current `git write-tree` index tree, and fenced stdout/stderr (byte-capped
  with an explicit truncation marker). Evidence content linting in
  `dw check`: ERROR for done stories whose evidence is empty or still
  contains the generator placeholder; WARNING when an evidence file
  contains no captured block (narrative-only evidence stays legal but gets
  named); WARNING when the capture timestamp is wildly inconsistent with
  the story's done-flip commit date once WLA-6-01 makes commits resolvable.
  Contract integration: a contract may reference a captured run
  (command + exit code + timestamp) to discharge the "tests actually ran"
  rule mechanically instead of by checkbox. A documented convention for
  binary/screenshot evidence (relative `assets/` paths next to the evidence
  file) so Phase 5's UI stories have a place to put screenshots that
  `dw check` can at least existence-check.
- **Out:** Sandboxing or replaying captured commands; guaranteeing
  reproducibility; semantic judgment of whether output proves the
  acceptance criteria (stays human/agent judgment); retrofitting captures
  into historical evidence files.

## Acceptance criteria

- [ ] `dw evidence capture` produces a block whose format is documented and
  stable, records nonzero exit codes honestly, and never edits content
  outside the evidence file it targets.
- [ ] `dw check` reports ERROR for a done story with empty or
  placeholder-only evidence (regression test in the broken fixture), and
  WARNING for evidence with no captured block.
- [ ] A contract that references a captured run discharges the
  tests-actually-ran rule, and the gate verifies the referenced capture
  exists in the staged evidence with exit code 0.
- [ ] Screenshot/asset references in evidence resolve to existing files
  under the phase directory or `dw check` flags them.
- [ ] The truncation cap is configurable and the marker is asserted in
  tests.

## Test plan

- **Unit:** Capture-block rendering, exit-code recording, truncation, and
  lint rules over fixtures in the `dw_pmo` suite.
- **Integration / Cypress:** `pmo-roadmap/tests/roadmap-cli.sh` extended:
  capture a real command in a temp repo, flip the story done, commit
  through the gate, and assert the lint outcomes.
- **Manual / device:** Use capture for one real Phase 6 story on this repo
  and confirm the evidence reads well to a human.

## Notes / open questions

Captured blocks make evidence longer; WLA-6-06's ceremony work should keep
the narrative sections short since the captures now carry the proof. The
anti-backfill lint is deliberately a warning, not an error — retroactive
evidence is sometimes the honest state of the world and banning it would
just push people to fake timestamps.
