# Evidence - WLA-13-05

- **Story:** WLA-13-05 - Prove mission control end-to-end with the Desk
- **Status:** done
- **Date:** 2026-07-04

## Proof

### Captured run — 2026-07-04T17:40:55Z

- **Command:** `bash -c echo "== the DW-side event log recorded the Desk steering (leg c) =="
.githooks/dw events --tail 12 | grep "story_status\|WLA-13-05" | tail -4
echo
echo "== full battery =="
python3 pmo-roadmap/tests/dw-core-tests.py 2>&1 | tail -3
python3 pmo-roadmap/tests/telegram-interface-tests.py 2>&1 | tail -3
bash pmo-roadmap/tests/docs-lint.sh 2>&1 | tail -1`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** b0fdf66b4b106a4c8835c0caa88c2e5b3bac7157

```text
== the DW-side event log recorded the Desk steering (leg c) ==
2026-07-04T17:34:20Z	story_status	WLA-13-05	from=backlog to=in-progress
2026-07-04T17:34:32Z	story_status	WLA-13-05	from=in-progress to=backlog
2026-07-04T17:40:45Z	story_status	WLA-13-05	from=backlog to=in-progress

== full battery ==
Ran 153 tests in 9.996s

OK
Ran 43 tests in 4.261s

OK
docs-lint.sh: ok (1s)
```

### The joint exit exam — all four legs, run live 2026-07-04

The counterpart phase is HoldSpeak's Phase 82 (branch
`holdspeak/hs-82-mission-control-conveyor`, CLOSED 5/5, PR #247
open at close time); its HS-82-05 evidence is the desk-side record
of the same run. The legs, DW-side view:

1. **Feed → conveyor.** The real web Desk (HoldSpeak's FastAPI
   runtime + React island, served from the counterpart branch)
   rendered this repo's live phase state via
   `/api/missioncontrol/state` relaying `dw state --json`:
   phase 13 at 5/6, WLA-13-05 next in the accent.
   Screenshot: [`assets/conveyor-live.png`](./assets/conveyor-live.png).
2. **Correlation live.** `dw sessions --json` relayed to the Desk:
   three codex sessions correlated `on_story WSH-1-02` (the
   WLA-13-03 fixture repo), claude sessions honest in `off_rails`,
   awaiting/stale flags rendered. Honest compatibility note,
   recorded on both sides: this repo itself correlates `off_rails`
   because its roadmap lives under `pmo-roadmap/pm/roadmap` rather
   than `pm/roadmap` — §2's rails-marker rule working as pinned.
3. **Steering live.** A Desk approval (actor `karol-at-the-desk`)
   flipped this story backlog→in-progress through the Phase 12
   connector seam (`dw_story_writer`, argv from the stored
   payload) and a second approval restored it. The captured run
   above shows both flips in this repo's own event log
   (17:34:20Z / 17:34:32Z) — the conveyor's ticker shows the same
   two lines in the screenshot.
4. **The crown case, with a UI.** An approved, evidence-less
   done-flip of this very story was refused by the rails —
   `dw: refusing to mark story done without evidence` — and the
   refusal rendered first-class on the Desk, driven through the
   real UI by a headless browser:
   [`assets/crown-refusal-on-the-desk.png`](./assets/crown-refusal-on-the-desk.png).
   (The banner is the story-mutation refusal; commit-gate
   `gate_refusal` events carry rule ids into the same ticker —
   both surfaces render refusals first-class.)

### Scope notes, honest

- The iOS leg: the counterpart phase scoped it out (documented
  there and here, per this story's own fallback) — the web Desk
  carries the joint proof; holdspeak-mobile picks up the conveyor
  in its own phase.
- The counterpart landed on its phase branch with PR #247 open;
  merging is the owner's tap. The proof ran against that branch's
  runtime on this desk — the demonstrated system, not a promise.
- Release decision for phase close: **v1.10.0** — the phase's CLI
  surface (`dw state`, `dw sessions [--registry]`, `dw events`)
  and the Telegram interface ship per docs/distribution.md.
