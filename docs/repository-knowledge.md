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
