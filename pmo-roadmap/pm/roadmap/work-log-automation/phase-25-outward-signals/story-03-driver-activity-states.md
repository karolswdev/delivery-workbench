# WLA-25-03 - Teach drivers to report activity states

- **Project:** work-log-automation
- **Phase:** 25
- **Status:** backlog
- **Depends on:** WLA-25-01
- **Unblocks:** WLA-25-04, WLA-25-07, WLA-25-09
- **Owner:** unassigned

## Problem

The Phase-24 driver protocol reports lifecycle outcomes (running,
succeeded, failed, lost, cancelled) but nothing about *why* a live agent
is not progressing. Agent Orchestrator's durable `activity_state`
distinguishes an agent at an empty prompt (`waiting_input`) from an agent
stopped on a permission decision (`blocked`) — and hangs its central
safety rule on that distinction: automation must never inject input into
a blocked session. Nudging (WLA-25-04) is impossible to do safely until
our drivers can report which state a session is in, and impossible to
test until the fixture driver can fake every state.

## Scope

- **In:** extend the driver `poll` contract with the contracted activity
  vocabulary `active | idle | waiting_input | blocked | exited` plus
  `unknown` for adapters that cannot observe a state; the receptivity
  table (nudges deliverable only in `waiting_input` and `idle`;
  `blocked` and `unknown` always refuse; `active` defers with a bounded
  re-poll; `exited` is terminal); activity facts recorded as ledger
  events and exposed through `run show`, `run view`, and the Workbench
  Run view; `FixtureDriver` scripting for every state and every
  transition, including a session that flips to `blocked` mid-nudge;
  `CodexExecDriver` mapping for its honest subset (non-interactive exec
  is `active` or `exited`; it reports `unknown` for the rest, never a
  guess).
- **Out:** the nudge engine itself (WLA-25-04); interactive terminal
  attachment or PTY multiplexing; inferring activity from terminal
  scraping — a driver reports only what its harness actually exposes.

## Acceptance criteria

- [ ] The driver protocol carries the six-value activity vocabulary with
  exact meanings from the WLA-25-01 contract, and adapters that cannot
  observe a state must report `unknown` — a conformance test rejects an
  adapter that invents states it cannot substantiate.
- [ ] The receptivity table is a pure function with exhaustive tests:
  every (state, intent) pair maps to deliver, defer, or refuse, and
  `blocked` and `unknown` refuse injection under every intent including
  an operator-initiated manual nudge.
- [ ] Activity transitions appear as ledger facts with timestamps and
  attempt binding, visible in `run show`/`run view` and the Workbench
  without any new polling authority.
- [ ] `FixtureDriver` can script every state, every transition, and a
  mid-flight flip to `blocked`, deterministically across restart.
- [ ] `CodexExecDriver` reports only `active`/`exited`/`unknown`, proven
  by test; no code path derives a richer state from output heuristics.

## Test plan

- **Unit:** vocabulary serialization, receptivity function, conformance
  suite for both adapters.
- **Integration:** a fixture run whose session walks
  `active → waiting_input → blocked → waiting_input → exited` with the
  projection and all surfaces agreeing at each step.
- **Manual / device:** observe a live non-interactive session and confirm
  it reports exactly `active` then `exited`, with `unknown` never shown
  as a receptive state anywhere in the Workbench.

## Notes / open questions

Interactive harnesses (a future tmux-resident session) are where
`waiting_input`/`blocked` become real rather than fixture-only; this
story deliberately lands the contract and the honest `unknown` before
any adapter claims interactive fidelity.
