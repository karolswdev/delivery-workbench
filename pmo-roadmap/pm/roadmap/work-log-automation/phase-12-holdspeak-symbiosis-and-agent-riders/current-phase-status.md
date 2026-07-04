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
| WLA-12-02 | Build the HoldSpeak roadmap-alignment synthesizer | done | [story-02-holdspeak-roadmap-alignment-synthesizer](./story-02-holdspeak-roadmap-alignment-synthesizer.md) | [evidence-story-02](./evidence-story-02.md) |
| WLA-12-03 | Build the HoldSpeak story actuator | done | [story-03-holdspeak-story-actuator](./story-03-holdspeak-story-actuator.md) | [evidence-story-03](./evidence-story-03.md) |
| WLA-12-04 | Collapse the agent-surface duplication behind a canonical brief | done | [story-04-canonical-brief-collapse-duplication](./story-04-canonical-brief-collapse-duplication.md) | [evidence-story-04](./evidence-story-04.md) |
| WLA-12-05 | Prove the Codex rider end-to-end | done | [story-05-codex-rider](./story-05-codex-rider.md) | [evidence-story-05](./evidence-story-05.md) |
| WLA-12-06 | Prove the pi rider end-to-end | done | [story-06-pi-rider](./story-06-pi-rider.md) | [evidence-story-06](./evidence-story-06.md) |
| WLA-12-07 | Desk presence, doctor awareness, and release | done | [story-07-desk-presence-doctor-release](./story-07-desk-presence-doctor-release.md) | [evidence-story-07](./evidence-story-07.md) |
| WLA-12-08 | Fix evidence-capture stdin inheritance under dw-mcp | done | [story-08-mcp-capture-stdin-fix](./story-08-mcp-capture-stdin-fix.md) | [evidence-story-08](./evidence-story-08.md) |
| WLA-12-09 | Release v1.9.0 and close the phase | done | [story-09-release-and-close](./story-09-release-and-close.md) | [evidence-story-09](./evidence-story-09.md) |

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
held-open pipe in 0.06s. WLA-12-02 then landed the first real pack
in HoldSpeak's ecosystem: the roadmap-alignment synthesizer proven
through real discovery, the real host, and the desk's real LLM
(both fixture story IDs grounded, hallucinations demoted to drift
by code, not trust), 10 tests green plus a `--no-deps` CI job
pinned to the public v0.3.1 tag, and the pack installed live on
the desk. The renderer-registration assumption died on contact
(private registries, no public API) — the summary became the
rendering, recorded in `docs/riders.md`. WLA-12-03 then stacked
the two consent systems: an actuator whose model produces fields
(never argv), a gated connector admitting exactly two `dw story`
argv prefixes, HoldSpeak's approval/policy/parity stack above, and
the captured crown proof underneath — an approved done-flip on an
evidence-less story refused by the gate with its banner verbatim,
audit `proposed -> approved -> failed`. 23 pack tests green, both
packs discovered live on the desk. WLA-12-04 then collapsed the
duplication: command-spec canon embedded in `dw_pmo/riderdocs.py`
(source files override in the framework tree), `dw rider docs`
regenerates every surface, drift is now a `dw check` ERROR on both
the CLI and MCP surfaces, and the AGENTS.md brief variant exists
behind the same markers. First canon regeneration: byte-identical
everywhere. WLA-12-05 then proved the Codex rider end-to-end:
`dw rider install codex` wires AGENTS.md + repo-level skills +
printed MCP snippet idempotently, the full story loop ran under
real Codex in a gated fixture (trailers stamped, `dw verify`
clean), and coexistence with HoldSpeak's hook is captured in one
run — hook reporting the session, gate stamping the commit. Two
live findings: codex's `workspace-write` sandbox keeps `.git`
read-only (automation uses `danger-full-access`; the model can't
tamper with gate hooks by default), and hooks are trust-gated
(their template is fine; trust once or bypass deliberately).
Codex itself refused to certify a contract after staging failed —
"would not be honest" — which says the contract reads as rules,
not tickboxes. WLA-12-06 then closed the phase's central claim:
the full loop ran under pi — a context file and a shell, no MCP,
no slash commands — with the commands rendered verbatim as
`.pi/prompts/` templates (pi's format is byte-identical to canon),
purity mechanically checked, the shared-AGENTS.md answer recorded,
and `docs/riders.md` carrying the "any other harness" recipe the
proof earned. Three harnesses, three model vendors, one gate.
WLA-12-07 then landed the last features: `dw doctor` reports a
`rider:` line per surface (wired / not-installed / drifted-fails),
`.hs/context.md` carries a live-rendered roadmap block outside the
byte-drift rule, and the real Desk shows the rails on the project
record — proven through the documented API with screenshots, the
unclickable-tab limit stated plainly. The release split into
WLA-12-09 per the story's own pre-decision. One story to close:
ship v1.9.0 and close the phase over it.

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
- 2026-07-03 - Pack copy step is a documented `cp` (docstring + `docs/riders.md`), not machinery; `dw doctor` learns to check the installation in WLA-12-07 (resolves the deferred question) - WLA-12-02.
- 2026-07-03 - holdspeak is NOT on PyPI (corrects an earlier report); CI pins the public v0.3.1 git tag with `--no-deps`, test-proven sufficient for the stdlib-only plugin surface - WLA-12-02.
- 2026-07-03 - Packs cannot register renderers/artifact types on 0.3.1; the typed payload rides the plugin-run output and the rich summary is the rendered body; upstream renderer-registration seam noted as a candidate contribution, not worked around - WLA-12-02.
- 2026-07-04 - One plugin per pack file (0.3.1 loader exports one MANIFEST): the actuator ships as its own `delivery_workbench_actuator_pack.py` beside the synthesizer - WLA-12-03, amends the story's "same file" wording.
- 2026-07-04 - Connector resolves `dw` as the target repo's own `.githooks/dw` first, installed `dw --root` second (resolves the story's open question); argv is always built by the connector from the stored payload, never by the model - WLA-12-03.
- 2026-07-04 - Command-spec canon embedded in `dw_pmo` with `pmo-roadmap/agent/*.md` as the source-tree override (the agentdocs/template pattern), so consumer repos drift-check with only the vendored CLI - WLA-12-04.
- 2026-07-04 - AGENTS.md keeps the same managed markers (never orphan deployed blocks) with variant content per filename; AGENTS.md files are created by rider installers, not by regeneration - WLA-12-04.
- 2026-07-04 - Brief wording deliberately unchanged this story so the regeneration proof stays pure; the release story owns any wording refresh - WLA-12-04.
- 2026-07-04 - Codex automation runs the loop under `-s danger-full-access` (workspace-write keeps `.git` read-only — verified live); interactive users approve commits instead - WLA-12-05.
- 2026-07-04 - HoldSpeak's Codex hook template works on codex-cli 0.142.4; the one-time hook-trust gate is codex's, not theirs — trust interactively or bypass deliberately in vetted automation - WLA-12-05.
- 2026-07-04 - One AGENTS.md serves every AGENTS.md-reading harness (single filename, forks impossible); the agents variant stays CLI-first with MCP as one optional aside (resolves WLA-12-06's open question) - WLA-12-06.
- 2026-07-04 - pi loop provider: openrouter, key sourced from the operator's shell at run time, never printed or stored in evidence - WLA-12-06.

## Decisions deferred

- Rendered command copies committed vs build products - resolved 2026-07-03 by WLA-12-01 (committed; drift is a `dw check` ERROR) - see "Decisions made".
- Who owns the pack copy step into `~/.holdspeak/plugin_packs/` (doctor vs install script) - resolved 2026-07-03 by WLA-12-02 (documented `cp`; doctor checks it in WLA-12-07) - see "Decisions made".
- Whether WLA-12-07 splits release into its own story - resolved 2026-07-04: the halves grew, WLA-12-09 owns release + close - see story 07's amendment.
