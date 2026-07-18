# WLA-24-06 - Schedule nodes, checks, failure routes, and recovery

- **Project:** work-log-automation
- **Phase:** 24
- **Status:** backlog
- **Depends on:** WLA-24-04, WLA-24-05
- **Unblocks:** WLA-24-07, WLA-24-08
- **Owner:** unassigned

## Problem

Agents and scores are components, not orchestration. One deterministic
conductor must reconcile ledger, repository, sessions, drivers, artifacts,
checks, grants, and budgets into the next eligible work while making every
failure route, retry, pause, approval, cancellation, and recovery observable.

## Scope

- **In:** pure eligibility/scheduling decision; one idempotent `run tick`;
  repeated supervised conductor with backoff/stop; dependency/fan-out/fan-in;
  stable tie-break; concurrency/resource locks; exact command/built-in checks
  with cwd/time/output/write bounds; artifact fan-in gates; fresh `dw step`
  for declared rail nodes; retry/repair-route/approval/pause/abort policy and
  visit ceilings; agent/check polling; expiry/budget/revocation; cancellation;
  crash/restart/poll-before-retry; terminal handoff and external-commit
  observation.
- **Out:** visual authoring or transport adapters; unbounded cycles; agent-
  supplied checks/routes; automatic evidence adequacy, certification, commit,
  merge, push, release, deployment.

## Acceptance criteria

- [ ] Replaying the same facts yields the same eligible set/order; a tick
  claims before dispatch, starts no more than granted concurrency, appends
  exact receipts, and returns without an unrecorded decision.
- [ ] Research fan-out waits for validated outputs before synthesis fan-in;
  implementation waits for synthesis; required checks gate downstream nodes;
  missing/malformed/oversized outputs cannot be waved through.
- [ ] Command checks run only exact score argv—never shell or agent output—in
  contained workspaces with timeout/output/write snapshots; built-in
  file/schema/diff/rail checks share the same bounded receipt contract.
- [ ] Every failure follows only its configured bounded retry, repair node,
  approval, pause, or abort route; planted retry/repair exhaustion, failed
  required check, unsupported elevation, expiry and budget exhaustion stop.
- [ ] Restart after each dispatch/completion boundary replays and polls before
  retry, never duplicates a claimed node, and cancellation revokes future
  scheduling before interrupting active drivers/checks.
- [ ] Declared rail nodes consume a fresh exact `dw step` lease; stale action,
  certification, and commit remain non-started. Terminal handoff is
  `awaiting-certification`, not a shipped claim.

## Test plan

- **Unit:** eligibility/order, dependencies, locks/concurrency, budgets,
  attempts/visits, check executor, artifact gates, failure routes, step seam,
  polling/recovery/cancel, terminal projection.
- **Integration:** crash injection at every claim/dispatch/collect/check/event
  boundary plus complete fixture score and all red routes.
- **Manual / device:** supervise one run with a failed check routed to repair,
  pause/resume once, cancel another, and inspect that the ledger explains every
  decision without transcript/content leakage.

## Notes / open questions

The directly callable tick is the test and recovery primitive. A supervised
long-running conductor is repetition around that primitive, not a second
scheduler. Success-graph cycles remain illegal; retries and repair visits are
finite counters owned by policy.
