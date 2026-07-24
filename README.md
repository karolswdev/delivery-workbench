# Delivery Workbench

[![validation](https://github.com/karolswdev/delivery-workbench/actions/workflows/validation.yml/badge.svg)](https://github.com/karolswdev/delivery-workbench/actions/workflows/validation.yml)
[![PyPI](https://img.shields.io/pypi/v/delivery-workbench)](https://pypi.org/project/delivery-workbench/)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](./LICENSE)

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

Delivery Workbench can also coordinate a bounded multi-agent delivery run.
Its visual orchestration editor configures the exact graph—research and worker
agents, dependencies, context, typed output conventions, checks, failure and
repair routes, budgets, approvals, and terminal handoff. A separate revocable
grant authorizes the compiled score; the conductor executes only those rules
and leaves certification and commit with the operator.

An additional, explicitly opt-in program layer sits above that one-run spine.
It compiles governed multi-story and multi-phase policy,
independent roles, bounded councils, carried obligations, and architecture
gates under a separate finite grant. Its restart-safe embedded conductor can
now execute one replay-derived act at a time through agent, check, repair,
council, meta-review, structural-loop, phase-architect, outward-signal, nudge,
story/phase-transition, and scope-completion boundaries. Its fresh-wheel exit
exam proves governed delivery across three stories and two phases, planted
crash recovery, exact refusal paths, and a separate dormant no-program
consumer. Integration/Git/roadmap rails remain fail-closed; ordinary Delivery
Workbench and bounded runs acquire none of this authority.

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
.githooks/dw status                     # is this repo ready, and what is safe next?
.githooks/dw step myapp                 # preview one state-bound, allowlisted action
# review the preview; run its exact apply=... command when it is applicable
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
| `dw status [project] [--json]` | One read-only readiness verdict and the next safe action across rails, workspace, and roadmap. |
| `dw step [project] [--json]` | Preview one state-bound action; `--json --apply --expect <token>` returns its bounded result after at most one allowlisted argv, never certification or commit. |
| `dw orchestration list\|show\|validate\|simulate` | Compile and explain exact `pm/orchestration/*.json` scores without starting agents or writing run state. |
| `dw organization list\|validate\|simulate` | Purely compile optional `pm/organizations/*.json`: logical pools, exact role packet/capability policy, principal/workspace separation, councils, resource waves, and finite replacement; an empty registry is healthy. |
| `dw workflow list\|validate\|simulate` | Purely compile reusable hierarchical `pm/workflows/*.json`: exact subflows, bounded runs/loops/debates, typed routes, finite envelopes, provenance, and capability consumers; an empty library is healthy. |
| `dw rubric list\|validate` | Purely compile optional governed-quality policy: mechanical versus judgment criteria, evidence/citations, aggregation/veto, and freshness; an empty registry is healthy. |
| `dw program list\|validate\|simulate\|plan` | Purely compile optional multi-phase policy, explain every roadmap candidate, and bind one deterministic workflow/team assignment to current Git, roadmap, and local roster facts; no grant or work starts. |
| `dw run plan\|start\|list\|show\|view\|preview\|tick\|supervise\|pause\|resume\|revoke\|cancel\|request\|checkpoint\|stream` | Preview and authorize an exact score-bound grant, conduct its bounded agent/check work, inspect its hash-chained run and outstanding typed requests, and apply only fresh-token controls. |
| `dw next` | The next actionable story. Exit 0 found, 2 nothing to do. |
| `dw context --compact` | JSON snapshot of the roadmap: issues, warnings, next story, trace paths. |
| `dw check` | Lints roadmap structure and evidence content. Greppable errors, exit 1 on issues. |
| `dw story status <p> <ph> <st> <status>` | Updates a story's status transactionally. Refuses done without evidence. |
| `dw evidence capture <p> <ph> <st> -- <cmd>` | Runs the command and records it into the story's evidence file. |
| `dw contract new` | Writes `.tmp/CONTRACT.md` with stamped, machine-verified facts. |
| `dw gate` | Dry-runs the commit gate against the current stage. |
| `dw verify [--all]` | Re-checks the gate's structural rules over pushed history. |
| `dw board [--json]` | The kanban in the terminal: a swimlane per phase, six status columns, evidence ticks. |
| `dw holds [--json]` | The ledger of parked work: every on-hold story and paused phase, each with its recorded reason. |
| `dw story show <p> <ph> <st> [--json]` | One story whole: header, status and why, story and evidence bodies, captured runs, receipts. |
| `dw phase create`, `dw story create` | Scaffolding for new roadmap work. |
| `dw doctor` | Checks the wiring in this clone. |

All commands have stable exit codes. `dw status` exits 0 for `ready` and
1 for `attention`; its JSON is a versioned contract suitable for an
agent's first repository read. `dw step` is its separate explicit act
boundary: preview is pure, stale tokens start nothing, and every invocation
stops after one child. Applied leases cannot replay even when the action was
read-only; JSON apply returns the versioned result and human apply renders the
same bounded streams. See [docs/deliberate-step.md](./docs/deliberate-step.md).
The specialist orientation commands
support `--json` or `--porcelain` output.

The optional `dw program` namespace now spans pure
`list|validate|simulate|plan`, exact grant `start`, canonical `show`, explicit
`preview`→`tick|supervise|request|pause|resume|revoke|cancel`, verified
`tail`, and bounded `stream`. MCP, localhost HTTP, SSE, and the progressively
disclosed Workbench `#/programs` control room adapt the same content-safe
projection and exact-token acts. No program configuration remains a healthy
ordinary mode, and opening a read or the Workbench starts no program, poller,
stream, process, or notification.

Parked work is first-class: a story goes on-hold only with a
recorded reason, whole phases pause and resume (`dw phase pause
--reason` / `resume`), and `dw next` skips parked work while naming
what it skipped. Every board card and holds entry carries its
receipt paths and workbench links, so a machine can walk card →
story → evidence without knowing the tree layout; the contract over
every supported CLI, HTTP, and MCP surface is
[docs/interop.md](./docs/interop.md).

## The MCP server

`dw install` also vendors `.githooks/dw-mcp` and writes an entry into
the repo's `.mcp.json`, which Claude Code and other MCP clients pick
up automatically. The server exposes 31 tools backed by the same
code as the CLI: orientation, browse, verification, guarded roadmap
mutations, pure orchestration reads/previews, and exact-token run acts. Run
tools accept selectors, run ids, bounded parameters, and fresh intent tokens;
they never accept score bodies, provider configuration, prompts, or check
commands from the caller.

An agent can take a story from backlog to done through tool calls
alone, with the same refusals the CLI gives. Two operations are
deliberately absent: certifying a contract and creating a commit.
Schemas and design are in [docs/mcp.md](./docs/mcp.md).

`dw step --json` is the shared preview handrail: CLI, MCP, and the workbench
HTTP API return the same state-bound document. Applying its exact token runs
at most the one closed-table action and returns the same bounded receipt on
all three transports; callers cannot supply argv, certify, commit, or loop.
See [the deliberate-step contract](./docs/deliberate-step.md).

## The web view

`dw-workbench --root /path/to/repo` serves a page for browsing the
roadmap. Its overview opens with the same briefing as `dw status`:
verdict, selected project, workspace/contract/gate state, and one
tokenized argv or explicitly manual next action. For an applicable action,
“review one deliberate step” opens a separate confirmation with the exact
token, authorized argv, and CLI fallback; applying runs at most that one
step, refreshes, and stops. Manual, certification, and commit states explain
why no apply control exists. The specialist views retain phase tables, story and evidence pairs, a health console,
the kanban board at `#/board` (drag moves ride the same guarded
preview-then-apply flow — a park demands its reason, done still
demands evidence), and the trace from a story to the commits that
shipped it. It can
edit roadmap files through a guarded preview-then-apply flow. It
never stages, certifies, or commits. Bound to localhost by default; reachable
over your own Tailscale network too (a `.ts.net` Host header is
allowed, since that name only resolves through your own
authenticated tailnet).

At `#/orchestration`, the same local Workbench now visually authors exact
coordination scores: typed agent/check/rail/approval/collect nodes, parallel
research and fan-in, prompts and context, output conventions, checks and red
failure routes, finite budgets, and terminal handoffs. Design, Validate, and
canonical JSON share one compiler; save/delete is a stale-safe
preview→diff→apply act and never grants or starts a run. The Run tab replays an
authorized execution on the same graph: attempts, agent/check sessions, typed
artifact lineage, budgets, repair routes, checkpoints, ledger receipts, and
explicit pause/resume/revoke/cancel decisions. Refresh and stream opens are
deliberate; there is no hidden poller, generic terminal, certification button,
or commit shortcut.

At `#/program-studio`, an explicitly entered advanced workspace authors the
optional Phase 26 policy family without changing that ordinary front door.
Programs show roadmap scope, binding rules, phase gates, requested
capabilities, finite budgets, and stops; workflows show accessible role lanes,
nested subflows, fan-in/out, typed loop/debate containers, verdicts, artifacts,
and exhaustion routes; organizations show implementer/verifier separation,
independent review panels, deliberative councils with explicit rule/decider/
checkpoint authority, meta-verifiers, architects, replacement, and audit
bounds. The runtime contract separately binds each resolved seat's logical
profile, harness, provider/router, model, principal/workspace/session identity,
and carried decision obligations; the live control room exposes those bindings,
nested activity, verdicts, dissent, obligations, delivery, and remaining
authority. Design, Simulate, Validate, JSON, and Authority are
projections of the same Python compilers. Graph/config round trips preserve
semantic and layout hashes, and
save/delete uses one stale-safe preview→diff→fingerprint→apply boundary scoped
to the selected tracked policy. Saving starts no work and grants no authority.
With no `pm/programs`, `pm/workflows`, or `pm/organizations`, the Studio is a
neutral optional empty state: `#/` remains ordinary Delivery Workbench, with
no setup prompt, background poller, or runtime state.

Tracked `pm/rubrics/*.json` policies use the same optional boundary.
`dw rubric list|validate` compiles exact criteria, evidence/citation rules,
mechanical versus judgment types, aggregation/veto policy, and freshness; the
wheel's example is never installed as project policy. The shared pure verdict
engine accepts mechanical facts only from typed check/rail receipts, binds
agent/meta/architect judgments to independently assigned read-only principals,
preserves independent-panel dissent and superseded verdicts, and emits a
pass/fail/pending/refused gate proof. Replay-derived council decisions remain a
separate input: rule outcomes name no agent decider, judge outcomes bind the
preassigned seat and full execution provenance, and every decision carries an
explicit obligations list. A green proof still starts nothing and grants no
integration, evidence, Git, or roadmap authority.

The optional program authority core now supplies the missing consent boundary:
one pure start preview freezes scope, policy hashes, worst-case budgets,
operator intent, every deterministic seat reachable across the granted scope,
and each seat's provider/model/auth execution binding; exact start creates
only a finite local grant and
hash-chained ledger under `.git`. Advisory grants permit no claims;
checkpointed and continuous grants reserve only named capabilities through
exclusive idempotent claims. Replay re-derives budgets and legal transitions,
child grants are strict non-delegable intersections, and pause/resume/revoke/
cancel use current-head generation-bound decisions. This remains invisible to
ordinary and bounded-run use unless a program is explicitly planned and
granted.

The embedded restart-safe program conductor now consumes that authority
through one deterministic `tick_program`. Every tick locks and replays the
program ledger, verifies immutable receipts, reconciles an already-dispatched
operation before retry, rebuilds the exact selection/team/workflow frontier,
claims at most one act, and stops. The delivered path covers isolated
implementation, deterministic fan-out/fan-in, built-in checks, independent
verification with finite repair, replay-derived council decisions and
meta-audit, obligation ingestion, typed finite workflow loops, and final-story
phase-architecture review. It also consumes already-observed Phase 25 signal
facts by hash, delivers only program-declared finite nudges to an already-run
agent under `nudge:deliver`, causally re-runs the declared downstream
verification path, carries non-blocking obligations across exact story/phase
selection, stops on blocking obligations, and enters `complete` only after the
pure planner proves the full granted scope done. Each completed loop round has
its own claim and
immutable receipt binding the typed predicate observation, producer receipt,
carried artifact hashes, exact round lineage, and success/continue/exhaustion
route; restart cannot spend or record that round twice. The conductor itself
still never integrates, certifies, commits, or edits roadmap status. The
separate WLA-26-10 `program_delivery` core now performs those acts only from a
pure exact preview and one claim per patch/evidence/roadmap/contract/
certification/commit/push effect, with crash reconciliation and no-force
remote leases. WLA-26-11 now exposes this same state and authority boundary
through CLI, MCP, HTTP, read-only SSE cursor replay, and the Workbench control
room. Its view explains the selected story/workflow/team, resolved execution
seats, active nested work, evidence/verdict/dissent/obligation gates, delivery,
budgets, controls, and exact stop reason without exposing credentials or raw
streams. Every mutation still requires a fresh matching exact token; bounded
supervision is an explicit finite invocation, never a hidden scheduler.

The installed-wheel exit exam composes the complete program path after one
continuous grant: three stories across two phases, one independent
reject/repair/pass, one bounded council with preserved dissent, a full
meta-audit, architect gates, exact evidence/integration/certification/commit/
push rails, and planted crash recovery. A second fresh consumer proves that
no-program use creates none of this state or activity.

![Workbench overview: repository briefing followed by project status and the next actionable story](./assets/workbench-overview.png)

More screenshots and two terminal recordings are in
[demos/](./demos/README.md).

## Mission control: steer from anywhere

The same roadmap state that gates commits is also a feed you can
watch and act on from outside the terminal. Three read-only CLI
documents make it a substrate any client can consume:

```bash
.githooks/dw state --json      # the roadmap: phases, stories, next actionable
.githooks/dw sessions --json   # which live agent is on which story
.githooks/dw events            # what happened on the rails (gate verdicts, flips)
```

Several clients consume that substrate today, including the
workbench web view above, which renders it as a read-only belt at
`#/mc`. A **Telegram interface**
(`integrations/telegram/`) puts mission control in your pocket:
bind a chat topic to a repo and it renders phases, stories, and
gate refusals; a blocked agent's question reaches your phone in
about a second through an installed hook — with arrow/Enter
buttons that drive the agent's actual prompt when the session is
bound and armed; and once you bind a session, you talk to the
agent by just typing, and your words relay into its terminal pane.
The pane itself arrives as a picture: `/screen` renders it to a
PNG with colors intact, `/live` keeps the picture refreshing, and
a configurable button toolbar covers the common keys. In a group,
consent belongs to the person who paired, not to the room. A **Desk conveyor** on the
[HoldSpeak](https://github.com/karolswdev/HoldSpeak) side renders
the same feed as a belt.

Everything that changes the rails stays gated. The owner is bound
by a one-time pairing token, not a hardcoded id. Story flips and
project creation are proposals that execute on an approval tap,
through the same allow-listed commands the CLI uses. The dw gate
still refuses a dishonest done-flip and relays the banner back
into the chat. Steering a terminal is guarded by explicit,
expiring session binding and a pane-ownership check on every
keystroke; sending a file runs it past seven refusal locks first.
The design is in
[docs/mission-control.md](./docs/mission-control.md) and
[docs/absorption-ccgram.md](./docs/absorption-ccgram.md).

## Other components

- Local work logs: consent-gated daily notes of what each commit delivered.
- A Claude Code plugin with slash commands and a skill covering the operating loop.
- A managed `CLAUDE.md` block installed into adopted repos.
- A copyable `verify-history` CI job that re-checks pushed history on every pull request.

## This repo runs on it

Every phase and story of the framework was shipped through its own
gate: each story with evidence, every commit with
trailers and an archived contract, the full history passing
`dw verify --all`. The trail is in
[pmo-roadmap/pm/roadmap/work-log-automation/](./pmo-roadmap/pm/roadmap/work-log-automation/).

## Documentation

- [Everyday product language](./docs/product-language.md): the Phase 27 vocabulary, presentation-only application-view boundary, complete surface inventory, technical-details escape hatch, and executable drift contract
- [Comprehensive solution overview](./docs/solution-overview.md): current architecture, workflows, trust model, proof snapshot, strengths, gaps, and delivered response
- [Status briefing contract](./docs/status-briefing.md): the Phase 22 one-answer model, readiness semantics, and guided action order
- [Deliberate step contract](./docs/deliberate-step.md): the Phase 23 state-bound preview/apply seam and closed executable action table
- [Visual orchestration contract](./docs/orchestration.md): the Phase 24 score editor, roles/research, outputs, checks/failures, grants, scheduling, drivers, recovery, and authority model
- [Optional autonomous-program contract](./docs/programs.md): the Phase 26 capability ladder, multi-phase scope, hierarchical workflows, organizations, independent verification, bounded councils/loops, grants, restart-safe conductor, and exact advancement boundaries
- [Architecture](./docs/architecture.md), with the test that proves each claim
- [Framework README](./pmo-roadmap/README.md): install, update, adopt, operate
- [The contract rules](./pmo-roadmap/templates/PMO-CONTRACT.md)
- [Remote verification design](./docs/remote-verification.md)
- [Contribution rails](./docs/contribution-rails.md): what survives a pull request
- [MCP surface design](./docs/mcp.md)
- [The interop contract](./docs/interop.md): every supported surface over CLI, HTTP, and MCP, with its schema version
- [Riders: the symbiosis contract](./docs/riders.md): one brief, every agent surface (Claude Code, Codex, pi, HoldSpeak)
- [The journal](./docs/journal/README.md): the worked example, phases delivered on their own rails, written in the moment with refusals and dead ends included (through the mission-control and ccgram-absorption phases)
- [Distribution design](./docs/distribution.md)
- [Contributing](./CONTRIBUTING.md) and [changelog](./CHANGELOG.md)

## Tests

The suites live in `pmo-roadmap/tests/` and run standalone. CI runs
all of them on ubuntu and macos, the unit suite on python 3.9 (the
floor), and history verification on every push. Two packaged exit exams
create fresh consumers: `guided-status-loop.sh` follows the shared briefing;
`deliberate-step-loop.sh` separately authorizes each CLI/MCP/HTTP lease without
reconstructing argv, proves same-action staleness, and keeps certification and
commit manual. Both reach real evidence, gate pass, trailers, archive, and
history verification.

## License

[MIT](./LICENSE). The PyPI badge above states the current version;
the [changelog](./CHANGELOG.md) tells each release's story.
