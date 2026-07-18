#!/usr/bin/env bash
# Optional live WLA-24-05 adapter proof. Deterministic CI uses FixtureDriver;
# set DW_CODEX_DRIVER_LIVE=1 when an authenticated Codex CLI is provisioned.

set -eu

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PMO_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
CODEX_BIN="${DW_CODEX_BIN:-$(command -v codex 2>/dev/null || true)}"

if [ "${DW_CODEX_DRIVER_LIVE:-0}" != "1" ]; then
  echo "codex-driver-smoke.sh: SKIP (set DW_CODEX_DRIVER_LIVE=1 for authenticated live proof)"
  exit 0
fi
[ -n "$CODEX_BIN" ] && [ -x "$CODEX_BIN" ] \
  || { echo "codex-driver-smoke.sh: requested live proof but codex is unavailable" >&2; exit 1; }

TMP_ROOT="$(mktemp -d "${TMPDIR:-/tmp}/dw-codex-driver.XXXXXX")"
cleanup() {
  if [ "${DW_CODEX_DRIVER_KEEP:-0}" = "1" ]; then
    echo "codex-driver-smoke.sh: retained fixture at $TMP_ROOT" >&2
  else
    rm -rf "$TMP_ROOT"
  fi
}
trap cleanup EXIT
REPO="$TMP_ROOT/repo"
mkdir -p "$REPO"
git -C "$REPO" init -q -b main
git -C "$REPO" config user.name "Codex Driver Smoke"
git -C "$REPO" config user.email "codex-driver@example.test"
"$PMO_DIR/bootstrap/new-project.sh" "$REPO" sample "Sample" SMP >/dev/null
"$PMO_DIR/install.sh" "$REPO" --skip-bootstrap >/dev/null
"$REPO/.githooks/dw" --root "$REPO" story status sample 0 SMP-0-01 in-progress >/dev/null
"$REPO/.githooks/dw" --root "$REPO" rider docs >/dev/null

cat > "$REPO/pm/orchestration/live-codex-research.json" <<'JSON'
{
  "kind": "delivery-workbench-orchestration",
  "schema_version": 1,
  "slug": "live-codex-research",
  "title": "Live Codex read-only research proof",
  "defaults": {
    "max_concurrency": 1,
    "max_wall_seconds": 900,
    "max_agent_starts": 1,
    "max_check_starts": 1,
    "default_timeout_seconds": 600,
    "max_artifact_bytes": 20000
  },
  "nodes": [
    {
      "id": "live-research",
      "type": "agent",
      "role": "research",
      "profile": "codex-readonly",
      "capabilities": ["repository-read"],
      "workspace": "read-only",
      "inputs": ["story"],
      "prompt": "Read the bounded story context. Return concise Markdown with exactly the headings Findings and Evidence. Do not edit files.",
      "outputs": [
        {
          "name": "live-findings",
          "format": "markdown",
          "path": "artifacts/live-findings.md",
          "required_sections": ["Findings", "Evidence"],
          "max_bytes": 12000
        }
      ],
      "timeout_seconds": 600,
      "on_failure": {"action": "abort"}
    },
    {
      "id": "human-handoff",
      "type": "approval",
      "needs": ["live-research"],
      "prompt": "Inspect the live adapter artifact.",
      "terminal": "awaiting-certification"
    }
  ]
}
JSON

git -C "$REPO" add .
git -C "$REPO" -c core.hooksPath=/dev/null commit -q -m "live driver fixture"

PYTHONPATH="$REPO/.githooks" CODEX_BIN="$CODEX_BIN" REPO="$REPO" \
  python3 - <<'PY'
import json
import os
import subprocess
from datetime import datetime, timedelta, timezone
from pathlib import Path

from dw_pmo.orchestration_driver import DriverManager, build_work_packet
from dw_pmo.orchestration_run import build_run_plan, claim_node, release_node_claim, start_run

root = Path(os.environ["REPO"])
now = datetime.now(timezone.utc).replace(microsecond=0)
plan = build_run_plan(
    root, "live-codex-research", "sample", "SMP-0-01",
    issued_at=now, expires_at=now + timedelta(minutes=15),
)
if not plan["applicable"]:
    raise SystemExit("live run plan refused: " + "; ".join(plan["issues"]))
run = start_run(
    root, plan, plan["start_token"], approved=True,
    approved_by="live-adapter-smoke", now=now,
)
claimed = claim_node(
    root, run["run_id"], "live-research", 1, "live-codex-claim",
    run["ledger_head"], now=now,
)
claim = claimed["active_claims"][0]
config = {
    "kind": "delivery-workbench-driver-config",
    "schema_version": 1,
    "workspace_root": None,
    "profiles": {
        "codex-readonly": {
            "adapter": "codex-exec",
            "capabilities": ["repository-read"],
            "workspace_modes": ["read-only"],
            "command": [os.environ["CODEX_BIN"]],
            "network": False,
            "max_context_bytes": 20000,
            "max_stream_bytes": 100000,
            "timeout_ceiling": 600,
        }
    },
}
packet = build_work_packet(root, run["run_id"], claim["claim_id"], config, now=now)
manager = DriverManager(root, config)
receipt = manager.start(packet, "live-codex-session")
if receipt["state"] != "succeeded":
    raise SystemExit("live Codex adapter failed: " + json.dumps(receipt, sort_keys=True))
artifacts = manager.collect(run["run_id"], receipt["session_id"])
projection = release_node_claim(
    root, run["run_id"], claim["claim_id"], "succeeded",
    sum(item["bytes"] for item in artifacts), claimed["ledger_head"],
)
print(json.dumps({
    "adapter": receipt["adapter"],
    "session_id": receipt["session_id"],
    "state": receipt["state"],
    "artifact": artifacts[0]["name"],
    "artifact_hash": artifacts[0]["sha256"],
    "checks": artifacts[0]["checks"],
    "ledger_events": projection["ledger_events"],
    "operator_tree_clean": subprocess.check_output(
        ["git", "-C", str(root), "status", "--porcelain"], text=True
    ) == "",
}, sort_keys=True))
PY

echo "codex-driver-smoke.sh: ok (authenticated read-only codex exec adapter)"
