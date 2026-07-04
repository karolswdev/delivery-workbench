# WLA-14-04 - Topics are projects, and conversation flows

- **Project:** work-log-automation
- **Phase:** 14
- **Status:** backlog
- **Depends on:** WLA-14-01, WLA-14-02, WLA-14-03.
- **Unblocks:** WLA-14-07.
- **Owner:** unassigned

## Problem

One flat chat is fine for one repo, and a proposal tap per spoken
sentence is fine for a demo — neither survives real use. ccgram's
deepest UX insight is spatial: one forum topic per unit of work,
and inside it you just TALK — type, and it lands in the agent's
pane. The owner's direction (2026-07-04) makes this binding: the
consent machinery gates entry, not every utterance. Transmuted:
a topic is a rails repo; a session bound into it converses
freely; the taps live at the boundaries where they belong.

## Scope

- **In:** (a) Forum-group support beside the flat chat (pairing
  binds the group; flat single-chat mode keeps working). (b) One
  topic per rails repo, bound via a tap flow (list the
  allow-listed workspace roots' rails repos, tap to bind; the
  ccgram directory browser reshaped into the ring-2 lifecycle
  envelope, `/newproject` included). (c) **Conversation flows:**
  binding an agent session into a topic IS the arming — one
  explicit, visible act (`⚡ bound claude @ gate — steering live`),
  after which plain typed text relays straight to the pane, no
  per-message proposal, and agent replies/questions land back in
  the topic (hook-driven, 14-02). The binding stays visible
  (`/armed`, topic emoji), revocable in one tap, expires on real
  idleness with an activity-refreshed TTL rather than a stopwatch
  — WLA-14-01 amends §4 ring 3 to say exactly this. Pane
  ownership verification stays beneath it all, per keystroke.
  (d) A per-topic router (bidirectional `(chat, thread) ↔ repo`,
  stale bindings evicted, names synced, topic emoji = rails
  state). (e) Commands scope to their topic's repo — `/state` in
  a topic means that repo. (f) Cross-topic pushes route home.
  What KEEPS a tap: rails verbs (`/flip`, `/newstory`), project
  lifecycle, and anything the gate itself guards — the taps that
  mean something because they are rare.
- **Out:** multi-owner groups (owner-only stands); per-topic
  pairing (one pairing, one owner, all topics).

## Acceptance criteria

- [ ] Binding a topic to a repo is a tap flow, allow-listed, and
  survives restart (runtime state, chmod 600).
- [ ] In a session-bound topic, plain text reaches the pane with
  zero intermediate taps (fixture: typed text → send-keys calls,
  nothing else); an unbound topic's text does NOT reach any pane.
- [ ] Revoking the binding (one tap or `/disarm`) stops relay
  immediately; idle expiry stops it honestly and says so in the
  topic.
- [ ] `/state`, `/flip` in a bound topic act on that repo with no
  repo argument; a question from a session in repo A lands in
  topic A, never elsewhere.
- [ ] Flat-chat mode still passes the whole Phase 13 suite.

## Test plan

- **Unit:** router map (bind, evict, reverse lookup); binding
  TTL/activity decision kernel; emoji state kernel.
- **Integration:** scripted forum-shaped updates — bind flow, free
  conversation relay, revocation, scoped commands, routed pushes.
- **Manual / device:** rides WLA-14-07.
