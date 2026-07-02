# Evidence - WLA-2-01

- **Story:** WLA-2-01 - Add configurable deferred summarizer command support
- **Status:** done
- **Date:** 2026-07-01

## Proof

- Commit hooks do not call the summarizer.
- `work-log-summarize` accepts `PMO_WORK_LOG_SUMMARIZER` or `--command`, sends a
  prepared prompt plus deterministic source log to stdin, and writes a
  companion `*-deferred-summary.md` digest.
- Tests use fake shell commands and no network/model dependency.

## Command Output

```text
$ rg -n "PMO_WORK_LOG_SUMMARIZER|SOURCE LOG|deferred-summary|summary_mode: deferred|command \"awk" \
  pmo-roadmap/bin/work-log-summarize pmo-roadmap/tests/work-log-mvp.sh
pmo-roadmap/bin/work-log-summarize:19:  --command CMD            Summarizer command (default: $PMO_WORK_LOG_SUMMARIZER)
pmo-roadmap/bin/work-log-summarize:119:    echo "--- SOURCE LOG ---"
pmo-roadmap/bin/work-log-summarize:177:    echo "summary_mode: deferred"
pmo-roadmap/tests/work-log-mvp.sh:117:.githooks/work-log-summarize --log-file "$LOG_FILE" --command "awk '/^Source log:/ {print \"Deferred summary for \" $0; exit}'" >/dev/null
```

```text
$ pmo-roadmap/tests/work-log-mvp.sh
work-log-mvp.sh: ok
```
