# WLA-6-03 - Ship verified contract v2 with durable audit trail

- **Project:** work-log-automation
- **Phase:** 6
- **Status:** backlog
- **Depends on:** WLA-6-02
- **Unblocks:** WLA-6-05, WLA-6-06
- **Owner:** unassigned

## Problem

The contract is the framework's most visible feature and its least
verified. Today the gate checks only form: the file exists, its mtime is
newer than HEAD, and it contains at least seven `- [x]` lines. Any seven
checked lines pass; the checkbox text is never compared to the rules; the
"Staged files (sample)" line can be invented; `touch .tmp/CONTRACT.md`
defeats staleness. Five of the seven rules are pure self-certification,
which for an LLM agent generating the whole file in one Write collapses the
intended moment of reflection into token prediction.

Worse, the contract leaves no durable trace. It is gitignored, deleted on
hook success, and persisted only inside the work-log payload when logging
is enabled and consented. In the default configuration nothing anywhere
proves a contract ever existed. `BUNDLE-OK.md` — whose entire purpose is
the recorded rationale — is destroyed unread on success. And because the
hook deletes the contract before git finishes the commit, a commit that
fails after the hook (empty message, commit-msg hook) silently consumes the
contract and forces re-authoring.

## Scope

- **In:** `dw contract new [--story <id>]` generates `.tmp/CONTRACT.md`
  from a real template file, stamping machine-verifiable facts: branch,
  HEAD SHA, `git write-tree` index tree, staged file list, UTC timestamp,
  and the story ID(s) detected in the staged diff. At commit time
  `dw gate` verifies the stamped facts against reality — index-tree match
  replaces mtime as the freshness proof (a contract written for a different
  staging state is stale by definition; `touch` no longer helps), branch
  and staged sample must match, and checkbox lines must correspond to the
  template's rule set (canonical plus project extensions) rather than being
  merely counted. Durable trail: the gate appends `PMO-Story:` and
  `PMO-Contract-Digest:` (sha256 of the contract body) trailers to the
  commit message, and archives the full contract plus any `BUNDLE-OK.md`
  rationale under `.git/pmo-contract-archive/<commit>` at post-commit time.
  Contract deletion moves from pre-commit success to post-commit finalize,
  so an aborted commit no longer consumes the contract.
- **Out:** Machine-verifying the "tests actually ran" rule (WLA-6-04);
  tiered/short-form contracts (WLA-6-06); any server-side or remote
  attestation; rewriting historical commits to add trailers.

## Acceptance criteria

- [ ] `dw contract new` writes a contract whose stamped branch, HEAD,
  index tree, and staged sample are real; tampering with any stamped fact
  and re-staging different content causes the gate to block with a message
  naming the mismatched fact.
- [ ] Re-using a contract after changing the staged index is blocked by the
  index-tree check; `touch .tmp/CONTRACT.md` alone no longer refreshes a
  stale contract (regression test).
- [ ] A checked box whose text does not correspond to a known rule (canonical
  or project extension) fails the gate; `EXPECTED_BOXES` count-only checking
  is retired.
- [ ] Every gated commit carries `PMO-Story:` and `PMO-Contract-Digest:`
  trailers, and `.git/pmo-contract-archive/<sha>` contains the exact
  contract (digest matches the trailer) plus the bundle rationale when one
  was used.
- [ ] A commit aborted after the pre-commit hook leaves `.tmp/CONTRACT.md`
  in place and the next attempt succeeds without re-authoring (regression
  test).
- [ ] `dw context --trace` surfaces contract digests alongside commits so
  the chain story -> evidence -> commit -> contract -> work-log resolves.

## Test plan

- **Unit:** Fact-stamping and fact-verification tests in the `dw_pmo`
  suite, including tamper cases for each stamped field.
- **Integration / Cypress:** `pmo-roadmap/tests/gate-parity.sh` extended
  with contract-v2 scenarios: stale index tree, invented staged sample,
  unknown checkbox, aborted-commit survival, trailer and archive
  verification via `git log --format=%(trailers)`.
- **Manual / device:** Author one real commit on this repo with
  `dw contract new` and inspect the trailer, archive, and trace output.

## Notes / open questions

The honor-system boxes that remain (evidence-not-vibes, greenfield
discipline) stay — the point is to shrink the honor surface to what is
genuinely unverifiable, and make everything else stamped or checked.
Whether the archive should also be mirrored into a committed, append-only
audit file (public tamper-evidence vs. repo noise) is deferred to the phase
decision log; the local archive plus digest trailer is the floor.
