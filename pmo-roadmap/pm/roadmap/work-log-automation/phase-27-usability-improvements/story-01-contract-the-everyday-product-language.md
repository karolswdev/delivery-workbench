# WLA-27-01 - Contract the everyday product language

- **Project:** work-log-automation
- **Phase:** 27
- **Status:** done
- **Depends on:** none
- **Unblocks:** WLA-27-02 through WLA-27-08
- **Owner:** unassigned

## Problem

Phase 26 proved exact, governed autonomous delivery, but its application layer
still asks people to understand protocol words such as grant, ledger, preview
token, content boundary, and certification. The Phase 26 handoff requires one
ordinary product vocabulary without blurring or replacing the exact trust
model underneath it.

This story creates the language and projection contract every later Phase 27
surface must share. It decides names and boundaries before implementation
locks accidental synonyms into more screens.

## Scope

- **In:** `docs/product-language.md`; an inventory of human-facing Workbench,
  CLI, notification, help, error, onboarding, and product-documentation
  language; canonical terms and definitions for delivery plan, team, work,
  review, decision, blocker, permission, progress, cost, and next step; rules
  for deriving an application view from canonical models; explicit
  everyday-versus-technical/audit boundaries; do/don't examples; versioned
  fixtures and an executable terminology check.
- **Out:** changing persisted or machine-contract field names; aliasing exact
  types; changing authority, evidence, eligibility, replay, or recovery
  semantics; implementing the redesigned screens; marketing voice or visual
  branding.

## Acceptance criteria

- [x] `docs/product-language.md` gives every required product concept one
  preferred name, definition, relationship, and representative good/bad
  microcopy example.
- [x] A checked-in inventory classifies every current human-facing surface as
  everyday, technical/audit, or mixed with an explicit disclosure boundary;
  no surface is silently omitted.
- [x] A versioned application-view contract says which canonical facts feed
  each product concept and forbids human renderers from recomputing
  eligibility, authority, evidence, or next-work rules.
- [x] Permission, cost, destructive effects, provenance, and refusal reasons
  remain precise in plain language, and exact source facts are reachable from
  the same task through an explicit technical/audit view.
- [x] Executable fixtures fail when reserved engineering vocabulary leaks into
  an everyday snapshot or when one product concept acquires conflicting names;
  allowlists are narrow, contextual, and reviewed.
- [x] Existing machine JSON/schema snapshots remain byte- or object-compatible;
  this contract adds a presentation projection, not a second runtime model.

## Test plan

- **Unit:** run the new product-language fixture/check suite against positive,
  negative, mixed-view, and allowed technical-view examples.
- **Integration:** run the existing schema and adapter-parity tests to prove
  that the language contract does not rename machine-facing fields.
- **Manual / device:** review the vocabulary against the seven operator
  questions in the Phase 26 handoff and trace each ordinary term to its exact
  technical source.

## Notes / open questions

The exact ordinary labels are outcomes of this story, not assumptions hidden
in later UI work. The handoff terms are the starting vocabulary. If one cannot
carry a safety-critical distinction, preserve the distinction in readable
language and document why rather than falling back to unexplained protocol
jargon.

Completed with `delivery-workbench-application-language@1`, ten canonical
product concepts mapped to nineteen existing interop models, an eighteen-row
surface inventory, eighteen reserved engineering terms, and ten versioned
positive/red fixtures. `pmo-roadmap/tests/product-language-contract.py` runs on
the Python 3.9 floor and in CI; it validates contract shape, source-model and
source-path traceability, naming uniqueness, surface boundaries, docs wiring,
and its own red cases. No runtime, persisted, CLI, MCP, HTTP, event, or
Workbench model changed.
