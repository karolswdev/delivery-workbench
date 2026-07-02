# Evidence - WLA-6-05

- **Story:** WLA-6-05 - Ship the first-class agent surface
- **Status:** done
- **Date:** 2026-07-02

## What shipped

- **Shipped slash commands** (`pmo-roadmap/agent/dw-next|dw-contract|
  dw-story-done|dw-adopt.md`): plain-markdown prompts invoking
  `.githooks/dw`, installed by `install.sh` and refreshed by
  `update.sh` into `.claude/commands/`.
- **Managed agent-docs block** (`dw_pmo/agentdocs.py`,
  `dw agent-docs`): a marker-delimited Delivery Workbench block written
  into `CLAUDE.md` (or an existing `AGENTS.md`) by install (default on,
  `--no-agent-docs` opt-out) and refreshed only inside the markers by
  update — created/added/refreshed/unchanged semantics, user content
  above and below untouched, never duplicated. The block is the snippet
  rewrite: it covers `dw context/check/next/gate/contract/evidence
  capture/doctor`, the roadmap location, the full commit ritual, and
  the status vocabulary. `templates/CLAUDE-snippet.md` is now generated
  from the same embedded canonical text (verified equal).
- **`dw doctor`** (`dw_pmo/doctor.py`): names every historically silent
  wiring failure — python3 off PATH (the gate's fail-closed dependency),
  unset `core.hooksPath`, each missing hook, missing dw/core install,
  missing or stale agent-docs block, missing roadmap — exit 0 only when
  healthy, and prints the canonical invocation.
- **Agent-honest ergonomics:** `dw next --json` with the documented
  0/2/1 exit contract (2 = nothing actionable, with an explicit
  `{"next_story": null}`); story statuses validated against the single
  vocabulary (`blocked` finally added to `OPEN_STATUSES`) with the
  allowed list in every rejection; the blocked-commit banner now embeds
  the copy-pasteable contract template with live stamped facts and the
  project's actual rule set; `work-log-read` prints full files by
  default with `--max-lines` + an explicit truncation marker replacing
  the old silent 260-line cut.
- **Bonus fix caught by the acceptance test:** `new-project.sh` left the
  phase-status template's placeholder story row (`story-01-…`) in the
  scaffolded table, so every fresh install failed `dw check` out of the
  box with a broken story link. The scaffold now writes the real
  bootstrap row; a fresh install passes `dw check` immediately.

## Acceptance proof

The full-lifecycle acceptance criterion is executed headlessly by
`pmo-roadmap/tests/agent-surface.sh` using only commands named in the
managed CLAUDE.md block and the shipped slash commands: install →
`dw doctor` healthy → `dw story create` → `dw next --json` →
in-progress → `dw evidence capture` → done → `dw contract new
--tests-capture` → certified → gated `git commit` → `PMO-Story` trailer
asserted → `dw check` green. The same suite covers the managed-block
lifecycle (fresh/existing/re-run/corrupt+update-restore), doctor
detections (unset hooksPath, missing hook, stale block, unhealthy exit
1), the inline banner template (boxes + live `**Index-tree:**` fact),
the `next` exit-2 drain, and `work-log-read` paging. On this repo,
`dw doctor` reports healthy (see WLA-6-05 shipping commit), satisfying
the phase exit criterion "there and here".

## Proof — captured runs (appended by `dw evidence capture`)

### Captured run — 2026-07-02T16:19:34Z

- **Command:** `pmo-roadmap/tests/agent-surface.sh`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** ca851da54bd23d6dbdc6e7a5e9e50d2ac662aec4

```text
agent-surface.sh: ok
```

### Captured run — 2026-07-02T16:19:38Z

- **Command:** `python3 pmo-roadmap/tests/dw-core-tests.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** ca851da54bd23d6dbdc6e7a5e9e50d2ac662aec4

```text
test_agent_docs_block_lifecycle (__main__.DwCoreTest.test_agent_docs_block_lifecycle) ... ok
test_apply_returns_changes_and_validation (__main__.DwCoreTest.test_apply_returns_changes_and_validation) ... ok
test_capture_appends_and_records (__main__.DwCoreTest.test_capture_appends_and_records) ... ok
test_capture_truncation_marker (__main__.DwCoreTest.test_capture_truncation_marker) ... ok
test_check_broken (__main__.DwCoreTest.test_check_broken) ... ok
test_check_clean (__main__.DwCoreTest.test_check_clean) ... ok
test_check_flags_placeholder_evidence_for_done_story (__main__.DwCoreTest.test_c
[PMO_EVIDENCE_OUTPUT_TRUNCATED]
```
