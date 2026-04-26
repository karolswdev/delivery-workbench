# WLA-1-01 - Add work-log consent to the canonical contract

- **Project:** work-log-automation
- **Phase:** 1
- **Status:** backlog
- **Depends on:** WLA-0-01
- **Unblocks:** WLA-1-02, WLA-1-03
- **Owner:** unassigned

## Problem

The existing contract certifies PMO rule compliance, but daily logging needs a
separate consent grant with reasons and exclusions. Without this, the framework
would turn every accepted commit into a work-log entry whether or not the
committer meant to create one.

## Scope

- **In:** Update `pmo-roadmap/templates/PMO-CONTRACT.md` and
  `pmo-roadmap/templates/CLAUDE-snippet.md` with consent instructions.
- **Out:** Hook parsing and log writing.

## Acceptance criteria

- [ ] Contract template contains `**Work-log consent:** yes|no`, reasons, and
  exclusions outside the canonical seven checkbox list.
- [ ] Contract text states that `yes` is required for logging and `no` is valid.
- [ ] Agent instructions explain how to choose consent honestly.
- [ ] Existing seven PMO rules remain intact and in order.
- [ ] The implementation notes say the consent line is not counted by
  `EXPECTED_BOXES`.

## Test plan

- **Unit:** n/a for docs-only.
- **Integration / Cypress:** n/a.
- **Manual / device:** Compare contract examples against expected hook parsing
  fields before implementing WLA-1-02.

## Notes / open questions

Do not bump `EXPECTED_BOXES` for work-log consent. The consent line is a
separate key-value contract surface, not an eighth PMO rule checkbox.
