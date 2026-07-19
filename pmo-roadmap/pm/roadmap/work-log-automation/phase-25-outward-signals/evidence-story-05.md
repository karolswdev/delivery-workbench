# Evidence - WLA-25-05

- **Story:** WLA-25-05 - Stream the ledger live
- **Status:** done
- **Date:** 2026-07-19

## Proof

The ledger now streams live without gaining any authority:

- **Core tails.** `tail_run_events` / `tail_signal_events` return the
  verified hash-chained suffix after an integer cursor — replay
  validates the whole chain before one line is emitted (corrupt chains
  fail closed instead of streaming), events are the canonical ledger
  documents (ids, hashes, states, bounded scalar details), and both
  stamp `starts_work: false`.
- **SSE endpoints.** `GET /api/runs/<run>/events` and
  `GET /api/signals/events?remote&branch` on the existing localhost
  Workbench runtime serve `text/event-stream` frames whose `id:` is the
  ledger sequence; `Last-Event-ID` (or `?from=`) resumes exactly the
  missed suffix, `?follow=0` closes after the replay, follow mode polls
  the chain with keepalive comments. The host guard applies first, the
  routes accept GET only, and no token, apply route, or mutation is
  reachable from the stream — enforced by test.
- **CLI.** `dw run tail <run> [--after N] [--follow]` prints the same
  canonical events one JSON object per line.
- **Live Run view.** The Workbench Run view opens an EventSource on the
  run's ledger tail; any arriving event debounce-refreshes the same
  read-model the refresh button uses, leaving explicit refresh as the
  degradation path when the stream closes. All 32 viewport renders stay
  green.

Three new tests (suite 320 → 323 on both Python floors) prove cursor
exactness and ledger derivability, the live-server SSE loop with
disconnect/resume via `Last-Event-ID` (the resumed suffix includes a
real nudge wake), the no-authority posture (POST refused, no token
substrings in any recorded stream), the signal-chain tail, and CLI/ledger
byte equality.

Both runs below are authoritative, in order:

- **2026-07-19T13:35:50Z (exit 0)** — the live demo on the installed
  rails: a real subscriber attached over HTTP while the run executed
  tick by tick, captured 8 frames culminating in `run_terminal`, and the
  frames matched the ledger byte for byte with no gaps; a planted
  `SECRET PROMPT TEXT` in the score's prompt never appeared in the
  stream and neither did any token; a mid-ledger reconnect with
  `Last-Event-ID` replayed exactly the missed suffix; `dw run tail`
  printed the identical event sequence.
- **2026-07-19T13:36:08Z (exit 0)** — the full battery: 323 core tests
  on both Python floors, docs lint/snippets, canon lint, agent surface,
  the 32-render Workbench UI smoke, the explorer integration test,
  roadmap check, rider parity, vendored-rails check, structural doc
  pins, and diff hygiene.

## Manual review

- Confirmed the SSE surface reuses the existing runtime boundary
  unchanged: same host guard, same 127.0.0.1 bind, no CORS headers, no
  new POST route, and the read-only fitness census untouched.
- Confirmed stream payloads are exactly ledger lines — nothing is
  synthesized for the stream, so the "recorded stream equals replay"
  property is structural rather than best-effort.

### Captured run — 2026-07-19T13:35:50Z

