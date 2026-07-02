# WLA-5-10 - Ship documentation tests and adoption path

- **Project:** work-log-automation
- **Phase:** 5
- **Status:** done
- **Depends on:** WLA-5-03, WLA-5-04, WLA-5-05, WLA-5-07, WLA-5-08, WLA-5-09
- **Unblocks:** Phase 5 close
- **Owner:** unassigned

## Problem

The workbench is not complete until a future human or agent can install/run it,
understand its safety model, validate it, and see proof that the PMO roadmap
dogfooded the feature. Documentation and tests are part of the product, not a
cleanup task.

## Scope

- **In:** README updates, command examples, API contract documentation,
  screenshots or equivalent artifacts, test suite integration, install/update
  notes, adoption guidance for consumer repos, Phase 5 evidence files, final
  summary, and requirement audit.
- **Out:** Hosted documentation site, marketing page, remote service docs, or
  examples that bypass preview/diff/apply.

## Acceptance criteria

- [ ] `pmo-roadmap/README.md` documents starting and using the local workbench.
- [ ] API and mutation contract docs explain read endpoints, preview/apply, and
  refusal states.
- [ ] Validation workflow docs tell agents which command output proves health.
- [ ] UI tests and server/API tests are wired into the repo validation path.
- [ ] Adoption guidance explains source-of-truth rules, permission boundaries,
  work-log caveats, and no-auto-commit behavior.
- [ ] Phase 5 story evidence files are complete for all done stories.
- [ ] `final-summary.md` maps Phase 5 requirements to files, tests, and command
  output.
- [ ] `dw check work-log-automation` passes at phase close.

## Test plan

- **Unit:** Documentation snippets are checked where practical.
- **Integration / Cypress:** Full validation command matrix includes core, CLI,
  API/server, UI, permission, and PMO roadmap checks.
- **Manual / device:** A cold agent follows the docs to start the workbench,
  inspect context, preview a mutation in a fixture repo, and verify no hidden
  state is created.

## Notes / open questions

The final summary must be written as an audit, not a celebration. It should
name residual risks and the exact command output that proves completion.
