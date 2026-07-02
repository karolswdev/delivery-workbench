# WLA-5-01 - Define Workbench product contract and UX architecture

- **Project:** work-log-automation
- **Phase:** 5
- **Status:** done
- **Depends on:** WLA-4-03
- **Unblocks:** WLA-5-02, WLA-5-03, WLA-5-04, WLA-5-05, WLA-5-06
- **Owner:** unassigned

## Problem

The Phase 4 CLI/core makes PMO roadmap manipulation safe for agents, but a
rich workbench can still fail if it starts as a UI sketch rather than a product
contract. Future agents need a written contract for what the workbench is, what
it refuses to be, which UX modes exist, how the API behaves, and how every
write remains evidence-first.

## Scope

- **In:** Product contract, user/operator modes, information architecture,
  local runtime assumptions, API envelope sketch, mutation lifecycle, design
  rules, accessibility expectations, mobile/desktop viewport requirements, and
  acceptance gates for the rest of Phase 5.
- **Out:** Implementing UI components, introducing a frontend framework,
  building the server, or editing PMO files through ad hoc browser code.

## Acceptance criteria

- [x] `implementation-plan.md` explains the objective, non-negotiable
  constraints, package layout, API shape, UI modes, mutation lifecycle, tests,
  and definition of done.
- [x] `current-phase-status.md` records Phase 5 scope, exit criteria,
  sequence, risks, and decisions with enough detail for a future agent to pick
  up WLA-5-02 without chat history.
- [x] All Phase 5 story files have concrete acceptance criteria and test plans.
- [x] The plan explicitly states that Markdown remains source of truth and no
  database/cache can become authoritative.
- [x] The plan explicitly requires preview/diff/apply/revalidate for every
  mutation.
- [x] The plan names UI modes for overview, phase board, story/evidence,
  health, trace, editor, and preview/diff.
- [x] `dw check work-log-automation` passes after planning artifacts are added.

## Test plan

- **Unit:** n/a for planning artifact.
- **Integration / Cypress:** `pmo-roadmap/bin/dw check work-log-automation`.
- **Manual / device:** Cold-read Phase 5 status, implementation plan, and story
  files; verify a new agent can identify the next safe implementation story and
  the quality gates.

## Notes / open questions

This story is planning work and may be completed with evidence once the Phase 5
roadmap artifacts are in place. It does not authorize building UI before
WLA-5-02 extracts the reusable core boundary.
