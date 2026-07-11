# Phase 19 - The front door — open-source readiness, docs caught up, v1.13.0

**Last updated:** 2026-07-11.

## Goal

A stranger arriving from PyPI, Homebrew, or GitHub meets a package
that states its case: complete metadata, a README that matches the
shipped surface, and phases 16-18 published as v1.13.0. Owner
direction: release the unreleased work on main, refresh the project
documentation, and take open-source readiness seriously — this is a
published pip package. An audit ran first (2026-07-11, findings in
WLA-19-01/02 scopes); it found no blockers, so this phase is the
should-fix list plus the release, in that order — readiness and docs
land BEFORE the tag so v1.13.0 ships them.

## Scope

- **In:** `pyproject.toml` metadata completion (urls, license
  classifier, author contact), LICENSE name consistency, README
  badges; README currency against the shipped phase 16-18 surface
  (MCP tool census, CLI verb table, docs links, phase count, the
  hardcoded current-version line); the v1.13.0 release per
  docs/distribution.md (bump, CHANGELOG section from the written
  Unreleased text, tag, GitHub Release, PyPI via trusted publishing,
  formula stamp, tap mirror).
- **Out:** new capabilities or CLI surface; docs/*.md rewrites beyond
  currency (mcp.md and interop.md verified current by the audit);
  announcement posts; docs site (parked candidate stays parked);
  packaging layout changes (MANIFEST.in verified deliberate).

## Exit criteria (evidence required)

- [x] PyPI-facing metadata is complete: `[project.urls]` carries
  Repository, Changelog, and Issues; the license ships as the SPDX
  expression `License-Expression: MIT` (upgraded from the audit's
  classifier suggestion — setuptools deprecates classifiers, see
  the story); author contact set; LICENSE holder name matches
  pyproject; README carries CI + PyPI + license badges
  (WLA-19-01 — [evidence](./evidence-story-01.md): 208 core tests,
  package smoke, and a METADATA inspection, all green).
- [x] The README matches the shipped surface: twelve MCP tools
  listed, `dw board` / `dw holds` / `dw story show` in the CLI
  table, `docs/interop.md` linked, phase count current, and the
  version line no longer hand-maintained ahead of the parity tests
  (WLA-19-02 — [evidence](./evidence-story-02.md): 208 core tests
  green; the census walk derives the 12 tools from mcpserver.py
  and finds each in the README; both rot-prone literals grep
  empty).
- [ ] v1.13.0 is live on every channel: annotated tag, GitHub
  Release with hash-verified artifacts, PyPI at 1.13.0 via the
  release workflow, formula stamped with the published wheel's
  sha256, tap mirrored, cold install reports 1.13.0 (WLA-19-03).

## Story status

| ID | Story | Status | Story file | Evidence |
|---|---|---|---|---|
| WLA-19-01 | The package states its case — metadata and community polish | done | [story-01-package-states-its-case](./story-01-package-states-its-case.md) | [evidence-story-01](./evidence-story-01.md) |
| WLA-19-02 | The README catches up with the shipped surface | done | [story-02-readme-catches-up](./story-02-readme-catches-up.md) | [evidence-story-02](./evidence-story-02.md) |
| WLA-19-03 | Release v1.13.0 | backlog | [story-03-release-v1-13-0](./story-03-release-v1-13-0.md) | - |

## Where we are

2/3. WLA-19-01 shipped the metadata (five Project-URLs, SPDX
license, contact, badges); WLA-19-02 caught the README up with
phases 16-18 (twelve MCP tools, the board/holds/story-show verbs,
the interop contract linked, the rot-prone version and phase-count
literals removed). Next: WLA-19-03 cuts v1.13.0.

## Active risks

| Risk | Likelihood | Mitigation | Stop signal |
|---|---|---|---|
| Unguarded version surfaces lag the bump (formula url/sha256, README version line) | medium | WLA-19-02 removes or automates the README line; the release story names both explicitly | a released surface still reads 1.12.0 |
| Metadata edits break the build or the parity family | low | full battery + both distribution smokes run at the release commit per the ritual | red package-smoke |
| CHANGELOG Unreleased text drifts from what actually ships | low | the section is already written and phases 16-18 are closed; the release story only renames and dates it | a phase link 404s |

## Decisions made (this phase)

- 2026-07-11 - Phase scaffolded with `dw phase create` - keeps roadmap structure consistent - CLI.
- 2026-07-11 - Readiness and docs land before the tag - v1.13.0 ships the fixes rather than recreating unreleased-on-main - sequencing.
- 2026-07-11 - Audit should-fixes only; nice-to-haves adopted are badges and author contact, the rest (per-minor Python classifiers, `.hs/context.md` tracking) deferred - keep the phase one sitting - scope.

## Decisions deferred

- Automating the README version line into the parity family vs
  removing it - decided inside WLA-19-02 - default: remove the
  hand-maintained number.
- Per-minor `Programming Language :: Python :: 3.x` classifiers -
  trigger: a floor change or a user asking - default: the plain
  `:: 3` classifier plus `requires-python` states it.
- `.hs/context.md` tracked-state question - trigger: rider state
  churning in diffs - default: stays tracked (install-managed
  dogfood state, not scratch).
