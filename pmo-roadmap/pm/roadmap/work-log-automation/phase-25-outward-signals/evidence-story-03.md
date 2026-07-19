# Evidence - WLA-25-03

- **Story:** WLA-25-03 - Teach drivers to report activity states
- **Status:** done
- **Date:** 2026-07-19

## Proof

The driver seam now reports the contracted activity vocabulary
(`active | idle | waiting_input | blocked | exited | unknown`) as an
honest, separate axis from lifecycle state:

- **Receipts carry `activity`.** The provider-neutral receipt gains an
  exact-key `activity` field; while running it must be a non-`exited`
  vocabulary value (default `active`), and terminal states map by rule —
  `lost` → `unknown` (the agent may still be alive somewhere), every
  other terminal → `exited`. Interrupts apply the same mapping.
- **Adapters declare plans; the manager enforces the vocabulary.** The
  adapter result gains `activity_plan` (bounded list, ≤64, no `exited`);
  an adapter inventing a state, scripting `exited` while running,
  returning a non-list, oversizing the plan, or omitting the key is a
  `DwError` conformance refusal at `DriverManager.start`. FixtureDriver
  scripts any walk via the `activities` key, persisted in the session
  record so a post-restart manager continues the same walk
  deterministically. `CodexExecDriver` hard-codes an empty plan —
  non-interactive exec claims nothing richer than active/exited, pinned
  by a source assertion.
- **Transitions are ledger facts, once per change.** The conductor
  records an `activity_observed` runtime event (node, attempt, claim,
  activity, session) only when the polled activity differs from the
  claim's last known state — a repeated `waiting_input` appends nothing,
  keeping replayed ticks idempotent. The event is gated by
  `_validate_runtime_transition` (active claim match + vocabulary) and
  folded into the projection as `last_activity`, so `run show`, the
  `run view` agent sessions (new `activity` column), and the Workbench
  surface it with no new polling or mutation authority.
- **The receptivity table is pure and exhaustive.**
  `signals.receptivity(state, intent)` maps every (state, intent) pair
  to deliver/defer/refuse; `blocked` and `unknown` refuse under every
  intent including a manual operator nudge, and unknown states or
  intents are refusals, not defaults.

Six new tests (suite 307 → 313 on both Python floors) cover the scripted
all-state walk with restart recovery, the lost→unknown mapping, the
five-case conformance refusal, the codex source pin, the ledgered
once-per-change transition sequence with the invented-state ledger
refusal, and the exhaustive receptivity table.

Both runs below are authoritative, in order:

- **2026-07-19T06:06:25Z (exit 0)** — the live demo through the
  installed rails on a scratch consumer: a real granted run whose
  research agent walks `active → waiting_input → waiting_input →
  blocked`, showing the deduped ledger sequence
  `[active, waiting_input, blocked, exited]`, an invented activity
  refused by name at the ledger boundary, the run view session showing
  the terminal activity, and the run finishing at
  `awaiting-certification`.
- **2026-07-19T06:06:39Z (exit 0)** — the full battery: 313 core tests
  on both Python floors, docs lint/snippets, canon lint, agent surface,
  roadmap check, rider parity, vendored-rails check, structural pins,
  and diff hygiene.

## Manual review

- Confirmed `blocked` here is a distinct axis from the run-control
  `blocked` state and the board's blocked story status: it lives only in
  receipt `activity` and `activity_observed` details, never in the
  node/run lifecycle enums.
- Confirmed no adapter path infers activity from output scraping: the
  only sources are the adapter's declared plan and the terminal mapping.

### Captured run — 2026-07-19T06:06:25Z

