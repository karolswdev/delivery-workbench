# WLA-8-01 - Define the remote verification contract

- **Project:** work-log-automation
- **Phase:** 8
- **Status:** done
- **Depends on:** none
- **Unblocks:** WLA-8-02
- **Owner:** unassigned

## Problem

The gate's guarantees currently end at the local clone. Contracts
live in `.tmp/`, archives under `.git/pmo-contract-archive/`, and the
hooks only run where `core.hooksPath` is configured. A push from an
unconfigured clone — or a deliberate `--no-verify` — lands commits
nobody re-checked, and the trailers on them are attestations, not
verified facts. Before building a verifier, we must decide precisely
which gate rules are re-derivable from a pushed commit range alone,
which are attested-only, and whether any local-only facts should be
made portable.

## Scope

- **In:** A design document `docs/remote-verification.md` that (a)
  enumerates every gate rule id from `dw_pmo/gate.py` and classifies
  it as remotely re-derivable, attested-only, or portable-with-change;
  (b) specifies the `dw verify` CLI surface: range semantics, which
  commits are in scope (gated-path touches), output format
  (greppable `ERROR <sha>: <rule>: <issue>` lines), exit codes
  aligned with `dw check`/`dw next` conventions, and `--porcelain`;
  (c) decides the bundle-consent question — remote verifiers cannot
  see `.tmp/BUNDLE-OK.md`, so multi-flip commits need a visible
  rationale (e.g. a `PMO-Bundle:` trailer) or remain flagged; (d)
  decides whether contract archives stay local-only in v1.
- **Out:** Any implementation (WLA-8-02), CI wiring (WLA-8-03),
  signing/attestation schemes beyond what git trailers carry.

## Acceptance criteria

- [ ] `docs/remote-verification.md` exists and classifies every rule
  id emitted by `gate.py` (grep-verifiable: each id appears in the
  doc's classification table).
- [ ] The `dw verify` CLI contract is specified: arguments, commit
  scoping, output line grammar, exit codes, porcelain mode.
- [ ] The bundle-visibility decision is recorded with its rationale,
  and the phase status file logs the decisions made.
- [ ] Docs-lint passes over the new document.

## Test plan

- **Unit:** n/a (design story).
- **Integration:** `pmo-roadmap/tests/docs-lint.sh` over the repo
  including the new doc.
- **Manual / device:** cross-check the rule table against
  `grep 'failed(' dw_pmo/gate.py` output — no rule id missing.

## Notes / open questions

- Trailer-based bundle rationale would make the atomicity rule fully
  remote-verifiable; decide whether the gate should stamp it.
- Contract digests are re-derivable only if the certified contract
  text is available remotely; shipping archives (git notes or a
  tracked directory) has privacy and noise costs — default to
  local-only unless the doc argues otherwise.
