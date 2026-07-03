# Evidence - WLA-10-03

- **Story:** WLA-10-03 - Expose guarded mutation tools
- **Status:** done
- **Date:** 2026-07-03

## Proof

Deliverables: the three guarded mutation tools registered in
`mcpserver.py`, each adapting the exact CLI path —
`dw_story_status` (plan_story_status + apply_plan, same
transactional header+table write, same done-without-evidence
refusal), `dw_evidence_capture` (run_capture with the shared
renderer and truncation bounds; result includes the ready-made
`tests_capture_ref`), and `dw_contract_new` (write_contract with
stamped facts; the result text states certification happens only by
manually editing `.tmp/CONTRACT.md`).

The captured run proves, in order:

- the full smoke including the mutation walk — a fixture story went
  backlog → in-progress → capture → done over MCP only; the
  done-without-evidence attempt on the second story was refused
  with the CLI's message;
- the certification exclusion held mechanically: after everything
  the server did, the stamped contract's boxes were all unchecked
  and a real `git commit` was still blocked by the gate — the
  server granted no shortcut;
- MCP/CLI byte-parity: a CLI-driven twin repo ran the same
  sequence; story, table, and evidence files are identical after
  normalizing timestamps/index-tree stamps;
- 10 in-process unit cases (refusal-message equality with the core,
  file-write parity, required-param enforcement) and the full
  128-test suite green.


### Captured run — 2026-07-03T19:59:44Z

- **Command:** `bash -c set -e -o pipefail; bash pmo-roadmap/tests/mcp-server.sh; python3 pmo-roadmap/tests/dw-core-tests.py MCPServerTest 2>&1 | tail -3; python3 pmo-roadmap/tests/dw-core-tests.py 2>&1 | tail -1`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** b1c5aaa6e7845d8143d9f3cf24c039d491e7e1fd

```text
protocol exchange: ok (8 replies)
no-rails refusal: ok
mutation walk: ok (done-without-evidence refused; contract stamped, certification manual)
gate still blocks uncertified commits: ok
MCP/CLI byte-parity (timestamps normalized): ok
mcp-server.sh: ok
Ran 10 tests in 0.020s

OK
OK
```
