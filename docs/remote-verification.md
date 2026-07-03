# Delivery Workbench — Remote Verification Contract

What the commit gate can and cannot re-verify from pushed history
alone, and the exact CLI surface of `dw verify`, the range verifier
that implements it. This is the design contract for WLA-8-02
(implementation) and WLA-8-03 (CI enforcement); the classifications
below are the specification the verifier is tested against.

## The trust gap

The gate runs where `core.hooksPath` points at `.githooks` — and only
there. Three artifacts it relies on never leave the local clone:

- the certified contract, `.tmp/CONTRACT.md` (cleared post-commit);
- the contract archive, `.git/pmo-contract-archive/<sha>` (`.git` is
  never pushed);
- the bundle consent file, `.tmp/BUNDLE-OK.md`.

A clone without the hooks configured — or a deliberate
`git commit --no-verify` — produces commits that skipped every rule,
and nothing downstream notices. What *does* travel with every pushed
commit: its tree, its parents, its message trailers (`PMO-Story:`,
`PMO-Contract-Digest:`), and the evidence files (with captured
command runs) inside the tree. Remote verification is the discipline
of re-deriving every rule those artifacts can support, and being
explicit that the rest is attestation.

## Rule classification

Every rule id the gate engine (`lib/dw_pmo/gate.py`) can emit,
classified. **Re-derivable** means a verifier with only the pushed
commits can re-check the rule mechanically. **Attested-only** means
the rule's inputs live in local-only artifacts; the trailers assert
it was checked, and the digest identifies which archived contract
certified it.

| Gate rule id | Classification | Remote re-derivation |
|---|---|---|
| `contract-missing` | attested-only | Contract text never leaves the clone. `PMO-Contract-Digest:` presence attests a contract existed. |
| `contract-facts-missing` | attested-only | Same artifact; same attestation. |
| `contract-tier-mismatch` | attested-only | Tier is a contract fact. |
| `contract-index-tree-mismatch` | attested-only | The stamped tree is in the contract; the commit's tree alone offers nothing to compare against. |
| `contract-head-mismatch` | attested-only | Stamped HEAD is a contract fact. |
| `contract-branch-mismatch` | attested-only | Branch is a contract fact; branch names are not commit properties. |
| `contract-sample-mismatch` | attested-only | Staged sample is a contract fact. |
| `contract-tests-capture-mismatch` | attested-only (portable-with-change) | The capture *reference* is a contract fact, but captured runs themselves ship in evidence files — see "Strengthening options". |
| `contract-unchecked` | attested-only | Checkbox state is contract text. |
| `contract-unknown-box` | attested-only | Same. |
| `contract-missing-box` | attested-only | Same. |
| `contract-boxes` | attested-only | Same. |
| `atomicity` | **re-derivable** | Count story files whose `**Status:**` header flips from not-done (in the first parent's tree) to a done-synonym (in the commit's tree). More than one flip without visible bundle rationale fails. |
| `contract-story-mismatch` | **re-derivable** | Every flipped story's ID must appear in the commit's `PMO-Story:` trailer. Subset semantics, mirroring the local gate: declared ⊇ flipped (phase-planning commits declare stories they do not flip — both such commits in real history, `62c5dce` and `ab66bec`, flip none). |
| `evidence-missing` | **re-derivable** | A flipped story's `evidence-story-NN.md` must be added or modified in the same commit (unpadded numbering accepted, as locally). |
| `evidence-deletion-orphans-story` | **re-derivable** | Evidence deleted while its story remains done in the commit's tree fails. |
| `orphan-evidence` | **re-derivable** | Evidence added without its story flipping, or modified while its story is not done in the commit's tree, fails. |

Two checks exist only remotely — locally they are enforced by
construction (the hooks stamp trailers mechanically), so the gate has
no rule ids for them:

| Remote-only rule id | Check |
|---|---|
| `trailer-missing` | An in-scope commit (see scoping) carries no `PMO-Contract-Digest:` trailer, or flips a story with no `PMO-Story:` trailer. |
| `trailer-format` | `PMO-Contract-Digest:` value does not match `sha256:[0-9a-f]{64}`, or a `PMO-Story:` value is not a well-formed story ID. |

The re-derivable set uses first-parent diffs. Everything the local
gate derives from HEAD-vs-index (`gate.py` steps 5–9), the verifier
derives from first-parent-tree-vs-commit-tree — same status
vocabulary (`DONE_STATUSES`), same filename grammars, same pairing
integers.

## Commit scoping

Which commits `dw verify` examines, and with which rules:

1. **Roadmap commits only.** A commit is in scope when its
   first-parent diff touches the roadmap tree (the `pm/roadmap/`
   prefix as resolved per-tree, so self-hosting layouts like
   `pmo-roadmap/pm/roadmap/` scope correctly). Commits that never
   touch the roadmap cannot flip stories or move evidence; trailer
   absence on them is not a violation (the local gate likewise
   requires only tier-appropriate contracts there, which are
   attested-only anyway).
