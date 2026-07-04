# WLA-14-03 - The message layer grows up

- **Project:** work-log-automation
- **Phase:** 14
- **Status:** backlog
- **Depends on:** WLA-14-01.
- **Unblocks:** WLA-14-04, WLA-14-05.
- **Owner:** unassigned

*Re-pinned by WLA-14-01 (2026-07-04): implement against [docs/absorption-ccgram.md](../../../../../docs/absorption-ccgram.md) §2.*

## Problem

Our transport is honest but primitive: plain text, hard truncation
at 3,900 characters, one send per say, no ordering guarantee under
burst, no flood-control handling beyond the retry loop. ccgram's
message layer is the part of their system most hardened by real
use, and every piece of it is consent-neutral — pure craft. Once
conversation flows (WLA-14-04), agent replies arrive as real
bursts, and this layer is what keeps them ordered, formatted, and
un-spammy.

## Scope

- **In:** (a) Entity-based formatting: markdown converted to plain
  text plus explicit entity offsets — nothing to escape, no parse
  errors possible — with the two-phase fallback (entities, then
  plain) and thread-gone short-circuit. (b) A per-chat FIFO send
  queue: ordered delivery, consecutive-text merge under the size
  cap, stale-status coalescing (only the latest status survives),
  flood-control pauses honored, dead-worker respawn. (c)
  Edit-in-place for evolving messages (proposal cards updating
  through their lifecycle instead of stacking; the belt-status
  message refreshed, not re-sent; live agent status bubbles). (d)
  Splitting only at the send layer — renderers keep full content.
  (e) The pure decision-kernel pattern applied to our own state
  transitions (pairing, proposal lifecycle, arming/binding
  expiry): inputs gathered into a context, decisions as pure
  functions, tested without mocks.
- **Out:** MarkdownV2 anywhere; webhook mode; TTS voice replies
  (parked unless the map says otherwise).

## Acceptance criteria

- [ ] A message containing every markdown-hostile character ships
  without escaping logic and renders formatted; the fallback path
  is test-forced and ships plain.
- [ ] Burst test: N rapid sends arrive ordered, merged where
  adjacent, with statuses coalesced to the latest — fixture
  transport asserts the exact sequence.
- [ ] A proposal card edits in place across proposed → decided →
  executed/refused; the chat history holds one card, not four
  messages.
- [ ] The consent state machine's transitions are pure-function
  tested with zero mocks (the decide-kernel pattern, cited).

## Test plan

- **Unit:** entity conversion, queue merge/coalesce, decision
  kernels.
- **Integration:** scripted transport burst-order proof;
  edit-in-place lifecycle.
- **Manual / device:** rides WLA-14-07.
