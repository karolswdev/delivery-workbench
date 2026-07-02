# Phase 2 - Hardening

**Last updated:** 2026-07-01.

## Goal

Add deferred LLM summarizer support and operational safety controls after the
local MVP lifecycle is proven.

## Scope

- **In:** Deferred summarizer command adapter, prompt/payload contract,
  timeouts, fallback behavior, max diff bytes, redaction seam, output bounds,
  and tests.
- **Out:** Installer basics already delivered in Phase 1, remote log sync, and
  dashboard/reporting features. Synchronous LLM calls on every commit remain
  out of scope unless explicitly re-approved.

## Exit criteria (evidence required)

- [x] A fake deferred summarizer can produce a bounded summary from a captured
  payload or deterministic entry.
- [x] Timeout, nonzero exit, and empty-output paths are tested.
- [x] Redaction or exclusion policy is documented and testable.
- [x] Deterministic fallback remains available when the summarizer is disabled.
- [x] Commit hooks remain fast and do not require network/model availability.

## Story status

| ID | Story | Status | Story file | Evidence |
|---|---|---|---|---|
| WLA-2-01 | Add configurable deferred summarizer command support | done | [story-01-summarizer-command](./story-01-summarizer-command.md) | [evidence-story-01](./evidence-story-01.md) |
| WLA-2-02 | Add timeout, fallback, and output bounds | done | [story-02-timeout-fallback-bounds](./story-02-timeout-fallback-bounds.md) | [evidence-story-02](./evidence-story-02.md) |
| WLA-2-03 | Add redaction and diff-size controls | done | [story-03-redaction-diff-controls](./story-03-redaction-diff-controls.md) | [evidence-story-03](./evidence-story-03.md) |

## Where we are

Phase 2 is complete. Deferred summarization is an explicit helper command with
timeout and output bounds, empty-output fallback, nonzero/timeout diagnostics,
and companion digest output. Exclusion and diff-size controls are documented
and covered by integration tests, while commit hooks remain deterministic and
model-free.

## Active risks

| Risk | Likelihood | Mitigation | Stop signal |
|---|---|---|---|
| Model output is too verbose | medium | Enforce output byte/line limits and deterministic section headings | A summary entry dominates the daily log with raw analysis |
| CLI invocation is not portable | medium | Treat the command as project config and test with fake shell scripts first | Framework assumes a specific `codex` prompt syntax |
| Redaction gives false confidence | medium | Keep consent/exclusions primary and make redaction explicit, limited, and tested | Secret-looking values appear in a test log payload |
| Deferred summarization loses useful context | medium | Decide what bounded payload is retained or rehydrated before deleting raw pending data | Summarizer cannot explain a deterministic entry without reopening Git history |

## Decisions made (this phase)

- 2026-04-25 - Summarization is a deferred adapter behind config, not a core
  hook dependency - Phase 0 architecture and Claude review incorporation.

## Decisions deferred

- Exact default `codex` command - intentionally left project-owned; the
  framework documents the command shape and keeps deterministic fallback as the
  default.
