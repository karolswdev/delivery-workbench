# WLA-2-03 - Add redaction and diff-size controls

- **Project:** work-log-automation
- **Phase:** 2
- **Status:** backlog
- **Depends on:** WLA-2-01, WLA-2-02
- **Unblocks:** Phase 3 rollout
- **Owner:** unassigned

## Problem

The daily log is local by default, but it can still preserve sensitive details
longer than intended. The framework needs basic controls for exclusions,
redaction, and large diffs.

## Scope

- **In:** Max diff bytes, excluded path patterns, secret-looking token redaction
  if practical in shell, and payload markers when content is omitted.
- **Out:** Full DLP scanning or policy-server integration.

## Acceptance criteria

- [ ] Diff capture respects `PMO_WORK_LOG_MAX_DIFF_BYTES`.
- [ ] Excluded paths are omitted from summarizer payloads and named as omitted.
- [ ] Redaction behavior is documented prominently as best effort, not a
  security boundary.
- [ ] Docs name categories redaction cannot reliably catch, such as base64
  blobs, JWT payloads, and env-expanded values.
- [ ] Tests prove excluded files do not appear in pending payload or final log.

## Test plan

- **Unit:** Shell tests for path exclusion and truncation helpers.
- **Integration / Cypress:** Temporary repo with staged secret-like file path
  excluded by config.
- **Manual / device:** Inspect payload and final log for omission markers.

## Notes / open questions

Consent remains the real privacy boundary. Redaction should reduce accidents,
not justify logging material the committer is uncomfortable preserving.
