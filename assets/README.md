# Repository assets

Every asset here is regenerated from current sources by a checked-in
script — never edited by hand.

| Asset | Used by | Regenerate with |
|---|---|---|
| `workbench-board.png` | root README | the browser exam's capture mode (below) |
| `workbench-memory.png` | root README | the browser exam's capture mode (below) |
| `social-preview.png` | GitHub social preview | `demos/scripts/render-social-preview.sh` |

The workbench stills are headless-Firefox captures of the live UI
serving the exam's fixture roadmap, exported straight from the
browser exam:

```bash
DW_UI_CAPTURE_DIR=/tmp/shots DW_UI_CAPTURE_PATTERN='*desktop*' \
  bash pmo-roadmap/tests/workbench-ui-smoke.sh
# workbench-board.png   <- board-home-desktop-light.png
# workbench-memory.png  <- memory-rich-desktop-light.png
```

The social preview is a 1280×640 card rendered from a self-contained
HTML template inside the script.

GitHub has no API for the social-preview setting: after regenerating
`social-preview.png`, upload it once by hand under
**Settings → General → Social preview**. The committed file stays the
source of truth for what is uploaded.

The framework icon lives at
[`pmo-roadmap/assets/delivery-workbench-icon.png`](../pmo-roadmap/assets/delivery-workbench-icon.png).
It is a one-off art asset, not script-regenerated: 400×400 pixel art
generated 2026-07-03 with the PixelLab MCP (`create_map_object`,
low top-down view, high detail, detailed shading, selective
outline; prompt: an isometric architect's delivery workbench — desk,
retro computer with a green checkmark on screen, stamped contract
papers, rubber stamp, checklist clipboard, coffee mug, and a cargo
cart carrying a sealed package). The uniform background PixelLab
produced was flood-filled to true transparency from the borders
(stdlib script, tolerance ±8 around RGB 157/156/157). Replacing the
icon means re-running `demos/scripts/render-social-preview.sh`,
which embeds it.
