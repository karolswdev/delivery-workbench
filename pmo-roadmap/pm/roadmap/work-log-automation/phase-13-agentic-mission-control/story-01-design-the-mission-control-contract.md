# WLA-13-01 - Design the mission-control contract

- **Project:** work-log-automation
- **Phase:** 13
- **Status:** done
- **Depends on:** Phase 12 landed (WLA-12-02, WLA-12-03, WLA-12-07)
- **Unblocks:** WLA-13-02, WLA-13-03, WLA-13-04, WLA-13-05
- **Owner:** unassigned

## Problem

Two repos are about to build one experience. Delivery Workbench
knows the roadmap truth (phases, stories, statuses, evidence, gate
verdicts); HoldSpeak knows the live session truth (which agent is
in which repo, whether it is waiting on a human) and owns the Desk
where the conveyor renders. Without a written contract between
them, the feed schema, the correlation rules, and the event
taxonomy get negotiated implicitly through whatever the first
implementation happens to emit — and the Desk's web and iOS
clients each fossilize a different accident. Phase 12's design
story caught two folklore errors before they shipped; this story
does the same job for mission control, after Phase 12's substrate
is real and can be designed against instead of guessed at.

## Scope

- **In:** A design document (working name `docs/mission-control.md`)
  that pins: (a) the state-feed schema — entities, fields, the
  versioning and stability promise, and the transport decision
  (file vs `dw state` invocation vs served endpoint — deferred
  from scaffold time); (b) the correlation model — how a HoldSpeak
  agent session (cwd, session id, awaiting_response) resolves to a
  rails repo and its in-progress story, including the ambiguous
  cases (no rails repo, multiple in-progress stories, worktrees);
  (c) the event taxonomy — which rail happenings become events
  (gate pass/refusal with rule id, evidence capture, status flip,
  contract certified), their shape, and the consent stance (events
  describe the rails, never transcript content); (d) the
  counterpart-phase seam — what the HoldSpeak-side phase may
  consume and must declare, mirroring how the Phase 12 pack
  declares its proven range; (e) re-pinned specs for stories
  02-05 against what Phase 12 actually shipped; (f) the journal
  decision (continue Phase 12's journal or charter a new one).
- **Out:** Any implementation; any HoldSpeak-side code or UI
  design; changing the Phase 12 actuator envelope.

## Acceptance criteria

- [ ] The design doc exists with schema, correlation model, event
  taxonomy, transport decision, and consent stance, each claim
  carrying the verified/cited/unverified discipline of
  `docs/riders.md`.
- [ ] Stories 02-05 are re-pinned: each cites the design-doc
  section it implements and carries testable acceptance criteria.
- [ ] The HoldSpeak counterpart phase is specced (in that repo)
  against the seam section, and this doc links to it.
- [ ] Docs-lint passes.

## Test plan

- **Unit:** n/a (design story).
- **Integration:** `pmo-roadmap/tests/docs-lint.sh`.
- **Manual / device:** verify every claimed HoldSpeak surface
  against the version the desk runs at design time; record
  versions in the doc.

## Notes / open questions

- Written at scaffold time, mid-Phase-12. If Phase 12 lands
  differently than planned, this story absorbs the delta before
  any Phase 13 implementation starts — that is its job.
