# Delivery Belt (substrate) — Roadmap

**Last updated:** 2026-07-07.
**Current phase:** [phase-0-substrate](./phase-0-substrate/current-phase-status.md)
**Status:** in-progress.

## Vision

The Delivery Belt is the factory-floor surface for delivery-workbench: each
project a belt, stories riding it through stations (candidate → scaffold →
story → evidence → contract gate → PR → CI → close), rendered in HoldSpeak's
DeskOS / web desk. The full RFC lives in the flagship consumer:
`HoldSpeak/pm/roadmap/holdspeak/proposals/delivery-belt.md`.

This roadmap project owns **B0 — the substrate**: the machine-readable state
layer the markdown renders FROM. Owner direction (2026-07-07, verbatim from
the proposal): the framework's agent integration today is
*"markdown-as-database plus hand-typed contracts — six prose surfaces per
shipping commit, edited by text surgery. CLI verbs and a machine-readable
state file are SUBSTRATE, not the product."*

B0 delivers a `dw` CLI: `dw state` (roadmap tree → JSON, generated-on-read),
`dw cadence check` (a linter that forces the prose surfaces into agreement),
and cadence verbs (`dw story start|done`, `dw phase close`) that replace the
mechanical half of the six-file surgery. The belt (B1+, in the HoldSpeak
roadmap) is the flagship consumer that forces this substrate honest; agents
get it as a by-product.

**The hard rule (from the proposal, canon):** the state layer RENDERS from
what already proves the work — story files, evidence files, final summaries,
the status tables. It never keeps a parallel truth. `dw state` is
generated-on-read; nothing is cached to disk in consumer repos.

## Source canon

- `HoldSpeak/pm/roadmap/holdspeak/proposals/delivery-belt.md` — the RFC
  (slices B0–B4, the two non-negotiables).
- `templates/roadmap-builder.md` — the directory + lifecycle contract `dw`
  parses. If `dw` disagrees with the methodology, the methodology wins.
- `templates/PMO-CONTRACT.md` + `hooks/pre-commit` — the rules `dw` verbs
  must mirror (evidence pairing, one story per commit).
- `install.sh` / `update.sh` — the distribution path `dw` rides.

## Phase index

| Phase | Goal (one line) | Status | Folder |
|---|---|---|---|
| 0 | The substrate: `dw state` + `dw cadence check` + cadence verbs, dogfooded on HoldSpeak's real roadmap | in-progress | [phase-0-substrate](./phase-0-substrate/) |

## Operating cadence

Every shipping commit for this roadmap updates, in the same commit:

1. The relevant story file header status.
2. The phase's `current-phase-status.md` story-status row and "Where we are".
3. This README's "Last updated" line.
4. Any canonical framework file touched by the story (README.md, install.sh,
   update.sh).
5. The evidence file for any story that flips to `done`.

This repo does not (yet) self-install the pre-commit gate; the cadence above
is honored manually. Self-installation is a recorded follow-up, not B0 scope.

## Project metadata

- **Slug:** `delivery-belt`
- **Story ID prefix:** `DW` (e.g. `DW-0-01`)
- **Greenfield?:** yes — `dw` does not exist; no compat surface to preserve.

## Glossary

- **Receipt** — an on-disk artifact that proves work (story file, evidence
  file, final summary, git/PR/CI state). The belt renders receipts only.
- **Surface** — one of the prose files the cadence requires updating per
  shipping commit (story header, status table, README lines).
- **Desync** — two surfaces disagreeing about the same fact; what
  `dw cadence check` exists to catch.
