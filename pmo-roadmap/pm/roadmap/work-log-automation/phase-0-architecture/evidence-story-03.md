# Evidence - WLA-0-03

- **Story:** WLA-0-03 - Specify the summarizer adapter and failure policy
- **Status:** done
- **Date:** 2026-07-01

## Proof

- `work-log-summarize` is an explicit deferred helper, not a commit hook call.
- The helper accepts `PMO_WORK_LOG_SUMMARIZER` or `--command`, prepares a stable
  stdin payload, enforces timeout/output bounds, and writes a companion digest.
- Empty output falls back to deterministic markdown; failures leave source logs
  untouched.

## Command Output

```text
$ rg -n "PMO_WORK_LOG_SUMMARIZER|timeout|fallback_summary|summary_mode: deferred|source_log" \
  pmo-roadmap/bin/work-log-summarize pmo-roadmap/tests/work-log-mvp.sh
pmo-roadmap/bin/work-log-summarize:19:  --command CMD            Summarizer command (default: $PMO_WORK_LOG_SUMMARIZER)
pmo-roadmap/bin/work-log-summarize:38:SUMMARIZER_CMD="${PMO_WORK_LOG_SUMMARIZER:-}"
pmo-roadmap/bin/work-log-summarize:89:fallback_summary() {
pmo-roadmap/bin/work-log-summarize:177:    echo "summary_mode: deferred"
pmo-roadmap/tests/work-log-mvp.sh:121:  fail "deferred summarizer should fail on timeout"
pmo-roadmap/tests/work-log-mvp.sh:126:  fail "deferred summarizer should fail on nonzero exit"
pmo-roadmap/tests/work-log-mvp.sh:129:grep -q '^## Deterministic Fallback$' "$DIGEST_FILE" || fail "empty summarizer output should write fallback digest"
```

```text
$ pmo-roadmap/tests/work-log-mvp.sh
work-log-mvp.sh: ok
```
