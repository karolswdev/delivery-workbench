# WLA-2-01 - Add configurable deferred summarizer command support

- **Project:** work-log-automation
- **Phase:** 2
- **Status:** backlog
- **Depends on:** WLA-1-05
- **Unblocks:** WLA-2-02, WLA-2-03
- **Owner:** unassigned

## Problem

The desired long-term log benefits from an LLM summary, but the framework must
not hard-code one model or CLI or make every commit wait for a model. It needs
a deferred command adapter that accepts a stable payload or deterministic entry
and returns bounded markdown.

## Scope

- **In:** `PMO_WORK_LOG_SUMMARIZER` command support for a deferred summarize
  operation, stdin payload contract, fake summarizer tests, and docs.
- **Out:** Timeout handling and redaction controls.

## Acceptance criteria

- [ ] The commit hooks do not synchronously call the LLM summarizer.
- [ ] When configured and invoked, the deferred summarizer receives a stable
  payload or deterministic entry on stdin.
- [ ] Command stdout can become a replacement technical summary or companion
  digest after validation.
- [ ] Empty or invalid output falls back to deterministic summary.
- [ ] Tests use fake summarizer scripts, not a real network/model dependency.

## Test plan

- **Unit:** Fake summarizer scripts for valid, empty, and malformed output.
- **Integration / Cypress:** Temporary repo commit followed by deferred
  summarize invocation with a configured fake command.
- **Manual / device:** Optional local trial with `codex` after fake tests pass.

## Notes / open questions

Keep prompt text outside the core hook if possible, or make it a compact
here-doc that is easy to audit. The first implementation should prefer a
manual command or documented recipe over background daemon behavior.
