# Evidence - WLA-25-04

- **Story:** WLA-25-04 - Nudge agents under grant authority
- **Status:** done
- **Date:** 2026-07-19

## Proof

The bounded nudge engine is delivered as the contract's four explicit
layers:

- **Rule (score, reviewable).** The `delivery-workbench-orchestration@1`
  score gains an optional `nudges` section: each rule binds one signal
  kind to one declared agent node with finite `max_per_signal`/`max_total`
  ceilings and a bounded expectation string. The compiler validates rules
  with JSON-pointer diagnostics (dangling/unsafe targets, unknown
  signals, missing bounds, duplicates), naming a failure-activated node
  in a rule makes it reachable exactly like a failure route, rules feed
  the semantic hash (editing them invalidates an unstarted grant), and
  simulation lists every nudge route. A score without the section leaves
  the engine inert — the entire pre-existing suite runs nudge-free and
  green.
- **Authority (grant, revocable).** `run plan` accepts
  `--standing-nudge signal[=target]` matchers (the exact-match grammar)
  and `--signal-channel remote/branch`; both ride the reproducible plan
  request, appear verbatim in the preview the operator approves, land in
  the grant (hash-covered — a tampered standing rule fails the integrity
  check), and die with it. `max_nudges` is a score-defaults budget with
  its own counter. All three transports carry the new plan/start fields.
- **Act (conductor, receipted).** Each tick matches current signal-chain
  facts (keyed by chain event hash) and live `waiting_input` ages against
  the rules and walks the refusal taxonomy — `no-standing-rule`,
  `nudge-budget-exhausted` (with a recorded `blocked` stop on an active
  run), `rule-exhausted`, `run-inactive`, `grant-expired`,
  `non-receptive`, `attempt-ceiling` — each a distinct, deduped
  `nudge_refused` event. A covered, budgeted, receptive match appends one
  `nudge_delivered` event binding rule, signal, signal hash, target,
  attempt, and remaining budget; the event is the at-most-once marker
  across restart, and it is the one sanctioned wake: on an
  `awaiting-certification` run it folds the state back to `active` for
  one more bounded round. Ring 5 is untouched.
- **Delivery (driver seam).** An idle target re-activates as a fresh
  scheduled attempt whose work packet carries an `@nudge` context
  document (facts, hashes, expectation — never argv or prose bodies); a
  live `waiting_input` target receives a hash-bound packet through the
  new `deliver_nudge` seam (fixture writes it into the session; a poked
  receipt returns to `active`), `active` defers, and `blocked`/`unknown`
  refuse per the receptivity table.

Seven new tests (suite 313 → 320 on both Python floors) cover compile
red cases, plan/grant authority with tamper detection, the
wake-and-repair loop with packet lineage and at-most-once replay, the
refusal taxonomy including pause and expiry, budget exhaustion into a
blocked stop, session receptivity (blocked/defer/deliver), and a planted
crash after delivery recovering without a duplicate.

Three runs below, in order:

- **2026-07-19T07:14:05Z (exit 1)** — an honest iteration: the
  end-to-end CLI demo exposed a real seam gap — the run-act surface
  still refused `tick` previews on `awaiting-certification` runs, which
  would have made the wake unreachable from CLI/MCP/HTTP. Fixed by
  allowing the tick act there exactly when the compiled score declares
  nudge rules (and threading the new plan fields through
  `start_run_by_id`); a shadowing local import found in the same pass
  was removed.
- **2026-07-19T07:23:17Z (exit 0)** — the authoritative live demo on the
  installed rails: score authored with a nudge rule, simulation showing
  the route, plan preview stating the standing rule and channel, exact
  token start, run to `awaiting-certification`, fixture `ci-failed`
  signal observed, preview→tick delivering the nudge under the standing
  rule, repair running with the `@nudge` packet context, re-terminal at
  `awaiting-certification`, budget `1/3` used, replayed signal delivering
  nothing more, and `run view` exposing the full nudge lineage.
- **2026-07-19T07:23:31Z (exit 0)** — the authoritative battery: 320
  core tests on both Python floors, docs lint/snippets, canon lint,
  agent surface, MCP server suite, orchestration transport parity, the
  packaged wheel exam, roadmap check, rider parity, vendored-rails
  check, structural doc pins, and diff hygiene.

