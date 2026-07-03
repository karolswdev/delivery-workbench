# Evidence - WLA-7-06

- **Story:** WLA-7-06 - Wire documentation CI checks
- **Status:** done
- **Date:** 2026-07-02

## What shipped

- **The checker** (`lib/dw_pmo/docslint.py`, stdlib only): every
  internal link, `#anchor`, and image in every Markdown file — all
  135, roadmap tree included — must resolve; anchors are matched with
  GitHub slug rules (markup stripped, punctuation dropped, duplicate
  headings suffixed `-1/-2`, headings inside code fences excluded);
  images must carry alt text (locking in WLA-7-05's audit as a CI
  rule); links inside code fences/spans and HTML comments are not
  linted; external URLs are deliberately unchecked (liveness polling
  is flaky in CI — per story scope). Escape hatches:
  `docs-lint: ignore` (line) and `docs-lint: skip-file`. Findings are
  greppable `ERROR <file>:<line>: <issue>` lines, exit 1.
- **The snippet smoke:** quickstart blocks marked
  `<!-- snippet: name [prep=…] [cwd=…] -->` are extracted and
  executed as printed — placeholder paths substituted, one throwaway
  fixture per snippet built by re-running the documented earlier
  steps (repo → installed → intaken → report ladder). Six framework
  README quickstarts are marked and pass: install, update,
  new-project bootstrap, the adopt three-step, no-prompt intake, and
  the adopt close-the-loop (preview → `--apply` → doctor). A marker
  with no bash fence is itself an error, and zero discovered snippets
  fails the smoke — coverage cannot silently vanish.
- **Deliberately unmarked:** blocks that spawn an agent
  (`--agent claude`), start a server (`dw-workbench`), depend on
  `~/.work` state, or run `npm test` as an illustrative placeholder —
  and the root README validation block, which would re-run the whole
  battery CI already runs step-by-step.
- **Suites and wiring:** `tests/docs-lint.sh` (self-checks the
  checker against a four-defect fixture before the real run, enforces
  the 30-second budget — actual: <1s) and
  `tests/docs-snippet-smoke.sh` (~4s), both in validation.yml on both
  OS legs alongside canon-lint, both shellchecked, both in the root
  README validation list; 10 new unit tests in dw-core-tests.py
  (96 total) cover slug rules, every defect class, pragmas,
  code-span exclusion, and snippet extraction.
- **Docs:** the framework README's Maintenance section teaches the
  marker convention and what to do when you edit a marked block.

## Honest notes

- The kill-test capture below proves both suites die on real drift:
  a dead link appended to the root README fails docs-lint with the
  greppable ERROR line, and a `--no-such-flag` planted in a marked
  quickstart fails the smoke naming the snippet — then both files are
  restored and both suites run green again, all inside the one
  captured run.
- All six marked quickstarts passed on the first run — WLA-7-02's
  verbatim-verification work held up; this story just made that state
  permanent.
- Existing docs passed the link/anchor/image lint with zero findings
  and zero pragma annotations needed.

## Proof

### Captured run — 2026-07-03T02:18:46Z

- **Command:** `pmo-roadmap/tests/docs-lint.sh`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 20ba604fb506ee433362498eb046d754690477bc

```text
docs-lint: ok (135 markdown files)
docs-lint.sh: ok (0s)
```

### Captured run — 2026-07-03T02:18:46Z

- **Command:** `pmo-roadmap/tests/docs-snippet-smoke.sh`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 20ba604fb506ee433362498eb046d754690477bc

```text
ok: pmo-roadmap/README.md snippet 'install' ran as printed
ok: pmo-roadmap/README.md snippet 'update' ran as printed
ok: pmo-roadmap/README.md snippet 'new-project' ran as printed
ok: pmo-roadmap/README.md snippet 'adopt-three-step' ran as printed
ok: pmo-roadmap/README.md snippet 'intake-no-prompt' ran as printed
ok: pmo-roadmap/README.md snippet 'adopt-close-loop' ran as printed
docs-lint snippets: ok
docs-snippet-smoke.sh: ok
```

### Captured run — 2026-07-03T02:19:03Z

