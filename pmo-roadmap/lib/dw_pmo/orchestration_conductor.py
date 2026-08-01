"""Deterministic orchestration scheduling, checks, routes, and recovery.

``tick_run`` is the only scheduler primitive.  It replays immutable score and
ledger facts, reconciles already-claimed work before considering anything new,
records every state-changing decision, and then dispatches one stable eligible
set within the grant's concurrency/resource/budget bounds.  Supervision is
only bounded repetition around that primitive.
"""

from __future__ import annotations

import fnmatch
import fcntl
import hashlib
import json
import os
import signal
import subprocess
import time
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Iterator

from .gitio import head_sha, in_rewrite_state
from .knowledge_packet import build_repository_knowledge_packet
from .memory_dispatch import (
    MemoryRecallActionNeeded,
    persist_recall_slices,
    recall_audience,
    recall_event_detail,
)
from .model import DwError
from .orchestration_driver import (
    DriverManager,
    _schema_check,
    artifact_inventory,
    build_work_packet,
    load_driver_config,
)
from .orchestration_run import (
    _format_time,
    _load_run_documents,
    _parse_time,
    _run_dir,
    _sha,
    claim_node,
    maintain_outstanding_requests,
    observed_external_fact_binding,
    observed_fact_binding,
    record_runtime_event,
    release_node_claim,
    replay_run,
    transition_run,
)
from .signals import receptivity as signal_receptivity
from .signals import latest_nudge_fact as signal_latest_nudge_fact
from .signals import replay_channel as signal_replay_channel
from .status import build_status
from .step import StepChild, apply_step, build_step


CONDUCTOR_DECISION_KIND = "delivery-workbench-conductor-decision"
CONDUCTOR_TICK_KIND = "delivery-workbench-conductor-tick"
CONDUCTOR_SUPERVISION_KIND = "delivery-workbench-conductor-supervision"
CHECK_RECEIPT_KIND = "delivery-workbench-check-receipt"
RAIL_RECEIPT_KIND = "delivery-workbench-rail-receipt"
CONDUCTOR_SCHEMA_VERSION = 1

MAX_SNAPSHOT_FILES = 20_000
MAX_SNAPSHOT_BYTES = 100_000_000
MAX_CHECK_OUTPUT_BYTES = 10_000_000
TERMINAL_STATES = {
    "complete", "blocked", "cancelled", "revoked", "awaiting-certification",
}
FATAL_RECEIPT_REASONS = {
    "unsupported-authority", "unsupported-capability", "unsupported-workspace",
    "profile-unconfigured", "adapter-unavailable", "grant-stale",
    "dispatch-refused", "artifact-budget", "forbidden-authority",
}

BoundaryHook = Callable[[str, dict[str, object]], None]
CheckRunner = Callable[
    [list[str], Path, int, Path, Path, dict[str, str]], int
]


def _nodes(compiled: dict[str, object]) -> list[dict[str, object]]:
    return list(compiled["score"]["nodes"])  # type: ignore[index]


def _node_index(compiled: dict[str, object]) -> dict[str, int]:
    return {str(node["id"]): index for index, node in enumerate(_nodes(compiled))}


def _node_map(compiled: dict[str, object]) -> dict[str, dict[str, object]]:
    return {str(node["id"]): node for node in _nodes(compiled)}


def _attempts(projection: dict[str, object], node_id: str) -> list[dict[str, object]]:
    values = [
        item for item in projection["completed_claims"]
        if item["node_id"] == node_id
    ]
    return sorted(values, key=lambda item: int(item["attempt"]))


def _active_by_node(projection: dict[str, object]) -> dict[str, dict[str, object]]:
    result = {
        str(item["node_id"]): item for item in projection["active_claims"]
    }
    if len(result) != len(projection["active_claims"]):
        raise DwError("run has concurrent attempts for one node; conductor refuses ambiguity")
    return result


def _approved_normal_nodes(projection: dict[str, object]) -> set[str]:
    return {
        str(item["node_id"])
        for item in projection["checkpoints"]
        if item.get("mode") == "normal" and item.get("decision") == "approve"
    }


def _successful_nodes(projection: dict[str, object]) -> set[str]:
    result = {
        str(item["node_id"])
        for item in projection["completed_claims"]
        if item["outcome"] == "succeeded"
    }
    result.update(_approved_normal_nodes(projection))
    return result


def _required_artifacts(node: dict[str, object]) -> list[str]:
    return [
        str(item["artifact"])
        for item in node.get("inputs", [])
        if isinstance(item, dict) and item.get("artifact")
    ]


def _open_route_for_target(
    projection: dict[str, object], node_id: str
) -> dict[str, object] | None:
    candidates = [
        item for item in projection["routes"]
        if item["action"] == "route"
        and item["target"] == node_id
        and not item.get("resolved")
    ]
    return candidates[0] if candidates else None


def _route_for_failure(
    projection: dict[str, object], node_id: str, attempt: int
) -> dict[str, object] | None:
    return next(
        (
            item for item in projection["routes"]
            if item["node_id"] == node_id and item["attempt"] == attempt
        ),
        None,
    )