2. **The epoch.** Trailers exist since contract v2 (`faa7de6`);
   every later commit in this repository carries the digest trailer
   (verified 2026-07-03: 48 of 65 commits carry it, with zero gaps
   after the first). All remote rules apply from the epoch onward;
   pre-epoch commits are reported as out-of-scope, never as
   violations. The epoch is auto-detected as the first commit in the
   walked range carrying a `PMO-Contract-Digest:` trailer, and can
   be pinned explicitly (`--epoch <rev>`, or `PMO_VERIFY_EPOCH` in
   `pre-commit.config`) — policy lives in configuration, the
   verifier stays mechanism. Per-sha exception lists are expressly
   rejected; if real history fails a rule, either the rule
   classification or the epoch is wrong, and the design must be
   revisited rather than patched around.
3. **Merge commits** are checked for trailer rules only; content
   rules apply to the first-parent diff of non-merge commits (the
   commits a merge introduces are themselves walked). Rebase-style
   linear history is the norm on this repository.

## Bundle visibility: the `PMO-Bundle:` trailer

The local atomicity rule accepts multi-flip commits when
`.tmp/BUNDLE-OK.md` exists — a file a remote verifier can never see.
**Decision:** the commit-msg hook stamps the bundle rationale's first
line as a `PMO-Bundle:` trailer whenever `BUNDLE-OK.md` authorizes a
multi-flip commit. Remotely, `atomicity` then reads: more than one
story flip in a commit without a `PMO-Bundle:` trailer is a
violation. This makes atomicity fully re-derivable at the cost of one
trailer line, keeps the rationale in the audit trail (today it only
survives in the local archive), and changes nothing for the
single-flip norm. History is compatible: no multi-flip commit exists
before the trailer's introduction (verified 2026-07-03 — the only
multi-story-trailer commits flip zero stories).

## Contract archives stay local in v1

Publishing archives (a `refs/notes/` ref or a tracked directory)
would let a remote verifier re-derive the digest and the stamped
facts — and would also push every certified contract's full text into
the shared repository, add a second copy of facts git already proves
(tree, parent), and make history noisier for a marginal gain: the
facts worth verifying remotely are exactly the structural ones the
tree already carries. **Decision: local-only in v1.** The digest
trailer remains the attestation anchor — anyone with the committing
clone can prove which contract certified a commit
(`git notes`-style publication can be revisited if multi-machine
audit becomes a requirement; recorded as deferred in the phase
status).

## `dw verify` CLI contract

```
dw verify [<base>..<head> | --all] [--epoch <rev>] [--porcelain]
```

- **Default range:** merge-base of the default branch and `HEAD`, to
  `HEAD` (i.e. "what this branch adds"). On the default branch
  itself, this is empty — use `--all` for the epoch-to-HEAD full
  sweep. An explicit `<base>..<head>` overrides both.
- **Read-only:** never writes to the work tree, the index, or
  `.tmp/`; safe on a bare CI checkout and on someone else's clone.
- **Output grammar** (one line per violation, greppable, mirroring
  `dw check`):

  ```
  ERROR <short-sha>: <rule-id>: <issue>
  ```

  Clean exit prints `dw verify: ok (<N> commits verified, <M> pre-epoch skipped)`.
- **`--porcelain`:** `key=value` lines per commit
  (`commit=`, `in_scope=`, `verdict=`, `rule=` on failure), matching
  the `dw gate --porcelain` idiom.
- **Exit codes**, aligned with the `dw next` convention:
  `0` = every in-scope commit verified clean; `1` = at least one
  violation (details on stdout); `2` = usage or git error (bad
  range, not a repository, truncated/shallow history that prevents
  first-parent diffing — a shallow clone must fail loudly, never
  pass silently).

## Strengthening options (deliberately not in v1)

- **Evidence-run presence:** flipped stories' evidence files carry
  captured runs (command, exit code) in-tree; a remote rule could
  require at least one exit-0 captured run in the evidence a flip
  ships. Deferred: pre-capture evidence (phases 0–5) would need its
  own epoch, and the value over `evidence-missing` is incremental.
- **Archive publication** — see above; deferred unless multi-machine
  audit becomes a requirement.
- **Signed trailers** (GPG/SSH commit signing tied to the digest):
  orthogonal to this contract; git already supports it independently.

## Proof obligations

This contract is verified by, and must stay in lockstep with:

- `tests/verify-range.sh` — fixture histories: clean, smuggled
  no-verify flip, double-flip without `PMO-Bundle:`, orphan
  evidence, missing trailer, pre-epoch grandfathering (WLA-8-02).
- `tests/dw-core-tests.py` — unit coverage of the re-derivation
  functions against synthetic commit data (WLA-8-02).
- The `verify-history` CI job in `validation.yml` running `dw verify`
  on every push and pull request (WLA-8-03).
- A rule-inventory cross-check: every rule id `gate.py` emits appears
  in the classification table above (`grep`-provable; asserted in
  the WLA-8-01 evidence and re-asserted by unit test in WLA-8-02).
