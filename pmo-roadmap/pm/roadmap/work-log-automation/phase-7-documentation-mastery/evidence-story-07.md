# Evidence - WLA-7-07

- **Story:** WLA-7-07 - OSS release preparation and versioned release
- **Status:** done
- **Date:** 2026-07-02

## What shipped

- **CONTRIBUTING.md teaches the rails using the rails:** clone →
  `core.hooksPath` → healthy doctor → a real gated commit with a
  certified short-tier contract and the `PMO-Contract-Digest` trailer
  printed back. Both command blocks are `<!-- snippet: … -->`-marked
  with the new `prep=clone` fixture, so CI executes the contributor
  path as printed on every push (captured below) — the gate accepting
  the worked-example commit is literally part of the test suite. The
  guide also covers the story loop, canon pointers, house constraints
  (bash 3.2 / shellcheck 0.9 / python 3.9 / docs-as-code), and PR
  expectations.
- **CODE_OF_CONDUCT.md** (Contributor Covenant 2.1) and **issue/PR
  templates** that ask for evidence in framework vocabulary: the bug
  form requires verbatim reproduction commands and the failing gate
  banner; the feature form asks what captured run would prove the
  story done; the PR template asks for proof, gate-passed commits,
  and the story/evidence pair. GitHub's community profile reads
  **100% health** (captured; its `issue_template` flag only counts
  the legacy single-file template — the modern issue forms render in
  the chooser regardless).
- **CHANGELOG.md derives v1.5.0 from the seven phase final
  summaries**, each linked, with Phase 7 pointing at its folder.
- **The version is defined once and locked three ways:** new
  `dw --version` (both source and installed copies), plugin.json, and
  the CHANGELOG heading all read or are test-asserted against
  `dw_pmo.__version__` — three unit tests (98 total) fail on any
  disagreement (captured alignment run).
- **v1.5.0 annotated tag + GitHub release** with notes on `712beaa`,
  cut only after the run's four CI jobs went green (captured
  `gh release view`).
- **Repo metadata:** description in place, topics extended to ten
  (added claude-code, evidence, markdown), social preview committed
  under `assets/` with its documented one-time upload step.
- **Release hygiene bonus:** `dw doctor` caught this repo's own
  installed hook snapshot drifted from source; `update.sh .` resynced
  `.githooks` (commit `19d162a`) so the released state is what the
  repo itself runs.

## Honest notes

- The tag is **annotated, not GPG-signed** — no signing key is
  configured on this machine. The release commit and every commit
  around it carry the gate's own authenticity trail instead
  (certified contract digests in trailers, archives under
  `.git/pmo-contract-archive/`).
- `update.sh` against the source repo also scaffolded a root
  `pm/roadmap/` canon copy that shadowed `pmo-roadmap/pm/roadmap`
  and broke `dw` project discovery until removed — named as a
  residual risk in the phase final summary.
- The release existed before this evidence was committed (the tag
  points at `712beaa`, two commits before the flip) — unavoidable
  ordering, since the acceptance criterion requires capturing
  `gh release view` of a live release, and the capture must ship
  with the flip.

## Proof

### Captured run — 2026-07-03T02:49:17Z

- **Command:** `gh release view v1.5.0`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** f487fee41ad45dbbac55280c0d861f4c05142c74

