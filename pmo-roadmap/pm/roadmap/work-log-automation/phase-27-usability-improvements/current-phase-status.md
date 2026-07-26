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
- [x] Workbench, human CLI output, notifications, help, errors, onboarding, and
  everyday docs use the same product terms; machine JSON and explicit
  technical/audit views retain exact engineering language (WLA-27-08).
- [x] Setup, authoring, live operation, decisions, and technical inspection are
  usable by keyboard, at narrow and wide viewports, and with meaningful
  structure/labels and stable focus (WLA-27-09).
- [x] A fresh installed-wheel exam completes the canonical journeys, proves
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
| WLA-27-08 | Make every everyday word agree | done | [story-08-make-every-everyday-word-agree](./story-08-make-every-everyday-word-agree.md) | [evidence-story-08](./evidence-story-08.md) |
| WLA-27-09 | Harden keyboard, screen-size, and assistive use | done | [story-09-harden-keyboard-screen-size-and-assistive-use](./story-09-harden-keyboard-screen-size-and-assistive-use.md) | [evidence-story-09](./evidence-story-09.md) |
| WLA-27-10 | Prove the redesigned application end to end | done | [story-10-prove-the-redesigned-application-end-to-end](./story-10-prove-the-redesigned-application-end-to-end.md) | [evidence-story-10](./evidence-story-10.md) |

## Where we are

Phase 27 is complete 10/10. One Python-floor installed consumer begins with
ordinary status, current work, next-step inspection, and setup while optional
policy, run/program stores, and processes remain absent. The same consumer then
deliberately authors lossless optional policy, resolves a real bounded human
decision, permanently stops a second bounded run, preflights exact team/review/
effects/limits, separately starts the program, and completes all thirteen
canonical journeys.

Independent `needs-repair` → repair → `pass`, preserved council dissent, nine
conductor and eighteen delivery-boundary crash recoveries, 3/3 completed
stories, and 203 ledger events equal to 203 SSE events prove the readable and
exact views together. Five planted report corruptions refuse. The acceptance
transcript records four explicit authority confirmations, thirteen safe
refusal paths, zero unresolved dead ends, and zero reserved engineering terms
in everyday regions.

All 499 core tests pass. Firefox 152 passes 88 retained wide/narrow renders,
thirteen keyboard/focus/semantic journey exams, 26 DOM audits, and 92
assertions. Python 3.9 builds and installs the wheel/sdist and passes every
packaged delivery mode; docs, parity, upgrade, history, and distribution
entry points are green. Exact proof is in
[evidence-story-10](./evidence-story-10.md), the phase outcome is in
[final-summary](./final-summary.md), and the owner snapshot is in
[handover](./handover.md). No landing or release action was inferred.

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
- 2026-07-25 - Add `delivery-workbench-presentation@1` as the single pure
  renderer-facing projection for status, roadmap steps, bounded/program live
  delivery, start and action review, and notifications; it groups canonical
  facts but explicitly starts no work, writes no state, selects no next work,
  and grants no permission - shared-language/source-of-truth boundary -
  WLA-27-08.
- 2026-07-25 - Account for every WLA-27-01 surface in an executable census:
  migrate fifteen everyday or mixed surfaces and retain three exact
  architecture/reference surfaces as technical/audit, with no unclassified
  remainder - whole-surface completion boundary - WLA-27-08.
- 2026-07-25 - Lead every human path with the ordinary task and outcome while
  keeping commands, paths, identities, hashes, tokens, states, source facts,
  and raw machine documents under the explicit `Technical details` label;
  machine JSON/MCP/HTTP/event/persistence contracts remain unchanged -
  readable-default/lossless-audit boundary - WLA-27-08.
- 2026-07-25 - Give route changes and background updates different focus
  contracts: navigation focuses and announces the destination heading, while
  refresh, polling, SSE, and compiler redraws restore the active control -
  predictable-focus boundary - WLA-27-09.
- 2026-07-25 - Announce only a changed ledger head and suppress duplicate
  poll/SSE versions and stable reconnect facts; interactive controls never sit
  inside a chatty live region - discoverable-without-flooding boundary -
  WLA-27-09.
- 2026-07-25 - Keep disclosures native and reviews non-modal; a safe Escape
  dismissal returns to the exact opener and retains in-memory draft input,
  while every existing preview/apply authority boundary remains unchanged -
  keyboard-without-new-authority boundary - WLA-27-09.
- 2026-07-25 - Fix the reviewed viewports at 1440×900 and 390×844, require
  locally owned overflow and no horizontal page scroll, and use Firefox's
  native page zoom to overcome its 500-pixel WebDriver outer-window floor
  while retaining exact unzoomed screenshots - reproducible viewport boundary
  - WLA-27-09.
- 2026-07-25 - Bind the dated assistive-use record to all thirteen canonical
  journey/state IDs and reject missing coverage, mismatched states, viewport
  drift, incomplete review notes, or a failed review result - accessibility is
  executable story evidence rather than a closeout waiver - WLA-27-09.
- 2026-07-25 - Compose the Phase 27 exit proof over one execution of the
  existing Phase 26 autonomous exam, then bind its production observations to
  the thirteen canonical journey IDs - the usability layer cannot fork or
  weaken delivery, authority, recovery, or adapter semantics - WLA-27-10.
- 2026-07-25 - Perform ordinary status, step, next-work, and setup inspection
  on the same installed consumer before authoring optional policy; assert an
  empty healthy inventory, absent stores/process start, and an unchanged file
  snapshot - a second no-program fixture remains a backstop, not a substitute
  for the ordered journey - WLA-27-10.
- 2026-07-25 - Render the acceptance transcript directly from
  `journeys-v1.json`, scan every everyday string against the reserved-language
  contract, and reject five planted report corruptions - friendly prose cannot
  manufacture a pass without the corresponding production fact - WLA-27-10.
- 2026-07-25 - Record thirteen journey checkpoints, four authority
  confirmations, thirteen safe refusals, zero transcript dead ends, and zero
  reserved everyday terms without subtracting them from the differently
  defined pre-redesign screen baseline - measured friction must not become a
  fabricated improvement score - WLA-27-10.
- 2026-07-25 - Close Phase 27 after the full core, browser, docs, parity,
  package, upgrade, history, and distribution audit while leaving version,
  commit, merge, tag, release, publication, deployment, and landing to separate
  owner decisions - phase completion is evidence, not release authority -
  WLA-27-10.

## Decisions deferred

- Channel-specific microcopy refinements - trigger: a concrete journey defect
  or observed user-research finding - default: the v1 preferred concept names
  and meanings are fixed; a preferred-name or meaning change requires a new
  application-language schema version.
- Quantitative product analytics or hosted usability telemetry - trigger: an
  explicit privacy, transport, retention, and authority contract - default:
  deterministic local fixtures and human review only.
- Release/version target - trigger: a separate owner landing/release decision
  after reviewing this closeout - default: remain unreleased.
