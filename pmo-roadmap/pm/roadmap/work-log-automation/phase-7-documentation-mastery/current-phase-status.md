# Phase 7 - Documentation Mastery

**Last updated:** 2026-07-02.

## Goal

Make the framework teachable: audited docs, a Claude Code plugin,
first-class assets, and OSS-grade repo hygiene with a versioned
release. After seven phases of building, the product is now also the
explanation of the product — and it gets the same evidence-first
treatment as the code.

## Operating principles

- **Audit before rewrite:** WLA-7-01's inventory and information
  architecture are the contract; later stories implement its
  dispositions instead of re-litigating them.
- **Docs are verified, not trusted:** every command printed in a
  quickstart runs verbatim in a fixture with output captured; links
  and images are CI-checked; canon claims name their enforcing rule
  or test.
- **One owner per topic:** duplication is replaced by links. The
  managed agent-docs block, the plugin skill, and the canon must
  agree — with parity tests where they overlap.
- **Assets are reproducible:** every rendered demo, diagram, and
  screenshot names the checked-in script that regenerates it.
- **The release ships through the gate:** contributors are taught the
  rails by CONTRIBUTING.md using the rails, and the release commit
  itself is contracted, trailered, and archived like every other.

## Exit criteria (evidence required)

- [x] A documentation inventory maps every doc surface to audience,
  purpose, freshness verdict, and disposition, with four executable
  audience paths (evaluator, adopter, contributor, operating agent)
  (evidence-story-01: 15 surfaces, 12 findings F1-F12, target IA).
- [x] The root README orients in one screen and every quickstart
  command runs as printed (captured verbatim in fixtures;
  evidence-story-02).
- [x] `docs/architecture.md` explains core, gate, contract v2,
  evidence, workbench, and work logs with accurate Mermaid diagrams,
  each behavioral claim naming its proving test or command (cited
  test names existence-verified; evidence-story-02).
- [x] Canon and templates pass a line-by-line accuracy audit with
  doc-parity tests covering newly cited machine-enforced statements
  (evidence-story-03: rule-id citations, fence/template/generator
  parity, byte-identical scaffolds).
- [x] A Claude Code plugin (manifest, skill, commands, marketplace
  entry) installs from this repo and passes a parity check against
  the managed agent-docs block; install.sh remains the non-plugin
  path and the docs say when to use which (evidence-story-04:
  captured live install at v1.5.0, three parity tests,
  plugin-validate.sh in CI).
- [x] All demos, screenshots, and diagrams are regenerated from
  current sources by checked-in scripts; the workbench appears in the
  root README; every image has alt text; a social preview is set
  (evidence-story-05: captured regeneration runs for both VHS tapes,
  the new workbench tour + README stills, and the social preview;
  10/10 Mermaid blocks render; alt-text audit; the GitHub-side
  preview upload is a documented one-time manual step).
- [x] Docs CI fails on broken internal links, missing images, or
  failing runnable snippets, wired into validation.yml and green
  (evidence-story-06: docslint module over all 135 Markdown files
  with GitHub-slug anchor checks and alt-text enforcement, six
  quickstarts executed as printed per run, captured kill tests
  proving both suites die on planted drift, <1s + ~4s runtimes,
  both OS legs).
- [x] CONTRIBUTING.md, CODE_OF_CONDUCT.md, and issue/PR templates
  exist, render on GitHub, and speak framework vocabulary
  (evidence-story-07: contributor clone-to-gated-commit path executed
  as printed in CI via prep=clone snippets; community profile 100%;
  bug form demands verbatim repro + the failing gate banner).
- [x] CHANGELOG.md derives from the phase final summaries; the
  version is single-sourced and test-asserted; a v1.x tag and GitHub
  release exist with notes (evidence-story-07: v1.5.0 from the seven
  linked final summaries; dw --version + plugin.json + changelog
  heading locked by three unit tests; annotated v1.5.0 tag + release
  on 712beaa, captured gh release view).
