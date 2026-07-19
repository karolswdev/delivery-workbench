# Evidence - WLA-25-07

- **Story:** WLA-25-07 - Drive Claude Code through the neutral seam
- **Status:** done
- **Date:** 2026-07-19

## Proof

The second real driver is live, least-privilege by construction:

- **`ClaudeCodeExecDriver`** wraps non-interactive `claude -p`: the
  packet's workspace mode maps to a closed tool allowlist — read-only
  gets `Read,Grep,Glob` (plus `WebSearch,WebFetch` only on network
  profiles), write mode adds the edit tools, and **no mode ever grants a
  shell tool**; `Bash,Task,NotebookEdit` are explicitly disallowed and
  `--dangerously-skip-permissions` never appears (argv-inspection
  tested). Writers run with the isolated worktree as cwd. The
  environment is scrubbed to a small allowlist — `USER`/`LOGNAME` ride
  along as identity (macOS keychain lookups fail closed without them,
  found live), authentication stays entirely harness-owned, and no
  credential-shaped field is accepted in `drivers.json`.
- **Version-pinned discovery** (the herdr version-skew lesson): the
  adapter probes `claude --version` and refuses content-free
  (`adapter-unavailable`) outside the tested major, before any prompt
  is sent — proven by a fake binary reporting 3.x whose `-p` call never
  happened. A missing binary refuses identically.
- **Honest activity**: source-pinned to `active`/`exited`/`unknown`
  with an empty activity plan, and no `deliver_nudge` seam — a live
  session nudge to this adapter refuses as non-receptive rather than
  pretending to inject.
- **A real phase-24 gap, found and fixed by the specimen**: the first
  live capture (15:04:53Z, exit 1) showed the real model succeeding on
  a nudged re-attempt while collect refused with `artifact-validation`
  — the artifact store treated any re-produced artifact as a receipt
  conflict, because until nudges existed no succeeded node ever ran
  again. `validate_and_store_outputs` now lets a **later attempt
  supersede atomically** (same attempt stays idempotent; an older
  attempt still refuses), with a fixture regression test
  (`test_nudged_reattempt_supersedes_its_stored_artifact`).

Four new tests raise the core suite 325 → 329 on both Python floors.

Three runs below, in order:

- **2026-07-19T15:04:53Z (exit 1)** — the honest iteration: the first
  authenticated live specimen; attempt 1 succeeded and printed a real
  model answer, and the nudged attempt 2 exposed the artifact-collision
  gap described above.
- **2026-07-19T15:10:05Z (exit 0)** — the authoritative live specimen:
  a granted run drove the real `claude` binary through the neutral
  seam twice under one grant — a bounded read-only research node
  answering from packet context, then a fixture `ci-failed` signal
  waking the terminal run through the standing rule and re-running the
  node with the `@nudge` context document; the superseding artifact
  carries attempt 2's receipt, budgets read `1/2` used, and the run
  re-terminaled at `awaiting-certification`.
- **2026-07-19T15:10:49Z (exit 0)** — the authoritative battery: 329
  core tests on both Python floors, docs lint/snippets, canon lint,
  agent surface, roadmap check, rider parity, vendored-rails check,
  structural doc pins, and diff hygiene.

## Manual review

- Confirmed CI never depends on model output: every claude-adapter test
  runs against the recording fake binary; the live specimen exists only
  in this captured evidence.
- Confirmed the adapter's argv is provider-neutral at the seam: the
  packet carries no Anthropic-specific field, and profile→adapter
  mapping stays in operator-local `drivers.json`.

### Captured run — 2026-07-19T15:04:53Z

