# Evidence - WLA-27-01

- **Story:** WLA-27-01 - Contract the everyday product language
- **Status:** done
- **Date:** 2026-07-23

## Proof

The reviewed [product-language guide](../../../../../docs/product-language.md)
and its
[`delivery-workbench-application-language@1`](../../../../../docs/product-language-contract-v1.json)
contract fix ten ordinary concepts and trace them to nineteen canonical models
already named by `docs/interop.md`. The contract inventories eighteen current
human surfaces, gives every mixed surface an explicit **Technical details**
boundary, and reserves eighteen protocol terms from everyday regions while
keeping them exact in machine, architecture, command, code, and audit contexts.

The checker is part of the Python-floor CI job. It validates exact contract and
fixture shapes, unique concept names, source-model and source-path existence,
all three surface classes, complete inventory IDs, docs/README/CI wiring, and
ten positive/red fixtures. Each reserved term carries its own planted leak, so
a relaxed pattern makes the checker fail its self-test. The same checker passes
under the declared system Python 3.9.6 and the development Python.

The captured integration run below adds 46 selected schema, MCP, program
surface, and status tests plus direct MCP and CLI/MCP/HTTP orchestration parity.
Before capture, the complete public core suite also passed:
`python3 pmo-roadmap/tests/dw-core-tests.py` — 473 tests in 835.198 seconds,
`OK`. No runtime or machine-contract source file is changed by this story.

### Captured run — 2026-07-24T05:29:31Z

- **Command:** `bash -o pipefail -c set -e
/usr/bin/python3 pmo-roadmap/tests/product-language-contract.py
python3 pmo-roadmap/tests/product-language-contract.py
python3 pmo-roadmap/tests/dw-core-tests.py -q ProgramContractTest MCPServerTest ProgramSurfaceTest StatusBriefingTest
pmo-roadmap/tests/mcp-server.sh
pmo-roadmap/tests/orchestration-interop.sh
pmo-roadmap/tests/agent-surface.sh
pmo-roadmap/tests/docs-lint.sh
pmo-roadmap/tests/docs-snippet-smoke.sh
pmo-roadmap/tests/canon-lint.sh
.githooks/dw check work-log-automation
.githooks/dw rider docs --check
pmo-roadmap/update.sh . --check
git diff --check
git diff --cached --check`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 0644196162fcdcd21b006bb31c7e458188b29b30

```text
product-language-contract: ok (10 concepts, 18 surfaces, 18 reserved terms, 10 fixtures)
product-language-contract: ok (10 concepts, 18 surfaces, 18 reserved terms, 10 fixtures)
dw-workbench: 127.0.0.1 "GET /api/programs/program-077559373db6695a9c7bc997/events?from=0&follow=0 HTTP/1.1" 200 -
----------------------------------------------------------------------
Ran 46 tests in 27.448s

OK
protocol exchange: ok (9 replies)
no-rails refusal: ok
mutation walk: ok (done-without-evidence refused; contract stamped, certification manual)
gate still blocks uncertified commits: ok
MCP/CLI byte-parity (timestamps normalized): ok
mcp-server.sh: ok
orchestration interop: exact CLI/MCP/HTTP lifecycle reached awaiting-certification
orchestration-interop.sh: ok
dw-workbench: shutting down
dw-workbench: serving /private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-orchestration-interop.HRes8H/repo
dw-workbench: http://127.0.0.1:24418/ (localhost or your own .ts.net tailnet; Ctrl-C to stop)
dw-workbench: writes require a guarded preview→apply content boundary or an exact step/run/program token; never stages, certifies, or commits
agent-surface.sh: ok
docs-lint: ok (459 markdown files)
docs-lint.sh: ok (1s)
ok: CONTRIBUTING.md snippet 'contributor-setup' ran as printed
ok: CONTRIBUTING.md snippet 'contributor-gated-commit' ran as printed
ok: pmo-roadmap/README.md snippet 'install' ran as printed
ok: pmo-roadmap/README.md snippet 'update' ran as printed
ok: pmo-roadmap/README.md snippet 'new-project' ran as printed
ok: pmo-roadmap/README.md snippet 'adopt-three-step' ran as printed
ok: pmo-roadmap/README.md snippet 'intake-no-prompt' ran as printed
ok: pmo-roadmap/README.md snippet 'adopt-close-loop' ran as printed
docs-lint snippets: ok
docs-snippet-smoke.sh: ok
canon-lint.sh: ok
dw check: ok
dw rider docs: all rendered surfaces match canon
update.sh: up to date (vendored rails match source v1.14.0)
```

## Manual review

The seven Phase 26 handoff questions trace without a renderer inventing a
fact:

| Operator question | Everyday concepts | Canonical sources |
|---|---|---|
| What are we delivering? | delivery plan, work | program policy/plan, roadmap context, Studio document |
| Who is doing and reviewing it? | team, review | compiled organization, team assignment, verdict and quality models |
| What passed? | review, progress | mechanical facts, verdicts, quality gate, program view |
| What is blocked? | blocker | status next action, program frontier, requests and obligations |
| Who needs to decide? | decision, team | program/run outstanding requests and governed decision |
| What may this still spend or change? | permission, cost | exact run/program grants, budgets, previews, current view |
| What happens next? | progress, blocker, decision, next step | canonical status action or program frontier/current action |

Reviewed the permission, cost, destructive-action, refusal, provenance, and
unknown examples against their source fields. Each ordinary explanation keeps
material scope, limits, exclusions, consequence, or uncertainty adjacent, and
the exact record remains reachable through **Technical details**. The contract
explicitly forbids application renderers from recomputing any of those facts.
