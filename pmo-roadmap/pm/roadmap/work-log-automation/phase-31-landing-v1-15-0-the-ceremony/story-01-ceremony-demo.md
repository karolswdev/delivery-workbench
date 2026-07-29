# WLA-31-01 - The ceremony demo

- **Project:** work-log-automation
- **Phase:** 31
- **Status:** in-progress
- **Depends on:** none
- **Unblocks:** WLA-31-02
- **Owner:** unassigned

## Problem

Phases 25-30 built the autonomy layer end to end, and the Phase 30
exam proved it live — but the proof lives in a Markdown transcript
only a reader of this roadmap ever sees. The release deserves a
demo a stranger can watch: the full pipeline on film, from an empty
directory to a delivered, playable product, with every approval and
refusal visible. Nothing sells evidence-first delivery like watching
the evidence get made.

## Scope

- **In:** One rendered `demos/rendered/full-pipeline.mp4` (H.264,
  watchable length; long agent stretches time-compressed) showing,
  in order: `mkdir` + `dw init` in a fresh directory; the intake /
  scope pass producing a setup proposal for a WebSocket Tic Tac Toe
  project with one delivery phase; `dw setup preview` + `dw setup
  apply` with the lease token on screen; the gated adopt commit;
  `dw program plan` / `dw program start --approve` with the finite
  grant visible; live claude + codex rider ticks delivering the
  game; evidence capture; the guarded finish and the gated ship
  commit; a closing shot of the game actually being played in two
  browser windows over WebSockets. The cut alternates surfaces on
  purpose (owner direction, 2026-07-28: "we need this all to be
  visual"): terminal for the command rituals, and the Workbench
  browser UI for the adoption/proposal review, Program Studio
  bundle, and Mission Control live during the run — the demo shows
  both hands, CLI and web. Supporting sources under
  `demos/`: the segment tapes / driver script and a
  `demos/README.md` row so the recording is regenerable. The demo
  project itself is a throwaway under `/tmp`; only the recording
  and its sources land here.
- **In (amended 2026-07-28):** minimal machinery fixes the ceremony
  run itself flushes out, shipped through the gate like the exam
  phases did. First finding: the scaffold's default `diff-scope`
  allowlist was Python-shaped, so any Node/web delivery failed its
  own governance check; the default now covers mainstream layouts
  (`test/**`, `public/**`, `*.js`, `package.json`, …).
- **Out:** publishing the video anywhere (README embed or hosting
  is the owner's call, and GitHub can't inline mp4 from the repo
  anyway); re-running the Phase 30 exam; framework changes beyond
  what the ceremony run itself proves necessary.

## Acceptance criteria

- [ ] `demos/rendered/full-pipeline.mp4` exists, plays, and shows
  every stage listed in scope, including at least one claude and
  one codex dispatch and the final game being played.
- [ ] The recording is regenerable: `demos/README.md` documents the
  command(s), and the segment sources are checked in.
- [ ] The demo run itself passed the real machinery — the throwaway
  repo's history passes `dw verify --all` at the moment of
  recording (captured in evidence).

## Test plan

- **Unit:** n/a.
- **Integration:** `dw verify --all` inside the finished demo repo;
  `ffprobe` on the rendered mp4 (codec, duration).
- **Manual / device:** watch the cut end to end; confirm the game
  plays over WebSockets in the closing segment.

## Notes / open questions

VHS renders mp4 natively and is already this repo's demo tooling;
live agent ticks run minutes, so the plan is segmented capture with
ffmpeg concat + timelapse rather than one continuous tape.
