# Phase 0 — The Substrate (`dw` state + cadence verbs)

**Last updated:** 2026-07-07 (phase scaffolded).

## Goal

Give delivery-workbench a machine-readable state layer and mechanical cadence
verbs: `dw state` emits the whole roadmap tree as JSON (generated-on-read,
never a parallel truth), `dw cadence check` lints the prose surfaces into
agreement, and `dw story start|done` / `dw phase close` perform the
mechanical half of the per-commit six-file surgery. Dogfooded against
HoldSpeak's real 85-phase roadmap — the flagship consumer that forces the
substrate honest.

## Scope

- In: a single-file `bin/dw` CLI (python3 stdlib only, no third-party deps);
  the `dw state` JSON contract (v1); the cadence linter with legacy-tolerant
  status normalization; the story/phase verbs mirroring the hook's rules;
  install.sh/update.sh distribution; README documentation; a bash test
  harness in `tests/`; the HoldSpeak dogfood run recorded as evidence.
- Out: anything belt-rendering (B1+, HoldSpeak roadmap); hub routes; UI;
  `gh`/CI receipts (the hub composes those in B1); a committed `state.json`
  in consumer repos (decided: generated-on-read); self-installing the PMO
  gate on this repo; rewriting the pre-commit hook to call `dw`.

## Exit criteria (evidence required)

- [ ] `bin/dw state` run at HoldSpeak's repo root emits valid JSON covering
      all `pm/roadmap/` projects and phases (spot-checked counts match the
      tree), with no writes to the consumer repo.
- [ ] `tests/dw-cli.sh` passes: state shape, linter catching a deliberately
      desynced fixture (story↔table mismatch, missing evidence, orphan
      evidence), verb mutations, and `done`-refusal without evidence.
- [ ] `dw cadence check` run on HoldSpeak's real roadmap completes with
      findings triaged: every reported desync is either a real, fixed desync
      or explained in evidence (no false-positive left unexplained).
- [ ] This phase's own paperwork is updated via the verbs at least once
      (the proposal's exit: "this repo's phase paperwork updates via verbs").
- [ ] `install.sh` and `update.sh` place `dw` into a target's `.githooks/`
      and the package README documents the CLI + the python3 requirement.

## Story status

| ID | Story | Status | Story file | Evidence |
|---|---|---|---|---|
| DW-0-01 | `dw state` — the machine-readable roadmap state | backlog | [story-01](./story-01-dw-state.md) | — |
| DW-0-02 | `dw cadence check` — the desync linter | backlog | [story-02](./story-02-cadence-check.md) | — |
| DW-0-03 | Cadence verbs — `dw story start\|done`, `dw phase close` | backlog | [story-03](./story-03-cadence-verbs.md) | — |
| DW-0-04 | Distribution, docs, and the HoldSpeak dogfood | backlog | [story-04](./story-04-distribution-and-dogfood.md) | — |

## Where we are

Phase scaffolded 2026-07-07 from the Delivery Belt RFC (HoldSpeak candidate
U, B0 slice). Nothing implemented yet. Next: DW-0-01, the parser and JSON
contract — everything else consumes it.

## Active risks

| Risk | Likelihood | Mitigation | Stop signal |
|---|---|---|---|
| HoldSpeak's 85 phases of legacy status vocabulary ("CLOSED ✅ (6/6)", "done", "scaffolded") defeat normalization and drown the linter in noise | medium | normalize by keyword containment, not equality; dogfood early (DW-0-02 runs against HoldSpeak before the verbs are built) | >10 unexplained false positives on the HoldSpeak run |
| Verbs corrupt hand-authored prose (HoldSpeak's README "Last updated" line carries a paragraph-long parenthetical) | medium | verbs replace only the date token / status cell, never the line; tests assert surrounding prose is byte-identical | any test showing prose loss |
| python3 dependency contradicts the package's "pure bash" convention | low | hooks stay bash; `dw` is optional tooling; README states the requirement explicitly | a consumer without python3 blocked at commit time (must never happen — the hook must not require `dw`) |

## Decisions made (this phase)

- 2026-07-07 — `dw state` is generated-on-read (no `state.json` committed in
  consumer repos) — receipts stay the only truth; a cached file is a second
  truth that can go stale — proposal §5 lean, confirmed here.
- 2026-07-07 — `dw` is a single-file python3-stdlib script, not bash — it
  must parse markdown tables and emit JSON reliably for a rendering consumer
  (B1); bash 3.2 cannot do that credibly. Hooks remain pure bash; the gate
  never depends on `dw`.
- 2026-07-07 — verbs mirror the hook's rules (done requires the evidence
  file; close requires the final summary) so the CLI can never author a
  state the gate would reject.

## Decisions deferred

- Whether `hooks/pre-commit` should call `dw cadence check` when present —
  revisit after B1 proves the substrate; default: no (the gate stays
  dependency-free).
- Self-installing the framework + gate on this repo — revisit at B0 close;
  default: manual cadence.
- Where the projects registry for multi-repo belts lives — B3 question,
  recorded in the RFC.
