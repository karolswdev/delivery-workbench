# WLA-30-10 - Pass the empty-directory exam

- **Project:** work-log-automation
- **Phase:** 30
- **Status:** backlog
- **Depends on:** WLA-30-02, WLA-30-04, WLA-30-05, WLA-30-06, WLA-30-07, WLA-30-08, WLA-30-09
- **Unblocks:** none
- **Owner:** unassigned

## Problem

Phase 29 closed on a real program run; Phase 30 closes on a real *journey*.
The exam: a neutral directory outside this checkout, a release-candidate
wheel, and a rough idea — through `dw init`, one Scope-Chat conversation, a
workbench review, one exact setup approval, one exact grant approval, a
live cross-provider program delivering a real first story to certified
handoff, manual certification, a manual commit, and `dw verify` green. A
fixture-only run, a hand-authored bundle, a checkout-relative install, or
an automatically checked contract box fails the exam. Phase 29's run cost
thirteen grants; this journey must cost at most two.

The exam also produces the landing evidence: whether to publish is the
owner's decision, and the recorded settling-period decision stands until
explicitly superseded — this story's job is to make that decision fully
informed, with the release-candidate proven cold-installable.

## Scope

- **In:** the full exam from an empty directory on a built wheel with a
  rough greenfield idea (e.g. "a small CLI that checks a list of URLs and
  exits nonzero when any are unavailable"): init → conversation → review →
  setup lease → grant lease → live run (implementer and verifier from
  different declared provider families, declared mechanical tests,
  rubric verdict, certified handoff, no commit authority) → lesson
  persisted → certified candidate integrated through the ordinary guarded
  rail → manual contract certification → manual `git commit` →
  `dw verify` → a second planning pass retrieving the first run's lesson.
  A cold-install repetition of init and status smoke from the packaged
  candidate in another neutral directory. A grant-count and budget summary
  compared against Phase 29's thirteen-grant baseline. The complete
  human-readable transcript and artifact chain captured as evidence. A
  landing packet presented for the owner's release decision.
- **Out:** the program publishing, merging, releasing, or deploying
  anything (permanent exclusions); auto-certification or auto-commit under
  any pretext; superseding the settling-period decision inside this story
  — the release itself, if the owner decides to land, follows the existing
  manual ritual and its own checklist.

## Acceptance criteria

- [ ] The journey completes from a genuinely empty directory on a
  release-candidate wheel: one command, one conversation, three
  approvals, live delivery, manual certification and commit, `dw verify`
  green.
- [ ] The generated program uses at least two declared provider families
  for implementer and verifier, with runtime independence evidenced in
  the ledger.
- [ ] The successful attempt consumes at most two program grants and stays
  within its declared budgets; unknown provider cost is reported unknown,
  never zero.
- [ ] No grant in the exam contains merge, release, deploy, publish,
  conflict-resolution, arbitrary-shell, or arbitrary-network authority,
  proven from the grant records.
- [ ] The no-commit run leaves at least one bounded lesson that a
  subsequent planning pass retrieves, captured in the transcript.
- [ ] Certification is hand-checked and commit is a human command, visible
  as such in the evidence.
- [ ] The cold-install repetition passes in a second neutral directory.
- [ ] The landing packet — exam transcript, artifact chain, grant/budget
  comparison, version-parity status — is assembled and presented for the
  owner's release decision, with the decision recorded either way.

## Test plan

- **Unit:** n/a — this story is the exam.
- **Integration:** the packaged-consumer suites on the release candidate
  before the live attempt; `dw verify` over the exam repository's history.
- **Manual / device:** the exam itself, driven by the operator with live
  adapters; the owner's review of the landing packet.

## Notes / open questions

If the exam surfaces stranded-claim recovery as a blocker, the deferred
recovery story gets pulled into this phase by decision, not by drift.
The two-grant ceiling is deliberately tight: it is the measurement Phase
29 asked for ("a cheaper second run"), and missing it is information, not
shame — but the phase does not close on a thirteen-grant journey.
