# WLA-36-01 - Design tokens and type

- **Project:** work-log-automation
- **Phase:** 36
- **Status:** backlog
- **Depends on:** none
- **Unblocks:** WLA-36-02, WLA-36-03, WLA-36-04
- **Owner:** unassigned

## Problem

The current UI has no designed foundation: monospace is used for every character of UI text, there is no type scale, no weight system, no luminance model, and colors/spacing/radii are ad hoc. The owner's verdict is on record and correct. The Linear design system (adopted token-for-token from the popular-web-designs reference) becomes the foundation.

## Scope

- **In:** A rebuilt token layer in pmo-roadmap/workbench/style.css: Linear's dark-native palette (canvas #08090a, panel #0f1011, elevated #191a1b, hover #28282c; text #f7f8f8/#d0d6e0/#8a8f98/#62666d; single accent #5e6ad2/#7170ff/#828fff; translucent-white borders 0.05/0.08), the Inter-first type scale (weights 400/510/590, cv01+ss03 feature settings, negative tracking at display sizes, mono ONLY for code/hashes/terminal), the 8px spacing grid, the radius scale (2/4/6/8/12/9999), and luminance-step elevation. Dark becomes the native default; light remains a first-class prefers-color-scheme override restyled to Linear's light neutrals. The two core tests pinning color-scheme literals are updated DELIBERATELY with the phase decision recorded. Reference: ~/dev/hermes-agent/skills/creative/popular-web-designs/templates/linear.app.md.
- **Out:** Component and layout rework (stories 02-04). No new fonts fetched at runtime — Inter via local-font stack with system fallbacks; the UI must stay dependency-free and offline.

## Acceptance criteria

- [ ] The token layer defines Linear's surfaces, text tiers, single accent family, translucent-white border tiers, radius scale, and 8px spacing scale as CSS custom properties; ad hoc hex values outside the token block are removed from style.css.
- [ ] UI text renders in the Inter-first stack with font-feature-settings 'cv01','ss03' and the 400/510/590 weight system; monospace appears only on code, hashes, IDs, and terminal output.
- [ ] Dark is the native default theme; light is a complete prefers-color-scheme override using Linear's light neutrals; both themes render every existing surface without regressions in the browser exam.
- [ ] The two core tests pinning the color-scheme literals are deliberately updated, and the flip is recorded as a phase decision.
- [ ] Elevation uses luminance stepping (0.02 -> 0.04 -> 0.05 translucent white) and the documented border tiers, not drop shadows, on dark surfaces.
- [ ] Full core suite green; accessibility contract green; language lint green.

## Test plan

- **Unit:** covered by the verification command below.
- **Integration:** `bash pmo-roadmap/tests/workbench-ui-smoke.sh`
- **Manual / device:** operator reviews rendered screenshots before the story flips done.

## Notes / open questions

Adopt values from ~/dev/hermes-agent/skills/creative/popular-web-designs/templates/linear.app.md exactly; when the reference is silent, choose the quietest option. Contrast must stay WCAG AA — verify the #8a8f98-on-#08090a class of pairings against their usage sizes.
