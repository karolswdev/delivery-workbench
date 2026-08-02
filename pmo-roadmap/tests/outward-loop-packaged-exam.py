#!/usr/bin/env python3
"""Phase-25 outward-loop exit exam against one wheel-installed consumer.

The forge and driver are deterministic fixtures.  The push is real (to a
local bare remote), every scheduler decision is ledgered, and the installed
CLI/MCP/HTTP/Workbench surfaces are exercised without making a live forge or
model a CI oracle.
"""

from __future__ import annotations

import argparse
import json
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


def parse_sse(body):
    frames = []
    for block in body.split("\n\n"):
        fields = {}
        for line in block.splitlines():
            if ":" in line and not line.startswith(":"):
                key, _, value = line.partition(":")
                fields[key.strip()] = value.strip()
        if "data" in fields:
            frames.append((int(fields["id"]), json.loads(fields["data"])))
    return frames


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dw", required=True, type=Path)
    parser.add_argument("--keep", action="store_true")
    args = parser.parse_args()
    global_dw = args.dw.resolve()
    if not global_dw.is_file():
        raise SystemExit("packaged dw is absent: {}".format(global_dw))

    temporary = Path(tempfile.mkdtemp(prefix="dw-outward-exam.")).resolve()
    root = temporary / "consumer"
    remote = temporary / "forge.git"
    scenario_dir = temporary / "forge-snapshots"
    root.mkdir()
    scenario_dir.mkdir()
    server = None
    try:
        run(["git", "init", "--bare", "-q", remote], cwd=temporary)
        run(["git", "init", "-q", "-b", "main"], cwd=root)
        run(["git", "config", "user.name", "Outward Exam Operator"], cwd=root)
        run(["git", "config", "user.email", "outward-exam@example.test"], cwd=root)
        run([
            global_dw, "install", root,
            "--project-name", "Outward Consumer",
            "--project-slug", "sample", "--project-prefix", "SMP",
        ], cwd=temporary)
        dw = root / ".githooks" / "dw"
        mcp = root / ".githooks" / "dw-mcp"
        workbench = root / ".githooks" / "dw-workbench"
        for executable in (dw, mcp, workbench):
            assert executable.is_file(), executable
        run(["git", "remote", "add", "origin", remote], cwd=root)
        run([dw, "--root", root, "story", "create", "sample", "0",
             "Follow-up deliberately left open"], cwd=root)

        defaults = {
            "max_concurrency": 2,
            "max_wall_seconds": 7200,
            "max_agent_starts": 12,
            "max_check_starts": 4,
            "default_timeout_seconds": 60,
            "max_artifact_bytes": 500000,
            "max_nudges": 2,
        }

        def writer(node_id, activation=None, failure=None):
            node = {
                "id": node_id,
                "type": "agent",
                "role": "repair" if "repair" in node_id else "implementation",
                "profile": "worker-write",
                "capabilities": ["repository-read", "repository-write"],
                "workspace": "isolated-worktree",
                "resource_groups": ["working-tree"],
                "outputs": [{
                    "name": node_id + "-diff",
                    "format": "git-diff",
                    "path": "workspace",
                    "allowed_paths": ["src/**", "tests/**"],
                    "max_bytes": 100000,
                }],
                "on_failure": failure or {"action": "abort"},
            }
            if activation:
                node["activation"] = activation
                node["needs"] = ["builder"]
            return node

        outward_score = {
            "kind": "delivery-workbench-orchestration",
            "schema_version": 1,
            "slug": "outward-loop",
            "title": "Push, observe, repair, and ask",
            "project": "sample",
            "defaults": defaults,
            "nodes": [
                writer("builder"),
                writer("ci-repair", "failure"),
                writer(
                    "review-repair", "failure",
                    {"action": "approval", "checkpoint": "review-decision"},
                ),
                {
                    "id": "handoff", "type": "approval", "needs": ["builder"],
                    "prompt": "Inspect and certify the operator-owned integration.",
                    "terminal": "awaiting-certification",
                },
            ],
            "nudges": [
                {
                    "id": "red-ci", "signal": "ci-failed",
                    "target": "ci-repair", "max_total": 1,
                    "expectation": "repair the pushed branch in isolation",
                },
                {
                    "id": "review-changes", "signal": "changes-requested",
                    "target": "review-repair", "max_total": 1,
                    "expectation": "address the bounded review facts in isolation",
                },
            ],
        }

        def session_score(slug, max_nudges=3, target="worker"):
            local_defaults = dict(defaults, max_nudges=max_nudges)
            nodes = [{
                "id": "worker", "type": "agent", "role": "research",
                "profile": "reasoning-readonly",
                "capabilities": ["repository-read"],
                "workspace": "read-only",
                "on_failure": {"action": "abort"},
            }]
            if target == "repair":
                nodes.append({
                    "id": "repair", "type": "agent", "activation": "failure",
                    "needs": ["worker"], "role": "repair",
                    "profile": "reasoning-readonly",
                    "capabilities": ["repository-read"],
                    "workspace": "read-only",
                    "on_failure": {"action": "abort"},
                })
            return {
                "kind": "delivery-workbench-orchestration",
                "schema_version": 1,
                "slug": slug,
                "title": slug.replace("-", " ").title(),
                "project": "sample",
                "defaults": local_defaults,
                "nodes": nodes,
                "nudges": [{
                    "id": "red-ci", "signal": "ci-failed", "target": target,
                    "max_total": 5,
                }],
            }

        scores = {
            "outward-loop": outward_score,
            "uncovered-loop": session_score("uncovered-loop", target="repair"),
            "budget-loop": session_score("budget-loop", max_nudges=1),
            "session-loop": session_score("session-loop"),
        }
        for slug, document in scores.items():
            write_json(root / "pm" / "orchestration" / (slug + ".json"), document)

        def cli_status():
            result = run(
                [dw, "--root", root, "status", "sample", "--json"],
                cwd=root, check=False,
            )
            assert result.returncode in (0, 1), result.stderr
            return json.loads(result.stdout)

        def execute_action(status, *extra):
            action = status["next_action"]
            assert action["kind"] == "command" and action["command"], action
            return run(list(action["command"]) + list(extra), cwd=root)

        def certify_contract():
            contract = root / ".tmp" / "CONTRACT.md"
            text = contract.read_text(encoding="utf-8")
            assert "- [ ]" in text, "operator had no unchecked contract rules"
            contract.write_text(text.replace("- [ ]", "- [x]"), encoding="utf-8")

        def commit_staged(message):
            status = cli_status()
            assert status["next_action"]["id"] == "generate-contract", status["next_action"]
            execute_action(status)
            status = cli_status()
            assert status["next_action"]["id"] == "certify-contract", status["next_action"]
            assert status["next_action"]["kind"] == "manual"
            certify_contract()
            status = cli_status()
            assert status["next_action"]["id"] == "commit", status["next_action"]
            execute_action(status, "-m", message)

        # Bootstrap and start the bound story entirely through normal rails.
        status = cli_status()
        assert status["next_action"]["id"] == "review-workspace", status["next_action"]
        execute_action(status)
        run(["git", "add", "-A"], cwd=root)
        commit_staged("Bootstrap packaged outward-loop exam")
        run(["git", "push", "-u", "origin", "main"], cwd=root)
        run([dw, "--root", root, "story", "status", "sample", "0",
             "SMP-0-01", "in-progress"], cwd=root)
        run(["git", "add", "-A"], cwd=root)
        commit_staged("Start SMP-0-01: packaged outward-loop exam")
        run(["git", "push", "origin", "main"], cwd=root)
        assert not run(["git", "status", "--porcelain"], cwd=root).stdout

        # Import only the wheel-installed/vendored package from the consumer.
        sys.path.insert(0, str(root / ".githooks"))
        from dw_pmo import (  # noqa: import after isolated install
            DwError, FixtureDriver, apply_run_act, build_run_act_preview,
            build_run_plan, replay_run, start_run, tail_run_events,
            tick_run, validate_score,
        )
        from dw_pmo.notifications import build_notifications
        from dw_pmo.orchestration_driver import artifact_inventory
        from dw_pmo.orchestration_surface import tail_signal_events
        from dw_pmo.signals import FixtureProvider, observe_signals, replay_channel

        config = {
            "kind": "delivery-workbench-driver-config",
            "schema_version": 1,
            "workspace_root": None,
            "profiles": {
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
            "builder": {
                "polls": 0,
                "workspace_files": {"src/outward.py": "READY = True"},
            },
            "ci-repair": {
                "polls": 0,
                "workspace_files": {"tests/test_outward.py": "def test_ready(): assert True"},
            },
            "review-repair": {
                "polls": 0, "state": "failed", "exit_code": 1,
                "workspace_files": {"src/review_attempt.py": "ATTEMPTED = True"},
            },
        }
        now = datetime.now(timezone.utc).replace(microsecond=0)
        expires = now + timedelta(hours=1)

        def start_named(score, channel, standing):
            plan = build_run_plan(
                root, score, "sample", "SMP-0-01", issued_at=now,
                expires_at=expires, standing_nudges=standing,
                signal_channel=channel,
            )
            assert plan["applicable"], plan["issues"]
            return start_run(
                root, plan, plan["start_token"], approved=True,
                approved_by="packaged-outward-operator", now=now,
            )

        def drive(run_id, driver, wanted, limit=20, observed=now):
            result = None
            for _ in range(limit):
                result = tick_run(
                    root, run_id, driver_config=config,
                    adapters={"fixture": driver}, now=observed,
                )
                if result["state"] in wanted:
                    return result
            raise AssertionError("run did not reach {}: {}".format(wanted, result))

        def snapshot(path, checks, review=None):
            document = {
                "prs": [{
                    "number": 1, "state": "open", "draft": False,
                    "head": "main", "base": "main", "url": "fixture://pr/1",
                    "checks": checks, "mergeable": "true",
                    "mergeable_reason": "clean",
                }]
            }
            if review is not None:
                document["prs"][0]["review"] = review
            write_json(path, document)

        def check(name, conclusion):
            return {
                "name": name, "status": "completed", "conclusion": conclusion,
                "url": "fixture://check/{}".format(name),
            }

        main_run = start_named(
            "outward-loop", "origin/main",
            ["ci-failed=ci-repair", "changes-requested=review-repair"],
        )
        main_id = main_run["run_id"]
        first_driver = FixtureDriver(responses)
        drive(main_id, first_driver, {"awaiting-certification"})
        initial = replay_run(root, main_id, now=now)
        assert initial["state"] == "awaiting-certification"
        assert first_driver.starts == 1
        assert not (root / "src" / "outward.py").exists()

        # The operator applies the isolated builder artifact.  Before manual
        # certification, an orchestration tick cannot alter a contract box.
        builder_artifact = next(
            item for item in artifact_inventory(root, main_id)
            if item["name"] == "builder-diff"
        )
        builder_patch = (
            root / ".git" / "pmo-orchestration" / "runs" / main_id
            / "artifacts" / "builder" / "builder-diff" / "content"
        )
        assert builder_artifact["valid"] and builder_patch.is_file()
        run(["git", "apply", builder_patch], cwd=root)
        run(["git", "add", "src/outward.py"], cwd=root)
        status = cli_status()
        assert status["next_action"]["id"] == "generate-contract", status["next_action"]
        execute_action(status)
        contract = root / ".tmp" / "CONTRACT.md"
        unchecked = contract.read_bytes()
        assert b"- [ ]" in unchecked
        tick_run(
            root, main_id, driver_config=config,
            adapters={"fixture": first_driver}, now=now,
        )
        assert contract.read_bytes() == unchecked
        forbidden = {
            "kind": "delivery-workbench-orchestration", "schema_version": 1,
            "slug": "forbidden-certify", "title": "Forbidden certify",
            "nodes": [{"id": "certify", "type": "rail", "action": "certify-contract"}],
        }
        forbidden_result = validate_score(forbidden)
        assert forbidden_result["valid"] is False
        assert "forbidden-authority" in {
            item["code"] for item in forbidden_result["diagnostics"]
        }
        certify_contract()
        status = cli_status()
        assert status["next_action"]["id"] == "commit", status["next_action"]
        execute_action(status, "-m", "Integrate outward-loop agent work")
        operator_head = run(["git", "rev-parse", "HEAD"], cwd=root).stdout.strip()
        run(["git", "push", "origin", "main"], cwd=root)
        assert run(
            ["git", "--git-dir", remote, "rev-parse", "refs/heads/main"], cwd=temporary
        ).stdout.strip() == operator_head
        assert not run(["git", "status", "--porcelain"], cwd=root).stdout

        # Observer side effects are confined to its local .git fact store.
        main_snapshot = scenario_dir / "main.json"
        snapshot(main_snapshot, [check("ci", "failure")])
        remote_before = run(
            ["git", "--git-dir", remote, "for-each-ref", "--format=%(refname) %(objectname)"],
            cwd=temporary,
        ).stdout
        tree_before = run(["git", "status", "--porcelain=v1"], cwd=root).stdout
        observed = observe_signals(
            root, FixtureProvider(main_snapshot), "origin", "main", now=now
        )
        assert observed["starts_work"] is False and observed["appended"] > 0
        assert run(
            ["git", "--git-dir", remote, "for-each-ref", "--format=%(refname) %(objectname)"],
            cwd=temporary,
        ).stdout == remote_before
        assert run(["git", "status", "--porcelain=v1"], cwd=root).stdout == tree_before
        signal_chain = (
            root / ".git" / "pmo-signals" / "origin" / "main" / "signals.jsonl"
        )
        before_replay = signal_chain.read_bytes()
        replayed_observe = observe_signals(
            root, FixtureProvider(main_snapshot), "origin", "main", now=now
        )
        assert replayed_observe["appended"] == 0
        assert signal_chain.read_bytes() == before_replay

        # Plant the crash after the nudge receipt and claim, before any driver
        # start.  A new driver instance must recover one claim with one start.
        def crash_after_claim(name, detail):
            if name == "after-claim" and detail.get("node_id") == "ci-repair":
                raise RuntimeError("planted crash after outward nudge claim")

        try:
            tick_run(
                root, main_id, driver_config=config,
                adapters={"fixture": first_driver}, now=now,
                boundary_hook=crash_after_claim,
            )
        except RuntimeError as exc:
            assert "planted crash" in str(exc)
        else:
            raise AssertionError("outward nudge crash boundary was not crossed")
        crashed = replay_run(root, main_id, now=now)
        assert len([item for item in crashed["nudges"] if item["delivered"]]) == 1
        assert [item["node_id"] for item in crashed["active_claims"]] == ["ci-repair"]
        recovery_driver = FixtureDriver(responses)
        drive(main_id, recovery_driver, {"awaiting-certification"})
        after_ci = replay_run(root, main_id, now=now)
        assert recovery_driver.starts == 1
        assert len([item for item in after_ci["completed_claims"]
                    if item["node_id"] == "ci-repair"]) == 1
        assert after_ci["external_commits"][-1]["head"] == operator_head
        assert after_ci["external_commits"][-1]["rebindable"] is True
        assert not (root / "tests" / "test_outward.py").exists()

        # Green replaces the failed check fact.  Review changes then produce a
        # second distinct nudge whose failed repair opens a typed checkpoint.
        snapshot(main_snapshot, [check("ci", "success")])
        observe_signals(root, FixtureProvider(main_snapshot), "origin", "main", now=now)
        tick_run(
            root, main_id, driver_config=config,
            adapters={"fixture": recovery_driver}, now=now,
        )
        snapshot(main_snapshot, [check("ci", "success")], {
            "unresolved": 1, "resolved": 0, "changes_requested": True,
            "approved": False, "reviewers": ["fixture-reviewer"],
            "url": "fixture://review/1",
        })
        observe_signals(root, FixtureProvider(main_snapshot), "origin", "main", now=now)
        drive(main_id, recovery_driver, {"awaiting-approval"})
        waiting = replay_run(root, main_id, now=now)
        assert len([item for item in waiting["nudges"] if item["delivered"]]) == 2
        assert waiting["pending_checkpoint"]["checkpoint"] == "review-decision"
        correlation = waiting["outstanding_requests"][0]["correlation_id"]

        def cli_json(*parts):
            return json.loads(run([dw, "--root", root] + list(parts), cwd=root).stdout)

        def installed_restart_tick():
            preview = cli_json("run", "preview", main_id, "tick", "--json")
            assert preview["applicable"] is True
            return cli_json(
                "run", "tick", main_id, "--expect", preview["act_token"], "--json"
            )

        for _ in range(3):
            installed_restart_tick()
        restarted = replay_run(root, main_id)
        republished = [
            json.loads(line) for line in (
                root / ".git" / "pmo-orchestration" / "runs" / main_id
                / "ledger.jsonl"
            ).read_text(encoding="utf-8").splitlines()
            if json.loads(line)["event"] == "request_republished"
        ]
        assert len(republished) == 1
        assert republished[0]["detail"]["correlation_id"] == correlation

        # A stale correlation crosses the same exact-token boundary, becomes a
        # content-free refusal, and leaves the real request live.
        wrong = "req-000000000000000000000000"
        wrong_preview = cli_json(
            "run", "preview", main_id, "request", "--correlation", wrong,
            "--decision", "approve", "--json",
        )
        wrong_result = cli_json(
            "run", "request", main_id, wrong, "approve",
            "--expect", wrong_preview["act_token"], "--json",
        )
        assert wrong_result["request_refusals"][-1]["reason"] == "correlation-mismatch"
        assert wrong_result["outstanding_requests"][0]["correlation_id"] == correlation

        # Start installed Workbench for HTTP, SSE, and cross-adapter parity.
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
            request = urllib.request.Request(
                base + route, data=data, headers=headers, method=method
            )
            try:
                response = urllib.request.urlopen(request, timeout=10)
                code = response.status
                body = json.load(response)
            except urllib.error.HTTPError as exc:
                code = exc.code
                body = json.load(exc)
            assert code == expected, (route, code, body)
            return body

        def http_raw(method, route, payload=None):
            data = None if payload is None else json.dumps(payload).encode("utf-8")
            request = urllib.request.Request(
                base + route, data=data,
                headers={"Content-Type": "application/json"} if data else {},
                method=method,
            )
            try:
                response = urllib.request.urlopen(request, timeout=10)
                return response.status, response.read().decode("utf-8")
            except urllib.error.HTTPError as exc:
                return exc.code, exc.read().decode("utf-8")

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

        def call_mcp(name, arguments):
            request = {
                "jsonrpc": "2.0", "id": 1, "method": "tools/call",
                "params": {"name": name, "arguments": arguments},
            }
            result = run(
                [mcp, "--root", root], cwd=root,
                input_text=json.dumps(request) + "\n",
            )
            payload = json.loads(result.stdout)["result"]
            assert not payload.get("isError"), payload
            return payload["structuredContent"]

        # Notification derivation is identical everywhere. Delivery and ack
        # are explicit receipts; neither grants the pending decision.
        direct_notifications = build_notifications(root)
        cli_notifications = cli_json("notifications", "list", "--json")
        mcp_notifications = call_mcp("dw_notifications", {})
        http_notifications = http("GET", "/api/notifications")["data"]
        assert direct_notifications == cli_notifications == mcp_notifications == http_notifications
        pending = next(
            item for item in direct_notifications["notifications"]
            if item["kind"] == "checkpoint-pending" and item["run_id"] == main_id
        )
        for excluded in ("act_token", "start_token", "--expect", "apply_command"):
            assert excluded not in pending["outbound"]
        run([
            dw, "--root", root, "notifications", "delivered", pending["id"],
            "--channel", "fixture-phone",
        ], cwd=root)
        ack = http("POST", "/api/notifications/ack", {"id": pending["id"]})["data"]
        assert ack["acknowledged"] is True and ack["changed"] is True
        after_ack = cli_json("notifications", "list", "--json")
        acked = next(item for item in after_ack["notifications"] if item["id"] == pending["id"])
        assert acked["unread"] is False and acked["delivered"] is True
        assert after_ack == call_mcp("dw_notifications", {})
        assert after_ack == http("GET", "/api/notifications")["data"]

        correct_preview = http("POST", "/api/runs/preview", {
            "run_id": main_id, "action": "request",
            "correlation_id": correlation, "decision": "approve",
        })["data"]
        decided = http("POST", "/api/runs/request", {
            "run_id": main_id, "expect": correct_preview["act_token"],
            "correlation_id": correlation, "decision": "approve",
        })["data"]
        assert decided["outstanding_requests"] == []
        drive(
            main_id, recovery_driver, {"awaiting-certification"}, observed=None
        )
        main_final = replay_run(root, main_id)
        assert main_final["state"] == "awaiting-certification"
        assert main_final["request_history"][-1]["status"] == "approved"

        # Canonical CLI and HTTP SSE replays equal the verified ledgers.  POST
        # is refused and the stream contains no authority material.
        ledger_path = (
            root / ".git" / "pmo-orchestration" / "runs" / main_id / "ledger.jsonl"
        )
        ledger = [json.loads(line) for line in ledger_path.read_text().splitlines()]
        cli_tail = [
            json.loads(line) for line in run(
                [dw, "--root", root, "run", "tail", main_id], cwd=root
            ).stdout.splitlines()
        ]
        assert cli_tail == ledger == tail_run_events(root, main_id)["events"]
        code, run_sse = http_raw("GET", "/api/runs/{}/events?follow=0".format(main_id))
        assert code == 200
        run_frames = parse_sse(run_sse)
        snapshot_seq, run_snapshot = run_frames[0]
        assert snapshot_seq == 0
        assert run_snapshot["run_id"] == main_id
        assert run_snapshot["ledger_events"] == len(ledger)
        assert run_snapshot["ledger_head"] == ledger[-1]["event_hash"]
        ledger_frames = run_frames[1:]
        assert [document for _seq, document in ledger_frames] == ledger
        assert [seq for seq, _document in ledger_frames] == [
            event["seq"] for event in ledger
        ]
        code, signal_sse = http_raw(
            "GET", "/api/signals/events?remote=origin&branch=main&follow=0"
        )
        assert code == 200
        assert [document for _seq, document in parse_sse(signal_sse)] == tail_signal_events(
            root, "origin", "main"
        )["events"]
        code, refused_stream = http_raw(
            "POST", "/api/runs/{}/events".format(main_id), {}
        )
        assert code >= 400
        stream_text = (run_sse + signal_sse + refused_stream).lower()
        for excluded in ("act_token", "start_token", "apply_command", '"argv"'):
            assert excluded not in stream_text

        # Runtime red matrix.  Every refusal is ledgered, deduped, and leaves
        # the tracked operator tree and bare forge unchanged.
        red_tree_before = run(["git", "status", "--porcelain=v1"], cwd=root).stdout
        red_remote_before = run(
            ["git", "--git-dir", remote, "for-each-ref", "--format=%(refname) %(objectname)"],
            cwd=temporary,
        ).stdout

        uncovered = start_named("uncovered-loop", "origin/uncovered", [])
        uncovered_driver = FixtureDriver({"worker": {"polls": 50}})
        tick_run(
            root, uncovered["run_id"], driver_config=config,
            adapters={"fixture": uncovered_driver}, now=now,
        )
        uncovered_snapshot = scenario_dir / "uncovered.json"
        snapshot(uncovered_snapshot, [check("ci", "failure")])
        observe_signals(
            root, FixtureProvider(uncovered_snapshot), "origin", "uncovered", now=now
        )
        for _ in range(2):
            tick_run(
                root, uncovered["run_id"], driver_config=config,
                adapters={"fixture": uncovered_driver}, now=now,
            )
        uncovered_projection = replay_run(root, uncovered["run_id"], now=now)
        assert [item["reason"] for item in uncovered_projection["nudges"]] == [
            "no-standing-rule"
        ]
        assert len(uncovered_projection["outstanding_requests"]) == 1
        revoke_preview = build_run_act_preview(
            root, uncovered["run_id"], "revoke", reason="stop outward exam", now=now
        )
        revoked = apply_run_act(
            root, uncovered["run_id"], "revoke", revoke_preview["act_token"],
            reason="stop outward exam", now=now,
        )
        assert revoked["state"] == "revoked" and revoked["outstanding_requests"] == []
        assert revoked["request_history"][-1]["status"] == "expired"
        before_future = len(revoked["nudges"])
        tick_run(
            root, uncovered["run_id"], driver_config=config,
            adapters={"fixture": uncovered_driver}, now=now,
        )
        assert len(replay_run(root, uncovered["run_id"], now=now)["nudges"]) == before_future

        budget = start_named("budget-loop", "origin/budget", ["ci-failed=worker"])
        budget_driver = FixtureDriver({
            "worker": {"polls": 50, "activities": ["waiting_input"]}
        })
        tick_run(
            root, budget["run_id"], driver_config=config,
            adapters={"fixture": budget_driver}, now=now,
        )
        budget_snapshot = scenario_dir / "budget.json"
        snapshot(budget_snapshot, [check("ci", "failure")])
        observe_signals(root, FixtureProvider(budget_snapshot), "origin", "budget", now=now)
        tick_run(
            root, budget["run_id"], driver_config=config,
            adapters={"fixture": budget_driver}, now=now,
        )
        first_budget = replay_run(root, budget["run_id"], now=now)
        assert len([item for item in first_budget["nudges"] if item["delivered"]]) == 1
        snapshot(budget_snapshot, [check("ci", "success")])
        observe_signals(root, FixtureProvider(budget_snapshot), "origin", "budget", now=now)
        snapshot(budget_snapshot, [check("ci", "failure")])
        observe_signals(root, FixtureProvider(budget_snapshot), "origin", "budget", now=now)
        tick_run(
            root, budget["run_id"], driver_config=config,
            adapters={"fixture": budget_driver}, now=now,
        )
        budget_projection = replay_run(root, budget["run_id"], now=now)
        assert budget_projection["state"] == "blocked"
        assert "nudge-budget-exhausted" in {
            item.get("reason") for item in budget_projection["nudges"]
        }

        receptive_refusals = {}
        for activity in ("blocked", "unknown"):
            channel = "session-" + activity
            session = start_named("session-loop", "origin/" + channel, ["ci-failed=worker"])
            session_driver = FixtureDriver({
                "worker": {"polls": 50, "activities": [activity]}
            })
            tick_run(
                root, session["run_id"], driver_config=config,
                adapters={"fixture": session_driver}, now=now,
            )
            session_snapshot = scenario_dir / (channel + ".json")
            snapshot(session_snapshot, [check("ci", "failure")])
            observe_signals(
                root, FixtureProvider(session_snapshot), "origin", channel, now=now
            )
            for _ in range(2):
                tick_run(
                    root, session["run_id"], driver_config=config,
                    adapters={"fixture": session_driver}, now=now,
                )
            session_projection = replay_run(root, session["run_id"], now=now)
            assert len(session_projection["nudges"]) == 1
            assert session_projection["nudges"][0]["reason"] == "non-receptive"
            receptive_refusals[activity] = session_projection["nudges"][0]["reason"]

        assert run(["git", "status", "--porcelain=v1"], cwd=root).stdout == red_tree_before
        assert run(
            ["git", "--git-dir", remote, "for-each-ref", "--format=%(refname) %(objectname)"],
            cwd=temporary,
        ).stdout == red_remote_before

        main_sessions = [
            json.loads(path.read_text(encoding="utf-8"))
            for path in (
                root / ".git" / "pmo-orchestration" / "runs" / main_id
                / "driver-sessions"
            ).glob("session-*.json")
        ]
        starts_by_node = {}
        for record in main_sessions:
            node = record["receipt"]["node_id"]
            starts_by_node[node] = starts_by_node.get(node, 0) + 1
        assert starts_by_node == {"builder": 1, "ci-repair": 1, "review-repair": 1}
        delivered = [item for item in main_final["nudges"] if item["delivered"]]
        assert len(delivered) == 2
        assert len({item["signal_hash"] for item in delivered}) == 2
        main_events = {event["event"] for event in ledger}
        assert {
            "external_commit_observed", "nudge_delivered", "request_republished",
            "request_refused", "request_decided", "checkpoint_reached",
        } <= main_events
        assert replay_channel(root, "origin", "main")["status"] == "changes-requested"
        assert not run(["git", "status", "--porcelain"], cwd=root).stdout
        run([dw, "--root", root, "check", "sample"], cwd=root)
        run([dw, "--root", root, "verify", "--all"], cwd=root)

        report = {
            "kind": "delivery-workbench-packaged-outward-exam",
            "schema_version": 1,
            "wheel_version": run([global_dw, "--version"], cwd=temporary).stdout.strip(),
            "run_id": main_id,
            "state": main_final["state"],
            "operator_push": operator_head,
            "external_rebind": main_final["external_commits"][-1]["rebindable"],
            "nudges": len(delivered),
            "duplicate_starts": 0,
            "duplicate_nudges": 0,
            "request_republishes": len(republished),
            "refusals": {
                "without-standing-grant": "no-standing-rule",
                "budget": "nudge-budget-exhausted",
                "blocked-session": receptive_refusals["blocked"],
                "unknown-session": receptive_refusals["unknown"],
                "stale-correlation": "correlation-mismatch",
                "revoked-request": "expired",
            },
            "stream_matches_ledger": True,
            "observer_side_effects": 0,
            "certification": "operator-only",
        }
        print(json.dumps(report, sort_keys=True))
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
            print(
                "outward-loop-packaged-exam.py: retained {}".format(temporary),
                file=sys.stderr,
            )
        else:
            shutil.rmtree(str(temporary), ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
