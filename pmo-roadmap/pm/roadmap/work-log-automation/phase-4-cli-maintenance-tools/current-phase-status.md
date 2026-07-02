# Phase 4 - CLI Maintenance Tools

**Last updated:** 2026-07-01.

## Goal

Make routine PMO maintenance mechanically boring by adding a small,
repo-native CLI for roadmap inspection and safe artifact creation: phases,
stories, status trees, done views, and validation.

## Scope

- **In:** CLI entrypoint, roadmap discovery, phase/story tree output, filters
  for done/backlog/evidence gaps, phase scaffolding, story scaffolding, README
  phase-index updates, phase story-table updates, evidence-backed status
  updates, phase close, JSON context, drift reporting, traceability, and
  focused validation.
- **Out:** A database-backed tracker, hosted UI, replacing the PMO contract
  hooks, rewriting hand-authored story content, or LLM-driven planning.

## Exit criteria (evidence required)

- [x] A documented CLI command can list roadmap projects, phases, and stories
  from the existing `pm/roadmap/` directory structure.
- [x] A tree command shows phase/story status and evidence presence without
  requiring manual directory inspection.
- [x] A phase-create command creates a correctly named phase directory and
  `current-phase-status.md` from the canonical template.
- [x] A story-create command creates the next story file and inserts the
  matching row into the phase story table.
- [x] A check command reports missing files, broken story links, status
  mismatches, and missing evidence references without modifying files.
- [x] Safe mutation commands can attach evidence, mark stories done only with
  evidence, close phases, and roll back touched files if a later write fails.
- [x] JSON context reports active phases, next work, stale pointers,
  supplemental canon, hook compatibility, trace paths, recent commits, and
  work-log entries where available.
- [x] Tests exercise the CLI against a temporary roadmap fixture.

## Story status

| ID | Story | Status | Story file | Evidence |
|---|---|---|---|---|
| WLA-4-01 | Add roadmap maintenance CLI | done | [story-01-roadmap-maintenance-cli](./story-01-roadmap-maintenance-cli.md) | [evidence-story-01](./evidence-story-01.md) |
| WLA-4-02 | Add agent-safe PMO mutation and drift context | done | [story-02-agent-safe-mutation-and-drift-context](./story-02-agent-safe-mutation-and-drift-context.md) | [evidence-story-02](./evidence-story-02.md) |
| WLA-4-03 | Complete PMO Workbench requirement audit | done | [story-03-pmo-workbench-requirement-audit](./story-03-pmo-workbench-requirement-audit.md) | [evidence-story-03](./evidence-story-03.md) |

## Where we are

Phase 4 is complete. `pmo-roadmap/bin/dw` and installed `.githooks/dw` support
project listing, tree views, JSON context snapshots, done filters, phase
listing/showing/creation/closing, story listing/creation/status/evidence
updates, next-story selection, drift reporting, trace paths, recent commit and
work-log trace where available, hook snapshot reporting, and structural checks
over the existing markdown artifacts. The CLI has temp-roadmap coverage and is
included in validation.

## Active risks

| Risk | Likelihood | Mitigation | Stop signal |
|---|---|---|---|
| The CLI corrupts hand-authored markdown | medium | Limit automatic edits to known template regions and tables with dry-run/check behavior | A command rewrites prose outside the target table or scaffolded file |
| The CLI becomes a second tracker | medium | Treat markdown files as the only source of truth | State is stored outside the repo roadmap tree |
| Parsing handles only the demo roadmap | medium | Test against temporary fixtures with multiple projects, phases, and story states | A valid scaffolded roadmap cannot be listed or checked |
| Scope grows into a UI before basics work | low | Ship list/tree/create/check first | The first implementation requires a web server or persistent service |

## Decisions made (this phase)

- 2026-07-01 - Build the CLI over existing roadmap markdown artifacts, not a
  database - preserves the Delivery Workbench source-of-truth model - user
  request and roadmap review.
- 2026-07-01 - Keep generated content structural, not editorial - the CLI may
  scaffold files and tables, but humans or agents still write story judgment -
  roadmap review.

## Decisions deferred

- Rich UI or local service wrapper - deferred; the CLI/core must stay the
  invariant-preserving source for any later presentation layer.
- Cross-repo synchronization - deferred; this phase keeps each repo's markdown
  roadmap authoritative.
