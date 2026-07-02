# Roadmap Builder — worked example (illustrative)

> Extracted from roadmap-builder.md §8 (WLA-6-06). This is the first
> real project that used the directory contract, kept as a concrete
> mapping reference. Names and paths are that project's own; nothing
> here is canonical.

## 8. Worked example — Pantrybot (illustrative)

> The section below is the first real project to use this contract. Treat
> it as a concrete reference for *how* to map a PMO plan onto the
> directory contract. Replace or delete when you have your own example.


The first project to use this contract is `pm/roadmap/pantrybot/`,
seeded from `pm/ROADMAP.md`. The mapping:

| `pm/ROADMAP.md` section | `pm/roadmap/pantrybot/` artifact |
|---|---|
| §0–§3 vision + convergence | `README.md` |
| §4 phase 0 | `phase-0-convergence-pm-lock/current-phase-status.md` + 2 stories |
| §4 phase 1 | `phase-1-raster-runtime-shell/current-phase-status.md` + 3 stories |
| §4 phase 2 | `phase-2-testflight-brand-pack/current-phase-status.md` + 6 stories |
| §4 phase 3 | `phase-3-pl-raster-catalog/current-phase-status.md` + 8 stories |
| §4 phase 4 | `phase-4-pre-testflight-polish/current-phase-status.md` + 4 stories |
| §4 phase 5 | not scaffolded yet (post-TestFlight, deferred) |
| §6 risks / §7 decisions | distributed across each phase's `current-phase-status.md` |
| §10 cadence log | per-phase `final-summary.md` files at close |

Story prefix: `PB`. Example IDs: `PB-0-01`, `PB-3-04`.

When the user approves Phase 0 of `pm/ROADMAP.md`, run this builder on
the Pantrybot project to produce the scaffold. The first story shipped
under the new contract should have its evidence file land in the same
PR as the story-status flip.

---

