# Delivery Workbench

![Pixel-art delivery workbench: a desk with a retro computer showing a green checkmark, stamped contract papers, a rubber stamp, and a cargo cart carrying a sealed package](./pmo-roadmap/assets/delivery-workbench-icon.png)

Delivery Workbench is a planning and commit gate system for Git
repositories where AI agents do much of the work. It addresses two
problems: agents claim work is done when it is not, and months later
nobody can tell what a commit shipped or what tested it.

Plans are Markdown files in the repo, organized as phases and
stories. A story cannot be marked done until a command run is
recorded in its evidence file. A commit cannot land until a
pre-commit hook checks a contract whose facts (branch, HEAD, staged
tree) are stamped and re-verified. Each commit carries trailers
naming the story it shipped and the contract that certified it.
State is Markdown files and git data; there is no database or
server.

Humans and agents use the same commands. Agents can also use the
included MCP server.

## Install

```bash
pipx install delivery-workbench
# or
brew install karolswdev/tap/delivery-workbench
```

Then set up any Git repository:

```bash
dw install /path/to/repo --skip-bootstrap
```

This copies the hooks, the CLI, and the MCP server into the repo's
`.githooks/` directory and points `core.hooksPath` at it. Commits
are gated by the copy inside the repo, not by the global install.
`dw update /path/to/repo` refreshes the copy;
`dw update /path/to/repo --check` reports if it is stale.

For a project with existing history, there is an adoption flow that
inspects the repo and drafts a roadmap for you. See the
[framework README](./pmo-roadmap/README.md).

## The daily loop

```bash
.githooks/dw next                       # what should I work on?
.githooks/dw story status myapp 2 3 in-progress
# ... do the work ...
.githooks/dw evidence capture myapp 2 3 -- npm test
.githooks/dw story status myapp 2 3 done    # refuses if no evidence exists
git add -A
.githooks/dw contract new               # stamps verified facts into .tmp/CONTRACT.md
# read the contract, verify each rule actually holds, check its boxes
git commit                              # the hook re-verifies everything
```

Checking the contract's boxes is deliberately manual: it is the
attestation that each rule was verified. No command or tool does it.

```mermaid
sequenceDiagram
  participant Dev as Human or agent
  participant DW as dw CLI
  participant Git as git commit
  participant Gate as pre-commit gate

  Dev->>DW: dw story status ... in-progress
  Dev->>Dev: do the work
  Dev->>DW: dw evidence capture ... -- <verify command>
  Dev->>DW: dw story status ... done (refuses without evidence)
  Dev->>DW: dw contract new (stamps verified facts)
  Dev->>Dev: verify each rule, check its boxes
  Dev->>Git: git commit
  Git->>Gate: re-derive every stamped fact
  Gate-->>Git: pass, or block naming the failed rule
  Git->>Git: stamp PMO trailers, archive the contract
```

## Tracing a commit

The artifact chain:

```mermaid
flowchart LR
  C[commit + PMO trailers] --> S[story file]
  S --> E[evidence file with captured runs]
  C --> A[archived contract in .git]
  P[current-phase-status] --> S
  E -.proves.-> S
```

This repository uses its own gate, so the chain can be inspected
here. One commit:

```text
$ git log -1 --format='%h %s%n%(trailers:key=PMO-Story)%(trailers:key=PMO-Contract-Digest)' ec1fb4a
ec1fb4a Complete WLA-10-03: guarded mutation tools on the MCP surface
PMO-Story: WLA-10-03
PMO-Contract-Digest: sha256:2700dd6a9c8e8ee8ec6053e7a741ace4123ba6750b8946bf2331af9ecadc3777
```

The trailer names the story. The story file states the acceptance
criteria. Its paired evidence file contains the recorded run that
justified marking it done, including the exact command, exit code,
and staged-tree hash at capture time:

```text
### Captured run — 2026-07-03T19:59:44Z

- **Command:** `bash -c ... bash pmo-roadmap/tests/mcp-server.sh; python3 pmo-roadmap/tests/dw-core-tests.py ...`
- **Exit code:** 0
- **Index-tree:** b1c5aaa6e7845d8143d9f3cf24c039d491e7e1fd
```

