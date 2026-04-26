# WLA-0-04 - Plan installer, update, and project configuration rollout

- **Project:** work-log-automation
- **Phase:** 0
- **Status:** backlog
- **Depends on:** WLA-0-01, WLA-0-02, WLA-0-03
- **Unblocks:** WLA-0-05
- **Owner:** unassigned

## Problem

The framework is installed into many projects by copying hooks and templates.
Work-log automation must fit that model without clobbering local project
policy, requiring every project to use the same summarizer, or surprising a
fresh clone with unwanted logging.

## Scope

- **In:** Installer changes, updater changes, hook file map, config defaults,
  generated snippet updates, and migration notes for existing consumers.
- **Out:** Enterprise policy management, cloud sync, or retroactive log import.

## Acceptance criteria

- [ ] `install.sh` installs any new canonical hook files needed for the
  lifecycle, including `post-commit` if selected.
- [ ] `update.sh` refreshes canonical hook files but preserves project-owned
  config and local extensions.
- [ ] Existing non-framework `post-commit` hooks are treated as project-owned
  and are not silently overwritten.
- [ ] `.githooks/pre-commit.config` can opt into logging without editing the
  canonical hook.
- [ ] The README documents first-use setup and the exact log path pattern.
- [ ] The CLAUDE/AGENTS snippet tells agents how to grant or deny work-log
  consent honestly.
- [ ] Existing projects that do nothing keep current behavior.

## Test plan

- **Unit:** `bash -n pmo-roadmap/install.sh pmo-roadmap/update.sh` and all hook
  scripts.
- **Integration / Cypress:** Install into a temporary git repo twice, update it,
  and verify hook files/config preservation.
- **Manual / device:** Compare generated hook tree against the README file map.

## Notes / open questions

If `core.hooksPath` points to `.githooks`, adding `post-commit` is simple.
The install/update scripts should treat new canonical hook files the same way
they currently treat `pre-commit`: framework-owned and refreshable.
