# Phase 32 - One workbench — Final summary

**Closed:** 2026-07-30. 8/8 stories done.

## Outcome vs exit criteria

- **Design-token layer everywhere — met.** style.css opens with a
  documented token layer (six type steps, six spacing steps, semantic
  color roles with complete light and dark values, three radii, two
  elevations); every route renders through the shared card, table,
  button, fold, and status-pill treatments, proven by the refreshed
  two-theme, two-viewport screenshot matrix (WLA-32-01).
- **Five plain destinations and a real project selector — met.** The
  shell offers Work, Plan, Delivery, Live, and Health; a multi-project
  repository stops at Choose-a-project (no silent first-project
  redirect), the choice persists across routes, reloads, and Technical
  details folds, and the language lint proves no technical contract
  term leaks into an ordinary panel (WLA-32-02, WLA-32-08).
- **The board is home and runs the project — met.** Opening the
  workbench lands on the selected project's board with needs-attention
  and one canonical next step above the lanes; create, move,
  park-with-reason, and phase pause/resume all work from the board
  through the existing preview → exact fingerprint → apply boundary;
  cross-phase drops are refused client-side with plain copy
  (WLA-32-03).
- **Rough idea to applied phase plan in the browser — met.** The Plan
  destination's five-step flow (Idea → Draft → Review → Preview →
  Apply) builds an inert setup proposal client-side, validates it
  through a read-only review adapter, and applies through the existing
  setup preview/apply routes and one-use lease; drafting writes
  nothing and grants nothing (WLA-32-04).
- **Task-shaped Program Studio — met.** Studio leads with seven
  ordered plain-language questions per docs/plan-authoring.md; graph
  and raw JSON live under Technical details with edits preserved;
  rubrics render read-only; unknown declaration fields survive
  preview and apply losslessly (WLA-32-05).
- **Consent as the headline — met.** Bounded-run and program start
  panels state allowed work, spend ceilings, expiry, stops, push
  destination, and the permanent never-allowed list before approval;
  narrowing controls can only reduce within the planned envelope;
  /api/runs/start accepts the standing_nudges and signal_channel
  fields its handler reads; the server's authority copy now states
  precisely that only a browser-confirmed program action may use
  pre-granted delivery permission (WLA-32-06).
- **One Live view with finite supervision — met.** Mission control
  lists every run and program with kind, status, canonical next step,
  and outstanding decisions; pause/revoke/cancel are visually distinct
  with consequences stated before confirmation; bounded runs gained a
  finite, preview-bound supervision contract whose single-use token
  binds action, ledger head, generation, and tick/second ceilings;
  event streams remain invalidation-only (WLA-32-07).
- **The exam — met.** The strict browser exam fails without Firefox,
  names the version (Firefox 152.0.5), and renders 304 screenshots
  (76 per viewport/theme bucket) across board home, ideation, both
  consent panels, and the eight-state Live matrix; journeys 6-13 each
  have keyboard-driven canonical next step, refusal/recovery, and
  Technical-details round trips; the new structure-aware
  workbench-language-lint.py proves leakage detection with a negative
  fixture; core suite, explorer, and accessibility suites captured
  green; `dw check` reports ok (WLA-32-08).

## What shipped beyond the criteria

- A load-hardened accessibility harness: a press_until retry helper
  for controls that race client re-renders, and 60-second default
  waits — the exam now survives a heavily loaded desk without
  weakening any assertion.
- Honest evidence of the road: several captured runs record real
  intermediate failures (stale test literals the new UI invalidated,
  two inventory guards the new supervision route tripped, and
  load-contention journey timeouts) followed by their green reruns.
- The core suite grew 692 → 697 tests across the phase; the
  product-language contract, interop surface inventory, and
  .githooks core snapshot stayed in lockstep with every change.

## Deliberately deferred

- Rubric authoring in the browser (rubrics stay readable, files stay
  the authoring surface — per the phase decision).
- SSE fan-out efficiency (shared ledger watcher) — the current
  per-subscriber adapter stayed comfortable throughout the exam.
- Hosted/multi-user deployment, authentication, and driver/credential
  management UI — out of phase scope by design.
