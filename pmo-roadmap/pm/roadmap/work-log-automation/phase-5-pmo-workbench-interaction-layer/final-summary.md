# Phase 5 Final Summary

**Status:** complete.
**Date:** 2026-07-02.

## Outcome vs exit criteria

All ten exit criteria closed with evidence. The audit trail, per
requirement: core extraction and CLI compatibility
(evidence-story-02: byte-identical Phase 4 output matrix); the
documented workbench command and read-only browsing surface
(evidence-story-03: `dw-workbench --root`, checksum-proved read-only
loads); trace UI across all seven artifact kinds (evidence-story-05);
editor through core mutation plans only (evidence-story-06/07);
preview/diff/validation/apply/revalidation on every write
(evidence-story-07: content-bound fingerprints, stale/tamper 409s,
rollback proof, scratch-tree projection); permission tests
(evidence-story-09: Host allowlist, slug alphabet, roadmap
containment, empty-git-index proof); viewport coverage
(evidence-story-10: workbench-ui-smoke.sh, 12 renders per run, CI-run
on ubuntu); dogfood evidence (ten evidence files, 15 screenshots
under assets/, captured suite runs). The proving commands:
`.githooks/dw check work-log-automation` → `dw check: ok`;
`python3 pmo-roadmap/tests/dw-core-tests.py` → 78 tests OK;
`pmo-roadmap/tests/workbench-explorer.sh` → ok;
`pmo-roadmap/tests/workbench-ui-smoke.sh` → 12 viewport renders.

## Evidence index

| ID | Story | Evidence | Landing commits |
|---|---|---|---|
| WLA-5-01 | Product contract & UX architecture | [evidence-story-01](./evidence-story-01.md) | pre-hardening |
| WLA-5-02 | Reusable core API boundary | [evidence-story-02](./evidence-story-02.md) | e23a958-era |
| WLA-5-03 | Read-only roadmap explorer | [evidence-story-03](./evidence-story-03.md) | 5d33da8, edf7d15 |
| WLA-5-04 | Health/drift console | [evidence-story-04](./evidence-story-04.md) | e0a328e, a2422c0 |
| WLA-5-05 | Traceability timeline | [evidence-story-05](./evidence-story-05.md) | eb2ee9e, f59a63a |
| WLA-5-06 | Structured editor | [evidence-story-06](./evidence-story-06.md) | b51aa11, 25308bd |
| WLA-5-07 | Preview/diff/apply workflow | [evidence-story-07](./evidence-story-07.md) | cb40bbe, b4b3b43 |
| WLA-5-08 | Commit/work-log evidence views | [evidence-story-08](./evidence-story-08.md) | eca6a81, 8eebe3f |
| WLA-5-09 | Permissions & runtime model | [evidence-story-09](./evidence-story-09.md) | 8c4e5d9, 5ada75b, 9814921 |
| WLA-5-10 | Docs, tests, adoption path | [evidence-story-10](./evidence-story-10.md) | this commit |

## Surprises and lessons

- The guard deadlocked against itself (the missing final summary
  guarded the close that writes it); the fix became a principle — a
  mutation whose projected issues strictly shrink the current set is
  remediation, and remediation is never ambiguous.
- The security tests found a real containment gap before shipping
  distribution: a hostile slug could escape its phase while staying
  inside pm/roadmap. Slug validation now lives in the core.
- Headless-Firefox screenshots demanded two rounds of engineering
  (isolated profiles; synchronous snapshot mode so capture-at-load
  sees data) — and then became a reusable viewport test harness.
- dw check's premature-evidence lint fired on this story's own
  evidence mid-flight: the rails guarded their last story (both
  captures kept in evidence-story-10).

## Residual risks (named, not hidden)

- Viewport smoke asserts rendered-size, not DOM content; real browser
  DOM assertions (Cypress-class) remain unbuilt.
- The workbench is single-root, single-user, HTTP/localhost; hosted
  or multi-user use would need WLA-5-09's out-of-scope list revisited.
- projected_issues copies the project tree per preview — fine at this
  repo's scale, unprofiled on very large roadmaps.
- macOS CI leg skips the viewport smoke (no Firefox on the runner).

## Handoff

- Everything runs from one core (`dw_pmo`): CLI, gate, and workbench
  share parsers, validators, planners, and renderers; Markdown under
  `pm/roadmap/**` stays the only source of truth.
- Consumer repos get the workbench via install.sh/update.sh
  (`.githooks/dw-workbench`); adoption guidance is in the framework
  README ("Workbench adoption guidance").
- Future work parked deliberately: hosted/multi-user mode, richer
  redaction, remote sync, DOM-level UI tests, and the deferred items
  in Phase 6's final summary (committed contract-archive mirror,
  work-log retention).
