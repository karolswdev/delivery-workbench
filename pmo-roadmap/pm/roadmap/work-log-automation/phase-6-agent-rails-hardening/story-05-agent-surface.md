# WLA-6-05 - Ship the first-class agent surface

- **Project:** work-log-automation
- **Phase:** 6
- **Status:** backlog
- **Depends on:** WLA-6-03, WLA-6-04
- **Unblocks:** WLA-6-06
- **Owner:** unassigned

## Problem

The framework is built for agentic delivery, but its entire agent-facing
contract is a markdown snippet a human must remember to paste
(`install.sh` prints it and hopes). The snippet never mentions `dw` — the
best mid-session discoverability tool the framework has — so an agent
onboarded through it hand-edits status tables the CLI could write safely.
There are no shipped Claude Code commands or skills. `dw` is installed to
`.githooks/dw`, off PATH and undiscoverable. Several tool behaviors are
agent-hostile: `dw next` exits 1 with zero output whether there is nothing
to do or something failed; `dw story status` accepts any string, silently
stranding typo'd stories outside every view; the hook's failure banner
paraphrases the rules but makes the agent fetch the exact template from a
doc; `work-log-read` silently truncates at 260 lines.

## Scope

- **In:** Shipped agent commands under `pmo-roadmap/agent/` installed by
  `install.sh` into the target's `.claude/commands/` (and mirrored guidance
  for AGENTS.md consumers): `/dw-next` (orient and pick up work),
  `/dw-contract` (author the v2 contract via `dw contract new`),
  `/dw-story-done` (capture evidence, flip status, prepare the gated
  commit), `/dw-adopt` (drive the adoption flow). Managed CLAUDE.md
  integration: `install.sh --write-agent-docs` (default on, opt-out)
  appends a marker-delimited block to `CLAUDE.md`/`AGENTS.md`;
  `update.sh` refreshes only inside the markers. Snippet rewrite that
  covers `dw context/check/next/gate/contract/evidence capture`, the
  roadmap tree location, and the status vocabulary. CLI ergonomics:
  `dw next --json` plus exit-code semantics documented as 0 = story found,
  2 = nothing actionable, 1 = error; status values validated against the
  single vocabulary with a hard error on unknown; `work-log-read` full
  output by default with explicit paging flags and a truncation marker.
  Hook failure banners include the exact contract template inline.
  `dw doctor`: verifies hooksPath is set, hooks present, agent docs block
  present and current, python3 available — the per-clone silent-failure
  detector.
- **Out:** The workbench UI (Phase 5); editor/IDE integrations beyond
  Claude Code command files; any network calls.

## Acceptance criteria

- [ ] In a fresh temp repo, `install.sh` followed by an agent session that
  reads only `CLAUDE.md` can complete a full story lifecycle (create,
  work, capture evidence, flip done, gated commit) without reading
  framework source — demonstrated in evidence with the actual transcript
  or command log.
- [ ] The managed CLAUDE.md block is created by install, refreshed by
  update, and never duplicates or clobbers user content outside the
  markers (tests cover fresh, existing-file, and re-run cases).
- [ ] `dw next --json` and the 0/2/1 exit contract are tested; unknown
  status strings are rejected with the allowed vocabulary in the error.
- [ ] `dw doctor` detects and names: unset hooksPath, missing hooks, stale
  or missing agent-docs block, missing python3.
- [ ] The blocked-commit banner contains a copy-pasteable contract
  template for the project's actual rule set (canonical plus extensions).

## Test plan

- **Unit:** JSON output shape, exit codes, status validation, doctor checks
  in the `dw_pmo` suite.
- **Integration / Cypress:** Install/update round-trip test asserting the
  managed block lifecycle; `pmo-roadmap/tests/agent-surface.sh` running the
  command files' underlying scripts headlessly.
- **Manual / device:** Run one real story on this repo end-to-end using only
  the shipped commands.

## Notes / open questions

Command-file format should stay plain markdown prompts invoking `dw` so
they work for both Claude Code and other agents reading AGENTS.md. Whether
`dw` also gets a PATH-friendly launcher (e.g. `git dw` alias or a bin
symlink suggestion) is decided during implementation; the doctor must at
least print the canonical invocation.
