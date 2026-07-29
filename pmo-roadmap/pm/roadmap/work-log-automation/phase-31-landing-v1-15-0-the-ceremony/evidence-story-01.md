# Evidence - WLA-31-01

- **Story:** WLA-31-01 - The ceremony demo
- **Status:** done
- **Date:** 2026-07-28

## Proof

The film exists and is real. `demos/rendered/full-pipeline.mp4`
(5:21, h264, 1280x720@30) shows, in order: an empty directory;
`dw init` bringing the rails up; the intake answers and the scope
conversation's inert proposal compiled by `dw program scaffold`; the
Workbench browser review of the adoption and the Program Studio
bundle; `dw setup preview`/`apply` with the lease token on screen;
the gated adopt commit; the start-story lease; the explicit
capability/budget grant and `dw program start --approve`; live
supervised delivery (claude opus implemented, both closed checks
passed, live codex issued the passing verdict) with Mission Control
tracking the run in the browser; the certified handoff; the operator
integrating the exact certified diff (`git apply --index`), running
`node --test` (35/35), capturing evidence, the guarded finish, the
phase close, the gated ship commit, `dw verify --all`; and two live
WebSocket clients playing the delivered game — a win and a synced
reset — recorded on one clock.

Every recorded command ran against the real machinery in
`/tmp/dw-ceremony-demo/tic-tac-toe`; nothing was mocked and no
output was fabricated. The tapes' `Wait` matchers double as
honesty checks: a beat that fails stops the recording. The first
captured run below proves the artifact's shape; the second proves
the demo repository's history passed the same gate every consumer
runs — three commits, `dw verify: ok`, phase 1 closed 1/1.

The ceremony also earned its keep as an exam: it flushed out a real
scaffold defect (the Python-shaped `diff-scope` allowlist, fixed and
committed earlier in this story) and recorded the rider/sandbox,
stale-baseline, and VHS-viewport lessons in the demo README.

### Captured run — 2026-07-29T05:52:08Z

- **Command:** `ffprobe -v error -show_entries format=duration,size:stream=codec_name,width,height,avg_frame_rate -of default=noprint_wrappers=1 demos/rendered/full-pipeline.mp4`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 1afa380c4b18f76918b959e3ad8c88d2bcc3fb8e

```text
codec_name=h264
width=1280
height=720
avg_frame_rate=30/1
duration=320.733333
size=7277497
```

### Captured run — 2026-07-29T05:52:08Z

- **Command:** `bash -c cd /tmp/dw-ceremony-demo/tic-tac-toe && .githooks/dw verify --all && git log --oneline && .githooks/dw status tic-tac-toe --json | jq -c '{verdict: .verdict, phase: .roadmap.projects[0].current_phase.status, done: .roadmap.projects[0].current_phase.stories_done}'`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 1afa380c4b18f76918b959e3ad8c88d2bcc3fb8e

```text
dw verify: ok (3 commits verified, 0 pre-epoch skipped)
4009d5e Complete TTT-1-01: two-player Tic Tac Toe over WebSockets
daaf3fa Start TTT-1-01
3bf7722 Adopt Tic Tac Toe: roadmap and governed delivery program
{"verdict":"ready","phase":"closed","done":1}
```
