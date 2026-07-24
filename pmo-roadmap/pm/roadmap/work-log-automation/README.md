# Work Log Automation - Roadmap

**Last updated:** 2026-07-24 (Phase 27 complete 3/10: the product language, whole-task journeys, and delivery-shaped first-arrival/setup flow are evidence-backed).
**Current phase:** [Phase 27 - Usability Improvements](./phase-27-usability-improvements/) (active, 3/10).
**Status:** Delivery Workbench now leads with healthy ordinary work and one pure shared setup view that compares ordinary, bounded, and optional-program delivery without preselection. Workbench and human CLI agree on scope/readiness/effects; exact details remain available, every optional save/start keeps separate permission, and the fresh-wheel no-program consumer stays dormant. Task-shaped plan/workflow authoring is next; landing and release remain separate decisions.

## Vision

Work Log Automation extends `pmo-roadmap` from a commit-time hygiene gate
into a durable architect's work ledger. When a commit has explicit contract
consent, the framework captures the staged diff at hook time, summarizes the
technical value delivered, and appends a compact entry to
`~/.work/log/YYYY-MM-DD/{project}-work-summary.log`.

The log is not a replacement for roadmap evidence, commit messages, or PRs.
It is a cross-project daily record: what changed, why it mattered, what was
verified, and which consented contract made the entry legitimate.

The design standard is: opt-in by contract, exact at the moment of commit,
durable after the commit exists, private by default, and mechanically boring
to install across projects.

The MVP standard is deliberately stricter: no LLM call in the commit path.
Commits produce deterministic, schema-conformant entries first; deferred LLM
summarization can improve those entries after the lifecycle is proven.

## Source canon

- `pmo-roadmap/templates/roadmap-builder.md`
- `pmo-roadmap/templates/PMO-CONTRACT.md`
- `pmo-roadmap/hooks/pre-commit`
- `pmo-roadmap/install.sh`
- `pmo-roadmap/update.sh`
- User requirement, 2026-04-25: consented commit summaries should flow into
  `~/.work/log/{yyyy-mm-dd}/{project-work-summary}.log` as a long-term
  architect's log of delivered value.
- Claude Opus architecture review, 2026-04-25:
  `/tmp/claudes-honest-but-supportive-opinion`.
- User requirement, 2026-07-01: make mundane PMO maintenance tasks such as
  creating phases, reading done trees, and listing phase contents available
  through a small CLI.
- User requirement, 2026-07-01: plan the next PMO Workbench interaction layer
  comprehensively and dogfood the PMO roadmap by giving that work its own
  phase, stories, sequencing, risks, and proof gates.
- User requirement, 2026-07-02: run a comprehensive architectural review of
  the framework as "rails" for agentic development (ease of use,
  transparency, auditability, value) and dogfood the resulting hardening
  plan as its own phase.
- Claude Fable architecture review, 2026-07-02: verification-vs-choreography
  gap, gate-logic drift bypasses, ephemeral contract audit trail, evidence
  backfill risk, missing agent surface, and dogfood-integrity findings that
  seed Phase 6.
- User requirement, 2026-07-15: comprehensively assess the whole solution,
  then push usability, interoperability, and agent-development guardrails
  forward by opening and executing the next phase from the audit findings.
- User follow-up, 2026-07-15: move beyond summarizing the briefing and push
  it into something operational; Phase 23 turns one observed recommendation
  into one explicit, stale-safe, allowlisted step.
- User requirement and correction, 2026-07-17: Delivery Workbench **can
  coordinate** agent work and comes with a rich visual editor for exact
  orchestration rules—research agents, dependencies, checks/failures, output
  conventions, budgets, approvals, and the rest of the run contract. A score
  is configuration; a separate grant is authority.
- [Solution overview](../../../../docs/solution-overview.md), 2026-07-15:
  the whole-system map, evidence snapshot, strengths, gaps, and rationale for
  Phase 22.
- Comparative study, 2026-07-18: AgentWrapper/agent-orchestrator (observation
  loops, activity states, CDC liveness, durable notifications, adapter
  roster) and microsoft/agent-framework-go (typed HITL request ports,
  outstanding requests in checkpoints, exact-match standing approval rules,
  privacy-defaulted telemetry) — absorbed under the consent spine as
  Phase 25.