## Manual review

- Confirmed the manual test plan's editor leg honestly: the Workbench
  editor's JSON view and compiler-backed preview→diff→apply save path
  author and round-trip the `nudges` section losslessly (the compiler
  owns the schema); a dedicated graphical inspector panel for nudge
  rules is left to the Workbench's future editor work and noted in the
  phase status.
- Confirmed no nudge path can mutate the forge, certify, or commit: the
  engine reads signal chains, writes only ledger events and driver-seam
  packets, and the terminal handoff stays `awaiting-certification`.

### Captured run — 2026-07-19T07:14:05Z

- **Command:** `bash -o pipefail -c 
set -e
python3 - <<PYDEMO
import json, subprocess, sys, tempfile
from pathlib import Path

repo_src = Path(".").resolve()
tmp = Path(tempfile.mkdtemp(prefix="dw-nudge-demo."))
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
  "slug": "nudge-loop", "title": "Nudge Loop", "project": "sample",
  "defaults": {"max_concurrency": 2, "max_wall_seconds": 3600, "max_agent_starts": 10,
               "max_check_starts": 10, "default_timeout_seconds": 60,
               "max_artifact_bytes": 1000000, "max_nudges": 3},
  "nodes": [
    {"id": "worker", "type": "agent", "role": "implementation", "profile": "worker-write",
     "prompt": "Do the granted work.", "capabilities": ["repository-read", "repository-write"],
     "workspace": "isolated-worktree"},
    {"id": "repair", "type": "agent", "role": "repair", "profile": "worker-write",
     "activation": "failure", "prompt": "Repair from the nudge facts.",
     "capabilities": ["repository-read", "repository-write"], "workspace": "isolated-worktree"}],
  "nudges": [{"id": "on-ci-failed", "signal": "ci-failed", "target": "repair",
              "max_total": 3, "expectation": "make the pushed branch green"}]}
(repo / "pm" / "orchestration").mkdir(parents=True, exist_ok=True)
(repo / "pm" / "orchestration" / "nudge-loop.json").write_text(json.dumps(score, indent=2) + "\n")
sh("git", "add", "."); sh("git", "-c", "core.hooksPath=/dev/null", "commit", "-q", "-m", "score")

sim = json.loads(sh(dw, "signals", "list", "--json", ok=False).stdout or "{}")
simulation = json.loads(sh(dw, "orchestration", "simulate", "nudge-loop", "--json").stdout)
assert simulation["nudges"][0]["id"] == "on-ci-failed"
print("simulation shows the nudge route:", simulation["nudges"][0]["signal"], "->", simulation["nudges"][0]["target"])

drivers_config = {"kind": "delivery-workbench-driver-config", "schema_version": 1,
  "workspace_root": None, "profiles": {
    "worker-write": {"adapter": "fixture", "capabilities": ["repository-read", "repository-write"],
                     "workspace_modes": ["isolated-worktree"]}}}
store = repo / ".git" / "pmo-orchestration"; store.mkdir(exist_ok=True)
(store / "drivers.json").write_text(json.dumps(drivers_config, indent=2) + "\n")

plan_run = sh(dw, "run", "plan", "nudge-loop", "--project", "sample", "--story", "SMP-0-01",
              "--standing-nudge", "ci-failed=repair", "--signal-channel", "origin/feature-x", "--json")
plan = json.loads(plan_run.stdout)
assert plan["applicable"], plan["issues"]
assert plan["authority"]["standing_nudge_rules"] == [{"signal": "ci-failed", "target": "repair"}]
print("plan preview states the standing rule and channel:", plan["authority"]["signal_channel"])
plan_file = tmp / "plan.json"; plan_file.write_text(plan_run.stdout)
started = json.loads(sh(dw, "run", "start", "--plan", plan_file, "--expect", plan["start_token"],
                        "--approve", "--operator", "nudge-demo", "--json").stdout)
run_id = started["run_id"]
print("run started:", run_id)

def tick():
    preview = json.loads(sh(dw, "run", "preview", run_id, "tick", "--json").stdout)
    return json.loads(sh(dw, "run", "tick", run_id, "--expect", preview["act_token"], "--json").stdout)

result = None
for _ in range(10):
    result = tick()
    if result["terminal"]:
        break
assert result["state"] == "awaiting-certification", result["state"]
print("run reached awaiting-certification; operator integrates and pushes...")

scenario = tmp / "scenario.json"
scenario.write_text(json.dumps({"prs": [{"number": 1, "state": "open", "head": "feature-x",
  "base": "main", "url": "u",
  "checks": [{"name": "ci", "status": "completed", "conclusion": "failure", "url": "u"}]}]}))
observed = json.loads(sh(dw, "signals", "observe", "--provider", "fixture", "--fixture-file", scenario,
                         "--remote", "origin", "--branch", "feature-x", "--json").stdout)
assert observed["status"] == "ci-failed" and observed["starts_work"] is False
print("outward signal recorded: ci-failed on origin/feature-x")

woke = tick()
nudge_actions = [a for a in woke["actions"] if a.get("action") == "nudge-delivered"]
assert nudge_actions, woke["actions"]
print("standing rule delivered the nudge:", nudge_actions[0]["rule"], "->", nudge_actions[0]["node_id"])
for _ in range(10):
    result = tick()
    if result["terminal"]:
        break
assert result["state"] == "awaiting-certification"
show = json.loads(sh(dw, "run", "show", run_id, "--json").stdout)
delivered = [n for n in show["nudges"] if n["delivered"]]
assert len(delivered) == 1 and delivered[0]["node_id"] == "repair"
assert show["budgets"]["max_nudges"]["used"] == 1
repaired = [c for c in show["completed_claims"] if c["node_id"] == "repair"]
assert repaired and repaired[0]["outcome"] == "succeeded"
print("repair ran under the nudge; run re-terminaled at awaiting-certification")

json.loads(sh(dw, "signals", "observe", "--provider", "fixture", "--fixture-file", scenario,
              "--remote", "origin", "--branch", "feature-x", "--json").stdout)
tick(); tick()
again = json.loads(sh(dw, "run", "show", run_id, "--json").stdout)
assert len([n for n in again["nudges"] if n["delivered"]]) == 1
print("replayed signal delivered nothing more: at-most-once holds")
view = json.loads(sh(dw, "run", "view", run_id, "--json").stdout)
assert view["nudges"] == again["nudges"]
print("DEMO COMPLETE: signal -> standing rule -> wake -> repair -> re-terminal, all receipted")
PYDEMO
`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** c683bdbb8dd4a47fa6e006392af743c371740f1c