- **Command:** `bash -c set -u; echo "── kill test 1: broken link in a real doc must fail CI ──"; printf "\n[deliberately dead](./no-such-file.md)\n" >> README.md; if pmo-roadmap/tests/docs-lint.sh 2>&1 | grep "^ERROR README.md"; then echo "docs-lint DIED as required"; else echo "docs-lint FAILED TO DIE"; sed -i "" -e "\$d" -e "\$d" README.md; exit 1; fi; sed -i "" -e "\$d" -e "\$d" README.md; echo "── kill test 2: quickstart drift must fail CI ──"; sed -i "" "s|^./install.sh /path/to/target-project --skip-bootstrap\$|./install.sh /path/to/target-project --skip-bootstrap --no-such-flag|" pmo-roadmap/README.md; if pmo-roadmap/tests/docs-snippet-smoke.sh 2>&1 | grep "^ERROR pmo-roadmap/README.md"; then echo "snippet smoke DIED as required"; else echo "snippet smoke FAILED TO DIE"; sed -i "" "s| --no-such-flag\$||" pmo-roadmap/README.md; exit 1; fi; sed -i "" "s| --no-such-flag\$||" pmo-roadmap/README.md; echo "── restored: both suites green again ──"; pmo-roadmap/tests/docs-lint.sh && pmo-roadmap/tests/docs-snippet-smoke.sh >/dev/null && echo "docs-snippet-smoke.sh: ok"`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 20ba604fb506ee433362498eb046d754690477bc

```text
── kill test 1: broken link in a real doc must fail CI ──
ERROR README.md:190: broken link: ./no-such-file.md
docs-lint DIED as required
── kill test 2: quickstart drift must fail CI ──
ERROR pmo-roadmap/README.md: snippet 'adopt-three-step' exited 1
snippet smoke DIED as required
── restored: both suites green again ──
docs-lint: ok (136 markdown files)
docs-lint.sh: ok (0s)
docs-snippet-smoke.sh: ok
```

### Captured run — 2026-07-03T02:19:32Z

- **Command:** `bash -c set -e; python3 pmo-roadmap/tests/dw-core-tests.py 2>&1 | tail -3; pmo-roadmap/tests/canon-lint.sh; pmo-roadmap/tests/docs-lint.sh; pmo-roadmap/tests/docs-snippet-smoke.sh >/dev/null && echo docs-snippet-smoke.sh: ok; pmo-roadmap/tests/adoption-discovery.sh >/dev/null && echo adoption-discovery.sh: ok; pmo-roadmap/tests/agent-surface.sh >/dev/null && echo agent-surface.sh: ok; pmo-roadmap/tests/gate-parity.sh >/dev/null && echo gate-parity.sh: ok; pmo-roadmap/tests/roadmap-cli.sh >/dev/null && echo roadmap-cli.sh: ok; pmo-roadmap/tests/work-log-mvp.sh >/dev/null 2>&1 && echo work-log-mvp.sh: ok; pmo-roadmap/tests/workbench-explorer.sh >/dev/null 2>&1 && echo workbench-explorer.sh: ok; pmo-roadmap/tests/workbench-ui-smoke.sh; pmo-roadmap/tests/plugin-validate.sh >/dev/null && echo plugin-validate.sh: ok; shellcheck -e SC2317 pmo-roadmap/install.sh pmo-roadmap/update.sh pmo-roadmap/hooks/* pmo-roadmap/bin/work-log-read pmo-roadmap/bin/work-log-summarize pmo-roadmap/bootstrap/*.sh pmo-roadmap/tests/*.sh demos/scripts/*.sh && echo shellcheck: ok`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 20ba604fb506ee433362498eb046d754690477bc

```text
Ran 96 tests in 7.317s

OK
canon-lint.sh: ok
docs-lint: ok (136 markdown files)
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
dw-workbench: serving /private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/pmo-ui-smoke.vzLDeK/repo
dw-workbench: http://127.0.0.1:22829/ (localhost only; Ctrl-C to stop)
dw-workbench: writes happen only via /api/mutations preview→apply inside pm/roadmap; never commits
plugin-validate.sh: ok
shellcheck: ok
```
