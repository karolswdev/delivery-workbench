# WLA-5-04 - Build health drift and validation console

- **Project:** work-log-automation
- **Phase:** 5
- **Status:** backlog
- **Depends on:** WLA-5-02, WLA-5-03
- **Unblocks:** WLA-5-06, WLA-5-07, WLA-5-10
- **Owner:** unassigned

## Problem

The workbench should make PMO drift obvious before an agent edits anything.
Broken links, stale current-phase pointers, multiple open phases, missing
evidence, orphan evidence, and older hook snapshots are not edge cases; they
are the exact problems the PMO Workbench exists to expose.

## Scope

- **In:** Health dashboard, issue grouping, severity model, source file links,
  drift explanations, validation refresh, hook snapshot panel, work-log config
  visibility, and refusal state handoff to the editor.
- **Out:** Automatic repair, hook installation/update, or suppressing issues
  without changing source Markdown.

## Acceptance criteria

- [ ] Health console renders all `dw check` issues and context warnings with
  source file paths.
- [ ] Issues are grouped by project, phase, story/evidence, hook/runtime, and
  supplemental canon.
- [ ] Stale README current-phase pointers are visibly distinct from broken
  story/evidence links.
- [ ] Multiple-open-phase warnings include the phase folders involved.
- [ ] Older hook snapshot reporting explains missing config/local/work-log
  seams without overwriting hooks.
- [ ] Editor entry points are disabled or guarded when validation issues would
  make a mutation ambiguous.
- [ ] The console includes copyable command output for `dw check` or equivalent
  core validation.

## Test plan

- **Unit:** View-model tests for each validation issue type and warning type.
- **Integration / Cypress:** Fixture with stale pointer, multiple open phases,
  broken story link, broken evidence link, missing evidence, orphan evidence,
  and older hook snapshot renders all issues.
- **Manual / device:** Verify keyboard navigation and readable issue density on
  desktop and mobile.

## Notes / open questions

Do not hide drift to make the UI look clean. A noisy but accurate health
console is better than a polished false green state.
