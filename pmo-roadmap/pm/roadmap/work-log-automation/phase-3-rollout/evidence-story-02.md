# Evidence - WLA-3-02

- **Story:** WLA-3-02 - Polish operator and agent documentation
- **Status:** done
- **Date:** 2026-07-01

## Proof

- README documents enablement from an installed repo, consent examples, log
  location, read flow, deferred summarization, troubleshooting, privacy limits,
  and multi-day review.
- The CLAUDE/AGENTS snippet explains when to consent, deny, and list exclusions.
- Examples match the pilot and integration output: finalization prints the log
  path, denied consent does not append, and omitted paths are listed.

## Command Output

```text
$ rg -n "Optional daily work log|Troubleshooting work logs|multi-day review|Work-log consent|Use `yes`|Use `no`|work-log-read" \
  pmo-roadmap/README.md pmo-roadmap/templates/CLAUDE-snippet.md
pmo-roadmap/README.md:134:## Optional daily work log
pmo-roadmap/README.md:230:### Troubleshooting work logs
pmo-roadmap/README.md:250:For a multi-day review, list each day's directory and read the same identity
pmo-roadmap/templates/CLAUDE-snippet.md:16:**Work-log consent:** yes | no
pmo-roadmap/templates/CLAUDE-snippet.md:24:Use `yes` only when this commit should become part of the local daily
pmo-roadmap/templates/CLAUDE-snippet.md:59:.githooks/work-log-read --date "$(date +%F)" --list
```

```text
$ pmo-roadmap/tests/work-log-mvp.sh
pmo-roadmap post-commit: work log appended to .../work-log/2026-07-01/demo-1116344482-work-summary.log
work-log-mvp.sh: ok
```
