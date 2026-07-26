# Evidence - WLA-27-09

- **Story:** WLA-27-09 - Harden keyboard, screen-size, and assistive use
- **Status:** done
- **Date:** 2026-07-25

## One interaction contract across the redesigned journeys

The Workbench shell and the Phase 27 views now implement one keyboard and focus
contract. The first Tab exposes a skip control; skip and route navigation focus
the page heading. Tabs use Left/Right/Home/End, delivery choices and plan
sections use arrow-key movement, and native controls retain Enter and Space
activation.

Reviews, confirmations, explicit streams, and action previews are labelled
non-modal dialogs. They remember the exact opener, receive focus when rendered,
support Escape where dismissal is safe, and restore focus to that opener.
Program Studio keeps the in-memory draft when a review is dismissed. Native
`details` disclosures remain native and keep focus on their summary.

Background redraws have a different contract from navigation. Refresh, polling,
SSE, and compiler redraws capture a stable control identity and restore it
without scrolling or moving focus to new activity. Only a changed ledger head
is announced; duplicate poll/SSE versions and stable reconnect facts are
suppressed. Route changes deliberately announce the destination and focus its
heading while the named main region exposes its loading state with
`aria-busy`.

## Meaningful structure without a second source of truth

The shell provides separately named primary navigation, breadcrumb navigation,
main content, route status, and material-update status. A shared client-side
semantic pass names rendered sections, forms, tables, progress, validation
errors, dialogs, tablists, tabs, and tab panels from their visible content.
Each dynamic view has one page heading. Progress exposes its numeric value and
plain-language value text.

Ready, active, completed, warning, blocked, failed, revoked, and unavailable
states retain visible text and a status symbol as well as color and border
shape. Exact IDs, hashes, paths, and receipts remain selectable and inspectable.
No canonical state, permission, action, event, persistence, JSON, MCP, HTTP, or
authority contract changed; this is an interaction and presentation layer over
the existing facts.

The complete keyboard, focus, semantics, live-update, and viewport behavior is
documented in the [Workbench accessibility contract](../../../../../docs/accessibility.md).

## Narrow, wide, long-content, and preference handling

The reviewed viewports are 1440×900 and 390×844. At narrow width the header,
primary navigation, tablists, delivery choices, tables, and graph canvases use
bounded local scrollers where necessary. Forms and fact grids collapse to one
column; run timelines, ledger hashes, long IDs, paths, and technical content
wrap or scroll inside their owner instead of widening the page. Coarse-pointer
targets are at least 44 pixels high.

Reduced-motion preferences remove repeating pulses and animated transitions.
Forced-colors rules retain focus, warning, status, and dialog boundaries.
Wide layouts keep their denser relationships without acquiring a minimum
content width that can force page scrolling.

## Executable journey and browser proof

The versioned
[`accessibility-journeys-v1.json`](../../../../tests/accessibility-journeys-v1.json)
matrix covers the same thirteen IDs and canonical starting states as the
WLA-27-02 journey contract. Every entry records:

- the keyboard path and focus-return behavior;
- headings, regions, forms, errors, progress, blockers, and state semantics;
- the live-update announcement rule;
- wide and narrow layout observations; and
- dated wide, narrow, and assistive-semantic review results.

[`workbench-accessibility-contract.py`](../../../../tests/workbench-accessibility-contract.py)
rejects missing journeys, mismatched canonical states, viewport drift,
incomplete manual records, and non-passing review results. Its four planted red
cases prove those failures are enforced.

[`workbench-accessibility.py`](../../../../tests/workbench-accessibility.py)
uses Firefox 152's Marionette WebDriver endpoint and the Python standard
library. It performs real key actions and checks skip behavior, destination
focus, dialog focus/return, Escape dismissal, tab keys, native disclosures,
draft retention, redraw focus, changed-only announcements, textual stop and
receipt evidence, completion text, semantic names, unique IDs, one page
heading, progress values, tab relationships, non-color state, owned overflow,
and page-level horizontal scrolling.

Firefox enforces a 500-pixel minimum outer window through WebDriver. The DOM
exam therefore uses native 150% page zoom for a stricter no-more-than-390
CSS-pixel interaction viewport, while the screenshot half of the harness
continues to render the exact unzoomed 390×844 viewport.

## Recorded manual review

All 88 rendered screenshots were retained for this review. Representative
wide and narrow contact sheets covered arrival, capability choice, delivery
plan authoring, team/review design, preflight, active progress, failed repair,
human decision, remaining permission/cost, permanent stop receipt, stale-live
recovery, certified completion, and technical inspection.

Direct inspection confirmed the hierarchy and safe next action remained
visible, responsive grids collapsed without overlap, local navigation and graph
scrollers did not widen the page, long exact values remained inspectable, and
state text/symbols remained understandable without color. Keyboard and
browser-derived semantic inspection confirmed the corresponding names,
relationships, focus returns, and update behavior. This is a recorded
assistive-use review of the declared browser matrix, not a formal third-party
accessibility certification.

