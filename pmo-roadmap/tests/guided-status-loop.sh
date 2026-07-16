#!/usr/bin/env bash
# Phase 22 exit exam: a packaged consumer follows dw status from install
# through an evidence-backed, gated story commit. Every transition asserts
# the recommendation before acting; red paths must never recommend commit.

set -eu

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PMO_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
ROOT="$(cd "$PMO_DIR/.." && pwd)"
TMP_ROOT="$(mktemp -d "${TMPDIR:-/tmp}/dw-guided-loop.XXXXXX")"

cleanup() {
  rm -rf "$TMP_ROOT"
}
trap cleanup EXIT

fail() {
  echo "guided-status-loop.sh: $1" >&2
  exit 1
}

# package-smoke.sh passes the CLI it installed from its just-built wheel.
# Standalone runs build and install that same wheel contract themselves.
DW="${DW_GUIDED_CLI:-}"
if [ -n "$DW" ]; then
  [ -x "$DW" ] || fail "DW_GUIDED_CLI is not executable: $DW"
  DW="$(cd "$(dirname "$DW")" && pwd)/$(basename "$DW")"
else
  PY=""
  for candidate in "${PMO_PACKAGE_PYTHON:-}" python3 /usr/bin/python3; do
    [ -n "$candidate" ] || continue
    command -v "$candidate" >/dev/null 2>&1 || continue
    probe="$TMP_ROOT/probe-venv"
    rm -rf "$probe"
    if "$candidate" -c "import pyexpat" >/dev/null 2>&1 \
      && "$candidate" -m venv "$probe" >/dev/null 2>&1 \
      && "$probe/bin/python" -m pip --version >/dev/null 2>&1; then
      PY="$candidate"
      break
    fi
  done
  [ -n "$PY" ] || fail "no interpreter with working venv+pip found"

  buildenv="$TMP_ROOT/buildenv"
  appenv="$TMP_ROOT/appenv"
  "$PY" -m venv "$buildenv"
  "$buildenv/bin/python" -m pip install --quiet --upgrade pip build \
    || fail "could not install the package builder"
  (cd "$ROOT" && "$buildenv/bin/python" -m build --wheel --outdir "$TMP_ROOT/dist") >/dev/null \
    || fail "wheel build failed"
  wheel="$(ls "$TMP_ROOT"/dist/*.whl)"
  "$PY" -m venv "$appenv"
  "$appenv/bin/python" -m pip install --quiet "$wheel" \
    || fail "wheel install failed"
  DW="$appenv/bin/dw"
fi

REPO="$TMP_ROOT/consumer"
mkdir -p "$REPO"
git -C "$REPO" init -q -b main
git -C "$REPO" config user.name "Guided Status Loop"
git -C "$REPO" config user.email "guided-status@example.test"

# Run the packaged launcher outside any adopted repo so defer-to-repo cannot
# accidentally substitute this checkout's source rails.
(cd "$TMP_ROOT" && "$DW" install "$REPO" \
  --project-name "Guided Consumer" --project-slug guided --project-prefix GS) >/dev/null \
  || fail "packaged install failed"
(cd "$TMP_ROOT" && "$DW" update "$REPO" --check) >/dev/null \
  || fail "packaged update check did not recognize the installed rails"
(cd "$TMP_ROOT" && "$DW" update "$REPO") >/dev/null \
  || fail "packaged update failed"

# Keep one follow-up story open so completing the exam story does not also
# require phase closure; this fixture is about the story/commit loop.
"$REPO/.githooks/dw" --root "$REPO" story create guided 0 \
  "Follow-up deliberately left open" >/dev/null \
  || fail "could not add the follow-up story"

python3 - "$REPO" <<'PY' || fail "guided recommendation sequence failed"
from __future__ import annotations

import hashlib
import json
import os
import socket
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

root = Path(sys.argv[1]).resolve()
dw = root / ".githooks" / "dw"
mcp = root / ".githooks" / "dw-mcp"
workbench = root / ".githooks" / "dw-workbench"
project = "guided"


def run(argv, *, check=True, input_text=None):
    result = subprocess.run(
        [str(part) for part in argv], cwd=root, input=input_text,
        text=True, capture_output=True,
    )
    if check and result.returncode:
        raise AssertionError(
            f"command failed ({result.returncode}): {argv}\n"
            f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        )
    return result


