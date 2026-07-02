# WLA-5-07 - Build safe mutation preview and diff workflow

- **Project:** work-log-automation
- **Phase:** 5
- **Status:** done
- **Depends on:** WLA-5-02, WLA-5-06
- **Unblocks:** WLA-5-09, WLA-5-10
- **Owner:** unassigned

## Problem

Structured forms are not enough. Before any write, the operator must see the
exact PMO files that will change, the diff, the validation result, and whether
the preview is still current. The apply step must reject stale previews and
leave no partial PMO edits.

## Scope

- **In:** Preview endpoint/UI, deterministic mutation fingerprints, diff view,
  stale preview refusal, apply endpoint/UI, rollback error reporting,
  post-apply reparse/revalidation, and changed-file summary.
- **Out:** Git commit creation, staging files, arbitrary patch application, or
  bypassing core mutation plans.

## Acceptance criteria

- [ ] Preview response names every file that would be created or updated.
- [ ] Preview response includes validation issues before write and projected
  validation issues after write where feasible.
- [ ] Diff view renders new, changed, and unchanged-owned files distinctly.
- [ ] Apply requires a preview fingerprint and refuses when source files changed
  after preview.
- [ ] Apply uses rollback-protected core writes and reports any rollback.
- [ ] Post-apply state reparses the roadmap and shows validation results.
- [ ] Repeating a no-op semantic mutation produces an empty or explicitly
  idempotent diff.

## Test plan

- **Unit:** Mutation fingerprint, stale preview, no-op diff, and rollback-path
  tests.
- **Integration / Cypress:** Preview/apply flow for create story, done with
  evidence, attach evidence, and close phase against a temporary repo.
- **Manual / device:** Confirm diff readability and refusal states on desktop
  and mobile.

## Notes / open questions

The preview token should be deterministic enough for tests but robust enough to
catch source-file drift between preview and apply.
