# Evidence - WLA-2-02

- **Story:** WLA-2-02 - Add timeout, fallback, and output bounds
- **Status:** done
- **Date:** 2026-07-01

## Proof

- Timeout and output byte limits are configurable.
- Timeout and nonzero exit fail the summarizer command without replacing the
  existing deterministic log or companion digest.
- Empty output writes a deterministic fallback digest.
- Oversized output is capped with `PMO_WORK_LOG_SUMMARY_TRUNCATED`.

## Command Output

```text
$ rg -n "timeout|MAX_OUTPUT_BYTES|SUMMARY_TRUNCATED|fallback_summary|nonzero|Deterministic Fallback|oversized" \
  pmo-roadmap/bin/work-log-summarize pmo-roadmap/tests/work-log-mvp.sh
pmo-roadmap/bin/work-log-summarize:40:MAX_OUTPUT_BYTES="${PMO_WORK_LOG_SUMMARY_MAX_BYTES:-20000}"
pmo-roadmap/bin/work-log-summarize:89:fallback_summary() {
pmo-roadmap/bin/work-log-summarize:128:      die "summarizer command timed out after ${TIMEOUT_SECONDS}s for $src"
pmo-roadmap/tests/work-log-mvp.sh:121:  fail "deferred summarizer should fail on timeout"
pmo-roadmap/tests/work-log-mvp.sh:126:  fail "deferred summarizer should fail on nonzero exit"
pmo-roadmap/tests/work-log-mvp.sh:129:grep -q '^## Deterministic Fallback$' "$DIGEST_FILE" || fail "empty summarizer output should write fallback digest"
pmo-roadmap/tests/work-log-mvp.sh:131:grep -q 'PMO_WORK_LOG_SUMMARY_TRUNCATED' "$DIGEST_FILE" || fail "oversized summarizer output should be truncated"
```

```text
$ pmo-roadmap/tests/work-log-mvp.sh
work-log-mvp.sh: ok
```
