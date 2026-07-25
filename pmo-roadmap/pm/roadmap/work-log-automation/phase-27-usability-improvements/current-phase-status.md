# Phase 27 - Usability Improvements

**Last updated:** 2026-07-25.

## Goal

Make Delivery Workbench's everyday application layer speak and behave like a practical delivery tool, with one plain-language vocabulary and coherent task flows across setup, Program Studio, live operation, help, errors, onboarding, and product documentation, while keeping exact protocol terms available in machine contracts, architecture, and explicit audit views.

## Scope

- **In:** a versioned product-language and application-view contract; an
  inventory of everyday versus technical surfaces; executable whole-task
  journeys; a delivery-shaped first-run experience; plain-language delivery
  plan, workflow, team, review, and council authoring; a live view centered on
  progress, passed work, blockers, decisions, remaining permission/cost, and
  the next step; actionable errors and recovery; consistent human-facing CLI,
  Workbench, notification, help, onboarding, and product-doc renderers; an
  explicit technical/audit view; keyboard, narrow-screen, and assistive
  semantics; terminology, journey, UI, parity, and fresh-consumer proof.
- **Out:** renaming machine-contract fields or exact internal types; weakening
  grant, ledger, preview-token, content-boundary, evidence, certification,
  replay, or authority rules; changing the no-program default; adding a new
  autonomy tier, workflow engine, provider, transport, hosted service,
  cross-repository authority, or usage telemetry; a visual-brand refresh;
  version bump, tag, release, package publication, formula update, or deploy.

## Exit criteria (evidence required)

- [x] `docs/product-language.md` defines one ordinary product vocabulary, the
  everyday/technical-view boundary, and a lossless mapping to existing exact
  semantics; executable language checks reject drift (WLA-27-01).
- [x] Versioned whole-task journeys and deterministic fixtures cover arrival,
  setup, plan/team/review design, live progress, a blocked decision, recovery,
  completion, and technical inspection before UI implementation begins
  (WLA-27-02).
- [x] A fresh user can understand the healthy no-program state, choose the
  optional delivery capability deliberately, and finish or leave setup without
  hidden writes or internal protocol vocabulary (WLA-27-03).
- [x] Program Studio makes delivery-plan/workflow authoring and team/review
  design understandable while round-tripping the existing exact configuration
  without semantic loss (WLA-27-04, WLA-27-05).
- [x] Live operation answers the seven operator questions from the Phase 26
  handoff and turns decisions, blockers, permission, cost, stop/revoke, and
  recoverable failures into clear bounded actions (WLA-27-06, WLA-27-07).
- [ ] Workbench, human CLI output, notifications, help, errors, onboarding, and
  everyday docs use the same product terms; machine JSON and explicit
  technical/audit views retain exact engineering language (WLA-27-08).
- [ ] Setup, authoring, live operation, decisions, and technical inspection are
  usable by keyboard, at narrow and wide viewports, and with meaningful
  structure/labels and stable focus (WLA-27-09).
- [ ] A fresh installed-wheel exam completes the canonical journeys, proves
  plain-language defaults plus exact audit escape hatches, and keeps the
  no-program, bounded-run, program, parity, recovery, and distribution suites
  green (WLA-27-10).

## Story status

