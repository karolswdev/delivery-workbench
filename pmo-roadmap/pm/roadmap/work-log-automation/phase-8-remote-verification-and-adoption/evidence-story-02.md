# Evidence - WLA-8-02

- **Story:** WLA-8-02 - Implement dw verify for commit ranges
- **Status:** done
- **Date:** 2026-07-03

## Proof

Deliverables:

- `lib/dw_pmo/verify.py` — the range verifier: one `git log` walk
  per range (fields/records/values on distinct control separators),
  first-parent re-derivation of `atomicity`,
  `contract-story-mismatch`, `evidence-missing`, `orphan-evidence`,
  and `evidence-deletion-orphans-story` with the local gate's rule
  ids, plus the remote-only `trailer-missing`/`trailer-format`.
  Epoch scoping per the design contract (auto-detect first
  digest-trailer commit; `--epoch`/`PMO_VERIFY_EPOCH` pin); shallow
  clones exit 2; read-only throughout.
- `bin/dw`: the `verify` subcommand (`[<base>..<head>] | --all`,
  `--epoch`, `--porcelain`; exit 0/1/2 per the contract).
- `PMO-Bundle:` trailer: `append_trailers` now stamps the BUNDLE-OK
  rationale's first line, wired through `dw contract trailers`
  (proven live in verify-range.sh — the real commit-msg hook stamps
  it and the verifier accepts the bundled double-flip).
- Tests: `VerifyTest` (13 cases) in dw-core-tests.py (98 → 111),
  including the rule-inventory parity assertion against gate.py and
  `docs/remote-verification.md`; `tests/verify-range.sh` fixture
  suite (clean / smuggled / double-flip red+green / wrong-story /
  orphan / deletion / malformed trailers / porcelain / bad ranges /
  pinned epoch / shallow-clone exit 2).
- Agent surface: managed-block, CLAUDE-snippet, and plugin SKILL.md
  teach `dw verify`; installed `.githooks` snapshot refreshed and
  diff-verified in sync with source.

The captured run below: full unit suite, both shell suites, and the
real-history sweep — 27 in-scope commits verified clean in ~1.3s,
17 pre-epoch commits skipped, epoch auto-detected at `faa7de6`
(contract v2), matching the design contract's survey exactly.

### Captured run — 2026-07-03T16:03:56Z

- **Command:** `bash -c set -e -o pipefail; python3 pmo-roadmap/tests/dw-core-tests.py 2>&1 | tail -3; bash pmo-roadmap/tests/verify-range.sh 2>&1 | tail -1; bash pmo-roadmap/tests/gate-parity.sh 2>&1 | tail -1; .githooks/dw verify --all; .githooks/dw verify --all --porcelain | head -6`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 9a6d3d1c7a624d384ca395210d8b9ad0b1fcf91d

```text
Ran 111 tests in 8.432s

OK
verify-range.sh: ok
gate-parity.sh: ok
dw verify: ok (27 commits verified, 17 pre-epoch skipped)
verify=pass
verified=27
pre_epoch_skipped=17
out_of_scope=22
epoch=faa7de6
commit=faa7de6
```
