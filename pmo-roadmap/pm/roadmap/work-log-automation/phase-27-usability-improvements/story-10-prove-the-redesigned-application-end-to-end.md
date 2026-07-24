# WLA-27-10 - Prove the redesigned application end to end

- **Project:** work-log-automation
- **Phase:** 27
- **Status:** backlog
- **Depends on:** WLA-27-01 through WLA-27-09
- **Unblocks:** Phase 27 closeout
- **Owner:** unassigned

## Problem

Phase 27 is complete only if the redesigned application helps a person perform
whole delivery tasks from a fresh package without protocol knowledge, while an
expert can still inspect the exact record and every Phase 26 trust invariant
survives. Component screenshots and terminology counts cannot prove that.

This story composes the canonical journeys into a fresh-installed-wheel exit
exam, runs the full regression battery, and records the phase handoff without
inferring release authority.

## Scope

- **In:** a fresh-consumer usability exam under `pmo-roadmap/tests/`; installed
  wheel and vendored-source parity; healthy no-program arrival; deliberate
  setup of a delivery plan, team, independent review, limits, and permission;
  preflight; live work with failed review/repair/pass; one blocked decision;
  remaining cost/permission; stop/recovery or crash replay; completion and
  exact audit inspection; human-readable acceptance transcript and responsive
  captures; full package/UI/core/docs/parity/regression entry points;
  `evidence-story-10.md`, `final-summary.md`, and `handover.md`.
- **Out:** live-provider quality claims, external user-study claims, release,
  version bump, tag, GitHub release, PyPI/Homebrew publication, deployment,
  hosted authority, or changes made only to let the exam bypass production
  boundaries.

## Acceptance criteria

- [ ] A fresh installed wheel begins in healthy no-program state and performs
  ordinary roadmap work without creating program state, starting processes, or
  requiring setup.
- [ ] The same consumer deliberately configures and preflights optional
  delivery, understands who does/reviews/decides, sees exact effects and
  limits, and starts only after the existing separate authority checks pass.
- [ ] The run demonstrates progress, independent reject/repair/pass, a blocked
  human decision, remaining cost/permission, and a clear next step using the
  ordinary application vocabulary.
- [ ] Crash/replay or stop/recovery proves that readable state remains honest
  at effect/receipt boundaries and exact events, hashes, identities, and
  receipts remain fully inspectable.
- [ ] A person can complete the everyday exam without needing grant, ledger,
  preview-token, content-boundary, or certification vocabulary; opening the
  technical/audit view exposes those exact facts without translation loss.
- [ ] Vanilla, bounded-run, program, no-program, schema, adapter parity,
  recovery, UI, docs, package, upgrade, and distribution suites remain green
  from their public entry points.
- [ ] The final audit traces every phase exit criterion to evidence and records
  measured friction or deferrals honestly; closeout does not bump, tag,
  publish, deploy, or infer a landing decision.

## Test plan

- **Unit:** run all focused language, journey, application-view, permission,
  accessibility, and renderer suites delivered by WLA-27-01 through WLA-27-09.
- **Integration:** run the fresh-wheel usability exam plus the repository's
  mandatory core, package, autonomous-program, Workbench UI, docs, parity,
  upgrade, and distribution entry points.
- **Manual / device:** replay the acceptance transcript at narrow and wide
  viewports by keyboard, inspect exact audit facts, and record any remaining
  jargon, dead end, ambiguity, or trust-boundary surprise.

## Notes / open questions

Deterministic provider fixtures are the CI oracle, as in Phase 26. An optional
authenticated live-agent specimen may be recorded separately but cannot
replace deterministic proof or be presented as broad usability research.
