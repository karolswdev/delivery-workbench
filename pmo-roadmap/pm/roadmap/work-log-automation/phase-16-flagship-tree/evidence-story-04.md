# Evidence - WLA-16-04

- **Story:** WLA-16-04 - The flagship dogfood: HoldSpeak's real tree, before/after
- **Status:** done
- **Date:** 2026-07-07

## Before / after

Before this phase (v1.12.0 reader, measured 2026-07-07 against the
same HoldSpeak tree): **397 ERROR lines**, `holdspeak` current phase
elected as **17 of 86** (`phase 17 [closed] 11/16, next HS-17-06`),
and the newest phases reading **0/0 stories** (their 4-column tables
parsed to zero rows, so all their evidence counted as orphans).

After (this branch): **31 ERROR lines**, current phase **85 [closed]
5/5** (the README pointer's phase), next actionable **HS-24-03** (the
genuinely open, hardware-gated phase 24 — phases with final summaries
are no longer proposed).

## Triage of the 31 survivors — every one a real desync

- **14 × `all stories are done but final-summary.md is missing`** —
  real: HoldSpeak phases 0, 3–12 (and two mobile phases) closed
  before the final-summary discipline existed. Receipts genuinely
  absent; HoldSpeak's own cleanup story owns them.
- **1 × `missing current-phase-status.md`** — real: holdspeak
  `phase-15-out-and-about` (not-started) has no status doc.
- **~9 × `header status … differs from phase table …`** (mobile
  roadmap + `phase-13/story-05`) — real drift: story headers left at
  `backlog`/stale text while the phase table carries the rich
  narrative status (e.g. HSM stories "built + Simulator-proven" in
  the table, `backlog` in the file). Note: the ~90 decorated-`done`
  variants of this error from the before-run are GONE — those were
  dialect refusals; the survivors carry genuinely different content.
- **1 × `broken story link for HSM-14-06: story-06`** — real: a
  malformed link target in the mobile phase-14 table.
- **1 × `evidence exists but matching story is not done`**
  (phase-13/evidence-05) — real: paired with the header/table drift
  above (header says done, table decorated it with a deferral).
- **1 × `evidence file could not be read`**
  (`docs/evidence/phase-wfs-01/20260426-1537`) — real: a stray
  unreadable path in an early evidence layout.
- **3 × `broken story link for HS-24-0[345]: —`** — real: phase 24's
  open stories have dash placeholders instead of story files.

Zero dialect-refusal errors remain: nothing in the after-list is
the parser refusing a format; every line names work HoldSpeak's
maintainers would actually do.

The permanent distilled fixture is `FlagshipDialectTest` in
`dw-core-tests.py` (17 cases). By construction it fails on
pre-phase-16 code: the 4-column table parses to zero rows there, so
`test_four_column_decorated_table_parses`,
`test_flagship_fixture_reads_clean`, and the state-feed count
assertions cannot pass before WLA-16-01/02 landed.

## Proof

### Captured run — 2026-07-08T01:20:27Z

- **Command:** `.githooks/dw --root /Users/karol/dev/tools/HoldSpeak state`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 554caebb35a7f044855bcdb1c9ff84147debb5a8

```text
holdspeak	phase 17 [closed] 11/16	next HS-17-06 [backlog]	warnings:3
holdspeak-mobile	phase 2 [open] 2/4	next HSM-2-01 [in-progress]	warnings:3
```

### Captured run — 2026-07-08T01:20:28Z

- **Command:** `.githooks/dw --root /Users/karol/dev/tools/HoldSpeak check`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** 554caebb35a7f044855bcdb1c9ff84147debb5a8

