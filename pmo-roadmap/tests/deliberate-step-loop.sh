#!/usr/bin/env bash
# Phase 23 exit exam: a wheel-installed consumer advances one real story by
# separately previewing and authorizing every deliberate step. The test never
# executes next_action argv itself; certification and commit stay manual.

set -eu

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PMO_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
ROOT="$(cd "$PMO_DIR/.." && pwd)"
TMP_ROOT="$(mktemp -d "${TMPDIR:-/tmp}/dw-deliberate-loop.XXXXXX")"

cleanup() {
  rm -rf "$TMP_ROOT"
}
trap cleanup EXIT

fail() {
  echo "deliberate-step-loop.sh: $1" >&2
  exit 1
}

# package-smoke.sh passes the CLI installed from its just-built wheel.
# Standalone runs build and install the same wheel contract first.
DW="${DW_STEP_CLI:-}"
if [ -n "$DW" ]; then
  [ -x "$DW" ] || fail "DW_STEP_CLI is not executable: $DW"
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
git -C "$REPO" config user.name "Deliberate Step Loop"
git -C "$REPO" config user.email "deliberate-step@example.test"

# Invoke the packaged launcher outside an adopted repo so it cannot defer to
# this source checkout's vendored rails.
(cd "$TMP_ROOT" && "$DW" install "$REPO" \
  --project-name "Deliberate Consumer" --project-slug deliberate --project-prefix DS) >/dev/null \
  || fail "packaged install failed"
(cd "$TMP_ROOT" && "$DW" update "$REPO" --check) >/dev/null \
  || fail "packaged update check failed"
(cd "$TMP_ROOT" && "$DW" update "$REPO") >/dev/null \
  || fail "packaged update failed"

# Leave a second story open so the exam can verify the post-commit handoff
# without closing the fixture phase.
"$REPO/.githooks/dw" --root "$REPO" story create deliberate 0 \
  "Follow-up deliberately left open" >/dev/null \
  || fail "could not create the follow-up story"

python3 - "$REPO" <<'PY' || fail "fresh-consumer deliberate-step sequence failed"
from __future__ import annotations

import hashlib
import json
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

root = Path(sys.argv[1]).resolve()
dw = root / ".githooks" / "dw"
mcp = root / ".githooks" / "dw-mcp"
workbench = root / ".githooks" / "dw-workbench"
project = "deliberate"
phase = "0"
story = "DS-0-01"
authorizations: list[str] = []


def run(argv, *, check=True, input_text=None):
    result = subprocess.run(
        [str(part) for part in argv],
        cwd=root,
        input=input_text,
        text=True,
        capture_output=True,
    )
    if check and result.returncode:
        raise AssertionError(
            f"command failed ({result.returncode}): {argv}\n"
            f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        )
    return result


def canonical(document):
    return json.dumps(
        document, ensure_ascii=False, separators=(",", ":"), sort_keys=True
    ).encode("utf-8")


def mcp_request(method, params=None, request_id=1):
    request = {"jsonrpc": "2.0", "id": request_id, "method": method}
    if params is not None:
        request["params"] = params
    result = run([mcp, "--root", root], input_text=json.dumps(request) + "\n")
    reply = json.loads(result.stdout)
    assert reply["id"] == request_id, reply
    return reply


def mcp_call(name, arguments):
    reply = mcp_request(
        "tools/call", {"name": name, "arguments": arguments}
    )
    assert "result" in reply, reply
    return reply["result"]


def http_json(url, *, body=None):
    data = None
    headers = {}
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        headers["Content-Type"] = "application/json"
    request = urllib.request.Request(url, data=data, headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            return response.status, json.load(response)
    except urllib.error.HTTPError as exc:
        return exc.code, json.load(exc)


def cli_preview():
    result = run([dw, "--root", root, "step", project, "--json"])
    return json.loads(result.stdout)


def mcp_preview():
    result = mcp_call("dw_step", {"project": project})
    assert not result.get("isError"), result
    return result["structuredContent"]


def http_preview(port):
    query = urllib.parse.urlencode({"project": project})
    status, body = http_json(f"http://127.0.0.1:{port}/api/step?{query}")
    assert status == 200 and body["ok"] is True, body
    return body["data"]


def tracked_snapshot():
    tracked = []
    for name in run(["git", "ls-files"]).stdout.splitlines():
        path = root / name
        digest = hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else "missing"
        tracked.append((name, digest))
    status = subprocess.check_output(
        ["git", "status", "--porcelain=v1", "-z"], cwd=root
    )
    events = root / ".git" / "pmo-events.jsonl"
    event_bytes = events.read_bytes() if events.is_file() else b""
    claims_dir = root / ".git" / "pmo-step-claims"
    claims = tuple(
        (path.name, path.read_bytes()) for path in sorted(claims_dir.glob("*.claim"))
    ) if claims_dir.is_dir() else ()
    contract = root / ".tmp" / "CONTRACT.md"
    contract_bytes = contract.read_bytes() if contract.is_file() else b""
    return tracked, status, event_bytes, claims, contract_bytes


def step_events():
    path = root / ".git" / "pmo-events.jsonl"
    if not path.exists():
        return []
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if json.loads(line).get("event") == "step_execution"
    ]


