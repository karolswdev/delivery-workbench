# Phase 19 Final Summary

**Status:** complete (3/3).
**Date:** 2026-07-11.

## Outcome vs exit criteria

All three exit criteria met, each with captured evidence:

1. **PyPI-facing metadata complete** (WLA-19-01): five
   Project-URLs (Homepage, Documentation, Repository, Changelog,
   Issues), the license as an SPDX expression
   (`License-Expression: MIT`, Metadata-Version 2.4,
   `setuptools>=77`), author contact, LICENSE holder normalized to
   "Karol Sane", three badges on the README. Proven by 208 core
   tests, the package smoke, and a METADATA inspection of a fresh
   wheel.
2. **The README matches the shipped surface** (WLA-19-02): twelve
   MCP tools (census derived from `mcpserver.py` in the evidence
   walk, not hand-counted), CLI rows for `dw board` / `dw holds` /
   `dw story show`, parked work and the receipts-and-links walk in
   prose, `#/board` named, `docs/interop.md` linked, and the two
   rot-prone literals removed (hand-maintained version line, phase
   count).
3. **v1.13.0 released** (WLA-19-03): full battery + both
   distribution smokes green at 1.13.0 with every version surface
   in lockstep at the release commit; tag, GitHub Release, PyPI
   via the trusted publisher, formula stamp, and tap mirror follow
   under the standing authorization, with post-publication
   confirmations recorded in the stamp commit.

## What shipped

The phase began with an open-source-readiness audit of everything
a stranger meets (packaging, community files, docs currency,
hygiene, CI, version surfaces). It found **no blockers** and a
short should-fix list; this phase is that list, shipped, plus the
release of phases 16-18 that had been sitting closed-but-unreleased
on main. Sequencing was the one real decision: readiness and docs
landed BEFORE the tag so v1.13.0 ships them.

Notable in-flight find: the audit suggested the MIT license
*classifier*, but the first build surfaced setuptools deprecating
license classifiers and the license TOML table outright (support
ends 2027-02-18) — the story shipped the SPDX expression instead.
The package now publishes Metadata-Version 2.4.

## Deliberately deferred

- Per-minor `Programming Language :: Python :: 3.x` classifiers
  (floor change or user demand triggers).
- `.hs/context.md` tracked-state question (stays tracked as
  install-managed dogfood state).
- Docs site and announcement post (parked candidates stay parked).

## Audit trail

| Story | Evidence |
|---|---|
| WLA-19-01 | [evidence-story-01](./evidence-story-01.md) |
| WLA-19-02 | [evidence-story-02](./evidence-story-02.md) |
| WLA-19-03 | [evidence-story-03](./evidence-story-03.md) |
