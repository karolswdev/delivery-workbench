# Evidence - WLA-25-02

- **Story:** WLA-25-02 - Observe SCM facts without acting
- **Status:** done
- **Date:** 2026-07-18

## Proof

`lib/dw_pmo/signals.py` delivers the authority-free observer contracted in
`docs/signals.md`: a provider port with a deterministic fixture oracle and
a thin least-privilege GitHub adapter (operator-environment token,
conditional requests, HTTP 401/403/429 and network failures collapsing to
content-free refusal reasons), hash-chained `signals.jsonl` facts under
`.git/pmo-signals/<remote>/<branch>/` mirroring the run-ledger discipline
exactly (canonical JSON, `sha256:` chain hashes, exact-key events,
scalar-only bounded details, flock store lock, disposable
`projection.json`), semantic dedup so unchanged forge responses append
nothing, and the ten-level derived-status precedence computed at read
time. Surfaces: `dw signals list|observe` (observe is the CLI-only
bounded pass stamping `starts_work: false`), MCP `dw_signals`, and
Workbench `GET /api/signals` — all returning the byte-identical
inventory; the read-only POST-route census is untouched. Wiring shipped
with its paper trail: `docs/interop.md` (CLI verbs, HTTP route, MCP
inventory), `docs/mcp.md`, the managed CLAUDE.md browse group, the pinned
MCP tool census, and the interop verbs list. Ten new `SignalsTest` cases
raise the core suite from 297 to 307.

Two runs below are authoritative, in order:

- **2026-07-19T04:10:30Z (exit 0)** — the live end-to-end demo on the
  real installed CLI against a scratch repository: failing → green →
  conflicted → closed scenarios deriving `ci-failed`/`mergeable`/
  `merge-conflict`/`closed-unmerged`, semantic dedup with
  `not_modified`, planted review/log prose proven absent from durable
  facts, projection-deletion invariance, CLI/MCP/HTTP byte-equivalence,
  a corrupt chain refused by name at exit 1, and a rate-limited forge
  recorded as a deduped content-free refusal. An earlier variant of this
  demo embedded markdown-link syntax in its fixture content, which
  docs-lint correctly flagged inside this evidence file once recorded;
  the demo was recaptured link-free.
- **2026-07-19T04:10:48Z (exit 0)** — the full battery: 307 core tests
  on both Python floors, docs lint/snippets, canon lint, agent surface,
  the MCP server shell suite, roadmap check, rider parity, vendored-
  rails check, structural pins on the new documentation rows, and diff
  hygiene.

## Manual review

- Ran `dw signals observe` against this repository's own `origin/main`
  channel path using the fixture provider and confirmed the operator
  tree stayed clean (`git status --porcelain` empty) with writes
  confined to `.git/pmo-signals/`.
- Confirmed the observer can never mutate the forge: the GitHub adapter
  issues only GET requests, and no code path in `signals.py` shells out
  to `git push`, posts, or writes outside the signal store.

### Captured run — 2026-07-19T04:10:30Z