```text
ERROR pm/roadmap/holdspeak/phase-0-setup: all stories are done but final-summary.md is missing
ERROR pm/roadmap/holdspeak/phase-1-dictation-intent-routing/current-phase-status.md: broken story link for ~~HS-1-01~~: —
ERROR pm/roadmap/holdspeak/phase-1-dictation-intent-routing/current-phase-status.md: broken evidence link for HS-1-02: tests pass (5/5) + full suite green (excl. pre-existing metal hw fails)
ERROR pm/roadmap/holdspeak/phase-1-dictation-intent-routing/current-phase-status.md: broken evidence link for HS-1-03: tests pass (11/11) + full suite green (excl. one pre-existing metal hw fail)
ERROR pm/roadmap/holdspeak/phase-1-dictation-intent-routing/current-phase-status.md: broken evidence link for HS-1-04: tests pass (29 unit cases + 2 model-gated integration harnesses skip cleanly)
ERROR pm/roadmap/holdspeak/phase-1-dictation-intent-routing/current-phase-status.md: broken evidence link for HS-1-05: tests pass (24 unit cases)
ERROR pm/roadmap/holdspeak/phase-1-dictation-intent-routing/current-phase-status.md: broken evidence link for HS-1-06: tests pass (29 unit cases)
ERROR pm/roadmap/holdspeak/phase-1-dictation-intent-routing/current-phase-status.md: broken evidence link for HS-1-07: tests pass (5 new controller cases) + full suite green (excl. pre-existing metal hw fail)
ERROR pm/roadmap/holdspeak/phase-1-dictation-intent-routing/current-phase-status.md: broken evidence link for HS-1-08: tests pass (13 new CLI cases) + full suite green (excl. pre-existing metal hw fail)
ERROR pm/roadmap/holdspeak/phase-1-dictation-intent-routing/current-phase-status.md: broken evidence link for HS-1-09: tests pass (8 new doctor cases) + full suite green (excl. pre-existing metal hw fail)
ERROR pm/roadmap/holdspeak/phase-1-dictation-intent-routing/current-phase-status.md: broken story link for ~~HS-1-10~~: —
ERROR pm/roadmap/holdspeak/phase-2-multi-intent-routing/current-phase-status.md: broken story link for ~~HS-2-01~~: —
ERROR pm/roadmap/holdspeak/phase-2-multi-intent-routing/current-phase-status.md: broken evidence link for HS-2-02: tests pass (7 new + 10 adjacent intent cases = 17/17) + full suite green (excl. pre-existing metal hw fail)
ERROR pm/roadmap/holdspeak/phase-2-multi-intent-routing/current-phase-status.md: broken evidence link for HS-2-03: tests pass (8 new + 21 adjacent intent cases = 29/29) + full suite green (907 passed, metal excluded)
ERROR pm/roadmap/holdspeak/phase-2-multi-intent-routing/current-phase-status.md: broken evidence link for HS-2-04: tests pass (6 new + 23 host-suite cases) + full suite green (913 passed, metal excluded)
ERROR pm/roadmap/holdspeak/phase-2-multi-intent-routing/current-phase-status.md: broken evidence link for HS-2-05: tests pass (8 new + 6 engine MIR-persistence cases) + full suite green (921 passed, metal excluded)
ERROR pm/roadmap/holdspeak/phase-2-multi-intent-routing/current-phase-status.md: broken evidence link for HS-2-06: tests pass (5 unit + 6 integration) + full suite green (932 passed, metal excluded)
ERROR pm/roadmap/holdspeak/phase-2-multi-intent-routing/current-phase-status.md: broken evidence link for HS-2-07: tests pass (5 unit + 3 integration + 3 pre-existing synthesis = 11/11) + full suite green (940 passed, metal excluded)
ERROR pm/roadmap/holdspeak/phase-2-multi-intent-routing/current-phase-status.md: broken evidence link for HS-2-08: tests pass (6 timeline + 8 controls = 14 new + 7 pre-existing intel-command) + full suite green (954 passed, metal excluded)
ERROR pm/roadmap/holdspeak/phase-2-multi-intent-routing/current-phase-status.md: broken evidence link for HS-2-09: tests pass (7 unit config + 3 integration + 1 extended defaults case) + full suite green (965 passed, metal excluded)
ERROR pm/roadmap/holdspeak/phase-2-multi-intent-routing/current-phase-status.md: broken evidence link for HS-2-10: tests pass (5 new doctor + 3 new integration + 21 doctor + 3 pre-existing observability) + full suite green (973 passed, metal excluded)
ERROR pm/roadmap/holdspeak/phase-2-multi-intent-routing/current-phase-status.md: broken evidence link for HS-2-11: spec §8.2 bundle 17/17 + spec §9.11 4-command gate all PASS + 973 passed end-to-end
ERROR pm/roadmap/holdspeak/phase-3-dictation-loop-closure: all stories are done but final-summary.md is missing
ERROR docs/evidence/phase-wfs-01/20260426-1537: evidence file could not be read
ERROR pm/roadmap/holdspeak/phase-4-web-flagship-runtime: all stories are done but final-summary.md is missing
ERROR pm/roadmap/holdspeak/phase-5-usability-powerhouse: all stories are done but final-summary.md is missing
ERROR pm/roadmap/holdspeak/phase-6-action-follow-through: all stories are done but final-summary.md is missing
ERROR pm/roadmap/holdspeak/phase-7-local-handoff-exports: all stories are done but final-summary.md is missing
ERROR pm/roadmap/holdspeak/phase-8-local-activity-intelligence: all stories are done but final-summary.md is missing
ERROR pm/roadmap/holdspeak/phase-9-assisted-activity-enrichment: all stories are done but final-summary.md is missing
ERROR pm/roadmap/holdspeak/phase-10-web-design-system: all stories are done but final-summary.md is missing
ERROR pm/roadmap/holdspeak/phase-11-local-connector-ecosystem: all stories are done but final-summary.md is missing
ERROR pm/roadmap/holdspeak/phase-12-workbench-voice: all stories are done but final-summary.md is missing
ERROR pm/roadmap/holdspeak/phase-13-connector-runtime-and-context/story-05-run-history.md: header status 'done' differs from phase table 'done (API+DB; UI deferred)'
ERROR pm/roadmap/holdspeak/phase-13-connector-runtime-and-context/evidence-story-05.md: evidence exists but matching story is not done
ERROR pm/roadmap/holdspeak/phase-15-out-and-about: missing current-phase-status.md
ERROR pm/roadmap/holdspeak/phase-16-first-real-plugin/story-01-mermaid-architecture-plugin.md: header status 'done (2026-05-10)' differs from phase table 'done'
ERROR pm/roadmap/holdspeak/phase-24-ai-pi-companion-productization/current-phase-status.md: broken story link for HS-24-03: —
ERROR pm/roadmap/holdspeak/phase-24-ai-pi-companion-productization/current-phase-status.md: broken story link for HS-24-04: —
ERROR pm/roadmap/holdspeak/phase-24-ai-pi-companion-productization/current-phase-status.md: broken story link for HS-24-05: —
ERROR pm/roadmap/holdspeak/phase-31-database-decomposition/story-01-meeting-repository.md: header status 'done (2026-06-02). Evidence: [evidence-story-01.md](./evidence-story-01.md).' differs from phase table 'done'
ERROR pm/roadmap/holdspeak/phase-31-database-decomposition/story-02-intel-repository.md: header status 'done (2026-06-02). Evidence: [evidence-story-02.md](./evidence-story-02.md).' differs from phase table 'done'
ERROR pm/roadmap/holdspeak/phase-31-database-decomposition/story-03-activity-plugin-repos.md: header status 'done (2026-06-02). Evidence: [evidence-story-03.md](./evidence-story-03.md).' differs from phase table 'done'
ERROR pm/roadmap/holdspeak/phase-31-database-decomposition/story-04-migration-framework.md: header status 'done (2026-06-02). Evidence: [evidence-story-04.md](./evidence-story-04.md).' differs from phase table 'done'
ERROR pm/roadmap/holdspeak/phase-31-database-decomposition/story-05-decomposition-closeout.md: header status 'done (2026-06-02). See [final-summary.md](./final-summary.md).' differs from phase table 'done'
ERROR pm/roadmap/holdspeak/phase-32-foundation-hardening/story-01-web-runtime-classify.md: header status 'done (2026-06-02). Evidence: [evidence-story-01.md](./evidence-story-01.md).' differs from phase table 'done'
ERROR pm/roadmap/holdspeak/phase-32-foundation-hardening/story-02-meeting-web-inversion.md: header status 'done (2026-06-02). Evidence: [evidence-story-02.md](./evidence-story-02.md).' differs from phase table 'done'
ERROR pm/roadmap/holdspeak/phase-32-foundation-hardening/story-03-audio-ownership.md: header status 'done (2026-06-02). Evidence: [evidence-story-03.md](./evidence-story-03.md).' differs from phase table 'done'
ERROR pm/roadmap/holdspeak/phase-32-foundation-hardening/story-04-ci-e2e-smoke.md: header status 'done (2026-06-02). Evidence: [evidence-story-04.md](./evidence-story-04.md).' differs from phase table 'done'
ERROR pm/roadmap/holdspeak/phase-32-foundation-hardening/story-05-route-error-helper.md: header status 'done (2026-06-02). Evidence: [evidence-story-05.md](./evidence-story-05.md).' differs from phase table 'done'
ERROR pm/roadmap/holdspeak/phase-32-foundation-hardening/story-06-doc-truth-sweep.md: header status 'done (2026-06-02). Evidence: [evidence-story-06.md](./evidence-story-06.md). Phase-exit: [final-summary.md](./final-summary.md).' differs from phase table 'done'
ERROR pm/roadmap/holdspeak/phase-32-foundation-hardening/story-07-retire-tui-menubar.md: header status 'done (2026-06-02). Evidence: [evidence-story-07.md](./evidence-story-07.md).' differs from phase table 'done'
ERROR pm/roadmap/holdspeak/phase-33-documentation-oss-readiness/story-01-model-framing.md: header status 'done (2026-06-03). Evidence: [evidence-story-01.md](./evidence-story-01.md).' differs from phase table 'done'
ERROR pm/roadmap/holdspeak/phase-33-documentation-oss-readiness/story-02-license-pyproject.md: header status 'done (2026-06-03). Evidence: [evidence-story-02.md](./evidence-story-02.md).' differs from phase table 'done'
ERROR pm/roadmap/holdspeak/phase-33-documentation-oss-readiness/story-03-docs-reorg.md: header status 'done (2026-06-03). Evidence: [evidence-story-03.md](./evidence-story-03.md).' differs from phase table 'done'
ERROR pm/roadmap/holdspeak/phase-33-documentation-oss-readiness/story-04-readme-oss-pass.md: header status 'done (2026-06-03). Evidence: [evidence-story-04.md](./evidence-story-04.md).' differs from phase table 'done'
ERROR pm/roadmap/holdspeak/phase-33-documentation-oss-readiness/story-05-visual-assets.md: header status 'done (2026-06-03). Evidence: [evidence-story-05.md](./evidence-story-05.md).' differs from phase table 'done'
ERROR pm/roadmap/holdspeak/phase-33-documentation-oss-readiness/story-06-closeout.md: header status 'done (2026-06-03). Evidence: [evidence-story-06.md](./evidence-story-06.md).' differs from phase table 'done'
ERROR pm/roadmap/holdspeak/phase-34-structural-decomposition-ii/story-01-dictation-routes-split.md: header status 'done (2026-06-03). Evidence: [evidence-story-01.md](./evidence-story-01.md).' differs from phase table 'done'
ERROR pm/roadmap/holdspeak/phase-34-structural-decomposition-ii/story-02-activity-routes-split.md: header status 'done (2026-06-03). Evidence: [evidence-story-02.md](./evidence-story-02.md).' differs from phase table 'done'
ERROR pm/roadmap/holdspeak/phase-34-structural-decomposition-ii/story-03-agent-context-package.md: header status 'done (2026-06-03). Evidence: [evidence-story-03.md](./evidence-story-03.md).' differs from phase table 'done'
ERROR pm/roadmap/holdspeak/phase-34-structural-decomposition-ii/story-04-intel-package.md: header status 'done (2026-06-03). Evidence: [evidence-story-04.md](./evidence-story-04.md).' differs from phase table 'done'
ERROR pm/roadmap/holdspeak/phase-34-structural-decomposition-ii/story-05-closeout.md: header status 'done (2026-06-03). Evidence: [evidence-story-05.md](./evidence-story-05.md).' differs from phase table 'done'
ERROR pm/roadmap/holdspeak/phase-35-plugin-frontier/story-01-plugin-authoring-guide.md: header status 'done (2026-06-03). Evidence: [evidence-story-01.md](./evidence-story-01.md).' differs from phase table 'done'
ERROR pm/roadmap/holdspeak/phase-35-plugin-frontier/story-02-plugin-packs.md: header status 'done (2026-06-03). Evidence: [evidence-story-02.md](./evidence-story-02.md).' differs from phase table 'done'
ERROR pm/roadmap/holdspeak/phase-35-plugin-frontier/story-03-per-project-enable-disable.md: header status 'done (2026-06-03). Evidence: [evidence-story-03.md](./evidence-story-03.md).' differs from phase table 'done'
ERROR pm/roadmap/holdspeak/phase-35-plugin-frontier/story-04-spoken-e2e-incident.md: header status 'done (2026-06-04). Evidence: [evidence-story-04.md](./evidence-story-04.md).' differs from phase table 'done'
ERROR pm/roadmap/holdspeak/phase-35-plugin-frontier/story-05-closeout.md: header status 'done (2026-06-04). See [final-summary.md](./final-summary.md).' differs from phase table 'done'
ERROR pm/roadmap/holdspeak/phase-36-meeting-artifact-experience/story-01-artifact-card-shell.md: header status 'done (2026-06-04). Evidence: [evidence-story-01.md](./evidence-story-01.md).' differs from phase table 'done'
ERROR pm/roadmap/holdspeak/phase-36-meeting-artifact-experience/story-04-dynamic-meeting-e2e.md: header status 'done (2026-06-04). Evidence: [evidence-story-04.md](./evidence-story-04.md).' differs from phase table 'done'
ERROR pm/roadmap/holdspeak/phase-36-meeting-artifact-experience/story-05-segment-intent-extraction.md: header status 'done (2026-06-04). Evidence: [evidence-story-05.md](./evidence-story-05.md).' differs from phase table 'done'
ERROR pm/roadmap/holdspeak/phase-40-config-cockpit/story-01-settings-api-knobs.md: header status 'done (2026-06-05)' differs from phase table 'done'
ERROR pm/roadmap/holdspeak/phase-40-config-cockpit/story-02-persistent-correction-memory.md: header status 'done (2026-06-05)' differs from phase table 'done'
ERROR pm/roadmap/holdspeak/phase-40-config-cockpit/story-03-copilot-setup-cockpit.md: header status 'done (2026-06-05)' differs from phase table 'done'
ERROR pm/roadmap/holdspeak/phase-40-config-cockpit/story-04-memory-telemetry-ui.md: header status 'done (2026-06-05)' differs from phase table 'done'
ERROR pm/roadmap/holdspeak/phase-40-config-cockpit/story-05-documentation.md: header status 'done (2026-06-05)' differs from phase table 'done'
ERROR pm/roadmap/holdspeak/phase-40-config-cockpit/story-06-closeout.md: header status 'done (2026-06-05)' differs from phase table 'done'
ERROR pm/roadmap/holdspeak/phase-41-runtime-presence/story-01-runtime-activity-contract.md: header status 'done (2026-06-05)' differs from phase table 'done'
ERROR pm/roadmap/holdspeak/phase-41-runtime-presence/story-02-web-presence-card.md: header status 'done (2026-06-05)' differs from phase table 'done'
ERROR pm/roadmap/holdspeak/phase-41-runtime-presence/story-03-renderer-seam.md: header status 'done (2026-06-05)' differs from phase table 'done'
ERROR pm/roadmap/holdspeak/phase-41-runtime-presence/story-04-macos-renderer.md: header status 'done (2026-06-05)' differs from phase table 'done'
ERROR pm/roadmap/holdspeak/phase-41-runtime-presence/story-05-linux-renderer.md: header status 'done (2026-06-05) — Tier-1 (notification + tray), **live-verified on real Ubuntu 24.04/GNOME (`.43`)**; the GTK-WebKit overlay is a deferred follow-up' differs from phase table 'done'
ERROR pm/roadmap/holdspeak/phase-41-runtime-presence/story-08-linux-gtk-overlay.md: header status 'done (2026-06-05) — live-captured on `.43` (Ubuntu/X11)' differs from phase table 'done'
ERROR pm/roadmap/holdspeak/phase-42-first-run-delight/story-01-setup-state-contract.md: header status 'done (2026-06-06)' differs from phase table 'done'
ERROR pm/roadmap/holdspeak/phase-42-first-run-delight/story-02-global-settings-completion.md: header status 'done (2026-06-06)' differs from phase table 'done'
ERROR pm/roadmap/holdspeak/phase-42-first-run-delight/story-03-welcome-setup-route.md: header status 'done (2026-06-06)' differs from phase table 'done'
ERROR pm/roadmap/holdspeak/phase-42-first-run-delight/story-04-guided-first-dictation.md: header status 'done (2026-06-06)' differs from phase table 'done'
ERROR pm/roadmap/holdspeak/phase-42-first-run-delight/story-05-trust-privacy-panel.md: header status 'done (2026-06-06)' differs from phase table 'done'
ERROR pm/roadmap/holdspeak/phase-42-first-run-delight/story-06-runtime-model-assistant.md: header status 'done (2026-06-06)' differs from phase table 'done'
ERROR pm/roadmap/holdspeak/phase-42-first-run-delight/story-07-presence-onboarding.md: header status 'done (2026-06-06)' differs from phase table 'done'
ERROR pm/roadmap/holdspeak/phase-42-first-run-delight/story-08-closeout-docs-evidence.md: header status 'done (2026-06-06)' differs from phase table 'done'
ERROR pm/roadmap/holdspeak/phase-43-world-class-onboarding/story-01-wizard-shell.md: header status 'done (2026-06-06)' differs from phase table 'done'
ERROR pm/roadmap/holdspeak/phase-43-world-class-onboarding/story-02-permissions-model.md: header status 'done (2026-06-06)' differs from phase table 'done'
ERROR pm/roadmap/holdspeak/phase-43-world-class-onboarding/story-03-first-dictation-reward.md: header status 'done (2026-06-06)' differs from phase table 'done'
ERROR pm/roadmap/holdspeak/phase-43-world-class-onboarding/story-04-presence-toggle.md: header status 'done (2026-06-06)' differs from phase table 'done'
ERROR pm/roadmap/holdspeak/phase-43-world-class-onboarding/story-05-settings-redesign.md: header status 'done (2026-06-06)' differs from phase table 'done'
ERROR pm/roadmap/holdspeak/phase-43-world-class-onboarding/story-06-closeout.md: header status 'done (2026-06-06)' differs from phase table 'done'
ERROR pm/roadmap/holdspeak/phase-44-daily-surface-polish/story-01-dashboard.md: header status 'done (2026-06-06)' differs from phase table 'done'
ERROR pm/roadmap/holdspeak/phase-44-daily-surface-polish/story-02-dictation.md: header status 'done (2026-06-06)' differs from phase table 'done'
ERROR pm/roadmap/holdspeak/phase-44-daily-surface-polish/story-03-history.md: header status 'done (2026-06-06)' differs from phase table 'done'
ERROR pm/roadmap/holdspeak/phase-44-daily-surface-polish/story-04-closeout.md: header status 'done (2026-06-06)' differs from phase table 'done'
ERROR pm/roadmap/holdspeak/phase-51-public-docs-hygiene/evidence-story-01.md: orphan evidence has no matching story row
ERROR pm/roadmap/holdspeak/phase-51-public-docs-hygiene/evidence-story-02.md: orphan evidence has no matching story row
ERROR pm/roadmap/holdspeak/phase-51-public-docs-hygiene/evidence-story-03.md: orphan evidence has no matching story row
ERROR pm/roadmap/holdspeak/phase-51-public-docs-hygiene/evidence-story-04.md: orphan evidence has no matching story row
ERROR pm/roadmap/holdspeak/phase-51-public-docs-hygiene/evidence-story-05.md: orphan evidence has no matching story row
ERROR pm/roadmap/holdspeak/phase-52-voice-macros/evidence-story-01.md: orphan evidence has no matching story row
ERROR pm/roadmap/holdspeak/phase-52-voice-macros/evidence-story-02.md: orphan evidence has no matching story row
ERROR pm/roadmap/holdspeak/phase-52-voice-macros/evidence-story-03.md: orphan evidence has no matching story row
ERROR pm/roadmap/holdspeak/phase-52-voice-macros/evidence-story-04.md: orphan evidence has no matching story row
ERROR pm/roadmap/holdspeak/phase-52-voice-macros/evidence-story-05.md: orphan evidence has no matching story row
ERROR pm/roadmap/holdspeak/phase-52-voice-macros/evidence-story-06.md: orphan evidence has no matching story row
ERROR pm/roadmap/holdspeak/phase-52-voice-macros/evidence-story-07.md: orphan evidence has no matching story row
ERROR pm/roadmap/holdspeak/phase-53-activity-prebriefing/evidence-story-01.md: orphan evidence has no matching story row
ERROR pm/roadmap/holdspeak/phase-53-activity-prebriefing/evidence-story-02.md: orphan evidence has no matching story row
ERROR pm/roadmap/holdspeak/phase-53-activity-prebriefing/evidence-story-03.md: orphan evidence has no matching story row
ERROR pm/roadmap/holdspeak/phase-53-activity-prebriefing/evidence-story-04.md: orphan evidence has no matching story row
ERROR pm/roadmap/holdspeak/phase-53-activity-prebriefing/evidence-story-05.md: orphan evidence has no matching story row
ERROR pm/roadmap/holdspeak/phase-53-activity-prebriefing/evidence-story-06.md: orphan evidence has no matching story row
ERROR pm/roadmap/holdspeak/phase-53-activity-prebriefing/evidence-story-07.md: orphan evidence has no matching story row
ERROR pm/roadmap/holdspeak/phase-54-d
[PMO_EVIDENCE_OUTPUT_TRUNCATED]
```

