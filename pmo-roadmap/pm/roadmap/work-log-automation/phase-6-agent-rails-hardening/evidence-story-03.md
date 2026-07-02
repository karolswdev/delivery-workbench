# Evidence - WLA-6-03 - Ship verified contract v2 with durable audit trail

- **Story:** [story-03-verified-contract-v2](./story-03-verified-contract-v2.md)
- **Status:** done
- **Date:** 2026-07-02

## What shipped

- `dw_pmo/contract.py`: `dw contract new` generates `.tmp/CONTRACT.md`
  from `templates/CONTRACT.md.tmpl` (embedded fallback), stamping
  branch, HEAD, `git write-tree` index tree, UTC timestamp, the staged
  file sample, and the story ID(s) auto-detected from the staged diff
  (flipped stories always declared; `--story` can add more). Boxes are
  emitted unchecked — flipping them remains the certification act.
  `dw contract digest` and `dw contract trailers` complete the CLI.
  Shared git plumbing moved to `dw_pmo/gitio.py`.
- Gate v2 (`dw_pmo/gate.py`): re-derives every stamped fact and blocks
  on mismatch with the fact named — `contract-index-tree-mismatch`
  (the freshness proof; mtime checking is deleted along with its
  BSD/GNU seam), `contract-head-mismatch`, `contract-branch-mismatch`,
  `contract-sample-mismatch`, `contract-facts-missing` (v1-style
  contracts are refused with "generate with dw contract new").
  Checkboxes verify **by rule title** against the rules doc's
  contract-template fence — unknown boxes fail, missing required boxes
  fail, project extension boxes are picked up by generator and gate
  alike — retiring `EXPECTED_BOXES` count-checking except as a
  fallback for repos without a rules doc. Flipped story IDs must be
  declared in the Story fact (`contract-story-mismatch`).
- Durable trail: a new `hooks/commit-msg` shim stamps `PMO-Story:` and
  `PMO-Contract-Digest:` (sha256 of the exact contract bytes) trailers
  via `git interpret-trailers` from the live contract — fail-closed
  when stamping fails, pass-through for contract-less flows (merges).
  `hooks/post-commit` archives the contract plus any `BUNDLE-OK.md`
  rationale under `.git/pmo-contract-archive/<sha>` and only then
  clears them; `hooks/pre-commit` no longer deletes the contract, so
  an aborted commit leaves it in place for the retry.
- `dw context --trace` commits now carry `pmo_story` and
  `contract_digest` fields, completing the chain
  story -> evidence -> commit -> contract digest -> work-log entry.
- Distribution: install.sh/update.sh ship `.githooks/commit-msg` with
  the same collision policy as post-commit; docs updated
  (PMO-CONTRACT.md v2 semantics and legacy EXPECTED_BOXES note,
  framework README gate/contract section and porcelain key list);
  `demos/scripts/write-demo-contract.sh` and both test harnesses now
  generate contracts with `dw contract new`.

## Command output

Unit suite — 36 tests including the tamper matrix (one per stamped
fact: tree+touch, HEAD, branch, invented sample; facts-missing on a
v1-style contract; unknown/missing/extension box titles from a rules
doc; story-declaration tamper; digest format and trailer stamping):

```text
$ python3 pmo-roadmap/tests/dw-core-tests.py
Ran 36 tests in 5.763s
OK
```

Parity suite — extended with the v2 scenarios the story required
(S17 stale index tree then `touch` still blocked, S18 invented staged
sample, S19 unknown checkbox, S13 reworked as the template-extension
seam, S20 story-declaration tamper plus trailer/archive verification,
S21 aborted-commit survival, S9 bundle-rationale archive):

```text
$ pmo-roadmap/tests/gate-parity.sh
gate-parity.sh: ok
$ pmo-roadmap/tests/work-log-mvp.sh
work-log-mvp.sh: ok        (generator-based contracts through the full
                            pre-commit -> commit-msg -> post-commit
                            lifecycle, including abort and amend)
$ pmo-roadmap/tests/roadmap-cli.sh ; pmo-roadmap/tests/adoption-discovery.sh
roadmap-cli.sh: ok
adoption-discovery.sh: ok
$ demos/scripts/prepare-commit-demo.sh
demo-prep ok               (real gated commit via the new generator)
```

Manual proof on this repository (test plan): the implementation commit
was authored with `dw contract new` (it auto-declared WLA-6-03 from
the staged story file) and verified end to end:

```text
$ git log -1 --format='%(trailers:key=PMO-Story,valueonly)'
WLA-6-03
$ git log -1 --format='%(trailers:key=PMO-Contract-Digest,valueonly)'
sha256:7e3a84afedf884dd3e001aba424258923d5f19cab077b7d3814bec163914608f
$ ls .git/pmo-contract-archive/faa7de61f4133c28a82a5f7a63ff123c09f9fadf/
CONTRACT.md
$ sha256(.git/pmo-contract-archive/faa7de6…/CONTRACT.md)
MATCH: trailer == sha256(archived contract)
$ .tmp/
gone (archived and cleared by post-commit)
```

Trace chain (acceptance #6), WLA-6-03's story context after the
implementation commit:

```json
{"sha": "faa7de61f4133c28a82a5f7a63ff123c09f9fadf",
 "pmo_story": "WLA-6-03",
 "contract_digest": "sha256:7e3a84afedf884dd3e001aba424258923d5f19cab077b7d3814bec163914608f",
 "subject": "Implement contract v2: stamped facts, trailers, and the archive"}
```

## Acceptance criteria check

- [x] `dw contract new` stamps real branch/HEAD/index-tree/sample;
  tampering with any stamped fact blocks with the fact named (unit
  tamper matrix + parity S18/S20).
- [x] Contract reuse after restaging is blocked by index-tree mismatch;
  `touch` no longer refreshes staleness (unit regression + parity S17,
  both CI-run).
- [x] Unknown checked boxes fail; required boxes verify by title
  including project extensions; `EXPECTED_BOXES` count-checking retired
  to a no-rules-doc fallback (unit + parity S13/S19).
- [x] Gated commits carry `PMO-Story:`/`PMO-Contract-Digest:` trailers
  and `.git/pmo-contract-archive/<sha>` holds the exact contract
  (digest match proven above) plus the bundle rationale (parity S9).
- [x] An aborted commit leaves `.tmp/CONTRACT.md` intact and the retry
  passes without re-authoring (parity S21 + work-log-mvp abort flow).
- [x] `dw context --trace` surfaces `pmo_story` and `contract_digest`
  per commit (output above).

## Notes

The deferred decision stands: the archive is local
(`.git/pmo-contract-archive/`) plus the public digest trailer;
mirroring into a committed audit file is revisited after dogfooding.
Pre-v2 commits in this repo's history carry no digest trailers —
recorded as expected history, not retrofitted.
