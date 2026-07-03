# WLA-7-04 - Package the Claude Code plugin

- **Project:** work-log-automation
- **Phase:** 7
- **Status:** done
- **Depends on:** WLA-7-01
- **Unblocks:** WLA-7-05, WLA-7-07
- **Owner:** unassigned

## Problem

Today the agent surface reaches Claude Code through copied
`.claude/commands/` files and the managed CLAUDE.md block — install
artifacts, not a distributable. A proper Claude Code plugin (manifest,
skill, commands, marketplace entry) makes the framework installable
into any Claude Code environment in one step, versioned with the
framework, without cloning this repo.

## Scope

- **In:** `plugin/` (or `.claude-plugin/`) package: plugin manifest
  with name/version/description, a Delivery Workbench **skill**
  (SKILL.md teaching orientation, story lifecycle, contract/gate
  operation, evidence capture, workbench usage, and refusal-state
  recovery), the four slash commands migrated in, a marketplace.json
  so `claude plugin` can install from this repo, install/update
  documentation, and a validation test that the plugin's declared
  files exist and its instructions match the shipped CLI (parity with
  agent-docs canon).
- **Out:** MCP servers, hooks that gate outside git, publishing to
  registries beyond this repo's marketplace file.

## Acceptance criteria

- [ ] The plugin manifest validates and declares skill + commands.
- [ ] The skill teaches the full operating loop (orient → work →
  prove → gate) with the same vocabulary as the managed block, and a
  parity test fails when they drift.
- [ ] `claude plugin install` from this repo's marketplace succeeds
  locally (captured), and the commands run in a fixture repo.
- [ ] install.sh/update.sh continue to work for non-plugin users; the
  README explains when to use which.
- [ ] Plugin version tracks the framework version in one place.

## Test plan

- **Unit:** manifest schema/parity checks in the core suite where
  practical.
- **Integration:** a plugin-validation script wired into CI.
- **Manual / device:** real `claude plugin install` + slash-command
  smoke in a fixture repo.
