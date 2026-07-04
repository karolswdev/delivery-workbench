# WLA-14-02 - The rails speak first: hook-driven push

- **Project:** work-log-automation
- **Phase:** 14
- **Status:** backlog
- **Depends on:** WLA-14-01.
- **Unblocks:** WLA-14-04, WLA-14-07.
- **Owner:** unassigned

## Problem

The interface polls: sessions every 15 seconds, and only while the
serve loop spins. ccgram proved the better shape releases ago —
agent hooks append to an events stream the instant something
happens, and a byte-offset reader drains it crash-safe and
truncation-tolerant. Today our awaiting-response push arrives up
to 15 seconds late and depends on HoldSpeak's registry hook being
installed; a dw-native hook seam makes the workbench's own phone
leg standalone and instant — and instant matters double once
conversation flows freely (WLA-14-04): a dialogue with a
15-second turn lag is not a dialogue.

## Scope

- **In:** (a) `dw hook --install/--uninstall/--status` for claude
  and codex (the ccgram installer discipline: settings-file edits
  idempotent, a nested-session guard so spawned observers don't
  double-fire, hooks that never import bot config); consumed
  events at minimum SessionStart / Notification / Stop /
  SessionEnd, appended to `~/.config/delivery-workbench/
  agent-events.jsonl` (flock-locked, rails-adjacent metadata only
  per the §3 consent stance). (b) A byte-offset event reader in
  the interface (offset persisted in runtime state; truncation
  resets honestly; malformed lines skipped) driving instant pushes
  — a blocked agent reaches the phone in about a second. (c) The
  15-second poll demoted to fallback and reconciliation, not
  removed. (d) Registry coexistence: when HoldSpeak's richer
  registry is present, correlation still comes from `dw sessions`;
  the hook stream is the wake-up, not a second source of truth.
- **Out:** gemini or other harness hooks (the seam stays open);
  transcript-content tailing beyond what WLA-14-01 decides for
  conversational echo.

## Acceptance criteria

- [ ] Hook install is idempotent, status-reportable, and
  uninstalls clean; a nested agent session does not double-fire
  (test-proven with a fixture process tree or env guard).
- [ ] An awaiting-response event reaches the scripted transport in
  the same poll cycle it is appended (fixture proof), and the
  live phone sees a question in ~1 s (manual leg, 07).
- [ ] The reader survives truncation, partial lines, and restart
  with no duplicate pushes (offset in runtime state).
- [ ] Events carry rails-adjacent metadata only — a content-audit
  test in the suite, the §3 precedent.

## Test plan

- **Unit:** event reader (offsets, truncation, malformed lines);
  installer edits against fixture settings files.
- **Integration:** scripted transport receives a push triggered by
  an appended fixture event, no poll needed.
- **Manual / device:** rides WLA-14-07.