- [ ] `dw check work-log-automation` and the full validation matrix
  are green at phase close, with a final summary written as an audit.

## Story status

| ID | Story | Status | Story file | Evidence |
|---|---|---|---|---|
| WLA-7-01 | Documentation audit and information architecture | done | [story-01-documentation-audit-and-information-architecture](./story-01-documentation-audit-and-information-architecture.md) | [evidence-story-01](./evidence-story-01.md) |
| WLA-7-02 | Core docs overhaul and architecture guide | done | [story-02-core-docs-overhaul-and-architecture-guide](./story-02-core-docs-overhaul-and-architecture-guide.md) | [evidence-story-02](./evidence-story-02.md) |
| WLA-7-03 | Canon and template accuracy pass | done | [story-03-canon-and-template-accuracy-pass](./story-03-canon-and-template-accuracy-pass.md) | [evidence-story-03](./evidence-story-03.md) |
| WLA-7-04 | Package the Claude Code plugin | done | [story-04-package-the-claude-code-plugin](./story-04-package-the-claude-code-plugin.md) | [evidence-story-04](./evidence-story-04.md) |
| WLA-7-05 | Regenerate demos diagrams and visual assets | done | [story-05-regenerate-demos-diagrams-and-visual-assets](./story-05-regenerate-demos-diagrams-and-visual-assets.md) | [evidence-story-05](./evidence-story-05.md) |
| WLA-7-06 | Wire documentation CI checks | done | [story-06-wire-documentation-ci-checks](./story-06-wire-documentation-ci-checks.md) | [evidence-story-06](./evidence-story-06.md) |
| WLA-7-07 | OSS release preparation and versioned release | done | [story-07-oss-release-preparation-and-versioned-release](./story-07-oss-release-preparation-and-versioned-release.md) | [evidence-story-07](./evidence-story-07.md) |

## Execution sequence

1. WLA-7-01 audits everything and freezes the information
   architecture — the contract for the phase.
2. WLA-7-02 and WLA-7-03 execute the audit's dispositions in
   parallel tracks: reader docs (README, quickstarts, architecture
   guide) and operator canon (contract, builder, templates).
3. WLA-7-04 packages the Claude Code plugin once the audited
   vocabulary is stable, with parity tests against the managed block.
4. WLA-7-05 regenerates all visual assets against the rewritten docs.
5. WLA-7-06 wires docs CI so the overhauled state cannot rot
   silently — landing before the release so the release is checked.
6. WLA-7-07 ships OSS hygiene and the versioned release, then the
   phase closes with an audit-style final summary.

## Where we are

WLA-7-07 is done with evidence: the repo is OSS-ready and released —
CONTRIBUTING teaches the rails using the rails with its command
blocks CI-executed as printed, templates ask for evidence in
framework vocabulary, CHANGELOG derives v1.5.0 from the seven phase
final summaries, the version is single-sourced with three test
locks, and the annotated v1.5.0 tag + GitHub release were cut on a
fully green CI run. All seven stories are done; the only remaining
step is the phase close itself (final summary + criterion 10).

## Active risks

| Risk | Likelihood | Mitigation | Stop signal |
|---|---|---|---|
| Rewrite without audit repeats accretion | medium | WLA-7-01 is a hard dependency of every rewrite story | A doc PR lands citing no audit disposition |
| Plugin drifts from managed agent-docs block | high | Single vocabulary source + parity test in WLA-7-04 | Skill and CLAUDE.md block disagree on a command or rule |
| Docs claim what tests don't prove | medium | Every behavioral claim names its proving command; snippet smoke in CI | A quickstart fails when run verbatim |
| Asset regeneration is manual and rots | medium | Checked-in scripts per asset, wired into the demo smoke | An asset in the README has no regeneration script |
| Release versioning splinters | low | Single-source version with a unit assertion | dw --version, plugin, and CHANGELOG disagree |
