# WLA-5-09 - Harden permissions and local runtime model

- **Project:** work-log-automation
- **Phase:** 5
- **Status:** backlog
- **Depends on:** WLA-5-02, WLA-5-07
- **Unblocks:** WLA-5-10
- **Owner:** unassigned

## Problem

A local workbench with write capability is only acceptable if its runtime
boundary is boring and explicit. It must not become an arbitrary filesystem
editor, background daemon, or hidden network service.

## Scope

- **In:** `dw-workbench` runtime flags, localhost binding, repo-root allowlist,
  PMO path allowlist, CORS/default-deny behavior, no-auto-commit enforcement,
  request logging, safe shutdown, port handling, and installation decision.
- **Out:** Hosted auth, multi-user ACLs, remote tunnel support, background
  service managers, or broad filesystem browsing.

## Acceptance criteria

- [ ] Server binds to localhost by default and prints the URL and repo root.
- [ ] Server refuses to start without an explicit repo root or discoverable PMO
  roadmap.
- [ ] API rejects path traversal, absolute-path mutation requests, non-PMO
  writes, and non-allowlisted repo roots.
- [ ] API has no endpoint that stages or commits git changes.
- [ ] Port conflict handling is documented and tested.
- [ ] Install/update behavior for `dw-workbench` is decided and documented.
- [ ] Security tests fail closed when runtime config is missing or malformed.

## Test plan

- **Unit:** Path allowlist, repo allowlist, request validation, and CORS/default
  behavior tests.
- **Integration / Cypress:** Server smoke test starts against a fixture repo,
  rejects unsafe requests, and shuts down cleanly.
- **Manual / device:** Start the workbench locally and verify the printed root,
  URL, and refusal messages are clear.

## Notes / open questions

If install/update copies `dw-workbench` into target projects, that must happen
only after this story proves the runtime boundary.
