# WLA-7-06 - Wire documentation CI checks

- **Project:** work-log-automation
- **Phase:** 7
- **Status:** done
- **Depends on:** WLA-7-02
- **Unblocks:** WLA-7-07
- **Owner:** unassigned

## Problem

Docs rot silently: links break, commands drift from reality, and no
gate notices. The same verification-over-trust principle that runs
the commit gate must run the documentation.

## Scope

- **In:** A docs-lint suite: internal link/anchor checker over every
  Markdown file (including the roadmap tree), image-reference
  checker, a doc-snippet smoke that executes the quickstart command
  blocks marked as runnable and compares exit codes, canon-lint
  integration, and CI wiring on both OS legs where feasible.
- **Out:** External-URL liveness polling (flaky in CI; local-only
  mode acceptable), prose style linting.

## Acceptance criteria

- [ ] A broken internal link or missing image anywhere in the repo
  fails CI with a greppable `ERROR <file>: <target>` line.
- [ ] Runnable-marked snippets in the quickstarts execute in CI and
  fail on nonzero exit.
- [ ] The checker is fast (<30s) and zero-dependency (bash/python
  stdlib), consistent with repo conventions.
- [ ] Existing docs pass clean at landing (fix or annotate every
  finding).

## Test plan

- **Unit:** checker self-tests on fixture files (good and broken).
- **Integration:** the docs-lint suite in validation.yml.
- **Manual / device:** introduce a broken link locally; watch it die.