- User requirement and correction, 2026-07-18: auto-nudging is supported —
  Delivery Workbench may route observed signals back to agents
  automatically, provided every nudge is score-declared, grant-authorized,
  budget-bounded, and ledgered.
- User requirement, 2026-07-21: push beyond bounded individual runs toward
  independently executed, rule-governed programs that can auto-advance a
  roadmap. The product destination combines reusable visually authored
  workflows, quality/evidence gates, repair and integration routes, and
  explicit autonomy policy rather than hiding a perpetual agent loop.
- User clarification, 2026-07-22: the destination is a configurable autonomous
  delivery organization operating across multiple stories and phases, not a
  linear next-story pipeline. Visually authored or file-configured workflows
  assign specific implementer and independent verifier agents and can include
  bounded debate corners, verifier-of-verifier audits, master architects,
  review/repair/escalation loops, and policy-authorized integration/roadmap
  advancement with no required human act after the continuous program grant.
- User clarification, 2026-07-22: autonomy is an optional capability, not a
  redefinition of Delivery Workbench. The complete vanilla product remains a
  first-class way to work, Phase 24/25 bounded orchestration remains an
  independent opt-in, and only an explicit program policy plus a separate
  program grant activates the Phase 26 layer.
- User direction, 2026-07-23: the next phase must make the application layer
  speak like a practical delivery tool, not expose its internal protocol
  vocabulary. Exact engineering names such as grant, ledger, preview token,
  content boundary, and certification may remain in code, machine contracts,
  architecture, and explicit audit views; everyday Program Studio, live
  operation, setup, help, errors, onboarding, and product docs must instead use
  consistent plain terms for the plan, team, work, review, decision, blocker,
  permission, progress, cost, and next delivery step.
- Comparative study (sidequest), 2026-07-19: ogulcancelik/herdr and its
  plugin ecosystem — declarative screen-state manifests with auditable
  `agent explain` derivation (strict blocked-detection, detection firewalled
  from action), herdr-remote's phone approval UX (one-tap closed response
  sets, push collapse, digests) whose transport-equals-authority model is
  explicitly rejected, reviewr's draft-into-input-box review loop, and the
  zero-SDK "CLI is the plugin API" ecosystem flywheel — candidate phase-26
  material recorded in the Phase 25 status.

## Current phase: usability improvements

Phase 27 redesigns the application and information layer around the questions
people actually bring to a delivery tool: What are we delivering? Who is doing
and reviewing it? What passed? What is blocked? Who needs to decide? What can
the work still spend or change? What happens next? Setup, Program Studio, live
operation, help, errors, onboarding, and everyday docs must answer those
questions with one stable product vocabulary and coherent whole-task flows.

This is not a rename pass. Human-facing renderers will project the existing
exact state into plain delivery concepts without changing authority, evidence,
replay, or machine-contract semantics. Exact terms such as grant, ledger,
preview token, content boundary, and certification remain available in code,
architecture, machine contracts, and an explicit technical/audit view.

The product therefore has a progressive, opt-in capability ladder:

1. **Vanilla:** roadmap, evidence, briefing, deliberate step, gate, and
   Workbench flows with no orchestration state or setup.
2. **Bounded orchestration:** one Phase 24/25 score plus one finite run grant,
   with a terminal handoff and no program implied.
3. **Program advisory:** multi-story planning and simulation without dispatch
   or mutation.
4. **Program checkpointed:** autonomous work only between named decision ports.
5. **Program continuous:** autonomous advancement inside one explicit, finite,
   revocable program grant.

These are capabilities, not migrations. Installing or updating Delivery
Workbench never selects a higher tier, creates program state, starts a process
or observer, performs network activity, or makes program setup mandatory. No
program configuration is ordinary healthy state, and the established `status`,
`next`, `step`, `gate`, and Workbench front-door behavior remains compatible.
Phase 27 adds no new autonomy, hosted authority, release, or publication scope.

## Phase index

