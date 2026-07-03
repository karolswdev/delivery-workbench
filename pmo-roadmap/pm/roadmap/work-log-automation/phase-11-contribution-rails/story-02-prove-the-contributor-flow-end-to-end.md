# WLA-11-02 - Prove the contributor flow end-to-end

- **Project:** work-log-automation
- **Phase:** 11
- **Status:** backlog
- **Depends on:** WLA-11-01
- **Unblocks:** WLA-11-03
- **Owner:** unassigned

## Problem

The contribution contract makes claims about what survives forks
and merges. Claims about git behavior are cheap; the squash
failure narrative in particular ("trailers get mangled,
multi-flips collapse") must be demonstrated, not asserted, before
the repo settings change bets on it.

## Scope

- **In:** `pmo-roadmap/tests/contributor-flow.sh`, a fixture
  exercising the full round trip the design doc describes:
  upstream repo with rails and a seeded roadmap; a contributor
  clone (fork stand-in) that installs nothing new (rails travel
  with the clone), branches, works one story through the gate
  (in-progress → evidence capture → done → contract → gated
  commit); `dw verify <base>..<head>` over the branch range —
  the same check CI runs on a PR — green. Then the merge legs:
  rebase-merge onto upstream main → full `dw verify --all` on
  main stays green (SHAs rewritten, trailers intact). Red leg 1:
  squash-merge a two-commit, two-story branch → verify names
  `atomicity` (or `trailer-missing` where the squash message
  dropped trailers from the final paragraph). Red leg 2:
  squash-merge a single-story branch with a fixup commit → verify
  names the trailer damage. Every red leg asserts the exact rule
  id, mirroring the design doc's narratives. Wired into CI's
  integration matrix and the shellcheck/syntax lists.
- **Out:** GitHub-side merge-button simulation (local `git
  rebase`/`git merge --squash` reproduce the same trees and
  messages; the API buttons are enforced in WLA-11-03), repo
  settings changes, docs.

## Acceptance criteria

- [ ] The green path passes: contributor branch → gated commits →
  PR-range verify → rebase onto main → `dw verify --all` green.
- [ ] Both squash red legs fail verification with the exact rule
  ids the design doc predicts.
- [ ] The suite runs standalone and in CI on both OS legs.
- [ ] No changes to verifier or gate code are needed (the rules
  as shipped catch the corruption) — or, if a gap is found, it is
  fixed in core with a unit test and called out in evidence.

## Test plan

- **Unit:** only if a core gap surfaces.
- **Integration:** `pmo-roadmap/tests/contributor-flow.sh`.
- **Manual / device:** n/a (the suite is the manual).

## Notes / open questions

- `git merge --squash` composes the message differently from
  GitHub's button (which concatenates all messages); the suite
  should reproduce GitHub's concatenation explicitly when building
  the squash commit so the red leg tests the real hazard.