```text
simulation shows the nudge route: ci-failed -> repair
plan preview states the standing rule and channel: origin/feature-x
run started: run-3d0f791d38d63cd8923dca2e
run reached awaiting-certification; operator integrates and pushes...
outward signal recorded: ci-failed on origin/feature-x
command failed: (PosixPath('/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-nudge-demo._n8um_2h/repo/.githooks/dw'), 'run', 'preview', 'run-3d0f791d38d63cd8923dca2e', 'tick', '--json')
```

### Captured run — 2026-07-19T07:23:17Z

- **Command:** `bash -o pipefail -c 
set -e
python3 - <<PYDEMO
import json, subprocess, sys, tempfile
from pathlib import Path

repo_src = Path(".").resolve()
tmp = Path(tempfile.mkdtemp(prefix="dw-nudge-demo."))
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
  "slug": "nudge-loop", "title": "Nudge Loop", "project": "sample",
  "defaults": {"max_concurrency": 2, "max_wall_seconds": 3600, "max_agent_starts": 10,
               "max_check_starts": 10, "default_timeout_seconds": 60,
               "max_artifact_bytes": 1000000, "max_nudges": 3},
  "nodes": [
    {"id": "worker", "type": "agent", "role": "implementation", "profile": "worker-write",
     "prompt": "Do the granted work.", "capabilities": ["repository-read", "repository-write"],
     "workspace": "isolated-worktree"},
    {"id": "repair", "type": "agent", "role": "repair", "profile": "worker-write",
     "activation": "failure", "prompt": "Repair from the nudge facts.",
     "capabilities": ["repository-read", "repository-write"], "workspace": "isolated-worktree"}],
  "nudges": [{"id": "on-ci-failed", "signal": "ci-failed", "target": "repair",
              "max_total": 3, "expectation": "make the pushed branch green"}]}
(repo / "pm" / "orchestration").mkdir(parents=True, exist_ok=True)
(repo / "pm" / "orchestration" / "nudge-loop.json").write_text(json.dumps(score, indent=2) + "\n")
sh("git", "add", "."); sh("git", "-c", "core.hooksPath=/dev/null", "commit", "-q", "-m", "score")

simulation = json.loads(sh(dw, "orchestration", "simulate", "nudge-loop", "--json").stdout)
assert simulation["nudges"][0]["id"] == "on-ci-failed"
print("simulation shows the nudge route:", simulation["nudges"][0]["signal"], "->", simulation["nudges"][0]["target"])

drivers_config = {"kind": "delivery-workbench-driver-config", "schema_version": 1,
  "workspace_root": None, "profiles": {
    "worker-write": {"adapter": "fixture", "capabilities": ["repository-read", "repository-write"],
                     "workspace_modes": ["isolated-worktree"]}}}
store = repo / ".git" / "pmo-orchestration"; store.mkdir(exist_ok=True)
(store / "drivers.json").write_text(json.dumps(drivers_config, indent=2) + "\n")

plan_run = sh(dw, "run", "plan", "nudge-loop", "--project", "sample", "--story", "SMP-0-01",
              "--standing-nudge", "ci-failed=repair", "--signal-channel", "origin/feature-x", "--json")
plan = json.loads(plan_run.stdout)
assert plan["applicable"], plan["issues"]
assert plan["authority"]["standing_nudge_rules"] == [{"signal": "ci-failed", "target": "repair"}]
print("plan preview states the standing rule and channel:", plan["authority"]["signal_channel"])
plan_file = tmp / "plan.json"; plan_file.write_text(plan_run.stdout)
started = json.loads(sh(dw, "run", "start", "--plan", plan_file, "--expect", plan["start_token"],
                        "--approve", "--operator", "nudge-demo", "--json").stdout)
run_id = started["run_id"]
print("run started:", run_id)

def tick():
    preview = json.loads(sh(dw, "run", "preview", run_id, "tick", "--json").stdout)
    return json.loads(sh(dw, "run", "tick", run_id, "--expect", preview["act_token"], "--json").stdout)

result = None
for _ in range(10):
    result = tick()
    if result["terminal"]:
        break
assert result["state"] == "awaiting-certification", result["state"]
print("run reached awaiting-certification; operator integrates and pushes...")

scenario = tmp / "scenario.json"
scenario.write_text(json.dumps({"prs": [{"number": 1, "state": "open", "head": "feature-x",
  "base": "main", "url": "u",
  "checks": [{"name": "ci", "status": "completed", "conclusion": "failure", "url": "u"}]}]}))
observed = json.loads(sh(dw, "signals", "observe", "--provider", "fixture", "--fixture-file", scenario,
                         "--remote", "origin", "--branch", "feature-x", "--json").stdout)
assert observed["status"] == "ci-failed" and observed["starts_work"] is False
print("outward signal recorded: ci-failed on origin/feature-x")

woke = tick()
nudge_actions = [a for a in woke["actions"] if a.get("action") == "nudge-delivered"]
assert nudge_actions, woke["actions"]
print("standing rule delivered the nudge:", nudge_actions[0]["rule"], "->", nudge_actions[0]["node_id"])
for _ in range(10):
    result = tick()
    if result["terminal"]:
        break
assert result["state"] == "awaiting-certification"
show = json.loads(sh(dw, "run", "show", run_id, "--json").stdout)
delivered = [n for n in show["nudges"] if n["delivered"]]
assert len(delivered) == 1 and delivered[0]["node_id"] == "repair"
assert show["budgets"]["max_nudges"]["used"] == 1
repaired = [c for c in show["completed_claims"] if c["node_id"] == "repair"]
assert repaired and repaired[0]["outcome"] == "succeeded"
print("repair ran under the nudge; run re-terminaled at awaiting-certification")

json.loads(sh(dw, "signals", "observe", "--provider", "fixture", "--fixture-file", scenario,
              "--remote", "origin", "--branch", "feature-x", "--json").stdout)
tick(); tick()
again = json.loads(sh(dw, "run", "show", run_id, "--json").stdout)
assert len([n for n in again["nudges"] if n["delivered"]]) == 1
print("replayed signal delivered nothing more: at-most-once holds")
view = json.loads(sh(dw, "run", "view", run_id, "--json").stdout)
assert view["nudges"] == again["nudges"]
print("DEMO COMPLETE: signal -> standing rule -> wake -> repair -> re-terminal, all receipted")
PYDEMO
`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** c683bdbb8dd4a47fa6e006392af743c371740f1c

