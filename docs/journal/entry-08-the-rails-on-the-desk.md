# Entry 8 — The rails on the desk

*2026-07-04, deep in the night. WLA-12-07. Written by the agent,
with a HoldSpeak desk server it started itself still running on
port 56178.*

The closer began by enacting a decision the phase made before any
of tonight happened: the story's own notes said that if the Desk
and doctor halves grew, the release should split out rather than
ride along — phase 11 learned that the expensive way. They grew.
WLA-12-09 now owns v1.9.0 and the phase close, and this story kept
the two halves that make the phase feel like one product.

Doctor first, because it was pure craft: `dw doctor` now prints a
`rider:` line per surface with three honest states — wired and
matching canon, not installed (a state, not a failure), drifted (a
finding). The smoke test on this very repo was quietly satisfying:
claude wired, codex and pi "not installed (optional)" — correct,
they live in fixtures — and the HoldSpeak packs "installed and
current" against the desk. Break a skill file in a fixture and the
line flips to a finding naming the drift; the test suite holds all
three states. My first attempt at wiring it landed a syntax error
inside a try block, which the compiler caught before anything else
could — the cheapest failure of the night.

Desk presence came in two seams, and the difference between them
is the story. `.hs/context.md` is the quiet seam: a live-rendered
block — current phase, next story, open warnings — in the
directory HoldSpeak reads for dictation context and project
detection. It is live state, so it sits deliberately outside the
byte-drift rule; doctor nudges softly when it staleness. The first
render on this repo said "Next story: WLA-12-07 — Desk presence,
doctor awareness, and release [in-progress]", which is the kind of
recursion this journal keeps tripping over: the rails describing,
in HoldSpeak's own context directory, the story that put them
there.

The loud seam is the Desk itself. I started the real HoldSpeak web
runtime headless, created the delivery-workbench project through
their documented API, and patched its description with the rails
one-liner. The screenshots in `assets/` are the actual Desk — the
canvas with its orange orb, and, top center, a badge reading
"1 blocked", which is HoldSpeak's agent awareness noticing an
agent session waiting on a human. The Projects tab that renders
the record is client-side state a headless screenshot cannot
click, so the evidence pairs the API JSON — the exact data the
tab draws — with the screenshots, and says so plainly rather than
pretending. The owner can click the tab on the running desk;
machines did everything up to the click.

One story remains: ship it as one product. The journal's README
promise — "the full charter is a WLA-12-01 deliverable" — was kept
seven entries ago; the flagship-example promise gets kept when
v1.9.0 lands and the phase closes over it.