- **Command:** `bash -o pipefail -c 
set -e
python3 - <<PYDEMO
import json, subprocess, sys, tempfile
from pathlib import Path

repo_src = Path(".").resolve()
tmp = Path(tempfile.mkdtemp(prefix="dw-claude-specimen."))
repo = tmp / "repo"; repo.mkdir()

def sh(*argv, cwd=repo, ok=True):
    r = subprocess.run([str(a) for a in argv], cwd=str(cwd), text=True,
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if ok and r.returncode != 0:
        raise SystemExit("command failed: %s\n%s" % (argv, r.stderr))
    return r

sh("git", "init", "-q", "-b", "main")
sh("git", "config", "user.name", "Specimen")
sh("git", "config", "user.email", "specimen@example.test")
sh(repo_src / "pmo-roadmap" / "bootstrap" / "new-project.sh", repo, "sample", "Sample", "SMP")
sh(repo_src / "pmo-roadmap" / "install.sh", repo, "--skip-bootstrap")
dw = repo / ".githooks" / "dw"
sh(dw, "story", "status", "sample", "0", "SMP-0-01", "in-progress")
sh(dw, "rider", "docs")
docs = repo / "docs"; docs.mkdir(exist_ok=True)
(docs / "context.md").write_text(
    "# Context\n\nDelivery Workbench is an evidence-first commit gate over a "
    "Markdown roadmap, with bounded multi-agent orchestration under revocable "
    "grants and an append-only hash-chained ledger.\n"
)
score = {"kind": "delivery-workbench-orchestration", "schema_version": 1,
  "slug": "claude-specimen", "title": "Claude Specimen", "project": "sample",
  "defaults": {"max_concurrency": 1, "max_wall_seconds": 3600, "max_agent_starts": 5,
               "max_check_starts": 5, "default_timeout_seconds": 300,
               "max_artifact_bytes": 1000000, "max_nudges": 2},
  "nodes": [{"id": "research", "type": "agent", "role": "research",
             "profile": "research-readonly",
             "prompt": "Using only the bounded context provided in this packet, state in two sentences what Delivery Workbench is and what its ledger guarantees.",
             "capabilities": ["repository-read"], "workspace": "read-only",
             "inputs": ["docs/**"],
             "outputs": [{"name": "answer", "format": "text",
                          "path": "artifacts/answer.txt", "max_bytes": 20000}],
             "timeout_seconds": 300}],
  "nudges": [{"id": "on-ci-failed", "signal": "ci-failed", "target": "research",
              "max_total": 2, "expectation": "restate the answer for the repaired branch"}]}
(repo / "pm" / "orchestration").mkdir(parents=True, exist_ok=True)
(repo / "pm" / "orchestration" / "claude-specimen.json").write_text(json.dumps(score, indent=2) + "\n")
sh("git", "add", "."); sh("git", "-c", "core.hooksPath=/dev/null", "commit", "-q", "-m", "score")
store = repo / ".git" / "pmo-orchestration"; store.mkdir(exist_ok=True)
(store / "drivers.json").write_text(json.dumps({"kind": "delivery-workbench-driver-config",
  "schema_version": 1, "workspace_root": None, "profiles": {
    "research-readonly": {"adapter": "claude-exec",
                          "capabilities": ["repository-read"],
                          "workspace_modes": ["read-only"]}}}, indent=2) + "\n")

plan_out = sh(dw, "run", "plan", "claude-specimen", "--project", "sample", "--story", "SMP-0-01",
              "--standing-nudge", "ci-failed=research", "--signal-channel", "origin/specimen-x", "--json")
plan = json.loads(plan_out.stdout)
assert plan["applicable"], plan["issues"]
plan_file = tmp / "plan.json"; plan_file.write_text(plan_out.stdout)
started = json.loads(sh(dw, "run", "start", "--plan", plan_file, "--expect", plan["start_token"],
                        "--approve", "--operator", "claude-specimen", "--json").stdout)
run_id = started["run_id"]
print("run started:", run_id)

def tick():
    preview = json.loads(sh(dw, "run", "preview", run_id, "tick", "--json").stdout)
    return json.loads(sh(dw, "run", "tick", run_id, "--expect", preview["act_token"], "--json").stdout)

result = None
for _ in range(6):
    result = tick()
    if result["terminal"]:
        break
assert result["state"] == "awaiting-certification", result
show = json.loads(sh(dw, "run", "show", run_id, "--json").stdout)
first = [c for c in show["completed_claims"] if c["node_id"] == "research"]
assert first and first[0]["outcome"] == "succeeded"
answer = (repo / ".git" / "pmo-orchestration" / "runs" / run_id
          / "artifacts" / "research" / "answer" / "content").read_text()
print("live claude answered (attempt 1):", answer.strip().replace("\\n", " ")[:160])

scenario = tmp / "scenario.json"
scenario.write_text(json.dumps({"prs": [{"number": 1, "state": "open", "head": "specimen-x",
  "base": "main", "url": "u",
  "checks": [{"name": "ci", "status": "completed", "conclusion": "failure", "url": "u"}]}]}))
observed = json.loads(sh(dw, "signals", "observe", "--provider", "fixture", "--fixture-file", scenario,
                         "--remote", "origin", "--branch", "specimen-x", "--json").stdout)
assert observed["status"] == "ci-failed"
print("fixture ci-failed signal recorded; nudging the live driver...")

woke = tick()
assert any(a.get("action") == "nudge-delivered" for a in woke["actions"]), woke["actions"]
for _ in range(6):
    result = tick()
    if result["terminal"]:
        break
assert result["state"] == "awaiting-certification"
show = json.loads(sh(dw, "run", "show", run_id, "--json").stdout)
attempts = [c for c in show["completed_claims"] if c["node_id"] == "research"]
assert len(attempts) == 2 and all(c["outcome"] == "succeeded" for c in attempts)
session_dir = repo / ".git" / "pmo-orchestration" / "runs" / run_id / "driver-sessions"
nudged_packets = []
for record_path in session_dir.glob("session-*.json"):
    record = json.loads(record_path.read_text())
    packet = json.loads(Path(record["packet_path"]).read_text())
    if packet["attempt"] == 2:
        nudged_packets.append(packet)
assert len(nudged_packets) == 1
selectors = [d["selector"] for d in nudged_packets[0]["context"]["documents"]]
assert "@nudge" in selectors
print("nudge round-trip complete: attempt 2 ran live with @nudge context")
delivered = [n for n in show["nudges"] if n["delivered"]]
assert len(delivered) == 1
print("budgets:", json.dumps(show["budgets"]["max_nudges"]))
print("SPECIMEN COMPLETE: real claude -p through the neutral seam, twice, under one grant")
PYDEMO
`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** fcbaf6c33525c799c4f4366b2965d5156ec063c7