def preview_triplet(port, expected_action, applicable):
    before = tracked_snapshot()
    cli = cli_preview()
    via_mcp = mcp_preview()
    via_http = http_preview(port)
    after = tracked_snapshot()
    assert before == after, "step previews changed repository or rail state"
    assert canonical(cli) == canonical(via_mcp) == canonical(via_http)
    assert cli["kind"] == "delivery-workbench-step"
    assert cli["schema_version"] == 1
    assert cli["action"]["id"] == expected_action, cli
    assert cli["applicable"] is applicable, cli
    if applicable:
        assert cli["apply_command"][-2:] == ["--expect", cli["token"]]
    else:
        assert cli["apply_command"] is None and cli["refusal"]
    return cli


def apply_cli(token):
    result = run(
        [
            dw, "--root", root, "step", project, "--json", "--apply",
            "--expect", token,
        ],
        check=False,
    )
    return result.returncode, json.loads(result.stdout)


def apply_mcp(token):
    result = mcp_call("dw_step_apply", {"project": project, "expect": token})
    assert not result.get("isError"), result
    return result["structuredContent"]


def apply_http(port, token):
    return http_json(
        f"http://127.0.0.1:{port}/api/step/apply",
        body={"project": project, "expect": token},
    )


def authorize_one(port, preview, adapter):
    """Cross exactly one step boundary; never inspect/execute action argv."""
    before_events = len(step_events())
    if adapter == "cli":
        code, receipt = apply_cli(preview["token"])
        assert code == 0, receipt
    elif adapter == "mcp":
        receipt = apply_mcp(preview["token"])
    elif adapter == "http":
        status, body = apply_http(port, preview["token"])
        assert status == 200 and body["ok"] is True, body
        receipt = body["data"]
    else:
        raise AssertionError(f"unknown adapter: {adapter}")
    assert receipt["kind"] == "delivery-workbench-step-result"
    assert receipt["outcome"] == "succeeded" and receipt["started"] is True
    assert receipt["before"] == {
        "token": preview["token"], "action_id": preview["action"]["id"]
    }
    assert receipt["action"] == preview["action"]
    assert len(step_events()) == before_events + 1
    authorizations.append(preview["action"]["id"])
    print(
        f"authorize {len(authorizations):02d} {adapter:4s} "
        f"{preview['action']['id']:18s} -> {receipt['after']['action_id']}"
    )
    return receipt


def refuse_everywhere(port, preview, label):
    """The same non-started core receipt crosses every adapter unchanged."""
    before = tracked_snapshot()
    before_events = len(step_events())
    code, cli = apply_cli(preview["token"])
    assert code == 1 and cli["outcome"] == "refused", cli
    via_mcp = apply_mcp(preview["token"])
    status, body = apply_http(port, preview["token"])
    assert status == 409 and body["ok"] is False, body
    via_http = body["data"]
    assert canonical(cli) == canonical(via_mcp) == canonical(via_http)
    assert all(item["started"] is False for item in (cli, via_mcp, via_http))
    assert len(step_events()) == before_events
    assert tracked_snapshot() == before
    print(f"refuse   {label:22s} started=0 step_events=+0")
    return cli


def certify_manually():
    contract = root / ".tmp" / "CONTRACT.md"
    text = contract.read_text(encoding="utf-8")
    assert "- [ ]" in text
    # This is the exit-exam operator attesting after the assertions above,
    # deliberately outside CLI/MCP/HTTP step capabilities.
    contract.write_text(text.replace("- [ ]", "- [x]"), encoding="utf-8")


def commit_manually(message):
    before = len(step_events())
    run(["git", "commit", "-m", message])
    assert len(step_events()) == before, "manual commit became a step event"
    return run(["git", "rev-parse", "HEAD"]).stdout.strip()


with socket.socket() as sock:
    sock.bind(("127.0.0.1", 0))
    port = sock.getsockname()[1]
