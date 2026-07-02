# WLA-7-07 - OSS release preparation and versioned release

- **Project:** work-log-automation
- **Phase:** 7
- **Status:** backlog
- **Depends on:** WLA-7-02, WLA-7-03, WLA-7-04, WLA-7-05, WLA-7-06
- **Unblocks:** Phase 7 close
- **Owner:** unassigned

## Problem

The repo has MIT LICENSE and SECURITY.md but no CONTRIBUTING guide,
code of conduct, issue/PR templates, changelog, or versioned release.
An OSS-ready repo tells contributors how to work, tells adopters what
changed, and ships a tag they can pin.

## Scope

- **In:** CONTRIBUTING.md (dev setup, the validation matrix, how
  work ships through the framework's own gate — contributors use the
  rails), CODE_OF_CONDUCT.md, issue and PR templates that ask for
  evidence, a CHANGELOG.md derived from the phase final summaries,
  version alignment (dw --version, plugin version, changelog) from
  one source, a v1 git tag and GitHub release with notes, and repo
  metadata review (description, topics, social preview wiring).
- **Out:** Package-registry publishing (brew/pip/npm), governance
  documents beyond CoC, roadmap promises.

## Acceptance criteria

- [ ] CONTRIBUTING.md walks a contributor from clone to a gated
  commit using the framework itself, and its commands run as printed
  (captured).
- [ ] Issue/PR templates render on GitHub and request reproduction/
  evidence in framework vocabulary.
- [ ] CHANGELOG.md summarizes each phase from its final summary with
  links; the version is defined once and asserted by a test
  everywhere it appears.
- [ ] A signed-off v1.x tag and GitHub release exist with notes
  (captured `gh release view`).
- [ ] `dw check` green and the full validation matrix green at
  release; the release commit itself passes the gate.

## Test plan

- **Unit:** version-single-source assertion in the core suite.
- **Integration:** docs-lint over the new documents; template render
  check via gh api where practical.
- **Manual / device:** view templates and release on GitHub.
