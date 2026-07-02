# Evidence - WLA-1-06

- **Story:** WLA-1-06 - Add read-flow and first-run discoverability
- **Status:** done
- **Date:** 2026-07-01

## Proof

- Successful finalization prints the exact log path.
- README and CLAUDE/AGENTS snippet document how to list/read today's log and
  how custom `PMO_WORK_LOG_DIR` affects location.
- `work-log-read` lists and prints local entries.

## Command Output

```text
$ pmo-roadmap/tests/work-log-mvp.sh
pmo-roadmap post-commit: work log appended to .../work-log/2026-07-01/demo-1116344482-work-summary.log
work-log-mvp.sh: ok
```

```text
$ rg -n "work log appended to|work-log-read|PMO_WORK_LOG_DIR" \
  pmo-roadmap/hooks/post-commit pmo-roadmap/README.md pmo-roadmap/templates/CLAUDE-snippet.md
pmo-roadmap/hooks/post-commit:218:echo "pmo-roadmap post-commit: work log appended to $log_file"
pmo-roadmap/README.md:144:PMO_WORK_LOG_DIR="$HOME/.work/log"
pmo-roadmap/README.md:201:.githooks/work-log-read --date "$(date +%F)" --list
pmo-roadmap/templates/CLAUDE-snippet.md:59:.githooks/work-log-read --date "$(date +%F)" --list
```
