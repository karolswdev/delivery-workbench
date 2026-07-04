# WLA-12-05 - Prove the Codex rider end-to-end

- **Project:** work-log-automation
- **Phase:** 12
- **Status:** done
- **Depends on:** WLA-12-04
- **Unblocks:** WLA-12-07
- **Owner:** unassigned

## Problem

Codex reads AGENTS.md natively, supports custom prompts and MCP
servers, and is already half-inside this ecosystem: HoldSpeak's
agent hook watches Codex sessions through `~/.codex/hooks.json`.
But nothing installs the rails for it — no rendered brief, no
prompt equivalents of the four commands, no MCP registration — and
nobody has proven the full story loop under Codex. Until the loop
runs end-to-end in a fixture repo, "works with Codex" is a claim,
not a property.

## Scope

- **In:** A Codex renderer on the WLA-12-04 seam plus an install
  verb (working name `dw rider install codex`): writes the
  AGENTS.md managed block, renders the four command specs as Codex
  custom prompts (location per the WLA-12-01 matrix, resolved
  against the installed version), and emits the MCP registration
  snippet for `~/.codex/config.toml` (printed for the user, not
  silently written into their home config). Installation is
  idempotent and doctor-visible. Must coexist with an existing
  HoldSpeak `~/.codex/hooks.json` — verified, not assumed. The
  proof: the full loop (next → in-progress → work → evidence
  capture → done → contract certified by the human → gated commit)
  run under Codex CLI in a rails fixture repo, captured with
  `dw evidence capture`. Journal entry written in the moment,
  including anything Codex did differently than Claude Code.
- **Out:** pi (WLA-12-06); doctor's full rider-validation matrix
  (WLA-12-07); changing HoldSpeak's hook templates.

## Acceptance criteria

- [ ] `dw rider install codex` (final name may differ) wires a
  fixture repo: AGENTS.md block present, prompts discoverable by
  the installed Codex, MCP snippet emitted; running it twice
  changes nothing.
- [ ] The full story loop runs under Codex in the fixture repo and
  the evidence file records the real session transcript path or
  output, exit codes included.
- [ ] With HoldSpeak's Codex hook installed simultaneously, both
  function: the hook still reports the session, the rails still
  gate the commit.
- [ ] Tests for the renderer/installer run in CI; docs updated
  (`docs/riders.md` gains the Codex how-to).

## Test plan

- **Unit:** renderer output; installer idempotency.
- **Integration:** installer against a fixture repo; drift rule
  covers the Codex-rendered surfaces.
- **Manual / device:** the live Codex loop, evidence-captured; the
  coexistence check with the HoldSpeak hook.

## Notes / open questions

- MCP under Codex is registered globally in `config.toml`, not
  per-repo — the snippet approach keeps us out of the user's home
  config; revisit only with a recorded decision.
