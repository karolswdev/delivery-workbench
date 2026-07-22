# WLA-26-11 — Operate the autonomous organization across every surface

- **Project:** work-log-automation
- **Phase:** 26
- **Status:** backlog
  <!-- status vocabulary: roadmap-builder.md §2.3 -->
- **Depends on:** WLA-26-06, WLA-26-08, WLA-26-09, WLA-26-10
- **Unblocks:** WLA-26-12
- **Owner:** unassigned

## Problem

An autonomous organization that can only be understood from ledger files is not
operable. Humans and external agents need one consistent control room showing
why this roadmap work, workflow, team, round and verdict are current; which
agents are active or waiting; what quality/dissent remains; what authority and
budget can still be consumed; and exactly why the program stopped. Observation
must not become a second consent or scheduler path.

## Scope

- **In:** canonical program inventory/detail/view models; CLI
  `program list|show|validate|simulate|plan|start|preview|tick|supervise|request|
  pause|resume|revoke|cancel|tail`; MCP/HTTP exact adapters; Workbench control
  room; live SSE ledger tail; nested graph/org chart; candidate/team/role/
  activity, artifacts, verdicts/dissent, councils/rounds, gates, child runs,
  integrations, phase progress, budgets and timeline; typed notifications and
  request ports; bounded stream opens.
- **Out:** arbitrary prompt/argv/provider configuration over remote adapters;
  generic terminal; mutation through SSE; auto-starting daemon; hidden browser
  polling as authority; hosted runner.

## Acceptance criteria

- [ ] CLI JSON, MCP `structuredContent`, HTTP `data`, Workbench bootstrap and
  SSE replay expose byte-equivalent program state at one observation instant;
  reads and stream carry no token or mutation authority.
- [ ] The control room answers: why this story/phase, why this workflow/team,
  who implements/verifies/meta-verifies/architects, which loop/round is active,
  which evidence/verdict/dissent gates progress, and what next action/refusal is
  derivable from the ledger.
- [ ] Applying routes accept only program/run ids, bounded reasons or closed
  typed decisions and fresh exact tokens; no adapter accepts policy documents,
  role assignments, prompts, rubrics, checks, capabilities, credentials,
  commands or retry overrides at act time.
- [ ] Bounded `supervise` repeats the core tick only under an existing grant and
  explicit local invocation, stops on checkpoint/no-progress/terminal/budget/
  duration, and exposes every tick rather than creating a hidden scheduler.
- [ ] Notifications cover required intervention, verifier/council disagreement,
  architect veto, budget/exhaustion, integration refusal and program completion;
  phone responses remain typed request documents and transport never equals
  authority.
- [ ] Desktop/mobile states cover planning, team assignment, nested execution,
  active debate, verifier repair, meta-overturn, phase transition, revocation,
  budget stop and complete, with accessible labels and content-safe streams.

## Test plan

- **Unit:** surface model, route/parameter allowlist, token/refusal and read-only
  stream tests.
- **Integration:** CLI/MCP/HTTP parity, SSE cursor replay, Workbench explorer/UI
  smoke, multi-process control races, notification/request tests.
- **Manual / device:** inspect the full control room at desktop/mobile; phone is
  optional because continuous programs must not require it.

## Notes / open questions

Remote clients may operate the local runner through exact adapters; hosting the
authority itself remains a different trust decision.
