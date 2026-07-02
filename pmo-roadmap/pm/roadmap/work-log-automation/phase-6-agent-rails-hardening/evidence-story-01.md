# Evidence - WLA-6-01 - Restore dogfood integrity and land the working tree through the rails

- **Story:** [story-01-dogfood-integrity](./story-01-dogfood-integrity.md)
- **Status:** done
- **Date:** 2026-07-02

## Proof summary

- The framework now enforces itself on this repository: `core.hooksPath`
  is `.githooks`, the hooks/helpers are installed and committed, work
  logging is enabled with per-commit consent, and every landing commit
  below passed the pre-commit gate with a fresh `.tmp/CONTRACT.md`.
- The previously uncommitted phase 0-5 proof layer (19 evidence files,
  4 final summaries, phases 4-6, `bin/dw`, its tests, CI updates) is
  fully landed; `git status --porcelain` is empty.
- All 8 work-log entries cryptographically match their commits
  (`index_tree` equals `git rev-parse <sha>^{tree}` for every entry).
- The full traceability chain resolves (WLA-0-01 shown below):
  README -> phase status -> story -> evidence -> commit -> work-log entry.

## Landing sequence (all gated, consented, and logged)

| Commit | Content | Flips | Bundle rationale |
|---|---|---|---|
| 690dcec | Rails install (.githooks incl. config + self-host pre-commit.local), dw CLI, work-log-summarize fallback, install/update dw distribution, roadmap-cli tests, CI dw-check step, gitignore pycache fix | 0 | n/a |
| df1221e | Phase 0 architecture: WLA-0-01..06 done + evidence + status + final summary | 6 | Retroactive landing of an already-shipped phase; per-story commits would fabricate sequence |
| e181a33 | Phase 1 MVP: WLA-1-01..06 done + evidence + status + final summary | 6 | Same retroactive-landing rationale |
| 79edd6c | Phase 2 hardening: WLA-2-01..03 done + evidence + status + final summary | 3 | Same |
| a447f26 | Phase 3 rollout: WLA-3-01..03 done + evidence + status + final summary | 3 | Same |
| e73a376 | Phase 4 CLI tools: WLA-4-01..03 done + evidence + completion audit + final summary | 3 | Same (dw CLI itself landed in 690dcec) |
| 6ed9122 | Phase 5 planning: WLA-5-01 done + evidence, WLA-5-02..10 planned, implementation plan | 1 | none needed (single flip) |
| 565a106 | Phase 6 Agent Rails Hardening plan: 8 stories + phase status + roadmap README | 0 | n/a |

BUNDLE-OK.md rationales are reproduced above verbatim because the hook
destroys the file on success (a WLA-6-03 driver: the audit trail should
survive the gate).

## Command output

Gate banner for the phase-0 landing (representative; every landing
commit produced the equivalent):

```text
✓ The system accepted your understanding of the project management framework.
  Contract acknowledged (7/7 checkboxes).
  Self-host roadmap checks passed (6 story flip(s), evidence verified).
  Work log payload captured for post-commit finalization.
  Commit proceeding.
pmo-roadmap post-commit: work log appended to /Users/karol/.work/log/2026-07-02/work-log-automation-3749607007-work-summary.log
```

Validation before the sequence (2026-07-02, exit 0, output read):

```text
bash -n <12 shipped scripts>            -> ok
python3 -m py_compile pmo-roadmap/bin/dw -> ok
pmo-roadmap/tests/adoption-discovery.sh  -> adoption-discovery.sh: ok
pmo-roadmap/tests/roadmap-cli.sh         -> roadmap-cli.sh: ok
pmo-roadmap/tests/work-log-mvp.sh        -> work-log-mvp.sh: ok
```

Post-landing state:

```text
$ git config core.hooksPath
.githooks
$ git status --porcelain
(empty)
$ pmo-roadmap/bin/dw check work-log-automation
dw check: ok            (exit 0)
```

Work-log integrity cross-check — every entry's `index_tree` verified
against the real commit tree:

```text
$ grep -c '^kind: pmo-work-log-entry' ~/.work/log/2026-07-02/work-log-automation-3749607007-work-summary.log
8
OK  690dcec18e20487fe2714a5a1bcc5ddc7248ecda tree=059f0cfc089efbbaf621f9d95ec414aee2f87bbb
OK  df1221ea0b5109b1eaef16d3533fadad36fc526e tree=129522c181283c344f9513c1f09f5bd065e16c83
OK  e181a33b0a8dcbac05856104d1da5b190bfd8db1 tree=22f918adaf2abea9e171471b7c55b1507bf53bb6
OK  79edd6cbef505c06a40a3a94ab491492ebdc8b79 tree=c16cf38a0c25fcd5fbcf31f074a1518ce87b574f
OK  a447f26d9a13b54766e5d4fafaec3e3c4a84ac35 tree=28f937f1487ebe3b502c7100fcd19bbdfd7baf53
OK  e73a3766d87c4879bf97d203bf6f4e848a7e8ce4 tree=0f2128b49047e199e552876bbffb28a5c10f2d49
OK  6ed9122f772aaf23bfc2a96645200bb9f5abf150 tree=aa748d5ead56fddafd86cccc0956cbc1e87e4d51
OK  565a1063b12dee24725d5136fe90a0c0806ca065 tree=70d5267c052f9172eace0b0ae33a78d5620e4221
```

