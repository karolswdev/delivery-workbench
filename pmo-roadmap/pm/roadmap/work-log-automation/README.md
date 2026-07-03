# Work Log Automation - Roadmap

**Last updated:** 2026-07-02.
**Current phase:** n/a.
**Status:** active — core framework shipped (phases 0-6); Phase 7 makes it teachable.

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

Phase 7 (Documentation Mastery) is the open phase: audit-first
documentation overhaul, a Claude Code plugin packaging the agent
surface, reproducible visual assets, docs CI, and OSS release
preparation ending in a versioned v1.x release. The phase was created
through the workbench's own mutation workflow — see
[phase-7-documentation-mastery](./phase-7-documentation-mastery/current-phase-status.md).

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
open as a new phase through the same gate that shipped these seven.

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
