# Evidence - WLA-5-02 - Extract reusable PMO core API boundary

- **Story:** [story-02-reusable-core-api-boundary](./story-02-reusable-core-api-boundary.md)
- **Status:** done
- **Date:** 2026-07-02

## What shipped

`pmo-roadmap/lib/dw_pmo/` now owns the parser, validator, trace, and
mutation logic previously embedded in `pmo-roadmap/bin/dw` (1,232
lines). `bin/dw` is a 362-line adapter: argparse plus thin handlers.

| Module | Owns | Lines |
|---|---|---|
| `model.py` | Project/Phase/StoryRow dataclasses, status vocabulary, regexes, `DwError` | 55 |
| `paths.py` | root discovery, roadmap-tree containment, work-log root, template dir | 93 |
| `parse.py` | project/phase/story discovery, table parsing, find_story, hook snapshot, canon scan | 220 |
| `validate.py` | `check_project` structural lint, drift warnings | 88 |
| `trace.py` | git history, work-log entry parsing/correlation | 71 |
| `render.py` | pure content rendering: templates + owned-region table rewrites | 251 |
| `mutations.py` | `MutationPlan`/`FileChange`, plan builders, `preview_plan`, `apply_plan`, rollback `write_changes` | 313 |
| `api.py` | `story_context`, `project_context`, `build_context_payload` envelopes, `next_story` | 161 |

Deliberate API changes (documented per the acceptance criterion's
"equivalent cohesive structure" clause):

- `die()` now raises a catchable `DwError(message, code)`; the CLI
  adapter converts it to the historical `dw: <message>` stderr line and
  exit code, so CLI behavior is unchanged while library consumers
  (workbench server, future `dw gate`) can handle refusals.
- Mutations are two-step primitives: `plan_*` (pure reads, all refusal
  checks, fingerprint of each target's current content) then
  `apply_plan` (re-verifies fingerprints — stale targets refused before
  any write — writes with the Phase 4 rollback behavior, returns changed
  files plus post-apply `check_project` issues). `preview_plan` renders
  a plan without touching disk. This is the preview -> diff ->
  apply-with-fingerprint -> revalidate seam the Phase 5 workbench
  requires.
- Distribution: `install.sh`/`update.sh` copy `lib/dw_pmo/` to
  `.githooks/dw_pmo/`; `bin/dw` bootstraps `sys.path` for both source
  and installed layouts and fails with a clear message if the core is
  missing.
- Dropped four dead write-wrapper functions (`replace_phase_index`,
  `replace_story_table`, `update_story_header_status`,
  `update_story_table_row`, `update_phase_index_status` write variants)
  that had no callers; guarded `story_title` against empty files
  (previously an IndexError).

## Compatibility proof (Phase 4 CLI contract intact)

Baseline outputs captured from the pre-extraction `dw`, re-run on the
identical tree with the adapter, compared byte-for-byte:

```text
IDENTICAL help.txt            IDENTICAL context-trace.json
IDENTICAL context.json        IDENTICAL tree.txt
IDENTICAL check.txt           IDENTICAL projects.txt
IDENTICAL story-list.txt      IDENTICAL phase-list.txt
IDENTICAL next.txt
```

Error-path parity:

```text
$ dw story status work-log-automation 6 2 done
dw: refusing to mark story done without evidence; pass --evidence-body or --evidence-from-file
exit=1
```

## Command output

Core unit tests (new, `pmo-roadmap/tests/dw-core-tests.py`, 12 cases:
parser fixtures, clean/broken validation fixtures, preview purity and
idempotence, apply-returns-changes-plus-validation, stale-target
refusal without partial writes, done-requires-evidence, roadmap-tree
write containment, phase create/close, work-log trace fallback):

```text
Ran 12 tests in 0.028s
OK
```

Full validation set after the extraction:

```text
python3 -m py_compile pmo-roadmap/bin/dw         -> ok
python3 -m compileall -q pmo-roadmap/lib/dw_pmo  -> ok
python3 pmo-roadmap/tests/dw-core-tests.py       -> OK (12 tests)
pmo-roadmap/tests/adoption-discovery.sh          -> adoption-discovery.sh: ok
pmo-roadmap/tests/roadmap-cli.sh                 -> roadmap-cli.sh: ok   (unchanged, passes)
pmo-roadmap/tests/work-log-mvp.sh                -> work-log-mvp.sh: ok  (strengthened: asserts
                                                    .githooks/dw_pmo/__init__.py exists and the
                                                    installed dw executes)
pmo-roadmap/bin/dw check work-log-automation     -> dw check: ok
.githooks/dw check work-log-automation           -> dw check: ok  (installed copy, bundled core)
```

CI: the WLA-6-01 push (run 28594155384) completed green including the
"Roadmap self-validation (dogfood)" step; this story adds the
"dw core unit tests" step to `.github/workflows/validation.yml`.

## Acceptance criteria check

- [x] `pmo-roadmap/lib/dw_pmo/` exists with model, paths, parse,
  validate, trace, mutations, render, and api modules (table above).
- [x] `pmo-roadmap/bin/dw` imports the shared core; Phase 4 command
  behavior proven intact by the byte-identical output matrix and the
  unchanged `roadmap-cli.sh` suite.
- [x] Core mutation APIs produce previews without writing
  (`preview_plan`; purity asserted by unit test).
- [x] Core apply APIs write only PMO-owned paths (`ensure_under`
  containment test), reuse rollback (`write_changes` unchanged), and
  return changed files plus validation results (unit test).
- [x] `roadmap-cli.sh` passes unchanged; `work-log-mvp.sh` gained only
  contract-strengthening assertions.
- [x] New core tests cover parser fixtures, validation fixtures,
  mutation preview idempotence, stale-target handling, and trace
  fallback behavior (12 cases listed above).
