# Whole-task usability journeys

Delivery Workbench's usability contract is a set of observable delivery tasks,
not a prescribed page layout and not a model-generated score. It fixes the
questions, facts, bounded choices, outcomes, safe exits, and exact-detail path
that a later interface must preserve while it improves the interaction.

The contract sits on top of the
[everyday product language](./product-language.md). It changes no workflow,
eligibility, review, permission, cost, or next-work semantics. Every displayed
fact names a canonical model already declared by
[`docs/interop.md`](./interop.md), and every mutation names an existing
preview/apply boundary.

## Versioned sources

| Source | Purpose |
|---|---|
| [`journeys-v1.json`](../pmo-roadmap/tests/fixtures/usability/journeys-v1.json) | The 13 whole-task journeys, operating tiers, canonical action sources, seven operator questions, and screen ownership |
| [`states-v1.json`](../pmo-roadmap/tests/fixtures/usability/states-v1.json) | Reachable canonical starting and exact-detail states, model paths, routes, and wide/narrow capture IDs |
| [`baseline-v1.json`](../pmo-roadmap/tests/fixtures/usability/baseline-v1.json) | Reproducible observations of the application before the Phase 27 screen redesign |
| [`red-fixtures-v1.json`](../pmo-roadmap/tests/fixtures/usability/red-fixtures-v1.json) | Planted incomplete, unsafe, ambiguous, inaccessible, and authority-invalid journeys |
| [`usability-journey-contract.py`](../pmo-roadmap/tests/usability-journey-contract.py) | Deterministic schema, source, reachability, language, ownership, baseline, and red-fixture validation |

All files use schema version 1. A new required journey field, changed tier
meaning, changed operator question, or changed outcome meaning requires a new
schema version. Additive baseline observations may remain in v1 when they do
not change the task contract.

## Operating tiers

| Tier ID | Product choice | Entry rule |
|---|---|---|
| `vanilla` | Everyday roadmap | The healthy default. It is usable immediately and creates no optional delivery state. |
| `bounded-run` | One bounded delivery | Optional. It starts only after the exact work and limits are reviewed and the separate start is confirmed. |
| `program` | Optional delivery program | Optional. Configuration, review, and the separate start are all deliberate; visiting setup or saving a draft starts nothing. |

The journey contract never treats `program` as required setup. An action that
changes tier must name the canonical start source and require explicit
confirmation. A renderer may recommend a tier, but it may not select or start
one silently.

## Required journey shape

Every journey has exactly these task elements:

1. A reachable `starting_state` and the operating tiers in which the journey
   applies.
2. One plain `user_question` plus the Phase 26 operator questions it answers.
3. Non-empty `visible_facts`; each fact uses a v1 everyday concept and names
   the canonical model that supplies it.
4. Non-empty `bounded_actions`; each action states its exact effect, available
   tier, resulting tier, confirmation requirement, and existing authority
   source.
5. One observable `success_outcome` and exactly one expected next step.
6. A `refusal_recovery` outcome that states what remains unchanged, keeps a
   safe exit, and names exactly one next step.
7. An explicit **Technical details** path, its canonical sources, and a
   labelled return to the ordinary task.
8. The Phase 27 screen slices that own it and both downstream consumers:
   `workbench-ui` and `fresh-wheel-exit-exam`.

Read-only inspection is represented explicitly and carries no mutation
authority. Draft saves use the existing Studio mutation boundary. Bounded
delivery and optional-program starts and controls use their existing exact
plan/preview and result models. A friendly button, notification, route, or
renderer is never an authority source.

## Journey catalog

