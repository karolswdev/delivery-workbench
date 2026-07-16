# WLA-22-01 - Map the solution and contract the briefing

- **Project:** work-log-automation
- **Phase:** 22
- **Status:** done
- **Depends on:** none
- **Unblocks:** WLA-22-02, WLA-22-03, WLA-22-04, WLA-22-05
- **Owner:** unassigned

## Problem

Twenty-one shipped phases have produced a capable system, but its
current explanation is distributed across the root README, architecture,
mission-control, MCP, interop, rider, distribution, contribution, and
roadmap documents. The roadmap README itself still said “last updated:
Phase 18” and “shipped through v1.8.0” after v1.14.0 and Phase 21. Link
lint and behavior tests cannot catch semantically stale prose. A new
operator or agent can discover every specialist command and still lack
one truthful answer to “where is this solution, and what should I do
next?”

This story makes the audit durable and contracts the aggregate answer
before code gives it authority.

## Scope

- **In:** `docs/solution-overview.md`, `docs/status-briefing.md`, the
  Phase 22 plan and story specifications, the root documentation index,
  and the project roadmap's current phase/release summary.
- **Out:** status implementation, new CLI/MCP/HTTP/UI behavior, a release
  bump, and rewriting specialist documents that remain accurate.

## Acceptance criteria

- [x] A dated solution overview maps product purpose, architecture,
  state/source ownership, supported workflows and surfaces, trust
  boundaries, distribution, verification evidence, current limitations,
  and the observations that selected Phase 22.
- [x] Every behavioral/current-state claim points to an executable test,
  command, or canonical specialist document; time-sensitive counts are
  explicitly a 2026-07-15 snapshot.
- [x] `docs/status-briefing.md` freezes the v1 model's keys, readiness
  meaning, project-selection rule, action precedence, purity boundary,
  exit contract, and cross-surface parity requirement before WLA-22-02.
- [x] Phase 22 has five sequenced, testable stories with explicit scope,
  dependencies, acceptance criteria, tests, risks, and deferred work.
- [x] The project README no longer claims Phase 18/v1.8.0 is current and
  the root README links the comprehensive overview and briefing contract.
- [x] `docs-lint.sh`, `canon-lint.sh`, `dw check`, and the core suite pass.

## Test plan

- **Unit:** core suite retains document/surface parity checks.
- **Integration:** `pmo-roadmap/tests/docs-lint.sh` and
  `pmo-roadmap/tests/canon-lint.sh`; `dw check work-log-automation`.
- **Manual / device:** read the two documents from the root README alone
  and verify every named path/command resolves in this checkout.

## Notes / open questions

The overview is a product/architecture map, not a replacement for the
specialist contracts. It owns the “whole”; each subsystem document still
owns its exact protocol and policy. Counts are snapshot evidence rather
than silently evergreen marketing claims.