- **Command:** `bash -o pipefail -c 
set -e
python3 - <<PYDEMO
import http.client, json, subprocess, sys, tempfile, threading, time
from pathlib import Path

repo_src = Path(".").resolve()
sys.path.insert(0, str(repo_src / ".githooks"))
tmp = Path(tempfile.mkdtemp(prefix="dw-sse-demo."))
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
sh(repo_src / "pmo-roadmap" / "bootstrap" / "new-project.sh", repo, "sample", "Sample", "SMP")
sh(repo_src / "pmo-roadmap" / "install.sh", repo, "--skip-bootstrap")
dw = repo / ".githooks" / "dw"
sh(dw, "story", "status", "sample", "0", "SMP-0-01", "in-progress")
sh(dw, "rider", "docs")
score = {"kind": "delivery-workbench-orchestration", "schema_version": 1,
  "slug": "sse-loop", "title": "SSE Loop", "project": "sample",
  "defaults": {"max_concurrency": 2, "max_wall_seconds": 3600, "max_agent_starts": 10,
               "max_check_starts": 10, "default_timeout_seconds": 60,
               "max_artifact_bytes": 1000000, "max_nudges": 3},
  "nodes": [{"id": "worker", "type": "agent", "role": "implementation", "profile": "worker-write",
             "prompt": "SECRET PROMPT TEXT do the work", "capabilities": ["repository-read", "repository-write"],
             "workspace": "isolated-worktree"}]}
(repo / "pm" / "orchestration").mkdir(parents=True, exist_ok=True)
(repo / "pm" / "orchestration" / "sse-loop.json").write_text(json.dumps(score, indent=2) + "\n")
sh("git", "add", "."); sh("git", "-c", "core.hooksPath=/dev/null", "commit", "-q", "-m", "score")
store = repo / ".git" / "pmo-orchestration"; store.mkdir(exist_ok=True)
(store / "drivers.json").write_text(json.dumps({"kind": "delivery-workbench-driver-config",
  "schema_version": 1, "workspace_root": None, "profiles": {
    "worker-write": {"adapter": "fixture", "capabilities": ["repository-read", "repository-write"],
                     "workspace_modes": ["isolated-worktree"]}}}, indent=2) + "\n")

import dw_pmo.workbench as wb
from http.server import ThreadingHTTPServer
server = ThreadingHTTPServer(("127.0.0.1", 0), wb.create_handler(repo, None))
threading.Thread(target=server.serve_forever, daemon=True).start()
port = server.server_address[1]
print("workbench serving on", port)

plan_out = sh(dw, "run", "plan", "sse-loop", "--project", "sample", "--story", "SMP-0-01", "--json")
plan = json.loads(plan_out.stdout)
plan_file = tmp / "plan.json"; plan_file.write_text(plan_out.stdout)
started = json.loads(sh(dw, "run", "start", "--plan", plan_file, "--expect", plan["start_token"],
                        "--approve", "--operator", "sse-demo", "--json").stdout)
run_id = started["run_id"]
print("run started:", run_id)

frames = []
def subscribe():
    conn = http.client.HTTPConnection("127.0.0.1", port, timeout=30)
    conn.request("GET", f"/api/runs/{run_id}/events")
    response = conn.getresponse()
    buffer = b""
    deadline = time.time() + 20
    while time.time() < deadline:
        chunk = response.read1(4096)
        if not chunk:
            break
        buffer += chunk
        while b"\\n\\n" in buffer:
            block, buffer = buffer.split(b"\\n\\n", 1)
            fields = {}
            for line in block.decode("utf-8").splitlines():
                if ":" in line and not line.startswith(":"):
                    key, _, value = line.partition(":")
                    fields[key.strip()] = value.strip()
            if "data" in fields:
                frames.append((int(fields["id"]), json.loads(fields["data"])))
        if frames and frames[-1][1].get("event") == "run_terminal":
            break
    conn.close()

listener = threading.Thread(target=subscribe, daemon=True)
listener.start()
time.sleep(1)

def tick():
    preview = json.loads(sh(dw, "run", "preview", run_id, "tick", "--json").stdout)
    return json.loads(sh(dw, "run", "tick", run_id, "--expect", preview["act_token"], "--json").stdout)

result = None
for _ in range(10):
    result = tick()
    if result["terminal"]:
        break
listener.join(timeout=25)
print("live subscriber captured", len(frames), "frames while the run executed")

ledger = [json.loads(line) for line in
          (repo / ".git" / "pmo-orchestration" / "runs" / run_id / "ledger.jsonl").read_text().splitlines()]
assert [d for _s, d in frames] == ledger[:len(frames)], "live frames diverge from the ledger"
assert any(d["event"] == "run_terminal" for _s, d in frames)
print("live frames are byte-derivable from the ledger, in order, no gaps")

body = json.dumps([d for _s, d in frames], sort_keys=True)
for excluded in ("SECRET PROMPT TEXT", "act_token", "start_token"):
    assert excluded not in body, excluded
print("stream carried no prompt text and no tokens")

mid = len(ledger) // 2
conn = http.client.HTTPConnection("127.0.0.1", port, timeout=10)
conn.request("GET", f"/api/runs/{run_id}/events?follow=0",
             headers={"Last-Event-ID": str(mid - 1)})
resumed_body = conn.getresponse().read().decode("utf-8")
conn.close()
resumed = []
for block in resumed_body.split("\\n\\n"):
    fields = {}
    for line in block.splitlines():
        if ":" in line and not line.startswith(":"):
            key, _, value = line.partition(":")
            fields[key.strip()] = value.strip()
    if "data" in fields:
        resumed.append(json.loads(fields["data"]))
assert resumed == ledger[mid:], "reconnect suffix diverges"
print("reconnect with Last-Event-ID replayed exactly the missed suffix")

tail_out = sh(dw, "run", "tail", run_id)
assert [json.loads(line) for line in tail_out.stdout.splitlines()] == ledger
print("dw run tail matches the ledger byte for byte")
print("DEMO COMPLETE: a live subscriber, a resumed subscriber, and the CLI all read one truth")
PYDEMO
`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** e46a0361f6b75940da2646411e76e343cfde485d

