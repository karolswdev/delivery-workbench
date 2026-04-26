# WLA-1-05 - Add temporary-repo integration coverage

- **Project:** work-log-automation
- **Phase:** 1
- **Status:** backlog
- **Depends on:** WLA-1-02, WLA-1-03, WLA-1-04
- **Unblocks:** Phase 2 hardening
- **Owner:** unassigned

## Problem

Hook behavior is easy to break with small shell changes. The MVP needs tests
that exercise real Git commits in a disposable repo so consent, abort, append,
and cleanup behavior are proven together.

## Scope

- **In:** A bash integration test script or documented manual harness that
  creates a temporary repo, installs the framework, commits with different
  consent states, and inspects pending/log files.
- **Out:** CI integration, cross-shell matrix, or model summarizer tests.

## Acceptance criteria

- [ ] Test covers logging disabled.
- [ ] Test covers logging enabled with consent `yes`.
- [ ] Test covers logging enabled with consent `no`.
- [ ] Test covers a commit aborted after `pre-commit` with no durable append.
- [ ] Test covers no duplicate append from repeated `post-commit`.
- [ ] Test covers `git commit --amend` according to WLA-0-06 policy.
- [ ] Test covers install/update behavior when a non-framework
  `.githooks/post-commit` already exists.
- [ ] Test output is suitable to paste into `evidence-story-05.md`.

## Test plan

- **Unit:** `bash -n` on the test harness.
- **Integration / Cypress:** Run the harness locally.
- **Manual / device:** Inspect the generated temporary log entry for readable
  markdown and correct commit hash.

## Notes / open questions

The harness should not write to the real `~/.work/log` by default. It should
override the log dir into the temporary repo so tests are repeatable. Start the
harness skeleton with WLA-1-02 rather than waiting until all hooks are built.
