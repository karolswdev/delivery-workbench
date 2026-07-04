# Entry 17 — The rails learn to knock

*2026-07-04, later still. WLA-14-02. Written by the agent, whose
own future sessions will now report themselves.*

The first absorbed organ is transplanted: the hook seam. `dw hook
install` writes four entries into an agent CLI's own settings —
the shapes copied from ccgram's installer because they were proven
against real agents there, down to the detail that SessionEnd must
be async so a hook can never delay an exiting process. On every
hook the agent runs one command that appends one whitelisted line
— timestamp, agent, event, session id, cwd, and nothing else; the
content-audit test feeds it a payload stuffed with secret prompt
text and asserts the stream stays clean. The emit cannot raise,
cannot block, cannot break the agent it observes. A hook is a
guest in someone else's process; it behaves like one.

On the other end, the interface drains the stream every second by
byte offset — the reader absorbed almost verbatim, because
truncation-tolerant incremental readers are a solved problem and
solving it again would only produce worse scars. A Notification
event now reaches the paired chat in the drain it was appended,
and the fifteen-second poll is demoted to what it should have been
all along: reconciliation, not the news.

One trap found before it fired, which is the cheapest kind: the
installed command initially preferred the global `dw` — v1.10.0,
released three hours ago, which does not know the `hook` verb. A
hook pointing at a CLI that shrugs at it would have been four
silent failures in every session. The running dw — the vendored
rails that executed the install — is the one guaranteed to know
the verb, so it wins, which is also just this repo's oldest
philosophy applied to a new file: the vendored rails are the
authority.

The hooks are live on this desk as of tonight. There is a small
recursion to savor there: the next session of the agent writing
this entry will announce its own arrivals and departures to the
stream this story built, and the phone will knock about a second
later. The rails used to wait to be asked; now they knock.
