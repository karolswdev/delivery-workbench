# Phase 5 - PMO Workbench Interaction Layer

**Last updated:** 2026-07-02.

## Goal

Ship the rich PMO Workbench interaction layer on top of the existing
agent-safe CLI/core without creating a second source of truth. Humans and AI
agents should be able to inspect, validate, trace, preview, and safely mutate
PMO roadmap state from a local workbench while Markdown under `pm/roadmap/**`
remains authoritative.

## Operating principles

- **Markdown is source of truth:** every view, API response, cache, and UI state
  is derived from files already governed by the PMO contract.
- **Core first, UI second:** the workbench must call the same parser,
  validator, trace, and mutation primitives as `dw`; no duplicate PMO parser in
  browser code.
- **Local-first runtime:** the first supported runtime is a repo-local process
  bound to localhost with an explicit repo allowlist.
- **Preview before write:** mutations expose a structured preview and file diff
  before any apply action.
- **Evidence before done:** the UI cannot mark a story done unless evidence is
  provided or already attached.
- **No auto-commit:** the workbench may draft contract text and show git diffs,
  but it does not commit on behalf of the operator.

## Scope

- **In:** reusable PMO core extraction, local API/server adapter, read-only
  roadmap explorer, health/drift console, trace timeline, structured editor,
  mutation preview/apply flow, commit/work-log evidence views, permission
  model, documentation, tests, and dogfood evidence.
- **Out:** hosted multi-tenant service, cloud sync, realtime co-editing, CRDTs,
  direct writes outside `pm/roadmap/**`, automatic story authorship, automatic
  commits, replacing git/PMO hooks, or a separate database as source of truth.

## Architecture target

```text
pm/roadmap/**/*.md
        |
        v
pmo-roadmap/lib/dw_pmo/          deterministic parser, validator, trace,
        |                         mutation planner, render/apply primitives
        +--> pmo-roadmap/bin/dw   CLI adapter
        |
        +--> pmo-roadmap/bin/dw-workbench
                                  localhost server, allowlisted repo root,
                                  JSON API, static workbench shell
        |
        +--> pmo-roadmap/workbench/
                                  local static UI: explorer, health, trace,
                                  editor, preview/diff, evidence views
```

The workbench may later be embedded into a consumer app, but the first
deliverable must work inside Delivery Workbench itself with no external PMO
state store.

## Exit criteria (evidence required)

- [x] `pmo-roadmap/lib/dw_pmo/` owns the parser, validator, context, trace, and
  mutation-planning code now embedded in `pmo-roadmap/bin/dw`
  (evidence-story-02).
- [x] `pmo-roadmap/bin/dw` remains compatible with the Phase 4 CLI contract and
  imports the shared core (byte-identical output matrix;
  evidence-story-02).
- [x] A documented local workbench command serves a read-only UI and JSON API
  against an allowlisted repo root (`dw-workbench --root PATH`;
  evidence-story-03).
- [x] The read-only UI can browse projects, phases, story/evidence pairs, final
  summaries, supplemental canon, drift warnings, validation issues, and next
  actionable work (evidence-story-03 with screenshots).
- [x] The trace UI links README, phase status, story, evidence, final summary,
  recent commits, and work-log entries where available
  (evidence-story-05 with screenshots).
- [ ] The editor supports create phase, create story, update story status,
  attach evidence, and close phase through core mutation plans only.
- [ ] Every write operation has preview, diff, validation, apply, and
  post-apply revalidation states.
- [ ] Permission tests prove the runtime refuses non-allowlisted repo roots,
  path traversal, arbitrary file writes, and auto-commit attempts.
- [ ] UI tests cover desktop and mobile viewports for explorer, health, trace,
  editor, preview, and validation states.
- [ ] Dogfood evidence records command output, screenshots or equivalent UI
  artifacts, `dw check work-log-automation`, and a final Phase 5 summary.

## Story status

