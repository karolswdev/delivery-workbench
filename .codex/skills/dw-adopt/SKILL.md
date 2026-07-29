---
name: dw-adopt
description: Drive Delivery Workbench adoption for this repository (intake → discovery → roadmap).
---

Drive the Delivery Workbench adoption flow for this repository. Ask
the user for anything you cannot infer; do not fabricate intent.

## Delivery task

Establish the repository's delivery scope, current work, and first safe next
step. Report what will change before creating roadmap files.

## Technical details

1. Verify the install: `.githooks/dw doctor`. If the framework is not
   installed, run `<framework>/pmo-roadmap/install.sh <this-repo> --skip-bootstrap`
   first (ask the user where the framework checkout lives).
2. Capture intent — run the session intake (interactive when the user
   is present, flags otherwise):
   `<framework>/pmo-roadmap/bootstrap/session-intake.sh <this-repo> --project-name "…" --project-slug <slug> --project-prefix <PFX>`
3. Run adoption discovery:
   `<framework>/pmo-roadmap/bootstrap/adopt-project.sh <this-repo> --project-name "…" --project-slug <slug> --project-prefix <PFX> --require-intake`
   Read the generated `pm/roadmap/<slug>/adoption/adoption-discovery.md`.
4. Turn the report's proposed phases and first stories into a real
   roadmap with `.githooks/dw phase create` and
   `.githooks/dw story create` (show the user the plan first).
5. Finish with `.githooks/dw doctor` and `.githooks/dw check`, and
   report the next actionable story from `.githooks/dw next`.
