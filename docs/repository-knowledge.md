# Repository knowledge contract

**Contract:** `delivery-workbench-repository-knowledge@1`

Repository knowledge lowers the cost of finding relevant code, tests, and past
lessons. It is advisory context. It is not a source of permission or proof.

## Authority exclusion

Knowledge may inform; it may never authorize. No derived fact, delivery record,
lesson, packet, or grounding result can mint authority, satisfy a gate rule,
change a grant or verdict, or substitute for captured evidence. Deleting every
knowledge file changes no authoritative answer.

The stored documents carry explicit false authority markers. Architecture
fitness tests also keep gate, contract, grant, and verdict modules from
importing this module or reading its stores.

## Storage classes

| Class | Location | Mutability | Required provenance | What deletion changes |
|---|---|---|---|---|
| **Derived facts** | `.git/pmo-knowledge/derived/` | Disposable cache. A fact may be replaced by a new derivation. | The phase-28 repofacts index tree used to compute it. | Latency only. The working tree can reproduce every fact. |
| **Earned records** | `.git/pmo-knowledge/earned/` | Append-only, hash-chained JSONL. Existing records are never rewritten. | Origin kind (`run` or `operator`), origin identifier, ISO-8601 UTC timestamp, and full HEAD SHA. | Delivery history and lessons are lost. No authoritative answer changes. |

The split is structural in `dw_pmo.knowledge`: `derived-fact` belongs to the
derived class; `delivery-record` and `lesson` belong to the earned class.
Unknown item kinds are refused rather than assigned a default class.

## Derived-fact freshness

Every derived document carries `index_tree`, the Git index tree from the
`delivery-workbench-repository-facts@1` boundary. A read must supply the current
index tree. `DerivedFactStore.read` refuses a mismatch with the typed
`StaleDerivedFact` refusal. `DerivedFactStore.read_or_recompute` is the explicit
alternative: it computes and stores a replacement under the current index tree.
A missing cache follows the same explicit recompute path.

Derived identity contains no timestamp, random value, network result, or other
ambient input. The value must be deterministic JSON (objects, arrays, strings,
integers, booleans, and null; floats and arbitrary Python objects are refused).
Deleting `.git/pmo-knowledge/derived/` therefore changes only whether the next
read has to recompute.

`DerivedFactStore.refresh` is the incremental variant of that explicit path. It
may expose a validated previous document only to the recomputation callback; it
never returns that document as an answer. The replacement is written under the
current tree after computation succeeds.

## Symbol and structure map

The `symbol-structure-map` derived fact is produced in two layers. The pure
`dw_pmo.symbol_map` extractor uses only `ast` and supplied blob bytes. The
Git-facing `dw_pmo.repository_map` layer obtains the index tree, tracked
path/blob/size inventory, and changed blob bytes through `dw_pmo.repofacts`,
then stores the model through `DerivedFactStore`. It never reads Python source
from the working tree.

Every tracked `.py` path has a module record. Parsed modules inventory imports
and module, class, function, and method symbols with qualified names and line
spans. An unparseable Python path remains a named `unparseable-python` gap.
Every other tracked path remains a named `non-python` gap. Both gap kinds state
`out of structural coverage; use git grep` rather than implying coverage the
extractor does not provide.

Refresh reuses a module extraction only when both its tracked path and blob id
match the previous map. Added or changed Python blobs are parsed; deleted paths
disappear; unchanged Python blobs are not read or parsed. The complete test map
is then resolved again from the cached lexical references, so a changed symbol
inventory cannot leave unchanged tests linked to an old answer.

The static test-resolution rule is deliberately conservative: a test file is
linked to every symbol whose exact terminal name appears there as an `ast.Name`,
`ast.Attribute`, or imported name. If several qualified symbols share that
terminal name, all matches remain. Symbols defined in that same test file are
excluded. Import-alias targets and runtime/data-flow behavior are not inferred;
use `git grep` or real test evidence when that distinction matters.

`dw knowledge map` and MCP `dw_knowledge_map` only read a fresh stored map and
refuse missing or stale facts. `dw knowledge refresh` is the explicit disposable
cache refresh. These surfaces start no work, mint no authority, and change no
tracked or authoritative repository state.

## Story grounding

A story may carry this optional advisory section:

```markdown
## Localization hints

- **Affected files:**
  - `path/to/existing.py`
  - `path/to/planned.py` (new)
- **Target symbols:**
  - `terminal_or.qualified_name`
  - `planned_symbol` (new)
```

