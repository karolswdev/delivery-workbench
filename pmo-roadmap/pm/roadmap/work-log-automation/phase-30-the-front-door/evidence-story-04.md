# Evidence - WLA-30-04

- **Story:** WLA-30-04 - Make setup one deliberate act
- **Status:** done
- **Date:** 2026-07-27

## Proof

Setup is now one deliberate act, delivered as `dw_pmo/setup_lease.py`
behind `dw setup preview <proposal-file>` and `dw setup apply
--proposal <id> --expect <token>` (the existing read-only `dw setup
[project]` delivery-choices view is untouched; `preview`/`apply` are
reserved subverbs). Preview validates the proposal through the
WLA-30-01 contract, computes the complete change set — tracked roadmap
and policy paths plus the `.git`-local driver roster — with explicit
before/after hashes, and mints one single-use `setup-sha256:` lease
bound to repository identity, branch, HEAD, index, the observed
roadmap and policy trees, the roster hash, the proposal's canonical
hash, and every before-hash. Apply re-observes all bound facts, refuses
any drift without writing, and lands the entire set as a journaled
transaction (temp-write + fsync + rename, byte backups, reverse-order
rollback proven by a planted failure). Success advances the journey
reviewed → configured only through the contract's transition function.
Setup and program tokens are typed separately and non-substitutable in
both directions. The old unleased multi-file side door — public
`dw adopt --apply` — is retired into this flow; single-file
`phase create`/`story create` conveniences keep riding the shared
plan/apply primitives. MCP (`dw_setup_preview`/`dw_setup_apply`) and
localhost HTTP expose the same canonical core, byte-parity tested.
Implementation by Sol (GPT-5.6) under orchestration in an isolated
worktree; ported to main and re-verified there.

Three captured runs, all authoritative: the **live demo** (a scratch
repository booted by `dw init`; preview shows the 4-path change set and
lease; drift in the bound roadmap tree refuses the stale token without
writing; a fresh lease applies roadmap plus local driver bindings
atomically; replay refuses; no grant, run, or commit exists after), the
**unit battery** (13 tests: happy path, the drift matrix, planted
rollback, transport parity, token non-substitutability, journey
advancement), and the **full core suite** via `tests/run-core-tests.py`
(final capture, machine-verified exit code).

One demo note recorded honestly: the first demo attempt planted drift
in CLAUDE.md and the stale token still applied — correctly, because
CLAUDE.md is outside the lease's bound observation set. The lease binds
exactly what its contract names; the recorded demo drifts the roadmap
tree and is refused.

### Captured run — 2026-07-28T00:20:27Z

- **Command:** `bash /private/tmp/claude-501/-Users-karol-dev-code-delivery-workbench/c4dc647a-d1b5-41ba-83af-e7d70e987de9/scratchpad/demo-setup-lease.sh`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** ae98701391fbaa491c893627f775f97fa71bbef9

```text
initialized Git repository: /private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-setup-lease-demo.VTAwZQ/site
→ Installing pmo-roadmap into /private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-setup-lease-demo.VTAwZQ/site
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

Delivery Workbench rails are ready in /private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-setup-lease-demo.VTAwZQ/site.
Next, start the intake conversation that will create your roadmap project:
  1. Open this directory in Claude Code.
  2. Run /dw-adopt and describe what you want to build.
No project or agent was started automatically.
wrote proposal.json (state=reviewed)

== preview: canonical change set + exact single-use lease ==
planned writes: 4
   .git/pmo-orchestration/drivers.json
   pm/roadmap/url-sentinel/README.md
   pm/roadmap/url-sentinel/phase-1-first-usable-check/current-phase-status.md
   pm/roadmap/url-sentinel/phase-1-first-usable-check/story-01-check-a-url-list.md
inertness: False False False False
lease type: setup-sha256:<hash>

== drift: change the bound roadmap tree, stale token refuses without writing ==
dw: stale setup lease: repository, branch, HEAD, index, roadmap, policy, or roster changed
confirmed: nothing was written

== fresh lease, atomic apply ==
{"certifies":false,"changed":[".git/pmo-orchestration/drivers.json","pm/roadmap/url-sentinel/README.md","pm/roadmap/url-sentinel/phase-1-first-usable-check/current-phase-status.md","pm/roadmap/url-sentinel/phase-1-first-usable-check/story-01-check-a-url-list.md"],"commits":false,"creates_grant":false,"expect":"setup-sha256:2cdfbd77a82021d726f0df680ebb4b4fa3c91280c85029d32233b8c27afbb845","journey_state":"configured","kind":"delivery-workbench-setup-apply","outcome":"applied","proposal_id":"setup:37be40f53858c40c99cdb4bfeae7cc76299a0cf60031704328eabd9ef42ac6ec","schema_version":1,"starts_work":false}
current-phase-status.md
story-01-check-a-url-list.md
local driver bindings landed under .git

== replay refuses ==
dw: setup lease was already used

== apply minted no authority ==
no grant, no run, no commit

demo: ok
```

### Captured run — 2026-07-28T00:20:30Z

- **Command:** `/usr/bin/python3 pmo-roadmap/tests/setup_lease_tests.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** ae98701391fbaa491c893627f775f97fa71bbef9

```text
.............
----------------------------------------------------------------------
Ran 13 tests in 3.389s

OK
```

### Captured run — 2026-07-28T00:20:58Z

- **Command:** `/usr/bin/python3 pmo-roadmap/tests/run-core-tests.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** ae98701391fbaa491c893627f775f97fa71bbef9

```text
run-core-tests: 642 units across 8 shards + 1 serial
  shard 0:  77 tests in  111.7s  ok
  shard 1:  88 tests in  104.2s  ok
  shard 2:  83 tests in  120.8s  ok
  shard 3:  83 tests in  113.3s  ok
  shard 4:  85 tests in  123.9s  ok
  shard 5:  78 tests in  119.6s  ok
  shard 6:  78 tests in  123.9s  ok
  shard 7:  78 tests in  127.8s  ok
  shard 8:   1 tests in    2.7s  ok
run-core-tests: 651 tests in 130.4s (OK)
```
