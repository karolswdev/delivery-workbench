# WLA-18-02 - dw story show — one story, whole

- **Project:** work-log-automation
- **Phase:** 18
- **Status:** backlog
- **Depends on:** WLA-18-01
- **Unblocks:** WLA-18-03
- **Owner:** unassigned

## Problem

The CLI can list stories, create them, and mutate them — but cannot
*browse one*. "Show me WLA-17-03: its status and why, its body, its
evidence, its captured runs, where its trace lives" takes four file
reads and tree knowledge today. The workbench story route already
assembles most of this, but inline — there is no shared core a CLI
verb or an MCP tool could call.

## Scope

- **In:** `api.py` — `story_detail(project, phase, selector, root)`:
  everything `story_context` carries plus `story_markdown`,
  `evidence_markdown`, `captured_runs` (via
  `evidence.parse_captured_runs`: timestamp/command/exit per run),
  `status_token`/`status_note`, and the `paths`/`links` shape from
  WLA-18-01. `workbench.py` — the existing
  `/api/projects/<slug>/stories/<id>` route refactors onto
  `story_detail` (response stays a superset-compatible shape;
  additions only). CLI — `dw story show <project> <phase> <story>
  [--json]`: human rendering (header, status + note, bodies,
  captured-runs table, trace paths) and the machine object.
- **Out:** MCP wiring (WLA-18-03); trace timeline merging (the
  `trace` paths point; `dw context --trace` and the trace route
  already exist for events).

## Acceptance criteria

- [ ] `dw story show work-log-automation 17 3` prints the story
  whole: ID/title, normalized status + note, header fields, story
  body, evidence body, one line per captured run
  (timestamp/command/exit), and trace paths.
- [ ] `--json` returns the same as one object, `paths`/`links`
  included; selector forms match `find_story` (id, number,
  filename).
- [ ] The workbench story route serves `story_detail` — one
  implementation, no drift; existing workbench story-route tests
  pass with additive-only changes.
- [ ] Missing story file / missing evidence render as honest
  absences (never a crash, never invented content).
- [ ] `/usr/bin/python3 pmo-roadmap/tests/dw-core-tests.py` green.

## Test plan

- **Unit:** story_detail shape (fixture with evidence + captured
  run; fixture without evidence); route parity (route response ⊇
  story_detail keys).
- **Integration:** CLI smoke on this repo's real WLA-17 stories.
- **Manual / device:** n/a.

## Notes / open questions

- Human rendering keeps the greppable-first house style: one fact
  per line, sections in trace-chain order (intent → proof).
