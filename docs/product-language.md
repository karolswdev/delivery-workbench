# The everyday product language

**Contract:** `delivery-workbench-application-language@1`
**Machine-readable canon:**
[product-language-contract-v1.json](./product-language-contract-v1.json)
**Scope:** human-facing application language and presentation only
**Not changed:** persisted state, machine schemas, commands, authority,
evidence, eligibility, replay, recovery, or delivery behavior

Delivery Workbench has exact engineering contracts for roadmaps, scores,
programs, workflows, organizations, grants, ledgers, reviews, events, and
delivery effects. Those contracts remain authoritative. People using the
application should not need to speak their implementation vocabulary to answer
ordinary delivery questions.

The everyday application must make these questions easy:

1. What are we delivering?
2. Who is doing and reviewing it?
3. What passed?
4. What is blocked?
5. Who needs to decide?
6. What may the delivery still change or spend?
7. What happens next?

This document defines one product vocabulary, the boundary between everyday
and technical language, and the projection rules every human renderer will
share. It is a design and compatibility contract, not a string-substitution
list.

## Product-language rules

1. **One concept, one ordinary name.** The same concept keeps the same preferred
   name in Workbench, human CLI output, notifications, help, errors,
   onboarding, and product guides.
2. **Canonical facts remain canonical.** An application view may group,
   label, order, and explain exact facts. It may not recompute eligibility,
   authority, evidence validity, review outcomes, resource use, or next work.
3. **Unknown beats guessed.** Missing, stale, or ambiguous facts render as
   unknown, unavailable, waiting, or blocked. Friendly language is not
   permission to manufacture certainty.
4. **Safety stays adjacent.** Scope, effects, exclusions, limits, expiry,
   destructive consequences, refusal reasons, and recovery guidance stay next
   to the action they qualify.
5. **Everyday first, exact on demand.** A normal task begins in product
   language. The same task offers an explicitly labelled **Technical details**
   path to exact fields, identifiers, events, paths, commands, and records.
6. **Machine contracts do not translate.** JSON keys, event kinds, persisted
   identifiers, command names, and stamped schemas keep their exact names.
   Human renderers explain them; they do not alias them.
7. **A summary creates no authority.** Preview, freshness, principal,
   permission, and response checks remain separate and decisive. Transporting
   or reading an explanation never starts work.
8. **Optional stays optional.** A healthy repository with no program
   configuration is a complete ordinary Delivery Workbench experience, not an
   incomplete setup.

## The ten product concepts

| Concept | Means | Relationship | Good application copy | Avoid as normal copy |
|---|---|---|---|---|
| `delivery plan` | Reviewed scope, route, quality points, decisions, limits, and stop conditions for one bounded delivery | Selects `work`, assigns a `team` and `review`, consumes `permission`, and reports `progress`, `cost`, and the `next step` | “Delivery plan: improve setup across three stories, with independent review before completion.” | “The program policy binds a governed scope to compiled workflows.” |
| `team` | Named people or agents responsible for doing, reviewing, deciding, or auditing | Owns `work`; its responsibilities and independence shape `review` | “Team: Maya implements; Rowan reviews independently.” | “Organization seat provenance satisfies principal separation.” |
| `work` | A roadmap story or bounded task being prepared, performed, checked, repaired, or completed | Belongs to a `delivery plan`, has a `team` owner, and contributes to `progress` | “Work: WLA-27-03 is being implemented, then moves to review.” | “The child run claimed the selected frontier node.” |
| `review` | Independent checks and judgments required before work can pass | Evaluates `work`, may request repair or a `decision`, and changes `progress` only through canonical quality rules | “Review: four checks passed; Rowan requested one repair.” | “The quality gate consumed facts under rubric quorum.” |
| `decision` | A current closed choice a named person, role, or review body must make | May resolve a `blocker` or route work to repair, review, stop, or escalation | “Decision needed from Karol: continue with the repair, or stop this delivery.” | “A correlation-bound typed request awaits a response.” |
| `blocker` | The concrete reason delivery cannot safely continue, and who or what can resolve it | Pauses `progress` and points to a failed check, missing fact, exhausted limit, `decision`, refusal, or recovery step | “Blocker: CI failed. Fix the failing check before work continues.” | “The conductor frontier stopped at reconciliation.” |
| `permission` | Exact actions the delivery may still take, over what scope, within which limits and lifetime | Constrains the `delivery plan` and `team`; using it may change remaining `cost` but never expands it | “Permission: may update these stories and push this branch until 17:00; merge and release are not allowed.” | “Grant capabilities authorize mutation under a fresh act token.” |
| `progress` | Source-backed completed, active, waiting, blocked, review, repair, and remaining work | Summarizes `work` against the `delivery plan`; stays distinct from activity, confidence, `permission`, and `cost` | “Progress: 3 of 5 stories complete; one is in review and one is blocked.” | “Projection generation 12 contains 203 ledger events.” |
| `cost` | Declared limit, measured use, and remaining amount for finite resources | Is consumed only under `permission` and appears beside `progress` without implying that spending proves value | “Cost: 8,000 of 12,000 model tokens used; 4,000 remain.” | “Budget projection shows an unbounded null ceiling.” |
| `next step` | One source-backed action or named wait condition that follows from current state | Follows `progress`, `review`, `decision`, `blocker`, and `permission`; a renderer never selects it independently | “Next step: Rowan reviews WLA-27-03 after its checks finish.” | “The frontier selected a conductor tick.” |

