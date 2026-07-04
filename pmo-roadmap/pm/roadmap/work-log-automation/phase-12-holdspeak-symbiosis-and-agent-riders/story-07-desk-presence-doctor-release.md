# WLA-12-07 - Desk presence, doctor awareness, and release

- **Project:** work-log-automation
- **Phase:** 12
- **Status:** done
- **Depends on:** WLA-12-03, WLA-12-05, WLA-12-06
- **Unblocks:** none (closes the phase)
- **Owner:** unassigned

## Problem

By this point the phase has four riders and two HoldSpeak plugins,
each proven in isolation. Three loose ends keep it from being one
product: the roadmap has no presence where HoldSpeak's projects
live (the Desk shows meetings and artifacts, but not "what the
rails say is next"); `dw doctor` still only knows about hooks and
agent docs, so a half-wired rider looks healthy; and none of it is
released or told as one story. The journal, complete through six
stories, is still seven files rather than the flagship worked
example it was chartered to become.

## Scope

- **In:** (a) Desk presence, smallest honest version: roadmap
  state surfaced through the seams HoldSpeak already offers —
  the `.hs/` project-context directory and/or a project briefing
  via the projects API, per what WLA-12-01 verified — so a project
  on the Desk can answer "current phase, next story, open drift"
  without leaving HoldSpeak. (b) `dw doctor` learns riders: detects
  which surfaces are wired in this repo/environment (Claude, Codex,
  pi, HoldSpeak pack) and validates each installation the same way
  it validates hooks today, honest about what it cannot see.
  (c) *Amended 2026-07-04, enacting this story's own note and the
  phase's deferred decision:* the Desk and doctor halves grew, so
  the release and phase close split into WLA-12-09 rather than
  rushing here. This story keeps: journal entry, README
  cross-link to the journal, `docs/riders.md` gaining the
  HoldSpeak-presence how-to. WLA-12-09 owns: CHANGELOG, version
  bump to v1.9.0, the distribution ritual, final journal entry,
  `dw phase close` with a real final-summary. 
- **Out:** New Desk object types or HoldSpeak UI changes (their
  roadmap, not ours); multi-project dashboards (parked candidate);
  announcement post (parked candidate).

## Acceptance criteria

- [ ] A HoldSpeak project wired to a rails repo shows current
  phase, next story, and last alignment through `.hs/`/briefing;
  evidence shows it on a real Desk.
- [ ] `dw doctor` reports per-rider wiring status; deliberately
  breaking one rider in a fixture flips its line to a finding.
- [ ] *(moved to WLA-12-09 by the recorded split)* v1.9.0 release
  criteria live there.
- [ ] The journal has an index, one entry per story 0–7, and is
  linked from README; docs-lint passes.
- [ ] *(moved to WLA-12-09 by the recorded split)* phase close
  criteria live there.

## Test plan

- **Unit:** doctor rider checks against fixtures (wired, broken,
  absent).
- **Integration:** full suite + docs-lint; release workflow dry
  run.
- **Manual / device:** the Desk check with screenshot; the release
  ritual itself, evidence-captured.

## Notes / open questions

- Cutting a release inside the same story as feature work has
  bitten before (phase 11 kept it separate); if the Desk/doctor
  halves grow, split the release into its own story rather than
  rushing it — record the decision.