```text
dw-workbench: 127.0.0.1 "GET /api/runs/run-84d561a019f0d809f037890c/events HTTP/1.1" 200 -
dw-workbench: 127.0.0.1 "GET /api/runs/run-84d561a019f0d809f037890c/events?follow=0 HTTP/1.1" 200 -
workbench serving on 52271
run started: run-84d561a019f0d809f037890c
live subscriber captured 8 frames while the run executed
live frames are byte-derivable from the ledger, in order, no gaps
stream carried no prompt text and no tokens
reconnect with Last-Event-ID replayed exactly the missed suffix
dw run tail matches the ledger byte for byte
DEMO COMPLETE: a live subscriber, a resumed subscriber, and the CLI all read one truth
```

### Captured run — 2026-07-19T13:36:08Z

- **Command:** `bash -o pipefail -c 
set -e
python3 pmo-roadmap/tests/dw-core-tests.py -q
/usr/bin/python3 pmo-roadmap/tests/dw-core-tests.py -q
bash pmo-roadmap/tests/docs-lint.sh
bash pmo-roadmap/tests/docs-snippet-smoke.sh
bash pmo-roadmap/tests/canon-lint.sh
bash pmo-roadmap/tests/agent-surface.sh
bash pmo-roadmap/tests/workbench-ui-smoke.sh
bash pmo-roadmap/tests/workbench-explorer.sh
.githooks/dw check work-log-automation
.githooks/dw rider docs --check
pmo-roadmap/update.sh . --check
rg -q "dw run tail" docs/interop.md
rg -q "api/runs/<run>/events" docs/interop.md
rg -q "api/signals/events" docs/interop.md
rg -q "WLA-25-05" docs/signals.md
git diff --check
git diff --cached --check
`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** e46a0361f6b75940da2646411e76e343cfde485d

