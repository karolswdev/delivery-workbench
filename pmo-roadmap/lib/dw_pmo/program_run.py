"""Finite local authority and replay ledger for Phase 26 programs.

The program compiler and planner are policy and observation only.  This module
adds the separate consent boundary required by WLA-26-08: one pure start
preview, one immutable grant, and one hash-chained ledger whose replay is the
only runtime authority.  It deliberately does not conduct workflow nodes or
perform repository/roadmap acts; WLA-26-09/10 consume these claims later.
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
import secrets
import shutil
import subprocess
import tempfile
from typing import Iterator

from . import repofacts
from .gitio import current_branch, head_sha, in_rewrite_state, run_git, write_tree
from .model import DwError
from .orchestration import canonical_json
from .orchestration_driver import (
    driver_capability,
    driver_inventory,
    load_driver_config,
)
from .test_baseline import (
    validate_baseline_fact,
    validate_test_debt_obligation,
)
from .programs import (
    BUDGET_DEFAULTS,
    MODE_CEILINGS,
    PROGRAM_CAPABILITIES,
    _assign_team,
    build_program_plan,
    compile_program_path,
    find_program_path,
)


PROGRAM_RUN_SCHEMA_VERSION = 1
PROGRAM_START_PLAN_KIND = "delivery-workbench-program-start-plan"
PROGRAM_GRANT_KIND = "delivery-workbench-program-grant"
PROGRAM_EVENT_KIND = "delivery-workbench-program-event"
PROGRAM_PROJECTION_KIND = "delivery-workbench-program-projection"
PROGRAM_CLAIM_PREVIEW_KIND = "delivery-workbench-program-claim-preview"
PROGRAM_COMPLETION_PREVIEW_KIND = "delivery-workbench-program-completion-preview"
PROGRAM_CONTROL_PREVIEW_KIND = "delivery-workbench-program-control-preview"
PROGRAM_CHILD_GRANT_KIND = "delivery-workbench-program-child-grant"
PROGRAM_RUN_LIST_KIND = "delivery-workbench-program-run-list"

PROGRAM_STATES = (
    "advisory", "running", "checkpoint", "paused", "expired",
    "exhausted", "revoked", "cancelled", "complete",
)
CONTROL_ACTIONS = ("pause", "resume", "revoke", "cancel")
CONTROL_DECISIONS = ("approve", "deny")
COMPLETION_RESULTS = ("succeeded", "failed", "refused", "lost", "cancelled")

_CONTROL_ALLOWED_STATES = {
    "pause": {"running", "checkpoint"},
    "resume": {"paused"},
    "revoke": {"running", "checkpoint", "paused", "expired", "exhausted", "advisory"},
    "cancel": {"running", "checkpoint", "paused", "expired", "exhausted"},
}

PROGRAM_PERMANENT_EXCLUSIONS = (
    "arbitrary-command",
    "arbitrary-network-destination",
    "authority-minting",
    "conflict-resolution",
    "credential-read",
    "cross-repository-write",
    "git-merge",
    "policy-edit",
    "publication",
    "release",
    "deployment",
)

_SAFE_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:@/-]{0,255}$")
_RUN_ID_RE = re.compile(r"^program-[0-9a-f]{24}$")
_HASH_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
_REF_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_./:@+-]{0,511}$")
_MODE_RANK = {mode: index for index, mode in enumerate(MODE_CEILINGS)}
_MAX_GRANT_SECONDS = 31_536_000

_START_PLAN_KEYS = {
    "kind", "schema_version", "applicable", "issues", "request",
    "planning", "program", "repository", "roadmap", "scope", "selection",
    "roster", "authority", "worst_case", "approval", "plan_hash",
    "start_token", "starts_work", "writes_policy", "writes_roadmap",
    "writes_run_state", "creates_grant",
}
_START_REQUEST_KEYS = {
    "program", "mode", "operator", "approval_reason", "intent_id",
    "capabilities", "budgets", "issued_at", "expires_at", "remote",
    "remote_ref",
}
_OPERATOR_KEYS = {"id", "principal_fingerprint"}
_APPROVAL_KEYS = {"action", "decision", "reason", "operator", "intent_id"}
_REPOSITORY_KEYS = {
    "id", "branch", "head", "index_tree", "operation", "clean",
    "change_count", "worktree_hash", "remote", "remote_ref",
    "remote_url_hash", "remote_head", "fast_forward_observed",
}
_ROADMAP_KEYS = {"project", "snapshot_hash", "healthy", "warning_count"}
_ROSTER_KEYS = {
    "roster_hash", "assignment_hash", "organization", "team", "seats",
    "councils", "separation",
}
_SEAT_KEYS = {
    "address", "role", "duty", "slot", "agent", "profile",
    "principal_fingerprint", "assignment_generation", "workspace_domain",
    "session_binding_key", "execution", "authority_ceiling",
}
_EXECUTION_KEYS = {
    "harness", "adapter", "adapter_version", "router", "provider",
    "model_vendor", "model_family", "model", "model_revision",
    "model_binding", "auth_domain_fingerprint", "capability_fingerprint",
}
_COUNCIL_KEYS = {
    "id", "members", "quorum", "method", "chair_seat", "decider_seat",
    "primary_authority", "tie_authority", "audit",
}
_AUTHORITY_KEYS = {
    "mode", "capabilities", "budgets", "stop_conditions",
    "checkpoint_ports", "child_capability_ceiling", "permanent_exclusions",
    "cost_accounting",
}
_GRANT_KEYS = {
    "kind", "schema_version", "run_id", "grant_hash", "plan_hash",
    "start_token", "program_selector", "program", "repository", "roadmap",
    "scope", "selection", "roster", "authority", "operator", "approval",
    "issued_at", "expires_at", "revocation_generation",
    "permanent_exclusions",
}
_EVENT_KEYS = {
    "kind", "schema_version", "run_id", "seq", "event", "generation",
    "at", "prev_hash", "detail", "event_hash",
}
_EVENT_DETAIL_KEYS = {
    "program_started": {
        "plan_hash", "grant_hash", "program_bundle_hash", "roster_hash",
        "mode", "expires_at",
    },
    "claim_reserved": {
        "claim_id", "idempotency_key", "request_hash", "category",
        "subject", "capability", "decision", "reason", "budget",
        "resource_estimate", "child_grant_hash", "request_port",
    },
    "claim_completed": {
        "claim_id", "request_hash", "result", "receipt_hash", "reason",
        "fact_binding",
    },
    "claim_dispatched": {
        "claim_id", "request_hash", "operation_id", "packet_hash",
        "idempotency_key", "profile", "adapter", "adapter_version",
        "execution", "child_grant_hash",
    },
    "test_baseline_captured": {"baseline"},
    "test_debt_recorded": {"baseline_hash", "obligations", "obligation_hashes"},
    "program_obligation_recorded": {
        "claim_id", "request_hash", "decision_hash", "obligation",
        "obligation_hash",
    },
    "program_obligation_disposed": {
        "claim_id", "request_hash", "obligation_id", "from_state",
        "to_state", "actor", "authority", "reason", "replacement_id",
    },
    "program_delivery_facts_recorded": {
        "claim_id", "request_hash", "proof_hash", "story_ids",
        "files_touched", "head_sha", "verdict_outcome", "obligation_ids",
    },
    "program_scope_completed": {
        "claim_id", "request_hash", "proof_hash", "completed_stories",
        "completed_phases", "open_obligation_ids",
    },
    "program_paused": {
        "action", "reason", "decision", "token_hash", "from_state",
        "to_state", "new_generation", "expired_request_ids",
        "interrupt_claim_ids",
    },
    "program_resumed": {
        "action", "reason", "decision", "token_hash", "from_state",
        "to_state", "new_generation", "expired_request_ids",
        "interrupt_claim_ids",
    },
    "program_revoked": {
        "action", "reason", "decision", "token_hash", "from_state",
        "to_state", "new_generation", "expired_request_ids",
        "interrupt_claim_ids",
    },
    "program_cancelled": {
        "action", "reason", "decision", "token_hash", "from_state",
        "to_state", "new_generation", "expired_request_ids",
        "interrupt_claim_ids",
    },
    "program_exhausted": {
        "counter", "used", "limit", "request_hash",
    },
}

_OBLIGATION_KEYS = {
    "id", "kind", "statement", "priority", "blocking",
    "accountable_role", "target", "citations", "acceptance", "state",
}
_OBLIGATION_KINDS = {
    "backlog", "technical-debt", "risk", "research", "follow-up",
}
_OBLIGATION_PRIORITIES = {"critical", "high", "medium", "low"}
_OBLIGATION_STATES = {
    "open", "in-progress", "completed", "superseded", "waived",
    "escalated",
}
_OBLIGATION_TERMINAL_STATES = {
    "completed", "superseded", "waived", "escalated",
}
_CLAIM_PREVIEW_KEYS = {
    "kind", "schema_version", "run_id", "applicable", "issues", "request",
    "binding", "budget", "child_grant", "exhaustion", "claim_token",
    "starts_work", "writes_state", "dispatches_child", "mutates_repository",
    "mutates_roadmap",
}
_CLAIM_REQUEST_KEYS = {
    "category", "subject", "idempotency_key", "decision", "reason",
    "resource_estimate", "request_port",
}
_SUBJECT_KEYS = {"kind", "id", "hash", "phase", "story"}
_RESOURCE_KEYS = {
    "artifact_bytes", "tokens", "observed_cost_microunits",
}
_BINDING_KEYS = {
    "grant_hash", "ledger_head", "generation", "state", "observed_at",
}
_COMPLETION_PREVIEW_KEYS = {
    "kind", "schema_version", "run_id", "applicable", "issues", "request",
    "binding", "fact_binding", "completion_token", "starts_work",
    "writes_state", "mutates_repository", "mutates_roadmap",
}
_COMPLETION_REQUEST_KEYS = {
    "claim_id", "result", "receipt_hash", "reason",
}
_CONTROL_PREVIEW_KEYS = {
    "kind", "schema_version", "run_id", "applicable", "issues", "request",
    "binding", "effect", "control_token", "starts_work", "writes_state",
    "dispatches_child", "mutates_repository", "mutates_roadmap",
}
_CONTROL_REQUEST_KEYS = {"action", "decision", "reason"}
_CONTROL_EFFECT_KEYS = {
    "from_state", "to_state", "new_generation", "expired_request_ids",
    "interrupt_claim_ids",
}
_CHILD_GRANT_KEYS = {
    "kind", "schema_version", "parent_run_id", "parent_grant_hash",
    "parent_ledger_head", "generation", "role", "node_address",
    "repository", "roadmap", "capabilities", "budgets", "expires_at",
    "permanent_exclusions", "grant_hash", "starts_work", "writes_state",
}
_FACT_BINDING_KEYS = {"repository", "roadmap"}

_ROLE_CAPABILITIES = {
    "implementer": {"agent:dispatch", "workspace:write"},
    "repairer": {"agent:dispatch", "workspace:write"},
    "researcher": {"agent:dispatch"},
    "critic": {"agent:dispatch", "verdict:issue"},
    "reviewer": {"agent:dispatch", "verdict:issue"},
    "verifier": {"agent:dispatch", "verdict:issue"},
    "meta-verifier": {"agent:dispatch", "verdict:issue"},
    "master-architect": {"agent:dispatch", "verdict:issue"},
    "judge": {"agent:dispatch", "council:decide", "obligation:record"},
}
_NON_DELEGABLE = {
    "program:select", "obligation:materialize", "obligation:disposition",
    "evidence:materialize", "knowledge:lesson-writeback",
    "integration:apply", "contract:generate",
    "certification:objective", "certification:verdict", "git:commit",
    "git:push", "roadmap:story-start", "roadmap:story-complete",
    "roadmap:phase-advance",
}

# category -> (required capability, decision, fixed budget reservations)
_CLAIM_RULES: dict[str, tuple[str, str, dict[str, int]]] = {
    "outward-fact": ("program:select", "observe", {}),
    "selection": ("program:select", "select", {"max_stories": 1}),
    "assignment": ("program:select", "bind", {}),
    "child-grant": ("agent:dispatch", "delegate", {"max_child_runs": 1}),
    "agent": (
        "agent:dispatch", "execute",
        {"max_agent_starts": 1, "max_provider_starts": 1, "max_model_starts": 1},
    ),
    "check": ("check:execute", "execute", {"max_check_starts": 1}),
    "council": ("council:decide", "deliberate", {"max_councils": 1}),
    "debate-round": (
        "council:decide", "continue",
        {"max_loop_rounds": 1, "max_debate_rounds": 1},
    ),
    "loop-round": ("agent:dispatch", "continue", {"max_loop_rounds": 1}),
    "verdict": ("verdict:issue", "evaluate", {"max_verdicts": 1}),
    "gate": ("verdict:issue", "evaluate", {}),
    "repair": ("agent:dispatch", "repair", {"max_repairs_per_story": 1}),
    "obligation-record": ("obligation:record", "record", {"max_obligations": 1}),
    "obligation-materialize": (
        "obligation:materialize", "materialize",
        {"max_obligation_materializations": 1},
    ),
    "obligation-disposition": (
        "obligation:disposition", "dispose",
        {"max_obligation_dispositions": 1},
    ),
    "integration": ("integration:apply", "apply", {"max_integrations": 1}),
    "evidence": ("evidence:materialize", "apply", {}),
    "lesson-writeback": (
        "knowledge:lesson-writeback", "record", {"max_lesson_writebacks": 1},
    ),
    "contract": ("contract:generate", "apply", {}),
    "certification-objective": ("certification:objective", "apply", {}),
    "certification-verdict": ("certification:verdict", "apply", {}),
    "commit": ("git:commit", "apply", {"max_commits": 1}),
    "push": ("git:push", "apply", {"max_pushes": 1}),
    "story-start": ("roadmap:story-start", "apply", {}),
    "story-complete": ("roadmap:story-complete", "apply", {}),
    "phase-advance": ("roadmap:phase-advance", "apply", {}),
    "nudge": ("nudge:deliver", "deliver", {"max_nudges": 1}),
    "notification": ("notification:send", "send", {}),
    "checkpoint-request": ("program:select", "request", {}),
}


def _sha(value: object) -> str:
    return "sha256:" + hashlib.sha256(
        canonical_json(value).encode("utf-8")
    ).hexdigest()


def _difference_paths(left: object, right: object, path: str = "") -> list[str]:
    """Return bounded structural difference pointers for stale-plan diagnostics."""
    if type(left) is not type(right):
        return [path or "/"]
    if isinstance(left, dict):
        differences: list[str] = []
        for key in sorted(set(left) | set(right)):
            pointer = f"{path}/{key}"
            if key not in left or key not in right:
                differences.append(pointer)
            else:
                differences.extend(_difference_paths(left[key], right[key], pointer))
            if len(differences) >= 8:
                break
        return differences[:8]
    if isinstance(left, list):
        if len(left) != len(right):
            return [path or "/"]
        differences = []
        for index, (left_item, right_item) in enumerate(zip(left, right)):
            differences.extend(
                _difference_paths(left_item, right_item, f"{path}/{index}")
            )
            if len(differences) >= 8:
                break
        return differences[:8]
    return [] if left == right else [path or "/"]


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise DwError(message)


def _exact(value: object, keys: set[str], label: str) -> dict[str, object]:
    _require(isinstance(value, dict), f"{label} must be an object")
    unknown = sorted(set(value) - keys)
    missing = sorted(keys - set(value))
    _require(
        not unknown and not missing,
        f"{label} must use exact keys"
        + (f"; unknown: {', '.join(unknown)}" if unknown else "")
        + (f"; missing: {', '.join(missing)}" if missing else ""),
    )
    return value


def _hash(value: object, label: str) -> str:
    _require(isinstance(value, str) and bool(_HASH_RE.fullmatch(value)), f"{label} must be a sha256 hash")
    return value


def _safe(value: object, label: str, *, reference: bool = False) -> str:
    pattern = _REF_RE if reference else _SAFE_ID_RE
    _require(isinstance(value, str) and bool(pattern.fullmatch(value)), f"{label} is unsafe")
    return value


def _text(value: object, label: str, maximum: int = 1_000) -> str:
    _require(
        isinstance(value, str) and 0 < len(value.encode("utf-8")) <= maximum
        and "\x00" not in value,
        f"{label} must be non-empty and at most {maximum} bytes",
    )
    return value


def _time(value: str | datetime | None, label: str, default: datetime | None = None) -> datetime:
    if value is None:
        parsed = default or datetime.now(timezone.utc)
    elif isinstance(value, datetime):
        parsed = value
    else:
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except (TypeError, ValueError) as exc:
            raise DwError(f"{label} must be an ISO-8601 timestamp") from exc
    _require(parsed.tzinfo is not None, f"{label} must include a timezone")
    return parsed.astimezone(timezone.utc).replace(microsecond=0)


def _format_time(value: datetime) -> str:
    return value.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _git_dir(root: Path) -> Path:
    # WLA-28-02: the repository-fact boundary owns this resolution and
    # memoizes it per root. Program authority still refuses a non-repository,
    # so the boundary's error is translated to this module's refusal.
    try:
        return repofacts.git_dir(root)
    except DwError as exc:
        raise DwError("program authority requires a Git repository") from exc


def program_store_dir(root: Path) -> Path:
    return _git_dir(root) / "pmo-programs"


def _run_dir(root: Path, run_id: str) -> Path:
    _require(bool(_RUN_ID_RE.fullmatch(run_id or "")), "unsafe program run id")
    runs = (program_store_dir(root) / "runs").resolve()
    path = (runs / run_id).resolve()
    _require(path.parent == runs, "program run path escapes the store")
    return path


def _repository_id(root: Path) -> str:
    return _sha({"root": str(root.resolve()), "git_dir": str(_git_dir(root))})


def _remote_observation(
    root: Path,
    remote: str | None,
    remote_ref: str | None,
    *,
    head: str | None = None,
) -> dict[str, object]:
    # WLA-28-03: ``head`` is the HEAD already observed by this derivation. It
    # is passed in rather than re-read so one observation asks git for HEAD
    # once. This is not a cache: nothing is retained between observations, and
    # a caller that does not supply it still gets a fresh read.
    if remote is None and remote_ref is None:
        return {
            "remote": None, "remote_ref": None, "remote_url_hash": None,
            "remote_head": None, "fast_forward_observed": None,
        }
    _require(remote is not None and remote_ref is not None, "remote and remote_ref must be supplied together")
    _safe(remote, "remote")
    _safe(remote_ref, "remote_ref", reference=True)
    url = (run_git(root, "remote", "get-url", remote) or "").strip()
    _require(bool(url), f"Git remote {remote!r} is not configured")
    remote_head = (run_git(root, "rev-parse", "--verify", remote_ref) or "").strip() or None
    if head is None:
        head = head_sha(root)
    fast_forward: bool | None = None
    if remote_head and head:
        try:
            completed = subprocess.run(
                ["git", "-C", str(root), "merge-base", "--is-ancestor", remote_head, head],
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=False,
            )
            fast_forward = completed.returncode == 0
        except OSError:
            fast_forward = None
    return {
        "remote": remote,
        "remote_ref": remote_ref,
        "remote_url_hash": _sha({"remote": remote, "url": url}),
        "remote_head": remote_head,
        "fast_forward_observed": fast_forward,
    }


def _program_signal_branch(
    remote: str | None,
    remote_ref: str | None,
) -> str | None:
    """Resolve one exact remote-tracking ref to its signal-channel branch."""
    if remote is None or remote_ref is None:
        return None
    for prefix in (
        f"refs/remotes/{remote}/",
        f"{remote}/",
    ):
        if remote_ref.startswith(prefix):
            branch = remote_ref[len(prefix):]
            if branch and branch != "HEAD":
                return branch
    return None


def _repository_facts(root: Path, remote: str | None = None, remote_ref: str | None = None) -> dict[str, object]:
    porcelain = run_git(root, "status", "--porcelain=v1", "-z", "--untracked-files=all")
    _require(porcelain is not None, "cannot observe repository status")
    changes = len([item for item in porcelain.split("\x00") if item])
    # WLA-28-03: one observation reads HEAD once. The remote leg used to
    # re-read it independently, so a repository with a remote configured spawned
    # `rev-parse --verify HEAD` twice to answer a single question.
    head = head_sha(root)
    return {
        "id": _repository_id(root),
        "branch": current_branch(root),
        "head": head or "none",
        "index_tree": write_tree(root) or "unknown",
        "operation": "rewrite" if in_rewrite_state(root) else "normal",
        "clean": changes == 0,
        "change_count": changes,
        "worktree_hash": _sha({"porcelain": porcelain}),
        **_remote_observation(root, remote, remote_ref, head=head),
    }


def _operator(value: object) -> dict[str, str]:
    if isinstance(value, str):
        operator_id = _safe(value, "operator")
        return {
            "id": operator_id,
            "principal_fingerprint": _sha({"operator": operator_id}),
        }
    raw = _exact(value, _OPERATOR_KEYS, "operator")
    return {
        "id": _safe(raw["id"], "operator.id"),
        "principal_fingerprint": _hash(raw["principal_fingerprint"], "operator.principal_fingerprint"),
    }


def _normalize_capabilities(value: object) -> list[str]:
    _require(isinstance(value, list), "program capabilities must be a list")
    _require(
        len(value) == len(set(value))
        and all(isinstance(item, str) and item in PROGRAM_CAPABILITIES for item in value),
        "program capabilities must be unique contracted names",
    )
    return sorted(value)


def _normalize_budgets(value: object, policy: dict[str, object]) -> tuple[dict[str, int], list[str]]:
    raw = value if value is not None else {}
    _require(isinstance(raw, dict), "grant budgets must be an object")
    _require(not (set(raw) - set(BUDGET_DEFAULTS)), "grant budgets contain an unknown counter")
    issues: list[str] = []
    normalized: dict[str, int] = {}
    for key in BUDGET_DEFAULTS:
        maximum = policy.get(key)
        _require(isinstance(maximum, int) and not isinstance(maximum, bool) and maximum > 0, f"policy budget {key} is invalid")
        candidate = raw.get(key, maximum)
        if isinstance(candidate, bool) or not isinstance(candidate, int) or candidate <= 0:
            issues.append(f"grant budget {key} must be finite and positive")
            candidate = int(maximum)
        if int(candidate) > int(maximum):
            issues.append(f"grant budget {key} exceeds policy ceiling")
        normalized[key] = int(candidate)
    return normalized, issues


def _capability_issues(mode: str, capabilities: list[str], requested: list[str]) -> list[str]:
    issues: list[str] = []
    chosen = set(capabilities)
    policy = set(requested)
    if not chosen <= policy:
        issues.append("grant capabilities exceed tracked program policy")
    if mode == "advisory" and chosen:
        issues.append("advisory mode authorizes no dispatch or mutation capability")
    if mode != "advisory":
        for required in ("program:select", "agent:dispatch"):
            if required not in chosen:
                issues.append(f"{mode} mode requires {required}")
    prerequisites = {
        "workspace:write": {"agent:dispatch"},
        "verdict:issue": {"agent:dispatch"},
        "council:decide": {"agent:dispatch", "verdict:issue"},
        "obligation:record": {"council:decide"},
        "obligation:materialize": {"obligation:record"},
        "obligation:disposition": {"obligation:record"},
        "certification:verdict": {"verdict:issue"},
        "git:commit": {"contract:generate"},
        "git:push": {"git:commit"},
        "roadmap:phase-advance": {"roadmap:story-complete"},
    }
    for capability, required in prerequisites.items():
        if capability in chosen and not required <= chosen:
            issues.append(
                f"{capability} is missing prerequisite(s): "
                + ", ".join(sorted(required - chosen))
            )
    if "roadmap:story-complete" in chosen:
        if "evidence:materialize" not in chosen:
            issues.append("roadmap:story-complete requires evidence:materialize")
        if not ({"certification:objective", "certification:verdict"} & chosen):
            issues.append("roadmap:story-complete requires an explicit certification capability")
    return issues


def _checkpoint_ports(compiled: dict[str, object], binding_id: str | None) -> list[dict[str, object]]:
    ports: list[dict[str, object]] = [
        {"id": "program-start", "kind": "system", "address": "program/start"},
        {"id": "story-boundary", "kind": "system", "address": "program/story-boundary"},
        {"id": "phase-boundary", "kind": "system", "address": "program/phase-boundary"},
    ]
    instances = compiled.get("references", {}).get("workflow_instances", {})  # type: ignore[union-attr]
    instance = instances.get(binding_id) if isinstance(instances, dict) and binding_id else None
    if isinstance(instance, dict):
        for node in instance.get("expanded_nodes", []):
            if isinstance(node, dict) and node.get("type") == "checkpoint":
                ports.append({
                    "id": str(node["address"]),
                    "kind": "workflow",
                    "address": str(node["address"]),
                })
        if any(
            isinstance(debate, dict)
            and debate.get("tie_policy") == "checkpoint"
            for debate in instance.get("debates", [])
        ):
            ports.append({
                "id": "program-decision-checkpoint",
                "kind": "workflow",
                "address": "program/decision-checkpoint",
            })
    ports.sort(key=lambda item: (str(item["kind"]), str(item["id"])))
    return ports


def _roster(assignment: dict[str, object], capabilities: list[str], workflow: dict[str, object] | None) -> dict[str, object]:
    selected = set(capabilities)
    seats: list[dict[str, object]] = []
    role_map: dict[str, dict[str, object]] = {}
    council_judge_roles = {
        str(council.get("judge"))
        for council in assignment.get("councils", [])
        if isinstance(council, dict) and council.get("judge") is not None
    }
    for role in assignment.get("roles", []):
        if not isinstance(role, dict):
            continue
        role_id = str(role["role"])
        role_map[role_id] = role
        packet = role.get("packet_policy", {})
        packet_caps = set(packet.get("effective_capability_ceiling", [])) if isinstance(packet, dict) else set()
        duty_caps = set(_ROLE_CAPABILITIES.get(str(role.get("duty")), {"agent:dispatch"}))
        if role_id in council_judge_roles:
            duty_caps.update({"council:decide", "obligation:record"})
        declared_caps = set(role.get("capability_ceiling", packet_caps))
        ceiling = sorted(selected & declared_caps & (packet_caps | duty_caps))
        for member in role.get("members", []):
            if not isinstance(member, dict):
                continue
            execution = _exact(member.get("execution"), _EXECUTION_KEYS, "assignment execution")
            seats.append({
                "address": str(member["address"]),
                "role": role_id,
                "duty": str(role["duty"]),
                "slot": int(member["slot"]),
                "agent": str(member["agent"]),
                "profile": str(member["profile"]),
                "principal_fingerprint": _hash(member["principal_fingerprint"], "seat principal"),
                "assignment_generation": int(member["assignment_generation"]),
                "workspace_domain": str(member["workspace_domain"]),
                "session_binding_key": _hash(member["session_binding_key"], "seat session"),
                "execution": dict(execution),
                "authority_ceiling": ceiling,
            })
    seats.sort(key=lambda item: str(item["address"]))
    by_role = {
        role: [seat for seat in seats if seat["role"] == role]
        for role in role_map
    }
    debates = workflow.get("debates", []) if isinstance(workflow, dict) else []
    councils: list[dict[str, object]] = []
    for council in assignment.get("councils", []):
        if not isinstance(council, dict):
            continue
        judge_role = str(council.get("judge"))
        chair = by_role.get(judge_role, [None])[0]
        chair_address = chair.get("address") if isinstance(chair, dict) else None
        decision = council.get("decision", {})
        method = str(decision.get("method", "majority")) if isinstance(decision, dict) else "majority"
        council_roles = set(council.get("members", []))
        matching_ties = {
            str(debate.get("tie_policy"))
            for debate in debates
            if isinstance(debate, dict)
            and debate.get("judge_role") == judge_role
            and set(debate.get("participants", [])) | {judge_role} == council_roles
        }
        _require(len(matching_ties) <= 1, "one council cannot have conflicting tie authorities in the selected workflow")
        tie_authority = next(iter(matching_ties), "none")
        _require(tie_authority in {"none", "judge", "checkpoint", "dissent"}, "council tie authority is unsupported")
        uses_agent_decider = method == "judge" or tie_authority == "judge"
        councils.append({
            "id": str(council["id"]),
            "members": list(council.get("assigned_members", [])),
            "quorum": int(council["quorum"]),
            "method": method,
            "chair_seat": chair_address,
            "decider_seat": chair_address if uses_agent_decider else None,
            "primary_authority": "judge" if method == "judge" else "rule",
            "tie_authority": tie_authority,
            "audit": dict(council.get("audit", {})),
        })
    councils.sort(key=lambda item: str(item["id"]))
    separation = dict(assignment.get("separation", {}))
    if assignment.get("diversity"):
        separation["diversity"] = dict(assignment["diversity"])
    return {
        "roster_hash": _hash(assignment["roster_hash"], "roster hash"),
        "assignment_hash": _hash(assignment["assignment_hash"], "assignment hash"),
        "organization": str(assignment["organization"]),
        "team": str(assignment["team"]),
        "seats": seats,
        "councils": councils,
        "separation": separation,
    }


def _scope_roster(
    compiled: dict[str, object],
    planning: dict[str, object],
    capabilities: list[str],
    driver_config: dict[str, object],
) -> tuple[dict[str, object], list[dict[str, str]]]:
    """Freeze every deterministic seat reachable inside the granted scope."""
    initial = planning.get("assignment")
    selection = planning.get("selection")
    _require(
        isinstance(initial, dict) and isinstance(selection, dict),
        "program planning produced no initial assignment",
    )
    instances = compiled["references"]["workflow_instances"]  # type: ignore[index]
    _require(
        isinstance(instances, dict),
        "compiled program has no workflow instances",
    )
    initial_instance = instances.get(str(selection["binding"]))
    base = _roster(
        initial,
        capabilities,
        initial_instance if isinstance(initial_instance, dict) else None,
    )
    initial_addresses = [
        str(seat["address"]) for seat in base["seats"]  # type: ignore[index]
    ]
    by_address = {
        str(seat["address"]): seat
        for seat in base["seats"]  # type: ignore[index]
    }
    issues: list[dict[str, str]] = []
    bindings = {
        str(binding["id"]): binding
        for binding in compiled["program"]["bindings"]  # type: ignore[index]
        if isinstance(binding, dict)
    }
    binding_by_story = compiled["analysis"]["binding_by_story"]  # type: ignore[index]
    _require(
        isinstance(binding_by_story, dict),
        "compiled program has no scope binding proof",
    )
    for story_id in compiled["program"]["scope"]["story_ids"]:  # type: ignore[index]
        story = str(story_id)
        binding_id = binding_by_story.get(story)
        binding = bindings.get(str(binding_id))
        if binding is None:
            issues.append({
                "code": "binding-missing",
                "message": (
                    f"scope roster cannot bind story {story!r} to one workflow"
                ),
            })
            continue
        try:
            phase = int(story.split("-")[-2])
        except (ValueError, IndexError):
            issues.append({
                "code": "scope-violation",
                "message": f"scope roster cannot parse story {story!r}",
            })
            continue
        assignment, assignment_issues = _assign_team(
            compiled,
            {"id": story, "phase": phase},
            binding,
            driver_config,
        )
        issues.extend(assignment_issues)
        if (
            not isinstance(assignment, dict)
            or not assignment.get("applicable")
        ):
            continue
        workflow = instances.get(str(binding["id"]))
        roster = _roster(
            assignment,
            capabilities,
            workflow if isinstance(workflow, dict) else None,
        )
        _require(
            roster["roster_hash"] == base["roster_hash"],
            "scope assignment resolved a different driver roster",
        )
        for seat in roster["seats"]:  # type: ignore[index]
            address = str(seat["address"])
            prior = by_address.get(address)
            _require(
                prior is None or prior == seat,
                "scope assignments conflict at one stable seat address",
            )
            by_address[address] = seat
    additional_addresses = sorted(
        set(by_address) - set(initial_addresses)
    )
    base["seats"] = [
        by_address[address]
        for address in initial_addresses + additional_addresses
    ]
    return base, issues


def _scope_checkpoint_ports(
    compiled: dict[str, object],
) -> list[dict[str, object]]:
    binding_ids = [
        str(binding["id"])
        for binding in compiled["program"]["bindings"]  # type: ignore[index]
        if isinstance(binding, dict)
    ]
    by_identity: dict[
        tuple[str, str, str], dict[str, object]
    ] = {}
    for binding_id in binding_ids:
        for port in _checkpoint_ports(compiled, binding_id):
            identity = (
                str(port["id"]),
                str(port["kind"]),
                str(port["address"]),
            )
            by_identity[identity] = port
    return [by_identity[key] for key in sorted(by_identity)]


def _validate_roster(value: object) -> dict[str, object]:
    roster = _exact(value, _ROSTER_KEYS, "program roster")
    _hash(roster["roster_hash"], "roster.roster_hash")
    _hash(roster["assignment_hash"], "roster.assignment_hash")
    seats = roster["seats"]
    _require(isinstance(seats, list) and seats, "program roster must contain seats")
    addresses: set[str] = set()
    for index, item in enumerate(seats):
        seat = _exact(item, _SEAT_KEYS, f"roster.seats[{index}]")
        address = _safe(seat["address"], f"roster.seats[{index}].address", reference=True)
        _require(address not in addresses, "program roster seat addresses must be unique")
        addresses.add(address)
        _exact(seat["execution"], _EXECUTION_KEYS, f"roster.seats[{index}].execution")
        _normalize_capabilities(seat["authority_ceiling"])
    councils = roster["councils"]
    _require(isinstance(councils, list), "program roster councils must be a list")
    for index, item in enumerate(councils):
        council = _exact(item, _COUNCIL_KEYS, f"roster.councils[{index}]")
        decider = council["decider_seat"]
        _require(decider is None or decider in addresses, "council decider seat is not assigned")
        _require(council["primary_authority"] in {"rule", "judge"}, "council primary authority is unsupported")
        _require(council["tie_authority"] in {"none", "judge", "checkpoint", "dissent"}, "council tie authority is unsupported")
        needs_decider = council["primary_authority"] == "judge" or council["tie_authority"] == "judge"
        _require((decider is not None) == needs_decider, "council decider seat does not match its declared authority")
    return roster


def _policy_for_plan(root: Path, selector: str) -> dict[str, object]:
    return compile_program_path(root, find_program_path(root, selector))


def build_program_start_plan(
    root: Path,
    program: str,
    *,
    mode: str,
    operator: object,
    approval_reason: str,
    intent_id: str,
    capabilities: list[str] | None = None,
    budgets: dict[str, int] | None = None,
    issued_at: str | datetime | None = None,
    expires_at: str | datetime | None = None,
    remote: str | None = None,
    remote_ref: str | None = None,
    driver_config: dict[str, object] | None = None,
) -> dict[str, object]:
    """Build an exact, pure grant preview over one current program plan."""
    root = root.resolve()
    _require(isinstance(program, str), "program start requires a tracked program selector")
    _safe(program, "program")
    _require(mode in MODE_CEILINGS, "unsupported program mode")
    normalized_operator = _operator(operator)
    reason = _text(approval_reason, "approval_reason", 1_000)
    intent = _safe(intent_id, "intent_id")
    issued = _time(issued_at, "issued_at")

    planning = build_program_plan(root, program, driver_config=driver_config)
    compiled = _policy_for_plan(root, program)
    policy_caps = list(planning["program"]["requested_capabilities"])  # type: ignore[index]
    chosen_caps = _normalize_capabilities(
        [] if mode == "advisory" and capabilities is None
        else list(policy_caps) if capabilities is None
        else capabilities
    )
    policy_budgets = dict(planning["program"]["budgets"])  # type: ignore[index]
    chosen_budgets, budget_issues = _normalize_budgets(budgets, policy_budgets)
    if expires_at is None:
        expiry = issued + timedelta(seconds=min(3_600, chosen_budgets["max_wall_seconds"]))
    else:
        expiry = _time(expires_at, "expires_at")

    issues: list[dict[str, str]] = [
        {"code": str(item["code"]), "message": str(item["message"])}
        for item in planning.get("issues", [])
        if item.get("code") != "scope-complete"
    ]
    if not planning.get("applicable"):
        issues.append({"code": "program-not-applicable", "message": "pure program planning found no grantable current selection"})
    ceiling = str(planning["program"]["mode_ceiling"])  # type: ignore[index]
    if _MODE_RANK[mode] > _MODE_RANK[ceiling]:
        issues.append({"code": "mode-denied", "message": f"{mode} exceeds tracked mode ceiling {ceiling}"})
    for message in _capability_issues(mode, chosen_caps, policy_caps):
        issues.append({"code": "capability-denied", "message": message})
    for message in budget_issues:
        issues.append({"code": "budget-denied", "message": message})
    if expiry <= issued:
        issues.append({"code": "grant-expired", "message": "grant expiry must be later than issuance"})
    lifetime = int((expiry - issued).total_seconds())
    if lifetime > min(_MAX_GRANT_SECONDS, chosen_budgets["max_wall_seconds"]):
        issues.append({"code": "budget-denied", "message": "grant lifetime exceeds its wall-time ceiling"})

    repository = _repository_facts(root, remote, remote_ref)
    if repository["operation"] != "normal":
        issues.append({"code": "repository-stale", "message": "repository is in a rewrite operation"})
    if repository["clean"] is not True:
        issues.append({"code": "repository-stale", "message": "repository worktree must be clean at program start"})
    program_nudges = [
        item
        for item in planning["program"].get("nudges", [])  # type: ignore[union-attr]
        if isinstance(item, dict)
    ]
    if program_nudges:
        signal_branch = _program_signal_branch(remote, remote_ref)
        if signal_branch is None:
            issues.append({
                "code": "capability-denied",
                "message": (
                    "program standing nudge rules require one exact "
                    "remote-tracking ref such as refs/remotes/origin/main"
                ),
            })
        elif repository["remote_head"] is None:
            issues.append({
                "code": "repository-stale",
                "message": (
                    "program standing nudge rules require the exact "
                    "remote-tracking ref to resolve at grant time"
                ),
            })
    if "git:push" in chosen_caps:
        if remote is None or remote_ref is None:
            issues.append({"code": "capability-denied", "message": "git:push requires one exact remote and ref observation"})
        elif repository["fast_forward_observed"] is not True:
            issues.append({"code": "remote-diverged", "message": "remote/ref is absent, divergent, or not observed as a fast-forward base"})

    assignment = planning.get("assignment")
    _require(isinstance(assignment, dict), "program planning produced no assignment document")
    selection = planning.get("selection")
    _require(isinstance(selection, dict), "program planning produced no selection document")
    config = load_driver_config(root, driver_config)
    roster, roster_issues = _scope_roster(
        compiled,
        planning,
        chosen_caps,
        config,
    )
    issues.extend(roster_issues)
    checkpoint_ports = _scope_checkpoint_ports(compiled)

    roadmap = {
        "project": str(planning["roadmap"]["project"]),  # type: ignore[index]
        "snapshot_hash": _hash(planning["roadmap"]["snapshot_hash"], "roadmap snapshot"),  # type: ignore[index]
        "healthy": bool(planning["roadmap"]["healthy"]),  # type: ignore[index]
        "warning_count": len(planning["roadmap"].get("warnings", [])),  # type: ignore[index]
    }
    authority = {
        "mode": mode,
        "capabilities": chosen_caps,
        "budgets": chosen_budgets,
        "stop_conditions": list(planning["program"]["stop_conditions"]),  # type: ignore[index]
        "checkpoint_ports": checkpoint_ports,
        "child_capability_ceiling": sorted(set(chosen_caps) - _NON_DELEGABLE),
        "permanent_exclusions": list(PROGRAM_PERMANENT_EXCLUSIONS),
        "cost_accounting": "observed-only",
    }
    approval = {
        "action": "start-program",
        "decision": "approve",
        "reason": reason,
        "operator": normalized_operator,
        "intent_id": intent,
    }
    request = {
        "program": program,
        "mode": mode,
        "operator": normalized_operator,
        "approval_reason": reason,
        "intent_id": intent,
        "capabilities": chosen_caps,
        "budgets": chosen_budgets,
        "issued_at": _format_time(issued),
        "expires_at": _format_time(expiry),
        "remote": remote,
        "remote_ref": remote_ref,
    }
    workflow_envelope = selection.get("workflow", {}).get("envelope", {})  # type: ignore[union-attr]
    unsigned: dict[str, object] = {
        "kind": PROGRAM_START_PLAN_KIND,
        "schema_version": PROGRAM_RUN_SCHEMA_VERSION,
        "applicable": not issues,
        "issues": issues,
        "request": request,
        "planning": planning,
        "program": dict(planning["program"]),
        "repository": repository,
        "roadmap": roadmap,
        "scope": planning["scope"],
        "selection": selection,
        "roster": roster,
        "authority": authority,
        "worst_case": {
            "grant_budgets": chosen_budgets,
            "selected_workflow_envelope": dict(workflow_envelope),
            "includes_failure_branches": True,
        },
        "approval": approval,
        "starts_work": False,
        "writes_policy": False,
        "writes_roadmap": False,
        "writes_run_state": False,
        "creates_grant": False,
    }
    plan_hash = _sha(unsigned)
    start_token = _sha({
        "action": "start-program", "plan_hash": plan_hash,
        "approval": approval,
    })
    return {**unsigned, "plan_hash": plan_hash, "start_token": start_token}


def _validate_start_plan(value: object) -> dict[str, object]:
    plan = _exact(value, _START_PLAN_KEYS, "program start plan")
    _require(plan["kind"] == PROGRAM_START_PLAN_KIND and plan["schema_version"] == PROGRAM_RUN_SCHEMA_VERSION, "unsupported program start plan")
    _exact(plan["request"], _START_REQUEST_KEYS, "program start request")
    _exact(plan["repository"], _REPOSITORY_KEYS, "program start repository")
    _exact(plan["roadmap"], _ROADMAP_KEYS, "program start roadmap")
    _validate_roster(plan["roster"])
    _exact(plan["authority"], _AUTHORITY_KEYS, "program start authority")
    _exact(plan["approval"], _APPROVAL_KEYS, "program start approval")
    _require(isinstance(plan["applicable"], bool) and isinstance(plan["issues"], list), "program start applicability is invalid")
    for effect in ("starts_work", "writes_policy", "writes_roadmap", "writes_run_state", "creates_grant"):
        _require(plan[effect] is False, f"program start preview {effect} must be false")
    unsigned = {key: value for key, value in plan.items() if key not in {"plan_hash", "start_token"}}
    expected_hash = _sha(unsigned)
    _require(plan["plan_hash"] == expected_hash, "program start plan hash is invalid")
    _require(
        plan["start_token"] == _sha({"action": "start-program", "plan_hash": expected_hash, "approval": plan["approval"]}),
        "program start token is invalid",
    )
    return plan


def _write_new(path: Path, value: object, mode: int = 0o600) -> None:
    data = (json.dumps(value, indent=2, sort_keys=True) + "\n").encode("utf-8")
    with path.open("xb") as handle:
        os.chmod(path, mode)
        handle.write(data)
        handle.flush()
        os.fsync(handle.fileno())


def _grant_hash(grant: dict[str, object]) -> str:
    return _sha({key: value for key, value in grant.items() if key != "grant_hash"})


def _event_document(
    run_id: str,
    seq: int,
    event: str,
    generation: int,
    at: datetime,
    detail: dict[str, object],
    prev_hash: str | None,
) -> dict[str, object]:
    _require(event in _EVENT_DETAIL_KEYS, f"unsupported program event {event!r}")
    _exact(detail, _EVENT_DETAIL_KEYS[event], f"{event} detail")
    unsigned = {
        "kind": PROGRAM_EVENT_KIND,
        "schema_version": PROGRAM_RUN_SCHEMA_VERSION,
        "run_id": run_id,
        "seq": seq,
        "event": event,
        "generation": generation,
        "at": _format_time(at),
        "prev_hash": prev_hash,
        "detail": detail,
    }
    return {**unsigned, "event_hash": _sha(unsigned)}


@contextmanager
def _lock(path: Path) -> Iterator[None]:
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    with path.open("a+b") as handle:
        os.chmod(path, 0o600)
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


def _load_json(path: Path, label: str) -> dict[str, object]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise DwError(f"cannot read {label}: {exc}") from exc
    _require(isinstance(value, dict), f"{label} must be an object")
    return value


def _load_documents(root: Path, run_id: str) -> tuple[Path, dict[str, object], dict[str, object]]:
    path = _run_dir(root, run_id)
    _require(path.is_dir(), f"program run not found: {run_id}")
    grant = _exact(_load_json(path / "grant.json", "program grant"), _GRANT_KEYS, "program grant")
    plan = _validate_start_plan(_load_json(path / "plan.json", "program start plan"))
    _require(grant["kind"] == PROGRAM_GRANT_KIND and grant["schema_version"] == PROGRAM_RUN_SCHEMA_VERSION, "unsupported program grant")
    _require(grant["run_id"] == run_id, "program grant run id mismatch")
    _require(grant["grant_hash"] == _grant_hash(grant), "program grant integrity check failed")
    _require(grant["plan_hash"] == plan["plan_hash"] and grant["start_token"] == plan["start_token"], "program grant does not match its immutable plan")
    expected_from_plan = {
        "program_selector": plan["request"]["program"],
        "program": plan["program"],
        "repository": plan["repository"],
        "roadmap": plan["roadmap"],
        "scope": plan["scope"],
        "selection": plan["selection"],
        "roster": plan["roster"],
        "authority": plan["authority"],
        "operator": plan["approval"]["operator"],
        "approval": plan["approval"],
        "issued_at": plan["request"]["issued_at"],
        "expires_at": plan["request"]["expires_at"],
        "revocation_generation": 0,
    }
    for key, expected in expected_from_plan.items():
        _require(grant[key] == expected, f"program grant {key} differs from its reviewed plan")
    _require(grant["permanent_exclusions"] == list(PROGRAM_PERMANENT_EXCLUSIONS), "program grant exclusions were altered")
    return path, grant, plan


def _find_start_token(root: Path, token: str) -> str | None:
    runs = program_store_dir(root) / "runs"
    if not runs.is_dir():
        return None
    for path in sorted(runs.iterdir(), key=lambda item: item.name):
        if not path.is_dir() or not _RUN_ID_RE.fullmatch(path.name):
            continue
        _path, grant, _plan = _load_documents(root, path.name)
        if grant.get("start_token") == token:
            return path.name
    return None


def start_program(
    root: Path,
    plan: object,
    *,
    start_token: str,
    now: str | datetime | None = None,
    driver_config: dict[str, object] | None = None,
) -> dict[str, object]:
    """Issue exactly one immutable local grant after a byte-exact re-plan."""
    root = root.resolve()
    submitted = _validate_start_plan(plan)
    _require(start_token == submitted["start_token"], "program start token does not match the submitted plan")
    request = submitted["request"]
    _require(bool(submitted["applicable"]), "program start plan is not applicable")
    observed = _time(now, "now")
    _require(observed >= _time(str(submitted["request"]["issued_at"]), "issued_at"), "program start plan is not issued yet")
    _require(observed < _time(str(submitted["request"]["expires_at"]), "expires_at"), "program start plan already expired")

    store = program_store_dir(root)
    # The race lock sits beside, not inside, the program store.  A stale or
    # refused first start therefore creates no run/grant/ledger directory.
    with _lock(_git_dir(root) / "pmo-programs.start.lock"):
        existing = _find_start_token(root, start_token)
        if existing is not None:
            return replay_program(root, existing, now=observed)
        fresh = build_program_start_plan(
            root,
            str(request["program"]),
            mode=str(request["mode"]),
            operator=request["operator"],
            approval_reason=str(request["approval_reason"]),
            intent_id=str(request["intent_id"]),
            capabilities=list(request["capabilities"]),
            budgets=dict(request["budgets"]),
            issued_at=str(request["issued_at"]),
            expires_at=str(request["expires_at"]),
            remote=request["remote"],
            remote_ref=request["remote_ref"],
            driver_config=driver_config,
        )
        differences = _difference_paths(submitted, fresh)
        _require(
            not differences,
            "program start facts changed before grant issuance at "
            + ", ".join(differences),
        )
        runs = store / "runs"
        runs.mkdir(parents=True, exist_ok=True, mode=0o700)
        run_id = "program-" + secrets.token_hex(12)
        while (runs / run_id).exists():
            run_id = "program-" + secrets.token_hex(12)
        grant: dict[str, object] = {
            "kind": PROGRAM_GRANT_KIND,
            "schema_version": PROGRAM_RUN_SCHEMA_VERSION,
            "run_id": run_id,
            "grant_hash": "",
            "plan_hash": submitted["plan_hash"],
            "start_token": submitted["start_token"],
            "program_selector": request["program"],
            "program": submitted["program"],
            "repository": submitted["repository"],
            "roadmap": submitted["roadmap"],
            "scope": submitted["scope"],
            "selection": submitted["selection"],
            "roster": submitted["roster"],
            "authority": submitted["authority"],
            "operator": submitted["approval"]["operator"],  # type: ignore[index]
            "approval": submitted["approval"],
            "issued_at": request["issued_at"],
            "expires_at": request["expires_at"],
            "revocation_generation": 0,
            "permanent_exclusions": list(PROGRAM_PERMANENT_EXCLUSIONS),
        }
        grant["grant_hash"] = _grant_hash(grant)
        first = _event_document(
            run_id, 1, "program_started", 0, observed,
            {
                "plan_hash": submitted["plan_hash"],
                "grant_hash": grant["grant_hash"],
                "program_bundle_hash": submitted["program"]["bundle_hash"],  # type: ignore[index]
                "roster_hash": submitted["roster"]["roster_hash"],  # type: ignore[index]
                "mode": submitted["authority"]["mode"],  # type: ignore[index]
                "expires_at": request["expires_at"],
            },
            None,
        )
        temporary = Path(tempfile.mkdtemp(prefix=".program.", dir=str(runs)))
        try:
            os.chmod(temporary, 0o700)
            _write_new(temporary / "plan.json", submitted, 0o400)
            _write_new(temporary / "grant.json", grant, 0o400)
            ledger = temporary / "ledger.jsonl"
            with ledger.open("xb") as handle:
                os.chmod(ledger, 0o600)
                handle.write((canonical_json(first) + "\n").encode("utf-8"))
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary, runs / run_id)
        finally:
            if temporary.exists():
                shutil.rmtree(temporary, ignore_errors=True)
    return replay_program(root, run_id, now=observed)


def _events(path: Path, run_id: str) -> list[dict[str, object]]:
    ledger = path / "ledger.jsonl"
    try:
        data = ledger.read_bytes()
    except OSError as exc:
        raise DwError(f"cannot read program ledger: {exc}") from exc
    _require(data.endswith(b"\n"), "program ledger is truncated")
    result: list[dict[str, object]] = []
    previous: str | None = None
    prior_at: datetime | None = None
    for index, line in enumerate(data.splitlines(), start=1):
        try:
            raw = json.loads(line)
        except json.JSONDecodeError as exc:
            raise DwError(f"program ledger line {index} is invalid JSON") from exc
        event = _exact(raw, _EVENT_KEYS, f"program ledger event {index}")
        _require(event["kind"] == PROGRAM_EVENT_KIND and event["schema_version"] == PROGRAM_RUN_SCHEMA_VERSION, "unsupported program ledger event")
        _require(event["run_id"] == run_id and event["seq"] == index, "program ledger sequence or run id is invalid")
        _require(event["event"] in _EVENT_DETAIL_KEYS, "program ledger event type is unsupported")
        _exact(event["detail"], _EVENT_DETAIL_KEYS[str(event["event"])], f"program ledger event {index} detail")
        _require(event["prev_hash"] == previous, "program ledger hash chain is broken")
        unsigned = {key: value for key, value in event.items() if key != "event_hash"}
        _require(event["event_hash"] == _sha(unsigned), "program ledger event hash is invalid")
        at = _time(str(event["at"]), "event.at")
        _require(prior_at is None or at >= prior_at, "program ledger timestamps moved backwards")
        previous = str(event["event_hash"])
        prior_at = at
        result.append(event)
    _require(bool(result), "program ledger is empty")
    return result


def _budget_map(value: object) -> dict[str, int]:
    _require(isinstance(value, dict), "claim budget must be an object")
    _require(not (set(value) - set(BUDGET_DEFAULTS)), "claim budget contains an unknown counter")
    result: dict[str, int] = {}
    for key, raw in value.items():
        _require(isinstance(raw, int) and not isinstance(raw, bool) and raw >= 0, f"claim budget {key} must be non-negative")
        if raw:
            result[str(key)] = int(raw)
    return result


def replay_program(root: Path, run_id: str, *, now: str | datetime | None = None) -> dict[str, object]:
    """Validate immutable documents and derive the complete disposable view."""
    path, grant, _plan = _load_documents(root.resolve(), run_id)
    events = _events(path, run_id)
    first = events[0]
    _require(first["event"] == "program_started", "program ledger does not start with program_started")
    _require(first["generation"] == 0, "program_started uses the wrong generation")
    expected_first = {
        "plan_hash": grant["plan_hash"],
        "grant_hash": grant["grant_hash"],
        "program_bundle_hash": grant["program"]["bundle_hash"],  # type: ignore[index]
        "roster_hash": grant["roster"]["roster_hash"],  # type: ignore[index]
        "mode": grant["authority"]["mode"],  # type: ignore[index]
        "expires_at": grant["expires_at"],
    }
    _require(first["detail"] == expected_first, "program_started does not match the grant")
    first_at = _time(str(first["at"]), "program_started.at")
    _require(
        _time(str(grant["issued_at"]), "issued_at") <= first_at
        < _time(str(grant["expires_at"]), "expires_at"),
        "program_started is outside the grant issuance window",
    )

    mode = str(grant["authority"]["mode"])  # type: ignore[index]
    state = "advisory" if mode == "advisory" else "running"
    generation = int(grant["revocation_generation"])
    counters = {key: 0 for key in BUDGET_DEFAULTS}
    active: dict[str, dict[str, object]] = {}
    completed: list[dict[str, object]] = []
    claims: list[dict[str, object]] = []
    dispatches: list[dict[str, object]] = []
    controls: list[dict[str, object]] = []
    obligations: dict[str, dict[str, object]] = {}
    obligation_history: list[dict[str, object]] = []
    delivery_facts: dict[str, object] | None = None
    scope_completion: dict[str, object] | None = None
    selected_stories: set[str] = set()
    selected_phases: set[int] = set()
    idempotency_keys: set[str] = set()
    expected_repository = dict(grant["repository"])
    expected_roadmap = dict(grant["roadmap"])
    exhaustion: dict[str, object] | None = None
    test_baseline: dict[str, object] | None = None
    expires = _time(str(grant["expires_at"]), "expires_at")

    for event in events[1:]:
        detail = event["detail"]
        event_name = str(event["event"])
        event_at = _time(str(event["at"]), "event.at")
        if event_at >= expires and state in {"running", "checkpoint", "paused"}:
            state = "expired"
        event_generation = event["generation"]
        _require(isinstance(event_generation, int) and not isinstance(event_generation, bool), "program event generation is invalid")
        if event_name == "test_baseline_captured":
            _require(event_generation == generation, "test baseline uses the wrong revocation generation")
            _require(state == "running", "test baseline was captured while program was not running")
            _require(test_baseline is None, "program test baseline was amended")
            _require(not dispatches, "program test baseline was captured after dispatch")
            try:
                test_baseline = validate_baseline_fact(detail["baseline"])
            except ValueError as exc:
                raise DwError(str(exc)) from exc
            _require(
                test_baseline["head_sha"] == grant["repository"]["head"],  # type: ignore[index]
                "program test baseline head differs from the granted head",
            )
        elif event_name == "claim_reserved":
            _require(event_generation == generation, "claim uses the wrong revocation generation")
            _require(state == "running", "claim was reserved while program was not running")
            category = str(detail["category"])
            _require(category in _CLAIM_RULES, "claim uses an unsupported category")
            subject = _subject(detail["subject"])
            _require(not _claim_scope_issues(grant, subject), "claim subject is outside the granted scope")
            idempotency_key = _safe(detail["idempotency_key"], "claim idempotency key")
            _require(idempotency_key not in idempotency_keys, "program claim idempotency key was reused")
            idempotency_keys.add(idempotency_key)
            capability, decision, _fixed = _CLAIM_RULES[category]
            _require(detail["capability"] == capability and capability in grant["authority"]["capabilities"], "claim capability differs from its grant/category")  # type: ignore[index]
            _require(detail["decision"] == decision, "claim decision differs from its category")
            _text(detail["reason"], "claim reason", 1_000)
            estimate = _resource_estimate(detail["resource_estimate"])
            if category == "checkpoint-request":
                declared_ports = {
                    str(item["id"])
                    for item in grant["authority"]["checkpoint_ports"]  # type: ignore[index]
                    if isinstance(item, dict) and "id" in item
                }
                _require(detail["request_port"] in declared_ports, "claim uses an undeclared checkpoint port")
            else:
                _require(detail["request_port"] is None, "non-checkpoint claim names a request port")
            if detail["child_grant_hash"] is not None:
                _hash(detail["child_grant_hash"], "claim child grant hash")
                _require(category == "child-grant", "non-child claim names a child grant")
            else:
                _require(category != "child-grant", "child-grant claim omits its authority hash")
            claim_id = str(detail["claim_id"])
            _require(claim_id not in active and all(item["claim_id"] != claim_id for item in completed), "program claim id was reused")
            expected_claim_id = "claim-" + hashlib.sha256(
                f"{run_id}|{idempotency_key}".encode("utf-8")
            ).hexdigest()[:24]
            _require(claim_id == expected_claim_id, "program claim id is not deterministic")
            budget = _budget_map(detail["budget"])
            expected_budget = _claim_budget(
                category,
                subject,
                estimate,
                {
                    "selected_phases": selected_phases,
                    "selected_stories": selected_stories,
                },
            )
            _require(budget == expected_budget, "claim ledger budget differs from its request")
            expected_request = {
                "category": category,
                "subject": subject,
                "idempotency_key": idempotency_key,
                "decision": decision,
                "reason": detail["reason"],
                "resource_estimate": estimate,
                "request_port": detail["request_port"],
            }
            _require(detail["request_hash"] == _sha(expected_request), "claim request hash is invalid")
            for key, amount in budget.items():
                counters[key] += amount
                _require(counters[key] <= int(grant["authority"]["budgets"][key]), f"program ledger exceeds {key}")  # type: ignore[index]
            claim = {
                "claim_id": claim_id,
                "idempotency_key": idempotency_key,
                "request_hash": detail["request_hash"],
                "category": category,
                "subject": subject,
                "capability": capability,
                "decision": decision,
                "reason": detail["reason"],
                "budget": budget,
                "resource_estimate": estimate,
                "child_grant_hash": detail["child_grant_hash"],
                "request_port": detail["request_port"],
                "reserved_at": event["at"],
                "dispatch": None,
                "status": "active",
            }
            active[claim_id] = claim
            claims.append(claim)
            if category == "selection":
                if subject.get("story") is not None:
                    selected_stories.add(str(subject["story"]))
                if subject.get("phase") is not None:
                    selected_phases.add(int(subject["phase"]))
            if category == "checkpoint-request":
                state = "checkpoint"
        elif event_name == "claim_dispatched":
            _require(event_generation == generation, "dispatch uses the wrong revocation generation")
            _require(state == "running", "dispatch was recorded while program was not running")
            claim_id = _safe(detail["claim_id"], "dispatch claim id")
            _require(claim_id in active, "dispatch does not match one active claim")
            claim = active[claim_id]
            _require(claim["category"] == "agent", "only an agent claim may be externally dispatched")
            _require(claim["request_hash"] == detail["request_hash"], "dispatch request hash differs from claim")
            _require(claim.get("dispatch") is None, "program claim was dispatched more than once")
            _safe(detail["operation_id"], "dispatch operation id")
            _hash(detail["packet_hash"], "dispatch packet hash")
            _safe(detail["idempotency_key"], "dispatch idempotency key")
            _safe(detail["profile"], "dispatch profile")
            _safe(detail["adapter"], "dispatch adapter")
            _safe(detail["adapter_version"], "dispatch adapter version", reference=True)
            execution = _exact(detail["execution"], _EXECUTION_KEYS, "dispatch execution")
            for field in ("auth_domain_fingerprint", "capability_fingerprint"):
                _hash(execution[field], f"dispatch execution {field}")
            child_hash = detail["child_grant_hash"]
            _require(child_hash is None or isinstance(child_hash, str), "dispatch child grant hash is invalid")
            if child_hash is not None:
                _hash(child_hash, "dispatch child grant hash")
            _require(child_hash == claim["subject"]["hash"], "dispatch child grant differs from its agent claim")
            expected_operation = "operation-" + hashlib.sha256(
                f"{run_id}|{claim_id}".encode("utf-8")
            ).hexdigest()[:24]
            _require(detail["operation_id"] == expected_operation, "dispatch operation id is not deterministic")
            seat = next(
                (
                    item for item in grant["roster"]["seats"]  # type: ignore[index]
                    if item["profile"] == detail["profile"]
                    and item["execution"] == execution
                ),
                None,
            )
            _require(seat is not None, "dispatch execution is outside the immutable grant roster")
            _require(
                detail["adapter"] == execution["adapter"]
                and detail["adapter_version"] == execution["adapter_version"],
                "dispatch adapter differs from its execution binding",
            )
            dispatch = {
                **detail,
                "dispatched_at": event["at"],
            }
            claim["dispatch"] = dispatch
            dispatches.append(dispatch)
            for item in claims:
                if item["claim_id"] == claim_id:
                    item["dispatch"] = dispatch
                    break
        elif event_name == "claim_completed":
            _require(event_generation == generation, "completion uses the wrong revocation generation")
            claim_id = _safe(detail["claim_id"], "completion claim id")
            _require(claim_id in active, "completion does not match one active claim")
            claim = active.pop(claim_id)
            _require(claim["request_hash"] == detail["request_hash"], "completion request hash differs from claim")
            _require(detail["result"] in COMPLETION_RESULTS, "completion result is unsupported")
            _hash(detail["receipt_hash"], "completion receipt hash")
            _text(detail["reason"], "completion reason", 1_000)
            fact_binding = _exact(detail["fact_binding"], _FACT_BINDING_KEYS, "claim fact binding")
            _exact(fact_binding["repository"], _REPOSITORY_KEYS, "claim repository facts")
            _exact(fact_binding["roadmap"], _ROADMAP_KEYS, "claim roadmap facts")
            completion = {
                **claim,
                "status": str(detail["result"]),
                "receipt_hash": detail["receipt_hash"],
                "completion_reason": detail["reason"],
                "completed_at": event["at"],
                "fact_binding": detail["fact_binding"],
            }
            completed.append(completion)
            for item in claims:
                if item["claim_id"] == claim_id:
                    item.update({
                        "status": detail["result"],
                        "receipt_hash": detail["receipt_hash"],
                        "completed_at": event["at"],
                    })
                    break
            if detail["result"] == "succeeded":
                expected_repository = dict(fact_binding["repository"])
                expected_roadmap = dict(fact_binding["roadmap"])
            if claim["category"] == "checkpoint-request" and state == "checkpoint":
                state = "running"
        elif event_name == "test_debt_recorded":
            _require(event_generation == generation, "test debt uses the wrong revocation generation")
            _require(test_baseline is not None, "test debt has no baseline fact")
            _require(detail["baseline_hash"] == _sha(test_baseline), "test debt baseline binding is stale")
            raw_obligations = detail["obligations"]
            raw_hashes = detail["obligation_hashes"]
            _require(
                isinstance(raw_obligations, list) and raw_obligations
                and len(raw_obligations) <= 200
                and isinstance(raw_hashes, list)
                and len(raw_hashes) == len(raw_obligations),
                "test debt batch is invalid",
            )
            normalized_batch: list[dict[str, object]] = []
            for raw_obligation in raw_obligations:
                try:
                    strict = validate_test_debt_obligation(raw_obligation)
                except ValueError as exc:
                    raise DwError(str(exc)) from exc
                obligation = _normalize_obligation(strict)
                _require(obligation == strict, "test debt obligation normalization changed its shape")
                normalized_batch.append(obligation)
            expected_hashes = [_sha(item) for item in normalized_batch]
            _require(raw_hashes == expected_hashes, "test debt obligation hashes are invalid")
            batch_ids = [str(item["id"]) for item in normalized_batch]
            _require(len(batch_ids) == len(set(batch_ids)), "test debt batch repeats an obligation id")
            _require(not (set(batch_ids) & set(obligations)), "test debt obligation id was reused")
            counters["max_obligations"] += len(normalized_batch)
            _require(
                counters["max_obligations"]
                <= int(grant["authority"]["budgets"]["max_obligations"]),  # type: ignore[index]
                "test debt exceeds the granted obligation budget",
            )
            for obligation, obligation_hash in zip(normalized_batch, expected_hashes):
                obligation_id = str(obligation["id"])
                obligations[obligation_id] = {
                    **obligation,
                    "source_decision_hash": detail["baseline_hash"],
                    "obligation_hash": obligation_hash,
                    "recorded_at": event["at"],
                    "record_claim_id": None,
                    "history": [],
                }
                obligation_history.append({
                    "event": event_name, "at": event["at"],
                    "obligation_id": obligation_id, "claim_id": None,
                    "to_state": "open",
                })
        elif event_name == "program_obligation_recorded":
            _require(event_generation == generation, "obligation record uses the wrong revocation generation")
            claim_id = _safe(detail["claim_id"], "obligation claim id")
            claim = next((item for item in completed if item["claim_id"] == claim_id), None)
            _require(claim is not None and claim["category"] == "obligation-record", "obligation event lacks one completed record claim")
            _require(claim["status"] == "succeeded" and claim["request_hash"] == detail["request_hash"], "obligation record claim did not succeed exactly")
            _hash(detail["decision_hash"], "obligation decision hash")
            obligation = _normalize_obligation(detail["obligation"])
            _require(detail["obligation_hash"] == _sha(obligation), "program obligation hash is invalid")
            obligation_id = str(obligation["id"])
            _require(
                claim["subject"]["kind"] == "program-obligation"
                and claim["subject"]["id"] == obligation_id
                and claim["subject"]["hash"] == _sha({
                    "decision_hash": detail["decision_hash"],
                    "obligation": obligation,
                }),
                "obligation event differs from its exact claim subject",
            )
            _require(obligation_id not in obligations, "program obligation id was reused")
            entry = {
                **obligation,
                "source_decision_hash": detail["decision_hash"],
                "obligation_hash": detail["obligation_hash"],
                "recorded_at": event["at"],
                "record_claim_id": claim_id,
                "history": [],
            }
            obligations[obligation_id] = entry
            obligation_history.append({
                "event": event_name,
                "at": event["at"],
                "obligation_id": obligation_id,
                "claim_id": claim_id,
                "to_state": "open",
            })
        elif event_name == "program_obligation_disposed":
            _require(event_generation == generation, "obligation disposition uses the wrong revocation generation")
            claim_id = _safe(detail["claim_id"], "obligation disposition claim id")
            claim = next((item for item in completed if item["claim_id"] == claim_id), None)
            _require(claim is not None and claim["category"] == "obligation-disposition", "obligation disposition lacks one completed claim")
            _require(claim["status"] == "succeeded" and claim["request_hash"] == detail["request_hash"], "obligation disposition claim did not succeed exactly")
            obligation_id = _safe(detail["obligation_id"], "obligation disposition id")
            _require(obligation_id in obligations, "obligation disposition names no durable obligation")
            obligation = obligations[obligation_id]
            _require(detail["from_state"] == obligation["state"], "obligation disposition source state is stale")
            _require(detail["to_state"] in _OBLIGATION_TERMINAL_STATES, "obligation disposition state is not terminal")
            _safe(detail["actor"], "obligation disposition actor", reference=True)
            _safe(detail["authority"], "obligation disposition authority", reference=True)
            _text(detail["reason"], "obligation disposition reason", 1_000)
            replacement_id = detail["replacement_id"]
            _require(
                replacement_id is None
                or (isinstance(replacement_id, str) and bool(_SAFE_ID_RE.fullmatch(replacement_id))),
                "obligation replacement id is unsafe",
            )
            _require(
                (detail["to_state"] == "superseded") == (replacement_id is not None),
                "superseded obligation must name exactly one replacement",
            )
            _require(
                claim["subject"]["kind"] == "program-obligation-disposition"
                and claim["subject"]["id"] == obligation_id
                and claim["subject"]["hash"] == _sha({
                    "obligation_id": obligation_id,
                    "from_state": detail["from_state"],
                    "to_state": detail["to_state"],
                    "actor": detail["actor"],
                    "authority": detail["authority"],
                    "reason": detail["reason"],
                    "replacement_id": replacement_id,
                }),
                "obligation disposition event differs from its exact claim subject",
            )
            disposition = {
                "claim_id": claim_id,
                "from_state": detail["from_state"],
                "to_state": detail["to_state"],
                "actor": detail["actor"],
                "authority": detail["authority"],
                "reason": detail["reason"],
                "replacement_id": replacement_id,
                "at": event["at"],
            }
            obligation["state"] = detail["to_state"]
            obligation["history"].append(disposition)  # type: ignore[union-attr]
            obligation_history.append({
                "event": event_name,
                "at": event["at"],
                "obligation_id": obligation_id,
                **disposition,
            })
        elif event_name == "program_delivery_facts_recorded":
            _require(event_generation == generation, "delivery facts use the wrong generation")
            _require(state == "running", "delivery facts were recorded outside running state")
            _require(delivery_facts is None, "program delivery facts were recorded more than once")
            claim_id = _safe(detail["claim_id"], "delivery facts claim id")
            claim = next((item for item in completed if item["claim_id"] == claim_id), None)
            _require(
                claim is not None and claim["category"] == "assignment"
                and claim["status"] == "succeeded"
                and claim["request_hash"] == detail["request_hash"]
                and claim["subject"]["kind"] == "program-scope-proof"
                and claim["subject"]["hash"] == detail["proof_hash"],
                "delivery facts lack the completed scope-proof claim",
            )
            _hash(detail["proof_hash"], "delivery facts proof hash")
            story_ids = detail["story_ids"]
            obligation_ids = detail["obligation_ids"]
            files_touched = detail["files_touched"]
            _require(
                isinstance(story_ids, list)
                and story_ids == sorted(set(story_ids))
                and story_ids == sorted(selected_stories),
                "delivery facts story set is invalid",
            )
            _require(
                isinstance(obligation_ids, list)
                and obligation_ids == sorted(obligations),
                "delivery facts obligation set is invalid",
            )
            _require(
                isinstance(files_touched, list)
                and files_touched == sorted(set(files_touched))
                and all(
                    isinstance(path, str) and bool(path) and len(path) <= 500
                    and "\x00" not in path and "\n" not in path and "\r" not in path
                    for path in files_touched
                ),
                "delivery facts touched-file set is invalid",
            )
            _require(
                isinstance(detail["head_sha"], str)
                and len(detail["head_sha"]) in {40, 64}
                and all(char in "0123456789abcdef" for char in detail["head_sha"])
                and detail["head_sha"] == expected_repository["head"],
                "delivery facts HEAD differs from the ledger fact binding",
            )
            _require(
                detail["verdict_outcome"] == "passed",
                "delivery facts verdict outcome is invalid",
            )
            delivery_facts = dict(detail)
        elif event_name == "program_scope_completed":
            _require(event_generation == generation, "scope completion uses the wrong revocation generation")
            _require(state == "running", "program scope completed outside running state")
            claim_id = _safe(detail["claim_id"], "scope completion claim id")
            claim = next((item for item in completed if item["claim_id"] == claim_id), None)
            _require(claim is not None and claim["category"] == "assignment", "scope completion lacks one completed assignment claim")
            _require(claim["status"] == "succeeded" and claim["request_hash"] == detail["request_hash"], "scope completion claim did not succeed exactly")
            _hash(detail["proof_hash"], "scope completion proof hash")
            _require(
                claim["subject"]["kind"] == "program-scope-proof"
                and claim["subject"]["hash"] == detail["proof_hash"],
                "scope completion proof differs from its exact claim subject",
            )
            stories = detail["completed_stories"]
            phases = detail["completed_phases"]
            open_ids = detail["open_obligation_ids"]
            _require(
                isinstance(stories, list) and stories == sorted(set(stories))
                and stories == sorted(grant["scope"]["story_ids"]),  # type: ignore[index]
                "scope completion story set is invalid",
            )
            _require(
                isinstance(phases, list) and phases == sorted(set(phases))
                and phases == sorted(grant["scope"]["phases"]),  # type: ignore[index]
                "scope completion phase set is invalid",
            )
            current_open = sorted(
                obligation_id for obligation_id, obligation in obligations.items()
                if obligation["state"] in {"open", "in-progress"}
            )
            _require(open_ids == current_open, "scope completion obligation frontier is stale")
            _require(
                not any(
                    obligation["blocking"] and obligation["state"] in {"open", "in-progress"}
                    for obligation in obligations.values()
                ),
                "scope completion has an open blocking obligation",
            )
            scope_completion = {
                **detail,
                "completed_at": event["at"],
            }
            state = "complete"
        elif event_name in {"program_paused", "program_resumed", "program_revoked", "program_cancelled"}:
            _require(detail["from_state"] == state, "program control source state is stale")
            expected_action = event_name.removeprefix("program_")
            if expected_action.endswith("d"):
                expected_action = {"paused": "pause", "resumed": "resume", "revoked": "revoke", "cancelled": "cancel"}[expected_action]
            _require(detail["action"] == expected_action, "program control action and event differ")
            _require(state in _CONTROL_ALLOWED_STATES[expected_action], "program control source state is not allowed")
            _require(detail["decision"] == "approve", "program control event was not approved")
            _text(detail["reason"], "program control reason", 1_000)
            _hash(detail["token_hash"], "program control token hash")
            expected_to_state = {
                "pause": "paused",
                "resume": "checkpoint" if any(
                    claim["category"] == "checkpoint-request"
                    for claim in active.values()
                ) else "running",
                "revoke": "revoked", "cancel": "cancelled",
            }[expected_action]
            _require(detail["to_state"] == expected_to_state, "program control target state is invalid")
            expected_expired = sorted(
                claim_id for claim_id, claim in active.items()
                if claim["category"] == "checkpoint-request"
                and expected_action in {"revoke", "cancel"}
            )
            expected_interrupts = sorted(active) if expected_action == "cancel" else []
            _require(detail["expired_request_ids"] == expected_expired, "program control request-expiry set is invalid")
            _require(detail["interrupt_claim_ids"] == expected_interrupts, "program control interrupt set is invalid")
            new_generation = int(detail["new_generation"])
            if event_name in {"program_revoked", "program_cancelled"}:
                _require(new_generation == generation + 1, "revocation generation did not increase exactly once")
            else:
                _require(new_generation == generation, "pause/resume changed revocation generation")
            _require(event_generation == new_generation, "program control event uses the wrong generation")
            generation = new_generation
            state = str(detail["to_state"])
            controls.append({"event": event_name, "at": event["at"], **detail})
        elif event_name == "program_exhausted":
            _require(event_generation == generation, "program exhaustion uses the wrong generation")
            _require(state == "running", "program exhausted outside running state")
            counter = str(detail["counter"])
            _require(counter in counters, "program exhausted an unknown counter")
            _hash(detail["request_hash"], "program exhaustion request hash")
            _require(detail["used"] == counters[counter] and detail["limit"] == grant["authority"]["budgets"][counter], "program exhaustion facts are invalid")  # type: ignore[index]
            state = "exhausted"
            exhaustion = dict(detail)

    observed = _time(now, "now")
    expired = observed >= expires
    if expired and state in {"running", "checkpoint", "paused"}:
        state = "expired"
    outstanding_requests = [
        {
            "claim_id": item["claim_id"],
            "port": item["request_port"],
            "status": (
                "expired" if state in {"revoked", "cancelled", "expired", "exhausted"}
                else "open"
            ),
        }
        for item in active.values()
        if item["category"] == "checkpoint-request"
    ]
    budget_state = {
        key: {
            "used": counters[key],
            "limit": int(grant["authority"]["budgets"][key]),  # type: ignore[index]
            "remaining": int(grant["authority"]["budgets"][key]) - counters[key],  # type: ignore[index]
        }
        for key in BUDGET_DEFAULTS
    }
    return {
        "kind": PROGRAM_PROJECTION_KIND,
        "schema_version": PROGRAM_RUN_SCHEMA_VERSION,
        "run_id": run_id,
        "grant_hash": grant["grant_hash"],
        "plan_hash": grant["plan_hash"],
        "program": grant["program"],
        "mode": mode,
        "state": state,
        "generation": generation,
        "ledger_head": events[-1]["event_hash"],
        "event_count": len(events),
        "capabilities": list(grant["authority"]["capabilities"]),  # type: ignore[index]
        "budgets": budget_state,
        "stop_conditions": list(grant["authority"]["stop_conditions"]),  # type: ignore[index]
        "cost_accounting": grant["authority"]["cost_accounting"],  # type: ignore[index]
        "scope": grant["scope"],
        "selection": grant["selection"],
        "roster": grant["roster"],
        "expected_repository": expected_repository,
        "expected_roadmap": expected_roadmap,
        "claims": claims,
        "dispatches": dispatches,
        "active_claims": sorted(active.values(), key=lambda item: str(item["claim_id"])),
        "completed_claims": completed,
        "outstanding_requests": outstanding_requests,
        "selected_stories": sorted(selected_stories),
        "selected_phases": sorted(selected_phases),
        "controls": controls,
        "obligations": sorted(obligations.values(), key=lambda item: str(item["id"])),
        "open_obligations": sorted(
            (
                item for item in obligations.values()
                if item["state"] in {"open", "in-progress"}
            ),
            key=lambda item: str(item["id"]),
        ),
        "blocking_obligations": sorted(
            (
                item for item in obligations.values()
                if item["blocking"] and item["state"] in {"open", "in-progress"}
            ),
            key=lambda item: str(item["id"]),
        ),
        "obligation_history": obligation_history,
        "scope_completion": scope_completion,
        "delivery_facts": delivery_facts,
        "exhaustion": exhaustion,
        "test_baseline": test_baseline,
        "issued_at": grant["issued_at"],
        "expires_at": grant["expires_at"],
        "expired": expired,
        "future_claims_allowed": state == "running" and mode != "advisory",
        "completion_receipts_allowed": bool(active),
        "interrupt_claim_ids": (
            sorted(active) if state in {"revoked", "cancelled"} else []
        ),
        "permanent_exclusions": list(grant["permanent_exclusions"]),
        "starts_work": False,
        "writes_repository": False,
        "writes_roadmap": False,
        "creates_grant": False,
    }


def _append_event(path: Path, event: dict[str, object]) -> None:
    ledger = path / "ledger.jsonl"
    with ledger.open("ab") as handle:
        handle.write((canonical_json(event) + "\n").encode("utf-8"))
        handle.flush()
        os.fsync(handle.fileno())


def _record_program_test_baseline(
    root: Path,
    run_id: str,
    baseline: object,
    *,
    now: str | datetime | None = None,
) -> dict[str, object]:
    """Append one conductor-observed baseline fact; no transport exposes this."""
    root = root.resolve()
    observed = _time(now, "now")
    try:
        fact = validate_baseline_fact(baseline)
    except ValueError as exc:
        raise DwError(str(exc)) from exc
    path, grant, _plan = _load_documents(root, run_id)
    with _lock(path / "ledger.lock"):
        projection = replay_program(root, run_id, now=observed)
        prior = projection.get("test_baseline")
        if prior is not None:
            _require(prior == fact, "program test baseline cannot be amended")
            return {**projection, "idempotent": True}
        _require(projection["state"] == "running", "program is not running")
        _require(not projection["dispatches"], "test baseline must precede first dispatch")
        _require(
            fact["head_sha"] == grant["repository"]["head"],  # type: ignore[index]
            "test baseline head differs from the granted head",
        )
        current_head = head_sha(root) or "none"
        _require(current_head == fact["head_sha"], "test baseline head is stale")
        event = _event_document(
            run_id,
            int(projection["event_count"]) + 1,
            "test_baseline_captured",
            int(projection["generation"]),
            observed,
            {"baseline": fact},
            str(projection["ledger_head"]),
        )
        _append_event(path, event)
        return {
            **projection,
            "test_baseline": fact,
            "event_count": int(projection["event_count"]) + 1,
            "ledger_head": event["event_hash"],
            "idempotent": False,
        }


def _record_program_test_debts(
    root: Path,
    run_id: str,
    obligations: object,
    *,
    now: str | datetime | None = None,
) -> dict[str, object]:
    """Append one bounded batch of deterministic baseline debt."""
    root = root.resolve()
    observed = _time(now, "now")
    _require(
        isinstance(obligations, list) and len(obligations) <= 200,
        "test debt obligations must be a bounded list",
    )
    strict_batch: list[dict[str, object]] = []
    for raw in obligations:
        try:
            strict = validate_test_debt_obligation(raw)
        except ValueError as exc:
            raise DwError(str(exc)) from exc
        normalized = _normalize_obligation(strict)
        _require(normalized == strict, "test debt obligation normalization changed its shape")
        strict_batch.append(normalized)
    path, _grant, _plan = _load_documents(root, run_id)
    with _lock(path / "ledger.lock"):
        projection = replay_program(root, run_id, now=observed)
        baseline = projection.get("test_baseline")
        _require(baseline is not None, "test debt cannot be recorded without a baseline")
        existing = {
            str(item["id"]): item for item in projection["obligations"]
        }
        pending: list[dict[str, object]] = []
        for obligation in strict_batch:
            prior = existing.get(str(obligation["id"]))
            if prior is not None:
                _require(prior["obligation_hash"] == _sha(obligation), "test debt obligation id conflicts")
            else:
                pending.append(obligation)
        if not pending:
            return {**projection, "recorded_obligations": [], "idempotent": True}
        _require(
            len(pending)
            <= projection["budgets"]["max_obligations"]["remaining"],
            "test debt exceeds the granted obligation budget",
        )
        hashes = [_sha(item) for item in pending]
        event = _event_document(
            run_id,
            int(projection["event_count"]) + 1,
            "test_debt_recorded",
            int(projection["generation"]),
            observed,
            {
                "baseline_hash": _sha(baseline),
                "obligations": pending,
                "obligation_hashes": hashes,
            },
            str(projection["ledger_head"]),
        )
        _append_event(path, event)
        return {
            **projection,
            "event_count": int(projection["event_count"]) + 1,
            "ledger_head": event["event_hash"],
            "recorded_obligations": pending,
            "idempotent": False,
        }


def _current_roster_hash(root: Path, driver_config: dict[str, object] | None = None) -> str:
    config = load_driver_config(root, driver_config)
    return _sha(driver_inventory(config))


def _execution_for_profile(
    root: Path,
    profile: str,
    driver_config: dict[str, object] | None = None,
) -> tuple[dict[str, object], dict[str, object]]:
    capability = driver_capability(load_driver_config(root, driver_config), profile)
    execution = {
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
    return capability, execution


def program_freshness_issues(
    root: Path,
    grant: dict[str, object],
    projection: dict[str, object],
    *,
    driver_config: dict[str, object] | None = None,
) -> list[str]:
    """Re-observe policy, roster, repository, and roadmap grant bindings."""
    issues: list[str] = []
    try:
        compiled = _policy_for_plan(root, str(grant["program_selector"]))
        if compiled["semantic_hash"] != grant["program"]["semantic_hash"]:  # type: ignore[index]
            issues.append("program semantic hash changed")
        if compiled["policy_bundle_hash"] != grant["program"]["policy_bundle_hash"]:  # type: ignore[index]
            issues.append("program policy bundle changed")
    except DwError as exc:
        issues.append(f"program policy cannot be recompiled: {exc.message}")
    try:
        if _current_roster_hash(root, driver_config) != grant["roster"]["roster_hash"]:  # type: ignore[index]
            issues.append("resolved driver roster changed")
    except DwError as exc:
        issues.append(f"driver roster cannot be re-observed: {exc.message}")
    expected_repository = projection["expected_repository"]
    try:
        current_repository = _repository_facts(
            root,
            expected_repository.get("remote"),  # type: ignore[union-attr]
            expected_repository.get("remote_ref"),  # type: ignore[union-attr]
        )
        for key in _REPOSITORY_KEYS:
            if current_repository[key] != expected_repository.get(key):  # type: ignore[union-attr]
                issues.append(f"repository {key} changed")
    except DwError as exc:
        issues.append(f"repository cannot be re-observed: {exc.message}")
    try:
        plan = build_program_plan(root, str(grant["program_selector"]), driver_config=driver_config)
        if plan["roadmap"]["snapshot_hash"] != projection["expected_roadmap"]["snapshot_hash"]:  # type: ignore[index]
            issues.append("roadmap snapshot changed")
    except DwError as exc:
        issues.append(f"roadmap cannot be re-observed: {exc.message}")
    return issues


def _subject(value: object) -> dict[str, object]:
    raw = _exact(value, _SUBJECT_KEYS, "program claim subject")
    phase = raw["phase"]
    _require(phase is None or (isinstance(phase, int) and not isinstance(phase, bool) and phase >= 0), "claim subject phase is invalid")
    story = raw["story"]
    _require(story is None or (isinstance(story, str) and _REF_RE.fullmatch(story)), "claim subject story is invalid")
    return {
        "kind": _safe(raw["kind"], "subject.kind"),
        "id": _safe(raw["id"], "subject.id", reference=True),
        "hash": _hash(raw["hash"], "subject.hash"),
        "phase": phase,
        "story": story,
    }


def _resource_estimate(value: object) -> dict[str, int]:
    raw = _exact(value, _RESOURCE_KEYS, "resource estimate")
    result: dict[str, int] = {}
    for key in _RESOURCE_KEYS:
        candidate = raw[key]
        _require(isinstance(candidate, int) and not isinstance(candidate, bool) and candidate >= 0, f"resource estimate {key} is invalid")
        result[key] = int(candidate)
    return result


def _normalize_obligation(value: object) -> dict[str, object]:
    raw = _exact(value, _OBLIGATION_KEYS, "program obligation")
    obligation_id = _safe(raw["id"], "obligation.id")
    _require(raw["kind"] in _OBLIGATION_KINDS, "program obligation kind is unsupported")
    _require(
        raw["priority"] in _OBLIGATION_PRIORITIES,
        "program obligation priority is unsupported",
    )
    _require(isinstance(raw["blocking"], bool), "program obligation blocking must be boolean")
    target = raw["target"]
    _require(
        target is None or (isinstance(target, str) and bool(_REF_RE.fullmatch(target))),
        "program obligation target is unsafe",
    )
    citations = raw["citations"]
    _require(
        isinstance(citations, list)
        and 0 < len(citations) <= 32
        and len(set(citations)) == len(citations)
        and all(isinstance(item, str) and bool(_REF_RE.fullmatch(item)) for item in citations),
        "program obligation citations must be non-empty unique references",
    )
    _require(raw["state"] == "open", "a recorded program obligation must start open")
    return {
        "id": obligation_id,
        "kind": str(raw["kind"]),
        "statement": _text(raw["statement"], "obligation.statement", 2_000),
        "priority": str(raw["priority"]),
        "blocking": bool(raw["blocking"]),
        "accountable_role": _safe(raw["accountable_role"], "obligation.accountable_role"),
        "target": target,
        "citations": list(citations),
        "acceptance": _text(raw["acceptance"], "obligation.acceptance", 2_000),
        "state": "open",
    }


def _claim_budget(
    category: str,
    subject: dict[str, object],
    estimate: dict[str, int],
    projection: dict[str, object],
) -> dict[str, int]:
    budget = dict(_CLAIM_RULES[category][2])
    if category == "selection":
        phase = subject["phase"]
        story = subject["story"]
        if phase is not None and int(phase) not in projection["selected_phases"]:
            budget["max_phases"] = 1
        if story is not None and str(story) in projection["selected_stories"]:
            budget["max_stories"] = 0
    resource_map = {
        "artifact_bytes": "max_artifact_bytes",
        "tokens": "max_tokens",
        "observed_cost_microunits": "max_observed_cost_microunits",
    }
    for source, target in resource_map.items():
        if estimate[source]:
            budget[target] = budget.get(target, 0) + estimate[source]
    return {key: amount for key, amount in budget.items() if amount}


def _binding(projection: dict[str, object], observed: datetime) -> dict[str, object]:
    return {
        "grant_hash": projection["grant_hash"],
        "ledger_head": projection["ledger_head"],
        "generation": projection["generation"],
        "state": projection["state"],
        "observed_at": _format_time(observed),
    }


def validate_child_grant(value: object) -> dict[str, object]:
    grant = _exact(value, _CHILD_GRANT_KEYS, "program child grant")
    _require(grant["kind"] == PROGRAM_CHILD_GRANT_KIND and grant["schema_version"] == PROGRAM_RUN_SCHEMA_VERSION, "unsupported child grant")
    expected = _sha({key: item for key, item in grant.items() if key != "grant_hash"})
    _require(grant["grant_hash"] == expected, "child grant hash is invalid")
    role = _exact(grant["role"], _SEAT_KEYS, "program child role")
    _exact(role["execution"], _EXECUTION_KEYS, "program child role execution")
    _exact(grant["repository"], _REPOSITORY_KEYS, "program child repository")
    _exact(grant["roadmap"], _ROADMAP_KEYS, "program child roadmap")
    _normalize_capabilities(grant["capabilities"])
    _budget_map(grant["budgets"])
    exclusions = grant["permanent_exclusions"]
    _require(
        isinstance(exclusions, list)
        and set(PROGRAM_PERMANENT_EXCLUSIONS) <= set(exclusions)
        and _NON_DELEGABLE <= set(exclusions),
        "child grant permanent exclusions are incomplete",
    )
    _require(grant["starts_work"] is False and grant["writes_state"] is False, "child grant preview effects must be false")
    return grant


def derive_child_grant(
    root: Path,
    run_id: str,
    *,
    role_address: str,
    node_address: str,
    capabilities: list[str],
    budgets: dict[str, int],
    now: str | datetime | None = None,
    driver_config: dict[str, object] | None = None,
) -> dict[str, object]:
    """Derive a non-stored strict intersection for one declared child."""
    observed = _time(now, "now")
    _path, grant, _plan = _load_documents(root.resolve(), run_id)
    projection = replay_program(root, run_id, now=observed)
    _require(projection["state"] == "running" and projection["mode"] != "advisory", "program does not currently permit child authority")
    freshness = program_freshness_issues(root, grant, projection, driver_config=driver_config)
    _require(not freshness, "program grant is stale: " + "; ".join(freshness))
    role = next(
        (seat for seat in grant["roster"]["seats"] if seat["address"] == role_address),  # type: ignore[index]
        None,
    )
    if role is None:
        # The immutable grant binds the complete policy bundle and local
        # driver roster, while a stable story assignment is derived only when
        # that story reaches the roadmap frontier.  Recompute that exact
        # assignment here rather than treating the first story's seat address
        # as authority for every later story in a multi-phase program.
        current = build_program_plan(
            root,
            str(grant["program_selector"]),
            driver_config=driver_config,
        )
        assignment = current.get("assignment")
        selection = current.get("selection")
        _require(
            current.get("applicable") is True
            and isinstance(assignment, dict)
            and isinstance(selection, dict),
            "current roadmap frontier has no grant-compatible assignment",
        )
        _require(
            assignment.get("roster_hash") == grant["roster"]["roster_hash"],  # type: ignore[index]
            "current assignment resolved a different driver roster",
        )
        _require(
            assignment.get("separation", {}).get("passed") is True,  # type: ignore[union-attr]
            "current assignment does not prove separation of duties",
        )
        for assigned_role in assignment.get("roles", []):
            if not isinstance(assigned_role, dict):
                continue
            for member in assigned_role.get("members", []):
                if not isinstance(member, dict) or member.get("address") != role_address:
                    continue
                role = {
                    "address": member["address"],
                    "role": assigned_role["role"],
                    "duty": assigned_role["duty"],
                    "slot": member["slot"],
                    "agent": member["agent"],
                    "profile": member["profile"],
                    "principal_fingerprint": member["principal_fingerprint"],
                    "assignment_generation": member["assignment_generation"],
                    "workspace_domain": member["workspace_domain"],
                    "session_binding_key": member["session_binding_key"],
                    "execution": member["execution"],
                    "authority_ceiling": sorted(
                        set(projection["capabilities"])
                        & set(assigned_role.get("capability_ceiling", []))
                        & set(
                            assigned_role.get("packet_policy", {}).get(  # type: ignore[union-attr]
                                "effective_capability_ceiling", []
                            )
                            or assigned_role.get("capability_ceiling", [])
                        )
                    ),
                }
                break
            if role is not None:
                break
    _require(isinstance(role, dict), "child role address is not assigned by the grant")
    requested = _normalize_capabilities(capabilities)
    allowed = set(grant["authority"]["child_capability_ceiling"]) & set(role["authority_ceiling"])  # type: ignore[index]
    _require(set(requested) <= allowed, "child capabilities exceed the program/role intersection")
    _require(not (set(requested) & _NON_DELEGABLE), "child grant contains a non-delegable rail")
    _require(bool(requested), "child grant needs at least one capability")
    _safe(node_address, "node_address", reference=True)
    _require(
        node_address.startswith(str(role_address).rsplit("/role/", 1)[0] + "/"),
        "child node address is outside its assigned workflow lineage",
    )
    normalized_budgets = _budget_map(budgets)
    _require(bool(normalized_budgets), "child grant needs finite local budgets")
    for key, amount in normalized_budgets.items():
        _require(amount > 0, f"child budget {key} must be positive")
        _require(amount <= projection["budgets"][key]["remaining"], f"child budget {key} exceeds remaining program authority")  # type: ignore[index]
    unsigned = {
        "kind": PROGRAM_CHILD_GRANT_KIND,
        "schema_version": PROGRAM_RUN_SCHEMA_VERSION,
        "parent_run_id": run_id,
        "parent_grant_hash": grant["grant_hash"],
        "parent_ledger_head": projection["ledger_head"],
        "generation": projection["generation"],
        "role": {key: role[key] for key in _SEAT_KEYS},
        "node_address": node_address,
        "repository": projection["expected_repository"],
        "roadmap": projection["expected_roadmap"],
        "capabilities": requested,
        "budgets": normalized_budgets,
        "expires_at": grant["expires_at"],
        "permanent_exclusions": sorted(set(PROGRAM_PERMANENT_EXCLUSIONS) | _NON_DELEGABLE),
        "starts_work": False,
        "writes_state": False,
    }
    return {**unsigned, "grant_hash": _sha(unsigned)}


def _claim_scope_issues(
    grant: dict[str, object], subject: dict[str, object]
) -> list[str]:
    scope = grant["scope"]
    _require(isinstance(scope, dict), "program grant scope is invalid")
    issues: list[str] = []
    phase = subject["phase"]
    story = subject["story"]
    if phase is not None and phase not in scope.get("phases", []):
        issues.append(f"phase {phase} is outside the granted roadmap scope")
    if story is not None and story not in scope.get("story_ids", []):
        issues.append(f"story {story} is outside the granted roadmap scope")
    return issues


def _derived_child_for_claim(
    root: Path,
    run_id: str,
    child: dict[str, object],
    *,
    now: datetime,
    driver_config: dict[str, object] | None,
) -> dict[str, object]:
    role = child["role"]
    _require(isinstance(role, dict), "child grant role is invalid")
    return derive_child_grant(
        root,
        run_id,
        role_address=str(role["address"]),
        node_address=str(child["node_address"]),
        capabilities=list(child["capabilities"]),
        budgets=dict(child["budgets"]),
        now=now,
        driver_config=driver_config,
    )


def build_program_claim_preview(
    root: Path,
    run_id: str,
    *,
    category: str,
    subject: object,
    idempotency_key: str,
    reason: str,
    resource_estimate: object | None = None,
    request_port: str | None = None,
    child_grant: dict[str, object] | None = None,
    now: str | datetime | None = None,
    driver_config: dict[str, object] | None = None,
) -> dict[str, object]:
    observed = _time(now, "now")
    _require(category in _CLAIM_RULES, "unsupported program claim category")
    normalized_subject = _subject(subject)
    idem = _safe(idempotency_key, "idempotency_key")
    normalized_reason = _text(reason, "claim reason", 1_000)
    estimate = _resource_estimate(resource_estimate or {
        "artifact_bytes": 0, "tokens": 0, "observed_cost_microunits": 0,
    })
    if request_port is not None:
        _safe(request_port, "request_port", reference=True)
    if category == "checkpoint-request":
        _require(request_port is not None, "checkpoint request needs a typed port")
    else:
        _require(request_port is None, "only checkpoint requests may name a request port")
    if category == "child-grant":
        _require(child_grant is not None, "child-grant claim needs one derived child grant")
        validate_child_grant(child_grant)
    else:
        _require(child_grant is None, "non-child claim cannot carry child authority")

    _path, grant, _plan = _load_documents(root.resolve(), run_id)
    projection = replay_program(root, run_id, now=observed)
    capability, decision, _fixed = _CLAIM_RULES[category]
    issues: list[dict[str, str]] = []
    if projection["state"] != "running" or projection["mode"] == "advisory":
        issues.append({"code": "grant-inactive", "message": f"program state {projection['state']} cannot reserve a claim"})
    if capability not in projection["capabilities"]:
        issues.append({"code": "capability-denied", "message": f"program grant lacks {capability}"})
    for message in _claim_scope_issues(grant, normalized_subject):
        issues.append({"code": "scope-violation", "message": message})
    if category == "checkpoint-request":
        declared_ports = {
            str(item["id"])
            for item in grant["authority"]["checkpoint_ports"]  # type: ignore[index]
            if isinstance(item, dict) and "id" in item
        }
        if request_port not in declared_ports:
            issues.append({"code": "request-port-denied", "message": "checkpoint request port is not declared by the grant"})
    for message in program_freshness_issues(root, grant, projection, driver_config=driver_config):
        issues.append({"code": "program-stale", "message": message})
    budget = _claim_budget(category, normalized_subject, estimate, projection)
    exhaustion: dict[str, object] | None = None
    for key, amount in budget.items():
        state = projection["budgets"][key]
        if amount > state["remaining"]:
            exhaustion = {"counter": key, "used": state["used"], "limit": state["limit"]}
            issues.append({"code": "budget-exhausted", "message": f"claim would exceed {key}"})
            break
    if child_grant is not None:
        if child_grant["parent_ledger_head"] != projection["ledger_head"] or child_grant["generation"] != projection["generation"]:
            issues.append({"code": "child-grant-stale", "message": "derived child grant no longer matches the program ledger"})
        try:
            expected_child = _derived_child_for_claim(
                root.resolve(), run_id, child_grant, now=observed,
                driver_config=driver_config,
            )
            if expected_child != child_grant:
                issues.append({"code": "child-grant-denied", "message": "child grant differs from the mechanical authority intersection"})
        except DwError as exc:
            issues.append({"code": "child-grant-denied", "message": exc.message})
    request = {
        "category": category,
        "subject": normalized_subject,
        "idempotency_key": idem,
        "decision": decision,
        "reason": normalized_reason,
        "resource_estimate": estimate,
        "request_port": request_port,
    }
    unsigned = {
        "kind": PROGRAM_CLAIM_PREVIEW_KIND,
        "schema_version": PROGRAM_RUN_SCHEMA_VERSION,
        "run_id": run_id,
        "applicable": not issues,
        "issues": issues,
        "request": request,
        "binding": _binding(projection, observed),
        "budget": budget,
        "child_grant": child_grant,
        "exhaustion": exhaustion,
        "starts_work": False,
        "writes_state": False,
        "dispatches_child": False,
        "mutates_repository": False,
        "mutates_roadmap": False,
    }
    return {**unsigned, "claim_token": _sha(unsigned)}


def _validate_claim_preview(value: object) -> dict[str, object]:
    preview = _exact(value, _CLAIM_PREVIEW_KEYS, "program claim preview")
    _require(preview["kind"] == PROGRAM_CLAIM_PREVIEW_KIND and preview["schema_version"] == PROGRAM_RUN_SCHEMA_VERSION, "unsupported program claim preview")
    request = _exact(preview["request"], _CLAIM_REQUEST_KEYS, "program claim request")
    category = request["category"]
    _require(category in _CLAIM_RULES, "unsupported program claim category")
    _subject(request["subject"])
    _safe(request["idempotency_key"], "idempotency_key")
    _require(request["decision"] == _CLAIM_RULES[str(category)][1], "program claim decision differs from its contracted category")
    _text(request["reason"], "claim reason", 1_000)
    _resource_estimate(request["resource_estimate"])
    if category == "checkpoint-request":
        _safe(request["request_port"], "request_port", reference=True)
    else:
        _require(request["request_port"] is None, "only checkpoint requests may name a request port")
    _exact(preview["binding"], _BINDING_KEYS, "program claim binding")
    _budget_map(preview["budget"])
    if category == "child-grant":
        _require(preview["child_grant"] is not None, "child-grant claim needs derived authority")
        validate_child_grant(preview["child_grant"])
    else:
        _require(preview["child_grant"] is None, "non-child claim cannot carry child authority")
    _require(isinstance(preview["applicable"], bool) and isinstance(preview["issues"], list), "program claim applicability is invalid")
    for effect in ("starts_work", "writes_state", "dispatches_child", "mutates_repository", "mutates_roadmap"):
        _require(preview[effect] is False, f"program claim preview {effect} must be false")
    unsigned = {key: item for key, item in preview.items() if key != "claim_token"}
    _require(preview["claim_token"] == _sha(unsigned), "program claim token is invalid")
    return preview


def apply_program_claim(
    root: Path,
    preview: object,
    *,
    claim_token: str,
    now: str | datetime | None = None,
    driver_config: dict[str, object] | None = None,
) -> dict[str, object]:
    """Reserve exactly one ledger claim; this still dispatches or mutates nothing."""
    submitted = _validate_claim_preview(preview)
    _require(claim_token == submitted["claim_token"], "claim token does not match preview")
    observed = _time(now, "now")
    run_id = str(submitted["run_id"])
    path, grant, _plan = _load_documents(root.resolve(), run_id)
    with _lock(path / "ledger.lock"):
        projection = replay_program(root, run_id, now=observed)
        request = submitted["request"]
        request_hash = _sha(request)
        duplicate = next(
            (item for item in projection["claims"] if item["idempotency_key"] == request["idempotency_key"]),
            None,
        )
        if duplicate is not None:
            _require(duplicate["request_hash"] == request_hash, "idempotency key was reused for a different program claim")
            return {**projection, "claim": duplicate, "idempotent": True}
        binding = submitted["binding"]
        _require(
            binding["grant_hash"] == projection["grant_hash"]
            and binding["ledger_head"] == projection["ledger_head"]
            and binding["generation"] == projection["generation"]
            and binding["state"] == projection["state"],
            "program claim token is stale",
        )
        _require(projection["state"] == "running" and projection["mode"] != "advisory", "program grant does not permit a new claim")
        freshness = program_freshness_issues(root, grant, projection, driver_config=driver_config)
        _require(not freshness, "program claim facts are stale: " + "; ".join(freshness))
        category = str(request["category"])
        capability = _CLAIM_RULES[category][0]
        _require(capability in projection["capabilities"], "program claim capability is no longer granted")
        scope_issues = _claim_scope_issues(grant, request["subject"])
        _require(not scope_issues, "program claim is outside scope: " + "; ".join(scope_issues))
        if category == "checkpoint-request":
            declared_ports = {
                str(item["id"])
                for item in grant["authority"]["checkpoint_ports"]  # type: ignore[index]
                if isinstance(item, dict) and "id" in item
            }
            _require(request["request_port"] in declared_ports, "checkpoint request port is not declared by the grant")
        budget = _budget_map(submitted["budget"])
        expected_budget = _claim_budget(
            category,
            request["subject"],
            request["resource_estimate"],
            projection,
        )
        _require(budget == expected_budget, "program claim budget differs from the mechanical reservation")
        child = submitted["child_grant"]
        if isinstance(child, dict):
            expected_child = _derived_child_for_claim(
                root.resolve(), run_id, child, now=observed,
                driver_config=driver_config,
            )
            _require(child == expected_child, "child grant differs from the mechanical authority intersection")
        if not submitted["applicable"]:
            exhaustion = submitted["exhaustion"]
            issue_codes = {
                str(item.get("code"))
                for item in submitted["issues"]
                if isinstance(item, dict)
            }
            _require(
                isinstance(exhaustion, dict)
                and issue_codes == {"budget-exhausted"},
                "only a purely budget-exhausted claim may append exhaustion",
            )
            counter = str(exhaustion["counter"])
            _require(
                counter in budget
                and budget[counter] > projection["budgets"][counter]["remaining"]
                and exhaustion["used"] == projection["budgets"][counter]["used"]
                and exhaustion["limit"] == projection["budgets"][counter]["limit"],
                "program exhaustion preview does not match current budget facts",
            )
            event = _event_document(
                run_id, projection["event_count"] + 1, "program_exhausted",
                int(projection["generation"]), observed,
                {
                    "counter": exhaustion["counter"],
                    "used": exhaustion["used"],
                    "limit": exhaustion["limit"],
                    "request_hash": request_hash,
                },
                str(projection["ledger_head"]),
            )
            _append_event(path, event)
            return {**replay_program(root, run_id, now=observed), "claim": None, "idempotent": False}
        for key, amount in budget.items():
            _require(amount <= projection["budgets"][key]["remaining"], f"program claim budget {key} is exhausted")
        child_hash = child["grant_hash"] if isinstance(child, dict) else None
        claim_id = "claim-" + hashlib.sha256(
            f"{run_id}|{request['idempotency_key']}".encode("utf-8")
        ).hexdigest()[:24]
        event = _event_document(
            run_id, projection["event_count"] + 1, "claim_reserved",
            int(projection["generation"]), observed,
            {
                "claim_id": claim_id,
                "idempotency_key": request["idempotency_key"],
                "request_hash": request_hash,
                "category": request["category"],
                "subject": request["subject"],
                "capability": capability,
                "decision": request["decision"],
                "reason": request["reason"],
                "budget": budget,
                "resource_estimate": request["resource_estimate"],
                "child_grant_hash": child_hash,
                "request_port": request["request_port"],
            },
            str(projection["ledger_head"]),
        )
        _append_event(path, event)
    after = replay_program(root, run_id, now=observed)
    claim = next(item for item in after["claims"] if item["claim_id"] == claim_id)
    return {**after, "claim": claim, "idempotent": False}


def _completion_fact_binding(
    root: Path,
    grant: dict[str, object],
    projection: dict[str, object],
) -> tuple[dict[str, object], list[dict[str, str]]]:
    issues: list[dict[str, str]] = []
    repository = _repository_facts(
        root,
        projection["expected_repository"].get("remote"),  # type: ignore[union-attr]
        projection["expected_repository"].get("remote_ref"),  # type: ignore[union-attr]
    )
    try:
        current_plan = build_program_plan(root, str(grant["program_selector"]))
        roadmap = {
            "project": str(current_plan["roadmap"]["project"]),
            "snapshot_hash": str(current_plan["roadmap"]["snapshot_hash"]),
            "healthy": bool(current_plan["roadmap"]["healthy"]),
            "warning_count": len(current_plan["roadmap"].get("warnings", [])),
        }
    except DwError:
        roadmap = dict(projection["expected_roadmap"])
        issues.append({"code": "roadmap-unobservable", "message": "completion cannot re-observe the program roadmap"})
    return {"repository": repository, "roadmap": roadmap}, issues


def build_program_completion_preview(
    root: Path,
    run_id: str,
    *,
    claim_id: str,
    result: str,
    receipt_hash: str,
    reason: str,
    now: str | datetime | None = None,
) -> dict[str, object]:
    observed = _time(now, "now")
    _safe(claim_id, "claim_id")
    _require(result in COMPLETION_RESULTS, "unsupported program claim result")
    _hash(receipt_hash, "receipt_hash")
    normalized_reason = _text(reason, "completion reason", 1_000)
    root = root.resolve()
    _path, grant, _plan = _load_documents(root, run_id)
    projection = replay_program(root, run_id, now=observed)
    claim = next((item for item in projection["active_claims"] if item["claim_id"] == claim_id), None)
    issues: list[dict[str, str]] = []
    if claim is None:
        issues.append({"code": "claim-not-active", "message": "completion names no active program claim"})
    fact_binding, observation_issues = _completion_fact_binding(root, grant, projection)
    issues.extend(observation_issues)
    request = {
        "claim_id": claim_id,
        "result": result,
        "receipt_hash": receipt_hash,
        "reason": normalized_reason,
    }
    unsigned = {
        "kind": PROGRAM_COMPLETION_PREVIEW_KIND,
        "schema_version": PROGRAM_RUN_SCHEMA_VERSION,
        "run_id": run_id,
        "applicable": not issues,
        "issues": issues,
        "request": request,
        "binding": _binding(projection, observed),
        "fact_binding": fact_binding,
        "starts_work": False,
        "writes_state": False,
        "mutates_repository": False,
        "mutates_roadmap": False,
    }
    return {**unsigned, "completion_token": _sha(unsigned)}


def _validate_completion_preview(value: object) -> dict[str, object]:
    preview = _exact(value, _COMPLETION_PREVIEW_KEYS, "program completion preview")
    _require(preview["kind"] == PROGRAM_COMPLETION_PREVIEW_KIND and preview["schema_version"] == PROGRAM_RUN_SCHEMA_VERSION, "unsupported completion preview")
    request = _exact(preview["request"], _COMPLETION_REQUEST_KEYS, "completion request")
    _safe(request["claim_id"], "claim_id")
    _require(request["result"] in COMPLETION_RESULTS, "unsupported program claim result")
    _hash(request["receipt_hash"], "receipt_hash")
    _text(request["reason"], "completion reason", 1_000)
    _exact(preview["binding"], _BINDING_KEYS, "completion binding")
    binding = _exact(preview["fact_binding"], _FACT_BINDING_KEYS, "completion fact binding")
    _exact(binding["repository"], _REPOSITORY_KEYS, "completion repository facts")
    _exact(binding["roadmap"], _ROADMAP_KEYS, "completion roadmap facts")
    _require(isinstance(preview["applicable"], bool) and isinstance(preview["issues"], list), "program completion applicability is invalid")
    for effect in ("starts_work", "writes_state", "mutates_repository", "mutates_roadmap"):
        _require(preview[effect] is False, f"program completion preview {effect} must be false")
    unsigned = {key: item for key, item in preview.items() if key != "completion_token"}
    _require(preview["completion_token"] == _sha(unsigned), "completion token is invalid")
    return preview


def apply_program_completion(
    root: Path,
    preview: object,
    *,
    completion_token: str,
    now: str | datetime | None = None,
) -> dict[str, object]:
    """Record one bounded receipt, even after revocation, for an active claim."""
    submitted = _validate_completion_preview(preview)
    _require(completion_token == submitted["completion_token"], "completion token does not match preview")
    _require(bool(submitted["applicable"]), "program completion preview is not applicable")
    observed = _time(now, "now")
    run_id = str(submitted["run_id"])
    root = root.resolve()
    path, grant, _plan = _load_documents(root, run_id)
    with _lock(path / "ledger.lock"):
        projection = replay_program(root, run_id, now=observed)
        binding = submitted["binding"]
        _require(
            binding["grant_hash"] == projection["grant_hash"]
            and binding["ledger_head"] == projection["ledger_head"]
            and binding["generation"] == projection["generation"]
            and binding["state"] == projection["state"],
            "program completion token is stale",
        )
        request = submitted["request"]
        claim = next((item for item in projection["active_claims"] if item["claim_id"] == request["claim_id"]), None)
        _require(claim is not None, "program claim is no longer active")
        current_facts, observation_issues = _completion_fact_binding(root, grant, projection)
        _require(not observation_issues, "program completion facts cannot be observed")
        _require(submitted["fact_binding"] == current_facts, "program completion facts changed after preview")
        event = _event_document(
            run_id, projection["event_count"] + 1, "claim_completed",
            int(projection["generation"]), observed,
            {
                "claim_id": request["claim_id"],
                "request_hash": claim["request_hash"],
                "result": request["result"],
                "receipt_hash": request["receipt_hash"],
                "reason": request["reason"],
                "fact_binding": submitted["fact_binding"],
            },
            str(projection["ledger_head"]),
        )
        _append_event(path, event)
    return replay_program(root, run_id, now=observed)


def record_program_dispatch(
    root: Path,
    run_id: str,
    *,
    claim_id: str,
    operation_id: str,
    packet_hash: str,
    idempotency_key: str,
    profile: str,
    adapter: str,
    adapter_version: str,
    execution: object,
    child_grant_hash: str | None,
    now: str | datetime | None = None,
    driver_config: dict[str, object] | None = None,
) -> dict[str, object]:
    """Record the durable external-operation boundary before dispatch.

    A mutable driver session file is never proof that an operation did or did
    not start.  This ledger event makes deletion of that file fail closed
    instead of turning restart into a duplicate provider invocation.
    """
    observed = _time(now, "now")
    claim_id = _safe(claim_id, "dispatch claim id")
    operation_id = _safe(operation_id, "dispatch operation id")
    packet_hash = _hash(packet_hash, "dispatch packet hash")
    idempotency_key = _safe(idempotency_key, "dispatch idempotency key")
    profile = _safe(profile, "dispatch profile")
    adapter = _safe(adapter, "dispatch adapter")
    adapter_version = _safe(adapter_version, "dispatch adapter version", reference=True)
    normalized_execution = dict(_exact(execution, _EXECUTION_KEYS, "dispatch execution"))
    if child_grant_hash is not None:
        child_grant_hash = _hash(child_grant_hash, "dispatch child grant hash")
    expected_operation = "operation-" + hashlib.sha256(
        f"{run_id}|{claim_id}".encode("utf-8")
    ).hexdigest()[:24]
    _require(operation_id == expected_operation, "dispatch operation id is not deterministic")

    root = root.resolve()
    path, grant, _plan = _load_documents(root, run_id)
    detail = {
        "claim_id": claim_id,
        "request_hash": "",
        "operation_id": operation_id,
        "packet_hash": packet_hash,
        "idempotency_key": idempotency_key,
        "profile": profile,
        "adapter": adapter,
        "adapter_version": adapter_version,
        "execution": normalized_execution,
        "child_grant_hash": child_grant_hash,
    }
    with _lock(path / "ledger.lock"):
        projection = replay_program(root, run_id, now=observed)
        claim = next(
            (item for item in projection["active_claims"] if item["claim_id"] == claim_id),
            None,
        )
        _require(claim is not None, "dispatch requires one active program claim")
        _require(claim["category"] == "agent", "only an agent claim may dispatch a driver")
        detail["request_hash"] = claim["request_hash"]
        prior = claim.get("dispatch")
        if prior is not None:
            expected_prior = {**detail, "dispatched_at": prior["dispatched_at"]}
            _require(prior == expected_prior, "program claim dispatch conflicts with its durable operation")
            return {**projection, "dispatch": prior, "idempotent": True}
        _require(
            projection["state"] == "running" and projection["mode"] != "advisory",
            "program grant does not permit driver dispatch",
        )
        freshness = program_freshness_issues(
            root, grant, projection, driver_config=driver_config
        )
        _require(not freshness, "program dispatch facts are stale: " + "; ".join(freshness))
        capability, expected_execution = _execution_for_profile(
            root, profile, driver_config
        )
        _require(capability["available"] is True, "dispatch profile is unavailable")
        _require(
            adapter == capability["adapter"]
            and adapter_version == capability["adapter_version"]
            and normalized_execution == expected_execution,
            "dispatch execution binding differs from the resolved profile",
        )
        _require(idempotency_key == claim["idempotency_key"], "driver idempotency key differs from its claim")
        _require(child_grant_hash is not None, "agent dispatch requires one exact child grant")
        _require(
            child_grant_hash == claim["subject"]["hash"],
            "agent claim subject does not bind its child grant",
        )
        event = _event_document(
            run_id,
            int(projection["event_count"]) + 1,
            "claim_dispatched",
            int(projection["generation"]),
            observed,
            detail,
            str(projection["ledger_head"]),
        )
        _append_event(path, event)
    after = replay_program(root, run_id, now=observed)
    dispatch = next(item for item in after["dispatches"] if item["claim_id"] == claim_id)
    return {**after, "dispatch": dispatch, "idempotent": False}


def record_program_obligation(
    root: Path,
    run_id: str,
    *,
    claim_id: str,
    decision_hash: str,
    obligation: object,
    now: str | datetime | None = None,
) -> dict[str, object]:
    """Append one exact council obligation after its reserved claim succeeds."""
    observed = _time(now, "now")
    claim_id = _safe(claim_id, "obligation claim id")
    decision_hash = _hash(decision_hash, "obligation decision hash")
    normalized = _normalize_obligation(obligation)
    root = root.resolve()
    path, _grant, _plan = _load_documents(root, run_id)
    with _lock(path / "ledger.lock"):
        projection = replay_program(root, run_id, now=observed)
        prior = next(
            (item for item in projection["obligations"] if item["id"] == normalized["id"]),
            None,
        )
        if prior is not None:
            _require(
                prior["source_decision_hash"] == decision_hash
                and prior["obligation_hash"] == _sha(normalized),
                "program obligation id was reused for different meaning",
            )
            return {**projection, "obligation": prior, "idempotent": True}
        claim = next(
            (item for item in projection["completed_claims"] if item["claim_id"] == claim_id),
            None,
        )
        _require(
            claim is not None
            and claim["category"] == "obligation-record"
            and claim["status"] == "succeeded"
            and claim["subject"]["kind"] == "program-obligation"
            and claim["subject"]["id"] == normalized["id"]
            and claim["subject"]["hash"] == _sha({
                "decision_hash": decision_hash,
                "obligation": normalized,
            }),
            "obligation record requires one succeeded reserved claim",
        )
        event = _event_document(
            run_id,
            int(projection["event_count"]) + 1,
            "program_obligation_recorded",
            int(projection["generation"]),
            observed,
            {
                "claim_id": claim_id,
                "request_hash": claim["request_hash"],
                "decision_hash": decision_hash,
                "obligation": normalized,
                "obligation_hash": _sha(normalized),
            },
            str(projection["ledger_head"]),
        )
        _append_event(path, event)
    after = replay_program(root, run_id, now=observed)
    recorded = next(item for item in after["obligations"] if item["id"] == normalized["id"])
    return {**after, "obligation": recorded, "idempotent": False}


def dispose_program_obligation(
    root: Path,
    run_id: str,
    *,
    claim_id: str,
    obligation_id: str,
    to_state: str,
    actor: str,
    authority: str,
    reason: str,
    replacement_id: str | None = None,
    now: str | datetime | None = None,
) -> dict[str, object]:
    """Record one separately claimed terminal obligation disposition."""
    observed = _time(now, "now")
    claim_id = _safe(claim_id, "obligation disposition claim id")
    obligation_id = _safe(obligation_id, "obligation disposition id")
    _require(to_state in _OBLIGATION_TERMINAL_STATES, "obligation disposition state is unsupported")
    actor = _safe(actor, "obligation disposition actor", reference=True)
    authority = _safe(authority, "obligation disposition authority", reference=True)
    reason = _text(reason, "obligation disposition reason", 1_000)
    if replacement_id is not None:
        replacement_id = _safe(replacement_id, "obligation replacement id")
    _require(
        (to_state == "superseded") == (replacement_id is not None),
        "superseded obligation must name exactly one replacement",
    )
    root = root.resolve()
    path, _grant, _plan = _load_documents(root, run_id)
    with _lock(path / "ledger.lock"):
        projection = replay_program(root, run_id, now=observed)
        obligation = next(
            (item for item in projection["obligations"] if item["id"] == obligation_id),
            None,
        )
        _require(obligation is not None, "obligation disposition names no durable obligation")
        if obligation["state"] in _OBLIGATION_TERMINAL_STATES:
            history = obligation["history"]
            prior = history[-1] if history else None
            _require(
                prior is not None
                and prior["claim_id"] == claim_id
                and prior["to_state"] == to_state
                and prior["actor"] == actor
                and prior["authority"] == authority
                and prior["reason"] == reason
                and prior["replacement_id"] == replacement_id,
                "obligation already has a different terminal disposition",
            )
            return {**projection, "obligation": obligation, "idempotent": True}
        claim = next(
            (item for item in projection["completed_claims"] if item["claim_id"] == claim_id),
            None,
        )
        _require(
            claim is not None
            and claim["category"] == "obligation-disposition"
            and claim["status"] == "succeeded"
            and claim["subject"]["kind"] == "program-obligation-disposition"
            and claim["subject"]["id"] == obligation_id
            and claim["subject"]["hash"] == _sha({
                "obligation_id": obligation_id,
                "from_state": obligation["state"],
                "to_state": to_state,
                "actor": actor,
                "authority": authority,
                "reason": reason,
                "replacement_id": replacement_id,
            }),
            "obligation disposition requires one succeeded reserved claim",
        )
        event = _event_document(
            run_id,
            int(projection["event_count"]) + 1,
            "program_obligation_disposed",
            int(projection["generation"]),
            observed,
            {
                "claim_id": claim_id,
                "request_hash": claim["request_hash"],
                "obligation_id": obligation_id,
                "from_state": obligation["state"],
                "to_state": to_state,
                "actor": actor,
                "authority": authority,
                "reason": reason,
                "replacement_id": replacement_id,
            },
            str(projection["ledger_head"]),
        )
        _append_event(path, event)
    after = replay_program(root, run_id, now=observed)
    disposed = next(item for item in after["obligations"] if item["id"] == obligation_id)
    return {**after, "obligation": disposed, "idempotent": False}


def record_program_delivery_facts(
    root: Path,
    run_id: str,
    *,
    claim_id: str,
    proof_hash: str,
    files_touched: list[str],
    now: str | datetime | None = None,
) -> dict[str, object]:
    """Ledger the bounded facts from which advisory delivery memory derives."""
    observed = _time(now, "now")
    claim_id = _safe(claim_id, "delivery facts claim id")
    proof_hash = _hash(proof_hash, "delivery facts proof hash")
    touched = sorted(set(files_touched))
    _require(touched == files_touched, "delivery touched-file set must be sorted and unique")
    _require(
        all(
            isinstance(item, str) and bool(item) and len(item) <= 500
            and "\x00" not in item and "\n" not in item and "\r" not in item
            for item in touched
        ),
        "delivery touched-file set contains an unsafe path",
    )
    root = root.resolve()
    path, grant, _plan = _load_documents(root, run_id)
    with _lock(path / "ledger.lock"):
        projection = replay_program(root, run_id, now=observed)
        expected = {
            "claim_id": claim_id,
            "request_hash": next(
                (
                    item["request_hash"]
                    for item in projection["completed_claims"]
                    if item["claim_id"] == claim_id
                ),
                None,
            ),
            "proof_hash": proof_hash,
            "story_ids": list(projection["selected_stories"]),
            "files_touched": touched,
            "head_sha": projection["expected_repository"]["head"],
            "verdict_outcome": "passed",
            "obligation_ids": sorted(
                item["id"] for item in projection["obligations"]
            ),
        }
        if projection["delivery_facts"] is not None:
            _require(
                projection["delivery_facts"] == expected,
                "program delivery facts were already recorded differently",
            )
            return {**projection, "idempotent": True}
        _require(projection["state"] == "running", "delivery facts require a running program")
        claim = next(
            (
                item for item in projection["completed_claims"]
                if item["claim_id"] == claim_id
            ),
            None,
        )
        _require(
            claim is not None
            and claim["category"] == "assignment"
            and claim["status"] == "succeeded"
            and claim["subject"]["kind"] == "program-scope-proof"
            and claim["subject"]["hash"] == proof_hash,
            "delivery facts require one succeeded scope-proof claim",
        )
        event = _event_document(
            run_id,
            int(projection["event_count"]) + 1,
            "program_delivery_facts_recorded",
            int(projection["generation"]),
            observed,
            expected,
            str(projection["ledger_head"]),
        )
        _append_event(path, event)
    return {**replay_program(root, run_id, now=observed), "idempotent": False}


def complete_program_scope(
    root: Path,
    run_id: str,
    *,
    claim_id: str,
    proof_hash: str,
    completed_stories: list[str],
    completed_phases: list[int],
    now: str | datetime | None = None,
) -> dict[str, object]:
    """Enter the exact authority terminal after a conductor proof is claimed."""
    observed = _time(now, "now")
    claim_id = _safe(claim_id, "scope completion claim id")
    proof_hash = _hash(proof_hash, "scope completion proof hash")
    stories = sorted(set(completed_stories))
    phases = sorted(set(completed_phases))
    _require(stories == completed_stories, "completed story set must be sorted and unique")
    _require(phases == completed_phases, "completed phase set must be sorted and unique")
    root = root.resolve()
    path, grant, _plan = _load_documents(root, run_id)
    with _lock(path / "ledger.lock"):
        projection = replay_program(root, run_id, now=observed)
        if projection["scope_completion"] is not None:
            prior = projection["scope_completion"]
            _require(
                prior["claim_id"] == claim_id
                and prior["proof_hash"] == proof_hash
                and prior["completed_stories"] == stories
                and prior["completed_phases"] == phases,
                "program scope already completed under a different proof",
            )
            return {**projection, "idempotent": True}
        _require(projection["state"] == "running", "program scope can complete only while running")
        _require(stories == sorted(grant["scope"]["story_ids"]), "scope completion omits a granted story")  # type: ignore[index]
        _require(phases == sorted(grant["scope"]["phases"]), "scope completion omits a granted phase")  # type: ignore[index]
        _require(not projection["blocking_obligations"], "scope completion has an open blocking obligation")
        claim = next(
            (item for item in projection["completed_claims"] if item["claim_id"] == claim_id),
            None,
        )
        _require(
            claim is not None
            and claim["category"] == "assignment"
            and claim["status"] == "succeeded"
            and claim["subject"]["kind"] == "program-scope-proof"
            and claim["subject"]["hash"] == proof_hash,
            "scope completion requires one succeeded reserved assignment claim",
        )
        freshness = program_freshness_issues(root, grant, projection)
        _require(not freshness, "scope completion facts are stale: " + "; ".join(freshness))
        current = build_program_plan(root, str(grant["program_selector"]))
        issue_codes = {
            str(item.get("code"))
            for item in current.get("issues", []) if isinstance(item, dict)
        }
        _require(
            current.get("selection") is None
            and "scope-complete" in issue_codes,
            "scope completion requires the roadmap planner to prove the exact grant scope complete",
        )
        event = _event_document(
            run_id,
            int(projection["event_count"]) + 1,
            "program_scope_completed",
            int(projection["generation"]),
            observed,
            {
                "claim_id": claim_id,
                "request_hash": claim["request_hash"],
                "proof_hash": proof_hash,
                "completed_stories": stories,
                "completed_phases": phases,
                "open_obligation_ids": sorted(
                    item["id"] for item in projection["open_obligations"]
                ),
            },
            str(projection["ledger_head"]),
        )
        _append_event(path, event)
    return {**replay_program(root, run_id, now=observed), "idempotent": False}


def _control_effect(projection: dict[str, object], action: str) -> dict[str, object]:
    to_state = {
        "pause": "paused",
        "resume": "checkpoint" if projection["outstanding_requests"] else "running",
        "revoke": "revoked", "cancel": "cancelled",
    }[action]
    new_generation = int(projection["generation"]) + (1 if action in {"revoke", "cancel"} else 0)
    return {
        "from_state": projection["state"],
        "to_state": to_state,
        "new_generation": new_generation,
        "expired_request_ids": sorted(
            item["claim_id"] for item in projection["outstanding_requests"]
            if action in {"revoke", "cancel"}
        ),
        "interrupt_claim_ids": sorted(
            item["claim_id"] for item in projection["active_claims"]
            if action == "cancel"
        ),
    }


def build_program_control_preview(
    root: Path,
    run_id: str,
    *,
    action: str,
    decision: str,
    reason: str,
    now: str | datetime | None = None,
    driver_config: dict[str, object] | None = None,
) -> dict[str, object]:
    observed = _time(now, "now")
    _require(action in CONTROL_ACTIONS, "unsupported program control action")
    _require(decision in CONTROL_DECISIONS, "unsupported program control decision")
    normalized_reason = _text(reason, "control reason", 1_000)
    _path, grant, _plan = _load_documents(root.resolve(), run_id)
    projection = replay_program(root, run_id, now=observed)
    issues: list[dict[str, str]] = []
    if projection["state"] not in _CONTROL_ALLOWED_STATES[action]:
        issues.append({"code": "control-state", "message": f"cannot {action} program state {projection['state']}"})
    if decision != "approve":
        issues.append({"code": "control-denied", "message": "denied control previews do not mutate the ledger"})
    if action == "resume":
        for message in program_freshness_issues(root, grant, projection, driver_config=driver_config):
            issues.append({"code": "program-stale", "message": message})
    request = {"action": action, "decision": decision, "reason": normalized_reason}
    effect = _control_effect(projection, action)
    unsigned = {
        "kind": PROGRAM_CONTROL_PREVIEW_KIND,
        "schema_version": PROGRAM_RUN_SCHEMA_VERSION,
        "run_id": run_id,
        "applicable": not issues,
        "issues": issues,
        "request": request,
        "binding": _binding(projection, observed),
        "effect": effect,
        "starts_work": False,
        "writes_state": False,
        "dispatches_child": False,
        "mutates_repository": False,
        "mutates_roadmap": False,
    }
    return {**unsigned, "control_token": _sha(unsigned)}


def _validate_control_preview(value: object) -> dict[str, object]:
    preview = _exact(value, _CONTROL_PREVIEW_KEYS, "program control preview")
    _require(preview["kind"] == PROGRAM_CONTROL_PREVIEW_KIND and preview["schema_version"] == PROGRAM_RUN_SCHEMA_VERSION, "unsupported control preview")
    request = _exact(preview["request"], _CONTROL_REQUEST_KEYS, "control request")
    _require(request["action"] in CONTROL_ACTIONS, "unsupported program control action")
    _require(request["decision"] in CONTROL_DECISIONS, "unsupported program control decision")
    _text(request["reason"], "control reason", 1_000)
    _exact(preview["binding"], _BINDING_KEYS, "control binding")
    _exact(preview["effect"], _CONTROL_EFFECT_KEYS, "program control effect")
    _require(isinstance(preview["applicable"], bool) and isinstance(preview["issues"], list), "program control applicability is invalid")
    for effect in ("starts_work", "writes_state", "dispatches_child", "mutates_repository", "mutates_roadmap"):
        _require(preview[effect] is False, f"program control preview {effect} must be false")
    unsigned = {key: item for key, item in preview.items() if key != "control_token"}
    _require(preview["control_token"] == _sha(unsigned), "control token is invalid")
    return preview


def apply_program_control(
    root: Path,
    preview: object,
    *,
    control_token: str,
    now: str | datetime | None = None,
    driver_config: dict[str, object] | None = None,
) -> dict[str, object]:
    submitted = _validate_control_preview(preview)
    _require(control_token == submitted["control_token"], "control token does not match preview")
    _require(bool(submitted["applicable"]), "program control preview is not applicable")
    observed = _time(now, "now")
    run_id = str(submitted["run_id"])
    path, grant, _plan = _load_documents(root.resolve(), run_id)
    with _lock(path / "ledger.lock"):
        projection = replay_program(root, run_id, now=observed)
        binding = submitted["binding"]
        _require(
            binding["grant_hash"] == projection["grant_hash"]
            and binding["ledger_head"] == projection["ledger_head"]
            and binding["generation"] == projection["generation"]
            and binding["state"] == projection["state"],
            "program control token is stale",
        )
        request = submitted["request"]
        action = str(request["action"])
        _require(request["decision"] == "approve", "only an approved control decision may mutate the ledger")
        _require(projection["state"] in _CONTROL_ALLOWED_STATES[action], f"cannot {action} program state {projection['state']}")
        if action == "resume":
            freshness = program_freshness_issues(root, grant, projection, driver_config=driver_config)
            _require(not freshness, "program resume facts are stale: " + "; ".join(freshness))
        effect = submitted["effect"]
        _require(effect == _control_effect(projection, action), "program control effect differs from current authority state")
        event_name = {
            "pause": "program_paused", "resume": "program_resumed",
            "revoke": "program_revoked", "cancel": "program_cancelled",
        }[action]
        event = _event_document(
            run_id, projection["event_count"] + 1, event_name,
            int(effect["new_generation"]), observed,
            {
                "action": action,
                "reason": request["reason"],
                "decision": request["decision"],
                "token_hash": _sha({"control_token": control_token}),
                "from_state": effect["from_state"],
                "to_state": effect["to_state"],
                "new_generation": effect["new_generation"],
                "expired_request_ids": effect["expired_request_ids"],
                "interrupt_claim_ids": effect["interrupt_claim_ids"],
            },
            str(projection["ledger_head"]),
        )
        _append_event(path, event)
    return replay_program(root, run_id, now=observed)


def program_run_inventory(root: Path, *, now: str | datetime | None = None) -> dict[str, object]:
    """Return a pure inventory; an absent program store is healthy and empty."""
    root = root.resolve()
    store = program_store_dir(root)
    runs_dir = store / "runs"
    runs: list[dict[str, object]] = []
    healthy = True
    if runs_dir.is_dir():
        for path in sorted(runs_dir.iterdir(), key=lambda item: item.name):
            if not path.is_dir() or not _RUN_ID_RE.fullmatch(path.name):
                continue
            try:
                projection = replay_program(root, path.name, now=now)
                runs.append({
                    "run_id": path.name,
                    "program": projection["program"]["slug"],
                    "mode": projection["mode"],
                    "state": projection["state"],
                    "grant_hash": projection["grant_hash"],
                    "ledger_head": projection["ledger_head"],
                })
            except DwError as exc:
                healthy = False
                runs.append({
                    "run_id": path.name, "program": None, "mode": None,
                    "state": "corrupt", "grant_hash": None,
                    "ledger_head": None, "error": exc.message,
                })
    return {
        "kind": PROGRAM_RUN_LIST_KIND,
        "schema_version": PROGRAM_RUN_SCHEMA_VERSION,
        "runs": runs,
        "healthy": healthy,
        "starts_work": False,
        "writes_state": False,
        "creates_grant": False,
    }
