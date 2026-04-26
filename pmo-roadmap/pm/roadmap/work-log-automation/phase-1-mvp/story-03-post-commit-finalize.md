# WLA-1-03 - Finalize daily log entries in post-commit

- **Project:** work-log-automation
- **Phase:** 1
- **Status:** backlog
- **Depends on:** WLA-1-02, WLA-0-06
- **Unblocks:** WLA-1-04, WLA-1-05
- **Owner:** unassigned

## Problem

A durable daily log entry should exist only after Git creates the commit.
`post-commit` can attach the final commit hash and append the entry to the
daily log path.

## Scope

- **In:** New canonical `post-commit` hook, deterministic markdown summary,
  date/project log path, collision-resistant log identity, pending cleanup, and
  idempotency protection.
- **Out:** LLM summarization in the commit path and redaction plugins.

## Acceptance criteria

- [ ] `post-commit` reads the pending payload and current `HEAD` metadata.
- [ ] The hook appends to `$HOME/.work/log/YYYY-MM-DD/{project}-work-summary.log`.
- [ ] The entry includes timestamp, repo, branch, commit hash, consent reasons,
  files changed, deterministic technical summary, verification pointers, and
  exclusions.
- [ ] The default log filename uses a collision-resistant identity, with a
  documented project override.
- [ ] The pending payload is removed after a successful append.
- [ ] Running `post-commit` with no pending payload exits successfully.
- [ ] Re-running `post-commit` does not duplicate the same entry.

## Test plan

- **Unit:** `bash -n pmo-roadmap/hooks/post-commit`.
- **Integration / Cypress:** Temporary repo commit with consent; assert one log
  entry with the final commit hash.
- **Manual / device:** Commit once, inspect the daily log, then run the hook
  again manually and confirm no duplicate entry appears.

## Notes / open questions

Project slug should follow WLA-0-06: config first, then unambiguous roadmap
slug, then repo basename, plus a short path hash by default. The first
implementation must avoid model calls so `post-commit` remains fast.