- **Command:** `bash -o pipefail -c 
set -e
python3 - <<PYDEMO
import json, subprocess, sys, tempfile
from pathlib import Path

dw = Path(".githooks/dw").resolve()
sys.path.insert(0, str(Path(".githooks").resolve()))
tmp = Path(tempfile.mkdtemp(prefix="dw-signals-demo."))
repo = tmp / "repo"; repo.mkdir()

def sh(*argv, cwd=repo, ok=True):
    r = subprocess.run([str(a) for a in argv], cwd=str(cwd), text=True,
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if ok and r.returncode != 0:
        raise SystemExit("command failed: %s\n%s" % (argv, r.stderr))
    return r

sh("git", "init", "-q", "-b", "main")
sh("git", "config", "user.name", "Demo")
sh("git", "config", "user.email", "demo@example.test")
demo = repo / "pm" / "roadmap" / "demo" / "phase-1-alpha"
demo.mkdir(parents=True)
(repo / "pm" / "roadmap" / "demo" / "README.md").write_text(
    "# Demo - Roadmap\n\n- **Slug:** demo\n- **Story ID prefix:** DM\n")
(demo / "current-phase-status.md").write_text("# Phase 1 - Alpha\n")
sh("git", "add", "."); sh("git", "-c", "core.hooksPath=/dev/null", "commit", "-q", "-m", "init")

scenario = tmp / "scenario.json"
def snap(state="open", conclusion="failure", status="completed", mergeable="true", changes=True, approved=False):
    return {"prs": [{"number": 7, "state": state, "draft": False, "head": "feature/x",
        "base": "main", "url": "https://example.test/pr/7",
        "checks": [{"name": "tests", "status": status, "conclusion": conclusion, "url": "u"}],
        "review": {"unresolved": 1 if changes else 0, "resolved": 0, "changes_requested": changes,
                   "approved": approved, "reviewers": ["alice"], "url": "u", "body": "PLANTED PROSE"},
        "mergeable": mergeable, "log_text": "PLANTED LOG"}]}

def observe():
    r = sh(dw, "--root", repo, "signals", "observe", "--provider", "fixture",
           "--fixture-file", scenario, "--remote", "origin", "--branch", "feature/x", "--json")
    return json.loads(r.stdout)

scenario.write_text(json.dumps(snap()))
one = observe()
assert one["status"] == "ci-failed" and one["starts_work"] is False and one["appended"] == 4, one
print("observe 1: ci-failed, starts_work false, appended 4: ok")
two = observe()
assert two["appended"] == 0 and two["not_modified"] is True, two
print("observe 2: semantic dedup and conditional not_modified: ok")

scenario.write_text(json.dumps(snap(conclusion="success", changes=False)))
assert observe()["status"] == "mergeable"
print("green scenario derives mergeable: ok")
scenario.write_text(json.dumps(snap(conclusion="success", changes=False, mergeable="false")))
assert observe()["status"] == "merge-conflict"
print("conflict scenario derives merge-conflict: ok")
scenario.write_text(json.dumps(snap(state="closed", conclusion="success", changes=False)))
assert observe()["status"] == "closed-unmerged"
print("closed scenario derives closed-unmerged: ok")

listing = json.loads(sh(dw, "--root", repo, "signals", "list", "--json").stdout)
assert listing["starts_work"] is False and len(listing["channels"]) == 1

chain = repo / ".git" / "pmo-signals" / "origin" / "feature%2Fx" / "signals.jsonl"
stored = chain.read_text()
assert "PLANTED" not in stored and "PROSE" not in stored, "content leak"
print("third-party content excluded from durable facts: ok")

(chain.parent / "projection.json").unlink()
relisting = json.loads(sh(dw, "--root", repo, "signals", "list", "--json").stdout)
assert relisting == listing, "projection deletion changed answers"
print("projection cache disposable: ok")

import dw_pmo.mcpserver as mcp
import dw_pmo.workbench as wb
tool = mcp.call_tool(repo, "dw_signals", {})
assert tool["structuredContent"] == listing, "MCP parity broke"
code, http = wb.handle_api(repo, "/api/signals", {})
assert code == 200 and http["data"] == listing, "HTTP parity broke"
print("CLI, MCP, and HTTP inventories byte-equivalent: ok")

good = stored
lines = good.splitlines(True)
chain.write_text("".join(lines[:-1]) + lines[-1].replace("event_hash", "event_hasX"))
broken = sh(dw, "--root", repo, "signals", "list", "--json", ok=False)
assert broken.returncode == 1 and "signal chain" in broken.stderr, broken.stderr
print("corrupt chain fails closed by name:", broken.stderr.strip())
chain.write_text(good)

scenario.write_text(json.dumps({"refusal": "rate-limited"}))
ref = observe()
assert ref["refusal"] == "rate-limited" and ref["appended"] == 1, ref
assert observe()["appended"] == 0
print("degraded forge becomes a content-free recorded refusal, deduped: ok")
print("DEMO COMPLETE: the observer records, derives, refuses, and starts nothing")
PYDEMO
`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 50fc618f23a2c174ed63965c0cff552504f87023

```text
observe 1: ci-failed, starts_work false, appended 4: ok
observe 2: semantic dedup and conditional not_modified: ok
green scenario derives mergeable: ok
conflict scenario derives merge-conflict: ok
closed scenario derives closed-unmerged: ok
third-party content excluded from durable facts: ok
projection cache disposable: ok
CLI, MCP, and HTTP inventories byte-equivalent: ok
corrupt chain fails closed by name: dw: signal chain line 9 has non-exact keys
degraded forge becomes a content-free recorded refusal, deduped: ok
DEMO COMPLETE: the observer records, derives, refuses, and starts nothing
```

