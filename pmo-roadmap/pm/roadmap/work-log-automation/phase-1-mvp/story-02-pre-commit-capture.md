# WLA-1-02 - Capture consented staged payloads in pre-commit

- **Project:** work-log-automation
- **Phase:** 1
- **Status:** backlog
- **Depends on:** WLA-1-01, WLA-0-06
- **Unblocks:** WLA-1-03, WLA-1-05
- **Owner:** unassigned

## Problem

The staged diff is authoritative only while `pre-commit` is running. The
framework needs to capture that exact state when consent is present, while
leaving denied-consent commits untouched.

## Scope

- **In:** Config flags, consent parsing, bounded staged diff capture, pending
  payload creation under `.git/pmo-work-log/`, and success banner extension.
- **Out:** Final log append, summarizer calls, and installer changes.

## Acceptance criteria

- [ ] Logging is disabled unless `PMO_WORK_LOG_ENABLED=1`.
- [ ] Consent must be explicitly `yes`; missing or `no` creates no pending
  work-log payload.
- [ ] Pending payload includes contract text, reasons, exclusions, branch,
  staged paths, diff stat, bounded unified diff, and capture timestamp.
- [ ] Pending payload includes enough identity data to detect stale or mismatched
  finalization attempts: index tree, branch, repo path, and capture timestamp.
- [ ] Capture does not mutate the index or working tree.
- [ ] Capture failure follows the configured MVP policy and prints an actionable
  message.

## Test plan

- **Unit:** `bash -n pmo-roadmap/hooks/pre-commit`.
- **Integration / Cypress:** Temporary git repo with staged file and consented
  contract; assert pending payload exists before commit finalization path.
- **Manual / device:** Inspect pending payload and confirm it contains staged
  changes, not unstaged changes.

## Notes / open questions

The diff bound should be configurable, with a clear truncation marker included
in the payload so the final summary does not imply complete diff coverage.
History-rewrite and stale-pending behavior follows WLA-0-06.
