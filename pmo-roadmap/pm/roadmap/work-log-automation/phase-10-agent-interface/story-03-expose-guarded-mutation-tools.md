# WLA-10-03 - Expose guarded mutation tools

- **Project:** work-log-automation
- **Phase:** 10
- **Status:** done
- **Depends on:** WLA-10-02
- **Unblocks:** WLA-10-04
- **Owner:** unassigned

## Problem

Orientation alone leaves agents shelling out for the work loop's
verbs. The mutations the CLI already guards — transactional story
flips, evidence capture from real runs, contract generation with
stamped facts — belong on the surface with identical guardrails.
What must NOT arrive with them: any tool that certifies a contract
or creates a commit. The server hands the agent the same pen the
CLI does, never the gate's rubber stamp.

## Scope

- **In:** `dw_story_status` (adapting the same plan/apply path the
  CLI uses — refuses done-without-evidence exactly like `dw story
  status`), `dw_evidence_capture` (argv-array command, captured
  run recorded with exit code and output into the story's evidence
  file), `dw_contract_new` (stamped facts; the result text says
  plainly that certification is a human/agent act done by editing
  `.tmp/CONTRACT.md`, never via a tool). Tool-level errors carry
  the same refusal messages the CLI prints. Tests: parity cases in
  `dw-core-tests.py` (flip refused without evidence via MCP ==
  refused via CLI; capture appends the same block; contract facts
  match `dw contract new`) and `mcp-server.sh` extended to walk a
  fixture story through in-progress → capture → done over MCP,
  then prove the certification exclusion (no such tool listed; the
  contract file's boxes remain unchecked by anything the server
  did).
- **Out:** Any commit/certify/bundle tool (excluded by contract),
  phase/story scaffolding tools (CLI ceremony is fine for those in
  v1 — recorded as deferred), wiring (WLA-10-04).

## Acceptance criteria

- [ ] A fixture story travels backlog → in-progress → evidence
  capture → done entirely over MCP tool calls, and the resulting
  files are byte-identical to the CLI driving the same sequence.
- [ ] `dw_story_status` to done without evidence fails with the
  CLI's refusal semantics; the gate still blocks an uncertified
  commit afterward (the server granted no shortcut).
- [ ] `tools/list` contains no certify/commit tool, asserted by
  test against the design doc's exclusion list.
- [ ] `dw_evidence_capture` records command, exit code, and output
  exactly as `dw evidence capture` does (shared renderer).

## Test plan

- **Unit:** MCP-vs-CLI parity cases in `dw-core-tests.py`.
- **Integration:** extended `pmo-roadmap/tests/mcp-server.sh`
  (full story walk + exclusion proof + gate still blocking).
- **Manual / device:** live-client walk deferred to WLA-10-05.

## Notes / open questions

- Evidence capture output limits: reuse the CLI's truncation
  bounds; MCP results additionally cap text content length per the
  design doc.
