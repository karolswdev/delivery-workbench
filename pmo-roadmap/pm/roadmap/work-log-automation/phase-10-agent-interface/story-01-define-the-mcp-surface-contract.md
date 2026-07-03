# WLA-10-01 - Define the MCP surface contract

- **Project:** work-log-automation
- **Phase:** 10
- **Status:** backlog
- **Depends on:** none
- **Unblocks:** WLA-10-02
- **Owner:** unassigned

## Problem

Agents currently drive the rails by shelling out to `.githooks/dw`
and parsing text, JSON blobs, and exit codes — workable (the exit
contracts were built for it) but lossy: schemas live in prose,
errors arrive as prefixed strings, and every agent reimplements the
parsing. MCP is the native tool surface for agents. Before writing
a server, the contract must fix which operations become tools,
their exact schemas, and — most importantly — which operations are
deliberately withheld, or the server will quietly become a second
gate.

## Scope

- **In:** A design document `docs/mcp.md` that decides: (a) the
  tool inventory with JSON Schemas — orientation (`dw_context`,
  `dw_next`, `dw_check`, `dw_doctor`), verification (`dw_verify`,
  `dw_gate`), and guarded mutations (`dw_story_status`,
  `dw_evidence_capture`, `dw_contract_new`), each a thin adapter
  over the same `dw_pmo` function the CLI calls; (b) the exclusion
  list with rationale — above all, NO certification tool: flipping
  contract checkboxes is a deliberate act of attestation and must
  never be mechanized behind a tool call, and `git commit` itself
  stays outside the surface; (c) the protocol subset — stdio
  JSON-RPC 2.0, `initialize`/`initialized`, `tools/list`,
  `tools/call`, `ping`, protocol version pinned, everything else
  method-not-found — implemented stdlib-only (no SDK dependency,
  consistent with the runtime posture CI's python-floor job
  proves); (d) error and result shape (`isError` + text content
  carrying the same greppable lines the CLI prints, plus
  `structuredContent` for machine consumption); (e) how the server
  binds to a repository (launched with cwd inside an adopted repo,
  same root discovery as the CLI; refuses repos without rails).
- **Out:** Implementation (WLA-10-02/03), wiring and distribution
  (WLA-10-04), HTTP/SSE transports, resources/prompts MCP
  capabilities (tools only in v1).

## Acceptance criteria

- [ ] `docs/mcp.md` exists with the full tool inventory, input
  schemas, result shapes, and the exclusion list with rationale
  (no-certify, no-commit stated explicitly).
- [ ] The protocol subset and stdlib-only decision are specified,
  including the pinned protocol version and the behavior for
  unsupported methods.
- [ ] Every listed tool names the `dw_pmo` core function it adapts
  (no rule logic in the server — Phase 6 invariant restated as a
  proof obligation).
- [ ] Decisions mirrored in the phase status; docs-lint passes.

## Test plan

- **Unit:** n/a (design story).
- **Integration:** `pmo-roadmap/tests/docs-lint.sh`.
- **Manual / device:** cross-check the tool inventory against the
  CLI command surface for gaps and for accidental over-exposure.

## Notes / open questions

- Tool naming: `dw_*` prefix keeps the tools greppable and avoids
  colliding with other servers' generic names.
- `dw_evidence_capture` runs a caller-supplied command — the same
  power the CLI already grants; the doc should say why that is
  in-scope (evidence must come from real runs) and note that MCP
  clients gate tool calls with their own permission prompts.
