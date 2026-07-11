# Work Log Automation - Roadmap

**Last updated:** 2026-07-11 (Phase 18 — Every element answers CLOSED 4/4 the same day as Phase 17: cards and holds carry receipts + links, `dw story show` browses one story whole, MCP gained dw_board/dw_holds/dw_story_show, and docs/interop.md pins the whole read surface. Earlier the same day: Phase 17 — Work that waits CLOSED 6/6, the hold vocabulary with mandatory reasons, phase pause/resume, honest `dw next` + `dw holds`, and the kanban board with guarded drag moves).
**Current phase:** n/a.
**Status:** active — framework shipped through v1.8.0 (phases 0-11); the gate's guarantees hold locally, remotely, across distribution channels, for agents, and across the pull-request boundary.

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
| 19 | A stranger arriving from PyPI, Homebrew, or GitHub meets a package that states its case: complete metadata, a README that matches the shipped surface, and phases 16-18 published as v1.13.0. | not-started | [phase-19-front-door](./phase-19-front-door/) |

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

## Active extension

No phase is open. Phase 11 (Contribution Rails) shipped: the
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
redaction, remote sync, hosted collaboration, and DOM-level UI tests —
each parked deliberately in the phase final summaries. Any of it would
open as a new phase through the same gate that shipped the ones above.

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
