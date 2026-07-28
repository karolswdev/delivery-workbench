# Front-door setup proposal

**Status:** `delivery-workbench-setup-proposal@1` is the versioned contract for
front-door drafts and proposal-shaped previews.
**Product claim:** A setup proposal can describe a project, a roadmap draft,
optional tracked program policy, and local non-secret driver bindings. It has
no authority. Parsing, validating, serializing, or previewing one writes
nothing and starts nothing.

The Python contract is
[`setup_proposal.py`](../pmo-roadmap/lib/dw_pmo/setup_proposal.py). It is a pure,
standard-library-only module. Later stories may add conversation, Workbench,
terminal, MCP, and HTTP surfaces, but those surfaces must use this contract
without inventing another proposal shape.

## Three surfaces, three jobs

The front-door journey has three surfaces. Each has one job:

| Surface | Job | Authority |
|---|---|---|
| Conversation | Draft the proposal from user answers, repository facts, and labeled recommendations | None |
| Workbench | Review the draft, its provenance, unresolved questions, tracked content, and local content | None |
| Terminal | Present and apply separate exact leases when a later contract permits it | Only the authority carried by that separate lease |

Conversation output and Workbench review are inert. A transcript, proposal, or
proposal-shaped preview is not a setup lease or program grant. The terminal
must not infer consent from review activity.

## Journey states

The closed state sequence is:

```text
uninitialized -> rails-ready -> draft -> reviewed -> configured -> grant-previewed
```

`transition_state(current, target)` permits only one adjacent forward move.
`reviewed -> draft` is the sole reverse move and means that review requested a
revision. Repeating a state, skipping a state, moving backward by another path,
or naming an unknown state refuses. Validation and serialization never move the
state. A caller must name both states for each transition.

The states describe progress through the front door. They do not grant runtime
authority:

| State | Meaning |
|---|---|
| `uninitialized` | The target has not been prepared for Delivery Workbench. |
| `rails-ready` | The rails are installed and healthy enough to draft setup. |
| `draft` | A schema-valid proposal exists and may still have unresolved questions. |
| `reviewed` | A person has reviewed the proposal. Review itself writes nothing. |
| `configured` | A separately authorized setup act has saved configuration. The proposal did not authorize that act. |
| `grant-previewed` | The existing program surface has produced a separate grant preview. The proposal is still inert. |

## Envelope

Every proposal has these exact top-level fields:

```json
{
  "schema": "delivery-workbench-setup-proposal@1",
  "state": "draft",
  "project": {
    "slug": "sample-project",
    "prefix": "SP",
    "title": "Sample project",
    "provenance": {
      "kind": "user-answer",
      "source_note": "The operator supplied the project identity."
    }
  },
  "source_intent": {
    "idea": "Build a small tool that keeps delivery work reviewable.",
    "mode": "build",
    "provenance": {
      "kind": "user-answer",
      "source_note": "The opening answer in the setup conversation."
    }
  },
  "tracked_content": {
    "roadmap": {
      "phases": [],
      "exit_criteria": []
    },
    "policy": null
  },
  "local_content": {
    "driver_bindings": {}
  },
  "unresolved_questions": [],
  "starts_work": false,
  "creates_grant": false,
  "certifies": false,
  "commits": false
}
```

The empty roadmap lists above show the field shape only. A valid proposal has
at least one phase, at least one story in each phase, at least one acceptance
criterion per story, and at least one roadmap exit criterion.

The four inertness fields are required on every proposal and every
proposal-shaped preview. Each value must be the JSON boolean `false`. Missing
fields and truthy substitutes refuse. `validate_preview` deliberately applies
the same complete validation as `validate_proposal`; preview is a presentation
role, not a more powerful document type.

## Field reference

### Project and source intent

`project` has the exact fields `slug`, `prefix`, `title`, and `provenance`.

- `slug` is a lowercase hyphenated identifier of at most 128 characters.
- `prefix` is an uppercase alphanumeric story prefix of at most 16 characters.
- `title` is a non-empty string of at most 300 characters.

An absent or partial project identity refuses. The contract never resolves a
missing identity by choosing a project.

`source_intent` has the exact fields `idea`, `mode`, and `provenance`. `idea` is
the rough source idea and is limited to 20,000 characters. `mode` is exactly
`build` or `maintain`.

### Tracked roadmap content

`tracked_content` has exactly two fields: `roadmap` and `policy`. This field
contains material intended for repository tracking if a later, separately
authorized setup apply saves it. Its presence in a proposal does not write
canon.