def schedule_decision(
    compiled: dict[str, object],
    projection: dict[str, object],
    artifacts: list[dict[str, object]],
) -> dict[str, object]:
    """Pure stable eligibility/resource/concurrency decision over replayed facts."""
    nodes = _nodes(compiled)
    active = _active_by_node(projection)
    successful = _successful_nodes(projection)
    artifact_names = {str(item["name"]) for item in artifacts if item.get("valid")}
    active_groups: set[str] = set()
    node_by_id = {str(node["id"]): node for node in nodes}
    for node_id in active:
        active_groups.update(str(group) for group in node_by_id[node_id].get("resource_groups", []))

    candidates: list[dict[str, object]] = []
    blocked: list[dict[str, str]] = []
    action_needed: list[dict[str, object]] = []
    resolution_needed: list[dict[str, object]] = []
    states: list[dict[str, object]] = []

    for node in nodes:
        node_id = str(node["id"])
        attempts = _attempts(projection, node_id)
        latest = attempts[-1] if attempts else None
        if node_id in active:
            states.append({"node_id": node_id, "state": "active", "attempt": active[node_id]["attempt"]})
            continue

        pending_nudge = _pending_nudge_for(projection, node_id)
        if pending_nudge is not None:
            candidates.append({
                "node_id": node_id, "attempt": int(pending_nudge["attempt"]),
                "kind": "claim", "reason": "nudge",
            })
            states.append({
                "node_id": node_id, "state": "eligible",
                "attempt": int(pending_nudge["attempt"]),
            })
            continue

        if node.get("activation") == "failure":
            route = _open_route_for_target(projection, node_id)
            if route is None:
                nudged = (
                    latest is not None
                    and any(
                        item.get("delivered")
                        and str(item.get("node_id")) == node_id
                        and int(item.get("attempt", 0)) == int(latest["attempt"])
                        for item in projection["nudges"]
                    )
                )
                if nudged:
                    if (
                        latest["outcome"] != "succeeded"
                        and _route_for_failure(
                            projection, node_id, int(latest["attempt"])
                        ) is None
                    ):
                        action_needed.append({
                            "node_id": node_id, "attempt": latest["attempt"],
                        })
                        states.append({
                            "node_id": node_id, "state": "routing",
                            "attempt": latest["attempt"],
                        })
                    else:
                        states.append({
                            "node_id": node_id, "state": latest["outcome"],
                            "attempt": latest["attempt"],
                        })
                else:
                    states.append({
                        "node_id": node_id, "state": "dormant", "attempt": 0,
                    })
                continue
            target_attempt = int(route["target_attempt"])
            target_result = next(
                (item for item in attempts if int(item["attempt"]) == target_attempt),
                None,
            )
            if target_result is not None:
                if not route.get("resolved"):
                    resolution_needed.append({
                        "node_id": route["node_id"], "attempt": route["attempt"],
                        "target": node_id, "target_attempt": target_attempt,
                        "visit": route["visit"], "outcome": target_result["outcome"],
                    })
                if (
                    target_result["outcome"] != "succeeded"
                    and _route_for_failure(projection, node_id, target_attempt) is None
                ):
                    action_needed.append({
                        "node_id": node_id, "attempt": target_attempt,
                    })
                states.append({"node_id": node_id, "state": target_result["outcome"], "attempt": target_attempt})
                continue
            route_source = str(route["node_id"])
            unmet = [
                need for need in node.get("needs", [])
                if need not in successful and need != route_source
            ]
            missing = [name for name in _required_artifacts(node) if name not in artifact_names]
            if unmet or missing:
                reason = "dependencies" if unmet else "artifact-gate"
                blocked.append({"node_id": node_id, "reason": reason})
                states.append({"node_id": node_id, "state": "blocked", "attempt": target_attempt})
                continue
            candidates.append({
                "node_id": node_id, "attempt": target_attempt,
                "kind": "claim", "reason": "failure-route",
            })
            states.append({"node_id": node_id, "state": "eligible", "attempt": target_attempt})
            continue

        if node_id in successful:
            states.append({"node_id": node_id, "state": "succeeded", "attempt": latest["attempt"] if latest else 0})
            continue

        if latest is not None and latest["outcome"] != "succeeded":
            route = _route_for_failure(projection, node_id, int(latest["attempt"]))
            if route is None:
                action_needed.append({"node_id": node_id, "attempt": latest["attempt"]})
                states.append({"node_id": node_id, "state": "routing", "attempt": latest["attempt"]})
                continue
            if route["action"] == "retry":
                next_attempt = int(route["target_attempt"])
            elif route["action"] == "route" and route.get("resolved") and route.get("outcome") == "succeeded":
                next_attempt = int(latest["attempt"]) + 1
            else:
                states.append({"node_id": node_id, "state": "blocked", "attempt": latest["attempt"]})
                continue
            if next_attempt > 20:
                blocked.append({"node_id": node_id, "reason": "attempt-ceiling"})
                states.append({"node_id": node_id, "state": "blocked", "attempt": next_attempt})
                continue
            attempt = next_attempt
        else:
            attempt = 1

        unmet = [need for need in node.get("needs", []) if need not in successful]
        missing = [name for name in _required_artifacts(node) if name not in artifact_names]
        if unmet or missing:
            reason = "dependencies" if unmet else "artifact-gate"
            blocked.append({"node_id": node_id, "reason": reason})
            states.append({"node_id": node_id, "state": "blocked", "attempt": attempt})
            continue
        if node["type"] == "approval":
            candidates.append({
                "node_id": node_id, "attempt": 0,
                "kind": "checkpoint", "reason": "dependencies-satisfied",
            })
        else:
            candidates.append({
                "node_id": node_id, "attempt": attempt,
                "kind": "claim", "reason": "dependencies-satisfied",
            })
        states.append({"node_id": node_id, "state": "eligible", "attempt": attempt})

    capacity = max(
        0,
        int(projection["budgets"]["max_concurrency"]["limit"])
        - len(projection["active_claims"]),
    )
    locked = set(active_groups)
    scheduled: list[dict[str, object]] = []
    for candidate in candidates:
        node = node_by_id[str(candidate["node_id"])]
        if candidate["kind"] == "checkpoint":
            if projection["active_claims"] or scheduled:
                continue
            scheduled.append(candidate)
            break
        if capacity <= 0:
            continue
        groups = {str(group) for group in node.get("resource_groups", [])}
        if groups & locked:
            continue
        budget_name = (
            "max_agent_starts" if node["type"] == "agent"
            else "max_check_starts" if node["type"] == "check" else None
        )
        if budget_name:
            budget = projection["budgets"][budget_name]
            already_selected = sum(
                1 for item in scheduled
                if node_by_id[str(item["node_id"])]["type"] == node["type"]
            )
            if int(budget["used"]) + already_selected >= int(budget["limit"]):
                blocked.append({"node_id": str(node["id"]), "reason": budget_name})
                continue
        scheduled.append(candidate)
        locked.update(groups)
        capacity -= 1

    success_nodes = [
        str(node["id"]) for node in nodes if node.get("activation") == "success"
    ]
    terminal_needed = (
        bool(success_nodes)
        and all(node_id in successful for node_id in success_nodes)
        and not active
        and not any(item["kind"] == "claim" for item in candidates)
    )
    return {
        "kind": CONDUCTOR_DECISION_KIND,
        "schema_version": CONDUCTOR_SCHEMA_VERSION,
        "run_id": projection["run_id"],
        "ledger_head": projection["ledger_head"],
        "state": projection["state"],
        "eligible": candidates,
        "scheduled": scheduled,
        "blocked": blocked,
        "action_needed": action_needed,
        "resolution_needed": resolution_needed,
        "node_states": states,
        "active_resource_groups": sorted(active_groups),
        "terminal_needed": terminal_needed,
        "starts_work": False,
        "writes_events": False,
    }


def _safe_environment() -> dict[str, str]:
    allowed = {"HOME", "PATH", "TMPDIR", "LANG", "LC_ALL", "TERM"}
    return {key: value for key, value in os.environ.items() if key in allowed}


def _bounded_reason(value: object, fallback: str) -> str:
    text = " ".join(str(value or fallback).split())
    return (text or fallback)[:200]


def _snapshot(base: Path) -> dict[str, str]:
    base = base.resolve()
    result: dict[str, str] = {}
    total = 0
    for path in sorted(base.rglob("*"), key=lambda item: str(item)):
        try:
            relative = path.relative_to(base)
        except ValueError as exc:
            raise DwError("check snapshot escaped its workspace") from exc
        if ".git" in relative.parts:
            continue
        if path.is_symlink():
            result[str(relative)] = "symlink:" + os.readlink(path)
            continue
        if not path.is_file():
            continue
        if len(result) >= MAX_SNAPSHOT_FILES:
            raise DwError("check workspace exceeds the snapshot file-count bound")
        data = path.read_bytes()
        total += len(data)
        if total > MAX_SNAPSHOT_BYTES:
            raise DwError("check workspace exceeds the snapshot byte bound")
        result[str(relative)] = hashlib.sha256(data).hexdigest()
    return result


def _changed_paths(before: dict[str, str], after: dict[str, str]) -> list[str]:
    return sorted(
        path for path in set(before) | set(after) if before.get(path) != after.get(path)
    )


def _workspace_for_check(
    root: Path,
    run_id: str,
    node: dict[str, object],
    projection: dict[str, object],
) -> tuple[Path, str]:
    candidates: list[dict[str, object]] = []
    permitted = set(str(value) for value in node.get("needs", []))
    for route in projection["routes"]:
        if route.get("resolved") and route.get("outcome") == "succeeded":
            permitted.add(str(route["target"]))
    for claim in projection["completed_claims"]:
        if claim["outcome"] == "succeeded" and claim["node_id"] in permitted:
            metadata = (
                _run_dir(root, run_id) / "workspaces" / str(claim["node_id"])
                / f"{claim['attempt']}.json"
            )
            if metadata.is_file():
                candidates.append({**claim, "metadata": metadata})
    if not candidates:
        raise DwError("check requested workspace but no successful isolated predecessor exists")
    selected = max(candidates, key=lambda item: int(item.get("release_seq", 0)))
    workspace = json.loads(Path(selected["metadata"]).read_text(encoding="utf-8"))
    path = Path(str(workspace["path"])).resolve()
    if workspace.get("mode") != "isolated-worktree" or not path.is_dir():
        raise DwError("check predecessor workspace is absent or not isolated")
    return path, str(workspace["identity"])


def _resolve_check_base(
    root: Path,
    run_id: str,
    node: dict[str, object],
    projection: dict[str, object],
    attempt: int,
) -> tuple[Path, str]:
    runner = node["runner"]
    cwd = str(runner.get("cwd", "."))
    if cwd == "workspace" or runner.get("path") == "workspace":
        return _workspace_for_check(root, run_id, node, projection)
    if runner["kind"] == "command":
        _run_path, grant, _compiled = _load_run_documents(root, run_id)
        tag = hashlib.sha256(str(root.resolve()).encode("utf-8")).hexdigest()[:16]
        workspace_root = root.resolve().parent / ".delivery-workbench-checks" / tag
        workspace_root.mkdir(parents=True, exist_ok=True, mode=0o700)
        workspace = workspace_root / run_id / f"{node['id']}-{attempt}"
        workspace.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        if workspace.exists():
            observed = subprocess.run(
                ["git", "-C", str(workspace), "rev-parse", "HEAD"],
                text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            )
            if observed.returncode or observed.stdout.strip() != grant["repository"]["head"]:
                raise DwError("existing check worktree differs from the granted HEAD")
        else:
            created = subprocess.run(
                ["git", "-C", str(root), "worktree", "add", "--detach",
                 str(workspace), str(grant["repository"]["head"])],
                text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            )
            if created.returncode:
                raise DwError("cannot create contained check worktree")
        base = workspace.resolve()
    else:
        base = root.resolve()
    identity_base = base
    if cwd not in {".", "workspace"}:
        target = (base / cwd).resolve()
        if target != base and base not in target.parents:
            raise DwError("check cwd escapes the repository")
        base = target
    return base, _sha({"path": str(identity_base), "head": head_sha(identity_base) or "none"})


