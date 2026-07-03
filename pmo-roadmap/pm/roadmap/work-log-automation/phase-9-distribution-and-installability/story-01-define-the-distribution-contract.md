# WLA-9-01 - Define the distribution contract

- **Project:** work-log-automation
- **Phase:** 9
- **Status:** backlog
- **Depends on:** none
- **Unblocks:** WLA-9-02
- **Owner:** unassigned

## Problem

Today the only way to get Delivery Workbench is to clone this
repository and run `pmo-roadmap/install.sh` from the checkout. That
conflates two different things: the framework's *distribution* (how
the bits reach a machine) and its *installation model* (vendored
per-repo rails under `.githooks/`, which is architectural — the gate
and CLI must travel with the repo they gate). Before packaging
anything, the boundary must be explicit, or a global `dw` will drift
from the per-repo snapshots and reintroduce exactly the two-sources
-of-truth problem Phase 6 killed.

## Scope

- **In:** A design document `docs/distribution.md` that decides:
  (a) the unit of distribution — the bootstrap vehicle (install /
  update / adopt entry points plus the payload they vendor), never a
  replacement for the per-repo rails; (b) the global-vs-repo `dw`
  relationship (a globally installed `dw` inside an adopted repo
  must defer to `.githooks/dw` so the gating version is always the
  vendored one); (c) how the payload (hooks, lib, templates,
  workbench assets) ships inside a Python package and how
  `install.sh`/`update.sh` locate it when running from an installed
  package vs a checkout; (d) version and upgrade policy —
  `dw_pmo.__version__` stays the single source, upgrades flow
  source → package → per-repo snapshot via the update path; (e)
  channel list for v1 (pipx/pip from a local build, Homebrew via
  local tap) and what is explicitly out (PyPI/tap publication —
  requires credentials and a public artifact host; curl|sh).
- **Out:** Implementation (WLA-9-02..04), publication to any
  registry, Windows support beyond what the scripts already have.

## Acceptance criteria

- [ ] `docs/distribution.md` exists, states the vendored-rails
  invariant and the defer-to-repo rule, and specifies the package
  layout, entry points, payload-location mechanism, and upgrade
  flow.
- [ ] The environment constraints are recorded (pipx and brew
  available; `build` module absent, so local builds use
  `--no-build-isolation` or `pipx run build` — verified on this
  machine).
- [ ] Decisions and their rationale are mirrored in the phase status
  file; docs-lint passes.

## Test plan

- **Unit:** n/a (design story).
- **Integration:** `pmo-roadmap/tests/docs-lint.sh`.
- **Manual / device:** cross-check the payload inventory against
  what `install.sh` actually copies today.

## Notes / open questions

- Package name: `delivery-workbench` (import package stays
  `dw_pmo`). Console scripts must not collide with the repo-local
  `dw` semantics — the defer rule resolves this.
- The plugin (`plugin/`) ships via Claude Code marketplace, not this
  package; the design doc should say so explicitly.