| Phase | Goal (one line) | Status | Folder |
|---|---|---|---|
| 0 | Lock the contract, lifecycle, and implementation slices before coding | done | [phase-0-architecture](./phase-0-architecture/) |
| 1 | Ship the local, opt-in MVP with pre-commit capture and post-commit append | done | [phase-1-mvp](./phase-1-mvp/) |
| 2 | Harden summarization, privacy controls, and failure behavior | done | [phase-2-hardening](./phase-2-hardening/) |
| 3 | Roll out installer/update/docs support and prove adoption on a consumer project | done | [phase-3-rollout](./phase-3-rollout/) |
| 4 | Add CLI support for routine roadmap maintenance and inspection | done | [phase-4-cli-maintenance-tools](./phase-4-cli-maintenance-tools/) |
| 5 | Ship the rich PMO Workbench interaction layer on top of the existing agent-safe CLI/core without creating a second source of truth. | done | [phase-5-pmo-workbench-interaction-layer](./phase-5-pmo-workbench-interaction-layer/) |
| 6 | Harden the agent rails: single machine-checked gate, durable contract audit trail, first-class agent surface, proportionate ceremony, dogfooded on this repo | done | [phase-6-agent-rails-hardening](./phase-6-agent-rails-hardening/) |
| 7 | Make the framework teachable: audited docs, a Claude Code plugin, first-class assets, and OSS-grade repo hygiene with a versioned release. | done | [phase-7-documentation-mastery](./phase-7-documentation-mastery/) |
| 8 | Make the gate's guarantees hold beyond the local clone: a range verifier that re-checks gate rules over pushed commits, CI wiring that enforces it on every PR, and a real external adoption exercising the rails end-to-end with friction folded back into the framework. | done | [phase-8-remote-verification-and-adoption](./phase-8-remote-verification-and-adoption/) |
| 9 | Make Delivery Workbench installable without cloning this repository: a distribution design contract, a pipx-installable package exposing the bootstrap commands, a proven consumer upgrade path from v1.5.0 rails, a Homebrew formula served from a local tap, and a v1.6.0 release that ships it all. | done | [phase-9-distribution-and-installability](./phase-9-distribution-and-installability/) |
| 10 | Give agents a first-class programmatic surface: a stdlib-only MCP stdio server exposing the dw core as structured JSON tools — orientation, verification, and guarded mutations, never certification — vendored and wired like every other rail, proven against a real client session, and shipped as v1.7.0. | done | [phase-10-agent-interface](./phase-10-agent-interface/) |
| 11 | Extend the gate's guarantees to work that arrives by pull request: a contribution contract defining how gated commits travel through forks and merges, an end-to-end contributor-flow proof with red paths for the merge methods that would corrupt the audit trail, repository enforcement and plain-language contributor docs, and a v1.8.0 release. | done | [phase-11-contribution-rails](./phase-11-contribution-rails/) |
| 12 | Make Delivery Workbench a plug-n-play side rider for every surface a developer works from: one canonical agent brief rendered for Claude Code, Codex, and pi, plus a first-class HoldSpeak integration (roadmap synthesizer, story actuator, Desk presence) - with every step journaled in the moment as the flagship worked example for both ecosystems. | done | [phase-12-holdspeak-symbiosis-and-agent-riders](./phase-12-holdspeak-symbiosis-and-agent-riders/) |
| 13 | Deliver Mission control: the Desk conveyor and the live roadmap. | done | [phase-13-agentic-mission-control](./phase-13-agentic-mission-control/) |
| 14 | Absorb and re-interpret ccgram's operational excellence under the consent spine: hook-driven push, the message layer, topics-as-projects, the driver's craft, guarded file sending. | done | [phase-14-absorbing-ccgram](./phase-14-absorbing-ccgram/) |
| 15 | The local dw-workbench browser grows a mission-control belt: the same feed, correlation, and events the phone and Desk render, now in the read-only roadmap view — no steering (that stays where the consent machinery lives), just the live picture at your desk. | done | [phase-15-mission-control-on-the-workbench](./phase-15-mission-control-on-the-workbench/) |
| 16 | The flagship tree: receipts-first reading — header-mapped tables, status normalization, receipts-first evidence pairing, pointer-driven current phase; the write gate unchanged | done | [phase-16-flagship-tree](./phase-16-flagship-tree/) |
| 17 | Parked work becomes first-class: on-hold with a reason, phase pause/resume, an honest dw next, a holds ledger, and a kanban board in the terminal and on the workbench. | done | [phase-17-work-that-waits](./phase-17-work-that-waits/) |
| 18 | Every element on the board is browsable by machines: cards and holds carry their receipts and links, dw story show browses one story whole, MCP gains the read surface (board, holds, story), and one versioned contract names it all. | done | [phase-18-interop-layer](./phase-18-interop-layer/) |
| 19 | A stranger arriving from PyPI, Homebrew, or GitHub meets a package that states its case: complete metadata, a README that matches the shipped surface, and phases 16-18 published as v1.13.0. | done | [phase-19-front-door](./phase-19-front-door/) |
| 20 | The Telegram interface becomes a first-class group surface: the pane becomes a picture (on demand and live), the buttons become a configurable toolbar and question-steering keyboards, and consent in a group belongs to a person, not a room — the second ccgram absorption (v4.3.11), every feature riding the existing consent spine. | done | [phase-20-group-grows-hands](./phase-20-group-grows-hands/) |
| 21 | Phase 20's interactive surface — screenshots, buttons, per-person consent — reaches every channel as v1.14.0, with the same machinery as the last six releases. | done | [phase-21-landing-v1-14-0](./phase-21-landing-v1-14-0/) |
| 22 | Give every human and agent one deterministic, versioned answer for repository readiness, current work, and the next safe action, shared across every supported surface. | done | [phase-22-agent-briefing](./phase-22-agent-briefing/) |
| 23 | Let a human or agent deliberately apply exactly one current, allowlisted recommendation without copy/paste, stale intent, arbitrary execution, certification, or commit automation. | done | [phase-23-deliberate-step](./phase-23-deliberate-step/) |
| 24 | Delivery Workbench can coordinate a bounded multi-agent run from an exact visually authored score and revocable grant: research, dependencies, context, outputs, checks, failures, budgets, recovery, and human checkpoints. | done | [phase-24-bounded-orchestration](./phase-24-bounded-orchestration/) |
| 25 | Delivery Workbench hears the world outside the run — CI, reviews, merge state, agent activity — records it as durable facts, and under an explicit grant nudges the right agent back to work: observed, bounded, ledgered, revocable. | done | [phase-25-outward-signals](./phase-25-outward-signals/) |
| 26 | Delivery Workbench optionally adds governed autonomous delivery programs across an explicit roadmap scope—without changing vanilla or bounded-run usage—with hierarchical workflows, independent verification, advanced bounded loops, and only the quality, integration, and roadmap acts named by a finite revocable program grant. | done | [phase-26-autonomous-delivery-programs](./phase-26-autonomous-delivery-programs/) |
| 27 | Make Delivery Workbench's everyday application layer speak and behave like a practical delivery tool, with one plain-language vocabulary and coherent task flows across setup, Program Studio, live operation, help, errors, onboarding, and product documentation, while keeping exact protocol terms available in machine contracts, architecture, and explicit audit views. | in-progress | [phase-27-usability-improvements](./phase-27-usability-improvements/) |

