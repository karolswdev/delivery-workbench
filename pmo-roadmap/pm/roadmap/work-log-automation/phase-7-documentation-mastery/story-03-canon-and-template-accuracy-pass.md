# WLA-7-03 - Canon and template accuracy pass

- **Project:** work-log-automation
- **Phase:** 7
- **Status:** done
- **Depends on:** WLA-7-01
- **Unblocks:** WLA-7-07
- **Owner:** unassigned

## Problem

The canon (PMO-CONTRACT.md, roadmap-builder.md) and the shipped
templates are the documents agents obey. They were hardened in Phase
6, but the audit must verify them against everything Phases 5 and 6
actually shipped (tiers, captures, workbench, remediation exemption,
adoption bridge) and against each other — canon drift is agent drift.

## Scope

- **In:** Line-by-line accuracy pass over both canon docs, template
  reconciliation (story/phase/README/evidence templates and examples
  match what generators emit today), doc-parity checks extended where
  canon states machine-enforced facts, and CLAUDE-snippet/agent-docs
  wording review.
- **Out:** Rule changes (this is an accuracy pass, not a redesign).

## Acceptance criteria

- [ ] Every mechanically-enforced statement in the canon names its
  enforcing rule id or test, and a doc-parity test covers each newly
  cited pairing.
- [ ] Generated scaffold output is byte-covered by the documented
  templates (captured diff of generator output vs template).
- [ ] The worked examples reflect contract v2, tiers, and captures.
- [ ] `canon-lint.sh` extended with any new forbidden-drift patterns
  the pass discovers.

## Test plan

- **Unit:** extended doc-parity tests in the core suite.
- **Integration:** canon-lint plus scaffold-vs-template captures.
- **Manual / device:** full read of both canon docs as an operator.
