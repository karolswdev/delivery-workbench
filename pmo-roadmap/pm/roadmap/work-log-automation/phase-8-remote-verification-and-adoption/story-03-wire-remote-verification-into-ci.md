# WLA-8-03 - Wire remote verification into CI

- **Project:** work-log-automation
- **Phase:** 8
- **Status:** backlog
- **Depends on:** WLA-8-02
- **Unblocks:** (optional)
- **Owner:** unassigned

## Problem

`dw verify` only closes the trust gap if something runs it where the
committer's hooks cannot be assumed: on every push and pull request.
Without CI enforcement, a bypassed local gate still lands unnoticed
and the trailers on public history remain unaudited claims.

## Scope

- **In:** A `verify-history` job in
  `.github/workflows/validation.yml` that runs `dw verify` over the
  pushed range (PR: merge-base..head with adequate fetch depth;
  push to main: the push range) on the Linux leg at minimum; a
  reusable snippet in the docs so adopting repositories can copy the
  job (documented in `docs/remote-verification.md` and the README's
  "what you get" list); a red-path proof — a scratch branch with a
  smuggled commit demonstrably failing the job.
- **Out:** GitHub branch-protection configuration (repo settings,
  not files), verification of other repositories' histories,
  marketplace-published composite actions (a copyable job is enough
  for this phase).

## Acceptance criteria

- [ ] CI fails on a branch containing a smuggled story-flip commit
  (evidence: the red run or its log excerpt) and passes on main.
- [ ] The job handles shallow checkouts correctly (explicit
  fetch-depth handling; no silent pass on truncated history).
- [ ] Adopters get a copy-pasteable job snippet in the docs, kept
  lint-clean by docs-lint.
- [ ] The README mentions history verification as part of the
  offering.

## Test plan

- **Unit:** n/a (workflow wiring).
- **Integration:** the validation.yml run on this repo's history;
  scratch-branch red run.
- **Manual / device:** inspect the Actions log for the failing rule
  line matching the `dw verify` output grammar.

## Notes / open questions

- Push-range verification on force-pushes falls back to full-history
  verify; acceptable if runtime stays in budget (<30s target from
  WLA-8-02).