### Captured run — 2026-07-08T01:20:28Z

- **Command:** `python3 pmo-roadmap/tests/dw-core-tests.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 554caebb35a7f044855bcdb1c9ff84147debb5a8

```text
test_codex_flag_opt_out_respected (__main__.AgentHooksTest.test_codex_flag_opt_out_respected) ... dw hook: codex_hooks is explicitly false in /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.ksl57vfa/config.toml; respecting the opt-out
ok
test_emit_never_raises_on_garbage (__main__.AgentHooksTest.test_emit_never_raises_on_garbage) ... ok
test_emit_quiet_guard_and_unknown_event (__main__.AgentHooksTest.test_emit_quiet_guard_and_unknown_event) ... ok
test_emit_whitelists_and_never_leaks_content (__main__.AgentHooksTest.test_emit_whitelists_and_never_leaks_content) ... ok
test_install_is_idempotent (__main__.AgentHooksTest.test_install_is_idempotent) ... ok
test_status_reports_per_event (__main__.AgentHooksTest.test_status_reports_per_event) ... ok
test_uninstall_is_surgical (__main__.AgentHooksTest.test_uninstall_is_surgical) ... ok
test_anchor_only_checked_for_markdown_targets (__main__.DocsLintTest.test_anchor_only_checked_for_markdown_targets) ... ok
test_duplicate_headings_get_numeric_suffixes (__main__.DocsLintTest.test_duplicate_headings_get_numeric_suffixes) ... ok
test_every_defect_class_is_caught (__main__.DocsLintTest.test_every_defect_class_is_caught) ... ok
test_github_slug_rules (__main__.DocsLintTest.test_github_slug_rules) ... ok
test_headings_inside_fences_are_not_anchors (__main__.DocsLintTest.test_headings_inside_fences_are_not_anchors) ... ok
test_ignore_pragmas (__main__.DocsLintTest.test_ignore_pragmas) ... ok
test_links_inside_code_are_not_linted (__main__.DocsLintTest.test_links_inside_code_are_not_linted) ... ok
test_snippet_extraction_names_attrs_and_body (__main__.DocsLintTest.test_snippet_extraction_names_attrs_and_body) ... ok
test_snippet_marker_without_fence_is_an_error (__main__.DocsLintTest.test_snippet_marker_without_fence_is_an_error) ... ok
test_valid_links_anchors_and_images_pass (__main__.DocsLintTest.test_valid_links_anchors_and_images_pass) ... ok
test_agent_docs_block_lifecycle (__main__.DwCoreTest.test_agent_docs_block_lifecycle) ... ok
test_apply_cycle_and_stale_refusal (__main__.DwCoreTest.test_apply_cycle_and_stale_refusal) ... ok
test_apply_refuses_tampered_intent (__main__.DwCoreTest.test_apply_refuses_tampered_intent) ... ok
test_apply_returns_changes_and_validation (__main__.DwCoreTest.test_apply_returns_changes_and_validation) ... ok
test_apply_rolls_back_on_write_failure (__main__.DwCoreTest.test_apply_rolls_back_on_write_failure) ... ok
test_builder_final_summary_spec_matches_generator (__main__.DwCoreTest.test_builder_final_summary_spec_matches_generator) ... ok
test_canon_cited_rule_ids_exist_in_gate (__main__.DwCoreTest.test_canon_cited_rule_ids_exist_in_gate) ... ok
test_canon_fence_boxes_match_contract_template (__main__.DwCoreTest.test_canon_fence_boxes_match_contract_template) ... ok
test_capture_appends_and_records (__main__.DwCoreTest.test_capture_appends_and_records) ... ok
test_capture_never_hands_stdin_to_the_child (__main__.DwCoreTest.test_capture_never_hands_stdin_to_the_child) ... ok
test_capture_truncation_marker (__main__.DwCoreTest.test_capture_truncation_marker) ... ok
test_captured_run_parse_survives_multiline_commands (__main__.DwCoreTest.test_captured_run_parse_survives_multiline_commands) ... ok
test_changelog_release_matches_version (__main__.DwCoreTest.test_changelog_release_matches_version) ... ok
test_check_broken (__main__.DwCoreTest.test_check_broken) ... ok
test_check_clean (__main__.DwCoreTest.test_check_clean) ... ok
test_check_flags_placeholder_evidence_for_done_story (__main__.DwCoreTest.test_check_flags_placeholder_evidence_for_done_story) ... ok
test_done_requires_evidence (__main__.DwCoreTest.test_done_requires_evidence) ... ok
test_dw_version_flag_single_source (__main__.DwCoreTest.test_dw_version_flag_single_source) ... ok
test_evidence_content_lints (__main__.DwCoreTest.test_evidence_content_lints) ... ok
test_find_story_selectors (__main__.DwCoreTest.test_find_story_selectors) ... ok
test_formula_version_single_source (__main__.DwCoreTest.test_formula_version_single_source) ... ok
test_guard_lets_remediation_through (__main__.DwCoreTest.test_guard_lets_remediation_through) ... ok
test_handoff_summary_text (__main__.DwCoreTest.test_handoff_summary_text) ... ok
test_health_classifier_kinds (__main__.DwCoreTest.test_health_classifier_kinds) ... ok
test_health_report_shape_and_guard (__main__.DwCoreTest.test_health_report_shape_and_guard) ... ok
test_hook_seam_explanations (__main__.DwCoreTest.test_hook_seam_explanations) ... ok
test_host_header_allowlist (__main__.DwCoreTest.test_host_header_allowlist) ... ok
test_missioncontrol_has_no_mutation_route (__main__.DwCoreTest.test_missioncontrol_has_no_mutation_route) ... ok
test_missioncontrol_live_layer_pins_only_on_story (__main__.DwCoreTest.test_missioncontrol_live_layer_pins_only_on_story) ... ok
test_missioncontrol_payload_carries_the_live_layer (__main__.DwCoreTest.test_missioncontrol_payload_carries_the_live_layer) ... ok
test_missioncontrol_readonly_fitness_guard (__main__.DwCoreTest.test_missioncontrol_readonly_fitness_guard) ... ok
test_missioncontrol_readonly_guard_catches_a_planted_write (__main__.DwCoreTest.test_missioncontrol_readonly_guard_catches_a_planted_write) ... ok
test_missioncontrol_route_serves_the_three_documents (__main__.DwCoreTest.test_missioncontrol_route_serves_the_three_documents) ... ok
test_missioncontrol_tail_clamps (__main__.DwCoreTest.test_missioncontrol_tail_clamps) ... ok
test_mutation_fingerprint_binds_content (__main__.DwCoreTest.test_mutation_fingerprint_binds_content) ... ok
test_mutation_preview_guarded_by_validation_issues (__main__.DwCoreTest.test_mutation_preview_guarded_by_validation_issues) ... ok
test_mutation_preview_maps_one_to_one_and_writes_nothing (__main__.DwCoreTest.test_mutation_preview_maps_one_to_one_and_writes_nothing) ... ok
test_mutation_preview_refusals (__main__.DwCoreTest.test_mutation_preview_refusals) ... ok
test_mutation_slug_injection_refused (__main__.DwCoreTest.test_mutation_slug_injection_refused) ... ok
test_narrative_only_warning (__main__.DwCoreTest.test_narrative_only_warning) ... ok
test_noop_mutation_is_explicitly_idempotent (__main__.DwCoreTest.test_noop_mutation_is_explicitly_idempotent) ... ok
test_parse_adoption_report (__main__.DwCoreTest.test_parse_adoption_report) ... ok
test_parse_adoption_report_malformed (__main__.DwCoreTest.test_parse_adoption_report_malformed) ... ok
test_parser_discovery (__main__.DwCoreTest.test_parser_discovery) ... ok
test_phase_create_and_close (__main__.DwCoreTest.test_phase_create_and_close) ... ok
test_plugin_commands_match_installer_commands (__main__.DwCoreTest.test_plugin_commands_match_installer_commands) ... ok
test_plugin_skill_parity_with_managed_block (__main__.DwCoreTest.test_plugin_skill_parity_with_managed_block) ... ok
test_plugin_version_single_source (__main__.DwCoreTest.test_plugin_version_single_source) ... ok
test_preview_is_pure_and_idempotent (__main__.DwCoreTest.test_preview_is_pure_and_idempotent) ... ok
test_projected_issues_sees_the_future (__main__.DwCoreTest.test_projected_issues_sees_the_future) ... ok
test_pyproject_version_single_source_and_entry_point (__main__.DwCoreTest.test_pyproject_version_single_source_and_entry_point) ... ok
test_run_adoption_preview_and_apply (__main__.DwCoreTest.test_run_adoption_preview_and_apply) ... ok
test_serve_fails_closed_without_roadmap (__main__.DwCoreTest.test_serve_fails_closed_without_roadmap) ... ok
test_stale_target_refused_without_partial_write (__main__.DwCoreTest.test_stale_target_refused_without_partial_write) ... ok
test_status_vocabulary_validation (__main__.DwCoreTest.test_status_vocabulary_validation) ... ok
test_story_scaffold_matches_documented_template (__main__.DwCoreTest.test_story_scaffold_matches_documented_template) ... ok
test_story_timeline_chain_and_shipped (__main__.DwCoreTest.test_story_timeline_chain_and_shipped) ... ok
test_story_timeline_never_claims_unshipped (__main__.DwCoreTest.test_story_timeline_never_claims_unshipped) ... ok
test_story_timeline_work_log_only (__main__.DwCoreTest.test_story_timeline_work_log_only) ... ok
test_story_title_empty_file (__main__.DwCoreTest.test_story_title_empty_file) ... ok
test_story_vocabulary_doc_parity (__main__.DwCoreTest.test_story_vocabulary_doc_parity)
roadmap-builder §2.3 declares the vocabulary; the constants must match. ... ok
test_work_log_trace_fallback (__main__.DwCoreTest.test_work_log_trace_fallback) ... ok
test_workbench_api_view_models (__main__.DwCoreTest.test_workbench_api_view_models) ... ok
test_workbench_file_endpoint_containment (__main__.DwCoreTest.test_workbench_file_endpoint_containment) ... ok
test_workbench_is_read_only (__main__.DwCoreTest.test_workbench_is_read_only) ... ok
test_worklog_absent_root_is_optional_not_error (__main__.DwCoreTest.test_worklog_absent_root_is_optional_not_error) ... ok
test_worklog_endpoint_containment_and_omission (__main__.DwCoreTest.test_worklog_endpoint_containment_and_omission) ... ok
test_write_containment (__main__.DwCoreTest.test_write_containment) ... ok
test_append_only_and_never_raises (__main__.EventsTest.test_append_only_and_never_raises) ... ok
test_content_audit_rogue_keys_dropped (__main__.EventsTest.test_content_audit_rogue_keys_dropped) ... ok
test_gate_refusal_carries_its_rule (__main__.EventsTest.test_gate_refusal_carries_its_rule) ... ok
test_rail_moments_emit (__main__.EventsTest.test_rail_moments_emit) ... ok
test_canonical_header_maps_identically (__main__.FlagshipDialectTest.test_canonical_header_maps_identically) ... ok
test_decorated_done_counts_in_state_feed (__main__.FlagshipDialectTest.test_decorated_done_counts_in_state_feed) ... ok
test_decorated_statuses_do_not_mismatch (__main__.FlagshipDialectTest.test_decorated_statuses_do_not_mismatch) ... ok
test_done_row_with_no_receipt_still_errors (__main__.FlagshipDialectTest.test_done_row_with_no_receipt_still_errors) ... ok
test_file_only_evidence_vouched_by_header (__main__.FlagshipDialectTest.test_file_only_evidence_vouched_by_header) ... ok
test_flagship_fixture_reads_clean (__main__.FlagshipDialectTest.test_flagship_fixture_reads_clean) ... ok
test_four_column_decorated_table_parses (__main__.FlagshipDialectTest.test_four_column_decorated_table_parses) ... ok
test_genuine_mismatch_still_reported (__main__.FlagshipDialectTest.test_genuine_mismatch_still_reported) ... ok
test_next_story_none_when_only_closed_phases_have_open_rows (__main__.FlagshipDialectTest.test_next_story_none_when_only_closed_phases_have_open_rows) ... ok
test_next_story_skips_closed_phases (__main__.FlagshipDialectTest.test_next_story_skips_closed_phases) ... ok
test_normalize_status_pinned_mappings (__main__.FlagshipDialectTest.test_normalize_status_pinned_mappings) ... /Users/karol/dev/reusable-processes/pmo-roadmap/lib/dw_pmo/model.py:69: DeprecationWarning: 'maxsplit' is passed as positional argument
  s = re.split(r"[(—–:;,.!]", s, 1)[0].strip()
