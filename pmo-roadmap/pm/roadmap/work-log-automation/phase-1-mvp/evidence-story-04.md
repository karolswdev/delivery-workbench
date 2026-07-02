# Evidence - WLA-1-04

- **Story:** WLA-1-04 - Install, update, and document the MVP hooks
- **Status:** done
- **Date:** 2026-07-01

## Proof

- `install.sh` copies `post-commit`, `dw`, `work-log-summarize`, and
  `work-log-read` into `.githooks/`.
- `update.sh` refreshes canonical files while preserving project-owned config
  and local extension files.
- README documents opt-in config, log path, consent behavior, reader flow, and
  summarizer use.

## Command Output

```text
$ rg -n "work-log-read|work-log-summarize|bin/dw|pre-commit.config|PMO_WORK_LOG_ENABLED|work-log consent" \
  pmo-roadmap/install.sh pmo-roadmap/update.sh pmo-roadmap/README.md
pmo-roadmap/install.sh:16:  - copies bin/dw                         -> .githooks/dw
pmo-roadmap/install.sh:108:cp "$SOURCE_DIR/bin/dw" "$TARGET/.githooks/dw"
pmo-roadmap/update.sh:82:cp "$SOURCE_DIR/bin/dw" "$TARGET/.githooks/dw"
pmo-roadmap/README.md:140:PMO_WORK_LOG_ENABLED=1
pmo-roadmap/README.md:149:Then fill the contract's work-log block for each commit:
pmo-roadmap/README.md:201:.githooks/work-log-read --date "$(date +%F)" --list
```

```text
$ pmo-roadmap/tests/work-log-mvp.sh
work-log-mvp.sh: ok
```
