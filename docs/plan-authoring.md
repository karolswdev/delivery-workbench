# Delivery-plan authoring

Program Studio's default plan and work-flow editor is organized around seven
delivery decisions:

1. What will be delivered?
2. How should work move?
3. What must be true before work can pass?
4. When should a person decide?
5. What happens when work does not pass?
6. When must delivery stop?
7. How much work may this delivery use?

The sequence is an application view over the existing exact program and
work-flow documents. It does not introduce another saved format, compiler, or
runtime meaning.

## Shared authoring model

`delivery-workbench-delivery-plan-authoring` schema version 1 is built by
`plan_authoring.build_delivery_plan_authoring`. Program Studio attaches it as
`authoring` to both selected-document reads and save previews.

Its only inputs are already-canonical Program Studio facts:

| Input | Use in the authoring view |
|---|---|
| exact source document | scoped values and targeted editable fields |
| exact graph | ordered work, review, decision, recovery, and finite-limit facts |
| shared validation result | decision-shaped corrections |
| graph/config round-trip result | lossless Technical-details assurance |

The model contains:

- the seven ordered sections and the question each answers;
- plain-language facts and source-backed items for each decision;
- one readable summary covering scope, flow, quality, decisions, recovery,
  stops, and limits before save;
- corrections grouped by affected decision;
- exact diagnostic source, pointer, code, and target inside
  `technical_details`;
- progressive flags for hierarchical work flows, bounded repair, discussion
  cells, exact conditions, graph editing, and JSON import/export;
- explicit edit-safety and no-side-effect facts.

The model groups and explains existing facts. It does not decide eligibility,
permission, review outcomes, evidence validity, or next work.

## Default authoring flow

Explicit family routes remain:

```text
#/program-studio/program/<name>
#/program-studio/workflow/<name>
#/program-studio/organization/<name>
```

Program and work-flow routes now open on **Plan**. A section rail follows the
seven decisions above, and the current section combines:

- its delivery question and source-backed answer;
- editable fields owned by that decision;
- a plain correction when the current source is incomplete;
- examples that explain a simple, repair-capable, and detailed delivery;
- a persistent **Review before save** summary.

Program plans can edit scope, work routes, phase decisions, stop conditions,
and finite limits without beginning from persisted object order. Work flows
can edit work inputs and ordinary steps—do work, run a check, review an
outcome, or ask for a decision—using delivery language.

Nested work flows, bounded repetition, multi-perspective discussion, exact
conditions, source identifiers, and raw configuration are not removed. They
live under **Technical details**, whose graph and lossless-configuration modes
edit the same in-memory source document.

Organization routes use the parallel
[Team and review design](./team-review.md) application view. It opens on work
responsibilities, independent review, contested decisions, escalation, and
review-of-review while preserving the same lossless Technical-details
boundary.

## Review a generated setup bundle

A proposal produced by `dw program scaffold` opens at:

```text
?proposal_file=<repository-relative-file>#/program-studio/bundle
```

This route reviews the five generated documents as one bundle. It shows the
selected roadmap scope, workflow, implementer and verifier seats, independence
rules, rubric criteria and their producing checks, requested capabilities,
budgets, stop conditions, and local driver availability. The overview uses
product language first. The existing graph and exact JSON views remain the
expert path for saved policy documents.

`GET /api/setup/bundle?proposal_file=...` loads the proposal without staging its
contents. It calls `validate_program` with the proposal's `bundle_documents` and
`roadmap_document`; Program Studio does not maintain a second whole-bundle
validator. Each diagnostic keeps the validator's source and JSON Pointer and
links to the affected overview section. The route also returns the pure
`simulate_scaffold_proposal` result, including the green, repair, failure, and
budget-exhaustion routes.

Tracked policy and `.git`-local driver bindings are shown separately under the
same "configuration, not permission" label used by adoption review. Neither
kind of configuration authorizes a run. This route accepts only
`proposal_file`: it does not accept or return a setup lease or program start
token, and it has no apply or grant control.

After `dw setup apply` saves the reviewed bundle, Program Studio hands the next
act back to the terminal:

```text
.githooks/dw program plan <program-slug>
```

That command is the existing separate program grant preview. The browser does
not run it or mint a grant.

The setup journey and proposal contract are documented in
[Front-door setup proposal](./setup-proposal.md).

## Lossless editing and safe refusal

The browser always edits a clone of `studio.raw`; it never reconstructs a
document from the readable summary. Targeted plan edits change only their
owned fields. Unedited fields, layout, exact conditions, input/output
expressions, and imported content remain in that source object.
Renaming a work route, work input, or work step also carries its declared
follow-up, parameter, dependency, route, artifact, fact, verdict, and layout
references so the intended edit does not strand exact configuration.

Every preview rebuilds the existing shared models:

```text
source document
  → existing family validator/compiler
  → exact graph and simulation
  → graph/config round-trip
  → delivery-plan authoring view
```

A valid imported document therefore exports with the same semantic and layout
identity. An unknown field remains present and is reported under Technical
details; because the existing validator rejects it, save remains unavailable.
The editor neither drops the field nor guesses how to translate it.

## Decision-shaped validation

Ordinary validation does not lead with source pointers or internal rule names.
Each refusal states:

- the affected delivery decision;
- what downstream behavior cannot be determined safely;
- the correction;
- a link back to the relevant plan section or work step.

The exact source, pointer, code, message, and remediation remain available in
the adjacent **Technical details** disclosure. Selecting an exact diagnostic
opens the graph field when one exists or the lossless configuration otherwise.

## Save boundary

Drafting, switching sections, trying a flow, checking, importing, exporting,
and abandoning a draft are browser-local or read-only. They start no work and
write no plan, roadmap, permission, run, process, observer, notification, or
network state.

**Review save** still calls the existing Program Studio preview endpoint. The
ordinary review states that confirming changes one named file and starts no
work. The exact path, fingerprint, and diff are disclosed only under
**Technical details**. Apply still requires the fresh fingerprint and can
write only that one direct-contained tracked JSON document.

Saving a delivery plan remains configuration. It provides no permission and
does not start delivery.

## Verification

Run the focused model, HTTP, and viewport proof with:

```bash
python3 pmo-roadmap/tests/dw-core-tests.py ProgramStudioTest
bash pmo-roadmap/tests/workbench-explorer.sh
bash pmo-roadmap/tests/workbench-ui-smoke.sh
```

The model tests cover the seven-section order, readable summary, advanced
disclosure, exact semantic/layout round trips, invalid decision mapping,
unknown-field preservation, and false effect flags. The explorer proves the
same model through the installed HTTP adapter. The viewport suite renders
valid program, work-flow, and team/review plans, an invalid preserved draft,
corrections, simulation, validation, and exact Technical-details modes at
1440×900 and 390×844.
