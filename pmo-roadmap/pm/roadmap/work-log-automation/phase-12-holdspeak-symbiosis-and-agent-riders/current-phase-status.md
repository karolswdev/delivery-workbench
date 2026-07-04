# Phase 12 - Symbiosis: HoldSpeak, agent riders, and the journaled proof

**Last updated:** 2026-07-03.

## Goal

Make Delivery Workbench a plug-n-play side rider for every surface a developer works from: one canonical agent brief rendered for Claude Code, Codex, and pi, plus a first-class HoldSpeak integration (roadmap synthesizer, story actuator, Desk presence) - with every step journaled in the moment as the flagship worked example for both ecosystems.

## Scope

- **In:** The symbiosis design doc (`docs/riders.md`) and journal
  charter (`docs/journal/`); a HoldSpeak plugin pack (read-only
  roadmap-alignment synthesizer, then a propose-approve-execute
  story actuator behind a `shell:exec` allow-list); the
  canonical-brief refactor collapsing `.claude/commands/` /
  `plugin/commands/` duplication with a `dw check` drift rule;
  Codex and pi riders proven with the full story loop in fixture
  repos; `dw doctor` rider awareness; Desk presence through
  HoldSpeak's existing seams (`.hs/`, project briefings); release
  v1.9.0.
- **Out:** Changes to HoldSpeak core or its UI; new Desk object
  types; machine certification of contracts (canon: never);
  actuator verbs beyond `dw story status`/`dw story create`;
  multi-project dashboard, announcement post, HTTP/SSE MCP
  transport (parked candidates, unchanged).

## Exit criteria (evidence required)

- [ ] The four-surface capability matrix exists, live-verified, and
  every later story's proof obligation traces to it (WLA-12-01).
- [ ] A real HoldSpeak meeting produces a roadmap-grounded artifact
  from the pack, and an approved actuator proposal is executed —
  including the case where the dw gate refuses it (WLA-12-02/03).
- [ ] One canonical brief renders all typing surfaces; hand-edited
  drift fails `dw check`; the full story loop is evidence-captured
  under Codex and under pi (WLA-12-04/05/06).
- [ ] `dw doctor` validates rider wiring; roadmap state is visible
  from the Desk; v1.9.0 is live on all three channels; the journal
  is complete and linked as the worked example (WLA-12-07).

## Story status

| ID | Story | Status | Story file | Evidence |
|---|---|---|---|---|
| WLA-12-01 | Design the symbiosis contract and the journal charter | done | [story-01-design-symbiosis-contract-and-journal-charter](./story-01-design-symbiosis-contract-and-journal-charter.md) | [evidence-story-01](./evidence-story-01.md) |
| WLA-12-02 | Build the HoldSpeak roadmap-alignment synthesizer | backlog | [story-02-holdspeak-roadmap-alignment-synthesizer](./story-02-holdspeak-roadmap-alignment-synthesizer.md) | - |
| WLA-12-03 | Build the HoldSpeak story actuator | backlog | [story-03-holdspeak-story-actuator](./story-03-holdspeak-story-actuator.md) | - |
| WLA-12-04 | Collapse the agent-surface duplication behind a canonical brief | backlog | [story-04-canonical-brief-collapse-duplication](./story-04-canonical-brief-collapse-duplication.md) | - |
| WLA-12-05 | Prove the Codex rider end-to-end | backlog | [story-05-codex-rider](./story-05-codex-rider.md) | - |
| WLA-12-06 | Prove the pi rider end-to-end | backlog | [story-06-pi-rider](./story-06-pi-rider.md) | - |
| WLA-12-07 | Desk presence, doctor awareness, and release | backlog | [story-07-desk-presence-doctor-release](./story-07-desk-presence-doctor-release.md) | - |
| WLA-12-08 | Fix evidence-capture stdin inheritance under dw-mcp | done | [story-08-mcp-capture-stdin-fix](./story-08-mcp-capture-stdin-fix.md) | [evidence-story-08](./evidence-story-08.md) |

