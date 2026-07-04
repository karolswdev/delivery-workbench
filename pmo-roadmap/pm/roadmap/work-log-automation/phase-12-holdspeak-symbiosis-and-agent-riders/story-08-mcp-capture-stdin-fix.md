# WLA-12-08 - Fix evidence-capture stdin inheritance under dw-mcp

- **Project:** work-log-automation
- **Phase:** 12
- **Status:** done
- **Depends on:** none
- **Unblocks:** WLA-12-02 (MCP-hosted agents capturing evidence)
- **Owner:** unassigned

## Problem

Found live while shipping WLA-12-01: `run_capture`
(`lib/dw_pmo/evidence.py`) spawns the captured command with
`stdout` and `stderr` wired but stdin untouched, so the child
inherits the parent's stdin. From the CLI that is a TTY and
harmless — eleven phases of captures never noticed. Under
`dw-mcp`, stdin is the JSON-RPC pipe the server is being driven
over: a child that reads stdin (`codex exec` reads piped stdin
until EOF) blocks on a pipe that never closes. Because the server
loop is single-threaded, the wedged capture also blocks every
subsequent MCP call — observed twice at ~29 minutes each before
the operator escaped, leaving an orphaned `codex exec` running for
over an hour. Worse than the hang: a stdin-reading child can
consume JSON-RPC bytes meant for the server. The phase that makes
MCP a first-class rider surface cannot ship on a capture path
that wedges its own server.

## Scope

- **In:** `stdin=subprocess.DEVNULL` on the `run_capture` spawn in
  `pmo-roadmap/lib/dw_pmo/evidence.py` (captures are
  non-interactive by design); the same explicit stdin on the other
  child-spawn sites in `dw_pmo` (`gitio.py`, `paths.py`,
  `launcher.py`, `trace.py`, `docslint.py` `_sh`) so no framework
  child ever inherits a host's stdin — `docslint.py`'s fixture
  runner already does this, making it the in-tree precedent; a
  regression test in `pmo-roadmap/tests/dw-core-tests.py` proving
  a captured `cat` completes and records none of the parent's
  stdin bytes; vendored `.githooks/dw_pmo/` copies synced (the
  `update.sh` copy step); journal entry 2.
- **Out:** MCP server concurrency or per-request timeouts (the
  single-threaded loop is a deliberate simplicity choice — this
  fix removes the only known way to wedge it); client-side
  cancellation semantics; anything in the Codex CLI.

## Acceptance criteria

- [ ] The regression test simulates the server condition (parent
  stdin swapped to a pipe holding sentinel bytes) and proves the
  captured child exits promptly and the sentinel never appears in
  the evidence file.
- [ ] Every `subprocess` call in `dw_pmo` passes explicit
  `stdin` — verifiable by grep, no call site relies on
  inheritance.
- [ ] `pmo-roadmap/lib/dw_pmo/` and `.githooks/dw_pmo/` are
  byte-identical after the fix.
- [ ] A real `dw evidence capture` of a stdin-reading command
  (`cat`) driven through `dw-mcp` over a held-open stdin pipe
  returns within seconds, response captured as evidence.
- [ ] `dw-core-tests.py` passes in full.

## Test plan

- **Unit:** new `test_capture_never_hands_stdin_to_the_child` in
  `dw-core-tests.py`, plus the full existing suite.
- **Integration:** `pmo-roadmap/tests/mcp-server.sh`.
- **Manual / device:** drive `.githooks/dw-mcp` by hand over a
  FIFO that stays open, call `dw_evidence_capture` with `cat`,
  observe the response arrive instead of the historic 29-minute
  wedge; capture the run.

## Notes / open questions

- `git` children (`gitio`, `paths`, `trace`, `launcher`) never
  read stdin in the modes we invoke, so their fix is defensive,
  not behavioral. Recorded here so the uniform rule is deliberate:
  a framework that may be hosted by a stdio JSON-RPC server hands
  its stdin to no one.
