# DW-0-04 — Distribution, docs, and the HoldSpeak dogfood

- **Project:** delivery-belt
- **Phase:** 0
- **Status:** backlog
- **Depends on:** DW-0-02, DW-0-03
- **Unblocks:** B1 (HoldSpeak phase-86, the read-only belt)
- **Owner:** unassigned

## Problem

A CLI that lives only in this repo helps nobody: consumers get framework
files via `install.sh`/`update.sh`, and the substrate's whole point is to be
read by a consumer (the HoldSpeak hub, B1). And an unproven parser is a
liability — the dogfood against HoldSpeak's real 85-phase roadmap is what
makes the substrate honest before anything renders from it.

## Scope

- **In:** `install.sh` + `update.sh` copy `bin/dw` → `target/.githooks/dw`
  (chmod +x; same pattern as `work-log-read`); package README documents the
  CLI (subcommands, the JSON contract pointer, the python3-stdlib
  requirement as a stated exception to the pure-bash convention — hooks
  remain bash and never depend on `dw`); `templates/CLAUDE-snippet.md`
  mentions the verbs; the dogfood run: `dw state` + `dw cadence check`
  against `~/dev/tools/HoldSpeak`, every finding triaged (real desyncs fixed
  in a HoldSpeak commit, tolerated legacy explained in evidence); this
  phase's paperwork for THIS story updated via the verbs themselves.
- **Out:** installing into HoldSpeak (that runs from HoldSpeak's side after
  merge); hub/UI consumption (B1); hook changes.

## Acceptance criteria

- [ ] Fresh `install.sh` into a temp repo places an executable
      `.githooks/dw`; `update.sh` refreshes it; `tests/dw-cli.sh` asserts
      both.
- [ ] Package README has a "The `dw` CLI" section: subcommands, JSON
      contract version, python3 requirement, and the "hooks never depend on
      `dw`" invariant.
- [ ] Evidence records the full HoldSpeak dogfood output: state counts
      (projects/phases/stories), check findings, and the triage of each.
- [ ] This story's own status flip is performed by `dw story done DW-0-04`
      (the command and resulting diff recorded in evidence).
- [ ] `tests/dw-cli.sh` green end-to-end; `bash -n install.sh update.sh`
      clean.

## Test plan

- **Unit:** `tests/dw-cli.sh` (install/update section).
- **Integration / Cypress:** the HoldSpeak dogfood run (recorded verbatim).
- **Manual / device:** n/a.

## Notes / open questions

- `.githooks/dw` is an odd home for a CLI, but it is the one directory the
  framework owns in a consumer; a `bin/` would be a new contract. Consumers
  invoke `.githooks/dw` or alias it. Revisit if B1 wants a stabler path.
