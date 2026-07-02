# WLA-4-02 - Add agent-safe PMO mutation and drift context

- **Project:** work-log-automation
- **Phase:** 4
- **Status:** done
- **Depends on:** WLA-4-01
- **Unblocks:** PMO Workbench agent workflows
- **Owner:** unassigned

## Problem

Agents need more than a pretty tree. They need a deterministic context snapshot
and safe write commands that preserve PMO invariants, especially when a real
consumer repo has stale README pointers, multiple open phases, supplemental
orchestrator files, or an older hook snapshot.

## Scope

- **In:** JSON context drift warnings, supplemental canon discovery, hook
  snapshot reporting, trace paths, status updates, evidence attachment, phase
  close, path allowlisting, rollback-protected write batches, and integration
  tests.
- **Out:** A browser UI, arbitrary markdown editing, cross-repo service hosting,
  or status mutation without paired evidence.

## Acceptance criteria

- [x] `context` reports current-phase pointer issues, multiple-open-phase
  warnings, supplemental canon files, active phases, trace paths, work-log
  entries where available, and hook snapshot compatibility.
- [x] `story status ... done` refuses to proceed without paired evidence.
- [x] `story status ... done --evidence-body ...` updates the story header,
  phase story table, and paired evidence file as one rollback-protected change
  set.
- [x] `story evidence` creates or attaches `evidence-story-N.md` only inside the
  story's phase folder.
- [x] `phase close` refuses open stories unless forced and creates
  `final-summary.md`.
- [x] Tests cover a canonical happy path, idempotent same-status writes,
  standalone evidence attachment, phase-close refusal, work-log trace,
  intentional validation failures, and a drifted consumer-style fixture.

## Test plan

- **Unit:** `python3 -m py_compile pmo-roadmap/bin/dw`.
- **Integration / Cypress:** `pmo-roadmap/tests/roadmap-cli.sh`.
- **Manual / device:** Run `pmo-roadmap/bin/dw context work-log-automation
  --compact` and verify the JSON is parseable.

## Notes / open questions

The CLI remains a constrained PMO mutation layer, not a markdown editor. Future
UI work should call these commands or the same core logic instead of inventing
its own roadmap state.
