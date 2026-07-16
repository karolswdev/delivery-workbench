# WLA-23-02 - Step receipts — stable result and event correlation

- **Project:** work-log-automation
- **Phase:** 23
- **Status:** done
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

- [x] Success, refusal, child failure, and interruption have pinned result
  shapes and truthful exit contracts.
- [x] Output is bounded and secrets/content do not enter rail events.
- [x] Exactly one event follows a started child; preview/refusal emits none.
- [x] Repeated application of an old token refuses rather than replaying.

## Test plan

- **Unit:** receipt schema, truncation, event allowlist, replay refusal.
- **Integration:** CLI JSON success and failing-child receipts.
- **Manual / device:** inspect event and receipt correlation.

## Notes / open questions

`delivery-workbench-step-result@1` uses one fixed shape for every operational
outcome. Before/after observations carry token plus action id; output streams
are separate and byte-capped; expected refusals are data in JSON mode. A
claim file under `.git/pmo-step-claims/` is exclusively created before spawn,
and the claim-set generation feeds the next token so a read-only action cannot
reuse its lease. The ledger, not best-effort telemetry, owns replay safety.

Every started child appends one `step_execution` event. Its closed detail
allowlist contains action/outcome/exit/before/after/next-action only; commands,
output, reasons, and prompts cannot enter. Underlying domain events remain
independent. MCP/HTTP transport mapping stays in WLA-23-03.
