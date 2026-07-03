# Phase 8 - Remote Verification and Adoption

**Last updated:** 2026-07-03.

## Goal

Make the gate's guarantees hold beyond the local clone: a range verifier that re-checks gate rules over pushed commits, CI wiring that enforces it on every PR, and a real external adoption exercising the rails end-to-end with friction folded back into the framework.

## Scope

- **In:** A remote-verification design contract
  (`docs/remote-verification.md`), a `dw verify` subcommand
  re-deriving the structurally-checkable gate rules over commit
  ranges, a CI job enforcing it on pushes and PRs, one real external
  adoption run through the documented three-command path with a
  severity-tagged friction log, and the fix-now slice of that
  friction folded back into code, scripts, and docs.
- **Out:** Server-side pre-receive hooks (unavailable on GitHub-hosted
  repos), publishing contract archives remotely, distribution work
  (Homebrew/pipx), multi-contributor adoption trials, marketplace
  composite actions.

## Exit criteria (evidence required)

- [ ] Every gate rule id is classified for remote verifiability in
  `docs/remote-verification.md`, and `dw verify` implements the
  re-derivable set with the local gate's rule ids.
- [ ] `dw verify` passes over this repository's full history and
  fails, with named rules, on a fixture history containing a
  smuggled (`--no-verify`-style) commit.
- [ ] CI runs history verification on PRs and pushes; a red-path run
  proves it blocks.
- [ ] An external repository reached doctor-green through the
  documented adoption path and shipped one gated story; its friction
  log is fully triaged with every fix-now item proven fixed.

## Story status

| ID | Story | Status | Story file | Evidence |
|---|---|---|---|---|
| WLA-8-01 | Define the remote verification contract | done | [story-01-define-the-remote-verification-contract](./story-01-define-the-remote-verification-contract.md) | [evidence-story-01](./evidence-story-01.md) |
| WLA-8-02 | Implement dw verify for commit ranges | done | [story-02-implement-dw-verify-for-commit-ranges](./story-02-implement-dw-verify-for-commit-ranges.md) | [evidence-story-02](./evidence-story-02.md) |
| WLA-8-03 | Wire remote verification into CI | backlog | [story-03-wire-remote-verification-into-ci](./story-03-wire-remote-verification-into-ci.md) | - |
| WLA-8-04 | Adopt Delivery Workbench in an external repository | backlog | [story-04-adopt-delivery-workbench-in-an-external-repository](./story-04-adopt-delivery-workbench-in-an-external-repository.md) | - |
| WLA-8-05 | Fold adoption friction back into the framework | backlog | [story-05-fold-adoption-friction-back-into-the-framework](./story-05-fold-adoption-friction-back-into-the-framework.md) | - |

## Where we are

WLA-8-02 shipped: `dw verify` re-derives the structural rules over
commit ranges (rule ids shared with the gate, epoch scoping, exit
0/1/2, porcelain), the commit-msg hook stamps `PMO-Bundle:` from
BUNDLE-OK, and the claim is held by 13 new unit cases plus the
verify-range.sh fixture suite — the repo's own history verifies
clean (27 commits, 17 pre-epoch skipped). Next: WLA-8-03 wires the
verifier into CI; WLA-8-04 (external adoption) remains independently
startable.

## Active risks

| Risk | Likelihood | Mitigation | Stop signal |
|---|---|---|---|
| Historical commits violate rules the verifier checks, forcing grandfather logic | medium | Design doc owns commit-scoping rules; verifier stays mechanism, policy lives in the contract | Verifier needs per-sha exception lists to pass main |
| Bundle consent is invisible remotely, weakening atomicity verification | medium | WLA-8-01 decides trailer-based bundle rationale before implementation | Multi-flip commits must be whitelisted by hand |
| External adoption target unavailable or too trivial to surface friction | low | Fall back to the Phase 7 clone fixture with real history | Friction log empty on a repo that clearly differs from this one |

## Decisions made (this phase)

- 2026-07-03 - Phase scaffolded with `dw phase create` - keeps roadmap structure consistent - CLI.
- 2026-07-03 - Verification thread (01→02→03) and adoption thread (04→05) run as parallel tracks - shortens the phase without coupling unrelated work - roadmap design.
- 2026-07-03 - Pre-receive enforcement is out of scope - GitHub-hosted repos cannot run server hooks; CI is the enforcement point - constraint.
- 2026-07-03 - Bundle rationale becomes a `PMO-Bundle:` trailer stamped by commit-msg when BUNDLE-OK authorizes a multi-flip - makes atomicity fully re-derivable remotely; no multi-flip commits predate it, so history stays compatible - WLA-8-01 (`docs/remote-verification.md`).
- 2026-07-03 - Contract archives stay local-only in v1 - the remotely-valuable facts are structural and already in the tree; publishing full contract text adds noise for marginal gain - WLA-8-01 (`docs/remote-verification.md`).
- 2026-07-03 - Verification epoch is auto-detected as the first digest-trailer commit (`faa7de6` here), pinnable via `--epoch`/`PMO_VERIFY_EPOCH`; per-sha exception lists rejected - policy in configuration, mechanism in the verifier - WLA-8-01.

## Decisions deferred

- Whether contract archives become remotely portable (notes ref or tracked dir) - trigger: a multi-machine audit requirement materializes - default is local-only (decided for v1 in WLA-8-01).
- Evidence-run presence as a remote rule (flip must ship an exit-0 captured run) - trigger: after WLA-8-02 lands and pre-capture epochs are understood - default is not-in-v1.
