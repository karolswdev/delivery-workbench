# The full-pipeline ceremony demo

One film, `demos/rendered/full-pipeline.mp4`: an empty directory becomes a
delivered, playable two-player WebSocket Tic Tac Toe — through the real
machinery, with live claude and codex riders, every approval on screen.

The cut alternates surfaces on purpose: the terminal for the command
rituals (init, intake, leases, the grant, the gate) and the Workbench
browser UI for what people actually review (the adoption proposal, the
generated program bundle, Mission Control during the live run), ending
with the game itself played in two browser windows.

## What the film shows, in order

1. `01-init.tape` — `mkdir`, `dw init`, the desk's rider roster, `dw doctor`.
2. `02-intake.tape` — the scope conversation's inert proposal, closed
   scaffold answers, `dw program scaffold` compiling the governed bundle.
3. `record-review.mjs` — browser: adoption review + Program Studio bundle.
4. `03-lease.tape` — reviewed state, `dw setup preview/apply` (approval 1),
   the gated adopt commit with a hand-certified contract.
5. `04-grant.tape` — start-story lease, the explicit capability/budget
   grant, `dw program start --approve` (approval 2).
6. `05-live.tape` + `record-mission-control.mjs` — live supervised
   delivery in the terminal, Mission Control tracking it in the browser.
7. `06-certified.tape` — certified handoff, operator integration
   (`git apply --index`), `node --test`, evidence capture, guarded
   finish, the phase close, the gated ship commit (approval 3),
   `dw verify --all`.
8. `record-gameplay.mjs` — two live WebSocket clients as two iframes
   in one page (one recording clock, so the board sync on film is
   the real sync), playing a full game, a win, and a reset.

## Regenerate

Requirements: `dw` (with the front-door verbs) on PATH, `vhs`, `ffmpeg`,
`node` + Playwright with chromium, authenticated `claude` and `codex`
CLIs, and a validated driver roster at the framework repo's
`.git/pmo-orchestration/drivers.json` (see `docs/riders.md`). Run from
the repository root, outside any proxying sandbox (the riders need
direct network):

```bash
demos/full-pipeline/prepare.sh          # DW_BIN / DW_ROSTER override the defaults
vhs demos/full-pipeline/01-init.tape
vhs demos/full-pipeline/02-intake.tape
node demos/full-pipeline/record-review.mjs /tmp/dw-ceremony-demo/tic-tac-toe demos/rendered/segments
vhs demos/full-pipeline/03-lease.tape
vhs demos/full-pipeline/04-grant.tape
# live segment: mission control records while the tape supervises
RUN=$(jq -r .run_id /tmp/dw-ceremony-demo/tic-tac-toe/.tmp/start.json)  # after 04
node demos/full-pipeline/record-mission-control.mjs /tmp/dw-ceremony-demo/tic-tac-toe "$RUN" \
  demos/rendered/segments /tmp/dw-ceremony-demo/tic-tac-toe/.tmp/supervise.json &
vhs demos/full-pipeline/05-live.tape
vhs demos/full-pipeline/06-certified.tape
node demos/full-pipeline/record-gameplay.mjs /tmp/dw-ceremony-demo/tic-tac-toe demos/rendered/segments
demos/full-pipeline/compose.sh   # cuts everything into demos/rendered/full-pipeline.mp4
```

The live segment runs real agents; expect five to twenty minutes and a
nonzero provider bill. The composer time-compresses the waiting, not
the acts. `assets/setup-proposal.json` is the scope conversation's real
draft (provenance inside the file); `assets/answers.json` is the closed
scaffold input. Both are the exact objects the film applies.

Recording notes learned the hard way, kept so the next run is boring:

- Node resolves ESM imports from the *script's* directory — run the
  `record-*.mjs` recorders from (or copy them next to) a directory
  where `playwright` is installed.
- VHS `Wait+Screen` matches the visible viewport; keep every beat's
  output shorter than the screen (pipe through `head`/`tail`) and
  `clear` between beats, or the matcher stares at stale rows forever.
- VHS double-quoted strings process no backslash escapes; any command
  that needs quotes or backslashes goes in a backtick-delimited
  `Type` string, exactly as typed.
- The riders need direct network: run the whole session outside any
  proxying sandbox, with proxy/CA environment variables unset.
