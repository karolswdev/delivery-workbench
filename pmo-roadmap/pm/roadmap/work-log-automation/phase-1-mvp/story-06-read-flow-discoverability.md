# WLA-1-06 - Add read-flow and first-run discoverability

- **Project:** work-log-automation
- **Phase:** 1
- **Status:** backlog
- **Depends on:** WLA-1-03, WLA-1-04
- **Unblocks:** Phase 2 hardening
- **Owner:** unassigned

## Problem

A daily architect log only creates value if it is easy to find and read later.
The MVP should not be a write-only artifact hidden in `~/.work/log`.

## Scope

- **In:** README read-flow recipe, hook success banner log path, first-entry
  discoverability, and a simple command example for today's log.
- **Out:** A dedicated CLI reader, weekly reports, dashboards, or search.

## Acceptance criteria

- [ ] Successful finalization prints the log path that received the entry.
- [ ] README documents how to read today's log with shell commands.
- [ ] README documents where logs live and how project identity affects
  filenames.
- [ ] The read-flow documentation is accurate for custom `PMO_WORK_LOG_DIR`.

## Test plan

- **Unit:** n/a.
- **Integration / Cypress:** Temporary-repo test asserts the hook output names
  the log path when an entry is appended.
- **Manual / device:** Follow the README recipe after a temporary-repo commit
  and confirm the entry is readable without inspecting implementation code.

## Notes / open questions

A future reader command may be valuable, but the MVP only needs a reliable
recipe such as listing `$PMO_WORK_LOG_DIR/$(date +%F)/` and opening the
matching project log.
