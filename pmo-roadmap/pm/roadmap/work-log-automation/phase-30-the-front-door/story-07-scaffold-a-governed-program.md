# WLA-30-07 - Scaffold a governed program

- **Project:** work-log-automation
- **Phase:** 30
- **Status:** done
- **Depends on:** WLA-30-06
- **Unblocks:** WLA-30-08
- **Owner:** unassigned

## Problem

Program configuration is the hardest artifact in the system: four linked
policy documents plus a driver roster, hand-written, with no generator and
no guide. Phase 29's one real run took thirteen grants partly because the
bundle was authored by trial. For the front door to mean anything, the
interview's answers — who implements, who verifies, what proves the work,
how much autonomy — must compile deterministically into a complete,
validated, *safe-by-default* bundle: checkpointed, no-commit, cross-provider
where the roster allows it, budgets derived from scope rather than copied
from an example.

The generator is a compiler, not an author: same normalized answers plus
same repository facts, byte-identical bundle. It never accepts agent-emitted
commands or unchecked JSON as behavior, and its output stays inside the
unsaved proposal until the one setup approval.

## Scope

- **In:** `dw program scaffold` compiling typed setup choices into linked
  program, workflow, organization, rubric, and local-roster proposals.
  Defaults: checkpointed mode; no commit, push, merge, release, deploy,
  publish, arbitrary-shell, or arbitrary-network authority; an
  implementer, an independent verifier, declared checks, a rubric-bound
  verdict, a finite repair route, and a certified handoff. Budgets derived
  from scope, team cardinality, workflow envelopes, retry ceilings, and
  requested mode. Driver selection only from validated local profiles,
  preserving the adapter's bounded model alias as configuration — never
  inferring provider family or model identity from a display name.
  Refusal over best-effort: unsatisfied diversity, missing verifier,
  unknown check, or incomplete budget refuses with diagnostics.
- **Out:** applying anything (the bundle rides the WLA-30-04 lease);
  new adapters or roster mutation; expert shapes the interview cannot
  elicit (multi-council debates, custom aggregation) — those remain
  hand-authored JSON the proposal can embed.

## Acceptance criteria

- [ ] Determinism: identical normalized answers and repository facts
  produce byte-identical bundles across repeated runs.
- [ ] The default bundle is checkpointed and contains none of the excluded
  authorities, proven by capability-set assertions.
- [ ] Budgets are derived — a fixture with a different scope/team shape
  produces correspondingly different budgets, and no budget is a copied
  constant from an example file.
- [ ] Golden bundles exist and validate (WLA-30-06) for: a greenfield
  build, an existing-project maintenance program, a cross-provider
  implement/review cell, and a single-provider refusal.
- [ ] Compiler simulation over each golden bundle shows one bounded green
  route and typed failure routes.
- [ ] Scaffolding writes nothing: mutation tests prove no file appears
  outside the in-memory/proposal representation.

## Test plan

- **Unit:** answer normalization; budget derivation arithmetic; driver
  profile selection and refusal cases.
- **Integration:** golden-bundle determinism across runs; full WLA-30-06
  validation of every golden; simulation captures; no-write mutation
  tests.
- **Manual / device:** scaffold a bundle from a real interview and compare
  it side by side with the hand-written Phase 29 bundle — the generated
  one should be visibly safer and simpler.

## Notes / open questions

The interview-to-answers normalization boundary lives here, not in the
skill: Scope-Chat elicits, this story defines the closed set of typed
choices scaffolding accepts. Keeping that set small is the design work —
every added knob is a knob the validator, the Studio review, and the exam
must also carry.
