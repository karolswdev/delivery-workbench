# pmo-roadmap

![Delivery Workbench icon](./assets/delivery-workbench-icon.png)

A drop-in PMO framework for any git project. Provides:

1. **Methodology** — phase-based, evidence-rich roadmap structure under
   `pm/roadmap/{project}/`. See `templates/roadmap-builder.md`.
2. **Hygiene gate** — a `pre-commit` hook that blocks commits until the
   committing agent (or human) writes a fresh `.tmp/CONTRACT.md` with
   per-rule checkboxes acknowledging the operating principles.
3. **Work log finalizer** — optional consent-gated `pre-commit` capture plus
   `post-commit` append into a local daily architect log.
4. **Deferred summarizer** — optional CLI adapter that can run `codex` or
   another command over deterministic logs after commits finish.
5. **Log reader** — small helper for listing or reading local daily logs.
6. **Bootstrapping** — scripts to scaffold a new project's roadmap tree.
7. **Updater** — pull methodology / contract / hook updates back into a
   project that already installed.

## Why

Plans rot when "done" is asserted, not evidenced. This package enforces
two things mechanically:

- A **directory contract** (each phase has its own folder with a known
  set of files: `current-phase-status.md`, `story-{n}-*.md`,
  `evidence-story-{n}.md`, `final-summary.md`).
- A **commit-time gate** that forces the committing agent to re-read the
  rules and certify (per-checkbox) that this commit complies. Stale
  contracts are rejected via mtime checks. The contract file is deleted
  on success so each commit needs a fresh one.

