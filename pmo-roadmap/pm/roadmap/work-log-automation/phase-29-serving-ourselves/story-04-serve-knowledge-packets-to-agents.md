# WLA-29-04 - Serve knowledge packets to agents

- **Project:** work-log-automation
- **Phase:** 29
- **Status:** done
- **Depends on:** WLA-29-02, WLA-29-03
- **Unblocks:** WLA-29-08
- **Owner:** unassigned

## Problem

The driver seam already hands agents bounded, hash-bound packets — but those
packets carry the work order, not the repository. Every dispatched agent
starts by rediscovering where things live, which is the localization tax this
phase exists to cut. The map (WLA-29-02) and grounding (WLA-29-03) produce
exactly what an implementer needs on arrival: verified locations, the code at
those locations, the tests that watch them, and — once WLA-29-07 lands —
what previous deliveries learned nearby.

Retrieval must fit the house floor: deterministic lexical scoring, no
embeddings, no network, and a hard size budget, because an unbounded context
channel is how packet hashing and content boundaries rot.

## Scope

- **In:** a pure knowledge-packet builder: given a story's criteria and
  grounded hints, select verified locations, bounded source snippets around
  them, the mapped tests, and (when the earned store exists) the most
  relevant lessons, under an explicit byte budget with a deterministic
  lexical relevance score and stable tie-breaking; inclusion of the packet in
  the existing agent-packet assembly for both bounded runs and programs,
  hash-bound like every other packet section, with the packet recording what
  was *excluded* by budget (named, not silent); an honest-telemetry pass over
  driver receipts: usage a backend does not report is recorded and rendered
  as unknown, never zero, across receipts, ledgers, and every surface that
  shows cost.
- **Out:** embeddings or model-scored retrieval (deferred, recorded in the
  phase status); packets for agents outside the driver seam; letting a packet
  grow past its budget for any reason; lesson *writing* (WLA-29-07); changing
  packet hashing or content-boundary semantics — the knowledge section rides
  the existing rules.

## Localization hints

- **Affected files:**
  - `pmo-roadmap/lib/dw_pmo/knowledge.py`
  - `pmo-roadmap/lib/dw_pmo/repository_map.py`
  - `pmo-roadmap/lib/dw_pmo/orchestration_driver.py`
  - `pmo-roadmap/lib/dw_pmo/knowledge_packet.py` (new)
- **Target symbols:**
  - `DerivedFactStore`
  - `EarnedRecordStore`
  - `build_knowledge_packet` (new)

## Acceptance criteria

- [ ] The packet builder is pure and deterministic: same story, same index
  tree, same earned store → byte-identical packet; it lives in the knowledge
  core and imports no authority surface.
- [ ] Packets respect a declared byte budget, degrade by dropping
  lowest-scored items whole (never truncating a snippet mid-symbol), and name
  every dropped item with its score so exclusion is auditable.
- [ ] A dispatched program agent's packet for a grounded story contains the
  verified locations, snippets, and test references; an ungrounded or
  hint-free story yields a packet that says so honestly rather than guessing.
- [ ] A stale map or stale grounding refuses packet assembly per the
  freshness rule; the dispatch path surfaces that refusal as the existing
  packet-assembly failure, not as an empty packet.
- [ ] Driver receipts distinguish unknown usage from zero usage end to end:
  a fixture backend reporting nothing produces unknown in the receipt, the
  ledger, and the rendered cost surfaces, proven by test.
- [ ] Packet hashing, replay, and content-boundary tests pass unchanged with
  the new section present.

## Test plan

- **Unit:** relevance scoring determinism and tie-breaking; budget
  degradation order; whole-item dropping; unknown-vs-zero usage modeling.
- **Integration:** `dw evidence capture` of a program plan + dispatch against
  a fixture adapter in this repository showing the knowledge section in the
  packet and the exclusion list; replay of an existing recorded run proving
  ledger compatibility.
- **Manual:** read one generated packet for a real phase-29 story and judge
  whether an implementer landing cold would start in the right file.

## Notes / open questions

The studied prototype pins retrieved context and also *verifies* the model's
claimed locations before trusting them; our equivalent is that only
WLA-29-03-verified locations enter the packet as fact — hints that grounded
as unknown may appear only labeled as unverified.

The right default budget is unknown until WLA-29-08 runs for real; ship a
conservative default and record the observed fit in the run's friction notes.

Implemented as `dw_pmo/knowledge_packet.py` (`build_knowledge_packet`),
wired hash-bound into bounded-run and program packet assembly with legacy
replay compatibility. Default budget 32,768 bytes — far under the 262,144
context and 1,500,000 packet ceilings; WLA-29-08 validates the fit.
Refusals are typed (`KnowledgePacketRefusal`, `StaleKnowledgePacket`) and
surface through the existing assembly failure path. Honest telemetry:
absent usage renders unknown (never zero) across driver receipts, run and
program ledgers, live progress, bounded actions, and workbench
projections; explicit zeros stay numeric. One live observation recorded:
the repository's stored symbol map was stale at delivery time and the
packet path refused until an explicit `dw knowledge refresh` — the
freshness rule working as contracted. Suite 573 → 581 green on both
interpreters; all prior phase-29 test modules unchanged and green.
