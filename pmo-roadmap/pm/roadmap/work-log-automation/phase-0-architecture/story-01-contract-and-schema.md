# WLA-0-01 - Define the consent and log-entry contract

- **Project:** work-log-automation
- **Phase:** 0
- **Status:** backlog
- **Depends on:** none
- **Unblocks:** WLA-0-02, WLA-0-03, WLA-0-04
- **Owner:** unassigned

## Problem

The framework currently requires a fresh `.tmp/CONTRACT.md`, but it does not
distinguish "this commit satisfies the PMO rules" from "this commit may be
written into my long-term work log." Work-log consent needs its own explicit
contract surface, reasons, and exclusions so logging is legitimate and
auditable.

## Scope

- **In:** Canonical contract language, required consent fields, expected
  parsing behavior, log-entry markdown schema, and example entries.
- **Out:** Hook implementation, model prompt tuning, or installation changes.

## Acceptance criteria

- [ ] `PMO-CONTRACT.md` documents a work-log consent section with a checkbox,
  explicit `**Work-log consent:** yes|no` value, reasons, and exclusions.
- [ ] The contract explains that no daily work-log entry is produced without
  explicit `yes` consent.
- [ ] A stable markdown log-entry schema is documented with timestamp, repo,
  branch, commit hash, staged files, consent reasons, technical summary,
  verification, and exclusions.
- [ ] The schema includes stable section markers or front matter so future
  agents can read the log predictably.
- [ ] The schema distinguishes roadmap evidence from daily architect log
  summaries.
- [ ] Examples cover consent granted, consent denied, and docs-only/n/a cases.

## Test plan

- **Unit:** `bash -n pmo-roadmap/hooks/pre-commit` once parsing hooks exist.
- **Integration / Cypress:** n/a.
- **Manual / device:** Review generated examples against the user requirement:
  `~/.work/log/YYYY-MM-DD/{project}-work-summary.log`.

## Notes / open questions

The parser must require `**Work-log consent:** yes` rather than inferring
consent from checkbox count. Reasons should be preserved verbatim in the
pending payload so the summarizer cannot invent consent after the fact.

## Proposed contract block

The work-log block should be outside the canonical seven PMO checkboxes. It is
not counted by `EXPECTED_BOXES`.

```markdown
## Work-log consent

**Work-log consent:** yes | no

**Work-log reasons:**
- {Why this commit is valid long-term technical work evidence, or "n/a".}

**Work-log exclusions:**
- {Paths, topics, or details that must not appear in the daily log, or "none".}
```

## Proposed log-entry schema

The final daily log entry should be stable markdown with light front matter.

```markdown
---
kind: pmo-work-log-entry
schema_version: 1
timestamp: YYYY-MM-DDTHH:MM:SSZ
project: {project-slug-or-override}
repo: {absolute-repo-path}
branch: {branch}
commit: {sha}
source: pmo-roadmap
summary_mode: deterministic | llm-deferred
---

## Commit

- **Subject:** {commit subject}
- **Staged files:** {count}
- **Log identity:** {project}-{pathhash}, or configured override

## Consent

**Work-log consent:** yes

**Reasons:**
- {verbatim reason from contract}

**Exclusions:**
- {verbatim exclusions from contract}

## Technical Summary

- {deterministic or summarized technical work delivered}

## Files Changed

| Status | Path |
|---|---|
| M | `path/to/file` |

## Verification And Evidence

- **Roadmap story:** {story IDs detected, or "n/a"}
- **Evidence files:** {paths detected, or "n/a"}
- **Tests:** {contract-provided pointer, or "not parsed"}

## Follow-ups

- {known follow-up from summary, or "none recorded"}
```

Denied-consent commits produce no daily log entry. They may produce a
diagnostic in the hook output, but no durable architect-log record.
