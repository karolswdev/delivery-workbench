# WLA-1-04 - Install, update, and document the MVP hooks

- **Project:** work-log-automation
- **Phase:** 1
- **Status:** backlog
- **Depends on:** WLA-1-03, WLA-0-06
- **Unblocks:** WLA-1-05
- **Owner:** unassigned

## Problem

The framework is only useful if the new hook lifecycle installs cleanly into
consumer projects and does not overwrite local policy. The docs must make the
opt-in behavior and daily log path obvious.

## Scope

- **In:** `install.sh`, `update.sh`, README, CLAUDE snippet, and file map
  updates for new hook files and config variables.
- **Out:** Consumer-project rollout and LLM summarizer docs.

## Acceptance criteria

- [ ] `install.sh` copies `hooks/post-commit` to `.githooks/post-commit`.
- [ ] `update.sh` refreshes canonical hook files and still preserves local
  config/extensions.
- [ ] Install/update detects an existing non-framework `.githooks/post-commit`
  and refuses, warns, or follows an explicit composition path rather than
  overwriting it silently.
- [ ] README documents `PMO_WORK_LOG_ENABLED`, project slug override, log dir
  override, and consent behavior.
- [ ] README documents the upgrade recipe for projects with customized
  `PMO-CONTRACT.md`: diff, merge the consent block manually, then update.
- [ ] CLAUDE snippet tells agents that daily logging requires explicit consent.
- [ ] Re-running install/update remains idempotent.

## Test plan

- **Unit:** `bash -n pmo-roadmap/install.sh pmo-roadmap/update.sh`.
- **Integration / Cypress:** Install/update into a temporary repo and assert
  `.githooks/pre-commit` and `.githooks/post-commit` exist and are executable.
- **Manual / device:** Read a fresh install output and confirm the operator can
  discover how to enable work logging.

## Notes / open questions

Do not silently enable logging during install. The first release should require
an explicit config line in the target project. Treat existing `post-commit`
hooks as project-owned unless they match the framework's installed hook marker.
