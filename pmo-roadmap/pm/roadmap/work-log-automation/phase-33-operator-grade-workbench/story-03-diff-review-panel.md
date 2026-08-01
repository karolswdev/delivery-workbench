# WLA-33-03 - Diff review panel

- **Project:** work-log-automation
- **Phase:** 33
- **Status:** done
- **Depends on:** WLA-33-02
- **Unblocks:** WLA-33-09
- **Owner:** unassigned

## Problem

Reviewing what an agent changed means switching to the terminal and
running `git diff`. Operator puts a diff panel next to the session
transcript so you can review and merge without leaving the workspace.
The workbench has guarded edit/apply but no way to see a change
side-by-side before acting on it.

## Scope

- **In:** Add a diff view to the session panel. When a story has
  uncommitted changes (from an agent or from manual edits), show them
  as a unified or side-by-side diff. Provide accept/reject controls
  per file or per hunk that go through the existing preview/token/apply
  boundary. Show the diff of the most recent evidence capture as well.
  A "changes" count badge on the story card when uncommitted work exists.
- **Out:** Syntax highlighting (plain monospace diff in v1). Full
  three-way merge. Automatic staging or committing. Cherry-picking
  across stories.

## Localization hints

- **Affected files:**
  - `pmo-roadmap/workbench/app.js` (new diff-panel module)
  - `pmo-roadmap/workbench/style.css`
  - `pmo-roadmap/lib/dw_pmo/workbench.py` (diff route: `git diff` output for a story's worktree)
  - `pmo-roadmap/tests/workbench-explorer.sh`

## Acceptance criteria

- [ ] When a story has uncommitted changes, a badge appears on its
  board card and the session panel shows a "Changes" tab.
- [ ] The diff view shows file-level and hunk-level changes in unified
  format, scrollable and collapsible per file.
- [ ] Accept/reject per file goes through preview/token/apply — the
  user sees the exact proposed action before it runs.
- [ ] A diff with 50+ changed files renders without freezing (evidence:
  interaction responsive within 500ms).
- [ ] The diff of the most recent evidence capture is viewable from the
  same panel.