| Journey | Starting state and tier | User question | Successful handoff |
|---|---|---|---|
| `healthy-first-arrival` | `everyday-ready` · `vanilla` | Is this repository ready, and what useful work can I do now? | Open current ordinary work without optional setup. |
| `deliberate-capability-choice` | `capability-choice` · all three choices visible | How much coordination do I want for this delivery? | Keep the selected tier explicit; any higher tier has its own confirmed start. |
| `delivery-plan-setup` | `plan-draft` · `program` | What will be delivered, in what order, and where should work stop? | Save only the reviewed draft, then set up the team and review. |
| `team-review-setup` | `team-review-draft` · `program` | Who will do, review, and decide on this work? | Preserve readable responsibility and independent review, then preflight. |
| `preflight` | `preflight-ready` · `bounded-run` | Is this delivery ready to start, and what exactly may it do? | Start the exact reviewed delivery once, or return without starting. |
| `live-progress` | `bounded-active` · `bounded-run` | What is happening now, what passed, and what happens next? | Advance at most one reviewed step, then show the updated canonical state. |
| `failed-review-and-repair` | `repair-needed` · `bounded-run` | What failed, what can repair it, and what remains safe? | Run only the reviewed repair and require the failed check to pass. |
| `blocked-human-decision` | `human-decision-needed` · `bounded-run` | Who must decide, which choices are valid, and what follows each choice? | Apply one exact response and recalculate the canonical next step. |
| `remaining-permission-and-cost` | `program-active` · `program` | What may this delivery still change or spend? | Distinguish allowed, consumed, remaining, forbidden, unknown, and not-applicable facts before action. |
| `stop-and-revoke` | `program-active` · `program` | How do I pause safely or permanently stop this delivery? | Apply the selected stop once and show its consequence. |
| `crash-recovery` | `bounded-active` · `bounded-run` | After interruption, what completed, what may resume, and what happens next? | Separate completed, incomplete, and eligible work before a deliberate resume. |
| `completion` | `delivery-complete` · `program` | What finished, what passed, and is there more work? | Distinguish work-item completion from whole-delivery completion and name the next work or finish path. |
| `technical-inspection` | `bounded-active` · `bounded-run` | How can I inspect the exact record without losing the delivery summary? | Inspect or copy the exact source, then return to the same ordinary task context. |

The success handoff is not the only valid ending. Every row also has a
versioned refusal/recovery outcome and safe leave path in the JSON contract.

## Seven-question coverage

| Phase 26 operator question | Journeys that directly answer it |
|---|---|
| What are we delivering? | `healthy-first-arrival`, `deliberate-capability-choice`, `delivery-plan-setup`, `preflight`, `live-progress`, `completion` |
| Who is doing and reviewing it? | `team-review-setup`, `preflight`, `live-progress` |
| What passed? | `live-progress`, `failed-review-and-repair`, `crash-recovery`, `completion`, `technical-inspection` |
| What is blocked? | `live-progress`, `failed-review-and-repair`, `blocked-human-decision`, `stop-and-revoke`, `crash-recovery` |
| Who needs to decide? | `team-review-setup`, `live-progress`, `blocked-human-decision` |
| What may the delivery still change or spend? | `deliberate-capability-choice`, `delivery-plan-setup`, `preflight`, `live-progress`, `remaining-permission-and-cost`, `stop-and-revoke`, `crash-recovery`, `technical-inspection` |
| What happens next? | All 13 journeys. |

Coverage means the answer is a source-linked visible fact, not that a renderer
may derive or guess an answer.

## Screen-slice ownership

| Story | Owned journeys |
|---|---|
| `WLA-27-03` | `healthy-first-arrival`, `deliberate-capability-choice`, `preflight` |
| `WLA-27-04` | `delivery-plan-setup`, `preflight`, `technical-inspection` |
| `WLA-27-05` | `team-review-setup`, `blocked-human-decision`, `technical-inspection` |
| `WLA-27-06` | `live-progress`, `failed-review-and-repair`, `crash-recovery`, `completion`, `technical-inspection` |
| `WLA-27-07` | `failed-review-and-repair`, `blocked-human-decision`, `remaining-permission-and-cost`, `stop-and-revoke`, `crash-recovery`, `technical-inspection` |
| `WLA-27-08` | All 13 journeys across human surfaces. |
| `WLA-27-09` | All 13 journeys at wide/narrow viewports and through keyboard/assistive interaction. |
| `WLA-27-10` | All 13 journeys in the fresh-wheel exit exam. |

The JSON mapping is bidirectional: each screen slice lists its journeys and
each journey lists its owners. The validator rejects drift in either
direction.

## WLA-27-03 delivered slice

The first owned slice now uses the shared
`delivery-workbench-delivery-setup` application view:

- `healthy-first-arrival` leads with **Your roadmap is ready**, current work,
  **Open current work**, and **Review delivery options**; repository protocol
  remains under **Technical details**;
- `deliberate-capability-choice` begins with project/phase scope and compares
  ordinary roadmap work, one bounded delivery, and an optional program without
  preselecting a higher tier; reviewing any choice shows its creation, later
  effect, disabled behavior, remaining permission, and safe exit;
