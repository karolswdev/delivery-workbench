# Work Log Automation - Roadmap

**Last updated:** 2026-04-25.
**Current phase:** [phase-0-architecture](./phase-0-architecture/current-phase-status.md)
**Status:** planning.

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

## Phase index

| Phase | Goal (one line) | Status | Folder |
|---|---|---|---|
| 0 | Lock the contract, lifecycle, and implementation slices before coding | in-progress | [phase-0-architecture](./phase-0-architecture/) |
| 1 | Ship the local, opt-in MVP with pre-commit capture and post-commit append | not-started | [phase-1-mvp](./phase-1-mvp/) |
| 2 | Harden summarization, privacy controls, and failure behavior | not-started | [phase-2-hardening](./phase-2-hardening/) |
| 3 | Roll out installer/update/docs support and prove adoption on a consumer project | not-started | [phase-3-rollout](./phase-3-rollout/) |

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
