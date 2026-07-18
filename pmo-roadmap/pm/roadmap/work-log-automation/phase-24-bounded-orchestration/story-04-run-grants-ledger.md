# WLA-24-04 - Authorize runs with grants and an append-only ledger

- **Project:** work-log-automation
- **Phase:** 24
- **Status:** backlog
- **Depends on:** WLA-24-02
- **Unblocks:** WLA-24-05, WLA-24-06, WLA-24-07
- **Owner:** unassigned

## Problem

A score describes capability but is not consent. Long-lived orchestration
needs a separately reviewable grant, authoritative event ledger, exclusive
claims, budgets, expiry/revocation, and crash-derived projection before any
agent, check, or rail node may start.

## Scope

- **In:** `delivery-workbench-run-plan@1`, `run-grant@1`, `run@1`, and bounded
  event/receipt models; pure plan over compiled score+status+repo/story facts;
  explicit start token; `.git/pmo-orchestration/runs/<id>/` score/grant/ledger/
  projection layout; score hash and capability/budget preview; exclusive run/
  node claims; deterministic replay/projection; plan/start/show/list/pause/
  resume/revoke/cancel state primitives and CLI; expiry/revocation generation;
  privacy allowlists; corruption/tamper red paths.
- **Out:** scheduling nodes, agents/checks, browser editor/control, remote
  portable grants, certification/commit.

## Acceptance criteria

- [ ] Run planning is pure and names exact score hash, branch/HEAD/status/story,
  requested profiles/capabilities, workspace mode, every budget, expiry, and
  permanent exclusions; changing any fact changes the start token.
- [ ] Start requires that exact token and one explicit approval, writes an
  immutable compiled score and grant plus initial ledger event atomically,
  and refuses stale/malformed/ambiguous/overbroad input without run state.
- [ ] Projection is a deterministic replay of schema-pinned append-only
  events; disposable cache loss changes nothing, truncated/corrupt/forked
  ledgers fail closed, and content/prompt/secrets cannot enter event detail.
- [ ] Exclusive run/node claims, idempotency keys, revocation, expiry, and all
  budget counters are test-proven across processes; an old start/claim cannot
  replay.
- [ ] Pause/resume/revoke/cancel record exact transitions and prevent future
  dispatch immediately; CLI JSON/human shapes, Python floors, package/update,
  docs and red-path tests are green with evidence.

## Test plan

- **Unit:** model exact keys, plan/token purity/freshness, storage containment,
  atomic creation, replay projection, claims/races, expiry/revocation/budgets,
  corrupt ledger, privacy allowlist.
- **Integration:** two-process claim race and restart from ledger with cache
  deleted; installed CLI plan/start/show/pause/resume/cancel lifecycle.
- **Manual / device:** inspect a complete grant preview and confirm that it
  makes capability expansion and finite limits understandable before approval.

## Notes / open questions

The grant is deliberately local and non-portable. It is not a secret bearer
token and cannot authorize a different clone. The compiled score captured by
the run is immutable even if the tracked source score changes later.