Traceability chain via `dw context work-log-automation --trace` for
WLA-0-01 (abridged):

```json
{
 "story_id": "WLA-0-01",
 "status": "done",
 "evidence_exists": true,
 "recent_commits": [
  {"sha": "df1221ea...", "subject": "Land phase 0 architecture proof layer through the PMO gate"},
  {"sha": "4b38e085...", "subject": "Initial delivery-workbench framework"}
 ],
 "work_log_entries": [
  {"commit": "690dcec1...", "path": "/Users/karol/.work/log/2026-07-02/work-log-automation-3749607007-work-summary.log",
   "timestamp": "2026-07-02T13:11:20Z"}
 ]
}
```

CI: `.github/workflows/validation.yml` now contains the
"Roadmap self-validation (dogfood)" step running
`pmo-roadmap/bin/dw check work-log-automation`; the same command exits 0
locally (above). Green-in-Actions is demonstrated on next push to
`origin` (not pushed as part of this story's execution).

## Friction log (recorded, not fixed inline — per story notes)

1. **install.sh cannot self-host** (WLA-6-07): running it against this
   repo would create a root `pm/roadmap/` (methodology copies) that
   shadows `pmo-roadmap/pm/roadmap/` and breaks `dw` root discovery.
   The install was performed by manually mirroring its hook/helper
   distribution steps.
2. **Canonical gate is blind to the nested roadmap** (WLA-6-02): the
   hook's `STORY_REGEX`/`EVIDENCE_REGEX` are anchored at `^pm/roadmap/`,
   so atomicity and evidence pairing had to be duplicated line-for-line
   in `.githooks/pre-commit.local` for the `pmo-roadmap/pm/roadmap/`
   prefix — a fourth copy of gate logic, existing only because the gate
   is not single-sourced and takes no roadmap-root parameter.
3. **post-commit evidence extraction is likewise anchored** (WLA-6-02):
   every landing entry's "Verification And Evidence" section says "n/a"
   despite dozens of staged story/evidence files, because the awk regex
   only matches `^pm/roadmap/`.
4. **Hook banner points at a nonexistent path** (WLA-6-02/06): failure
   output references `pm/roadmap/PMO-CONTRACT.md`, which does not exist
   in the self-hosted layout (`pmo-roadmap/templates/PMO-CONTRACT.md`).
5. **README same-commit cadence is impossible for retro-landing**
   (WLA-6-06): the roadmap README was one working-tree blob mixing
   2026-07-01 and 2026-07-02 edits; it landed with 565a106 instead of
   incrementally per commit. Recorded as a deviation in each contract.
6. **BUNDLE-OK rationale is destroyed on success** (WLA-6-03): the hook
   deletes it unread; rationales survive only because this evidence file
   duplicates them.
7. **`PMO-Story:` did not parse as a git trailer** (WLA-6-03): in
   commits 690dcec..565a106 a blank line separates it from the
   `Co-Authored-By:` trailer block, so `%(trailers:key=PMO-Story)`
   returns empty — the ID is greppable body text only. Discovered after
   landing; rewriting would dangle the work-log entries' recorded SHAs,
   so the defect stands as evidence. This story's own commit formats the
   trailer block correctly. Mechanical trailer emission is a WLA-6-03
   deliverable.
8. **dw work-log correlation is per-file, not per-entry** (WLA-6-02/05):
   `parse_work_log_entry` reads the whole daily log and returns the
   first `commit:` line, so WLA-0-01's trace cites 690dcec rather than
   its actual landing commit df1221e.
9. **Evidence backfill remains visible** (WLA-6-04): phases 0-5
   evidence is dated 2026-07-01, authored months after the underlying
   work, with the known weak specimens (phase-3 pilot unreproducible,
   phase-5 planning evidence thin) — the exact gap `dw evidence capture`
   closes.

## Acceptance criteria check

- [x] `git config core.hooksPath` returns `.githooks`; hooks/helpers
  present and committed (690dcec).
- [x] `git status --porcelain` empty after the landing sequence.
- [x] Every landing commit passed the gate with a fresh contract;
  8 consented work-log entries in
  `~/.work/log/2026-07-02/work-log-automation-3749607007-work-summary.log`
  cite the SHAs above.
- [x] WLA-0-01 resolves README -> phase status -> story -> evidence ->
  commit -> work-log entry via `dw context --trace` (output above).
- [x] `validation.yml` runs `dw check work-log-automation`; command
  exits 0 locally; Actions run pending next push.
- [x] This evidence records the commit-by-commit landing plan and every
  BUNDLE-OK rationale used.
