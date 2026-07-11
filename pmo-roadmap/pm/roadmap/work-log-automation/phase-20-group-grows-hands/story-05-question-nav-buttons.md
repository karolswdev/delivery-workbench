# WLA-20-05 - Questions answer with buttons

- **Project:** work-log-automation
- **Phase:** 20
- **Status:** done
- **Depends on:** WLA-20-01, WLA-20-03
- **Unblocks:** (optional)
- **Owner:** unassigned

## Problem

When a blocked agent's question reaches the phone, answering means
typing `/reply` or steering text — but the question on screen is
usually a TUI menu wanting arrows and Enter. ccgram's interactive
UI puts the navigation ON the question: up/down/left/right, enter,
esc, refresh, as inline buttons that drive the actual prompt. We
have every piece (question push, driver keys, callback routing);
this story assembles them.

## Scope

- **In:** the pushed question card (hook-drain + poll_tick
  enrichment) gains a nav keyboard when the question's session is
  BOUND in a topic and ARMED: `qn:` callbacks for up/down/enter/esc
  and a 📸 refresh that delivers a fresh capture through the
  story-01 flow whole (photo with its own refresh button, or the
  stated text fallback — cleaner than overloading the text card
  with media it cannot hold). Keys route
  through `TmuxDriver.send_key` (existing floors: armed, owned).
  Unarmed/unbound question cards keep today's shape (the proposal
  path with one-tap arming stands — a nav tap NEVER arms). Taps
  are owner-checked (story 03). After enter/esc the card notes the
  action taken.
- **Out:** parsing menu options out of the pane to render
  option-labeled buttons (deferred — nav keys are the honest
  primitive); auto-screenshot on every question (deferred, phase
  decision); any change to the `/reply` proposal flow.

## Acceptance criteria

- [ ] A question from a bound+armed session renders the nav
  keyboard; each nav tap produces exactly one driver `send_key`
  with the right key name (RecordingRunner asserts); refresh edits
  the card with a fresh capture.
- [ ] A question from an unarmed or unbound session renders
  today's card (no nav keyboard) — pinned against the existing
  QARelay tests; a forged `qn:` tap against it is refused and
  DOES NOT arm.
- [ ] Non-owner taps refused (story 03 guard covers `qn:`).
- [ ] Full telegram suites green.

## Test plan

- **Unit:** keyboard-eligibility decision (bound × armed matrix).
- **Integration:** end-to-end via ScriptedTransport + fake driver:
  push question → tap arrows → tap enter → card updated;
  refusal legs (unarmed, non-owner, forged).
- **Manual / device:** answer a real Claude Code menu from the
  phone with buttons on the desk.

## Notes / open questions

The nav keyboard is deliberately dumb: it never claims to know
what the menu says — refresh shows the truth, arrows move, enter
commits. Honesty over cleverness.
