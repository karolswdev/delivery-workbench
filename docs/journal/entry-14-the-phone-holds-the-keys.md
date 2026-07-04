# Entry 14 — The phone holds the keys, the gate keeps the lock

*2026-07-04. WLA-13-06. Written by the agent, with the fixture
phone in one hand.*

The Telegram interface is the whole program in miniature: read
freely, propose everything, execute nothing without a tap, and let
the gate keep final say over every remote hand. Building it was
mostly assembling seams the earlier stories already sharpened — the
feed renders for chat the way it rendered for the Desk, the
correlation document already carried `awaiting_response` and
`last_assistant_text` precisely so a phone could relay them, and
the story verbs ride the same two allow-listed argv shapes the
HoldSpeak connector pinned in Phase 12. The new inventions are
small and all of them are refusals.

Pairing first, because identity was the owner's decision: no
hardcoded chat ID anywhere, ever. `run.py pair` prints a token on
the operator's terminal and stores only its hash; the phone sends
it back within five minutes or starts over. Wrong token, expired
token, reused token, a stranger's chat — four tests, four
silences. Re-pairing revokes the old binding by overwrite, which
means losing a phone costs one terminal command.

Arming is the edge I respected most. `send-keys` is raw input into
a terminal running with the owner's rights, and no allow-list can
bound free text — so the arming is the boundary, and it lives in
the driver, not the chat layer: `send_text` checks the grant at
the moment of use and raises before one keystroke leaves. The test
I care about proves a negative: an approved reply into an unarmed
session produces an empty tmux call log.

The crown case ran third time in the program's history and it
still lands: `/flip … done` on an evidence-less story, approved
with a genuine tap on a genuine button object, and the rails
answer `refusing to mark story done without evidence` — relayed
into chat verbatim, exit code and all. An approved proposal
refused by the gate is the stack working. From a phone now.

One decision needed making rather than inheriting, and it is
recorded in the contract: the first gated commit of a
chat-created project. Certification is human, always — but the
human is on a phone, and the bootstrap contract of a repo with no
stories, no evidence, and no history is the one contract whose
every rule is mechanically checkable. So the approval tap is the
certifying act, the consent is recorded in the contract itself,
and the delegation ends there: story-work certification never
leaves human hands, and the story verbs cannot commit at all. The
test for this is the one that surprised me by passing first try —
scaffold, rails, doctor, contract, commit, hooks live, no fakes.

What CI cannot prove stays owed and named: the live phone leg,
screenshots into the evidence assets, the same loop against the
real desk. The fixture phone tapped every button; Karol's phone
gets the next turn.
