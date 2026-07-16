# Delivery Workbench — Distribution Contract

How Delivery Workbench reaches a machine that never cloned this
repository, without weakening the architecture that makes it
trustworthy. This is the design contract for WLA-9-02 (packaging),
WLA-9-03 (upgrades), and WLA-9-04 (Homebrew); the invariants below
are what those stories are tested against.

## The invariant distribution must not break

**Per-repo vendored rails are the only gating authority.** Every
adopted repository carries its own copy of the hooks and the
`dw_pmo` core under `.githooks/`, pinned by `core.hooksPath`. The
gate that certifies a commit is the gate that travels with that
repo's history — reproducible years later from the repo alone,
immune to whatever version happens to be installed globally that
day. Phase 6 spent an entire hardening pass making sure there is no
second implementation of any rule; a global CLI that gated repos
directly would resurrect exactly that split.

Therefore: **the unit of distribution is the bootstrap vehicle, not
the gate.** What ships globally is the ability to install, update,
and adopt — plus a convenience launcher. What gates commits is
always the vendored copy.

## The defer-to-repo rule

A globally installed `dw`, invoked inside a repository that has
`.githooks/dw`, must `exec` that vendored copy with the same
arguments — unconditionally, even (especially) when the global
version is newer. Version honesty over convenience: the output a
user sees must come from the rails their commits actually pass
through. The global CLI acts in its own right only:

- outside any adopted repository (bootstrap verbs, `--version`,
  help), or
- for the bootstrap verbs themselves (`install`, `update`,
  `adopt-project`, `new-project`, `intake`), which by definition
  operate on a target repo from outside its rails.

Staleness becomes visible, never silently "fixed": when the global
launcher defers to older vendored rails it may print a one-line
notice to stderr naming both versions and the upgrade command
(`dw update <path>`), but the vendored copy still runs.

## Package layout

- **Distribution name:** `delivery-workbench` (PyPI-style name;
  publication itself is out of scope this phase).
- **Import package:** `dw_pmo`, sourced from `pmo-roadmap/lib/` —
  the same files the repo vendors; no fork, no shim package.
- **Payload:** everything `install.sh` copies ships as package data
  in a `dw_pmo/_payload/` directory that mirrors the `pmo-roadmap/`
  source layout exactly:

  | Payload path | Vendored to (by install.sh) |
  |---|---|
  | `hooks/pre-commit`, `hooks/commit-msg`, `hooks/post-commit` | `.githooks/` (chmod +x) |
  | `bin/dw`, `bin/dw-workbench`, `bin/dw-mcp`, `bin/work-log-summarize`, `bin/work-log-read` | `.githooks/` |
  | `lib/dw_pmo/` | `.githooks/dw_pmo/` |
  | `workbench/` (local web UI assets) | `.githooks/workbench/` |
  | `templates/roadmap-builder.md`, `templates/PMO-CONTRACT.md` | `pm/roadmap/` |
  | `agent/dw-*.md` | `.claude/commands/` |
  | `install.sh`, `update.sh`, `bootstrap/*.sh` | (executed, not vendored) |

  Because the payload mirrors the source layout and the shell
  scripts locate everything relative to `SOURCE_DIR` (their own
  directory, resolved physically), `install.sh` and `update.sh` run
  unmodified from inside the installed package — the packaged and
  checkout paths are the same code taking the same relative turns.
- **Entry points:** a single console script, `dw`, bound to a small
  launcher module (`dw_pmo.launcher:main`) that implements the
  defer-to-repo rule, dispatches the bootstrap verbs to the payload
  scripts, and otherwise delegates to the packaged `bin/dw` for the
  roadmap commands (useful outside adopted repos, e.g. `dw
  --version`). No second console script: `dw-workbench` and the
  work-log helpers are repo-scoped tools that arrive via vendoring.
- **Runtime dependencies: none.** The stdlib-only, python ≥ 3.9
  floor is a distribution feature; `install_requires` stays empty
  and CI's `python-floor` job remains the proof.
- **What does not ship here:** the Claude Code plugin (`plugin/`)
  distributes through the plugin marketplace; the roadmap tree,
  docs, demos, and CI of this repository are not payload.

## Version and upgrade flow

`dw_pmo.__version__` remains the single version source. Surfaces
that repeat it — `dw --version`, the plugin manifest, CHANGELOG,
`pyproject.toml`, the Homebrew formula — are held equal by the
version-parity unit test, which grows with each new surface.

Upgrades flow one direction: **source → package → per-repo
snapshot.** A new release produces new artifacts; `dw update
<repo>` (the packaged `update.sh`) refreshes the vendored rails;
the repo's own gate then certifies the refresh commit like any
other change. Staleness is content-based, not version-string-based —
`dw update <repo> --check` diffs the vendored core, CLI, and
pre-commit hook against the distributing source (exit 0 fresh / 3
stale) and prints both versions as context, because version strings
match between releases while code moves. Consumer roadmap content (`pm/roadmap/<slug>/`),
`pre-commit.config`, and `pre-commit.local` are never touched by
updates — that contract predates this phase and WLA-9-03 proves it
against real v1.5.0 rails.