```text
run started: run-376cf7c94c3500cc8754b8cf
live claude answered (attempt 1): Delivery Workbench is an evidence-first commit gate built over a Markdown roadmap, extended with bounded multi-agent orchestration in which agents operate under
fixture ci-failed signal recorded; nudging the live driver...
Traceback (most recent call last):
  File "<stdin>", line 99, in <module>
AssertionError
```

### Captured run — 2026-07-19T15:10:05Z

- **Command:** `bash -o pipefail -c 
set -e
python3 - <<PYDEMO
import json, subprocess, sys, tempfile
from pathlib import Path

repo_src = Path(".").resolve()
tmp = Path(tempfile.mkdtemp(prefix="dw-claude-specimen."))
repo = tmp / "repo"; repo.mkdir()

def sh(*argv, cwd=repo, ok=True):
    r = subprocess.run([str(a) for a in argv], cwd=str(cwd), text=True,
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if ok and r.returncode != 0:
        raise SystemExit("command failed: %s\n%s" % (argv, r.stderr))
    return r

sh("git", "init", "-q", "-b", "main")
sh("git", "config", "user.name", "Specimen")
sh("git", "config", "user.email", "specimen@example.test")
sh(repo_src / "pmo-roadmap" / "bootstrap" / "new-project.sh", repo, "sample", "Sample", "SMP")
sh(repo_src / "pmo-roadmap" / "install.sh", repo, "--skip-bootstrap")
dw = repo / ".githooks" / "dw"
sh(dw, "story", "status", "sample", "0", "SMP-0-01", "in-progress")
sh(dw, "rider", "docs")
docs = repo / "docs"; docs.mkdir(exist_ok=True)
(docs / "context.md").write_text(
    "# Context\n\nDelivery Workbench is an evidence-first commit gate over a "
    "Markdown roadmap, with bounded multi-agent orchestration under revocable "
    "grants and an append-only hash-chained ledger.\n"
)
score = {"kind": "delivery-workbench-orchestration", "schema_version": 1,
  "slug": "claude-specimen", "title": "Claude Specimen", "project": "sample",
  "defaults": {"max_concurrency": 1, "max_wall_seconds": 3600, "max_agent_starts": 5,
               "max_check_starts": 5, "default_timeout_seconds": 300,
               "max_artifact_bytes": 1000000, "max_nudges": 2},
  "nodes": [{"id": "research", "type": "agent", "role": "research",
             "profile": "research-readonly",
             "prompt": "Using only the bounded context provided in this packet, state in two sentences what Delivery Workbench is and what its ledger guarantees.",
             "capabilities": ["repository-read"], "workspace": "read-only",
             "inputs": ["docs/**"],
             "outputs": [{"name": "answer", "format": "text",
                          "path": "artifacts/answer.txt", "max_bytes": 20000}],
             "timeout_seconds": 300}],
  "nudges": [{"id": "on-ci-failed", "signal": "ci-failed", "target": "research",
              "max_total": 2, "expectation": "restate the answer for the repaired branch"}]}
(repo / "pm" / "orchestration").mkdir(parents=True, exist_ok=True)
(repo / "pm" / "orchestration" / "claude-specimen.json").write_text(json.dumps(score, indent=2) + "\n")
sh("git", "add", "."); sh("git", "-c", "core.hooksPath=/dev/null", "commit", "-q", "-m", "score")
store = repo / ".git" / "pmo-orchestration"; store.mkdir(exist_ok=True)
(store / "drivers.json").write_text(json.dumps({"kind": "delivery-workbench-driver-config",
  "schema_version": 1, "workspace_root": None, "profiles": {
    "research-readonly": {"adapter": "claude-exec",
                          "capabilities": ["repository-read"],
                          "workspace_modes": ["read-only"]}}}, indent=2) + "\n")

plan_out = sh(dw, "run", "plan", "claude-specimen", "--project", "sample", "--story", "SMP-0-01",
              "--standing-nudge", "ci-failed=research", "--signal-channel", "origin/specimen-x", "--json")
plan = json.loads(plan_out.stdout)
assert plan["applicable"], plan["issues"]
plan_file = tmp / "plan.json"; plan_file.write_text(plan_out.stdout)
started = json.loads(sh(dw, "run", "start", "--plan", plan_file, "--expect", plan["start_token"],
                        "--approve", "--operator", "claude-specimen", "--json").stdout)
run_id = started["run_id"]
print("run started:", run_id)

def tick():
    preview = json.loads(sh(dw, "run", "preview", run_id, "tick", "--json").stdout)
    return json.loads(sh(dw, "run", "tick", run_id, "--expect", preview["act_token"], "--json").stdout)

result = None
for _ in range(6):
    result = tick()
    if result["terminal"]:
        break
assert result["state"] == "awaiting-certification", result
answer_path = (repo / ".git" / "pmo-orchestration" / "runs" / run_id
               / "artifacts" / "research" / "answer" / "content")
print("live claude answered (attempt 1):", answer_path.read_text().strip().replace("\\n", " ")[:150])

scenario = tmp / "scenario.json"
scenario.write_text(json.dumps({"prs": [{"number": 1, "state": "open", "head": "specimen-x",
  "base": "main", "url": "u",
  "checks": [{"name": "ci", "status": "completed", "conclusion": "failure", "url": "u"}]}]}))
observed = json.loads(sh(dw, "signals", "observe", "--provider", "fixture", "--fixture-file", scenario,
                         "--remote", "origin", "--branch", "specimen-x", "--json").stdout)
assert observed["status"] == "ci-failed"
print("fixture ci-failed signal recorded; nudging the live driver...")

woke = tick()
assert any(a.get("action") == "nudge-delivered" for a in woke["actions"]), woke["actions"]
for _ in range(6):
    result = tick()
    if result["terminal"]:
        break
assert result["state"] == "awaiting-certification"
show = json.loads(sh(dw, "run", "show", run_id, "--json").stdout)
attempts = [c for c in show["completed_claims"] if c["node_id"] == "research"]
assert [c["outcome"] for c in attempts] == ["succeeded", "succeeded"], attempts
print("live claude answered (attempt 2, nudged):", answer_path.read_text().strip().replace("\\n", " ")[:150])
metadata = json.loads((answer_path.parent / "metadata.json").read_text())
assert metadata["attempt"] == 2
session_dir = repo / ".git" / "pmo-orchestration" / "runs" / run_id / "driver-sessions"
nudged = []
for record_path in session_dir.glob("session-*.json"):
    record = json.loads(record_path.read_text())
    packet = json.loads(Path(record["packet_path"]).read_text())
    if packet["attempt"] == 2:
        nudged.append(packet)
assert len(nudged) == 1
assert "@nudge" in [d["selector"] for d in nudged[0]["context"]["documents"]]
delivered = [n for n in show["nudges"] if n["delivered"]]
assert len(delivered) == 1
print("nudge round-trip complete: attempt 2 superseded the stored artifact under one grant")
print("budgets:", json.dumps(show["budgets"]["max_nudges"]))
print("SPECIMEN COMPLETE: real claude -p through the neutral seam, twice, least-privilege")
PYDEMO
`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** fcbaf6c33525c799c4f4366b2965d5156ec063c7

