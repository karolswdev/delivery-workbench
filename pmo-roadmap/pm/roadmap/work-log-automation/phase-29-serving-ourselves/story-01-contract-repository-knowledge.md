# WLA-29-01 - Contract repository knowledge

- **Project:** work-log-automation
- **Phase:** 29
- **Status:** ready
- **Depends on:** -
- **Unblocks:** WLA-29-02, WLA-29-03, WLA-29-04, WLA-29-05, WLA-29-07
- **Owner:** unassigned

## Problem

Every agent Delivery Workbench dispatches pays the full localization tax:
nothing the engine hands an agent says where anything is, what tests cover
it, or what previous deliveries learned. The comparative study (autodev-studio,
2026-07-26) showed the antidote is persistent repository knowledge — but that
codebase also showed the failure mode: an untyped file store with no locking,
no provenance, no versioning, and LLM prose mixed freely with static fact.

Before any extraction, retrieval, or write-back exists, the code has to say
what repository knowledge *is*, where it lives, which parts are disposable,
and — because this project's spine demands it — that none of it is authority.
Phase 28 proved this order works: the contract lands before anything reuses a
fact, so every later story is mechanical against a stated rule instead of a
guess.

## Scope

- **In:** one versioned contract, `delivery-workbench-repository-knowledge@1`,
  in a new `dw_pmo/knowledge.py` (or a small package if the split is cleaner);
  the storage split into **derived facts** (re-derivable from the working
  tree, disposable, cached under `.git/pmo-knowledge/derived/`) and **earned
  records** (delivery records and lessons, append-only and provenance-stamped
  under `.git/pmo-knowledge/earned/`); the freshness rule binding derived
  facts to the phase-28 repofacts index tree; typed record shapes with
  per-field caps for earned records, in the signals content-boundary style;
  the authority exclusion stated in code and prose; fitness tests keeping the
  knowledge core deterministic, stdlib-only, and offline, and keeping
  gate/grant/verdict paths free of knowledge reads.
- **Out:** extracting anything (WLA-29-02); retrieval or packets (WLA-29-04);
  write-back (WLA-29-07); tracking earned knowledge in the repository rather
  than `.git` (deferred, recorded in the phase status); any schema for
  LLM-interpreted repository views — agent-authored content only ever arrives
  through the typed earned-record shapes.

## Acceptance criteria

- [ ] The contract document exists alongside the other machine contracts,
  names the two storage classes, and states per class: location, mutability,
  provenance requirements, and what deleting it may change (derived: nothing
  but latency; earned: history is lost, no authoritative answer changes).
- [ ] The freshness rule is expressed in code, not only prose: a derived fact
  carries the index tree it was computed from, and a reader must refuse or
  recompute when the current derivation's index tree differs.
- [ ] Earned-record shapes are typed with closed field sets and per-field
  length caps, and every record carries its provenance (run id or operator,
  timestamp, head SHA).
- [ ] The authority exclusion is test-enforced: no module under the gate,
  grant, contract, or verdict paths imports or reads knowledge stores, and
  the knowledge core imports no subprocess-spawning authority surface.
- [ ] A fitness test fails if the knowledge core imports network, non-stdlib,
  or nondeterministic-time modules, in the style of the existing architecture
  fitness tests.
- [ ] The contract changes no observable behavior: the full core suite passes
  unchanged.

## Test plan

- **Unit:** storage-class classification is total; freshness refusal fires on
  a mismatched index tree; earned-record caps and provenance are enforced on
  append.
- **Integration:** full core suite green with the contract module present and
  nothing calling it yet; planted knowledge read inside a gate path is
  rejected by the fitness test.
- **Manual:** read the contract and confirm each later story in this phase
  names which class it touches.

## Notes / open questions

The studied prototype kept lessons and deliveries safe across knowledge
rebuilds by segregating them in the store — the same split this contract
makes structural. Its missing locking and versioning are answered here by
append-only earned records and index-tree-keyed derived facts rather than by
adding a lock protocol.

Whether `.git/pmo-knowledge/` should ever become repository-tracked is
deliberately deferred; the contract only promises that moving it later cannot
change any authoritative answer, because knowledge never authorizes anything.
