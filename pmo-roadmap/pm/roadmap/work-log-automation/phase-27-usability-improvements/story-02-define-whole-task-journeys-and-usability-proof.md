# WLA-27-02 - Define whole-task journeys and usability proof

- **Project:** work-log-automation
- **Phase:** 27
- **Status:** backlog
- **Depends on:** WLA-27-01
- **Unblocks:** WLA-27-03 through WLA-27-10
- **Owner:** unassigned

## Problem

A terminology pass can make individual labels friendlier while leaving the
overall job incomprehensible. Phase 27 needs task-shaped acceptance or each
screen will optimize its own fragment and the user will still have to assemble
the delivery model mentally.

This story turns the Phase 26 handoff questions into deterministic journeys
and fixtures before UI implementation. The same journeys become design
constraints, regression inputs, and the final exit exam.

## Scope

- **In:** `docs/usability-journeys.md`; versioned fixtures under
  `pmo-roadmap/tests/fixtures/usability/`; journeys for healthy first arrival,
  deliberate capability choice, delivery-plan setup, team/review setup,
  preflight, live progress, failed review and repair, blocked human decision,
  remaining permission/cost, stop/revoke, crash recovery, completion, and
  technical inspection; a small deterministic journey validator; a recorded
  baseline of current friction.
- **Out:** production UI changes; model-generated usability scoring; remote
  analytics or recording; pretending automated checks replace human review;
  changing canonical workflow or authority semantics to simplify a journey.

## Acceptance criteria

- [ ] Every journey names its starting state, user question, visible facts,
  bounded actions, success outcome, refusal/recovery outcome, and exact
  technical-details escape hatch.
- [ ] Fixtures cover vanilla, bounded-run, and optional program states without
  implying that a program is required or that one capability tier silently
  upgrades to another.
- [ ] The baseline records steps, decisions, exposed engineering terms, dead
  ends, and context switches for the current application; later stories can
  demonstrate a real task improvement rather than a subjective restyle.
- [ ] Each of the seven Phase 26 handoff questions is answered by at least one
  journey, and each Phase 27 screen slice names the journeys it owns.
- [ ] A deterministic validator rejects incomplete fixtures, missing safe
  exits, invented authority, inaccessible technical details, and ambiguous
  expected next steps.
- [ ] Journey fixtures are reusable by Workbench UI tests and the fresh-wheel
  exit exam rather than re-described separately in each test.

## Test plan

- **Unit:** run the journey-schema validator against valid fixtures and
  intentional red fixtures for hidden authority, missing recovery, and
  ambiguous outcomes.
- **Integration:** load every fixture through the canonical core/read models
  and prove it represents a reachable product state.
- **Manual / device:** perform the baseline journeys in the current Workbench
  at wide and narrow widths and record observable friction without changing
  production behavior.

## Notes / open questions

The fixtures describe observable tasks, not a required page layout. Later
stories may improve the interaction design as long as the same state, trust
boundary, and outcome remain provable.
