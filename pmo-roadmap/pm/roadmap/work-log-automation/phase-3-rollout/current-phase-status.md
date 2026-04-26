# Phase 3 - Rollout

**Last updated:** 2026-04-25.

## Goal

Prove Work Log Automation in a real consumer project, document the operating
model, and close the roadmap with evidence that the framework is installable,
useful, and safe by default.

## Scope

- **In:** Consumer-project pilot, docs polish, generated snippets, phase close
  evidence, and adoption checklist.
- **Out:** Multi-user log aggregation, cloud publishing, and analytics UI.

## Exit criteria (evidence required)

- [ ] One consumer project opts in through config and produces consented logs
  matching the WLA-0-01 schema.
- [ ] Denied-consent and excluded-path examples are documented.
- [ ] README and snippet instructions match actual behavior.
- [ ] A multi-day pilot review confirms the log remains readable after entries
  accumulate.
- [ ] Final summary names what shipped, what remains manual, and rollout risks.

## Story status

| ID | Story | Status | Story file | Evidence |
|---|---|---|---|---|
| WLA-3-01 | Pilot in one consumer project | backlog | [story-01-consumer-pilot](./story-01-consumer-pilot.md) | - |
| WLA-3-02 | Polish operator and agent documentation | backlog | [story-02-docs-polish](./story-02-docs-polish.md) | - |
| WLA-3-03 | Close the roadmap with final evidence | backlog | [story-03-final-summary](./story-03-final-summary.md) | - |

## Where we are

Phase 3 waits for Phase 2 hardening. The pilot should use an existing consumer
project, not a synthetic repo, because the feature's value is daily technical
memory across real work. A single successful commit is necessary but not enough;
the pilot should include a short multi-day review or explicitly defer that
review with a reason.

## Active risks

| Risk | Likelihood | Mitigation | Stop signal |
|---|---|---|---|
| Pilot produces noisy summaries | medium | Tune summary prompt/schema only after reviewing schema-conformant real entries | Three consecutive entries fail to identify changed files, verified work, or follow-ups |
| Docs overstate safety | low | Document consent, local-only default, and redaction limits plainly | A reader could think redaction makes secret logging safe |
| Rollout adds too much ceremony | medium | Keep opt-in config small and contracts explicit | A normal commit requires more work-log text than PMO certification text |

## Decisions made (this phase)

- 2026-04-25 - Pilot after hardening, not during MVP - keeps early development
  focused on lifecycle correctness - Phase 0 architecture.

## Decisions deferred

- Which consumer project pilots first - trigger after Phase 2 passes - default
  is the first active project where daily work logs would be valuable.
