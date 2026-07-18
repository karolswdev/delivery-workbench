# Phase 24 Final Summary

**Status:** complete.
**Date:** 2026-07-18.

## Delivered value

Delivery Workbench can coordinate a bounded multi-agent delivery run from a
rich, visually authored score. The editor makes the whole run contract
explicit: research, synthesis, implementation, review, repair, check, rail,
collection, approval, and terminal nodes; dependencies and parallel fan-out;
context and artifact lineage; typed output conventions and citations; exact
checks and failure routes; finite retries, budgets, concurrency, and timeouts;
and named human checkpoints. Design, Validate, canonical JSON, simulation, and
Run are views over one stdlib-only compiler and runtime—not separate browser
policy.

A tracked score is configuration, not ambient authority. An operator first
reviews a pure plan that binds the compiled score hash to repository HEAD,
roadmap status/story facts, capabilities, workspaces, budgets, expiry, and
permanent exclusions. A separate single-use approval creates an immutable,
revocable grant and the first event in a hash-chained ledger. Only then may the
deterministic conductor dispatch score-declared work. Pause, resume, revoke,
cancel, checkpoint decisions, and each tick are fresh-ledger-head acts; stale
tokens refuse before dispatch or mutation.

Agent harnesses receive structured, hash-bound work packets rather than shell
commands. Parallel research runs read-only, synthesis consumes only validated
artifacts, and every writer receives a distinct worktree pinned to the granted
HEAD. Outputs must satisfy their declared format, schema, sections, paths,
sizes, citations, and diff scope before fan-in. Exact checks run without a
shell in contained check or writer worktrees. Required failures can advance
only through the score's bounded retry, repair, approval, pause, or abort
route. Crash recovery polls persisted claims before retry, preventing duplicate
agent or check starts.

The same exact run is available through CLI, MCP, HTTP, and the Workbench Run
tab. The visual Run surface replays the authoritative graph with node attempts,
agent/check sessions, artifact lineage, budgets, routes, checkpoints, bounded
streams, controls, and the ledger timeline. It refreshes only on request,
contains no generic terminal or hidden scheduler loop, and cannot elevate
capabilities, alter retry policy, certify a contract, commit, push, release, or
deploy. Every green orchestration stops at `awaiting-certification` and hands
the evidence and isolated diff back to a person.

## Outcome against exit criteria

1. The versioned `delivery-workbench-orchestration@1` score expresses the
   complete bounded coordination contract. Its pure compiler normalizes the
   document, separates semantic and layout hashes, emits JSON-pointer
   diagnostics, simulates scheduling, and rejects cycles, dangling lineage,
   shell strings, escaped paths, unbounded retry, and unsupported capability.
2. The Workbench's graph canvas, typed palette, full inspector, live errors,
   capability/output lineage, simulation, JSON view, and guarded
   preview→diff→apply save form a lossless editor. Opening, moving, validating,
   saving, or deleting a score starts no work and grants no authority.
3. Exact run plans, expiring/revocable grants, cross-process locks, immutable
   score snapshots, append-only hash-chained events, exclusive attempt claims,
   counters, and disposable replay projections make consent and runtime state
   auditable and recovery-safe.
4. Provider-neutral fixture and Codex drivers prove the structured packet,
   capability, workspace, cancellation, artifact, and receipt seams. Research
   fans out concurrently; synthesis accepts only validated fan-in; writer
   worktrees are isolated and never implicitly integrated.
5. One idempotent conductor tick reconciles existing work, selects a stable
   eligible set, enforces concurrency/resources/budgets, dispatches bounded
   work, validates results, and records the exact next route. Supervision is
   bounded repetition of that same primitive, not a second scheduler.
6. CLI JSON, MCP `structuredContent`, HTTP `data`, and Workbench projections
   are equivalent. Applying adapters accept only identifiers, bounded
   reasons/decisions, and fresh tokens—not score documents, prompts, provider
   configuration, credentials, or check argv.
7. The fresh-wheel exit exam exercised the whole graph: two parallel research
   agents, typed and cited artifacts, synthesis, isolated implementation, a
   planted failing check, exactly one configured repair visit, passing
   recheck, crash recovery with zero duplicate starts, cancellation and budget
   red paths, terminal handoff, operator certification, gated commit, and
   verified history.
8. Manual desktop/mobile inspection confirmed that active, repair, and
   terminal graphs remain legible and expose the current state, authority,
   budgets, ledger head, and explicit refresh. The visual editor and Run view
   do not conceal a poller, shell, retry override, or certification shortcut.

## Measured proof

- 297 core tests passed on the local Python interpreter and the declared
  Python 3.9.6 floor.
- Python 3.9 built the v1.14.0 sdist and wheel. A fresh installed consumer
  passed guided-status, deliberate-step, and packaged orchestration exams.
