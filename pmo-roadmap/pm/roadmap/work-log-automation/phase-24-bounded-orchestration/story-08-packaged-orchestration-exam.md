# WLA-24-08 - Prove a packaged multi-agent orchestration

- **Project:** work-log-automation
- **Phase:** 24
- **Status:** backlog
- **Depends on:** WLA-24-01 through WLA-24-07
- **Unblocks:** phase close and release decision
- **Owner:** unassigned

## Problem

Component tests cannot prove that a visually authored score, compiled package,
grant, parallel agents, artifact fan-in, checks/repair, restart, interop, and
human terminal boundary work as one trustworthy orchestration framework in a
consumer repository.

## Scope

- **In:** one Python-3.9-built wheel; fresh consumer; visual/reference score
  round trip; two parallel research fixtures, synthesis, isolated
  implementation, planted failing check routed once to repair, passing recheck,
  approval terminal; score/token/capability/path/cycle red fixtures; duplicate-
  dispatch crash/restart; expiry/budget/cancel; CLI/MCP/HTTP/Workbench parity;
  one provisioned live agent-harness specimen; evidence/gate/history handoff;
  complete distribution/Python/UI/agent/optional/docs/history matrix and final
  summary.
- **Out:** publication/tag/formula change without separate owner authority;
  automatic certification/commit/push/release/deploy; non-reproducible live
  agent output as the CI oracle.

## Acceptance criteria

- [ ] A fresh installed Workbench authors/loads the complete score and proves
  visual graph↔canonical JSON/hash parity; malformed cycle, dangling output,
  shell check, path escape, unbounded retry, and unsupported capability refuse.
- [ ] One exact grant runs two research agents concurrently, validates their
  differently typed/citation-bound outputs, synthesizes them, and gives a
  write agent an isolated worktree and exact implementation brief.
- [ ] A planted check failure follows only the configured repair route once,
  then passes; restart during a claimed node produces zero duplicate starts;
  expiry, budget exhaustion, stale rail action, and cancel stop truthfully.
- [ ] Every preview/projection/receipt is equal over CLI/MCP/HTTP; Workbench
  desktop/mobile views expose all rules and state without a generic shell or
  hidden loop; one provisioned live supported agent validates the real driver
  seam separately from deterministic fixture proof.
- [ ] The run stops at `awaiting-certification`. Only the fixture operator
  reviews evidence, certifies the contract, and commits; trailers/archive/
  `dw verify --all`, full matrix, Phase-24 final summary, and clean next-run
  handoff are green.

## Test plan

- **Unit:** full core on local and Python 3.9.
- **Integration:** dedicated packaged orchestration exam plus the complete CI
  matrix, upgrade, interop, browser, driver, optional-host and history suites.
- **Manual / device:** visually inspect editor/run graph and receipts; execute
  the provisioned live-agent specimen and final certification/commit by hand.

## Notes / open questions

The deterministic fixture driver is the CI oracle because it can prove exact
scheduling, failure, recovery, and receipt behavior. A real supported agent
run proves the integration seam and usability, but variable model output must
not be translated into a flaky or unverifiable release gate.
