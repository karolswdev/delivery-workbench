# Phase 9 - Distribution and Installability

**Last updated:** 2026-07-03.

## Goal

Make Delivery Workbench installable without cloning this repository: a distribution design contract, a pipx-installable package exposing the bootstrap commands, a proven consumer upgrade path from v1.5.0 rails, a Homebrew formula served from a local tap, and a v1.6.0 release that ships it all.

## Scope

- **In:** A distribution design contract (`docs/distribution.md`)
  that preserves the vendored-rails architecture; `pyproject.toml`
  packaging with a proven local `pipx install` and a global `dw`
  that defers to repo-local rails; an end-to-end upgrade proof from
  real v1.5.0 rails to current (content untouched, staleness
  visible); a Homebrew formula tracked in-repo and proven from a
  local tap; a v1.6.0 release commit with version parity enforced
  across every surface and an annotated local tag.
- **Out:** PyPI publication and public tap creation (credentials
  and new public repos — user decisions; the artifacts make each a
  one-command follow-up), pushing commits or tags, bottling,
  Windows-native installers, changes to the per-repo gate
  architecture.

## Exit criteria (evidence required)

- [ ] `docs/distribution.md` locks the vendored-rails invariant, the
  defer-to-repo rule, package layout, and upgrade flow.
- [ ] `pipx install` from a locally built artifact adopts a fixture
  repo to doctor-green with no framework checkout present, and the
  global `dw` provably defers to `.githooks/dw` inside adopted
  repos.
- [ ] A repo adopted from the real v1.5.0 tag upgrades to current
  rails with roadmap content and config byte-untouched, gains
  `dw verify`, and ships a gated commit afterward.
- [ ] `brew install` from a local tap yields a working, version-true
  toolchain on this machine.
- [ ] v1.6.0: every version surface agrees under test, CHANGELOG
  covers phases 8-9, the annotated tag exists locally, and
  `dw verify --all` passes at the release commit.

## Story status

| ID | Story | Status | Story file | Evidence |
|---|---|---|---|---|
| WLA-9-01 | Define the distribution contract | done | [story-01-define-the-distribution-contract](./story-01-define-the-distribution-contract.md) | [evidence-story-01](./evidence-story-01.md) |
| WLA-9-02 | Package the framework for pipx | done | [story-02-package-the-framework-for-pipx](./story-02-package-the-framework-for-pipx.md) | [evidence-story-02](./evidence-story-02.md) |
| WLA-9-03 | Prove the consumer upgrade path | done | [story-03-prove-the-consumer-upgrade-path](./story-03-prove-the-consumer-upgrade-path.md) | [evidence-story-03](./evidence-story-03.md) |
| WLA-9-04 | Author a Homebrew formula on a local tap | done | [story-04-author-a-homebrew-formula-on-a-local-tap](./story-04-author-a-homebrew-formula-on-a-local-tap.md) | [evidence-story-04](./evidence-story-04.md) |
| WLA-9-05 | Release v1.6.0 | done | [story-05-release-v1-6-0](./story-05-release-v1-6-0.md) | [evidence-story-05](./evidence-story-05.md) |

## Where we are

All five stories shipped and the phase is closed: the framework is
installable without cloning (pipx + Homebrew from a local tap), the
upgrade path is proven from real v1.5.0 rails, and v1.6.0 is tagged
with every version surface under parity tests. Publication (PyPI,
public tap, pushes) remains a set of one-command user follow-ups.

## Active risks

| Risk | Likelihood | Mitigation | Stop signal |
|---|---|---|---|
| Global `dw` drifts from per-repo snapshots, resurrecting two sources of truth | medium | Defer-to-repo rule is a design invariant with a test proving the vendored copy wins | Any test or doc suggests running the global CLI against a repo's gate |
| Build tooling assumes network (build isolation pulls setuptools) | high on this machine | Design doc fixes the offline build recipe; package-smoke must pass without network | Smoke test needs a download to pass |
| Homebrew formula audit demands artifact hosting we don't have yet | medium | Local tap + file:// URL with computed sha256; audit waivers recorded | Formula cannot install without a public URL |
| update.sh silently misses files added since v1.5.0 | medium | WLA-9-03 upgrades from the real tag and diffs the refreshed rails against source | Upgraded fixture lacks verify.py or stamps no PMO-Bundle |

## Decisions made (this phase)

- 2026-07-03 - Phase scaffolded with `dw phase create` - keeps roadmap structure consistent - CLI.
- 2026-07-03 - The unit of distribution is the bootstrap vehicle; per-repo vendored rails remain the only gating authority - preserves the Phase 6 single-source-of-truth invariant - locked in WLA-9-01 (`docs/distribution.md`).
- 2026-07-03 - Publication (PyPI, public tap, pushes) stays out of scope - requires credentials and public artifacts; every publication becomes a one-command user action after this phase - constraint.
- 2026-07-03 - Defer-to-repo rule: a global `dw` inside an adopted repo execs `.githooks/dw` unconditionally, staleness reported on stderr but never silently "fixed" - version honesty over convenience - WLA-9-01.
- 2026-07-03 - Payload ships as `dw_pmo/_payload/` mirroring the `pmo-roadmap/` layout so install.sh/update.sh run unmodified from checkout or package - one script, two homes, zero forks - WLA-9-01.
- 2026-07-03 - Single console script `dw` via a launcher module; workbench and work-log tools arrive only by vendoring - keeps the global surface minimal - WLA-9-01.
- 2026-07-03 - Builds may fetch the build backend (network verified available; system python lacks setuptools); runtime stays stdlib-only with empty install_requires - WLA-9-01.
- 2026-07-03 - curl|sh installers declined - unauditable by design, contrary to evidence-first posture - WLA-9-01.

## Decisions deferred

- PyPI project registration and public tap repository - trigger: user decides to publish v1.6.0 - default is local artifacts only.
- Bottles / prebuilt binaries - trigger: measurable install friction from source builds - default is none.
