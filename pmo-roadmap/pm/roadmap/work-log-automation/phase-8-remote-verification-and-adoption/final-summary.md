# Phase 8 Final Summary

**Status:** complete.
**Date:** 2026-07-03.

Phase 8 extended the gate's guarantees beyond the local clone: the
trust story no longer ends where `core.hooksPath` does. What a
bypassed local gate lets through, pushed history now betrays — a
design contract classified every rule for remote re-derivability,
`dw verify` implements the re-derivable set with the local gate's
own rule ids, CI enforces the sweep on every push and PR, and the
first real external adoption shipped a gated story and paid its
friction findings back into the framework.

## Outcome vs exit criteria

All four exit criteria closed with evidence:

1. **Every gate rule id classified; `dw verify` implements the
   re-derivable set** — `docs/remote-verification.md` classifies all
   17 gate rule ids plus the 2 remote-only trailer rules, held in
   lockstep by a doc-parity test and a unit assertion; the verifier
   emits the local gate's rule ids (evidence-story-01,
   evidence-story-02).
2. **Own history passes; smuggled commits fail with named rules** —
   `dw verify --all` verifies the repository's in-scope history
   clean with pre-epoch commits skipped (never flagged), and fixture
   histories fail on the exact rules a `--no-verify` bypass violates
   (evidence-story-02, `tests/verify-range.sh`).
3. **CI enforcement with a red-path proof** — the `verify-history`
   job runs the full sweep on push and PR with shallow-clone refusal
   baked in; the job's exact command blocks a scratch branch
   carrying a smuggled story flip with three named rules
   (evidence-story-03).
4. **External adoption, gated story, friction triaged** — a scratch
   clone of fridgr (real 133-commit product repo) went through the
   documented three-command path headlessly, reached doctor-green,
   shipped FR-1-01 through the gate with trailers and archive, and
   `dw verify` passed there with the entire pre-adoption history
   pre-epoch-skipped; all five friction findings triaged, four fixes
   landed with re-run proofs and regression coverage
   (evidence-story-04, evidence-story-05, `adoption-friction.md`).

## What shipped

- `docs/remote-verification.md` — the remote verification contract:
  re-derivable vs attested-only classification, commit scoping and
  epoch policy, `PMO-Bundle:` trailer decision, CLI specification,
  CI wiring with a copyable adopter snippet.
- `lib/dw_pmo/verify.py` + the `dw verify` subcommand — one-pass
  range walk, first-parent re-derivation of the structural rules,
  epoch auto-detection (pinnable via `--epoch`/`PMO_VERIFY_EPOCH`),
  merge commits out of scope, loud shallow-clone failure, porcelain
  mode, exit codes 0/1/2.
- `PMO-Bundle:` trailer stamping in the commit-msg path, making
  atomicity fully re-derivable remotely.
- `verify-history` job in `validation.yml`.
- Adoption-friction fixes: discovery launch messaging, README
  headless expectations, stdout-is-the-report prompt instruction,
  self-hosting-aware `install.sh`.
- Tests: 14 `VerifyTest` unit cases (suite 98 → 112),
  `tests/verify-range.sh`, `tests/remote-verification-doc-check.py`,
  and a two-direction self-hosting regression case in
  `tests/adoption-discovery.sh`.

## Deliberately deferred

Recorded with triggers in `current-phase-status.md`: remote-portable
contract archives, evidence-run presence as a remote rule, discovery
`--timeout`/heartbeat, and sandbox allowlisting of read-only `dw`
orientation for discovery agents. Distribution (Homebrew/pipx),
branch-protection configuration, and multi-contributor adoption
trials remain future-phase candidates.

Future work starts by opening a new phase with `dw phase create` and
letting the rails do what they were built to do.
