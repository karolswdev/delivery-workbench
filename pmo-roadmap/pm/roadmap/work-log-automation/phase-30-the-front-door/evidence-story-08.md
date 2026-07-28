# Evidence - WLA-30-08

- **Story:** WLA-30-08 - Review the generated program in Studio
- **Status:** done
- **Date:** 2026-07-27

## Proof

Program Studio now opens a setup proposal's generated bundle as one
linked object: `GET /api/setup/bundle?proposal_file=...` behind the
`#/program-studio/bundle` route (no new top-level navigation; the
primary nav keeps seven entries). The review model carries roadmap
scope, workflow shape, the two seats with their independence rules,
rubric criteria bound to their producing checks, requested capabilities
(including the newly defaulted `knowledge:lesson-writeback`), finite
budgets, stop conditions, and local non-secret driver availability.
Whole-bundle diagnostics come from the one `validate_program` core with
`bundle_documents` + `roadmap_document` injection — no second
validator — and every diagnostic carries source, JSON pointer,
remediation, and an `anchor_id`/`anchor_href` linking it to the section
it affects. One pure simulation renders alongside, parity-shared with
the scaffold's own simulation core. Tracked policy and `.git`-local
bindings are visually distinct under the exact "configuration, not
permission" label. The route accepts and emits no token of any kind;
the terminal handoff names `dw setup apply` then the exact
`dw program plan` grant preview — consent stays in the terminal.
The adoption review links generated policy through to this route, so
the two reviews form one journey. Implementation by Sol (GPT-5.6)
under orchestration in an isolated worktree; ported to main and
re-verified there.

Three captured runs, all authoritative: the **live demo** (the real
exam-rehearsal artifacts — the Scope-Chat proposal scaffolded against
the real roster — rendered as a valid bundle with the label, the
lesson capability, the simulation, no token, and the grant handoff; a
planted rubric-fact mismatch surfaces `mechanical-fact-unproduced`
with source, pointer, and anchors; the review session writes nothing),
the **unit battery** (6 tests: ready/invalid/missing-driver/
insufficient-budget/same-family models, simulation parity, anchors,
token rejection, purity, nav inventory), and the **full core suite**
via `tests/run-core-tests.py` (final capture, machine-verified exit
code).

### Captured run — 2026-07-28T01:34:33Z

- **Command:** `/usr/bin/python3 /private/tmp/claude-501/-Users-karol-dev-code-delivery-workbench/c4dc647a-d1b5-41ba-83af-e7d70e987de9/scratchpad/demo-studio-bundle.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 4cd7f840e5ca34fefee90f1642045f2ab671a68d

```text
initialized Git repository: /private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-studio-demo.qj_r9vmp/site
→ Installing pmo-roadmap into /private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-studio-demo.qj_r9vmp/site
  ✓ wrote pm/roadmap/roadmap-builder.md
  ✓ wrote pm/roadmap/PMO-CONTRACT.md
  ✓ wrote pm/orchestration/research-build-review.json
  ✓ wrote .githooks/pre-commit
  ✓ wrote .githooks/post-commit
  ✓ wrote .githooks/commit-msg
  ✓ wrote .githooks/dw
  ✓ wrote .githooks/dw_pmo/
  ✓ wrote .githooks/dw-workbench + .githooks/workbench/ (local explorer UI)
  ✓ wrote .githooks/work-log-summarize
  ✓ wrote .githooks/work-log-read
  ✓ wrote .githooks/dw-mcp (MCP stdio server; see docs/mcp.md)
  ✓ wrote .mcp.json (delivery-workbench MCP server entry)
  ✓ git config core.hooksPath = .githooks
  ✓ added .tmp/ to .gitignore
  ✓ added __pycache__/ to .gitignore
  ✓ wrote .claude/commands/dw-*.md
  ✓ agent docs block created in CLAUDE.md

✓ pmo-roadmap installed. Verify the wiring any time with: .githooks/dw doctor

Delivery Workbench rails are ready in /private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-studio-demo.qj_r9vmp/site.
Next, start the intake conversation that will create your roadmap project:
  1. Open this directory in Claude Code.
  2. Run /dw-scope and describe what you want to build.
No project or agent was started automatically.
bundle review valid: True
capabilities shown: 0
configuration label: present verbatim
lesson write-back visible in the reviewed request
simulation present: True | token fields: []
no token emitted by the review route
terminal handoff: {'after': 'dw setup apply', 'label': 'Preview the separate program grant in the 
planted fact mismatch anchored: setup-proposal:/tracked_content/policy/r /criteria/0/evaluation/fact | keys: ['anchor_href', 'anchor_id', 'code', 'message', 'pointer', 'remediation', 'source']
bundle review wrote nothing
demo: ok
```

### Captured run — 2026-07-28T01:34:35Z

- **Command:** `/usr/bin/python3 pmo-roadmap/tests/studio_bundle_tests.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 4cd7f840e5ca34fefee90f1642045f2ab671a68d

```text
......
----------------------------------------------------------------------
Ran 6 tests in 0.283s

OK
```

### Captured run — 2026-07-28T01:34:48Z

- **Command:** `/usr/bin/python3 pmo-roadmap/tests/run-core-tests.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 4cd7f840e5ca34fefee90f1642045f2ab671a68d

```text
run-core-tests: 679 units across 8 shards + 1 serial
  shard 0:  87 tests in   74.4s  ok
  shard 1:  91 tests in   75.3s  ok
  shard 2:  83 tests in   91.0s  ok
  shard 3:  87 tests in   85.3s  ok
  shard 4:  89 tests in   86.7s  ok
  shard 5:  85 tests in  107.9s  ok
  shard 6:  83 tests in   90.6s  ok
  shard 7:  85 tests in   90.1s  ok
  shard 8:   1 tests in    2.2s  ok
run-core-tests: 691 tests in 110.0s (OK)
```