- `preflight` leads with work/order, team, review, permission, limits/stops,
  and one separate-start next step; invalid plans lead with the affected
  delivery decision and correction while exact compiler targets remain under
  **Technical details**.

Human `dw setup` renders the same labels and readiness. The Workbench setup
renderer has no mutation or live-activity primitive, and the fresh-wheel
no-program proof requires all optional policy/runtime stores to remain absent.
See [delivery setup and first arrival](./delivery-setup.md).

## WLA-27-04 delivered slice

`delivery-plan-setup` now begins with
`delivery-workbench-delivery-plan-authoring@1`, a pure application view over
the exact Program Studio document, graph, validation, and round-trip models.
Its default **Plan** view follows the seven reviewed delivery decisions:

1. delivery scope;
2. work flow;
3. quality and review;
4. decision points;
5. repair and escalation;
6. stop conditions;
7. finite limits.

Each section states its question, answer, source-backed items, correction
count, and example. A persistent **Review before save** summary covers all
seven decisions. Program plans edit scope, work routes, phase decisions,
stops, and limits; work flows edit work inputs and ordinary work, check,
review, and decision steps.

`technical-inspection` remains adjacent rather than becoming the default.
Hierarchical flows, bounded repair, discussion cells, exact conditions, graph
layout, and raw import/export remain editable under **Technical details**.
Both modes edit the same in-memory source document. Valid imports preserve
semantic and layout identity; unknown fields remain present and make the
existing save boundary refuse safely.

Invalid drafts lead with the affected delivery decision, downstream behavior,
and correction. Exact source paths, pointers, rule codes, and technical
fingerprints stay in Technical details. Drafting, trying the flow, checking,
reviewing, and abandoning remain no-write reads; the existing separate
preview/confirmation is still the only tracked save boundary.

See [delivery-plan authoring](./plan-authoring.md).

## WLA-27-05 delivered slice

`team-review-setup` now begins with
`delivery-workbench-team-review@1`, the same application view used for live
ownership and review. The default **Team & review** view asks five questions:

1. who does each kind of work;
2. who reviews it independently;
3. who decides when reviewers disagree;
4. who receives help or an escalation; and
5. who audits review or phase-level design.

Responsibility cards show required coverage and available backup. Quality
constraints name both conflicting responsibilities and distinguish a
policy-ready candidate pairing from a runtime-proven assignment. Panels,
decision groups, required reviewer agreement, objections, dissent, named
decision owners, review auditors, and architecture checks appear
progressively when the source declares them.

The explicit team Technical-details state retains stable IDs, candidate
profiles, exact permissions, packet and schema fields, provider/model/auth and
principal fingerprints, work areas, session bindings, finite decision bounds,
and lossless JSON. Provider or model diversity never substitutes for exact
identity separation.

Invalid separation leads with the affected responsibilities, unsafe behavior,
and correction while preserving the draft and refusing save. The existing
review/fingerprint/confirmation boundary remains the only tracked write and
starts no work. See [team and review design](./team-review.md).

## WLA-27-06 delivered slice

`live-progress`, `failed-review-and-repair`, `crash-recovery`, `completion`,
and `technical-inspection` now use
`delivery-workbench-live-progress@1`. The same pure projection is nested in
both the bounded Run view and optional-program view, so CLI, MCP, HTTP, SSE,
and Workbench receive identical answers to all seven operator questions.

The default live page leads with delivery state, declared scope denominator,
one canonical next step, doing/reviewing ownership, passed and blocked work,
decision need, remaining permission and counted limits, readable activity,
and recovery truth. Work is grouped as active, waiting, review, repair,
blocked, recovering, stopped, or complete while preserving its exact identity
for inspection. Mechanical checks, agent judgment, dissent, repair, and final
governed decisions remain separate proof classes.

The bounded next step copies the canonical scheduled item, active work,
request, or terminal/stop fact. The program next step copies the canonical
first action, reconciliation work, request, checkpoint, or terminal/stop fact.
The application builder and browser both declare that they select no work,
decide no recovery, grant no permission, and write no state.

Readable activity groups related work and outcomes; the exact graph,
assignments, controls, streams, counters, ordered hash-linked history, and
provenance remain under **Technical details**. A stale live connection keeps
the last verified view, says that completed work remains recorded, and asks
the user to check the saved history again without claiming loss or duplicate
execution. The harness includes dedicated wide/narrow active, review/repair,
terminal, stale, and Technical-details captures.

