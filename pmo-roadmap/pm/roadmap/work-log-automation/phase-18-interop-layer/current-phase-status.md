# Phase 18 - Every element answers — the interop layer

**Last updated:** 2026-07-11.

## Goal

The board became the picture in phase 17; this phase makes every
element on it a door. Owner direction: "each of those elements —
whether backlog, whether on the board — should be browsable; it
should expose things like evidence." Concretely: board cards and
holds-ledger entries carry their receipts (paths) and links (API
routes) so any consumer walks card → story → evidence → trace
without knowing the tree layout; `dw story show` browses one story
whole from the CLI; MCP gains the read surface (`dw_board`,
`dw_holds`, `dw_story_show`) so agents interop without shelling
out; and one versioned contract document names every read surface
and is pinned by tests.

## Scope

- **In:** `board.py` (cards + lanes gain `paths`/`links`; model gains
  `kind` + `schema_version`), `api.py` (`parked_summary` entries gain
  the same; a shared `story_detail()` powering the workbench story
  route, the new CLI verb, and MCP), `workbench.py` (story route
  refactored onto `story_detail`, board route unchanged in shape but
  stamped), CLI (`dw story show [--json]`), `mcpserver.py` (three
  new read-only tools), docs (`docs/interop.md` — the read-surface
  contract: CLI `--json` verbs, workbench GET routes, MCP tools,
  schema versions), tests (shape pins for links/paths, story_detail
  round-trip, MCP tool wiring, docs↔code parity).
- **Out:** any write-path change (the interop layer is READ-ONLY;
  mutations stay preview→apply and the MCP mutation stance is
  unchanged); authentication/remote transport (the workbench stays
  localhost/tailnet); feed schema changes (`dw state` is already
  contracted in docs/mission-control.md §1).

## Exit criteria (evidence required)

- [x] Every board card and every `dw holds` entry carries
  repo-relative `paths` (story, evidence, phase status) and
  workbench `links` (story, trace) — pinned in tests; the board
  model is stamped `kind` + `schema_version: 1` (WLA-18-01 —
  [evidence](./evidence-story-01.md): 201 tests green incl. the
  no-rot link walk; live HTTP walk card → story → evidence →
  trace with zero tree knowledge).
- [x] `dw story show <project> <phase> <story>` prints one story
  whole — header fields, normalized status + note, story body,
  evidence body, captured runs, trace paths — and `--json` returns
  the same as one object; the workbench story route serves the
  same `story_detail` core (WLA-18-02 —
  [evidence](./evidence-story-02.md): 204 tests green + live browse
  of WLA-17-03 with its real captured runs).
- [x] MCP exposes `dw_board`, `dw_holds`, `dw_story_show` as
  read-only tools returning the same models as the CLI `--json`
  verbs; refusals identical (WLA-18-03 —
  [evidence](./evidence-story-03.md): 207 tests green incl.
  core-parity, refusal-parity, and the read-only census;
  mcp-server.sh live round-trip green).
- [ ] `docs/interop.md` names every read surface (CLI, HTTP, MCP)
  with its schema version; a test pins the doc's inventory against
  the code so a new surface cannot ship undocumented (WLA-18-04).

## Story status

| ID | Story | Status | Story file | Evidence |
|---|---|---|---|---|
| WLA-18-01 | Self-describing cards: the board and the ledger carry their receipts | done | [story-01-self-describing-cards](./story-01-self-describing-cards.md) | [evidence-story-01](./evidence-story-01.md) |
| WLA-18-02 | dw story show — one story, whole | done | [story-02-story-show](./story-02-story-show.md) | [evidence-story-02](./evidence-story-02.md) |
| WLA-18-03 | The MCP read surface: board, holds, story | done | [story-03-mcp-read-surface](./story-03-mcp-read-surface.md) | [evidence-story-03](./evidence-story-03.md) |
| WLA-18-04 | The interop contract, versioned and pinned | backlog | [story-04-interop-contract](./story-04-interop-contract.md) | - |

## Where we are

WLA-18-03 done (2026-07-11): the MCP read surface — `dw_board`,
`dw_holds` (text via the shared `parked_lines` renderer, extracted
so CLI and MCP cannot drift), `dw_story_show`; structuredContent
byte-equal with the core, refusals identical, read-only census
pinned; docs/mcp.md gained the Browse table, the CLAUDE block
regenerated and the snapshot synced in the same commit. 207 core
tests green. Earlier: WLA-18-02 (`story_detail` + `dw story show`),
WLA-18-01 (self-describing cards). Next: WLA-18-04 (the interop
contract) — the last story, then the phase closes.

## Active risks

| Risk | Likelihood | Mitigation | Stop signal |
|---|---|---|---|
| Interop layer grows a write path by accident | low | every new surface is GET/read-only; MCP tools call read functions only; the WLA-15 fitness guard patterns extend | any new tool/route calling a plan_* or apply |
| Link rot between board JSON and workbench routes | medium | links are derived from one helper, pinned by a test that resolves them against handle_api | a pinned link 404ing in tests |
| Schema stamped but then mutated silently | medium | shape-pinning tests on the stamped models; version bumps deliberate | a shape test edited without a version bump |
| Doc inventory drifts from code | medium | WLA-18-04 parity test enumerates routes/tools/verbs from code and greps the doc | parity test weakened |

## Decisions made (this phase)

- 2026-07-11 - Phase scaffolded with `dw phase create` - keeps roadmap structure consistent - CLI.
- 2026-07-11 - The interop layer is read-only; certification and mutation stances are untouched - interop means seeing clearly, not new hands - owner charter (phase 15 precedent).
- 2026-07-11 - Links point at the workbench HTTP routes (the one server), paths are repo-relative - consumers with a filesystem use paths, consumers over HTTP use links, both derived from one helper - design.

## Decisions deferred

- Remote/authenticated transport for the read surface - trigger: a consumer beyond localhost/tailnet - default: the workbench serving model stands.
- Webhooks/SSE push for board changes - trigger: a consumer polling painfully - default: pull.
- A GraphQL-ish query layer - trigger: real demand - default: the fixed routes are the contract.
