# Adoption friction log — fridgr (WLA-8-04)

Target: scratch clone of `~/dev/code/fridgr` (Pantrybot; 133 commits,
Next.js + Express monorepo, pre-existing `CLAUDE.md` and its own
`EXP-*` planning conventions). Adoption run 2026-07-03 following the
README's three-command path verbatim, driven headlessly by an agent —
exactly the audience the quickstart targets. Every deviation from
"the documented commands just worked" is an entry.

Severity vocabulary: **blocker** (path fails without operator
intervention) / **papercut** (works, but costs time or confidence) /
**docs** (behavior is fine, documentation sets the wrong expectation).

## Entries

1. **(papercut)** `adopt-project.sh --agent claude` runs discovery
   with zero progress output and no timeout. For ~10 minutes the only
   liveness signals were a `claude -p` process in `ps` and a 0-byte
   `adoption-discovery.md`. An operator cannot distinguish "working"
   from "hung"; a supervising agent has to poll process tables.
   Wanted: a heartbeat line (or at least a "this typically takes
   5–15 minutes" note at launch) and a `--timeout`.

2. **(docs)** The README quickstart shows
   `--with-intake --agent claude` without saying that (a) intake
   silently falls back to placeholder mode when stdin is not a TTY,
   leaving a "mostly unanswered" intake the discovery then has to
   flag, (b) discovery spawns a nested `claude` CLI needing its own
   auth in headless/CI contexts, and (c) the step takes minutes, not
   seconds.

3. **(papercut)** The sandboxed discovery agent cannot write its own
   report (read-only permission mode is by design), so the wrapper
   captures stdout into `adoption-discovery.md` — including the
   agent's meta-preamble about being blocked ("here is the full
   report, ready to be saved verbatim…"). The canonical report file
   ships with confusion at the top, and the agent itself believed
   the hand-off had failed. The section parser in `dw adopt`
   tolerated it, but nothing guarantees agents keep the headings
   intact around such preambles. Wanted: the discovery prompt should
   tell the agent its stdout IS the report (emit nothing else), or
   the wrapper should strip pre-`#` content.

4. **(papercut)** The discovery agent was also denied executing
   `.githooks/dw doctor|check` inside its sandbox, so the report's
   verification-command table carries "unverified here" caveats for
   the very rails the adoption just installed. The default sandbox
   arguably should allowlist the freshly installed read-only `dw`
   orientation commands.

5. **(docs)** `install.sh` unconditionally writes
   `pm/roadmap/{roadmap-builder,PMO-CONTRACT}.md` to the target —
   correct for consumers, but when run against this source
   repository itself (snapshot refresh during WLA-8-02) it scaffolds
   a stray root `pm/` tree that must be deleted by hand. The
   self-hosting refresh path deserves either a flag or a documented
   convention.

## What worked without friction

For the record, the core loop was clean on first contact with a
foreign repo: `install.sh` (hooks, CLI, managed CLAUDE.md block
appended below the project's existing content), `dw adopt` preview →
`--apply` (3 phases, 6 stories from the report), `dw doctor` green,
`dw check` ok, `dw next` pointing at FR-1-01, evidence capture,
contract, gated commit with trailers and archive — and `dw verify
--all` passing with all 133 pre-adoption commits skipped as
pre-epoch, exactly as the remote verification contract specifies.

## Triage (WLA-8-05, 2026-07-03)

| # | Verdict | Action taken / rationale |
|---|---|---|
| 1 | fix-now (partial) + defer | `adopt-project.sh` now announces the agent launch with expected duration and where the report lands (proof: the lines print before the agent exec). A `--timeout` flag and mid-run heartbeat are **deferred** — they need process supervision the wrapper doesn't have yet; trigger: next long discovery run. |
| 2 | fix-now | README quickstart now sets expectations: stdout-captured report, 5–15 minute duration, headless auth requirement, placeholder-intake behavior. Docs-lint clean. |
| 3 | fix-now | The discovery prompt template gained a "How to deliver the report" section: stdout IS the report, emit only the report starting at the `#` title, never attempt the write. Proof: rendered prompt in a fixture carries the section. Wrapper-side stripping of pre-title content was **declined** — risk of eating legitimate report content outweighs the cosmetic gain, and the prompt fix addresses the cause. |
| 4 | defer | Allowing the sandboxed discovery agent to run the read-only `dw doctor/check/context` needs per-CLI permission plumbing (`--allowedTools` equivalents differ between claude and codex). The report's "unverified here" caveats stay honest meanwhile. Trigger: next external adoption run. |
| 5 | fix-now | `install.sh` detects self-hosting (source inside target, physical-path comparison — `git rev-parse` returns physical paths) and skips the root `pm/roadmap` canon scaffold; external installs unchanged. Regression case added to `tests/adoption-discovery.sh` covering both directions. |

All five entries triaged; counts match the log. Deferred items are
mirrored in the phase status "Decisions deferred" section.
