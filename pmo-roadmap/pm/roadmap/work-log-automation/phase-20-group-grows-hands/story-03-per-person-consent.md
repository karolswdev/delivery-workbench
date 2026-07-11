# WLA-20-03 - Consent belongs to a person — groups get faces

- **Project:** work-log-automation
- **Phase:** 20
- **Status:** backlog
- **Depends on:** none
- **Unblocks:** WLA-20-04, WLA-20-05
- **Owner:** unassigned

## Problem

Authorization today is chat-granularity: `paired_chat` is the only
guard, and no handler ever reads `from.id` (capability map §2).
In a private chat that IS the person; in a group it means every
member holds full owner power — steer, flip, launch, send files,
approve proposals. The owner's direction makes groups the primary
surface, so the gap is now load-bearing. Phase 14 refused ccgram's
user-ID allowlist (row 15) as ambient config authority; this story
transmutes rather than repeals it: the pairing act itself names the
owner — no allowlist file appears.

## Scope

- **In:** `pairing.py` records `owner_user_id` from the `/pair`
  message's `from.id` (state field, persisted). `interface.py` gains
  one guard helper: in a chat where sender identity is ambiguous
  (any chat, honestly — but private chats have one sender by
  construction), consent-bearing surfaces require
  `from.id == owner_user_id`: the steering/lifecycle/file/arming
  commands (`/steer /unsteer /reply /flip /newstory /launch
  /install /newproject /arm /disarm /open /send /bind /unbind`),
  ALL callback taps (approve/reject, toolbar, refresh, nav), and
  plain-text relay inside a live binding. Read commands (`/status
  /state /events /sessions /questions /peek /help /start /armed`)
  stay chat-scoped. Refusal is by name ("consent belongs to the
  paired owner"). Legacy state without `owner_user_id`: today's
  behavior, `/status` warns, and the NEXT `/pair` (or a new
  `/owner claim` no — out of scope) records it. Docs note in the
  mission-control contract deferred to WLA-20-06.
- **Out:** multi-owner delegation, allowlist files, per-command
  grants (one owner, one identity); revoking pairing (exists:
  re-pair); any change to what commands require proposals (the
  tap surface is unchanged — only WHO may tap).

## Acceptance criteria

- [ ] In a group, every consent-bearing command and every callback
  tap from a non-owner `from.id` is refused by name; the identical
  action from the owner succeeds — one test walks both for each
  surface class (command, tap, relay).
- [ ] Read commands from a non-owner in the paired chat still
  answer.
- [ ] `/pair` records `owner_user_id`; the state round-trips through
  persistence; token hygiene unaffected.
- [ ] Legacy state (no `owner_user_id`): all existing tests pass
  unmodified against it, and `/status` carries the warning.
- [ ] Full telegram suites green.

## Test plan

- **Unit:** guard helper truth table (owner / non-owner / legacy /
  private).
- **Integration:** group-chat scenario tests per surface class;
  persistence round-trip; regression suite against legacy state.
- **Manual / device:** two-account group walk on the desk (owner
  phone + second account) when convenient.

## Notes / open questions

The relay guard matters most: flowing conversation stays flowing
for the OWNER (no new taps — §0 untouched); a second human typing
into a steered topic is the exact scenario the guard exists for.
