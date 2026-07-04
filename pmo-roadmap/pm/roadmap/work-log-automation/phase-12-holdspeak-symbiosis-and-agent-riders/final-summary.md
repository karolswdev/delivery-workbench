# Phase 12 Final Summary

**Status:** complete.
**Date:** 2026-07-03.

# Phase 12 — Final summary

**Closed:** 2026-07-04. **Released as:** v1.9.0.

## Outcome vs exit criteria

All four exit criteria met, with evidence in the story files:

1. **The capability matrix** (WLA-12-01): `docs/riders.md` holds
   the four-surface matrix, every Codex and pi claim verified
   against the installed CLIs with versions recorded, HoldSpeak
   pinned at 0.3.1. It killed two folklore assumptions before they
   shipped (Codex prompts → skills; `shell:exec` is a connector
   permission) and every later story's proof obligation traces to
   it.
2. **HoldSpeak value** (WLA-12-02/03): the ecosystem's first real
   plugin packs. The synthesizer grounds meetings in story IDs with
   grounding enforced in code (the desk's real LLM in the captured
   proof; hallucinated IDs demoted to drift). The actuator stacks
   HoldSpeak's propose→approve→execute on the dw gate — the
   captured crown case shows an approved dishonest done-flip
   refused with the banner verbatim, audit
   `proposed -> approved -> failed`. Both packs live on the desk.
   Deviation, recorded: a real *meeting* artifact screenshot is
   owed (the packs are installed; the next delivery meeting fires
   them) — the exit criterion's artifact was proven through the
   real host, real discovery, and real LLM instead.
3. **One canonical brief** (WLA-12-04/05/06): command-spec canon
   embedded in `dw_pmo` with source-tree override; hand-edited
   drift in any rendered copy fails `dw check` on both the CLI and
   MCP surfaces; the full story loop ran end-to-end under Codex
   (skills, sandbox lesson, hook coexistence in one capture) and
   under pi (a context file and a shell — the "any other harness"
   recipe is now a description, not a claim).
4. **Doctor, Desk, release** (WLA-12-07/09): `dw doctor` reports
   per-rider status with three honest states; roadmap state is on
   the real Desk (projects API + `.hs/context.md`, screenshots in
   evidence, the unclickable-tab limit stated); v1.9.0 shipped
   through the distribution ritual; the journal is complete
   (entries 0–9) and linked from the README as the worked example.

## What shipped beyond the plan

- WLA-12-08 (unplanned): the dw-mcp stdin-inheritance bug, found
  by this phase's own first evidence capture, fixed with a
  regression test and a 0.06s replay of a 29-minute wedge.
- WLA-12-09 (split from 12-07 by pre-decision): this release.
- Phase 13 scaffolded mid-phase (owner's call, scope untouched):
  mission control — Desk conveyor, state feed, correlation,
  events, and the Telegram rider with its credential-hygiene and
  steering-consent decisions already recorded.

## Deliberately deferred

- Live-meeting artifact screenshot and pack-actuator
  pending-actions wiring verification (owed in evidence, land with
  the next real meeting / Phase 13).
- Upstream HoldSpeak candidates, noted not worked around: a public
  renderer-registration seam; pack routing hints that actually
  route (HS-35-03).
- Parked candidates unchanged: multi-project dashboard,
  announcement post, HTTP/SSE MCP transport.

## The stop-signal audit

Every risk in the table fired at least once and none stopped the
phase: rider stories falsified 12-01 assumptions twice (prompts,
PyPI), the 0.x surface moved underfoot (renderers,
one-plugin-per-file), and scope pressure arrived twice mid-story —
each became a recorded decision. Eight stories became ten commits,
every one through the gate it was building.