```text
dw hook: codex_hooks is explicitly false in /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.ydr1tj7s/config.toml; respecting the opt-out
dw-workbench: 127.0.0.1 "GET /api/runs/run-fdd6e40685582d21b7f5c5e4/events?follow=0 HTTP/1.1" 200 -
dw-workbench: 127.0.0.1 "GET /api/runs/run-fdd6e40685582d21b7f5c5e4/events?follow=0 HTTP/1.1" 200 -
dw-workbench: 127.0.0.1 "POST /api/runs/run-fdd6e40685582d21b7f5c5e4/events HTTP/1.1" 405 -
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
Ran 323 tests in 145.277s

OK
dw hook: claude — 4 installed, 0 already present in /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.celhbdmq/settings.json
dw hook: claude — 0 installed, 4 already present in /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.celhbdmq/settings.json
dw hook: claude — 4 installed, 0 already present in /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.4yqo4ljs/settings.json
dw hook: claude — 4 installed, 0 already present in /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.nkj257wc/settings.json
dw hook: claude — 4 removed from /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.nkj257wc/settings.json
dw hook: codex_hooks is explicitly false in /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.rwbz3jp0/config.toml; respecting the opt-out
dw-workbench: 127.0.0.1 "GET /api/runs/run-0cf6329ea4ca04153279ef33/events?follow=0 HTTP/1.1" 200 -
dw-workbench: 127.0.0.1 "GET /api/runs/run-0cf6329ea4ca04153279ef33/events?follow=0 HTTP/1.1" 200 -
dw-workbench: 127.0.0.1 "POST /api/runs/run-0cf6329ea4ca04153279ef33/events HTTP/1.1" 405 -
dw-workbench: 127.0.0.1 "GET /api/signals/events?remote=origin&branch=sse-x&follow=0 HTTP/1.1" 200 -
dw-workbench: 127.0.0.1 "GET /api/runs/run-000000000000000000000000/events?follow=0 HTTP/1.1" 400 -
----------------------------------------------------------------------
Ran 323 tests in 138.078s

OK
dw hook: claude — 4 installed, 0 already present in /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.tshksgeh/settings.json
dw hook: claude — 0 installed, 4 already present in /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.tshksgeh/settings.json
dw hook: claude — 4 installed, 0 already present in /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.jdznto64/settings.json
dw hook: claude — 4 installed, 0 already present in /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.ckz5dpdx/settings.json
dw hook: claude — 4 removed from /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.ckz5dpdx/settings.json
docs-lint: ok (414 markdown files)
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
workbench-ui-smoke.sh: ok (32 viewport renders: 14 views + attention + ambiguity, desktop+mobile)
dw-workbench: shutting down
dw-workbench: serving /private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/pmo-ui-smoke.mCj7LK/repo
dw-workbench: http://127.0.0.1:22432/ (localhost or your own .ts.net tailnet; Ctrl-C to stop)
dw-workbench: writes require /api/mutations preview→apply or an exact /api/step/apply token; never stages, certifies, or commits
dw-workbench: serving /private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/pmo-workbench-test.tOhOZm/repo
dw-workbench: http://127.0.0.1:19232/ (localhost or your own .ts.net tailnet; Ctrl-C to stop)
dw-workbench: writes require /api/mutations preview→apply or an exact /api/step/apply token; never stages, certifies, or commits
dw-workbench: shutting down
dw-workbench: serving /private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/pmo-workbench-test.tOhOZm/installed
dw-workbench: http://127.0.0.1:19233/ (localhost or your own .ts.net tailnet; Ctrl-C to stop)
dw-workbench: writes require /api/mutations preview→apply or an exact /api/step/apply token; never stages, certifies, or commits
workbench-explorer.sh: ok
dw-workbench: shutting down
dw-workbench: serving /private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/pmo-workbench-test.tOhOZm/repo
dw-workbench: http://127.0.0.1:19232/ (localhost or your own .ts.net tailnet; Ctrl-C to stop)
dw-workbench: writes require /api/mutations preview→apply or an exact /api/step/apply token; never stages, certifies, or commits
dw check: ok
dw rider docs: all rendered surfaces match canon
update.sh: up to date (vendored rails match source v1.14.0)
```
