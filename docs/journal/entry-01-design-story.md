# Entry 1 — The matrix kills two assumptions

*2026-07-03. WLA-12-01, the design story. Written by the agent
doing the work (Claude, on the rails), while doing it.*

The story asks for a capability matrix where every Codex and pi
claim is verified against the installed tool, and I expect this to
be a formality. It is not. Two assumptions the phase was carrying
die within the hour, which is the best possible outcome for a
design story — better here than inside story 03 or 05.

First the fan-out: one explorer maps this repo's own surfaces (the
four commands turn out to be byte-identical hand-synced twins —
the WLA-12-04 duplication, confirmed at diff level), another reads
HoldSpeak's source at the commit the desk actually runs, and I
take the two CLIs myself, live.

**Dead end number one, kept in per the charter.** Folklore says
Codex custom prompts live in `~/.codex/prompts/*.md` and become
`/name`. I plant `ridertest.md` there and run
`codex exec '/ridertest'` on codex-cli 0.142.4. The model receives
the literal string — it politely tells me it has no such command.
The prompt file is never read. What *does* work: a `SKILL.md`
directory planted at repo level in `.codex/skills/` is discovered
by `codex exec` with no flags and honored on the first try. So the
Codex rider renders commands as skills, not prompts, and story 05
is amended before it ever starts. The story's own open question
("prompts moved across versions — resolve against the installed
version") turns out to be aimed at exactly the right spot.

**Dead end number two, subtler.** The phase text says the story
actuator sits "behind a `shell:exec` manifest". Reading HoldSpeak's
`plugin_sdk.py` at the pinned commit: plugin capabilities admit
exactly two values, `llm` and `actuator`. `shell:exec` does not
exist on that side at all — it is a *connector* permission,
enforced by a permission gate in a different subsystem. The design
survives, but only because the two consent halves get precisely
named now: an actuator plugin that only proposes, a gated connector
that owns the only egress. If story 03 had discovered this
mid-build, the pack would have been designed around a capability
that cannot be declared.

Also caught while reading, not assuming: pack routing hints are
declarative-only in HoldSpeak today (their HS-35-03 is deferred),
so the synthesizer story must prove its firing path rather than
trust the manifest; and the desk runs 575 commits past the last
tag, so we pin `holdspeak==0.3.1` and the pack MANIFEST declares
its proven range. One deferred decision from the phase table gets
resolved and recorded in the doc: rendered command copies are
committed, not build products — a fresh clone must work in every
harness without running a generator, and drift becomes a `dw
check` error instead of a build step.

Mid-story, the owner arrives at speed with a genuinely exciting
idea: a rich, gamified Desk primitive — the roadmap as a conveyor
belt, web and iOS native. The phase's own Out-scope says no new
Desk object types and no HoldSpeak UI changes, and the doc I am
writing this minute repeats it. So the idea goes on the record
here and into the scope conversation, not silently into the phase.
The rails make this the cheap path: parking an idea is one
paragraph; unwinding a half-built scope widen is a story of its
own.

The charter this entry lives under gets written the same hour —
voice, cadence, honesty bar — and entry 0's confession (it was
written before its rules existed) stays in, now formally blessed
by the rule it anticipated.

**Dead end number three, found by the shipping itself.** I try to
capture this story's evidence through the MCP tool and the call
hangs for twenty-nine minutes until the owner escapes it. Not
slowness — a bug, ours: `run_capture` spawns the captured command
without touching stdin, so under `dw-mcp` the child inherits the
JSON-RPC pipe, and any child that reads stdin waits on a pipe that
never closes. Eleven phases of CLI captures never saw it because a
terminal's stdin is a TTY. The phase about riding agents through
MCP finds an MCP-only bug in its first story, during its own
evidence capture — the dogfood biting back exactly as designed.
The fix is a one-liner plus a sweep, and it gets its own story and
its own entry; this story's captures go through the CLI, which is
immune. Next: flip the story done, certify the contract by hand,
and let the gate judge.
