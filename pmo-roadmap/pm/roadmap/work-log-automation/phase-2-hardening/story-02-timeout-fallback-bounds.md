# WLA-2-02 - Add timeout, fallback, and output bounds

- **Project:** work-log-automation
- **Phase:** 2
- **Status:** backlog
- **Depends on:** WLA-2-01
- **Unblocks:** WLA-2-03
- **Owner:** unassigned

## Problem

An external summarizer can hang, fail, or produce too much text. Work-log
summarization must remain reliable even when the summarizer does not, and
ordinary commits must not depend on the summarizer being available.

## Scope

- **In:** Timeout command strategy, deterministic fallback preservation, output
  length bounds, and user-facing diagnostics.
- **Out:** Redaction and secret scanning.

## Acceptance criteria

- [ ] Timeout is configurable.
- [ ] Failure leaves the deterministic entry intact and reports a clear warning.
- [ ] No failure mode rewrites or deletes the original deterministic entry.
- [ ] Summary output is capped with a truncation marker.
- [ ] Tests cover slow, failing, and oversized summarizer output.

## Test plan

- **Unit:** Fake commands that sleep, exit nonzero, and emit oversized output.
- **Integration / Cypress:** Temporary repo commits followed by deferred
  summarizer runs for timeout, failure, and oversized-output cases.
- **Manual / device:** Confirm diagnostics are clear enough for a developer
  committing from a terminal.

## Notes / open questions

Because summarization is deferred, fail-closed semantics are unnecessary for
the first implementation. A failed summarizer should leave deterministic logs
untouched and make the failure visible to the operator.