| ID | Story | Status | Story file | Evidence |
|---|---|---|---|---|
| WLA-27-01 | Contract the everyday product language | done | [story-01-contract-the-everyday-product-language](./story-01-contract-the-everyday-product-language.md) | [evidence-story-01](./evidence-story-01.md) |
| WLA-27-02 | Define whole-task journeys and usability proof | done | [story-02-define-whole-task-journeys-and-usability-proof](./story-02-define-whole-task-journeys-and-usability-proof.md) | [evidence-story-02](./evidence-story-02.md) |
| WLA-27-03 | Give first-time users a delivery-shaped front door | done | [story-03-give-first-time-users-a-delivery-shaped-front-door](./story-03-give-first-time-users-a-delivery-shaped-front-door.md) | [evidence-story-03](./evidence-story-03.md) |
| WLA-27-04 | Make plan and workflow authoring task-shaped | done | [story-04-make-plan-and-workflow-authoring-task-shaped](./story-04-make-plan-and-workflow-authoring-task-shaped.md) | [evidence-story-04](./evidence-story-04.md) |
| WLA-27-05 | Make teams and review rules understandable | done | [story-05-make-teams-and-review-rules-understandable](./story-05-make-teams-and-review-rules-understandable.md) | [evidence-story-05](./evidence-story-05.md) |
| WLA-27-06 | Make live delivery explain progress and next steps | done | [story-06-make-live-delivery-explain-progress-and-next-steps](./story-06-make-live-delivery-explain-progress-and-next-steps.md) | [evidence-story-06](./evidence-story-06.md) |
| WLA-27-07 | Turn decisions, blockers, permissions, and cost into actions | done | [story-07-turn-decisions-blockers-permissions-and-cost-into-actions](./story-07-turn-decisions-blockers-permissions-and-cost-into-actions.md) | [evidence-story-07](./evidence-story-07.md) |
| WLA-27-08 | Make every everyday word agree | backlog | [story-08-make-every-everyday-word-agree](./story-08-make-every-everyday-word-agree.md) | - |
| WLA-27-09 | Harden keyboard, screen-size, and assistive use | backlog | [story-09-harden-keyboard-screen-size-and-assistive-use](./story-09-harden-keyboard-screen-size-and-assistive-use.md) | - |
| WLA-27-10 | Prove the redesigned application end to end | backlog | [story-10-prove-the-redesigned-application-end-to-end](./story-10-prove-the-redesigned-application-end-to-end.md) | - |

## Where we are

Phase 27 is OPEN 7/10. Bounded-run and program control rooms now share the pure
`delivery-workbench-live-progress@1` and
`delivery-workbench-bounded-actions@1` projections. The default action center
shows affected work, exact current choices, permission scope, ceilings,
expiry/stops, current use, forbidden effects, and distinct consequences before
the existing exact confirmation. Zero, finite, unbounded, unknown, and not
applicable values remain different. Pause, saved repair, resume, permanent
revoke, cancel, and rejection do not collapse into one generic control.
Structured refusals explain what happened, what stayed unchanged, effect
uncertainty, and the safe reload/inspection path; notifications and Telegram
carry responses without manufacturing authority. Exact identities, tokens,
controls, and receipts remain under `Technical details`. The 88-render
wide/narrow harness, 23-state journey contract, focused action/refusal/parity
tests, fresh Python 3.9 wheel, and autonomous/no-program consumers are green.
WLA-27-08 is next: make every everyday renderer use the same product terms.
There are no known blockers.

## Active risks

| Risk | Likelihood | Mitigation | Stop signal |
|---|---|---|---|
| The work becomes a cosmetic string replacement over the same confusing tasks | high | Contract whole-task journeys before UI work and require each slice to remove task ambiguity | A renamed screen still requires knowledge of grants, ledgers, tokens, or certification to complete an everyday task |
| Plain language hides facts needed for informed permission or recovery | high | Keep exact effects, limits, provenance, and an explicit technical/audit view adjacent to summaries | A person can act without seeing what may change, what remains, or how to inspect the exact record |
| Human renderers drift into a second source of truth | high | Derive one versioned application view from canonical models and keep adapters semantic-free | A renderer computes eligibility, authority, evidence, or next-work rules |
| Surfaces choose different names for the same concept | medium | Maintain one vocabulary inventory and executable snapshots across all human surfaces | One concept has two ordinary names or one ordinary name means two things |
| Optional programs become implied setup | high | Preserve the no-program fresh-consumer exam and progressive capability ladder | Install, update, status, or Workbench startup creates or requires program state |
| Accessibility is postponed until after visual structure hardens | medium | Include keyboard, focus, semantics, and narrow viewports in each journey fixture | A core journey needs a pointer, loses focus, clips its action, or has an unlabeled control |
| The phase expands into new orchestration semantics | medium | Treat exact runtime behavior as an invariant and park capability requests | A story needs a new authority, workflow, transport, provider, or persistence model to satisfy its acceptance criteria |

## Decisions made (this phase)

- 2026-07-23 - Phase scaffolded with `dw phase create` - keeps roadmap structure consistent - CLI.
- 2026-07-23 - Name the phase `Usability Improvements` and center it on the
  plain delivery questions recorded in the Phase 26 handoff - direct user
  direction and closeout evidence - user.
