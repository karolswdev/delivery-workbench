# WLA-24-03 - Build the rich visual orchestration editor

- **Project:** work-log-automation
- **Phase:** 24
- **Status:** done
- **Depends on:** WLA-24-02
- **Unblocks:** WLA-24-07, WLA-24-08
- **Owner:** unassigned

## Problem

An orchestration score is too consequential and interconnected to configure
as an opaque JSON exercise. Operators need to see the whole graph, exact
rules, capability expansion, output lineage, checks, and fail routes before
granting a run—and must still be able to inspect the canonical diff.

## Scope

- **In:** Workbench `#/orchestration` Design/Validate views; graph canvas;
  accessible node palette and typed edges; inspector for roles/profiles,
  prompts/context, capabilities, workspaces, inputs/outputs/conventions,
  checks, dependencies, fail routes, retries, budgets, concurrency,
  approvals, and terminals; presets/import/duplicate/delete; JSON view;
  live compiler errors, lineage/capability panel and scheduling trace;
  dedicated contained score mutation preview/diff/apply; lossless round trip;
  desktop/mobile/keyboard/a11y/static fitness coverage.
- **Out:** run grant/start/monitor; browser-owned validation; arbitrary files,
  provider credentials/executables, shell input, automatic save or execution.

## Acceptance criteria

- [x] An operator can visually author the representative parallel research→
  synthesis→implementation→check/repair→approval score without editing JSON;
  every contract field is visible and editable in the inspector.
- [x] Canvas and canonical JSON round-trip without semantic/hash drift,
  including custom roles, output schemas/conventions, failure edges, and
  layout metadata that cannot affect runtime semantics.
- [x] Compiler errors attach to nodes/ports/fields, block apply, and explain
  remediation; Validate shows normalized graph, capability inventory, output
  lineage, bounds, and deterministic scheduling/failure simulation.
- [x] Save is two-act preview→diff→apply, contained to
  `pm/orchestration/*.json`, fingerprint-stale safe, atomic/rollback protected,
  and never starts a run. Unknown JSON fields are preserved or explicitly
  refused—never silently dropped.
- [x] The UI has no generic shell field: command checks use tokenized argv;
  secrets/provider executables cannot be entered; opening/saving a score emits
  no run/agent/check event.
- [x] Firefox desktop/mobile visual coverage plus keyboard/a11y and static
  policy guards are green; generated assets/docs and installed Workbench
  exercise the editor from the shared compiler.

## Test plan

- **Unit:** score mutation containment/fingerprint/rollback; layout exclusion
  from semantic hash; API exact models.
- **Integration:** create/edit/reload/delete score, planted stale/tampered/
  invalid cases, graph↔JSON round trip, compiler parity, no-run purity.
- **Manual / device:** author the full reference score at desktop and mobile,
  inspect diff and simulation, and visually verify success/failure edges,
  warnings, focus order, and no hidden rule surface.

## Notes / open questions

The editor is the product center, but not the source of policy. It consumes
the same compiler documents used by CLI and later adapters. SVG plus vanilla
DOM is the default implementation to preserve the dependency-free package;
that choice may change only with measured accessibility/performance evidence.

Research fan-out, output lineage, checks, and red failure routes are mandatory
visual states in the first editor slice—not a later “advanced” mode.
