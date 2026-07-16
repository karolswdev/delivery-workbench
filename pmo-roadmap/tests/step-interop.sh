#!/usr/bin/env bash
# WLA-23-03: the deliberate step is one core capability across CLI, MCP,
# and HTTP. A freshly installed fixture proves byte-stable core documents,
# exact-token application, replay refusal, and the certification/commit floor.

set -eu

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PMO_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
TMP_ROOT="$(mktemp -d "${TMPDIR:-/tmp}/dw-step-interop.XXXXXX")"

cleanup() {
  rm -rf "$TMP_ROOT"
}
trap cleanup EXIT

fail() {
  echo "step-interop.sh: $1" >&2
  exit 1
}

REPO="$TMP_ROOT/consumer"
mkdir -p "$REPO"
git -C "$REPO" init -q -b main
git -C "$REPO" config user.name "Step Interop"
git -C "$REPO" config user.email "step-interop@example.test"

"$PMO_DIR/install.sh" "$REPO" \
  --project-name "Step Interop" --project-slug interop --project-prefix SI \
  >/dev/null || fail "fixture install failed"
git -C "$REPO" add -A
git -C "$REPO" commit -q --no-verify -m "fixture scaffold"

python3 - "$REPO" <<'PY' || fail "transport parity or consent-floor assertion failed"
from __future__ import annotations

import json
import shutil
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
project = "interop"


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


def preview_parity(port, expected_action, applicable):
    cli = cli_preview()
    via_mcp = mcp_preview()
    via_http = http_preview(port)
    assert canonical(cli) == canonical(via_mcp) == canonical(via_http)
    assert cli["kind"] == "delivery-workbench-step"
    assert cli["schema_version"] == 1
    assert cli["action"]["id"] == expected_action, cli
    assert cli["applicable"] is applicable, cli
    return cli


def reset_fixture():
    run(["git", "reset", "--hard", "-q", "HEAD"])
    run(["git", "clean", "-fdq"])
    shutil.rmtree(root / ".git" / "pmo-step-claims", ignore_errors=True)
    events = root / ".git" / "pmo-events.jsonl"
    if events.exists():
        events.unlink()
    shutil.rmtree(root / ".tmp", ignore_errors=True)


def step_events():
    path = root / ".git" / "pmo-events.jsonl"
    if not path.exists():
        return []
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if json.loads(line).get("event") == "step_execution"
    ]


def cli_apply(token):
    result = run(
        [
            dw,
            "--root",
            root,
            "step",
            project,
            "--json",
            "--apply",
            "--expect",
            token,
        ],
        check=False,
    )
    return result.returncode, json.loads(result.stdout)


def mcp_apply(token):
    result = mcp_call("dw_step_apply", {"project": project, "expect": token})
    assert not result.get("isError"), result
    return result["structuredContent"]