- 2026-07-23 - Preserve exact protocol language in code, architecture, machine
  contracts, and explicit technical/audit views while removing it from normal
  task flows - usability must not weaken inspectability or create new runtime
  semantics - user direction.
- 2026-07-23 - Contract vocabulary and whole-task journeys before changing the
  UI - this is product and information design, not a find-and-replace pass -
  Phase 26 handoff.
- 2026-07-23 - Keep no-program healthy state and every established authority,
  evidence, replay, recovery, and adapter-parity invariant in the exit exam -
  usability is an application projection over the shipped trust model -
  architecture boundary.
- 2026-07-23 - Keep landing and release outside Phase 27 - opening work does
  not imply version, tag, publication, formula, or deployment authority -
  owner boundary.
- 2026-07-23 - Fix `delivery plan`, `team`, `work`, `review`, `decision`,
  `blocker`, `permission`, `progress`, `cost`, and `next step` as the v1
  everyday concepts - one concept needs one stable product name across every
  human surface - WLA-27-01.
- 2026-07-23 - Classify each current surface as everyday, mixed, or
  technical/audit; mixed surfaces must use the explicit label `Technical
  details` - “advanced” does not tell a person that the mental model changed -
  WLA-27-01.
- 2026-07-23 - Make the application view a source-traceable presentation
  projection over the stamped models in `docs/interop.md`; it may group and
  explain facts but owns no eligibility, authority, evidence, review, cost, or
  next-work semantics - source-of-truth boundary - WLA-27-01.
- 2026-07-23 - Reserve eighteen engineering terms from everyday fixture
  regions while keeping them exact in machine contracts, architecture, code,
  commands, and technical/audit views - readable defaults and lossless audit
  are complementary requirements - WLA-27-01.
- 2026-07-24 - Fix thirteen observable whole-task journeys rather than a page
  layout: each names its canonical start, ordinary question and facts, bounded
  actions, one success next step, one safe refusal/recovery next step, and an
  explicit `Technical details` state - later screens may improve interaction
  design without changing trust or outcome semantics - WLA-27-02.
- 2026-07-24 - Treat `vanilla` as the healthy default and `bounded-run` plus
  `program` as separate optional tiers; every tier-changing action must use an
  existing start boundary and explicit confirmation - setup may recommend but
  never silently upgrade - WLA-27-02.
- 2026-07-24 - Reuse the existing canonical Workbench fixture builders as the
  reachable-state seam: fifteen state IDs map declared `docs/interop.md`
  models to both 1440x900 and 390x844 capture IDs - the journey contract does
  not create a parallel UI-only state model - WLA-27-02.
- 2026-07-24 - Record steps, user decisions, engineering terms, dead ends, and
  context switches as descriptive baseline counts, not a model-generated
  usability score - later stories must show task improvement and retain any
  tradeoff honestly - WLA-27-02.
- 2026-07-24 - Add `delivery-workbench-delivery-setup@1` as a pure application
  view over existing status, orchestration-inventory, and Program Studio
  models; Workbench and human CLI may explain and group those facts, but
  existing machine documents and all source authority remain unchanged -
  WLA-27-03.
- 2026-07-24 - Compare ordinary, bounded, and optional-program delivery without
  preselecting a higher tier; choice review must state creation, later change,
  disabled behavior, and remaining permission before handing off to an
  existing save or start boundary - informed optionality - WLA-27-03.
- 2026-07-24 - Keep setup, comparison, technical disclosure, and leave paths
  read-only; a program choice seeds browser memory only, tracked save retains
  its exact preview/confirmation, and every runtime start remains a separate
  reviewed act - no friendly navigation may acquire authority - WLA-27-03.
- 2026-07-24 - Treat invalid optional policy as an affected optional decision,
  not a failure of ordinary delivery: the ordinary front door remains healthy
  and the program choice names its correction - progressive capability
  isolation - WLA-27-03.
- 2026-07-24 - Add `delivery-workbench-delivery-plan-authoring@1` as a pure
  application view over the exact Program Studio source, graph, validation,
  and round-trip documents; renderers may group and explain those facts but
  own no new saved format or runtime meaning - source-of-truth boundary -
  WLA-27-04.
- 2026-07-24 - Fix the default authoring order as scope, flow, quality,
  decisions, recovery, stops, and limits, each led by its delivery question;
  move hierarchy, bounded repetition, discussion, exact conditions, graph
  fields, and raw configuration behind the explicit `Technical details`
  boundary - progressive authoring contract - WLA-27-04.
