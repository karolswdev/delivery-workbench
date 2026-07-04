# Entry 23 — The fifth window

*2026-07-05, the small hours. Phase 15, all three stories. Written
by the agent, with a cadence note up front.*

A charter note first, kept honest: this entry covers the whole
phase rather than one entry per story — a deliberate deviation for
a compact three-story phase shipped in one sitting, recorded here
so the exception stays an exception. The evidence files carry the
story-by-story record as always.

The workbench browser was the only surface that couldn't see
mission control — which was absurd, because it is the surface that
sits closest to the roadmap. Now `#/mc` renders the belt: one
read-only route returning the feed, the correlation, and the
events through the in-process API, and a hash view that draws
phases as segments, the current phase's stories as chips, and the
next actionable story in accent. The screenshot in evidence caught
the recursion this program keeps producing: the belt showing
WLA-15-01 in progress — the story that was, at that instant,
building the belt.

The live layer went in with the decision kernel server-side, which
is the honest shape for this repo: there is no JavaScript test
runner here, so the pinning logic — on_story pins to its story,
ambiguous never guesses, everything else off-belt in its named
bucket — lives in Python where the suite can hold it. The browser
just renders what the kernel decided. The real registry proved it
live: three codex sessions pinned to their story, eight held
off-belt honestly.

And because a read-only surface earns the claim only under guard,
the phase closes with a fitness test in the Phase 14 style: the
mutation dispatcher's source may never mention the mission-control
path, exactly two POST routes may exist, and the guard's self-test
plants a violation to prove the scan would catch it. The web view
stays the picture without the hands — five windows now, one
substrate, and the gate above all of them unchanged.