| ID | Story | Status | Story file | Evidence |
|---|---|---|---|---|
| WLA-5-01 | Define Workbench product contract and UX architecture | done | [story-01-product-contract-ux-architecture](./story-01-product-contract-ux-architecture.md) | [evidence-story-01](./evidence-story-01.md) |
| WLA-5-02 | Extract reusable PMO core API boundary | done | [story-02-reusable-core-api-boundary](./story-02-reusable-core-api-boundary.md) | [evidence-story-02](./evidence-story-02.md) |
| WLA-5-03 | Build read-only roadmap explorer | done | [story-03-read-only-roadmap-explorer](./story-03-read-only-roadmap-explorer.md) | [evidence-story-03](./evidence-story-03.md) |
| WLA-5-04 | Build health drift and validation console | done | [story-04-health-drift-validation-console](./story-04-health-drift-validation-console.md) | [evidence-story-04](./evidence-story-04.md) |
| WLA-5-05 | Build traceability timeline | done | [story-05-traceability-timeline](./story-05-traceability-timeline.md) | [evidence-story-05](./evidence-story-05.md) |
| WLA-5-06 | Build structured PMO editor | backlog | [story-06-structured-pmo-editor](./story-06-structured-pmo-editor.md) | - |
| WLA-5-07 | Build safe mutation preview and diff workflow | backlog | [story-07-mutation-preview-diff-workflow](./story-07-mutation-preview-diff-workflow.md) | - |
| WLA-5-08 | Integrate commit and work-log evidence views | backlog | [story-08-commit-worklog-evidence-views](./story-08-commit-worklog-evidence-views.md) | - |
| WLA-5-09 | Harden permissions and local runtime model | backlog | [story-09-permissions-local-runtime-model](./story-09-permissions-local-runtime-model.md) | - |
| WLA-5-10 | Ship documentation tests and adoption path | backlog | [story-10-docs-tests-adoption-path](./story-10-docs-tests-adoption-path.md) | - |

## Execution sequence

1. WLA-5-01 freezes the product contract, UX modes, API surface, and design
   standard before implementation starts.
2. WLA-5-02 extracts the shared core so all later UI/API work uses the same
   parser, validator, trace, and mutation planner as `dw`.
3. WLA-5-03 through WLA-5-05 ship read-only value first: explorer, health, and
   trace.
4. WLA-5-06 and WLA-5-07 add mutation through structured editor forms,
   previews, diffs, guarded apply, and revalidation.
5. WLA-5-08 adds commit/work-log evidence views after the base trace model is
   reliable.
6. WLA-5-09 hardens local runtime boundaries before this can be recommended to
   consumer projects.
7. WLA-5-10 closes the adoption loop with docs, screenshots, test coverage, and
   the final dogfood audit.

## Where we are

WLA-5-05 is done with evidence, completing the read-only tier
(explorer, health, trace). The timeline normalizes the intent-to-proof
chain — five hops with explicit absent states, commits scoped to the
story's PMO files carrying the Phase 6 trailers, work-log entries under
the unified PMO_WORK_LOG_DIR resolution — and never claims a story is
shipped unless status and evidence agree. Five phase exit criteria are
checked. Next per the execution sequence: WLA-5-06 (structured editor)
and WLA-5-07 (mutation preview/diff) open the write tier on the core's
preview → apply-with-fingerprint → revalidate primitives, guarded by
the health console's mutation_safe handoff.

## Active risks

| Risk | Likelihood | Mitigation | Stop signal |
|---|---|---|---|
| UI duplicates PMO parsing logic | high | Extract shared `dw_pmo` core before UI routes | Browser or server code parses roadmap files independently of the shared core |
| Workbench becomes a second source of truth | high | No database; every state response derives from Markdown | A persisted cache is required to recover roadmap state |
| Mutation flow corrupts prose | medium | Use structured mutation plans and only rewrite owned rows/metadata | A no-op preview produces a non-empty diff |
| Permission boundary is too broad | medium | Require repo allowlist and PMO path allowlist | An API can read/write arbitrary paths outside the allowlist |
| UI ships before validation is trustworthy | medium | Read-only explorer depends on validator and health surfaces | A story can be edited while `dw check` reports unresolved structural errors |
| Local runtime becomes operationally heavy | medium | Prefer stdlib/simple local server and static assets first | A consumer must install a database or background service manager to use it |

## Decisions made (this phase)

- 2026-07-01 - Plan Phase 5 as a local workbench layer over the shipped PMO
  CLI/core - preserves source-of-truth and agent-safety constraints - user
  requirement.
- 2026-07-01 - Keep WLA-5-01 and WLA-5-02 ahead of UI implementation - avoids
  UI-first shortcuts and duplicate parser state - PMO quality gate.
- 2026-07-01 - Treat mutation as preview/diff/apply/revalidate, not direct
  form writes - keeps agent and human edits auditable - Phase 4 CLI behavior.

## Decisions deferred

- Exact UI technology - decide in WLA-5-01; default is a local static web shell
  served by `dw-workbench` unless a stronger repo-native option is justified.
- Whether `dw-workbench` is installed into target `.githooks/` in the first
  release - decide after WLA-5-09; default is source-repo only until the
  permission model is proven.
- Hosted or multi-repo service mode - revisit only after local runtime dogfood;
  default is no hosted mode.