- 2026-07-24 - Keep every edit on the cloned exact source document, carry
  declared references during ordinary renames, preserve unknown extensions,
  and refuse invalid save rather than reconstructing or silently simplifying
  policy - lossless-edit boundary - WLA-27-04.
- 2026-07-24 - Add `delivery-workbench-team-review@1` as the shared pure
  application projection for Program Studio organization design and live
  assigned ownership/review; it groups existing organization, validation,
  assignment, and program-view facts but owns no assignment, review,
  decision, escalation, or authority meaning - source-of-truth boundary -
  WLA-27-05.
- 2026-07-24 - Distinguish `policy-ready` compatible candidates from
  `runtime-proven` separation; only the assignment engine's exact candidate,
  profile, principal, work-area, session, and read-only-review facts may
  establish the latter, while provider/model diversity remains descriptive -
  independence boundary - WLA-27-05.
- 2026-07-24 - Ask five ordinary questions—work responsibility, independent
  review, contested decisions, help/escalation, and review-of-review—while
  progressively disclosing panels, dissent, judges, review auditors, and
  architecture checks and retaining all stable IDs, exact provenance, and raw
  configuration under `Technical details` - progressive team-design contract
  - WLA-27-05.
- 2026-07-24 - Apply targeted organization edits to the cloned exact source,
  carry responsibility references during renames, preserve unknown fields,
  and refuse invalid save; team design and live review displays remain pure
  and never start work or mint authority - lossless/no-side-effect boundary -
  WLA-27-05.
- 2026-07-24 - Add `delivery-workbench-live-progress@1` as one pure
  application projection over canonical bounded-run and program state; its
  seven answers, grouped activity, and recovery explanation may summarize
  saved facts but never select work, start work, write events, recover work, or
  grant authority - source-of-truth boundary - WLA-27-06.
- 2026-07-24 - Derive one visible next step with terminal, outstanding
  request, active reconciliation, repair, and saved-frontier precedence from
  canonical facts; dependency waits remain waiting unless a declared blocker
  exists, and incomparable remaining units are never added together -
  truth-in-status boundary - WLA-27-06.
- 2026-07-24 - Keep readable delivery state, evidence classes, and activity in
  the default view while placing exact identities, ordered hash-linked events,
  controls, limits, and provenance behind one-click `Technical details`;
  disconnects retain the last verified view and recovery names both preserved
  work and duplicate protection - progressive inspection and recovery
  contract - WLA-27-06.
- 2026-07-25 - Add `delivery-workbench-bounded-actions@1` as one pure
  application projection over existing run/program controls, requests,
  blockers, permission, usage, failures, and receipts; it may explain and
  group facts but never select/apply an action, start work, write events, grant
  authority, change retry policy, or notify - source-of-truth boundary -
  WLA-27-07.
- 2026-07-25 - Put allowed effects, affected scope, ceilings, expiry/stops,
  measured consumption, remaining capacity, and permanent exclusions before
  actions; preserve finite, zero, explicitly unbounded, unknown, and not
  applicable as different measurement states - informed-permission boundary -
  WLA-27-07.
- 2026-07-25 - Keep continue/repair, pause, resume, permanent revoke, cancel,
  reject, unavailable retry, and separate permission elevation materially
  distinct; explain their effects before the existing exact preview and show
  readable receipts after completion - consequence-first action contract -
  WLA-27-07.
- 2026-07-25 - Treat notifications and Telegram as response carriers only:
  they may present and carry an exact closed response, while local principal,
  outstanding request, response-set, freshness, ledger/generation, and exact
  confirmation checks remain decisive - transport-is-not-authority boundary -
  WLA-27-07.

## Decisions deferred

- Channel-specific microcopy refinements - trigger: the owning WLA-27-03
  through WLA-27-08 journey implementation and device review - default: the v1
  preferred concept names and meanings are fixed; a preferred-name or meaning
  change requires a new application-language schema version.
- Quantitative product analytics or hosted usability telemetry - trigger: an
  explicit privacy, transport, retention, and authority contract - default:
  deterministic local fixtures and human review only.
- Release/version target - trigger: all ten stories and the exit audit are
  complete plus a separate owner decision - default: remain unreleased.
