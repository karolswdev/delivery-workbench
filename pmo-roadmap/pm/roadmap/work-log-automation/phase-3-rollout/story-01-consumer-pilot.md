# WLA-3-01 - Pilot in one consumer project

- **Project:** work-log-automation
- **Phase:** 3
- **Status:** backlog
- **Depends on:** WLA-2-03
- **Unblocks:** WLA-3-02, WLA-3-03
- **Owner:** unassigned

## Problem

Temporary-repo tests prove mechanics, but the feature's real value is whether a
developer can commit normally and get a useful daily architect log.

## Scope

- **In:** Install/update into one chosen consumer project, opt-in config, one
  consented commit, one denied-consent commit, and review of generated logs.
- **Out:** Broad rollout to every project.

## Acceptance criteria

- [ ] Consumer project has logging enabled through project config.
- [ ] A consented commit writes a schema-conformant daily log entry with repo,
  branch, commit, reasons, files changed, verification/evidence pointers, and
  follow-ups.
- [ ] A denied-consent commit writes no entry.
- [ ] Any project-specific exclusions are documented.
- [ ] Evidence captures the exact commands and resulting log excerpts.
- [ ] Pilot review covers at least two separate work sessions or explicitly
  records why a longer review is deferred.

## Test plan

- **Unit:** n/a.
- **Integration / Cypress:** Real consumer project commits.
- **Manual / device:** Read the resulting daily log as a next-day handoff.

## Notes / open questions

Choose a project with active technical work, not a docs-only repo, so the
summary has meaningful diff and verification content. A one-commit pilot proves
mechanics; a two-session pilot starts to prove memory value.
