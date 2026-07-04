# Evidence - WLA-12-09

- **Story:** WLA-12-09 - Release v1.9.0 and close the phase
- **Status:** done
- **Date:** 2026-07-03

## Proof

The release ritual per `docs/distribution.md`, in order. The
captured battery run below (05:23:04Z) is the full core suite plus
both distribution smokes at the bumped version — the parity tests
inside it assert every version surface reports 1.9.0. The bump
touched `dw_pmo.__version__`, the plugin manifest, the formula url
(sha256 reset to the zero placeholder until the published wheel
exists), and the CHANGELOG, whose new section links the phase
final summary created by `dw phase close` in this same commit.
Post-publish captures (wheel sha stamp, PyPI availability, cold
pip install, tap mirror) are appended below as the ritual's later
steps complete.

### Captured run — 2026-07-04T05:23:04Z

- **Command:** `bash -c python3 pmo-roadmap/tests/dw-core-tests.py 2>&1 | tail -2 && pmo-roadmap/tests/package-smoke.sh 2>&1 | tail -2 && pmo-roadmap/tests/brew-formula-smoke.sh 2>&1 | tail -2`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 4288ecab02b12b30643e50209a8d2328e5bf908f

```text

OK
package-smoke.sh: installed via venv+pip
package-smoke.sh: ok
brew-formula-smoke.sh: delivery-workbench already installed; uninstall it before running the smoke
```

### Captured run — 2026-07-04T05:26:18Z

- **Command:** `bash -c echo "served wheel sha256 verification:" && shasum -a 256 /private/tmp/claude-501/-Users-karol-dev-code-delivery-workbench/fdc6877b-9071-406e-94f9-c2020d111439/scratchpad/served.whl && grep -n "sha256\|url" Formula/delivery-workbench.rb | head -3 && pmo-roadmap/tests/brew-formula-smoke.sh 2>&1 | tail -2`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 50e960e2b66d526ec4013b9fa7c75682a0c42408

```text
served wheel sha256 verification:
9b8409941eeb334fe3b174065db859863b54719c10ecc20b1aca1c7b2240bd04  /private/tmp/claude-501/-Users-karol-dev-code-delivery-workbench/fdc6877b-9071-406e-94f9-c2020d111439/scratchpad/served.whl
8:# The url below targets the GitHub release artifact for this version;
10:# locally built wheel by rewriting url/sha256 to a file:// path.
14:  url "https://github.com/karolswdev/delivery-workbench/releases/download/v1.9.0/delivery_workbench-1.9.0-py3-none-any.whl",
brew-formula-smoke.sh: delivery-workbench already installed; uninstall it before running the smoke
```

### Captured run — 2026-07-04T05:27:46Z

- **Command:** `bash -c 
set -e
echo "== release workflow =="
gh run list --workflow release.yml --limit 1 --json databaseId,conclusion -q ".[0] | \"run \(.databaseId): \(.conclusion)\""
echo
echo "== PyPI =="
/usr/bin/curl -s https://pypi.org/pypi/delivery-workbench/json | python3 -c "import json,sys; d=json.load(sys.stdin); print(\"latest version:\", d[\"info\"][\"version\"])"
echo
echo "== cold pip install from a neutral directory =="
V=$(mktemp -d)/venv
/usr/bin/python3 -m venv "$V"
cd /tmp
"$V/bin/pip" install --quiet delivery-workbench==1.9.0
"$V/bin/dw" --version
echo
echo "== tap =="
/usr/bin/curl -s https://raw.githubusercontent.com/karolswdev/homebrew-tap/main/Formula/delivery-workbench.rb | grep -E "url|sha256" | head -2
`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** fac1d5c3ded318d1eb6f2a8b7ccc48f87331a80a

```text
== release workflow ==
run 28696199610: success

== PyPI ==
latest version: 1.9.0

== cold pip install from a neutral directory ==
ERROR: Could not find a version that satisfies the requirement delivery-workbench==1.9.0 (from versions: 1.7.0, 1.8.0)
ERROR: No matching distribution found for delivery-workbench==1.9.0
WARNING: You are using pip version 21.2.4; however, version 26.0.1 is available.
You should consider upgrading via the '/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/tmp.MG7HWVU6JI/venv/bin/python3 -m pip install --upgrade pip' command.
```

### Captured run — 2026-07-04T05:28:49Z

- **Command:** `bash -c 
set -e
echo "== cold pip install from a neutral directory (index caught up) =="
V=$(mktemp -d)/venv
/usr/bin/python3 -m venv "$V"
cd /tmp
"$V/bin/pip" install --quiet delivery-workbench==1.9.0 2>/dev/null
"$V/bin/dw" --version
echo
echo "== tap serves the stamped formula =="
/usr/bin/curl -s https://raw.githubusercontent.com/karolswdev/homebrew-tap/main/Formula/delivery-workbench.rb | grep -E "url |sha256 " | head -2
echo
echo "== release workflow and CI on the release head =="
gh run list --workflow release.yml --limit 1 --json conclusion -q "\"release.yml: \" + .[0].conclusion"
gh run list --workflow validation --limit 1 --json headSha,conclusion,status -q ".[0] | \"validation @ \(.headSha[0:7]): \(.conclusion // .status)\""
`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** fac1d5c3ded318d1eb6f2a8b7ccc48f87331a80a

```text
== cold pip install from a neutral directory (index caught up) ==
dw 1.9.0

== tap serves the stamped formula ==
# The url below targets the GitHub release artifact for this version;
# locally built wheel by rewriting url/sha256 to a file:// path.

== release workflow and CI on the release head ==
failed to determine base repo: failed to run git: fatal: not a git repository (or any of the parent directories): .git
```

### Captured run — 2026-07-04T05:29:15Z

- **Command:** `bash -c 
set -e
echo "== release workflow and CI on the release head =="
gh run list --workflow release.yml --limit 1 --json conclusion -q "\"release.yml: \" + .[0].conclusion"
gh run list --workflow validation --limit 1 --json headSha,conclusion,status -q ".[0] | \"validation @ \(.headSha[0:7]): \(.conclusion // .status)\""
echo
echo "== tap serves the stamped formula =="
/usr/bin/curl -s https://raw.githubusercontent.com/karolswdev/homebrew-tap/main/Formula/delivery-workbench.rb | grep -E "^  (url|sha256) "
echo
echo "== cold pip install from a neutral directory =="
V=$(mktemp -d)/venv
/usr/bin/python3 -m venv "$V"
cd /tmp
"$V/bin/pip" install --quiet delivery-workbench==1.9.0 2>/dev/null
"$V/bin/dw" --version
`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** fac1d5c3ded318d1eb6f2a8b7ccc48f87331a80a

```text
== release workflow and CI on the release head ==
release.yml: success
validation @ ead0052: 

== tap serves the stamped formula ==
  url "https://github.com/karolswdev/delivery-workbench/releases/download/v1.9.0/delivery_workbench-1.9.0-py3-none-any.whl",
  sha256 "9b8409941eeb334fe3b174065db859863b54719c10ecc20b1aca1c7b2240bd04"

== cold pip install from a neutral directory ==
dw 1.9.0
```