class CheckManager:
    """Persistent, idempotent exact-check executor with bounded receipts."""

    def __init__(self, root: Path, runner: CheckRunner | None = None) -> None:
        self.root = root.resolve()
        self.runner = runner

    def _path(self, run_id: str, claim_id: str) -> Path:
        directory = _run_dir(self.root, run_id) / "check-sessions"
        directory.mkdir(parents=True, exist_ok=True, mode=0o700)
        return directory / (claim_id.split(":", 1)[-1] + ".json")

    @staticmethod
    def _write(path: Path, value: dict[str, object]) -> None:
        temporary = path.with_name("." + path.name + ".tmp")
        temporary.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        os.chmod(temporary, 0o600)
        os.replace(temporary, path)

    def _run_command(
        self,
        argv: list[str],
        cwd: Path,
        timeout: int,
        stdout: Path,
        stderr: Path,
        env: dict[str, str],
        path: Path,
        record: dict[str, object],
    ) -> int:
        if self.runner is not None:
            record["started"] = True
            self._write(path, record)
            return self.runner(argv, cwd, timeout, stdout, stderr, env)
        try:
            with stdout.open("wb") as out, stderr.open("wb") as err:
                process = subprocess.Popen(
                    argv,
                    cwd=str(cwd),
                    stdin=subprocess.DEVNULL,
                    stdout=out,
                    stderr=err,
                    env=env,
                    shell=False,
                    start_new_session=True,
                )
                record["started"] = True
                record["pid"] = process.pid
                self._write(path, record)
                try:
                    return int(process.wait(timeout=timeout))
                except subprocess.TimeoutExpired:
                    try:
                        os.killpg(process.pid, signal.SIGTERM)
                        process.wait(timeout=1)
                    except (OSError, subprocess.TimeoutExpired):
                        try:
                            os.killpg(process.pid, signal.SIGKILL)
                        except OSError:
                            pass
                        process.wait()
                    return 124
        except OSError:
            return 127

    def cancel(
        self, run_id: str, claim_id: str
    ) -> dict[str, object] | None:
        path = self._path(run_id, claim_id)
        if not path.is_file():
            return None
        record = json.loads(path.read_text(encoding="utf-8"))
        if record.get("state") == "starting":
            pid = record.get("pid")
            if isinstance(pid, int) and pid > 1:
                try:
                    os.killpg(pid, signal.SIGTERM)
                except ProcessLookupError:
                    pass
                except OSError:
                    record["state"] = "lost"
                    record["reason"] = "interrupt-unconfirmed"
                else:
                    record["state"] = "cancelled"
                    record["reason"] = "interrupted"
            else:
                record["state"] = "cancelled"
                record["reason"] = "cancelled-before-start"
            record["finished_at"] = _format_time(datetime.now(timezone.utc))
            self._write(path, record)
        return record

    def execute(
        self,
        run_id: str,
        claim: dict[str, object],
        node: dict[str, object],
        projection: dict[str, object],
    ) -> dict[str, object]:
        path = self._path(run_id, str(claim["claim_id"]))
        if path.is_file():
            record = json.loads(path.read_text(encoding="utf-8"))
            if record.get("state") == "starting":
                pid = record.get("pid")
                alive = False
                if isinstance(pid, int) and pid > 1:
                    try:
                        os.kill(pid, 0)
                        alive = True
                    except OSError:
                        alive = False
                if alive:
                    return {**record, "state": "running", "reason": "running"}
                record.update({
                    "state": "lost", "reason": "recovery-uncertain",
                    "finished_at": _format_time(datetime.now(timezone.utc)),
                })
                self._write(path, record)
            return record

        runner = node["runner"]
        base, workspace_identity = _resolve_check_base(
            self.root, run_id, node, projection, int(claim["attempt"])
        )
        timeout = int(runner["timeout_seconds"])
        output_limit = min(int(runner["output_bytes"]), MAX_CHECK_OUTPUT_BYTES)
        execution_id = "check-" + str(claim["claim_id"]).split(":", 1)[-1][:24]
        staging = path.parent / execution_id
        staging.mkdir(parents=True, exist_ok=True, mode=0o700)
        stdout = staging / "stdout.log"
        stderr = staging / "stderr.log"
        started_at = _format_time(datetime.now(timezone.utc))
        record: dict[str, object] = {
            "kind": CHECK_RECEIPT_KIND,
            "schema_version": CONDUCTOR_SCHEMA_VERSION,
            "run_id": run_id,
            "node_id": node["id"],
            "attempt": claim["attempt"],
            "claim_id": claim["claim_id"],
            "execution_id": execution_id,
            "runner_kind": runner["kind"],
            "runner_hash": _sha(runner),
            "workspace_identity": workspace_identity,
            "state": "starting",
            "started": False,
            "reason": "starting",
            "expected_exit_code": node["expect"]["exit_code"],
            "actual_exit_code": None,
            "timeout_seconds": timeout,
            "stdout_bytes": 0,
            "stderr_bytes": 0,
            "stdout_truncated": False,
            "stderr_truncated": False,
            "declared_writes": list(runner.get("writes", [])),
            "changed_paths": [],
            "started_at": started_at,
            "finished_at": None,
            "pid": None,
        }
        self._write(path, record)

        try:
            before = _snapshot(base)
            exit_code = 1
            reason = "check-failed"
            if runner["kind"] == "command":
                argv = list(runner["argv"])
                exit_code = self._run_command(
                    argv, base, timeout, stdout, stderr, _safe_environment(),
                    path, record,
                )
                concurrent = json.loads(path.read_text(encoding="utf-8"))
                if concurrent.get("state") in {"cancelled", "lost"}:
                    return concurrent
                reason = (
                    "timeout" if exit_code == 124
                    else "start-failed" if exit_code == 127
                    else "completed"
                )
            elif runner["kind"] == "builtin":
                record["started"] = True
                name = str(runner["name"])
                target_value = runner.get("path")
                target = base if target_value == "workspace" else (
                    (self.root / str(target_value)).resolve() if target_value else None
                )
                if (
                    target is not None
                    and target not in {self.root, base}
                    and self.root not in target.parents
                    and base not in target.parents
                ):
                    raise DwError("built-in check path escapes its contained workspace")
                if name == "file-exists":
                    exit_code = 0 if target is not None and target.is_file() else 1
                elif name == "json-schema":
                    if target is None or not target.is_file() or not runner.get("schema"):
                        exit_code = 1
                    else:
                        schema_path = (self.root / str(runner["schema"])).resolve()
                        if self.root not in schema_path.parents or not schema_path.is_file():
                            raise DwError("built-in JSON schema is absent or escaped")
                        value = json.loads(target.read_text(encoding="utf-8"))
                        schema = json.loads(schema_path.read_text(encoding="utf-8"))
                        exit_code = 0 if not _schema_check(value, schema) else 1
                elif name == "diff-scope":
                    status = subprocess.run(
                        ["git", "-C", str(base), "status", "--porcelain=v1", "-z"],
                        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                    )
                    paths = []
                    for token in status.stdout.split(b"\0"):
                        if len(token) >= 4:
                            paths.append(os.fsdecode(token[3:]))
                    allowed = list(runner.get("allowed_paths", []))
                    exit_code = 0 if status.returncode == 0 and all(
                        any(fnmatch.fnmatch(item, pattern) for pattern in allowed)
                        for item in paths
                    ) else 1
                elif name == "rail-status":
                    status = build_status(self.root, str(projection["project"]))
                    exit_code = 0 if status.get("rails", {}).get("healthy") and status.get("roadmap", {}).get("healthy") else 1
                else:
                    exit_code = 1
                reason = "completed"
            else:
                raise DwError("check runner kind is unsupported")
            after = _snapshot(base)
            changed = _changed_paths(before, after)
            writes = list(runner.get("writes", []))
            escaped = [
                item for item in changed
                if not any(fnmatch.fnmatch(item, pattern) for pattern in writes)
            ]
            if escaped:
                exit_code = 1
                reason = "write-scope"
            stdout_bytes = stdout.stat().st_size if stdout.is_file() else 0
            stderr_bytes = stderr.stat().st_size if stderr.is_file() else 0
            expected = int(node["expect"]["exit_code"])
            success = exit_code == expected and reason not in {"write-scope", "timeout", "start-failed"}
            record.update({
                "state": "succeeded" if success else "failed",
                "reason": "passed" if success else reason,
                "actual_exit_code": exit_code,
                "stdout_bytes": min(stdout_bytes, output_limit + 1),
                "stderr_bytes": min(stderr_bytes, output_limit + 1),
                "stdout_truncated": stdout_bytes > output_limit,
                "stderr_truncated": stderr_bytes > output_limit,
                "changed_paths": changed,
                "finished_at": _format_time(datetime.now(timezone.utc)),
            })
            if stdout_bytes > output_limit or stderr_bytes > output_limit:
                record["state"] = "failed"
                record["reason"] = "oversized-output"
        except (DwError, OSError, ValueError, json.JSONDecodeError):
            record.update({
                "state": "failed", "reason": "check-refused",
                "actual_exit_code": None,
                "finished_at": _format_time(datetime.now(timezone.utc)),
            })
        self._write(path, record)
        return record


