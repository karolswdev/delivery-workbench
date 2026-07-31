# WLA-33-00 - Design system and component foundation

- **Project:** work-log-automation
- **Phase:** 33
- **Status:** done
- **Depends on:** none
- **Unblocks:** WLA-33-01, WLA-33-02, WLA-33-03, WLA-33-04, WLA-33-05, WLA-33-06, WLA-33-07, WLA-33-08
- **Owner:** unassigned

## Problem

Phase 32 added CSS custom properties (tokens) but the rendering layer
is still 5,000 lines of hand-wired DOM manipulation. Every story in
this phase will add panels, interactions, and real-time updates. Building
those on raw `createElement` / `innerHTML` will produce the same kind of
functional-but-ugly interface the current workbench has. Operator feels
good because it has a real component system with consistent interaction
patterns, not because it has the right feature list.

The workbench needs a design system before it needs features: reusable
components, a layout grid, interaction primitives (drag, resize, stream),
transitions, and visual patterns for every state a piece of UI can be in
(loading, empty, error, active, disabled). Without this, nine feature
stories will produce nine differently-styled panels.

## Scope

- **In:**
  - Evaluate and adopt a lightweight framework (Preact, Lit, or vanilla
    web components) to replace the monolithic `app.js` DOM manipulation.
    The choice is recorded as a decision in this story.
  - Build a component library covering: Button (primary, secondary,
    danger, ghost), Card (story card, status card, info card), Panel
    (resizable, collapsible, with header/toolbar/body slots), StatusPill
    (backlog, ready, in-progress, blocked, done, on-hold — with the
    existing color roles from Phase 32 tokens), Badge (count, alert,
    "needs you"), Fold/Disclosure (the Technical Details pattern),
    Toolbar, Divider (draggable resize handle), Skeleton (loading
    placeholder), EmptyState (illustration + message + action),
    Toast/Notification, StreamLine (a single line in a live transcript).
  - Define interaction primitives: drag-and-drop with ghost preview and
    drop-zone highlighting, panel resize with min/max constraints and
    snap, keyboard navigation (focus trap in panels, arrow keys on
    board, Escape to close), transitions (panel open/close, card move,
    status change — 150-200ms ease-out, respect prefers-reduced-motion).
  - Define the layout grid: a CSS grid shell with named areas (board,
    session, diff, terminal, sidebar) that the multi-panel story (08)
    will populate. Responsive breakpoints at 768px and 1200px.
  - Define visual patterns: typography scale (4 sizes max), spacing
    scale (4px base), elevation (flat, raised, overlay), focus rings,
    scrollbar styling, selection colors, monospace blocks for code/diffs/
    terminal output.
  - Migrate the existing board and navigation to the new components as
    proof that the system works — the board must render identically (or
    better) after migration.
  - A living reference page at `#/design` (dev-only, not in production
    navigation) showing every component in every state and both themes.
- **Out:** New features or panels (those are stories 01-08). Changes to
  the Python server or API routes. Changes to the authority model.

## Localization hints

- **Affected files:**
  - `pmo-roadmap/workbench/app.js` (refactor into framework + components)
  - `pmo-roadmap/workbench/style.css` (component styles, layout grid)
  - `pmo-roadmap/workbench/index.html` (framework bootstrap)
  - `pmo-roadmap/tests/workbench-ui-smoke.sh`
  - `pmo-roadmap/tests/workbench-accessibility.py`

## Framework decision

**Vanilla Web Components (Custom Elements v1, no Shadow DOM).**

The project has no build step and a stdlib-only philosophy. Vanilla Custom
Elements give a real component model with lifecycle hooks and attribute
observation, require no dependencies, and work with the existing CSS custom
property theming system because they render to light DOM. Shadow DOM was
rejected because it would isolate component internals from the design-token
stylesheet. Preact+htm was considered but adds a runtime dependency and
a mental-model shift the codebase doesn't need at this scale. The component
file self-registers via `customElements.define()` and loads as a plain
`<script>` tag — no bundler, no imports, no build.

## Acceptance criteria

- [x] A framework decision is recorded (Preact, Lit, or vanilla web
  components) with a one-paragraph rationale.
- [x] A component library exists with at least: Button (4 variants),
  Card, Panel (resizable, collapsible), StatusPill (6 statuses), Badge,
  Fold, Skeleton, EmptyState, and StreamLine.
- [x] Every component renders correctly in both light and dark themes.
- [x] Drag-and-drop on the board shows a ghost preview of the card and
  highlights valid drop zones.
- [x] Panel resize works with draggable dividers, min/max constraints,
  and a visible resize cursor.
- [x] Transitions on panel open/close and card move are 150-200ms
  ease-out, and are suppressed under prefers-reduced-motion.
- [x] Keyboard navigation works: Tab moves between panels, arrow keys
  move between board cards, Escape closes the active panel.
- [x] A reference page at `#/design` shows every component in every
  state (default, hover, focus, active, disabled, loading, empty, error)
  in both themes.
- [x] The existing board renders through the new component system with
  no functional regression — all existing board tests pass.
- [x] The existing UI smoke and accessibility suites pass after the
  migration.
- [x] Wide (1440px) and mobile (390px) screenshots in both themes show
  the migrated board looking better than before, not just equivalent.
