# WLA-16-04 - The flagship dogfood: HoldSpeak's real tree, before/after

- **Project:** work-log-automation
- **Phase:** 16
- **Status:** done
- **Depends on:** WLA-16-02, WLA-16-03
- **Unblocks:** the Delivery Belt (HoldSpeak phase 86)
- **Owner:** unassigned

## Problem

The three stories above were motivated by one consumer's real tree;
the phase is not honest until re-run against it. Before: 397 `dw
check` errors, phase 17/86 elected current, recent phases reading
0/0 stories. After: the reader must see the tree as its authors do —
every remaining error a desync a HoldSpeak maintainer would fix, not
a dialect the parser refuses.

## Scope

- **In:** A distilled permanent fixture in `dw-core-tests.py`
  reproducing the flagship dialects (so the coverage survives without
  reaching outside the repo), plus the documented live run against
  `~/dev/tools/HoldSpeak`: before/after error counts, the after-list
  triaged line by line in evidence (real desync vs dialect, zero of
  the latter), `current_phase`/`next_story` identity, and story
  coverage for the newest phase. CHANGELOG entry for the release
  notes.
- **Out:** fixing HoldSpeak's real desyncs (that repo's own work, on
  its own gate); shipping a release (the maintainer cuts versions).

## Acceptance criteria

- [ ] `dw check` against the HoldSpeak tree: every remaining ERROR
  line is triaged in evidence as a real desync (missing final
  summaries, a missing status doc, and their like) — zero
  dialect-refusal errors remain.
- [ ] `dw state --json` against the same tree: `current_phase` is
  the README pointer's phase; the newest phase reports its real
  story counts (not 0/0).
- [ ] The distilled fixture fails on pre-phase-16 code (asserted by
  construction notes in evidence) and passes on this branch.
- [ ] Full CI-equivalent local run green: `dw-core-tests.py`,
  `telegram-interface-tests.py`, `gate-parity.sh`,
  `package-smoke.sh`, `workbench-explorer.sh`.
- [ ] CHANGELOG.md gains the phase entry under Unreleased/next.

## Test plan

- **Unit:** the distilled fixture in `dw-core-tests.py`.
- **Integration:** the live HoldSpeak run, captured via
  `dw evidence capture`.
- **Manual / device:** n/a.

## Notes / open questions

- The triaged after-list is the input to HoldSpeak's own cleanup
  story (its phase 86 scaffold consumes it).
