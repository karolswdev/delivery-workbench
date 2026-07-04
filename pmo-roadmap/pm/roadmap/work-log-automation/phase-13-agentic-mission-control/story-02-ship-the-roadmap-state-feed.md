# WLA-13-02 - Ship the roadmap state feed

- **Project:** work-log-automation
- **Phase:** 13
- **Status:** backlog
- **Depends on:** WLA-13-01
- **Unblocks:** WLA-13-03, WLA-13-05
- **Owner:** unassigned

*Scaffold-grade spec (2026-07-03): direction is firm, details are
not. WLA-13-01 re-pins this story before it starts.*

## Problem

Every external consumer of roadmap state today scrapes it: the
workbench parses Markdown, `dw context --compact` emits a
CLI-shaped snapshot, and the Desk conveyor would be a third ad-hoc
reader. Mission control needs one versioned, schema-stable feed
that external consumers can build against without inheriting the
Markdown layout as an API.

## Scope

- **In:** `dw state --json` (working name): a versioned roadmap
  feed — project, phases, stories with status/evidence trace, next
  actionable story, gate health — with a schema pinned by tests
  and a documented stability promise; the workbench and the
  HoldSpeak counterpart consume it instead of private scraping.
- **Out:** Live sessions and events (stories 03 and 04); any
  transport beyond what WLA-13-01 decided; multi-project
  aggregation (parked candidate, stays parked).

## Acceptance criteria

- [ ] The feed emits the WLA-13-01 schema, version-stamped;
  schema-pinning tests fail on unannounced shape changes.
- [ ] At least one real external reader (the workbench or the
  counterpart pack) consumes the feed in place of private
  scraping, proven by test.
- [ ] Full battery and docs-lint pass.

## Test plan

- **Unit:** schema-pinning tests in `dw-core-tests.py`.
- **Integration:** the consuming reader's suite.
- **Manual / device:** feed rendered from this repo's live
  roadmap, captured as evidence.

## Notes / open questions

- Whether `dw context --compact` becomes an alias of the feed or
  stays a separate CLI-facing view - decide in WLA-13-01.
