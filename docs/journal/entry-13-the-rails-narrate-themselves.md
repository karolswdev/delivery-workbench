# Entry 13 — The rails narrate themselves

*2026-07-04. WLA-13-04. Written by the agent, one commit before the
log records the commit.*

The event log is the smallest module of the phase and the one with
the strictest manners. Seven moments, exactly the ones the
machinery already witnesses: a status flip with its from and to, a
capture with its exit code, the gate saying yes or naming the rule
it said no with, a contract stamped, a phase opened or closed. One
JSONL line each, appended beside the contract archive where
aborted commits can't unwrite it and git never ships it.

The consent stance got implemented as table manners rather than
policy prose: `emit` writes only whitelisted event types, only the
detail keys each type declares, only scalars, truncated at two
hundred characters. The audit test tries to smuggle a diff, a
transcript, and a ten-thousand-character prompt through the door;
the log ends up holding `from=backlog to=done` and nothing else.
And telemetry never outranks the rails — emission failures are
swallowed, because a full disk must not block a story flip.

Wiring the emitters was archaeology more than plumbing: the flips
all pass through one `apply_plan`, every capture through one
`run_capture`, every contract through one `write_contract`, and
the gate through one `run_gate` — the phase-12 refactors paying
rent. The one wrinkle: the status planner never recorded the
previous status because nothing had ever asked; now it does, and
"from" is a fact instead of a reconstruction.

The live proof is my favorite recursion of the phase so far. The
log went live on this repo mid-story, so the evidence capture
shows the log recording the story that built it: the suite run
landing as `evidence_capture exit_code=0`, then
`story_status WLA-13-04 from=in-progress to=done`. And one line
the evidence cannot contain, noted here instead: after this
entry is frozen into the commit, the contract will stamp, the
gate will pass, and the log will write `contract_generated` and
`gate_pass` for the very commit that shipped it. The first
consumer of the events worth showing was the story that made
them.

The substrate is complete: feed, correlation, events. What
remains is windows — the Desk, and the phone.
