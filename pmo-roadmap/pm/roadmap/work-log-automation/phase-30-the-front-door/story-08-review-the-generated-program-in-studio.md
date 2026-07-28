# WLA-30-08 - Review the generated program in Studio

- **Project:** work-log-automation
- **Phase:** 30
- **Status:** done
- **Depends on:** WLA-30-07
- **Unblocks:** WLA-30-10
- **Owner:** unassigned

## Problem

A generated program bundle is five linked documents a newcomer has never
seen before. Program Studio already owns policy review and simulation, and
Live delivery already owns run inspection — so the generated bundle gets
reviewed *there*, as one linked object, not in a new pane. The minimum
lovable slice is a coherent overview — scope, team, reviewer independence,
rubric, capabilities, budgets, stops, driver resolution — plus whole-bundle
diagnostics and one pure simulation, ending in a handoff to the existing
exact grant preview. Visual authoring of every council seat and rubric
criterion is deliberately not this story, or this phase.

## Scope

- **In:** Program Studio opening a setup proposal's bundle as one linked
  object: roadmap scope, workflow, team and independence rules, rubric,
  requested capabilities, budgets, stops, and local driver resolution.
  Whole-bundle diagnostics from WLA-30-06, each issue linked to the source
  decision that caused it. One pure simulation of candidate selection,
  implementation, check, verdict, repair/exhaustion, and certified
  handoff, parity-checked against `dw program simulate`. Tracked policy
  and `.git`-local bindings visually distinct, both labeled
  non-authorizing. Handoff after setup-apply to the existing program
  start-plan surface — a fresh grant token, never derivable from the
  setup token.
- **Out:** saving the proposal or starting anything from the browser;
  drag-and-drop workflow authoring, council composers, rubric form
  builders; any change to the existing `#/programs` live-run route; new
  top-level navigation.

## Acceptance criteria

- [ ] Studio renders ready, invalid, missing-driver, insufficient-budget,
  and diversity-refused bundles, with each diagnostic linked to its
  source decision.
- [ ] The embedded simulation result is parity-tested against
  `dw program simulate` for the same bundle.
- [ ] Setup tokens and grant tokens are proven different, non-substitutable,
  and separately stale from this route's perspective.
- [ ] The browser can neither apply setup nor mint a grant; the
  browser-to-terminal handoff is captured as the documented flow.
- [ ] Tracked and local configuration are visually distinct and labeled
  non-authorizing.
- [ ] The existing workbench snapshot suite stays green; no duplicate run
  view or new top-level item appears.

## Test plan

- **Unit:** bundle-to-view model mapping across the five fixture states.
- **Integration:** browser snapshot and interaction tests; simulation
  parity; token non-substitutability tests; handoff capture.
- **Manual / device:** review a scaffolded bundle end to end and confirm
  the overview answers "what will run, who verifies, what can it spend,
  when does it stop" without opening raw JSON.

## Notes / open questions

The existing Studio graph and JSON views remain the expert escape hatch —
this story adds the generated-bundle overview in front of them, it does
not hide them.
