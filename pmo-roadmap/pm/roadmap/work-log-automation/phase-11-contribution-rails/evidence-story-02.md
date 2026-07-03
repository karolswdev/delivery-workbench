# Evidence - WLA-11-02

- **Story:** WLA-11-02 - Prove the contributor flow end-to-end
- **Status:** done
- **Date:** 2026-07-03

## Proof

Deliverable: `pmo-roadmap/tests/contributor-flow.sh`, wired into CI
(integration step plus the shellcheck and syntax lists). The suite
builds a real upstream with rails and a seeded roadmap, then proves
each claim of `docs/contribution-rails.md` against actual git
behavior:

- Green: a contributor clone activates the traveling rails with one
  config command (doctor green), works a story through the gate on
  a branch, passes the PR-range verify, and lands via rebase merge
  onto a drifted main — SHAs rewritten, trailers intact, full
  `dw verify --all` green afterward.
- Red 1a: the maintainer's own local gate refuses the two-flip
  squash commit outright — the corruption cannot even be created
  without `--no-verify`.
- Red 1b: forced through anyway, `dw verify` names `atomicity`,
  exactly as the design doc predicts.
- Red 2: a single-flip branch with a fixup commit, squashed with
  GitHub's message-concatenation format, leaves no valid trailers
  in the final block; `dw verify` names `trailer-missing`, and the
  suite additionally asserts git itself no longer parses a digest
  trailer from the squashed message.

No verifier or gate changes were needed: the rules as shipped catch
both corruption modes. One doc correction came out of the fixture:
a fresh clone needs `git config core.hooksPath .githooks` before
the rails gate anything, so the design doc's "already gates
commits" phrasing was tightened to name the activation step.


### Captured run — 2026-07-03T23:25:10Z

- **Command:** `bash -c set -e -o pipefail; bash pmo-roadmap/tests/contributor-flow.sh 2>&1 | grep -E "^(green|red|contributor-flow)"`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 0e98138c3ea3c9b0e9567eaebe5934d7d92585db

```text
green path: ok (gated branch, PR-range verify, rebase merge, main verify green)
red 1a: the maintainer's own gate refuses the two-flip squash
red 1b: forced two-flip squash lands and dw verify names atomicity
red 2: fixup squash displaces trailers mid-body and dw verify names trailer-missing
contributor-flow.sh: ok
```
