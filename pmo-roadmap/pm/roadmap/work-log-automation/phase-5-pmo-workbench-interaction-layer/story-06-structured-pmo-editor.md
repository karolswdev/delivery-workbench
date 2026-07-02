# WLA-5-06 - Build structured PMO editor

- **Project:** work-log-automation
- **Phase:** 5
- **Status:** backlog
- **Depends on:** WLA-5-02, WLA-5-03, WLA-5-04, WLA-5-05
- **Unblocks:** WLA-5-07, WLA-5-10
- **Owner:** unassigned

## Problem

Agents need to update PMO roadmaps without hand-editing brittle Markdown
tables. The editor must expose structured PMO operations while preserving
hand-authored prose and refusing unsafe states.

## Scope

- **In:** Forms for create phase, create story, update story status, attach
  evidence, close phase, field validation, source preview, evidence-required
  done transition, and revalidation after edits.
- **Out:** Arbitrary Markdown editor, WYSIWYG authoring, acceptance-criteria
  generation, auto-commit, or mutation types not supported by the shared core.

## Acceptance criteria

- [ ] Editor actions map one-to-one to core mutation kinds.
- [ ] Create phase form validates phase number, slug, goal, and README phase
  index collision before preview.
- [ ] Create story form validates title, status, story numbering, and phase
  story-table availability before preview.
- [ ] Status update form refuses `done` unless existing or provided evidence is
  present.
- [ ] Attach evidence form writes only paired `evidence-story-N.md` in the
  story phase.
- [ ] Close phase form refuses open stories unless the operator explicitly
  chooses the same force semantics supported by core.
- [ ] Editor preserves existing prose outside owned metadata/table regions.

## Test plan

- **Unit:** Editor state tests for field validation, refusal states, and
  mutation request construction.
- **Integration / Cypress:** Browser tests exercise each form through preview
  without applying writes.
- **Manual / device:** Verify form density, keyboard flow, error placement, and
  no text overlap on desktop and mobile.

## Notes / open questions

The editor is not the mutation applier. It constructs structured intent and
hands that intent to the preview/diff workflow.
