# WLA-23-03 - One step across MCP and HTTP

- **Project:** work-log-automation
- **Phase:** 23
- **Status:** backlog
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

- [ ] CLI, MCP, and HTTP preview/result core documents are byte-equal.
- [ ] Apply requires the exact token and preserves MCP/HTTP mutation guards.
- [ ] Commit/certification and modified argv cannot cross either adapter.
- [ ] Tool/route inventories and interop documentation fail on drift.

## Test plan

- **Unit:** adapter maps and exclusion census.
- **Integration:** protocol parity and stale-token red paths.
- **Manual / device:** one real client preview/apply exchange.

## Notes / open questions

Record unresolved decisions here before implementation starts.
