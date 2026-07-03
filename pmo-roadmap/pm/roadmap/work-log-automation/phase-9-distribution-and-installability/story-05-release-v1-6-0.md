# WLA-9-05 - Release v1.6.0

- **Project:** work-log-automation
- **Phase:** 9
- **Status:** backlog
- **Depends on:** WLA-9-03, WLA-9-04
- **Unblocks:** (optional)
- **Owner:** unassigned

## Problem

Phases 8 and 9 shipped remote verification and distribution — both
user-visible capabilities that v1.5.0 does not have. The release
machinery from Phase 7 (version single-sourced from
`dw_pmo.__version__`, test-asserted against `dw --version`, the
plugin manifest, and the CHANGELOG) must absorb the new
`pyproject.toml` and formula surfaces and produce a tagged v1.6.0.

## Scope

- **In:** Bump `dw_pmo.__version__` to 1.6.0; CHANGELOG entries for
  Phase 8 (remote verification and adoption) and Phase 9
  (distribution) linking both final summaries; version-parity test
  extended to every surface that now carries a version
  (`pyproject.toml`, `Formula/delivery-workbench.rb`, plugin
  manifest, CHANGELOG, `dw --version`); full test battery green;
  rebuild the package artifacts at 1.6.0 and re-run the package and
  formula smokes; annotated tag `v1.6.0` created locally. Phase 9
  closes with its final summary in the same commit as this story's
  flip.
- **Out:** Pushing commits/tags to GitHub, publishing to PyPI or a
  public tap, GitHub Release notes (all user-triggered; the release
  commit and tag make them one command each).

## Acceptance criteria

- [ ] Every version surface reports 1.6.0 and the parity test proves
  it (red if any surface lags).
- [ ] CHANGELOG covers phases 8 and 9 in the house style, links both
  final summaries, docs-lint clean.
- [ ] Package + formula smokes pass against the 1.6.0 artifacts.
- [ ] `git tag -l v1.6.0` shows an annotated tag whose target is the
  release commit; `dw verify --all` passes ending at that commit.

## Test plan

- **Unit:** extended version-parity assertions.
- **Integration:** full `pmo-roadmap/tests/` battery plus the two
  new smokes.
- **Manual / device:** `git show v1.6.0` inspection.

## Notes / open questions

- Tag locally only; pushing the tag publishes the release surface
  and stays with the user.