The certified contract is archived under
`.git/pmo-contract-archive/<sha>`. Because hooks only run where they
are installed, `dw verify` re-checks the structural rules from
pushed history, and CI catches commits that bypassed a local gate:

```text
$ .githooks/dw verify --all
dw verify: ok (45 commits verified, 17 pre-epoch skipped)
```

## The CLI

| Command | What it does |
|---|---|
| `dw next` | The next actionable story. Exit 0 found, 2 nothing to do. |
| `dw context --compact` | JSON snapshot of the roadmap: issues, warnings, next story, trace paths. |
| `dw check` | Lints roadmap structure and evidence content. Greppable errors, exit 1 on issues. |
| `dw story status <p> <ph> <st> <status>` | Updates a story's status transactionally. Refuses done without evidence. |
| `dw evidence capture <p> <ph> <st> -- <cmd>` | Runs the command and records it into the story's evidence file. |
| `dw contract new` | Writes `.tmp/CONTRACT.md` with stamped, machine-verified facts. |
| `dw gate` | Dry-runs the commit gate against the current stage. |
| `dw verify [--all]` | Re-checks the gate's structural rules over pushed history. |
| `dw phase create`, `dw story create` | Scaffolding for new roadmap work. |
| `dw doctor` | Checks the wiring in this clone. |

All commands have stable exit codes. The orientation commands
support `--json` or `--porcelain` output.

## The MCP server

`dw install` also vendors `.githooks/dw-mcp` and writes an entry into
the repo's `.mcp.json`, which Claude Code and other MCP clients pick
up automatically. The server exposes nine tools backed by the same
code as the CLI: `dw_context`, `dw_next`, `dw_check`, `dw_doctor`,
`dw_verify`, `dw_gate`, `dw_story_status`, `dw_evidence_capture`, and
`dw_contract_new`.

An agent can take a story from backlog to done through tool calls
alone, with the same refusals the CLI gives. Two operations are
deliberately absent: certifying a contract and creating a commit.
Schemas and design are in [docs/mcp.md](./docs/mcp.md).

## The web view

`dw-workbench --root /path/to/repo` serves a localhost-only page for
browsing the roadmap: phase tables, story and evidence pairs, a
health console, and the trace from a story to the commits that
shipped it. It can edit roadmap files through a guarded
preview-then-apply flow. It never stages or commits.

![Workbench project overview: phase table with status badges, evidence counts, the next actionable story, and a validation warning](./assets/workbench-overview.png)

More screenshots and two terminal recordings are in
[demos/](./demos/README.md).

## Other components

- Local work logs: consent-gated daily notes of what each commit delivered.
- A Claude Code plugin with slash commands and a skill covering the operating loop.
- A managed `CLAUDE.md` block installed into adopted repos.
- A copyable `verify-history` CI job that re-checks pushed history on every pull request.

## This repo runs on it

Every phase and story of the framework was shipped through its own
gate: ten phases, each story with evidence, every commit with
trailers and an archived contract, the full history passing
`dw verify --all`. The trail is in
[pmo-roadmap/pm/roadmap/work-log-automation/](./pmo-roadmap/pm/roadmap/work-log-automation/).

## Documentation

- [Architecture](./docs/architecture.md), with the test that proves each claim
- [Framework README](./pmo-roadmap/README.md): install, update, adopt, operate
- [The contract rules](./pmo-roadmap/templates/PMO-CONTRACT.md)
- [Remote verification design](./docs/remote-verification.md)
- [MCP surface design](./docs/mcp.md)
- [Distribution design](./docs/distribution.md)
- [Contributing](./CONTRIBUTING.md) and [changelog](./CHANGELOG.md)

## Tests

The suites live in `pmo-roadmap/tests/` and run standalone. CI runs
all of them on ubuntu and macos, the unit suite on python 3.9 (the
floor), and history verification on every push.

## License

[MIT](./LICENSE). Current version: 1.7.0.