## Operating cadence

Every shipping commit for this roadmap updates, in the same commit:

1. The relevant story file header status.
2. The phase's `current-phase-status.md` story-status row and "Where we are".
3. This README's "Last updated" line.
4. Any canonical framework file touched by the story.
5. The evidence file for any story that flips to `done`.

Per `pmo-roadmap/templates/PMO-CONTRACT.md`, the pre-commit hook gates every
commit on a fresh `.tmp/CONTRACT.md`. Once Work Log Automation ships, commits
that opt into logging must also carry explicit work-log consent and reasons.

## Shipped foundation

Work Log Automation and the PMO CLI/core foundation are shipped. The durable
behavior is:

- Work logging is opt-in through `.githooks/pre-commit.config`.
- A commit creates a daily log entry only when the fresh PMO contract says
  `**Work-log consent:** yes`.
- `pre-commit` captures the staged payload under `.git/pmo-work-log/`.
- `post-commit` appends deterministic markdown after Git creates the commit.
- `work-log-summarize` can create bounded companion digests after commits.
- `work-log-read` reads or lists local daily logs.
- `dw` performs routine roadmap inspection, scaffolding, evidence-backed status
  updates, phase closing, drift reporting, and checks.

## Latest extension

Phase 24 (The conductor's score — visual orchestration) is closed at 8/8.
Its completed architecture contract and exact score compiler turn the Phase-22 observation and
Phase-23 one-step lease into a
configurable coordination framework rather than a hidden loop. A rich
Workbench editor authors a tracked, versioned score: research/synthesis/
implementation/review/repair agents, dependencies and concurrency, bounded
context, typed output conventions, exact checks, fail routes, retries,
budgets, approvals, and terminal meanings. One delivered pure compiler owns
schema semantics, stable hashes, diagnostics, and scheduling simulation. The
delivered rich editor adds the complete typed graph/inspector, live Validate
and JSON views, and a fingerprint-bound preview→diff→atomic-save boundary;
opening or saving a score starts nothing. The delivered pure run-plan and
exact approval boundary binds that score to local repo/status/story facts,
capabilities, workspaces, finite budgets, expiry, and permanent exclusions;
an immutable grant plus hash-chained, replayable ledger owns lifecycle,
exclusive claims, revocation, and budget counters. A deterministic conductor
now schedules through the delivered provider-neutral seam: capability-checked
logical profiles, bounded hash-bound packets, concurrent read-only research,
validated synthesis inputs, persistent driver receipts, and distinct isolated
writer worktrees whose scoped diffs require later review. Deterministic fixture
and live Codex adapters prove the seam without making model output a CI oracle.
One replayable tick polls before retry, schedules stable eligible sets within
grant concurrency/resource/budget limits, runs exact contained command and
built-in checks, validates artifact fan-in, consumes fresh declared `dw step`
leases, and records bounded retry/repair/approval/pause/abort/cancel routes.
Crash boundaries recover without duplicate starts, and terminal handoff stays
`awaiting-certification`. The delivered interop layer now returns those exact
models through CLI, MCP, and HTTP, while the rich Workbench Run view explains
the live graph, attempts, agent/check sessions, explicit bounded streams,
artifact lineage, budgets, failure routes, checkpoints, controls, and ledger
without polling or acquiring shell/certification/commit authority. A
real-process fixture crosses each applying adapter, and 32 desktop/mobile
renders cover active, repair, and terminal states. The Python-3.9-built wheel
exam then proved the entire configured score: two concurrent research agents,
typed/cited fan-in, synthesis, isolated implementation, planted crash recovery
with zero duplicate starts, one exact fail→repair→recheck route, six compiler
and five runtime red cases, operator-only certification/commit, and terminal
`awaiting-certification`. A separate authenticated live Codex specimen proved
the real driver seam. See the
[Phase 24 final summary](./phase-24-bounded-orchestration/final-summary.md) and
[visual orchestration contract](../../../../docs/orchestration.md).

Phase 23 (The handrail — one deliberate step) is closed at 5/5. It keeps
Phase 22's status model pure while binding its one recommendation to a
deterministic token over the complete briefing. The delivered `dw step`
core/CLI surface previews and explicitly applies at most one closed-table
action, re-reading state first and permanently refusing arbitrary commands,
certification, commit, project choice, and automatic loops. Its delivered
result separates success, child failure, interruption, spawn failure, and
non-started refusal; streams are bounded, consumed tokens cannot replay, and
every started child emits one content-safe correlation event. The same
preview/result now crosses CLI, MCP, and HTTP byte-for-byte through
thin adapters whose apply schemas accept no caller-supplied argv; a fresh
installed fixture proves exact-token success, replay/injection refusal, and
the certification/commit exclusions. The Workbench now exposes that lease as
a separate review→confirm act boundary, and generated riders require a fresh
exact token, preserve manual seams, and stop after one receipt. A wheel-
installed consumer separately authorizes seven CLI/MCP/HTTP actions, proves
same-id stale refusal without a child or event, and keeps certification and
commit manual through a verified fixture commit. See
[the Phase 23 status](./phase-23-deliberate-step/current-phase-status.md) and
[final summary](./phase-23-deliberate-step/final-summary.md).

Phase 22 (The briefing — one answer before agents act) is closed. It turned
the audit in `docs/solution-overview.md` into one deterministic,
versioned, read-only status model shared by CLI, MCP, HTTP, the browser,
and generated agent riders. The model composes existing authorities; it
does not invent a second gate or automate certification. See
[phase-22-agent-briefing/current-phase-status.md](./phase-22-agent-briefing/current-phase-status.md)
and [the final summary](./phase-22-agent-briefing/final-summary.md).

The most recent shipped foundation is v1.14.0: Phase 20 made the Telegram
interface a first-class group surface (screenshots, live pictures,
configurable buttons, question steering, and per-person consent), and
Phase 21 landed it across the release channels. Phases 16-19 delivered
legacy-tree absorption, first-class holds/board, the interop layer, and
the open-source front door. Their receipts remain in their phase folders
and the release narrative is in the root CHANGELOG.

Earlier, Phase 11 (Contribution Rails) shipped: the
contribution contract classifies what survives the fork boundary,
contributor-flow.sh proved the rebase green path and both squash
corruption modes with exact rule ids, the repository is rebase-merge
only, and the contributor docs walk the loop in plain language. See
[phase-11-contribution-rails/final-summary.md](./phase-11-contribution-rails/final-summary.md).

Phase 10 (Agent Interface) shipped: `dw-mcp`, a
stdlib-only MCP stdio server, exposes nine tools as thin adapters
over the shared core with CLI-identical guardrails — certification
and commits deliberately excluded, enforced by test — vendored and
wired through every distribution channel and proven by a live
Claude Code session driving a story backlog → done over MCP alone.
See
[phase-10-agent-interface/final-summary.md](./phase-10-agent-interface/final-summary.md).

Phase 9 (Distribution and Installability)
shipped: the distribution contract keeps per-repo vendored rails
authoritative, the framework builds and installs as
delivery-workbench (pipx and a Homebrew formula from a local tap)
with a defer-to-repo global `dw`, the upgrade path is proven from
real v1.5.0 rails with content-based staleness reporting, and
v1.6.0 is tagged with version parity test-enforced. See
[phase-9-distribution-and-installability/final-summary.md](./phase-9-distribution-and-installability/final-summary.md).

Phase 8 (Remote Verification and Adoption)
shipped: `docs/remote-verification.md` classifies every gate rule
for remote re-derivability, `dw verify` re-checks pushed history
with the gate's own rule ids, the `verify-history` CI job enforces
the sweep on every push and PR, and the first real external
adoption (fridgr) shipped a gated story with its friction triaged
back into the framework. See
[phase-8-remote-verification-and-adoption/final-summary.md](./phase-8-remote-verification-and-adoption/final-summary.md).

Phase 7 (Documentation Mastery) shipped: audit-first documentation
overhaul, a Claude Code plugin packaging the agent surface,
reproducible visual assets, docs CI, and OSS release preparation
ending in the versioned v1.5.0 release. See
[phase-7-documentation-mastery/final-summary.md](./phase-7-documentation-mastery/final-summary.md).

Phase 5 (PMO Workbench Interaction Layer) shipped: the local
workbench serves explorer, health console, trace timeline with agent
handoff, work-log viewer, guarded editor, and the
preview→diff→apply mutation workflow — all through the shared
`dw_pmo` core with Markdown as the only source of truth, behind a
tested localhost runtime boundary, distributed to consumer repos by
install.sh/update.sh. See
[phase-5-pmo-workbench-interaction-layer/final-summary.md](./phase-5-pmo-workbench-interaction-layer/final-summary.md).

Phase 6 (Agent Rails Hardening) shipped: the gate is single-sourced in the
`dw_pmo` core, contracts carry gate-verified stamped facts with durable
trailers and archives, evidence carries captured runs, the agent surface is
installed automatically, ceremony is tier-proportional, adoption is three
commands, and CI runs the full suite on two OSes with shellcheck and a
python-floor job. See
[phase-6-agent-rails-hardening/final-summary.md](./phase-6-agent-rails-hardening/final-summary.md).

Future work remains possible around default-on policy, richer
redaction, remote sync, hosted collaboration, and deeper browser
interaction tests. Those remain deliberately deferred; the next phase has
not been invented implicitly after Phase 22's bounded closeout.

## Project metadata

- **Slug:** `work-log-automation`
- **Story ID prefix:** `WLA`
- **Greenfield?:** yes, for this feature inside the framework.

## Glossary

- **Contract consent:** An explicit per-commit statement in `.tmp/CONTRACT.md`
  that the staged work is appropriate to summarize into the architect log.
- **Capture:** The hook-time snapshot of contract, staged file metadata, and
  staged diff.
- **Finalize:** The post-commit step that adds commit hash/message and writes
  the durable log entry.
- **Summarizer adapter:** The command boundary that can call `codex` or another
  CLI without making the hook depend on one vendor or prompt shape.
- **Log identity:** The project-specific filename stem used under
  `~/.work/log/YYYY-MM-DD/`; defaults should avoid collisions across repos.
