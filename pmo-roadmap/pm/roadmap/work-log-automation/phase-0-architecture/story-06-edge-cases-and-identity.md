# WLA-0-06 - Define git edge cases and log identity policy

- **Project:** work-log-automation
- **Phase:** 0
- **Status:** backlog
- **Depends on:** WLA-0-01, WLA-0-02
- **Unblocks:** WLA-1-02, WLA-1-03, WLA-1-04
- **Owner:** unassigned

## Problem

Daily logs are global user state, while Git hooks fire in many repo states:
normal commits, amended commits, rebases, cherry-picks, aborted editor commits,
and concurrent terminal sessions. The roadmap needs explicit policies before
code decides these by accident.

## Scope

- **In:** MVP behavior for amend, rebase, cherry-pick, aborted commits,
  concurrent commit attempts, stale pending payloads, project/log identity, and
  existing `post-commit` hook collision policy.
- **Out:** Full history-rewrite detection, cloud synchronization, or retroactive
  log deduplication.

## Acceptance criteria

- [ ] A truth table documents normal commit, editor-aborted commit,
  concurrent commit, amend, rebase, and cherry-pick behavior.
- [ ] MVP default for history rewrites is explicit, even if imperfect.
- [ ] Project log identity cannot silently collide for two repos with the same
  basename.
- [ ] Existing project `post-commit` hooks are detected and preserved, composed,
  or reported before install/update overwrites anything.
- [ ] The policies are referenced by Phase 1 implementation stories.

## Test plan

- **Unit:** n/a.
- **Integration / Cypress:** Temporary-repo tests in Phase 1 should cover at
  least normal commit, aborted commit, amend, and existing hook collision.
- **Manual / device:** Review the truth table against Git commands an agent is
  likely to run during normal development.

## Notes / open questions

Recommended defaults:

| Scenario | MVP policy |
|---|---|
| Normal commit with consent `yes` | Capture in `pre-commit`; append once in `post-commit`. |
| Normal commit with consent `no` or missing | Do not capture and do not append. |
| Editor-aborted commit after `pre-commit` | Leave pending payload stale; next `pre-commit` overwrites it after warning. |
| Concurrent commits in one repo | Best-effort unsupported in MVP; pending payload includes capture timestamp and index tree so mismatches can be detected. |
| `git commit --amend` | Append a new entry marked `amend` if `GIT_REFLOG_ACTION` or command context exposes it; otherwise append normally and rely on commit hash uniqueness. |
| Rebase/cherry-pick replay | MVP should skip logging when common rebase/cherry-pick state files are present under `.git/`, unless explicitly overridden. |
| Existing `.githooks/post-commit` | Installer refuses to overwrite unless the existing file matches the canonical installed hook or the user passes an explicit force/composition path. |

Recommended log identity: default to `{project-slug}-{path-hash}` where
`project-slug` comes from config first, then a single `pm/roadmap/{slug}/`
folder if unambiguous, then `basename "$REPO_ROOT"`. The path hash should be
stable for the absolute repo path and short enough for readable filenames.