class RailManager:
    """Idempotent bridge to one fresh exact ``dw step`` lease."""

    def __init__(
        self, root: Path, runner: Callable[[list[str], Path], StepChild] | None = None
    ) -> None:
        self.root = root.resolve()
        self.runner = runner

    def execute(
        self,
        run_id: str,
        claim: dict[str, object],
        node: dict[str, object],
        project: str,
    ) -> dict[str, object]:
        directory = _run_dir(self.root, run_id) / "rail-sessions"
        directory.mkdir(parents=True, exist_ok=True, mode=0o700)
        path = directory / (str(claim["claim_id"]).split(":", 1)[-1] + ".json")
        if path.is_file():
            record = json.loads(path.read_text(encoding="utf-8"))
            if record["state"] == "starting":
                record.update({"state": "lost", "reason": "recovery-uncertain"})
                CheckManager._write(path, record)
            return record
        action = str(node["action"])
        execution_id = "rail-" + str(claim["claim_id"]).split(":", 1)[-1][:24]
        preview = build_step(self.root, project)
        observed_action = preview.get("action", {}).get("id") if isinstance(preview.get("action"), dict) else None
        record: dict[str, object] = {
            "kind": RAIL_RECEIPT_KIND,
            "schema_version": CONDUCTOR_SCHEMA_VERSION,
            "run_id": run_id,
            "node_id": node["id"],
            "attempt": claim["attempt"],
            "claim_id": claim["claim_id"],
            "execution_id": execution_id,
            "action": action,
            "lease": preview["token"],
            "state": "starting",
            "started": False,
            "reason": "starting",
            "exit_code": None,
            "before_action": observed_action,
            "after_action": None,
        }
        CheckManager._write(path, record)
        if action in {"certify-contract", "commit", "push", "release", "deploy"}:
            record.update({"state": "refused", "reason": "forbidden-authority"})
        elif not preview["applicable"] or observed_action != action:
            record.update({"state": "refused", "reason": "stale-action"})
        else:
            result, _code = apply_step(
                self.root,
                project,
                str(preview["token"]),
                runner=self.runner,
                max_output_bytes=10_000,
            )
            after = result.get("after")
            record.update({
                "state": "succeeded" if result["outcome"] == "succeeded" else "failed",
                "started": result["started"],
                "reason": result["outcome"],
                "exit_code": result["exit_code"],
                "after_action": after.get("action_id") if isinstance(after, dict) else None,
            })
        CheckManager._write(path, record)
        return record


def _executor_receipt(
    run_id: str,
    claim: dict[str, object],
    executor: str,
    state: str,
    reason: str,
) -> dict[str, object]:
    return {
        "kind": "delivery-workbench-executor-receipt",
        "schema_version": CONDUCTOR_SCHEMA_VERSION,
        "run_id": run_id,
        "node_id": claim["node_id"],
        "attempt": claim["attempt"],
        "claim_id": claim["claim_id"],
        "executor": executor,
        "state": state,
        "reason": reason,
    }


def _append_receipt(
    root: Path,
    projection: dict[str, object],
    claim: dict[str, object],
    executor: str,
    receipt: dict[str, object],
    execution_id: object,
    *,
    now: datetime | None,
) -> tuple[dict[str, object], bool]:
    receipt_hash = _sha(receipt)
    previous = [
        item for item in projection["node_receipts"]
        if item["claim_id"] == claim["claim_id"]
    ]
    if previous and previous[-1]["receipt_hash"] == receipt_hash:
        return projection, False
    usage = receipt.get("usage") if executor == "driver" else None
    usage_doc = usage if isinstance(usage, dict) else {}
    usage_status = (
        str(usage_doc.get("status") or "unknown")
        if executor == "driver" else "not-applicable"
    )
    total_tokens = usage_doc.get("total_tokens")
    cost_microunits = usage_doc.get("cost_microunits")
    updated = record_runtime_event(
        root,
        str(projection["run_id"]),
        "node_receipt",
        {
            "node_id": claim["node_id"],
            "attempt": claim["attempt"],
            "claim_id": claim["claim_id"],
            "executor": executor,
            "execution_id": str(execution_id or "none"),
            "state": str(receipt["state"]),
            "reason": _bounded_reason(receipt.get("reason"), str(receipt["state"])),
            "receipt_hash": receipt_hash,
            "usage_status": usage_status,
            "total_tokens": (
                int(total_tokens) if total_tokens is not None else "unknown"
            ),
            "cost_microunits": (
                int(cost_microunits) if cost_microunits is not None else "unknown"
            ),
        },
        str(projection["ledger_head"]),
        now=now,
    )
    return updated, True


def _observe_activity(
    root: Path,
    projection: dict[str, object],
    claim: dict[str, object],
    receipt: dict[str, object],
    *,
    now: datetime | None,
) -> dict[str, object]:
    """Record a driver activity transition as a ledger fact, once per change.

    Activity is a separate axis from lifecycle state: it says what a live
    session is doing. Unchanged activity appends nothing, so a replayed
    tick stays idempotent.
    """
    activity = receipt.get("activity")
    if not activity:
        return projection
    last = claim.get("last_activity") or {}
    if last.get("activity") == activity:
        return projection
    updated = record_runtime_event(
        root,
        str(projection["run_id"]),
        "activity_observed",
        {
            "node_id": claim["node_id"],
            "attempt": claim["attempt"],
            "claim_id": claim["claim_id"],
            "activity": str(activity),
            "session_id": str(receipt.get("session_id") or "none"),
        },
        str(projection["ledger_head"]),
        now=now,
    )
    claim["last_activity"] = {"activity": str(activity)}
    return updated


def _boundary(hook: BoundaryHook | None, name: str, detail: dict[str, object]) -> None:
    if hook is not None:
        hook(name, detail)


def _driver_manager(
    root: Path,
    driver_config: object | None,
    adapters: dict[str, object] | None,
) -> DriverManager:
    config = load_driver_config(root, driver_config)
    return DriverManager(root, config, adapters=adapters)


def _run_memory_recall(
    root: Path,
    run_id: str,
    projection: dict[str, object],
    grant: dict[str, object],
    compiled: dict[str, object],
    actions: list[dict[str, object]],
    *,
    now: datetime | None,
) -> tuple[dict[str, object], dict[str, dict]]:
    story = grant.get("story")
    if not isinstance(story, dict) or not story.get("story_path"):
        raise MemoryRecallActionNeeded(
            "malformed", "run grant has no story path for memory recall"
        )
    story_path = root / str(story["story_path"])
    try:
        story_criteria = story_path.read_text(encoding="utf-8")
        knowledge = build_repository_knowledge_packet(root, story_path)
        story_id = str(story.get("story_id") or story.get("id") or "")
        phase = str(story.get("phase") or "")
        documents, _built = persist_recall_slices(
            _run_dir(root, run_id),
            subject=run_id,
            knowledge=knowledge,
            story_criteria=story_criteria,
            story_ids=[story_id] if story_id else [],
            phase_ids=[phase] if phase else [],
            orchestration_tags=[str(compiled["score"].get("slug") or "bounded-run")],  # type: ignore[union-attr]
            require_existing=bool(projection.get("memory_recalls")),
        )
    except MemoryRecallActionNeeded:
        raise
    except (DwError, OSError, UnicodeError, ValueError) as exc:
        raise MemoryRecallActionNeeded(
            "malformed", "memory recall could not be assembled: " + str(exc)
        ) from exc
    for audience in sorted(documents):
        document = documents[audience]
        prior = next((
            item for item in projection["memory_recalls"]
            if item["recall_id"] == document["recall_id"]
            and item["audience"] == audience
        ), None)
        if prior is not None:
            continue
        projection = record_runtime_event(
            root,
            run_id,
            "memory-recall-built",
            recall_event_detail(document),
            str(projection["ledger_head"]),
            now=now,
        )
        actions.append({
            "action": "memory-recall-built",
            "audience": audience,
            "recall_id": document["recall_id"],
        })
    return projection, documents


def _memory_action_needed(
    started: dict[str, object],
    projection: dict[str, object],
    actions: list[dict[str, object]],
    error: MemoryRecallActionNeeded,
    decision: dict[str, object] | None = None,
) -> dict[str, object]:
    item = {
        "kind": "memory-recall",
        "reason": error.reason,
        "message": error.message,
    }
    actions.append({"action": "action-needed", **item})
    if decision is None:
        decision = {
            "eligible": [], "scheduled": [], "blocked": [],
            "action_needed": [item],
        }
    else:
        decision = {**decision, "scheduled": [],
                    "action_needed": list(decision.get("action_needed", [])) + [item]}
    return _tick_document(started, projection, actions, decision)


