# WLA-0-02 - Design the capture/finalize hook lifecycle

- **Project:** work-log-automation
- **Phase:** 0
- **Status:** backlog
- **Depends on:** WLA-0-01
- **Unblocks:** WLA-0-03, WLA-0-04
- **Owner:** unassigned

## Problem

The desired summary needs the staged diff at the moment the hook fires, but a
`pre-commit` hook cannot know the final commit hash and should not create
durable log entries for commits that later fail. The framework needs a two-step
lifecycle that captures exact inputs early and appends only after the commit
exists.

## Scope

- **In:** `pre-commit` capture behavior, pending payload location under `.git`,
  `post-commit` finalize behavior, cleanup rules, idempotency, abort handling,
  and commit metadata attachment.
- **Out:** The actual summarizer prompt, remote log storage, or end-of-day
  rollups.

## Acceptance criteria

- [ ] The design captures `git diff --cached --name-status`, `--stat`, and a
  bounded unified diff while the index still represents the commit.
- [ ] The pending payload includes the contract file, repo root, branch, project
  slug, staged paths, and capture timestamp.
- [ ] Durable append happens in `post-commit`, after `git rev-parse HEAD`
  returns the final commit.
- [ ] If the commit aborts after `pre-commit`, no daily log entry is appended.
- [ ] Pending payloads are cleaned up after successful finalization and safely
  overwritten or expired on a later attempt.
- [ ] Hook behavior is Bash 3.2 compatible on macOS and Linux.

## Test plan

- **Unit:** Shellcheck if available; always run `bash -n` on hook scripts.
- **Integration / Cypress:** Create a temporary git repo, install hooks, stage
  files, run commits for consent yes/no, and assert pending/final log behavior.
- **Manual / device:** Verify a deliberately aborted commit leaves no durable
  daily log entry.

## Notes / open questions

The pending path should be inside `.git/pmo-work-log/` rather than `.tmp/`,
because `.tmp/CONTRACT.md` is deleted on success and is intentionally ignored.
Use one pending file per attempted commit, plus a `latest` pointer only if it
simplifies cleanup.
