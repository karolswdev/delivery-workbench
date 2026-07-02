# WLA-6-08 - Harden CI, parity, and portability testing

- **Project:** work-log-automation
- **Phase:** 6
- **Status:** done
- **Depends on:** WLA-6-02
- **Unblocks:** none
- **Owner:** unassigned

## Problem

The framework's core value proposition — the commit gate blocks bad commits
— has zero negative-path tests. Every test commit writes a valid contract
first; nothing in CI proves a missing, stale, unchecked, or under-counted
contract actually blocks, nor that the pairing and atomicity rules fire.
The only demonstration lives in a VHS demo that CI never plays. CI runs
ubuntu-only although the hooks carry explicit BSD/GNU dual code paths
(`stat -f %m` vs `stat -c %Y`) and the author develops on macOS, so the
macOS branch is exercised only by hand. There is no shellcheck step despite
`# shellcheck disable` annotations implying local use, no `permissions:`
stanza (defaulting to a write token), no concurrency group, and duplicate
push+PR runs. The `pre-commit.local` extension seam — the mechanism
consumer projects depend on for custom rules — is untested.

## Scope

- **In:** A negative-path gate suite (`pmo-roadmap/tests/gate-negative.sh`
  or folded into `gate-parity.sh` from WLA-6-02) proving each block fires
  and each remediation unblocks: missing contract, stale contract (index
  tree), unchecked box, unknown box, multi-story commit without
  `BUNDLE-OK.md`, missing forward evidence, orphan evidence, and the
  `pre-commit.local` seam adding a custom failing rule. CI matrix:
  `ubuntu-latest` plus `macos-latest` running the full test set; a
  shellcheck job over all shipped shell (annotations become enforced);
  `dw check work-log-automation` self-validation (landed in WLA-6-01,
  kept green here); Python version coverage matching the supported floor
  declared in docs. Workflow hygiene: `permissions: contents: read`,
  a concurrency group with cancel-in-progress, and push filtered to `main`
  so PRs run once.
- **Out:** Browser/UI test infrastructure (Phase 5, WLA-5-10); Windows
  support; performance benchmarking; publishing the framework as a
  package.

## Acceptance criteria

- [ ] Every gate rule has at least one CI-run test that asserts the block
  fires (non-zero exit plus the rule's name in output) and one that
  asserts the documented remediation unblocks.
- [ ] The full suite passes on `ubuntu-latest` and `macos-latest` in the
  same workflow run, exercising both `stat` branches.
- [ ] `shellcheck` passes over `install.sh`, `update.sh`, both hooks, the
  bootstrap scripts, helpers, and tests, with remaining `disable`
  directives carrying a reason comment.
- [ ] `.github/workflows/validation.yml` declares least-privilege
  permissions and a concurrency group, and does not double-run on PRs from
  branches.
- [ ] The `pre-commit.local` seam test proves a project-local rule can
  block a commit and is preserved across `update.sh`.

## Test plan

- **Unit:** n/a (this story is the test infrastructure).
- **Integration / Cypress:** The new negative-path suite plus the existing
  three suites, all green in the CI matrix.
- **Manual / device:** Trigger one PR run and one push run; confirm single
  execution per event and green matrix.

## Notes / open questions

Keep the negative-path suite hermetic (temp repos) so it can run on
contributor machines without touching their hooks. If macOS runner minutes
are a concern, run the macOS leg on push-to-main only — but the gate suite
itself must be in both legs, since the `stat` divergence lives in the gate
path.