def _reconcile_claim(
    root: Path,
    run_id: str,
    claim_id: str,
    driver_config: object | None,
    adapters: dict[str, object] | None,
    check_manager: CheckManager,
    rail_manager: RailManager,
    actions: list[dict[str, object]],
    *,
    now: datetime | None,
    boundary_hook: BoundaryHook | None,
) -> dict[str, object]:
    projection = replay_run(root, run_id, now=now)
    claim = next(
        (item for item in projection["active_claims"] if item["claim_id"] == claim_id),
        None,
    )
    if claim is None:
        return projection
    _run_path, grant, compiled = _load_run_documents(root, run_id)
    node = _node_map(compiled)[str(claim["node_id"])]
    control_state = str(projection["state"])

    if node["type"] == "agent":
        projection, memory_documents = _run_memory_recall(
            root, run_id, projection, grant, compiled, actions, now=now
        )
        audience = recall_audience(node.get("role"))
        memory_document = memory_documents[audience]
        manager = _driver_manager(root, driver_config, adapters)
        receipt = manager.receipt_for_claim(run_id, claim_id)
        if control_state == "cancelled":
            if receipt is not None and receipt["state"] == "running":
                receipt = manager.interrupt(run_id, str(receipt["session_id"]))
            if receipt is None:
                receipt = _executor_receipt(run_id, claim, "driver", "cancelled", "cancelled-before-start")
        elif control_state in {"revoked", "blocked", "awaiting-certification"} and receipt is None:
            receipt = _executor_receipt(run_id, claim, "driver", "cancelled", "authority-ended-before-start")
        elif control_state == "paused" and receipt is None:
            receipt = _executor_receipt(run_id, claim, "driver", "cancelled", "paused-before-start")
        elif receipt is None:
            try:
                packet = build_work_packet(
                    root, run_id, claim_id, manager.config, now=now,
                    memory_recall=memory_document,
                )
                attachment = next((
                    item for item in projection["memory_attachments"]
                    if item["claim_id"] == claim_id
                ), None)
                attachment_detail = {
                    **recall_event_detail(memory_document),
                    "node_id": node["id"],
                    "claim_id": claim_id,
                    "packet_hash": packet["packet_hash"],
                }
                if attachment is None:
                    projection = record_runtime_event(
                        root, run_id, "memory-recall-attached",
                        attachment_detail, str(projection["ledger_head"]), now=now,
                    )
                    actions.append({
                        "action": "memory-recall-attached",
                        "node_id": node["id"],
                        "recall_id": memory_document["recall_id"],
                    })
                elif any(
                    attachment.get(key) != value
                    for key, value in attachment_detail.items()
                ):
                    raise MemoryRecallActionNeeded(
                        "tampered", "memory recall attachment differs on recovery"
                    )
                _boundary(boundary_hook, "before-driver-start", {"node_id": node["id"], "attempt": claim["attempt"]})
                receipt = manager.start(
                    packet, f"dispatch-{node['id']}-{claim['attempt']}"
                )
                _boundary(boundary_hook, "after-driver-start", {"node_id": node["id"], "attempt": claim["attempt"]})
            except MemoryRecallActionNeeded:
                raise
            except DwError as exc:
                message = exc.message.lower()
                reason = (
                    "unsupported-authority"
                    if any(mark in message for mark in ("profile", "capabil", "workspace", "adapter", "ceiling"))
                    else "artifact-gate" if "artifact" in message
                    else "grant-stale" if "grant" in message or "dispatch" in message
                    else "driver-refused"
                )
                receipt = _executor_receipt(run_id, claim, "driver", "failed", reason)
        projection, appended = _append_receipt(
            root, projection, claim, "driver", receipt,
            receipt.get("session_id"), now=now,
        )
        if appended:
            actions.append({"action": "receipt", "node_id": node["id"], "state": receipt["state"]})
        projection = _observe_activity(root, projection, claim, receipt, now=now)
        if receipt["state"] == "running" and control_state not in {"cancelled"}:
            polled = manager.poll(run_id, str(receipt["session_id"]))
            projection, appended = _append_receipt(
                root, projection, claim, "driver", polled,
                polled.get("session_id"), now=now,
            )
            if appended:
                actions.append({
                    "action": "poll", "node_id": node["id"],
                    "state": polled["state"],
                    "activity": polled.get("activity"),
                })
            projection = _observe_activity(root, projection, claim, polled, now=now)
            receipt = polled
        if receipt["state"] == "running":
            return projection
        artifact_bytes = 0
        outcome = str(receipt["state"])
        if outcome == "succeeded":
            try:
                artifacts = manager.collect(run_id, str(receipt["session_id"]))
                artifact_bytes = sum(int(item["bytes"]) for item in artifacts)
                _boundary(
                    boundary_hook,
                    "after-collect",
                    {"node_id": node["id"], "attempt": claim["attempt"]},
                )
                budget = projection["budgets"]["max_artifact_bytes"]
                if int(budget["used"]) + artifact_bytes > int(budget["limit"]):
                    raise DwError("artifact budget exhausted")
            except DwError as exc:
                reason = "artifact-budget" if "budget" in exc.message.lower() else "artifact-validation"
                validation = _executor_receipt(run_id, claim, "driver", "failed", reason)
                projection, _ = _append_receipt(
                    root, projection, claim, "driver", validation,
                    receipt.get("session_id"), now=now,
                )
                outcome = "failed"
                artifact_bytes = 0
        ledger_outcome = outcome if outcome in {"succeeded", "failed", "cancelled", "lost"} else "failed"
        projection = release_node_claim(
            root, run_id, claim_id, ledger_outcome, artifact_bytes,
            str(projection["ledger_head"]), now=now,
        )
        actions.append({"action": "release", "node_id": node["id"], "outcome": ledger_outcome})
        _boundary(boundary_hook, "after-release", {"node_id": node["id"], "attempt": claim["attempt"]})
        return projection

    if control_state in {"cancelled", "revoked", "paused", "blocked", "awaiting-certification"}:
        if node["type"] == "check" and control_state == "cancelled":
            receipt = check_manager.cancel(run_id, claim_id)
        elif node["type"] == "check":
            receipt = check_manager.execute(run_id, claim, node, projection)
        else:
            receipt = None
        if receipt is None:
            receipt = _executor_receipt(
                run_id, claim, str(node["type"]), "cancelled",
                "authority-ended-before-start",
            )
        projection, _ = _append_receipt(
            root, projection, claim, str(node["type"]), receipt,
            receipt.get("execution_id"), now=now,
        )
        if receipt["state"] == "running":
            return projection
        state = str(receipt["state"])
        outcome = state if state in {"succeeded", "failed", "cancelled", "lost"} else "cancelled"
        return release_node_claim(
            root, run_id, claim_id, outcome, 0,
            str(projection["ledger_head"]), now=now,
        )

    if node["type"] == "check":
        _boundary(boundary_hook, "before-check", {"node_id": node["id"], "attempt": claim["attempt"]})
        receipt = check_manager.execute(run_id, claim, node, projection)
        _boundary(boundary_hook, "after-check", {"node_id": node["id"], "attempt": claim["attempt"]})
        executor = "check"
    elif node["type"] == "rail":
        _boundary(boundary_hook, "before-rail", {"node_id": node["id"], "attempt": claim["attempt"]})
        receipt = rail_manager.execute(run_id, claim, node, str(grant["project"]))
        _boundary(boundary_hook, "after-rail", {"node_id": node["id"], "attempt": claim["attempt"]})
        executor = "rail"
    elif node["type"] == "collect":
        required = _required_artifacts(node)
        present = {str(item["name"]) for item in artifact_inventory(root, run_id)}
        success = set(required) <= present and not node.get("outputs")
        receipt = _executor_receipt(
            run_id, claim, "collect",
            "succeeded" if success else "failed",
            "collected" if success else "unsupported-collection-output",
        )
        receipt["execution_id"] = "collect-" + str(claim_id).split(":", 1)[-1][:24]
        executor = "collect"
    else:
        raise DwError(f"unsupported claimed node type: {node['type']}")

    projection, _ = _append_receipt(
        root, projection, claim, executor, receipt,
        receipt.get("execution_id"), now=now,
    )
    if receipt["state"] == "running":
        return projection
    if executor == "rail" and receipt["state"] == "succeeded":
        facts = observed_fact_binding(root, grant, str(node["id"]), str(node["action"]))
        projection = record_runtime_event(
            root, run_id, "rail_advanced", facts,
            str(projection["ledger_head"]), now=now,
        )
    outcome = "succeeded" if receipt["state"] == "succeeded" else (
        "lost" if receipt["state"] == "lost" else "failed"
    )
    projection = release_node_claim(
        root, run_id, claim_id, outcome, 0,
        str(projection["ledger_head"]), now=now,
    )
    actions.append({"action": "release", "node_id": node["id"], "outcome": outcome})
    _boundary(boundary_hook, "after-release", {"node_id": node["id"], "attempt": claim["attempt"]})
    return projection


