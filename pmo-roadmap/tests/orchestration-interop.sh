#!/usr/bin/env bash
# WLA-24-07 interop exam: one installed run crosses CLI, MCP, and HTTP
# without any adapter owning score semantics or continuing implicitly.

set -eu

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PMO_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
TMP_ROOT="$(mktemp -d "${TMPDIR:-/tmp}/dw-orchestration-interop.XXXXXX")"
SERVER_PID=""

cleanup() {
  if [ -n "$SERVER_PID" ]; then
    kill "$SERVER_PID" 2>/dev/null || true
    wait "$SERVER_PID" 2>/dev/null || true
  fi
  rm -rf "$TMP_ROOT"
}
trap cleanup EXIT

fail() {
  echo "orchestration-interop.sh: $1" >&2
  exit 1
}

REPO="$TMP_ROOT/repo"
mkdir -p "$REPO"
git -C "$REPO" init -q -b main
git -C "$REPO" config user.name "Orchestration Interop"
git -C "$REPO" config user.email "orchestration-interop@example.test"
"$PMO_DIR/bootstrap/new-project.sh" "$REPO" sample "Sample" SMP >/dev/null
"$PMO_DIR/install.sh" "$REPO" --skip-bootstrap >/dev/null
DW="$REPO/.githooks/dw"
MCP="$REPO/.githooks/dw-mcp"
WORKBENCH="$REPO/.githooks/dw-workbench"
"$DW" --root "$REPO" story status sample 0 SMP-0-01 in-progress >/dev/null
mkdir -p "$REPO/pm/orchestration"
python3 - "$REPO/pm/orchestration/interop-approval.json" <<'PY'
import json
import sys

path = sys.argv[1]
document = {
    "kind": "delivery-workbench-orchestration",
    "schema_version": 1,
    "slug": "interop-approval",
    "title": "Interop approval",
    "project": "sample",
    "nodes": [
        {
            "id": "review", "type": "approval",
            "prompt": "Approve the bounded interop result.",
            "options": ["approve", "reject"],
        },
        {
            "id": "handoff", "type": "approval", "needs": ["review"],
            "prompt": "Review exact run receipts.",
            "terminal": "awaiting-certification",
        },
    ],
}
with open(path, "w", encoding="utf-8") as handle:
    json.dump(document, handle, indent=2)
    handle.write("\n")
PY
git -C "$REPO" add .
git -C "$REPO" -c core.hooksPath=/dev/null commit -q -m "interop fixture"

PORT=$(( (RANDOM % 2000) + 23000 ))
"$WORKBENCH" --root "$REPO" --port "$PORT" --quiet &
SERVER_PID=$!
i=0
until curl -sf "http://127.0.0.1:$PORT/api/projects" >/dev/null 2>&1; do
  i=$((i + 1))
  [ "$i" -lt 60 ] || fail "installed Workbench did not start"
  sleep 0.2
done

python3 - "$REPO" "$DW" "$MCP" "http://127.0.0.1:$PORT" <<'PY' \
  || fail "cross-adapter lifecycle failed"
import datetime
import hashlib
import json
import pathlib
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

repo = pathlib.Path(sys.argv[1])
dw, mcp, base = sys.argv[2:]
run_root = repo / ".git" / "pmo-orchestration" / "runs"


def cli(*args, expect_ok=True):
    proc = subprocess.run(
        [dw, "--root", str(repo), *args], cwd=repo, text=True,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )
    if expect_ok:
        assert proc.returncode == 0, (args, proc.returncode, proc.stdout, proc.stderr)
        return json.loads(proc.stdout)
    assert proc.returncode != 0, (args, proc.stdout, proc.stderr)
    return proc


