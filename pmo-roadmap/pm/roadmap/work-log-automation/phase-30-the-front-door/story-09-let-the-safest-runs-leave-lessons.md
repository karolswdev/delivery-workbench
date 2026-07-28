# WLA-30-09 - Let the safest runs leave lessons

- **Project:** work-log-automation
- **Phase:** 30
- **Status:** done
- **Depends on:** WLA-30-01
- **Unblocks:** WLA-30-10
- **Owner:** unassigned

## Problem

Phase 29's named follow-up obligation: lesson write-back only fires inside
the commit-capable delivery bundle, so a no-commit grant — the safest kind,
and the kind the scaffold generates by default — can never make the next
run cheaper. The compounding thesis of the knowledge layer breaks exactly
where the front door needs it most: a newcomer's first program is
no-commit, and it currently learns nothing.

The fix is a terminal seam, not a loophole: a narrow, independently
budgeted lesson-write-back capability that a no-commit grant may request,
persisting bounded lessons at certified handoff — honestly labeled as
certified-but-not-integrated, because a lesson from an unintegrated
candidate is a different epistemic object than one from shipped work.

## Scope

- **In:** a narrow knowledge-write-back capability (or equivalent exact
  act) requestable by no-commit grants without receiving integration,
  certification, commit, push, or roadmap authority; persistence at
  certified handoff of bounded lessons carrying exact run, story, subject,
  adapter, verdict, and delivery-state provenance; a
  `certified-not-integrated` label that later integration may confirm or
  supersede without rewriting history; idempotent replay of the same
  terminal receipt with no double budget consumption; retrieval through
  the existing knowledge-packet path with the delivery-state label
  preserved.
- **Out:** lessons from any non-success terminal (failed, refused,
  revoked, cancelled, expired, malformed, uncertified — all persist
  nothing); repo-tracked lessons, shared or hosted knowledge, embeddings
  (all still deferred); any weakening of the knowledge hard constraint —
  lessons still inform and never authorize.

## Acceptance criteria

- [ ] A no-commit grant can request the capability, and the granted set
  provably excludes integration, certification, commit, push, and
  roadmap authority.
- [ ] A certified handoff persists a bounded lesson with full provenance
  and the `certified-not-integrated` label; later integration confirms or
  supersedes it append-only.
- [ ] Negative tests across every non-success terminal state persist no
  lesson.
- [ ] Replaying the same terminal receipt is idempotent and consumes no
  additional lesson budget, including across a planted crash-and-replay.
- [ ] A subsequent knowledge packet retrieves the lesson with its
  delivery-state label intact.
- [ ] Authority-fitness tests prove gate, grant, verdict, and
  certification code cannot consume a lesson as proof of anything.

## Test plan

- **Unit:** capability narrowing; label transitions; receipt idempotency.
- **Integration:** a two-run fixture — the first no-commit run emits a
  lesson, the second retrieves it in its packet; the non-success terminal
  matrix; crash replay; authority-fitness suite.
- **Manual / device:** none beyond the live capture WLA-30-10 performs.

## Notes / open questions

The label vocabulary (`certified-not-integrated` → confirmed/superseded)
should be closed and small; resist a general lifecycle enum. Whether
supersession on integration is automatic (post-commit hook observes the
landed tree) or a guarded act is open; default is automatic observation,
since it derives from repository facts and mints nothing.