def _latest_receipt_reason(claim: dict[str, object]) -> str:
    receipts = claim.get("receipts", [])
    return str(receipts[-1]["reason"]) if receipts else str(claim["outcome"])


def _record_failure_policy(
    root: Path,
    run_id: str,
    projection: dict[str, object],
    compiled: dict[str, object],
    node_id: str,
    attempt: int,
    actions: list[dict[str, object]],
    *,
    now: datetime | None,
) -> dict[str, object]:
    node = _node_map(compiled)[node_id]
    claim = next(
        item for item in projection["completed_claims"]
        if item["node_id"] == node_id and int(item["attempt"]) == attempt
    )
    fatal = _latest_receipt_reason(claim) in FATAL_RECEIPT_REASONS
    policy = node.get("on_failure") if not fatal else {"action": "abort"}
    policy = policy if isinstance(policy, dict) else {"action": "abort"}
    action = str(policy["action"])
    target = "none"
    visit = 0
    target_attempt = 0
    if action == "retry":
        maximum = int(policy["max_attempts"])
        if attempt >= maximum or attempt >= 20:
            action = "exhausted"
            target = "max-attempts"
            visit = maximum
        else:
            target = node_id
            target_attempt = attempt + 1
            visit = attempt
    elif action == "route":
        target = str(policy["node"])
        prior = [
            item for item in projection["routes"]
            if item["node_id"] == node_id and item["action"] == "route"
        ]
        visit = len(prior) + 1
        if visit > int(policy["max_visits"]):
            action = "exhausted"
            target = "max-visits"
            target_attempt = 0
        else:
            target_attempt = 1 + max(
                [
                    int(item["attempt"])
                    for item in projection["active_claims"] + projection["completed_claims"]
                    if item["node_id"] == target
                ] or [0]
            )
            if target_attempt > 20:
                action = "exhausted"
                target = "attempt-ceiling"
                target_attempt = 0
    elif action == "approval":
        target = str(policy["checkpoint"])
        visit = 1
    elif action in {"pause", "abort"}:
        target = action
        visit = 1
    projection = record_runtime_event(
        root,
        run_id,
        "failure_routed",
        {
            "node_id": node_id,
            "attempt": attempt,
            "action": action,
            "target": target,
            "visit": visit,
            "target_attempt": target_attempt,
        },
        str(projection["ledger_head"]),
        now=now,
    )
    actions.append({"action": "failure-route", "node_id": node_id, "route": action})
    if action == "pause":
        projection = transition_run(
            root, run_id, "pause", str(projection["ledger_head"]),
            reason=f"node {node_id} attempt {attempt} failed", now=now,
        )
    elif action in {"abort", "exhausted"}:
        projection = record_runtime_event(
            root,
            run_id,
            "run_aborted",
            {
                "node_id": node_id,
                "reason": "failure-policy-abort" if action == "abort" else "failure-policy-exhausted",
                "generation": int(projection["control_generation"]) + 1,
            },
            str(projection["ledger_head"]),
            now=now,
        )
    elif action == "approval":
        projection = record_runtime_event(
            root,
            run_id,
            "checkpoint_reached",
            {
                "node_id": node_id,
                "checkpoint": target,
                "mode": "failure",
                "terminal": "none",
                "reason": "node-failed",
            },
            str(projection["ledger_head"]),
            now=now,
        )
    return projection


_SCM_NUDGE_KINDS = {"ci-failed", "changes-requested", "merge-conflict"}


def _pending_nudge_for(
    projection: dict[str, object], node_id: str
) -> dict[str, object] | None:
    completed = {
        int(item["attempt"]) for item in projection["completed_claims"]
        if str(item["node_id"]) == node_id
    }
    active = {
        int(item["attempt"]) for item in projection["active_claims"]
        if str(item["node_id"]) == node_id
    }
    for entry in reversed(list(projection.get("nudges", []))):
        if entry.get("delivered") and str(entry["node_id"]) == node_id:
            attempt = int(entry["attempt"])
            if attempt not in completed and attempt not in active:
                return entry
    return None


def _nudge_triggers(
    root: Path,
    grant: dict[str, object],
    projection: dict[str, object],
    rules: list[dict[str, object]],
    observed: datetime,
) -> list[tuple[dict[str, object], str]]:
    """Match current outward facts against score rules; pure read."""
    triggers: list[tuple[dict[str, object], str]] = []
    channel = str(grant.get("signal_channel") or "")
    chan: dict[str, object] | None = None
    if channel and any(r.get("signal") in _SCM_NUDGE_KINDS for r in rules):
        remote, _, branch = channel.partition("/")
        try:
            chan = signal_replay_channel(root, remote, branch)
        except DwError:
            chan = None
    for rule in rules:
        kind = str(rule.get("signal"))
        if kind in _SCM_NUDGE_KINDS:
            if chan is None:
                continue
            fact = signal_latest_nudge_fact(chan, kind)
            if fact is not None:
                triggers.append((rule, str(fact["event_hash"])))
        elif kind == "waiting-input-timeout":
            after = int(rule.get("after_seconds", 60))
            for claim in projection["active_claims"]:
                if str(claim["node_id"]) != str(rule.get("target")):
                    continue
                last = claim.get("last_activity") or {}
                if last.get("activity") != "waiting_input" or not last.get("ts"):
                    continue
                age = (observed - _parse_time(last["ts"], "ts")).total_seconds()
                if age >= after:
                    triggers.append((
                        rule,
                        _sha(["waiting-input", claim["claim_id"], last.get("seq")]),
                    ))
    return triggers


def _standing_covers(grant: dict[str, object], rule: dict[str, object]) -> bool:
    for item in grant.get("standing_nudge_rules", []):  # type: ignore[union-attr]
        if str(item.get("signal")) != str(rule.get("signal")):
            continue
        target = str(item.get("target") or "")
        if not target or target == str(rule.get("target")):
            return True
    return False


def _manual_nudge_decision(
    projection: dict[str, object], rule_id: str, signal_hash: str
) -> str:
    for request in reversed(list(projection.get("request_history", []))):
        if (
            request.get("kind") == "nudge"
            and request.get("origin") == rule_id
            and request.get("signal_hash") == signal_hash
        ):
            return str(request.get("status") or "")
    return ""


