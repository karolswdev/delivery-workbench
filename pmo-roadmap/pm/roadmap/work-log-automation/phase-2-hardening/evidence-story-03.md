# Evidence - WLA-2-03

- **Story:** WLA-2-03 - Add redaction and diff-size controls
- **Status:** done
- **Date:** 2026-07-01

## Proof

- `PMO_WORK_LOG_MAX_DIFF_BYTES` bounds captured unified diffs and writes a
  truncation marker.
- `PMO_WORK_LOG_EXCLUDE_REGEX` omits matching paths from name/status, diff
  stat, and diff payloads while naming them under omitted paths.
- README documents that exclusions and consent are the privacy boundary and
  names categories that are not reliably caught by best-effort controls.
- Tests inspect pending payload and final logs to prove excluded content does
  not appear.

## Command Output

```text
$ rg -n "PMO_WORK_LOG_MAX_DIFF_BYTES|PMO_WORK_LOG_EXCLUDE_REGEX|DIFF_TRUNCATED|not-for-log|base64|JWT|privacy boundary" \
  pmo-roadmap/hooks/pre-commit pmo-roadmap/README.md pmo-roadmap/tests/work-log-mvp.sh
pmo-roadmap/hooks/pre-commit:24:PMO_WORK_LOG_MAX_DIFF_BYTES=120000
pmo-roadmap/hooks/pre-commit:27:PMO_WORK_LOG_EXCLUDE_REGEX=""
pmo-roadmap/hooks/pre-commit:217:        printf "\n[PMO_WORK_LOG_DIFF_TRUNCATED]\n"
pmo-roadmap/README.md:194:Treat consent and exclusions as the privacy boundary.
pmo-roadmap/README.md:197:cannot reliably catch base64 blobs, JWT payloads, generated credentials,
pmo-roadmap/tests/work-log-mvp.sh:95:PMO_WORK_LOG_EXCLUDE_REGEX='^secrets/'
pmo-roadmap/tests/work-log-mvp.sh:141:  fail "excluded file content should not appear in pending payload"
pmo-roadmap/tests/work-log-mvp.sh:151:  fail "excluded file content should not appear in final log"
```

```text
$ pmo-roadmap/tests/work-log-mvp.sh
work-log-mvp.sh: ok
```