def http_apply(port, token, **extra):
    payload = {"project": project, "expect": token}
    payload.update(extra)
    return http_json(f"http://127.0.0.1:{port}/api/step/apply", body=payload)


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

    # Inventory is closed: neither step adapter accepts caller-supplied argv,
    # certification, or commit authority.
    tools_reply = mcp_request("tools/list")
    tools = {item["name"]: item for item in tools_reply["result"]["tools"]}
    assert {"dw_step", "dw_step_apply"} <= set(tools)
    apply_schema = tools["dw_step_apply"]["inputSchema"]
    assert set(apply_schema["properties"]) == {"project", "expect"}
    assert apply_schema["required"] == ["expect"]
    assert apply_schema["additionalProperties"] is False

    # Each adapter starts from the identical committed state and empty lease
    # generation. Their core previews and execution receipts must be exact.
    receipts = []

    reset_fixture()
    preview = preview_parity(port, "start-story", True)
    code, receipt = cli_apply(preview["token"])
    assert code == 0 and receipt["outcome"] == "succeeded", receipt
    assert len(step_events()) == 1
    receipts.append(receipt)

    reset_fixture()
    preview = preview_parity(port, "start-story", True)
    receipt = mcp_apply(preview["token"])
    assert receipt["outcome"] == "succeeded", receipt
    assert len(step_events()) == 1
    receipts.append(receipt)

    reset_fixture()
    preview = preview_parity(port, "start-story", True)
    status, body = http_apply(port, preview["token"])
    assert status == 200 and body["ok"] is True, body
    receipt = body["data"]
    assert receipt["outcome"] == "succeeded", receipt
    receipts.append(receipt)

    encoded = [canonical(item) for item in receipts]
    assert encoded[0] == encoded[1] == encoded[2]
    assert receipt["started"] is True and receipt["exit_code"] == 0
    assert receipt["before"]["action_id"] == "start-story"
    assert receipt["after"]["action_id"] == "continue-story"
    assert len(step_events()) == 1

    # The same lease cannot cross the boundary twice, and a refusal emits no
    # second execution event.
    status, replay = http_apply(port, preview["token"])
    assert status == 409 and replay["ok"] is False, replay
    assert replay["data"]["outcome"] == "refused"
    assert replay["data"]["started"] is False
    assert len(step_events()) == 1

    # Caller-supplied commands are rejected at both remote adapter schemas.
    injected = mcp_call(
        "dw_step_apply",
        {"project": project, "expect": preview["token"], "command": ["git", "commit"]},
    )
    assert injected.get("isError") is True, injected
    assert "unknown parameter" in injected["content"][0]["text"]
    status, rejected = http_apply(port, preview["token"], command=["git", "commit"])
    assert status == 400 and rejected["ok"] is False, rejected
    assert "unknown step parameter" in rejected["data"]["error"]

    # Certification is a manual recommendation and commit is an operator
    # action. All transports preview both states identically, but none apply.
    reset_fixture()
    readme = root / "pm" / "roadmap" / project / "README.md"
    readme.write_text(readme.read_text(encoding="utf-8") + "\nInterop proof.\n", encoding="utf-8")
    run(["git", "add", str(readme.relative_to(root))])
    run([dw, "--root", root, "contract", "new"])

    manual = preview_parity(port, "certify-contract", False)
    code, cli_refusal = cli_apply(manual["token"])
    assert code == 1 and cli_refusal["outcome"] == "refused"
    mcp_refusal = mcp_apply(manual["token"])
    status, http_refusal = http_apply(port, manual["token"])
    assert status == 409
    assert canonical(cli_refusal) == canonical(mcp_refusal) == canonical(http_refusal["data"])
    assert step_events() == []

    contract = root / ".tmp" / "CONTRACT.md"
    contract_text = contract.read_text(encoding="utf-8")
    assert "- [ ]" in contract_text
    contract.write_text(contract_text.replace("- [ ]", "- [x]"), encoding="utf-8")

    head_before = run(["git", "rev-parse", "HEAD"]).stdout
    staged_before = run(["git", "diff", "--cached", "--binary"]).stdout
    commit = preview_parity(port, "commit", False)
    code, cli_refusal = cli_apply(commit["token"])
    assert code == 1 and cli_refusal["outcome"] == "refused"
    mcp_refusal = mcp_apply(commit["token"])
    status, http_refusal = http_apply(port, commit["token"])
    assert status == 409
    assert canonical(cli_refusal) == canonical(mcp_refusal) == canonical(http_refusal["data"])
    assert run(["git", "rev-parse", "HEAD"]).stdout == head_before
    assert run(["git", "diff", "--cached", "--binary"]).stdout == staged_before
    assert step_events() == []

    print("preview parity: CLI = MCP = HTTP")
    print("result parity:  CLI = MCP = HTTP")
    print("replay/injection: refused without another child")
    print("certification/commit: previewable, never applicable")
finally:
    server.terminate()
    try:
        server.wait(timeout=10)
    except subprocess.TimeoutExpired:
        server.kill()
        server.wait(timeout=10)
PY

echo "step-interop.sh: ok"
