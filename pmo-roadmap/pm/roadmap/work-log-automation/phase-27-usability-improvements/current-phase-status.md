# Phase 27 - Usability Improvements

**Last updated:** 2026-07-23.

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

- [ ] `docs/product-language.md` defines one ordinary product vocabulary, the
  everyday/technical-view boundary, and a lossless mapping to existing exact
  semantics; executable language checks reject drift (WLA-27-01).
- [ ] Versioned whole-task journeys and deterministic fixtures cover arrival,
  setup, plan/team/review design, live progress, a blocked decision, recovery,
  completion, and technical inspection before UI implementation begins
  (WLA-27-02).
- [ ] A fresh user can understand the healthy no-program state, choose the
  optional delivery capability deliberately, and finish or leave setup without
  hidden writes or internal protocol vocabulary (WLA-27-03).
- [ ] Program Studio makes delivery-plan/workflow authoring and team/review
  design understandable while round-tripping the existing exact configuration
  without semantic loss (WLA-27-04, WLA-27-05).
- [ ] Live operation answers the seven operator questions from the Phase 26
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
| WLA-27-01 | Contract the everyday product language | backlog | [story-01-contract-the-everyday-product-language](./story-01-contract-the-everyday-product-language.md) | - |
| WLA-27-02 | Define whole-task journeys and usability proof | backlog | [story-02-define-whole-task-journeys-and-usability-proof](./story-02-define-whole-task-journeys-and-usability-proof.md) | - |
| WLA-27-03 | Give first-time users a delivery-shaped front door | backlog | [story-03-give-first-time-users-a-delivery-shaped-front-door](./story-03-give-first-time-users-a-delivery-shaped-front-door.md) | - |
| WLA-27-04 | Make plan and workflow authoring task-shaped | backlog | [story-04-make-plan-and-workflow-authoring-task-shaped](./story-04-make-plan-and-workflow-authoring-task-shaped.md) | - |
| WLA-27-05 | Make teams and review rules understandable | backlog | [story-05-make-teams-and-review-rules-understandable](./story-05-make-teams-and-review-rules-understandable.md) | - |
| WLA-27-06 | Make live delivery explain progress and next steps | backlog | [story-06-make-live-delivery-explain-progress-and-next-steps](./story-06-make-live-delivery-explain-progress-and-next-steps.md) | - |
| WLA-27-07 | Turn decisions, blockers, permissions, and cost into actions | backlog | [story-07-turn-decisions-blockers-permissions-and-cost-into-actions](./story-07-turn-decisions-blockers-permissions-and-cost-into-actions.md) | - |
| WLA-27-08 | Make every everyday word agree | backlog | [story-08-make-every-everyday-word-agree](./story-08-make-every-everyday-word-agree.md) | - |
| WLA-27-09 | Harden keyboard, screen-size, and assistive use | backlog | [story-09-harden-keyboard-screen-size-and-assistive-use](./story-09-harden-keyboard-screen-size-and-assistive-use.md) | - |
| WLA-27-10 | Prove the redesigned application end to end | backlog | [story-10-prove-the-redesigned-application-end-to-end](./story-10-prove-the-redesigned-application-end-to-end.md) | - |

## Where we are

Phase 27 is OPEN 0/10. Phase 26 is merged and local `main` is synchronized with
the remote; this branch contains only the new roadmap plan. WLA-27-01 is the
first implementation story, followed by executable journey fixtures in
WLA-27-02. Onboarding, plan authoring, and team/review design can then proceed
in parallel before the live-operation, consistency, accessibility, and exit
proof slices. There are no known blockers.

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

## Decisions deferred

- Final ordinary labels and microcopy - trigger: WLA-27-01 inventory and
  journey review - default: the handoff terms (`delivery plan`, `team`, `work`,
  `review`, `decision`, `blocker`, `permission`, `progress`, `cost`, `next
  step`) are the working vocabulary.
- Quantitative product analytics or hosted usability telemetry - trigger: an
  explicit privacy, transport, retention, and authority contract - default:
  deterministic local fixtures and human review only.
- Release/version target - trigger: all ten stories and the exit audit are
  complete plus a separate owner decision - default: remain unreleased.
