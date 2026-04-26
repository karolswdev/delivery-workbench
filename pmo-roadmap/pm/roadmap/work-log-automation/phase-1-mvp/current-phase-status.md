# Phase 1 - MVP

**Last updated:** 2026-04-25.

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

- [ ] A consented commit writes one markdown entry to
  `~/.work/log/YYYY-MM-DD/{project}-work-summary.log`.
- [ ] A denied-consent commit writes no daily log entry.
- [ ] A commit that aborts after `pre-commit` writes no daily log entry.
- [ ] Pending payloads are cleaned after successful `post-commit` finalization.
- [ ] `install.sh` and `update.sh` install/update all canonical hook files.
- [ ] Temporary-repo tests prove consent yes/no and abort behavior.
- [ ] The README gives a simple read-flow recipe for today's work log.

## Story status

| ID | Story | Status | Story file | Evidence |
|---|---|---|---|---|
| WLA-1-01 | Add work-log consent to the canonical contract | backlog | [story-01-contract-consent](./story-01-contract-consent.md) | - |
| WLA-1-02 | Capture consented staged payloads in pre-commit | backlog | [story-02-pre-commit-capture](./story-02-pre-commit-capture.md) | - |
| WLA-1-03 | Finalize daily log entries in post-commit | backlog | [story-03-post-commit-finalize](./story-03-post-commit-finalize.md) | - |
| WLA-1-04 | Install, update, and document the MVP hooks | backlog | [story-04-install-update-docs](./story-04-install-update-docs.md) | - |
| WLA-1-05 | Add temporary-repo integration coverage | backlog | [story-05-integration-tests](./story-05-integration-tests.md) | - |
| WLA-1-06 | Add read-flow and first-run discoverability | backlog | [story-06-read-flow-discoverability](./story-06-read-flow-discoverability.md) | - |

## Where we are

Phase 1 starts after Phase 0 validates the architecture. The first
implementation move is WLA-1-01, because the hook must not infer daily-log
permission from the existing PMO checkbox count. WLA-1-05 should begin as a
test-harness skeleton alongside WLA-1-02, then grow assertions as capture and
finalization land. WLA-1-02 and WLA-1-03 should still ship separately so each
lifecycle boundary can be evidenced.

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

- Exact deferred summarizer prompt and command shape - trigger in Phase 2 after
  deterministic entry shape is stable - default is no LLM call in the commit
  path.
