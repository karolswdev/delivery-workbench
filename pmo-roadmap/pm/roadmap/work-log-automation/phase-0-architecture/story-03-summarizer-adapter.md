# WLA-0-03 - Specify the summarizer adapter and failure policy

- **Project:** work-log-automation
- **Phase:** 0
- **Status:** backlog
- **Depends on:** WLA-0-01, WLA-0-02
- **Unblocks:** WLA-0-04
- **Owner:** unassigned

## Problem

Calling an LLM CLI from the work-log flow is useful but risky: it can be slow,
unavailable, too verbose, or accidentally include sensitive payloads. The
framework needs a narrow deferred adapter contract and a deliberate failure
policy so `codex` is only the first implementation, not a hard dependency or a
commit-path requirement.

## Scope

- **In:** Config variables, deferred command invocation shape, stdin payload
  contract, timeout behavior, fallback summary, redaction hook seam, max diff
  bytes, and output validation.
- **Out:** Vendor-specific model selection, remote API configuration, or
  sophisticated semantic diff analysis.

## Acceptance criteria

- [ ] The deferred summarizer can be configured with a command variable such as
  `PMO_WORK_LOG_SUMMARIZER`.
- [ ] The framework defines a stdin payload format that includes metadata,
  contract consent, staged file list, diff stat, and bounded diff.
- [ ] A no-LLM fallback writes a deterministic summary from git metadata and
  consent reasons.
- [ ] Timeout behavior is explicit and configurable.
- [ ] Summarizer failure leaves the deterministic log entry intact.
- [ ] Summary output is bounded and appended as markdown, not raw model chatter.

## Test plan

- **Unit:** Fake summarizer scripts for success, timeout, empty output, and
  nonzero exit.
- **Integration / Cypress:** Temporary repo commits followed by a deferred fake
  summarizer invocation configured through project config.
- **Manual / device:** Run one local deferred summarization with `codex`
  configured and inspect the resulting entry or companion digest for usefulness
  and restraint.

## Notes / open questions

The first prompt should ask for a technical work-summary, not a performance
review. The log should emphasize delivered value, files changed, tests/evidence,
and follow-ups. It should not fabricate impact that is not visible in the diff
or contract reasons. Keep this out of synchronous commit hooks unless a future
phase explicitly reverses that decision.
