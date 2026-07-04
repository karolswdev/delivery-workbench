# WLA-12-06 - Prove the pi rider end-to-end

- **Project:** work-log-automation
- **Phase:** 12
- **Status:** backlog
- **Depends on:** WLA-12-04
- **Unblocks:** WLA-12-07
- **Owner:** unassigned

## Problem

pi is the minimalist of the three typing surfaces: a context file
and a shell, deliberately no MCP. That makes it the honest test of
a claim this framework has always made — that the rails are just
git and a CLI, and any agent that can run commands can work a
story. If the loop needs MCP or slash-command sugar to be workable,
the pi rider will expose it; if it does not, the pi rendering of
the brief becomes the reference "any harness" document, the one a
user of some fifth tool we never heard of would follow.

## Scope

- **In:** A pi renderer on the WLA-12-04 seam and
  `dw rider install pi`: the AGENTS.md/context block rendered
  CLI-first — no MCP references, no slash commands, the four
  workflows written as plain `dw` invocations with their exit-code
  meanings — plus whatever native extension surface the WLA-12-01
  matrix verified pi actually has (commands/extensions if real,
  context-only if not; the matrix decides, this story implements).
  The proof: the full story loop under pi in a rails fixture repo,
  evidence-captured, with the contract certification done by the
  human as always. `docs/riders.md` gains the pi how-to and an
  explicit "any other harness" section derived from it. Journal
  entry written in the moment, especially where pi's minimalism
  pinched or didn't.
- **Out:** Codex (WLA-12-05); building pi extensions beyond what
  the verified matrix supports; doctor matrix (WLA-12-07).

## Acceptance criteria

- [ ] `dw rider install pi` wires a fixture repo idempotently with
  the CLI-first brief; no MCP or Claude-isms appear in the rendered
  output (checked, not eyeballed).
- [ ] The full story loop runs under pi in the fixture repo;
  evidence records the real run.
- [ ] `docs/riders.md` contains the "any other harness" section
  and it is consistent with what the pi proof actually required.
- [ ] Renderer/installer tests in CI; docs-lint passes.

## Test plan

- **Unit:** renderer output (assert absence of MCP/slash-command
  references); installer idempotency.
- **Integration:** drift rule covers the pi-rendered surface.
- **Manual / device:** the live pi loop, evidence-captured.

## Notes / open questions

- If pi turns out to read AGENTS.md with different precedence than
  Codex (both claim it), the shared-file case — one repo, both
  harnesses — needs a recorded answer in `docs/riders.md`.
