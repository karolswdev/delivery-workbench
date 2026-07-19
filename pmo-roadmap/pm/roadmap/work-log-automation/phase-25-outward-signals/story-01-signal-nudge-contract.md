# WLA-25-01 - Contract the outward signal and nudge authority

- **Project:** work-log-automation
- **Phase:** 25
- **Status:** done
- **Depends on:** none
- **Unblocks:** WLA-25-02 through WLA-25-09
- **Owner:** unassigned

## Problem

Phase 24 closed the inward loop: a granted run observes its own checks,
routes its own repairs, and stops at `awaiting-certification`. The world
outside the run stays invisible — a pushed branch whose CI fails, a review
that requests changes, a merge conflict forming under an open PR, an agent
sitting at an empty prompt. Agent Orchestrator (AgentWrapper/agent-orchestrator)
proves the value of watching those facts continuously and routing them back
to the right agent; it also proves the danger of doing so from a daemon that
holds unaccounted authority. Before any observer or nudge code exists, one
contract must say exactly which outward facts Delivery Workbench records,
what a nudge is, who may authorize one, and which injections remain
prohibited forever — otherwise the observer becomes a second hidden loop.

## Scope

- **In:** `docs/signals.md` (new architecture contract, cross-linked from
  `docs/orchestration.md`); the `delivery-workbench-signal@1` durable fact
  model (SCM facts: PR identity/state, checks, review threads, mergeability;
  driver facts: activity states); the derived-status precedence table
  (observed facts in, display status computed at read time, never stored);
  the nudge definition — a structured, hash-bound packet tied to one
  triggering signal, one target node/session, and one granted nudge budget;
  the activity-state vocabulary (`active | idle | waiting_input | blocked |
  exited`) and the invariant that a `blocked` session (pending
  permission/approval decision) never receives injected input; authority
  rings for observe (pure) vs nudge (granted) vs operator decision (manual);
  storage/privacy boundaries; threat table; the Phase-25 story plan with
  ordered dependencies.
- **Out:** observer code, nudge engine code, transports, provider adapters,
  notification channels; any automatic certification, commit, merge, push,
  or conflict resolution; hosted/central observers.

## Acceptance criteria

- [x] The contract states Delivery Workbench **can observe** outward facts
  and **can nudge** under an explicit grant, in capability language, and
  cleanly separates the authority-free observer (records facts, derives
  status, starts nothing) from the granted nudge engine (acts, bounded,
  ledgered, revocable).
- [x] One versioned `delivery-workbench-signal@1` fact model covers SCM
  facts (PR, checks, review threads, mergeability) and driver activity
  facts, with the precedence rules that derive display status at read time
  and a rule that raw third-party content (CI logs, review bodies) is
  referenced, never copied into durable facts.
- [x] A nudge is defined exactly: triggering signal hash, target, bounded
  structured content, grant binding, budget accounting, single ledger
  receipt; nudge policy lives in the score, nudge authority lives in the
  grant, and neither the observer nor a driver can invent a nudge.
- [x] The activity-state vocabulary and the `blocked`-never-receives-input
  invariant are stated as testable refusals, alongside the permanent
  exclusions: no injection into interactive permission prompts, no
  auto-merge, no auto-certification/commit/push, no cross-repository
  nudging, no secrets in signal facts.
- [x] The threat table contains fail checks for observer-becomes-actor,
  nudge storms (budget exhaustion semantics), stale-signal nudges, forged
  or replayed signals, nudging a revoked/expired run, injecting into a
  blocked session, and status derived from stored (rather than observed)
  state.
- [x] Phase status and all eight dependent stories have ordered
  dependencies, bounded scope, and testable acceptance criteria; docs and
  roadmap validation pass with captured evidence.

## Test plan

- **Unit:** structural doc assertions pin the fact model, nudge definition,
  activity vocabulary, authority rings, and permanent exclusions until
  executable tests own them.
- **Integration:** docs lint/snippets, roadmap self-check, generated-surface
  parity, diff hygiene.
- **Manual / device:** walk one narrated scenario — push, CI fails, signal
  recorded, nudge previewed and delivered under grant, repair runs, operator
  notified — and verify every step maps to one contracted fact, act, or
  refusal.

## Notes / open questions

Owner direction, 2026-07-18: auto-nudging is supported — the corrective from
the Agent Orchestrator comparison is not "never inject" but "never inject
without a grant, a budget, and a receipt". The observer stays authority-free
the way `dw status` is; the nudge engine is authority the way `dw run` is.

The `blocked` exclusion is not a softening of that direction: a session
stopped on a permission decision is awaiting an *approval*, and approvals
are ring-4 human acts everywhere else in the product. Nudges deliver to
receptive states (`waiting_input`, `idle`) only.