```text
simulation shows the nudge route: ci-failed -> repair
plan preview states the standing rule and channel: origin/feature-x
run started: run-aed4f0b0bdffe5232c983fb0
run reached awaiting-certification; operator integrates and pushes...
outward signal recorded: ci-failed on origin/feature-x
standing rule delivered the nudge: on-ci-failed -> repair
repair ran under the nudge; run re-terminaled at awaiting-certification
replayed signal delivered nothing more: at-most-once holds
DEMO COMPLETE: signal -> standing rule -> wake -> repair -> re-terminal, all receipted
```

### Captured run — 2026-07-19T07:23:31Z

- **Command:** `bash -o pipefail -c 
set -e
python3 pmo-roadmap/tests/dw-core-tests.py -q
/usr/bin/python3 pmo-roadmap/tests/dw-core-tests.py -q
bash pmo-roadmap/tests/docs-lint.sh
bash pmo-roadmap/tests/docs-snippet-smoke.sh
bash pmo-roadmap/tests/canon-lint.sh
bash pmo-roadmap/tests/agent-surface.sh
bash pmo-roadmap/tests/mcp-server.sh
bash pmo-roadmap/tests/orchestration-interop.sh
bash pmo-roadmap/tests/package-smoke.sh
.githooks/dw check work-log-automation
.githooks/dw rider docs --check
pmo-roadmap/update.sh . --check
rg -q "nudges" docs/orchestration.md
rg -q "standing_nudges" docs/mcp.md
rg -q "WLA-25-04" docs/signals.md
git diff --check
git diff --cached --check
`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** c683bdbb8dd4a47fa6e006392af743c371740f1c

