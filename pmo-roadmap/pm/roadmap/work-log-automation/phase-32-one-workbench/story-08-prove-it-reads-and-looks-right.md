# WLA-32-08 - Prove it reads and looks right

- **Project:** work-log-automation
- **Phase:** 32
- **Status:** done
- **Depends on:** WLA-32-03, WLA-32-04, WLA-32-07
- **Unblocks:** phase close
- **Owner:** unassigned

## Problem

The phase changes the workbench's main routes, language, consent flow, and live controls. Passing server tests alone would miss cramped mobile layouts, hidden keyboard traps, technical terms leaking into ordinary panels, and browser tests that silently skipped because Firefox was absent. The phase exam must prove both the authority boundary and the experience a person sees.

## Scope

- **In:** Extend `pmo-roadmap/tests/workbench-ui-smoke.sh` with a route and state matrix for the board home, ideation flow, consent panels, and Live view in light and dark themes at 1440x900 and 390x844. Extend keyboard and focus journeys in `pmo-roadmap/tests/workbench-accessibility.py`. Add a language-lint check under `pmo-roadmap/tests/` that scans ordinary panel templates against `pmo-roadmap/docs/product-language-contract-v1.json` and permits exact contract terms only inside Technical details folds. Re-run `pmo-roadmap/tests/workbench-explorer.sh` and `pmo-roadmap/tests/dw-core-tests.py`, including permission-model and server-handler checks. Store screenshot outputs only in the existing test artifact location during the run; the story's captured evidence must show that Firefox-dependent paths ran.
- **Out:** New product behavior, a replacement browser-test framework, changes to the language contract, waived accessibility failures, silent browser skips, and visual approval based only on desktop or one theme.

## Localization hints

- **Affected files:**
  - `pmo-roadmap/tests/workbench-ui-smoke.sh`
  - `pmo-roadmap/tests/workbench-accessibility.py`
  - `pmo-roadmap/tests/workbench-language-lint.py` (new)
  - `pmo-roadmap/tests/workbench-explorer.sh`
  - `pmo-roadmap/tests/dw-core-tests.py`

## Acceptance criteria

- [ ] The UI smoke matrix opens the board home, ideation flow, bounded-run consent, program consent, and combined Live view in both light and dark themes at 1440x900 and 390x844.
- [ ] The screenshot matrix includes ordinary, empty, blocked or refused, stale or disconnected, paused, revoked, cancelled, and complete states where those states apply.
- [ ] Every journey from 6 through 13 has one canonical next step, one refusal or recovery outcome, and a route into Technical details and back, all exercised by an automated browser or accessibility check.
- [ ] Keyboard-only checks can reach every ordinary action, open and close Technical details, move through confirmation dialogs without a focus trap, return focus to the control that opened them, and see a visible focus indicator in both viewport sizes.
- [ ] The language check fails when a forbidden technical contract term appears in an ordinary panel, reports the file and offending text, and passes when that same exact term appears only inside the panel's Technical details fold.
- [ ] The explorer suite proves HTTP and CLI permission parity, including stale-token refusal, no start-on-open, no live-event mutation, no runtime authority increase, and no generic certify or commit action.
- [ ] Core handler tests cover the bounded-run start property fix and the finite preview-bound bounded-run supervision contract, including invalid properties, stale tokens, excessive ceilings, and no-progress stops.
- [ ] The browser exam fails if Firefox is missing, cannot launch, or skips a required route or state; captured output names the Firefox version and reports a nonzero count of screenshots from both viewports and both themes.
- [ ] Review of the captured screenshots finds no clipped controls, body-level horizontal scroll, unreadable contrast, hidden consequence copy, or missing stale-state marker in either viewport or theme.
- [ ] `.githooks/dw check work-log-automation` reports `dw check: ok` after the phase-exam story and evidence are complete.

## Test plan

- **Unit:** `/usr/bin/python3 pmo-roadmap/tests/dw-core-tests.py`
- **Integration:** `bash pmo-roadmap/tests/workbench-explorer.sh`; `/usr/bin/python3 pmo-roadmap/tests/workbench-accessibility.py`; run the language-lint command added under `pmo-roadmap/tests/` directly and inject one temporary ordinary-panel violation to prove its refusal before restoring the fixture.
- **Manual / device:** `bash pmo-roadmap/tests/workbench-ui-smoke.sh`; inspect every generated 1440x900 and 390x844 screenshot in light and dark themes, verify the command output names Firefox and the screenshot counts, then run `.githooks/dw check work-log-automation`.

## Notes / open questions

Choose the language-lint mechanism during implementation. A DOM-aware fixture check may be safer than plain grep because the same exact term is allowed under Technical details and forbidden beside it. Whatever mechanism lands must have a negative fixture that proves it catches leakage, and the test command must be stable enough for evidence capture. Firefox availability is a precondition for this exam, not a reason to skip it.
