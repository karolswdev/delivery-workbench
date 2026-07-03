---
name: delivery-workbench
description: Operate a Delivery Workbench repository — evidence-first Markdown roadmaps with a machine-verified commit gate. Use when the repo has a pm/roadmap/ tree and .githooks/dw, when a commit is blocked by the PMO gate, or when asked to work, prove, or ship roadmap stories.
---

# Operating Delivery Workbench

This repository uses Delivery Workbench: an evidence-first commit gate
over a Markdown roadmap under `pm/roadmap/<project>/` (phases, stories,
paired evidence files). Markdown is the source of truth; `.githooks/dw`
is the CLI for everything below. Run `.githooks/dw doctor` if anything
seems miswired. `.githooks/dw-workbench --root .` serves a localhost
web view of the roadmap (browse, health, trace, guarded edit).

## Orient before working

- `.githooks/dw context [project] --compact` — JSON snapshot: issues,
  warnings, next story, per-story trace paths.
- `.githooks/dw next [project]` — the next actionable story
  (exit 0 = found, 2 = nothing actionable, 1 = error; `--json` for a
  machine-readable object).
- `.githooks/dw check [project]` — structural and evidence-content
  lint; greppable `ERROR <path>: <issue>` lines, exit 1 on issues.
  `dw check: ok` is the green signal.

## Work a story

Statuses: `backlog | ready | in-progress | blocked | done`;
done-synonyms `complete | closed | shipped` gate identically.

1. `.githooks/dw story status <project> <phase> <story> in-progress`
2. Do the work.
3. Prove it — run the real verification through
   `.githooks/dw evidence capture <project> <phase> <story> -- <command>`
   (records command, exit code, index tree, and output into the story's
   evidence file; screenshots/binaries go under `assets/` next to it).
4. `.githooks/dw story status <project> <phase> <story> done`
   (refuses without evidence).

## Commit — every commit passes the gate

1. Stage everything (`git add …`), THEN generate the contract:
   `.githooks/dw contract new [--story ID] [--consent yes --reasons "…"]
   [--tests-capture <evidence-path>[#ts]]`
   It stamps machine-verified facts (branch, HEAD, index tree, staged
   sample, story IDs); restaging afterwards invalidates it (regenerate
   with `--force`).
2. Honestly verify each rule, then flip every `- [ ]` to `- [x]` in
   `.tmp/CONTRACT.md`. A `--tests-capture` reference pre-checks the
   "Tests ran." box and is re-verified by the gate.
3. `git commit`. Trailers (`PMO-Story`, `PMO-Contract-Digest`) and the
   contract archive under `.git/pmo-contract-archive/<sha>` are
   automatic; the contract survives an aborted commit.

## Gate rules and recovery

The machinery enforces: one story flips done per commit (bundle only
with `.tmp/BUNDLE-OK.md` + one-line rationale), the flipped story's
`evidence-story-NN.md` ships in the same commit, and evidence never
appears or disappears orphaned. Preflight any time with
`.githooks/dw gate [--porcelain]` — it never consumes the contract.
`.githooks/dw verify [<base>..<head> | --all]` re-derives the
structural rules from pushed history alone — audit any range,
no local contract needed.
`.githooks/dw-mcp` serves the same core as MCP tools
(dw_context, dw_next, dw_check, dw_verify, dw_story_status,
dw_evidence_capture, ...) over stdio for MCP-capable agents —
wired via `.mcp.json`; certification is never a tool call
(`docs/mcp.md`).

**Never use `--no-verify`.** When blocked, read the banner — it names
the failed rule id and the remediation, and includes the exact
contract template to regenerate. Fix what it names, re-run
`dw contract new --force`, re-certify, and commit again. If the rules
themselves seem wrong for the work, stop and raise it with the user
rather than bypassing.

## Canon

- `pm/roadmap/PMO-CONTRACT.md` — the rules and the contract template
  (rule ids, tiers, project extensions).
- `pm/roadmap/roadmap-builder.md` — the methodology: directory
  contract, file specs, lifecycle, naming.

## If the repo lacks the rails

The plugin teaches the operating loop; the rails themselves are
per-repository. If `pm/roadmap/` or `.githooks/dw` is missing, install
them from https://github.com/karolswdev/delivery-workbench
(`pmo-roadmap/install.sh /path/to/repo`, or the three-command adoption
path for running projects — see `/dw-adopt`).
