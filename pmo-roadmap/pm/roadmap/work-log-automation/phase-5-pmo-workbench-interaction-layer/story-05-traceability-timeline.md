# WLA-5-05 - Build traceability timeline

- **Project:** work-log-automation
- **Phase:** 5
- **Status:** done
- **Depends on:** WLA-5-02, WLA-5-03
- **Unblocks:** WLA-5-06, WLA-5-08, WLA-5-10
- **Owner:** unassigned

## Problem

The PMO model pays off when a reader can trace a story from intent to proof:
README, phase status, story file, evidence file, final summary, commits, and
work-log entries. The workbench needs this trace as a first-class view, not an
afterthought.

## Scope

- **In:** Story trace view, phase trace view, recent commit list, work-log
  entry list, missing-link states, final-summary connection, source backlinks,
  and timeline event normalization.
- **Out:** Git history rewriting, commit graph visualization beyond PMO paths,
  remote PR integration, or inferring proof that is not present in source files.

## Acceptance criteria

- [ ] Story detail includes a trace chain for README, phase status, story,
  evidence, final summary, recent commits, and work-log entries where present.
- [ ] Missing evidence/final-summary/work-log entries render as explicit absent
  states rather than disappearing.
- [ ] Recent commit links are scoped to the relevant PMO files.
- [ ] Work-log entries honor `PMO_WORK_LOG_DIR` and degrade cleanly when no log
  root exists.
- [ ] Timeline events are sortable, source-linked, and exportable as JSON for
  agents.
- [ ] The timeline does not claim a story is shipped unless story status and
  evidence agree.

## Test plan

- **Unit:** Trace normalization tests with no git, git only, work-log only, and
  both git/work-log available.
- **Integration / Cypress:** Fixture story with evidence and fake work-log entry
  renders complete trace; fixture without evidence renders missing state.
- **Manual / device:** Verify trace readability on desktop and mobile and that
  source links point to real files.

## Notes / open questions

Trace is read-only in this story. Editor affordances can link from trace later,
but should not be required for this slice.
