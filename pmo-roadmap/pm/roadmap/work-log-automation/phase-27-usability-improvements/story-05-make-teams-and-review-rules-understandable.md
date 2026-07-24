# WLA-27-05 - Make teams and review rules understandable

- **Project:** work-log-automation
- **Phase:** 27
- **Status:** backlog
- **Depends on:** WLA-27-01, WLA-27-02
- **Unblocks:** WLA-27-06 through WLA-27-10
- **Owner:** unassigned

## Problem

The organization editor can represent implementers, independent verifiers,
panels, councils, judges, meta-reviewers, and architect gates, but the exact
topology does not naturally answer who will do the work, who will review it,
who can decide, or whether independence is real. Misunderstanding those
relationships is both a usability defect and a quality risk.

This story makes team and review design legible in ordinary role and
responsibility language while keeping every separation and provenance rule
mechanically exact.

## Scope

- **In:** task-centered team/review sections in Program Studio; readable role,
  responsibility, independence, quorum, dissent, escalation, and meta-review
  summaries; assignment and validation guidance; council/panel progressive
  detail; provenance and exact technical inspection; round-trip fixtures.
- **Out:** new agent providers or models; automatic credential selection;
  weakening independent-verifier or principal/workspace/session separation;
  changing quorum, verdict, debate, or architect-gate semantics; live review
  operation owned by WLA-27-06 and WLA-27-07.

## Acceptance criteria

- [ ] Before starting, a person can answer who does each kind of work, who
  reviews it independently, who makes contested decisions, and who receives an
  escalation from the ordinary summary.
- [ ] Independence and incompatible assignments are shown as understandable
  quality constraints with the exact conflicting roles and a corrective path,
  not only as topology or provenance errors.
- [ ] Panels, councils, dissent, judges, meta-review, and architect checks are
  progressively disclosed with plain descriptions of when they run and what
  their outcomes can change.
- [ ] Provider/model/auth/principal/workspace/session provenance remains
  inspectable in the technical view and is never collapsed in a way that could
  falsely claim independence.
- [ ] Existing organizations, including advanced council fixtures, round-trip
  without semantic loss; invalid organizations continue to refuse.
- [ ] Team and review summaries use the WLA-27-01 vocabulary and share the same
  data projection as live-operation ownership/review displays.

## Test plan

- **Unit:** cover responsibility summaries, independence explanations,
  quorum/dissent descriptions, provenance disclosure, and red assignments.
- **Integration:** extend Program Studio round-trip and compiler tests across
  simple pairs, specialist teams, councils, meta-review, and invalid
  separation.
- **Manual / device:** configure and explain the canonical team/review journey
  without consulting technical fields, then verify those fields in the audit
  view.

## Notes / open questions

Plain role names cannot replace stable role IDs in machine contracts. The UI
may offer readable display names while exact identity and provenance remain
available and authoritative.
