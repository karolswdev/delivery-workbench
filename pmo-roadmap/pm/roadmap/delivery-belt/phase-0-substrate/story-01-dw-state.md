# DW-0-01 — `dw state`: the machine-readable roadmap state

- **Project:** delivery-belt
- **Phase:** 0
- **Status:** backlog
- **Depends on:** none
- **Unblocks:** DW-0-02, DW-0-03, DW-0-04
- **Owner:** unassigned

## Problem

The roadmap is markdown-as-database: every consumer (agent, hook, and soon
the Belt UI) re-derives state by regexing prose. The RFC's substrate slice
starts here: one parser, one JSON contract, generated-on-read, so the desk
reads state, not regex.

## Scope

- **In:** `bin/dw` (single-file, python3 stdlib only) with the `state`
  subcommand; the v1 JSON contract below; parsing of: project dirs under
  `pm/roadmap/` (excluding the framework's own `roadmap-builder.md` /
  `PMO-CONTRACT.md`), project README (`Last updated`, current-phase pointer,
  phase-index rows), phase dirs (`phase-{n}-{slug}`), story files (H1 id +
  title, `- **Status:**` header, `Depends on`), evidence existence pairing,
  `final-summary.md` existence, `current-phase-status.md` (H1 title, `Last
  updated`, story-table rows, exit-criteria checkbox counts, "Where we are"
  block); status normalization (see DW-0-02 — shared helper); derived phase
  status. `--project <slug>` and `--root <path>` flags. Exit 0 with JSON on
  stdout; parse warnings on stderr, never fatal.
- **Out:** the linter (DW-0-02), mutations (DW-0-03), git/PR/CI receipts
  (B1 composes those hub-side), any on-disk cache.

## The v1 JSON contract

```json
{
  "dw_state_version": 1,
  "root": "<abs path>",
  "generated_at": "<ISO-8601 UTC>",
  "projects": [{
    "slug": "…", "dir": "pm/roadmap/…", "prefix": "HS",
    "readme": {"last_updated": "YYYY-MM-DD|null", "current_phase": "phase-…|null",
               "index": [{"phase": "…", "status_raw": "…", "folder": "…"}]},
    "phases": [{
      "number": "…", "slug": "…", "dir": "…", "title": "…|null",
      "status": "scaffolded|in-progress|done|closed|unknown",
      "status_source": "derived",
      "last_updated": "…|null",
      "where_we_are": "…|null",
      "exit_criteria": {"checked": 0, "total": 0},
      "has_final_summary": false,
      "table_rows": [{"id": "…", "status_raw": "…", "status": "…"}],
      "stories": [{
        "id": "…", "seq": 1, "slug": "…", "title": "…", "file": "…",
        "status_raw": "…", "status": "backlog|ready|in-progress|blocked|done|cut|unknown",
        "depends_on": [], "evidence_file": "…|null", "evidence_exists": false
      }]
    }]
  }]
}
```

Derived phase status: `closed` if `final-summary.md` exists; else `done` if
all stories are terminal (done/cut) and there is at least one story; else
`in-progress` if any story is in-progress/done; else `scaffolded` if stories
exist; else `unknown`.

## Acceptance criteria

- [ ] `bin/dw state` at this repo's root emits valid JSON (parses with
      `python3 -m json.tool`) listing the `work-log-automation` and
      `delivery-belt` projects with correct phase/story counts.
- [ ] `bin/dw state --root ~/dev/tools/HoldSpeak` covers the `holdspeak` and
      `holdspeak-mobile` projects; phase count for `holdspeak` matches
      `ls -d pm/roadmap/holdspeak/phase-* | wc -l`; no file in the consumer
      repo is created or modified (verified via `git status --porcelain`).
- [ ] A story with header `- **Status:** done` and an existing
      `evidence-story-{n}.md` reports `"status": "done"`,
      `"evidence_exists": true`.
- [ ] Malformed/legacy files degrade to warnings on stderr + `"unknown"`
      fields, never a traceback; exit code stays 0.
- [ ] `tests/dw-cli.sh` covers the above on a temp fixture; runs green.

## Test plan

- **Unit:** `python3 -m py_compile bin/dw`; `tests/dw-cli.sh` (fixture
  roadmap in a temp dir; JSON assertions via python3).
- **Integration / Cypress:** `bin/dw state --root ~/dev/tools/HoldSpeak`
  spot-checks recorded in evidence.
- **Manual / device:** n/a.

## Notes / open questions

- The prefix is inferred from the majority of story IDs in the project;
  projects with no stories get `null`.
- "Where we are" is included raw (the Belt renders it as the phase's voice);
  it is the one prose field in the contract, clearly labeled prose.
