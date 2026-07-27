"""Deterministic, restart-safe conductor for finite Phase-26 programs.

``tick_program`` is the only scheduling primitive.  It composes the immutable
program grant and hash-chained claim ledger with the pure program/workflow/
organization/verdict cores.  External work always has two durable boundaries:
an authority claim and a ``claim_dispatched`` event.  Mutable driver session
records can help reconcile an operation, but deleting one can never make a
previously dispatched operation eligible to start again.

This module deliberately contains no Git integration or roadmap mutation
rails.  It conducts workflow and governed judgment work; WLA-26-10 consumes
the resulting certified receipts under separately reserved rail claims.
"""

from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import time
from typing import Callable, Iterator

from .knowledge_packet import (
    build_hint_free_knowledge_packet,
    build_repository_knowledge_packet,
)
from .model import DwError
from .orchestration import canonical_json
from .orchestration_driver import (
    ClaudeCodeExecDriver,
    CodexExecDriver,
    DRIVER_RECEIPT_KIND,
    DRIVER_SCHEMA_VERSION,
    PiExecDriver,
    WORK_PACKET_KIND,
    _git_diff_artifact,
    _safe_child,
    _schema_check,
    _workspace_base,
    driver_capability,
    load_driver_config,
    normalize_driver_usage,
    validate_work_packet,
)
from .program_run import (
    _format_time,
    _events,
    _load_documents,
    _program_signal_branch,
    _run_dir,
    _sha,
    _time,
    apply_program_claim,
    apply_program_completion,
    build_program_claim_preview,
    build_program_completion_preview,
    complete_program_scope,
    derive_child_grant,
    program_freshness_issues,
    record_program_obligation,
    record_program_dispatch,
    replay_program,
    validate_child_grant,
)
from .program_deliberation import (
    ARCHITECT_VERDICT_KIND,
    COUNCIL_DECISION_KIND,
    COUNCIL_VERDICT_KIND,
    META_VERDICT_KIND,
    claim_next_deliberation,
    compile_deliberation_plan,
    record_deliberation_submission,
    replay_deliberation,
    start_deliberation,
    validate_council_decision,
)
from .program_verdict import (
    GREEN_RESULTS,
    build_mechanical_fact,
    build_verdict_assignment,
    compile_rubric,
    evaluate_quality_gate,
    issue_agent_verdict,
    validate_mechanical_fact,
    validate_verdict_document,
)
from .program_workflow import find_workflow_path, load_workflow
from .programs import build_program_plan, compile_program_path, find_program_path
from .signals import (
    build_signals_inventory,
    latest_nudge_fact,
    receptivity as signal_receptivity,
    replay_channel as replay_signal_channel,
)


PROGRAM_CONDUCTOR_SCHEMA_VERSION = 1
PROGRAM_TICK_KIND = "delivery-workbench-program-tick"
PROGRAM_SUPERVISION_KIND = "delivery-workbench-program-supervision"
PROGRAM_FRONTIER_KIND = "delivery-workbench-program-frontier"
PROGRAM_RECEIPT_KIND = "delivery-workbench-program-conductor-receipt"
PROGRAM_ARTIFACT_KIND = "delivery-workbench-program-artifact-receipt"
PROGRAM_DRIVER_OPERATION_KIND = "delivery-workbench-program-driver-operation"
PROGRAM_REQUEST_RESULT_KIND = "delivery-workbench-program-request-result"

TERMINAL_AUTHORITY_STATES = {
    "advisory", "complete", "expired", "exhausted", "revoked", "cancelled",
}
TERMINAL_DRIVER_STATES = {"succeeded", "failed", "cancelled", "lost", "refused"}
RECONCILIATION_STOPS = {
    "external-operation-uncertain", "driver-session-corrupt",
    "driver-receipt-missing", "artifact-invalid",
}
MAX_PACKET_BYTES = 1_500_000
MAX_RECEIPT_BYTES = 2_000_000
MAX_ARTIFACT_BYTES = 100_000_000
_SAFE_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:@/-]{0,511}$")
_HASH_RE = re.compile(r"^sha256:[0-9a-f]{64}$")

BoundaryHook = Callable[[str, dict[str, object]], None]


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise DwError(message)


def _safe(value: object, label: str) -> str:
    _require(isinstance(value, str) and bool(_SAFE_ID_RE.fullmatch(value)), f"{label} is unsafe")
    return value


def _hash(value: object, label: str) -> str:
    _require(isinstance(value, str) and bool(_HASH_RE.fullmatch(value)), f"{label} must be a sha256 hash")
    return value


def _bounded_text(value: object, label: str, maximum: int = 20_000) -> str:
    _require(
        isinstance(value, str)
        and 0 < len(value.encode("utf-8")) <= maximum
        and "\x00" not in value,
        f"{label} must be non-empty and at most {maximum} bytes",
    )
    return value


def _boundary(
    hook: BoundaryHook | None,
    name: str,
    detail: dict[str, object],
) -> None:
    if hook is not None:
        hook(name, dict(detail))