## Regression and distribution proof

- The complete core suite passes all 496 tests in 868.038 seconds, including
  the four new accessibility contract tests and all exact core/MCP/HTTP/CLI,
  authority, recovery, and replay invariants.
- The browser harness passes 88 exact viewport renders. Its core accessibility
  suite covers 10 journeys with 20 wide/narrow audits and 70 assertions; its
  program suite covers 3 journeys with 6 audits and 22 assertions.
- Product-language, usability-journey, documentation/link, canonical-roadmap,
  Workbench explorer, shell, Python, JavaScript, mirror, and whitespace checks
  pass.
- Fresh wheel and source distributions build and install on Python 3.9. The
  packaged no-program, deliberate-step, bounded-orchestration, outward-signal,
  and autonomous-program exams pass. The packaged autonomous exam replays and
  streams 203 events across three stories and two phases with nine conductor
  and eighteen delivery-boundary crash recoveries and no duplicate starts.

## Acceptance mapping

- Keyboard-only completion and visible logical focus order are covered by all
  thirteen matrix entries and real WebDriver key actions.
- Structure, labels, relationships, errors, progress, blockers, state changes,
  and non-color meaning are covered by the rendered DOM audit and retained
  captures.
- Predictable review/disclosure focus, safe dismissal, exact return, and draft
  retention are covered by the core and program interaction exams.
- Non-stealing, changed-only live updates are covered by redraw focus tests and
  duplicate announcement assertions.
- Exact narrow/wide rendering, locally owned overflow, long identifiers, and
  no horizontal page scroll are covered by 88 captures and 26 DOM audits.
- The dated matrix, static contract, planted red cases, browser interaction
  exam, and manual review bind every failure to its canonical journey and
  owning state.

### Captured run — 2026-07-26T04:35:41Z

- **Command:** `set -e
python3 pmo-roadmap/tests/workbench-accessibility-contract.py
DW_UI_FAST_A11Y=1 bash pmo-roadmap/tests/workbench-ui-smoke.sh
python3 pmo-roadmap/tests/product-language-contract.py
python3 pmo-roadmap/tests/usability-journey-contract.py
bash pmo-roadmap/tests/docs-lint.sh
bash pmo-roadmap/tests/canon-lint.sh
node --check pmo-roadmap/workbench/app.js
python3 -m py_compile pmo-roadmap/tests/workbench-accessibility-contract.py pmo-roadmap/tests/workbench-accessibility.py
bash -n pmo-roadmap/tests/workbench-ui-smoke.sh pmo-roadmap/tests/package-smoke.sh
cmp pmo-roadmap/workbench/app.js .githooks/workbench/app.js
cmp pmo-roadmap/workbench/index.html .githooks/workbench/index.html
cmp pmo-roadmap/workbench/style.css .githooks/workbench/style.css
.githooks/dw rider docs --check
bash pmo-roadmap/update.sh . --check
git diff --check`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 2dbc94019263e8423d99c3d2d9b005397b673e76

```text
workbench-accessibility-contract.py: ok (13 journeys, 2 viewports, keyboard/focus/semantics/manual evidence)
workbench-accessibility.py: ok (10 journeys, 20 wide/narrow audits, 70 assertions, suite=core)
dw-workbench: shutting down
dw-workbench: serving /private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/pmo-ui-smoke.oGHKJj/repo
dw-workbench: http://127.0.0.1:21566/ (localhost or your own .ts.net tailnet; Ctrl-C to stop)
dw-workbench: writes require a guarded preview→apply content boundary or an exact step/run/program token; never stages, certifies, or commits
workbench-accessibility.py: ok (3 journeys, 6 wide/narrow audits, 22 assertions, suite=program)
workbench-ui-smoke.sh: ok (88 viewport renders plus 13 keyboard, semantic, focus, and wide/narrow journey exams)
dw-workbench: shutting down
dw-workbench: serving /private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/pmo-ui-smoke.oGHKJj/dw-program-test.s8is231j/repo
dw-workbench: http://127.0.0.1:24836/ (localhost or your own .ts.net tailnet; Ctrl-C to stop)
dw-workbench: writes require a guarded preview→apply content boundary or an exact step/run/program token; never stages, certifies, or commits
product-language-contract: ok (10 concepts, 18 surfaces, 15 migrated, 18 reserved terms, 13 fixtures, 7 snapshots, 8 source regions)
usability-journey-contract: ok (13 journeys, 23 reachable states, 6 red fixtures; baseline 88 steps, 38 decisions, 81 engineering terms, 13 dead ends, 26 context switches)
docs-lint: ok (474 markdown files)
docs-lint.sh: ok (0s)
canon-lint.sh: ok
dw rider docs: all rendered surfaces match canon
update.sh: up to date (vendored rails match source v1.14.0)
```
