# WLA-13-05 - Prove mission control end-to-end with the Desk

- **Project:** work-log-automation
- **Phase:** 13
- **Status:** done
- **Depends on:** WLA-13-02, WLA-13-03, WLA-13-04, counterpart phase (HoldSpeak repo)
- **Unblocks:** phase close
- **Owner:** unassigned

*Re-pinned by WLA-13-01 (2026-07-04): implement against
[docs/mission-control.md](../../../../../docs/mission-control.md) §1+§3 consumed via §5; approvals ride §4 ring 2.*

## Problem

Four seams built in two repos prove nothing until one continuous
demonstration runs through all of them. This story is the joint
exit exam: the Desk conveyor rendering real roadmap state, a real
approval steering the rails, and the rails refusing dishonesty in
front of the UI that proposed it.

## Scope

- **In:** The end-to-end proof, evidence-captured: (a) a real Desk
  (web, and iOS if the counterpart phase shipped it) renders this
  repo's live phase state from the feed; (b) a live agent session
  shows up correlated to its story with its blocked state; (c) an
  approval from the Desk executes a story flip through the
  Phase 12 actuator and the conveyor moves; (d) the crown case
  again, now with a UI: an approved-but-evidence-less done flip is
  refused by the dw gate and the refusal renders as a first-class
  event on the Desk; whatever release the phase-close version
  decision names.
- **Out:** New capability in either repo (this story integrates
  and proves; gaps found here become stories, not scope creep —
  the WLA-12-08 precedent).

## Acceptance criteria

- [ ] Feed → conveyor: real phase state visible on a real Desk,
  screenshot/recording in evidence assets.
- [ ] Correlation live: a real session appears on the right story
  with the right state.
- [ ] Steering live: a Desk approval flips a story through the
  actuator; the event log and the conveyor both show it.
- [ ] The gate refusal surfaces on the Desk with its rule id,
  captured verbatim.
- [ ] Full battery, docs-lint, and the phase's release checklist
  pass.

## Test plan

- **Unit:** n/a (integration story).
- **Integration:** scripted end-to-end run in fixture repos.
- **Manual / device:** the real-Desk demonstration above, every
  leg evidence-captured.

## Notes / open questions

- iOS leg depends on the counterpart phase's scope; if it slips,
  the web Desk carries the proof and the iOS leg is a documented
  compatibility note, not a silent absence.