```text
dw hook: codex_hooks is explicitly false in /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.661wb4ay/config.toml; respecting the opt-out
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
Ran 320 tests in 210.030s

OK
dw hook: claude — 4 installed, 0 already present in /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.2zc6psyd/settings.json
dw hook: claude — 0 installed, 4 already present in /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.2zc6psyd/settings.json
dw hook: claude — 4 installed, 0 already present in /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.9tb8vgbg/settings.json
dw hook: claude — 4 installed, 0 already present in /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test._t9rkgnq/settings.json
dw hook: claude — 4 removed from /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test._t9rkgnq/settings.json
dw hook: codex_hooks is explicitly false in /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.fjfhyuh3/config.toml; respecting the opt-out
----------------------------------------------------------------------
Ran 320 tests in 150.121s

OK
dw hook: claude — 4 installed, 0 already present in /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.066xz9ox/settings.json
dw hook: claude — 0 installed, 4 already present in /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.066xz9ox/settings.json
dw hook: claude — 4 installed, 0 already present in /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.5uactx8i/settings.json
dw hook: claude — 4 installed, 0 already present in /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.akenya_8/settings.json
dw hook: claude — 4 removed from /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.akenya_8/settings.json
docs-lint: ok (413 markdown files)
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
protocol exchange: ok (9 replies)
no-rails refusal: ok
mutation walk: ok (done-without-evidence refused; contract stamped, certification manual)
gate still blocks uncertified commits: ok
MCP/CLI byte-parity (timestamps normalized): ok
mcp-server.sh: ok
orchestration interop: exact CLI/MCP/HTTP lifecycle reached awaiting-certification
orchestration-interop.sh: ok
dw-workbench: shutting down
dw-workbench: serving /private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-orchestration-interop.g52tes/repo
dw-workbench: http://127.0.0.1:24152/ (localhost or your own .ts.net tailnet; Ctrl-C to stop)
dw-workbench: writes require /api/mutations preview→apply or an exact /api/step/apply token; never stages, certifies, or commits
package-smoke.sh: skipping unhealthy interpreter: python3
package-smoke.sh: building with: /usr/bin/python3 (Python 3.9.6)
* Creating isolated environment: venv+pip...
* Installing packages in isolated environment:
  - setuptools>=77
* Getting build dependencies for sdist...
warning: no previously-included files matching '*.pyc' found anywhere in distribution
* Building sdist...
warning: no previously-included files matching '*.pyc' found anywhere in distribution
* Building wheel from sdist
* Creating isolated environment: venv+pip...
* Installing packages in isolated environment:
  - setuptools>=77
* Getting build dependencies for wheel...
warning: no previously-included files matching '__pycache__/*' found anywhere in distribution
warning: no previously-included files matching '*.pyc' found anywhere in distribution
* Building wheel...
warning: no previously-included files matching '__pycache__/*' found anywhere in distribution
warning: no previously-included files matching '*.pyc' found anywhere in distribution
package-smoke.sh: built delivery_workbench-1.14.0-py3-none-any.whl and delivery_workbench-1.14.0.tar.gz
package-smoke.sh: pipx cannot create environments here; falling back to venv+pip
WARNING: You are using pip version 21.2.4; however, version 26.0.1 is available.
You should consider upgrading via the '/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/pmo-package-smoke.VhkUyN/appenv/bin/python -m pip install --upgrade pip' command.
package-smoke.sh: installed via venv+pip
ready     review-workspace   absent     not-applicable
ready     generate-contract  absent     fail
ready     certify-contract   unchecked  fail
ready     commit             passing    pass
ready     start-story        absent     not-applicable
ready     continue-story     absent     not-applicable
attention repair-roadmap     absent     not-applicable
ready     continue-story     absent     not-applicable
ready     continue-story     absent     not-applicable
attention finish-story       absent     not-applicable
ready     review-workspace   absent     not-applicable
ready     generate-contract  absent     fail
ready     certify-contract   unchecked  fail
ready     generate-contract  stale      fail
ready     certify-contract   unchecked  fail
ready     commit             passing    pass
ready     start-story        absent     not-applicable
commit     d3a7971341d3         trailers+archive+verify=ok
guided-status-loop.sh: ok (packaged CLI/MCP/HTTP recommendation sequence)
authorize 01 cli  review-workspace   -> review-workspace
authorize 02 mcp  generate-contract  -> certify-contract
refuse   bootstrap certification started=0 step_events=+0
refuse   bootstrap commit       started=0 step_events=+0
authorize 03 http start-story        -> continue-story
refuse   same-id stale token    started=0 step_events=+0
authorize 04 mcp  continue-story     -> continue-story
authorize 05 cli  finish-story       -> review-workspace
authorize 06 http review-workspace   -> review-workspace
authorize 07 cli  generate-contract  -> certify-contract
refuse   story certification    started=0 step_events=+0
refuse   story commit           started=0 step_events=+0
bootstrap  d80105c3faea         certification+commit=manual
commit     956a641c0b6a         trailers+archive+verify=ok
handoff    start-story        authorizations=7
deliberate-step-loop.sh: ok (fresh token per action; no argv reconstruction or consent shortcut)
{"artifact_count": 5, "checks": 2, "compiler_red_cases": 6, "duplicate_restarts": 0, "exam": "packaged multi-agent orchestration", "operator_commit": "dac28781d53c4c9743c9943eaeb9a2cac26d9bf3", "parallel_research": 2, "repair_visits": 1, "run_id": "run-b8cdedd38b7d88e40f59666f", "runtime_red_cases": 5, "state": "awaiting-certification", "verify_all": "ok"}
package-smoke.sh: ok
dw check: ok
dw rider docs: all rendered surfaces match canon
update.sh: up to date (vendored rails match source v1.14.0)
```
