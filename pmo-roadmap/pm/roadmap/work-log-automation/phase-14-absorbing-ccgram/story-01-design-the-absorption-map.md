# WLA-14-01 - Design: the absorption map

- **Project:** work-log-automation
- **Phase:** 14
- **Status:** done
- **Depends on:** Phase 13 closed (the Telegram interface exists and
  runs live); the ccgram study (alexei-led/ccgram v4.3.5, MIT,
  lineage six-ddc — read in full 2026-07-04).
- **Unblocks:** WLA-14-02..07.
- **Owner:** unassigned

## Problem

ccgram solved, in production, a dozen problems our Telegram
interface will otherwise rediscover one live bug at a time — we
found four in our first hour of operation; they found theirs over
4.3 releases. But ccgram and the workbench disagree at the root:
their auth is a user-ID allowlist, ours is pairing; their
`/command` forwards straight to the pane, our every steering act
is a proposal; their events describe an agent, ours describe
rails. Absorbing without a written map either imports their trust
model by accident or waters ours down. The map says, idea by
idea: absorb wholesale, transmute under the consent spine, or
refuse with a reason.

## Scope

- **In:** `docs/absorption-ccgram.md` — the design contract for
  this phase, with the verified/cited/decided discipline and full
  attribution (MIT, alexei-led/ccgram, six-ddc lineage; ideas
  re-interpreted, any ported code carrying its notice). It pins,
  at minimum: (a) **absorb** — entity-based message formatting
  with two-phase fallback; per-chat FIFO queue with
  merge/coalesce/rate-limit; hook-driven push over an append-only
  events stream read by byte offset; the multi-layer file-send
  security pipeline; the pure decision-kernel pattern for state
  transitions; the cleanup-callback registry; the TUI send craft
  (literal-then-Enter, per-harness quirks); capability-flag
  harness descriptors. (b) **transmute** — the topic model becomes
  topics-are-projects (one forum topic per rails repo, the
  roadmap as the topic's spine, sessions riding inside); the
  directory browser becomes the path-allow-listed project picker;
  the action toolbar and live view go behind the arming envelope;
  session recovery (resume/fresh) becomes capability-aware
  one-tap offers. (c) **The interaction stance, owner decision
  2026-07-04, binding on this doc:** consent gates ENTRY, not
  every utterance. Pairing admits the owner; binding a session
  into a topic is the arming — one explicit, visible, revocable
  act — and inside a live binding, conversation FLOWS: typed text
  relays directly, agent replies land back, the toolbar fires
  without ceremony. Taps remain only at boundaries: rails verbs,
  project lifecycle, session launch/recovery — the acts the gate
  itself cares about. This amends §4 ring 3 (arming semantics:
  activity-refreshed TTL over a stopwatch) and retires the
  per-reply proposal from 13-06. Pane-ownership verification
  stays beneath everything, per keystroke. (d) **refuse** —
  user-ID allowlists as the identity model (pairing stands, §4
  ring 1); NL→LLM shell command suggestion (we relay to agents,
  we do not synthesize shell); transcript content in rails events
  (their LLM completion summaries and conversational echo are the
  owner's own content flowing to the owner's own chat —
  permissible, but a deliberate §3-adjacent decision this doc
  must make, not inherit). (e) re-pinned specs for 02–07, each
  citing its section.
- **Out:** implementation; any change to the Phase 13 contract's
  consent envelope semantics (amendments ride the stories that
  earn them).

## Acceptance criteria

- [ ] The design doc exists; every ccgram idea it treats is marked
  absorb/transmute/refuse with a one-line reason and a file:line
  citation into the studied source.
- [ ] The consent spine survives on paper: pairing, proposals,
  arming, and the gate's final say are each explicitly traced
  through the absorbed features.
- [ ] Stories 02–07 are re-pinned to the sections they implement.
- [ ] Attribution is explicit and licensing is clean (MIT notice
  carried wherever code, not just ideas, is ported).
- [ ] Docs-lint passes.

## Test plan

- **Unit:** n/a (design story).
- **Integration:** `pmo-roadmap/tests/docs-lint.sh`.
- **Manual / device:** the studied claims spot-checked against the
  clone at the pinned version (v4.3.5).

## Notes / open questions

- The completion-summary question (LLM summaries of agent output
  pushed to chat) is the one place their design is more permissive
  than our §3 consent stance about content — decide it here, on
  purpose, either way.
- ccgram supports herdr as a second multiplexer; whether our
  driver abstracts beyond tmux is a 05 question the design should
  answer cheaply (probably: not yet, note the seam).
