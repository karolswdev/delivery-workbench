# WLA-29-08 - Serve ourselves for real

- **Project:** work-log-automation
- **Phase:** 29
- **Status:** backlog
- **Depends on:** WLA-29-03, WLA-29-04, WLA-29-05, WLA-29-06, WLA-29-07
- **Unblocks:** -
- **Owner:** unassigned

## Problem

The program engine is architecturally complete and fixture-proven — the
packaged exam drives it end to end — and it has never once run for real.
This repository's own `.git` holds zero program runs and exactly one bounded
run, revoked at its first checkpoint (2026-07-22). Every guarantee the engine
makes about real work is, today, an extrapolation from fixtures.

The studied prototype fails at the gate; we have not yet earned the right to
say we don't. This story is the phase's exit exam: a real checkpointed
autonomous program, on live adapters, delivers at least one real story in
this repository through everything this phase built — knowledge packets,
grounding, baseline subtraction, the diversity rule, lesson write-back —
ending where it must: at the human certification seam, because certification
and commit are manual by contract and stay that way.

## Scope

- **In:** authoring a real program (checkpointed mode) over a genuine
  maintenance-scale story in this repository — real enough to require code,
  tests, and evidence, small enough that a failed run costs a day, chosen and
  recorded at run time; live claude and/or codex adapters satisfying the
  diversity rule; the run driven through the existing surfaces (Workbench or
  CLI) with its checkpoints decided by the operator; capture of the complete
  receipts — grant, ledger, packets, verdicts, obligations, lessons,
  certification handoff, and the operator-certified gated commit that ships
  the delivered story; a friction ledger: every rough edge the run exposes is
  recorded as a follow-up story draft or a typed obligation before this story
  closes; honest accounting of attempts — if the first run is revoked or
  blocked, that run's receipts are part of the evidence, not discarded.
- **Out:** continuous mode (checkpointed is the deliberate ceiling for the
  first real run); granting merge, push, release, or publication capability
  (excluded since Phase 26); fixture adapters anywhere in the evidence;
  choosing a story so trivial the run proves nothing (a docs-typo story does
  not qualify — the run must produce code and tests judged by verdicts);
  fixing every discovered friction inside this story — recording it is the
  deliverable, fixing it is the next phase's backlog.

## Acceptance criteria

- [ ] A program grant exists for a named real story in this repository, in
  checkpointed mode, with live adapters and the diversity rule in force; the
  grant, score, and organization are part of the evidence.
- [ ] The run's ledger shows the phase's machinery working on real work:
  a knowledge packet with verified locations in the dispatch, a ledgered
  baseline fact before dispatch, verdicts classifying failures, and lessons
  persisted at the seam.
- [ ] At least one checkpoint was reached and decided by the operator through
  an existing decision surface (Workbench, CLI, or Telegram `/decision`),
  and the decision is visible in the ledger.
- [ ] The run ends at the certification seam; a human certifies and commits;
  the delivered story flips done through the ordinary gate with its evidence
  in the same commit — the gate, not this story, judges that work.
- [ ] The friction ledger exists and is honest: every manual intervention,
  refusal, stall, unclear surface, or wrong packet observed during the run is
  recorded with what happened and where, as follow-up story drafts or typed
  obligations. An empty friction ledger is treated as a red flag, not a
  success.
- [ ] The evidence file tells the whole truth: attempts, revocations, and
  restarts included, with wall-clock and cost figures (unknowns reported as
  unknown).

## Test plan

- **Unit:** n/a — this story exercises shipped machinery.
- **Integration:** the run itself, captured via `dw evidence capture` around
  the driving commands and the final `dw verify` over the resulting range.
- **Manual:** operator drives checkpoints and performs certification and
  commit; a read-back of the ledger against what the operator actually
  observed.

## Notes / open questions

The delivered story's own commit passes the ordinary gate under the ordinary
rules; this story's evidence is *about the run*, and the one-story-per-commit
rule is respected by keeping the two flips in separate commits.

What "maintenance-scale" concretely is gets decided when the run is
authorized, against the backlog that exists then — candidates include a
budget follow-up from phase 28's deferred items or a friction story from
earlier in this phase. Recording the choice and why is part of the evidence.

If the run fails badly enough that no story can be delivered after honest
attempts, this story does not close by lowering the bar; it goes on hold with
the receipts recorded, and the blockers become the phase's most important
output.