def _evaluate_nudges(
    root: Path,
    run_id: str,
    projection: dict[str, object],
    compiled: dict[str, object],
    grant: dict[str, object],
    actions: list[dict[str, object]],
    *,
    driver_config: object | None = None,
    adapters: dict[str, object] | None = None,
    now: datetime | None,
) -> dict[str, object]:
    """Turn matched outward facts into at-most-once ledgered nudges.

    Rule (score) -> authority (grant standing rules + budgets) ->
    receptivity (target session) -> receipt (ledger). Every stop on that
    path is a distinct recorded refusal; delivery on an
    awaiting-certification run is the sanctioned wake.
    """
    rules = [
        rule for rule in compiled["score"].get("nudges", [])  # type: ignore[union-attr]
        if isinstance(rule, dict)
    ]
    if not rules:
        return projection
    state = str(projection["state"])
    if state not in {"active", "awaiting-certification", "paused"}:
        return projection
    observed = (now or datetime.now(timezone.utc)).astimezone(timezone.utc).replace(microsecond=0)
    triggers = _nudge_triggers(root, grant, projection, rules, observed)
    for rule, signal_hash in triggers:
        rule_id = str(rule["id"])
        entries = [
            item for item in projection["nudges"]
            if item["rule"] == rule_id and item["signal_hash"] == signal_hash
        ]
        if any(item["delivered"] for item in entries):
            continue

        def refused(reason: str) -> bool:
            if any(
                not item["delivered"] and item.get("reason") == reason
                for item in entries
            ):
                return False
            nonlocal projection
            projection = record_runtime_event(
                root, run_id, "nudge_refused",
                {"rule": rule_id, "signal": str(rule["signal"]),
                 "signal_hash": signal_hash, "reason": reason},
                str(projection["ledger_head"]), now=now,
            )
            actions.append({
                "action": "nudge-refused", "rule": rule_id, "reason": reason,
            })
            return True

        if projection["expired"]:
            refused("grant-expired")
            continue
        if state == "paused":
            refused("run-inactive")
            continue
        delivered_total = [
            item for item in projection["nudges"]
            if item["delivered"] and item["rule"] == rule_id
        ]
        if len(delivered_total) >= int(rule.get("max_total", 1)):
            refused("rule-exhausted")
            continue
        budget = projection["budgets"]["max_nudges"]
        if int(budget["used"]) >= int(budget["limit"]):
            if refused("nudge-budget-exhausted") and str(projection["state"]) == "active":
                projection = record_runtime_event(
                    root, run_id, "run_aborted",
                    {"node_id": "conductor", "reason": "nudge-budget-exhausted",
                     "generation": int(projection["control_generation"]) + 1},
                    str(projection["ledger_head"]), now=now,
                )
                actions.append({"action": "abort", "reason": "nudge-budget-exhausted"})
            continue
        manual = _manual_nudge_decision(projection, rule_id, signal_hash)
        if not _standing_covers(grant, rule) and manual != "approved":
            if manual != "rejected":
                refused("no-standing-rule")
            continue
        target = str(rule["target"])
        active_claim = next(
            (item for item in projection["active_claims"]
             if str(item["node_id"]) == target),
            None,
        )
        if active_claim is None:
            activity = "idle"
        else:
            activity = str(
                (active_claim.get("last_activity") or {}).get("activity", "unknown")
            )
        verdict = signal_receptivity(activity, "auto")
        if verdict == "defer":
            actions.append({"action": "nudge-deferred", "rule": rule_id})
            continue
        if verdict == "refuse":
            refused("non-receptive")
            continue
        session_id = None
        if active_claim is not None:
            # Session delivery: the target is live and receptive; the
            # packet goes through the driver seam. Adapters that cannot
            # inject (non-interactive exec) refuse honestly.
            attempt = int(active_claim["attempt"])
            manager = _driver_manager(root, driver_config, adapters)
            receipt = manager.receipt_for_claim(run_id, str(active_claim["claim_id"]))
            session_id = str(receipt["session_id"]) if receipt else None
            if session_id is None or not manager.can_nudge(run_id, session_id):
                refused("non-receptive")
                continue
        else:
            past = [
                int(item["attempt"]) for item in projection["completed_claims"]
                if str(item["node_id"]) == target
            ]
            attempt = (max(past) + 1) if past else 1
            if attempt > 20:
                refused("attempt-ceiling")
                continue
        remaining = int(budget["limit"]) - int(budget["used"]) - 1
        projection = record_runtime_event(
            root, run_id, "nudge_delivered",
            {"rule": rule_id, "signal": str(rule["signal"]),
             "signal_hash": signal_hash, "node_id": target,
             "attempt": attempt, "remaining": remaining},
            str(projection["ledger_head"]), now=now,
        )
        if session_id is not None:
            manager.nudge_session(run_id, session_id, {
                "kind": "delivery-workbench-nudge",
                "schema_version": 1,
                "run_id": run_id,
                "rule": rule_id,
                "signal": str(rule["signal"]),
                "signal_hash": signal_hash,
                "node_id": target,
                "attempt": attempt,
                "expectation": str(rule.get("expectation") or ""),
            })
        actions.append({
            "action": "nudge-delivered", "rule": rule_id,
            "node_id": target, "attempt": attempt,
        })
        state = str(projection["state"])
    return projection


