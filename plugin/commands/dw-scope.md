---
description: Hold one scope conversation and draft one inert Delivery Workbench setup proposal.
---

Turn a rough idea or an existing project's next direction into one reviewable
setup proposal. This is a drafting conversation. It does not authorize or save
roadmap work.

## Choose one mode

Name the mode at the start and keep it for the whole conversation.

- **Build mode:** use this for a rails-ready repository and a new idea. Read the
  Delivery Workbench status first. If the rails are not healthy or the
  repository already has roadmap canon that would make this a maintenance
  change, explain the mismatch and stop rather than silently switching modes.
- **Maintain mode:** use this for an existing codebase or roadmap. Inspect it
  before asking the user to restate facts the repository already supplies. Use
  only the dedicated read surfaces `dw_status`, `dw_context`, `dw_board`, and
  `dw_story_show`, plus file reads. Read the project README, current phase,
  relevant stories, source canon, tests, and package or build files needed to
  understand the requested change. If a dedicated read surface is unavailable,
  ask the user for its output instead of replacing it with a shell command.

In either mode, read
`docs/setup-proposal.md`, `pmo-roadmap/lib/dw_pmo/setup_proposal.py`, and
`pmo-roadmap/templates/roadmap-builder.md` before drafting. Use read operations
only until the final proposal write.

## Hold one guided conversation

Start with one open question: what should this project make possible, and for
whom? Use the answer and repository facts to avoid a mechanical questionnaire.
Ask follow-ups together when they are related, but do not finish until these
minimum subjects are answered or recorded as unresolved:

1. Project identity: title, stable kebab-case slug, and uppercase story prefix.
2. Desired outcome: what changes for the user when the work succeeds.
3. Intended users: who uses or depends on the result.
4. First usable milestone: the smallest end-to-end result worth handing over.
5. Constraints: technical, product, time, compliance, compatibility, or
   operating limits.
6. Non-goals: nearby work that must stay out of scope.
7. Verification expectations: the checks and observable evidence that should
   prove the milestone works.
8. Desired autonomy level: how independently agents may work, what must be
   reviewed, and where the person expects a stop or approval.

Offer a recommendation when it helps the user react to something concrete, but
label it as a recommendation. Do not turn uncertainty into a fact. If two
reasonable interpretations would produce materially different phases, stories,
criteria, policy, or driver choices, ask. If the user cannot answer yet, add an
entry to `unresolved_questions`.

## Keep provenance honest

Every generated project identity, source intent, phase, story, scope item,
acceptance criterion, dependency, policy choice, policy document, driver
binding, and unresolved question must carry exactly one provenance object:

```json
{"kind":"user-answer","source_note":"The user named the first usable milestone."}
```

`kind` is exactly one of:

- `user-answer` for a value the person supplied;
- `repository-fact` for a value established by a named repository read; or
- `recommendation` for a value you proposed for review.

Use a specific `source_note`. Name the answer or repository path that supports
the item. A recommendation remains a recommendation even when it looks
obvious. An unresolved question is an item location, not a fourth provenance
kind; its provenance records where the uncertainty came from.

## Assemble the contracted proposal

Write exactly one `delivery-workbench-setup-proposal@1` object with these
closed fields:

```text
schema, state, project, source_intent, tracked_content, local_content,
unresolved_questions, starts_work, creates_grant, certifies, commits
```

Set `state` to `draft`. Set all four inertness fields to the JSON boolean
`false`.

Use these exact nested shapes:

```text
project = {slug, prefix, title, provenance}
source_intent = {idea, mode, provenance}
tracked_content = {roadmap, policy}
roadmap = {phases, exit_criteria}
phase = {number, title, goal, provenance, stories}
story = {id_sketch, title, problem, scope_in, scope_out,
         acceptance_criteria, dependencies, provenance}
text item = {text, provenance}
dependency = {id_sketch, provenance}
local_content = {driver_bindings}
driver binding = {adapter, model, provider, provenance}
unresolved question = {question, provenance}
provenance = {kind, source_note}
```

The roadmap needs at least one phase, one story in every phase, one acceptance
criterion in every story, and one roadmap exit criterion. Phase numbers must be
unique integers from 0 through 9999. Keep story `id_sketch` values stable within
the draft and use the selected project prefix. Lists may be empty only where the
contract permits it, such as story dependencies and scope lists.

Set `tracked_content.policy` to `null` unless the conversation has enough
information for one complete policy bundle. A non-null bundle has exactly
`program`, `workflows`, `organization`, `rubrics`, and `provenance`; each
wrapped document has exactly `document` and `provenance`. Do not invent a
partial policy to fill the field.

`local_content.driver_bindings` is an object keyed by logical profile name. It
may contain only non-secret adapter metadata. Never include credentials,
tokens, passwords, secrets, API keys, or a key whose name suggests one. An
empty object is valid.

Map the autonomy answer into concrete, traced scope, criteria, policy, or driver
choices only when the answer supports them. Otherwise add an unresolved
question. The proposal has no free-form autonomy field and its closed schema
must not be extended.

## Validate without acting

Validate the complete in-memory object against every closed field, bound,
identifier rule, provenance location, and inertness rule in
`setup_proposal.py`. Material ambiguity must be present in
`unresolved_questions`, not hidden in prose. Re-read the finished file and make
sure it is the same object you validated.

Before writing, read `.gitignore` and confirm that `.tmp/` is ignored. If it is
not ignored, report the blocker and do not edit `.gitignore` or write the
proposal. If it is ignored, the only write this skill may make is:

```text
.tmp/setup-proposal.json
```

Serialize as UTF-8 canonical JSON: object keys sorted recursively, compact
separators, Unicode preserved, finite JSON values only, and no trailing newline.
The serialization must match `canonical_json` from the contract module.

For a revision, start from the last validated proposal. Change only the sections
whose source answer or derived recommendation changed. Preserve every unaffected
JSON value exactly, keep list ordering deterministic, then serialize again with
the same canonical rules. Compare the canonical bytes of each unaffected
section before replacing the file. If an unaffected section changed, restore it
before writing. This makes one changed answer produce byte-stable unchanged
sections.

## Hard boundary

Do not create or edit any file outside `.tmp/setup-proposal.json`. Do not use a
shell or a general-purpose command runner. Never invoke `phase create`,
`story create`, `story status`, `setup apply`, `git commit`, a setup preview, or any
other mutation. Do not start a story, process, run, or program. Do not mint a
lease or grant. Do not certify anything. The finished JSON remains inert even
when it has no unresolved questions.

End every successful conversation with these exact three lines, unchanged:

```text
Review it in the Workbench under Roadmap changes (`#/edit`).
Next command: `dw setup preview .tmp/setup-proposal.json`
nothing has been saved
```
