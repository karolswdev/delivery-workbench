# WLA-14-05 - The driver learns the desk's manners

- **Project:** work-log-automation
- **Phase:** 14
- **Status:** done
- **Depends on:** WLA-14-01, WLA-14-03.
- **Unblocks:** WLA-14-07.
- **Owner:** unassigned

*Re-pinned by WLA-14-01 (2026-07-04): implement against [docs/absorption-ccgram.md](../../../../../docs/absorption-ccgram.md) §4.*

## Problem

Our tmux driver is safe (pane-ownership proven per keystroke) but
blunt: it types and hopes. ccgram's driver knows the terminal it
is typing into — the literal-then-pause-then-Enter dance Claude's
TUI needs, per-harness quirks as capability data instead of
if-branches, a live view that edits one message in place instead
of flooding, and recovery verbs when a session dies. With
conversation flowing (WLA-14-04), the driver's manners ARE the
interaction quality.

## Scope

- **In:** (a) TUI send craft: literal text, a settle delay, then
  Enter as its own keystroke; per-harness follow-up quirks from
  data. (b) Harness capability descriptors: the HARNESS table
  grows flags (submit style, resume support, recovery verbs) —
  behavior is data, no `if harness ==` branches. (c)
  `/live <session>`: the capture-pane preview upgraded —
  auto-refresh by edit-in-place with content-hash gating (no
  change, no edit, no API call), stop on tap or timeout;
  read-only, ring 1. (d) An action toolbar in session-bound
  topics: a small inline grid (Esc, Enter, arrows, refresh) —
  buttons fire directly while the binding is live (the binding is
  the grant; no tap-per-tap), and the toolbar dies with the
  binding. (e) Session recovery offered when a bound session
  dies: resume / fresh per capability flags — one tap each,
  previewed inline, because launching a process is a boundary
  act even in the flowing model.
- **Out:** vim-mode detection (park until a real need); herdr or
  other multiplexers (note the seam, stay tmux).

## Acceptance criteria

- [ ] Submit reliability: the literal/delay/Enter sequence is the
  driver's shape (fixture asserts exact call order and spacing
  policy); per-harness quirks come from the capability table.
- [ ] `/live` edits one message in place, skips no-change frames
  by hash, and never sends a keystroke (read-only proven).
- [ ] The toolbar renders only in session-bound topics, fires
  without intermediate taps while bound, and refuses after the
  binding ends (test); every press routes through the driver's
  pane-ownership check.
- [ ] A dead session's recovery offers are capability-aware
  (claude resumes; a harness without resume offers fresh only).

## Test plan

- **Unit:** capability table; hash-gated refresh decisions.
- **Integration:** scripted transport + recording tmux runner:
  toolbar lifecycle, live view edits, recovery flow.
- **Manual / device:** rides WLA-14-07.
