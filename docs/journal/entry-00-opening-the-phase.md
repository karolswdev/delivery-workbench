# Entry 0 — Opening the phase

*2026-07-03. Repo: delivery-workbench, main, clean tree, v1.8.0
shipped three commits ago.*

Phase 12 starts as a conversation, not a command. The idea on the
table: the commit gate has always been harness-agnostic, but the
experience around it is Claude-shaped, and meanwhile HoldSpeak —
the other resident of this desk — already watches Claude Code and
Codex sessions, runs a plugin host with a `delivery` intent, and
refuses to act without approval. Two consent systems, one desk,
no contract between them. That's the phase.

Before designing anything I read HoldSpeak's own docs the way I'd
want mine read: `PLUGIN_AUTHORING.md` for the pack contract (one
`.py` file, a `MANIFEST`, a `create_plugin()` factory, never raise
from `run()`), `API_SURFACE.md` for what the Desk exposes, and
`AGENT_HOOK_INSTALL.md`, which is where the convergence appeared —
HoldSpeak already bridges the same two agents I was planning riders
for. The riders plan and the HoldSpeak plan turned out to be one
plan. Designs that collapse like that are usually right.

Opening a phase here is CLI work, so the roadmap can't drift from
the tool's idea of a roadmap:

```
.githooks/dw phase create work-log-automation 12 \
  "Symbiosis: HoldSpeak, agent riders, and the journaled proof" \
  --slug holdspeak-symbiosis-and-agent-riders
.githooks/dw story create work-log-automation 12 "Design the symbiosis contract and the journal charter" ...
# ... six more
```

Seven stubs, then the honest part: filling each one with a Problem
that names why it exists, Scope that says what we will *not* do,
and acceptance criteria something can actually check. Seven stories
is the biggest phase this repo has run — the risk table says so out
loud — but the ordering is deliberate: HoldSpeak value lands by
story 3 even if the riders slip.

One confession for the record, because the charter (when WLA-12-01
writes it) will demand this kind of thing: this entry exists before
the charter that governs it. Entry 0 is written under rules that
story 01 may yet amend. If the charter contradicts me, the charter
wins and this paragraph stays as the first documented dead end.

Next: `dw check` to prove the scaffold is structurally sound, flip
WLA-12-01 to in-progress, stage everything, generate the contract,
certify it by hand — the boxes are mine to flip, not the
machinery's — and put this opening through the same gate every
other commit faces. If the gate objects to anything, the objection
goes in entry 1 verbatim.
