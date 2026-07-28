# WLA-30-03 - Hold the scope conversation

- **Project:** work-log-automation
- **Phase:** 30
- **Status:** done
- **Depends on:** WLA-30-01, WLA-30-04
- **Unblocks:** WLA-30-10
- **Owner:** unassigned

## Problem

The rough idea has no front door. Discovery assumes an existing codebase;
roadmap authoring is 500 lines of methodology an agent may or may not
follow; the bridge that turns a report into real phases
(`dw adopt --from-report`) exists but the shipped skill routes around it.
Phase 29 deferred the conversational intake until the engine proved itself
on real work. It has.

Scope-Chat is that front door: one guided conversation that elicits what
only the human knows — the outcome, the users, the first usable milestone,
the constraints, the quality bar, the autonomy appetite — and compiles it
into one inert setup proposal. The conversation drafts; it never writes.
Everything it produces waits for the workbench review and the one setup
lease.

## Scope

- **In:** a Scope-Chat skill (shipped through the existing rider/skill
  distribution) with two explicit modes — **build** (from an idea in a
  rails-ready repository) and **maintain** (inspect an existing codebase
  and roadmap first, then propose changes). A minimum interview covering
  project identity, desired outcome, intended users, first usable
  milestone, constraints, non-goals, verification expectations, and
  desired autonomy level. Proposal assembly against the WLA-30-01
  contract, with every phase, story, criterion, and policy choice traced
  to a user answer, a repository fact, or a labeled recommendation.
  Revision support: change one answer, get a new proposal whose unchanged
  sections are byte-stable. A closing handoff naming the workbench review
  location and the exact next preview command, stating plainly that
  nothing has been saved.
- **Out:** any mutation — the skill calls no file writes, no
  `phase create`/`story create`, no apply commands; program-bundle
  generation internals (WLA-30-07, which this skill's answers feed);
  browser-hosted chat; multi-session interview persistence beyond the
  proposal document itself.

## Acceptance criteria

- [ ] Both modes work end to end against the contract: a greenfield
  conversation and an existing-project conversation each produce a
  schema-valid proposal.
- [ ] Every generated item carries provenance, and a provenance test
  distinguishes user facts, repository facts, recommendations, and
  unresolved items.
- [ ] Material ambiguity becomes a question or an unresolved proposal
  item — never silently converted into canon; a fixture conversation with
  an ambiguous answer proves it.
- [ ] A tool-call audit over both fixture transcripts proves the skill
  used only read surfaces plus proposal submission — no writes, no shell,
  no apply.
- [ ] Revising one answer yields a new proposal with unchanged sections
  byte-stable.
- [ ] The conversation ends with the review location, the exact preview
  command, and an explicit "nothing has been saved" statement.

## Test plan

- **Unit:** proposal assembly from normalized answers; provenance
  labeling; revision stability.
- **Integration:** two scripted transcript fixtures (build, maintain)
  validated against the contract; the tool-call audit.
- **Manual / device:** run the skill from a neutral packaged consumer with
  a real rough idea and judge whether the questions would make sense to
  someone who has never seen Delivery Workbench.

## Notes / open questions

The interview's craft — question order, when to recommend versus ask, how
deep to go on verification expectations — will need iteration the criteria
cannot fully capture; the fixtures pin the floor, not the ceiling. Whether
the maintain mode should reuse the existing adoption discovery prompt's
inspection list or subsume it is open; default is reuse.