ok
test_planted_desyncs_still_fire (__main__.FlagshipDialectTest.test_planted_desyncs_still_fire) ... ok
test_pointer_absent_falls_back_to_next_story_phase (__main__.FlagshipDialectTest.test_pointer_absent_falls_back_to_next_story_phase) ... ok
test_pointer_names_current_phase_even_closed (__main__.FlagshipDialectTest.test_pointer_names_current_phase_even_closed) ... ok
test_struck_row_makes_no_demands (__main__.FlagshipDialectTest.test_struck_row_makes_no_demands) ... /Users/karol/dev/reusable-processes/pmo-roadmap/lib/dw_pmo/model.py:69: DeprecationWarning: 'maxsplit' is passed as positional argument
  s = re.split(r"[(—–:;,.!]", s, 1)[0].strip()
/Users/karol/dev/reusable-processes/pmo-roadmap/lib/dw_pmo/model.py:69: DeprecationWarning: 'maxsplit' is passed as positional argument
  s = re.split(r"[(—–:;,.!]", s, 1)[0].strip()
ok
test_tableless_phase_reads_from_files (__main__.FlagshipDialectTest.test_tableless_phase_reads_from_files) ... ok
test_added_orphan_evidence_blocked (__main__.GateTest.test_added_orphan_evidence_blocked) ... ok
test_atomicity_and_bundle_ok (__main__.GateTest.test_atomicity_and_bundle_ok) ... ok
test_branch_mismatch (__main__.GateTest.test_branch_mismatch) ... ok
test_capital_x_boxes_count (__main__.GateTest.test_capital_x_boxes_count) ... ok
test_digest_and_trailers (__main__.GateTest.test_digest_and_trailers) ... ok
test_doctor_detections_and_health (__main__.GateTest.test_doctor_detections_and_health) ... ok
test_evidence_deletion_orphaning_done_story_blocked (__main__.GateTest.test_evidence_deletion_orphaning_done_story_blocked) ... ok
test_evidence_deletion_with_regressed_story_passes (__main__.GateTest.test_evidence_deletion_with_regressed_story_passes) ... ok
test_expected_boxes_config_fallback_beats_env (__main__.GateTest.test_expected_boxes_config_fallback_beats_env) ... ok
test_facts_missing_on_v1_style_contract (__main__.GateTest.test_facts_missing_on_v1_style_contract) ... ok
test_forced_full_tier_config (__main__.GateTest.test_forced_full_tier_config) ... ok
test_head_mismatch_after_history_moves (__main__.GateTest.test_head_mismatch_after_history_moves) ... ok
test_index_tree_mismatch_and_touch_bypass_dead (__main__.GateTest.test_index_tree_mismatch_and_touch_bypass_dead) ... ok
test_invented_staged_sample_refused (__main__.GateTest.test_invented_staged_sample_refused) ... ok
test_missing_unchecked_and_count_fallback (__main__.GateTest.test_missing_unchecked_and_count_fallback) ... ok
test_modified_evidence_of_done_story_passes (__main__.GateTest.test_modified_evidence_of_done_story_passes) ... ok
test_orphan_evidence_deletion_passes (__main__.GateTest.test_orphan_evidence_deletion_passes) ... ok
test_paths_with_spaces (__main__.GateTest.test_paths_with_spaces) ... ok
test_porcelain_verbatim (__main__.GateTest.test_porcelain_verbatim) ... ok
test_rename_of_done_story_is_not_a_flip (__main__.GateTest.test_rename_of_done_story_is_not_a_flip) ... ok
test_rules_doc_titles_extension_and_tampering (__main__.GateTest.test_rules_doc_titles_extension_and_tampering) ... ok
test_short_tier_blocked_for_roadmap_commits (__main__.GateTest.test_short_tier_blocked_for_roadmap_commits) ... ok
test_short_tier_docs_only_passes (__main__.GateTest.test_short_tier_docs_only_passes) ... ok
test_story_declaration_enforced_for_flips (__main__.GateTest.test_story_declaration_enforced_for_flips) ... ok
test_story_timeline_with_git_and_work_log (__main__.GateTest.test_story_timeline_with_git_and_work_log) ... ok
test_synonym_status_counts_as_flip (__main__.GateTest.test_synonym_status_counts_as_flip) ... ok
test_tests_capture_discharge_and_tamper (__main__.GateTest.test_tests_capture_discharge_and_tamper) ... ok
test_unpadded_numbers_pair_both_ways (__main__.GateTest.test_unpadded_numbers_pair_both_ways) ... ok
test_work_log_dir_precedence (__main__.GateTest.test_work_log_dir_precedence) ... ok
test_worklog_preconditions (__main__.GateTest.test_worklog_preconditions) ... ok
test_payload_dir_resolves_checkout_layout (__main__.LauncherTest.test_payload_dir_resolves_checkout_layout) ... ok
test_repo_dw_found_only_in_adopted_repos (__main__.LauncherTest.test_repo_dw_found_only_in_adopted_repos) ... ok
test_vendored_version_parses_init (__main__.LauncherTest.test_vendored_version_parses_init) ... ok
test_check_and_next_agree_with_core (__main__.MCPServerTest.test_check_and_next_agree_with_core) ... ok
test_core_refusal_becomes_tool_error (__main__.MCPServerTest.test_core_refusal_becomes_tool_error) ... ok
test_initialize_pins_protocol_version (__main__.MCPServerTest.test_initialize_pins_protocol_version) ... ok
test_mutation_tools_require_their_params (__main__.MCPServerTest.test_mutation_tools_require_their_params) ... ok
test_no_rails_is_a_discoverable_refusal (__main__.MCPServerTest.test_no_rails_is_a_discoverable_refusal) ... ok
test_notifications_get_no_reply_and_unknown_methods_error (__main__.MCPServerTest.test_notifications_get_no_reply_and_unknown_methods_error) ... ok
test_story_status_flip_writes_what_the_core_writes (__main__.MCPServerTest.test_story_status_flip_writes_what_the_core_writes) ... ok
test_story_status_refusal_matches_core (__main__.MCPServerTest.test_story_status_refusal_matches_core) ... ok
test_tools_list_matches_contract_and_excludes_attestation (__main__.MCPServerTest.test_tools_list_matches_contract_and_excludes_attestation) ... ok
test_unknown_tool_and_unknown_params (__main__.MCPServerTest.test_unknown_tool_and_unknown_params) ... ok
test_agents_md_gets_the_agents_variant (__main__.RiderDocsTest.test_agents_md_gets_the_agents_variant) ... ok
test_agents_transformations_actually_fire (__main__.RiderDocsTest.test_agents_transformations_actually_fire) ... ok
test_codex_and_pi_share_agents_md_without_conflict (__main__.RiderDocsTest.test_codex_and_pi_share_agents_md_without_conflict) ... ok
test_codex_installer_is_idempotent (__main__.RiderDocsTest.test_codex_installer_is_idempotent) ... ok
test_codex_skill_drift_is_a_check_error (__main__.RiderDocsTest.test_codex_skill_drift_is_a_check_error) ... ok
test_codex_skill_renders_frontmatter_and_body (__main__.RiderDocsTest.test_codex_skill_renders_frontmatter_and_body) ... ok
test_doctor_riders_wired_absent_and_broken (__main__.RiderDocsTest.test_doctor_riders_wired_absent_and_broken) ... ok
test_embedded_specs_match_source_canon (__main__.RiderDocsTest.test_embedded_specs_match_source_canon) ... ok
test_hand_edited_copy_is_a_check_error (__main__.RiderDocsTest.test_hand_edited_copy_is_a_check_error) ... ok
test_hand_edited_doc_block_is_a_check_error (__main__.RiderDocsTest.test_hand_edited_doc_block_is_a_check_error) ... ok
test_hs_context_block_lifecycle (__main__.RiderDocsTest.test_hs_context_block_lifecycle) ... ok
test_pi_installer_is_idempotent (__main__.RiderDocsTest.test_pi_installer_is_idempotent) ... ok
test_pi_prompt_drift_is_a_check_error (__main__.RiderDocsTest.test_pi_prompt_drift_is_a_check_error) ... ok
test_pi_prompt_is_verbatim_canon_and_pure (__main__.RiderDocsTest.test_pi_prompt_is_verbatim_canon_and_pure) ... ok
test_real_tree_matches_canon (__main__.RiderDocsTest.test_real_tree_matches_canon) ... ok
test_regeneration_is_idempotent (__main__.RiderDocsTest.test_regeneration_is_idempotent) ... ok
test_all_outcomes (__main__.SessionsTest.test_all_outcomes) ... ok
test_registry_failure_shapes (__main__.SessionsTest.test_registry_failure_shapes) ... ok
test_feed_reflects_real_state (__main__.StateFeedTest.test_feed_reflects_real_state) ... ok
test_schema_is_pinned (__main__.StateFeedTest.test_schema_is_pinned) ... ok
test_write_emits_the_same_document (__main__.StateFeedTest.test_write_emits_the_same_document) ... ok
test_bundled_double_flip_with_trailer_passes (__main__.VerifyTest.test_bundled_double_flip_with_trailer_passes) ... ok
test_clean_flip_with_trailers_passes (__main__.VerifyTest.test_clean_flip_with_trailers_passes) ... ok
test_double_flip_without_bundle_fails_atomicity (__main__.VerifyTest.test_double_flip_without_bundle_fails_atomicity) ... ok
test_errors_exit_via_error_field (__main__.VerifyTest.test_errors_exit_via_error_field) ... ok
test_every_rederivable_rule_id_is_a_gate_rule_or_remote_only (__main__.VerifyTest.test_every_rederivable_rule_id_is_a_gate_rule_or_remote_only) ... ok
test_evidence_deletion_orphans_done_story (__main__.VerifyTest.test_evidence_deletion_orphans_done_story) ... ok
test_flip_not_declared_in_story_trailer (__main__.VerifyTest.test_flip_not_declared_in_story_trailer) ... ok
test_malformed_digest_and_story_id (__main__.VerifyTest.test_malformed_digest_and_story_id) ... ok
test_merge_commits_are_out_of_scope (__main__.VerifyTest.test_merge_commits_are_out_of_scope) ... ok
test_non_roadmap_commits_are_out_of_scope (__main__.VerifyTest.test_non_roadmap_commits_are_out_of_scope) ... ok
test_orphan_evidence_added_without_flip (__main__.VerifyTest.test_orphan_evidence_added_without_flip) ... ok
test_pre_epoch_commits_are_skipped_not_flagged (__main__.VerifyTest.test_pre_epoch_commits_are_skipped_not_flagged) ... ok
test_render_gram
[PMO_EVIDENCE_OUTPUT_TRUNCATED]
```

### Captured run — 2026-07-08T01:23:21Z

- **Command:** `python3 pmo-roadmap/tests/dw-core-tests.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** e8a0b8299b3c64700c698f768045e001a0d45f1c

