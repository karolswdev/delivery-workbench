# WLA-29-02 - Build the symbol and structure map

- **Project:** work-log-automation
- **Phase:** 29
- **Status:** done
- **Depends on:** WLA-29-01
- **Unblocks:** WLA-29-03, WLA-29-04
- **Owner:** unassigned

## Problem

The first derived fact worth having is the map: which symbols exist, where
they are defined, which modules contain them, and which tests exercise them.
The studied prototype builds this once per repository and it is the backbone
of both its grounding pass and its retrieval — and its static layer needs no
model at all. Ours must not use one: the knowledge core is contracted
deterministic, stdlib-only, and offline.

Everything downstream leans on this story. Grounding (WLA-29-03) verifies
story hints against the map; packets (WLA-29-04) resolve verified locations
through it. If the map is stale or partial, both inherit the defect, so
freshness and honest coverage reporting matter more than richness.

## Scope

- **In:** deterministic extraction of a symbol map for Python sources using
  `ast` (module, class, function, method: name, file, line span), a module
  inventory (files, sizes, imports), and a test map linking test files to the
  symbols they reference; storage as derived facts under the WLA-29-01
  contract, keyed to the repofacts index tree; incremental refresh that
  re-extracts only files whose blobs changed between index trees; a
  greppable-fallback note in the map for non-Python files (shell, JS) rather
  than pretending coverage; read-only surfaces `dw knowledge map` /
  `dw knowledge refresh` on the CLI and one MCP read tool with the identical
  model.
- **Out:** parsing non-Python languages structurally (recorded as
  out-of-coverage, not silently absent); retrieval scoring (WLA-29-04);
  LLM-interpreted architecture views; watching the filesystem — refresh is
  explicit or freshness-triggered, never a daemon.

## Acceptance criteria

- [ ] Extraction over this repository completes with stdlib alone, produces a
  map covering every tracked `.py` file, and records files it cannot parse as
  named gaps rather than omitting them.
- [ ] The map states the index tree it was computed from; reading it under a
  different index tree either refuses or triggers incremental refresh, per
  the WLA-29-01 freshness rule — a planted stale read cannot return an
  answer.
- [ ] Incremental refresh re-extracts only changed files: a one-file edit is
  proven to re-parse one file, not the tree.
- [ ] The test map resolves at least the core suite: for a sampled set of
  `dw_pmo` symbols, the tests that reference them are found and correct.
- [ ] `dw knowledge map` and the MCP tool return the same versioned model
  byte-for-byte in the established interop style, and both are read-only.
- [ ] Extraction is deterministic: two runs over the same index tree produce
  identical bytes.

## Test plan

- **Unit:** extractor on fixture sources (nested classes, async defs, name
  collisions across modules); incremental diff selection; determinism
  (byte-identical double run).
- **Integration:** `dw evidence capture` of a full extraction over this
  repository plus a one-file-edit incremental refresh; CLI/MCP parity in the
  existing parity-test style.
- **Manual:** spot-check five symbols across `dw_pmo` for correct file/line
  and test attribution.

## Notes / open questions

Coverage honesty is the point of the gaps list: this repository is mostly
Python, but `dw` itself is a large shell entrypoint and `app.js` is 346 KB of
JavaScript. The map must say "out of structural coverage, use `git grep`"
about those, because WLA-29-03's grounding falls back to `git grep` exactly
where the map ends.

Line spans move on every edit; that is why freshness is index-tree-keyed
rather than time-based, and why nothing may cache a location across a
derivation boundary.

Implemented as `dw_pmo/symbol_map.py` (pure `ast` extraction) plus
`dw_pmo/repository_map.py` (derived-fact assembly through
`DerivedFactStore`). Blob enumeration goes through two new
derivation-scoped repofacts (`tracked_files`, `blob_content`) rather than
any private git access, keeping the WLA-28 boundary intact. Measured over
this repository at delivery: 771 tracked files, 147 Python files, 4,388
symbols, 624 named gaps; extraction determinism proven at 2,680,222
identical bytes across double runs; incremental refresh re-parsed exactly
one file for a one-file edit. CLI (`dw knowledge map|refresh`) and MCP
(`dw_knowledge_map`) emit identical canonical JSON, parity-tested. Ten new
tests in `repository_map_tests.py`; suite 547 → 559 green on both the
desk interpreter and the 3.9 floor.