```text
title:	Delivery Workbench v1.5.0
tag:	v1.5.0
draft:	false
prerelease:	false
immutable:	false
author:	karolswdev
created:	2026-07-03T02:49:00Z
published:	2026-07-03T02:49:02Z
url:	https://github.com/karolswdev/delivery-workbench/releases/tag/v1.5.0
--
First public release: evidence-first rails for agentic software delivery.

Delivery Workbench turns a Git repository into a self-verifying delivery system: work is planned as Markdown roadmaps, proven by paired evidence files with captured command runs, and gated at commit time by machine-verified contracts (v2: index-tree freshness, gate-decided ceremony tiers, trailer + archive audit trail). A localhost workbench serves explore/health/trace/guarded-edit views over the same core, optional consent-gated work logs record what shipped, and a managed agent surface (CLAUDE.md block + Claude Code plugin) lets agents operate the rails headlessly.

Everything here shipped through its own gate: the seven-phase roadmap, story by story, with evidence, contracts, trailers, and archives — inspect `pmo-roadmap/pm/roadmap/work-log-automation/` for the audit trail.

**Getting started**

```bash
pmo-roadmap/install.sh /path/to/project --skip-bootstrap
```

then see the [README](https://github.com/karolswdev/delivery-workbench#delivery-workbench) for the adoption path, and [CONTRIBUTING](https://github.com/karolswdev/delivery-workbench/blob/main/CONTRIBUTING.md) to send a change through the gate yourself.

**What's in v1.5.0** — the phase-by-phase story is in [CHANGELOG.md](https://github.com/karolswdev/delivery-workbench/blob/main/CHANGELOG.md): architecture contract (0), deterministic opt-in work-log MVP (1), summarizer hardening (2), local-first rollout (3), the `dw` maintenance CLI (4), the workbench interaction layer (5), agent-rails hardening + contract v2 (6), and documentation mastery — audited docs, plugin, reproducible assets, docs CI, this release (7).

Validation: 98 unit tests, nine shell suites, plugin validation, docs lint + quickstart snippet smoke, shellcheck, on ubuntu + macos + a python 3.9 floor job — all green at this tag.
```

### Captured run — 2026-07-03T02:49:18Z

- **Command:** `bash -c echo "── version single-source alignment ──"; .githooks/dw --version; pmo-roadmap/bin/dw --version; PYTHONPATH=pmo-roadmap/lib python3 -c "import dw_pmo; print(\"dw_pmo.__version__:\", dw_pmo.__version__)"; grep -o "\"version\": \"[^\"]*\"" plugin/.claude-plugin/plugin.json; grep -m1 "^## v" CHANGELOG.md; git describe --tags; echo "── the three test locks ──"; python3 pmo-roadmap/tests/dw-core-tests.py DwCoreTest.test_dw_version_flag_single_source DwCoreTest.test_changelog_release_matches_version DwCoreTest.test_plugin_version_single_source 2>&1 | tail -3`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** f487fee41ad45dbbac55280c0d861f4c05142c74

```text
── version single-source alignment ──
dw 1.5.0
dw 1.5.0
dw_pmo.__version__: 1.5.0
"version": "1.5.0"
## v1.5.0 — 2026-07-03
v1.5.0
── the three test locks ──
Ran 3 tests in 0.065s

OK
```

### Captured run — 2026-07-03T02:49:29Z

- **Command:** `pmo-roadmap/tests/docs-snippet-smoke.sh`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** f487fee41ad45dbbac55280c0d861f4c05142c74

```text
ok: CONTRIBUTING.md snippet 'contributor-setup' ran as printed
ok: CONTRIBUTING.md snippet 'contributor-gated-commit' ran as printed
ok: pmo-roadmap/README.md snippet 'install' ran as printed
ok: pmo-roadmap/README.md snippet 'update' ran as printed
ok: pmo-roadmap/README.md snippet 'new-project' ran as printed
ok: pmo-roadmap/README.md snippet 'adopt-three-step' ran as printed
ok: pmo-roadmap/README.md snippet 'intake-no-prompt' ran as printed
ok: pmo-roadmap/README.md snippet 'adopt-close-loop' ran as printed
docs-lint snippets: ok
docs-snippet-smoke.sh: ok
```

### Captured run — 2026-07-03T02:49:35Z

- **Command:** `gh api repos/karolswdev/delivery-workbench/community/profile --jq {health_percentage, code_of_conduct: .files.code_of_conduct.name, contributing: (.files.contributing != null), pull_request_template: (.files.pull_request_template != null), license: .files.license.spdx_id}`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** f487fee41ad45dbbac55280c0d861f4c05142c74

