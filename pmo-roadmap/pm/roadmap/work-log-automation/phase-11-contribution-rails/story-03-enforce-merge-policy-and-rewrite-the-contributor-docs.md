# WLA-11-03 - Enforce merge policy and rewrite the contributor docs

- **Project:** work-log-automation
- **Phase:** 11
- **Status:** backlog
- **Depends on:** WLA-11-02
- **Unblocks:** WLA-11-04
- **Owner:** unassigned

## Problem

The squash hazard is proven (WLA-11-02) but the squash button is
still enabled, and the contributor documentation predates every
capability shipped since v1.5.0: it does not mention `dw verify`
as the required PR check, the MCP tools, the pipx/brew install
path, or the one-story-per-PR convention. A contributor following
CONTRIBUTING today gets an incomplete picture, and a maintainer
click on the wrong merge button corrupts main's audit trail.

## Scope

- **In:** Repository enforcement: disable squash and merge-commit
  methods, leaving rebase-only (`gh api` PATCH; setting captured
  in evidence before and after). PR template
  (`.github/PULL_REQUEST_TEMPLATE.md`) audited and updated: story
  ID, evidence link, and a note that the range must pass
  `dw verify` (the required check). CONTRIBUTING.md rewritten in
  the plain register the root README now uses, humanizer pass
  included: the fork-to-merged loop step by step, the
  one-story-per-PR convention, what the required checks verify and
  what stays attested, the no-clone toolchain install, and where
  the MCP tools fit for agent contributors.
  `docs/contribution-rails.md` linked from the docs index in the
  README.
- **Out:** Merge queues, auto-merge, CODEOWNERS, CLA bots,
  release notes (WLA-11-04).

## Acceptance criteria

- [ ] `gh api` shows `allow_squash_merge` and `allow_merge_commit`
  false, `allow_rebase_merge` true — captured in evidence.
- [ ] CONTRIBUTING walks clone → branch → gated story → PR →
  rebase merge without referencing stale facts, passes docs-lint,
  and contains no em dashes outside quoted output.
- [ ] The PR template asks for the story ID and evidence link.
- [ ] All doc parity and lint suites green.

## Test plan

- **Unit:** n/a.
- **Integration:** docs-lint, docs-snippet-smoke, agent-surface.
- **Manual / device:** the `gh api` before/after capture.

## Notes / open questions

- Rebase-only means contributors with merge-commit habits get a
  button that is simply absent; the PR template should say why in
  one line so it reads as policy, not accident.