Each hint is one nested list item. File hints use exact repository-relative
tracked paths. Symbol hints use an exact terminal or qualified symbol name.
Grounding checks the fresh symbol map first. For files outside structural
coverage, it performs the `git grep` equivalent in pure code over the tracked
blob bytes already exposed by `repofacts`; it does not add another private Git
spawn or repository fact. The declaring story is excluded so a hint does not
match its own declaration. Fallback output and bytes are bounded, and the result
records the exclusion plus any skipped files or truncation.

`(new)` is the only newness rule. It is a claim that an absent file or symbol is
planned, not a shortcut around verification. An existing marked hint is
verified and warned as contradictory. An absent marked symbol is **new** only
when both the map and a complete fallback scan record no match. An absent
unmarked hint, a textual fallback match, or any scan that cannot complete is
**unknown**. Thus every new classification carries explicit complete no-match
evidence; grounding never infers newness merely because a name was not found.
Unknown hints carry at most three deterministic name-distance suggestions.
Verified hints carry their repository path and line span.

`dw knowledge ground <project> <story>` and MCP `dw_knowledge_ground` are
read-only and refuse a missing or stale map. `dw check` renders unknown hints,
contradictory new markers, malformed hint syntax, and acceptance-criteria code
identifiers as greppable `WARNING` lines. Such findings never change its exit
code. A program plan adds grounding only for a selected story that actually has
hints; a story without hints retains the previous plan shape byte for byte.

## Agent knowledge packets

`dw_pmo.knowledge_packet.build_knowledge_packet` turns one already-read story,
fresh symbol map, grounding result, indexed blob snapshot, and earned-record
snapshot into `delivery-workbench-knowledge-packet@1`. The pure builder performs
no Git, filesystem, clock, network, or authority read. Repository-facing packet
assembly reads those inputs first, then calls the pure boundary.

A packet contains only WLA-29-03-verified locations as fact. Source snippets use
the symbol map's complete line spans, so a budget decision keeps or drops a
whole symbol; it never cuts a symbol in half. Static test-map references and
lexically relevant lesson records ride as separate items. Unknown hints may be
shown only under `unverified_hints`, with the explicit `unverified` label. A
story with no localization hints receives an explicit `hint-free` packet and no
guessed location.

Selection uses deterministic lexical overlap with lexical-name tie-breaking.
The default byte budget is 32,768 bytes and callers may declare a different
budget. If the canonical packet would exceed that budget, assembly drops the
lowest-scored whole item and records its stable name, kind, score, and
`byte-budget` reason under `exclusions`. If even the empty packet and complete
exclusion audit cannot fit, assembly refuses rather than silently omitting the
audit.

Grounding and the symbol map must name the same current repofacts index tree.
A mismatch raises the typed `StaleKnowledgePacket` refusal; a refused grounding
raises `KnowledgePacketRefusal`. Driver packet assembly surfaces either through
its existing packet-assembly failure path. It never substitutes an empty
knowledge section. Both bounded-run and program work packets carry the
knowledge document as a top-level, hash-bound section. Legacy packets without
the section remain replayable.

## Honest usage telemetry

Every new driver receipt carries a closed `usage` object. A backend that reports
nothing records `status: unknown` and null token and money measurements. A
backend that explicitly reports zero records `status: reported` and numeric
zero. Program receipts bind that usage through the action receipt referenced by
the ledger; bounded-run ledger receipt events carry scalar usage status, total
tokens, and cost, spelling an absent measurement as `unknown` rather than `0`.
Live progress, bounded-action projections, and workbench API responses preserve
null as unknown and render an honest unknown label.

## Earned-record boundary

Earned records are scalar-only typed shapes with exact field sets:

| Kind | Exact detail fields | Per-field caps |
|---|---|---|
| `delivery-record` | `story_id`, `outcome`, `summary`, `evidence_ref` | 64, 32, 500, 500 characters respectively |
| `lesson` | `subject`, `lesson`, `supersedes` | 200, 1,000, 80 characters respectively |

`supersedes` is either empty or an earned-record `sha256:` hash reference. It
expresses correction without rewriting history.

Every append validates the exact fields, scalar types, caps, provenance, and
Git object identifiers before writing. Every read repeats those validations and
also verifies sequence, previous-hash linkage, record hash, and nondecreasing
provenance timestamps. A malformed, truncated, rewritten, reordered, or
content-expanded chain refuses closed. The store exposes append and read
primitives only; it has no update, replace, or delete API. Real delivery
write-back remains the responsibility of WLA-29-07.

## Runtime boundary

The knowledge core is standard-library-only and offline. It does not import a
network client, subprocess, LLM SDK, gate, grant, contract, or verdict surface.
It resolves `.git` through the repository-facts boundary rather than privately.
Wall-clock time is permitted only for earned-record provenance and never enters
a derived fact's value, identity, or freshness decision.
