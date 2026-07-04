# WLA-12-01 - Design the symbiosis contract and the journal charter

- **Project:** work-log-automation
- **Phase:** 12
- **Status:** done
- **Depends on:** none
- **Unblocks:** WLA-12-02, WLA-12-04
- **Owner:** unassigned

## Problem

The gate is harness-agnostic (git hooks plus a CLI), but everything
around it is Claude-shaped: the orientation block targets CLAUDE.md
first, the four commands exist as hand-synced twins in
`.claude/commands/` and `plugin/commands/`, and MCP is stdio wired
for one client. Meanwhile HoldSpeak — the voice surface on the same
desk — already hooks Claude Code and Codex sessions, ships a plugin
host with a `delivery` intent, and gates external side effects
behind propose → approve → execute. Nobody has written down the
contract that makes these one system: which surfaces exist, what
each can actually host (verified against the live tools, not
folklore), what renders from a single canonical brief, and which
HoldSpeak seams we ride versus leave alone. Without that document,
stories 02–07 would each improvise their own answer and the phase
would ship four integrations instead of one contract with four
renderings. The phase also commits to journaling every step in the
moment; the journal needs a charter before entry 1 exists, or the
entries will drift in voice and honesty bar.

## Scope

- **In:** A design document `docs/riders.md` that records: (a) the
  capability matrix for the four surfaces — Claude Code (context
  file, commands, plugin, MCP stdio: all proven today), Codex CLI
  (AGENTS.md, custom prompts, MCP config, hooks file — each claim
  verified against the installed CLI), pi (context file and
  extension surface verified the same way; expected CLI-first, no
  MCP), HoldSpeak (plugin packs, `.hs/` project context, agent
  hook, projects API — cited to its docs and pinned to the version
  we integrate against); (b) the canonical-brief architecture: one
  source of truth for the agent brief and the four command specs,
  rendered per surface, with drift between rendered copies made a
  `dw check`-able offense (implemented in WLA-12-04); (c) the
  chosen HoldSpeak seams — roadmap-alignment synthesizer
  (WLA-12-02), story actuator behind a `shell:exec` manifest
  (WLA-12-03), Desk/`.hs/` presence (WLA-12-07) — and, explicitly,
  what we do not touch (HoldSpeak core, its meeting pipeline, any
  new egress path on their side); (d) proof obligations for
  02–07: the full story loop (next → in-progress → work → evidence
  → done → contract → gated commit) must run end-to-end under each
  typing surface in a fixture repo, and the HoldSpeak pieces must
  clear that project's own "shipped bar" (real run, real artifact,
  registered renderer, chain membership, tests). Also the journal
  charter in `docs/journal/README.md`: voice (first person,
  present tense, written while the work happens), cadence (one
  entry per story, shipped in the story's commit), and the honesty
  bar (refusals, dead ends, and failed captures stay in). Journal
  entries 0 (phase opening) and 1 (this story) written under it.
- **Out:** Implementing any renderer, pack, or CLI change
  (WLA-12-02 through 12-07); changing HoldSpeak itself; deciding
  Desk visual presentation (WLA-12-07 explores it).

## Acceptance criteria

- [ ] `docs/riders.md` exists with the four-surface capability
  matrix, every Codex and pi claim marked verified-against-live-tool
  or explicitly unverified-with-reason, and the HoldSpeak version we
  integrate against pinned.
- [ ] The canonical-brief architecture is recorded with the drift
  rule WLA-12-04 must implement, and each of stories 02–07 has its
  proof obligation named in the doc.
- [ ] `docs/journal/README.md` states the charter (voice, cadence,
  honesty bar) and entries 0 and 1 exist under it.
- [ ] Docs-lint passes.

## Test plan

- **Unit:** n/a (design story).
- **Integration:** `pmo-roadmap/tests/docs-lint.sh`.
- **Manual / device:** run the actual Codex and pi CLIs to verify
  each capability claim; record versions in the matrix.

## Notes / open questions

- HoldSpeak is 0.x; its plugin/config surface can move. The matrix
  pins the version and the pack (WLA-12-02) declares it — drift
  becomes a documented compatibility note, not a silent break.
- Codex custom-prompt location has moved across versions (global
  `~/.codex/prompts` vs repo-level); resolve against the installed
  version, note the answer with the version that gave it.