def tracked_snapshot():
    names = run(["git", "ls-files"]).stdout.splitlines()
    files = []
    for name in names:
        path = root / name
        digest = hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else "missing"
        files.append((name, digest))
    porcelain = subprocess.check_output(
        ["git", "status", "--porcelain=v1", "-z"], cwd=root
    )
    events = root / ".git" / "pmo-events.jsonl"
    return files, porcelain, events.read_bytes() if events.is_file() else b""


def cli_status():
    result = run([dw, "--root", root, "status", project, "--json"], check=False)
    assert result.returncode in (0, 1), result.stderr
    payload = json.loads(result.stdout)
    assert result.returncode == (0 if payload["verdict"] == "ready" else 1)
    return payload


def mcp_status():
    request = {
        "jsonrpc": "2.0", "id": 1, "method": "tools/call",
        "params": {"name": "dw_status", "arguments": {"project": project}},
    }
    result = run(
        [mcp, "--root", root], input_text=json.dumps(request) + "\n"
    )
    reply = json.loads(result.stdout)["result"]
    assert not reply.get("isError"), reply
    return reply["structuredContent"]


def http_status(port):
    with urllib.request.urlopen(
        f"http://127.0.0.1:{port}/api/status?project={project}", timeout=10
    ) as response:
        assert response.status == 200
        body = json.load(response)
    assert body["ok"] is True  # attention is successful status data
    return body["data"]


def parity(port, action_id, verdict="ready"):
    before = tracked_snapshot()
    cli = cli_status()
    mcp_payload = mcp_status()
    http_payload = http_status(port)
    after = tracked_snapshot()
    assert before == after, "status reads changed tracked state or rail events"
    assert cli == mcp_payload == http_payload
    assert cli["verdict"] == verdict, cli
    assert cli["next_action"]["id"] == action_id, cli["next_action"]
    print(f"{verdict:9s} {action_id:18s} {cli['repository']['contract']['state']:10s} {cli['repository']['gate']['state']}")
    return cli


def execute(action, *extra):
    command = action["command"]
    assert action["kind"] == "command" and command, action
    return run(command + list(extra))


def certify():
    path = root / ".tmp" / "CONTRACT.md"
    text = path.read_text(encoding="utf-8")
    unchecked = text.count("- [ ]")
    assert unchecked, "manual certification expected unchecked rules"
    # This is the exit-exam operator's deliberate attestation after the
    # preceding assertions and test capture, never a product API/tool.
    path.write_text(text.replace("- [ ]", "- [x]"), encoding="utf-8")


with socket.socket() as sock:
    sock.bind(("127.0.0.1", 0))
    port = sock.getsockname()[1]
