# Phase 11 Final Summary

**Status:** complete.
**Date:** 2026-07-03.

Phase 11 extended the gate's guarantees across the last uncovered
boundary: other people. Work arriving by pull request now has a
written contract for what survives the fork, a fixture that proved
the merge-corruption narratives before any settings changed, a
repository that physically cannot squash-merge an audit trail into
garbage, and contributor docs that walk the whole loop in plain
language.

## Outcome vs exit criteria

All four exit criteria closed with evidence:

1. **Contribution contract** — `docs/contribution-rails.md`
   classifies every guarantee across a PR (mechanically verified by
   the required range check, attestation anchored by the digest
   trailer, or out of scope), with both squash failure narratives
   and the merge-commit rationale written out, and rebase-only plus
   one-story-per-PR locked with reasons (evidence-story-01,
   including the rule-id cross-check against the verifier source
   and the pre-enforcement settings baseline).
2. **Contributor flow proven** — `contributor-flow.sh`: a real
   clone activates the traveling rails with one config command,
   works a gated story on a branch, passes the PR-range verify, and
   lands by rebase merge with full-history verification green
   afterward. Both red legs fail with exactly the predicted rule
   ids (`atomicity`, `trailer-missing`), and the two-flip squash is
   refused by the local gate itself before the verifier is needed.
   No core changes were required (evidence-story-02).
3. **Enforcement and docs** — squash and merge-commit disabled
   (before/after captured), CONTRIBUTING rewritten in the plain
   register with its CI-executed snippets byte-identical and zero
   em dashes, the PR template asking for story, evidence, and a
   green `dw verify main..HEAD` (evidence-story-03).
4. **v1.8.0** — every version surface agrees under the parity
   tests, full battery and both distribution smokes green at the
   release commit, annotated tag, `dw verify --all` clean
   (evidence-story-04). Publication per the standing authorization;
   this release is the first where PyPI publishes automatically on
   the GitHub Release event.

## What shipped

`docs/contribution-rails.md`; `tests/contributor-flow.sh` in CI on
both OS legs; rebase-only repository settings; rewritten
CONTRIBUTING.md and PR template; the doc-correction that a fresh
clone activates rails with one config command; CHANGELOG v1.8.0.

## Deliberately deferred

Merge queues (trigger: concurrent-PR contention), CLA/DCO
machinery (trigger: legal need), GitHub-side button simulation
(local git reproduces the same trees and messages).

Future work starts by opening a new phase with `dw phase create`
and letting the rails do what they were built to do.