```text
test_codex_flag_opt_out_respected (__main__.AgentHooksTest.test_codex_flag_opt_out_respected) ... dw hook: codex_hooks is explicitly false in /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.mokc69vf/config.toml; respecting the opt-out
ok
test_emit_never_raises_on_garbage (__main__.AgentHooksTest.test_emit_never_raises_on_garbage) ... ok
test_emit_quiet_guard_and_unknown_event (__main__.AgentHooksTest.test_emit_quiet_guard_and_unknown_event) ... ok
test_emit_whitelists_and_never_leaks_content (__main__.AgentHooksTest.test_emit_whitelists_and_never_leaks_content) ... ok
test_install_is_idempotent (__main__.AgentHooksTest.test_install_is_idempotent) ... ok
test_status_reports_per_event (__main__.AgentHooksTest.test_status_reports_per_event) ... ok
test_uninstall_is_surgical (__main__.AgentHooksTest.test_uninstall_is_surgical) ... ok
test_anchor_only_checked_for_markdown_targets (__main__.DocsLintTest.test_anchor_only_checked_for_markdown_targets) ... ok
test_duplicate_headings_get_numeric_suffixes (__main__.DocsLintTest.test_duplicate_headings_get_numeric_suffixes) ... ok
test_every_defect_class_is_caught (__main__.DocsLintTest.test_every_defect_class_is_caught) ... ok
test_github_slug_rules (__main__.DocsLintTest.test_github_slug_rules) ... ok
test_headings_inside_fences_are_not_anchors (__main__.DocsLintTest.test_headings_inside_fences_are_not_anchors) ... ok
test_ignore_pragmas (__main__.DocsLintTest.test_ignore_pragmas) ... ok
test_links_inside_code_are_not_linted (__main__.DocsLintTest.test_links_inside_code_are_not_linted) ... ok
test_snippet_extraction_names_attrs_and_body (__main__.DocsLintTest.test_snippet_extraction_names_attrs_and_body) ... ok
test_snippet_marker_without_fence_is_an_error (__main__.DocsLintTest.test_snippet_marker_without_fence_is_an_error) ... ok
test_valid_links_anchors_and_images_pass (__main__.DocsLintTest.test_valid_links_anchors_and_images_pass) ... ok
test_agent_docs_block_lifecycle (__main__.DwCoreTest.test_agent_docs_block_lifecycle) ... ok
test_apply_cycle_and_stale_refusal (__main__.DwCoreTest.test_apply_cycle_and_stale_refusal) ... ok
test_apply_refuses_tampered_intent (__main__.DwCoreTest.test_apply_refuses_tampered_intent) ... ok
test_apply_returns_changes_and_validation (__main__.DwCoreTest.test_apply_returns_changes_and_validation) ... ok
test_apply_rolls_back_on_write_failure (__main__.DwCoreTest.test_apply_rolls_back_on_write_failure) ... ok
test_builder_final_summary_spec_matches_generator (__main__.DwCoreTest.test_builder_final_summary_spec_matches_generator) ... ok
test_canon_cited_rule_ids_exist_in_gate (__main__.DwCoreTest.test_canon_cited_rule_ids_exist_in_gate) ... ok
test_canon_fence_boxes_match_contract_template (__main__.DwCoreTest.test_canon_fence_boxes_match_contract_template) ... ok
test_capture_appends_and_records (__main__.DwCoreTest.test_capture_appends_and_records) ... ok
test_capture_never_hands_stdin_to_the_child (__main__.DwCoreTest.test_capture_never_hands_stdin_to_the_child) ... ok
test_capture_truncation_marker (__main__.DwCoreTest.test_capture_truncation_marker) ... ok
test_captured_run_parse_survives_multiline_commands (__main__.DwCoreTest.test_captured_run_parse_survives_multiline_commands) ... ok
test_changelog_release_matches_version (__main__.DwCoreTest.test_changelog_release_matches_version) ... ok
test_check_broken (__main__.DwCoreTest.test_check_broken) ... ok
test_check_clean (__main__.DwCoreTest.test_check_clean) ... ok
test_check_flags_placeholder_evidence_for_done_story (__main__.DwCoreTest.test_check_flags_placeholder_evidence_for_done_story) ... ok
test_done_requires_evidence (__main__.DwCoreTest.test_done_requires_evidence) ... ok
test_dw_version_flag_single_source (__main__.DwCoreTest.test_dw_version_flag_single_source) ... ok
test_evidence_content_lints (__main__.DwCoreTest.test_evidence_content_lints) ... ok
test_find_story_selectors (__main__.DwCoreTest.test_find_story_selectors) ... ok
test_formula_version_single_source (__main__.DwCoreTest.test_formula_version_single_source) ... ok
test_guard_lets_remediation_through (__main__.DwCoreTest.test_guard_lets_remediation_through) ... ok
test_handoff_summary_text (__main__.DwCoreTest.test_handoff_summary_text) ... ok
test_health_classifier_kinds (__main__.DwCoreTest.test_health_classifier_kinds) ... ok
test_health_report_shape_and_guard (__main__.DwCoreTest.test_health_report_shape_and_guard) ... ok
test_hook_seam_explanations (__main__.DwCoreTest.test_hook_seam_explanations) ... ok
test_host_header_allowlist (__main__.DwCoreTest.test_host_header_allowlist) ... ok
test_missioncontrol_has_no_mutation_route (__main__.DwCoreTest.test_missioncontrol_has_no_mutation_route) ... ok
test_missioncontrol_live_layer_pins_only_on_story (__main__.DwCoreTest.test_missioncontrol_live_layer_pins_only_on_story) ... ok
test_missioncontrol_payload_carries_the_live_layer (__main__.DwCoreTest.test_missioncontrol_payload_carries_the_live_layer) ... ok
test_missioncontrol_readonly_fitness_guard (__main__.DwCoreTest.test_missioncontrol_readonly_fitness_guard) ... ok
test_missioncontrol_readonly_guard_catches_a_planted_write (__main__.DwCoreTest.test_missioncontrol_readonly_guard_catches_a_planted_write) ... ok
test_missioncontrol_route_serves_the_three_documents (__main__.DwCoreTest.test_missioncontrol_route_serves_the_three_documents) ... ok
test_missioncontrol_tail_clamps (__main__.DwCoreTest.test_missioncontrol_tail_clamps) ... ok
test_mutation_fingerprint_binds_content (__main__.DwCoreTest.test_mutation_fingerprint_binds_content) ... ok
test_mutation_preview_guarded_by_validation_issues (__main__.DwCoreTest.test_mutation_preview_guarded_by_validation_issues) ... ok
test_mutation_preview_maps_one_to_one_and_writes_nothing (__main__.DwCoreTest.test_mutation_preview_maps_one_to_one_and_writes_nothing) ... ok
test_mutation_preview_refusals (__main__.DwCoreTest.test_mutation_preview_refusals) ... ok
test_mutation_slug_injection_refused (__main__.DwCoreTest.test_mutation_slug_injection_refused) ... ok
test_narrative_only_warning (__main__.DwCoreTest.test_narrative_only_warning) ... ok
test_noop_mutation_is_explicitly_idempotent (__main__.DwCoreTest.test_noop_mutation_is_explicitly_idempotent) ... ok
test_parse_adoption_report (__main__.DwCoreTest.test_parse_adoption_report) ... ok
test_parse_adoption_report_malformed (__main__.DwCoreTest.test_parse_adoption_report_malformed) ... ok
test_parser_discovery (__main__.DwCoreTest.test_parser_discovery) ... ok
test_phase_create_and_close (__main__.DwCoreTest.test_phase_create_and_close) ... ok
test_plugin_commands_match_installer_commands (__main__.DwCoreTest.test_plugin_commands_match_installer_commands) ... ok
test_plugin_skill_parity_with_managed_block (__main__.DwCoreTest.test_plugin_skill_parity_with_managed_block) ... ok
test_plugin_version_single_source (__main__.DwCoreTest.test_plugin_version_single_source) ... ok
test_preview_is_pure_and_idempotent (__main__.DwCoreTest.test_preview_is_pure_and_idempotent) ... ok
test_projected_issues_sees_the_future (__main__.DwCoreTest.test_projected_issues_sees_the_future) ... ok
test_pyproject_version_single_source_and_entry_point (__main__.DwCoreTest.test_pyproject_version_single_source_and_entry_point) ... ok
test_run_adoption_preview_and_apply (__main__.DwCoreTest.test_run_adoption_preview_and_apply) ... ok
test_serve_fails_closed_without_roadmap (__main__.DwCoreTest.test_serve_fails_closed_without_roadmap) ... ok
test_stale_target_refused_without_partial_write (__main__.DwCoreTest.test_stale_target_refused_without_partial_write) ... ok
test_status_vocabulary_validation (__main__.DwCoreTest.test_status_vocabulary_validation) ... ok
test_story_scaffold_matches_documented_template (__main__.DwCoreTest.test_story_scaffold_matches_documented_template) ... ok
test_story_timeline_chain_and_shipped (__main__.DwCoreTest.test_story_timeline_chain_and_shipped) ... ok
test_story_timeline_never_claims_unshipped (__main__.DwCoreTest.test_story_timeline_never_claims_unshipped) ... ok
test_story_timeline_work_log_only (__main__.DwCoreTest.test_story_timeline_work_log_only) ... ok
test_story_title_empty_file (__main__.DwCoreTest.test_story_title_empty_file) ... ok
test_story_vocabulary_doc_parity (__main__.DwCoreTest.test_story_vocabulary_doc_parity)
roadmap-builder §2.3 declares the vocabulary; the constants must match. ... ok
test_work_log_trace_fallback (__main__.DwCoreTest.test_work_log_trace_fallback) ... ok
test_workbench_api_view_models (__main__.DwCoreTest.test_workbench_api_view_models) ... ok
test_workbench_file_endpoint_containment (__main__.DwCoreTest.test_workbench_file_endpoint_containment) ... ok
test_workbench_is_read_only (__main__.DwCoreTest.test_workbench_is_read_only) ... ok
test_worklog_absent_root_is_optional_not_error (__main__.DwCoreTest.test_worklog_absent_root_is_optional_not_error) ... ok
test_worklog_endpoint_containment_and_omission (__main__.DwCoreTest.test_worklog_endpoint_containment_and_omission) ... ok
test_write_containment (__main__.DwCoreTest.test_write_containment) ... ok
test_append_only_and_never_raises (__main__.EventsTest.test_append_only_and_never_raises) ... ok
test_content_audit_rogue_keys_dropped (__main__.EventsTest.test_content_audit_rogue_keys_dropped) ... ok
test_gate_refusal_carries_its_rule (__main__.EventsTest.test_gate_refusal_carries_its_rule) ... ok
test_rail_moments_emit (__main__.EventsTest.test_rail_moments_emit) ... ok
test_canonical_header_maps_identically (__main__.FlagshipDialectTest.test_canonical_header_maps_identically) ... ok
test_decorated_done_counts_in_state_feed (__main__.FlagshipDialectTest.test_decorated_done_counts_in_state_feed) ... ok
test_decorated_statuses_do_not_mismatch (__main__.FlagshipDialectTest.test_decorated_statuses_do_not_mismatch) ... ok
test_done_row_with_no_receipt_still_errors (__main__.FlagshipDialectTest.test_done_row_with_no_receipt_still_errors) ... ok
test_file_only_evidence_vouched_by_header (__main__.FlagshipDialectTest.test_file_only_evidence_vouched_by_header) ... ok
test_flagship_fixture_reads_clean (__main__.FlagshipDialectTest.test_flagship_fixture_reads_clean) ... ok
test_four_column_decorated_table_parses (__main__.FlagshipDialectTest.test_four_column_decorated_table_parses) ... ok
test_genuine_mismatch_still_reported (__main__.FlagshipDialectTest.test_genuine_mismatch_still_reported) ... ok
test_next_story_none_when_only_closed_phases_have_open_rows (__main__.FlagshipDialectTest.test_next_story_none_when_only_closed_phases_have_open_rows) ... ok
test_next_story_skips_closed_phases (__main__.FlagshipDialectTest.test_next_story_skips_closed_phases) ... ok
test_normalize_status_pinned_mappings (__main__.FlagshipDialectTest.test_normalize_status_pinned_mappings) ... ok
test_planted_desyncs_still_fire (__main__.FlagshipDialectTest.test_planted_desyncs_still_fire) ... ok
test_pointer_absent_falls_back_to_next_story_phase (__main__.FlagshipDialectTest.test_pointer_absent_falls_back_to_next_story_phase) ... ok
test_pointer_names_current_phase_even_closed (__main__.FlagshipDialectTest.test_pointer_names_current_phase_even_closed) ... ok
test_struck_row_makes_no_demands (__main__.FlagshipDialectTest.test_struck_row_makes_no_demands) ... ok
test_tableless_phase_reads_from_files (__main__.FlagshipDialectTest.test_tableless_phase_reads_from_files) ... ok
test_added_orphan_evidence_blocked (__main__.GateTest.test_added_orphan_evidence_blocked) ... ok
test_atomicity_and_bundle_ok (__main__.GateTest.test_atomicity_and_bundle_ok) ... ok
test_branch_mismatch (__main__.GateTest.test_branch_mismatch) ... ok
test_capital_x_boxes_count (__main__.GateTest.test_capital_x_boxes_count) ... ok
test_digest_and_trailers (__main__.GateTest.test_digest_and_trailers) ... ok
test_doctor_detections_and_health (__main__.GateTest.test_doctor_detections_and_health) ... ok
test_evidence_deletion_orphaning_done_story_blocked (__main__.GateTest.test_evidence_deletion_orphaning_done_story_blocked) ... ok
test_evidence_deletion_with_regressed_story_passes (__main__.GateTest.test_evidence_deletion_with_regressed_story_passes) ... ok
test_expected_boxes_config_fallback_beats_env (__main__.GateTest.test_expected_boxes_config_fallback_beats_env) ... ok
test_facts_missing_on_v1_style_contract (__main__.GateTest.test_facts_missing_on_v1_style_contract) ... ok
test_forced_full_tier_config (__main__.GateTest.test_forced_full_tier_config) ... ok
test_head_mismatch_after_history_moves (__main__.GateTest.test_head_mismatch_after_history_moves) ... ok
test_index_tree_mismatch_and_touch_bypass_dead (__main__.GateTest.test_index_tree_mismatch_and_touch_bypass_dead) ... ok
test_invented_staged_sample_refused (__main__.GateTest.test_invented_staged_sample_refused) ... ok
test_missing_unchecked_and_count_fallback (__main__.GateTest.test_missing_unchecked_and_count_fallback) ... ok
test_modified_evidence_of_done_story_passes (__main__.GateTest.test_modified_evidence_of_done_story_passes) ... ok
test_orphan_evidence_deletion_passes (__main__.GateTest.test_orphan_evidence_deletion_passes) ... ok
test_paths_with_spaces (__main__.GateTest.test_paths_with_spaces) ... ok
test_porcelain_verbatim (__main__.GateTest.test_porcelain_verbatim) ... ok
test_rename_of_done_story_is_not_a_flip (__main__.GateTest.test_rename_of_done_story_is_not_a_flip) ... ok
test_rules_doc_titles_extension_and_tampering (__main__.GateTest.test_rules_doc_titles_extension_and_tampering) ... ok
test_short_tier_blocked_for_roadmap_commits (__main__.GateTest.test_short_tier_blocked_for_roadmap_commits) ... ok
test_short_tier_docs_only_passes (__main__.GateTest.test_short_tier_docs_only_passes) ... ok
test_story_declaration_enforced_for_flips (__main__.GateTest.test_story_declaration_enforced_for_flips) ... ok
test_story_timeline_with_git_and_work_log (__main__.GateTest.test_story_timeline_with_git_and_work_log) ... ok
test_synonym_status_counts_as_flip (__main__.GateTest.test_synonym_status_counts_as_flip) ... ok
test_tests_capture_discharge_and_tamper (__main__.GateTest.test_tests_capture_discharge_and_tamper) ... ok
test_unpadded_numbers_pair_both_ways (__main__.GateTest.test_unpadded_numbers_pair_both_ways) ... ok
test_work_log_dir_precedence (__main__.GateTest.test_work_log_dir_precedence) ... ok
test_worklog_preconditions (__main__.GateTest.test_worklog_preconditions) ... ok
test_payload_dir_resolves_checkout_layout (__main__.LauncherTest.test_payload_dir_resolves_checkout_layout) ... ok
test_repo_dw_found_only_in_adopted_repos (__main__.LauncherTest.test_repo_dw_found_only_in_adopted_repos) ... ok
test_vendored_version_parses_init (__main__.LauncherTest.test_vendored_version_parses_init) ... ok
test_check_and_next_agree_with_core (__main__.MCPServerTest.test_check_and_next_agree_with_core) ... ok
test_core_refusal_becomes_tool_error (__main__.MCPServerTest.test_core_refusal_becomes_tool_error) ... ok
test_initialize_pins_protocol_version (__main__.MCPServerTest.test_initialize_pins_protocol_version) ... ok
test_mutation_tools_require_their_params (__main__.MCPServerTest.test_mutation_tools_require_their_params) ... ok
test_no_rails_is_a_discoverable_refusal (__main__.MCPServerTest.test_no_rails_is_a_discoverable_refusal) ... ok
test_notifications_get_no_reply_and_unknown_methods_error (__main__.MCPServerTest.test_notifications_get_no_reply_and_unknown_methods_error) ... ok
test_story_status_flip_writes_what_the_core_writes (__main__.MCPServerTest.test_story_status_flip_writes_what_the_core_writes) ... ok
test_story_status_refusal_matches_core (__main__.MCPServerTest.test_story_status_refusal_matches_core) ... ok
test_tools_list_matches_contract_and_excludes_attestation (__main__.MCPServerTest.test_tools_list_matches_contract_and_excludes_attestation) ... ok
test_unknown_tool_and_unknown_params (__main__.MCPServerTest.test_unknown_tool_and_unknown_params) ... ok
test_agents_md_gets_the_agents_variant (__main__.RiderDocsTest.test_agents_md_gets_the_agents_variant) ... ok
test_agents_transformations_actually_fire (__main__.RiderDocsTest.test_agents_transformations_actually_fire) ... ok
test_codex_and_pi_share_agents_md_without_conflict (__main__.RiderDocsTest.test_codex_and_pi_share_agents_md_without_conflict) ... ok
test_codex_installer_is_idempotent (__main__.RiderDocsTest.test_codex_installer_is_idempotent) ... ok
test_codex_skill_drift_is_a_check_error (__main__.RiderDocsTest.test_codex_skill_drift_is_a_check_error) ... ok
test_codex_skill_renders_frontmatter_and_body (__main__.RiderDocsTest.test_codex_skill_renders_frontmatter_and_body) ... ok
test_doctor_riders_wired_absent_and_broken (__main__.RiderDocsTest.test_doctor_riders_wired_absent_and_broken) ... ok
test_embedded_specs_match_source_canon (__main__.RiderDocsTest.test_embedded_specs_match_source_canon) ... ok
test_hand_edited_copy_is_a_check_error (__main__.RiderDocsTest.test_hand_edited_copy_is_a_check_error) ... ok
test_hand_edited_doc_block_is_a_check_error (__main__.RiderDocsTest.test_hand_edited_doc_block_is_a_check_error) ... ok
test_hs_context_block_lifecycle (__main__.RiderDocsTest.test_hs_context_block_lifecycle) ... ok
test_pi_installer_is_idempotent (__main__.RiderDocsTest.test_pi_installer_is_idempotent) ... ok
test_pi_prompt_drift_is_a_check_error (__main__.RiderDocsTest.test_pi_prompt_drift_is_a_check_error) ... ok
test_pi_prompt_is_verbatim_canon_and_pure (__main__.RiderDocsTest.test_pi_prompt_is_verbatim_canon_and_pure) ... ok
test_real_tree_matches_canon (__main__.RiderDocsTest.test_real_tree_matches_canon) ... ok
test_regeneration_is_idempotent (__main__.RiderDocsTest.test_regeneration_is_idempotent) ... ok
test_all_outcomes (__main__.SessionsTest.test_all_outcomes) ... ok
test_registry_failure_shapes (__main__.SessionsTest.test_registry_failure_shapes) ... ok
test_feed_reflects_real_state (__main__.StateFeedTest.test_feed_reflects_real_state) ... ok
test_schema_is_pinned (__main__.StateFeedTest.test_schema_is_pinned) ... ok
test_write_emits_the_same_document (__main__.StateFeedTest.test_write_emits_the_same_document) ... ok
test_bundled_double_flip_with_trailer_passes (__main__.VerifyTest.test_bundled_double_flip_with_trailer_passes) ... ok
test_clean_flip_with_trailers_passes (__main__.VerifyTest.test_clean_flip_with_trailers_passes) ... ok
test_double_flip_without_bundle_fails_atomicity (__main__.VerifyTest.test_double_flip_without_bundle_fails_atomicity) ... ok
test_errors_exit_via_error_field (__main__.VerifyTest.test_errors_exit_via_error_field) ... ok
test_every_rederivable_rule_id_is_a_gate_rule_or_remote_only (__main__.VerifyTest.test_every_rederivable_rule_id_is_a_gate_rule_or_remote_only) ... ok
test_evidence_deletion_orphans_done_story (__main__.VerifyTest.test_evidence_deletion_orphans_done_story) ... ok
test_flip_not_declared_in_story_trailer (__main__.VerifyTest.test_flip_not_declared_in_story_trailer) ... ok
test_malformed_digest_and_story_id (__main__.VerifyTest.test_malformed_digest_and_story_id) ... ok
test_merge_commits_are_out_of_scope (__main__.VerifyTest.test_merge_commits_are_out_of_scope) ... ok
test_non_roadmap_commits_are_out_of_scope (__main__.VerifyTest.test_non_roadmap_commits_are_out_of_scope) ... ok
test_orphan_evidence_added_without_flip (__main__.VerifyTest.test_orphan_evidence_added_without_flip) ... ok
test_pre_epoch_commits_are_skipped_not_flagged (__main__.VerifyTest.test_pre_epoch_commits_are_skipped_not_flagged) ... ok
test_render_grammar (__main__.VerifyTest.test_render_grammar) ... ok
test_smuggled_flip_names_missing_trailer_and_evidence (__main__.VerifyTest.test_smuggled_flip_names_missing_trailer_and_evidence) ... ok

----------------------------------------------------------------------
Ran 183 tests in 10.054s

OK
dw hook: claude — 4 installed, 0 already present in /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.5mzxjo95/settings.json
dw hook: claude — 0 installed, 4 already present in /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.5mzxjo95/sett
[PMO_EVIDENCE_OUTPUT_TRUNCATED]
```
