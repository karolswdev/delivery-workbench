# Evidence - WLA-0-01

- **Story:** WLA-0-01 - Define the consent and log-entry contract
- **Status:** done
- **Date:** 2026-07-01

## Proof

- `pmo-roadmap/templates/PMO-CONTRACT.md` documents the work-log consent block,
  requires explicit `yes`, keeps consent outside `EXPECTED_BOXES`, and describes
  the durable log path.
- `pmo-roadmap/hooks/post-commit` renders the stable markdown front matter and
  sections for deterministic entries.
- `pmo-roadmap/tests/work-log-mvp.sh` verifies consent yes/no behavior and the
  schema marker in generated logs.

## Command Output

```text
$ rg -n "Work-log consent|pmo-work-log-entry|summary_mode" \
  pmo-roadmap/templates/PMO-CONTRACT.md pmo-roadmap/hooks/post-commit \
  pmo-roadmap/tests/work-log-mvp.sh
pmo-roadmap/tests/work-log-mvp.sh:61:## Work-log consent
pmo-roadmap/tests/work-log-mvp.sh:63:**Work-log consent:** $consent
pmo-roadmap/tests/work-log-mvp.sh:113:grep -q '^summary_mode: deterministic$' "$LOG_FILE" || fail "log entry should be deterministic"
pmo-roadmap/tests/work-log-mvp.sh:115:.githooks/work-log-read --log-file "$LOG_FILE" | grep -q '^kind: pmo-work-log-entry$' || fail "reader should print log content"
pmo-roadmap/hooks/post-commit:113:  echo "kind: pmo-work-log-entry"
pmo-roadmap/hooks/post-commit:122:  echo "summary_mode: deterministic"
pmo-roadmap/hooks/post-commit:142:  echo "**Work-log consent:** yes"
pmo-roadmap/templates/PMO-CONTRACT.md:140:## Work-log consent
pmo-roadmap/templates/PMO-CONTRACT.md:142:**Work-log consent:** no
pmo-roadmap/templates/PMO-CONTRACT.md:164:**Work-log consent:** yes
```

```text
$ pmo-roadmap/tests/work-log-mvp.sh
work-log-mvp.sh: ok
```
