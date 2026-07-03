# WLA-9-03 - Prove the consumer upgrade path

- **Project:** work-log-automation
- **Phase:** 9
- **Status:** backlog
- **Depends on:** WLA-9-02
- **Unblocks:** WLA-9-05
- **Owner:** unassigned

## Problem

Distribution makes upgrades routine, and upgrades are where vendored
rails can rot: a consumer repo adopted at v1.5.0 has no `verify.py`
in its snapshot, no `PMO-Bundle:` stamping, and a pre-Phase-8 agent
block. `update.sh` claims to bring rails forward; nothing proves it
end-to-end against a genuinely old snapshot, and nothing tells a
consumer that their rails are stale in the first place.

## Scope

- **In:** An upgrade fixture built from the real v1.5.0 tag: adopt a
  scratch repo using `git worktree`/archive of `v1.5.0`, ship a
  gated commit there with the old rails, then upgrade via the
  packaged/update path from current source and prove: hooks and
  `dw_pmo` refreshed (`dw verify` now available and passing over the
  fixture's mixed-version history), `pm/roadmap/<slug>/` content and
  `pre-commit.config`/`pre-commit.local` untouched, agent-docs block
  refreshed, doctor green. Staleness visibility: `dw doctor` (or
  `update.sh --check`) reports the vendored snapshot's version
  against the distributing package/source version so consumers learn
  they are behind. Automate as `pmo-roadmap/tests/upgrade-path.sh`.
- **Out:** Downgrades, migrations of roadmap *content* (Markdown is
  forward-compatible by design), multi-version upgrade chains beyond
  v1.5.0 → current.

## Acceptance criteria

- [ ] The v1.5.0-adopted fixture upgrades to current rails with
  project content and config provably untouched (byte-compare), and
  `dw verify --all` passes over its mixed-version history.
- [ ] A gated commit ships in the fixture after upgrade (the gate
  still works with the refreshed rails).
- [ ] Version staleness is visible to the consumer via a documented
  command, asserted in the test.
- [ ] `upgrade-path.sh` wired into `validation.yml`.

## Test plan

- **Unit:** version-report formatting if any new core code appears.
- **Integration:** `pmo-roadmap/tests/upgrade-path.sh` (v1.5.0 →
  current), full battery green.
- **Manual / device:** run the upgrade on the WLA-8-04 fridgr clone
  (its rails predate the PMO-Bundle stamping).

## Notes / open questions

- The v1.5.0 tag exists locally; the fixture must not need network.
- If update.sh gaps are found (files added since v1.5.0 that it
  does not copy), fixing them is in-scope here — that is the point
  of the story.