### Relationship and distinction rules

- A delivery plan is configuration; it is not permission and does not prove
  that work started.
- A team is responsibility plus exact identity. A display name never erases
  principal, provider, workspace, session, or independence facts.
- Work describes a deliverable task. Agent activity, a spawned process, an
  event, or token use alone is not work completed.
- Review distinguishes mechanical checks, agent judgment, dissent, repair,
  and the final governed outcome.
- A decision has a closed source-defined response set. Free text may explain a
  choice but cannot create a new choice.
- A blocker is a current reason, not a generic warning. It identifies affected
  work, unchanged state, a resolver, and a safe next step when known.
- Permission describes both what is allowed and what remains forbidden.
  “Approved” describes a completed human act; it is not a synonym for all
  remaining permission.
- Progress always names its denominator or says it is unknown. Event volume and
  agent activity are not progress.
- Cost distinguishes limit, estimate, measured use, remaining amount, zero,
  unbounded, unknown, and not applicable.
- The next step is derived by the canonical status or delivery core. When
  none is safe, show the blocker, decision owner, wait condition, or unknown
  state.

## The application-view boundary

The versioned JSON contract names the source facts for each concept. The
application flow is:

```text
canonical stamped models and exact records
        ↓ read only
shared presentation projection
        ↓ facts + source references, no policy
Workbench / human CLI / notifications / help / errors / product docs
```

The projection may:

- select facts already chosen by a canonical model;
- group related facts under a product concept;
- choose the preferred label and readable order;
- format known counts, times, scopes, and limits;
- attach a source reference for **Technical details**;
- state unknown, unavailable, waiting, blocked, or not applicable.

The projection must not:

- choose eligible work, a reviewer, a route, or an action;
- interpret raw events as success, evidence, or completion;
- decide that permission exists or that an effect is safe;
- recalculate a review outcome, quorum, resource use, or remaining limit;
- translate one machine field into an alias accepted by another adapter;
- hide a refusal, destructive effect, expiry, provenance issue, or unknown;
- turn a notification, response transport, or readable summary into authority.

Every projected value needs a stable product concept and enough source identity
to open the exact record. A renderer may omit technical identity from the
default sentence, but it cannot discard it.

## Surface classes

Every current human-facing surface is one of three classes:

- **Everyday:** product language is the default. Exact commands and identifiers
  may remain copyable, but prose does not require engineering vocabulary.
- **Mixed:** the ordinary task and safety facts lead. Exact material is
  reachable inside an explicitly labelled **Technical details** region.
- **Technical/audit:** exact vocabulary is intentional. The surface is entered
  deliberately from an everyday task or specialist documentation; it is not
  the normal explanation.