- **Command:** `bash -o pipefail -c 
set -e
python3 - <<PYDEMO
import json, subprocess, sys, tempfile
from pathlib import Path

repo_src = Path(".").resolve()
sys.path.insert(0, str(repo_src / ".githooks"))
tmp = Path(tempfile.mkdtemp(prefix="dw-activity-demo."))
repo = tmp / "repo"; repo.mkdir()

def sh(*argv, cwd=repo):
    r = subprocess.run([str(a) for a in argv], cwd=str(cwd), text=True,
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if r.returncode != 0:
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
schema = repo / "schemas" / "risk-register-v1.json"
schema.parent.mkdir(exist_ok=True)
schema.write_text(json.dumps({"type": "object", "required": ["risks"],
    "properties": {"risks": {"type": "array", "items": {"type": "string"}}},
    "additionalProperties": False}) + "\n")
docs = repo / "docs"; docs.mkdir(exist_ok=True)
(docs / "context.md").write_text("# Context\n\nBounded.\n")
sh("git", "add", "."); sh("git", "-c", "core.hooksPath=/dev/null", "commit", "-q", "-m", "fixture")

import dw_pmo.orchestration_run as runs
import dw_pmo.orchestration_conductor as conductor
import dw_pmo.orchestration_driver as drivers
import dw_pmo.orchestration_surface as surface
from dw_pmo import DwError
from datetime import datetime, timezone, timedelta

now = datetime.now(timezone.utc).replace(microsecond=0)
config = {"kind": "delivery-workbench-driver-config", "schema_version": 1,
    "workspace_root": None, "profiles": {
        "research-readonly": {"adapter": "fixture", "capabilities": ["repository-read", "network"],
            "workspace_modes": ["read-only"], "network": True},
        "reasoning-readonly": {"adapter": "fixture", "capabilities": ["repository-read"],
            "workspace_modes": ["read-only"]},
        "worker-write": {"adapter": "fixture", "capabilities": ["repository-read", "repository-write"],
            "workspace_modes": ["isolated-worktree"]}}}

plan = runs.build_run_plan(repo, "research-build-review", "sample", "SMP-0-01",
    issued_at=now, expires_at=now + timedelta(hours=1))
projection = runs.start_run(repo, plan, plan["start_token"], approved=True,
    approved_by="activity-demo", now=now)
run_id = projection["run_id"]
print("run started:", run_id)

responses = {
    "research-api": {"polls": 4,
        "activities": ["active", "waiting_input", "waiting_input", "blocked"],
        "outputs": {"api-findings": "# Findings\nBounded.\n\n# Sources\n[Primary](https://example.test/api)\n\n# Risks\nNone.\n"}},
    "research-risks": {"polls": 1, "outputs": {"risk-register": {"risks": ["bounded"]}}},
    "synthesize": {"polls": 1, "outputs": {"implementation-brief": "# Scope\nSmall.\n\n# Decisions\nExact.\n\n# Acceptance checks\nGreen.\n"}},
    "implement": {"polls": 1, "workspace_files": {"src/feature.py": "VALUE = 1"}},
    "repair": {"polls": 1, "workspace_files": {"tests/test_repair.py": "def test_repair(): assert True"}},
}
fixture = drivers.FixtureDriver(responses)
def check_runner(_argv, _cwd, _timeout, _stdout, _stderr, _env):
    return 0

conductor.tick_run(repo, run_id, driver_config=config, adapters={"fixture": fixture},
    check_runner=check_runner, now=now)
live = runs.replay_run(repo, run_id, now=now)
claim = next(item for item in live["active_claims"] if item["node_id"] == "research-api")
print("live claim activity after first tick:", claim["last_activity"]["activity"])

try:
    runs.record_runtime_event(repo, run_id, "activity_observed",
        {"node_id": claim["node_id"], "attempt": claim["attempt"],
         "claim_id": claim["claim_id"], "activity": "daydreaming", "session_id": "none"},
        str(live["ledger_head"]), now=now)
    raise SystemExit("FAIL: invented activity accepted")
except DwError as exc:
    print("invented activity refused by name:", exc.args[0])

for _ in range(24):
    result = conductor.tick_run(repo, run_id, driver_config=config,
        adapters={"fixture": fixture}, check_runner=check_runner, now=now)
    if result["terminal"]:
        break

ledger = (repo / ".git" / "pmo-orchestration" / "runs" / run_id / "ledger.jsonl").read_text()
observed = [json.loads(line)["detail"]["activity"] for line in ledger.splitlines()
            if json.loads(line)["event"] == "activity_observed"
            and json.loads(line)["detail"]["node_id"] == "research-api"]
print("ledgered research-api activity transitions:", observed)
assert observed == ["active", "waiting_input", "blocked", "exited"], observed

view = surface.build_run_view(repo, run_id, now=now)
agents = [item for item in view["sessions"]["agents"] if item["node_id"] == "research-api"]
assert agents[0]["activity"] == "exited"
print("run view session activity:", agents[0]["activity"])

final = runs.replay_run(repo, run_id, now=now)
print("terminal state:", final["state"])
print("DEMO COMPLETE: activity is a ledgered, deduped, honest axis; repeated waiting_input appended once")
PYDEMO
`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 62b904fe5da0107ceeba1f9f09675a172afaa390

```text
run started: run-25dc202f6fcee5de4cce18a2
live claim activity after first tick: waiting_input
invented activity refused by name: activity observation has an unsupported state
ledgered research-api activity transitions: ['active', 'waiting_input', 'blocked', 'exited']
run view session activity: exited
terminal state: awaiting-certification
DEMO COMPLETE: activity is a ledgered, deduped, honest axis; repeated waiting_input appended once
```

### Captured run — 2026-07-19T06:06:39Z

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
rg -q "activity_observed" pmo-roadmap/lib/dw_pmo/orchestration_run.py
rg -q "ACTIVITY_STATES" pmo-roadmap/lib/dw_pmo/orchestration_driver.py
rg -q "def receptivity" pmo-roadmap/lib/dw_pmo/signals.py
rg -q "WLA-25-03" docs/signals.md
git diff --check
git diff --cached --check
`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 62b904fe5da0107ceeba1f9f09675a172afaa390

```text
dw hook: codex_hooks is explicitly false in /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.xxngkvgq/config.toml; respecting the opt-out
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
Ran 313 tests in 141.292s

OK
dw hook: claude — 4 installed, 0 already present in /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.r43_925t/settings.json
dw hook: claude — 0 installed, 4 already present in /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.r43_925t/settings.json
dw hook: claude — 4 installed, 0 already present in /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.9v0o0d9t/settings.json
dw hook: claude — 4 installed, 0 already present in /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.9o6itwz1/settings.json
dw hook: claude — 4 removed from /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.9o6itwz1/settings.json
dw hook: codex_hooks is explicitly false in /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.xog415nw/config.toml; respecting the opt-out
----------------------------------------------------------------------
Ran 313 tests in 126.648s

OK
dw hook: claude — 4 installed, 0 already present in /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.lhurb4e4/settings.json
dw hook: claude — 0 installed, 4 already present in /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.lhurb4e4/settings.json
dw hook: claude — 4 installed, 0 already present in /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.0gyawkob/settings.json
dw hook: claude — 4 installed, 0 already present in /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.x21_6ezb/settings.json
dw hook: claude — 4 removed from /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.x21_6ezb/settings.json
docs-lint: ok (412 markdown files)
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
