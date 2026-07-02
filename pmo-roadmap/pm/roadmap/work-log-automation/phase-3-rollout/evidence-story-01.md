# Evidence - WLA-3-01

- **Story:** WLA-3-01 - Pilot in one consumer project
- **Status:** done
- **Date:** 2026-07-01

## Proof

- A temporary clone of the local Pantrybot repository was used as the consumer
  project so the original Pantrybot checkout was not mutated.
- The clone opted into work logging with `.githooks/pre-commit.config`.
- One consented commit wrote a schema-conformant entry, one denied commit wrote
  no entry, and a second consented commit omitted a configured private fixture
  path without leaking its contents.
- Longer multi-day review is deferred because the pilot clone is intentionally
  short-lived; README now documents the multi-day review command.

## Command Output

```text
$ pantrybot temporary-clone pilot
pilot_tmp=/var/folders/.../wla-pantrybot-pilot.9wTygZ
log_file=/var/folders/.../work-log/2026-07-01/pantrybot-pilot-2791557243-work-summary.log
entry_count=2
commit_subjects:
- **Subject:** pilot consented work log
- **Subject:** pilot excluded work log path
omitted_paths:
119:- `private-fixtures/token.txt`
last_commits:
3dcfdcf pilot excluded work log path
1b0e405 pilot denied work log
53d84ea pilot consented work log
```

```text
commit1_hook_output:
Work log payload captured for post-commit finalization.
pmo-roadmap post-commit: work log appended to .../pantrybot-pilot-2791557243-work-summary.log

commit2_hook_output:
Contract acknowledged (7/7 checkboxes).
Commit proceeding.

commit3_hook_output:
Work log payload captured for post-commit finalization.
pmo-roadmap post-commit: work log appended to .../pantrybot-pilot-2791557243-work-summary.log
```
