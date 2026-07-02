# WLA-5-08 - Integrate commit and work-log evidence views

- **Project:** work-log-automation
- **Phase:** 5
- **Status:** done
- **Depends on:** WLA-5-02, WLA-5-05
- **Unblocks:** WLA-5-10
- **Owner:** unassigned

## Problem

PMO evidence often lives across story files, evidence files, git commits, and
local work logs. The workbench should make that evidence visible without
turning logs into a new source of truth or leaking excluded paths.

## Scope

- **In:** Commit list panels, work-log entry panels, PMO file path scoping,
  absent-state rendering, exclusion-aware work-log reading, evidence export for
  agents, and handoff snippets for commit contracts.
- **Out:** Remote GitHub/GitLab integration, PR review UI, secret scanning, log
  summarization, or changing work-log capture behavior.

## Acceptance criteria

- [ ] Story and phase trace views show recent commits scoped to PMO files.
- [ ] Work-log entries render when `PMO_WORK_LOG_DIR` or default log root
  contains matching entries.
- [ ] Missing work logs are shown as absent optional evidence, not errors.
- [ ] Excluded/omitted work-log paths remain omitted in the UI.
- [ ] Evidence panels can produce a concise agent handoff summary that includes
  source PMO paths and command output references.
- [ ] The UI never treats a work-log entry as a replacement for
  `evidence-story-N.md`.

## Test plan

- **Unit:** Work-log parsing and omission rendering tests.
- **Integration / Cypress:** Fixture with fake commits/work logs renders commit
  and work-log evidence; fixture without logs renders absence states.
- **Manual / device:** Verify evidence panels remain readable without exposing
  full diffs by default.

## Notes / open questions

Remote PR/issue context is intentionally later. Phase 5 should prove local git
and local work-log value first.
