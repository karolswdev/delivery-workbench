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

To deliberately apply a command recommendation, never reconstruct its argv:

1. Preview a fresh lease with `.githooks/dw step [project] --json` (or MCP
   `dw_step`). Reading status alone is not consent to act.
2. Require `applicable: true`, review the exact action, token, and
   `apply_command`, and stop for the user when the preview is manual or
   prohibited. Project choice, contract certification, and commit always stay
   manual; `dw step` cannot perform them.
3. Only after explicit authorization, invoke that preview's exact
   `apply_command` (or `dw_step_apply` with its exact `expect` token). Never
   modify its argv. One apply starts at most one child and stops; read a fresh
   status/step before considering anything else. Never build an automatic
   step loop.

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

1. After authorization, use the fresh deliberate-step flow above and require
   its action to be `start-story`; apply its exact lease and stop.
2. Do the work.
3. Prove it — run the real verification through
   `.githooks/dw evidence capture <project> <phase> <story> -- <command>`
   (records command, exit code, index tree, and output into the story's
   evidence file; screenshots/binaries go under `assets/` next to it).
4. Preview a fresh step, require its action to be the guarded `finish-story`,
   apply that exact lease, and stop (it refuses without evidence).

Commit — every commit passes the gate:

1. Stage everything (`git add …`), THEN preview a fresh deliberate step. If it
   is the allowlisted `generate-contract` action, apply its exact lease and
   stop. The generated contract stamps machine-verified facts (branch, HEAD,
   index tree, staged sample, story IDs); restaging afterwards invalidates it
   (preview and apply a fresh `--force` lease). If explicit
   story/consent/tests-capture metadata is required, supply it deliberately
   through `dw contract new`; step never invents operator metadata.
2. Honestly verify each rule, then flip every `- [ ]` to `- [x]` in
   `.tmp/CONTRACT.md`. A `--tests-capture` reference pre-checks the
   "Tests ran." box and is re-verified by the gate.
3. Run `git commit` yourself — `dw step` never does this. Trailers
   (`PMO-Story`, `PMO-Contract-Digest`) and the
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
`.githooks/dw-mcp` (stdio JSON-RPC; wire it per your client — Claude Code reads `.mcp.json`, Codex uses `codex mcp add`) serves the same core as
structured tools with identical refusals: orientation (`dw_status`, `dw_context`,
`dw_step`, `dw_next`, `dw_check`, `dw_doctor`), browse (`dw_board`, `dw_holds`,
`dw_story_show`, `dw_signals`, `dw_notifications`), verification (`dw_verify`, `dw_gate`), guarded
mutations (`dw_step_apply`, `dw_story_status`, `dw_evidence_capture`,
`dw_contract_new`). Certification is never a tool call: flipping
contract boxes stays a manual, deliberate edit (see `docs/mcp.md`
in the framework repo).

Never use `--no-verify`; when blocked, read the banner — it names the
rule and the remediation, and includes the exact contract template.

Canon: `pm/roadmap/PMO-CONTRACT.md` (rules),
`pm/roadmap/roadmap-builder.md` (methodology).

Agents without MCP support: the CLI commands above are the complete surface — nothing below requires MCP.

<!-- END DELIVERY WORKBENCH -->
