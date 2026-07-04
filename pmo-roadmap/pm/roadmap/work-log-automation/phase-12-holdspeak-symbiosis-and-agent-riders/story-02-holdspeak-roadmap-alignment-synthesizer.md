# WLA-12-02 - Build the HoldSpeak roadmap-alignment synthesizer

- **Project:** work-log-automation
- **Phase:** 12
- **Status:** backlog
- **Depends on:** WLA-12-01
- **Unblocks:** WLA-12-03
- **Owner:** unassigned

## Problem

A delivery meeting about a Delivery Workbench project produces
decisions and action items that already have names on the roadmap —
story IDs, an active phase, a next actionable story — but HoldSpeak
extracts them as free text and the mapping happens in somebody's
head, or not at all. HoldSpeak's plugin host was built for exactly
this: a plugin pack is one `.py` file with a `MANIFEST` and a
`create_plugin()` factory, its router has a `delivery` intent
waiting for members, and the context dict already carries the
detected `project`. The first Delivery Workbench presence inside
HoldSpeak should be the read-only one: a synthesizer that grounds a
meeting in the roadmap without touching it.

## Scope

- **In:** A plugin pack `integrations/holdspeak/
  delivery_workbench_pack.py` in this repo, installable by copying
  into `~/.holdspeak/plugin_packs/`, containing a synthesizer
  plugin (`kind: synthesizer`, `execution_mode: deferred`,
  `required_capabilities: ["llm"]`, routed on the `delivery`
  intent). Given the transcript and the detected project, it reads
  roadmap state (`dw context --compact` when the project maps to a
  rails repo; degrade honestly to a no-roadmap-found failure shape
  when it does not) and returns a typed `roadmap_alignment`
  artifact: meeting decisions and action items mapped to story IDs
  where the LLM can ground them, the next actionable story, and
  drift flags (work discussed that no story covers). Follows the
  canonical LLM-plugin pattern from HoldSpeak's authoring guide:
  JSON-only prompt, parse defensively, success shape with
  `confidence_hint` 1.0 / failure shape with 0.0, never raise from
  `run()`. Registered renderer for the artifact. Unit tests with an
  injected `intel_call` seam covering success, failure, and the
  capability gate. An install note in the pack's docstring and in
  `docs/riders.md`. Journal entry written in the moment.
- **Out:** Proposing any change to the roadmap (WLA-12-03); Desk
  zones or briefings (WLA-12-07); modifying HoldSpeak core or its
  built-in chains (routing via the pack manifest's `intents` hint
  only).

## Acceptance criteria

- [ ] The pack passes HoldSpeak discovery (`validate_manifest`)
  and its plugin runs against a real transcript fixture through the
  HoldSpeak host with an LLM configured, producing a rendered
  `roadmap_alignment` artifact that names at least one real story
  ID from a rails fixture repo.
- [ ] With no roadmap resolvable for the project, the plugin
  returns the failure shape (summary explains why,
  `confidence_hint` 0.0, no typed keys) rather than inventing
  alignment.
- [ ] Unit tests cover success, unparseable-LLM-response failure,
  and the blocked-without-llm gate; they run in this repo's CI.
- [ ] The evidence file records the real HoldSpeak run (command,
  exit code, artifact output), not a simulation.

## Test plan

- **Unit:** pack tests with canned `intel_call` responses (success,
  garbage JSON, missing fields).
- **Integration:** discovery + dispatch of the pack through a
  scripted HoldSpeak host against a transcript fixture and a rails
  fixture repo.
- **Manual / device:** one live meeting or imported transcript on
  the desk with the pack installed; screenshot of the artifact at
  `/history` under evidence `assets/`.

## Notes / open questions

- The pack lives in this repo (single source, versioned, tested
  here) and is *installed* into HoldSpeak's pack directory; decide
  in-story whether `dw doctor` or an install script owns the copy
  step, and record it in the journal either way.
- Version pinning per WLA-12-01: the MANIFEST declares the
  HoldSpeak version range the pack was proven against.
