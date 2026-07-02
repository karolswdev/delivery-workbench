# Evidence - WLA-0-06

- **Story:** WLA-0-06 - Define git edge cases and log identity policy
- **Status:** done
- **Date:** 2026-07-01

## Proof

- `pre-commit` derives a collision-resistant log identity from project slug and
  repo path hash unless `PMO_WORK_LOG_ID` is configured.
- Common rewrite states are skipped; aborted commits leave pending payloads for
  overwrite on the next attempt.
- Tests cover amend, aborted editor commit, stale pending overwrite, and
  existing `post-commit` collision policy.

## Command Output

```text
$ rg -n "work_log_identity|path_hash|in_rewrite_state|overwriting stale pending|commit --amend|aborted commit|post-commit" \
  pmo-roadmap/hooks/pre-commit pmo-roadmap/tests/work-log-mvp.sh
pmo-roadmap/hooks/pre-commit:139:work_log_identity() {
pmo-roadmap/hooks/pre-commit:151:in_rewrite_state() {
pmo-roadmap/hooks/pre-commit:242:    echo "  Work log warning: overwriting stale pending payload from an earlier aborted commit." >&2
pmo-roadmap/tests/work-log-mvp.sh:180:git commit --amend -m "commit after abort amended" >/dev/null
pmo-roadmap/tests/work-log-mvp.sh:181:assert_eq "$(entry_count)" "4" "amend should append according to MVP policy"
pmo-roadmap/tests/work-log-mvp.sh:205:  fail "install should refuse to overwrite existing non-framework post-commit"
```

```text
$ pmo-roadmap/tests/work-log-mvp.sh
work-log-mvp.sh: ok
```
