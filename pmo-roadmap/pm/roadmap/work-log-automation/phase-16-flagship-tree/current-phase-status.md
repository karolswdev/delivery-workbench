# Phase 16 - The flagship tree — receipts-first reading

**Last updated:** 2026-07-07.

## Goal

Reading a decade-shaped legacy roadmap (HoldSpeak: 86 phases, drifted table dialects, decorated statuses) must be honest: the read layer parses header-mapped tables, normalizes status decoration, pairs evidence against on-disk receipts, and honors the README current-phase pointer — while the write gate stays exactly as strict as today.

## Scope

- **In:** The READ layer only — `parse.py` (header-mapped table
  detection, column mapping, decoration-tolerant status
  normalization in `model.py`), `validate.py` (receipts-first
  evidence pairing, retired-row semantics, prose evidence cells
  accepted when the receipt file exists), `statefeed.py` /
  `api.py` (README current-phase pointer precedence, next-story
  skipping closed phases, file-derived stories where a table is
  absent), the read-only consumers that key on raw statuses
  (`workbench.py` counts, `sessions.py` correlation), tests in
  `dw-core-tests.py` including a fixture distilled from the
  flagship consumer's real dialects, and a documented before/after
  run against HoldSpeak's tree.
- **Out:** ANY write-path change — `mutations.py`, `gate.py`,
  `verify.py`, `contract.py` keep their exact strict vocabulary
  (`STORY_STATUSES`) and diff rules; the feed schema number
  (coverage grows, shape does not change); rewriting any consumer
  repo's history to fit the parser.

## Exit criteria (evidence required)

- [ ] A story table with the canonical 5-column header parses
  byte-identically to today (existing `dw-core-tests.py` fixtures
  pass unmodified), and a 4-column header-mapped variant with
  decorated statuses parses to the same rows (WLA-16-01).
- [ ] `dw check` on a fixture carrying the flagship dialects
  (decorated statuses, prose evidence cells with receipts on disk,
  struck-through retired rows, a table-less phase with story
  files) reports only the planted real desyncs (WLA-16-02).
- [ ] `dw state --json` on a project whose README pointer names a
  closed phase reports that phase as `current_phase`, and
  `dw next` never proposes a story from a phase with a
  `final-summary.md` (WLA-16-03).
- [ ] The before/after against HoldSpeak's real tree is recorded in
  evidence: error count, current-phase identity, and story
  coverage (phases no longer reading 0/0) — with every remaining
  error a real desync in that repo, named (WLA-16-04).

## Story status

| ID | Story | Status | Story file | Evidence |
|---|---|---|---|---|
| WLA-16-01 | Header-mapped story tables + status normalization | backlog | [story-01-header-mapped-tables](./story-01-header-mapped-tables.md) | - |
| WLA-16-02 | Receipts-first evidence pairing + retired rows + file-derived stories | backlog | [story-02-receipts-first-pairing](./story-02-receipts-first-pairing.md) | - |
| WLA-16-03 | The README pointer drives current phase; next-story skips closed phases | backlog | [story-03-pointer-current-phase](./story-03-pointer-current-phase.md) | - |
| WLA-16-04 | The flagship dogfood: HoldSpeak's real tree, before/after | backlog | [story-04-flagship-dogfood](./story-04-flagship-dogfood.md) | - |

## Where we are

Phase scaffolded and story breakdown written 2026-07-07, from the
flagship consumer's dogfood: `dw check` on HoldSpeak reported 397
errors, most of them the reader going blind on legacy dialects (a
4-column story table parses to zero rows, so phase 85 reads 0/0 and
its evidence files count as orphans; `**done** (2026-07-07 — …)`
never equals `done`; the state feed picks phase 17 of 86 as
current). Next: WLA-16-01.

## Active risks

| Risk | Likelihood | Mitigation | Stop signal |
|---|---|---|---|
| Normalization maps a deliberately-not-done status (e.g. `host-complete`) into done | medium | keyword matching with token boundaries, never substring containment; the fixture pins `host-complete` staying un-done | any fixture showing a non-done decoration classified done |
| Read-layer loosening leaks into the gate (strict vocabulary weakens) | low | gate/verify/mutations excluded from the diff; `gate-parity.sh` + existing gate tests must pass untouched | any gate test edit in this phase's diffs |
| Feed consumers (Desk conveyor, Telegram, HoldSpeak packs) see a shape change | low | `FEED_SCHEMA` stays 1; shape-pinning tests unmodified; only coverage grows | a feed test needing a shape edit |

## Decisions made (this phase)

- 2026-07-07 - Phase scaffolded with `dw phase create` - keeps roadmap structure consistent - CLI.
- 2026-07-07 - Tolerance lives in the READ layer only; the write gate keeps the strict single vocabulary - the gate's strictness is what makes new trees clean; the reader's tolerance is what makes old trees legible - owner direction via the Delivery Belt RFC (HoldSpeak candidate U).
- 2026-07-07 - Status normalization is keyword-at-token-boundary, longest-first, never substring containment - `host-complete` must not read as `complete` - dogfood finding.

## Decisions deferred

- Whether `dw verify` (range audit) should learn the same normalization for auditing legacy history - trigger: a consumer actually running `dw verify --all` over a pre-workbench history - default: no change.
- A `cut` status in the write vocabulary (today: delete the row or strike it) - trigger: a consumer asking to cut a story through the CLI - default: read-side recognition only.
