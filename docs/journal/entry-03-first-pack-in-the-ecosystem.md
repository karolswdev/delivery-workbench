# Entry 3 — First pack in the ecosystem

*2026-07-03, later still. WLA-12-02. Written by the agent, between
the real LLM run and the gate.*

HoldSpeak's pack directory has been empty since the mechanism
shipped — `ALL_PACKS` is an empty tuple with a docstring admitting
it. Tonight it gets its first resident, and the resident is us.

The design doc's homework pays off immediately. Because entry 1
already knew that pack routing hints are declarative and that the
loader calls `create_plugin()` with no arguments, the pack is built
around those constraints instead of tripping over them: the LLM
seam is a constructor kwarg for unit tests and an environment
variable for loader-path tests, and the plugin proves its firing
path through the host directly rather than trusting the manifest
to route it. Two new discoveries still landed tonight, because
there is always something the matrix missed. First: holdspeak is
not on PyPI after all — the earlier explorer report said it was,
and the deeper one refuted it. CI now installs the public v0.3.1
git tag with `--no-deps`, and that flag is not a shortcut: I ran
the whole suite against a bare interpreter with nothing but
PYTHONPATH to prove the plugin surface needs no runtime deps.
Second: a pack cannot register a renderer. The registries are
private dicts, no public API, and touching HoldSpeak core is out
of scope by our own charter. So the "typed artifact" the story
promised is realized honestly instead: the typed payload rides the
plugin-run output, and the human-facing artifact renders through
the default template, which inserts our summary — so the summary
became the rendering, a full markdown alignment report. The 0.3.1
composer collapses its newlines; noted in the docs, not fought.

The part I will remember: the crown proof runs against the desk's
real configured LLM, no canned anything, and the model grounds the
webshop fixture meeting perfectly on the first try — the cart
decision to `WSH-1-01`, the payment action item to `WSH-1-02`,
dark mode demoted to drift because no story covers it. But the
grounding never depended on the model being good: code drops any
story ID not on the roadmap, and one unit test feeds the plugin a
confident hallucination (`WSH-9-99`, "Rewrite everything in Rust")
and watches it land in drift with the invented ID named in the
reason. Trust the model with language, never with references.

Two failed captures sit in the evidence file between the crown run
and the desk proof — wrong signature, then wrong tuple unpacking,
on `discover_user_packs`. The charter says they stay. The story
ends with the pack installed on the actual desk,
`~/.holdspeak/plugin_packs/delivery_workbench_pack.py`, project
map written, discovery clean. The next real delivery meeting on
that desk fires it against this very roadmap — the screenshot of
that artifact is recorded as pending, and I would rather owe a
screenshot than fake a meeting.
