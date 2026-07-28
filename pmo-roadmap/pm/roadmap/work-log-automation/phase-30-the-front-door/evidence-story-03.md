# Evidence - WLA-30-03

- **Story:** WLA-30-03 - Hold the scope conversation
- **Status:** done
- **Date:** 2026-07-27

## Proof

The Scope-Chat front door ships as the `/dw-scope` rider command
(canonical source `pmo-roadmap/agent/dw-scope.md`, distributed to
`.claude/commands/` and `plugin/commands/` through the riderdocs
inventory, which grew from four commands to five with published counts
updated). Two explicit modes — **build** (rails-ready repository plus
an idea) and **maintain** (inspect the existing codebase and roadmap
through read surfaces first) — drive the minimum interview: identity,
outcome, users, first usable milestone, constraints, non-goals,
verification expectations, autonomy appetite. The skill's only
permitted write is `.tmp/setup-proposal.json` (gitignored); every
generated item carries honest provenance (user-answer /
repository-fact / recommendation), material ambiguity becomes an
unresolved question, revisions keep unchanged sections byte-stable,
and the conversation ends with the exact handoff — the workbench
roadmap-changes review location, `dw setup preview
.tmp/setup-proposal.json`, and the sentence "nothing has been saved".
A skill-document fitness test greps the shipped prose: both modes
named, no mutation command instructed, the closing handoff exact.
Two complete fixture conversations (a greenfield build, a
repository-grounded maintain) validate against the WLA-30-01 contract.
One integration nit fixed on landing: `dw init`'s closing message now
hands off to `/dw-scope` instead of the generic adoption command — the
boot command and the conversation now form one continuous journey.
Implementation by Sol (GPT-5.6) under orchestration in an isolated
worktree; ported to main and re-verified there.

Three captured runs, all authoritative: the **live demo** (both
fixtures validate with all three provenance kinds and unresolved
questions; the skill document holds the read-only line; the build
fixture feeds `dw setup preview` in an init-booted scratch repo and
mints a real setup lease — conversation output is working input), the
**unit battery** (8 tests), and the **full core suite** via
`tests/run-core-tests.py` (final capture, machine-verified exit code).

### Captured run — 2026-07-28T00:40:18Z

- **Command:** `bash /private/tmp/claude-501/-Users-karol-dev-code-delivery-workbench/c4dc647a-d1b5-41ba-83af-e7d70e987de9/scratchpad/demo-scope-chat.sh`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** c892a98df4a8855abe98722ca0cda0bdc695a0d2

```text
== 1. fixture proposals validate against the contract ==
scope-chat-build-proposal: valid, state=draft, provenance kinds=['recommendation', 'repository-fact', 'user-answer'], unresolved=1
scope-chat-maintain-proposal: valid, state=draft, provenance kinds=['recommendation', 'repository-fact', 'user-answer'], unresolved=1

== 2. the skill document holds the line ==
closing handoff names: dw setup preview .tmp/setup-proposal.json
closing handoff states: nothing has been saved

== 3. the conversation's artifact feeds dw setup preview ==
initialized Git repository: /private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-scope-demo.WKaKEh/site
→ Installing pmo-roadmap into /private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-scope-demo.WKaKEh/site
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

Delivery Workbench rails are ready in /private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-scope-demo.WKaKEh/site.
Next, start the intake conversation that will create your roadmap project:
  1. Open this directory in Claude Code.
  2. Run /dw-scope and describe what you want to build.
No project or agent was started automatically.
wrote .tmp/setup-proposal.json at journey state: reviewed
preview kind: delivery-workbench-setup-preview
planned writes: 5
lease minted: setup-sha256:<hash>
starts_work: False

demo: ok
```

### Captured run — 2026-07-28T00:40:20Z

- **Command:** `/usr/bin/python3 pmo-roadmap/tests/scope_chat_tests.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** c892a98df4a8855abe98722ca0cda0bdc695a0d2

```text
........
----------------------------------------------------------------------
Ran 8 tests in 0.003s

OK
```

### Captured run — 2026-07-28T00:40:31Z

- **Command:** `/usr/bin/python3 pmo-roadmap/tests/run-core-tests.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** c892a98df4a8855abe98722ca0cda0bdc695a0d2

```text
run-core-tests: 655 units across 8 shards + 1 serial
  shard 0:  84 tests in  106.5s  ok
  shard 1:  85 tests in  103.3s  ok
  shard 2:  82 tests in  133.8s  ok
  shard 3:  84 tests in  122.9s  ok
  shard 4:  86 tests in  124.4s  ok
  shard 5:  80 tests in  140.6s  ok
  shard 6:  83 tests in  132.6s  ok
  shard 7:  82 tests in  132.7s  ok
  shard 8:   1 tests in    2.4s  ok
run-core-tests: 667 tests in 143.0s (OK)
```
