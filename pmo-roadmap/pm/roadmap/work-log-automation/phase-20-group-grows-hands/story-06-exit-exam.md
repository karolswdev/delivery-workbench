# WLA-20-06 - The exit exam — fitness, ledger, and the contract amended

- **Project:** work-log-automation
- **Phase:** 20
- **Status:** backlog
- **Depends on:** WLA-20-01, WLA-20-02, WLA-20-03, WLA-20-04, WLA-20-05
- **Unblocks:** (optional)
- **Owner:** unassigned

## Problem

Phase 14 closed with an exit exam: the architecture rules became
executable fitness tests and the absorption ledger recorded every
upstream idea's verdict. This phase adds two leaves, two API verbs,
an identity guard, and three button surfaces — the exam must grow
to pin them, and the documents must tell the truth about what was
absorbed from v4.3.11, transmuted, or refused again.

## Scope

- **In:** `telegram-fitness-tests.py`: `screenshot.py` and
  `toolbarcfg.py` join LEAVES (zero internal imports); a census
  pins photo/media/`setMyCommands` API strings to `transport.py`
  only; the send-keys census re-asserted unchanged; the planted
  self-test extended to a planted leaf violation in a NEW leaf.
  `docs/absorption-ccgram.md`: a "second absorption — v4.3.11"
  section with ledger rows for screenshot renderer (absorb/
  transmute: stdlib+optional-PIL, one font), live image view
  (absorb), toolbar config (transmute: JSON, closed builtins),
  interactive nav (transmute: nav-only), per-person consent
  (transmute of row 15: owner-of-record, no allowlist),
  setMyCommands (absorb), and re-refusals (voice, dashboard,
  directory browser deferred, herdr). `docs/mission-control.md`:
  amendments — owner-of-record in the consent section, the new
  read surfaces (`/screen`, image `/live`), the button surfaces
  and their floors. README: the mission-control paragraph gains
  one sentence (screenshots + buttons). Phase close: final
  summary, this story's flip in the same commit.
- **Out:** CHANGELOG (release-time, next release story); any new
  feature code (this story only pins and documents).

## Acceptance criteria

- [ ] Fitness suite green with the new pins; the self-test proves
  a planted violation in a new leaf bites.
- [ ] Absorption ledger v2 rows name every phase-20 feature with
  its verdict and upstream source file; the lineage note cites
  v4.3.11.
- [ ] mission-control.md names the new surfaces and the
  owner-of-record rule; docs-lint green.
- [ ] Full battery green (core + telegram + docs + plugin).
- [ ] Phase 20 final summary closes the phase in this commit.

## Test plan

- **Unit:** fitness suite.
- **Integration:** full battery.
- **Manual / device:** read the amended contract top to bottom.

## Notes / open questions

None — this story is the mirror of WLA-14-07, one phase later.
