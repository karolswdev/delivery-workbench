# WLA-29-05 - Judge only the failures we introduced

- **Project:** work-log-automation
- **Phase:** 29
- **Status:** done
- **Depends on:** WLA-29-01
- **Unblocks:** WLA-29-08
- **Owner:** unassigned

## Problem

The verdict layer currently judges a change against the repository's test
outcome as a whole. On this repository that is fine — the suite is green —
but on any adopted repository with pre-existing failures it makes autonomous
delivery impossible: every change inherits every old failure and no verdict
can pass. The studied prototype's most practical pattern answers this: run
the tests on the clean tree before dispatch, record the failing set, and
after the change judge only `current failures − baseline failures`.

The pattern is only safe if the baseline is a fact, not a claim. An agent
must never be able to assert its own baseline, and a failure absent from the
baseline must block without appeal — the prototype's proceed-on-exhausted-
budget behavior is exactly what this project rejects.

## Scope

- **In:** baseline capture at run/program start: the declared test command
  runs on the clean workspace before any dispatch, and the failing-test set
  is recorded as a ledgered fact (bounded: test identifiers and counts, never
  output prose) tied to the head SHA it was observed at; verdict semantics
  that classify post-change failures as **introduced** (block, no budget or
  loop may advance past them) or **pre-existing** (reported, non-blocking,
  and emitted as typed obligations of kind `technical-debt` so they enter the
  existing obligation machinery); rubric and gate-proof-packet surfaces
  showing both sets explicitly; refusal when the baseline is missing or was
  captured at a different head than the workspace branched from.
- **Out:** weakening any existing check — on a green baseline the behavior is
  exactly today's; auto-fixing pre-existing failures; flake detection or
  retry heuristics (a flaky test appears introduced and blocks, and that is
  the honest default); baselines for anything but the declared test command.

## Acceptance criteria

- [ ] Baseline capture runs before first dispatch, is recorded in the ledger
  as a bounded fact with head-SHA provenance, and cannot be written or
  amended by any agent-facing surface.
- [ ] A post-change failure present in the baseline is classified
  pre-existing; one absent from it blocks the verdict, and no revision loop,
  budget exhaustion, or supervision ceiling can advance work past it —
  proven by a planted regression that must end at a checkpoint or refusal.
- [ ] Pre-existing failures emit obligations of kind `technical-debt` with
  test identifiers, deduplicated across ticks of the same run.
- [ ] A missing, foreign-head, or stale baseline refuses subtraction and
  falls back to judging all failures as introduced — fail closed, never open.
- [ ] Verdict and gate-proof surfaces render both sets distinctly; nothing
  reports a run "green" while pre-existing failures exist — the honest state
  is "no introduced failures, N pre-existing".
- [ ] On a green baseline, byte-identical verdict behavior to today, proven
  by the existing verdict suite passing unchanged.

## Test plan

- **Unit:** subtraction classification; fail-closed paths (missing baseline,
  head mismatch); obligation emission and dedup; bounded fact shape.
- **Integration:** `dw evidence capture` of a fixture program run on a
  repository with one pre-existing failure, showing dispatch proceeding, a
  planted new failure blocking, and the obligation appearing in `dw holds`
  -adjacent surfaces.
- **Manual:** read the rendered verdict for the fixture run and confirm the
  two sets cannot be confused.

## Notes / open questions

The baseline is deliberately per-run, not cached across runs: freshness is
the same argument as phase 28's — re-observation is the job, and a stale
baseline would let a regression hide behind an old failure list.

Flakiness is recorded as an open question, not solved: the honest default
(flakes block) will surface real flaky tests as friction in WLA-29-08, which
is where the evidence for any future flake policy should come from.

Implemented as `dw_pmo/test_baseline.py` (parsing, bounded fact shapes,
classification, shared failure projection) with capture and enforcement in
the conductor/verdict layers. Delivery details worth keeping: the declared
test command is the unique exact command runner across a program's
workflows (repeated identical declarations collapse; multiple distinct
commands make subtraction unavailable and fail closed); the parser accepts
only exactly reconciled unittest/pytest markers, so opaque output is
introduced failure, not debt; baseline worktrees persist per repository
and recreate only on head change; mechanical facts now carry an explicit
`validates_exit_code` field instead of predicate-name branching. Bounded
score runs keep existing whole-result semantics untouched. Review absorbed
before landing: batched obligation recording (one event, one replay),
cached replay on baseline write, strict `technical-debt` obligation shape
validation, one shared projection helper. Suite 581 → 589 green; packaged
exam complete on the merged tree.
