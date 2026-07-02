# WLA-7-01 - Documentation audit and information architecture

- **Project:** work-log-automation
- **Phase:** 7
- **Status:** done
- **Depends on:** none
- **Unblocks:** WLA-7-02, WLA-7-03, WLA-7-04, WLA-7-05
- **Owner:** unassigned

## Problem

Documentation grew organically across seven phases: the root README,
the framework README, canon docs, templates, demos, agent docs, and
CLAUDE.md each accreted content at different moments of the
architecture. Before rewriting anything, we need an audit: what
exists, who each document serves, what is stale, what is duplicated,
and what a newcomer (human or agent) actually needs on each path.

## Scope

- **In:** Full inventory of every Markdown/document surface, an
  audience map (evaluator, adopter, contributor, operating agent),
  per-document staleness findings against post-Phase-5/6 reality, a
  duplication/conflict list, the target information architecture
  (which doc owns which topic, with links not copies), and the
  audit's own evidence file as the friction log for the phase.
- **Out:** Rewriting content (WLA-7-02/03), new assets (WLA-7-05).

## Acceptance criteria

- [ ] An inventory table lists every doc surface with audience,
  purpose, freshness verdict, and disposition (keep/rewrite/merge/
  delete).
- [ ] Each of the four audience paths names its entry point and the
  ordered documents it should traverse.
- [ ] Every stale or wrong claim found is quoted with its file path.
- [ ] The target IA assigns exactly one owning document per topic;
  duplications are marked for link-replacement.
- [ ] The audit lands as evidence with captured verification of the
  claims that are mechanically checkable.

## Test plan

- **Unit:** n/a (analysis story).
- **Integration:** captured `grep`/link checks proving cited
  staleness findings exist where claimed.
- **Manual / device:** read each audience path start-to-finish.

## Notes / open questions

The audit is the contract for the rest of the phase: later stories
implement its dispositions rather than re-litigating them.