def _write_json_atomic(path: Path, value: object, *, immutable: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    data = (json.dumps(value, indent=2, sort_keys=True) + "\n").encode("utf-8")
    if immutable and path.exists():
        _require(path.read_bytes() == data, f"immutable program document conflicts: {path.name}")
        return
    fd, temporary = tempfile.mkstemp(prefix="." + path.name + ".", dir=str(path.parent))
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(temporary, 0o400 if immutable else 0o600)
        if immutable and path.exists():
            _require(path.read_bytes() == data, f"immutable program document conflicts: {path.name}")
            return
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def _load_json(path: Path, label: str) -> dict[str, object]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise DwError(f"cannot read {label}: {exc}") from exc
    _require(isinstance(value, dict), f"{label} must be an object")
    return value


def _conductor_dir(root: Path, run_id: str) -> Path:
    path = _run_dir(root.resolve(), run_id) / "conductor"
    if path.is_symlink():
        raise DwError("refusing symlinked program conductor store")
    path.mkdir(parents=True, exist_ok=True, mode=0o700)
    return path


@contextmanager
def _file_lock(path: Path) -> Iterator[None]:
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    with path.open("a+b") as handle:
        os.chmod(path, 0o600)
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


@contextmanager
def _conductor_lock(root: Path, run_id: str) -> Iterator[None]:
    with _file_lock(_run_dir(root.resolve(), run_id) / ".program-conductor.lock"):
        yield


def _operation_id(run_id: str, claim_id: str) -> str:
    return "operation-" + hashlib.sha256(
        f"{run_id}|{claim_id}".encode("utf-8")
    ).hexdigest()[:24]


def _action_id(address: str, kind: str, attempt: int) -> str:
    return "act-" + hashlib.sha256(
        f"{address}|{kind}|{attempt}".encode("utf-8")
    ).hexdigest()[:24]


def _driver_node_id(address: str, attempt: int) -> str:
    return "program-" + hashlib.sha256(
        f"{address}|{attempt}".encode("utf-8")
    ).hexdigest()[:24]


def _receipt_path(root: Path, run_id: str, receipt_hash: str) -> Path:
    _hash(receipt_hash, "program receipt hash")
    return _conductor_dir(root, run_id) / "receipts" / f"{receipt_hash.split(':', 1)[1]}.json"


def _store_receipt(
    root: Path,
    run_id: str,
    payload: dict[str, object],
) -> dict[str, object]:
    unsigned = {
        "kind": PROGRAM_RECEIPT_KIND,
        "schema_version": PROGRAM_CONDUCTOR_SCHEMA_VERSION,
        "run_id": run_id,
        **payload,
    }
    _require(
        len(canonical_json(unsigned).encode("utf-8")) <= MAX_RECEIPT_BYTES,
        "program conductor receipt exceeds its byte ceiling",
    )
    receipt = {**unsigned, "receipt_hash": _sha(unsigned)}
    _write_json_atomic(
        _receipt_path(root, run_id, str(receipt["receipt_hash"])),
        receipt,
        immutable=True,
    )
    return receipt


def _load_receipt(root: Path, run_id: str, receipt_hash: str) -> dict[str, object]:
    receipt = _load_json(_receipt_path(root, run_id, receipt_hash), "program conductor receipt")
    _require(receipt.get("kind") == PROGRAM_RECEIPT_KIND, "program conductor receipt kind is invalid")
    _require(receipt.get("schema_version") == PROGRAM_CONDUCTOR_SCHEMA_VERSION, "program conductor receipt schema is invalid")
    _require(receipt.get("run_id") == run_id, "program conductor receipt run id differs")
    stored = receipt.get("receipt_hash")
    _require(stored == receipt_hash, "program conductor receipt filename hash differs")
    unsigned = {key: value for key, value in receipt.items() if key != "receipt_hash"}
    _require(_sha(unsigned) == stored, "program conductor receipt hash is invalid")
    return receipt


def _artifact_store(root: Path, run_id: str) -> Path:
    path = _conductor_dir(root, run_id) / "artifacts"
    path.mkdir(parents=True, exist_ok=True, mode=0o700)
    return path


def _store_artifact(
    root: Path,
    run_id: str,
    *,
    action_id: str,
    address: str,
    attempt: int,
    name: str,
    kind: str,
    data: bytes,
    checks: list[str],
) -> dict[str, object]:
    _require(len(data) <= MAX_ARTIFACT_BYTES, "program artifact exceeds the absolute byte ceiling")
    digest = "sha256:" + hashlib.sha256(data).hexdigest()
    artifact_id = "artifact-" + hashlib.sha256(
        f"{action_id}|{name}|{digest}".encode("utf-8")
    ).hexdigest()[:24]
    directory = _artifact_store(root, run_id) / artifact_id
    metadata = {
        "kind": PROGRAM_ARTIFACT_KIND,
        "schema_version": PROGRAM_CONDUCTOR_SCHEMA_VERSION,
        "run_id": run_id,
        "artifact_id": artifact_id,
        "action_id": action_id,
        "address": address,
        "attempt": attempt,
        "name": name,
        "artifact_kind": kind,
        "bytes": len(data),
        "sha256": digest,
        "ref": f"conductor/artifacts/{artifact_id}/content",
        "checks": sorted(set(checks)),
        "valid": True,
    }
    if directory.exists():
        prior = _load_json(directory / "metadata.json", "program artifact metadata")
        _require(prior == metadata, "program artifact id conflicts with different metadata")
        _require((directory / "content").read_bytes() == data, "program artifact bytes conflict")
        return prior
    temporary = Path(tempfile.mkdtemp(prefix=".artifact.", dir=str(directory.parent)))
    try:
        (temporary / "content").write_bytes(data)
        os.chmod(temporary / "content", 0o400)
        _write_json_atomic(temporary / "metadata.json", metadata, immutable=True)
        os.replace(temporary, directory)
    finally:
        if temporary.exists():
            shutil.rmtree(temporary, ignore_errors=True)
    return metadata


def _artifact_content(root: Path, run_id: str, artifact: dict[str, object]) -> bytes:
    artifact_id = _safe(artifact.get("artifact_id"), "artifact id")
    directory = _artifact_store(root, run_id) / artifact_id
    metadata = _load_json(directory / "metadata.json", "program artifact metadata")
    _require(metadata == artifact, "program artifact metadata changed")
    data = (directory / "content").read_bytes()
    digest = "sha256:" + hashlib.sha256(data).hexdigest()
    _require(len(data) == artifact["bytes"] and digest == artifact["sha256"], "program artifact content changed")
    return data


class ProgramFixtureDriver:
    """Persisted fixture adapter with an explicit reconcile/not-found seam."""

    adapter = "fixture"

    def __init__(self, responses: dict[str, dict[str, object]] | None = None) -> None:
        self.responses = responses or {}
        self.starts = 0

    def _response(self, packet: dict[str, object]) -> dict[str, object]:
        prompt: dict[str, object] = {}
        try:
            candidate = json.loads(str(packet.get("prompt") or "{}"))
            if isinstance(candidate, dict):
                prompt = candidate
        except json.JSONDecodeError:
            pass
        for key in (
            str(prompt.get("address") or ""),
            str(prompt.get("action_kind") or ""),
            str(packet.get("role") or ""),
            str(packet.get("node_id") or ""),
            "*",
        ):
            if key and key in self.responses:
                return dict(self.responses[key])
        return {}

    @staticmethod
    def _default_judgment(prompt: dict[str, object]) -> dict[str, object]:
        criteria: list[dict[str, object]] = []
        evidence_items = [
            item for item in prompt.get("evidence", []) if isinstance(item, dict)
        ]
        facts = {
            str(item.get("id")): item
            for item in prompt.get("mechanical_facts", [])
            if isinstance(item, dict)
        }
        rubric = prompt.get("rubric", {})
        rubric_criteria = rubric.get("criteria", []) if isinstance(rubric, dict) else []
        for raw in rubric_criteria:
            if not isinstance(raw, dict):
                continue
            required = list(raw.get("required_evidence_kinds", []))
            selected: list[dict[str, object]] = []
            for kind in required:
                match = next(
                    (item for item in evidence_items if item.get("kind") == kind),
                    None,
                )
                if match is not None:
                    selected.append({
                        "id": f"evidence-{len(selected) + 1}",
                        "kind": match["kind"],
                        "hash": match["hash"],
                        "ref": match["ref"],
                    })
            citations = []
            minimum = int(raw.get("min_citations", 0))
            for index in range(minimum):
                if not selected:
                    break
                evidence = selected[min(index, len(selected) - 1)]
                citations.append({
                    "id": f"citation-{index + 1}",
                    "evidence_id": evidence["id"],
                    "locator": f"{evidence['ref']}#fixture",
                    "hash": evidence["hash"],
                })
            evaluation = raw.get("evaluation", {})
            mechanical = evaluation.get("kind") == "mechanical-fact" if isinstance(evaluation, dict) else False
            fact = facts.get(str(evaluation.get("fact"))) if mechanical else None
            criteria.append({
                "id": raw["id"],
                "result": str(fact.get("result", "pass")) if isinstance(fact, dict) else "pass",
                "evidence": selected,
                "citations": citations,
                "rationale": None if mechanical else "Fixture judgment over the exact declared evidence.",
                "mechanical_fact_hash": fact.get("fact_hash") if isinstance(fact, dict) else None,
            })
        return {"criteria": criteria}

    @staticmethod
    def _default_deliberation(
        prompt: dict[str, object],
        response: dict[str, object],
    ) -> dict[str, object]:
        stage = str(prompt.get("deliberation_stage"))
        citation_refs = [
            str(item) for item in prompt.get("citation_refs", [])
            if isinstance(item, str)
        ]
        vote: str | None = None
        result: str | None = None
        rationale: str | None = None
        obligations: object = None
        if stage == "rebuttal":
            vote = str(response.get("vote", "advance"))
        elif stage == "judgment":
            result = str(response.get("decision_result", "advance"))
            rationale = "Fixture council judgment over the exact declared evidence."
            obligations = response.get("obligations", [])
        elif stage == "meta-audit":
            result = str(response.get("meta_result", "uphold"))
            rationale = "Fixture meta-audit over the exact council receipt lineage."
        elif stage == "architect-review":
            result = str(response.get("architect_result", "approve"))
            rationale = "Fixture architecture review over the exact boundary evidence."
        return {
            "citations": citation_refs[:1],
            "vote": vote,
            "result": result,
            "rationale": rationale,
            "obligations": obligations,
        }

    def start(
        self,
        packet: dict[str, object],
        profile: dict[str, object],
        staging: Path,
    ) -> dict[str, object]:
        external = staging / "external-operation.json"
        if external.is_file():
            return _load_json(external, "fixture external operation")
        self.starts += 1
        response = self._response(packet)
        prompt: dict[str, object] = {}
        try:
            candidate = json.loads(str(packet.get("prompt") or "{}"))
            if isinstance(candidate, dict):
                prompt = candidate
        except json.JSONDecodeError:
            pass
        output_dir = staging / "outputs"
        output_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
        supplied_outputs = response.get("outputs", {})
        if not isinstance(supplied_outputs, dict):
            supplied_outputs = {}
        for spec in packet.get("outputs", []):
            if not isinstance(spec, dict):
                continue
            name = str(spec["name"])
            fmt = str(spec["format"])
            if fmt == "git-diff":
                if packet["workspace"]["mode"] != "isolated-worktree":  # type: ignore[index]
                    continue
                files = response.get("workspace_files")
                if not isinstance(files, dict):
                    files = {
                        f".delivery-workbench-fixture-{packet['node_id']}.txt":
                        "deterministic program fixture output\n"
                    }
                workspace = Path(str(packet["workspace"]["path"]))  # type: ignore[index]
                for relative, content in files.items():
                    target = (workspace / str(relative)).resolve()
                    _require(target != workspace and workspace.resolve() in target.parents, "fixture workspace output escaped")
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_text(str(content), encoding="utf-8")
                continue
            content = supplied_outputs.get(name)
            if content is None and prompt.get("deliberation_stage") in {
                "proposal", "critique", "rebuttal", "judgment",
                "meta-audit", "architect-review",
            }:
                content = self._default_deliberation(prompt, response)
            elif content is None and prompt.get("action_kind") in {"verdict", "story-verification", "architect-verdict", "meta-verdict"}:
                content = self._default_judgment(prompt)
                forced = response.get("judgment_result")
                if forced in {"pass", "fail", "abstain", "inconclusive"}:
                    for criterion in content["criteria"]:
                        if criterion.get("mechanical_fact_hash") is None:
                            criterion["result"] = forced
            elif content is None and fmt == "json":
                content = {"fixture": True, "address": prompt.get("address")}
            elif content is None and fmt == "markdown":
                content = "# Result\n\nDeterministic fixture result.\n"
            elif content is None:
                content = "deterministic fixture result\n"
            text = content if isinstance(content, str) else json.dumps(content, indent=2, sort_keys=True) + "\n"
            (output_dir / name).write_text(str(text), encoding="utf-8")
        final_state = str(response.get("state", "succeeded"))
        if final_state not in {"succeeded", "failed", "cancelled", "lost"}:
            final_state = "failed"
        polls = response.get("polls", 0)
        if isinstance(polls, bool) or not isinstance(polls, int) or polls < 0:
            polls = 0
        result = {
            "state": final_state if polls == 0 else "running",
            "exit_code": (0 if final_state == "succeeded" else 1) if polls == 0 else None,
            "reason": "completed" if final_state == "succeeded" and polls == 0 else (
                "running" if polls else final_state
            ),
            "polls_remaining": polls,
            "final_state": final_state,
            "stdout_bytes": 0,
            "stderr_bytes": 0,
            "activity_plan": list(response.get("activities", [])) if isinstance(response.get("activities", []), list) else [],
            "usage": response.get("usage"),
        }
        _write_json_atomic(external, result, immutable=True)
        return result

    def reconcile(
        self,
        _packet: dict[str, object],
        _profile: dict[str, object],
        staging: Path,
    ) -> dict[str, object]:
        external = staging / "external-operation.json"
        if not external.is_file():
            return {"status": "not-found", "result": None}
        return {
            "status": "found",
            "result": _load_json(external, "fixture external operation"),
        }

    def interrupt(self, _session: dict[str, object]) -> bool:
        return True


class ProgramDriverManager:
    """Program-local driver journal with durable-dispatch reconciliation."""

    def __init__(
        self,
        root: Path,
        run_id: str,
        config: object | None,
        adapters: dict[str, object] | None = None,
    ) -> None:
        self.root = root.resolve()
        self.run_id = run_id
        self.config = load_driver_config(self.root, config)
        self.adapters = adapters or {
            "fixture": ProgramFixtureDriver(),
            "codex-exec": CodexExecDriver(),
            "claude-exec": ClaudeCodeExecDriver(),
            "pi-exec": PiExecDriver(),
        }

    @property
    def directory(self) -> Path:
        path = _conductor_dir(self.root, self.run_id) / "driver-sessions"
        path.mkdir(parents=True, exist_ok=True, mode=0o700)
        return path

    def _path(self, operation_id: str) -> Path:
        _safe(operation_id, "driver operation id")
        return self.directory / f"{operation_id}.json"

    def _record(self, operation_id: str) -> dict[str, object] | None:
        path = self._path(operation_id)
        return _load_json(path, "program driver operation") if path.is_file() else None

    def _write(self, record: dict[str, object]) -> None:
        _write_json_atomic(self._path(str(record["operation_id"])), record)

    def prepare(
        self,
        claim: dict[str, object],
        packet: dict[str, object],
        *,
        profile: str,
        child_grant_hash: str,
    ) -> dict[str, object]:
        packet = validate_work_packet(packet)
        operation_id = _operation_id(self.run_id, str(claim["claim_id"]))
        with _file_lock(self.directory / ".lock"):
            prior = self._record(operation_id)
            if prior is not None:
                _require(prior["packet_hash"] == packet["packet_hash"], "driver operation packet changed")
                _require(prior["claim_id"] == claim["claim_id"], "driver operation claim changed")
                return prior
            capability = driver_capability(self.config, profile)
            session_id = "session-" + hashlib.sha256(
                f"{operation_id}|{packet['packet_hash']}".encode("utf-8")
            ).hexdigest()[:24]
            staging = self.directory / session_id
            staging.mkdir(parents=True, exist_ok=False, mode=0o700)
            packet_path = staging / "packet.json"
            _write_json_atomic(packet_path, packet, immutable=True)
            record = {
                "kind": PROGRAM_DRIVER_OPERATION_KIND,
                "schema_version": PROGRAM_CONDUCTOR_SCHEMA_VERSION,
                "run_id": self.run_id,
                "operation_id": operation_id,
                "session_id": session_id,
                "claim_id": claim["claim_id"],
                "request_hash": claim["request_hash"],
                "idempotency_key": claim["idempotency_key"],
                "packet_hash": packet["packet_hash"],
                "packet_path": str(packet_path),
                "staging": str(staging),
                "profile": profile,
                "adapter": capability["adapter"],
                "adapter_version": capability["adapter_version"],
                "child_grant_hash": child_grant_hash,
                "status": "prepared",
                "result": None,
                "receipt": None,
            }
            self._write(record)
            return record

    @staticmethod
    def _driver_receipt(
        record: dict[str, object],
        result: dict[str, object],
        now: datetime,
    ) -> dict[str, object]:
        state = str(result["state"])
        return {
            "kind": DRIVER_RECEIPT_KIND,
            "schema_version": DRIVER_SCHEMA_VERSION,
            "run_id": record["run_id"],
            "node_id": json.loads(Path(str(record["packet_path"])).read_text())["node_id"],
            "attempt": json.loads(Path(str(record["packet_path"])).read_text())["attempt"],
            "claim_id": record["claim_id"],
            "profile": record["profile"],
            "adapter": record["adapter"],
            "session_id": record["session_id"],
            "idempotency_key": record["idempotency_key"],
            "packet_hash": record["packet_hash"],
            "state": state,
            "started": True,
            "exit_code": result["exit_code"],
            "reason": result["reason"],
            "started_at": _format_time(now),
            "updated_at": _format_time(now),
            "stdout_bytes": int(result["stdout_bytes"]),
            "stderr_bytes": int(result["stderr_bytes"]),
            "activity": "active" if state == "running" else ("unknown" if state == "lost" else "exited"),
            "usage": normalize_driver_usage(result.get("usage")),
        }

    def _accept_result(
        self,
        record: dict[str, object],
        result: object,
        now: datetime,
    ) -> dict[str, object]:
        _require(isinstance(result, dict), "driver adapter result must be an object")
        accepted = dict(result)
        accepted["usage"] = normalize_driver_usage(accepted.get("usage"))
        expected = {
            "state", "exit_code", "reason", "polls_remaining", "final_state",
            "stdout_bytes", "stderr_bytes", "activity_plan", "usage",
        }
        _require(set(accepted) == expected, "driver adapter result has non-exact keys")
        _require(result["state"] in TERMINAL_DRIVER_STATES | {"running"}, "driver adapter state is unsupported")
        _require(result["final_state"] in TERMINAL_DRIVER_STATES - {"refused"}, "driver final state is unsupported")
        _require(
            isinstance(result["polls_remaining"], int)
            and not isinstance(result["polls_remaining"], bool)
            and int(result["polls_remaining"]) >= 0,
            "driver poll count is invalid",
        )
        receipt = self._driver_receipt(record, accepted, now)
        record["status"] = "running" if accepted["state"] == "running" else "terminal"
        record["result"] = accepted
        record["receipt"] = receipt
        self._write(record)
        return record

    def start(
        self,
        operation_id: str,
        *,
        now: datetime,
        boundary_hook: BoundaryHook | None = None,
    ) -> dict[str, object]:
        with _file_lock(self.directory / ".lock"):
            record = self._record(operation_id)
            _require(record is not None, "driver operation was not prepared")
            if record["status"] != "prepared":
                return record
            packet = validate_work_packet(_load_json(Path(str(record["packet_path"])), "program work packet"))
            profile = self.config["profiles"].get(record["profile"])  # type: ignore[union-attr]
            _require(isinstance(profile, dict), "driver profile disappeared")
            adapter = self.adapters.get(str(record["adapter"]))
            _require(adapter is not None and hasattr(adapter, "start"), "driver adapter is unavailable")
            result = adapter.start(packet, profile, Path(str(record["staging"])))  # type: ignore[attr-defined]
            _boundary(boundary_hook, "after-dispatch", {
                "claim_id": record["claim_id"],
                "operation_id": operation_id,
            })
            return self._accept_result(record, result, now)

    def reconcile(
        self,
        claim: dict[str, object],
        *,
        now: datetime,
        boundary_hook: BoundaryHook | None = None,
    ) -> dict[str, object]:
        dispatch = claim.get("dispatch")
        _require(isinstance(dispatch, dict), "active driver claim has no durable dispatch")
        operation_id = str(dispatch["operation_id"])
        with _file_lock(self.directory / ".lock"):
            record = self._record(operation_id)
            if record is None:
                return {
                    "status": "uncertain",
                    "reason": "driver-session-missing-after-dispatch",
                    "operation_id": operation_id,
                }
            _require(record["claim_id"] == claim["claim_id"], "driver session claim binding changed")
            _require(record["packet_hash"] == dispatch["packet_hash"], "driver session packet binding changed")
            packet = validate_work_packet(_load_json(Path(str(record["packet_path"])), "program work packet"))
            profile = self.config["profiles"].get(record["profile"])  # type: ignore[union-attr]
            _require(isinstance(profile, dict), "driver profile disappeared")
            adapter = self.adapters.get(str(record["adapter"]))
            _require(adapter is not None, "driver adapter disappeared")
            if record["status"] == "prepared":
                reconcile = getattr(adapter, "reconcile", None)
                if reconcile is None:
                    return {
                        "status": "uncertain",
                        "reason": "adapter-cannot-reconcile-start",
                        "operation_id": operation_id,
                    }
                observed = reconcile(packet, profile, Path(str(record["staging"])))
                _require(
                    isinstance(observed, dict)
                    and set(observed) == {"status", "result"}
                    and observed["status"] in {"found", "not-found", "uncertain"},
                    "driver reconcile result is invalid",
                )
                if observed["status"] == "uncertain":
                    return {
                        "status": "uncertain",
                        "reason": "adapter-reported-uncertainty",
                        "operation_id": operation_id,
                    }
                if observed["status"] == "found":
                    record = self._accept_result(record, observed["result"], now)
                else:
                    result = adapter.start(packet, profile, Path(str(record["staging"])))
                    _boundary(boundary_hook, "after-dispatch", {
                        "claim_id": record["claim_id"],
                        "operation_id": operation_id,
                        "reconciled_not_found": True,
                    })
                    record = self._accept_result(record, result, now)
            if record["status"] == "running":
                result = dict(record["result"])
                remaining = max(0, int(result["polls_remaining"]) - 1)
                result["polls_remaining"] = remaining
                if remaining == 0:
                    state = str(result["final_state"])
                    result["state"] = state
                    result["exit_code"] = 0 if state == "succeeded" else (None if state in {"lost", "cancelled"} else 1)
                    result["reason"] = "completed" if state == "succeeded" else state
                record = self._accept_result(record, result, now)
            return {
                "status": str(record["status"]),
                "reason": str(record.get("receipt", {}).get("reason", "running")),
                "operation_id": operation_id,
                "record": record,
            }


def _execution(capability: dict[str, object]) -> dict[str, object]:
    return {
        "harness": capability["harness"],
        "adapter": capability["adapter"],
        "adapter_version": capability["adapter_version"],
        "router": capability["router"],
        "provider": capability["provider"],
        "model_vendor": capability["model_vendor"],
        "model_family": capability["model_family"],
        "model": capability["model"],
        "model_revision": capability["model_revision"],
        "model_binding": capability["model_binding"],
        "auth_domain_fingerprint": capability["auth_domain_fingerprint"],
        "capability_fingerprint": capability["capability_fingerprint"],
    }


def _role_document(
    assignment: dict[str, object],
    *,
    role_id: str | None = None,
    duty: str | None = None,
) -> dict[str, object]:
    matches = [
        item for item in assignment.get("roles", [])
        if isinstance(item, dict)
        and (role_id is None or item.get("role") == role_id)
        and (duty is None or item.get("duty") == duty)
        and item.get("members")
    ]
    _require(len(matches) == 1, f"required program role did not resolve uniquely: {role_id or duty}")
    return matches[0]


def _role_member(role: dict[str, object]) -> dict[str, object]:
    members = role.get("members")
    _require(isinstance(members, list) and len(members) == 1, "program conductor requires one exact role member")
    member = members[0]
    _require(isinstance(member, dict), "program role member is invalid")
    return member


def _workflow_address(plan: dict[str, object]) -> str:
    assignment = plan.get("assignment")
    _require(isinstance(assignment, dict), "program plan has no workflow assignment")
    return _safe(assignment.get("workflow_address"), "workflow address")


def _lineage_address(
    workflow_address: str,
    instance_slug: str,
    expanded_address: str,
    *,
    round_number: int = 1,
) -> str:
    relative = expanded_address
    prefix = instance_slug + "/"
    if relative.startswith(prefix):
        relative = relative[len(prefix):]
    relative = relative.replace("{round}", str(round_number))
    pieces = [piece for piece in relative.split("/") if piece]
    result = workflow_address
    index = 0
    while index < len(pieces):
        remaining = len(pieces) - index
        if remaining >= 3 and pieces[index + 1] == "round":
            result += (
                f"/loop/{pieces[index]}/round/{pieces[index + 2]}"
            )
            index += 3
            if index < len(pieces):
                result += f"/subflow/{pieces[index]}"
                index += 1
            continue
        if remaining >= 3:
            # Compiled nested subflow paths alternate parent-node and
            # child-workflow before ending in the executable child node.
            result += f"/subflow/{pieces[index]}:{pieces[index + 1]}"
            index += 2
            continue
        result += "/node/" + "/".join(pieces[index:])
        break
    return result


def _node_policy(
    root: Path,
    expanded: dict[str, object],
) -> dict[str, object]:
    workflow = str(expanded["workflow"])
    raw = load_workflow(find_workflow_path(root, workflow))
    matches = [
        node for node in raw.get("nodes", [])
        if isinstance(node, dict) and node.get("id") == expanded.get("node")
    ]
    _require(len(matches) == 1, f"compiled workflow node disappeared: {workflow}/{expanded.get('node')}")
    node = dict(matches[0])
    node.setdefault("activation", expanded.get("activation", "success"))
    node.setdefault("needs", [])
    node.setdefault("resource_groups", [])
    node.setdefault("inputs", {})
    node.setdefault("outputs", [])
    return node


def _prepare_workspace(
    root: Path,
    run_id: str,
    action_id: str,
    attempt: int,
    mode: str,
    groups: list[str],
    config: dict[str, object],
    expected_head: str,
) -> dict[str, object]:
    if mode == "read-only":
        return {
            "mode": "read-only",
            "path": str(root.resolve()),
            "identity": _sha({"root": str(root.resolve()), "head": expected_head}),
            "base_head": expected_head,
            "resource_groups": groups,
            "integration": "not-applicable",
        }
    _require(mode == "isolated-worktree", f"unsupported program workspace mode: {mode}")
    base = _workspace_base(root, config)
    selector = f"{action_id}-{attempt}"
    path = _safe_child(base, run_id, selector)
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    if path.exists():
        _require((path / ".git").is_file(), "existing program workspace is not a Git worktree")
        observed = subprocess.run(
            ["git", "-C", str(path), "rev-parse", "HEAD"],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        _require(observed.returncode == 0 and observed.stdout.strip() == expected_head, "program workspace base HEAD changed")
    else:
        result = subprocess.run(
            ["git", "-C", str(root), "worktree", "add", "--detach", str(path), expected_head],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        _require(result.returncode == 0, "cannot create isolated program worktree: " + result.stderr.strip()[:500])
    return {
        "mode": mode,
        "path": str(path),
        "identity": _sha({"run": run_id, "action": action_id, "attempt": attempt, "path": str(path)}),
        "base_head": expected_head,
        "resource_groups": groups,
        "integration": "review-required",
    }


def _packet_outputs(outputs: list[dict[str, object]]) -> list[dict[str, object]]:
    result: list[dict[str, object]] = []
    for output in outputs:
        kind = str(output["kind"])
        fmt = "json" if kind in {"verdict", "decision", "mechanical-fact"} else kind
        result.append({
            "name": str(output["id"]),
            "format": fmt,
            "max_bytes": int(output["max_bytes"]),
            "schema": output.get("schema"),
            "required_sections": [],
            "citations": "optional",
            "allowed_paths": ["*", "**/*"],
            "artifact_kind": kind,
        })
    return result


def _build_packet(
    root: Path,
    run_id: str,
    claim: dict[str, object],
    action: dict[str, object],
    child_grant: dict[str, object],
    role: dict[str, object],
    member: dict[str, object],
    config: dict[str, object],
    projection: dict[str, object],
    selection: dict[str, object],
    *,
    now: datetime,
) -> dict[str, object]:
    validate_child_grant(child_grant)
    profile = str(member["profile"])
    capability = driver_capability(config, profile)
    packet_policy = role.get("packet_policy", {})
    _require(isinstance(packet_policy, dict), "program role packet policy is absent")
    workspace_mode = str(action.get("workspace") or packet_policy.get("workspace") or "read-only")
    _require(workspace_mode in capability["workspace_modes"], "driver profile cannot provide the assigned workspace")
    driver_capabilities = list(packet_policy.get("driver_capabilities", []))
    _require(set(driver_capabilities) <= set(capability["capabilities"]), "driver profile lost an assigned capability")
    groups = sorted(set(str(item) for item in role.get("resource_groups", [])))
    workspace = _prepare_workspace(
        root,
        run_id,
        str(action["action_id"]),
        int(action["attempt"]),
        workspace_mode,
        groups,
        config,
        str(projection["expected_repository"]["head"]),
    )
    timeout = min(int(action.get("timeout_seconds", 900)), int(capability["timeout_ceiling"]))
    deadline = min(
        now + timedelta(seconds=timeout),
        _time(str(projection["expires_at"]), "program expiry"),
    )
    child_data = canonical_json(child_grant)
    context = [{
        "selector": "@child-grant",
        "path": "@child-grant",
        "bytes": len(child_data.encode("utf-8")),
        "included_bytes": len(child_data.encode("utf-8")),
        "sha256": _sha(child_grant),
        "truncated": False,
        "content": child_data,
    }]
    prompt_document = dict(action["prompt_document"])
    prompt_document.update({
        "address": action["address"],
        "action_kind": action["kind"],
        "child_grant_hash": child_grant["grant_hash"],
    })
    grounding = selection.get("grounding")
    if isinstance(grounding, dict):
        story_path = grounding.get("story")
        _require(bool(story_path), "grounded program selection has no story path")
        knowledge = build_repository_knowledge_packet(
            root, root / str(story_path), grounding=grounding
        )
    else:
        knowledge = build_hint_free_knowledge_packet(
            root, str(selection.get("story") or action.get("story") or "")
        )
    unsigned = {
        "kind": WORK_PACKET_KIND,
        "schema_version": DRIVER_SCHEMA_VERSION,
        "run_id": run_id,
        "node_id": _driver_node_id(str(action["address"]), int(action["attempt"])),
        "attempt": int(action["attempt"]),
        "claim_id": claim["claim_id"],
        "idempotency_key": claim["idempotency_key"],
        "role": role["role"],
        "profile": profile,
        "prompt": canonical_json(prompt_document),
        "capabilities": driver_capabilities,
        "workspace": workspace,
        "resource_groups": groups,
        "context": {"documents": context, "truncated": False},
        "inputs": list(action.get("inputs", [])),
        "outputs": _packet_outputs(list(action.get("outputs", []))),
        "timeout_seconds": timeout,
        "deadline": _format_time(deadline),
        "max_stream_bytes": int(capability["max_stream_bytes"]),
        "permanent_exclusions": list(child_grant["permanent_exclusions"]),
        "knowledge": knowledge,
    }
    _require(len(canonical_json(unsigned).encode("utf-8")) <= MAX_PACKET_BYTES, "program work packet exceeds its byte ceiling")
    return validate_work_packet({**unsigned, "packet_hash": _sha(unsigned)})


_PROTECTED_PROGRAM_PATHS = (
    "pm/programs/", "pm/workflows/", "pm/organizations/", "pm/rubrics/",
)


def _collect_outputs(
    root: Path,
    run_id: str,
    action: dict[str, object],
    packet: dict[str, object],
    record: dict[str, object],
) -> list[dict[str, object]]:
    staging = Path(str(record["staging"]))
    output_dir = staging / "outputs"
    artifacts: list[dict[str, object]] = []
    for spec in packet["outputs"]:
        name = str(spec["name"])
        fmt = str(spec["format"])
        kind = str(spec.get("artifact_kind") or fmt)
        checks = ["declared", "bounded", "contained"]
        if fmt == "git-diff":
            _require(packet["workspace"]["mode"] == "isolated-worktree", "git-diff output lacks an isolated workspace")
            data, paths = _git_diff_artifact(
                Path(str(packet["workspace"]["path"])),
                list(spec["allowed_paths"]),
            )
            _require(
                not any(path.startswith(_PROTECTED_PROGRAM_PATHS) for path in paths),
                "program child attempted to edit tracked autonomous policy",
            )
            checks.extend(["git-diff", "paths:" + ",".join(paths)])
        else:
            source = output_dir / name
            _require(source.is_file() and not source.is_symlink(), f"declared program output is missing: {name}")
            data = source.read_bytes()
        _require(len(data) <= int(spec["max_bytes"]), f"program output {name!r} exceeds its declared byte bound")
        try:
            text = data.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise DwError(f"program output {name!r} is not UTF-8") from exc
        if fmt == "json":
            try:
                json.loads(text)
            except json.JSONDecodeError as exc:
                raise DwError(f"program JSON output {name!r} is malformed") from exc
            checks.append("json")
        elif fmt == "markdown":
            _require(bool(text.strip()), f"program Markdown output {name!r} is empty")
            checks.append("markdown")
        elif fmt not in {"text", "git-diff", "directory"}:
            raise DwError(f"unsupported program artifact format: {fmt}")
        artifacts.append(_store_artifact(
            root,
            run_id,
            action_id=str(action["action_id"]),
            address=str(action["address"]),
            attempt=int(action["attempt"]),
            name=name,
            kind=kind,
            data=data,
            checks=checks,
        ))
    return artifacts


def _claim_subject(
    action: dict[str, object],
    *,
    kind: str,
    content_hash: str,
    subject_id: str | None = None,
) -> dict[str, object]:
    phase = action.get("phase")
    story = action.get("story")
    _require(
        phase is None
        or (
            isinstance(phase, int)
            and not isinstance(phase, bool)
            and phase >= 0
        ),
        "program action phase is invalid",
    )
    _require(
        story is None or isinstance(story, str),
        "program action story is invalid",
    )
    return {
        "kind": kind,
        "id": subject_id or str(action["address"]),
        "hash": content_hash,
        "phase": phase,
        "story": story,
    }


def _reserve_claim(
    root: Path,
    run_id: str,
    *,
    action: dict[str, object],
    category: str,
    subject_kind: str,
    subject_hash: str,
    suffix: str,
    now: datetime,
    driver_config: dict[str, object],
    child_grant: dict[str, object] | None = None,
    resource_estimate: dict[str, int] | None = None,
    subject_id: str | None = None,
    request_port: str | None = None,
) -> dict[str, object]:
    key = f"program-conductor/{action['action_id']}/{suffix}"
    estimate = resource_estimate or {
        "artifact_bytes": 0,
        "tokens": 0,
        "observed_cost_microunits": 0,
    }
    subject = _claim_subject(
        action, kind=subject_kind, content_hash=subject_hash,
        subject_id=subject_id,
    )
    existing = _claim_by_key(replay_program(root, run_id, now=now), key)
    if existing is not None:
        _require(existing["category"] == category, "existing conductor claim category changed")
        _require(existing["subject"] == subject, "existing conductor claim subject changed")
        _require(existing["resource_estimate"] == estimate, "existing conductor claim resource estimate changed")
        _require(existing.get("request_port") == request_port, "existing conductor claim request port changed")
        expected_child_hash = child_grant["grant_hash"] if child_grant is not None else None
        _require(existing.get("child_grant_hash") == expected_child_hash, "existing conductor claim child authority changed")
        return existing
    preview = build_program_claim_preview(
        root,
        run_id,
        category=category,
        subject=subject,
        idempotency_key=key,
        reason=f"Conduct declared {action['kind']} at its stable hierarchy address.",
        resource_estimate=estimate,
        child_grant=child_grant,
        request_port=request_port,
        now=now,
        driver_config=driver_config,
    )
    _require(preview["applicable"], "program act claim refused: " + "; ".join(
        str(item.get("message")) for item in preview["issues"] if isinstance(item, dict)
    ))
    applied = apply_program_claim(
        root,
        preview,
        claim_token=str(preview["claim_token"]),
        now=now,
        driver_config=driver_config,
    )
    claim = applied.get("claim")
    _require(isinstance(claim, dict), "program act claim produced no reservation")
    return claim


def _complete_claim(
    root: Path,
    run_id: str,
    claim: dict[str, object],
    receipt_hash: str,
    *,
    result: str,
    reason: str,
    now: datetime,
) -> dict[str, object]:
    preview = build_program_completion_preview(
        root,
        run_id,
        claim_id=str(claim["claim_id"]),
        result=result,
        receipt_hash=receipt_hash,
        reason=reason,
        now=now,
    )
    _require(preview["applicable"], "program completion receipt was refused")
    return apply_program_completion(
        root,
        preview,
        completion_token=str(preview["completion_token"]),
        now=now,
    )


def _local_action(
    root: Path,
    run_id: str,
    action: dict[str, object],
    *,
    category: str,
    subject_hash: str,
    payload: dict[str, object],
    now: datetime,
    driver_config: dict[str, object],
    boundary_hook: BoundaryHook | None = None,
    result: str = "complete",
    route: object = None,
    subject_kind: str | None = None,
    subject_id: str | None = None,
) -> tuple[dict[str, object], dict[str, object]]:
    claim = _reserve_claim(
        root,
        run_id,
        action=action,
        category=category,
        subject_kind=subject_kind or f"program-{action['kind']}",
        subject_hash=subject_hash,
        subject_id=subject_id,
        suffix="local",
        now=now,
        driver_config=driver_config,
    )
    if claim["status"] != "active":
        receipt = _load_receipt(root, run_id, str(claim["receipt_hash"]))
        return replay_program(root, run_id, now=now), receipt
    _boundary(boundary_hook, "after-claim", {
        "action_id": action["action_id"],
        "claim_id": claim["claim_id"],
        "category": category,
    })
    receipt = _store_receipt(root, run_id, {
        "action_id": action["action_id"],
        "address": action["address"],
        "action_kind": action["kind"],
        "phase": action["phase"],
        "story": action["story"],
        "workflow_address": action["workflow_address"],
        "node": action.get("node"),
        "role": action.get("role"),
        "role_address": action.get("role_address"),
        "attempt": action["attempt"],
        "claim_id": claim["claim_id"],
        "request_hash": claim["request_hash"],
        "outcome": "succeeded",
        "result": result,
        "route": route,
        "operation": None,
        "artifacts": [],
        "verdict": None,
        "decision": None,
        "obligation_ids": [],
        "payload": payload,
        "issued_at": str(claim["reserved_at"]),
    })
    _boundary(boundary_hook, "after-receipt", {
        "action_id": action["action_id"],
        "claim_id": claim["claim_id"],
        "receipt_hash": receipt["receipt_hash"],
        "receipt_kind": str(action["kind"]),
    })
    projection = _complete_claim(
        root,
        run_id,
        claim,
        str(receipt["receipt_hash"]),
        result="succeeded",
        reason=f"Recorded deterministic {action['kind']} receipt.",
        now=now,
    )
    return projection, receipt


def _quality_subject(
    run_id: str,
    context: dict[str, object],
    projection: dict[str, object],
    *,
    kind: str,
    subject_hash: str,
) -> dict[str, object]:
    assignment = context["assignment"]
    plan = context["plan"]
    grant = context["grant"]
    assert isinstance(assignment, dict) and isinstance(plan, dict) and isinstance(grant, dict)
    implementer = _role_member(_role_document(assignment, duty="implementer"))
    return {
        "kind": kind,
        "hash": subject_hash,
        "repository_hash": _sha(projection["expected_repository"]),
        "program_hash": grant["program"]["bundle_hash"],
        "program_run_id": run_id,
        "phase": int(plan["selection"]["phase"]),
        "story": str(plan["selection"]["story"]),
        "workflow_address": _workflow_address(plan),
        "assignment_hash": assignment["assignment_hash"],
        "assignment_generation": int(implementer["assignment_generation"]),
        "ledger_head": projection["ledger_head"],
        "implementer_principals": [implementer["principal_fingerprint"]],
    }


def _check_session_path(root: Path, run_id: str, claim_id: str) -> Path:
    _safe(claim_id, "check claim id")
    return _conductor_dir(root, run_id) / "check-sessions" / f"{claim_id}.json"


def _contained_policy_path(root: Path, relative: object, label: str) -> Path:
    _require(isinstance(relative, str) and relative and not Path(relative).is_absolute(), f"{label} path is unsafe")
    candidate = (root / relative).resolve()
    _require(candidate == root or root in candidate.parents, f"{label} path escaped the repository")
    return candidate


def _run_closed_check(
    root: Path,
    runner: object,
    receipts: list[dict[str, object]],
) -> dict[str, object]:
    _require(isinstance(runner, dict), "check node has no closed runner")
    kind = runner.get("kind")
    _require(kind == "builtin", "program conductor refuses tracked command argv; use a registered built-in check")
    name = str(runner.get("name"))
    detail: dict[str, object] = {"runner": name}
    if name == "file-exists":
        path = _contained_policy_path(root, runner.get("path"), "file-exists")
        passed = path.is_file() and not path.is_symlink()
        detail.update({"path": str(path.relative_to(root)), "observed": "file" if passed else "missing"})
        predicate = "artifact-conformance"
    elif name == "json-schema":
        path = _contained_policy_path(root, runner.get("path"), "json-schema document")
        schema_path = _contained_policy_path(root, runner.get("schema"), "json-schema schema")
        errors: list[str]
        try:
            document = json.loads(path.read_text(encoding="utf-8"))
            schema = json.loads(schema_path.read_text(encoding="utf-8"))
            errors = _schema_check(document, schema)
        except (OSError, json.JSONDecodeError) as exc:
            errors = [str(exc)[:500]]
        passed = not errors
        detail.update({
            "path": str(path.relative_to(root)),
            "schema": str(schema_path.relative_to(root)),
            "errors": errors[:20],
        })
        predicate = "schema-conformance"
    elif name == "diff-scope":
        allowed = runner.get("allowed_paths", [])
        _require(isinstance(allowed, list) and all(isinstance(item, str) for item in allowed), "diff-scope allowed paths are invalid")
        changed: list[str] = []
        for receipt in receipts:
            for artifact in receipt.get("artifacts", []):
                if not isinstance(artifact, dict) or artifact.get("artifact_kind") != "git-diff":
                    continue
                for check in artifact.get("checks", []):
                    if isinstance(check, str) and check.startswith("paths:"):
                        changed.extend(item for item in check.removeprefix("paths:").split(",") if item)
        outside = sorted({
            path for path in changed
            if not any(Path(path).match(pattern) for pattern in allowed)
        })
        passed = not outside
        detail.update({"allowed_paths": allowed, "changed_paths": sorted(set(changed)), "outside": outside})
        predicate = "diff-scope"
    elif name == "rail-status":
        raise DwError("rail-status belongs to the separately authorized WLA-26-10 rail adapter")
    else:
        raise DwError(f"unsupported registered program check: {name}")
    return {"passed": passed, "predicate": predicate, "detail": detail}


def _execute_check_action(
    root: Path,
    run_id: str,
    action: dict[str, object],
    context: dict[str, object],
    config: dict[str, object],
    *,
    now: datetime,
    boundary_hook: BoundaryHook | None,
) -> dict[str, object]:
    runner_hash = _sha(action["runner"])
    claim = _reserve_claim(
        root, run_id, action=action, category="check",
        subject_kind="program-check", subject_hash=runner_hash,
        suffix="check", now=now, driver_config=config,
    )
    if claim["status"] != "active":
        return {"status": "complete", "projection": replay_program(root, run_id, now=now), "receipt": _load_receipt(root, run_id, str(claim["receipt_hash"]))}
    _boundary(boundary_hook, "after-claim", {
        "action_id": action["action_id"], "claim_id": claim["claim_id"],
        "category": "check",
    })
    session_path = _check_session_path(root, run_id, str(claim["claim_id"]))
    if session_path.is_file():
        session = _load_json(session_path, "program check session")
        _require(session.get("runner_hash") == runner_hash, "program check runner changed")
    else:
        _write_json_atomic(session_path, {
            "kind": "delivery-workbench-program-check-session",
            "schema_version": PROGRAM_CONDUCTOR_SCHEMA_VERSION,
            "claim_id": claim["claim_id"],
            "runner_hash": runner_hash,
            "status": "prepared",
            "result": None,
        })
        session = _load_json(session_path, "program check session")
    if session["status"] == "prepared":
        operation_id = "check-" + hashlib.sha256(str(claim["claim_id"]).encode()).hexdigest()[:24]
        _boundary(boundary_hook, "before-dispatch", {
            "action_id": action["action_id"], "claim_id": claim["claim_id"],
            "operation_id": operation_id,
        })
        observed = _run_closed_check(
            root,
            action["runner"],
            _receipts_for_plan(
                replay_program_conductor(root, run_id, now=now)["receipts"],
                context["plan"],
            ),
        )
        session = {**session, "status": "observed", "result": observed}
        _write_json_atomic(session_path, session)
        _boundary(boundary_hook, "after-dispatch", {
            "action_id": action["action_id"], "claim_id": claim["claim_id"],
            "operation_id": operation_id,
        })
    observed = session["result"]
    _require(isinstance(observed, dict), "program check observation disappeared")
    observation_data = (canonical_json(observed["detail"]) + "\n").encode("utf-8")
    observation = _store_artifact(
        root, run_id, action_id=str(action["action_id"]),
        address=str(action["address"]), attempt=int(action["attempt"]),
        name="check-observation", kind="check-result", data=observation_data,
        checks=["closed-runner", "contained", "deterministic"],
    )
    projection = replay_program(root, run_id, now=now)
    subject = _quality_subject(
        run_id, context, projection, kind="artifact-set",
        subject_hash=_sha(_evidence_from_receipts(_receipts_for_plan(
            replay_program_conductor(root, run_id, now=now)["receipts"],
            context["plan"],
        ))),
    )
    mechanical_unsigned = {
        "kind": "delivery-workbench-mechanical-receipt",
        "schema_version": 1,
        "adapter_kind": "check-adapter",
        "adapter_id": "program-builtin-checks",
        "adapter_fingerprint": _sha({"adapter": "program-builtin-checks", "version": 1}),
        "capability": "check:execute",
        "predicate": observed["predicate"],
        "passed": observed["passed"],
        "observation_ref": observation["ref"],
        "observation_hash": observation["sha256"],
        "observation_bytes": observation["bytes"],
        "command": None,
        "issued_at": claim["reserved_at"],
    }
    mechanical_receipt = {
        **mechanical_unsigned,
        "receipt_hash": _sha(mechanical_unsigned),
    }
    fact = validate_mechanical_fact(build_mechanical_fact(
        str(action["node"]), mechanical_receipt, subject
    ))
    fact_spec = next(
        (item for item in action.get("outputs", []) if isinstance(item, dict)),
        {"id": "fact", "max_bytes": 100_000},
    )
    fact_data = (canonical_json(fact) + "\n").encode("utf-8")
    _require(len(fact_data) <= int(fact_spec["max_bytes"]), "mechanical fact exceeds its declared output bound")
    fact_artifact = _store_artifact(
        root, run_id, action_id=str(action["action_id"]),
        address=str(action["address"]), attempt=int(action["attempt"]),
        name=str(fact_spec["id"]), kind="mechanical-fact", data=fact_data,
        checks=["mechanical-fact-core", "closed-runner", "subject-bound"],
    )
    outcome = "succeeded" if observed["passed"] else "failed"
    result = "pass" if observed["passed"] else "fail"
    receipt = _store_receipt(root, run_id, {
        "action_id": action["action_id"], "address": action["address"],
        "action_kind": "check", "phase": action["phase"], "story": action["story"],
        "workflow_address": action["workflow_address"], "node": action["node"],
        "role": None, "role_address": None, "attempt": action["attempt"],
        "claim_id": claim["claim_id"], "request_hash": claim["request_hash"],
        "outcome": outcome, "result": result, "route": result,
        "operation": {"runner_hash": runner_hash, "predicate": observed["predicate"]},
        "artifacts": [observation, fact_artifact], "verdict": None,
        "decision": None, "obligation_ids": [],
        "payload": {"fact_hash": fact["fact_hash"]},
        "issued_at": claim["reserved_at"],
    })
    _boundary(boundary_hook, "after-receipt", {
        "action_id": action["action_id"], "claim_id": claim["claim_id"],
        "receipt_hash": receipt["receipt_hash"], "receipt_kind": "check",
    })
    projection = _complete_claim(
        root, run_id, claim, str(receipt["receipt_hash"]), result=outcome,
        reason=f"Closed built-in check returned {result}.", now=now,
    )
    return {"status": "complete", "projection": projection, "receipt": receipt}


def _execute_collect_action(
    root: Path,
    run_id: str,
    action: dict[str, object],
    context: dict[str, object],
    config: dict[str, object],
    *,
    now: datetime,
    boundary_hook: BoundaryHook | None,
) -> dict[str, object]:
    prior_receipts = _receipts_for_plan(
        replay_program_conductor(root, run_id, now=now)["receipts"],
        context["plan"],
    )
    evidence = _evidence_from_receipts(prior_receipts)
    manifest_hash = _sha({"evidence": evidence, "outputs": action.get("outputs", [])})
    claim = _reserve_claim(
        root, run_id, action=action, category="check",
        subject_kind="program-artifact-collection", subject_hash=manifest_hash,
        suffix="collect", now=now, driver_config=config,
    )
    if claim["status"] != "active":
        return {"status": "complete", "projection": replay_program(root, run_id, now=now), "receipt": _load_receipt(root, run_id, str(claim["receipt_hash"]))}
    _boundary(boundary_hook, "after-claim", {
        "action_id": action["action_id"], "claim_id": claim["claim_id"],
        "category": "check",
    })
    artifacts: list[dict[str, object]] = []
    for spec in action.get("outputs", []):
        _require(isinstance(spec, dict), "collect output is invalid")
        kind = str(spec["kind"])
        if kind == "json":
            data = (canonical_json({"artifacts": evidence}) + "\n").encode("utf-8")
        elif kind in {"markdown", "text"}:
            lines = ["# Collected artifacts", ""] if kind == "markdown" else []
            lines.extend(
                f"- {item['kind']} {item['hash']} ({item['ref']})"
                for item in evidence
            )
            data = ("\n".join(lines) + "\n").encode("utf-8")
        elif kind == "directory":
            data = (canonical_json({"entries": evidence}) + "\n").encode("utf-8")
        else:
            raise DwError(f"collect node cannot synthesize artifact kind {kind}")
        _require(len(data) <= int(spec["max_bytes"]), "collected artifact exceeds its declared bound")
        artifacts.append(_store_artifact(
            root, run_id, action_id=str(action["action_id"]),
            address=str(action["address"]), attempt=int(action["attempt"]),
            name=str(spec["id"]), kind=kind, data=data,
            checks=["deterministic-collection", "input-hashes-bound", "bounded"],
        ))
    receipt = _store_receipt(root, run_id, {
        "action_id": action["action_id"], "address": action["address"],
        "action_kind": "collect", "phase": action["phase"], "story": action["story"],
        "workflow_address": action["workflow_address"], "node": action["node"],
        "role": None, "role_address": None, "attempt": action["attempt"],
        "claim_id": claim["claim_id"], "request_hash": claim["request_hash"],
        "outcome": "succeeded", "result": "complete", "route": "success",
        "operation": None, "artifacts": artifacts, "verdict": None,
        "decision": None, "obligation_ids": [],
        "payload": {"input_manifest_hash": manifest_hash, "input_count": len(evidence)},
        "issued_at": claim["reserved_at"],
    })
    _boundary(boundary_hook, "after-receipt", {
        "action_id": action["action_id"], "claim_id": claim["claim_id"],
        "receipt_hash": receipt["receipt_hash"], "receipt_kind": "collect",
    })
    projection = _complete_claim(
        root, run_id, claim, str(receipt["receipt_hash"]), result="succeeded",
        reason="Collected the exact validated dependency artifacts.", now=now,
    )
    return {"status": "complete", "projection": projection, "receipt": receipt}


def _execute_architecture_boundary(
    root: Path,
    run_id: str,
    action: dict[str, object],
    config: dict[str, object],
    *,
    now: datetime,
    boundary_hook: BoundaryHook | None,
) -> dict[str, object]:
    claim = _reserve_claim(
        root,
        run_id,
        action=action,
        category="gate",
        subject_kind="program-architecture-boundary",
        subject_hash=str(action["subject_hash"]),
        suffix="boundary",
        now=now,
        driver_config=config,
    )
    if claim["status"] != "active":
        return {
            "status": "complete",
            "projection": replay_program(root, run_id, now=now),
            "receipt": _load_receipt(
                root, run_id, str(claim["receipt_hash"])
            ),
        }
    _boundary(boundary_hook, "after-claim", {
        "action_id": action["action_id"],
        "claim_id": claim["claim_id"],
        "category": "gate",
    })
    document = str(action["document"]).encode("utf-8")
    digest = "sha256:" + hashlib.sha256(document).hexdigest()
    _require(
        digest == action["subject_hash"],
        "phase architecture boundary document changed",
    )
    artifact = _store_artifact(
        root,
        run_id,
        action_id=str(action["action_id"]),
        address=str(action["address"]),
        attempt=int(action["attempt"]),
        name="boundary-snapshot",
        kind="markdown",
        data=document,
        checks=[
            "phase-boundary", "receipt-lineage-bound",
            "evidence-hashes-only", "no-repository-write",
        ],
    )
    receipt = _store_receipt(root, run_id, {
        "action_id": action["action_id"],
        "address": action["address"],
        "action_kind": "architecture-boundary",
        "phase": action["phase"],
        "story": action["story"],
        "workflow_address": action["workflow_address"],
        "node": action["node"],
        "role": None,
        "role_address": None,
        "attempt": action["attempt"],
        "claim_id": claim["claim_id"],
        "request_hash": claim["request_hash"],
        "outcome": "succeeded",
        "result": "frozen",
        "route": None,
        "operation": None,
        "artifacts": [artifact],
        "verdict": None,
        "decision": None,
        "obligation_ids": [],
        "payload": {
            "boundary": action["boundary"],
            "gate": action["gate"],
            "snapshot_hash": action["subject_hash"],
        },
        "issued_at": claim["reserved_at"],
    })
    _boundary(boundary_hook, "after-receipt", {
        "action_id": action["action_id"],
        "claim_id": claim["claim_id"],
        "receipt_hash": receipt["receipt_hash"],
        "receipt_kind": "architecture-boundary",
    })
    projection = _complete_claim(
        root,
        run_id,
        claim,
        str(receipt["receipt_hash"]),
        result="succeeded",
        reason="Froze the exact immutable phase architecture boundary.",
        now=now,
    )
    return {
        "status": "complete",
        "projection": projection,
        "receipt": receipt,
    }


def _execute_architecture_gate(
    root: Path,
    run_id: str,
    action: dict[str, object],
    config: dict[str, object],
    *,
    now: datetime,
    boundary_hook: BoundaryHook | None,
) -> dict[str, object]:
    proof = action["proof"]
    _require(
        isinstance(proof, dict)
        and proof.get("proof_hash") == action["subject_hash"]
        and _sha({
            key: value for key, value in proof.items()
            if key != "proof_hash"
        }) == proof["proof_hash"],
        "phase architecture gate proof is invalid",
    )
    for flag in (
        "starts_work", "writes_state", "writes_repository",
        "writes_roadmap", "materializes_evidence", "creates_grant",
    ):
        _require(
            proof.get(flag) is False,
            "phase architecture gate proof attempted a side effect",
        )
    claim = _reserve_claim(
        root,
        run_id,
        action=action,
        category="gate",
        subject_kind="program-architecture-gate",
        subject_hash=str(action["subject_hash"]),
        suffix="evaluation",
        now=now,
        driver_config=config,
    )
    if claim["status"] != "active":
        return {
            "status": "complete",
            "projection": replay_program(root, run_id, now=now),
            "receipt": _load_receipt(
                root, run_id, str(claim["receipt_hash"])
            ),
        }
    _boundary(boundary_hook, "after-claim", {
        "action_id": action["action_id"],
        "claim_id": claim["claim_id"],
        "category": "gate",
    })
    artifact = _store_artifact(
        root,
        run_id,
        action_id=str(action["action_id"]),
        address=str(action["address"]),
        attempt=int(action["attempt"]),
        name="architecture-gate-proof",
        kind="verdict",
        data=(canonical_json(proof) + "\n").encode("utf-8"),
        checks=[
            "quality-gate-core", "architect-verdict-bound",
            "rubric-bound", "side-effect-free",
        ],
    )
    receipt = _store_receipt(root, run_id, {
        "action_id": action["action_id"],
        "address": action["address"],
        "action_kind": "architecture-gate",
        "phase": action["phase"],
        "story": action["story"],
        "workflow_address": action["workflow_address"],
        "node": action["node"],
        "role": action["role"],
        "role_address": action["role_address"],
        "attempt": action["attempt"],
        "claim_id": claim["claim_id"],
        "request_hash": claim["request_hash"],
        "outcome": "succeeded",
        "result": proof["result"],
        "route": action["route"],
        "operation": None,
        "artifacts": [artifact],
        "verdict": {
            "hash": action["verdict"]["verdict_hash"],  # type: ignore[index]
            "result": action["verdict"]["result"],  # type: ignore[index]
            "type": action["verdict"]["verdict_type"],  # type: ignore[index]
        },
        "decision": None,
        "obligation_ids": [],
        "payload": {
            "boundary": action["boundary"],
            "gate": action["gate"],
            "policy_hash": proof["gate"]["semantic_hash"],  # type: ignore[index]
            "proof_hash": proof["proof_hash"],
        },
        "issued_at": claim["reserved_at"],
    })
    _boundary(boundary_hook, "after-receipt", {
        "action_id": action["action_id"],
        "claim_id": claim["claim_id"],
        "receipt_hash": receipt["receipt_hash"],
        "receipt_kind": "architecture-gate",
    })
    projection = _complete_claim(
        root,
        run_id,
        claim,
        str(receipt["receipt_hash"]),
        result="succeeded",
        reason=(
            "Recorded the pure phase architecture gate proof and its "
            "declared route."
        ),
        now=now,
    )
    return {
        "status": "complete",
        "projection": projection,
        "receipt": receipt,
    }


def _execute_scope_completion(
    root: Path,
    run_id: str,
    action: dict[str, object],
    config: dict[str, object],
    *,
    now: datetime,
    boundary_hook: BoundaryHook | None,
) -> dict[str, object]:
    projection, receipt = _local_action(
        root,
        run_id,
        action,
        category="assignment",
        subject_hash=str(action["subject_hash"]),
        subject_kind="program-scope-proof",
        payload=dict(action["payload"]),
        now=now,
        driver_config=config,
        boundary_hook=boundary_hook,
        result="scope-complete",
    )
    payload = action["payload"]
    _require(
        isinstance(payload, dict),
        "program scope completion payload is invalid",
    )
    projection = complete_program_scope(
        root,
        run_id,
        claim_id=str(receipt["claim_id"]),
        proof_hash=str(action["subject_hash"]),
        completed_stories=list(payload["completed_stories"]),
        completed_phases=list(payload["completed_phases"]),
        now=now,
    )
    _boundary(boundary_hook, "after-scope-completion", {
        "action_id": action["action_id"],
        "claim_id": receipt["claim_id"],
        "proof_hash": action["subject_hash"],
    })
    return {
        "status": "complete",
        "projection": projection,
        "receipt": receipt,
    }


def _is_conductor_claim(claim: dict[str, object]) -> bool:
    return str(claim.get("idempotency_key", "")).startswith("program-conductor/")


def replay_program_conductor(
    root: Path,
    run_id: str,
    *,
    now: str | datetime | None = None,
) -> dict[str, object]:
    """Replay ledger authority and verify every conductor receipt it binds.

    Receipts are deliberately not an alternative projection.  A completed
    conductor claim is meaningful only when the ledger binds the exact
    immutable receipt hash, and a missing or edited receipt stops replay.
    """
    observed = _time(now, "now")
    projection = replay_program(root.resolve(), run_id, now=observed)
    receipts: list[dict[str, object]] = []
    active: list[dict[str, object]] = []
    for claim in projection["claims"]:
        if not isinstance(claim, dict) or not _is_conductor_claim(claim):
            continue
        if claim["status"] == "active":
            active.append(claim)
            continue
        receipt_hash = claim.get("receipt_hash")
        _require(isinstance(receipt_hash, str), "completed conductor claim has no receipt hash")
        receipt = _load_receipt(root.resolve(), run_id, receipt_hash)
        _require(receipt.get("claim_id") == claim["claim_id"], "conductor receipt claim binding changed")
        _require(receipt.get("request_hash") == claim["request_hash"], "conductor receipt request binding changed")
        receipts.append(receipt)
    receipts.sort(key=lambda item: (str(item.get("address")), str(item.get("action_kind")), int(item.get("attempt", 0))))
    return {
        "kind": PROGRAM_FRONTIER_KIND,
        "schema_version": PROGRAM_CONDUCTOR_SCHEMA_VERSION,
        "run_id": run_id,
        "authority": projection,
        "active_conductor_claims": active,
        "receipts": receipts,
        "receipt_hashes": [item["receipt_hash"] for item in receipts],
        "starts_work": False,
        "writes_state": False,
    }


def _receipt_for(
    receipts: list[dict[str, object]],
    action_id: str,
    *,
    action_kind: str | None = None,
) -> dict[str, object] | None:
    matches = [
        item for item in receipts
        if item.get("action_id") == action_id
        and (action_kind is None or item.get("action_kind") == action_kind)
    ]
    _require(len(matches) <= 1, f"duplicate conductor receipt for {action_id}")
    return matches[0] if matches else None


def _base_action(
    plan: dict[str, object],
    *,
    kind: str,
    address: str,
    attempt: int = 1,
    node: str | None = None,
    role: str | None = None,
    role_address: str | None = None,
) -> dict[str, object]:
    selection = plan["selection"]
    _require(isinstance(selection, dict), "program plan has no selected story")
    workflow_address = _workflow_address(plan)
    action_address = address
    return {
        "action_id": _action_id(action_address, kind, attempt),
        "kind": kind,
        "address": action_address,
        "phase": int(selection["phase"]),
        "story": str(selection["story"]),
        "workflow_address": workflow_address,
        "node": node,
        "role": role,
        "role_address": role_address,
        "attempt": attempt,
    }


def _current_program_context(
    root: Path,
    run_id: str,
    projection: dict[str, object],
    driver_config: dict[str, object],
) -> dict[str, object]:
    _path, grant, _starting_plan = _load_documents(root, run_id)
    freshness = program_freshness_issues(
        root, grant, projection, driver_config=driver_config
    )
    _require(not freshness, "program grant is stale: " + "; ".join(freshness))
    selector = str(grant["program_selector"])
    plan = build_program_plan(root, selector, driver_config=driver_config)
    _require(plan["program"]["policy_bundle_hash"] == grant["program"]["policy_bundle_hash"], "program policy bundle changed")  # type: ignore[index]
    program_path = find_program_path(root, selector)
    compiled = compile_program_path(root, program_path)
    selection = plan["selection"]
    issue_codes = {
        str(item.get("code"))
        for item in plan.get("issues", [])
        if isinstance(item, dict)
    }
    if selection is None:
        _require(
            not plan["applicable"] and issue_codes == {"scope-complete"},
            "program frontier is not runnable: " + "; ".join(
                sorted(issue_codes)
            ),
        )
        return {
            "grant": grant,
            "plan": plan,
            "compiled": compiled,
            "instance": None,
            "assignment": None,
        }
    _require(
        plan["applicable"],
        "program frontier is not runnable: " + "; ".join(
            sorted(issue_codes)
        ),
    )
    assert isinstance(selection, dict)
    instance = compiled["references"]["workflow_instances"].get(selection["binding"])  # type: ignore[index,union-attr]
    _require(isinstance(instance, dict), "selected workflow instance disappeared")
    assignment = plan["assignment"]
    _require(isinstance(assignment, dict) and assignment.get("separation", {}).get("passed") is True, "program assignment does not prove separation")
    _require(
        assignment["roster_hash"] == grant["roster"]["roster_hash"],
        "program roster changed",
    )
    return {
        "grant": grant,
        "plan": plan,
        "compiled": compiled,
        "instance": instance,
        "assignment": assignment,
    }


def _evidence_from_receipts(
    receipts: list[dict[str, object]],
) -> list[dict[str, object]]:
    evidence: list[dict[str, object]] = []
    seen: set[tuple[str, str]] = set()
    for receipt in receipts:
        for artifact in receipt.get("artifacts", []):
            if not isinstance(artifact, dict) or not artifact.get("valid"):
                continue
            key = (str(artifact["sha256"]), str(artifact["ref"]))
            if key in seen:
                continue
            seen.add(key)
            evidence.append({
                "kind": artifact["artifact_kind"],
                "hash": artifact["sha256"],
                "ref": artifact["ref"],
            })
    evidence.sort(key=lambda item: (str(item["kind"]), str(item["hash"]), str(item["ref"])))
    return evidence


def _receipts_for_plan(
    receipts: list[dict[str, object]],
    plan: dict[str, object],
) -> list[dict[str, object]]:
    selection = plan["selection"]
    assert isinstance(selection, dict)
    workflow_address = _workflow_address(plan)
    return [
        item for item in receipts
        if item.get("phase") == selection["phase"]
        and item.get("story") == selection["story"]
        and item.get("workflow_address") == workflow_address
    ]


def _claim_order(
    projection: dict[str, object],
) -> dict[str, int]:
    return {
        str(claim["claim_id"]): index
        for index, claim in enumerate(projection.get("claims", []))
        if isinstance(claim, dict) and isinstance(claim.get("claim_id"), str)
    }


def _receipt_order(
    receipt: dict[str, object],
    order: dict[str, int],
) -> int:
    return order.get(str(receipt.get("claim_id") or ""), -1)


def _obligation_frontier(
    projection: dict[str, object],
) -> dict[str, object]:
    open_items = [
        item for item in projection.get("open_obligations", [])
        if isinstance(item, dict)
    ]
    blocking = [
        item for item in projection.get("blocking_obligations", [])
        if isinstance(item, dict)
    ]
    return {
        "open_obligations": [
            {
                "id": item["id"],
                "kind": item["kind"],
                "priority": item["priority"],
                "blocking": item["blocking"],
                "state": item["state"],
                "target": item["target"],
                "obligation_hash": item["obligation_hash"],
            }
            for item in open_items
        ],
        "open_obligation_ids": [
            item["id"] for item in open_items
        ],
        "blocking_obligation_ids": [
            item["id"] for item in blocking
        ],
    }


def _scope_completion_action(
    grant: dict[str, object],
    plan: dict[str, object],
    projection: dict[str, object],
) -> dict[str, object]:
    program = plan["program"]
    scope = grant["scope"]
    _require(
        isinstance(program, dict) and isinstance(scope, dict),
        "program scope completion context is invalid",
    )
    completed_stories = sorted(
        str(item) for item in scope.get("story_ids", [])
    )
    completed_phases = sorted(
        int(item) for item in scope.get("phases", [])
    )
    obligations = [
        {
            "id": item["id"],
            "hash": item["obligation_hash"],
            "state": item["state"],
            "blocking": item["blocking"],
        }
        for item in projection.get("open_obligations", [])
        if isinstance(item, dict)
    ]
    payload = {
        "program": program["slug"],
        "program_bundle_hash": program["bundle_hash"],
        "policy_bundle_hash": program["policy_bundle_hash"],
        "repository_hash": _sha(projection["expected_repository"]),
        "roadmap_hash": _sha(projection["expected_roadmap"]),
        "scope_hash": _sha(scope),
        "completed_stories": completed_stories,
        "completed_phases": completed_phases,
        "open_obligations": obligations,
    }
    address = f"program/{program['slug']}/scope/completion/attempt/1"
    action = {
        "action_id": _action_id(address, "scope-completion", 1),
        "kind": "scope-completion",
        "address": address,
        "phase": None,
        "story": None,
        "workflow_address": f"program/{program['slug']}/scope",
        "node": None,
        "role": None,
        "role_address": None,
        "attempt": 1,
        "payload": payload,
        "subject_hash": _sha(payload),
    }
    return action


def _workflow_node_action(
    root: Path,
    plan: dict[str, object],
    instance: dict[str, object],
    expanded: dict[str, object],
    receipts: list[dict[str, object]],
    *,
    attempt: int = 1,
) -> dict[str, object]:
    node = _node_policy(root, expanded)
    workflow_address = _workflow_address(plan)
    node_base = _lineage_address(
        workflow_address,
        str(instance["slug"]),
        str(expanded["address"]),
    )
    node_type = str(node["type"])
    kind = "verdict" if node_type in {"verdict", "panel"} else node_type
    role_id = node.get("role")
    _require(isinstance(role_id, str), f"workflow node {node['id']} has no singular assigned role")
    assignment = plan["assignment"]
    assert isinstance(assignment, dict)
    role = _role_document(assignment, role_id=role_id)
    member = _role_member(role)
    address = f"{node_base}/role/{role_id}/attempt/{attempt}"
    action = _base_action(
        plan,
        kind=kind,
        address=address,
        node=str(node["id"]),
        role=role_id,
        role_address=str(member["address"]),
        attempt=attempt,
    )
    action.update({
        "node_address": node_base,
        "workspace": node.get("workspace", role.get("packet_policy", {}).get("workspace", "read-only")),
        "capabilities": list(node.get("capability_ceiling", [])),
        "timeout_seconds": int(node.get("timeout_seconds", 900)),
        "outputs": list(node.get("outputs", [])),
        "inputs": [],
        "prompt_document": {
            "task": node.get("task") or f"Execute the declared {node_type} node.",
            "workflow": str(expanded["workflow"]),
            "node": str(node["id"]),
            "evidence": _evidence_from_receipts(receipts),
        },
    })
    if kind == "verdict":
        rubric_selector = str(node.get("rubric") or plan["selection"]["rubrics"][0]["slug"])  # type: ignore[index]
        rubric = compile_rubric(root, rubric_selector)
        action["rubric"] = rubric_selector
        action["outputs"] = [{
            "id": "judgment", "kind": "verdict",
            "max_bytes": int(node.get("max_rationale_bytes", 100_000)),
        }]
        action["prompt_document"].update({  # type: ignore[union-attr]
            "action_kind": "verdict",
            "rubric": rubric["rubric"],
        })
    return action


def _local_workflow_action(
    root: Path,
    plan: dict[str, object],
    instance: dict[str, object],
    expanded: dict[str, object],
    *,
    attempt: int = 1,
) -> dict[str, object]:
    node = _node_policy(root, expanded)
    node_type = str(node["type"])
    _require(node_type in {"check", "collect"}, "local workflow action type is unsupported")
    node_base = _lineage_address(
        _workflow_address(plan),
        str(instance["slug"]),
        str(expanded["address"]),
    )
    address = f"{node_base}/attempt/{attempt}"
    action = _base_action(
        plan,
        kind=node_type,
        address=address,
        node=str(node["id"]),
        attempt=attempt,
    )
    action.update({
        "node_address": node_base,
        "outputs": list(node.get("outputs", [])),
        "runner": node.get("runner"),
        "prompt_document": {"task": f"Execute deterministic {node_type} node."},
    })
    return action


def _program_nudge_rules(
    plan: dict[str, object],
) -> list[dict[str, object]]:
    selection = plan["selection"]
    _require(
        isinstance(selection, dict),
        "program nudge derivation requires one selected story",
    )
    return [
        rule
        for rule in plan["program"].get("nudges", [])  # type: ignore[union-attr]
        if isinstance(rule, dict)
        and rule.get("binding") == selection.get("binding")
    ]


def _program_nudge_target(
    instance: dict[str, object],
    rule: dict[str, object],
) -> dict[str, object]:
    matches = [
        item
        for item in instance.get("expanded_nodes", [])
        if isinstance(item, dict)
        and item.get("address") == rule.get("target")
    ]
    _require(
        len(matches) == 1 and matches[0].get("type") == "agent",
        "compiled program nudge target is no longer one exact agent",
    )
    return matches[0]


def _program_signal_projection(
    root: Path,
    projection: dict[str, object],
) -> tuple[dict[str, object] | None, str | None]:
    repository = projection["expected_repository"]
    _require(
        isinstance(repository, dict),
        "program repository fact binding is invalid",
    )
    remote = repository.get("remote")
    remote_ref = repository.get("remote_ref")
    _require(
        isinstance(remote, str) and isinstance(remote_ref, str),
        "program standing nudge rules lost their exact remote/ref binding",
    )
    branch = _program_signal_branch(remote, remote_ref)
    _require(
        isinstance(branch, str),
        "program standing nudge remote/ref does not name one channel branch",
    )
    inventory = build_signals_inventory(
        root, remote=remote, branch=branch
    )
    channels = [
        item for item in inventory.get("channels", [])
        if isinstance(item, dict)
        and item.get("remote") == remote
        and item.get("branch") == branch
    ]
    _require(
        len(channels) <= 1,
        "program signal channel is ambiguous",
    )
    if not channels:
        return None, _sha({"remote": remote, "branch": branch})
    return (
        replay_signal_channel(root, remote, branch),
        _sha({"remote": remote, "branch": branch}),
    )


def _nudge_target_action(
    root: Path,
    plan: dict[str, object],
    instance: dict[str, object],
    rule: dict[str, object],
    receipts: list[dict[str, object]],
    payload: dict[str, object],
) -> dict[str, object]:
    expanded = _program_nudge_target(instance, rule)
    action = _workflow_node_action(
        root,
        plan,
        instance,
        expanded,
        receipts,
        attempt=int(payload["target_attempt"]),
    )
    _require(
        action["kind"] == "agent"
        and action["action_id"] == payload["target_action_id"],
        "program nudge target action changed after delivery",
    )
    nudge = {
        "rule_id": payload["rule_id"],
        "rule_hash": payload["rule_hash"],
        "signal": payload["signal"],
        "signal_event_hash": payload["signal_event_hash"],
        "outward_fact_receipt_hash": payload[
            "outward_fact_receipt_hash"
        ],
        "nudge_receipt_hash": payload["nudge_receipt_hash"],
        "expectation": payload["expectation"],
    }
    action["nudge"] = nudge
    prompt = action["prompt_document"]
    _require(
        isinstance(prompt, dict),
        "program nudge target prompt is invalid",
    )
    prompt["nudge"] = nudge
    return action


def _derive_program_outward_step(
    root: Path,
    run_id: str,
    context: dict[str, object],
    projection: dict[str, object],
    all_receipts: list[dict[str, object]],
    receipts: list[dict[str, object]],
) -> dict[str, object]:
    plan = context["plan"]
    instance = context["instance"]
    _require(
        isinstance(plan, dict) and isinstance(instance, dict),
        "program outward derivation has no selected workflow",
    )
    rules = _program_nudge_rules(plan)
    if not rules:
        return {"action": None, "stop": None}

    # A delivered nudge is already authority.  Rebuild its exact target
    # attempt before consulting newer outward facts so restart cannot strand
    # or supersede a previously claimed delivery.
    for rule in rules:
        deliveries = [
            item
            for item in all_receipts
            if item.get("action_kind") == "nudge"
            and isinstance(item.get("payload"), dict)
            and item["payload"].get("rule_id") == rule.get("id")
        ]
        for delivery in sorted(
            deliveries,
            key=lambda item: int(
                item.get("payload", {}).get("delivery", 0)
            ),
        ):
            payload = dict(delivery["payload"])
            target_action_id = str(payload.get("target_action_id") or "")
            completed = _receipt_for(
                all_receipts, target_action_id, action_kind="agent"
            )
            if completed is not None:
                continue
            selection = plan["selection"]
            assert isinstance(selection, dict)
            if (
                delivery.get("phase") != selection.get("phase")
                or delivery.get("story") != selection.get("story")
                or delivery.get("workflow_address")
                != _workflow_address(plan)
            ):
                return {
                    "action": None,
                    "stop": "nudge-target-lineage-stale",
                }
            payload["nudge_receipt_hash"] = delivery["receipt_hash"]
            return {
                "action": _nudge_target_action(
                    root,
                    plan,
                    instance,
                    rule,
                    receipts,
                    payload,
                ),
                "stop": None,
            }

    try:
        channel, channel_hash = _program_signal_projection(
            root, projection
        )
    except DwError:
        return {"action": None, "stop": "outward-facts-invalid"}
    if channel is None:
        return {"action": None, "stop": None}

    workflow_address = _workflow_address(plan)
    for rule in rules:
        rule_id = str(rule["id"])
        rule_hash = _sha(rule)
        fact = latest_nudge_fact(channel, str(rule["signal"]))
        if fact is None:
            continue
        signal_hash = str(fact["event_hash"])
        fact_receipts = [
            item
            for item in all_receipts
            if item.get("action_kind") == "outward-fact"
            and isinstance(item.get("payload"), dict)
            and item["payload"].get("rule_id") == rule_id
        ]
        for receipt in fact_receipts:
            payload = receipt["payload"]
            assert isinstance(payload, dict)
            _require(
                payload.get("rule_hash") == rule_hash,
                "program outward fact rule binding changed",
            )
        fact_receipt = next(
            (
                item for item in fact_receipts
                if item["payload"].get("signal_event_hash")  # type: ignore[union-attr]
                == signal_hash
            ),
            None,
        )
        if fact_receipt is None:
            if len(fact_receipts) >= int(rule["max_total"]):
                continue
            payload = {
                "rule_id": rule_id,
                "rule_hash": rule_hash,
                "signal": rule["signal"],
                "signal_event_hash": signal_hash,
                "signal_event_kind": fact["fact"],
                "signal_seq": int(fact["seq"]),
                "channel_hash": channel_hash,
            }
            digest = signal_hash.split(":", 1)[1][:24]
            address = (
                f"{workflow_address}/outward/rule/{rule_id}/"
                f"signal/{digest}/fact/attempt/1"
            )
            action = _base_action(
                plan,
                kind="outward-fact",
                address=address,
                attempt=1,
            )
            action.update({
                "payload": payload,
                "subject_hash": _sha(payload),
            })
            return {"action": action, "stop": None}

        deliveries = [
            item
            for item in all_receipts
            if item.get("action_kind") == "nudge"
            and isinstance(item.get("payload"), dict)
            and item["payload"].get("rule_id") == rule_id
        ]
        matching_deliveries = [
            item
            for item in deliveries
            if item["payload"].get("signal_event_hash") == signal_hash  # type: ignore[union-attr]
        ]
        if (
            len(deliveries) >= int(rule["max_total"])
            or len(matching_deliveries)
            >= int(rule["max_per_signal"])
        ):
            continue

        expanded = _program_nudge_target(instance, rule)
        node_base = _lineage_address(
            workflow_address,
            str(instance["slug"]),
            str(expanded["address"]),
        )
        target_receipts = [
            item
            for item in receipts
            if item.get("action_kind") == "agent"
            and str(item.get("address", "")).startswith(node_base + "/")
            and item.get("parent_action_id") is None
        ]
        if not target_receipts:
            # A standing nudge may wake or repeat declared work, never start
            # a node before its ordinary workflow activation.
            continue
        order = _claim_order(projection)
        latest_target_order = max(
            _receipt_order(item, order) for item in target_receipts
        )
        if any(
            item.get("action_kind") in {
                "council-decision",
                "loop-round",
            }
            and _receipt_order(item, order) > latest_target_order
            for item in receipts
        ):
            return {
                "action": None,
                "stop": "nudge-governance-replay-required",
            }
        _require(
            signal_receptivity("idle", "auto") == "deliver",
            "idle program nudge target became non-receptive",
        )
        target_attempt = max(
            int(item.get("attempt", 0)) for item in target_receipts
        ) + 1
        target_preview = _workflow_node_action(
            root,
            plan,
            instance,
            expanded,
            receipts,
            attempt=target_attempt,
        )
        delivery = len(deliveries) + 1
        payload = {
            "rule_id": rule_id,
            "rule_hash": rule_hash,
            "signal": rule["signal"],
            "signal_event_hash": signal_hash,
            "outward_fact_receipt_hash": fact_receipt["receipt_hash"],
            "channel_hash": channel_hash,
            "target": rule["target"],
            "target_lineage": target_preview["node_address"],
            "target_attempt": target_attempt,
            "target_action_id": target_preview["action_id"],
            "delivery": delivery,
            "max_per_signal": rule["max_per_signal"],
            "max_total": rule["max_total"],
            "expectation": str(rule.get("expectation") or ""),
            "receptivity": "idle",
        }
        digest = signal_hash.split(":", 1)[1][:24]
        address = (
            f"{workflow_address}/nudge/rule/{rule_id}/signal/{digest}/"
            f"delivery/{delivery}/attempt/1"
        )
        action = _base_action(
            plan,
            kind="nudge",
            address=address,
            attempt=delivery,
            node=str(expanded["node"]),
        )
        action.update({
            "payload": payload,
            "subject_hash": _sha(payload),
        })
        existing = next(
            (
                claim
                for claim in projection.get("active_claims", [])
                if isinstance(claim, dict)
                and claim.get("category") == "nudge"
                and claim.get("subject", {}).get("hash")  # type: ignore[union-attr]
                == action["subject_hash"]
                and str(claim.get("idempotency_key", "")).startswith(
                    f"program-conductor/{action['action_id']}/"
                )
            ),
            None,
        )
        if existing is None:
            if int(
                projection["budgets"]["max_nudges"]["remaining"]  # type: ignore[index]
            ) <= 0:
                return {
                    "action": None,
                    "stop": "nudge-budget-exhausted",
                }
            if any(
                int(projection["budgets"][key]["remaining"]) <= 0  # type: ignore[index]
                for key in (
                    "max_child_runs",
                    "max_agent_starts",
                    "max_provider_starts",
                    "max_model_starts",
                )
            ):
                return {
                    "action": None,
                    "stop": "nudge-target-budget-exhausted",
                }
            output_bytes = sum(
                int(item.get("max_bytes", 0))
                for item in target_preview.get("outputs", [])
                if isinstance(item, dict)
            )
            if output_bytes > int(
                projection["budgets"]["max_artifact_bytes"]["remaining"]  # type: ignore[index]
            ):
                return {
                    "action": None,
                    "stop": "nudge-target-budget-exhausted",
                }
        return {"action": action, "stop": None}
    return {"action": None, "stop": None}


def _synthetic_verifier_action(
    root: Path,
    plan: dict[str, object],
    receipts: list[dict[str, object]],
    *,
    attempt: int = 1,
) -> dict[str, object]:
    assignment = plan["assignment"]
    assert isinstance(assignment, dict)
    role = _role_document(assignment, duty="verifier")
    member = _role_member(role)
    role_id = str(role["role"])
    rubric_selector = str(plan["selection"]["rubrics"][0]["slug"])  # type: ignore[index]
    rubric = compile_rubric(root, rubric_selector)
    base = f"{_workflow_address(plan)}/verifier/{rubric_selector}"
    address = f"{base}/role/{role_id}/attempt/{attempt}"
    action = _base_action(
        plan,
        kind="story-verification",
        address=address,
        node="story-verification",
        role=role_id,
        role_address=str(member["address"]),
        attempt=attempt,
    )
    action.update({
        "node_address": base,
        "workspace": "read-only",
        "capabilities": ["agent:dispatch", "verdict:issue"],
        "timeout_seconds": 900,
        "outputs": [{"id": "judgment", "kind": "verdict", "max_bytes": 100_000}],
        "inputs": [],
        "rubric": rubric_selector,
        "prompt_document": {
            "action_kind": "story-verification",
            "task": "Independently verify the exact candidate artifacts against the bound rubric.",
            "rubric": rubric["rubric"],
            "evidence": _evidence_from_receipts(receipts),
        },
    })
    return action


def _synthetic_repair_action(
    plan: dict[str, object],
    *,
    round_number: int,
) -> dict[str, object]:
    assignment = plan["assignment"]
    assert isinstance(assignment, dict)
    # A compact team may assign repair authority to its implementation role;
    # the subsequent verifier remains independently preassigned.
    role = _role_document(assignment, duty="repairer") if any(
        item.get("duty") == "repairer" for item in assignment.get("roles", [])
    ) else _role_document(assignment, duty="implementer")
    member = _role_member(role)
    role_id = str(role["role"])
    base = f"{_workflow_address(plan)}/repair/round/{round_number}"
    address = f"{base}/role/{role_id}/attempt/1"
    action = _base_action(
        plan, kind="repair", address=address, node="story-repair",
        role=role_id, role_address=str(member["address"]), attempt=1,
    )
    action.update({
        "node_address": base,
        "workspace": "isolated-worktree",
        "capabilities": ["agent:dispatch", "workspace:write"],
        "timeout_seconds": 900,
        "outputs": [{"id": "repair-candidate", "kind": "git-diff", "max_bytes": 500_000}],
        "inputs": [],
        "prompt_document": {
            "action_kind": "repair",
            "task": "Repair only the exact failed rubric findings while preserving prior evidence.",
            "repair_round": round_number,
        },
    })
    return action


def _phase_gate_due(plan: dict[str, object]) -> bool:
    selection = plan["selection"]
    scope = plan["scope"]
    assert isinstance(selection, dict) and isinstance(scope, dict)
    selected_story = str(selection["story"])
    phase = int(selection["phase"])
    scoped = set(str(item) for item in scope.get("story_ids", []))
    remaining = [
        item for item in plan.get("candidates", [])
        if isinstance(item, dict)
        and item.get("story") in scoped
        and int(item.get("phase", -1)) == phase
        and item.get("story") != selected_story
        and item.get("reason") not in {"already-done", "closed"}
    ]
    return not remaining


def _architecture_gate_base(
    plan: dict[str, object],
    gate: dict[str, object],
) -> str:
    selection = plan["selection"]
    assert isinstance(selection, dict)
    return (
        f"{_workflow_address(plan)}/architect-gate"
        f"/phase/{selection['phase']}/{gate['id']}"
    )


def _architecture_boundary_action(
    run_id: str,
    plan: dict[str, object],
    gate: dict[str, object],
    receipts: list[dict[str, object]],
    projection: dict[str, object],
    *,
    attempt: int = 1,
) -> dict[str, object]:
    base = _architecture_gate_base(plan, gate)
    prior = [
        item for item in receipts
        if not str(item.get("address", "")).startswith(base + "/")
    ]
    evidence = _evidence_from_receipts(prior)
    snapshot = {
        "kind": "delivery-workbench-architecture-boundary",
        "schema_version": PROGRAM_CONDUCTOR_SCHEMA_VERSION,
        "boundary": "phase",
        "program_run_id": run_id,
        "program": plan["program"]["slug"],  # type: ignore[index]
        "phase": plan["selection"]["phase"],  # type: ignore[index]
        "candidate_story": plan["selection"]["story"],  # type: ignore[index]
        "policy_bundle_hash": plan["program"]["policy_bundle_hash"],  # type: ignore[index]
        "roadmap_snapshot_hash": plan["roadmap"]["snapshot_hash"],  # type: ignore[index]
        "repository_hash": _sha(projection["expected_repository"]),
        "workflow_bundle_hash": plan["selection"]["workflow"]["bundle_hash"],  # type: ignore[index]
        "assignment_hash": plan["assignment"]["assignment_hash"],  # type: ignore[index]
        "gate": dict(gate),
        "receipt_lineage": [
            {
                "receipt_hash": item["receipt_hash"],
                "action_kind": item["action_kind"],
                "address": item["address"],
                "outcome": item["outcome"],
                "result": item["result"],
            }
            for item in prior
        ],
        "evidence": evidence,
        "open_obligations": [
            {
                "id": item["id"],
                "kind": item["kind"],
                "blocking": item["blocking"],
                "state": item["state"],
            }
            for item in projection.get("open_obligations", [])
            if isinstance(item, dict)
        ],
    }
    document = (
        f"# Phase {snapshot['phase']} architecture boundary\n\n"
        "```json\n"
        f"{canonical_json(snapshot)}\n"
        "```\n"
    ).encode("utf-8")
    _require(
        len(document) <= 500_000,
        "architecture boundary snapshot exceeds its 500000-byte ceiling",
    )
    digest = "sha256:" + hashlib.sha256(document).hexdigest()
    action = _base_action(
        plan,
        kind="architecture-boundary",
        address=f"{base}/boundary/attempt/{attempt}",
        node=str(gate["id"]),
        attempt=attempt,
    )
    action.update({
        "boundary": "phase",
        "gate": dict(gate),
        "snapshot": snapshot,
        "document": document.decode("utf-8"),
        "subject_hash": digest,
    })
    return action


def _architect_gate_action(
    root: Path,
    plan: dict[str, object],
    gate: dict[str, object],
    boundary_receipt: dict[str, object],
    *,
    attempt: int = 1,
) -> dict[str, object]:
    assignment = plan["assignment"]
    assert isinstance(assignment, dict)
    role = _role_document(assignment, duty=str(gate["role"]))
    _require(
        role.get("duty") == "master-architect",
        "phase architecture gate requires the master-architect duty",
    )
    member = _role_member(role)
    packet = role.get("packet_policy")
    _require(isinstance(packet, dict), "master architect packet policy is absent")
    context = packet.get("context")
    artifacts = packet.get("artifacts")
    _require(
        isinstance(context, dict) and "phase" in context.get("allow", []),
        "master architect cannot inspect phase context",
    )
    _require(
        isinstance(artifacts, dict) and "markdown" in artifacts.get("read", []),
        "master architect cannot read the phase boundary artifact",
    )
    rubric = compile_rubric(root, str(gate["rubric"]))
    _require(
        rubric["rubric"]["subject_type"] == "phase-snapshot",
        "phase architecture gate rubric must govern a phase-snapshot",
    )
    boundary_artifact = next(
        (
            item for item in boundary_receipt.get("artifacts", [])
            if isinstance(item, dict)
            and item.get("name") == "boundary-snapshot"
            and item.get("artifact_kind") == "markdown"
        ),
        None,
    )
    _require(
        isinstance(boundary_artifact, dict),
        "phase architecture boundary receipt lost its snapshot artifact",
    )
    boundary_data = _artifact_content(
        root,
        str(boundary_receipt["run_id"]),
        boundary_artifact,
    )
    try:
        boundary_document = boundary_data.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise DwError("phase architecture boundary is not UTF-8") from exc
    evidence = [{
        "kind": "markdown",
        "hash": boundary_artifact["sha256"],
        "ref": boundary_artifact["ref"],
    }]
    role_id = str(role["role"])
    base = _architecture_gate_base(plan, gate)
    action = _base_action(
        plan,
        kind="architect-verdict",
        address=f"{base}/review/role/{role_id}/attempt/{attempt}",
        node=str(gate["id"]),
        role=role_id,
        role_address=str(member["address"]),
        attempt=attempt,
    )
    action.update({
        "boundary": "phase",
        "gate": dict(gate),
        "workspace": "read-only",
        "capabilities": ["agent:dispatch", "verdict:issue"],
        "timeout_seconds": 900,
        "outputs": [{
            "id": "judgment",
            "kind": "verdict",
            "max_bytes": 100_000,
        }],
        "inputs": [{
            "name": "phase-boundary",
            "kind": "artifact",
            "ref": boundary_artifact["ref"],
            "sha256": boundary_artifact["sha256"],
            "required": True,
            "max_bytes": boundary_artifact["bytes"],
        }],
        "rubric": str(gate["rubric"]),
        "verdict_type": "architect-verdict",
        "subject_story": None,
        "prompt_document": {
            "action_kind": "architect-verdict",
            "task": (
                "Review the exact immutable phase boundary against the "
                "declared architecture rubric without modifying implementation."
            ),
            "boundary": "phase",
            "gate": dict(gate),
            "rubric": rubric["rubric"],
            "evidence": evidence,
            "boundary_receipt_hash": boundary_receipt["receipt_hash"],
            "boundary_document": boundary_document,
        },
    })
    return action


def _verdict_document_from_receipt(
    root: Path,
    run_id: str,
    receipt: dict[str, object],
) -> dict[str, object]:
    artifact = next(
        (
            item for item in receipt.get("artifacts", [])
            if isinstance(item, dict) and item.get("name") == "issued-verdict"
        ),
        None,
    )
    _require(isinstance(artifact, dict), "verdict receipt lost its issued document")
    try:
        value = json.loads(_artifact_content(root, run_id, artifact).decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise DwError("issued verdict artifact is malformed") from exc
    verdict = validate_verdict_document(value)
    reference = receipt.get("verdict")
    _require(
        isinstance(reference, dict)
        and reference.get("hash") == verdict["verdict_hash"]
        and reference.get("result") == verdict["result"]
        and reference.get("type") == verdict["verdict_type"],
        "verdict receipt reference changed",
    )
    return verdict


def _architecture_gate_policy(
    gate: dict[str, object],
    role_id: str,
    subject_type: str,
) -> dict[str, object]:
    return {
        "kind": "delivery-workbench-quality-gate",
        "schema_version": 1,
        "id": str(gate["id"]),
        "subject_type": subject_type,
        "mechanical_facts": [],
        "requirements": [{
            "id": "master-architect",
            "kind": "architect",
            "rubric": str(gate["rubric"]),
            "roles": [role_id],
            "method": "at_least",
            "threshold": 1,
            "veto_roles": [role_id],
            "meta_audit": {
                "mode": "none",
                "sample_size": 0,
                "rubric": None,
                "role": None,
            },
        }],
        "operator": "all",
        "threshold": 1,
        "dissent_policy": "preserve",
        "routes": {
            "pass": "advance",
            "fail": "block",
            "pending": "wait",
            "refused": "block",
        },
        "repair": {"max_rounds": 1, "on_exhausted": "block"},
    }


def _architecture_gate_evaluation_action(
    root: Path,
    run_id: str,
    plan: dict[str, object],
    gate: dict[str, object],
    architect_receipt: dict[str, object],
    *,
    now: datetime,
    attempt: int = 1,
) -> dict[str, object]:
    verdict = _verdict_document_from_receipt(
        root, run_id, architect_receipt
    )
    _require(
        verdict["verdict_type"] == "architect-verdict"
        and verdict["issuer"]["duty"] == "master-architect",
        "phase architecture gate received a non-architect verdict",
    )
    policy = _architecture_gate_policy(
        gate,
        str(verdict["issuer"]["role"]),
        str(verdict["subject"]["kind"]),
    )
    rubric = compile_rubric(root, str(gate["rubric"]))
    proof = evaluate_quality_gate(
        root,
        policy,
        verdict["subject"],
        {str(gate["rubric"]): rubric},
        [],
        [verdict],
        now=_format_time(now),
    )
    route = (
        "advance"
        if proof["result"] == "pass"
        else str(gate["on_fail"])
        if proof["result"] == "fail"
        else str(proof["route"])
    )
    base = _architecture_gate_base(plan, gate)
    action = _base_action(
        plan,
        kind="architecture-gate",
        address=f"{base}/evaluation/attempt/{attempt}",
        node=str(gate["id"]),
        role=str(verdict["issuer"]["role"]),
        role_address=str(verdict["issuer"]["address"]),
        attempt=attempt,
    )
    action.update({
        "boundary": "phase",
        "gate": dict(gate),
        "policy": policy,
        "proof": proof,
        "verdict": verdict,
        "subject_hash": str(proof["proof_hash"]),
        "route": route,
    })
    return action


def _architecture_checkpoint_action(
    plan: dict[str, object],
    gate: dict[str, object],
    evaluation: dict[str, object],
    *,
    attempt: int = 1,
) -> dict[str, object]:
    port = "phase-boundary"
    base = _architecture_gate_base(plan, gate)
    action = _base_action(
        plan,
        kind="checkpoint-request",
        address=f"{base}/checkpoint/{port}/attempt/{attempt}",
        node=str(gate["id"]),
        attempt=attempt,
    )
    action.update({
        "subject_hash": evaluation["subject_hash"],
        "request_port": port,
        "checkpoint_subject_kind": "program-architecture-checkpoint",
        "checkpoint_reason": (
            "A separately authorized principal must resolve the failed "
            "phase architecture gate."
        ),
    })
    return action


def _checkpoint_resolution(
    receipts: list[dict[str, object]],
    action: dict[str, object],
) -> dict[str, object] | None:
    """Return one validated public response to a derived checkpoint action."""
    receipt = _receipt_for(
        receipts,
        str(action["action_id"]),
        action_kind="checkpoint-request",
    )
    if receipt is None:
        return None
    _require(
        receipt.get("result") in {"approve", "reject"}
        and receipt.get("route") == receipt.get("result")
        and receipt.get("outcome") == "succeeded",
        "program checkpoint response receipt is invalid",
    )
    payload = receipt.get("payload")
    _require(
        isinstance(payload, dict)
        and payload.get("request_id") == receipt.get("claim_id")
        and payload.get("port") == action.get("request_port")
        and payload.get("decision") == receipt.get("result"),
        "program checkpoint response binding changed",
    )
    return receipt


def _derive_architecture_gate_step(
    root: Path,
    run_id: str,
    plan: dict[str, object],
    receipts: list[dict[str, object]],
    projection: dict[str, object],
    *,
    now: datetime,
) -> dict[str, object]:
    gates = [
        item for item in plan["selection"].get("phase_gates", [])  # type: ignore[union-attr]
        if isinstance(item, dict)
        and item.get("when") == "before-phase-complete"
    ]
    if not gates or not _phase_gate_due(plan):
        return {"completed": True, "required": False}
    order = _claim_order(projection)
    for gate in gates:
        base = _architecture_gate_base(plan, gate)
        prior_boundaries = sorted(
            [
                item
                for item in receipts
                if item.get("action_kind") == "architecture-boundary"
                and str(item.get("address", "")).startswith(
                    base + "/boundary/"
                )
            ],
            key=lambda item: int(item.get("attempt", 0)),
        )
        quality_receipts = [
            item
            for item in receipts
            if item.get("action_kind")
            in {"story-verification", "verdict"}
            and item.get("parent_action_id") is None
        ]
        attempt = (
            int(prior_boundaries[-1].get("attempt", 0))
            if prior_boundaries
            else 1
        )
        if (
            prior_boundaries
            and quality_receipts
            and max(
                _receipt_order(item, order)
                for item in quality_receipts
            )
            > _receipt_order(prior_boundaries[-1], order)
        ):
            attempt += 1
        boundary = _architecture_boundary_action(
            run_id,
            plan,
            gate,
            receipts,
            projection,
            attempt=attempt,
        )
        boundary_receipt = _receipt_for(
            receipts, str(boundary["action_id"]),
            action_kind="architecture-boundary",
        )
        if boundary_receipt is None:
            return {"completed": False, "required": True, "action": boundary}
        _require(
            boundary_receipt.get("result") == "frozen"
            and boundary_receipt.get("payload", {}).get("snapshot_hash")
            == boundary["subject_hash"],
            "phase architecture boundary receipt changed",
        )

        review = _architect_gate_action(
            root,
            plan,
            gate,
            boundary_receipt,
            attempt=attempt,
        )
        architect_receipt = _receipt_for(
            receipts, str(review["action_id"]),
            action_kind="architect-verdict",
        )
        if architect_receipt is None:
            return {"completed": False, "required": True, "action": review}
        if architect_receipt.get("outcome") != "succeeded":
            return {
                "completed": False,
                "required": True,
                "stop": f"architect-{architect_receipt.get('outcome')}",
            }

        evaluation = _architecture_gate_evaluation_action(
            root,
            run_id,
            plan,
            gate,
            architect_receipt,
            now=now,
            attempt=attempt,
        )
        gate_receipt = _receipt_for(
            receipts, str(evaluation["action_id"]),
            action_kind="architecture-gate",
        )
        if gate_receipt is None:
            return {
                "completed": False,
                "required": True,
                "action": evaluation,
            }
        _require(
            gate_receipt.get("payload", {}).get("proof_hash")
            == evaluation["subject_hash"]
            and gate_receipt.get("result")
            == evaluation["proof"]["result"]
            and gate_receipt.get("route") == evaluation["route"],
            "phase architecture gate receipt changed",
        )
        result = str(evaluation["proof"]["result"])
        if result == "pass":
            continue
        if result == "fail" and gate["on_fail"] == "checkpoint":
            checkpoint = _architecture_checkpoint_action(
                plan,
                gate,
                evaluation,
                attempt=attempt,
            )
            resolution = _checkpoint_resolution(receipts, checkpoint)
            if resolution is not None:
                if resolution["result"] == "approve":
                    continue
                return {
                    "completed": False,
                    "required": True,
                    "stop": "checkpoint-rejected",
                }
            return {
                "completed": False,
                "required": True,
                "action": checkpoint,
            }
        if result == "fail" and gate["on_fail"] == "abort":
            return {
                "completed": False,
                "required": True,
                "stop": "architect-abort",
            }
        if result == "fail":
            return {
                "completed": False,
                "required": True,
                "stop": "architect-veto",
            }
        return {
            "completed": False,
            "required": True,
            "stop": f"architect-gate-{result}",
        }
    return {"completed": True, "required": True}


_DELIBERATION_STAGE_KINDS = {
    "proposal": "debate-proposal",
    "critique": "debate-critique",
    "rebuttal": "debate-rebuttal",
    "judgment": "council-judgment",
    "meta-audit": "council-meta-audit",
    "architect-review": "council-architect-review",
}


def _initial_program_ledger_head(root: Path, run_id: str) -> str:
    events = _events(_run_dir(root.resolve(), run_id), run_id)
    _require(events[0]["event"] == "program_started", "program ledger has no stable start event")
    return _hash(events[0]["event_hash"], "program start ledger head")


def _deliberation_council(
    assignment: dict[str, object],
    node: dict[str, object],
) -> dict[str, object]:
    required = set(str(item) for item in node.get("participants", []))
    required.add(str(node.get("judge_role")))
    matches = [
        item for item in assignment.get("councils", [])
        if isinstance(item, dict)
        and set(str(role) for role in item.get("members", [])) == required
        and item.get("judge") == node.get("judge_role")
    ]
    _require(
        len(matches) == 1,
        "debate node did not resolve exactly one predeclared council",
    )
    return matches[0]


def _deliberation_plan(
    root: Path,
    run_id: str,
    context: dict[str, object],
    expanded: dict[str, object],
    receipts: list[dict[str, object]],
    projection: dict[str, object],
) -> tuple[dict[str, object], str]:
    plan = context["plan"]
    assignment = context["assignment"]
    instance = context["instance"]
    grant = context["grant"]
    assert isinstance(plan, dict) and isinstance(assignment, dict)
    assert isinstance(instance, dict) and isinstance(grant, dict)
    node = _node_policy(root, expanded)
    _require(node.get("type") == "debate", "deliberation plan requires a debate node")
    node_base = _lineage_address(
        _workflow_address(plan),
        str(instance["slug"]),
        str(expanded["address"]),
    )
    source_address = str(expanded["address"])
    compiled = json.loads(json.dumps(instance))
    debates = compiled.get("debates", [])
    matches = [
        item for item in debates
        if isinstance(item, dict) and item.get("address") == source_address
    ]
    _require(len(matches) == 1, "compiled debate address did not resolve uniquely")
    matches[0]["address"] = node_base
    council = _deliberation_council(assignment, node)
    frozen = [
        item for item in receipts
        if item.get("action_kind") == "debate-round"
        and str(item.get("address", "")).startswith(
            f"{node_base}/council/{council['id']}/round/"
        )
        and isinstance(item.get("payload"), dict)
        and isinstance(item["payload"].get("plan"), dict)
    ]
    if frozen:
        stored = frozen[0]["payload"]["plan"]
        assert isinstance(stored, dict)
        start_deliberation(stored, str(projection["issued_at"]))
        current_bindings = {
            "program_run_id": run_id,
            "phase": int(plan["selection"]["phase"]),  # type: ignore[index]
            "story": str(plan["selection"]["story"]),  # type: ignore[index]
            "workflow_address": node_base,
            "workflow_bundle_hash": compiled["bundle_hash"],
            "assignment_hash": assignment["assignment_hash"],
            "council_id": council["id"],
        }
        for field, expected in current_bindings.items():
            _require(
                stored[field] == expected,
                f"frozen deliberation plan {field} is stale",
            )
        _require(
            all(item["payload"]["plan"] == stored for item in frozen),
            "debate rounds disagree about their frozen deliberation plan",
        )
        return stored, node_base
    rubric_selector = str(plan["selection"]["rubrics"][0]["slug"])  # type: ignore[index]
    rubric = compile_rubric(root, rubric_selector)
    upstream = [
        item for item in receipts
        if not str(item.get("address", "")).startswith(node_base + "/")
    ]
    evidence = _evidence_from_receipts(upstream)
    _require(len(evidence) <= 100, "deliberation evidence exceeds its finite receipt ceiling")
    implementer = _role_member(_role_document(assignment, duty="implementer"))
    subject = {
        "kind": str(rubric["rubric"]["subject_type"]),
        "hash": _sha({"evidence": evidence}),
        "repository_hash": _sha(projection["expected_repository"]),
        "program_hash": grant["program"]["bundle_hash"],
        "program_run_id": run_id,
        "phase": int(plan["selection"]["phase"]),  # type: ignore[index]
        "story": str(plan["selection"]["story"]),  # type: ignore[index]
        "workflow_address": node_base,
        "assignment_hash": assignment["assignment_hash"],
        "assignment_generation": int(implementer["assignment_generation"]),
        "ledger_head": _initial_program_ledger_head(root, run_id),
        "implementer_principals": [implementer["principal_fingerprint"]],
    }
    deliberation = compile_deliberation_plan(
        compiled,
        assignment,
        council_id=str(council["id"]),
        program_run_id=run_id,
        phase=int(plan["selection"]["phase"]),  # type: ignore[index]
        story=str(plan["selection"]["story"]),  # type: ignore[index]
        rubric={
            "slug": rubric["rubric"]["slug"],
            "semantic_hash": rubric["semantic_hash"],
            "criteria": [
                item["id"] for item in rubric["rubric"]["criteria"]
            ],
        },
        subject=subject,
        evidence=evidence,
        debate_address=node_base,
    )
    return deliberation, node_base


def _deliberation_citation_refs(
    plan: dict[str, object],
    projection: dict[str, object],
) -> list[str]:
    refs = {
        str(item["ref"]) for item in plan.get("evidence", [])
        if isinstance(item, dict) and isinstance(item.get("ref"), str)
    }
    for round_state in projection.get("rounds", []):
        if not isinstance(round_state, dict):
            continue
        for artifact in round_state.get("artifacts", []):
            if isinstance(artifact, dict) and isinstance(artifact.get("content_ref"), str):
                refs.add(str(artifact["content_ref"]))
    return sorted(refs)


def _deliberation_agent_action(
    plan: dict[str, object],
    program_plan: dict[str, object],
    node: dict[str, object],
    expanded: dict[str, object],
    claim: dict[str, object],
    projection: dict[str, object],
) -> dict[str, object]:
    stage = str(claim["stage"])
    _require(stage in _DELIBERATION_STAGE_KINDS, "deliberation stage is unsupported")
    role_id = str(claim["role"])
    slot = int(claim["slot"])
    council_id = str(plan["council_id"])
    node_base = str(plan["workflow_address"])
    address = (
        f"{node_base}/council/{council_id}/round/{claim['round']}"
        f"/{stage}/seat/{role_id}/{slot}/role/{role_id}/attempt/1"
    )
    action = _base_action(
        program_plan,
        kind=_DELIBERATION_STAGE_KINDS[stage],
        address=address,
        node=str(node["id"]),
        role=role_id,
        role_address=str(claim["seat_address"]),
        attempt=1,
    )
    citation_refs = _deliberation_citation_refs(plan, projection)
    action.update({
        "node_address": node_base,
        "expanded_address": expanded["address"],
        "workspace": "read-only",
        "capabilities": ["agent:dispatch"],
        "timeout_seconds": int(node.get("round_timeout_seconds", 900)),
        "outputs": [{
            "id": "submission",
            "kind": "decision",
            "max_bytes": int(node.get("artifact_max_bytes", 100_000)),
        }],
        "inputs": [],
        "deliberation": {
            "plan_hash": plan["plan_hash"],
            "protocol_id": plan["protocol_id"],
            "claim_id": claim["claim_id"],
            "stage": stage,
            "round": claim["round"],
            "council_id": council_id,
        },
        "prompt_document": {
            "action_kind": _DELIBERATION_STAGE_KINDS[stage],
            "task": (
                "Return only the closed bounded deliberation submission for "
                "the assigned seat and stage."
            ),
            "deliberation_stage": stage,
            "deliberation_packet": claim["packet"],
            "citation_refs": citation_refs,
            "evidence": plan["evidence"],
        },
    })
    return action


def _deliberation_protocol(
    root: Path,
    run_id: str,
    context: dict[str, object],
    expanded: dict[str, object],
    receipts: list[dict[str, object]],
    projection: dict[str, object],
    *,
    now: datetime,
) -> dict[str, object]:
    plan, node_base = _deliberation_plan(
        root, run_id, context, expanded, receipts, projection
    )
    program_plan = context["plan"]
    assert isinstance(program_plan, dict)
    node = _node_policy(root, expanded)
    events = start_deliberation(plan, str(projection["issued_at"]))
    while True:
        before_claim = list(events)
        claimed = claim_next_deliberation(plan, events, _format_time(now))
        events = claimed["events"]
        pure_claim = claimed["claim"]
        if pure_claim is None:
            return {
                "plan": plan,
                "events": events,
                "projection": claimed["projection"],
                "claim": None,
                "action": None,
                "node_base": node_base,
                "node": node["id"],
            }
        action = _deliberation_agent_action(
            plan, program_plan, node, expanded, pure_claim,
            claimed["projection"],
        )
        receipt = _receipt_for(receipts, str(action["action_id"]))
        if receipt is None:
            key = f"program-conductor/{action['action_id']}/agent"
            active = _claim_by_key(projection, key)
            if active is not None:
                claimed = claim_next_deliberation(
                    plan, before_claim, str(active["reserved_at"])
                )
                events = claimed["events"]
                pure_claim = claimed["claim"]
                _require(isinstance(pure_claim, dict), "active debate claim no longer resolves")
                action = _deliberation_agent_action(
                    plan, program_plan, node, expanded, pure_claim,
                    claimed["projection"],
                )
            return {
                "plan": plan,
                "events": events,
                "projection": claimed["projection"],
                "claim": pure_claim,
                "action": action,
                "node_base": node_base,
                "node": node["id"],
            }
        payload = receipt.get("payload")
        _require(isinstance(payload, dict), "deliberation receipt payload disappeared")
        stored = payload.get("deliberation_submission")
        _require(
            isinstance(stored, dict)
            and set(stored) == {
                "plan_hash", "protocol_id", "claim_id", "claimed_at",
                "stage", "round", "submission", "pure_receipt_hash",
            },
            "deliberation receipt has an invalid exact submission binding",
        )
        expected_binding = {
            "plan_hash": plan["plan_hash"],
            "protocol_id": plan["protocol_id"],
            "claim_id": pure_claim["claim_id"],
            "stage": pure_claim["stage"],
            "round": pure_claim["round"],
        }
        observed_binding = {
            key: stored[key] for key in expected_binding
        }
        _require(
            observed_binding == expected_binding,
            "deliberation receipt belongs to a different protocol slot: "
            "changed " + ", ".join(
                key for key in expected_binding
                if expected_binding[key] != observed_binding[key]
            ),
        )
        claimed = claim_next_deliberation(
            plan, before_claim, str(stored["claimed_at"])
        )
        pure_claim = claimed["claim"]
        _require(isinstance(pure_claim, dict), "completed debate slot no longer resolves")
        recorded = record_deliberation_submission(
            plan,
            claimed["events"],
            str(pure_claim["claim_id"]),
            stored["submission"],  # type: ignore[arg-type]
            str(receipt["issued_at"]),
        )
        detail = recorded["events"][-1]["detail"]
        _require(
            detail["receipt_hash"] == stored["pure_receipt_hash"],
            "deliberation pure receipt hash changed during replay",
        )
        events = recorded["events"]


def _round_authorization_action(
    program_plan: dict[str, object],
    protocol: dict[str, object],
) -> dict[str, object]:
    pure_claim = protocol["claim"]
    plan = protocol["plan"]
    assert isinstance(pure_claim, dict) and isinstance(plan, dict)
    round_number = int(pure_claim["round"])
    address = (
        f"{protocol['node_base']}/council/{plan['council_id']}"
        f"/round/{round_number}/authorization/attempt/1"
    )
    action = _base_action(
        program_plan,
        kind="debate-round",
        address=address,
        node=str(protocol["node"]),
        attempt=1,
    )
    action.update({
        "subject_hash": _sha({
            "plan_hash": plan["plan_hash"], "round": round_number,
        }),
        "payload": {
            "plan_hash": plan["plan_hash"],
            "protocol_id": plan["protocol_id"],
            "council_id": plan["council_id"],
            "round": round_number,
            "plan": plan,
        },
    })
    return action


def _issuance_action(
    program_plan: dict[str, object],
    protocol: dict[str, object],
    *,
    kind: str,
    document: dict[str, object],
) -> dict[str, object]:
    plan = protocol["plan"]
    assert isinstance(plan, dict)
    round_number = int(document["round"])
    if kind == "council-decision":
        authority = document["authority"]
        assert isinstance(authority, dict)
        authority_kind = str(authority["kind"])
        suffix = f"authority/{authority_kind}"
        if authority_kind == "rule":
            suffix += f"/{authority['rule']}"
        elif authority_kind == "judge":
            decider = authority["decider"]
            assert isinstance(decider, dict)
            suffix += f"/seat/{decider['role']}/{decider['slot']}"
        else:
            suffix += f"/port/{authority['checkpoint_port']}"
        address = (
            f"{protocol['node_base']}/council/{plan['council_id']}"
            f"/decision/round/{round_number}/{suffix}/attempt/1"
        )
        role = (
            str(authority["decider"]["role"])
            if isinstance(authority.get("decider"), dict) else None
        )
        role_address = (
            str(authority["decider"]["address"])
            if isinstance(authority.get("decider"), dict) else None
        )
        content_hash = str(document["decision_hash"])
    else:
        stage = "meta-audit" if kind == "meta-verdict-issuance" else "architect-review"
        address = (
            f"{protocol['node_base']}/council/{plan['council_id']}"
            f"/{stage}/round/{round_number}/issuance/attempt/1"
        )
        role = str(document["role"])
        role_address = str(document["seat_address"])
        content_hash = str(document["receipt_hash"])
    action = _base_action(
        program_plan,
        kind=kind,
        address=address,
        node=str(protocol["node"]),
        role=role,
        role_address=role_address,
        attempt=1,
    )
    action.update({
        "document": document,
        "subject_hash": content_hash,
        "payload": {
            "plan_hash": plan["plan_hash"],
            "protocol_id": plan["protocol_id"],
            "council_id": plan["council_id"],
            "round": round_number,
            "pure_receipt_hash": content_hash,
        },
    })
    return action


def _obligation_action(
    program_plan: dict[str, object],
    protocol: dict[str, object],
    decision: dict[str, object],
    obligation: dict[str, object],
) -> dict[str, object]:
    address = (
        f"{protocol['node_base']}/council/{decision['council_id']}"
        f"/decision/round/{decision['round']}/obligation/{obligation['id']}"
        "/ingestion/attempt/1"
    )
    action = _base_action(
        program_plan,
        kind="obligation-ingestion",
        address=address,
        node=str(protocol["node"]),
        role=str(obligation["accountable_role"]),
        attempt=1,
    )
    action.update({
        "decision": decision,
        "obligation": obligation,
        "subject_hash": _sha({
            "decision_hash": decision["decision_hash"],
            "obligation": obligation,
        }),
    })
    return action


def _checkpoint_request_action(
    program_plan: dict[str, object],
    protocol: dict[str, object],
    decision: dict[str, object],
) -> dict[str, object]:
    authority = decision["authority"]
    assert isinstance(authority, dict)
    port = str(authority["checkpoint_port"])
    address = (
        f"{protocol['node_base']}/council/{decision['council_id']}"
        f"/decision/round/{decision['round']}/checkpoint/{port}/attempt/1"
    )
    action = _base_action(
        program_plan,
        kind="checkpoint-request",
        address=address,
        node=str(protocol["node"]),
        attempt=1,
    )
    action.update({
        "decision": decision,
        "subject_hash": str(decision["decision_hash"]),
        "request_port": port,
    })
    return action


def _derive_deliberation_step(
    root: Path,
    run_id: str,
    context: dict[str, object],
    expanded: dict[str, object],
    receipts: list[dict[str, object]],
    projection: dict[str, object],
    *,
    now: datetime,
) -> dict[str, object]:
    protocol = _deliberation_protocol(
        root, run_id, context, expanded, receipts, projection, now=now
    )
    plan = protocol["plan"]
    deliberation = protocol["projection"]
    program_plan = context["plan"]
    assert isinstance(plan, dict) and isinstance(deliberation, dict)
    assert isinstance(program_plan, dict)
    decision = deliberation.get("council_decision")
    if isinstance(decision, dict):
        issuance = _issuance_action(
            program_plan, protocol, kind="council-decision",
            document=decision,
        )
        receipt = _receipt_for(receipts, str(issuance["action_id"]))
        if receipt is None:
            return {"action": issuance, "completed": False, "stop": None}
        reference = receipt.get("decision")
        _require(
            isinstance(reference, dict)
            and reference.get("hash") == decision["decision_hash"],
            "issued council decision receipt changed",
        )
        durable_ids = {
            str(item["id"]) for item in projection.get("obligations", [])
            if isinstance(item, dict)
        }
        for obligation in decision["obligations"]:
            if str(obligation["id"]) not in durable_ids:
                return {
                    "action": _obligation_action(
                        program_plan, protocol, decision, obligation
                    ),
                    "completed": False,
                    "stop": None,
                }
    meta = deliberation.get("meta_verdict")
    if isinstance(meta, dict):
        issuance = _issuance_action(
            program_plan, protocol, kind="meta-verdict-issuance",
            document=meta,
        )
        receipt = _receipt_for(receipts, str(issuance["action_id"]))
        if receipt is None:
            return {"action": issuance, "completed": False, "stop": None}
        reference = receipt.get("verdict")
        _require(
            isinstance(reference, dict)
            and reference.get("hash") == meta["receipt_hash"],
            "issued meta-verdict receipt changed",
        )
    architect = deliberation.get("architect_verdict")
    if isinstance(architect, dict):
        issuance = _issuance_action(
            program_plan, protocol, kind="architect-verdict-issuance",
            document=architect,
        )
        receipt = _receipt_for(receipts, str(issuance["action_id"]))
        if receipt is None:
            return {"action": issuance, "completed": False, "stop": None}
        reference = receipt.get("verdict")
        _require(
            isinstance(reference, dict)
            and reference.get("hash") == architect["receipt_hash"],
            "issued architect-verdict receipt changed",
        )
    pending = protocol.get("action")
    if isinstance(pending, dict):
        round_action = _round_authorization_action(program_plan, protocol)
        if _receipt_for(receipts, str(round_action["action_id"])) is None:
            return {"action": round_action, "completed": False, "stop": None}
        return {"action": pending, "completed": False, "stop": None}
    route = deliberation.get("route")
    if not isinstance(route, dict):
        return {
            "action": None, "completed": False,
            "stop": "deliberation-no-route",
        }
    if route.get("kind") == "action":
        if route.get("target") == "checkpoint":
            _require(isinstance(decision, dict), "checkpoint route has no council decision")
            checkpoint = _checkpoint_request_action(
                program_plan, protocol, decision
            )
            resolution = _checkpoint_resolution(receipts, checkpoint)
            if resolution is not None:
                if resolution["result"] == "approve":
                    return {
                        "action": None,
                        "completed": True,
                        "stop": None,
                        "result": "approved",
                        "route": {"kind": "terminal", "target": "complete"},
                    }
                return {
                    "action": None,
                    "completed": False,
                    "stop": "checkpoint-rejected",
                }
            return {
                "action": checkpoint,
                "completed": False,
                "stop": None,
            }
        return {
            "action": None,
            "completed": False,
            "stop": f"route-{route.get('target')}",
        }
    return {
        "action": None,
        "completed": True,
        "stop": None,
        "result": {
            "advance": "consensus",
            "quorum-lost": "quorum_lost",
        }.get(
            str(deliberation.get("final_result")),
            str(deliberation.get("final_result")),
        ),
        "route": route,
    }


def _loop_contexts(
    expanded_address: str,
    loops: list[dict[str, object]],
) -> list[dict[str, object]]:
    contexts = [
        loop for loop in loops
        if expanded_address.startswith(str(loop["address"]) + "/round/{round}/")
    ]
    contexts.sort(key=lambda item: len(str(item["address"])))
    return contexts


def _instantiate_loop_rounds(
    expanded_address: str,
    loops: list[dict[str, object]],
    rounds: dict[str, int],
) -> str | None:
    instantiated = expanded_address
    for loop in _loop_contexts(expanded_address, loops):
        loop_address = str(loop["address"])
        round_number = rounds.get(loop_address)
        if round_number is None:
            return None
        instantiated = instantiated.replace("{round}", str(round_number), 1)
    return instantiated


def _loop_lineage_address(
    workflow_address: str,
    instance_slug: str,
    expanded_address: str,
) -> str:
    node_address = _lineage_address(
        workflow_address, instance_slug, expanded_address
    )
    marker = "/node/"
    _require(marker in node_address, "compiled loop address lost its node lineage")
    prefix, loop_node = node_address.rsplit(marker, 1)
    _require("/" not in loop_node, "compiled loop node address is ambiguous")
    return f"{prefix}/loop/{loop_node}"


def _loop_round_receipts(
    receipts: list[dict[str, object]],
    loop_address: str,
    *,
    loop_lineage: str,
    max_rounds: int,
) -> list[dict[str, object]]:
    found = sorted(
        [
            receipt for receipt in receipts
            if receipt.get("action_kind") == "loop-round"
            and isinstance(receipt.get("payload"), dict)
            and receipt["payload"].get("loop_address") == loop_address
            and receipt["payload"].get("loop_lineage") == loop_lineage
        ],
        key=lambda item: int(item.get("payload", {}).get("round", 0)),
    )
    rounds = [
        int(item.get("payload", {}).get("round", 0)) for item in found
    ]
    _require(
        rounds == list(range(1, len(rounds) + 1)),
        "loop-round receipts are not contiguous",
    )
    _require(
        len(found) <= max_rounds,
        "loop-round receipts exceed the compiled maximum",
    )
    for receipt in found:
        payload = receipt["payload"]
        assert isinstance(payload, dict)
        _require(
            payload.get("max_rounds") == max_rounds,
            "loop-round receipt maximum differs from compiled policy",
        )
        _require(
            payload.get("result") in {"continue", "success", "exhausted"}
            and receipt.get("result") == payload.get("result"),
            "loop-round receipt result is invalid",
        )
    return found


def _round_source_receipts(
    receipts: list[dict[str, object]],
    *,
    round_prefix: str,
    source_node: str,
) -> list[dict[str, object]]:
    return sorted(
        [
            receipt for receipt in receipts
            if receipt.get("node") == source_node
            and str(receipt.get("address", "")).startswith(
                round_prefix + "/"
            )
            and receipt.get("parent_action_id") is None
        ],
        key=lambda item: (
            int(item.get("attempt", 0)),
            str(item.get("address", "")),
            str(item.get("action_kind", "")),
        ),
    )


def _loop_result_is_green(value: object) -> bool:
    if value is True:
        return True
    return isinstance(value, str) and value in (
        GREEN_RESULTS
        | {
            "advance", "complete", "consensus", "green",
            "success", "succeeded",
        }
    )


def _loop_predicate_observation(
    root: Path,
    run_id: str,
    *,
    loop_node: dict[str, object],
    loop_base: str,
    round_number: int,
    receipts: list[dict[str, object]],
) -> dict[str, object] | None:
    predicate = loop_node["until"]
    _require(isinstance(predicate, dict), "compiled loop predicate disappeared")
    source = str(predicate["source"])
    source_node, separator, output_id = source.partition(".")
    child_slug = str(loop_node["workflow"])
    round_prefix = (
        f"{loop_base}/round/{round_number}/subflow/{child_slug}"
    )
    candidates = _round_source_receipts(
        receipts,
        round_prefix=round_prefix,
        source_node=source_node,
    )
    kind = str(predicate["kind"])
    expected_kinds = {
        "check-result": {"check"},
        "verdict-result": {
            "verdict", "story-verification", "meta-verdict",
            "architect-verdict",
        },
        "decision-result": {
            "council-decision", "checkpoint-request",
        },
    }
    if kind != "artifact-valid":
        candidates = [
            item for item in candidates
            if item.get("action_kind") in expected_kinds.get(kind, set())
        ]
    if not candidates:
        return None
    producer = candidates[-1]
    value: object = producer.get("result")
    valid = True
    artifact_summary: dict[str, object] | None = None
    if kind == "artifact-valid":
        _require(
            bool(separator) and bool(output_id),
            "artifact-valid predicate lost its node.output source",
        )
        artifacts = [
            artifact for artifact in producer.get("artifacts", [])
            if isinstance(artifact, dict)
            and artifact.get("name") == output_id
        ]
        _require(
            len(artifacts) <= 1,
            "loop predicate source produced duplicate artifacts",
        )
        if not artifacts:
            return None
        artifact = artifacts[0]
        valid = artifact.get("valid") is True
        if artifact.get("artifact_kind") == "mechanical-fact":
            try:
                fact_raw = json.loads(
                    _artifact_content(root, run_id, artifact).decode("utf-8")
                )
            except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                raise DwError(
                    "loop mechanical-fact predicate content is malformed"
                ) from exc
            fact = validate_mechanical_fact(fact_raw)
            value = fact["result"]
        artifact_summary = {
            "name": artifact["name"],
            "kind": artifact["artifact_kind"],
            "hash": artifact["sha256"],
            "ref": artifact["ref"],
            "valid": valid,
        }
    _require(
        isinstance(value, (str, int, bool, type(None)))
        and not isinstance(value, float),
        "loop predicate observed a non-scalar result",
    )
    green = valid and _loop_result_is_green(value)
    return {
        "kind": kind,
        "source": source,
        "producer_action_id": producer["action_id"],
        "producer_receipt_hash": producer["receipt_hash"],
        "producer_outcome": producer["outcome"],
        "value": value,
        "valid": valid,
        "green": green,
        "artifact": artifact_summary,
    }


def _loop_predicate_matches(
    predicate: dict[str, object],
    observation: dict[str, object],
) -> bool:
    operator = str(predicate["operator"])
    if operator == "valid":
        return observation["valid"] is True
    if operator == "green":
        return observation["green"] is True
    expected = predicate.get("value")
    observed = observation.get("value")
    if operator == "equals":
        return type(observed) is type(expected) and observed == expected
    if operator == "not-equals":
        return not (
            type(observed) is type(expected) and observed == expected
        )
    if operator == "contains":
        return (
            isinstance(observed, str)
            and isinstance(expected, str)
            and expected in observed
        )
    raise DwError(f"unsupported compiled loop predicate operator: {operator}")


def _loop_carried_artifacts(
    loop_node: dict[str, object],
    *,
    loop_base: str,
    round_number: int,
    receipts: list[dict[str, object]],
) -> list[dict[str, object]]:
    child_slug = str(loop_node["workflow"])
    round_prefix = (
        f"{loop_base}/round/{round_number}/subflow/{child_slug}"
    )
    carried: list[dict[str, object]] = []
    for reference in loop_node.get("carry", []):
        _require(
            isinstance(reference, str) and "." in reference,
            "compiled loop carry reference is invalid",
        )
        source_node, output_id = reference.split(".", 1)
        candidates = _round_source_receipts(
            receipts,
            round_prefix=round_prefix,
            source_node=source_node,
        )
        matches = [
            artifact
            for receipt in candidates
            for artifact in receipt.get("artifacts", [])
            if isinstance(artifact, dict)
            and artifact.get("name") == output_id
            and artifact.get("valid") is True
        ]
        _require(
            len(matches) == 1,
            f"loop carry source {reference!r} did not resolve uniquely",
        )
        artifact = matches[0]
        carried.append({
            "source": reference,
            "kind": artifact["artifact_kind"],
            "hash": artifact["sha256"],
            "ref": artifact["ref"],
        })
    return carried


def _loop_round_action(
    root: Path,
    run_id: str,
    plan: dict[str, object],
    loop_spec: dict[str, object],
    loop_node: dict[str, object],
    loop_base: str,
    round_number: int,
    receipts: list[dict[str, object]],
) -> dict[str, object] | None:
    observation = _loop_predicate_observation(
        root,
        run_id,
        loop_node=loop_node,
        loop_base=loop_base,
        round_number=round_number,
        receipts=receipts,
    )
    if observation is None:
        return None
    predicate = loop_node["until"]
    assert isinstance(predicate, dict)
    matched = _loop_predicate_matches(predicate, observation)
    maximum = int(loop_node["max_rounds"])
    if matched:
        result = "success"
        route = loop_node["on_success"]
    elif round_number >= maximum:
        result = "exhausted"
        route = loop_node["on_exhausted"]
    else:
        result = "continue"
        route = {"kind": "round", "target": round_number + 1}
    payload = {
        "loop_address": str(loop_spec["address"]),
        "loop_lineage": loop_base,
        "workflow": str(loop_node["workflow"]),
        "purpose": str(loop_node["purpose"]),
        "round": round_number,
        "max_rounds": maximum,
        "predicate": predicate,
        "observation": observation,
        "matched": matched,
        "carried_artifacts": _loop_carried_artifacts(
            loop_node,
            loop_base=loop_base,
            round_number=round_number,
            receipts=receipts,
        ),
        "result": result,
        "route": route,
    }
    address = f"{loop_base}/round/{round_number}/predicate/attempt/1"
    action = _base_action(
        plan,
        kind="loop-round",
        address=address,
        node=str(loop_node["id"]),
        attempt=round_number,
    )
    action.update({
        "subject_hash": _sha(payload),
        "payload": payload,
        "local_result": result,
        "local_route": route,
    })
    return action


def derive_program_frontier(
    root: Path,
    run_id: str,
    *,
    driver_config: object | None = None,
    now: str | datetime | None = None,
    _ignore_active: bool = False,
) -> dict[str, object]:
    """Derive one stable next act without reserving or dispatching it."""
    root = root.resolve()
    observed = _time(now, "now")
    config = load_driver_config(root, driver_config)
    replayed = replay_program_conductor(root, run_id, now=observed)
    projection = replayed["authority"]
    all_receipts = replayed["receipts"]
    if projection["state"] != "running":
        return {
            "kind": PROGRAM_FRONTIER_KIND,
            "schema_version": PROGRAM_CONDUCTOR_SCHEMA_VERSION,
            "run_id": run_id,
            "state": projection["state"],
            "terminal": projection["state"] in TERMINAL_AUTHORITY_STATES,
            "checkpoint": projection["state"] == "checkpoint",
            "stop": "authority-not-running",
            "next_actions": [],
            "lineage": None,
            **_obligation_frontier(projection),
            "starts_work": False,
            "writes_state": False,
        }
    if replayed["active_conductor_claims"] and not _ignore_active:
        active = replayed["active_conductor_claims"]
        return {
            "kind": PROGRAM_FRONTIER_KIND,
            "schema_version": PROGRAM_CONDUCTOR_SCHEMA_VERSION,
            "run_id": run_id,
            "state": "reconciling",
            "terminal": False,
            "checkpoint": False,
            "stop": None,
            "next_actions": [],
            "active_claim_ids": [item["claim_id"] for item in active],
            "lineage": None,
            **_obligation_frontier(projection),
            "starts_work": False,
            "writes_state": False,
        }
    context = _current_program_context(root, run_id, projection, config)
    plan = context["plan"]
    instance = context["instance"]
    _require(isinstance(plan, dict), "program context lost its pure plan")
    plan["_frontier_obligations"] = _obligation_frontier(projection)
    if (
        projection.get("blocking_obligations")
        and not (_ignore_active and replayed["active_conductor_claims"])
    ):
        selection = plan.get("selection")
        return {
            "kind": PROGRAM_FRONTIER_KIND,
            "schema_version": PROGRAM_CONDUCTOR_SCHEMA_VERSION,
            "run_id": run_id,
            "state": "stopped",
            "terminal": False,
            "checkpoint": False,
            "stop": "blocking-obligation-open",
            "next_actions": [],
            "lineage": (
                {
                    "program": plan["program"]["slug"],  # type: ignore[index]
                    "phase": selection["phase"],
                    "story": selection["story"],
                    "workflow": _workflow_address(plan),
                }
                if isinstance(selection, dict)
                else {
                    "program": plan["program"]["slug"],  # type: ignore[index]
                    "phase": None,
                    "story": None,
                    "workflow": None,
                }
            ),
            **_obligation_frontier(projection),
            "starts_work": False,
            "writes_state": False,
        }
    if plan.get("selection") is None:
        action = _scope_completion_action(
            context["grant"], plan, projection  # type: ignore[arg-type]
        )
        return {
            "kind": PROGRAM_FRONTIER_KIND,
            "schema_version": PROGRAM_CONDUCTOR_SCHEMA_VERSION,
            "run_id": run_id,
            "state": "ready",
            "terminal": False,
            "checkpoint": False,
            "stop": None,
            "next_actions": [action],
            "lineage": {
                "program": plan["program"]["slug"],  # type: ignore[index]
                "phase": None,
                "story": None,
                "workflow": action["workflow_address"],
            },
            **_obligation_frontier(projection),
            "starts_work": False,
            "writes_state": False,
        }
    _require(
        isinstance(instance, dict),
        "selected program workflow instance disappeared",
    )
    receipts = _receipts_for_plan(all_receipts, plan)
    workflow_address = _workflow_address(plan)
    outward = _derive_program_outward_step(
        root,
        run_id,
        context,
        projection,
        all_receipts,
        receipts,
    )
    if outward.get("stop") is not None:
        return _frontier_result(
            run_id,
            plan,
            "stopped",
            [],
            stop=str(outward["stop"]),
        )
    outward_action = outward.get("action")
    if isinstance(outward_action, dict):
        return _frontier_result(
            run_id, plan, "ready", [outward_action]
        )
    selection_action = _base_action(
        plan, kind="selection",
        address=f"{workflow_address}/selection/attempt/1",
    )
    if _receipt_for(receipts, str(selection_action["action_id"])) is None:
        selection_action["payload"] = plan["selection"]
        selection_action["subject_hash"] = _sha(plan["selection"])
        return _frontier_result(run_id, plan, "ready", [selection_action])
    assignment_action = _base_action(
        plan, kind="assignment",
        address=f"{workflow_address}/assignment/attempt/1",
    )
    if _receipt_for(receipts, str(assignment_action["action_id"])) is None:
        assignment_action["payload"] = {
            "assignment_hash": plan["assignment"]["assignment_hash"],  # type: ignore[index]
            "roster_hash": plan["assignment"]["roster_hash"],  # type: ignore[index]
            "separation": plan["assignment"]["separation"],  # type: ignore[index]
        }
        assignment_action["subject_hash"] = str(plan["assignment"]["assignment_hash"])  # type: ignore[index]
        return _frontier_result(run_id, plan, "ready", [assignment_action])

    expanded_nodes = list(instance.get("expanded_nodes", []))
    loops = [
        item for item in instance.get("loops", [])
        if isinstance(item, dict)
    ]
    loop_by_address = {
        str(item["address"]): item for item in loops
    }
    _require(
        len(loop_by_address) == len(loops),
        "compiled workflow contains duplicate loop addresses",
    )
    explicit_verdict = False
    route_edges = [
        item for item in instance.get("routes", [])
        if isinstance(item, dict)
    ]
    virtual_results: dict[str, str] = {}
    loop_rounds: dict[str, int] = {}
    loop_states: dict[str, str] = {}
    loop_candidates: list[
        tuple[dict[str, object], dict[str, object], str, int]
    ] = []
    pending_structural: set[str] = set()
    claim_order = _claim_order(projection)

    def lineage_for(expanded_address: object) -> str:
        if not isinstance(expanded_address, str):
            return ""
        instantiated = _instantiate_loop_rounds(
            expanded_address, loops, loop_rounds
        )
        if instantiated is None:
            return ""
        if expanded_address in loop_by_address:
            return _loop_lineage_address(
                workflow_address,
                str(instance["slug"]),
                instantiated,
            )
        return _lineage_address(
            workflow_address, str(instance["slug"]), instantiated
        )

    def observed_outcome(receipt: dict[str, object]) -> object:
        if receipt.get("action_kind") in {
            "verdict", "story-verification", "check",
            "council-decision", "loop-round",
        }:
            return receipt.get("result")
        return (
            "success"
            if receipt.get("outcome") == "succeeded"
            else "failure"
        )

    def latest_main_receipt(
        address: str,
    ) -> dict[str, object] | None:
        matches = [
            receipt
            for receipt in receipts
            if str(receipt.get("address", "")).startswith(address + "/")
            and receipt.get("parent_action_id") is None
        ]
        if not matches:
            return None
        return max(
            matches,
            key=lambda item: (
                _receipt_order(item, claim_order),
                int(item.get("attempt", 0)),
            ),
        )

    def activation_sources(
        expanded: dict[str, object],
    ) -> list[str]:
        sources = [
            lineage_for(item) for item in expanded.get("needs", [])
        ]
        if expanded.get("activation") == "route":
            for edge in route_edges:
                if (
                    edge.get("kind") != "node"
                    or edge.get("target") != expanded.get("address")
                ):
                    continue
                source = lineage_for(edge.get("source"))
                latest = latest_main_receipt(source) if source else None
                if (
                    latest is not None
                    and observed_outcome(latest) == edge.get("outcome")
                ):
                    sources.append(source)
        return [item for item in sources if item]

    def dependency_satisfied(need: str) -> bool:
        if not need:
            return False
        if need in virtual_results:
            return virtual_results[need] == "success"
        if need in pending_structural:
            return False
        return any(
            receipt.get("address", "").startswith(need + "/")
            and receipt.get("outcome") == "succeeded"
            and receipt.get("parent_action_id") is None
            for receipt in receipts
        )

    def is_activated(expanded: dict[str, object]) -> bool:
        needs = [
            lineage_for(item) for item in expanded.get("needs", [])
        ]
        if expanded.get("activation") != "route":
            return all(dependency_satisfied(need) for need in needs)
        incoming = [
            edge for edge in route_edges
            if edge.get("kind") == "node"
            and edge.get("target") == expanded.get("address")
        ]
        for edge in incoming:
            source = lineage_for(edge.get("source"))
            if not source or source in pending_structural:
                continue
            if source in virtual_results:
                if virtual_results[source] == edge.get("outcome"):
                    return True
                continue
            source_receipts = [
                receipt for receipt in receipts
                if receipt.get("address", "").startswith(source + "/")
                and receipt.get("parent_action_id") is None
            ]
            if source_receipts:
                latest = max(
                    source_receipts,
                    key=lambda item: int(item.get("attempt", 0)),
                )
                if observed_outcome(latest) == edge.get("outcome"):
                    return True
        return False

    for expanded in expanded_nodes:
        if not isinstance(expanded, dict):
            continue
        expanded_template = str(expanded["address"])
        contexts = _loop_contexts(expanded_template, loops)
        if any(
            loop_states.get(str(loop["address"])) != "active"
            for loop in contexts
        ):
            continue
        instantiated_address = _instantiate_loop_rounds(
            expanded_template, loops, loop_rounds
        )
        if instantiated_address is None:
            continue
        runtime_expanded = {
            **expanded,
            "address": instantiated_address,
        }
        node = _node_policy(root, expanded)
        node_type = str(node["type"])
        if not is_activated(expanded):
            if node_type == "loop":
                loop_states[expanded_template] = "inactive"
            continue
        if node_type == "subflow":
            # Executable child claims keep the subflow segment. A typed loop
            # below receives its own structural receipt rather than borrowing
            # this parent's identity.
            continue
        if node_type == "loop":
            loop_spec = loop_by_address.get(expanded_template)
            _require(
                isinstance(loop_spec, dict),
                "compiled loop node has no finite loop proof",
            )
            loop_base = _loop_lineage_address(
                workflow_address,
                str(instance["slug"]),
                instantiated_address,
            )
            maximum = int(node["max_rounds"])
            prior_rounds = _loop_round_receipts(
                receipts,
                expanded_template,
                loop_lineage=loop_base,
                max_rounds=maximum,
            )
            if prior_rounds:
                latest_round = prior_rounds[-1]
                result = str(latest_round["result"])
                payload = latest_round["payload"]
                assert isinstance(payload, dict)
                expected_route = (
                    node["on_success"]
                    if result == "success"
                    else (
                        node["on_exhausted"]
                        if result == "exhausted"
                        else {
                            "kind": "round",
                            "target": len(prior_rounds) + 1,
                        }
                    )
                )
                _require(
                    payload.get("route") == expected_route,
                    "loop-round receipt route differs from compiled policy",
                )
                if result in {"success", "exhausted"}:
                    loop_states[expanded_template] = result
                    virtual_results[loop_base] = result
                    if (
                        isinstance(expected_route, dict)
                        and expected_route.get("kind") == "action"
                    ):
                        return _frontier_result(
                            run_id,
                            plan,
                            "stopped",
                            [],
                            stop=f"route-{expected_route.get('target')}",
                        )
                    continue
                _require(
                    result == "continue"
                    and len(prior_rounds) < maximum,
                    "loop continuation exceeds its compiled maximum",
                )
                current_round = len(prior_rounds) + 1
            else:
                current_round = 1
            loop_rounds[expanded_template] = current_round
            loop_states[expanded_template] = "active"
            pending_structural.add(loop_base)
            loop_candidates.append(
                (loop_spec, node, loop_base, current_round)
            )
            continue
        if node_type in {"verdict", "panel"}:
            explicit_verdict = True
        node_base = lineage_for(expanded_template)
        _require(
            bool(node_base),
            "executable node lost its active loop lineage",
        )
        if any(
            loop_states.get(str(loop["address"])) != "active"
            for loop in contexts
        ):
            # A structural parent may have completed while deriving a nested
            # path earlier in this same pure pass.
            continue
        if node_type == "debate":
            deliberation = _derive_deliberation_step(
                root,
                run_id,
                context,
                runtime_expanded,
                receipts,
                projection,
                now=observed,
            )
            action = deliberation.get("action")
            if isinstance(action, dict):
                return _frontier_result(run_id, plan, "ready", [action])
            if deliberation.get("stop") is not None:
                return _frontier_result(
                    run_id, plan, "stopped", [],
                    stop=str(deliberation["stop"]),
                )
            _require(
                deliberation.get("completed") is True
                and isinstance(deliberation.get("result"), str),
                "completed deliberation lost its governed result",
            )
            virtual_results[node_base] = str(deliberation["result"])
            continue
        if node_type not in {"agent", "verdict", "panel", "check", "collect"}:
            return _frontier_result(
                run_id, plan, "stopped", [],
                stop=f"unsupported-workflow-node:{node_type}",
            )
        expected_kind = "verdict" if node_type in {"verdict", "panel"} else node_type
        prior_attempts = sorted(
            [
                item for item in receipts
                if item.get("action_kind") == expected_kind
                and item.get("address", "").startswith(node_base + "/")
                and item.get("parent_action_id") is None
            ],
            key=lambda item: int(item.get("attempt", 0)),
        )
        attempt = 1
        if prior_attempts:
            prior = prior_attempts[-1]
            failed = prior.get("outcome") != "succeeded"
            red = expected_kind == "verdict" and prior.get("result") not in GREEN_RESULTS
            if not failed and not red:
                prior_order = _receipt_order(prior, claim_order)
                upstream = [
                    latest_main_receipt(address)
                    for address in activation_sources(expanded)
                ]
                if any(
                    item is not None
                    and _receipt_order(item, claim_order) > prior_order
                    for item in upstream
                ):
                    # A standing nudge may have repeated an upstream agent.
                    # Re-run only the already-declared downstream DAG path;
                    # the nudge never manufactures a new node or route.
                    attempt = int(prior.get("attempt", 0)) + 1
                else:
                    continue
            if failed or red:
                controlling_loop = contexts[-1] if contexts else None
                controlled_node: str | None = None
                if isinstance(controlling_loop, dict):
                    loop_parent = next(
                        (
                            item for item in expanded_nodes
                            if isinstance(item, dict)
                            and item.get("address")
                            == controlling_loop.get("address")
                        ),
                        None,
                    )
                    if isinstance(loop_parent, dict):
                        loop_policy = _node_policy(root, loop_parent)
                        controlled_node = str(
                            loop_policy["until"]["source"]
                        ).split(".", 1)[0]
                if controlled_node == str(node["id"]):
                    # A typed red/failed predicate source is a completed loop
                    # observation. The loop policy, not the child's ordinary
                    # failure route, decides whether to continue or exhaust.
                    continue
                route = (
                    node.get(
                        "on_failure",
                        {"kind": "action", "target": "block"},
                    )
                    if failed
                    else node.get("routes", {}).get(  # type: ignore[union-attr]
                        str(prior.get("result")),
                        {"kind": "action", "target": "block"},
                    )
                )
                maximum = int(node.get("max_attempts", 1))
                if (
                    isinstance(route, dict)
                    and route.get("kind") == "action"
                    and route.get("target") in {"retry", "repair"}
                    and int(prior.get("attempt", 0)) < maximum
                ):
                    attempt = int(prior["attempt"]) + 1
                else:
                    return _frontier_result(
                        run_id, plan, "stopped", [],
                        stop=(
                            "route-"
                            + str(
                                route.get("target", "block")
                                if isinstance(route, dict)
                                else "block"
                            )
                        ),
                    )
        action = (
            _local_workflow_action(
                root,
                plan,
                instance,
                runtime_expanded,
                attempt=attempt,
            )
            if node_type in {"check", "collect"}
            else _workflow_node_action(
                root,
                plan,
                instance,
                runtime_expanded,
                receipts,
                attempt=attempt,
            )
        )
        if not prior_attempts or attempt > int(prior_attempts[-1].get("attempt", 0)):
            return _frontier_result(run_id, plan, "ready", [action])

    if loop_candidates:
        for loop_spec, loop_node, loop_base, round_number in reversed(
            loop_candidates
        ):
            action = _loop_round_action(
                root,
                run_id,
                plan,
                loop_spec,
                loop_node,
                loop_base,
                round_number,
                receipts,
            )
            if action is not None:
                return _frontier_result(
                    run_id, plan, "ready", [action]
                )
        innermost = loop_candidates[-1][1]
        return _frontier_result(
            run_id,
            plan,
            "stopped",
            [],
            stop=f"loop-round-incomplete:{innermost['id']}",
        )

    if not explicit_verdict:
        verifications = sorted(
            [item for item in receipts if item.get("action_kind") == "story-verification"],
            key=lambda item: int(item.get("attempt", 0)),
        )
        repairs = sorted(
            [item for item in receipts if item.get("action_kind") == "repair"],
            key=lambda item: int(item.get("payload", {}).get("repair_round", item.get("attempt", 0))),
        )
        if not verifications:
            return _frontier_result(
                run_id, plan, "ready",
                [_synthetic_verifier_action(root, plan, receipts, attempt=1)],
            )
        prior = verifications[-1]
        if prior.get("outcome") == "succeeded" and prior.get("result") in GREEN_RESULTS:
            prior_order = _receipt_order(prior, claim_order)
            evidence_work = [
                item
                for item in receipts
                if item.get("parent_action_id") is None
                and item.get("action_kind") in {
                    "agent",
                    "check",
                    "collect",
                    "repair",
                    "loop-round",
                    "council-decision",
                }
            ]
            if any(
                _receipt_order(item, claim_order) > prior_order
                for item in evidence_work
            ):
                return _frontier_result(
                    run_id,
                    plan,
                    "ready",
                    [
                        _synthetic_verifier_action(
                            root,
                            plan,
                            receipts,
                            attempt=int(prior.get("attempt", 0)) + 1,
                        )
                    ],
                )
        elif prior.get("result") in {"needs-repair", "fail"} or prior.get("outcome") == "failed":
            round_number = len(verifications)
            repair = next(
                (item for item in repairs if item.get("payload", {}).get("repair_round") == round_number),
                None,
            )
            remaining_repairs = int(projection["budgets"]["max_repairs_per_story"]["remaining"])
            if repair is None:
                if remaining_repairs <= 0:
                    return _frontier_result(
                        run_id, plan, "stopped", [], stop="repair-exhausted"
                    )
                return _frontier_result(
                    run_id, plan, "ready",
                    [_synthetic_repair_action(plan, round_number=round_number)],
                )
            if repair.get("outcome") != "succeeded":
                return _frontier_result(
                    run_id, plan, "stopped", [], stop="repair-failed"
                )
            return _frontier_result(
                run_id, plan, "ready",
                [_synthetic_verifier_action(
                    root, plan, receipts, attempt=round_number + 1
                )],
            )
        else:
            return _frontier_result(
                run_id, plan, "stopped", [],
                stop=f"verdict-{prior.get('result') or prior.get('outcome')}",
            )
    architecture = _derive_architecture_gate_step(
        root,
        run_id,
        plan,
        receipts,
        projection,
        now=observed,
    )
    architect_action = architecture.get("action")
    if isinstance(architect_action, dict):
        return _frontier_result(
            run_id, plan, "ready", [architect_action]
        )
    if architecture.get("stop") is not None:
        return _frontier_result(
            run_id,
            plan,
            "stopped",
            [],
            stop=str(architecture["stop"]),
        )
    _require(
        architecture.get("completed") is True,
        "phase architecture gate lost its deterministic completion state",
    )
    return _frontier_result(
        run_id, plan, "story-certified", [],
        checkpoint=True, stop="integration-required",
    )


def _frontier_result(
    run_id: str,
    plan: dict[str, object],
    state: str,
    actions: list[dict[str, object]],
    *,
    checkpoint: bool = False,
    stop: str | None = None,
) -> dict[str, object]:
    selection = plan["selection"]
    obligations = plan.get("_frontier_obligations", {
        "open_obligations": [],
        "open_obligation_ids": [],
        "blocking_obligation_ids": [],
    })
    _require(
        isinstance(obligations, dict),
        "program frontier obligation projection is invalid",
    )
    return {
        "kind": PROGRAM_FRONTIER_KIND,
        "schema_version": PROGRAM_CONDUCTOR_SCHEMA_VERSION,
        "run_id": run_id,
        "state": state,
        "terminal": False,
        "checkpoint": checkpoint,
        "stop": stop,
        "next_actions": actions,
        "lineage": {
            "program": plan["program"]["slug"],  # type: ignore[index]
            "phase": selection["phase"],  # type: ignore[index]
            "story": selection["story"],  # type: ignore[index]
            "workflow": _workflow_address(plan),
        },
        **obligations,
        "starts_work": False,
        "writes_state": False,
    }


def _child_grant_path(root: Path, run_id: str, grant_hash: str) -> Path:
    _hash(grant_hash, "child grant hash")
    return _conductor_dir(root, run_id) / "child-grants" / f"{grant_hash.split(':', 1)[1]}.json"


def _store_child_grant(
    root: Path,
    run_id: str,
    grant: dict[str, object],
) -> None:
    validated = validate_child_grant(grant)
    _write_json_atomic(
        _child_grant_path(root, run_id, str(validated["grant_hash"])),
        validated,
        immutable=True,
    )


def _load_child_grant(
    root: Path,
    run_id: str,
    grant_hash: str,
) -> dict[str, object]:
    value = _load_json(_child_grant_path(root, run_id, grant_hash), "program child grant")
    validate_child_grant(value)
    _require(value["grant_hash"] == grant_hash, "stored child grant hash differs")
    return value


def _claim_by_key(
    projection: dict[str, object],
    key: str,
) -> dict[str, object] | None:
    matches = [
        item for item in projection["claims"]
        if isinstance(item, dict) and item.get("idempotency_key") == key
    ]
    _require(len(matches) <= 1, f"duplicate program claim for {key}")
    return matches[0] if matches else None


def _ensure_child_grant(
    root: Path,
    run_id: str,
    action: dict[str, object],
    projection: dict[str, object],
    config: dict[str, object],
    *,
    now: datetime,
    boundary_hook: BoundaryHook | None,
) -> tuple[dict[str, object], dict[str, object]]:
    key = f"program-conductor/{action['action_id']}/child-grant"
    prior = _claim_by_key(projection, key)
    if prior is not None:
        grant_hash = prior.get("child_grant_hash")
        _require(isinstance(grant_hash, str), "child-grant claim lost its grant hash")
        child = _load_child_grant(root, run_id, grant_hash)
    else:
        output_bytes = sum(
            int(item.get("max_bytes", 0))
            for item in action.get("outputs", []) if isinstance(item, dict)
        )
        remaining = projection["budgets"]["max_artifact_bytes"]["remaining"]
        child = derive_child_grant(
            root,
            run_id,
            role_address=str(action["role_address"]),
            node_address=str(action["address"]),
            capabilities=sorted(set(str(item) for item in action["capabilities"])),
            budgets={
                "max_agent_starts": 1,
                "max_artifact_bytes": max(1, min(max(output_bytes, 1), int(remaining))),
            },
            now=now,
            driver_config=config,
        )
        _store_child_grant(root, run_id, child)
    claim = _reserve_claim(
        root,
        run_id,
        action=action,
        category="child-grant",
        subject_kind="program-child-grant",
        subject_hash=str(child["grant_hash"]),
        suffix="child-grant",
        now=now,
        driver_config=config,
        child_grant=child,
    )
    if claim["status"] == "active":
        _boundary(boundary_hook, "after-claim", {
            "action_id": action["action_id"],
            "claim_id": claim["claim_id"],
            "category": "child-grant",
        })
        receipt = _store_receipt(root, run_id, {
            "action_id": _action_id(str(action["address"]) + "/child-grant", "child-grant", int(action["attempt"])),
            "parent_action_id": action["action_id"],
            "address": str(action["address"]) + "/child-grant",
            "action_kind": "child-grant",
            "phase": action["phase"],
            "story": action["story"],
            "workflow_address": action["workflow_address"],
            "node": action.get("node"),
            "role": action.get("role"),
            "role_address": action.get("role_address"),
            "attempt": action["attempt"],
            "claim_id": claim["claim_id"],
            "request_hash": claim["request_hash"],
            "outcome": "succeeded",
            "result": "delegated",
            "route": None,
            "operation": None,
            "artifacts": [],
            "verdict": None,
            "decision": None,
            "obligation_ids": [],
            "payload": {
                "child_grant_hash": child["grant_hash"],
                "capabilities": child["capabilities"],
                "budgets": child["budgets"],
            },
            "issued_at": claim["reserved_at"],
        })
        _boundary(boundary_hook, "after-receipt", {
            "action_id": action["action_id"],
            "claim_id": claim["claim_id"],
            "receipt_hash": receipt["receipt_hash"],
            "receipt_kind": "child-grant",
        })
        projection = _complete_claim(
            root, run_id, claim, str(receipt["receipt_hash"]),
            result="succeeded", reason="Recorded exact derived child authority.",
            now=now,
        )
    else:
        projection = replay_program(root, run_id, now=now)
    return child, projection


def _ensure_repair_reservation(
    root: Path,
    run_id: str,
    action: dict[str, object],
    config: dict[str, object],
    *,
    now: datetime,
    boundary_hook: BoundaryHook | None,
) -> dict[str, object]:
    claim = _reserve_claim(
        root, run_id, action=action, category="repair",
        subject_kind="program-repair-round",
        subject_hash=_sha(action["prompt_document"]),
        suffix="repair-authorization", now=now, driver_config=config,
    )
    if claim["status"] != "active":
        return replay_program(root, run_id, now=now)
    _boundary(boundary_hook, "after-claim", {
        "action_id": action["action_id"], "claim_id": claim["claim_id"],
        "category": "repair",
    })
    receipt = _store_receipt(root, run_id, {
        "action_id": _action_id(str(action["address"]) + "/authorization", "repair", int(action["attempt"])),
        "parent_action_id": action["action_id"],
        "address": str(action["address"]) + "/authorization",
        "action_kind": "repair-authorization",
        "phase": action["phase"], "story": action["story"],
        "workflow_address": action["workflow_address"], "node": action["node"],
        "role": action["role"], "role_address": action["role_address"],
        "attempt": action["attempt"], "claim_id": claim["claim_id"],
        "request_hash": claim["request_hash"], "outcome": "succeeded",
        "result": "authorized", "route": None, "operation": None,
        "artifacts": [], "verdict": None, "decision": None,
        "obligation_ids": [],
        "payload": {"repair_round": action["prompt_document"]["repair_round"]},
        "issued_at": claim["reserved_at"],
    })
    _boundary(boundary_hook, "after-receipt", {
        "action_id": action["action_id"], "claim_id": claim["claim_id"],
        "receipt_hash": receipt["receipt_hash"],
        "receipt_kind": "repair-authorization",
    })
    return _complete_claim(
        root, run_id, claim, str(receipt["receipt_hash"]),
        result="succeeded", reason="Authorized one finite repair round.", now=now,
    )


def _verdict_subject(
    run_id: str,
    context: dict[str, object],
    projection: dict[str, object],
    evidence: list[dict[str, object]],
    rubric: dict[str, object],
    verdict_assignment: dict[str, object],
    *,
    story: str | None,
) -> dict[str, object]:
    _require(evidence, "verdict has no validated candidate evidence")
    assignment = context["assignment"]
    plan = context["plan"]
    grant = context["grant"]
    assert isinstance(assignment, dict) and isinstance(plan, dict) and isinstance(grant, dict)
    implementers = [
        member["principal_fingerprint"]
        for role in assignment["roles"]
        if role.get("duty") == "implementer"
        for member in role.get("members", [])
    ]
    _require(bool(implementers), "verdict subject has no implementer principal")
    subject_type = str(rubric["rubric"]["subject_type"])
    primary = next(
        (item for item in evidence if item["kind"] == subject_type),
        evidence[0],
    )
    return {
        "kind": subject_type,
        "hash": primary["hash"],
        "repository_hash": _sha(projection["expected_repository"]),
        "program_hash": grant["program"]["bundle_hash"],
        "program_run_id": run_id,
        "phase": int(plan["selection"]["phase"]),
        "story": story,
        "workflow_address": _workflow_address(plan),
        "assignment_hash": assignment["assignment_hash"],
        "assignment_generation": int(
            verdict_assignment["assignment_generation"]
        ),
        "ledger_head": projection["ledger_head"],
        "implementer_principals": sorted(set(implementers)),
    }


def _issue_bound_verdict(
    root: Path,
    run_id: str,
    action: dict[str, object],
    artifacts: list[dict[str, object]],
    driver_record: dict[str, object],
    context: dict[str, object],
    config: dict[str, object],
    *,
    now: datetime,
    boundary_hook: BoundaryHook | None,
) -> tuple[dict[str, object], dict[str, object], list[dict[str, object]]]:
    judgment_artifact = next(
        (item for item in artifacts if item.get("name") == "judgment"),
        None,
    )
    _require(isinstance(judgment_artifact, dict), "verdict action produced no judgment artifact")
    try:
        judgment = json.loads(_artifact_content(root, run_id, judgment_artifact).decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise DwError("verdict judgment artifact is malformed") from exc
    _require(isinstance(judgment, dict) and isinstance(judgment.get("criteria"), list), "verdict judgment has no criterion results")
    assignment = context["assignment"]
    assert isinstance(assignment, dict)
    verdict_assignment = build_verdict_assignment(
        assignment,
        str(action["role"]),
        member_address=str(action["role_address"]),
    )
    verdict_type = str(action.get("verdict_type") or {
        "master-architect": "architect-verdict",
        "meta-verifier": "meta-verdict",
    }.get(str(verdict_assignment["duty"]), "agent-verdict"))
    subject_story = action.get(
        "subject_story",
        context["plan"]["selection"]["story"],  # type: ignore[index]
    )
    _require(
        subject_story is None or isinstance(subject_story, str),
        "verdict subject story is invalid",
    )
    if subject_story is None:
        verdict_assignment = {**verdict_assignment, "story": None}
    verdict_action = dict(action)
    verdict_action["address"] = str(action["address"]) + "/issuance"
    verdict_action["action_id"] = _action_id(
        str(verdict_action["address"]),
        verdict_type,
        int(action["attempt"]),
    )
    verdict_claim = _reserve_claim(
        root,
        run_id,
        action=action,
        category="verdict",
        subject_kind="program-judgment",
        subject_hash=str(judgment_artifact["sha256"]),
        suffix="verdict",
        now=now,
        driver_config=config,
    )
    if verdict_claim["status"] != "active":
        prior_receipt = _load_receipt(root, run_id, str(verdict_claim["receipt_hash"]))
        verdict_ref = prior_receipt.get("verdict")
        _require(isinstance(verdict_ref, dict), "completed verdict claim lost its verdict reference")
        verdict_artifact = next(
            (item for item in prior_receipt.get("artifacts", []) if isinstance(item, dict) and item.get("name") == "issued-verdict"),
            None,
        )
        _require(isinstance(verdict_artifact, dict), "completed verdict claim lost its artifact")
        verdict = json.loads(_artifact_content(root, run_id, verdict_artifact).decode("utf-8"))
        return validate_verdict_document(verdict), prior_receipt, artifacts + [verdict_artifact]
    _boundary(boundary_hook, "after-claim", {
        "action_id": verdict_action["action_id"],
        "claim_id": verdict_claim["claim_id"],
        "category": "verdict",
    })
    projection = replay_program(root, run_id, now=now)
    rubric = compile_rubric(root, str(action["rubric"]))
    durable_evidence = _evidence_from_receipts(_receipts_for_plan(
        replay_program_conductor(root, run_id, now=now)["receipts"],
        context["plan"],
    ))
    packet_evidence = action["prompt_document"].get("evidence", [])  # type: ignore[union-attr]
    _require(
        isinstance(packet_evidence, list) and packet_evidence,
        "verdict packet has no exact durable evidence",
    )
    durable_keys = {
        (str(item["kind"]), str(item["hash"]), str(item["ref"]))
        for item in durable_evidence
    }
    evidence: list[dict[str, object]] = []
    for item in packet_evidence:
        _require(
            isinstance(item, dict)
            and set(item) == {"kind", "hash", "ref"},
            "verdict packet evidence is malformed",
        )
        normalized = {
            "kind": str(item["kind"]),
            "hash": _hash(item["hash"], "verdict evidence hash"),
            "ref": _safe(item["ref"], "verdict evidence reference"),
        }
        _require(
            (
                normalized["kind"],
                normalized["hash"],
                normalized["ref"],
            ) in durable_keys,
            "verdict packet cites evidence outside durable conductor receipts",
        )
        evidence.append(normalized)
    allowed_evidence = {
        (str(item["kind"]), str(item["hash"]), str(item["ref"]))
        for item in evidence
    }
    for criterion in judgment["criteria"]:
        _require(
            isinstance(criterion, dict)
            and isinstance(criterion.get("evidence"), list),
            "verdict criterion evidence is malformed",
        )
        for item in criterion["evidence"]:
            _require(
                isinstance(item, dict)
                and (
                    str(item.get("kind")),
                    str(item.get("hash")),
                    str(item.get("ref")),
                ) in allowed_evidence,
                "verdict criterion cites evidence outside its exact packet",
            )
    driver_receipt = driver_record["receipt"]
    _require(isinstance(driver_receipt, dict), "terminal driver operation has no receipt")
    issued_at = str(driver_receipt["updated_at"])
    verdict = issue_agent_verdict(
        root,
        str(action["rubric"]),
        verdict_assignment,
        _verdict_subject(
            run_id,
            context,
            projection,
            evidence,
            rubric,
            verdict_assignment,
            story=subject_story,
        ),
        judgment["criteria"],
        issued_at=issued_at,
        idempotency_key=str(verdict_claim["idempotency_key"]),
        attestation_receipt_hash=_sha(driver_receipt),
        verdict_type=verdict_type,
    )
    verdict = validate_verdict_document(verdict)
    verdict_bytes = (canonical_json(verdict) + "\n").encode("utf-8")
    verdict_artifact = _store_artifact(
        root,
        run_id,
        action_id=str(verdict_action["action_id"]),
        address=str(verdict_action["address"]),
        attempt=int(action["attempt"]),
        name="issued-verdict",
        kind=(
            "architecture-verdict"
            if verdict_type == "architect-verdict"
            else "meta-verdict"
            if verdict_type == "meta-verdict"
            else "verdict"
        ),
        data=verdict_bytes,
        checks=[
            "verdict-core", "rubric-bound", "separation-proved", "attested",
            "packet-evidence-bound",
        ],
    )
    verdict_ref = {
        "hash": verdict["verdict_hash"],
        "result": verdict["result"],
        "type": verdict["verdict_type"],
        "ref": verdict_artifact["ref"],
    }
    receipt = _store_receipt(root, run_id, {
        "action_id": verdict_action["action_id"],
        "parent_action_id": action["action_id"],
        "address": verdict_action["address"],
        "action_kind": (
            "architect-verdict-issuance"
            if verdict_type == "architect-verdict"
            else "meta-verdict-issuance"
            if verdict_type == "meta-verdict"
            else "verdict-issuance"
        ),
        "phase": action["phase"],
        "story": action["story"],
        "workflow_address": action["workflow_address"],
        "node": action.get("node"),
        "role": action.get("role"),
        "role_address": action.get("role_address"),
        "attempt": action["attempt"],
        "claim_id": verdict_claim["claim_id"],
        "request_hash": verdict_claim["request_hash"],
        "outcome": "succeeded",
        "result": verdict["result"],
        "route": verdict["result"],
        "operation": {"driver_receipt_hash": _sha(driver_receipt)},
        "artifacts": [verdict_artifact],
        "verdict": verdict_ref,
        "decision": None,
        "obligation_ids": [],
        "payload": {"rubric": verdict["rubric"], "subject_hash": verdict["subject"]["hash"]},
        "issued_at": issued_at,
    })
    _boundary(boundary_hook, "after-receipt", {
        "action_id": verdict_action["action_id"],
        "claim_id": verdict_claim["claim_id"],
        "receipt_hash": receipt["receipt_hash"],
        "receipt_kind": receipt["action_kind"],
    })
    _complete_claim(
        root, run_id, verdict_claim, str(receipt["receipt_hash"]),
        result="succeeded",
        reason=f"Issued one rubric-bound {verdict_type}.",
        now=now,
    )
    return verdict, receipt, artifacts + [verdict_artifact]


def _expanded_deliberation_node(
    context: dict[str, object],
    action: dict[str, object],
) -> dict[str, object]:
    instance = context["instance"]
    assert isinstance(instance, dict)
    matches = [
        item for item in instance.get("expanded_nodes", [])
        if isinstance(item, dict)
        and item.get("address") == action.get("expanded_address")
        and item.get("type") == "debate"
    ]
    _require(len(matches) == 1, "deliberation action lost its compiled debate node")
    return matches[0]


def _record_deliberation_agent_submission(
    root: Path,
    run_id: str,
    action: dict[str, object],
    claim: dict[str, object],
    artifacts: list[dict[str, object]],
    context: dict[str, object],
    *,
    issued_at: str,
) -> tuple[dict[str, object], dict[str, object]]:
    artifact = next(
        (item for item in artifacts if item.get("name") == "submission"),
        None,
    )
    _require(isinstance(artifact, dict), "deliberation action produced no submission artifact")
    try:
        raw = json.loads(_artifact_content(root, run_id, artifact).decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise DwError("deliberation submission artifact is malformed") from exc
    expected = {"citations", "vote", "result", "rationale", "obligations"}
    _require(
        isinstance(raw, dict) and set(raw) == expected,
        "deliberation submission must use the exact closed output keys",
    )
    citations = raw.get("citations")
    allowed = set(str(item) for item in action["prompt_document"]["citation_refs"])  # type: ignore[index]
    _require(
        isinstance(citations, list) and citations
        and all(isinstance(item, str) and item in allowed for item in citations)
        and len(set(citations)) == len(citations),
        "deliberation submission cites evidence outside its exact packet",
    )
    expanded = _expanded_deliberation_node(context, action)
    conductor = replay_program_conductor(root, run_id, now=issued_at)
    program_projection = conductor["authority"]
    protocol = _deliberation_protocol(
        root,
        run_id,
        context,
        expanded,
        _receipts_for_plan(conductor["receipts"], context["plan"]),
        program_projection,
        now=_time(str(claim["reserved_at"]), "deliberation claim time"),
    )
    pending = protocol.get("action")
    pure_claim = protocol.get("claim")
    _require(
        isinstance(pending, dict)
        and pending["action_id"] == action["action_id"]
        and isinstance(pure_claim, dict)
        and pure_claim["claim_id"] == action["deliberation"]["claim_id"],  # type: ignore[index]
        "deliberation driver result no longer matches the deterministic slot",
    )
    content = _artifact_content(root, run_id, artifact).decode("utf-8")
    token_count = max(1, len(content.split()))
    plan = protocol["plan"]
    assert isinstance(plan, dict)
    _require(
        token_count <= int(plan["debate"]["artifact_max_tokens"]),  # type: ignore[index]
        "deliberation submission exceeds its content-token ceiling",
    )
    submission = {
        "kind": {
            "proposal": "proposal",
            "critique": "critique",
            "rebuttal": "rebuttal",
            "judgment": COUNCIL_VERDICT_KIND,
            "meta-audit": META_VERDICT_KIND,
            "architect-review": ARCHITECT_VERDICT_KIND,
        }[str(pure_claim["stage"])],
        "content_hash": artifact["sha256"],
        "content_ref": artifact["ref"],
        "bytes": artifact["bytes"],
        "tokens": token_count,
        "citations": citations,
        "vote": raw["vote"],
        "result": raw["result"],
        "rationale": raw["rationale"],
        "obligations": raw["obligations"],
    }
    recorded = record_deliberation_submission(
        plan,
        protocol["events"],  # type: ignore[arg-type]
        str(pure_claim["claim_id"]),
        submission,
        issued_at,
    )
    detail = recorded["events"][-1]["detail"]
    _require(
        detail["claim_id"] == pure_claim["claim_id"],
        "pure deliberation core closed a different claim",
    )
    return submission, detail


def _execute_deliberation_issuance(
    root: Path,
    run_id: str,
    action: dict[str, object],
    config: dict[str, object],
    *,
    now: datetime,
    boundary_hook: BoundaryHook | None,
) -> dict[str, object]:
    kind = str(action["kind"])
    document = action["document"]
    _require(isinstance(document, dict), "deliberation issuance has no document")
    if kind == "council-decision":
        document = validate_council_decision(document)
        category = "council"
        subject_kind = "program-council-decision"
        artifact_kind = "decision"
        artifact_name = "issued-decision"
        content_hash = str(document["decision_hash"])
        verdict_ref = None
        decision_ref = {
            "hash": document["decision_hash"],
            "result": document["result"],
            "type": document["decision_type"],
        }
    else:
        _require(
            kind in {"meta-verdict-issuance", "architect-verdict-issuance"},
            "unsupported deliberation issuance kind",
        )
        category = "verdict"
        subject_kind = "program-deliberation-verdict"
        artifact_kind = (
            "meta-verdict"
            if kind == "meta-verdict-issuance" else "architecture-verdict"
        )
        artifact_name = "issued-" + artifact_kind
        content_hash = _hash(document.get("receipt_hash"), "deliberation verdict receipt hash")
        verdict_ref = {
            "hash": content_hash,
            "result": document["result"],
            "type": artifact_kind,
        }
        decision_ref = None
    claim = _reserve_claim(
        root,
        run_id,
        action=action,
        category=category,
        subject_kind=subject_kind,
        subject_hash=content_hash,
        suffix="issuance",
        now=now,
        driver_config=config,
    )
    if claim["status"] != "active":
        return {
            "status": "complete",
            "projection": replay_program(root, run_id, now=now),
            "receipt": _load_receipt(root, run_id, str(claim["receipt_hash"])),
        }
    _boundary(boundary_hook, "after-claim", {
        "action_id": action["action_id"],
        "claim_id": claim["claim_id"],
        "category": category,
    })
    artifact = _store_artifact(
        root,
        run_id,
        action_id=str(action["action_id"]),
        address=str(action["address"]),
        attempt=int(action["attempt"]),
        name=artifact_name,
        kind=artifact_kind,
        data=(canonical_json(document) + "\n").encode("utf-8"),
        checks=[
            "deliberation-core", "authority-bound", "finite-protocol",
            "assignment-bound",
        ],
    )
    if decision_ref is not None:
        decision_ref = {**decision_ref, "ref": artifact["ref"]}
    if verdict_ref is not None:
        verdict_ref = {**verdict_ref, "ref": artifact["ref"]}
    receipt = _store_receipt(root, run_id, {
        "action_id": action["action_id"],
        "address": action["address"],
        "action_kind": kind,
        "phase": action["phase"],
        "story": action["story"],
        "workflow_address": action["workflow_address"],
        "node": action.get("node"),
        "role": action.get("role"),
        "role_address": action.get("role_address"),
        "attempt": action["attempt"],
        "claim_id": claim["claim_id"],
        "request_hash": claim["request_hash"],
        "outcome": "succeeded",
        "result": document["result"],
        "route": document.get("route"),
        "operation": None,
        "artifacts": [artifact],
        "verdict": verdict_ref,
        "decision": decision_ref,
        "obligation_ids": [
            item["id"] for item in (
                document.get("obligations")
                if isinstance(document.get("obligations"), list) else []
            )
            if isinstance(item, dict)
        ],
        "payload": {
            "deliberation_issuance": action["payload"],
        },
        "issued_at": claim["reserved_at"],
    })
    _boundary(boundary_hook, "after-receipt", {
        "action_id": action["action_id"],
        "claim_id": claim["claim_id"],
        "receipt_hash": receipt["receipt_hash"],
        "receipt_kind": kind,
    })
    projection = _complete_claim(
        root,
        run_id,
        claim,
        str(receipt["receipt_hash"]),
        result="succeeded",
        reason=f"Issued the exact pure-core {artifact_kind}.",
        now=now,
    )
    return {"status": "complete", "projection": projection, "receipt": receipt}


def _execute_obligation_ingestion(
    root: Path,
    run_id: str,
    action: dict[str, object],
    config: dict[str, object],
    *,
    now: datetime,
    boundary_hook: BoundaryHook | None,
) -> dict[str, object]:
    decision = action["decision"]
    obligation = action["obligation"]
    assert isinstance(decision, dict) and isinstance(obligation, dict)
    claim = _reserve_claim(
        root,
        run_id,
        action=action,
        category="obligation-record",
        subject_kind="program-obligation",
        subject_hash=str(action["subject_hash"]),
        subject_id=str(obligation["id"]),
        suffix="obligation",
        now=now,
        driver_config=config,
    )
    if claim["status"] == "active":
        _boundary(boundary_hook, "after-claim", {
            "action_id": action["action_id"],
            "claim_id": claim["claim_id"],
            "category": "obligation-record",
        })
        decision_receipts = [
            item for item in replay_program_conductor(
                root, run_id, now=now
            )["receipts"]
            if isinstance(item.get("decision"), dict)
            and item["decision"].get("hash") == decision["decision_hash"]
        ]
        _require(
            len(decision_receipts) == 1,
            "obligation ingestion lost its unique issued council decision",
        )
        decision_artifacts = [
            item
            for item in decision_receipts[0].get("artifacts", [])
            if isinstance(item, dict) and item.get("name") == "issued-decision"
        ]
        _require(
            len(decision_artifacts) == 1,
            "obligation ingestion lost its issued decision artifact",
        )
        receipt = _store_receipt(root, run_id, {
            "action_id": action["action_id"],
            "address": action["address"],
            "action_kind": action["kind"],
            "phase": action["phase"],
            "story": action["story"],
            "workflow_address": action["workflow_address"],
            "node": action.get("node"),
            "role": action.get("role"),
            "role_address": action.get("role_address"),
            "attempt": action["attempt"],
            "claim_id": claim["claim_id"],
            "request_hash": claim["request_hash"],
            "outcome": "succeeded",
            "result": "recorded",
            "route": None,
            "operation": None,
            "artifacts": [],
            "verdict": None,
            "decision": {
                "hash": decision["decision_hash"],
                "result": decision["result"],
                "type": decision["decision_type"],
                "ref": decision_artifacts[0]["ref"],
            },
            "obligation_ids": [obligation["id"]],
            "payload": {
                "decision_hash": decision["decision_hash"],
                "obligation_hash": _sha(obligation),
            },
            "issued_at": claim["reserved_at"],
        })
        _boundary(boundary_hook, "after-receipt", {
            "action_id": action["action_id"],
            "claim_id": claim["claim_id"],
            "receipt_hash": receipt["receipt_hash"],
            "receipt_kind": "obligation-ingestion",
        })
        projection = _complete_claim(
            root,
            run_id,
            claim,
            str(receipt["receipt_hash"]),
            result="succeeded",
            reason="Validated one exact council obligation for durable ingestion.",
            now=now,
        )
        _boundary(boundary_hook, "after-obligation-completion", {
            "action_id": action["action_id"],
            "claim_id": claim["claim_id"],
            "obligation_id": obligation["id"],
        })
    else:
        receipt = _load_receipt(root, run_id, str(claim["receipt_hash"]))
        projection = replay_program(root, run_id, now=now)
    recorded = record_program_obligation(
        root,
        run_id,
        claim_id=str(claim["claim_id"]),
        decision_hash=str(decision["decision_hash"]),
        obligation=obligation,
        now=now,
    )
    return {
        "status": "complete",
        "projection": recorded,
        "receipt": receipt,
    }


def _execute_checkpoint_request(
    root: Path,
    run_id: str,
    action: dict[str, object],
    config: dict[str, object],
    *,
    now: datetime,
    boundary_hook: BoundaryHook | None,
) -> dict[str, object]:
    claim = _reserve_claim(
        root,
        run_id,
        action=action,
        category="checkpoint-request",
        subject_kind=str(
            action.get(
                "checkpoint_subject_kind",
                "program-decision-checkpoint",
            )
        ),
        subject_hash=str(action["subject_hash"]),
        suffix="checkpoint",
        request_port=str(action["request_port"]),
        now=now,
        driver_config=config,
    )
    _boundary(boundary_hook, "after-claim", {
        "action_id": action["action_id"],
        "claim_id": claim["claim_id"],
        "category": "checkpoint-request",
    })
    return {
        "status": "checkpoint",
        "projection": replay_program(root, run_id, now=now),
        "reason": str(action.get(
            "checkpoint_reason",
            (
                "A separately authorized principal must answer the typed "
                "council checkpoint."
            ),
        )),
    }


def respond_program_request(
    root: Path,
    run_id: str,
    request_id: str,
    decision: str,
    *,
    reason: str,
    now: str | datetime | None = None,
    driver_config: object | None = None,
    _expected_binding: dict[str, object] | None = None,
) -> dict[str, object]:
    """Resolve one exact typed program checkpoint through its existing claim.

    This is intentionally narrower than the low-level completion API.  The
    caller may name only the active request, one closed decision, and a bounded
    reason.  Receipt shape, responder identity, fact binding, and route remain
    owned by the conductor and immutable grant.
    """
    root = root.resolve()
    observed = _time(now, "now")
    request_id = _safe(request_id, "program request id")
    decision = str(decision or "").strip().lower()
    _require(
        decision in {"approve", "reject"},
        "program request decision must be approve or reject",
    )
    normalized_reason = _bounded_text(
        str(reason or "").strip(),
        "program request reason",
        1_000,
    )
    # Resolving a request is a conductor-owned receipt transition, so serialize
    # it with ticks as well as the authority ledger's own append lock.
    with _conductor_lock(root, run_id):
        projection = replay_program(root, run_id, now=observed)
        if _expected_binding is not None:
            _require(
                all(
                    projection.get(key) == _expected_binding.get(key)
                    for key in (
                        "grant_hash", "ledger_head", "generation", "state",
                    )
                ),
                "program act token is stale at the request lock",
            )
        matches = [
            item
            for item in projection["outstanding_requests"]
            if item.get("claim_id") == request_id
        ]
        _require(
            len(matches) == 1,
            "program request is stale, unknown, or no longer outstanding",
        )
        claim = next(
            (
                item
                for item in projection["active_claims"]
                if item.get("claim_id") == request_id
                and item.get("category") == "checkpoint-request"
            ),
            None,
        )
        _require(
            isinstance(claim, dict),
            "program request has no active checkpoint claim",
        )
        _path, grant, _plan = _load_documents(root, run_id)
        key = str(claim["idempotency_key"])
        pieces = key.split("/")
        _require(
            len(pieces) == 3
            and pieces[0] == "program-conductor"
            and pieces[2] == "checkpoint",
            "program request is outside the conductor checkpoint boundary",
        )
        action_id = _safe(pieces[1], "program request action id")
        subject = claim["subject"]
        _require(
            isinstance(subject, dict),
            "program request subject is invalid",
        )
        address = _safe(subject.get("id"), "program request address")
        workflow_address = str(
            grant.get("selection", {})
            .get("workflow", {})
            .get("slug", "")
        )
        assignment = grant.get("selection")
        if isinstance(assignment, dict):
            # The durable address is the canonical source.  Keep the compact
            # workflow lineage used by all other conductor receipts.
            marker = "/workflow/"
            if marker in address:
                prefix, tail = address.split(marker, 1)
                workflow_slug = tail.split("/", 1)[0]
                workflow_address = f"{prefix}{marker}{workflow_slug}"
        attempt_match = re.search(r"/attempt/([1-9][0-9]*)$", address)
        _require(
            attempt_match is not None,
            "program request address has no bounded attempt",
        )
        attempt = int(attempt_match.group(1))
        responder = grant["operator"]
        receipt = _store_receipt(root, run_id, {
            "action_id": action_id,
            "address": address,
            "action_kind": "checkpoint-request",
            "phase": subject.get("phase"),
            "story": subject.get("story"),
            "workflow_address": workflow_address,
            "node": None,
            "role": None,
            "role_address": None,
            "attempt": attempt,
            "claim_id": claim["claim_id"],
            "request_hash": claim["request_hash"],
            "outcome": "succeeded",
            "result": decision,
            "route": decision,
            "operation": None,
            "artifacts": [],
            "verdict": None,
            "decision": {
                "kind": "typed-checkpoint-response",
                "option": decision,
                "responder": responder,
            },
            "obligation_ids": [],
            "payload": {
                "request_id": request_id,
                "port": claim["request_port"],
                "decision": decision,
                "reason": normalized_reason,
                "generation": projection["generation"],
                "ledger_head": projection["ledger_head"],
            },
            "issued_at": _format_time(observed),
        })
        after = _complete_claim(
            root,
            run_id,
            claim,
            str(receipt["receipt_hash"]),
            result="succeeded",
            reason="Recorded one closed typed program checkpoint response.",
            now=observed,
        )
    # Rebuild once so a corrupt/mismatched response cannot hide until the next
    # tick.  This remains a read after the exact receipt transition.
    frontier = derive_program_frontier(
        root,
        run_id,
        driver_config=driver_config,
        now=observed,
    )
    return {
        "kind": PROGRAM_REQUEST_RESULT_KIND,
        "schema_version": PROGRAM_CONDUCTOR_SCHEMA_VERSION,
        "run_id": run_id,
        "request_id": request_id,
        "decision": decision,
        "receipt_hash": receipt["receipt_hash"],
        "state": after["state"],
        "frontier": frontier,
        "content_safe": True,
    }


def _execute_deliberation_local_action(
    root: Path,
    run_id: str,
    action: dict[str, object],
    config: dict[str, object],
    *,
    now: datetime,
    boundary_hook: BoundaryHook | None,
) -> dict[str, object]:
    kind = str(action["kind"])
    if kind == "debate-round":
        projection, receipt = _local_action(
            root,
            run_id,
            action,
            category="debate-round",
            subject_hash=str(action["subject_hash"]),
            payload=dict(action["payload"]),
            now=now,
            driver_config=config,
            boundary_hook=boundary_hook,
        )
        return {"status": "complete", "projection": projection, "receipt": receipt}
    if kind in {
        "council-decision", "meta-verdict-issuance",
        "architect-verdict-issuance",
    }:
        return _execute_deliberation_issuance(
            root, run_id, action, config, now=now,
            boundary_hook=boundary_hook,
        )
    if kind == "obligation-ingestion":
        return _execute_obligation_ingestion(
            root, run_id, action, config, now=now,
            boundary_hook=boundary_hook,
        )
    if kind == "checkpoint-request":
        return _execute_checkpoint_request(
            root, run_id, action, config, now=now,
            boundary_hook=boundary_hook,
        )
    raise DwError(f"unsupported local deliberation action: {kind}")


def _driver_operation_summary(record: dict[str, object]) -> dict[str, object]:
    receipt = record.get("receipt")
    return {
        "operation_id": record["operation_id"],
        "session_id": record["session_id"],
        "packet_hash": record["packet_hash"],
        "profile": record["profile"],
        "adapter": record["adapter"],
        "adapter_version": record["adapter_version"],
        "state": receipt.get("state") if isinstance(receipt, dict) else record["status"],
        "receipt_hash": _sha(receipt) if isinstance(receipt, dict) else None,
        "usage": (
            normalize_driver_usage(receipt.get("usage"))
            if isinstance(receipt, dict) else normalize_driver_usage()
        ),
    }


def _finish_agent_action(
    root: Path,
    run_id: str,
    action: dict[str, object],
    claim: dict[str, object],
    record: dict[str, object],
    context: dict[str, object],
    config: dict[str, object],
    *,
    now: datetime,
    boundary_hook: BoundaryHook | None,
) -> tuple[dict[str, object], dict[str, object]]:
    packet = validate_work_packet(
        _load_json(Path(str(record["packet_path"])), "program work packet")
    )
    driver_receipt = record.get("receipt")
    _require(isinstance(driver_receipt, dict), "terminal program driver operation has no receipt")
    state = str(driver_receipt["state"])
    _require(state in TERMINAL_DRIVER_STATES, "cannot finish a non-terminal driver operation")
    artifacts: list[dict[str, object]] = []
    verdict: dict[str, object] | None = None
    verdict_ref: dict[str, object] | None = None
    deliberation_binding: dict[str, object] | None = None
    result = state
    route: object = state
    if state == "succeeded":
        artifacts = _collect_outputs(root, run_id, action, packet, record)
        if isinstance(action.get("deliberation"), dict):
            submission, pure_receipt = _record_deliberation_agent_submission(
                root,
                run_id,
                action,
                claim,
                artifacts,
                context,
                issued_at=str(driver_receipt["updated_at"]),
            )
            result = str(
                pure_receipt.get("result")
                or pure_receipt.get("vote")
                or "submitted"
            )
            route = pure_receipt.get("route")
            deliberation = action["deliberation"]
            assert isinstance(deliberation, dict)
            deliberation_binding = {
                "plan_hash": deliberation["plan_hash"],
                "protocol_id": deliberation["protocol_id"],
                "claim_id": deliberation["claim_id"],
                "claimed_at": claim["reserved_at"],
                "stage": deliberation["stage"],
                "round": deliberation["round"],
                "submission": submission,
                "pure_receipt_hash": pure_receipt["receipt_hash"],
            }
        elif action["kind"] in {"verdict", "story-verification", "meta-verdict", "architect-verdict"}:
            verdict, _verdict_receipt, artifacts = _issue_bound_verdict(
                root,
                run_id,
                action,
                artifacts,
                record,
                context,
                config,
                now=now,
                boundary_hook=boundary_hook,
            )
            result = str(verdict["result"])
            route = result
            issued = next(
                item for item in artifacts if item.get("name") == "issued-verdict"
            )
            verdict_ref = {
                "hash": verdict["verdict_hash"],
                "result": verdict["result"],
                "type": verdict["verdict_type"],
                "ref": issued["ref"],
            }
    receipt = _store_receipt(root, run_id, {
        "action_id": action["action_id"],
        "address": action["address"],
        "action_kind": action["kind"],
        "phase": action["phase"],
        "story": action["story"],
        "workflow_address": action["workflow_address"],
        "node": action.get("node"),
        "role": action.get("role"),
        "role_address": action.get("role_address"),
        "attempt": action["attempt"],
        "claim_id": claim["claim_id"],
        "request_hash": claim["request_hash"],
        "outcome": state,
        "result": result,
        "route": route,
        "operation": _driver_operation_summary(record),
        "artifacts": artifacts,
        "verdict": verdict_ref,
        "decision": None,
        "obligation_ids": [],
        "payload": {
            "child_grant_hash": record["child_grant_hash"],
            "driver_receipt_hash": _sha(driver_receipt),
            **({"repair_round": action["prompt_document"]["repair_round"]} if action["kind"] == "repair" else {}),
            **(
                {"nudge": action["nudge"]}
                if isinstance(action.get("nudge"), dict)
                else {}
            ),
            **(
                {"deliberation_submission": deliberation_binding}
                if deliberation_binding is not None else {}
            ),
        },
        "issued_at": driver_receipt["updated_at"],
    })
    _boundary(boundary_hook, "after-receipt", {
        "action_id": action["action_id"],
        "claim_id": claim["claim_id"],
        "receipt_hash": receipt["receipt_hash"],
        "receipt_kind": str(action["kind"]),
    })
    completion_result = state if state in {"succeeded", "failed", "cancelled", "lost", "refused"} else "failed"
    projection = _complete_claim(
        root,
        run_id,
        claim,
        str(receipt["receipt_hash"]),
        result=completion_result,
        reason=(
            "Validated and recorded the exact driver result."
            if state == "succeeded"
            else f"Driver operation ended as {state}."
        ),
        now=now,
    )
    return projection, receipt


def _execute_agent_action(
    root: Path,
    run_id: str,
    action: dict[str, object],
    context: dict[str, object],
    manager: ProgramDriverManager,
    config: dict[str, object],
    *,
    now: datetime,
    boundary_hook: BoundaryHook | None,
) -> dict[str, object]:
    projection = replay_program(root, run_id, now=now)
    if action["kind"] == "repair":
        projection = _ensure_repair_reservation(
            root, run_id, action, config, now=now,
            boundary_hook=boundary_hook,
        )
    child, projection = _ensure_child_grant(
        root,
        run_id,
        action,
        projection,
        config,
        now=now,
        boundary_hook=boundary_hook,
    )
    claim = _reserve_claim(
        root,
        run_id,
        action=action,
        category="agent",
        subject_kind="program-agent-dispatch",
        subject_hash=str(child["grant_hash"]),
        suffix="agent",
        now=now,
        driver_config=config,
        resource_estimate={
            "artifact_bytes": sum(
                int(item.get("max_bytes", 0))
                for item in action.get("outputs", []) if isinstance(item, dict)
            ),
            "tokens": 0,
            "observed_cost_microunits": 0,
        },
    )
    if claim["status"] != "active":
        receipt = _load_receipt(root, run_id, str(claim["receipt_hash"]))
        return {"status": "complete", "projection": replay_program(root, run_id, now=now), "receipt": receipt}
    if claim.get("dispatch") is None:
        _boundary(boundary_hook, "after-claim", {
            "action_id": action["action_id"],
            "claim_id": claim["claim_id"],
            "category": "agent",
        })
    assignment = context["assignment"]
    assert isinstance(assignment, dict)
    role = _role_document(assignment, role_id=str(action["role"]))
    member = _role_member(role)
    if claim.get("dispatch") is None:
        plan = context.get("plan")
        _require(isinstance(plan, dict), "program packet assembly has no current plan")
        selection = plan.get("selection")
        _require(isinstance(selection, dict), "program packet assembly has no selected story")
        packet = _build_packet(
            root,
            run_id,
            claim,
            action,
            child,
            role,
            member,
            config,
            replay_program(root, run_id, now=now),
            selection,
            now=now,
        )
        record = manager.prepare(
            claim,
            packet,
            profile=str(member["profile"]),
            child_grant_hash=str(child["grant_hash"]),
        )
        operation_id = str(record["operation_id"])
        capability = driver_capability(config, str(member["profile"]))
        _boundary(boundary_hook, "before-dispatch", {
            "action_id": action["action_id"],
            "claim_id": claim["claim_id"],
            "operation_id": operation_id,
        })
        projection = record_program_dispatch(
            root,
            run_id,
            claim_id=str(claim["claim_id"]),
            operation_id=operation_id,
            packet_hash=str(packet["packet_hash"]),
            idempotency_key=str(claim["idempotency_key"]),
            profile=str(member["profile"]),
            adapter=str(capability["adapter"]),
            adapter_version=str(capability["adapter_version"]),
            execution=_execution(capability),
            child_grant_hash=str(child["grant_hash"]),
            now=now,
            driver_config=config,
        )
        claim = next(
            item for item in projection["active_claims"]
            if item["claim_id"] == claim["claim_id"]
        )
        _boundary(boundary_hook, "after-dispatch-record", {
            "action_id": action["action_id"],
            "claim_id": claim["claim_id"],
            "operation_id": operation_id,
        })
        record = manager.start(
            operation_id, now=now, boundary_hook=boundary_hook
        )
        status = "terminal" if record["status"] == "terminal" else "running"
        reconciled = {"status": status, "record": record, "operation_id": operation_id, "reason": "started"}
    else:
        operation_id = str(claim["dispatch"]["operation_id"])
        reconciled = manager.reconcile(
            claim, now=now, boundary_hook=boundary_hook
        )
    if reconciled["status"] == "uncertain":
        return {
            "status": "uncertain",
            "stop": "external-operation-uncertain",
            "reason": reconciled["reason"],
            "operation_id": reconciled["operation_id"],
            "projection": replay_program(root, run_id, now=now),
        }
    if reconciled["status"] == "running":
        return {
            "status": "running",
            "operation_id": reconciled["operation_id"],
            "projection": replay_program(root, run_id, now=now),
        }
    record = reconciled["record"]
    projection, receipt = _finish_agent_action(
        root,
        run_id,
        action,
        claim,
        record,
        context,
        config,
        now=now,
        boundary_hook=boundary_hook,
    )
    return {
        "status": "complete",
        "projection": projection,
        "receipt": receipt,
        "operation_id": reconciled["operation_id"],
    }


def _public_action(action: dict[str, object] | None) -> dict[str, object] | None:
    if action is None:
        return None
    return {
        key: action.get(key)
        for key in (
            "action_id", "kind", "address", "phase", "story",
            "workflow_address", "node", "role", "role_address", "attempt",
        )
    }


def tick_program(
    root: Path,
    run_id: str,
    *,
    driver_config: object | None = None,
    adapters: dict[str, object] | None = None,
    now: str | datetime | None = None,
    boundary_hook: BoundaryHook | None = None,
    _expected_binding: dict[str, object] | None = None,
) -> dict[str, object]:
    """Perform one deterministic program scheduling/reconciliation turn."""
    root = root.resolve()
    observed = _time(now, "now")
    config = load_driver_config(root, driver_config)
    with _conductor_lock(root, run_id):
        before = replay_program_conductor(root, run_id, now=observed)
        before_projection = before["authority"]
        if _expected_binding is not None:
            _require(
                all(
                    before_projection.get(key) == _expected_binding.get(key)
                    for key in (
                        "grant_hash", "ledger_head", "generation", "state",
                    )
                ),
                "program act token is stale at the conductor lock",
            )
        before_head = str(before_projection["ledger_head"])
        before_receipts = len(before["receipts"])
        if before_projection["state"] != "running":
            frontier = derive_program_frontier(
                root, run_id, driver_config=config, now=observed
            )
            return _tick_result(
                run_id,
                before_head,
                before_head,
                before_receipts,
                before_receipts,
                frontier,
                None,
                False,
                stop="authority-not-running",
            )
        active = before["active_conductor_claims"]
        _require(len(active) <= 1, "program conductor found multiple unresolved authority claims")
        frontier = derive_program_frontier(
            root,
            run_id,
            driver_config=config,
            now=observed,
            _ignore_active=True,
        )
        actions = frontier["next_actions"]
        if not actions:
            return _tick_result(
                run_id,
                before_head,
                before_head,
                before_receipts,
                before_receipts,
                frontier,
                None,
                False,
                stop=frontier.get("stop"),
            )
        _require(len(actions) == 1, "program conductor frontier exceeded its deterministic writable lane")
        action = actions[0]
        if active:
            key = str(active[0]["idempotency_key"])
            expected_prefix = f"program-conductor/{action['action_id']}/"
            _require(key.startswith(expected_prefix), "active program claim is outside the rebuilt frontier")
        context = _current_program_context(
            root, run_id, before_projection, config
        )
        execution: dict[str, object]
        if action["kind"] == "scope-completion":
            execution = _execute_scope_completion(
                root,
                run_id,
                action,
                config,
                now=observed,
                boundary_hook=boundary_hook,
            )
        elif action["kind"] in {
            "outward-fact",
            "selection",
            "assignment",
            "loop-round",
            "nudge",
        }:
            category = (
                "loop-round"
                if action["kind"] == "loop-round"
                else str(action["kind"])
            )
            projection, receipt = _local_action(
                root,
                run_id,
                action,
                category=category,
                subject_hash=str(action["subject_hash"]),
                payload=dict(action["payload"]),
                now=observed,
                driver_config=config,
                boundary_hook=boundary_hook,
                result=str(action.get("local_result", "complete")),
                route=action.get("local_route"),
            )
            execution = {
                "status": "complete",
                "projection": projection,
                "receipt": receipt,
            }
        elif action["kind"] == "check":
            execution = _execute_check_action(
                root, run_id, action, context, config, now=observed,
                boundary_hook=boundary_hook,
            )
        elif action["kind"] == "collect":
            execution = _execute_collect_action(
                root, run_id, action, context, config, now=observed,
                boundary_hook=boundary_hook,
            )
        elif action["kind"] == "architecture-boundary":
            execution = _execute_architecture_boundary(
                root, run_id, action, config, now=observed,
                boundary_hook=boundary_hook,
            )
        elif action["kind"] == "architecture-gate":
            execution = _execute_architecture_gate(
                root, run_id, action, config, now=observed,
                boundary_hook=boundary_hook,
            )
        elif action["kind"] in {
            "debate-round", "council-decision",
            "meta-verdict-issuance", "architect-verdict-issuance",
            "obligation-ingestion", "checkpoint-request",
        }:
            execution = _execute_deliberation_local_action(
                root, run_id, action, config, now=observed,
                boundary_hook=boundary_hook,
            )
        else:
            manager = ProgramDriverManager(
                root, run_id, config, adapters=adapters
            )
            execution = _execute_agent_action(
                root,
                run_id,
                action,
                context,
                manager,
                config,
                now=observed,
                boundary_hook=boundary_hook,
            )
        after = replay_program_conductor(root, run_id, now=observed)
        after_projection = after["authority"]
        progressed = (
            str(after_projection["ledger_head"]) != before_head
            or len(after["receipts"]) != before_receipts
            or execution["status"] == "running"
        )
        if execution["status"] == "uncertain":
            after_frontier = {
                **frontier,
                "state": "stopped",
                "stop": execution["stop"],
                "next_actions": [],
            }
            stop = str(execution["stop"])
        else:
            after_frontier = derive_program_frontier(
                root, run_id, driver_config=config, now=observed
            )
            stop = after_frontier.get("stop")
        return _tick_result(
            run_id,
            before_head,
            str(after_projection["ledger_head"]),
            before_receipts,
            len(after["receipts"]),
            after_frontier,
            action,
            progressed,
            operation_id=execution.get("operation_id"),
            execution_status=str(execution["status"]),
            stop=stop,
            reason=execution.get("reason"),
        )


def _tick_result(
    run_id: str,
    before_head: str,
    after_head: str,
    before_receipts: int,
    after_receipts: int,
    frontier: dict[str, object],
    action: dict[str, object] | None,
    progressed: bool,
    *,
    operation_id: object = None,
    execution_status: str | None = None,
    stop: object = None,
    reason: object = None,
) -> dict[str, object]:
    state = str(frontier["state"])
    terminal = bool(frontier.get("terminal"))
    checkpoint = bool(frontier.get("checkpoint"))
    return {
        "kind": PROGRAM_TICK_KIND,
        "schema_version": PROGRAM_CONDUCTOR_SCHEMA_VERSION,
        "run_id": run_id,
        "state": state,
        "terminal": terminal,
        "checkpoint": checkpoint,
        "progressed": progressed,
        "before_ledger_head": before_head,
        "after_ledger_head": after_head,
        "receipts_before": before_receipts,
        "receipts_after": after_receipts,
        "action": _public_action(action),
        "execution_status": execution_status,
        "operation_id": operation_id,
        "stop": stop,
        "reason": reason,
        "next_action_count": len(frontier.get("next_actions", [])),
        "lineage": frontier.get("lineage"),
        "next_poll_seconds": 0 if execution_status == "running" else None,
        "content_safe": True,
    }


def supervise_program(
    root: Path,
    run_id: str,
    *,
    max_ticks: int = 100,
    max_seconds: int = 300,
    driver_config: object | None = None,
    adapters: dict[str, object] | None = None,
    now: str | datetime | None = None,
    boundary_hook: BoundaryHook | None = None,
) -> dict[str, object]:
    """Repeat only ``tick_program`` within explicit finite ceilings."""
    _require(
        isinstance(max_ticks, int) and not isinstance(max_ticks, bool)
        and 1 <= max_ticks <= 10_000,
        "program supervisor max_ticks must be between 1 and 10000",
    )
    _require(
        isinstance(max_seconds, int) and not isinstance(max_seconds, bool)
        and 1 <= max_seconds <= 86_400,
        "program supervisor max_seconds must be between 1 and 86400",
    )
    started = time.monotonic()
    ticks: list[dict[str, object]] = []
    stop = "tick-ceiling"
    for _index in range(max_ticks):
        if time.monotonic() - started >= max_seconds:
            stop = "time-ceiling"
            break
        tick = tick_program(
            root,
            run_id,
            driver_config=driver_config,
            adapters=adapters,
            now=now,
            boundary_hook=boundary_hook,
        )
        ticks.append(tick)
        if tick["terminal"]:
            stop = "terminal"
            break
        if tick["checkpoint"]:
            stop = "checkpoint"
            break
        if tick["stop"] in RECONCILIATION_STOPS or (
            tick["stop"] is not None
            and tick["execution_status"] != "running"
            and tick["state"] == "stopped"
        ):
            stop = str(tick["stop"])
            break
        if not tick["progressed"]:
            stop = str(tick["stop"] or "no-progress")
            break
    last = ticks[-1] if ticks else None
    return {
        "kind": PROGRAM_SUPERVISION_KIND,
        "schema_version": PROGRAM_CONDUCTOR_SCHEMA_VERSION,
        "run_id": run_id,
        "ticks": len(ticks),
        "stop": stop,
        "state": last["state"] if last else "not-started",
        "terminal": bool(last and last["terminal"]),
        "checkpoint": bool(last and last["checkpoint"]),
        "progressed": any(bool(item["progressed"]) for item in ticks),
        "last_tick": last,
        "bounded": True,
    }
