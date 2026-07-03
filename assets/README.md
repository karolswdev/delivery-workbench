# Repository assets

Every asset here is regenerated from current sources by a checked-in
script — never edited by hand.

| Asset | Used by | Regenerate with |
|---|---|---|
| `workbench-overview.png` | root README | `demos/scripts/capture-workbench-demo.sh` |
| `workbench-trace.png` | root README | `demos/scripts/capture-workbench-demo.sh` |
| `workbench-editor.png` | root README | `demos/scripts/capture-workbench-demo.sh` |
| `social-preview.png` | GitHub social preview | `demos/scripts/render-social-preview.sh` |

The workbench stills are headless-Firefox captures of the live UI
serving a fixture roadmap (the same capture session that produces
`demos/rendered/workbench-tour.gif`). The social preview is a
1280×640 card rendered from a self-contained HTML template inside the
script.

GitHub has no API for the social-preview setting: after regenerating
`social-preview.png`, upload it once by hand under
**Settings → General → Social preview**. The committed file stays the
source of truth for what is uploaded.

The framework icon lives at
[`pmo-roadmap/assets/delivery-workbench-icon.png`](../pmo-roadmap/assets/delivery-workbench-icon.png)
(original artwork, not generated).
