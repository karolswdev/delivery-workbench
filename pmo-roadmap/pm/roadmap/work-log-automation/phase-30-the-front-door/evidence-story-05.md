# Evidence - WLA-30-05

- **Story:** WLA-30-05 - Review the adoption in the workbench
- **Status:** done
- **Date:** 2026-07-27

## Proof

The adoption review lives under the existing roadmap-changes workspace
(`?proposal=<file>#/edit/adoption_review`, or `?setuppreview=setup:<id>`
for a pending lease preview — no new top-level navigation; the primary
nav keeps its seven entries). A read-only `GET /api/setup/review`
returns the product-language model — project vision first, ordered
phases and stories with dependencies and acceptance criteria,
provenance on every item, unresolved questions always visible, the
complete changed-path list, and tracked policy plus `.git`-local driver
bindings visibly separated under the exact label "configuration, not
permission" — with exact JSON, fingerprints, and paths behind a
technical-details substructure. The model derives from the same
`setup_plan_facts` core as `dw setup preview` (HTTP/CLI parity tested).
Review marks (accepted-for-preview, rejected with structured per-item
objections) are entirely ephemeral browser state: no POST, no storage,
no repository note — closing the page loses them, and the terminal
handoff stays `dw setup preview <file>`. Accessibility rides the
existing bar: keyboard operation, focus preservation, 390px layout,
light/dark. Implementation by Sol (GPT-5.6) under orchestration in an
isolated worktree; ported to main and re-verified there.

Two orchestrator findings while landing, both fixed and pinned by
tests: the review's first cut reused the lease preview's
reviewed-state gate and refused every draft — but a draft is exactly
what a human reviews, so `build_setup_plan` gained a
`require_reviewed=False` read path used only by the review (the lease
gate is untouched); and the composed demo exposed a WLA-30-07 gap —
build-mode scaffolding could not run before the roadmap exists —
fixed as the separate rider commit "Scaffold scopes against the
conversation's draft before the roadmap exists".

Three captured runs, all authoritative: the **live demo** (a scratch
site booted by `dw init`; the scope-chat build fixture as base
proposal; `dw program scaffold --proposal` embeds policy; the review
API renders the draft with vision, one phase, two unresolved
questions, the separation label verbatim, four changed paths, and
technical details; an invalid proposal renders its refusal verbatim;
the review-only session writes nothing), the **unit battery** (6
review tests including the new draft-render case), and the **full
core suite** via `tests/run-core-tests.py` (final capture,
machine-verified exit code).

### Captured run — 2026-07-28T01:10:20Z

- **Command:** `/usr/bin/python3 /private/tmp/claude-501/-Users-karol-dev-code-delivery-workbench/c4dc647a-d1b5-41ba-83af-e7d70e987de9/scratchpad/demo-adoption-review.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** a0e2ca7ef8382882b6d9a553738c43e9d8a1c0f6

```text
initialized Git repository: /private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-review-demo.vlqujkt0/site
→ Installing pmo-roadmap into /private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-review-demo.vlqujkt0/site
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

Delivery Workbench rails are ready in /private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-review-demo.vlqujkt0/site.
Next, start the intake conversation that will create your roadmap project:
  1. Open this directory in Claude Code.
  2. Run /dw-scope and describe what you want to build.
No project or agent was started automatically.
scaffolded proposal: schema=delivery-workbench-setup-proposal@1 state=draft
review valid: True
vision: Help a household notice pantry food that should be used soon without requiring a
phases: 1 | unresolved questions: 2
configuration separated from authority: label present verbatim
changed paths in review: 4
technical details substructure: present
invalid proposal renders refusal verbatim: /starts_work: must be false
review-only session wrote nothing: tree unchanged, no authority paths
demo: ok
```

### Captured run — 2026-07-28T01:10:21Z

- **Command:** `/usr/bin/python3 pmo-roadmap/tests/setup_review_tests.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** a0e2ca7ef8382882b6d9a553738c43e9d8a1c0f6

```text
......
----------------------------------------------------------------------
Ran 6 tests in 0.366s

OK
```

### Captured run — 2026-07-28T01:10:30Z

- **Command:** `/usr/bin/python3 pmo-roadmap/tests/run-core-tests.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** a0e2ca7ef8382882b6d9a553738c43e9d8a1c0f6

```text
run-core-tests: 672 units across 8 shards + 1 serial
  shard 0:  88 tests in   79.9s  ok
  shard 1:  90 tests in   81.4s  ok
  shard 2:  83 tests in   97.9s  ok
  shard 3:  86 tests in   91.2s  ok
  shard 4:  88 tests in   91.6s  ok
  shard 5:  84 tests in  113.0s  ok
  shard 6:  82 tests in   97.6s  ok
  shard 7:  82 tests in   96.7s  ok
  shard 8:   1 tests in    2.2s  ok
run-core-tests: 684 tests in 115.2s (OK)
```
