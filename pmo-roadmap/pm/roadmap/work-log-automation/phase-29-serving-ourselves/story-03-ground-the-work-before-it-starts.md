# WLA-29-03 - Ground the work before it starts

- **Project:** work-log-automation
- **Phase:** 29
- **Status:** backlog
- **Depends on:** WLA-29-02
- **Unblocks:** WLA-29-04, WLA-29-08
- **Owner:** unassigned

## Problem

Stories tell an agent what behavior to deliver, but nothing verifies that the
files and symbols a story mentions actually exist. A hallucinated identifier
in a story becomes an agent confidently editing the wrong thing. The studied
prototype's best discipline is the split it enforces: acceptance criteria
describe observable behavior only, while files and symbols are *advisory
localization hints* — generated freely, then verified deterministically
against the symbol map and `git grep` before any implementer sees them, with
absent symbols marked as genuinely new rather than silently trusted.

Delivery Workbench's stories should get the same treatment: hints welcome,
hints checked, and the check mechanical.

## Scope

- **In:** an optional `## Localization hints` section in the story template
  (affected files, target symbols), explicitly advisory and never part of the
  gate; a grounding pass that classifies every hint as **verified** (found in
  the symbol map at a stated location), **new** (absent, plausibly to be
  created), or **unknown** (absent with near-miss suggestions from map
  lookup and `git grep` fallback); surfacing through `dw knowledge ground
  <project> <story>` and as advisory findings in `dw check` (warnings, never
  errors); grounding results feeding the program planner's work orders so
  packets (WLA-29-04) start from verified locations; a lint-style advisory
  when acceptance criteria name exact code identifiers (behavior belongs in
  criteria, identifiers in hints).
- **Out:** making grounding a gate rule or a story-flip requirement —
  knowledge never authorizes and never blocks; auto-editing stories to fix
  hints; grounding non-story prose; any change to gate parsing of story
  files beyond tolerating the new optional section.

## Acceptance criteria

- [ ] The story template gains the optional advisory section, existing
  stories without it stay fully valid, and the gate's story parsing is
  provably unchanged (parity tests untouched).
- [ ] Grounding classifies hints as verified/new/unknown with the symbol map
  as the first authority and `git grep` as the fallback where the map
  declares itself out of coverage; every verified hint carries file and line
  span.
- [ ] Unknown hints come with bounded near-miss suggestions (name-distance
  against the map), and a hint matching nothing anywhere is never silently
  upgraded to "new" without the no-match evidence recorded.
- [ ] `dw check` reports grounding findings as warnings with the established
  greppable line format, and exit codes are unchanged by grounding-only
  findings.
- [ ] Grounding refuses on a stale map rather than answering from it, per the
  WLA-29-01 freshness rule.
- [ ] Program plan output for a story with hints includes the grounding
  result, and a story with no hints plans exactly as today.

## Test plan

- **Unit:** classification on fixture maps (present, absent-new,
  absent-with-near-miss); suggestion bounding; stale-map refusal.
- **Integration:** `dw evidence capture` of grounding a real story in this
  repository containing one verified, one new, and one misspelled hint;
  `dw check` warning output; gate suite green with the new section present in
  a fixture story.
- **Manual:** write hints for one upcoming phase-29 story and confirm the
  verified locations are where an implementer should actually look.

## Notes / open questions

The temptation this story must resist is promotion: grounding output looks so
much like a gate that someone will want failures to block. The hard constraint
says no — a story with wrong hints is a story with bad advice, and the gate
judges delivered evidence, not advice. `dw check` warnings are the ceiling.

Whether hints should be suggested automatically from story prose (extraction,
not generation) is left open; nothing in this story writes hints, it only
judges the ones humans or agents wrote.
