<!-- BEGIN DELIVERY WORKBENCH (managed by pmo-roadmap install.sh/update.sh — edits inside are overwritten) -->

## Delivery Workbench (PMO rails)

This repository uses Delivery Workbench: an evidence-first commit gate
over a Markdown roadmap under `pm/roadmap/<project>/` (phases, stories,
paired evidence files). Markdown is the source of truth; `.githooks/dw`
is the CLI for everything below. Run `.githooks/dw doctor` if anything
seems miswired. `.githooks/dw-workbench --root .` serves a localhost
web view of the roadmap (browse, health, trace, guarded edit).

Start every work session with one briefing read (do not call both
transports):

- `.githooks/dw status [project] --json` — the versioned readiness,
  workspace, roadmap, and next-safe-action object. Exit 0 means `ready`;
  exit 1 means `attention`. Attention is valid JSON: follow its blocking
  repair action before work. Status reads only; it never executes the action.
- MCP-capable agents may call `dw_status` instead. It returns the identical
  object in `structuredContent`; an `attention` verdict is not a tool error.

Use specialist surfaces for depth after the briefing:

- `.githooks/dw context [project] --compact` — JSON snapshot: issues,
  warnings, next story, per-story trace paths.
- `.githooks/dw next [project]` — the next actionable story
  (exit 0 = found, 2 = nothing actionable, 1 = error; `--json` for a
  machine-readable object).
- `.githooks/dw check [project]` — structural and evidence-content
  lint; greppable `ERROR <path>: <issue>` lines, exit 1 on issues.
- `.githooks/dw doctor` — detailed clone-wiring diagnosis when status names
  unhealthy rails.

Work a story (statuses: backlog | ready | in-progress | blocked |
on-hold | done; done-synonyms complete/closed/shipped gate identically,
paused = on-hold; parking a story on-hold requires `--reason "why"`,
recorded in the status cell):

1. `.githooks/dw story status <project> <phase> <story> in-progress`
2. Do the work.
3. Prove it — run the real verification through
   `.githooks/dw evidence capture <project> <phase> <story> -- <command>`
   (records command, exit code, index tree, and output into the story's
   evidence file; screenshots/binaries go under `assets/` next to it).
4. `.githooks/dw story status <project> <phase> <story> done`
   (refuses without evidence).

Commit — every commit passes the gate:

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

Gate rules the machinery enforces: one story flips done per commit
(bundle only with `.tmp/BUNDLE-OK.md` + one-line rationale), the
flipped story's `evidence-story-NN.md` ships in the same commit, and
evidence never appears or disappears orphaned. Preflight any time with
`.githooks/dw gate [--porcelain]` — it never consumes the contract.
`.githooks/dw verify [<base>..<head> | --all]` re-derives the
structural rules from pushed history alone — audit any range,
no local contract needed.

MCP-capable agents: prefer the MCP tools over shelling out —
`.githooks/dw-mcp` (wired via `.mcp.json`) serves the same core as
structured tools with identical refusals: orientation (`dw_status`, `dw_context`,
`dw_next`, `dw_check`, `dw_doctor`), browse (`dw_board`, `dw_holds`,
`dw_story_show`), verification (`dw_verify`, `dw_gate`), guarded
mutations (`dw_story_status`, `dw_evidence_capture`,
`dw_contract_new`). Certification is never a tool call: flipping
contract boxes stays a manual, deliberate edit (see `docs/mcp.md`
in the framework repo).

Never use `--no-verify`; when blocked, read the banner — it names the
rule and the remediation, and includes the exact contract template.

Slash commands (Claude Code, under `.claude/commands/`): `/dw-next`,
`/dw-story-done`, `/dw-contract`, `/dw-adopt`.

Canon: `pm/roadmap/PMO-CONTRACT.md` (rules),
`pm/roadmap/roadmap-builder.md` (methodology).

<!-- END DELIVERY WORKBENCH -->
