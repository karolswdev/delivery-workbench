# Evidence - WLA-1-05

- **Story:** WLA-1-05 - Add temporary-repo integration coverage
- **Status:** done
- **Date:** 2026-07-01

## Proof

- `pmo-roadmap/tests/work-log-mvp.sh` creates a temporary repo, installs the
  framework, and runs real Git commits through the hooks.
- Coverage includes logging disabled, consent yes, consent no, editor abort,
  duplicate post-commit, amend, excluded paths, deferred summarizer behavior,
  and existing `post-commit` hook collisions.

## Command Output

```text
$ pmo-roadmap/tests/work-log-mvp.sh
Work log payload captured for post-commit finalization.
pmo-roadmap post-commit: work log appended to .../work-log/2026-07-01/demo-1116344482-work-summary.log
Work log warning: overwriting stale pending payload from an earlier aborted commit.
work-log-mvp.sh: ok
```

```text
$ rg -n "logging disabled|consent yes|consent no|aborted commit|post-commit rerun|commit --amend|refuse to overwrite" \
  pmo-roadmap/tests/work-log-mvp.sh
pmo-roadmap/tests/work-log-mvp.sh:86:assert_eq "$(find "$LOG_ROOT" -type f 2>/dev/null | wc -l | tr -d ' ')" "0" "logging disabled should not write logs"
pmo-roadmap/tests/work-log-mvp.sh:156:assert_eq "$(entry_count)" "2" "denied consent should not append"
pmo-roadmap/tests/work-log-mvp.sh:159:assert_eq "$(entry_count)" "2" "manual post-commit rerun should not duplicate without pending"
pmo-roadmap/tests/work-log-mvp.sh:168:assert_eq "$(entry_count)" "2" "aborted commit should not append"
pmo-roadmap/tests/work-log-mvp.sh:181:assert_eq "$(entry_count)" "4" "amend should append according to MVP policy"
```