- The orchestration exam recorded five artifacts, two checks, two concurrent
  research starts, one repair visit, zero duplicate restarts, six compiler red
  cases, and five runtime red cases, ending at
  `awaiting-certification`. The fixture operator alone certified and committed;
  fixture `dw check` and `dw verify --all` both passed.
- The authenticated live Codex adapter produced and validated its declared
  Markdown/citation artifact in an ephemeral read-only workspace, recorded a
  bounded receipt, and left the operator tree clean. Deterministic fixture
  output remains the CI oracle.
- Exact orchestration lifecycle and run-view parity passed across CLI, MCP,
  and HTTP, including stale-token, replay, injection, capability, expiry,
  budget, cancellation, and checkpoint refusal paths.
- Firefox rendered 32 viewport states: 14 product views plus attention and
  ambiguity at desktop and mobile sizes. Active, fail/repair, and terminal Run
  captures were manually inspected. Explorer and demo-asset smokes passed.
- Canon/docs/snippet, adoption, roadmap, gate, work-log, contribution,
  upgrade, range, MCP, step, orchestration, agent/rider/plugin, generated-copy,
  package, static, credential, and history suites passed.
- Telegram passed 147 interface and 10 architecture-fitness tests on the
  provisioned Python 3.9/Pillow host. Pinned HoldSpeak v0.4.0 + NumPy passed
  23/23 pack tests.
- The pre-close history sweep verified 136 gated commits and skipped 17
  documented pre-epoch commits. Full commands and receipts are in
  [WLA-24-08 evidence](./evidence-story-08.md).
- Homebrew correctly abstained locally because the operator formula is already
  installed; clean-machine macOS CI remains the proving environment and no
  uninstall was attempted.

## Product and authority decisions

- Say Delivery Workbench **can coordinate**. Coordination is a configured
  capability centered on the visual editor, not a promise to autonomously run
  every repository.
- The canonical score is portable, reviewable policy. Provider executables,
  credentials, and profile-to-harness resolution remain operator-local.
- Layout changes round-trip without changing runtime semantics; every complete
  document still has a stale-safe hash so no visual edit is silently lost.
- The score never grants itself. A run needs a separate, exact, expiring,
  revocable authorization over repository and roadmap facts.
- Claims precede dispatch and the ledger is authoritative. Projection caches
  are disposable; recovery polls persisted work before any retry.
- Research is read-only, writers are isolated, artifacts are typed and scoped,
  and integration remains a reviewed operator act.
- Check commands are tokenized argv from the authorized score, run without a
  shell under cwd, time, output, environment, and filesystem-change bounds.
- Retry and repair policy is immutable for a run. Operators may control or
  decide named checkpoints, but cannot invent a new route or elevate authority
  in place.
- Remote clients can coordinate the delivered local runner through the exact
  adapters. Moving repository authority into a hosted control plane would be
  a distinct security/operations decision, not unfinished local orchestration.
- `awaiting-certification` means orchestration is finished, not that the work
  is safe to commit. Evidence judgment, contract attestation, and commit remain
  manual.

## Deliberate boundaries and later options

- Arbitrary cyclic workflow graphs are excluded; finite DAG scheduling plus
  bounded retry/repair routes supplies recoverability without hidden loops.
- Repository-defined drivers, secrets in scores, provider-specific executable
  fields, cross-repository write transactions, automatic merge/conflict
  resolution, automatic evidence judgment, certification, commit, push,
  release, and deployment are outside this authority model.
- A hosted or cross-machine control service can be evaluated on top of the
  delivered adapters if an owner explicitly wants a new trust root, identity
  model, persistence/availability contract, and operations surface. It is not
  required to use the complete local orchestration framework delivered here.

## Release readiness

The Unreleased changelog now describes Phases 22–24 as a coherent
observe→authorize-one-step→coordinate-a-bounded-run advance. Distribution,
upgrade, interop, browser, agent, optional-host, docs, and history proof are
green. Version v1.14.0 remains the single source of truth; this phase does not
authorize a version bump, tag, GitHub release, PyPI upload, or Homebrew formula
or tap change.

## Audit trail

| Story | Evidence |
|---|---|
| WLA-24-01 | [score, editor, authority, runtime, and threat contract](./evidence-story-01.md) |
| WLA-24-02 | [pure compiler, validation, and simulation](./evidence-story-02.md) |
| WLA-24-03 | [rich visual orchestration editor](./evidence-story-03.md) |
| WLA-24-04 | [grants, ledger, replay, and revocation](./evidence-story-04.md) |
| WLA-24-05 | [drivers, typed artifacts, and isolated workspaces](./evidence-story-05.md) |
| WLA-24-06 | [conductor, checks, repair routes, and recovery](./evidence-story-06.md) |
| WLA-24-07 | [CLI/MCP/HTTP interoperability and Run view](./evidence-story-07.md) |
| WLA-24-08 | [packaged multi-agent orchestration exit exam](./evidence-story-08.md) |
