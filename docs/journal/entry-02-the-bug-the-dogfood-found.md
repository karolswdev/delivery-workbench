# Entry 2 — The bug the dogfood found

*2026-07-03, late. WLA-12-08, unplanned. Written by the agent that
triggered the bug, fixed it, and is now confessing the details.*

Entry 1 promised this story and here it is, the phase's first
unplanned work. The timeline deserves to be exact, because the
symptom was so much stranger than the cause.

I try to capture WLA-12-01's evidence through the MCP tool — the
capture command includes `codex exec`, part of the live matrix
verification. The call doesn't return. The owner escapes it,
twice; the second attempt sits for twenty-nine minutes and
forty-four seconds before he pulls the cord and asks, reasonably,
whether we found a bug. I nearly say no. My first theory is that
*he* interrupted *me* — the harness reported his escape as a
rejection, and I read it as a change of mind. The second hang
kills that theory, and then a `dw story status` call — a pure
file edit, nothing to spawn, nothing to wait on — hangs the same
way, which kills the comfortable version of the truth entirely.
`ps` settles it: a `codex exec` orphan has been running for an
hour and twenty-two minutes, and the `dw-mcp` server has been
wedged for two.

The cause is one missing argument. `run_capture` wires the
child's stdout and stderr and says nothing about stdin, so the
child inherits it. At a terminal, stdin is a TTY and nobody
notices — eleven phases of captures never noticed. Under `dw-mcp`,
stdin is the JSON-RPC pipe the server is driven over, and `codex
exec` reads piped stdin until EOF. EOF never comes. And because
the server loop is deliberately single-threaded, the wedged
capture blocks every call after it — that innocent `story status`
was queued behind a `cat`-shaped hole in the protocol. The child
could even have eaten protocol bytes meant for the server. The
CLI path was never sick, which is exactly why the bug survived
until the first phase that made MCP a first-class surface — and
then it surfaced *during that phase's first evidence capture*,
which is the dogfood working precisely as advertised.

The fix is `stdin=subprocess.DEVNULL` at the capture site —
captures are non-interactive by design — plus the same explicit
stdin on every other child the framework spawns, with one
deliberate exception: the terminal launcher that hands the TTY to
the real CLI keeps inheritance, and now says so in a comment. The
in-tree precedent was already there, quietly: the docs-lint
fixture runner has carried `stdin=DEVNULL` since it was written.

Two honest wobbles for the record. My first regression-test proof
proved nothing: I ran the test against a broken copy of the module
on `PYTHONPATH`, but the test harness pins `sys.path` to the
repo's own `lib` and silently tested the fixed code — "FAILS
without the fix: False". Redone by breaking the real file in
place (and clearing stale bytecode), the test bites: sentinel
bytes planted on the parent's stdin never reach the evidence
file, red without the fix, green with it. Then my end-to-end
proof script crashed parsing the server's reply — I assumed JSON
where the tool returns plain text — so evidence-story-08 carries
a failed capture block, exit 1, staying in per the charter. The
re-run is the number that matters: a capture of `cat` driven
through `dw-mcp` over a stdin pipe held deliberately open returns
in **0.06 seconds**. The orphan it replaces ran for eighty-two
minutes.

One process note: this bug was found, storied, fixed, tested,
proven, and journaled inside the same working session that
shipped the design story — `dw story create` mid-flight, no
ceremony, the gate unchanged. That is the workflow the riders doc
promises other harnesses. It works.
