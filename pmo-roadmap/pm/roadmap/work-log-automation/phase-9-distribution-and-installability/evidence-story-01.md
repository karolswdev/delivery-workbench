# Evidence - WLA-9-01

- **Story:** WLA-9-01 - Define the distribution contract
- **Status:** done
- **Date:** 2026-07-03

## Proof

Deliverable: `docs/distribution.md` — the distribution contract. It
locks the invariant (per-repo vendored rails are the only gating
authority; the unit of distribution is the bootstrap vehicle), the
defer-to-repo rule (global `dw` execs `.githooks/dw` unconditionally
inside adopted repos, staleness reported but never silently fixed),
the package layout (`delivery-workbench` distribution, `dw_pmo`
import package, payload as `dw_pmo/_payload/` mirroring the source
layout so install.sh/update.sh run unmodified from either home), a
single `dw` console script, the source → package → snapshot upgrade
flow under the existing version-parity regime, and the v1 channels
(pipx + Homebrew-from-local-tap; PyPI/tap publication and curl|sh
explicitly out). Decisions are mirrored in
`current-phase-status.md`.

Environment facts recorded in the doc and verified in the first
captured run: pipx 1.11.1 present, system python 3.14 lacks
setuptools, PyPI reachable (HTTP 200) — so builds use isolation /
`pipx run build`, runtime stays stdlib-only.

Four captured runs below: the first passed with an under-extracting
regex (9 of 12 sources), the middle two are honest red iterations of
the cross-check itself (uppercase names, the combined workbench
line, then a miscount), and the final run is authoritative — all 12
`install.sh` copy sources confirmed present in the design doc's
payload table, docs-lint clean.

### Captured run — 2026-07-03T16:36:31Z

- **Command:** `bash -c set -e; echo "== payload inventory cross-check: every install.sh copy source appears in docs/distribution.md =="; python3 - <<PYEOF
import re, sys
usage = open("pmo-roadmap/install.sh").read()
doc = open("docs/distribution.md").read()
sources = re.findall(r"copies ([a-z/._*-]+[a-z*])\s+", usage)
missing = [s for s in sources if s.rstrip("/").split("/")[-1].replace("dw-*.md","agent/dw-*.md") not in doc and s not in doc]
print("install.sh copy sources:", len(sources))
for s in sources: print(" -", s, "OK" if (s in doc or s.rstrip("/").split("/")[-1] in doc) else "MISSING")
bad = [s for s in sources if s not in doc and s.rstrip("/").split("/")[-1] not in doc]
sys.exit(1 if bad else 0)
PYEOF
echo; echo "== environment facts recorded in the doc =="; pipx --version; python3 -c "import setuptools" 2>&1 | tail -1; curl -sI -m 8 https://pypi.org/simple/ | head -1; echo; echo "== docs-lint =="; bash pmo-roadmap/tests/docs-lint.sh 2>&1 | tail -1`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** f9684a102ef0326bd1ef060bf27c7edf8cd5ae11

```text
== payload inventory cross-check: every install.sh copy source appears in docs/distribution.md ==
install.sh copy sources: 9
 - templates/roadmap-builder.md OK
 - hooks/pre-commit OK
 - hooks/commit-msg OK
 - hooks/post-commit OK
 - bin/dw OK
 - bin/dw-workbench OK
 - bin/work-log-summarize OK
 - bin/work-log-read OK
 - agent/dw-*.md OK

== environment facts recorded in the doc ==
1.11.1
ModuleNotFoundError: No module named 'setuptools'
HTTP/2 200 

== docs-lint ==
docs-lint.sh: ok (0s)
```

### Captured run — 2026-07-03T16:36:49Z

- **Command:** `bash -c set -e; echo "== payload cross-check v2 (full inventory incl. uppercase and dirs) =="; python3 - <<PYEOF
import re, sys
usage = open("pmo-roadmap/install.sh").read()
doc = open("docs/distribution.md").read()
sources = re.findall(r"copies ([A-Za-z0-9/._*-]+?) +→", usage)
assert len(sources) == 11, sources
bad = [s for s in sources if s.rstrip("/").split("/")[-1] not in doc and s not in doc]
print("install.sh copy sources:", len(sources))
for s in sources: print(" -", s, "MISSING" if s in bad else "OK")
sys.exit(1 if bad else 0)
PYEOF
echo; echo "== docs-lint =="; bash pmo-roadmap/tests/docs-lint.sh 2>&1 | tail -1`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** f9684a102ef0326bd1ef060bf27c7edf8cd5ae11