## Channels (v1)

1. **pipx / pip** — canonical build: `pipx run build` (sdist +
   wheel); canonical install: `pipx install <artifact-or-source-dir>`.
   Network at build time may fetch the build backend only; runtime
   installs nothing. Verified on this machine: pipx 1.11.1, brew
   python 3.14, PyPI reachable; the system interpreter has no
   `setuptools`, so builds rely on isolation (or `pipx run build`)
   rather than `--no-build-isolation`.
2. **Homebrew** — a formula tracked in this repository
   (`Formula/delivery-workbench.rb`) as the source of truth for a
   future public tap, proven locally via a throwaway tap and a
   `file://` artifact URL with computed sha256 (WLA-9-04).

**Explicitly out:** `curl | sh` installers (unauditable by design,
contrary to the framework's evidence-first posture), OS packages,
and bottles.

Publication status (updated post-phase, 2026-07-03): the public tap
(`karolswdev/homebrew-tap`) is live and the GitHub Release serves
the artifacts the formula names. PyPI publishing is wired as
`.github/workflows/release.yml` using Trusted Publishing (OIDC — no
token stored in the repo): it re-verifies the history, re-runs the
package smoke, builds, and publishes on every published GitHub
Release. It activates once the one-time publisher registration
exists on pypi.org (project `delivery-workbench` → Publishing → add
GitHub publisher: owner `karolswdev`, repo `delivery-workbench`,
workflow `release.yml`, environment `pipit` — yes, `pipit`: the
registered publisher's environment field caught an autocorrect typo
and the workflow matches it deliberately; both sides must agree for
the OIDC exchange).

## Cutting a release

The ritual, as run for v1.6.0 through v1.8.0 (a release story in the
roadmap carries it; see WLA-11-04 for the worked example):

1. Bump `dw_pmo.__version__`; the plugin manifest and the formula
   url follow it (reset the formula sha256 to the zero placeholder).
   `pyproject.toml` is dynamic and needs no edit. Add the CHANGELOG
   section linking the phase final summary.
2. Refresh the vendored snapshot (`pmo-roadmap/install.sh .
   --skip-bootstrap`), then run the full battery and both
   distribution smokes at the new version. The parity tests fail if
   any surface lags.
3. Ship the release story through the gate, close the phase, create
   the annotated tag, push main and the tag.
4. Build sdist and wheel, publish the GitHub Release with both
   artifacts and their sha256 in the notes. The release event
   triggers `release.yml`, which re-verifies history, re-runs the
   package smoke, and publishes to PyPI via trusted publishing with
   no manual step.
5. Download the served wheel, confirm its sha256, stamp it into
   `Formula/delivery-workbench.rb`, commit through the gate, push.
6. Mirror the formula into the tap repository
   (https://github.com/karolswdev/homebrew-tap, `Formula/` directory,
   one commit per release) and push it. `brew upgrade
   delivery-workbench` then serves the new version.
7. Confirm: PyPI JSON lists the version (CDN can lag a minute), a
   cold `pip install` from a neutral directory reports it, and CI is
   green on the release head.

## Proof obligations

- `tests/package-smoke.sh` — build artifacts, `pipx install` from
  the local artifact, bootstrap a fixture repo to doctor-green with
  no checkout present, invoke both packaged status and deliberate-step exit
  exams, and prove the defer-to-repo rule (WLA-9-02, WLA-22-05, WLA-23-05).
- `tests/guided-status-loop.sh` — install/update a fresh consumer and
  assert each byte-equal CLI/MCP/HTTP recommendation from initial work
  through evidence, manual certification, live gate pass, trailers,
  archived contract, verified commit, and the next clean story.
- `tests/deliberate-step-loop.sh` — install/update from that same wheel,
  compare every fresh CLI/MCP/HTTP step lease, and apply each real transition
  separately using only project+token. A workspace change invalidates an old
  token while `continue-story` stays the action; all three adapters report
  `started: false` with zero new events. Certification and commit refuse on
  every step surface before the fixture operator performs them manually.
- `tests/upgrade-path.sh` — adopt from the real `v1.5.0` tag,
  upgrade, byte-compare protected content, `dw verify` over the
  mixed-version history, gated commit after refresh (WLA-9-03).
- `tests/brew-formula-smoke.sh` — local-tap install, version truth,
  graceful skip where brew is absent (WLA-9-04).
- Version parity — the existing unit test extended to
  `pyproject.toml` and the formula (WLA-9-02/04/05).
