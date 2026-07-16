# WLA-23-05 - Fresh-consumer deliberate-step exit exam

- **Project:** work-log-automation
- **Phase:** 23
- **Status:** done
- **Depends on:** WLA-23-04
- **Unblocks:** phase close and next release decision
- **Owner:** unassigned

## Problem

Component tests cannot prove that repeated explicit one-step authorization is
usable, stale-safe, and incapable of crossing the consent boundary in a
wheel-installed consumer.

## Scope

- **In:** packaged install/update fixture; successive preview/token/apply
  transitions; stale same-id and prohibited commit red paths; transport/UI
  parity; full regression and release-readiness closeout.
- **Out:** publishing/tagging without a separate owner request; multi-step
  automation.

## Acceptance criteria

- [x] A fresh consumer advances one real story by authorizing every step
  separately and never reconstructing the underlying action argv.
- [x] A relevant state change invalidates the token even when the action id
  stays constant; runner/event counts remain zero.
- [x] Certification and commit remain manual through every surface.
- [x] Full distribution, Python-floor, UI, agent, optional integration, docs,
  and history suites are green with a phase final summary.

## Test plan

- **Unit:** full core suite.
- **Integration:** dedicated package exit exam plus complete CI matrix.
- **Manual / device:** inspect fresh-consumer receipts and final commit chain.

## Notes / open questions

- `deliberate-step-loop.sh` consumes the CLI installed from the wheel built by
  `package-smoke.sh`; it updates and boots a disposable repository rather than
  importing the source checkout accidentally.
- Before all seven authorizations, the fixture proves exact CLI JSON = MCP
  `structuredContent` = HTTP envelope `data`. It applies only `project` plus
  the opaque token and never reads or reconstructs `next_action.command`.
- The seven leases cross every applying adapter: CLI review, MCP contract
  generation, HTTP story start, MCP story continuation, CLI guarded finish,
  HTTP review, and CLI final contract generation. Each receipt stops before
  the next preview.
- A real workspace edit preserves the `continue-story` action id while
  changing the token. The old lease refuses through CLI, MCP, and HTTP with
  `started: false`, no child, no claim, no state change, and zero new step
  events; the fresh lease remains usable.
- Bootstrap and story certification/commit are previewed and refused through
  all three step transports. The fixture operator performs both attestations
  and commits manually, then proves trailers, archived contract, and
  `dw verify --all`.
- The complete capture at `2026-07-16T15:24:47Z` passed 230 core tests on
  Python 3.14 and the declared Python 3.9 floor, both package-installed
  consumer loops, 20 Firefox viewport renders, 147 Telegram interface tests,
  10 Telegram fitness tests, 23 pinned HoldSpeak tests, all shipped-shell and
  docs checks, upgrade/range fixtures, and the pre-close 128-commit history.
- Homebrew alone abstained locally because the operator's formula is already
  installed; the smoke refuses to uninstall user state and remains wired on
  the clean macOS CI runner.
