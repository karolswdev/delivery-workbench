# Terminal Demos

These tapes are Charm VHS sources for repository demos. They require the `vhs`
CLI from Charmbracelet.

- `onboarding.vhs` shows guided session intake followed by adoption prompt
  generation.
- `commit-gate.vhs` shows the commit hook blocking a missing contract, then
  accepting a fresh contract and appending a consented work-log entry.

Render them from the repository root:

```bash
vhs demos/onboarding.vhs
vhs demos/commit-gate.vhs
```

## Rendered Assets

![Onboarding demo](./rendered/onboarding.gif)

![Commit-gate demo](./rendered/commit-gate.gif)

The GIF outputs are written to `demos/rendered/`. The helper scripts create
throwaway repositories under `/tmp` and do not touch the current checkout.
Only the published demo GIFs are tracked; other generated files in
`demos/rendered/` stay ignored.
