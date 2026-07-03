#!/usr/bin/env bash
# MCP server smoke (WLA-10-02).
#
# Spawns the real dw-mcp subprocess against a freshly installed
# fixture repo and drives a full client exchange over stdio:
# initialize handshake (pinned protocol version), tools/list
# (orientation inventory), tools/call round-trips whose verdicts
# must equal the CLI's on the same state, JSON-RPC errors for
# unknown methods, loop survival on malformed frames, and the
# no-rails refusal outside adopted repos.

set -eu

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PMO_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
TMP_ROOT="$(mktemp -d "${TMPDIR:-/tmp}/pmo-mcp-smoke.XXXXXX")"

cleanup() {
  rm -rf "$TMP_ROOT"
}
trap cleanup EXIT

fail() {
  echo "mcp-server.sh: $1" >&2
  exit 1
}

REPO="$TMP_ROOT/repo"
mkdir -p "$REPO"
git -C "$REPO" init -q -b main
git -C "$REPO" config user.name "MCP Smoke"
git -C "$REPO" config user.email "mcp-smoke@example.test"
"$PMO_DIR/install.sh" "$REPO" --skip-bootstrap >/dev/null

PHASE="$REPO/pm/roadmap/demo/phase-1-alpha"
mkdir -p "$PHASE"
cat > "$REPO/pm/roadmap/demo/README.md" <<'EOF'
# Demo - Roadmap

**Last updated:** 2026-07-03.
**Current phase:** [phase-1-alpha](./phase-1-alpha/current-phase-status.md).
**Status:** active.

## Phase index

| Phase | Goal (one line) | Status | Folder |
|---|---|---|---|
| 1 | Ship the alpha | active | [phase-1-alpha](./phase-1-alpha/) |

## Project metadata

- **Slug:** `demo`
- **Story ID prefix:** DM
EOF
cat > "$PHASE/current-phase-status.md" <<'EOF'
# Phase 1 - Alpha

**Last updated:** 2026-07-03.

## Story status

| ID | Story | Status | Story file | Evidence |
|---|---|---|---|---|
| DM-1-01 | Thing 1 | backlog | [story-01-thing-1](./story-01-thing-1.md) | - |
EOF
cat > "$PHASE/story-01-thing-1.md" <<'EOF'
# DM-1-01 - Thing 1

- **Project:** demo
- **Phase:** 1
- **Status:** backlog
EOF

# dw_verify needs a HEAD; the scaffold commit is pre-epoch (no
# trailers), which the verifier must skip, not flag.
git -C "$REPO" add -A
git -C "$REPO" commit -q --no-verify -m "fixture scaffold"

DWMCP="$REPO/.githooks/dw-mcp"
if [ ! -f "$DWMCP" ]; then
  # Until WLA-10-04 vendors the server, run the source copy bound to
  # the fixture root.
  DWMCP="$PMO_DIR/bin/dw-mcp"
fi

python3 - "$DWMCP" "$REPO" <<'PYEOF' || fail "protocol exchange failed"
import json
import subprocess
import sys

dwmcp, repo = sys.argv[1], sys.argv[2]
proc = subprocess.Popen(
    ["python3", dwmcp, "--root", repo],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    cwd=repo,
    text=True,
)
msgs = [
    {"jsonrpc": "2.0", "id": 1, "method": "initialize",
     "params": {"protocolVersion": "2025-06-18", "capabilities": {},
                "clientInfo": {"name": "smoke", "version": "0"}}},
    {"jsonrpc": "2.0", "method": "notifications/initialized"},
    {"jsonrpc": "2.0", "id": 2, "method": "tools/list"},
    {"jsonrpc": "2.0", "id": 3, "method": "tools/call",
     "params": {"name": "dw_next", "arguments": {"project": "demo"}}},
    {"jsonrpc": "2.0", "id": 4, "method": "tools/call",
     "params": {"name": "dw_check", "arguments": {}}},
    {"jsonrpc": "2.0", "id": 5, "method": "tools/call",
     "params": {"name": "dw_verify", "arguments": {"all": True}}},
    {"jsonrpc": "2.0", "id": 6, "method": "no/such"},
    "GARBAGE-NOT-JSON",
    {"jsonrpc": "2.0", "id": 7, "method": "tools/call",
     "params": {"name": "dw_nonexistent", "arguments": {}}},
    {"jsonrpc": "2.0", "id": 8, "method": "ping"},
]
inp = "\n".join(m if isinstance(m, str) else json.dumps(m) for m in msgs) + "\n"
out, _ = proc.communicate(inp, timeout=120)
assert proc.returncode == 0, proc.returncode
replies = {}
parse_errors = 0
for line in out.strip().splitlines():
    r = json.loads(line)
    if r.get("id") is None and "error" in r:
        parse_errors += 1
        assert r["error"]["code"] == -32700, r
        continue
    replies[r["id"]] = r