## Where we are

WLA-12-01 landed 2026-07-03: `docs/riders.md` holds the
live-verified four-surface matrix (which killed two assumptions —
Codex commands render as skills, not `~/.codex/prompts`; and
`shell:exec` is a connector permission, not a plugin capability),
the canonical-brief architecture with the drift rule, and every
later story's proof obligation. The journal charter is recorded
and entries 0–1 stand under it. Shipping the story surfaced a real
bug: evidence capture through `dw-mcp` inherits the server's
JSON-RPC stdin, so a stdin-reading child wedges the single-threaded
server. WLA-12-08 fixed it the same session: every framework child
now gets explicit stdin (`DEVNULL` everywhere except the terminal
launcher, which inherits deliberately), a regression test proves
the sentinel can't leak, and the wedge scenario replays through a
held-open pipe in 0.06s. WLA-12-02 is next.

## Active risks

| Risk | Likelihood | Mitigation | Stop signal |
|---|---|---|---|
| HoldSpeak is 0.x; plugin/config surface moves under us | medium | WLA-12-01 pins the version; the pack MANIFEST declares its proven range | Pack fails discovery on a HoldSpeak upgrade |
| Codex/pi capability folklore is wrong | medium | Matrix claims verified against installed CLIs, versions recorded | A rider story finds its 12-01 assumption false |
| Seven stories is our largest phase; drift between design and late stories | medium | 12-01 names each story's proof obligation; ordering lands HoldSpeak value by story 3 | A story's scope no longer matches the design doc |
| Actuator widens the rails' attack surface | low | Two argv prefixes only, empty-allow-list default, gate still refuses dishonest flips | Any path where an unapproved or out-of-list proposal reaches egress |

## Decisions made (this phase)

- 2026-07-03 - Phase scaffolded with `dw phase create` - keeps roadmap structure consistent - CLI.
- 2026-07-03 - HoldSpeak integration ordered before the Codex/pi riders (value by story 3; riders depend only on the 12-04 seam) - Karol + agent.
- 2026-07-03 - Every story ships a journal entry in its own commit; charter formalized in WLA-12-01 - the phase is itself the worked example - Karol.
- 2026-07-03 - Actuator scope pinned to two `dw story` verbs; certification stays human, always - canon.
- 2026-07-03 - Rendered command copies are committed, not build products; drift becomes a `dw check` ERROR (resolves the deferred question) - recorded in `docs/riders.md` - WLA-12-01.
- 2026-07-03 - Codex rider renders commands as `.codex/skills/` skills, not custom prompts: live verification on codex-cli 0.142.4 showed `codex exec` never expands `~/.codex/prompts` - WLA-12-01 matrix, amends WLA-12-05.
- 2026-07-03 - HoldSpeak pinned at released 0.3.1; desk runs main 575 commits ahead, so the pack MANIFEST declares its proven range - WLA-12-01.
- 2026-07-03 - Agentic mission-control / Desk conveyor vision (rich web+iOS roadmap primitive fed by the agent hook + rails) lands as Phase 13, scaffolded after 12-01 ships; Phase 12 scope unchanged - Karol.
- 2026-07-03 - MCP evidence-capture stdin bug (captured child inherits the JSON-RPC pipe; wedges the single-threaded server) found while shipping 12-01; fix is its own story with its own evidence - Karol + agent.

## Decisions deferred

- Rendered command copies committed vs build products - resolved 2026-07-03 by WLA-12-01 (committed; drift is a `dw check` ERROR) - see "Decisions made".
- Who owns the pack copy step into `~/.holdspeak/plugin_packs/` (doctor vs install script) - decide in WLA-12-02.
- Whether WLA-12-07 splits release into its own story - trigger if Desk/doctor halves grow - default is split rather than rush.
