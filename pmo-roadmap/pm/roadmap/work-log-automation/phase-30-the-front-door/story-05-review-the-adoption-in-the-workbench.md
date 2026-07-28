# WLA-30-05 - Review the adoption in the workbench

- **Project:** work-log-automation
- **Phase:** 30
- **Status:** done
- **Depends on:** WLA-30-04
- **Unblocks:** WLA-30-10
- **Owner:** unassigned

## Problem

Between the conversation that drafts and the terminal that consents sits
the human who must actually understand what they are approving. A raw
proposal document is honest but unreadable; the approval it earns is
rubber-stamped, not informed. The workbench already owns the reviewing
role — board, health, trace, roadmap changes. It needs one contextual
view that renders a setup proposal in product language: what the project
is, what the phases accomplish, what the first stories prove, which
assumptions remain unresolved, and which delivery policies will be saved
alongside the roadmap.

This is a review surface, not a fourth authoring environment and not an
authority surface. The browser reads and annotates; the terminal consents.

## Scope

- **In:** an adoption-review view under the existing roadmap-changes
  workspace (no new top-level navigation): project vision, phase sequence,
  story dependencies, acceptance criteria, provenance, unresolved
  questions, and the full changed-path list. Program policy and
  `.git`-local driver bindings rendered visibly separate from roadmap
  truth, labeled "configuration, not permission." Product language first;
  exact JSON, hashes, and paths under technical details. Accept-for-preview
  and reject-with-corrections marks that feed back to the conversation —
  neither of which applies anything. Existing accessibility conventions:
  keyboard navigation, focus restoration, narrow-screen layout,
  light/dark.
- **Out:** applying the proposal or minting any token from the browser;
  editing proposal content in the browser beyond the bounded correction
  packet; the generated-program review (WLA-30-08); any new pane or route
  outside roadmap-changes.

## Acceptance criteria

- [ ] The view renders greenfield, existing-project, unresolved-heavy, and
  invalid proposals correctly, with provenance and unresolved questions
  always visible.
- [ ] Configuration (policy + driver bindings) is visually and semantically
  separated from roadmap content and labeled as non-authorizing.
- [ ] Review can mark accepted-for-preview or rejected-with-corrections;
  neither mark mutates the repository, roadmap, policy, roster, grant, or
  run state — proven by before/after filesystem and store assertions.
- [ ] The route lives under roadmap-changes with no new top-level item.
- [ ] The HTTP model is parity-tested against the CLI proposal model.
- [ ] Keyboard navigation, focus restoration, narrow-screen, and
  light/dark checks pass at the existing workbench bar.

## Test plan

- **Unit:** proposal-to-view model mapping, including invalid and
  unresolved shapes.
- **Integration:** browser snapshot tests for the four proposal states;
  HTTP/CLI parity; review-only session side-effect assertions.
- **Manual / device:** review a real generated proposal and judge whether
  a non-expert could say, in their own words, what approving it would
  save.

## Notes / open questions

The correction packet's shape (free text vs. structured per-item
objections) is open; default is per-item with an overall note, because the
conversation needs addressable feedback to revise deterministically.
