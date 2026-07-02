# WLA-5-03 - Build read-only roadmap explorer

- **Project:** work-log-automation
- **Phase:** 5
- **Status:** backlog
- **Depends on:** WLA-5-02
- **Unblocks:** WLA-5-04, WLA-5-05, WLA-5-06
- **Owner:** unassigned

## Problem

Humans and agents need a first screen that answers the operational questions
without opening a directory tree: which projects exist, which phases are
active, what is done, what lacks evidence, and what should be picked up next.
The first UI slice must be read-only so trust is built before mutation.

## Scope

- **In:** Local workbench shell, project overview, phase board, story/evidence
  pair read view, final-summary visibility, supplemental canon links, next
  actionable work, empty states, loading states, and API-backed refresh.
- **Out:** Editing, mutation preview/apply, committing, hosted auth, or
  realtime collaboration.

## Acceptance criteria

- [ ] A documented local command starts the workbench against an explicit repo
  root.
- [ ] The first screen shows projects, active phase count, validation count,
  next story, and last refresh time.
- [ ] Project detail shows phase list, phase status, story counts by status,
  evidence presence, and final-summary presence.
- [ ] Phase detail shows the story table normalized from
  `current-phase-status.md` with links to source files.
- [ ] Story detail shows normalized metadata and source-faithful Markdown
  preview for story and evidence files.
- [ ] Supplemental canon files appear as indexed context, not as editable state.
- [ ] UI refresh never writes files and can be verified by filesystem checksums
  across repeated loads.

## Test plan

- **Unit:** API response mapping tests for overview/project/phase/story view
  models.
- **Integration / Cypress:** Browser test loads the explorer against a fixture
  repo and asserts project, phase, story, evidence, and supplemental canon
  rendering.
- **Manual / device:** Desktop and mobile screenshots prove the first viewport
  is the actual PMO overview and text does not overlap.

## Notes / open questions

Use dense operational UI rather than a landing page. The workbench is a tool
surface for repeated use, not a marketing site.
