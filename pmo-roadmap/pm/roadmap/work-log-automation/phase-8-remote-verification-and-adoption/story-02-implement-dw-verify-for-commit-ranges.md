# WLA-8-02 - Implement dw verify for commit ranges

- **Project:** work-log-automation
- **Phase:** 8
- **Status:** backlog
- **Depends on:** WLA-8-01
- **Unblocks:** WLA-8-03
- **Owner:** unassigned

## Problem

The structural gate rules — one story flips done per commit, flipped
stories ship their evidence, evidence never appears or disappears
orphaned, trailers match the flipped story — are all derivable from
commit content alone, but nothing re-checks them after the fact. A
verifier that walks a commit range and re-derives those rules turns
the audit trail from "trust the committer's hooks" into "verify the
history", locally or in CI.

## Scope

- **In:** A `dw verify <range>` subcommand in `dw_pmo` implementing
  the contract from `docs/remote-verification.md`: per-commit
  re-derivation of the remotely-checkable rules over `<base>..<head>`
  (default: merge-base with the default branch to HEAD), greppable
  `ERROR <sha>: <rule>: <issue>` output, `--porcelain` mode, exit 0
  clean / 1 violations / 2 usage-or-git errors. Read-only: it never
  writes to the work tree or index. Unit coverage in
  `pmo-roadmap/tests/dw-core-tests.py` plus a shell suite
  `pmo-roadmap/tests/verify-range.sh` building fixture histories
  (clean, missing trailer, double-flip, evidence orphan) and
  asserting verdicts.
- **Out:** CI wiring (WLA-8-03), verifying contract-fact rules that
  the design doc classified attested-only, server-side enforcement
  hooks (pre-receive) — GitHub-hosted repos cannot run them anyway.

## Acceptance criteria

- [ ] `dw verify` re-derives every rule the design doc classifies as
  remotely re-derivable, and flags each violation with the rule id
  the local gate uses.
- [ ] A fixture history with a smuggled commit (story flipped done,
  no evidence, no trailers — as `--no-verify` would produce) fails
  with exit 1 and named rules; the repo's own history passes clean.
- [ ] Zero-dependency (python stdlib + git plumbing), consistent with
  repo conventions; runs on the full self-hosted history in <30s.
- [ ] `dw verify --help` and the agent-facing docs surface the
  command.

## Test plan

- **Unit:** rule re-derivation functions in
  `pmo-roadmap/tests/dw-core-tests.py` on synthetic commit data.
- **Integration:** `pmo-roadmap/tests/verify-range.sh` fixture
  histories, plus `dw verify` over this repository's real history.
- **Manual / device:** craft a `--no-verify` commit in a scratch
  clone; watch `dw verify` name it.

## Notes / open questions

- Historical commits predate some conventions; the design doc's
  scoping rules (which commits are in scope) must let the real
  history pass without grandfather hacks in the verifier itself.
