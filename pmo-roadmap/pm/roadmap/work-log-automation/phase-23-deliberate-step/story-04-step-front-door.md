# WLA-23-04 - Workbench and riders expose the handrail

- **Project:** work-log-automation
- **Phase:** 23
- **Status:** done
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

- [x] Applicable actions expose an explicit preview→confirm step; prohibited
  actions state why no apply control exists.
- [x] Stale confirmation returns a non-mutating conflict and refreshes state.
- [x] Riders use `dw step` only with a fresh token and preserve manual seams.
- [x] Desktop/mobile and static fitness tests pin the trust boundary.

## Test plan

- **Unit:** rendering/security fitness.
- **Integration:** workbench preview/apply/stale lifecycle.
- **Manual / device:** desktop and mobile visual inspection.

## Notes / open questions

- The overview fetches the pure status and step documents together. The
  recommendation itself has no button; an applicable lease gets a separate
  “review one deliberate step” act boundary.
- Confirmation shows the full token, authorized argv, exact CLI fallback, and
  one-child/no-loop warning. Its only mutation request is
  `{project: step.project, expect: step.token}`; there is no input field or
  client-built command.
- One apply disables immediately, renders the bounded receipt, refreshes both
  status and step, and stops. HTTP 409 is rendered as “nothing started” and
  also refreshes; it never retries the old token.
- Manual, prohibited, certification, and commit states display the core
  refusal and contain no apply control.
- The canonical managed block, packaged fallback, `/dw-next`,
  `/dw-story-done`, plugin skill, and generated Claude/Codex/pi copies require
  a fresh applicable lease, exact `apply_command`/`expect`, and a stop after
  every receipt. Operator metadata, certification, and commit remain manual.
- `workbench-ui-smoke.sh` now pins the static request boundary and renders 20
  desktop/mobile snapshots, including an open confirmation plus attention and
  ambiguous/prohibited states. The actual Story-04 confirmation was visually
  inspected at 1440×900 and 390×844 on Firefox.
