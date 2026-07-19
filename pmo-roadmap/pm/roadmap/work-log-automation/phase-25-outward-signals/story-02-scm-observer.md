# WLA-25-02 - Observe SCM facts without acting

- **Project:** work-log-automation
- **Phase:** 25
- **Status:** backlog
- **Depends on:** WLA-25-01
- **Unblocks:** WLA-25-04, WLA-25-06, WLA-25-09
- **Owner:** unassigned

## Problem

Once a run's writer worktree diff is integrated and pushed, Delivery
Workbench goes blind: CI verdicts, review threads, and mergeability live
only in the forge. Agent Orchestrator's SCM observer shows the shape that
works — poll with ETag guards, diff semantically, persist only what
changed — but stores those facts inside a daemon that also acts on them.
This story delivers the observation half alone: an authority-free surface
that records `delivery-workbench-signal@1` facts and derives display
status at read time, exactly as contracted in WLA-25-01, so that later
stories can act on facts that already exist and are already auditable.

## Scope

- **In:** an SCM provider port with a GitHub adapter (token from operator
  environment, never stored) and a deterministic fixture provider for
  tests; polling with ETag guards and semantic diffing so unchanged
  responses write nothing; durable signal facts under
  `.git/pmo-signals/<remote>/<branch>/` (append-only `signals.jsonl`,
  hash-chained like the run ledger, plus a disposable projection cache);
  fact kinds: PR identity/state/draft, per-check status/conclusion,
  review-thread counts and resolution state, mergeability; derived
  statuses (`ci-failed`, `ci-pending`, `changes-requested`, `approved`,
  `merge-conflict`, `mergeable`, `merged`, `closed-unmerged`) computed at
  read time by the contracted precedence, never stored; `dw signals
  [--json]` CLI plus `dw_signals` MCP and HTTP read surfaces; a bounded
  observe pass (`dw signals observe`) that performs exactly one poll
  sweep and exits — long-running observation is only repetition, exactly
  like `run supervise` over ticks.
- **Out:** nudging, notification delivery, auto-merge, PR mutations of
  any kind, review-comment bodies or CI log content in durable facts
  (references/URLs only), non-GitHub forges (the port stays neutral;
  further adapters are later work).

## Acceptance criteria

- [ ] The observer is pure read: no code path mutates the repository, the
  forge, any run, or any agent; `starts_work: false` is stamped on every
  observe result and enforced by test.
- [ ] Signal facts are append-only, hash-chained, and deduplicated by
  semantic diff — an unchanged forge response appends nothing; a corrupt
  or forked signal chain fails closed exactly like the run ledger.
- [ ] Derived status follows the contracted precedence table and is
  computed at read time; deleting the projection cache changes no answer.
- [ ] Raw third-party content stays out of durable facts: checks carry
  name/status/conclusion/URL, review threads carry counts/authors/URLs,
  and a test proves no comment body or log text is persisted.
- [ ] CLI, MCP, and HTTP return byte-equivalent signal and status models,
  with the fixture provider proving green, failing, conflicted, and
  closed-unmerged scenarios end to end.
- [ ] ETag/conditional requests are used when the forge offers them, and
  a rate-limited or unauthenticated forge degrades to a recorded
  content-free refusal, never a crash or a stale-silent success.

## Test plan

- **Unit:** semantic diff, precedence derivation, chain verification,
  content-exclusion assertions, provider-port conformance for both
  adapters.
- **Integration:** one observe sweep against the fixture provider through
  CLI/MCP/HTTP parity; corrupt-chain and rate-limit red paths.
- **Manual / device:** run `dw signals observe` against a real pushed
  branch of this repository and confirm the derived status matches the
  forge UI.

## Notes / open questions

The `.git/pmo-signals/` location keeps outward facts out of the operator
tree and out of the repository, mirroring `.git/pmo-orchestration/`.
Whether signal history should ever be exportable into evidence files is
deferred to the exam story's findings.
