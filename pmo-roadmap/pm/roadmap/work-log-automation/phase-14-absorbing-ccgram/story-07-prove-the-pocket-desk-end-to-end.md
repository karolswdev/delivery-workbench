# WLA-14-07 - Prove the pocket desk end-to-end

- **Project:** work-log-automation
- **Phase:** 14
- **Status:** backlog
- **Depends on:** WLA-14-02..06.
- **Unblocks:** phase close.
- **Owner:** unassigned

## Problem

Six stories of absorbed craft prove nothing until the whole pocket
desk runs one honest day: topics bound to real repos, a hook-fired
question arriving in a second, a real back-and-forth conversation
with an agent — typed, not tapped — a toolbar Esc, a file through
the locks, and the gate still refusing dishonesty in front of all
of it. Phase 13's live hour found four real bugs the fixtures
missed; this story exists because that will happen again.

## Scope

- **In:** (a) The live phone leg, evidence-captured with
  screenshots under `assets/`: a forum group with two bound repo
  topics; a hook-pushed question answered by just typing; a
  multi-turn conversation flowing through a bound session; the
  live view refreshing in place; a toolbar press; `/send`
  delivering an evidence file and refusing a planted secret; a
  story flip and the crown case, once more, from a topic. (b)
  Architecture fitness tests, the ccgram runner-up absorbed:
  layering guards for `integrations/telegram/` (transport never
  imports rails; handlers read through the query surface; the
  pane-ownership check not bypassable by import path) running in
  CI. (c) Whatever the phase-close version decision names ships
  per docs/distribution.md. (d) Bugs found live become fixes in
  this story or stories in the next phase — the WLA-12-08
  precedent, no silent scope creep.
- **Out:** new features (this story integrates and proves).

## Acceptance criteria

- [ ] Every leg above captured (fixture where CI-provable, live
  where not, screenshots in assets — the 13-06 owed-screenshot
  debt does not repeat).
- [ ] Fitness tests fail on a planted layering violation and pass
  on the real tree, wired into validation.yml.
- [ ] Full battery + docs-lint green; release checklist per the
  phase-close decision.
- [ ] The journal entry ships in the same commit (charter
  cadence).

## Test plan

- **Unit:** the fitness tests themselves.
- **Integration:** full scripted-transport battery across 02–06
  features composed.
- **Manual / device:** the live day above.
