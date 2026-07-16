# Phase 23 Final Summary

**Status:** complete.
**Date:** 2026-07-16.

## Delivered value

Delivery Workbench now carries a recommendation across the read-to-act
boundary without turning agent convenience into arbitrary execution. Phase
22's pure `delivery-workbench-status@1` briefing remains the source of the
next action. Phase 23 adds a separate `delivery-workbench-step@1` lease over
that complete observation and a bounded `delivery-workbench-step-result@1`
receipt. Apply accepts only a project plus exact token, re-reads current state,
matches the action id and whole argv shape against a second closed table,
claims the lease atomically, starts at most one child, reports what happened,
and stops.

The same core is available as `dw step`, MCP `dw_step` / `dw_step_apply`,
`GET /api/step` / `POST /api/step/apply`, and the Workbench's explicit
review-then-confirm panel. Generated Claude, Codex, pi, and plugin riders teach
the same discipline: obtain a fresh lease, use its exact apply form, inspect
one receipt, and stop. Project choice, manual repair, contract certification,
and commit remain outside the capability on every surface.

## Outcome against exit criteria

1. The CLI previews a deterministic token over the complete current briefing
   and applies only an exact fresh token. A closed action/argv table, immediate
   re-read, and one-child return prohibit arbitrary commands and hidden loops.
2. Every started action returns a bounded, versioned receipt and appends one
   content-safe `step_execution` event. Atomic claims prevent replay even when
   the action itself is read-only; failures and interruptions never masquerade
   as success.
3. MCP and HTTP are thin adapters over the same preview/apply functions. Their
   schemas accept only `project` and `expect`, their documents are byte-equal
   to CLI JSON, and certification/commit are never applicable.
4. The Workbench separates recommendation, review, and confirmation; exposes
   the token, authorized argv, and CLI fallback; refreshes after exactly one
   result; and offers no apply control for manual or prohibited states. All
   generated riders carry the same operating boundary.
5. A wheel-installed consumer used seven separately authorized CLI/MCP/HTTP
   steps to deliver a real story. Same-id stale state refused before spawn with
   zero events, and bootstrap/story certification and commit stayed manual.

## Proof

- 230 core tests passed on Python 3.14.6 and the declared Python 3.9.6 floor;
  all CLI, MCP, workbench, and core compilation checks passed.
- Python 3.9 built the v1.14.0 sdist and wheel. The installed wheel completed
  both the guided-status loop and deliberate-step loop through real trailered,
  contract-archived, history-verified fixture commits.
- CLI, MCP, and HTTP preview/result parity passed, including replay, injection,
  same-action staleness, certification, and commit red paths.
- Firefox produced 20 viewport renders: eight views plus attention and
  ambiguous-project states at desktop and mobile sizes. Workbench, demo asset,
  and social-preview smokes passed.
- Every shipped shell parsed and passed ShellCheck. Agent, rider, plugin,
  adoption, gate, roadmap, contribution, work-log, docs/snippets, upgrade,
  range, generated-source, and credential-clean suites passed.
- Telegram passed 147 interface and 10 architecture-fitness tests on Python
  3.9 + Pillow. Pinned HoldSpeak v0.4.0 + NumPy passed 23/23 pack tests.
- The pre-close history sweep verified 128 gated commits and skipped 17
  documented pre-epoch commits. Full commands and receipts are in
  [WLA-23-05 evidence](./evidence-story-05.md).
- Homebrew correctly abstained locally because the operator formula is already
  installed; no uninstall was attempted. Its clean-machine macOS CI leg stays
  wired and is the honest proving environment.

## Decisions that now constrain the product

- A step is a short-lived authorization over one complete observation, not an
  action id, shell string, durable queue item, or permission to continue.
- The status core still decides what is next; step adds freshness, a closed
  execution table, and receipts without becoming another planner or gate.
- Caller-supplied argv is forbidden on every adapter. An implementation change
  that alters an allowed argv shape must update the closed table and tests.
- Claims happen before spawn and are token-generating state, so even a
  read-only successful action cannot replay the original lease.
- A rail event exists only for a child that started and contains hashes,
  outcome, exit information, and next action—not argv, stdout, or stderr.
- Certification and commit remain deliberate operator acts. A recommendation
  can explain them but no step adapter or browser control can perform them.

## Limitations and deliberately deferred work

- The lease is local repository state, not a hosted or cross-machine
  capability. Remote orchestration, CI/forge receipts, and release-channel
  health still need separate authority and protocols.
- `dw step` is intentionally one child at a time. Automatic loops, unattended
  retries, batched transitions, and token waivers remain out until measured
  operator friction justifies a new consent design.
- Manual choices remain manual: ambiguous projects, roadmap repairs, evidence
  commands, contract attestations, and commits cannot be inferred safely.
- Optional integration hosts still require their test amenities. Pillow,
  HoldSpeak, and NumPy are not product runtime dependencies; CI provisions
  them explicitly. Homebrew smoke needs a clean machine by design.

## Release readiness

The Unreleased changelog now describes Phases 22 and 23 as one orientation-to-
deliberate-action advance. Distribution, upgrade, interoperability, browser,
agent, optional-host, docs, and history proof are green. Version v1.14.0
remains the single source of truth; this phase does not itself authorize a
version bump, tag, GitHub release, PyPI upload, or Homebrew formula/tap change.

## Audit trail

| Story | Evidence |
|---|---|
| WLA-23-01 | [step core and CLI](./evidence-story-01.md) |
| WLA-23-02 | [receipts, claims, and events](./evidence-story-02.md) |
| WLA-23-03 | [MCP/HTTP transport parity](./evidence-story-03.md) |
| WLA-23-04 | [Workbench and generated riders](./evidence-story-04.md) |
| WLA-23-05 | [packaged deliberate-step exit exam](./evidence-story-05.md) |