```text
run started: run-286f3199dd45771cfae0f23c
live claude answered (attempt 1): Delivery Workbench is an evidence-first commit gate built over a Markdown roadmap, providing bounded multi-agent orchestration in which agents operate
fixture ci-failed signal recorded; nudging the live driver...
live claude answered (attempt 2, nudged): Delivery Workbench is an evidence-first commit gate built over a Markdown roadmap, with bounded multi-agent orchestration performed under revocable gr
nudge round-trip complete: attempt 2 superseded the stored artifact under one grant
budgets: {"limit": 2, "used": 1}
SPECIMEN COMPLETE: real claude -p through the neutral seam, twice, least-privilege
```

### Captured run — 2026-07-19T15:10:49Z

- **Command:** `bash -o pipefail -c 
set -e
python3 pmo-roadmap/tests/dw-core-tests.py -q
/usr/bin/python3 pmo-roadmap/tests/dw-core-tests.py -q
bash pmo-roadmap/tests/docs-lint.sh
bash pmo-roadmap/tests/docs-snippet-smoke.sh
bash pmo-roadmap/tests/canon-lint.sh
bash pmo-roadmap/tests/agent-surface.sh
.githooks/dw check work-log-automation
.githooks/dw rider docs --check
pmo-roadmap/update.sh . --check
rg -q "ClaudeCodeExecDriver" docs/orchestration.md
rg -q "WLA-25-07" docs/signals.md
rg -q "claude-exec" pmo-roadmap/lib/dw_pmo/orchestration_driver.py
git diff --check
git diff --cached --check
`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** fcbaf6c33525c799c4f4366b2965d5156ec063c7

