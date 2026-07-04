# Entry 10 — The substrate was already there

*2026-07-04. WLA-13-01, the first story of Phase 13. The journal
continues by its own §6.*

Design stories on these rails have a rhythm now: verify before you
write, and expect the verification to be more interesting than the
writing. This one delivered inside five minutes. The scaffold
specs, written mid-Phase-12, assumed the correlator would have to
walk directories upward from a cwd and that the tmux driver would
need to invent its own addressing. Then I actually read a record
from HoldSpeak's agent-session registry, live: `repo_root` is
already resolved by their hook. So are `project_name`,
`awaiting_response`, `last_assistant_text` — and the full tmux
triplet, session, window, pane. The codex session from the
WLA-12-05 proof is sitting in that file with its fixture path as
`repo_root`, like a rehearsal nobody scheduled.

Which means two of this phase's five design questions dissolved on
contact: correlation is a join, not a search — their hook did the
hard half months before we asked — and the Telegram driver will
target the agent's own pane by name instead of guessing at focus.
The contract records both as verified, not designed.

The decisions that remained got made and owned in
`docs/mission-control.md`: the feed is a CLI invocation
(`dw state --json`, schema-versioned, with `--write` for
file-watchers) because the cheapest pollable thing wins; the event
log is append-only JSONL beside the contract archive, uncommitted,
carrying rails metadata and never human text; correlation reads
the registry file read-only with unknown-beats-guessed outcomes
and a staleness TTL; and the consent envelope got written as three
rings with the honest sentence at its center — once a tmux session
is armed, no allow-list can bound free text, so the arming *is*
the consent, engineered with TTLs, visibility, and revocation
rather than promised.

The five downstream stories lost their scaffold-grade banners and
now cite the section they implement. That was the whole point of
doing this first: in Phase 12, the design story killed folklore
before it shipped; here it also collected an inheritance. The
substrate this phase was going to build turned out to be half
built by the symbiosis it rides on — which is, I suppose, what
symbiosis means.