def _observe_external_commit(
    root: Path,
    run_id: str,
    projection: dict[str, object],
    grant: dict[str, object],
    *,
    now: datetime | None,
) -> tuple[dict[str, object], bool]:
    if projection["state"] not in {"awaiting-certification", "complete", "blocked"}:
        return projection, False
    previous = str(
        projection["external_commits"][-1]["head"]
        if projection["external_commits"]
        else (
            projection["fact_binding"]["head"]
            if projection.get("fact_binding") else grant["repository"]["head"]
        )
    )
    current = head_sha(root) or "none"
    if current == previous or any(item["head"] == current for item in projection["external_commits"]):
        return projection, False
    if in_rewrite_state(root):
        relation = "rewritten"
    else:
        ancestor = subprocess.run(
            ["git", "-C", str(root), "merge-base", "--is-ancestor", previous, current],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
        relation = "fast-forward" if ancestor.returncode == 0 else "diverged"
    binding = observed_external_fact_binding(root, grant, relation)
    updated = record_runtime_event(
        root,
        run_id,
        "external_commit_observed",
        {
            "previous_head": previous,
            "relation": relation,
            **binding,
        },
        str(projection["ledger_head"]),
        now=now,
    )
    return updated, True


def _tick_run_once(
    root: Path,
    run_id: str,
    *,
    driver_config: object | None = None,
    adapters: dict[str, object] | None = None,
    check_runner: CheckRunner | None = None,
    rail_runner: Callable[[list[str], Path], StepChild] | None = None,
    now: datetime | None = None,
    boundary_hook: BoundaryHook | None = None,
) -> dict[str, object]:
    """Reconcile and dispatch one deterministic, restart-safe scheduler tick."""
    root = root.resolve()
    started = replay_run(root, run_id, now=now)
    before_head = str(started["ledger_head"])
    _run_path, grant, compiled = _load_run_documents(root, run_id)
    actions: list[dict[str, object]] = []
    closes_requests = (
        started["state"] in TERMINAL_STATES
        and started["state"] != "awaiting-certification"
    )
    maintained = maintain_outstanding_requests(
        root, run_id, before_head, now=now,
        republish=not closes_requests,
        force_expire=closes_requests,
    )
    if maintained["ledger_head"] != before_head:
        actions.append({
            "action": "requests-maintained",
            "outstanding": len(maintained["outstanding_requests"]),
        })
    check_manager = CheckManager(root, check_runner)
    rail_manager = RailManager(root, rail_runner)

    active_agent = any(
        _node_map(compiled)[str(claim["node_id"])]["type"] == "agent"
        for claim in maintained["active_claims"]
    )
    if active_agent and maintained["state"] == "active":
        try:
            maintained, _documents = _run_memory_recall(
                root, run_id, maintained, grant, compiled, actions, now=now
            )
        except MemoryRecallActionNeeded as exc:
            return _memory_action_needed(started, maintained, actions, exc)

    # Claims always reconcile before new eligibility. Cancellation first
    # prevents any future start, then interrupts a persisted live session.
    ordered = sorted(
        list(maintained["active_claims"]),
        key=lambda item: (_node_index(compiled)[str(item["node_id"])], int(item["attempt"])),
    )
    for claim in ordered:
        try:
            _reconcile_claim(
                root, run_id, str(claim["claim_id"]), driver_config, adapters,
                check_manager, rail_manager, actions, now=now,
                boundary_hook=boundary_hook,
            )
        except MemoryRecallActionNeeded as exc:
            return _memory_action_needed(
                started, replay_run(root, run_id, now=now), actions, exc
            )

    projection = replay_run(root, run_id, now=now)
    if projection["state"] == "awaiting-certification":
        # Outward observation first, then the nudge engine: a granted,
        # covered nudge is the one sanctioned wake from this terminal.
        projection, observed = _observe_external_commit(
            root, run_id, projection, grant, now=now
        )
        if observed:
            actions.append({"action": "external-commit-observed", "state": projection["state"]})
        projection = _evaluate_nudges(
            root, run_id, projection, compiled, grant, actions,
            driver_config=driver_config, adapters=adapters, now=now,
        )
    elif projection["state"] in {"active", "paused"}:
        projection = _evaluate_nudges(
            root, run_id, projection, compiled, grant, actions,
            driver_config=driver_config, adapters=adapters, now=now,
        )
    if projection["state"] in TERMINAL_STATES:
        projection, observed = _observe_external_commit(
            root, run_id, projection, grant, now=now
        )
        if observed:
            actions.append({"action": "external-commit-observed", "state": projection["state"]})
        return _tick_document(started, projection, actions, None)
    if projection["state"] != "active":
        return _tick_document(started, projection, actions, None)
    if projection["expired"] or projection["budgets"]["max_wall_seconds"]["used"] >= projection["budgets"]["max_wall_seconds"]["limit"]:
        reason = "grant-expired" if projection["expired"] else "wall-budget-exhausted"
        projection = record_runtime_event(
            root,
            run_id,
            "run_aborted",
            {"node_id": "conductor", "reason": reason,
             "generation": int(projection["control_generation"]) + 1},
            str(projection["ledger_head"]),
            now=now,
        )
        actions.append({"action": "abort", "reason": reason})
        return _tick_document(started, projection, actions, None)

    # Every failed completion receives exactly one configured finite route.
    decision = schedule_decision(compiled, projection, artifact_inventory(root, run_id))
    for needed in decision["action_needed"]:
        projection = _record_failure_policy(
            root, run_id, projection, compiled,
            str(needed["node_id"]), int(needed["attempt"]), actions, now=now,
        )
        if projection["state"] != "active":
            return _tick_document(started, projection, actions, None)

    decision = schedule_decision(compiled, projection, artifact_inventory(root, run_id))
    for resolution in decision["resolution_needed"]:
        projection = record_runtime_event(
            root, run_id, "route_resolved", dict(resolution),
            str(projection["ledger_head"]), now=now,
        )
        actions.append({
            "action": "route-resolved", "node_id": resolution["node_id"],
            "outcome": resolution["outcome"],
        })

    decision = schedule_decision(compiled, projection, artifact_inventory(root, run_id))
    if decision["terminal_needed"]:
        projection = record_runtime_event(
            root,
            run_id,
            "run_terminal",
            {"node_id": "conductor", "meaning": "awaiting-certification"},
            str(projection["ledger_head"]),
            now=now,
        )
        actions.append({"action": "terminal", "state": "awaiting-certification"})
        return _tick_document(started, projection, actions, decision)

    budget_blocks = {
        str(item["reason"])
        for item in decision["blocked"]
        if str(item["reason"]).startswith("max_")
        or item["reason"] in {"attempt-ceiling", "artifact-budget"}
    }
    if not decision["scheduled"] and not projection["active_claims"] and budget_blocks:
        projection = record_runtime_event(
            root,
            run_id,
            "run_aborted",
            {
                "node_id": "conductor",
                "reason": "budget-exhausted",
                "generation": int(projection["control_generation"]) + 1,
            },
            str(projection["ledger_head"]),
            now=now,
        )
        actions.append({"action": "abort", "reason": "budget-exhausted"})
        return _tick_document(started, projection, actions, decision)

    scheduled_agent = any(
        candidate["kind"] == "claim"
        and _node_map(compiled)[str(candidate["node_id"])]["type"] == "agent"
        for candidate in decision["scheduled"]
    )
    if scheduled_agent:
        try:
            projection, _documents = _run_memory_recall(
                root, run_id, projection, grant, compiled, actions, now=now
            )
        except MemoryRecallActionNeeded as exc:
            return _memory_action_needed(
                started, projection, actions, exc, decision
            )

    for candidate in decision["scheduled"]:
        node_id = str(candidate["node_id"])
        node = _node_map(compiled)[node_id]
        if candidate["kind"] == "checkpoint":
            projection = record_runtime_event(
                root,
                run_id,
                "checkpoint_reached",
                {
                    "node_id": node_id,
                    "checkpoint": node_id,
                    "mode": "normal",
                    "terminal": str(node.get("terminal") or "none"),
                    "reason": "dependencies-satisfied",
                },
                str(projection["ledger_head"]),
                now=now,
            )
            actions.append({"action": "checkpoint", "node_id": node_id, "state": projection["state"]})
            break
        attempt = int(candidate["attempt"])
        projection = claim_node(
            root,
            run_id,
            node_id,
            attempt,
            f"conduct-{node_id}-{attempt}",
            str(projection["ledger_head"]),
            now=now,
        )
        claim = next(
            item for item in projection["active_claims"]
            if item["node_id"] == node_id and int(item["attempt"]) == attempt
        )
        actions.append({"action": "claim", "node_id": node_id, "attempt": attempt})
        _boundary(boundary_hook, "after-claim", {"node_id": node_id, "attempt": attempt})
        try:
            projection = _reconcile_claim(
                root, run_id, str(claim["claim_id"]), driver_config, adapters,
                check_manager, rail_manager, actions, now=now,
                boundary_hook=boundary_hook,
            )
        except MemoryRecallActionNeeded as exc:
            return _memory_action_needed(
                started, replay_run(root, run_id, now=now), actions, exc, decision
            )
        if projection["state"] != "active":
            break
    return _tick_document(started, projection, actions, decision)


def _tick_document(
    before: dict[str, object],
    after: dict[str, object],
    actions: list[dict[str, object]],
    decision: dict[str, object] | None,
) -> dict[str, object]:
    active = list(after["active_claims"])
    next_poll = 1 if active else 0
    return {
        "kind": CONDUCTOR_TICK_KIND,
        "schema_version": CONDUCTOR_SCHEMA_VERSION,
        "run_id": after["run_id"],
        "before_head": before["ledger_head"],
        "after_head": after["ledger_head"],
        "state": after["state"],
        "progressed": before["ledger_head"] != after["ledger_head"],
        "actions": actions,
        "eligible": decision["eligible"] if decision else [],
        "scheduled": decision["scheduled"] if decision else [],
        "blocked": decision["blocked"] if decision else [],
        "action_needed": decision.get("action_needed", []) if decision else [],
        "active_claims": len(active),
        "next_poll_seconds": next_poll,
        "terminal": after["state"] in TERMINAL_STATES,
    }


@contextmanager
def _conductor_lock(root: Path, run_id: str) -> Iterator[None]:
    """Serialize whole ticks, including provider/check side effects.

    Ledger appends are already individually locked, but an exact-token control
    surface also needs the observation and the first possible dispatch to be
    one critical section.  Otherwise two HTTP/MCP clients could both observe
    the same head before either has claimed work.
    """
    path = _run_dir(root, run_id) / ".conductor.lock"
    with path.open("a+", encoding="utf-8") as handle:
        os.chmod(path, 0o600)
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


def tick_run(
    root: Path,
    run_id: str,
    *,
    expect: str | None = None,
    driver_config: object | None = None,
    adapters: dict[str, object] | None = None,
    check_runner: CheckRunner | None = None,
    rail_runner: Callable[[list[str], Path], StepChild] | None = None,
    now: datetime | None = None,
    boundary_hook: BoundaryHook | None = None,
) -> dict[str, object]:
    """Run one serialized tick, optionally bound to an exact ledger head.

    Internal supervisors may omit ``expect``.  Every agent/HTTP/Workbench
    applying surface supplies the head from a fresh act preview; a mismatch is
    refused before reconciliation, dispatch, checks, rails, or ledger writes.
    """
    root = root.resolve()

    # A terminal control event may be appended while a synchronous provider
    # or check is still inside the serialized dispatch tick.  Cancellation
    # must be able to cross that boundary immediately: this cleanup-only tick
    # cannot schedule work because replay already says authority has ended.
    # Ledger compare-and-append still serializes the two reconcilers; the
    # dispatching tick is expected to lose that race and stop on its stale
    # head after the contained process has been interrupted.
    observed = replay_run(root, run_id, now=now)
    cleanup_states = {"cancelled", "revoked", "blocked", "awaiting-certification"}
    if observed["state"] in cleanup_states and observed["active_claims"]:
        if expect is not None and str(expect or "") != observed["ledger_head"]:
            raise DwError(
                "stale run tick token refused; no work started and no event was appended"
            )
        return _tick_run_once(
            root,
            run_id,
            driver_config=driver_config,
            adapters=adapters,
            check_runner=check_runner,
            rail_runner=rail_runner,
            now=now,
            boundary_hook=boundary_hook,
        )
    with _conductor_lock(root, run_id):
        if expect is not None:
            observed = replay_run(root, run_id, now=now)
            if str(expect or "") != observed["ledger_head"]:
                raise DwError(
                    "stale run tick token refused; no work started and no event was appended"
                )
        return _tick_run_once(
            root,
            run_id,
            driver_config=driver_config,
            adapters=adapters,
            check_runner=check_runner,
            rail_runner=rail_runner,
            now=now,
            boundary_hook=boundary_hook,
        )


def supervise_run(
    root: Path,
    run_id: str,
    *,
    max_ticks: int = 100,
    interval_seconds: float = 1.0,
    **tick_options: object,
) -> dict[str, object]:
    """Boundedly repeat ``tick_run``; stop at terminal/wait/no-progress states."""
    if isinstance(max_ticks, bool) or not 1 <= max_ticks <= 10_000:
        raise DwError("max_ticks must be from 1 through 10000")
    if not 0 <= interval_seconds <= 30:
        raise DwError("interval_seconds must be from 0 through 30")
    first_head: str | None = None
    last: dict[str, object] | None = None
    progressed = 0
    for number in range(1, max_ticks + 1):
        last = tick_run(root, run_id, **tick_options)
        if first_head is None:
            first_head = str(last["before_head"])
        progressed += int(bool(last["progressed"]))
        if last["terminal"] or last["state"] in {"paused", "awaiting-approval"}:
            break
        if not last["progressed"] and int(last["active_claims"]) == 0:
            break
        if interval_seconds:
            time.sleep(interval_seconds)
    assert last is not None
    return {
        "kind": CONDUCTOR_SUPERVISION_KIND,
        "schema_version": CONDUCTOR_SCHEMA_VERSION,
        "run_id": run_id,
        "ticks": number,
        "progressed_ticks": progressed,
        "before_head": first_head,
        "after_head": last["after_head"],
        "state": last["state"],
        "terminal": last["terminal"],
        "last_tick": last,
    }
