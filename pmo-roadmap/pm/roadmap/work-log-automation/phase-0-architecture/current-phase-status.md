# Phase 0 - Architecture

**Last updated:** 2026-07-01.

## Goal

Define a careful implementation roadmap for consent-gated daily work logs so
the feature can be added to `pmo-roadmap` without weakening the existing hook
contract, introducing false audit entries, or making every commit depend on a
fragile external LLM call.

## Scope

- **In:** Contract language, consent semantics, capture/finalize lifecycle,
  log-entry schema, summarizer command boundary, failure policy, rollout plan,
  and implementation stories.
- **Out:** Building the feature, selecting a final prompt for every future
  model, syncing logs to remote storage, analytics dashboards, or replacing
  roadmap evidence files.

## Exit criteria (evidence required)

- [x] A project roadmap exists under `pmo-roadmap/pm/roadmap/work-log-automation/`.
- [x] Each implementation slice has a story with acceptance criteria and test
  plan.
- [x] The roadmap names the architectural decisions that must hold before code
  changes begin.
- [x] The log-entry schema, consent syntax, git edge-case policy, and log
  identity policy are pinned before Phase 1 implementation.
- [x] The risks table has concrete stop signals, not vague concerns.
- [x] The phase can hand off directly into Phase 1 MVP implementation.

## Story status

| ID | Story | Status | Story file | Evidence |
|---|---|---|---|---|
| WLA-0-01 | Define the consent and log-entry contract | done | [story-01-contract-and-schema](./story-01-contract-and-schema.md) | [evidence-story-01](./evidence-story-01.md) |
| WLA-0-02 | Design the capture/finalize hook lifecycle | done | [story-02-hook-lifecycle](./story-02-hook-lifecycle.md) | [evidence-story-02](./evidence-story-02.md) |
| WLA-0-03 | Specify the summarizer adapter and failure policy | done | [story-03-summarizer-adapter](./story-03-summarizer-adapter.md) | [evidence-story-03](./evidence-story-03.md) |
| WLA-0-04 | Plan installer, update, and project configuration rollout | done | [story-04-rollout-and-config](./story-04-rollout-and-config.md) | [evidence-story-04](./evidence-story-04.md) |
| WLA-0-05 | Prove the roadmap against the framework's own constraints | done | [story-05-roadmap-validation](./story-05-roadmap-validation.md) | [evidence-story-05](./evidence-story-05.md) |
| WLA-0-06 | Define git edge cases and log identity policy | done | [story-06-edge-cases-and-identity](./story-06-edge-cases-and-identity.md) | [evidence-story-06](./evidence-story-06.md) |

## Where we are

Phase 0 is complete. The roadmap pins the consent syntax, two-step
capture/finalize lifecycle, deterministic log-entry schema, deferred
summarizer boundary, install/update policy, git edge-case policy, and
collision-resistant log identity. Phase 1 implementation proceeded without
moving model calls into the commit path.

## Active risks

| Risk | Likelihood | Mitigation | Stop signal |
|---|---|---|---|
| The log records work that never committed | medium | Capture in `pre-commit`, append only in `post-commit` after a commit hash exists | Any design appends directly from `pre-commit` without a pending/finalize step |
| The hook becomes slow or network-dependent | high | Keep MVP deterministic; move LLM work to a deferred adapter with timeout and fallback | A normal commit blocks because a model or network call is unavailable |
| Sensitive diffs leak into a broad daily log | medium | Require explicit consent, exclusions, max diff bytes, redaction hooks, and local-only default path | A diff containing secrets or credentials is included in a summarized payload |
| The contract becomes performative | medium | Require reasons, not only a checkbox; persist consent text with the pending capture | Consent can be inferred from box count alone |
| Framework updates clobber project-specific logging choices | low | Put behavior behind config variables and preserve local config in `update.sh` | `update.sh` overwrites `.githooks/pre-commit.config` or local policy files |
| Rebase, amend, or cherry-pick creates misleading log entries | medium | Define an explicit MVP policy and detect common Git actions where practical | A history rewrite appends duplicate entries without a documented policy |
| Global log filenames collide across projects | medium | Default to a collision-resistant log identity, with project override | Two repos append to the same daily file without explicit shared identity |
| Existing project `post-commit` hooks are displaced | medium | Installer/update must detect and preserve or compose existing local hooks | Installing WLA silently overwrites an existing project `post-commit` hook |

## Decisions made (this phase)

- 2026-04-25 - Use a two-step lifecycle: `pre-commit` captures, `post-commit`
  finalizes - prevents false log entries when a commit aborts - architecture
  review.
- 2026-04-25 - Make logging opt-in by explicit contract consent for the first
  release - protects privacy and keeps the PMO contract honest - architecture
  review.
- 2026-04-25 - Treat `codex` as a replaceable CLI adapter, not a hard framework
  dependency - preserves generic framework portability - architecture review.
- 2026-04-25 - Pin consent as a key-value line, not an extra checkbox:
  `**Work-log consent:** yes|no` - avoids entangling logging with
  `EXPECTED_BOXES` - Claude review incorporation.
- 2026-04-25 - Keep the MVP deterministic and keep LLM summarization out of the
  commit path - preserves fast, offline-safe commits - Claude review
  incorporation.
- 2026-04-25 - Default log identity should be collision-resistant, using a
  project slug plus a stable repo-path hash unless explicitly overridden -
  prevents silent cross-project log mixing - Claude review incorporation.

## Decisions deferred

- Whether logging should eventually become default-on - revisit after sustained
  consumer use - default remains opt-in.
- Whether to store raw captured diffs after finalization - revisit after privacy
  review - default is delete pending payload after successful append.
- Whether deferred LLM summaries should edit entries in place or create a
  companion digest - resolved for this roadmap as companion digest; revisit
  only for a future major workflow.
- Whether to retain logs forever - revisit when `~/.work/log` exceeds 1GB or
  one year of entries - default is local retention forever.
