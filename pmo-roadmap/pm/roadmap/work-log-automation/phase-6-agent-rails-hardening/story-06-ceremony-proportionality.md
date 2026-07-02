# WLA-6-06 - Right-size ceremony and unify template canon

- **Project:** work-log-automation
- **Phase:** 6
- **Status:** done
- **Depends on:** WLA-6-03, WLA-6-05
- **Unblocks:** none
- **Owner:** unassigned

## Problem

The framework's own dogfood history proves the ceremony is heavy enough to
get skipped: the prescribed same-commit cadence was abandoned for one giant
batched working tree. A one-line docs fix outside `pm/` costs the same
seven-rule ritual as shipping a story. Meanwhile the canon contradicts
itself and leaks author-specific content into every consumer install:

- Status vocabulary is defined three different ways (roadmap-builder §2.1
  vs `project-README.md.tmpl` vs PMO-CONTRACT rule 2, which omits
  `blocked`).
- `story.md.tmpl` and `phase-status.md.tmpl` omit sections that
  roadmap-builder §2 declares required, while the builder prompt says to
  follow both "exactly."
- Canonical templates tell consumers' agents to honor the author's private
  `~/.claude` memory keys, embed the Pantrybot worked example, carry a dead
  `https://github.com/` link, and hardcode `~/dev/reusable-processes/`
  paths that exist on no consumer machine.
- The framework README claims "no external runtime dependencies; pure
  bash" while shipping a 1,200-line Python CLI.
- `final-summary.md` requires eight sections that mostly restate the phase
  status and evidence links; the "Integration / Cypress" test-plan heading
  is a web-app vestige that all 31 dogfood stories carry as `n/a`.

## Scope

- **In:** Tiered contract: the full contract remains required for commits
  that touch `pm/roadmap/**` or flip story status; commits that do not may
  use a short-form contract (stamped facts plus the no-bypass rule),
  configurable per project with the conservative default documented.
  Single status vocabulary defined once in roadmap-builder §2 and
  referenced — never restated — by every other template, checked by
  `dw check` against the same constant the gate uses. Template
  reconciliation: `.tmpl` files and roadmap-builder §2 agree; the builder
  names one winner. De-personalization: private memory instructions and
  machine paths removed from canon; Pantrybot moves to
  `pmo-roadmap/templates/examples/`; links fixed; the runtime-dependency
  claim corrected to name python3. Lighter closure: `final-summary.md`
  slims to four sections (outcome vs exit criteria, evidence index,
  surprises, handoff); the test-plan heading becomes
  "Integration" with project-appropriate examples.
- **Out:** Removing the contract concept or weakening rules 6/7; changing
  the story/evidence pairing model; renaming existing dogfood artifacts to
  match the slimmed templates (grandfathered).

## Acceptance criteria

- [ ] A docs-only commit outside `pm/roadmap/**` passes the gate with the
  short-form contract, and a story-flipping commit with only a short-form
  contract is blocked (both tested).
- [ ] Exactly one file defines the status vocabulary; `grep -r` across
  templates finds references, not restatements, and `dw`/gate/`dw check`
  consume the same list (asserted by the parity suite).
- [ ] No canonical template or builder doc contains `~/.claude`,
  `reusable-processes`, Pantrybot content, or placeholder links (asserted
  by a lint script run in CI).
- [ ] `story.md.tmpl` and `phase-status.md.tmpl` match roadmap-builder §2
  section-for-section.
- [ ] The framework README's dependency and validation sections are
  accurate for the post-Phase-6 toolchain.

## Test plan

- **Unit:** Vocabulary-constant parity assertions in the `dw_pmo` suite.
- **Integration / Cypress:** Gate tests for both contract tiers; the new
  canon-lint script in `.github/workflows/validation.yml`.
- **Manual / device:** Fresh install into a temp repo; read the rendered
  templates as a consumer and confirm nothing author-specific remains.

## Notes / open questions

The tier boundary (touches `pm/roadmap/**` or flips status) is deliberately
mechanical so the gate can decide the required tier itself and tell the
agent which one it expects. If a project wants full ceremony everywhere,
one config line restores it.