init = replies[1]["result"]
assert init["protocolVersion"] == "2025-06-18", init
assert init["capabilities"] == {"tools": {}}, init
assert init["serverInfo"]["name"] == "delivery-workbench", init

names = [t["name"] for t in replies[2]["result"]["tools"]]
expected = ["dw_context", "dw_next", "dw_check", "dw_doctor", "dw_verify", "dw_gate"]
for name in expected:
    assert name in names, (name, names)
for banned in ("certify", "commit", "bundle"):
    assert not any(banned in n for n in names), names

nxt = replies[3]["result"]
assert not nxt.get("isError"), nxt
assert nxt["structuredContent"]["next_story"]["story_id"] == "DM-1-01", nxt

chk = replies[4]["result"]
assert chk["structuredContent"]["ok"] is True, chk
assert "dw check: ok" in chk["content"][0]["text"], chk

ver = replies[5]["result"]
assert ver["structuredContent"]["ok"] is True, ver

assert replies[6]["error"]["code"] == -32601, replies[6]
assert parse_errors == 1, parse_errors
bad = replies[7]["result"]
assert bad.get("isError") is True and "unknown tool" in bad["content"][0]["text"], bad
assert replies[8]["result"] == {}, replies[8]

print("protocol exchange: ok (%d replies)" % len(replies))
PYEOF

# ── CLI parity on the same fixture state ───────────────────────────
CLI_NEXT="$(cd "$REPO" && ./.githooks/dw next demo --json)"
echo "$CLI_NEXT" | grep -q '"story_id": "DM-1-01"' \
  || fail "CLI next disagrees with fixture expectation: $CLI_NEXT"
(cd "$REPO" && ./.githooks/dw check) >/dev/null \
  || fail "CLI check disagrees with MCP verdict"

# ── outside any adopted repo: discoverable refusal, not a dead socket ─
NOWHERE="$TMP_ROOT/nowhere"
mkdir -p "$NOWHERE"
python3 - "$PMO_DIR/bin/dw-mcp" "$NOWHERE" <<'PYEOF' || fail "no-rails behavior wrong"
import json
import subprocess
import sys

dwmcp, nowhere = sys.argv[1], sys.argv[2]
proc = subprocess.Popen(
    ["python3", dwmcp, "--root", nowhere],
    stdin=subprocess.PIPE, stdout=subprocess.PIPE, cwd=nowhere, text=True,
)
msgs = [
    {"jsonrpc": "2.0", "id": 1, "method": "initialize",
     "params": {"protocolVersion": "2025-06-18", "capabilities": {},
                "clientInfo": {"name": "smoke", "version": "0"}}},
    {"jsonrpc": "2.0", "id": 2, "method": "tools/call",
     "params": {"name": "dw_check", "arguments": {}}},
]
inp = "\n".join(json.dumps(m) for m in msgs) + "\n"
out, _ = proc.communicate(inp, timeout=60)
replies = {json.loads(l)["id"]: json.loads(l) for l in out.strip().splitlines()}
assert "result" in replies[1], replies[1]  # initialize still succeeds
result = replies[2]["result"]
assert result.get("isError") is True, result
text = result["content"][0]["text"]
assert "no Delivery Workbench rails" in text and "dw install" in text, text
print("no-rails refusal: ok")
PYEOF

echo "mcp-server.sh: ok"
