# WLA-23-04 - Workbench and riders expose the handrail

- **Project:** work-log-automation
- **Phase:** 23
- **Status:** backlog
- **Depends on:** WLA-23-03
- **Unblocks:** WLA-23-05
- **Owner:** unassigned

## Problem

The status panel and agent brief currently stop at a command. The deliberate
step boundary must be visible where users already orient, without making the
workbench a shell or teaching agents to bypass manual actions.

## Scope

- **In:** workbench preview/confirm experience using the guarded mutation
  lifecycle; generated rider wording; responsive/manual/prohibited/stale
  states; copyable tokenized argv fallback.
- **Out:** arbitrary command inputs, auto-run, commit/certification buttons,
  hidden polling loops.

## Acceptance criteria

- [ ] Applicable actions expose an explicit preview→confirm step; prohibited
  actions state why no apply control exists.
- [ ] Stale confirmation returns a non-mutating conflict and refreshes state.
- [ ] Riders use `dw step` only with a fresh token and preserve manual seams.
- [ ] Desktop/mobile and static fitness tests pin the trust boundary.

## Test plan

- **Unit:** rendering/security fitness.
- **Integration:** workbench preview/apply/stale lifecycle.
- **Manual / device:** desktop and mobile visual inspection.

## Notes / open questions

Record unresolved decisions here before implementation starts.
