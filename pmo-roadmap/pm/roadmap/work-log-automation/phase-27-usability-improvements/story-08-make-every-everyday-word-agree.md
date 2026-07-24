# WLA-27-08 - Make every everyday word agree

- **Project:** work-log-automation
- **Phase:** 27
- **Status:** backlog
- **Depends on:** WLA-27-01, WLA-27-03, WLA-27-04, WLA-27-05, WLA-27-06, WLA-27-07
- **Unblocks:** WLA-27-10
- **Owner:** unassigned

## Problem

A clear Workbench can still fail if CLI help, notifications, errors,
onboarding, and docs use different names or drop users back into protocol
vocabulary. Parallel adapters are especially prone to copy and semantic drift.

This story carries the product-language contract through every everyday
surface, backed by one presentation projection and executable inventory
coverage, while deliberately leaving machine contracts exact and stable.

## Scope

- **In:** human CLI output/help, Workbench labels and summaries, human-readable
  HTTP pages and stream/notification summaries, setup/onboarding, errors,
  examples, README and everyday product docs; shared render/application-view
  helpers; complete surface inventory; terminology and snapshot checks;
  mirrored source/package parity; links to technical docs and audit views.
- **Out:** renaming CLI commands solely for tone; changing JSON/MCP/HTTP
  machine keys, event kinds, persisted identifiers, or schemas; rewriting
  architecture/code documentation that intentionally uses exact terms;
  marketing-site work or localization infrastructure.

## Acceptance criteria

- [ ] Every surface in the WLA-27-01 inventory is migrated, explicitly marked
  technical/audit, or documented as out of scope with a reason; there are no
  silent leftovers.
- [ ] Human CLI, Workbench, notifications, help, errors, onboarding, and
  everyday docs use the same preferred term and definition for each product
  concept.
- [ ] Shared application-view/render helpers receive canonical facts and
  produce presentation content; individual adapters do not copy policy or
  independently translate state.
- [ ] Exact command names and machine payloads remain copyable and stable where
  users or agents need them, but surrounding explanations state the ordinary
  task and outcome first.
- [ ] Technical/audit and architecture material remains discoverable,
  internally precise, and clearly distinguished from the everyday path.
- [ ] Terminology, human-output snapshots, adapter parity, mirrored-tree
  checks, link checks, and package tests fail on drift.
- [ ] Product docs teach complete tasks from the WLA-27-02 journeys rather
  than listing internal objects as the primary mental model.

## Test plan

- **Unit:** run terminology and renderer snapshot cases for each concept,
  including allowed exact-language contexts and accidental leakage.
- **Integration:** run CLI/MCP/HTTP/Workbench/notification parity, docs/link,
  mirrored-tree, and packaged-help checks.
- **Manual / device:** follow one canonical journey from each human surface and
  verify the same concept names, outcome, next step, and technical-details
  path.

## Notes / open questions

Parity does not require prose to be byte-identical across channels. It requires
the same canonical facts, product concepts, action identity, and trust boundary
with channel-appropriate rendering.
