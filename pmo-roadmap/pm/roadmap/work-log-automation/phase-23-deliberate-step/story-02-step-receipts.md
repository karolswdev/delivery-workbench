# WLA-23-02 - Step receipts — stable result and event correlation

- **Project:** work-log-automation
- **Phase:** 23
- **Status:** backlog
- **Depends on:** WLA-23-01
- **Unblocks:** WLA-23-03
- **Owner:** unassigned

## Problem

Executing one command is useful to a person, but agents and later adapters
need an honest bounded receipt: what preview was authorized, whether a child
started, its outcome, and what the next observation became.

## Scope

- **In:** stamped result schema; bounded stdout/stderr; before/after tokens and
  action ids; one content-safe rail event; CLI JSON apply mode; failure and
  interruption shapes.
- **Out:** transport adapters and UI; storing command output in roadmap
  evidence automatically; retry or loop behavior.

## Acceptance criteria

- [ ] Success, refusal, child failure, and interruption have pinned result
  shapes and truthful exit contracts.
- [ ] Output is bounded and secrets/content do not enter rail events.
- [ ] Exactly one event follows a started child; preview/refusal emits none.
- [ ] Repeated application of an old token refuses rather than replaying.

## Test plan

- **Unit:** receipt schema, truncation, event allowlist, replay refusal.
- **Integration:** CLI JSON success and failing-child receipts.
- **Manual / device:** inspect event and receipt correlation.

## Notes / open questions

Record unresolved decisions here before implementation starts.