```text
== payload cross-check v2 (full inventory incl. uppercase and dirs) ==
Traceback (most recent call last):
  File "<stdin>", line 5, in <module>
AssertionError: ['templates/roadmap-builder.md', 'templates/PMO-CONTRACT.md', 'hooks/pre-commit', 'hooks/commit-msg', 'hooks/post-commit', 'bin/dw', 'lib/dw_pmo/', 'bin/work-log-summarize', 'bin/work-log-read', 'agent/dw-*.md']
```

### Captured run — 2026-07-03T16:37:06Z

- **Command:** `bash -c set -e; echo "== payload cross-check v3: all 11 install.sh copy sources vs docs/distribution.md =="; python3 - <<PYEOF
import re, sys
usage = open("pmo-roadmap/install.sh").read()
doc = open("docs/distribution.md").read()
sources = re.findall(r"copies ([A-Za-z0-9/._*-]+?) +→", usage)
combo = re.findall(r"copies (bin/dw-workbench) \+ (workbench/) +→", usage)
sources += [t for pair in combo for t in pair]
assert len(sources) == 11, (len(sources), sources)
bad = [s for s in sources if s.rstrip("/").split("/")[-1] not in doc and s not in doc]
print("install.sh copy sources:", len(sources))
for s in sorted(sources): print(" -", s, "MISSING" if s in bad else "OK")
sys.exit(1 if bad else 0)
PYEOF
echo; echo "== docs-lint =="; bash pmo-roadmap/tests/docs-lint.sh 2>&1 | tail -1`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** f9684a102ef0326bd1ef060bf27c7edf8cd5ae11

```text
== payload cross-check v3: all 11 install.sh copy sources vs docs/distribution.md ==
Traceback (most recent call last):
  File "<stdin>", line 7, in <module>
AssertionError: (12, ['templates/roadmap-builder.md', 'templates/PMO-CONTRACT.md', 'hooks/pre-commit', 'hooks/commit-msg', 'hooks/post-commit', 'bin/dw', 'lib/dw_pmo/', 'bin/work-log-summarize', 'bin/work-log-read', 'agent/dw-*.md', 'bin/dw-workbench', 'workbench/'])
```

### Captured run — 2026-07-03T16:37:29Z

- **Command:** `bash -c set -e; echo "== payload cross-check v4: all 12 install.sh copy sources vs docs/distribution.md =="; python3 - <<PYEOF
import re, sys
usage = open("pmo-roadmap/install.sh").read()
doc = open("docs/distribution.md").read()
sources = re.findall(r"copies ([A-Za-z0-9/._*-]+?) +→", usage)
combo = re.findall(r"copies (bin/dw-workbench) \+ (workbench/) +→", usage)
sources += [t for pair in combo for t in pair]
assert len(sources) == 12, (len(sources), sources)
bad = [s for s in sources if s.rstrip("/").split("/")[-1] not in doc and s not in doc]
print("install.sh copy sources:", len(sources))
for s in sorted(sources): print(" -", s, "MISSING" if s in bad else "OK")
sys.exit(1 if bad else 0)
PYEOF
echo; echo "== docs-lint =="; bash pmo-roadmap/tests/docs-lint.sh 2>&1 | tail -1`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** f9684a102ef0326bd1ef060bf27c7edf8cd5ae11

```text
== payload cross-check v4: all 12 install.sh copy sources vs docs/distribution.md ==
install.sh copy sources: 12
 - agent/dw-*.md OK
 - bin/dw OK
 - bin/dw-workbench OK
 - bin/work-log-read OK
 - bin/work-log-summarize OK
 - hooks/commit-msg OK
 - hooks/post-commit OK
 - hooks/pre-commit OK
 - lib/dw_pmo/ OK
 - templates/PMO-CONTRACT.md OK
 - templates/roadmap-builder.md OK
 - workbench/ OK

== docs-lint ==
docs-lint.sh: ok (1s)
```
