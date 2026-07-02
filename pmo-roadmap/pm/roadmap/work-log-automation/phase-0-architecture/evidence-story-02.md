# Evidence - WLA-0-02

- **Story:** WLA-0-02 - Design the capture/finalize hook lifecycle
- **Status:** done
- **Date:** 2026-07-01

## Proof

- `pre-commit` captures consented staged metadata under `.git/pmo-work-log/`
  after PMO checks pass.
- `post-commit` appends only after `HEAD` exists, removes successful pending
  payloads, and deduplicates by commit hash.
- The integration harness covers consented commits, denied commits, editor
  aborts, stale pending overwrite, amend, and duplicate post-commit runs.

## Command Output

```text
$ rg -n "capture_work_log_payload|STAGED_NAME_STATUS|STAGED_STAT|STAGED_DIFF|PENDING_FILE|commit_sha|already contains" \
  pmo-roadmap/hooks/pre-commit pmo-roadmap/hooks/post-commit
pmo-roadmap/hooks/pre-commit:221:capture_work_log_payload() {
pmo-roadmap/hooks/pre-commit:276:    echo "--- STAGED_NAME_STATUS ---"
pmo-roadmap/hooks/pre-commit:282:    echo "--- STAGED_STAT ---"
pmo-roadmap/hooks/pre-commit:284:    echo "--- STAGED_DIFF ---"
pmo-roadmap/hooks/post-commit:68:PENDING_FILE="$gd/pmo-work-log/pending"
pmo-roadmap/hooks/post-commit:76:commit_sha=$(git rev-parse HEAD 2>/dev/null || true)
pmo-roadmap/hooks/post-commit:93:if [ -f "$log_file" ] && grep -q "^commit: $commit_sha$" "$log_file"; then
```

```text
$ pmo-roadmap/tests/work-log-mvp.sh
pmo-roadmap post-commit: work log appended to .../work-log/2026-07-01/demo-1116344482-work-summary.log
work-log-mvp.sh: ok
```
