# Evidence - WLA-8-01

- **Story:** WLA-8-01 - Define the remote verification contract
- **Status:** done
- **Date:** 2026-07-03

## Proof

Deliverable: `docs/remote-verification.md` — the remote verification
contract. It classifies all 17 gate rule ids (plus 2 remote-only
trailer rules) as re-derivable vs attested-only, specifies the
`dw verify` CLI (range semantics, epoch scoping, output grammar,
exit codes 0/1/2, `--porcelain`), and records three decisions:
`PMO-Bundle:` trailer makes atomicity fully re-derivable, contract
archives stay local-only in v1, and the verification epoch is
auto-detected from the first digest-trailer commit (`faa7de6`) with
per-sha exception lists rejected. Decisions are mirrored in
`current-phase-status.md`. The classification is kept honest by a
new doc-parity check, `pmo-roadmap/tests/remote-verification-doc-check.py`.

Empirical grounding (2026-07-03 survey of this repo's history):
65 commits, 48 carry `PMO-Contract-Digest:` with zero gaps after
`faa7de6`; the only multi-story-trailer commits (`62c5dce`,
`ab66bec`) flip zero stories, so subset semantics and the bundle
trailer are history-compatible.

The first captured run below failed on its own garbled inline
extraction regex (it matched a spurious 18th id, "ule"); the check
was moved into the repo as the doc-parity test and the second run is
the authoritative pass, chained with docs-lint.

### Captured run — 2026-07-03T15:52:57Z

- **Command:** `bash -c python3 -c "
import re,sys
src=open(str(chr(46))+chr(47)+chr(46)+str()+\"githooks/dw_pmo/gate.py\".lstrip()) if False else open(\".githooks/dw_pmo/gate.py\")
src=src.read()
doc=open(\"docs/remote-verification.md\").read()
ids=sorted(set(re.findall(r\"failed\(\s*.([a-z-]+).\", src)))
missing=[i for i in ids if (chr(96)+i+chr(96)) not in doc]
print(\"gate rule ids classified:\", len(ids))
assert len(ids)==17, ids
if missing: print(\"MISSING:\", missing); sys.exit(1)
print(\"all 17 gate rule ids appear in docs/remote-verification.md classification\")
" && bash pmo-roadmap/tests/docs-lint.sh`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** dd84d532945ceae691ee8109f8dbc208df91e5bf

```text
Traceback (most recent call last):
  File "<string>", line 9, in <module>
    assert len(ids)==17, ids
           ^^^^^^^^^^^^
AssertionError: ['atomicity', 'contract-boxes', 'contract-branch-mismatch', 'contract-facts-missing', 'contract-head-mismatch', 'contract-index-tree-mismatch', 'contract-missing', 'contract-missing-box', 'contract-sample-mismatch', 'contract-story-mismatch', 'contract-tests-capture-mismatch', 'contract-tier-mismatch', 'contract-unchecked', 'contract-unknown-box', 'evidence-deletion-orphans-story', 'evidence-missing', 'orphan-evidence', 'ule']
gate rule ids classified: 18
```

### Captured run — 2026-07-03T15:53:26Z

- **Command:** `bash -c python3 pmo-roadmap/tests/remote-verification-doc-check.py && bash pmo-roadmap/tests/docs-lint.sh`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** dd84d532945ceae691ee8109f8dbc208df91e5bf

```text
remote-verification-doc-check: ok (17 gate rule ids + 2 remote-only ids classified in docs/remote-verification.md)
docs-lint: ok (150 markdown files)
docs-lint.sh: ok (0s)
```
