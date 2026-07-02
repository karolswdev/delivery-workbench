# WLA-4-01 - Add roadmap maintenance CLI

- **Project:** work-log-automation
- **Phase:** 4
- **Status:** done
- **Depends on:** WLA-3-03
- **Unblocks:** future roadmap maintenance automation
- **Owner:** unassigned

## Problem

Maintaining Delivery Workbench roadmaps currently requires remembering the
directory contract, filenames, phase index rows, story table rows, and evidence
conventions by hand. That makes routine PMO work feel heavier than it should,
especially for simple questions like "what is done?", "what is in this phase?",
or "create the next phase."

## Scope

- **In:** A small CLI for listing roadmap projects, rendering a phase/story
  tree, creating phases, creating stories, and checking structural consistency.
- **Out:** A web UI, remote sync, a database, automatic acceptance-criteria
  authorship, and replacing the commit-time PMO contract.

## Acceptance criteria

- [x] A CLI entrypoint exists under `pmo-roadmap/bin/` and can run from the
  repository root without external dependencies.
- [x] `tree` output shows roadmap project, phase, story ID, story status, and
  evidence presence.
- [x] `context` output exposes the same roadmap state as JSON for agents.
- [x] `phase create` creates a `phase-{n}-{slug}/current-phase-status.md` file
  using the canonical phase template and updates the project README phase
  index.
- [x] `story create` creates the next numbered story file, assigns the correct
  story ID prefix, and inserts a matching row into `current-phase-status.md`.
- [x] `check` validates missing phase status files, broken story links, header
  status/table status mismatches, and missing evidence references.
- [x] CLI docs include examples for creating a phase, viewing done work, and
  listing stories in a phase.

## Test plan

- **Unit:** Syntax/compile check for the chosen implementation language.
- **Integration / Cypress:** Temporary-repo CLI smoke tests covering
  `tree`, `phase create`, `story create`, and `check`.
- **Manual / device:** Run the CLI against this repository's
  `work-log-automation` roadmap and verify the output matches the current
  phase/story files.

## Notes / open questions

The CLI should automate the artifact mechanics without inventing roadmap
content. Generated files can use templates and placeholders; problem
statements, scope tradeoffs, acceptance criteria, and evidence still need
human or agent judgment.
