# DW-0-02 — `dw cadence check`: the desync linter

- **Project:** delivery-belt
- **Phase:** 0
- **Status:** backlog
- **Depends on:** DW-0-01
- **Unblocks:** DW-0-04
- **Owner:** unassigned

## Problem

The operating cadence requires up to six surfaces to agree per shipping
commit, and today nothing checks that they do — desyncs are found by the
next reader. The linter turns the cadence from discipline into a check:
"the surfaces disagree HERE" instead of prose archaeology.

## Scope

- **In:** `dw cadence check [--project <slug>] [--root <path>]` consuming
  the DW-0-01 state; finding codes (below); human-readable one-line-per-
  finding output (`CODE path — message`) + `--json`; exit 1 on any error-
  level finding, 0 otherwise; the shared status normalizer (keyword
  containment over equality: "CLOSED ✅ (7/7)" → done, "shipped" → done,
  "planning" → scaffolded, "not-started" → backlog, "cancelled"/"cut" →
  cut, "paused" → blocked).
- **Out:** auto-fixing (verbs are DW-0-03); checking prose quality; git/CI
  state; gating commits (the hook stays independent).

## Finding codes

| Code | Level | Meaning |
|---|---|---|
| E-STORY-TABLE | error | story header status ≠ its status-table row (normalized) |
| E-EVIDENCE-MISSING | error | story done but `evidence-story-{n}.md` absent |
| E-EVIDENCE-ORPHAN | error | evidence file exists but its story is not done |
| E-TABLE-GHOST | error | status-table row whose story file does not exist |
| E-STORY-UNLISTED | error | story file with no row in the status table |
| E-CLOSED-OPEN-STORY | error | phase has `final-summary.md` but a story is neither done nor cut |
| W-INDEX-MISSING | warn | phase dir with no row in the project README phase index |
| W-INDEX-STATUS | warn | README index row status disagrees with derived phase status |
| W-POINTER-STALE | warn | README current-phase pointer targets a phase with a final summary |

Errors are facts two receipts disagree on; warnings are index/pointer drift
(legacy READMEs narrate status too richly to gate on).

## Acceptance criteria

- [ ] A deliberately desynced fixture (each error code staged once) reports
      exactly the planted findings — no more, no fewer — and exits 1.
- [ ] A clean fixture (the scaffold this phase shipped) exits 0 with no
      findings.
- [ ] The normalizer maps at least: `done`, `**CLOSED (7/7)**`,
      `CLOSED ✅ (6/6)`, `shipped`, `in-progress (3/6)`, `not-started`,
      `planning`, `scaffolded`, `paused`, `cancelled` — asserted in tests.
- [ ] Run against HoldSpeak's real roadmap: completes in <5s, and every
      finding is triaged in DW-0-04's evidence (real desync fixed, or
      explained).
- [ ] `--json` emits the findings as a JSON array (the Belt's stall chips
      read this in B1).

## Test plan

- **Unit:** `tests/dw-cli.sh` sections: normalizer table, planted-desync
  fixture, clean fixture.
- **Integration / Cypress:** the HoldSpeak run (recorded in DW-0-04
  evidence).
- **Manual / device:** n/a.

## Notes / open questions

- E-CLOSED-OPEN-STORY accepts `cut`/`cancelled` as terminal because the
  methodology's final-summary template has a "Stories cut or deferred"
  section — a cut story in a closed phase is a recorded outcome, not a
  desync.
