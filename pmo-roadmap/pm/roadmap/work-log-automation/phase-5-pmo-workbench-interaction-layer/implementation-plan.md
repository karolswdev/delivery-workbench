# PMO Workbench Interaction Layer - Implementation Plan

**Date:** 2026-07-01.
**Phase:** WLA-5.
**Status:** planning.

## Objective

Build a local PMO Workbench that lets humans and AI agents inspect, validate,
trace, preview, and safely mutate Delivery Workbench roadmap files. The UI/API
is a presentation and command surface over Markdown. It is not a tracker,
database, or replacement for the PMO contract.

## Non-negotiable constraints

- `pm/roadmap/**` Markdown remains authoritative.
- JSON context, UI state, generated indexes, and caches are disposable.
- All writes use shared PMO mutation plans and remain allowlisted to PMO-owned
  paths.
- `done` status requires paired evidence.
- Every mutation has preview, diff, apply, and post-apply validation.
- The workbench never auto-commits.
- The workbench must remain useful to an AI agent that has no chat history.

## Target package layout

```text
pmo-roadmap/
  lib/
    dw_pmo/
      __init__.py
      model.py          # Project, Phase, Story, Evidence, Issue, Trace types
      paths.py          # root discovery, allowlist, safe path utilities
      parse.py          # deterministic markdown/path classification
      validate.py       # structural and drift validation
      trace.py          # git/work-log trace collection
      mutations.py      # preview/apply plans for PMO writes
      render.py         # narrowly owned markdown row/metadata rendering
      api.py            # stable JSON envelope helpers
  bin/
    dw                 # CLI adapter over dw_pmo
    dw-workbench       # localhost workbench server
  workbench/
    index.html
    assets/
    src/
      app.js
      api.js
      state.js
      views/
        overview.js
        phase.js
        story.js
        health.js
        trace.js
        editor.js
        preview.js
```

The exact frontend implementation can change in WLA-5-01, but the layering
must not: core model first, adapters second.

## API contract sketch

All responses use a stable envelope:

```json
{
  "kind": "delivery-workbench-workbench-response",
  "schema_version": 1,
  "ok": true,
  "data": {},
  "issues": [],
  "warnings": []
}
```

Read endpoints:

| Endpoint | Purpose |
|---|---|
| `GET /api/context?trace=1` | Full roadmap context snapshot |
| `GET /api/projects` | Project summaries and health |
| `GET /api/projects/{project}` | One project with phase summaries |
| `GET /api/projects/{project}/phases/{phase}` | Phase status, stories, summary |
| `GET /api/projects/{project}/stories/{story}` | Story, evidence, trace, health |
| `GET /api/health` | Validation issues and drift warnings |
| `GET /api/trace/{story}` | README -> phase -> story -> evidence -> commits/work logs |

Mutation endpoints:

| Endpoint | Purpose |
|---|---|
| `POST /api/mutations/preview` | Return planned file changes and validation result |
| `POST /api/mutations/apply` | Apply a previously previewed valid mutation |
| `POST /api/validate` | Re-run validation after external edits |

Mutation request kinds:

- `create_phase`
- `create_story`
- `update_story_status`
- `attach_evidence`
- `close_phase`

The `apply` request must include a preview token or deterministic mutation
fingerprint so stale previews cannot be applied after the working tree changes.

## UI modes

1. **Overview:** project cards/table, active phases, next actionable stories,
   validation counts, drift warnings, hook snapshot, and supplemental canon.
2. **Phase Board:** phase rows, story status, evidence presence, final-summary
   state, and "what changed since last look" cues.
3. **Story/Evidence Pair:** source-faithful markdown preview beside normalized
   metadata, acceptance criteria, evidence, and validation.
4. **Health Console:** stale README pointers, multiple open phases, broken
   links, status mismatches, missing evidence, orphan evidence, and older hook
   snapshots.
5. **Trace Timeline:** README -> phase status -> story -> evidence -> final
   summary -> commits -> work-log entries.
6. **Structured Editor:** create phase/story, update status, attach evidence,
   close phase, with domain fields rather than raw arbitrary filesystem edits.
7. **Preview/Diff:** file-by-file diff, issue list, post-apply validation, and
   clear refusal states.

## Mutation lifecycle

```text
operator intent
  -> structured command
  -> core mutation plan
  -> validate before write
  -> render exact file changes
  -> preview and diff
  -> apply if still current
  -> rollback on write failure
  -> reparse and revalidate
  -> show evidence/check result
```

Preview output must name every file that would change. Apply output must name
every file that changed and every validation issue that remains.

## Test matrix

| Layer | Required coverage |
|---|---|
| Core extraction | Golden parser fixtures, validation fixtures, mutation idempotence, trace fallbacks |
| CLI compatibility | Existing `roadmap-cli.sh` passes without contract changes |
| API | Read endpoints, preview/apply lifecycle, stale preview refusal, error envelopes |
| Permissions | Repo allowlist, PMO path allowlist, path traversal refusal, no auto-commit |
| UI | Explorer, health, trace, editor, preview, empty states, refusal states |
| Dogfood | Phase 5 roadmap updated through PMO process with evidence and final audit |

## Definition of done

- The local workbench can be started from a documented command.
- The first screen is the useful PMO overview, not a marketing page.
- The UI can answer: what is active, what is done, what is blocked, what lacks
  evidence, what drift exists, and what the next safe move is.
- Mutations are impossible without preview and validation.
- Tests prove the workbench cannot write outside PMO-owned paths.
- Phase 5 closes with evidence files and `final-summary.md`.
