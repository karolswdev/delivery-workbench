# Delivery Workbench

[![validation](https://github.com/karolswdev/delivery-workbench/actions/workflows/validation.yml/badge.svg)](https://github.com/karolswdev/delivery-workbench/actions/workflows/validation.yml)
[![PyPI](https://img.shields.io/pypi/v/delivery-workbench)](https://pypi.org/project/delivery-workbench/)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](./LICENSE)

![Pixel-art delivery workbench: a desk with a retro computer showing a green checkmark, stamped contract papers, a rubber stamp, and a cargo cart carrying a sealed package](./pmo-roadmap/assets/delivery-workbench-icon.png)

<!-- BEGIN EVERYDAY PRODUCT GUIDE -->
Delivery Workbench keeps your work honest. You plan in Markdown, prove
your work ran, and every commit checks that the proof matches. Humans
and AI agents use the same commands and see the same facts.
<!-- END EVERYDAY PRODUCT GUIDE -->

## Install

```bash
pipx install delivery-workbench   # or: brew install karolswdev/tap/delivery-workbench
```

Set up any Git repo:

```bash
dw install /path/to/repo
```

Or start fresh:

```bash
mkdir my-project && dw init my-project
```

## The loop

The whole workflow is four steps:

```bash
# 1. See where you are
dw status

# 2. Do the work, then prove it
dw evidence capture myapp 2 3 -- npm test

# 3. Mark it done (refuses without proof)
dw story status myapp 2 3 done

# 4. Commit (the gate checks everything)
git add -A && dw contract new
# read .tmp/CONTRACT.md, verify each rule, check the boxes
git commit
```

That's it. The pre-commit hook re-derives every fact in the contract.
If something doesn't match, it tells you what failed and how to fix it.

```mermaid
sequenceDiagram
  participant You as You (human or agent)
  participant DW as dw
  participant Git as git commit
  participant Gate as pre-commit hook

  You->>DW: evidence capture -- <test command>
  You->>DW: story status ... done
  You->>DW: contract new
  You->>You: verify rules, check boxes
  You->>Git: git commit
  Git->>Gate: re-check every stamped fact
  Gate-->>Git: pass or block (names the rule)
```

## What you get

Every commit carries its receipt:

```
$ git log -1 --format='%h %s%n%(trailers:key=PMO-Story)'
ec1fb4a Complete WLA-10-03: guarded mutation tools
PMO-Story: WLA-10-03
```

The story file states what had to be true. The evidence file proves
it was. The archived contract binds both to the exact staged tree.
`dw verify --all` re-checks the whole history from pushed commits
alone — CI catches anything that bypassed a local hook.

## Common commands

| Command | What it does |
|---|---|
| `dw status` | Where am I? What's next? |
| `dw next` | The next story to work on |
| `dw board` | Kanban view of all stories |
| `dw evidence capture <p> <ph> <st> -- <cmd>` | Run a command and record the proof |
| `dw story status <p> <ph> <st> <status>` | Move a story (refuses done without evidence) |
| `dw contract new` | Stamp the facts for your commit |
| `dw gate` | Dry-run the commit check |
| `dw check` | Lint the roadmap for issues |
| `dw doctor` | Diagnose the wiring in this clone |
| `dw verify [--all]` | Re-check history from pushed commits |

Run any command with `--help` for details. Most support `--json` for
machine-readable output.

## The workbench

```bash
dw-workbench --root /path/to/repo
```

A multi-panel workspace for managing delivery — inspired by
[Operator](https://github.com/iishyfishyy/operator-oss), built on
DW's evidence-first model.

![Dark workbench board with four story lanes, one item needing input, and one completed story](./assets/workbench-board.png)

- **Kanban board** as the home view — drag stories, create inline,
  park with a reason
- **Live session stream** — watch agents work in real time (tool
  calls, edits, questions)
- **"Needs you" inbox** — a global count of pending decisions with
  browser notifications and one-click jump
- **Inline ask-and-resume** — answer an agent's typed request right
  in the transcript, and the agent continues
- **Diff review** — see what changed, file by file
- **Integrated terminal** — run `dw` and `git` commands without
  leaving the browser
- **Session telemetry** — per-turn tokens, cache hits, cost
- **Insights dashboard** — stories shipped, evidence captured,
  commit activity over time
- **Memory pane** — for any run or program, see exactly what the
  agent recalled before it acted, why each item matched, and what it
  wrote back when it finished
- **Decision timeline** — every scheduling, routing, verdict, and
  council decision explained from recorded facts and rules, with
  mechanical checks and model judgments labeled differently
- **Command palette** — Ctrl+K to jump to any project, story, run,
  or request
- **Reconnect-safe** — close your laptop, reopen, pick up where you
  left off; the stream announces disconnected, retrying, and
  caught-up states instead of going silently stale
- **Comfortable or compact** — a density setting that sticks, honest
  dark mode, and reduced-motion support throughout

Panels coexist side-by-side (board + session + diff + terminal),
resize with dividers, and remember their layout. On mobile they
stack with a tab bar. Advanced features (orchestration, programs,
grants) live behind one "Advanced" entry — out of sight until you
need them.

The workbench never commits for you. Every mutation goes through
preview, exact token, apply.

## Memory that compounds

Every bounded run and autonomous program is memory-driven:

- **Recall before dispatch.** Before any agent acts, the workbench
  assembles a bounded recall from what the repository has learned —
  earned lessons, prior outcomes, evidence digests, past decisions,
  grounded code locations. The ranking is deterministic and
  explainable: every included item says why it matched, every
  excluded item says why it was dropped. No embeddings, no services.
- **A glass pane, not a black box.** The memory pane shows what the
  agent knew; the decision timeline shows which facts and rules
  produced each decision. Neither ever shows (or stores) hidden
  model reasoning.
- **Writeback at the end.** Every outcome — success or failure —
  leaves a distilled, provenance-bound receipt. Failures become
  candidate warnings future runs can see; only evidence-backed
  outcomes become confirmed lessons. The next related run recalls
  them; an unrelated run provably does not.
- **Memory informs, never authorizes.** No memory document can start
  work, widen a grant, satisfy evidence, or alter a verdict — the
  test suite proves it at every seam.

![Dark memory pane showing recalled facts, match reasons, source details, and decision use](./assets/workbench-memory.png)

Inspect it anywhere:

```bash
dw knowledge recall --run <run-id>     # what a run recalled, and why
dw knowledge writebacks --story <id>   # what past runs left behind
```

The same projections are byte-identical over MCP
(`dw_knowledge_recall`, `dw_knowledge_writebacks`) and read-only
HTTP (`/api/runs/{id}/memory`).

## AI agents

The same CLI works from Claude Code, Codex, or any MCP client.
`dw install` vendors an MCP server (`.githooks/dw-mcp`) that
exposes the same operations as tool calls. An agent can take a story
from backlog to done through tools alone — with the same refusals a
human gets.

Two things stay manual on purpose: verifying the contract and
creating the commit.

## Going further

Delivery Workbench has optional layers for teams that need more
structure. These are all opt-in and don't change ordinary use:

- **Bounded runs** — compiled coordination scores with typed agents,
  checks, failure routes, budgets, and grants
  ([docs/orchestration.md](./docs/orchestration.md))
- **Delivery programs** — multi-phase workflows with roles,
  independent verification, and replay-safe conductors
  ([docs/programs.md](./docs/programs.md))
- **Mission control** — watch and steer from Telegram, HoldSpeak,
  or any client that reads the event feed
  ([docs/mission-control.md](./docs/mission-control.md))
- **Project context** — revisioned, hash-bound instructions injected
  into every agent session, with agent-draft and operator-accept
  lifecycle (stored under `pm/context/`)
- **Agent suggestions** — agents propose follow-up work with
  provenance; accept to create a roadmap story, dismiss to archive
  (stored under `pm/suggestions/`)

## This repo runs on it

Every phase and story of this project shipped through its own gate.
The full trail is in
[pmo-roadmap/pm/roadmap/work-log-automation/](./pmo-roadmap/pm/roadmap/work-log-automation/).

## Docs

- [Everyday delivery](./docs/everyday-delivery.md) — the full walkthrough
- [Architecture](./docs/architecture.md) — how it works, with the test that proves each claim
- [Repository knowledge](./docs/repository-knowledge.md) — the memory layer's contract
- [Product language](./docs/product-language.md) — the words the product uses, pinned
- [Usability journeys](./docs/usability-journeys.md) — the thirteen canonical journeys the exams drive
- [MCP surface](./docs/mcp.md) — tool schemas and design
- [The contract rules](./pmo-roadmap/templates/PMO-CONTRACT.md)
- [Contributing](./CONTRIBUTING.md) and [changelog](./CHANGELOG.md)

Full documentation index: [docs/](./docs/)

## Tests

```bash
cd pmo-roadmap/tests && python3 dw-core-tests.py
```

CI runs the full suite on Ubuntu and macOS, with floor-version
coverage on Python 3.9 and history verification on every push.

## License

[MIT](./LICENSE)
