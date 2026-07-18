# WLA-24-02 - Compile and validate exact orchestration rules

- **Project:** work-log-automation
- **Phase:** 24
- **Status:** backlog
- **Depends on:** WLA-24-01
- **Unblocks:** WLA-24-03, WLA-24-04, WLA-24-05
- **Owner:** unassigned

## Problem

Neither the editor nor runtime can own orchestration semantics. One stdlib
core must parse, normalize, validate, hash, and simulate the exact score so a
graph means the same thing over CLI, browser, MCP, HTTP, and a packaged repo.

## Scope

- **In:** `dw_pmo.orchestration`; schema-v1 exact keys; contained discovery
  under `pm/orchestration`; node/input/output/check/failure/budget models;
  canonical hash; graph/type/capability/path/bound validation; normalized
  compiled model and deterministic dry scheduling trace; CLI list/show/
  validate/simulate; source/vendored/package parity; presets as ordinary
  score files.
- **Out:** browser editor, grants/runtime state, actual checks or agents,
  provider config, certification/commit.

## Acceptance criteria

- [ ] Valid representative and minimal scores compile to exact-key, stamped,
  canonical documents and stable hashes on Python 3.9; key/order-only JSON
  changes do not change semantics or hash.
- [ ] Red fixtures refuse duplicate/missing ids, dangling refs, success cycles,
  unbounded retries/visits/time/concurrency/output, multiple producers,
  incompatible artifact types, unsafe selectors/paths, shell strings,
  undeclared executable behavior, and impossible capabilities with JSON
  pointers plus remediation.
- [ ] Built-in agent role presets include research/synthesis/implementation/
  review/verification/documentation/repair without hard-coding capability;
  custom roles round-trip.
- [ ] Simulation deterministically reports eligibility waves, fan-out/fan-in,
  locks, capabilities, output lineage, checkpoints, failure branches, budgets,
  and terminal meanings without starting work or writing events.
- [ ] CLI JSON/human output, installed package, docs/interop inventory, full
  core tests on both Python floors, and update parity are green with evidence.

## Test plan

- **Unit:** exhaustive schema, graph, path, capability, artifact, check,
  failure, budget, normalization, hash, purity, and simulation matrix.
- **Integration:** fixture score discovery/CLI; package import and installed
  invocation; score save containment remains absent until WLA-24-03.
- **Manual / device:** inspect compiler diagnostics for a deliberately broken
  research fan-in score; every error names the graph element and repair.

## Notes / open questions

Canonical semantic hashing excludes editor-only layout metadata but includes
every runtime rule. The compiler must expose both hashes/sections explicitly
so lossless visual layout cannot become hidden execution policy.