`roadmap` has `phases` and `exit_criteria`:

- `phases` contains 1 through 100 phase objects. A phase has `number`, `title`,
  `goal`, `provenance`, and `stories`. The number is unique in the draft and
  falls from 0 through 9999. A phase contains 1 through 200 stories.
- A story has `id_sketch`, `title`, `problem`, `scope_in`, `scope_out`,
  `acceptance_criteria`, `dependencies`, and `provenance`. An ID sketch is a
  bounded draft identifier, not an existing-story claim. Scope lists contain
  at most 100 items. Acceptance criteria contain 1 through 100 items.
  Dependencies contain at most 100 items.
- Scope entries and criteria use `{ "text": ..., "provenance": ... }`.
  Text is non-empty and limited to 5,000 characters.
- A dependency uses `{ "id_sketch": ..., "provenance": ... }`. The ID sketch
  is non-empty and limited to 128 characters.
- `exit_criteria` contains 1 through 100 text-and-provenance items.

### Optional tracked policy

`tracked_content.policy` is either `null` or one complete embedded bundle with
these exact fields:

| Field | Shape |
|---|---|
| `program` | One document wrapper |
| `workflows` | 1 through 100 document wrappers |
| `organization` | One document wrapper |
| `rubrics` | 1 through 100 document wrappers |
| `provenance` | Provenance for the choice to include this policy bundle |

A document wrapper has `document` and `provenance`. `document` must be a JSON
object. The setup-proposal validator treats its program, workflow,
organization, or rubric semantics as opaque. The policy validators in
[`programs.py`](../pmo-roadmap/lib/dw_pmo/programs.py) own those semantics.

Opaque does not mean unbounded. Each embedded document is limited to 262,144
canonical JSON bytes, 20 nested levels, 2,000 fields per object, 2,000 items per
list, 128 characters per object key, and 32,768 characters per string.
Floating-point and non-JSON values refuse. The complete proposal is limited to
1,000,000 canonical JSON bytes.

### Local driver content

`local_content` is structurally separate from `tracked_content`. It has one
field, `driver_bindings`, which maps at most 100 logical profile names to local
adapter metadata. This content is intended for `.git`-local configuration if a
later exact setup lease authorizes saving it. It is not tracked policy and is
not a program grant.

A profile name uses the local driver identifier form and is limited to 128
characters. Each profile has the exact fields `adapter`, `model`, `provider`,
and `provenance`. The three metadata strings are non-empty and limited to 128
characters.

No key in the driver-binding structure may match `credential`, `token`,
`secret`, `password`, or `api_key` patterns, including hyphenated API-key
forms. Profile names are keys and follow the same refusal. Values are metadata,
not credential storage. Runtime authentication remains owned by the local
adapter or harness outside this proposal.

### Unresolved questions

`unresolved_questions` is a list of at most 100 objects. Each object has
`question` and `provenance`. A question is non-empty and limited to 5,000
characters.

A material ambiguity belongs in this list. Producers must not silently omit an
unknown answer or turn it into an unlabeled recommendation. An empty list means
the producer found no unresolved question; it does not relax any required
identity, roadmap, or policy field.

### Provenance

Every project identity, source intent, phase, story, scope item, criterion,
dependency, policy choice, embedded policy document, driver binding, and
unresolved question carries provenance. The shape is exact:

```json
{
  "kind": "repository-fact",
  "source_note": "pm/roadmap/demo/README.md declares the DM prefix."
}
```

`kind` is one of:

- `user-answer`: the person supplied the value;
- `repository-fact`: a read of repository state supplied the value; or
- `recommendation`: the drafting surface proposed the value for review.

`source_note` is a non-empty string of at most 2,000 characters. Provenance
explains origin. It does not increase authority or satisfy evidence rules.

## Canonical serialization

`canonical_json(proposal)` performs full validation, sorts object keys, uses
compact separators, preserves Unicode with `ensure_ascii=False`, and rejects
non-finite numbers. Its UTF-8 encoding is the canonical byte representation.

`load_proposal(text)` accepts bounded UTF-8 text or bytes, rejects duplicate
object keys and non-finite numbers, validates the complete proposal, and
returns the parsed object. Every accepted value must survive a canonical
serialize/load round trip without a data change. The module reads no file and
consults no process, network, clock, environment, repository, or random source.

## Refusal catalogue