### Captured run — 2026-07-19T04:10:48Z

- **Command:** `bash -o pipefail -c 
set -e
python3 pmo-roadmap/tests/dw-core-tests.py -q
/usr/bin/python3 pmo-roadmap/tests/dw-core-tests.py -q
bash pmo-roadmap/tests/docs-lint.sh
bash pmo-roadmap/tests/docs-snippet-smoke.sh
bash pmo-roadmap/tests/canon-lint.sh
bash pmo-roadmap/tests/agent-surface.sh
bash pmo-roadmap/tests/mcp-server.sh
.githooks/dw check work-log-automation
.githooks/dw rider docs --check
pmo-roadmap/update.sh . --check
rg -q "dw_signals" docs/interop.md
rg -q "dw signals list" docs/interop.md
rg -q "api/signals" docs/interop.md
rg -q "dw_signals" docs/mcp.md
rg -q "dw_signals" CLAUDE.md
git diff --check
git diff --cached --check
`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 50fc618f23a2c174ed63965c0cff552504f87023

```text
dw hook: codex_hooks is explicitly false in /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.mu7jtvds/config.toml; respecting the opt-out
/opt/homebrew/Cellar/python@3.14/3.14.6/Frameworks/Python.framework/Versions/3.14/lib/python3.14/tempfile.py:484: ResourceWarning: Implicitly cleaning up <HTTPError 401: 'refused'>
  _warnings.warn(self.warn_message, ResourceWarning)
/opt/homebrew/Cellar/python@3.14/3.14.6/Frameworks/Python.framework/Versions/3.14/lib/python3.14/tempfile.py:484: ResourceWarning: Implicitly cleaning up <HTTPError 403: 'refused'>
  _warnings.warn(self.warn_message, ResourceWarning)
/opt/homebrew/Cellar/python@3.14/3.14.6/Frameworks/Python.framework/Versions/3.14/lib/python3.14/tempfile.py:484: ResourceWarning: Implicitly cleaning up <HTTPError 429: 'refused'>
  _warnings.warn(self.warn_message, ResourceWarning)
/opt/homebrew/Cellar/python@3.14/3.14.6/Frameworks/Python.framework/Versions/3.14/lib/python3.14/tempfile.py:484: ResourceWarning: Implicitly cleaning up <HTTPError 500: 'refused'>
  _warnings.warn(self.warn_message, ResourceWarning)
/opt/homebrew/Cellar/python@3.14/3.14.6/Frameworks/Python.framework/Versions/3.14/lib/python3.14/tempfile.py:484: ResourceWarning: Implicitly cleaning up <HTTPError 304: 'refused'>
  _warnings.warn(self.warn_message, ResourceWarning)
----------------------------------------------------------------------
Ran 307 tests in 156.989s

OK
dw hook: claude — 4 installed, 0 already present in /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.5atn8645/settings.json
dw hook: claude — 0 installed, 4 already present in /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.5atn8645/settings.json
dw hook: claude — 4 installed, 0 already present in /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.al80emrf/settings.json
dw hook: claude — 4 installed, 0 already present in /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.d2i7bm_s/settings.json
dw hook: claude — 4 removed from /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.d2i7bm_s/settings.json
dw hook: codex_hooks is explicitly false in /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.27m4wt40/config.toml; respecting the opt-out
----------------------------------------------------------------------
Ran 307 tests in 140.450s

OK
dw hook: claude — 4 installed, 0 already present in /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.mha_ufdo/settings.json
dw hook: claude — 0 installed, 4 already present in /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.mha_ufdo/settings.json
dw hook: claude — 4 installed, 0 already present in /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.8c9l670w/settings.json
dw hook: claude — 4 installed, 0 already present in /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.m3rn4e77/settings.json
dw hook: claude — 4 removed from /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.m3rn4e77/settings.json
docs-lint: ok (411 markdown files)
docs-lint.sh: ok (0s)
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
canon-lint.sh: ok
agent-surface.sh: ok
protocol exchange: ok (9 replies)
no-rails refusal: ok
mutation walk: ok (done-without-evidence refused; contract stamped, certification manual)
gate still blocks uncertified commits: ok
MCP/CLI byte-parity (timestamps normalized): ok
mcp-server.sh: ok
dw check: ok
dw rider docs: all rendered surfaces match canon
update.sh: up to date (vendored rails match source v1.14.0)
```
