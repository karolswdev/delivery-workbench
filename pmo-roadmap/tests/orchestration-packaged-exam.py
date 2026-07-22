#!/usr/bin/env python3
"""Phase-24 exit exam against one wheel-installed fresh consumer.

The deterministic fixture driver is the scheduling oracle.  A separately
provisioned Codex smoke covers the real adapter seam; variable model output is
deliberately not a release oracle here.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path


def run(argv, *, cwd, check=True, input_text=None):
    result = subprocess.run(
        [str(part) for part in argv], cwd=str(cwd), input=input_text,
        text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )
    if check and result.returncode:
        raise AssertionError(
            "command failed ({}): {}\nstdout:\n{}\nstderr:\n{}".format(
                result.returncode, argv, result.stdout, result.stderr
            )
        )
    return result


def write_json(path, document):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(document, indent=2) + "\n", encoding="utf-8")


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dw", required=True, type=Path)
    parser.add_argument("--keep", action="store_true")
    args = parser.parse_args()
    global_dw = args.dw.resolve()
    if not global_dw.is_file():
        raise SystemExit("packaged dw is absent: {}".format(global_dw))

    temporary = Path(tempfile.mkdtemp(prefix="dw-orchestration-exam.")).resolve()
    root = temporary / "consumer"
    root.mkdir()
    server = None
    try:
        run(["git", "init", "-q", "-b", "main"], cwd=root)
        run(["git", "config", "user.name", "Orchestration Exam Operator"], cwd=root)
        run(["git", "config", "user.email", "orchestration-exam@example.test"], cwd=root)
        run([
            global_dw, "install", root,
            "--project-name", "Orchestration Consumer",
            "--project-slug", "sample", "--project-prefix", "SMP",
        ], cwd=temporary)
        dw = root / ".githooks" / "dw"
        mcp = root / ".githooks" / "dw-mcp"
        workbench = root / ".githooks" / "dw-workbench"
        for executable in (dw, mcp, workbench):
            assert executable.is_file(), executable

        # Keep the phase open after the exam story is finished, and bind every
        # run to a clean in-progress story.
        run([dw, "--root", root, "story", "create", "sample", "0",
             "Follow-up deliberately left open"], cwd=root)
        schema_path = root / "schemas" / "risk-register-v1.json"
        write_json(schema_path, {
            "type": "object", "required": ["risks"],
            "properties": {"risks": {"type": "array", "items": {"type": "string"}}},
            "additionalProperties": False,
        })

        defaults = {
            "max_concurrency": 2, "max_wall_seconds": 3600,
            "max_agent_starts": 4, "max_check_starts": 4,
            "default_timeout_seconds": 60, "max_artifact_bytes": 100000,
        }
        runtime_scores = {
            "expiry-exam": {
                "kind": "delivery-workbench-orchestration", "schema_version": 1,
                "slug": "expiry-exam", "title": "Expiry refusal", "project": "sample",
                "defaults": defaults,
                "nodes": [{"id": "handoff", "type": "approval",
                           "prompt": "Review", "terminal": "awaiting-certification"}],
            },
            "budget-exam": {
                "kind": "delivery-workbench-orchestration", "schema_version": 1,
                "slug": "budget-exam", "title": "Budget refusal", "project": "sample",
                "defaults": dict(defaults, max_agent_starts=1),
                "nodes": [
                    {"id": "one", "type": "agent", "role": "research",
                     "profile": "reasoning-readonly", "capabilities": ["repository-read"],
                     "workspace": "read-only", "on_failure": {"action": "abort"}},
                    {"id": "two", "type": "agent", "role": "research",
                     "profile": "reasoning-readonly", "capabilities": ["repository-read"],
                     "workspace": "read-only", "on_failure": {"action": "abort"}},
                    {"id": "handoff", "type": "approval", "needs": ["one", "two"],
                     "prompt": "Review", "terminal": "awaiting-certification"},
                ],
            },
            "stale-rail-exam": {
                "kind": "delivery-workbench-orchestration", "schema_version": 1,
                "slug": "stale-rail-exam", "title": "Stale rail refusal", "project": "sample",
                "defaults": defaults,
                "nodes": [{"id": "advance", "type": "rail", "action": "start-story",
                           "on_failure": {"action": "abort"}}],
            },
            "cancel-exam": {
                "kind": "delivery-workbench-orchestration", "schema_version": 1,
                "slug": "cancel-exam", "title": "Cancellation", "project": "sample",
                "defaults": defaults,
                "nodes": [{"id": "worker", "type": "agent", "role": "research",
                           "profile": "reasoning-readonly",
                           "capabilities": ["repository-read"], "workspace": "read-only",
                           "on_failure": {"action": "abort"}}],
            },
        }
        for slug, document in runtime_scores.items():
            write_json(root / "pm" / "orchestration" / (slug + ".json"), document)

        def cli_status():
            result = run([dw, "--root", root, "status", "sample", "--json"],
                         cwd=root, check=False)
            assert result.returncode in (0, 1), result.stderr
            return json.loads(result.stdout)

        def execute_action(payload, *extra):
            action = payload["next_action"]
            assert action["kind"] == "command" and action["command"], action
            return run(list(action["command"]) + list(extra), cwd=root)

        def certify_contract():
            contract = root / ".tmp" / "CONTRACT.md"
            text = contract.read_text(encoding="utf-8")
            assert "- [ ]" in text, "operator certification had no unchecked rules"
            contract.write_text(text.replace("- [ ]", "- [x]"), encoding="utf-8")

        # The first commit is made through the product's review/contract/manual
        # certification/commit spine.  The orchestration runtime has no route
        # into any of these steps.
        status = cli_status()
        assert status["next_action"]["id"] == "review-workspace", status["next_action"]
        execute_action(status)
        run(["git", "add", "-A"], cwd=root)
        status = cli_status()
        assert status["next_action"]["id"] == "generate-contract", status["next_action"]
        execute_action(status)
        status = cli_status()
        assert status["next_action"]["id"] == "certify-contract", status["next_action"]
        assert status["next_action"]["kind"] == "manual"
        certify_contract()
        status = cli_status()
        assert status["next_action"]["id"] == "commit", status["next_action"]
        execute_action(status, "-m", "Bootstrap packaged orchestration exam")
        assert not run(["git", "status", "--porcelain"], cwd=root).stdout

        run([dw, "--root", root, "story", "status", "sample", "0",
             "SMP-0-01", "in-progress"], cwd=root)
        run(["git", "add", "-A"], cwd=root)
        status = cli_status()
        assert status["next_action"]["id"] == "generate-contract", status["next_action"]
        execute_action(status)
        status = cli_status()
        assert status["next_action"]["id"] == "certify-contract", status["next_action"]
        certify_contract()
        status = cli_status()
        assert status["next_action"]["id"] == "commit", status["next_action"]
        execute_action(status, "-m", "Start SMP-0-01: packaged orchestration exam")
        assert not run(["git", "status", "--porcelain"], cwd=root).stdout

        # Import only the wheel-installed/vendored core from the consumer.
        sys.path.insert(0, str(root / ".githooks"))
        from dw_pmo import (  # noqa: import after isolated install
            DwError, FixtureDriver, apply_run_act, build_run_act_preview,
            build_run_plan, build_run_view, build_score_mutation_plan,
            compile_score, compile_score_path, load_score, replay_run,
            run_summary_inventory, score_mutation_preview, start_run,
            tick_run, validate_score,
        )
        from dw_pmo.orchestration_driver import artifact_inventory
        from dw_pmo.workbench import handle_api

        reference_path = root / "pm" / "orchestration" / "research-build-review.json"
        raw = load_score(reference_path)
        compiled = compile_score_path(reference_path)
        status_code, visual = handle_api(
            root, "/api/orchestration/research-build-review", {}
        )
        assert status_code == 200
        visual_doc = visual["data"]
        assert visual_doc["raw"] == raw
        assert visual_doc["compiled"] == compiled
        round_trip = json.loads(json.dumps(visual_doc["raw"], sort_keys=True))
        round_compiled = compile_score(round_trip)
        assert round_compiled["semantic_hash"] == compiled["semantic_hash"]
        assert round_compiled["document_hash"] == compiled["document_hash"]
        visual_preview = score_mutation_preview(build_score_mutation_plan(
            root, "save", "research-build-review", round_trip
        ))
        assert visual_preview["compiled"]["semantic_hash"] == compiled["semantic_hash"]
        assert visual_preview["starts_work"] is False
        assert visual_preview["writes_events"] is False

        # Compiler red matrix: each class is refused as data in the same fresh
        # installed package, without creating a run or an executor session.
        minimal = {
            "kind": "delivery-workbench-orchestration", "schema_version": 1,
            "slug": "red", "title": "Red",
            "nodes": [{"id": "handoff", "type": "approval", "prompt": "Review",
                       "terminal": "awaiting-certification"}],
        }
        red = {}
        cycle = copy.deepcopy(minimal)
        cycle["nodes"] = [
            {"id": "a", "type": "approval", "needs": ["b"], "prompt": "A"},
            {"id": "b", "type": "approval", "needs": ["a"], "prompt": "B",
             "terminal": "awaiting-certification"},
        ]
        red["cycle"] = cycle
        dangling = copy.deepcopy(minimal)
        dangling["nodes"].insert(0, {
            "id": "consumer", "type": "agent", "role": "synthesis",
            "profile": "reasoning-readonly", "capabilities": ["repository-read"],
            "workspace": "read-only",
            "inputs": [{"artifact": "missing", "format": "markdown"}],
        })
        red["dangling-output"] = dangling
        shell = copy.deepcopy(minimal)
        shell["nodes"].insert(0, {
            "id": "check", "type": "check",
            "runner": {"kind": "command", "shell": "pytest -q", "cwd": ".",
                       "timeout_seconds": 10, "output_bytes": 1000, "writes": []},
        })
        red["shell-check"] = shell
        escaped = copy.deepcopy(minimal)
        escaped["nodes"].insert(0, {
            "id": "check", "type": "check",
            "runner": {"kind": "builtin", "name": "file-exists", "path": "../escape"},
        })
        red["path-escape"] = escaped
        unbounded = copy.deepcopy(minimal)
        unbounded["nodes"].insert(0, {
            "id": "agent", "type": "agent", "role": "research",
            "profile": "reasoning-readonly", "capabilities": ["repository-read"],
            "workspace": "read-only", "on_failure": {"action": "retry"},
        })
        red["unbounded-retry"] = unbounded
        capability = copy.deepcopy(minimal)
        capability["nodes"].insert(0, {
            "id": "agent", "type": "agent", "role": "research",
            "profile": "reasoning-readonly", "capabilities": ["repository-root"],
            "workspace": "read-only",
        })
        red["unsupported-capability"] = capability
        red_diagnostics = {}
        for name, document in red.items():
            result = validate_score(document)
            assert result["valid"] is False, name
            assert result["diagnostics"], name
            red_diagnostics[name] = [item["code"] for item in result["diagnostics"]]

        # Start the installed HTTP adapter before planning so the exact plan
        # can be compared over direct core, CLI, MCP, and HTTP.
        with socket.socket() as sock:
            sock.bind(("127.0.0.1", 0))
            port = sock.getsockname()[1]
        server = subprocess.Popen(
            [str(workbench), "--root", str(root), "--port", str(port), "--quiet"],
            cwd=str(root), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
        base = "http://127.0.0.1:{}".format(port)

        def http(method, route, payload=None, expected=200):
            data = None
            headers = {}
            if payload is not None:
                data = json.dumps(payload).encode("utf-8")
                headers["Content-Type"] = "application/json"
            request = urllib.request.Request(base + route, data=data, headers=headers, method=method)
            try:
                response = urllib.request.urlopen(request, timeout=10)
                code = response.status
                body = json.load(response)
            except urllib.error.HTTPError as exc:
                code = exc.code
                body = json.load(exc)
            assert code == expected, (route, code, body)
            return body

        for _ in range(80):
            try:
                http("GET", "/api/projects")
                break
            except Exception:
                if server.poll() is not None:
                    raise AssertionError("installed Workbench exited during startup")
                time.sleep(0.1)
        else:
            raise AssertionError("installed Workbench did not start")

        def cli_json(*parts):
            return json.loads(run([dw, "--root", root] + list(parts), cwd=root).stdout)

        def call_mcp(name, arguments):
            request = {
                "jsonrpc": "2.0", "id": 1, "method": "tools/call",
                "params": {"name": name, "arguments": arguments},
            }
            result = run([mcp, "--root", root], cwd=root,
                         input_text=json.dumps(request) + "\n")
            payload = json.loads(result.stdout)["result"]
            assert not payload.get("isError"), payload
            return payload["structuredContent"]

        now = datetime.now(timezone.utc).replace(microsecond=0)
        issued = now.isoformat().replace("+00:00", "Z")
        expires = (now + timedelta(hours=1)).isoformat().replace("+00:00", "Z")
        plan_args = {
            "score": "research-build-review", "project": "sample",
            "story": "SMP-0-01", "issued_at": issued, "expires_at": expires,
        }
        plan = build_run_plan(
            root, "research-build-review", "sample", "SMP-0-01",
            issued_at=issued, expires_at=expires,
        )
        cli_plan = cli_json(
            "run", "plan", "research-build-review", "--project", "sample",
            "--story", "SMP-0-01", "--issued-at", issued,
            "--expires-at", expires, "--json",
        )
        mcp_plan = call_mcp("dw_run_plan", plan_args)
        query = urllib.parse.urlencode(plan_args)
        http_plan = http("GET", "/api/run-plan?" + query)["data"]
        assert plan == cli_plan == mcp_plan == http_plan

        config = {
            "kind": "delivery-workbench-driver-config", "schema_version": 1,
            "workspace_root": None,
            "profiles": {
                "research-readonly": {
                    "adapter": "fixture", "capabilities": ["repository-read", "network"],
                    "workspace_modes": ["read-only"], "network": True,
                },
                "reasoning-readonly": {
                    "adapter": "fixture", "capabilities": ["repository-read"],
                    "workspace_modes": ["read-only"],
                },
                "worker-write": {
                    "adapter": "fixture",
                    "capabilities": ["repository-read", "repository-write"],
                    "workspace_modes": ["isolated-worktree"],
                },
            },
        }
        responses = {
            "research-api": {"polls": 3, "outputs": {"api-findings": (
                "# Findings\nBounded package.\n\n# Sources\n"
                "[Primary](https://example.test/api)\n\n# Risks\nNone.\n"
            )}},
            "research-risks": {"polls": 3,
                               "outputs": {"risk-register": {"risks": ["bounded"]}}},
            "synthesize": {"polls": 1, "outputs": {"implementation-brief": (
                "# Scope\nSmall.\n\n# Decisions\nExact.\n\n"
                "# Acceptance checks\nGreen.\n"
            )}},
            "implement": {"polls": 1,
                          "workspace_files": {"src/feature.py": "VALUE = 1"}},
            "repair": {"polls": 1,
                       "workspace_files": {"tests/test_repair.py":
                                           "def test_repair(): assert True"}},
        }
        main_run = start_run(
            root, plan, plan["start_token"], approved=True,
            approved_by="packaged-exam-operator", now=now,
        )
        first_driver = FixtureDriver(responses)
        boundaries = {"driver_starts": 0}

        def crash_after_parallel_start(name, _detail):
            if name == "after-driver-start":
                boundaries["driver_starts"] += 1
                if boundaries["driver_starts"] == 2:
                    raise RuntimeError("planted restart after parallel dispatch")

        try:
            tick_run(
                root, main_run["run_id"], driver_config=config,
                adapters={"fixture": first_driver}, now=now,
                boundary_hook=crash_after_parallel_start,
            )
        except RuntimeError as exc:
            assert "planted restart" in str(exc)
        else:
            raise AssertionError("planted restart did not cross the driver boundary")
        crashed = replay_run(root, main_run["run_id"], now=now)
        assert [item["node_id"] for item in crashed["active_claims"]] == [
            "research-api", "research-risks"
        ]
        assert first_driver.starts == 2
        recovery_driver = FixtureDriver(responses)
        tick_run(
            root, main_run["run_id"], driver_config=config,
            adapters={"fixture": recovery_driver}, now=now,
        )
        assert recovery_driver.starts == 0, "restart duplicated an active research start"
        checks = {"starts": 0}

        def planted_check(_argv, _cwd, _timeout, _stdout, _stderr, _env):
            checks["starts"] += 1
            return 1 if checks["starts"] == 1 else 0

        tick_document = None
        for _ in range(30):
            tick_document = tick_run(
                root, main_run["run_id"], driver_config=config,
                adapters={"fixture": recovery_driver},
                check_runner=planted_check, now=now,
            )
            if tick_document["terminal"]:
                break
        assert tick_document and tick_document["terminal"], tick_document
        final = replay_run(root, main_run["run_id"], now=now)
        assert final["state"] == "awaiting-certification"
        assert checks["starts"] == 2
        assert len([item for item in final["completed_claims"]
                    if item["node_id"] in ("research-api", "research-risks")]) == 2
        assert len([item for item in final["completed_claims"]
                    if item["node_id"] == "tests"]) == 2
        route = next(item for item in final["routes"] if item["node_id"] == "tests")
        assert route["action"] == "route" and route["resolved"] is True
        assert route["outcome"] == "succeeded" and route["visit"] == 1
        assert final["checkpoints"][-1]["node_id"] == "human-handoff"

        artifacts = artifact_inventory(root, main_run["run_id"])
        by_name = {item["name"]: item for item in artifacts}
        assert {"api-findings", "risk-register", "implementation-brief",
                "implementation-diff", "repair-diff"} <= set(by_name)
        assert "citations" in by_name["api-findings"]["checks"]
        assert "json-schema" in by_name["risk-register"]["checks"]
        assert any(item.startswith("diff-scope:")
                   for item in by_name["implementation-diff"]["checks"])
        assert "git-diff" in by_name["implementation-diff"]["checks"]
        assert not (root / "src" / "feature.py").exists(), "writer touched operator tree"
        run_dir = (root / ".git" / "pmo-orchestration" / "runs"
                   / main_run["run_id"])
        sessions = [json.loads(path.read_text(encoding="utf-8"))
                    for path in (run_dir / "driver-sessions").glob("session-*.json")]
        implement = next(item for item in sessions
                         if item["receipt"]["node_id"] == "implement")
        packet = json.loads(Path(implement["packet_path"]).read_text(encoding="utf-8"))
        assert packet["workspace"]["mode"] == "isolated-worktree"
        assert any(item["artifact"] == "implementation-brief"
                   for item in packet["inputs"])
        assert Path(packet["workspace"]["path"]).resolve() != root
        ledger_text = (run_dir / "ledger.jsonl").read_text(encoding="utf-8")
        for private in ("Bounded package.", "pytest", '"argv"', "implementation-brief.md"):
            assert private not in ledger_text

        def start_named(score, lifetime=3600):
            candidate = build_run_plan(
                root, score, "sample", "SMP-0-01", issued_at=now,
                expires_at=now + timedelta(seconds=lifetime),
            )
            assert candidate["applicable"], candidate["issues"]
            return start_run(
                root, candidate, candidate["start_token"], approved=True,
                approved_by="packaged-exam-operator", now=now,
            )

        expired = start_named("expiry-exam", lifetime=1)
        expired_tick = tick_run(root, expired["run_id"], now=now + timedelta(seconds=2))
        assert expired_tick["state"] == "blocked"
        assert replay_run(root, expired["run_id"], now=now + timedelta(seconds=2))["completed_claims"] == []

        budget = start_named("budget-exam")
        budget_driver = FixtureDriver({"one": {"polls": 0}, "two": {"polls": 0}})
        for _ in range(4):
            budget_tick = tick_run(
                root, budget["run_id"], driver_config=config,
                adapters={"fixture": budget_driver}, now=now,
            )
            if budget_tick["state"] == "blocked":
                break
        assert budget_tick["state"] == "blocked"
        assert budget_driver.starts == 1

        stale_rail = start_named("stale-rail-exam")
        tick_run(root, stale_rail["run_id"], now=now)
        stale_tick = tick_run(root, stale_rail["run_id"], now=now)
        assert stale_tick["state"] == "blocked"
        stale_projection = replay_run(root, stale_rail["run_id"], now=now)
        assert stale_projection["node_receipts"][-1]["reason"] == "stale-action"

        cancelled = start_named("cancel-exam")
        cancel_driver = FixtureDriver({"worker": {"polls": 50}})
        running = tick_run(
            root, cancelled["run_id"], driver_config=config,
            adapters={"fixture": cancel_driver}, now=now,
        )
        assert running["active_claims"] == 1
        old_tick = build_run_act_preview(root, cancelled["run_id"], "tick", now=now)
        cancel_preview = build_run_act_preview(
            root, cancelled["run_id"], "cancel",
            reason="packaged exit cancellation", now=now,
        )
        apply_run_act(
            root, cancelled["run_id"], "cancel", cancel_preview["act_token"],
            reason="packaged exit cancellation", now=now,
        )
        before_stale = (root / ".git" / "pmo-orchestration" / "runs"
                        / cancelled["run_id"] / "ledger.jsonl").read_bytes()
        try:
            apply_run_act(
                root, cancelled["run_id"], "tick", old_tick["act_token"], now=now
            )
        except DwError as exc:
            assert "stale or altered" in exc.message
        else:
            raise AssertionError("cross-state tick token replay was accepted")
        after_stale = (root / ".git" / "pmo-orchestration" / "runs"
                       / cancelled["run_id"] / "ledger.jsonl").read_bytes()
        assert before_stale == after_stale
        tick_run(
            root, cancelled["run_id"], driver_config=config,
            adapters={"fixture": cancel_driver}, now=now,
        )
        cancelled_projection = replay_run(root, cancelled["run_id"], now=now)
        assert cancelled_projection["state"] == "cancelled"
        assert cancelled_projection["active_claims"] == []

        # Final projection, receipt-rich Run model, and act preview are exact
        # shared documents over all installed adapters.  Align pure reads to
        # one UTC second because wall-budget usage is an explicit live fact.
        def same_observation(*readers):
            last = None
            for _ in range(5):
                time.sleep(1.05 - (time.time() % 1.0))
                values = [reader() for reader in readers]
                if all(value == values[0] for value in values[1:]):
                    return values[0]
                last = values
            raise AssertionError(("adapter reads did not share an observation", last))

        projection_doc = same_observation(
            lambda: cli_json("run", "show", main_run["run_id"], "--json"),
            lambda: call_mcp("dw_run_show", {"run_id": main_run["run_id"]}),
            lambda: http("GET", "/api/runs/" + main_run["run_id"])["data"],
        )
        view_doc = same_observation(
            lambda: cli_json("run", "view", main_run["run_id"], "--json"),
            lambda: call_mcp("dw_run_view", {"run_id": main_run["run_id"]}),
            lambda: http("GET", "/api/runs/" + main_run["run_id"] + "/view")["data"],
        )
        assert projection_doc["state"] == "awaiting-certification"
        assert view_doc["terminal"] is True
        assert len(view_doc["sessions"]["agents"]) == 5
        assert len(view_doc["sessions"]["checks"]) == 2
        terminal_cli = run([
            dw, "--root", root, "run", "preview", main_run["run_id"],
            "tick", "--json",
        ], cwd=root, check=False)
        assert terminal_cli.returncode == 1
        terminal_preview = json.loads(terminal_cli.stdout)
        assert terminal_preview == call_mcp("dw_run_preview", {
            "run_id": main_run["run_id"], "action": "tick",
        })
        assert terminal_preview == http("POST", "/api/runs/preview", {
            "run_id": main_run["run_id"], "action": "tick",
        })["data"]
        assert terminal_preview["applicable"] is False

        summary = run_summary_inventory(root, now=now)
        serialized_summary = json.dumps(summary, sort_keys=True).lower()
        for private in ("prompt", "argv", "packet", "transcript", "artifact content"):
            assert private not in serialized_summary
        app = (root / ".githooks" / "workbench" / "app.js").read_text(encoding="utf-8")
        run_source = app[
            app.index("function runStateBadge"):
            app.index("/* ── optional Program / Workflow Studio")
        ]
        for token in ("live run · ledger replay", "fail checks", "failure routes",
                      "human checkpoints", "confirm this exact act"):
            assert token in run_source
        assert "setInterval" not in run_source
        assert "driver_config" not in run_source and "argv:" not in run_source
        assert "<textarea" not in run_source, "Run view grew a generic terminal/editor"

        report = {
            "kind": "delivery-workbench-packaged-orchestration-exam",
            "schema_version": 1,
            "wheel_version": run([global_dw, "--version"], cwd=temporary).stdout.strip(),
            "semantic_hash": compiled["semantic_hash"],
            "document_hash": compiled["document_hash"],
            "run_id": main_run["run_id"],
            "terminal": final["state"],
            "parallel_research_starts": first_driver.starts,
            "recovery_duplicate_starts": 0,
            "check_starts": checks["starts"],
            "repair_route": route,
            "artifacts": sorted(by_name),
            "compiler_refusals": red_diagnostics,
            "runtime_refusals": ["expiry", "budget", "stale-rail", "cancel", "stale-token"],
            "interop": ["cli", "mcp", "http", "workbench"],
            "operator_tree_clean_before_handoff": not bool(
                run(["git", "status", "--porcelain"], cwd=root).stdout
            ),
        }
        report_path = root / "orchestration-exam.json"
        write_json(report_path, report)

        # The fixture operator—not the score, conductor, driver, or Run view—
        # captures evidence, flips the story, reviews, certifies, and commits.
        capture = run([
            dw, "--root", root, "evidence", "capture", "sample", "0", "SMP-0-01",
            "--", sys.executable, "-c",
            "import json; d=json.load(open('orchestration-exam.json')); "
            "assert d['terminal']=='awaiting-certification'; "
            "assert d['check_starts']==2 and d['recovery_duplicate_starts']==0",
        ], cwd=root)
        capture_parts = capture.stdout.strip().split("\t")
        assert len(capture_parts) == 3 and capture_parts[1] == "0", capture.stdout
        status = cli_status()
        assert status["next_action"]["id"] == "finish-story", status["next_action"]
        execute_action(status)
        status = cli_status()
        assert status["next_action"]["id"] == "review-workspace", status["next_action"]
        execute_action(status)
        run(["git", "add", "-A"], cwd=root)
        status = cli_status()
        assert status["next_action"]["id"] == "generate-contract", status["next_action"]
        execute_action(status)
        status = cli_status()
        assert status["next_action"]["id"] == "certify-contract", status["next_action"]
        assert status["next_action"]["kind"] == "manual"
        certify_contract()
        status = cli_status()
        assert status["next_action"]["id"] == "commit", status["next_action"]
        execute_action(status, "-m", "Complete SMP-0-01: packaged orchestration exam")
        run([dw, "--root", root, "verify", "--all"], cwd=root)
        run([dw, "--root", root, "check", "sample"], cwd=root)
        assert not run(["git", "status", "--porcelain"], cwd=root).stdout
        head = run(["git", "rev-parse", "HEAD"], cwd=root).stdout.strip()
        trailers = run(["git", "log", "-1", "--format=%(trailers)"], cwd=root).stdout
        assert "PMO-Story: SMP-0-01" in trailers
        assert "PMO-Contract-Digest: sha256:" in trailers
        archive = root / ".git" / "pmo-contract-archive" / head / "CONTRACT.md"
        assert archive.is_file() and "- [x]" in archive.read_text(encoding="utf-8")

        observed = tick_run(root, main_run["run_id"])
        assert observed["state"] == "awaiting-certification"
        observed_projection = replay_run(root, main_run["run_id"])
        assert observed_projection["external_commits"][-1]["head"] == head

        print(json.dumps({
            "exam": "packaged multi-agent orchestration",
            "run_id": main_run["run_id"],
            "state": observed["state"],
            "parallel_research": 2,
            "duplicate_restarts": 0,
            "checks": checks["starts"],
            "repair_visits": route["visit"],
            "artifact_count": len(artifacts),
            "compiler_red_cases": len(red_diagnostics),
            "runtime_red_cases": 5,
            "operator_commit": head,
            "verify_all": "ok",
        }, sort_keys=True))
        return 0
    finally:
        if server is not None and server.poll() is None:
            server.terminate()
            try:
                server.wait(timeout=10)
            except subprocess.TimeoutExpired:
                server.kill()
                server.wait(timeout=5)
        if args.keep:
            print("orchestration-packaged-exam.py: retained {}".format(temporary),
                  file=sys.stderr)
        else:
            shutil.rmtree(str(temporary), ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
