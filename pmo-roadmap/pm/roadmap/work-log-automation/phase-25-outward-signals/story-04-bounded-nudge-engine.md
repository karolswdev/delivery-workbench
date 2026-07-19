# WLA-25-04 - Nudge agents under grant authority

- **Project:** work-log-automation
- **Phase:** 25
- **Status:** done
- **Depends on:** WLA-25-01, WLA-25-02, WLA-25-03
- **Unblocks:** WLA-25-06, WLA-25-09
- **Owner:** unassigned

## Problem

Signals that only sit in a ledger still leave the operator as the
message bus: CI fails, and a human copies the failure back to the agent
that caused it. Agent Orchestrator closes this loop by auto-nudging —
and the owner direction for this phase is explicit: auto-nudging is
supported. What Delivery Workbench refuses is not the nudge but the
unaccounted nudge. This story makes the nudge a first-class granted act:
declared in the score, authorized by the grant, budgeted, delivered only
to receptive sessions, and receipted in the ledger like every other
dispatch.

## Scope

- **In:** a `nudges` section in the `delivery-workbench-orchestration@1`
  score — each rule binds one signal kind (`ci-failed`,
  `changes-requested`, `merge-conflict`, plus activity-derived
  `waiting-input-timeout`) to one target (a named node/profile or the
  node that produced the triggering artifact), a bounded structured
  content template (facts and references only, no free-form prose
  injection), and per-rule/per-run nudge ceilings; grant extensions:
  nudge budgets and **standing nudge rules** using the exact-match
  grammar absorbed from microsoft/agent-framework-go's tool-approval
  harness — a standing rule matches a signal kind exactly or a kind plus
  exact target, is narrow by default, run-scoped, and revocable with the
  grant; conductor integration: during a tick, fresh signal facts are
  matched against rules, each candidate nudge is previewed
  (token-bound, like every act), auto-applied only when a standing rule
  covers it exactly, delivered through the driver seam as a hash-bound
  structured packet, and receipted with the triggering signal hash,
  target, attempt, and budget counters; delivery respects the WLA-25-03
  receptivity table; pause/revoke/cancel/expiry stop future nudges
  immediately.
- **Out:** nudging sessions outside a granted run; free-text operator
  chat to agents; nudges that carry commands, shell strings, secrets, or
  third-party content bodies; cross-repository nudging; auto-merge or
  any SCM mutation as a "nudge".

## Acceptance criteria

- [x] A score without a `nudges` section compiles to a run in which the
  nudge engine is inert, proven by test; nudge rules are validated at
  compile time (known signal kinds, resolvable targets, finite ceilings)
  with exact diagnostics.
- [x] A nudge happens only under a grant whose budgets cover it: no
  grant, exhausted budget, expired/revoked/paused run, or missing
  standing rule each produce a distinct recorded refusal, never a
  delivery.
- [x] Standing nudge rules follow the exact-match grammar (kind, or
  kind + exact target), default to absent, are stated in the grant
  preview the operator approves, and revoke with the grant; a rule can
  never broaden at runtime.
- [x] Every delivered nudge is one ledger receipt binding signal hash,
  rule, target, attempt, packet hash, and remaining budgets; replaying
  the same signal fact cannot produce a second delivery (at-most-once
  per signal per rule, enforced across restart).
- [x] Delivery consults the receptivity table at dispatch time:
  `blocked`/`unknown` refuse, `active` defers with bounded re-poll, and
  a mid-flight flip to `blocked` (fixture-scripted) converts the nudge
  to a recorded refusal.
- [x] Budget exhaustion converts the run to a recorded `blocked` stop
  with an operator-facing reason — a nudge storm can never loop; the
  fixture exam in WLA-25-09 includes this red path.

## Test plan

- **Unit:** rule compilation, standing-rule matching, budget accounting,
  at-most-once dedup keyed on signal hash, refusal taxonomy.
- **Integration:** fixture run — CI-failed signal → standing rule →
  preview → delivery → repair dispatch; red paths for every refusal
  class; crash between match and delivery recovers without a duplicate.
- **Manual / device:** author nudge rules in the Workbench editor,
  approve a grant with one standing rule, watch one auto-nudge land in
  the Run view with its signal lineage visible.

## Notes / open questions

Owner direction, 2026-07-18: auto-nudging is in scope — bounded by
grant, not forbidden. The design splits AO's single implicit behavior
into three explicit layers: rule (score, reviewable), authority (grant,
revocable), act (ledger, auditable).

The target question was settled by the WLA-25-01 contract before this
story started: nudge targets are declared route targets only — a rule may
name any agent node in the score (naming a failure-activated node makes
it reachable exactly like a failure route does), and an unwired fixer
remains a score edit plus re-grant.