```text
{"code_of_conduct":"Contributor Covenant","contributing":true,"health_percentage":100,"license":"MIT","pull_request_template":true}
```

### Captured run — 2026-07-03T02:49:48Z

- **Command:** `bash -c set -e; python3 pmo-roadmap/tests/dw-core-tests.py 2>&1 | tail -3; pmo-roadmap/tests/canon-lint.sh; pmo-roadmap/tests/docs-lint.sh; pmo-roadmap/tests/docs-snippet-smoke.sh >/dev/null && echo docs-snippet-smoke.sh: ok; pmo-roadmap/tests/adoption-discovery.sh >/dev/null && echo adoption-discovery.sh: ok; pmo-roadmap/tests/agent-surface.sh >/dev/null && echo agent-surface.sh: ok; pmo-roadmap/tests/gate-parity.sh >/dev/null && echo gate-parity.sh: ok; pmo-roadmap/tests/roadmap-cli.sh >/dev/null && echo roadmap-cli.sh: ok; pmo-roadmap/tests/work-log-mvp.sh >/dev/null 2>&1 && echo work-log-mvp.sh: ok; pmo-roadmap/tests/workbench-explorer.sh >/dev/null 2>&1 && echo workbench-explorer.sh: ok; pmo-roadmap/tests/workbench-ui-smoke.sh; pmo-roadmap/tests/plugin-validate.sh >/dev/null && echo plugin-validate.sh: ok; shellcheck -e SC2317 pmo-roadmap/install.sh pmo-roadmap/update.sh pmo-roadmap/hooks/* pmo-roadmap/bin/work-log-read pmo-roadmap/bin/work-log-summarize pmo-roadmap/bootstrap/*.sh pmo-roadmap/tests/*.sh demos/scripts/*.sh && echo shellcheck: ok; echo "CI at release commit: run 28635033969 all four jobs success (712beaa)"`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** f487fee41ad45dbbac55280c0d861f4c05142c74

```text
Ran 98 tests in 6.952s

OK
canon-lint.sh: ok
docs-lint: ok (141 markdown files)
docs-lint.sh: ok (0s)
docs-snippet-smoke.sh: ok
adoption-discovery.sh: ok
agent-surface.sh: ok
gate-parity.sh: ok
roadmap-cli.sh: ok
work-log-mvp.sh: ok
workbench-explorer.sh: ok
workbench-ui-smoke.sh: ok (12 viewport renders: 6 views x desktop+mobile)
dw-workbench: shutting down
dw-workbench: serving /private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/pmo-ui-smoke.EFQbnk/repo
dw-workbench: http://127.0.0.1:21517/ (localhost only; Ctrl-C to stop)
dw-workbench: writes happen only via /api/mutations preview→apply inside pm/roadmap; never commits
plugin-validate.sh: ok
shellcheck: ok
CI at release commit: run 28635033969 all four jobs success (712beaa)
```

### Captured run — 2026-07-03T02:53:48Z

- **Command:** `bash -c set -e; echo "── phase 7 closed state ──"; grep -m1 "Current phase" pmo-roadmap/pm/roadmap/work-log-automation/README.md; head -4 pmo-roadmap/pm/roadmap/work-log-automation/phase-7-documentation-mastery/final-summary.md; .githooks/dw check work-log-automation; .githooks/dw next work-log-automation || [ $? -eq 2 ] && echo "dw next exit 2: nothing actionable — roadmap fully shipped"`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** cd57a3a6b69ff527267457026172a137910cd89c

```text
── phase 7 closed state ──
**Current phase:** n/a.
# Phase 7 Final Summary

**Status:** complete.
**Date:** 2026-07-02.
dw check: ok
dw next: nothing actionable (no in-progress, ready, or backlog stories)
dw next exit 2: nothing actionable — roadmap fully shipped
```
