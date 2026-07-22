# WLA-25-09 - Prove the outward loop end to end

- **Project:** work-log-automation
- **Phase:** 25
- **Status:** in-progress
- **Depends on:** WLA-25-02, WLA-25-03, WLA-25-04, WLA-25-05, WLA-25-06, WLA-25-07, WLA-25-08
- **Unblocks:** none
- **Owner:** unassigned

## Problem

Phase 24 closed on a wheel-installed exam because packaged proof is the
only claim that survives contact with a fresh machine. Phase 25 makes a
larger promise — the product hears the outside world and acts on it
under grant — so its exit must walk the entire outward loop on a fresh
consumer with deterministic oracles, red paths for every new refusal,
and a separate live specimen, without ever letting model output or a
real forge become the CI oracle.

## Scope

- **In:** a Python-floor-built wheel installed into a fresh fixture
  consumer; a scripted end-to-end scenario on fixture SCM provider plus
  fixture driver: authorized run completes to `awaiting-certification`
  → operator integrates and pushes → fixture CI fails → signal recorded
  → standing-rule auto-nudge delivered to a receptive session → repair
  in an isolated worktree → recheck green → `changes-requested` signal
  → second nudge → checkpoint pending → conductor killed and resumed →
  outstanding request republished → decision answered through the typed
  port → notifications delivered, acknowledged, and consistent across
  CLI/MCP/HTTP/Workbench with the live stream replay matching the
  ledger byte for byte; red cases proving the new refusals: nudge
  without grant, nudge past exhausted budget, nudge to a
  `blocked`/`unknown` session, replayed signal fact, stale correlation
  id, revocation mid-loop stopping nudges and expiring outstanding
  requests, stream carrying no authority, observer writing nothing to
  forge or tree; certification and commit performed by the fixture
  operator alone; full test matrix, docs validation, and pre-close
  history green.
- **Out:** any real forge or live model in the CI path; release/version
  bump (a landing phase decides that separately); hosted or
  cross-machine transports.

## Acceptance criteria

- [ ] The fresh-wheel scenario passes end to end with every act, signal,
  nudge, refusal, republish, and decision present in the ledger and
  reproduced identically by stream replay.
- [ ] Every red case produces its exact contracted refusal with a
  recorded reason, and no red case leaves a side effect on the forge
  fixture, the operator tree, or any workspace.
- [ ] At-most-once holds under the planted mid-loop crash: zero
  duplicate node starts, zero duplicate nudges, exactly one republished
  request per outstanding decision.
- [ ] Certification and commit remain operator acts: the exam proves the
  run cannot flip a contract box, and the terminal state remains
  `awaiting-certification` until the fixture operator certifies.
- [ ] One authenticated live specimen exercises the outward seam with a
  real harness (WLA-25-07 driver receiving one real nudge round-trip),
  recorded as evidence outside CI.
- [ ] Phase exit: all Phase-25 exit criteria check against captured
  evidence, `dw check` and `dw verify` are clean, and the phase status
  and roadmap README tell the finished story.

## Test plan

- **Unit:** n/a (this story composes; units live in WLA-25-02..08).
- **Integration:** the packaged scenario and red-case suite, run on the
  supported OS matrix.
- **Manual / device:** the live specimen, captured with
  `dw evidence capture`; one phone-side checkpoint answer over the
  consented Telegram surface.

## Notes / open questions

The exam deliberately includes the operator's integration push as a
manual step in the script narrative: the outward loop begins where run
authority ended, and the exam must show that boundary rather than blur
it.
