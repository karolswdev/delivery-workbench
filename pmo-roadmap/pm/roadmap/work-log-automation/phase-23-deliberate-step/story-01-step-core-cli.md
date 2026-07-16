# WLA-23-01 - dw step — preview and apply one allowlisted action

- **Project:** work-log-automation
- **Phase:** 23
- **Status:** done
- **Depends on:** none
- **Unblocks:** WLA-23-02, WLA-23-03
- **Owner:** unassigned

## Problem

The Phase-22 briefing removes interpretation risk but still ends in copied
argv. Copy/paste loses the observed-state boundary: between reading and
acting, the workspace, selected story, contract, or gate can move. Agents
also need a closed capability surface, not permission to execute whatever a
model happens to put in a command field.

## Scope

- **In:** `dw_pmo.step` preview/apply core; `delivery-workbench-step@1`;
  full-status SHA-256 token; exact closed action-id/argv-shape validation;
  `dw step [project] [--json] [--apply --expect <token>]`; source/vendored/
  package parity; unit, CLI integration, docs, and red paths.
- **Out:** result receipt schema and event append (WLA-23-02); MCP/HTTP
  adapters; workbench controls; arbitrary argv; action loops; certification;
  commit; automatic project selection.

## Acceptance criteria

- [x] Preview returns an exact-key, schema-v1 document containing the current
  status action, selected project, deterministic `sha256:` state token,
  applicability/refusal, and a tokenized apply argv; repeated previews are
  byte-identical and change no tracked file or event.
- [x] Apply requires `--expect`; it re-builds the whole preview immediately
  before execution and refuses a mismatch without invoking the runner, even
  when the new state retains the same action id.
- [x] A closed table validates both action id and exact argv shape. Manual
  actions, `commit`, unknown ids, modified paths/verbs/options, and shell
  strings are not applicable and cannot reach the runner.
- [x] An applicable preview executes at most its one existing argv from the
  repository root, mirrors the child exit code, then reports the newly
  observed next action. It never follows that action automatically.
- [x] Python 3.9, full core, installed CLI lifecycle, shellcheck/docs, self-
  update parity, roadmap check, and diff hygiene are green with captured
  evidence.

## Test plan

- **Unit:** exact schema/token; purity; stale same-id refusal; closed-table
  positive/negative matrix; commit/manual refusal; runner call count/root.
- **Integration:** installed fixture previews `start-story`, rejects a stale
  token without flipping, then explicitly applies a fresh token and stops at
  `continue-story`.
- **Manual / device:** dogfood preview on this repository; inspect that the
  generated apply argv is explicit and that the current in-progress story is
  not changed by preview.

## Notes / open questions

`--json --apply` is deferred to the receipt story. Story 01 JSON is the pure
preview contract; apply has intentionally small human output plus the child
process's own authoritative output.

Implemented as a separate `dw_pmo.step` composition boundary so status stays
pure and later adapters can reuse policy without parsing CLI output. The
complete status document, not an action id subset, is the token input. A
closed action-id/argv-shape matrix is checked again at the execution seam;
commit and certification are explicit permanent exclusions. The repository
dogfood preview/apply ran `continue-story` once and stopped, and the guarded
story-closing transition itself is exercised through a fresh `dw step` token.
