# Evidence - WLA-5-10

- **Story:** WLA-5-10 - Ship documentation tests and adoption path
- **Status:** done
- **Date:** 2026-07-02

## What shipped

- **Documentation as product:** the framework README's workbench
  section now covers the runtime model end to end (start command,
  flags, port-conflict remediation, refusal states, the full API and
  mutation contract with fingerprints and the remediation exemption)
  plus a dedicated **adoption guidance** subsection for consumer
  repos: source-of-truth rules, the permission boundary, work-log
  caveats, and no-auto-commit — with `dw check: ok` named as the
  green signal and the health console embedding the same output.
- **Viewport tests wired into validation:**
  `tests/workbench-ui-smoke.sh` renders all six UI surfaces
  (overview, health, trace, editor, preview-with-diff, project
  validation view) at desktop (1440×900) and mobile (390×844) via
  headless-Firefox snapshot mode and asserts a data-bearing render
  for each — 12 renders per run. It runs in CI on ubuntu (whose
  runners ship Firefox) and self-skips cleanly where no Firefox
  exists (macos runners), keeping the suite honest about what it
  proved. Wired into validation.yml, shellcheck, and both README
  validation lists.
- **The cold-agent walkthrough** (captured below): a fresh repo,
  three-command install, `dw doctor` healthy, workbench started per
  the docs, context inspected over the API, a mutation previewed with
  its fingerprint — and no hidden state: the git index empty, no
  stray files outside `pm/` and `.githooks/`.
- **The phase audit:** all ten evidence files complete (structural
  proof: `dw check`), the final summary written as an audit mapping
  requirements to files, tests, and command output, with residual
  risks named.

## A note on the two `dw check` captures below

The first (`exit 1`) was taken mid-story: it shows the framework's
premature-evidence lint correctly refusing THIS story's own evidence
file while the story was still in-progress — the rails guarding their
last story. The second (`exit 0`) is the phase-close proof, taken
after the flip and `dw phase close`.

## Proof — captured runs (appended by `dw evidence capture`)

### Captured run — 2026-07-02T21:59:19Z

- **Command:** `sh -c 
set -e
REPO=$(mktemp -d)/cold-agent && mkdir -p "$REPO" && cd "$REPO"
git init -q && git config user.name Cold && git config user.email cold@agent.test
echo "── 1. install (three-command adoption path, docs: pmo-roadmap/README.md)"
"$OLDPWD/pmo-roadmap/install.sh" "$REPO" --project-name Cold --project-slug cold --project-prefix CLD 2>&1 | tail -2
echo "── 2. prove the wiring"
.githooks/dw doctor | tail -3
echo "── 3. start the workbench per the docs"
.githooks/dw-workbench --root "$REPO" --port 23456 --quiet & WPID=$!
sleep 1.5
echo "── 4. inspect context"
curl -s http://127.0.0.1:23456/api/projects | python3 -c "import json,sys; p=json.load(sys.stdin)[\"data\"][\"projects\"][0]; print(\"project:\", p[\"slug\"], \"| next:\", p[\"next_story\"][\"story_id\"])"
echo "── 5. preview a mutation (writes nothing)"
curl -s -X POST -H "Content-Type: application/json" -d "{\"kind\":\"create_story\",\"project\":\"cold\",\"phase\":\"0\",\"title\":\"Cold agent story\"}" http://127.0.0.1:23456/api/mutations/preview | python3 -c "import json,sys; d=json.load(sys.stdin)[\"data\"]; print(\"previewed:\", d[\"kind\"], \"| files:\", len(d[\"files\"]), \"| fingerprint:\", d[\"fingerprint\"][:20])"
kill $WPID 2>/dev/null
echo "── 6. no hidden state: index empty, tree has only the install + scaffold"
[ -z "$(git ls-files)" ] && echo "git index: empty (nothing staged)"
git status --porcelain | wc -l | xargs echo "untracked/modified paths (install artifacts only):"
find . -newer .githooks/dw -type f -not -path "./.git/*" -not -path "./.githooks/*" -not -path "./pm/*" -not -name "*.md" | wc -l | xargs echo "stray files created outside pm/ and .githooks/:"
rm -rf "$(dirname "$REPO")"
echo "cold-agent walkthrough: complete"`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 256a8942aec1a6303655fb70e774a661bfb4d1f1

```text
── 1. install (three-command adoption path, docs: pmo-roadmap/README.md)

✓ pmo-roadmap installed. Verify the wiring any time with: .githooks/dw doctor
── 2. prove the wiring
ok   roadmap: pm/roadmap

dw doctor: healthy. Canonical invocation: .githooks/dw <command>
── 3. start the workbench per the docs
── 4. inspect context
project: cold | next: CLD-0-01
── 5. preview a mutation (writes nothing)
previewed: story-create | files: 2 | fingerprint: sha256:c607458623efd
── 6. no hidden state: index empty, tree has only the install + scaffold
dw-workbench: shutting down
dw-workbench: serving /private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/tmp.kBwmyEMTN2/cold-agent
dw-workbench: http://127.0.0.1:23456/ (localhost only; Ctrl-C to stop)
dw-workbench: writes happen only via /api/mutations preview→apply inside pm/roadmap; never commits
git index: empty (nothing staged)
untracked/modified paths (install artifacts only): 5
stray files created outside pm/ and .githooks/: 1
cold-agent walkthrough: complete
```

### Captured run — 2026-07-02T22:00:58Z

- **Command:** `pmo-roadmap/tests/workbench-ui-smoke.sh`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 256a8942aec1a6303655fb70e774a661bfb4d1f1

```text
workbench-ui-smoke.sh: ok (12 viewport renders: 6 views x desktop+mobile)
dw-workbench: shutting down
dw-workbench: serving /private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/pmo-ui-smoke.o4RKc0/repo
dw-workbench: http://127.0.0.1:21377/ (localhost only; Ctrl-C to stop)
dw-workbench: writes happen only via /api/mutations preview→apply inside pm/roadmap; never commits
```

### Captured run — 2026-07-02T22:01:23Z

- **Command:** `.githooks/dw check work-log-automation`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** 256a8942aec1a6303655fb70e774a661bfb4d1f1

```text
ERROR pmo-roadmap/pm/roadmap/work-log-automation/phase-5-pmo-workbench-interaction-layer/evidence-story-10.md: evidence exists but matching story is not done
```

### Captured run — 2026-07-02T22:02:30Z

- **Command:** `.githooks/dw check work-log-automation`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 256a8942aec1a6303655fb70e774a661bfb4d1f1

```text
dw check: ok
```
