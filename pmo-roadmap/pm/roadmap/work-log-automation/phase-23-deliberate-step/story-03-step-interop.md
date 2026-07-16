# WLA-23-03 - One step across MCP and HTTP

- **Project:** work-log-automation
- **Phase:** 23
- **Status:** done
- **Depends on:** WLA-23-02
- **Unblocks:** WLA-23-04
- **Owner:** unassigned

## Problem

The handrail fails interoperability if terminal agents can use it but MCP and
browser clients must reconstruct its token, allowlist, or receipt rules.

## Scope

- **In:** MCP preview/apply tools and HTTP preview/apply routes over the same
  core documents; inventory/docs pins; parity, containment, and exclusions.
- **Out:** commit/certification; generic process execution; cross-repo or
  remote tokens.

## Acceptance criteria

- [x] CLI, MCP, and HTTP preview/result core documents are byte-equal.
- [x] Apply requires the exact token and preserves MCP/HTTP mutation guards.
- [x] Commit/certification and modified argv cannot cross either adapter.
- [x] Tool/route inventories and interop documentation fail on drift.

## Test plan

- **Unit:** adapter maps and exclusion census.
- **Integration:** protocol parity and stale-token red paths.
- **Manual / device:** one real client preview/apply exchange.

## Notes / open questions

- `dw_step` and `GET /api/step` call `step.build_step` directly; `dw_step_apply`
  and `POST /api/step/apply` call `step.apply_step` directly. The adapters own
  framing only.
- An expected apply refusal remains a versioned result document over MCP;
  HTTP carries the same result in a 409 envelope. Neither forces clients to
  parse prose or loses the `started: false` fact.
- Both apply schemas accept only `project` and the exact `expect` token.
  Certification, commit, caller-supplied argv, and loops have no input seam.
- `tests/step-interop.sh` drives a freshly installed repo through real CLI,
  MCP stdio, and HTTP exchanges, resetting identical fixture state between
  adapters so preview/result documents compare exactly. It also proves replay,
  injection, certification, and commit red paths without another child.