server = subprocess.Popen(
    [str(workbench), "--root", str(root), "--port", str(port), "--quiet"],
    cwd=root, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
)
try:
    for _ in range(80):
        try:
            http_status(port)
            break
        except Exception:
            if server.poll() is not None:
                raise AssertionError("installed workbench exited during startup")
            time.sleep(0.1)
    else:
        raise AssertionError("installed workbench did not start")

    # Bootstrap commit: make the packaged install a clean starting point,
    # following the same review → contract → certify → commit recommendations.
    current = parity(port, "review-workspace")
    execute(current["next_action"])
    run(["git", "add", "-A"])
    current = parity(port, "generate-contract")
    execute(current["next_action"])
    current = parity(port, "certify-contract")
    assert current["next_action"]["kind"] == "manual"
    assert current["next_action"]["command"] is None
    certify()
    current = parity(port, "commit")
    execute(current["next_action"], "-m", "Bootstrap guided consumer")

    # Clean → in-progress. The action itself supplies the selected story,
    # phase, and project; the test never reconstructs those facts.
    current = parity(port, "start-story")
    start = current["next_action"]
    assert start["command"][-1] == "in-progress"
    execute(start)
    project_slug, phase, story = start["command"][3:6]
    assert project_slug == project
    current = parity(port, "continue-story")
    execute(current["next_action"])

    # The guarded mutation refuses done without evidence.
    refused = run(
        [dw, "story", "status", project, phase, story, "done"], check=False
    )
    assert refused.returncode == 1
    assert "evidence" in (refused.stdout + refused.stderr).lower()
    assert cli_status()["next_action"]["id"] != "commit"

    # Plant the equivalent malformed Markdown state to prove aggregate status
    # promotes missing evidence to attention, then restore byte-for-byte.
    phase_dir = next((root / "pm" / "roadmap" / project).glob("phase-*/current-phase-status.md")).parent
    story_path = next(
        path for path in phase_dir.glob("story-*.md")
        if story in path.read_text(encoding="utf-8")
    )
    phase_path = phase_dir / "current-phase-status.md"
    good_story = story_path.read_text(encoding="utf-8")
    good_phase = phase_path.read_text(encoding="utf-8")
    story_path.write_text(
        good_story.replace("- **Status:** in-progress", "- **Status:** done"),
        encoding="utf-8",
    )
    phase_path.write_text(
        good_phase.replace("| in-progress |", "| done |", 1), encoding="utf-8"
    )
    broken = parity(port, "repair-roadmap", "attention")
    assert broken["next_action"]["blocking"] is True
    assert broken["next_action"]["id"] != "commit"
    story_path.write_text(good_story, encoding="utf-8")
    phase_path.write_text(good_phase, encoding="utf-8")
    parity(port, "continue-story")

    # Do and prove real work, then flip through the guarded mutation.
    (root / "app.py").write_text(
        'def answer():\n    return "guided"\n', encoding="utf-8"
    )
    parity(port, "continue-story")
    captured = run([
        dw, "evidence", "capture", project, phase, story, "--",
        "python3", "-c",
        'from pathlib import Path; assert "guided" in Path("app.py").read_text()',
    ])
    evidence_path, exit_code, capture_ts = captured.stdout.strip().split("\t")
    assert exit_code == "0" and (root / evidence_path).is_file() and capture_ts.endswith("Z")
    evidenced = parity(port, "finish-story", "attention")
    assert evidenced["next_action"]["command"][-1] == "done"
    execute(evidenced["next_action"])
    current = parity(port, "review-workspace")
    execute(current["next_action"])

    # Stage → generate → stale-on-restage → regenerate. At no point may a
    # stale contract recommend commit.
    run(["git", "add", "-A"])
    current = parity(port, "generate-contract")
    execute(current["next_action"])
    manual = parity(port, "certify-contract")
    assert manual["next_action"]["kind"] == "manual"
    (root / "operator-notes.md").write_text(
        "# Operator notes\n\nRestaged deliberately for the stale-contract red path.\n",
        encoding="utf-8",
    )
    run(["git", "add", "operator-notes.md"])
    stale = parity(port, "generate-contract")
    assert stale["repository"]["contract"]["state"] == "stale"
    assert stale["next_action"]["command"][-1] == "--force"
    assert stale["next_action"]["id"] != "commit"
    execute(stale["next_action"])

    manual = parity(port, "certify-contract")
    assert manual["next_action"]["kind"] == "manual"
    certify()
    ready = parity(port, "commit")
    assert ready["repository"]["gate"]["state"] == "pass"
    execute(ready["next_action"], "-m", f"Complete {story}: guided packaged loop")

    # Durable proof: trailers, archived certified contract, pushed-history
    # verifier, and a clean next recommendation for the remaining story.
    head = run(["git", "rev-parse", "HEAD"]).stdout.strip()
    trailers = run(["git", "log", "-1", "--format=%(trailers)"]).stdout
    assert f"PMO-Story: {story}" in trailers
    assert "PMO-Contract-Digest: sha256:" in trailers
    archive = root / ".git" / "pmo-contract-archive" / head / "CONTRACT.md"
    assert archive.is_file() and "- [x]" in archive.read_text(encoding="utf-8")
    run([dw, "verify", "--all"])
    final = parity(port, "start-story")
    assert final["repository"]["clean"] is True
    print(f"commit     {head[:12]}         trailers+archive+verify=ok")
finally:
    server.terminate()
    try:
        server.wait(timeout=10)
    except subprocess.TimeoutExpired:
        server.kill()
        server.wait(timeout=5)
PY

echo "guided-status-loop.sh: ok (packaged CLI/MCP/HTTP recommendation sequence)"
