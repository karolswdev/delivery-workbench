# WLA-12-04 - Collapse the agent-surface duplication behind a canonical brief

- **Project:** work-log-automation
- **Phase:** 12
- **Status:** backlog
- **Depends on:** WLA-12-01
- **Unblocks:** WLA-12-05, WLA-12-06
- **Owner:** unassigned

## Problem

The four slash commands exist twice — `.claude/commands/` and
`plugin/commands/` — kept identical by hand, and the orientation
brief is written directly into whichever of CLAUDE.md/AGENTS.md
`dw agent-docs` targets. Every new surface added this way is
another copy to forget. Before the Codex and pi riders exist
(WLA-12-05/06), the brief and the command specs need a single
canonical source with per-surface renderers, and drift between a
rendered copy and its source needs to be a `dw check` offense —
otherwise parity across four surfaces is a promise, not a property.

## Scope

- **In:** Canonical sources under the framework tree (brief +
  four command specs, format decided in WLA-12-01). A renderer —
  grown out of `dw agent-docs`, working name `dw rider docs` —
  that emits the Claude surfaces (`.claude/commands/*.md`,
  `plugin/commands/*.md`, the CLAUDE.md managed block) and the
  harness-appropriate AGENTS.md block, with per-surface variation
  (MCP wiring mentioned only where MCP exists). A `dw check` rule:
  rendered copy differs from what the source renders → `ERROR`
  line, exit 1. The existing Claude Code surfaces regenerated from
  canon with a provably-empty behavioral diff. Tests for renderer
  and drift rule. Journal entry written in the moment.
- **Out:** Codex- and pi-specific output targets (WLA-12-05/06 add
  their renderers on this seam); changing what any command *does*;
  the plugin skill's operating text beyond mechanical regeneration.

## Acceptance criteria

- [ ] One canonical source exists for the brief and each command;
  `.claude/commands/`, `plugin/commands/`, and the managed doc
  block are generated from it.
- [ ] Regenerating over the current tree produces no semantic diff
  (whitespace/marker changes enumerated and justified in evidence).
- [ ] Hand-editing a rendered copy makes `dw check` fail with an
  `ERROR` naming the file and the source; test proves it.
- [ ] Full test suite and docs-lint pass.

## Test plan

- **Unit:** renderer output per surface; drift-rule detection.
- **Integration:** `dw check` over a fixture with deliberate drift;
  regeneration idempotency (run twice, no diff).
- **Manual / device:** `/dw-next` and `/dw-contract` exercised in
  Claude Code after regeneration.

## Notes / open questions

- Decide in WLA-12-01 whether rendered copies stay committed
  (likely yes — plugin consumers read the repo) with the drift rule
  as the guard, or become build products.