The hygiene gate works for human commits too. CI is unaffected (hooks
don't run server-side).

## How the pieces fit

```mermaid
flowchart TD
  Install[install.sh] --> Hooks[.githooks]
  Install --> Canon[pm/roadmap/PMO-CONTRACT.md + roadmap-builder.md]
  Install --> Snippet[CLAUDE.md / AGENTS.md snippet]
  Hooks --> Pre[pre-commit]
  Hooks --> Post[post-commit]
  Hooks --> Read[work-log-read]
  Hooks --> Summarize[work-log-summarize]

  Canon --> Contract[.tmp/CONTRACT.md per commit]
  Contract --> Pre
  Pre --> Gate{PMO checks pass?}
  Gate -->|No| Block[Commit blocked]
  Gate -->|Yes| Commit[Commit proceeds]
  Pre -->|optional consented payload| Pending[.git/pmo-work-log/pending]
  Commit --> Post
  Pending --> Post
  Post --> Log[~/.work/log/YYYY-MM-DD/*.log]
  Log --> Read
  Log --> Summarize
```

## Install into a target project

```bash
cd ~/dev/reusable-processes/pmo-roadmap
./install.sh /path/to/target-project
```

Optional flags:

- `--project-name "Pantrybot"` — human name (used in scaffold)
- `--project-slug pantrybot` — kebab slug (used in `pm/roadmap/{slug}/`)
- `--project-prefix PB` — story-ID prefix (`PB-0-01`, …)
- `--skip-bootstrap` — install methodology + hook only; don't scaffold
  `pm/roadmap/{slug}/`
- `--force` — overwrite existing methodology/contract files

The installer:

1. Copies `templates/roadmap-builder.md` → `target/pm/roadmap/roadmap-builder.md`
2. Copies `templates/PMO-CONTRACT.md` → `target/pm/roadmap/PMO-CONTRACT.md`
3. Copies `hooks/pre-commit` → `target/.githooks/pre-commit` (chmod +x)
4. Copies `hooks/post-commit` → `target/.githooks/post-commit` (chmod +x)
5. Copies `bin/dw` → `target/.githooks/dw` and the `lib/dw_pmo/` core
   package → `target/.githooks/dw_pmo/`
6. Copies `bin/work-log-summarize` → `target/.githooks/work-log-summarize`
7. Copies `bin/work-log-read` → `target/.githooks/work-log-read`
8. Sets `git config core.hooksPath .githooks` in target
9. Adds `.tmp/` to target `.gitignore` if missing
10. (Optional) scaffolds `pm/roadmap/{slug}/` with `README.md` + a starter
   `phase-0-setup/` folder
11. Prints a snippet to add to target's `CLAUDE.md` / `AGENTS.md`

Re-running is safe (idempotent) but will refuse to overwrite existing
methodology/contract without `--force`.

## Installation Decision Tree

```mermaid
flowchart TD
  A[Target Git project] --> B{New roadmap or existing project?}
  B -->|New / greenfield| C[install.sh with project slug]
  C --> D[new-project.sh creates README, phase status, bootstrap story]
  B -->|Existing / mid-project| E[install.sh --skip-bootstrap]
  E --> U[session-intake.sh captures user goal + handoff]
  U --> F[adopt-project.sh renders discovery prompt]
  F --> G{Run agent discovery?}
  G -->|No| H[Human fills adoption report]
  G -->|Codex or Claude| I[Agent writes adoption-discovery.md]
  H --> J[Create current phase and first stories]
  I --> J
```

## Update an installed project

```bash
cd ~/dev/reusable-processes/pmo-roadmap
./update.sh /path/to/target-project
```

This re-copies the methodology and hook (overwriting). It refuses to
overwrite `PMO-CONTRACT.md` if it has been customized locally — pass
`--force` only after reconciling project-extension rules manually.

It never touches:

- `pm/roadmap/{slug}/` content (your phases and stories).
- `.githooks/pre-commit.local` (your project-specific rule checks).
- `.githooks/pre-commit.config` (your project-specific config).
- `.gitignore`.

If a target already has a non-framework `.githooks/post-commit`, install/update
refuses to replace it unless you pass `--force` after deciding how to preserve
or compose the existing behavior.

For a project with a customized `pm/roadmap/PMO-CONTRACT.md`, run `update.sh`
without `--force` first. If it reports a contract difference, compare the
project file with `pmo-roadmap/templates/PMO-CONTRACT.md`, manually merge the
canonical consent block and any new framework language around your
project-specific extensions, then rerun with `--force` only if you intend to
replace the whole target contract.

## Optional daily work log

Work logging is off by default. To enable deterministic local architect-log
entries for a project, add this to `.githooks/pre-commit.config`:

```bash
PMO_WORK_LOG_ENABLED=1
# Optional. Defaults to a roadmap slug or repo basename plus a path hash.
PMO_WORK_LOG_PROJECT_SLUG=myproject
# Optional. Defaults to "$HOME/.work/log".
PMO_WORK_LOG_DIR="$HOME/.work/log"
# Optional. Excludes matching staged paths from work-log payloads.
PMO_WORK_LOG_EXCLUDE_REGEX='(^secrets/|\\.env$|private-fixtures/)'
```

Then fill the contract's work-log block for each commit:

```markdown
**Work-log consent:** yes

**Work-log reasons:**
- Shipped MP-1-02 with evidence and test output.

**Work-log exclusions:**
- none
```

Only explicit `yes` consent creates a log entry. `pre-commit` captures the
staged payload under `.git/pmo-work-log/`; `post-commit` appends after Git
creates the commit. The MVP writes deterministic markdown and does not call an
LLM in the commit path.

```mermaid
sequenceDiagram
  participant Dev as Human or Agent
  participant Contract as .tmp/CONTRACT.md
  participant Pre as pre-commit
  participant Git as Git
  participant Post as post-commit
  participant Log as ~/.work/log
  participant Summ as work-log-summarize

  Dev->>Contract: Work-log consent: yes
  Dev->>Git: git commit
  Git->>Pre: validate PMO contract
  Pre->>Pre: filter excluded paths
  Pre->>.git/pmo-work-log: write pending payload
  Git->>Post: after commit exists
  Post->>Log: append deterministic entry
  Dev->>Summ: optional deferred summarization
  Summ->>Log: write companion deferred summary
```

`PMO_WORK_LOG_EXCLUDE_REGEX` is the mechanical privacy/noise control. Matching
paths are omitted from captured name/status, diff stat, and diff payloads, and
the final log lists them under "Omitted Paths". Contract exclusions remain the
human rationale; the regex is what the hook enforces.

Treat consent and exclusions as the privacy boundary. Delivery Workbench does
not perform general-purpose secret scanning. Best-effort omission by path
cannot reliably catch base64 blobs, JWT payloads, generated credentials,
environment-expanded values, screenshots, binary files, or secrets pasted into
otherwise safe paths. If the material should not be preserved in a local daily
log, deny consent or exclude the path mechanically before committing.

Logs land under:

```bash
~/.work/log/$(date +%F)/{log-identity}-work-summary.log
```

To read today's entries:

```bash
.githooks/work-log-read --date "$(date +%F)" --list
.githooks/work-log-read --date "$(date +%F)" --identity myproject-123456789
```

To create a deferred LLM digest after commits are complete, configure a command
and run the helper:

```bash
PMO_WORK_LOG_SUMMARIZER='codex -p --model gpt-5.5'
.githooks/work-log-summarize --date "$(date +%F)" --timeout-seconds 120
```

The helper writes `{log-identity}-deferred-summary.md` beside the source log.
It does not rewrite deterministic commit entries. If the configured command
times out or exits nonzero, the deterministic log remains untouched and the
helper reports the failure. If the command returns empty output, the helper
writes a small deterministic fallback digest instead of inventing a model
summary. Oversized output is capped and marked with
`[PMO_WORK_LOG_SUMMARY_TRUNCATED]`.

### Troubleshooting work logs

- **No log entry:** confirm `.githooks/pre-commit.config` contains
  `PMO_WORK_LOG_ENABLED=1`, the commit contract says
  `**Work-log consent:** yes`, and the commit actually completed.
- **Stale pending payload:** an editor-aborted commit can leave
  `.git/pmo-work-log/pending`; the next consented `pre-commit` overwrites it
  with a warning before finalization.
- **Unexpected log path:** check `PMO_WORK_LOG_DIR`, `PMO_WORK_LOG_ID`, and
  `PMO_WORK_LOG_PROJECT_SLUG`. By default the filename includes a stable hash
  of the absolute repo path to avoid collisions.
- **Summarizer failure:** rerun `.githooks/work-log-summarize` after fixing the
  configured command. The source `*-work-summary.log` is append-only and is not
  deleted or rewritten by summarizer failures.

For a multi-day review, list each day's directory and read the same identity
across dates:

```bash
find "${PMO_WORK_LOG_DIR:-$HOME/.work/log}" -maxdepth 2 -name '*-work-summary.log' | sort
.githooks/work-log-read --date "$(date +%F)" --identity myproject-123456789
```

## Project-specific rules

The canonical contract owns 7 rules. To add an 8th rule (or more) for
a specific project — for example, "every UI-facing change must update
the design handoff" — see
[`templates/PMO-CONTRACT.md` §"Extending"](./templates/PMO-CONTRACT.md).
The pattern: append the rule to your project's `PMO-CONTRACT.md`,
add a checkbox to the contract template, and put the structural
enforcement in `.githooks/pre-commit.local`. The canonical hook
sources that file after its own checks; `update.sh` never touches it.

## Bootstrap a new project's roadmap (post-install)

```bash
./bootstrap/new-project.sh /path/to/target-project myproject "My Project" MP
```

Creates `target/pm/roadmap/myproject/` with the project README and
`phase-0-setup/current-phase-status.md` ready to extend.

## Roadmap maintenance CLI

The installed `.githooks/dw` helper performs routine roadmap maintenance over
the existing markdown files; it does not create a separate tracker.

```bash
.githooks/dw projects
.githooks/dw tree myproject
.githooks/dw tree myproject --done
.githooks/dw context myproject --trace
.githooks/dw phase list myproject
.githooks/dw phase create myproject 1 "MVP" \
  --goal "Ship the smallest useful release."
.githooks/dw story create myproject 1 "Add the first feature"
.githooks/dw story status myproject 1 PRJ-1-01 done \
  --evidence-body "- Test output and implementation notes."
.githooks/dw story evidence myproject 1 PRJ-1-01 \
  --body "- Additional verification detail."
.githooks/dw phase close myproject 1 \
  --summary "Phase closed with all stories evidenced."
.githooks/dw check myproject
```

Use `tree` to see what is in a phase, `tree --done` to see completed work, and
`check` before a status update to catch broken links or story/table status
mismatches. Use `context` when an agent needs a JSON snapshot with projects,
active phases, stories, evidence presence, next story, stale-pointer issues,
drift warnings, supplemental canon, hook compatibility, trace paths, optional
recent commits, and work-log entries before it chooses a write operation.

Write commands are intentionally narrow. `story status ... done` refuses to
proceed unless paired evidence already exists or evidence text is provided in
the same command. `story evidence` only creates or attaches
`evidence-story-N.md` in the story's phase folder. `phase close` refuses open
stories unless forced and writes only `final-summary.md` plus the project README
phase-index status. These commands compute all affected file contents before
writing and restore already-touched files if a later write fails. The CLI treats
generated JSON as disposable context; the markdown files remain the source of
truth.

## Adopt an existing project

For a running project, install the mechanics first, then run session intake and
adoption discovery before writing stories:

```bash
./install.sh /path/to/target-project --skip-bootstrap
./bootstrap/session-intake.sh /path/to/target-project \
  --project-name "My Project" \
  --project-slug myproject \
  --project-prefix MP
./bootstrap/adopt-project.sh /path/to/target-project \
  --project-name "My Project" \
  --project-slug myproject \
  --project-prefix MP \
  --require-intake
```

The intake runs as a guided terminal interview when attached to a TTY. It keeps
the tone light but practical: a small banner, numbered choices, checkbox-style
priorities and deliverables, risk posture, discovery depth, session goal,
desired direction, success evidence, constraints, and handoff expectations.
The discovery step then anchors repository research to that intent instead of
producing generic reconnaissance.

For automation, pass the same values as flags and add `--no-prompt`:

```bash
./bootstrap/session-intake.sh /path/to/target-project \
  --project-name "My Project" \
  --project-slug myproject \
  --project-prefix MP \
  --mode "Delivery slice: identify and execute the next valuable change" \
  --priorities "- [x] Create a durable handoff" \
  --risk "Read-only until the plan is explicit" \
  --depth "Standard: repo map, commands, risks, first stories" \
  --deliverables "- [x] Immediate session plan" \
  --handoff-audience "Future agent" \
  --goal "Turn discovery into a first actionable roadmap" \
  --no-prompt
```

That creates:

```text
pm/roadmap/myproject/adoption/session-intake.md
pm/roadmap/myproject/adoption/adoption-discovery-prompt.md
```

To have an agent perform the read-only discovery:

```bash
./bootstrap/adopt-project.sh /path/to/target-project \
  --project-name "My Project" \
  --project-slug myproject \
  --project-prefix MP \
  --with-intake \
  --agent codex \
  --model gpt-5.5 \
  --dangerous \
  --force
```

or:

```bash
./bootstrap/adopt-project.sh /path/to/target-project \
  --project-slug myproject \
  --project-prefix MP \
  --with-intake \
  --agent claude \
  --model opus \
  --dangerous \
  --force
```

The report is written to:

```text
pm/roadmap/myproject/adoption/adoption-discovery.md
```

Use that report to decide whether to run `bootstrap/new-project.sh`, how to
name the current phase, which source canon matters, which tests prove health,
and whether the project needs local PMO contract extensions.

## Roadmap Lifecycle

```mermaid
stateDiagram-v2
  [*] --> PhaseOpen
  PhaseOpen --> StoryReady: create story files
  StoryReady --> InProgress: pick one story
  InProgress --> CommitGate: stage implementation + docs
  CommitGate --> Blocked: missing contract/evidence
  Blocked --> CommitGate: fix docs/evidence/contract
  CommitGate --> StoryDone: commit accepted
  StoryDone --> EvidenceWritten: evidence-story-N.md ships
  EvidenceWritten --> PhaseStatusUpdated: current-phase-status updated
  PhaseStatusUpdated --> StoryReady: next story
  PhaseStatusUpdated --> PhaseClosed: exit criteria complete
  PhaseClosed --> [*]: final-summary.md
```

## File map

```
pmo-roadmap/
├── README.md                     ← this file
├── install.sh                    ← initial install into a target project
├── update.sh                     ← re-pull methodology/contract/hook
├── bootstrap/
│   ├── adopt-project.sh          ← mid-project adoption discovery runner
│   ├── new-project.sh            ← scaffold pm/roadmap/{slug}/ skeleton
│   └── session-intake.sh         ← capture user goal, direction, handoff
├── hooks/
│   ├── pre-commit                ← hygiene gate + optional work-log capture
│   └── post-commit               ← optional daily work-log finalizer
├── bin/
│   ├── dw                       ← roadmap maintenance CLI (adapter)
│   ├── work-log-read             ← daily work-log reader
│   └── work-log-summarize        ← deferred summarizer helper
├── lib/
│   └── dw_pmo/                   ← reusable PMO core: model, paths, parse,
│                                    validate, trace, render, mutations, api
├── tests/
│   ├── dw-core-tests.py          ← dw_pmo core unit tests
│   ├── roadmap-cli.sh            ← temp-roadmap CLI coverage
│   └── work-log-mvp.sh           ← temp-repo integration coverage
└── templates/
    ├── roadmap-builder.md        ← canonical methodology
    ├── adoption-discovery-prompt.md ← mid-project discovery prompt
    ├── session-intake.md.tmpl    ← user/session intake template
    ├── PMO-CONTRACT.md           ← rules + contract template
    ├── CLAUDE-snippet.md         ← snippet to add to target CLAUDE.md
    ├── project-README.md.tmpl    ← stub for pm/roadmap/{slug}/README.md
    ├── phase-status.md.tmpl      ← stub for current-phase-status.md
    └── story.md.tmpl             ← stub for story-{n}-*.md
```

## First real consumer

`~/dev/projects/pantrybot/` — installed 2026-04-25.

## Conventions

- Bash 3.2 compatible (default macOS shell).
- POSIX `stat` differences (macOS `-f %m` vs Linux `-c %Y`) handled.
- No external runtime dependencies; the hooks are pure bash + `git` + `grep`.
- Hook never auto-stages or auto-commits anything; it only blocks or passes.

## Maintenance

- Edit canonical files here, then run `update.sh` against each consumer
  project to roll the change forward.
- Keep `templates/PMO-CONTRACT.md`, `hooks/pre-commit`, and
  `hooks/post-commit` in sync when changing work-log contract behavior.
