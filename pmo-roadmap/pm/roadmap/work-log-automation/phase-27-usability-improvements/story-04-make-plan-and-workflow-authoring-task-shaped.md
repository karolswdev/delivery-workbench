# WLA-27-04 - Make plan and workflow authoring task-shaped

- **Project:** work-log-automation
- **Phase:** 27
- **Status:** done
- **Depends on:** WLA-27-01, WLA-27-02
- **Unblocks:** WLA-27-06, WLA-27-08, WLA-27-09, WLA-27-10
- **Owner:** unassigned

## Problem

Program Studio is lossless and powerful, but its configuration structure is
closer to the underlying score and policy than to the task of designing how
work should move. People need to describe what will be delivered, how it
progresses, what quality means, when to ask for help, and where the limits are
without first reverse-engineering the runtime.

This story reorganizes plan and workflow authoring around those decisions while
preserving exact round-trip behavior and advanced technical control.

## Scope

- **In:** Program Studio information architecture for delivery scope,
  work/sequence, quality and review points, repair/escalation paths, decision
  checkpoints, stop conditions, and limits; plain-language summaries and
  preflight; progressive technical editing; templates/examples; lossless
  import/export and round-trip tests against existing policy/score contracts.
- **Out:** team/reviewer assignment details owned by WLA-27-05; live operation;
  new workflow nodes, policy fields, loop semantics, or authority; a simplified
  format that cannot round-trip existing advanced configurations.

## Acceptance criteria

- [x] The default authoring sequence follows delivery decisions rather than
  persisted object order, and each section says what question it answers.
- [x] A readable plan summary shows scope, flow, quality/review points,
  decision points, repair/escalation routes, stop conditions, and limits before
  the user saves or requests permission.
- [x] Advanced hierarchical workflows, subflows, bounded loops, debate cells,
  and exact conditions remain editable through progressive technical detail
  without appearing as mandatory first-run concepts.
- [x] Existing valid configurations import into the redesigned Studio and
  export to an object that is semantically identical; unknown/extensions are
  preserved or editing refuses safely.
- [x] Validation identifies the delivery decision that is incomplete, shows
  affected downstream behavior, and links to the relevant editor section.
- [x] Drafting, previewing, and abandoning a plan have no execution, roadmap,
  permission, or network side effects.

## Test plan

- **Unit:** cover application summaries, section validation, advanced-detail
  disclosure, unknown-field preservation, and semantic round trips.
- **Integration:** extend Program Studio and configuration parity tests with
  simple, hierarchical, looped, and deliberately invalid plans.
- **Manual / device:** author the canonical plan journey by keyboard at narrow
  and wide widths, then inspect the exact exported configuration.

## Notes / open questions

The product-language contract decides the final labels. "Task-shaped" changes
navigation and explanation, not the underlying workflow compiler or policy
meaning.
