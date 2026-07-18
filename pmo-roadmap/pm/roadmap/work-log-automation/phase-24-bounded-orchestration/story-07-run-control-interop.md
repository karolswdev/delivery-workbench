# WLA-24-07 - Expose and monitor runs across every surface

- **Project:** work-log-automation
- **Phase:** 24
- **Status:** done
- **Depends on:** WLA-24-03, WLA-24-04, WLA-24-06
- **Unblocks:** WLA-24-08
- **Owner:** unassigned

## Problem

An orchestration framework is not usable if only its local Python core can
see or control a run. Humans and agents need the same exact score/run state,
grant preview, bounded acts, failures, outputs, and checkpoints through CLI,
MCP, HTTP, the rich Workbench Run view, and mission-control summaries.

## Scope

- **In:** CLI surface completion; MCP score/run reads and exact-token run
  acts; HTTP routes/envelopes; Workbench Run view joined to Design/Validate;
  graph node states, attempts, agents/sessions, check streams, artifact
  metadata/lineage, budgets/time, failures/routes, ledger timeline, approvals,
  pause/resume/cancel, terminal handoff; state-feed/event summary; adapter
  inventories/parity/purity/privacy and responsive visual coverage.
- **Out:** provider argv/credentials, generic shell/terminal, adapter-owned
  scheduling, remote portable grant, automatic checkpoint approval,
  certification/commit.

## Acceptance criteria

- [x] CLI JSON, MCP `structuredContent`, and HTTP `data` return byte-equivalent
  compiler, plan, projection, tick-result, and act documents; adapters accept
  only score/run ids and exact tokens, never score semantics or driver/check
  argv.
- [x] Workbench Run renders the graph as live state with agents, attempts,
  checks, artifacts/lineage, budgets, failures/routes, ledger receipts, and
  terminal meaning; inspection does not write or pollute rail/run events.
- [x] Grant/start, checkpoint, pause/resume, retry/elevation where permitted,
  and cancel are separate preview→confirm acts with changed-state refusal;
  unsupported/manual/certification/commit states have no apply control.
- [x] Output/check streams are bounded and explicitly opened; secrets,
  prompts, transcripts, source content, and undeclared artifacts never appear
  in list/feed/event documents.
- [x] MCP/HTTP inventories, parity, read purity, replay/injection/stale red
  paths,  desktop/mobile/a11y visual states, and installed package surfaces are
  pinned in tests and interop docs.

## Test plan

- **Unit:** route/tool schemas and exclusions; shared-core call ownership;
  serialization and privacy keys.
- **Integration:** one run lifecycle over each applying adapter, cross-adapter
  stale/replay refusal, UI control walk, read checksums/events unchanged.
- **Manual / device:** inspect and control a live parallel/failed/repaired run
  at desktop and mobile sizes; verify the graph explains why each node is
  waiting, running, failed, or eligible.

## Notes / open questions

The Run view is an explanation and consent surface, not merely a progress
dashboard. Every act gets its own current preview; no client-side poller may
turn a newly eligible node into implicit authorization.
