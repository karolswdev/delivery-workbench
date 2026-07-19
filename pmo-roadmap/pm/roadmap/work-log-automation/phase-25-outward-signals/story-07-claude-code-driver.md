# WLA-25-07 - Drive Claude Code through the neutral seam

- **Project:** work-log-automation
- **Phase:** 25
- **Status:** backlog
- **Depends on:** WLA-25-01, WLA-25-03
- **Unblocks:** WLA-25-09
- **Owner:** unassigned

## Problem

The provider-neutral driver seam is proven by one deterministic oracle
and one live adapter (`codex exec`). Agent Orchestrator ships
twenty-three adapters; its lesson is that the adapter roster is where an
orchestration layer becomes broadly useful, and that every adapter must
be least-privilege by construction. The obvious second live adapter for
this project is Claude Code's non-interactive mode — the harness this
repository is developed with — which also gives the activity-state
contract (WLA-25-03) and nudge delivery (WLA-25-04) a second real
implementation, keeping the seam honest about what is fixture-only.

## Scope

- **In:** `ClaudeCodeExecDriver` using non-interactive `claude -p`
  invocation mirroring the `CodexExecDriver` posture: explicit
  read-only versus workspace-write sandbox selection mapped from the
  granted capability, ephemeral session state under the run's
  `driver-sessions/`, no inherited host secrets beyond what the harness
  itself owns, bounded stdout/stderr capture, cancellation via
  interrupt, receipts persisted across restart; capability discovery
  reporting exactly what the local `claude` binary version supports and
  refusing content-free on mismatch; activity mapping per WLA-25-03
  (`active`/`exited`/`unknown` only); nudge packets delivered as a
  follow-up non-interactive turn only when the receptivity table
  permits; operator-local `drivers.json` profile mapping documented
  alongside the existing adapters.
- **Out:** interactive/PTY Claude Code sessions; MCP-transport driving;
  making live model output a CI oracle (live runs stay smoke/specimen,
  exactly like Codex); any Anthropic-specific field entering the score
  or the packet schema.

## Acceptance criteria

- [ ] The adapter passes the full driver conformance suite (start, poll,
  interrupt, collect, restart-receipt, capability refusal) with no
  changes to the seam's neutral schemas.
- [ ] Sandbox selection is least-privilege by construction: a read-only
  capability can never produce a workspace-write invocation, proven by
  argv inspection tests; writer invocations run only in the node's
  isolated worktree.
- [ ] No credential-shaped configuration is accepted in `drivers.json`
  for this adapter; authentication remains entirely harness-owned, and
  the adapter refuses content-free when the harness is unauthenticated.
- [ ] Activity reporting claims only `active`/`exited`/`unknown`, and
  nudge delivery through the adapter respects the receptivity table
  with a test for the refusal path.
- [ ] One authenticated live specimen — a bounded read-only research
  node and one nudge round-trip — passes outside CI, recorded as
  evidence the way the Codex specimen was; CI itself stays green on
  fixtures alone.

## Test plan

- **Unit:** argv construction, sandbox mapping, capability discovery,
  output bounding, receipt persistence.
- **Integration:** conformance suite; fixture-substituted binary proving
  refusal and interrupt paths without network.
- **Manual / device:** the live specimen run, captured with
  `dw evidence capture`.

## Notes / open questions

Version skew is the real maintenance cost AO absorbs across 23 adapters;
capability discovery must pin the tested `claude` version range and
refuse outside it rather than degrade silently.
