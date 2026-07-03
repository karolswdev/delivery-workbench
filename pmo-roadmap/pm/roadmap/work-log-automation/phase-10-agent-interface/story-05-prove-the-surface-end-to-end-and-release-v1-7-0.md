# WLA-10-05 - Prove the surface end-to-end and release v1.7.0

- **Project:** work-log-automation
- **Phase:** 10
- **Status:** backlog
- **Depends on:** WLA-10-04
- **Unblocks:** (optional)
- **Owner:** unassigned

## Problem

Protocol tests prove frames; they do not prove that a real agent
session can orient, work, and prove a story through the MCP surface
alone. The phase closes with that demonstration — and with v1.7.0
carrying the new surface through the same release machinery phases
7 and 9 built.

## Scope

- **In:** An end-to-end exercise against a real client: the server
  registered in a live MCP client (Claude Code counts — this
  session, or a scripted client speaking the full handshake if a
  live one is unavailable at execution time, honestly labeled),
  driving a real story in a fixture or scratch repo from
  orientation to done via tools only, captured as evidence. The
  v1.7.0 release: version bump in the single source, CHANGELOG
  section for Phase 10 linking the final summary, parity tests
  green across every surface (now including the plugin manifest's
  mcpServers), both distribution smokes re-run at 1.7.0, annotated
  local tag, phase close with final summary. Push/publication
  follow the standing authorization from v1.6.0 (push, release
  with artifacts, formula sha stamp, tap update) unless the user
  says otherwise at execution time.
- **Out:** New tools beyond the contract, PyPI activation (still
  pending the one-time registration).

## Acceptance criteria

- [ ] Evidence captures a real client session (or an honestly
  labeled scripted-client fallback) completing the orientation →
  flip → capture → done loop via MCP tools only.
- [ ] Every version surface reports 1.7.0 under the parity tests;
  the full battery and both smokes are green at the release
  commit.
- [ ] `git tag -l v1.7.0` shows the annotated tag; `dw verify
  --all` passes at it.
- [ ] Phase 10 final summary closes the phase in the same commit
  as this story's flip.

## Test plan

- **Unit:** parity family at 1.7.0.
- **Integration:** full `pmo-roadmap/tests/` battery.
- **Manual / device:** the live client session itself.

## Notes / open questions

- If the live-client leg runs inside this repo, keep the exercise
  in a scratch fixture so the demo never mutates the real roadmap.
