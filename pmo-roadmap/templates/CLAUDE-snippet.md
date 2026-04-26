## PMO hygiene gate (pre-commit hook)

This repo uses [pmo-roadmap](https://github.com/) (installed locally from
`~/dev/reusable-processes/pmo-roadmap`). Before every commit:

1. Write `.tmp/CONTRACT.md` per the template in
   `pm/roadmap/PMO-CONTRACT.md` §"Contract template".
2. Set every checkbox to `[x]` only after honestly verifying each rule
   for **this** commit.
3. The pre-commit hook validates and deletes the file on success.

If this project enables PMO work logging (`PMO_WORK_LOG_ENABLED=1` in
`.githooks/pre-commit.config`), also fill the contract's work-log block:

```markdown
**Work-log consent:** yes | no

**Work-log reasons:**
- ...

**Work-log exclusions:**
- ...
```

Use `yes` only when this commit should become part of the local daily
architect log. Use `no` for private, noisy, experimental, or otherwise
non-log-worthy commits. Work-log consent is separate from the PMO checkboxes
and is not counted by `EXPECTED_BOXES`.

If the project config defines `PMO_WORK_LOG_EXCLUDE_REGEX`, matching staged
paths are mechanically omitted from work-log payloads. Still list human-readable
exclusions in the contract so the reason is auditable.

**One-time setup per clone:**

```bash
git config core.hooksPath .githooks
```

(The installer set this for the original clone; fresh clones must
re-run it.)

**Methodology:** `pm/roadmap/roadmap-builder.md`.
**Rules:** `pm/roadmap/PMO-CONTRACT.md`.

A stale contract (older than `HEAD`) is rejected. An unchecked
contract is rejected. The file is deleted on every successful commit
so each commit requires a fresh one.

If the hook ever blocks you, read its stderr — it tells you exactly
which rule failed and what to fix.

When work logging is enabled and consent is `yes`, the post-commit hook
prints the log path it appended under `~/.work/log/YYYY-MM-DD/`.

To inspect local entries for the day:

```bash
.githooks/work-log-read --date "$(date +%F)" --list
```

Do not run model summarization inside the commit hook. If a deferred summary is
needed after commits finish, use the installed helper with an explicit command:

```bash
PMO_WORK_LOG_SUMMARIZER='codex -p --model gpt-5.5' \
  .githooks/work-log-summarize --date "$(date +%F)" --timeout-seconds 120
```
