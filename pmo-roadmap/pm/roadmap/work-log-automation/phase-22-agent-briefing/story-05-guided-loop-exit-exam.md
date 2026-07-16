# WLA-22-05 - Prove the guided loop in a fresh consumer

- **Project:** work-log-automation
- **Phase:** 22
- **Status:** done
- **Depends on:** WLA-22-04
- **Unblocks:** phase close and next release
- **Owner:** unassigned

## Problem

Component tests cannot prove that the recommendation sequence is usable
from an operator's actual starting point. The phase closes only when a
fresh consumer follows the briefing from unknown state through delivery
and every transition matches what the underlying rails will accept.

## Scope

- **In:** packaged install/update fixture; clean → in-progress → dirty →
  evidenced → staged → contract/manual certification → gate-pass → commit
  status sequence; red paths for missing evidence and stale contracts;
  full regression battery; overview/README/changelog/release-readiness
  updates and phase summary.
- **Out:** publishing or tagging a release without an explicit owner
  request; network service; weakening manual certification to make the
  demo easier.

## Acceptance criteria

- [x] A temporary repo installed from the built artifact completes one
  story and gated commit by following each successive status action;
  every recommendation is asserted before execution.
- [x] Missing evidence and restaging after contract generation produce
  attention/manual repair and never recommend commit.
- [x] CLI/MCP/HTTP payloads agree at representative transitions and all
  reads leave tracked state and rail-event count unchanged.
- [x] Python 3.9, shell/integration, package/upgrade, MCP, workbench UI,
  Telegram, HoldSpeak CI, docs, self-check, and history verification are
  green with evidence captured.
- [x] The phase final summary names delivered value, proof, decisions,
  limitations, and deliberately deferred work; release files are ready
  but no external publication is performed implicitly.

## Test plan

- **Unit:** full core suite.
- **Integration:** a dedicated fresh-consumer status loop plus the complete
  validation matrix.
- **Manual / device:** live source-repo walk and workbench visual check;
  inspect the resulting commit's PMO trailers and archived contract.

## Notes / open questions

The exit exam asserts recommendations, not merely eventual success. A
workflow that succeeds despite a wrong briefing is a failed test.