server = subprocess.Popen(
    [workbench, "--root", root, "--port", str(port), "--quiet"],
    cwd=root,
    stdout=subprocess.DEVNULL,
    stderr=subprocess.DEVNULL,
)
try:
    for _ in range(80):
        try:
            http_preview(port)
            break
        except Exception:
            if server.poll() is not None:
                raise AssertionError("installed workbench exited during startup")
            time.sleep(0.1)
    else:
        raise AssertionError("installed workbench did not start")

    # The wheel-installed browser ships the same two-act control. There is no
    # command input; its mutation body is project+token only.
    with urllib.request.urlopen(f"http://127.0.0.1:{port}/", timeout=10) as response:
        shell = response.read().decode("utf-8")
    with urllib.request.urlopen(f"http://127.0.0.1:{port}/app.js", timeout=10) as response:
        app_js = response.read().decode("utf-8")
    assert 'id="app"' in shell
    for token in ("step-review", "step-apply", 'postJson("/api/step/apply"',
                  "project: step.project", "expect: step.token", "nothing started"):
        assert token in app_js, token

    # Bootstrap the installed rails. Read-only review and contract generation
    # each consume their own lease; certification and commit refuse everywhere
    # before the test operator performs them manually.
    preview = preview_triplet(port, "review-workspace", True)
    authorize_one(port, preview, "cli")
    run(["git", "add", "-A"])
    preview = preview_triplet(port, "generate-contract", True)
    authorize_one(port, preview, "mcp")
    manual = preview_triplet(port, "certify-contract", False)
    refuse_everywhere(port, manual, "bootstrap certification")
    certify_manually()
    prohibited = preview_triplet(port, "commit", False)
    assert prohibited["action"]["command"] == ["git", "commit"]
    refuse_everywhere(port, prohibited, "bootstrap commit")
    bootstrap_head = commit_manually("Bootstrap deliberate consumer")
    assert run(["git", "status", "--porcelain"]).stdout == ""

    # Start the real story with one HTTP authorization. No test helper ever
    # calls the underlying story-status argv.
    preview = preview_triplet(port, "start-story", True)
    authorize_one(port, preview, "http")

    # Same action id, changed relevant state: the old continue-story token is
    # stale after app.py appears. All three attempts report started=false and
    # add zero step events/claims; the fresh lease remains usable.
    old = preview_triplet(port, "continue-story", True)
    (root / "app.py").write_text(
        'def answer():\n    return "deliberate"\n', encoding="utf-8"
    )
    fresh = preview_triplet(port, "continue-story", True)
    assert fresh["action"]["id"] == old["action"]["id"]
    assert fresh["token"] != old["token"]
    stale = refuse_everywhere(port, old, "same-id stale token")
    assert "stale" in stale["reason"]
    authorize_one(port, fresh, "mcp")

    # Evidence remains an explicit operator-chosen command outside step. Once
    # captured, the guarded finish transition gets its own fresh authorization.
    captured = run([
        dw, "evidence", "capture", project, phase, story, "--",
        "python3", "-c",
        'from pathlib import Path; assert "deliberate" in Path("app.py").read_text()',
    ])
    evidence_path, exit_code, captured_at = captured.stdout.strip().split("\t")
    assert exit_code == "0" and captured_at.endswith("Z")
    assert (root / evidence_path).is_file()
    preview = preview_triplet(port, "finish-story", True)
    authorize_one(port, preview, "cli")

    # Review is itself a separately consumed read-only step. Staging remains
    # explicit operator work; generation is one more exact HTTP lease.
    preview = preview_triplet(port, "review-workspace", True)
    authorize_one(port, preview, "http")
    run(["git", "add", "-A"])
    preview = preview_triplet(port, "generate-contract", True)
    authorize_one(port, preview, "cli")

    manual = preview_triplet(port, "certify-contract", False)
    refuse_everywhere(port, manual, "story certification")
    certify_manually()
    prohibited = preview_triplet(port, "commit", False)
    assert prohibited["action"]["command"] == ["git", "commit"]
    refuse_everywhere(port, prohibited, "story commit")
    head = commit_manually(f"Complete {story}: deliberate packaged loop")

    # Durable outcome: manual commit trailers/archive, history verification,
    # the exact expected step-event sequence, and a clean next-story lease.
    trailers = run(["git", "log", "-1", "--format=%(trailers)"]).stdout
    assert f"PMO-Story: {story}" in trailers
    assert "PMO-Contract-Digest: sha256:" in trailers
    archive = root / ".git" / "pmo-contract-archive" / head / "CONTRACT.md"
    assert archive.is_file() and "- [x]" in archive.read_text(encoding="utf-8")
    run([dw, "verify", "--all"])
    final = preview_triplet(port, "start-story", True)
    assert run(["git", "status", "--porcelain"]).stdout == ""
    actions = [event["detail"]["action"] for event in step_events()]
    assert actions == [
        "review-workspace", "generate-contract", "start-story",
        "continue-story", "finish-story", "review-workspace",
        "generate-contract",
    ], actions
    assert authorizations == actions
    print(f"bootstrap  {bootstrap_head[:12]}         certification+commit=manual")
    print(f"commit     {head[:12]}         trailers+archive+verify=ok")
    print(f"handoff    {final['action']['id']:18s} authorizations={len(authorizations)}")
finally:
    server.terminate()
    try:
        server.wait(timeout=10)
    except subprocess.TimeoutExpired:
        server.kill()
        server.wait(timeout=5)
PY

echo "deliberate-step-loop.sh: ok (fresh token per action; no argv reconstruction or consent shortcut)"
