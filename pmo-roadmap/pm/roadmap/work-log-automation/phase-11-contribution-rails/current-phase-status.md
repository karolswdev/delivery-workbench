# Phase 11 - Contribution Rails

**Last updated:** 2026-07-03.

## Goal

Extend the gate's guarantees to work that arrives by pull request: a contribution contract defining how gated commits travel through forks and merges, an end-to-end contributor-flow proof with red paths for the merge methods that would corrupt the audit trail, repository enforcement and plain-language contributor docs, and a v1.8.0 release.

## Scope

- **In:** A contribution contract (`docs/contribution-rails.md`)
  classifying what survives the fork boundary mechanically vs as
  attestation; a `contributor-flow.sh` fixture proving the green
  rebase path and demonstrating the squash corruption red paths
  with exact rule ids; rebase-only merge settings enforced via the
  API with before/after evidence; a CONTRIBUTING rewrite in the
  plain register (fork-to-merged loop, one-story-per-PR, required
  checks, no-clone toolchain, MCP for agent contributors) and a PR
  template asking for story and evidence; the v1.8.0 release —
  expected to be the first with fully automatic PyPI publication.
- **Out:** Merge queues, auto-merge, CODEOWNERS, CLA machinery,
  signed commits, GitHub-side button simulation (local git
  reproduces the same trees and messages).

## Exit criteria (evidence required)

- [ ] `docs/contribution-rails.md` states, per gate guarantee,
  what survives a PR mechanically, what survives as attestation,
  and what does not apply — with squash and merge-commit failure
  narratives written out.
- [ ] `contributor-flow.sh` passes the green path (gated branch →
  PR-range verify → rebase merge → main verify green) and both
  squash red legs fail with the predicted rule ids.
- [ ] The repo allows rebase merges only, captured before/after;
  CONTRIBUTING and the PR template match the enforced reality.
- [ ] v1.8.0 ships with version parity, green battery, the
  annotated tag, and PyPI publication requiring zero manual steps.

## Story status

| ID | Story | Status | Story file | Evidence |
|---|---|---|---|---|
| WLA-11-01 | Define the contribution contract | backlog | [story-01-define-the-contribution-contract](./story-01-define-the-contribution-contract.md) | - |
| WLA-11-02 | Prove the contributor flow end-to-end | backlog | [story-02-prove-the-contributor-flow-end-to-end](./story-02-prove-the-contributor-flow-end-to-end.md) | - |
| WLA-11-03 | Enforce merge policy and rewrite the contributor docs | backlog | [story-03-enforce-merge-policy-and-rewrite-the-contributor-docs](./story-03-enforce-merge-policy-and-rewrite-the-contributor-docs.md) | - |
| WLA-11-04 | Release v1.8.0 | backlog | [story-04-release-v1-8-0](./story-04-release-v1-8-0.md) | - |

## Where we are

Phase scaffolded with full story specs, grounded in a settings
audit at phase open: squash, merge-commit, and rebase are all
currently enabled; linear history is required; a PR template
exists and predates the last three releases. Sequential:
contract → proof → enforcement → release.

## Active risks

| Risk | Likelihood | Mitigation | Stop signal |
|---|---|---|---|
| The squash failure narrative is wrong in detail (git composes messages differently than assumed) | medium | WLA-11-02 reproduces GitHub's message concatenation explicitly before any settings change | Red legs fail with different rule ids than the doc predicts |
| Rebase-only policy surprises a real contributor mid-PR | low | Template and CONTRIBUTING state the policy and the reason in one line | A PR gets stuck on a missing merge button with no explanation in sight |
| First automatic PyPI publish fails despite registration | low | The v1.7.0 manual dispatch proved the exchange; the release story records any manual step as a finding | publish-pypi job red on the v1.8.0 release |

## Decisions made (this phase)

- 2026-07-03 - Phase scaffolded with `dw phase create` - keeps roadmap structure consistent - CLI.
- 2026-07-03 - Rebase-only merges, one story per PR - squash mangles trailer position and collapses flips; merge commits are outside the verifier's scope; one-story-per-PR extends the one-flip-per-commit rule to the PR unit - phase design (to be locked in WLA-11-01).

## Decisions deferred

- Merge queue adoption - trigger: enough concurrent PRs that rebase races hurt - default is none.
- Contributor CLA or DCO sign-off - trigger: external legal need - default is none.
