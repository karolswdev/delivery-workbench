# WLA-11-01 - Define the contribution contract

- **Project:** work-log-automation
- **Phase:** 11
- **Status:** done
- **Depends on:** none
- **Unblocks:** WLA-11-02
- **Owner:** unassigned

## Problem

Every guarantee so far assumes the committer is the pusher. A pull
request breaks that assumption: the contributor's contract archive
stays in their clone, their commits get rewritten by whatever merge
method the button offers, and the maintainer merges work they did
not gate. Today all three merge methods are enabled on the repo;
a squash merge would concatenate commit messages (mangling PMO
trailers out of the final-paragraph position git requires) and can
collapse several story flips into one commit — planting an
atomicity violation directly on main that `verify-history` then
flags on every subsequent push. Nobody has written down what the
gate's guarantees mean across a fork boundary, so the enforcement
and the docs (WLA-11-02/03) have nothing to be tested against.

## Scope

- **In:** A design document `docs/contribution-rails.md` that
  decides: (a) what survives the fork boundary — trailers and
  roadmap/evidence structure travel with commits and are
  remotely verifiable (`dw verify` over the PR range); contract
  archives and certification remain attestations anchored by the
  digest trailer, exactly as `docs/remote-verification.md`
  classifies them; (b) merge-method policy — rebase-only, with the
  precise failure narrative for squash (trailer mangling +
  multi-flip collapse) and merge commits (out of scope for the
  verifier, blocked by linear history); note that rebase rewrites
  SHAs, which is safe because every stamped fact that mentions a
  SHA is attested-only; (c) the one-story-per-PR convention as the
  natural extension of the one-flip-per-commit gate rule; (d) what
  reviewers check mechanically before merging (`dw verify` over the
  PR range is already a required check; the doc says what the
  green checkmark does and does not prove); (e) what contributors
  without rails produce (commits outside the roadmap tree are out
  of the verifier's scope by design — state this honestly and say
  why gated commits are still required by convention for roadmap
  work).
- **Out:** Implementing the fixture proof (WLA-11-02), changing
  repo settings or CONTRIBUTING (WLA-11-03), merge queues, signed
  commits, CLA machinery.

## Acceptance criteria

- [ ] `docs/contribution-rails.md` exists and states, for each gate
  guarantee, whether it survives a PR mechanically, survives as an
  attestation, or does not apply to fork-boundary work — with the
  squash and merge-commit failure narratives written out.
- [ ] The rebase-only and one-story-per-PR decisions are recorded
  with rationale, mirrored in the phase status.
- [ ] The doc names the proof obligations WLA-11-02 must implement
  (green rebase path, red squash paths).
- [ ] Docs-lint passes.

## Test plan

- **Unit:** n/a (design story).
- **Integration:** `pmo-roadmap/tests/docs-lint.sh`.
- **Manual / device:** cross-check the claims against the actual
  repo settings captured at phase open (squash/merge/rebase all
  enabled; linear history required).

## Notes / open questions

- Single-commit PRs squash cleanly in principle, but the message
  concatenation still moves trailers when the PR has fixup commits;
  the policy is rebase-only across the board rather than a
  conditional rule nobody will remember.
