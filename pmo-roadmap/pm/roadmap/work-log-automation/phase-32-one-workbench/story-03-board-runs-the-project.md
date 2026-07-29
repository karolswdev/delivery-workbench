# WLA-32-03 - The board runs the project

- **Project:** work-log-automation
- **Phase:** 32
- **Status:** done
- **Depends on:** WLA-32-02
- **Unblocks:** WLA-32-08
- **Owner:** unassigned

## Problem

The board already moves work safely, but it is one route behind an overview
page and sends common project actions elsewhere. A user cannot create work
from a lane or pause and resume a phase from the board, and a cross-phase
drag has no useful, friendly outcome.

## Scope

- **In:** Make the board the home route in
  `pmo-roadmap/workbench/app.js` and move the overview's needs-attention and
  next-step strip above its phase lanes. Add story creation from the chosen
  lane, keep parking behind a required reason, and expose phase pause and
  resume through the server's existing guarded mutation path. Keep drag,
  move, create, park, pause, and resume on preview, exact diff, and apply.
  Add a clear refusal for cross-phase drops. Update board coverage in
  `pmo-roadmap/tests/workbench-explorer.sh`,
  `pmo-roadmap/tests/workbench-ui-smoke.sh`,
  `pmo-roadmap/tests/workbench-accessibility.py`, and
  `pmo-roadmap/tests/dw-core-tests.py`.
- **Out:** Cross-phase story moves; a new mutation kind; automatic phase or
  story changes; changes to the evidence requirement for done work; generic
  certify or commit controls; a browser scheduler.

## Localization hints

- **Affected files:**
  - `pmo-roadmap/workbench/app.js`
  - `pmo-roadmap/lib/dw_pmo/workbench.py`
  - `pmo-roadmap/tests/dw-core-tests.py`
  - `pmo-roadmap/tests/workbench-explorer.sh`

## Acceptance criteria

- [ ] Opening the workbench or following its home link shows the selected
  project's board, with needs-attention and one canonical next step above
  the phase lanes.
- [ ] A user can create a story from a lane without leaving the board. The
  chosen phase and starting status are visible before preview, and the board
  updates only after the user reviews the exact change and applies it.
- [ ] Dragging a story or using its move control shows the exact proposed
  status change before apply. Parking cannot be previewed without a reason,
  and marking work done is refused when its required proof is missing.
- [ ] A user can pause or resume a phase from its lane. The preview names the
  phase and action, and no phase state changes until the matching fresh
  preview is applied.
- [ ] Dropping a story on a different phase is refused with plain copy that
  says cross-phase moves are not supported and returns the card to its
  original lane; no preview or apply request changes the roadmap.
- [ ] Every board action remains a client of the canonical preview and apply
  boundary. A stale, altered, reused, or mismatched preview token is refused
  and leaves the board unchanged.
- [ ] Create, move, park, pause, resume, and refusal paths work by keyboard
  and at 390x844 without horizontal page overflow or color-only status cues.

## Test plan

- **Unit:** `python3 pmo-roadmap/tests/dw-core-tests.py`
- **Integration:** `bash pmo-roadmap/tests/workbench-explorer.sh`
- **Browser:** `bash pmo-roadmap/tests/workbench-ui-smoke.sh`
- **Accessibility:** `python3 pmo-roadmap/tests/workbench-accessibility.py`
- **Manual / device:** At 1440x900 and 390x844, open the root route; create a
  story from a lane; move it; park it with and without a reason; pause and
  resume its phase; attempt a cross-phase drop; and try to reuse an applied
  preview. Confirm the board changes only after each valid apply.

## Notes / open questions

Story creation should be a short board task, not the full planning form.
Keep advanced fields under Technical details or link to the full editor after
the basic story exists. Cross-phase movement remains out of scope even if
native drag behavior makes it look easy; the refusal should teach that
boundary without exposing internal mutation names.

The board renderer and movement controls sit near the `#/board` route in app.js; phase pause/resume should join the same guarded action map as the existing edits, reusing the server's existing mutation kinds rather than adding a new endpoint.
