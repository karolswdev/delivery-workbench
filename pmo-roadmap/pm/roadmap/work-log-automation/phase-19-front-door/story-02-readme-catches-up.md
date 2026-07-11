# WLA-19-02 - The README catches up with the shipped surface

- **Project:** work-log-automation
- **Phase:** 19
- **Status:** done
- **Depends on:** none
- **Unblocks:** WLA-19-03
- **Owner:** unassigned

## Problem

The README is the front door and it describes the house two phases
ago: it counts nine MCP tools where phase 18 shipped twelve, its
CLI table has no row for `dw board`, `dw holds`, or `dw story show`,
it never links `docs/interop.md` (the one versioned read-surface
contract), it says "sixteen phases" with eighteen closed, and it
hand-maintains "Current version: 1.12.0" on a line the parity tests
do not guard — the exact line most likely to ship stale.

## Scope

- **In:** README only — MCP tool census updated to twelve (matching
  docs/mcp.md), CLI table rows for the board/holds/story-show
  verbs, a Documentation-section link to docs/interop.md, phase
  count made current (or phrased so it cannot rot), a short prose
  mention that parked work and the kanban board exist (phase 17)
  and that every element is browsable (phase 18), and the
  hand-maintained version line removed in favor of the badge from
  WLA-19-01 (default) or wired into the parity test.
- **Out:** restructuring the README; docs/*.md content (mcp.md and
  interop.md verified current); CHANGELOG (release story's job).

## Acceptance criteria

- [ ] Every MCP tool the server registers appears in the README
  list; the stated count matches.
- [ ] `dw board`, `dw holds`, and `dw story show` each have a CLI
  table row consistent with `--help`.
- [ ] `docs/interop.md` is linked from the Documentation section.
- [ ] No hardcoded version string remains in the README that the
  parity family does not check.
- [ ] Full core suite green.

## Test plan

- **Unit:** core suite.
- **Integration:** grep-based check in the evidence capture: README
  names all twelve MCP tools and the three CLI verbs; no
  `Current version:` literal survives.
- **Manual / device:** read the rendered README top to bottom as
  the stranger it is written for.

## Notes / open questions

Default per the phase decision: remove the version line rather than
automate it — the PyPI badge states the number live.
