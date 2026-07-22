# WLA-26-02 — Select work across a governed roadmap scope

- **Project:** work-log-automation
- **Phase:** 26
- **Status:** done
  <!-- status vocabulary: roadmap-builder.md §2.3 -->
- **Depends on:** WLA-26-01
- **Unblocks:** WLA-26-03, WLA-26-04, WLA-26-06, WLA-26-08, WLA-26-09
- **Owner:** unassigned

## Problem

Autonomy starts with choosing the right work, but “next” is not merely the
first backlog row. A program may cover selected phases, dependency chains, and
story classes while respecting active work, holds, blocks, phase state, risk,
and workflow/team policy. Every choice and exclusion must be deterministic and
explainable before it may start an agent.

## Scope

- **In:** pure program parser/compiler and roadmap-scope planner; explicit
  phase/story selectors and bounded phase ranges; eligibility/dependency/hold/
  status rules; ordered workflow and organization binding rules; candidate,
  assignment, refusal, and simulation documents; CLI
  `program validate|simulate|plan` reads.
- **Out:** starting a run; creating a grant; mutating roadmap files; model-based
  prioritization; cross-repository selection; auto-skipping failed work.

## Acceptance criteria

- [x] The compiler rejects unknown keys, duplicate ids, invalid phase ranges,
  dangling workflow/role/rubric references, ambiguous equal-priority matches,
  unsupported status, and scope that can never select work.
- [x] The pure planner chooses an already-in-progress eligible story first,
  otherwise a stable declared order, and explains paused/on-hold/blocked,
  dependency-incomplete, out-of-scope, closed, already-active, and no-work
  candidates distinctly.
- [x] One result binds repository HEAD/index/operation, roadmap snapshot and
  health, program hash, scope, story, workflow/template version, implementer,
  required independent verifier, optional council/meta-verifier/architect
  policy, and a human-readable “why this assignment” derivation.
- [x] Repeated planning is byte-equivalent at one observation time and starts
  no work, writes no policy/roadmap/run state, and creates no grant.
- [x] CLI/core parity and red fixtures cover multiple phases, dependency
  boundaries, holds, active-story resumption, exhausted scope, and an
  intentionally ambiguous rule set.

## Test plan

- **Unit:** planner/compiler fixtures in `pmo-roadmap/tests/dw-core-tests.py`.
- **Integration:** CLI JSON against a fixture roadmap containing two phases,
  dependencies, a hold, one active story, and multiple workflow/team bindings.
- **Manual / device:** inspect explanation output for both the chosen story and
  every refused candidate; no device work.

## Notes / open questions

Phase 26 uses declared stable policy, not an LLM ranking stories. An architect
agent may recommend roadmap changes inside a workflow, but selection authority
continues to come from the compiled program.

Delivered `dw program list|validate|simulate|plan` as a pure optional surface.
The compiler resolves one tracked program/workflow/organization/rubric family,
keeps layout-only edits outside semantic authority, and requires both a writer
and an independently resolved read-only verifier. The planner binds Git,
roadmap, policy, workflow/rubric versions, and local roster facts; explains all
five fixture stories; and stamps every write/start/grant effect false.