The baseline below remains the dated pre-redesign observation. Its stable
capture IDs now exercise the improved routes, allowing later whole-journey
comparison without erasing the original finding.

## Current-friction baseline

The baseline was captured on 2026-07-24 from the existing canonical UI
fixture builders:

```bash
DW_UI_CAPTURE_DIR=.tmp/wla27-current-baseline \
DW_UI_CAPTURE_PATTERN='*' \
pmo-roadmap/tests/workbench-ui-smoke.sh
```

The harness now produces all 76 views and passes. Each mapped state has a
1440×900 desktop capture and a 390×844 mobile capture. The screenshots are
reproducible test output under ignored `.tmp/`; the versioned baseline records
the observable findings, not machine-specific image bytes.

Across the 13 journeys, the current application requires **88 visible steps**
and **38 user decisions**, exposes **81 engineering-term occurrences**, and
contains **13 recorded dead ends** plus **26 context switches**. These are
descriptive counts, not a quality score. A later story demonstrates
improvement by updating its owned journey against the same categories and
recording any tradeoff honestly.

| Journey | Steps | Decisions | Engineering terms | Dead ends | Context switches |
|---|---:|---:|---:|---:|---:|
| `healthy-first-arrival` | 5 | 2 | 5 | 1 | 2 |
| `deliberate-capability-choice` | 6 | 3 | 5 | 1 | 2 |
| `delivery-plan-setup` | 7 | 3 | 9 | 1 | 2 |
| `team-review-setup` | 6 | 3 | 6 | 1 | 2 |
| `preflight` | 8 | 3 | 7 | 1 | 2 |
| `live-progress` | 7 | 3 | 6 | 1 | 2 |
| `failed-review-and-repair` | 7 | 3 | 6 | 1 | 2 |
| `blocked-human-decision` | 7 | 3 | 6 | 1 | 2 |
| `remaining-permission-and-cost` | 7 | 3 | 7 | 1 | 2 |
| `stop-and-revoke` | 7 | 3 | 6 | 1 | 2 |
| `crash-recovery` | 7 | 3 | 6 | 1 | 2 |
| `completion` | 8 | 3 | 7 | 1 | 2 |
| `technical-inspection` | 6 | 3 | 5 | 1 | 2 |

The consistent baseline finding is not that exact data is absent. It is
abundant and inspectable. The friction is its placement: generated IDs,
hashes, exact authority state, raw bindings, counters, graph taxonomy, and JSON
often precede the ordinary delivery answer. On narrow screens, wrapped global
navigation and stacked protocol cards commonly push the decisive fact and safe
action beyond the first viewport.

Notable specific findings:

- healthy ordinary work exists, but contract/gate/workspace language leads the
  arrival view;
- optional setup is technically healthy, but a large new-program editor can
  look mandatory;
- plan and team design begin with node, topology, role, and exact capability
  structures rather than delivery decisions and responsibilities;
- live, repair, and decision states are reconstructable from graphs and exact
  state, but their human answer and next step are not adjacent;
- remaining permission and cost are precise but distributed across raw
  bindings and many counters;
- the captured completion specimen simultaneously presents `running`,
  `story-certified`, and `integration-required`, requiring the person to infer
  whether one work item or the whole delivery completed;
- exact inspection is reachable through a `JSON` tab, but the required
  **Technical details** label and a task-preserving return path are absent.

## Reuse contract

Workbench UI tests load state IDs from `states-v1.json`, build those states
through the existing core/read-model fixture paths, and resolve each
`capture_id` to both viewport renders in
`pmo-roadmap/tests/workbench-ui-smoke.sh`. They do not hand-author a parallel
UI-only state.

The WLA-27-10 fresh-wheel exam loads the same journey IDs, starting states,
visible facts, actions, outcomes, and exact-detail state. It may add an
acceptance transcript, but it may not re-describe or weaken the task. A screen
test or exit exam that needs a different fact or outcome must change the
versioned contract first.

Run the deterministic contract check with:

```bash
python3 pmo-roadmap/tests/usability-journey-contract.py
```

The checker rejects incomplete journeys, unknown source models, capture IDs
without both viewports, reserved engineering language in everyday regions,
missing safe exits, invented or over-broad action sources, silent tier
changes, ambiguous next steps, inaccessible **Technical details**, missing
question or screen coverage, incomplete baselines, reuse drift, and missing
docs/README/CI wiring. It also applies every planted mutation in
`red-fixtures-v1.json` and proves the intended refusal still fires.