def call_mcp(name, arguments):
    request = {
        "jsonrpc": "2.0", "id": 1, "method": "tools/call",
        "params": {"name": name, "arguments": arguments},
    }
    proc = subprocess.run(
        [mcp, "--root", str(repo)], cwd=repo, text=True,
        input=json.dumps(request) + "\n", stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    assert proc.returncode == 0, proc.stderr
    result = json.loads(proc.stdout)["result"]
    return result


def http(method, route, payload=None, expected=200):
    data = None
    headers = {}
    if payload is not None:
        data = json.dumps(payload).encode()
        headers["Content-Type"] = "application/json"
    request = urllib.request.Request(base + route, data=data, headers=headers, method=method)
    try:
        response = urllib.request.urlopen(request)
        status = response.status
        body = json.load(response)
    except urllib.error.HTTPError as exc:
        status = exc.code
        body = json.load(exc)
    assert status == expected, (method, route, status, body)
    return body


def ledger_bytes(run_id):
    return (run_root / run_id / "ledger.jsonl").read_bytes()


def digest(data):
    return hashlib.sha256(data).hexdigest()


def same_observation(*readers):
    """Take pure reads inside one UTC-second wall-budget observation."""
    last = None
    for _ in range(5):
        time.sleep(1.05 - (time.time() % 1.0))
        values = [reader() for reader in readers]
        if all(value == values[0] for value in values[1:]):
            return values[0]
        last = values
    raise AssertionError(("read adapters did not converge in one observation second", last))


now = datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0)
issued = now.isoformat().replace("+00:00", "Z")
expires = (now + datetime.timedelta(hours=1)).isoformat().replace("+00:00", "Z")
plan_args = {
    "score": "interop-approval", "project": "sample", "story": "SMP-0-01",
    "issued_at": issued, "expires_at": expires,
}
cli_plan = cli(
    "run", "plan", "interop-approval", "--project", "sample",
    "--story", "SMP-0-01", "--issued-at", issued,
    "--expires-at", expires, "--json",
)
mcp_plan = call_mcp("dw_run_plan", plan_args)
assert not mcp_plan.get("isError"), mcp_plan
query = urllib.parse.urlencode(plan_args)
http_plan = http("GET", "/api/run-plan?" + query)["data"]
assert cli_plan == mcp_plan["structuredContent"] == http_plan
assert cli_plan["starts_work"] is False and cli_plan["writes_run_state"] is False

started = http("POST", "/api/runs/start", {
    **plan_args, "expect": cli_plan["start_token"], "approve": True,
    "operator": "interop-fixture",
})["data"]
run_id = started["run_id"]
assert started["state"] == "active" and started["active_claims"] == []

# Projection and the explanation-oriented Run model are byte-equivalent
# transport payloads, and all reads leave the ledger unchanged.
before_reads = digest(ledger_bytes(run_id))
cli_projection = same_observation(
    lambda: cli("run", "show", run_id, "--json"),
    lambda: call_mcp("dw_run_show", {"run_id": run_id})["structuredContent"],
    lambda: http("GET", "/api/runs/" + run_id)["data"],
)
cli_view = same_observation(
    lambda: cli("run", "view", run_id, "--json"),
    lambda: call_mcp("dw_run_view", {"run_id": run_id})["structuredContent"],
    lambda: http("GET", "/api/runs/" + run_id + "/view")["data"],
)
assert cli_view["starts_work"] is False and cli_view["writes_events"] is False
assert digest(ledger_bytes(run_id)) == before_reads

# CLI preview -> MCP pause. Replaying that exact token over HTTP is stale and
# appends no event. The reason is part of the token, not free text at apply.
reason = "inspect exact interop state"
cli_pause = cli("run", "preview", run_id, "pause", "--reason", reason, "--json")
mcp_pause = call_mcp("dw_run_preview", {
    "run_id": run_id, "action": "pause", "reason": reason,
})["structuredContent"]
http_pause = http("GET", "/api/runs/" + run_id + "/act/pause?" + urllib.parse.urlencode({"reason": reason}))["data"]
assert cli_pause == mcp_pause == http_pause and cli_pause["applicable"]
paused = call_mcp("dw_run_pause", {
    "run_id": run_id, "expect": cli_pause["act_token"], "reason": reason,
})
assert not paused.get("isError"), paused
assert paused["structuredContent"]["state"] == "paused"
stale_before = ledger_bytes(run_id)
http("POST", "/api/runs/pause", {
    "run_id": run_id, "expect": cli_pause["act_token"], "reason": reason,
}, expected=409)
assert ledger_bytes(run_id) == stale_before

