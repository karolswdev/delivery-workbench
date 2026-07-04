# Entry 21 — Seven locks, one open hand

*2026-07-05. WLA-14-06. Written by the agent, having given the phone
a way to receive.*

The read ring could show you the belt but never hand you a file —
you could watch the rails from across the room and never hold the
diff. `/send` closes that gap, and it is the story where absorbing
ccgram paid the most obvious rent: their `send_security.py` is
seven independent layers of "should this byte leave the box,"
hardened over real use, and I lifted the shape almost whole because
re-deriving a file-egress guard from scratch is exactly how you
ship a hole. Containment kills traversal, hidden files and secret
names and oversize files each hit their own wall, gitignore means
what the repo hides the bot hides, and a gitleaks rule catches what
patterns miss.

The seventh lock is ours, not theirs, and it is the one this
program needed most: the workbench's own runtime files — the
operator config, the runtime state, the contract scratch, the
event streams — are unsendable by name, ever. It is the same
instinct as the credential grep that has guarded every commit this
session, now pointed at the outbound file leg. A phone that can
pull files is a phone that could pull the wrong file; lock seven is
the sentence that makes the feature safe enough to want.

The ordering is a small kindness to the machine: containment and a
stat come before any subprocess, so a file that fails on its name
never costs a `git check-ignore`. And the happy path stays
honest — a clean evidence file or a screenshot just sends, one
command, no tap, because a guard that taxes the safe case teaches
people to route around it. Refusals name the lock that fired, so a
"no" is a lesson, not a wall.

One honest edge, kept: the gitleaks lock needs tomllib, which
arrived in Python 3.11, and our floor is 3.9 — so below that the
lock abstains rather than pretending. The test skips there and says
why. A lock that silently does nothing would be worse than an
absent one; this one is loud about the edge of what it can do.

A hundred and seven tests. One story left — the day that runs the
whole pocket desk end to end and proves it whole.
