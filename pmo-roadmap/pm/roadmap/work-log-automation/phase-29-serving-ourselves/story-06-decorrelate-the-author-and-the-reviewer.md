# WLA-29-06 - Decorrelate the author and the reviewer

- **Project:** work-log-automation
- **Phase:** 29
- **Status:** done
- **Depends on:** -
- **Unblocks:** WLA-29-08
- **Owner:** unassigned

## Problem

The organization layer already models roles, pools, duties, and separation:
an implementer's work is reviewed independently, and the assignment machinery
enforces that they are different agents. But two different agents on the same
model family share the same blind spots, and a reviewer that thinks exactly
like the author approves exactly what the author got wrong. The studied
prototype makes provider diversity a first-class stage choice for this
reason, and it is cheap insurance we cannot currently express: no
organization policy can say "the reviewer must not share the implementer's
provider family."

## Scope

- **In:** a provider-family attribute on the driver adapter roster (claude,
  codex, pi, fixture — declared, not inferred); an organization-policy rule
  expressing diversity requirements between named role pairs (at minimum
  implementer/reviewer), compiled and validated like existing separation
  duties; enforcement at assignment time — an assignment violating the rule
  is never made, and an organization whose rosters cannot satisfy it refuses
  at plan/validate time with a diagnostic naming the missing family, not at
  mid-run dispatch; surfacing in the plain-language team/review views so an
  operator sees "reviewed by a different model family" in product terms;
  fixture adapters carrying declarable families so the exam suite can prove
  both satisfaction and refusal.
- **Out:** any default-on behavior — existing organizations without the rule
  are untouched and stay valid; scoring or ranking providers; diversity
  requirements beyond family (version pinning, temperature, and similar stay
  out); changing separation-of-duties semantics for agents on one family
  when no rule is declared.

## Acceptance criteria

- [ ] Provider family is a declared adapter attribute; every shipped adapter
  declares one, and an adapter without a declaration cannot satisfy a
  diversity rule (fail closed, not assumed distinct).
- [ ] The organization schema accepts a diversity rule between role pairs,
  validation rejects rules naming unknown roles, and existing organization
  fixtures compile unchanged.
- [ ] With the rule present, no assignment ever pairs implementer and
  reviewer from one family — proven across the assignment property tests,
  including pools where only one valid pairing exists.
- [ ] An unsatisfiable roster refuses at validate/plan time with a diagnostic
  naming the rule and the missing family; nothing discovers the problem
  mid-run.
- [ ] The team and review presentation surfaces state the diversity rule and
  its satisfaction in plain product language, snapshot-pinned like the other
  Phase 27 copy.
- [ ] The packaged exam gains one organization exercising the rule end to
  end: a satisfying assignment and a refused unsatisfiable variant.

## Test plan

- **Unit:** schema validation; assignment enforcement including
  single-pairing corners; fail-closed undeclared-family behavior.
- **Integration:** `dw evidence capture` of `dw program validate` on a
  satisfying and an unsatisfiable fixture organization; packaged-exam leg.
- **Manual:** read the team view for the fixture organization and confirm the
  rule reads as product language, not protocol vocabulary.

## Notes / open questions

Family is declared on the adapter rather than inferred from binary names
because inference is a guess and the rule fails closed on guesses. If a
future adapter proxies multiple families, the declaration moves to the
logical profile; that corner is recorded, not solved.

This story has no dependency on the knowledge stories and can proceed in
parallel with WLA-29-02 through WLA-29-05.

Delivered out of sequence (after WLA-29-03, before WLA-29-04/05) by the
recorded scheduling decision in the phase status. Implemented as declared
`provider_family` on the adapter roster, optional named `diversity` rules
(`provider-family` kind, exactly two roles, unknown roles rejected) in
`program_organization.py`, enforcement at assignment/replacement/candidate
search plus plan- and start-time diagnostics via
`provider-diversity-unsatisfied`, fail-closed undeclared families, and
assignment receipts recording the pairing. Product language: "reviewed by a
different model family", snapshot-pinned. Evidence carries the full
packaged autonomous exam on the merged tree (complete, 203 ledger events)
and the two focused enforcement tests verbatim; the exam's own JSON output
exceeded the evidence capture bound and is truncated there, so the focused
second run is the readable proof. Suite 571 → 573 green.
