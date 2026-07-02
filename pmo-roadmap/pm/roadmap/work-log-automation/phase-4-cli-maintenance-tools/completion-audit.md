# PMO Workbench Completion Audit

**Date:** 2026-07-01.
**Scope:** PMO Workbench as an evidence-first, agent-safe roadmap manipulation
layer over Delivery Workbench PMO files.

## Requirement Mapping

| Requirement | Evidence |
|---|---|
| Markdown remains authoritative; generated JSON/cache is disposable | `pmo-roadmap/bin/dw` reads/writes `pm/roadmap/**`; `pmo-roadmap/README.md` documents markdown as source of truth |
| Deterministic PMO core parses projects, phases, stories, evidence, final summaries, supplemental canon, and validation issues | `pmo-roadmap/bin/dw` functions `discover_projects`, `discover_phases`, `parse_story_rows`, `supplemental_canon`, `check_project`; covered by `pmo-roadmap/tests/roadmap-cli.sh` |
| Machine-readable context includes projects, active phases, story status, evidence presence, next work, stale pointers, missing files, and drift warnings | `dw context`; tested in `roadmap-cli.sh` canonical and drift fixtures |
| Safe mutation commands exist for create phase, create story, update story status, attach evidence, close phase, and validate | `dw phase create`, `dw story create`, `dw story status`, `dw story evidence`, `dw phase close`, `dw check`; tested in `roadmap-cli.sh` |
| Writes are constrained to PMO-owned paths | `ensure_under` guards PMO writes in `dw`; write commands operate under `roadmap_dir(root)` |
| Mutation commands refuse partial invariant-breaking updates | `write_changes` batches affected PMO file contents and restores originals if a later write fails; status/evidence/phase-close commands compute all changed files before writing |
| Preserve hand-authored prose and normalize only owned metadata/tables | `update_story_header_status`, `update_story_table_row`, `update_phase_index_status`; no broad markdown rendering is used |
| No done without evidence | `dw story status ... done` refuses without evidence; tested in `roadmap-cli.sh` |
| Validation catches broken links, status mismatches, stale phase pointers, missing evidence, orphan evidence, and missing final summaries | `check_project`; `roadmap-cli.sh` asserts broken story link, broken evidence link, done-without-evidence-link, orphan evidence, status mismatch, stale pointer, and missing final-summary failures |
| Supports multiple open phases, stale README pointers, supplemental orchestrator files, handover/audit/vision docs, and older hooks | `project_warnings`, `parse_current_phase_target`, `supplemental_canon`, `hook_snapshot`; tested in `roadmap-cli.sh` drift fixture |
| Traceability spans README, phase status, story, evidence, final summary, commits, and work logs where available | `story_context(..., include_trace=True)`, `recent_commits`, `work_log_entries`; work-log trace tested in `roadmap-cli.sh` |
| Parse/write idempotence where no semantic edit is requested | `roadmap-cli.sh` compares checksums before/after repeating the same done status with existing evidence; `context --trace` output is also compared across runs |
| Parser/validator/CLI exists before any UI | This implementation is CLI/core only; no UI files added |
| Tests cover canonical and realistic drift cases | `pmo-roadmap/tests/roadmap-cli.sh` creates a canonical sample roadmap plus a drifted consumer-style roadmap |

## Validation Commands

```text
bash -n pmo-roadmap/bin/work-log-read \
  pmo-roadmap/bin/work-log-summarize \
  pmo-roadmap/bootstrap/adopt-project.sh \
  pmo-roadmap/bootstrap/new-project.sh \
  pmo-roadmap/bootstrap/session-intake.sh \
  pmo-roadmap/hooks/pre-commit \
  pmo-roadmap/hooks/post-commit \
  pmo-roadmap/install.sh \
  pmo-roadmap/update.sh \
  pmo-roadmap/tests/adoption-discovery.sh \
  pmo-roadmap/tests/roadmap-cli.sh \
  pmo-roadmap/tests/work-log-mvp.sh \
  demos/scripts/prepare-onboarding-demo.sh \
  demos/scripts/prepare-commit-demo.sh \
  demos/scripts/write-demo-contract.sh

python3 -m py_compile pmo-roadmap/bin/dw
pmo-roadmap/tests/adoption-discovery.sh
pmo-roadmap/tests/roadmap-cli.sh
pmo-roadmap/tests/work-log-mvp.sh
demos/scripts/prepare-onboarding-demo.sh
demos/scripts/prepare-commit-demo.sh
pmo-roadmap/bin/dw check work-log-automation
git diff --check
```

## Residual Scope

A rich PMO Workbench UI or local service wrapper can be built later, but it
should reuse this invariant-preserving CLI/core behavior instead of creating a
parallel roadmap model.
