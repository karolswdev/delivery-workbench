# WLA-22-02 - dw status — one deterministic core and CLI

- **Project:** work-log-automation
- **Phase:** 22
- **Status:** done
- **Depends on:** WLA-22-01
- **Unblocks:** WLA-22-03, WLA-22-04, WLA-22-05
- **Owner:** unassigned

## Problem

An agent must currently combine `doctor`, `check`, `next`, `holds`,
`git status`, contract inspection, and sometimes `gate` to know whether
it can work and which transition is safe. Each component is correct;
the orchestration is repeated, easy to omit, and unavailable as one
stable document.

## Scope

- **In:** a new stdlib-only `dw_pmo/status.py`; read-only gate inspection;
  Git workspace/contract classification; roadmap/project summaries;
  ordered structured actions; `dw status [project] [--json]`; exports;
  text renderer; a self-hosted update seam that cannot create a root
  roadmap shadow; schema, red-path, action-precedence, path-safety, and
  purity tests.
- **Out:** MCP, HTTP, UI, agent-doc changes (later stories); executing an
  action; network/CI checks; changing existing command exit contracts.

## Acceptance criteria

- [x] The model matches `docs/status-briefing.md` v1 exactly and derives
  semantics only by composing existing core functions.
- [x] Workspace state distinguishes staged, unstaged, untracked, rewrite,
  and absent/stale/unchecked/passing contract/gate states with bounded,
  repo-relative path lists.
- [x] Rails or roadmap failures produce `attention` and a blocking repair
  action; ambiguous multi-project state produces a manual selection
  action; normal work states select the documented next action in order.
- [x] `git commit` is recommended only when there is a staged index, no
  overlooked worktree change outranks it, and a side-effect-free gate
  inspection passes.
- [x] Repeated core/CLI reads are byte-stable in JSON and change neither
  tracked files nor `.git/pmo-events.jsonl`.
- [x] Human output leads with verdict and `next`, while `--json` emits the
  core object byte-for-byte; exit 0 means ready and exit 1 means attention.
- [x] Refreshing vendored rails from inside the framework repository does
  not create `pm/roadmap/` and cannot make status inspect an empty shadow
  instead of the canonical `pmo-roadmap/pm/roadmap/` tree.

## Test plan

- **Unit:** fixture matrix for clean next story, active dirty work, mixed
  staging, missing/stale/unchecked/passing contracts, broken rails,
  roadmap issues, rewrite state, multiple projects, path bounds, purity.
- **Integration:** extend `roadmap-cli.sh` with a guided sequence and JSON
  parity; run the complete core suite.
- **Manual / device:** run text and JSON status against this source repo at
  clean, dirty, staged, contracted, and gate-passing transitions.

## Notes / open questions

`ready` means “safe to continue on these rails,” not “clean” or “done.”
Certification stays a manual action with no command array. Status may
inspect the gate but must suppress rail-event emission; a read is not a
gate attempt.

Implemented by `dw_pmo.status`, with the CLI as a zero-semantics adapter.
The fixture matrix pins the exact schema and precedence across clean, dirty,
staged, contracted, gate-ready, invalid-roadmap, rewrite, and ambiguous
project states. During dogfooding, the self-hosted updater was also corrected
so it cannot introduce a root roadmap shadow ahead of the canonical nested
roadmap.