All contract refusals raise `DwError`. The message begins with a JSON Pointer
path. `/` in a dynamic object key is escaped as `~1`; `~` is escaped as `~0`.
Examples include:

```text
/schema: unsupported setup proposal schema
/project/title: field is required
/tracked_content/roadmap/phases/0/title: must be a bounded string (maximum 300 characters)
/tracked_content/roadmap/phases/0/stories/0/extra: unknown field
/local_content/driver_bindings/api_token: profile names may not match credential, token, password, secret, or API-key patterns
/state: transition from reviewed to configured is not permitted
```

Validation fails closed for:

- an unsupported or missing schema;
- an unknown, missing, or wrongly typed field at any contracted level;
- an absent or malformed project identity;
- an empty required list or any list, string, object, phase number, or complete
  proposal beyond its declared bound;
- missing or unknown provenance;
- a policy document that is not an object, cannot be represented as
  deterministic JSON, or exceeds an opaque-document bound;
- a credential-shaped key in local driver bindings;
- a missing inertness field or any inertness value other than `false`;
- duplicate JSON keys, non-finite numbers, malformed UTF-8, or malformed JSON;
  and
- an unknown, implicit, repeated, skipped, or otherwise prohibited journey
  transition.

The validator reports the first deterministic refusal. It never repairs,
defaults, truncates, selects, saves, or authorizes a proposal.

## Guarded setup lease

A reviewed proposal reaches canon only through one guarded setup act. The CLI
signatures are:

```text
dw setup preview <proposal-file>
dw setup apply --proposal <setup:id> --expect <setup-sha256:token>
```

`preview` validates the proposal with the contract above and computes the full
write set before it creates a pending lease record under the repository's Git
directory. The returned `delivery-workbench-setup-preview@1`-shaped document is
canonical JSON with sorted keys and compact separators. It lists every tracked
roadmap and policy path plus the Git-local driver roster, with an explicit
`null` before-hash for an absent file and a SHA-256 after-hash. The same core
document is returned by MCP `dw_setup_preview` and HTTP
`POST /api/setup/preview`.

A setup token is bound to the repository identity, branch, HEAD, exact staged
index contents, complete observed roadmap and policy trees, driver-roster hash,
every target before/after hash, the proposal's canonical hash, and the current
setup-claim generation. The token begins `setup-sha256:`. Program-start and
step tokens are different token types and cannot be substituted. Preview writes
no tracked content, starts no process, and keeps all four inertness fields
false.

`apply` accepts only the proposal ID and exact token. It loads the pending plan,
re-observes every bound fact, and refuses unknown IDs, wrong token types, drift,
or reuse before changing a target. A successful apply exclusively consumes the
token, temp-writes and renames the complete tracked-and-local set under a
recoverable journal, and advances `reviewed` to `configured` through
`transition_state`. If any rename fails, rollback restores every prior byte and
removes every newly created path. Apply creates no grant, run, contract, or
commit and invokes no child process.

The transport signatures mirror the same core:

- MCP `dw_setup_preview({"proposal_file": "..."})` and
  `dw_setup_apply({"proposal": "setup:...", "expect": "setup-sha256:..."})`;
- HTTP `POST /api/setup/preview` with only `proposal_file`, and
  `POST /api/setup/apply` with only `proposal` and `expect`.

The older `dw setup [project] [--technical]` delivery-choice view remains
read-only. `preview` and `apply` are reserved setup subverbs and cannot be
project slugs in a setup proposal. Public `dw adopt --apply` is retired because
it was an unleased multi-file write; adoption parsing and phase/story planning
remain internal building blocks. `dw phase create` and `dw story create` remain
single-file operator conveniences. They already use the shared `plan_*` then
`apply_plan` primitives, so roadmap writes still have one planned, stale-checked,
rollback-capable implementation path rather than a second writer.

## What a proposal can never do

A proposal or proposal-shaped preview can never:

- choose a project on the operator's behalf;
- write a roadmap, tracked policy, or local driver file;
- mint or substitute for a setup lease;
- create or substitute for a program grant;
- start a story, run, process, or program;
- satisfy a gate, evidence, verdict, or certification rule;
- check or certify a commit contract;
- create a commit or invoke `git commit`; or
- store credentials, tokens, passwords, secrets, or API keys.

Project choice, setup consent, runtime grant, certification, and commit remain
separate deliberate acts under their owning contracts. A later surface that
assigns any of that authority to this proposal violates
`delivery-workbench-setup-proposal@1`.
