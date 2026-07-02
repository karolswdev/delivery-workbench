# Phase 1 - MVP

**Last updated:** 2026-07-01.

## Goal

Ship the smallest trustworthy Work Log Automation path: explicit consent in
the contract, exact staged-diff capture in `pre-commit`, durable append in
`post-commit`, deterministic summaries, and installer/update support.

## Scope

- **In:** Canonical contract update, hook lifecycle, pending payloads, local log
  append, deterministic summary fallback, installation/update mechanics, and
  focused shell/integration tests.
- **Out:** LLM summarizer calls in the commit path, redaction plugins, remote
  sync, end-of-day aggregation, and consumer-project pilot rollout.

## Exit criteria (evidence required)

- [x] A consented commit writes one markdown entry to
  `~/.work/log/YYYY-MM-DD/{project}-work-summary.log`.
- [x] A denied-consent commit writes no daily log entry.
- [x] A commit that aborts after `pre-commit` writes no daily log entry.
- [x] Pending payloads are cleaned after successful `post-commit` finalization.
- [x] `install.sh` and `update.sh` install/update all canonical hook files.
- [x] Temporary-repo tests prove consent yes/no and abort behavior.
- [x] The README gives a simple read-flow recipe for today's work log.

## Story status

| ID | Story | Status | Story file | Evidence |
|---|---|---|---|---|
| WLA-1-01 | Add work-log consent to the canonical contract | done | [story-01-contract-consent](./story-01-contract-consent.md) | [evidence-story-01](./evidence-story-01.md) |
| WLA-1-02 | Capture consented staged payloads in pre-commit | done | [story-02-pre-commit-capture](./story-02-pre-commit-capture.md) | [evidence-story-02](./evidence-story-02.md) |
| WLA-1-03 | Finalize daily log entries in post-commit | done | [story-03-post-commit-finalize](./story-03-post-commit-finalize.md) | [evidence-story-03](./evidence-story-03.md) |
| WLA-1-04 | Install, update, and document the MVP hooks | done | [story-04-install-update-docs](./story-04-install-update-docs.md) | [evidence-story-04](./evidence-story-04.md) |
| WLA-1-05 | Add temporary-repo integration coverage | done | [story-05-integration-tests](./story-05-integration-tests.md) | [evidence-story-05](./evidence-story-05.md) |
| WLA-1-06 | Add read-flow and first-run discoverability | done | [story-06-read-flow-discoverability](./story-06-read-flow-discoverability.md) | [evidence-story-06](./evidence-story-06.md) |

## Where we are

Phase 1 is complete. The canonical contract exposes explicit work-log consent,
`pre-commit` captures consented staged payloads, `post-commit` appends
deterministic daily entries, install/update copy the full hook/helper set, and
the temporary-repo integration harness proves disabled, consented, denied,
aborted, amend, duplicate, and hook-collision behavior.

## Active risks

| Risk | Likelihood | Mitigation | Stop signal |
|---|---|---|---|
| Consent parsing is too loose | medium | Require an explicit `Work-log consent: yes` line and reasons block | A checked box alone enables logging |
| Pending files collide across commit attempts | low | Use a single repo-local pending file with capture timestamp and overwrite rules for aborted attempts | Two commits append the same pending payload |
| Log path expansion behaves differently on macOS/Linux | low | Use shell-tested `$HOME/.work/log/$(date +%F)` creation | Tests pass on one platform but path contains literal `~` on another |
| The log becomes write-only memory | medium | Add a read-flow recipe and print the log path when entries are written | A user cannot find today's entry from the README or hook output |

## Decisions made (this phase)

- 2026-04-25 - MVP summaries are deterministic rather than LLM-generated -
  proves the lifecycle before adding model latency - Phase 0 architecture.

## Decisions deferred

- Exact deferred summarizer prompt and command shape - resolved in Phase 2 as
  an explicit operator-provided command with deterministic fallback and no LLM
  call in the commit path.
