# WLA-26-03 — Compile reusable hierarchical workflows and bounded loops

- **Project:** work-log-automation
- **Phase:** 26
- **Status:** done
  <!-- status vocabulary: roadmap-builder.md §2.3 -->
- **Depends on:** WLA-26-01, WLA-26-02
- **Unblocks:** WLA-26-05, WLA-26-06, WLA-26-09
- **Owner:** unassigned

## Problem

Real delivery organizations reuse structures larger than a flat DAG: research
cells, build/review subflows, implementer↔verifier repair cycles, architect
audits, and bounded debate rounds. Copying those nodes into every story makes
policy drift inevitable; permitting arbitrary cycles makes autonomous runtime
unsafe. The workflow language needs reusable hierarchy and loops whose
finiteness is mechanically provable.

## Scope

- **In:** tracked reusable workflow/template registry; typed parameters and
  story/program bindings; subflow references; role lanes; fan-out/fan-in;
  `repeat-until`, retry/repair, review/audit, and escalation loop primitives;
  maximum rounds/visits/starts/time/artifacts; convergence and exhaustion
  routes; normalized compile, semantic/layout hashes, simulation, provenance,
  and compatibility with v1 orchestration nodes.
- **Out:** arbitrary scripts/templates; runtime-selected graph structure;
  unbounded recursion; provider executables/secrets; browser-owned semantics.

## Acceptance criteria

- [x] Templates bind only schema-declared values and context references; text
  substitution cannot create nodes, commands, capabilities, paths, checks,
  routes, limits, or provider configuration.
- [x] Subflow references resolve to exact version/hash provenance, detect
  recursion/cycles, and produce stable namespaced node/artifact/role lineage.
- [x] Every loop declares a finite ceiling, progress/exit predicate, and
  exhaustion route; the compiler computes a finite worst-case envelope for
  rounds, agent/check starts, wall time, and artifacts.
- [x] Simulation expands hierarchy legibly, shows each green/red/repair/
  exhaustion route and loop iteration, and refuses any graph whose finiteness
  cannot be proven statically.
- [x] Existing v1 scores keep their exact semantics; migration/embedding is
  explicit and tested rather than inferred.
- [x] At least three shipped templates cover docs-only, research→build→verify,
  and architect/debate/implementation/verification organizations.

## Test plan

- **Unit:** compiler, normalization, hash, recursion, bound, binding, and
  simulation fixtures in `dw-core-tests.py`.
- **Integration:** validate/simulate the shipped templates through installed
  CLI and compare canonical output after graph↔JSON round trips.
- **Manual / device:** review nested simulation readability at desktop/mobile
  once WLA-26-06 renders it.

## Notes / open questions

The runtime may execute hierarchy without fully flattening it, but the compiler
must still prove a finite envelope and provide a stable address for every
possible attempt and artifact.

## Delivered

- Added a pure workflow registry/compiler and CLI list, validate, and simulate
  surfaces. An absent workflow directory remains a healthy empty inventory.
- Closed eleven typed node kinds, exact parameter/context/artifact bindings,
  version-and-hash-pinned subflows, stable hierarchical lineage, deterministic
  fan-out/fan-in waves, and typed forward outcome routes.
- Made loops and debates statically finite through exact predicates, ceilings,
  exhaustion routes, and a conservative envelope over node visits, starts,
  rounds, child runs, rail acts, wall time, and artifact bytes.
- Preserved Phase 24 scores as explicit bounded-run leaves, with immutable
  score provenance and budgets; no existing score is silently migrated.
- Shipped three optional templates without seeding consumer policy, and bound
  compiled workflow instances into pure program plans under intersected
  capability and budget ceilings.