“Advanced” is not a boundary label. A disclosure that contains protocol terms
must say **Technical details** so a person knows the mental model is changing.

## Complete current-surface inventory

The JSON contract records source paths, entry points, and owning Phase 27
stories for every row. This table is the human review of that inventory.

| Surface ID | Class | Default responsibility | Technical boundary |
|---|---|---|---|
| `workbench-orientation-roadmap` | everyday | Repository readiness, roadmap, current work, holds, and next step | Exact files and evidence open deliberately |
| `workbench-health-and-edit` | mixed | Explain the issue, affected work, unchanged state, and correction | Paths, diffs, fingerprints, and rule IDs under **Technical details** |
| `workbench-mission-control-and-history` | mixed | Group progress and outcomes | Sessions, event kinds, file paths, and logs under **Technical details** |
| `workbench-bounded-delivery` | mixed | Delivery plan, team, work, review, decisions, limits, progress | Exact score/run fields, events, hashes, tokens, and streams under **Technical details** |
| `workbench-delivery-studio` | mixed | Task-shaped delivery and team design | Lossless JSON, compiler diagnostics, exact fields, and fingerprints under **Technical details** |
| `workbench-live-delivery` | mixed | Progress, ownership, review, blockers, decisions, permission, cost, next step | Grants, ledgers, hashes, identifiers, events, and streams under **Technical details** |
| `cli-orientation-and-roadmap` | everyday | Readiness, work, blocker, evidence, next step | `--json` remains the exact machine contract |
| `cli-setup-health-help-and-errors` | mixed | Task, effect, unchanged state, and correction | Gate rules, contract fields, commands, and paths remain copyable under **Technical details** |
| `cli-bounded-delivery` | mixed | Human delivery summaries and actions | `--json`, identifiers, and copyable commands stay exact under **Technical details** |
| `cli-program-delivery` | mixed | Human plan, team, review, operation, and outcome summaries | Command names, policy fields, JSON, IDs, and audit tails stay exact under **Technical details** |
| `machine-json-adapters` | technical/audit | Stable machine interoperability | No presentation aliases; schemas and keys remain exact |
| `operator-notifications-and-telegram` | mixed | Affected work, blocker/decision, valid choices, next step | Request identity and transport records under **Technical details**; transport is not authority |
| `agent-riders-and-holdspeak` | mixed | Delivery task and safe next step | Exact commands, paths, story IDs, and payloads remain copyable under **Technical details** |
| `readme-and-first-use` | everyday | Product case, healthy default, first complete task | Protocol contracts are linked specialist reading |
| `everyday-product-guides` | everyday | Complete setup and delivery tasks | Exact contracts are linked when implementation or audit detail is needed |
| `architecture-and-protocol-contracts` | technical/audit | Exact trust model, schemas, and subsystem semantics | Engineering terms are intentional and authoritative |
| `exact-events-streams-and-files` | technical/audit | Exact ordering, identity, paths, events, fingerprints, and bounded content | Opened deliberately from an everyday task |
| `cross-surface-errors-and-refusals` | mixed | What happened, what did not change, affected work, next safe step | Codes, paths, tokens, and source records under **Technical details** |

This is the Phase 27 opening inventory. New human surfaces must add a row when
they are introduced. WLA-27-08 will enforce coverage against the redesigned
source inventory rather than treating this initial census as permanently
self-discovering.

## Reserved engineering vocabulary

Reserved does not mean forbidden everywhere. It means “do not require this
word in an everyday sentence.” The terms remain exact and welcome in machine
contracts, architecture, code identifiers, copyable commands, and labelled
technical/audit regions.

| Engineering term | Everyday explanation |
|---|---|
| `grant` | `permission` |
| `ledger` | activity or technical record |
| `preview token` | current confirmation |
| `start token` | start confirmation |
| `act token` | action confirmation |
| `content boundary` | what details are visible |
| `certification` | final evidence check |
| `capability` | allowed action or `permission` |
| `projection` | current status |
| `conductor` | delivery coordinator or current delivery state |
| `frontier` | `next step` or `blocker` |
| `receipt` | proof or technical record |
| `correlation id` | technical reference |
| `schema version` | format version |
| `rubric` | review criteria |
| `quorum` | required reviewer agreement |
| `meta-verifier` | review auditor |
| `hash` | technical fingerprint |

