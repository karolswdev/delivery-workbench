# WLA-30-06 - Validate the whole bundle before runtime

- **Project:** work-log-automation
- **Phase:** 30
- **Status:** backlog
- **Depends on:** WLA-30-01
- **Unblocks:** WLA-30-07
- **Owner:** unassigned

## Problem

Phase 29's real run burned grants discovering, at live verdict time, what
static analysis could have refused at validation time: rubric mechanical
facts no workflow check produces, budgets that cannot cover the team the
organization requires, workflow nodes the compiler accepts but the
conductor cannot conduct. `dw program validate` checks documents; it does
not check the *bundle*. Before a scaffold generates policy for newcomers,
validation must preflight the complete linked object — program, workflow,
organization, rubric, roadmap scope, and local driver roster — so a
generated setup that validates is a setup that runs.

## Scope

- **In:** whole-bundle validation in `dw program validate` (CLI, MCP,
  HTTP): every rubric mechanical fact traceable to a reachable check or
  trusted rail in the bound workflow; budgets covering minimum team
  cardinality, verifier separation, provider-diversity requirements,
  workflow fan-out, and at least one complete green route;
  compiler/conductor node-support parity including checkpoint nodes —
  accepted-but-unconductable is rejected before grant planning; driver
  validation reporting available profiles, adapter kind and version,
  provider family, capabilities, principal and workspace constraints, and
  bounded model alias with credentials structurally impossible to emit;
  refusal of tracked policy naming executables, arbitrary argv, arbitrary
  environment, or undeclared driver flags; source-and-pointer diagnostics
  with remediation on every refusal.
- **Out:** fixing the Phase 29 defects' runtime behavior (already
  refused correctly at runtime — this story moves detection earlier); the
  scaffold itself (WLA-30-07); any write — validation stays pure.

## Acceptance criteria

- [ ] A cross-product fixture suite proves fact/check matching, team-size
  and diversity coverage, budget envelopes, and node-support parity, with
  each refusal carrying source, pointer, and remediation.
- [ ] The Phase 29 runtime failures that motivated this story are encoded
  as fixtures and are now rejected at validation, before any grant plan.
- [ ] Driver diagnostics never contain credentials, proven by a redaction
  test over adversarial roster content.
- [ ] Tracked policy naming executables, argv, environment variables, or
  undeclared flags refuses with pointer diagnostics.
- [ ] Validation is pure: no policy, roster, grant, run, or roadmap state
  changes, proven by side-effect assertions.
- [ ] CLI, MCP, and HTTP validation results are canonical-byte equivalent
  for the same bundle.

## Test plan

- **Unit:** each cross-check in isolation on minimal fixtures.
- **Integration:** the cross-product suite; the Phase 29 regression
  fixtures; transport parity captures; the packaged autonomous-program
  suite green.
- **Manual / device:** validate the real Phase 29 bundle
  (`pm/programs/wla-29-08-first-real-run.json` and its links) and confirm
  the diagnostics would have saved the grants they cost.

## Notes / open questions

The green-route proof is the subtle one: it needs the workflow graph, the
budget arithmetic, and the org constraints simultaneously. Reuse the
existing pure simulation machinery rather than building a second
reachability engine; if simulation cannot yet answer it, extend
simulation, not validate.