# HTTP preview -> CLI resume.
resume = http("POST", "/api/runs/preview", {
    "run_id": run_id, "action": "resume",
})["data"]
resumed = cli("run", "resume", run_id, "--expect", resume["act_token"], "--json")
assert resumed["state"] == "active"

# MCP preview -> HTTP conductor tick. A token replay through CLI refuses
# before dispatch or an event. This score reaches an explicit checkpoint.
tick = call_mcp("dw_run_preview", {"run_id": run_id, "action": "tick"})
assert not tick.get("isError"), tick
tick_doc = http("POST", "/api/runs/tick", {
    "run_id": run_id, "expect": tick["structuredContent"]["act_token"],
})["data"]
assert tick_doc["kind"] == "delivery-workbench-conductor-tick", tick_doc
assert tick_doc["state"] == "awaiting-approval", tick_doc
stale_before = ledger_bytes(run_id)
replay = cli(
    "run", "tick", run_id, "--expect", tick["structuredContent"]["act_token"],
    "--json", expect_ok=False,
)
assert "stale or altered" in replay.stderr
assert ledger_bytes(run_id) == stale_before

# The checkpoint preview is the same exact document on every read surface;
# MCP consumes it and the run stops at the non-certifying terminal handoff.
cli_checkpoint = cli(
    "run", "preview", run_id, "checkpoint", "--decision", "approve", "--json"
)
mcp_checkpoint = call_mcp("dw_run_preview", {
    "run_id": run_id, "action": "checkpoint", "decision": "approve",
})["structuredContent"]
http_checkpoint = http("POST", "/api/runs/preview", {
    "run_id": run_id, "action": "checkpoint", "decision": "approve",
})["data"]
assert cli_checkpoint == mcp_checkpoint == http_checkpoint
approved = call_mcp("dw_run_checkpoint", {
    "run_id": run_id, "expect": cli_checkpoint["act_token"],
    "decision": "approve",
})
assert not approved.get("isError"), approved
assert approved["structuredContent"]["state"] == "active"
handoff_preview = http("POST", "/api/runs/preview", {
    "run_id": run_id, "action": "tick",
})["data"]
handoff_tick = cli(
    "run", "tick", run_id, "--expect", handoff_preview["act_token"], "--json"
)
assert handoff_tick["state"] == "awaiting-certification"
terminal = http("GET", "/api/runs/" + run_id + "/view")["data"]
assert terminal["terminal"] is True, terminal
assert "human inspection" in terminal["terminal_meaning"], terminal
assert not any(control["available"] for control in terminal["controls"]), terminal["controls"]

# Inventory/feed documents remain content-safe. Explicit stream opens are
# bounded and malformed execution identities refuse. Applying adapters reject
# any attempt to smuggle score or executor semantics through them.
mission = http("GET", "/api/missioncontrol")["data"]["feed"]["orchestration_runs"]
serialized = json.dumps(mission, sort_keys=True).lower()
assert run_id in serialized
for forbidden in ("prompt", "argv", "transcript", "packet", "artifact content"):
    assert forbidden not in serialized
http("GET", "/api/runs/" + run_id + "/streams/check/not-a-check/stdout", expected=400)
http("POST", "/api/runs/tick", {
    "run_id": run_id, "expect": "x", "driver_config": {},
}, expected=400)
smuggle = call_mcp("dw_run_start", {
    **plan_args, "expect": cli_plan["start_token"], "approve": True,
    "operator": "interop-fixture", "argv": ["sh", "-c", "danger"],
})
assert smuggle.get("isError") and "unknown parameter" in smuggle["content"][0]["text"]

print("orchestration interop: exact CLI/MCP/HTTP lifecycle reached awaiting-certification")
PY

echo "orchestration-interop.sh: ok"
