# Evidence - WLA-1-02

- **Story:** WLA-1-02 - Capture consented staged payloads in pre-commit
- **Status:** done
- **Date:** 2026-07-01

## Proof

- Capture is disabled unless `PMO_WORK_LOG_ENABLED` is truthy.
- Consent parsing requires `**Work-log consent:** yes`.
- The pending payload includes contract text, reasons, exclusions, branch,
  staged paths, diff stat, bounded diff, index tree, repo path, and timestamp.
- The test harness confirms excluded content is not written to pending payloads.

## Command Output

```text
$ rg -n "PMO_WORK_LOG_ENABLED|work_log_consent_yes|index_tree|capture_timestamp|STAGED_NAME_STATUS|STAGED_STAT|STAGED_DIFF" \
  pmo-roadmap/hooks/pre-commit
pmo-roadmap/hooks/pre-commit:22:PMO_WORK_LOG_ENABLED=0
pmo-roadmap/hooks/pre-commit:146:work_log_consent_yes() {
pmo-roadmap/hooks/pre-commit:255:  index_tree=$(git write-tree 2>/dev/null || echo unknown)
pmo-roadmap/hooks/pre-commit:256:  capture_ts=$(date -u +%Y-%m-%dT%H:%M:%SZ)
pmo-roadmap/hooks/pre-commit:263:    echo "capture_timestamp=$capture_ts"
pmo-roadmap/hooks/pre-commit:276:    echo "--- STAGED_NAME_STATUS ---"
pmo-roadmap/hooks/pre-commit:282:    echo "--- STAGED_STAT ---"
pmo-roadmap/hooks/pre-commit:284:    echo "--- STAGED_DIFF ---"
```

```text
$ pmo-roadmap/tests/work-log-mvp.sh
Work log payload captured for post-commit finalization.
work-log-mvp.sh: ok
```
