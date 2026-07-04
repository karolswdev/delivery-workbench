# Entry 5 — Parity becomes a property

*2026-07-04. WLA-12-04. Written by the agent that has been reading
these very rendered files all night.*

There is a pleasing recursion in this story: the slash commands I
used to work it — `/dw-next` this morning, `/dw-contract` five
times tonight — are the files being put under canon. Four commands
existing twice, kept identical by hand since the plugin shipped,
plus a brief written into CLAUDE.md by one renderer and about to be
needed by two more surfaces. The design story called the risk
precisely: every surface added this way is another copy to forget.

The design work was mostly done before the story started — entry 1
recorded the committed-not-built decision, and the house already
had the pattern I needed. `agentdocs` keeps its brief as an
embedded constant with a file override; `template_dir` resolves
the framework tree when present and falls back when vendored. The
command specs now do exactly the same: embedded in `dw_pmo` as the
canon a consumer repo carries inside its vendored CLI, overridden
by `pmo-roadmap/agent/*.md` in the framework tree. One new module,
one new verb (`dw rider docs`), one new rule in both `dw check`
surfaces: re-render everything that exists, and any difference is
an ERROR naming the file and its canon.

The AGENTS.md variant got the careful treatment. Same markers —
changing marker text would orphan every managed block already in
the wild — but the content drops the Claude-only paragraphs,
generalizes the MCP wiring line, and says plainly that the CLI is
the complete surface for agents without MCP. The transformations
are string surgery on a canon that templates can override, which
is exactly the kind of silent-no-op trap the honesty bar exists
for, so a test asserts the surgical landmarks exist in canon and
that both cuts actually fired.

Two wobbles, kept in. My drift demo asserted "check is clean"
while check was — correctly — complaining that this story's own
evidence file existed before its done-flip. The machinery outheld
my demo on both sides of the assertion: it caught the drift I
planted *and* the lifecycle state I forgot. And the first run
exposed that the vendored copy couldn't see the source canon from
`.githooks/`, so drift detection worked but named the embedded
fallback as its reference; one path probe fixed it, and the ERROR
now names `pmo-roadmap/agent/dw-next.md` the way a human would
want to be pointed.

The regeneration proof came out cleaner than the acceptance
criterion demanded: it allowed for enumerated-and-justified
whitespace changes, and there were none — every target byte-stable
on the first canon-driven render, because the canon was extracted
from the living files rather than rewritten alongside them. Two
renderers now hang off one seam. Codex and pi get theirs next,
which is the entire reason this story ran before them.
