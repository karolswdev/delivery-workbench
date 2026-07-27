# WLA-30-01 - Contract the front-door journey

- **Project:** work-log-automation
- **Phase:** 30
- **Status:** done
- **Depends on:** none
- **Unblocks:** WLA-30-02, WLA-30-03, WLA-30-06, WLA-30-09
- **Owner:** unassigned

## Problem

Every piece of this phase — the boot command, the conversation, the atomic
apply, the workbench review, the scaffold — needs to agree on what a
"proposed setup" is before any of them is built. Without one contract, the
conversation invents its own shape, the workbench renders a second one, and
the apply surface trusts whichever arrives. Phase 26 taught the pattern:
fix the vocabulary and the refusal rules first, in a versioned envelope,
and every later story composes instead of negotiating.

The contract must also preserve the constitution under new pressure: a
conversational front door is exactly the surface most likely to blur
drafting into authorizing. The contract is where that line is drawn in
type, not in prose.

## Scope

- **In:** a versioned `delivery-workbench-setup-proposal@1` contract
  covering project identity and source intent; roadmap phases, stories,
  dependencies, acceptance and exit criteria; optional
  program/workflow/organization/rubric documents; optional `.git`-local
  driver-profile bindings (never credentials); unresolved questions; and
  per-item provenance (user answer, repository fact, or labeled
  recommendation). Explicit inertness fields on every proposal and
  preview (`starts_work: false`, `creates_grant: false`,
  `certifies: false`, `commits: false`). A documented journey state
  sequence — uninitialized → rails-ready → draft → reviewed → configured →
  grant-previewed — with no implicit transition. Documentation under
  `docs/` alongside the schema and refusal catalogue.
- **Out:** any command, skill, or UI that produces or consumes the
  contract (later stories); changing the program, grant, gate, or
  certification contracts; representing secrets or credentials in any
  field.

## Acceptance criteria

- [ ] The versioned contract exists with closed fields; unknown fields,
  missing bounds, unresolved project identity, and unsupported schema
  versions fail closed with JSON-pointer diagnostics.
- [ ] Every proposal and preview carries the four inertness fields, and a
  fitness test proves loading or validating a proposal creates no file,
  grant, run, process, or roadmap event.
- [ ] Tracked roadmap/policy content and `.git`-local driver bindings are
  distinct in type, and neither is representable as authority; project
  choice, program grant, certification, and commit are documented as
  outside proposal scope.
- [ ] Every proposal item carries provenance, and a proposal containing
  material ambiguity must represent it as an unresolved item rather than
  omitting it.
- [ ] A journey-level fixture proves the state sequence with each
  transition named, and no transition reachable implicitly.
- [ ] Canonical serialization is byte-stable: the same proposal serializes
  identically across CLI, MCP, and HTTP surfaces.

## Test plan

- **Unit:** canonical serialization; closed-field refusals; provenance
  presence; inertness fields; bounds on every list and string.
- **Integration:** the journey fixture walking all six states; a fitness
  test asserting zero filesystem/ledger side effects from load + validate.
- **Manual / device:** read the contract document cold and confirm a
  later-story implementer could build against it without asking questions.

## Notes / open questions

The temptation is to let the contract grow toward everything Program
Studio can express. Resist it: the proposal represents what the interview
can honestly elicit and the scaffold can deterministically generate.
Expert-only shapes stay in the policy JSON files the proposal embeds.
