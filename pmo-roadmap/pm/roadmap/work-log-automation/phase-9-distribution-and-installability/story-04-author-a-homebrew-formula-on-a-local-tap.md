# WLA-9-04 - Author a Homebrew formula on a local tap

- **Project:** work-log-automation
- **Phase:** 9
- **Status:** done
- **Depends on:** WLA-9-02
- **Unblocks:** WLA-9-05
- **Owner:** unassigned

## Problem

For macOS developers — the platform this framework is developed on —
`brew install` is the expected install verb. A formula proven
against a local tap gives the release everything except the final
`git push` of a tap repository, which stays a user decision.

## Scope

- **In:** A formula `Formula/delivery-workbench.rb` tracked in this
  repository (source of truth for the future public tap), building
  from the local sdist/wheel or repo archive per the design
  contract, installing the same entry-point surface as the pipx
  package. Proof on this machine: create a throwaway local tap
  (`brew tap-new` + copy the formula), `brew install --formula` from
  it (or `brew install --build-from-source <path>` if tap-new is
  unavailable offline), then `dw --version` matches
  `dw_pmo.__version__` and the packaged bootstrap adopts a fixture
  repo to doctor-green. `brew audit --formula` findings addressed or
  explicitly waived with reasons. Documentation: an "Install"
  section in the README covering pipx and brew, marked honestly as
  "from a local build until the tap/PyPI publication lands".
- **Out:** Publishing a `homebrew-tap` repository (new public repo —
  user decision), bottling, Linuxbrew validation.

## Acceptance criteria

- [ ] `brew install` from the local tap/formula succeeds on this
  machine; `dw --version` agrees with the single version source.
- [ ] The brew-installed bootstrap adopts a fixture repo to
  doctor-green, and the defer-to-repo rule holds there too.
- [ ] `brew audit` is clean or waivers are recorded in the story.
- [ ] README "Install" section exists and passes docs-lint.

## Test plan

- **Unit:** n/a.
- **Integration:** scripted where brew allows
  (`tests/brew-formula-smoke.sh`, skipping gracefully when brew is
  absent — CI's ubuntu leg must not fail).
- **Manual / device:** the local-tap install run, captured as
  evidence.

## Notes / open questions

- Formula strategy (python virtualenv formula vs. shelling to pipx)
  follows the design contract; virtualenv_install_with_resources
  with zero resources (stdlib-only) should keep it trivial.
- Untar-from-local-path formulas need a `file://` URL with a sha256
  of the built artifact — the smoke script computes it at run time.
