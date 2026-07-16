---
name: delivery-workbench
description: Operate a Delivery Workbench repository — evidence-first Markdown roadmaps with a machine-verified commit gate, plus the dw-mcp server exposing the same operations as MCP tools. Use when the repo has a pm/roadmap/ tree and .githooks/dw, when a commit is blocked by the PMO gate, when dw_* MCP tools are available, or when asked to work, prove, or ship roadmap stories.
---

# Operating Delivery Workbench

This repository uses Delivery Workbench: an evidence-first commit gate
over a Markdown roadmap under `pm/roadmap/<project>/` (phases, stories,
paired evidence files). Markdown is the source of truth; `.githooks/dw`
is the CLI for everything below. Run `.githooks/dw doctor` if anything
seems miswired. `.githooks/dw-workbench --root .` serves a localhost
web view of the roadmap (browse, health, trace, guarded edit).

## Start with one briefing

Start every work session with one briefing read; do not call both transports.

- `.githooks/dw status [project] --json` — the versioned readiness,
  workspace, roadmap, and next-safe-action object. Exit 0 means `ready`;
  exit 1 means `attention`. Attention is valid JSON: follow its blocking
  repair action before work. Status reads only; it never executes the action.
- MCP-capable agents may call `dw_status` instead. It returns the identical
  object in `structuredContent`; an `attention` verdict is not a tool error.

To act on a command recommendation, preview a fresh lease with
`.githooks/dw step [project] --json` (or MCP `dw_step`). Require
`applicable: true`, review the exact action/token/`apply_command`, and only
after explicit authorization invoke that exact command (or `dw_step_apply`
with the same `expect` token). Never reconstruct argv. One apply starts at
most one child and stops; re-read status and preview a new lease before any
next act. Manual/project-selection states, certification, and commit are
never applicable—stop for the user, and never build a step loop.

Use specialist surfaces for depth after the briefing:

- `.githooks/dw context [project] --compact` — JSON snapshot: issues,
  warnings, next story, per-story trace paths.
- `.githooks/dw next [project]` — the next actionable story
  (exit 0 = found, 2 = nothing actionable, 1 = error; `--json` for a
  machine-readable object).
- `.githooks/dw check [project]` — structural and evidence-content
  lint; greppable `ERROR <path>: <issue>` lines, exit 1 on issues.
  `dw check: ok` is the green signal.
- `.githooks/dw doctor` — detailed clone-wiring diagnosis when status names
  unhealthy rails.

## Work a story

Statuses: `backlog | ready | in-progress | blocked | done`;
done-synonyms `complete | closed | shipped` gate identically.

1. After authorization, require and apply a fresh `start-story` step lease;
   stop after its receipt.
2. Do the work.
3. Prove it — run the real verification through
   `.githooks/dw evidence capture <project> <phase> <story> -- <command>`
   (records command, exit code, index tree, and output into the story's
   evidence file; screenshots/binaries go under `assets/` next to it).
4. Require and apply a fresh `finish-story` step lease; stop after its receipt
   (it refuses without evidence).

## Commit — every commit passes the gate

1. Stage everything (`git add …`), THEN apply a fresh, exact
   `generate-contract` step lease and stop. It stamps machine-verified facts
   (branch, HEAD, index tree, staged sample, story IDs); restaging afterwards
   invalidates it (preview and apply a fresh `--force` lease). If explicit
   story/consent/tests-capture metadata is required, supply it deliberately
   through `dw contract new`; step never invents operator metadata.
2. Honestly verify each rule, then flip every `- [ ]` to `- [x]` in
   `.tmp/CONTRACT.md`. A `--tests-capture` reference pre-checks the
   "Tests ran." box and is re-verified by the gate.
3. Run `git commit` yourself—`dw step` never does this. Trailers
   (`PMO-Story`, `PMO-Contract-Digest`) and the
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

**Never use `--no-verify`.** When blocked, read the banner — it names
the failed rule id and the remediation, and includes the exact
contract template to regenerate. Fix what it names, re-run
`dw contract new --force`, re-certify, and commit again. If the rules
themselves seem wrong for the work, stop and raise it with the user
rather than bypassing.

## MCP tools

MCP-capable agents: prefer the MCP tools over shelling out —
`.githooks/dw-mcp` (wired via `.mcp.json`) serves the same core as
structured tools with identical refusals: orientation (`dw_status`, `dw_step`, `dw_context`,
`dw_next`, `dw_check`, `dw_doctor`), verification (`dw_verify`,
`dw_gate`), guarded mutations (`dw_step_apply`, `dw_story_status`,
`dw_evidence_capture`, `dw_contract_new`). Certification is never a
tool call: flipping contract boxes stays a manual, deliberate edit
(see `docs/mcp.md` in the framework repo).

## Canon

- `pm/roadmap/PMO-CONTRACT.md` — the rules and the contract template
  (rule ids, tiers, project extensions).
- `pm/roadmap/roadmap-builder.md` — the methodology: directory
  contract, file specs, lifecycle, naming.

## If the repo lacks the rails

The plugin teaches the operating loop; the rails themselves are
per-repository. If `pm/roadmap/` or `.githooks/dw` is missing, adopt
the repo — no clone of the framework needed:

```bash
brew install karolswdev/tap/delivery-workbench   # or pipx install the
                                                 # release wheel from GitHub
dw install /path/to/repo --skip-bootstrap        # rails + MCP server + .mcp.json
```

For running projects with history, use the three-command adoption
path instead (see `/dw-adopt`). Source and releases:
https://github.com/karolswdev/delivery-workbench.