Exact command names and identifiers are never rewritten. For example, the
application may say “Review the current confirmation, then run this exact
command” and show `dw program tick --expect <act-token>` as copyable technical
material. It must not relabel the token inside the command or machine payload.

## Safety-sensitive copy

Plain language must become more precise when an action matters.

| Situation | Required facts | Good pattern | Insufficient pattern |
|---|---|---|---|
| Permission | effects, scope, ceilings, expiry/stop, current use, exclusions | “May update these stories and push this branch until 17:00; merge and release are not allowed.” | “Authorized.” |
| Cost | unit, limit, measured/estimated status, used, remaining, unknown/unbounded distinction | “8,000 of 12,000 measured model tokens used; 4,000 remain.” | “Budget OK.” |
| Destructive or irreversible act | exact target, consequence, recovery, separate confirmation | “Stop this delivery permanently. Completed commits remain; this permission cannot resume.” | “Are you sure?” |
| Refusal | what failed, what did not change, whether an effect may already exist, next safe step | “The confirmation expired. No new event was written. Review the current plan and try again.” | “Invalid token.” |
| Provenance/independence | readable responsibility plus exact inspectable identity facts | “Rowan reviews independently. Technical details show separate principal and workspace.” | “Reviewer assigned.” |
| Unknown | named missing fact and consequence | “Cost is unavailable, so no remaining amount is claimed.” | “0 used.” |

Friendly language never softens a refusal, merges materially different
actions, or hides uncertainty.

## Versioning

`delivery-workbench-application-language@1` is the Phase 27 contract.

A new `schema_version` is required when:

- a preferred product term changes;
- one concept splits, merges, or changes meaning;
- a projection rule gains or loses semantic responsibility;
- a surface moves between everyday, mixed, and technical/audit in a way that
  changes its default mental model;
- a previously exact-only fact becomes an everyday action contract.

Adding examples, recording a new surface that follows an existing class, or
clarifying prose without changing meaning is additive. Machine contracts keep
their own independent versions; this presentation contract never versions
them by proxy.

## Executable enforcement

Run:

```sh
python3 pmo-roadmap/tests/product-language-contract.py
```

The check:

- validates the exact contract shape and required concept/rule/surface census;
- proves every source path in the inventory exists;
- rejects duplicate preferred names and incomplete source-fact mappings;
- rejects reserved engineering language in everyday fixture regions;
- permits exact language in labelled technical/audit regions;
- rejects a mixed surface that hides or mislabels its technical boundary;
- rejects a conflicting product name for a canonical concept;
- verifies this guide, the root documentation index, and CI remain wired.

The versioned positive and red fixtures live in
`pmo-roadmap/tests/product-language-fixtures-v1.json`. They are a contract
self-test, not a claim that the current application has already been
redesigned. WLA-27-03 through WLA-27-08 migrate the inventoried surfaces;
WLA-27-10 proves the whole application from a fresh package.

## Phase 27 implementation boundary

WLA-27-01 changed no runtime semantics and established this boundary.
WLA-27-03's first presentation adapter,
`delivery-workbench-delivery-setup@1`, derives only from the canonical status,
orchestration inventory, and Program Studio models. Workbench and human CLI
render that same application view; existing machine responses remain
unchanged, and exact data stays reachable through **Technical details**.

WLA-27-04 adds `delivery-workbench-delivery-plan-authoring@1` over the existing
Program Studio document, graph, validation, and round-trip models. Its ordinary
view groups those facts into delivery scope, work flow, quality/review,
decisions, repair/escalation, stops, and limits. Exact graph structure, source
fields, diagnostics, and JSON remain under **Technical details**. The
projection edits no source and owns no compiler or permission decision.

Later stories follow the same rule. If a desired sentence cannot be supported
by canonical facts, the renderer must say it is unknown or the canonical model
must be changed in a separately reviewed story. The UI may never fill the gap
with policy of its own.
