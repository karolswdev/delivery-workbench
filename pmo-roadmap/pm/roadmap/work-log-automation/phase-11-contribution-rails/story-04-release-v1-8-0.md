# WLA-11-04 - Release v1.8.0

- **Project:** work-log-automation
- **Phase:** 11
- **Status:** backlog
- **Depends on:** WLA-11-03
- **Unblocks:** (optional)
- **Owner:** unassigned

## Problem

The contribution contract, the contributor-flow proof, and the
policy enforcement change what the project promises to outside
contributors. That belongs in a versioned release with the same
machinery as the last three.

## Scope

- **In:** Bump `dw_pmo.__version__` to 1.8.0 with the plugin
  manifest and formula url in lockstep (sha256 reset to
  placeholder until publication); CHANGELOG section for Phase 11
  linking the final summary; parity family and full battery green
  at 1.8.0; both distribution smokes re-run; annotated `v1.8.0`
  tag on the release commit; phase close with final summary in the
  same commit as this story's flip. Publication follows the
  standing authorization: push main and the tag, GitHub Release
  with hash-verified artifacts (PyPI publishes itself via the
  release workflow now that the trusted publisher exists), stamp
  the published wheel's sha256 into the formula, update the public
  tap, upgrade the local brew install.
- **Out:** New capabilities, announcement posts.

## Acceptance criteria

- [ ] Every version surface reports 1.8.0 under the parity tests;
  full battery and both smokes green at the release commit.
- [ ] `git tag -l v1.8.0` shows the annotated tag; `dw verify
  --all` passes at it.
- [ ] The release workflow publishes to PyPI without manual steps
  (first fully automatic release).
- [ ] Phase 11 final summary closes the phase in this commit.

## Test plan

- **Unit:** parity family at 1.8.0.
- **Integration:** full `pmo-roadmap/tests/` battery.
- **Manual / device:** post-publication install checks (pip and
  brew report 1.8.0).

## Notes / open questions

- First release where PyPI publication should require zero manual
  action; if it does not, that is a finding to record.
