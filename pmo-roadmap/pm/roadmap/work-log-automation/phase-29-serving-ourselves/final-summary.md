# Phase 29 - Serving ourselves - Final summary

**Closed:** 2026-07-27. **Stories:** 9/9 done, every one shipped through the
gate with captured evidence.

## What this phase set out to do

Adopt the grounding layer a comparative study (krishagarwal314/autodev-studio,
2026-07-26) showed we lacked — persistent repository knowledge, deterministic
grounding, baseline failure subtraction, cross-provider review, honest
telemetry — and then prove the program engine on ourselves: a real
checkpointed autonomous program delivering a real story in this repository,
where before this phase the engine had zero real runs.

## What was delivered

- **WLA-29-01** — `delivery-workbench-repository-knowledge@1`: derived facts
  (disposable, index-tree-bound) vs earned records (append-only, capped,
  provenance-stamped), with the authority exclusion fitness-tested in both
  directions. Knowledge informs; it never authorizes.
- **WLA-29-02** — the deterministic symbol and structure map: 4,388 symbols,
  honest out-of-coverage gaps, incremental refresh proven at one parse per
  changed file, CLI/MCP parity.
- **WLA-29-03** — mechanical grounding of advisory story hints
  (verified/new/unknown), `(new)` honored only with complete no-match
  evidence, warnings-only by contract.
- **WLA-29-04** — knowledge packets in the agent-packet seam: pure,
  deterministic, byte-budgeted with named exclusions, typed stale refusals;
  plus honest-unknown usage telemetry end to end.
- **WLA-29-05** — baseline failure subtraction: ledgered pre-dispatch
  baseline facts, introduced failures block unconditionally, pre-existing
  failures become typed `technical-debt` obligations, fail-closed on any
  stale baseline.
- **WLA-29-06** — provider-family diversity as organization policy, enforced
  at assignment and refused at validate time when unsatisfiable; not
  default-on.
- **WLA-29-07** — delivery write-back: ledger-derived delivery records and
  capped, provenance-stamped lessons persisted only at the terminal seam,
  retrieved by later packets with supersession chains.
- **WLA-29-08** — the exit exam: thirteen ledgered grants; seven
  machinery/configuration defect classes found by real execution and fixed
  through the gate (write containment vs bytecode, driver env allowlists,
  empty verdict child grants, unledgered crash paths, missing live-verdict
  response contracts, mechanical-fact subject binding, inherited child
  stdin); a 17-entry friction ledger in evidence; attempt 13 ran the full
  arc to `story-certified / integration-required` with no commit authority.
- **WLA-29-09** — delivered *by* that program: live claude implemented from
  a knowledge packet, the focused regression passed, live codex certified
  all four rubric criteria under the diversity rule, and the operator
  integrated and shipped it through the ordinary gate. The story itself
  fixed the phase's own worst operational friction (worktree
  `core.hooksPath` corruption).

## The numbers

Core suite 530 → 604 tests, all green throughout. Ten gated commits of
machinery, four of program configuration, thirteen program grants, one
autonomous delivery. `dw verify` clean over the full range.

## What the exam taught (the phase's real product)

Fixture-proven is not operationally proven. Every defect the exam found was
invisible to a 3,181-line packaged exam because fixtures conform by
construction; live models, live CLIs, and live environments do not. The
fail-closed spine held every single time — no failure advanced work, no
crash minted state — and the cost of that honesty was thirteen attempts.
The friction ledger (17 entries, evidence-story-08) is the seed backlog for
the next phase, headlined by: lesson write-back requires commit-capable
grants (structural), a stranded-claim recovery act, compiler/conductor
node-type parity, driver env allowlist gaps, and validate-time
rubric-vs-workflow fact cross-checks.

## Decisions that bound the future

Knowledge informs, never authorizes — now contract, fitness tests, and
habit. Introduced failures block, unconditionally. Quality inconclusiveness
stops at seams and summons humans; it never advances by exhausting budgets.
Configuration is not authority: thirteen grants, each finite, reasoned, and
revocable, are the record of what deliberate autonomy looks like.