```text
dw hook: codex_hooks is explicitly false in /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.xrlv1huz/config.toml; respecting the opt-out
dw-workbench: 127.0.0.1 "GET /api/runs/run-5bc45dfc5813abea6fd60f77/events?follow=0 HTTP/1.1" 200 -
dw-workbench: 127.0.0.1 "GET /api/runs/run-5bc45dfc5813abea6fd60f77/events?follow=0 HTTP/1.1" 200 -
dw-workbench: 127.0.0.1 "POST /api/runs/run-5bc45dfc5813abea6fd60f77/events HTTP/1.1" 405 -
dw-workbench: 127.0.0.1 "GET /api/signals/events?remote=origin&branch=sse-x&follow=0 HTTP/1.1" 200 -
dw-workbench: 127.0.0.1 "GET /api/runs/run-000000000000000000000000/events?follow=0 HTTP/1.1" 400 -
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
Ran 329 tests in 183.871s

OK
dw hook: claude — 4 installed, 0 already present in /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.00hnkpfn/settings.json
dw hook: claude — 0 installed, 4 already present in /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.00hnkpfn/settings.json
dw hook: claude — 4 installed, 0 already present in /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.ha8zts4b/settings.json
dw hook: claude — 4 installed, 0 already present in /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.w7p7ef08/settings.json
dw hook: claude — 4 removed from /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.w7p7ef08/settings.json
dw hook: codex_hooks is explicitly false in /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.rfuypfiy/config.toml; respecting the opt-out
dw-workbench: 127.0.0.1 "GET /api/runs/run-53e1bb97bb987790e9d70506/events?follow=0 HTTP/1.1" 200 -
dw-workbench: 127.0.0.1 "GET /api/runs/run-53e1bb97bb987790e9d70506/events?follow=0 HTTP/1.1" 200 -
dw-workbench: 127.0.0.1 "POST /api/runs/run-53e1bb97bb987790e9d70506/events HTTP/1.1" 405 -
dw-workbench: 127.0.0.1 "GET /api/signals/events?remote=origin&branch=sse-x&follow=0 HTTP/1.1" 200 -
dw-workbench: 127.0.0.1 "GET /api/runs/run-000000000000000000000000/events?follow=0 HTTP/1.1" 400 -
----------------------------------------------------------------------
Ran 329 tests in 169.497s

OK
dw hook: claude — 4 installed, 0 already present in /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.ca5g8af8/settings.json
dw hook: claude — 0 installed, 4 already present in /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.ca5g8af8/settings.json
dw hook: claude — 4 installed, 0 already present in /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.6vc1rn3l/settings.json
dw hook: claude — 4 installed, 0 already present in /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.cufghzoo/settings.json
dw hook: claude — 4 removed from /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.cufghzoo/settings.json
docs-lint: ok (416 markdown files)
docs-lint.sh: ok (1s)
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
dw check: ok
dw rider docs: all rendered surfaces match canon
update.sh: up to date (vendored rails match source v1.14.0)
```
