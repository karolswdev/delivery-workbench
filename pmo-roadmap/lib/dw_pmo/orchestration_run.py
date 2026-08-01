"""Run authorization, immutable grants, and the orchestration event ledger.

A tracked orchestration score is configuration, never consent.  This module
adds the separate local authority ring: a pure plan binds the current score,
Git/status/story facts, requested capabilities, finite budgets, and expiry;
one exact approval can atomically create an immutable grant and hash-chained
ledger.  Runtime modules may later claim nodes, but only through the replayed
grant projection and an exclusive ledger lock.
"""

from __future__ import annotations

import fcntl
import hashlib
import json
import os
import re
import shutil
import tempfile
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Iterator

from . import repofacts
from .gitio import current_branch, head_sha, in_rewrite_state, run_git, write_tree
from .model import DwError, normalize_status
from .orchestration import (
    NUDGE_SIGNALS,
    canonical_json,
    compile_score,
    compile_score_path,
    find_score_path,
)
from .parse import discover_phases, discover_projects, find_story, get_project, story_title
from .paths import rel
from .status import build_status


RUN_PLAN_KIND = "delivery-workbench-run-plan"
RUN_GRANT_KIND = "delivery-workbench-run-grant"
RUN_EVENT_KIND = "delivery-workbench-run-event"
RUN_KIND = "delivery-workbench-run"
RUN_SCHEMA_VERSION = 1
MAX_GRANT_SECONDS = 86_400
PERMANENT_EXCLUSIONS = (
    "certify-contract",
    "commit",
    "push",
    "release",
    "deploy",
    "provider-credentials",
    "provider-executables",
    "agent-invented-commands",
)

_RUN_ID_RE = re.compile(r"^run-[0-9a-f]{24}$")
_SAFE_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}$")
_SAFE_NODE_RE = re.compile(r"^[a-z][a-z0-9]*(?:-[a-z0-9]+)*$")

_PLAN_KEYS = {
    "kind", "schema_version", "applicable", "issues", "request",
    "repository", "status", "story", "score", "authority",
    "start_token", "starts_work", "writes_run_state",
}
_REQUEST_KEYS = {
    "score", "project", "story", "issued_at", "expires_at",
    "standing_nudges", "signal_channel",
}
_GRANT_KEYS = {
    "kind", "schema_version", "run_id", "grant_hash", "start_token",
    "repository", "status_hash", "score", "project", "story",
    "capabilities", "profiles", "workspace_modes", "budgets",
    "standing_nudge_rules", "signal_channel",
    "issued_at", "expires_at", "approved_at", "approved_by",
    "revocation_generation", "permanent_exclusions",
}
_NUDGE_REFUSAL_REASONS = {
    "no-standing-rule", "nudge-budget-exhausted", "rule-exhausted",
    "run-inactive", "grant-expired", "non-receptive", "attempt-ceiling",
}
_REQUEST_REFUSAL_REASONS = {
    "correlation-mismatch", "invalid-response", "expired",
}
_REQUEST_CLOSED_STATES = {"complete", "blocked", "cancelled", "revoked"}
_EXTERNAL_COMMIT_LEGACY_KEYS = {"previous_head", "head", "relation"}
_EXTERNAL_COMMIT_BOUND_KEYS = _EXTERNAL_COMMIT_LEGACY_KEYS | {
    "repository_id", "branch", "index_tree", "operation", "status_hash",
    "story_hash", "rebindable",
}
_EVENT_KEYS = {
    "kind", "schema_version", "run_id", "seq", "event", "ts", "detail",
    "prev_hash", "event_hash",
}
_NODE_RECEIPT_LEGACY_KEYS = {
    "node_id", "attempt", "claim_id", "executor", "execution_id",
    "state", "reason", "receipt_hash",
}
_EVENT_DETAIL_KEYS = {
    "run_started": {"semantic_hash", "status_hash", "expires_at"},
    "run_paused": {"reason", "generation"},
    "run_resumed": {"generation"},
    "run_revoked": {"reason", "generation"},
    "run_cancelled": {"reason", "generation"},
    "node_claimed": {
        "node_id", "node_type", "attempt", "claim_id", "idempotency_key",
        "generation",
    },
    "node_released": {
        "node_id", "attempt", "claim_id", "outcome", "artifact_bytes",
    },
    "node_receipt": {
        "node_id", "attempt", "claim_id", "executor", "execution_id",
        "state", "reason", "receipt_hash", "usage_status", "total_tokens",
        "cost_microunits",
    },
    "activity_observed": {
        "node_id", "attempt", "claim_id", "activity", "session_id",
    },
    "nudge_delivered": {
        "rule", "signal", "signal_hash", "node_id", "attempt", "remaining",
    },
    "nudge_refused": {
        "rule", "signal", "signal_hash", "reason",
    },
    "failure_routed": {
        "node_id", "attempt", "action", "target", "visit",
        "target_attempt",
    },
    "route_resolved": {
        "node_id", "attempt", "target", "target_attempt", "visit",
        "outcome",
    },
    "checkpoint_reached": {
        "node_id", "checkpoint", "mode", "terminal", "reason",
    },
    "checkpoint_decided": {
        "node_id", "checkpoint", "mode", "decision",
    },
    "request_republished": {"correlation_id", "generation"},
    "request_decided": {"correlation_id", "decision", "response_hash"},
    "request_refused": {"correlation_id", "reason", "response_hash"},
    "run_aborted": {"node_id", "reason", "generation"},
    "run_terminal": {"node_id", "meaning"},
    "rail_advanced": {
        "node_id", "action", "repository_id", "branch", "head",
        "index_tree", "operation", "status_hash", "story_hash",
    },
    "external_commit_observed": _EXTERNAL_COMMIT_BOUND_KEYS,
    "memory-recall-built": {
        "recall_id", "subject", "source_revision", "audience", "byte_count",
        "included_item_count", "exclusion_count",
    },
    "memory-recall-attached": {
        "recall_id", "subject", "source_revision", "audience", "byte_count",
        "included_item_count", "exclusion_count", "node_id", "claim_id",
        "packet_hash",
    },
}

_RUNTIME_EVENTS = {
    "node_receipt", "activity_observed", "nudge_delivered", "nudge_refused",
    "failure_routed", "route_resolved",
    "checkpoint_reached", "checkpoint_decided", "run_aborted",
    "request_republished", "request_decided", "request_refused",
    "run_terminal", "rail_advanced", "external_commit_observed",
    "memory-recall-built", "memory-recall-attached",
}

# The driver activity vocabulary (docs/signals.md). This is a separate
# axis from run/node lifecycle states: it says what a live agent session
# is doing, not whether the node succeeded. `blocked` here means the
# agent is stopped on a pending permission/approval decision.
ACTIVITY_STATES = frozenset(
    {"active", "idle", "waiting_input", "blocked", "exited", "unknown"}
)


def _utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(microsecond=0)


def _format_time(value: datetime) -> str:
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc).replace(microsecond=0).strftime(
        "%Y-%m-%dT%H:%M:%SZ"
    )


def _parse_time(value: object, field: str) -> datetime:
    if not isinstance(value, str) or not value:
        raise DwError(f"{field} must be a UTC timestamp")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise DwError(f"{field} must be an ISO-8601 timestamp") from exc
    if parsed.tzinfo is None:
        raise DwError(f"{field} must include a timezone")
    return parsed.astimezone(timezone.utc).replace(microsecond=0)


def _sha(value: object) -> str:
    return "sha256:" + hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def _request_correlation(event: dict[str, object]) -> str:
    """Derive a stable, content-free request id from its opening event.

    ``checkpoint_reached`` and ``nudge_refused:no-standing-rule`` already are
    the authoritative, hash-chained facts that a human decision is needed.
    Deriving the id from that fact keeps older ledgers readable and avoids a
    second request store or a crash gap between "checkpoint" and "request".
    """
    digest = str(event["event_hash"]).partition(":")[2]
    return "req-" + digest[:24]


def _file_sha(path: Path | None) -> str | None:
    if path is None or not path.is_file():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return "sha256:" + digest.hexdigest()


def _git_dir(root: Path) -> Path:
    # WLA-28-02: routed through the repository-fact boundary, which memoizes
    # the resolution per root. The previous fast path returned root/.git
    # without asking git; that is wrong for a linked worktree, where .git is a
    # file. The boundary asks git and gets it right.
    try:
        path = repofacts.git_dir(root)
    except DwError as exc:
        raise DwError("orchestration runs require a Git repository") from exc
    if not path.is_dir():
        raise DwError("cannot resolve the repository Git directory")
    return path


def run_store_dir(root: Path) -> Path:
    git_dir = _git_dir(root)
    store = git_dir / "pmo-orchestration"
    if store.is_symlink():
        raise DwError("refusing symlinked orchestration run store")
    if store.exists():
        resolved = store.resolve()
        if resolved != git_dir and git_dir not in resolved.parents:
            raise DwError("orchestration run store escapes the Git directory")
        if not resolved.is_dir():
            raise DwError("orchestration run store is not a directory")
    return store


def _run_dir(root: Path, run_id: str, *, must_exist: bool = True) -> Path:
    if not _RUN_ID_RE.fullmatch(run_id or ""):
        raise DwError(f"unsafe orchestration run id: {run_id!r}")
    store = run_store_dir(root)
    path = store / "runs" / run_id
    if path.is_symlink():
        raise DwError(f"refusing symlinked orchestration run: {run_id}")
    if must_exist and not path.is_dir():
        raise DwError(f"orchestration run not found: {run_id}")
    if path.exists():
        resolved = path.resolve()
        runs = (store / "runs").resolve()
        if resolved.parent != runs:
            raise DwError(f"orchestration run escapes the run store: {run_id}")
    return path


@contextmanager
def _store_lock(root: Path) -> Iterator[Path]:
    store = run_store_dir(root)
    store.mkdir(parents=True, exist_ok=True, mode=0o700)
    os.chmod(store, 0o700)
    lock_path = store / ".ledger.lock"
    with lock_path.open("a+", encoding="utf-8") as handle:
        os.chmod(lock_path, 0o600)
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
        try:
            yield store
        finally:
            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


def _story_facts(root: Path, project_slug: str, selector: str) -> dict[str, object]:
    root = root.resolve()
    project = get_project(root, project_slug)
    found: list[tuple[object, object, int, Path]] = []
    for phase in discover_phases(project):
        try:
            row, number, path = find_story(project, phase, selector)
        except DwError:
            continue
        found.append((phase, row, number, path))
    if not found:
        raise DwError(f"story not found in {project_slug}: {selector}")
    if len(found) > 1:
        raise DwError(f"ambiguous story selector in {project_slug}: {selector}")
    phase, row, _number, path = found[0]
    evidence = phase.path / f"evidence-story-{_number:02d}.md"  # type: ignore[attr-defined]
    return {
        "id": row.story_id,  # type: ignore[attr-defined]
        "title": story_title(path),
        "status": normalize_status(row.status),  # type: ignore[attr-defined]
        "phase": phase.number,  # type: ignore[attr-defined]
        "story_path": rel(path, root),
        "story_hash": _file_sha(path),
        "evidence_path": rel(evidence, root) if evidence.is_file() else None,
        "evidence_hash": _file_sha(evidence),
    }


def _status_binding(status: dict[str, object]) -> dict[str, object]:
    repository = status["repository"]  # type: ignore[index]
    roadmap = status["roadmap"]  # type: ignore[index]
    projects = roadmap.get("projects", [])  # type: ignore[union-attr]
    selected = roadmap.get("selected_project")  # type: ignore[union-attr]
    selected_summary = next(
        (item for item in projects if item.get("slug") == selected),
        None,
    )
    next_action = status.get("next_action") or {}
    return {
        "kind": status.get("kind"),
        "schema_version": status.get("schema_version"),
        "verdict": status.get("verdict"),
        "summary": status.get("summary"),
        "repository": {
            "branch": repository.get("branch"),  # type: ignore[union-attr]
            "head": repository.get("head"),  # type: ignore[union-attr]
            "operation": repository.get("operation"),  # type: ignore[union-attr]
            "clean": repository.get("clean"),  # type: ignore[union-attr]
            "changes": repository.get("changes"),  # type: ignore[union-attr]
            "contract_state": repository.get("contract", {}).get("state"),  # type: ignore[union-attr]
            "gate_state": repository.get("gate", {}).get("state"),  # type: ignore[union-attr]
        },
        "rails_healthy": status.get("rails", {}).get("healthy"),  # type: ignore[union-attr]
        "roadmap_healthy": roadmap.get("healthy"),  # type: ignore[union-attr]
        "selected_project": selected,
        "project": selected_summary,
        "next_action": {
            "id": next_action.get("id"),  # type: ignore[union-attr]
            "kind": next_action.get("kind"),  # type: ignore[union-attr]
            "blocking": next_action.get("blocking"),  # type: ignore[union-attr]
        },
    }


def _repository_id(root: Path) -> str:
    return _sha({"root": str(root.resolve()), "git_dir": str(_git_dir(root))})


def _normalize_standing_nudges(value: object) -> tuple[list[str], list[str]]:
    """Normalize `signal` / `signal=target` matchers; return (rules, issues)."""
    if value is None:
        return [], []
    if not isinstance(value, (list, tuple)):
        return [], ["standing nudge rules must be a list of matcher strings"]
    issues: list[str] = []
    rules: set[str] = set()
    for raw in value:
        text = str(raw).strip()
        if not text:
            continue
        signal, _, target = text.partition("=")
        if signal not in NUDGE_SIGNALS:
            issues.append(f"standing nudge rule names unknown signal {signal!r}")
            continue
        if target and not _SAFE_NODE_RE.fullmatch(target):
            issues.append(f"standing nudge rule has unsafe target {target!r}")
            continue
        rules.add(f"{signal}={target}" if target else signal)
    if len(rules) > 20:
        issues.append("standing nudge rules exceed the 20-rule bound")
        return [], issues
    return sorted(rules), issues


def build_run_plan(
    root: Path,
    score_selector: str,
    project: str | None,
    story: str | None,
    *,
    expires_at: str | datetime | None = None,
    issued_at: str | datetime | None = None,
    standing_nudges: object = None,
    signal_channel: str | None = None,
) -> dict[str, object]:
    """Build a pure, exact start plan.  No run directory is read or written."""
    root = root.resolve()
    issued = (
        _parse_time(issued_at, "issued_at") if isinstance(issued_at, str)
        else (issued_at or _utc_now()).astimezone(timezone.utc).replace(microsecond=0)
    )
    if expires_at is None:
        expiry = issued + timedelta(hours=1)
    elif isinstance(expires_at, str):
        expiry = _parse_time(expires_at, "expires_at")
    else:
        expiry = expires_at.astimezone(timezone.utc).replace(microsecond=0)

    score_path = find_score_path(root, score_selector)
    compiled = compile_score_path(score_path)
    score = compiled["score"]
    configured_project = str(score.get("project") or "")
    if project is None:
        if configured_project:
            project = configured_project
        else:
            projects = discover_projects(root)
            if len(projects) != 1:
                raise DwError("run planning requires an explicit unambiguous project")
            project = projects[0].slug
    if not story:
        raise DwError("run planning requires an explicit story id")

    story_document = _story_facts(root, project, story)
    status_document = build_status(root, project)
    status_binding = _status_binding(status_document)
    repository = {
        "id": _repository_id(root),
        "branch": current_branch(root),
        "head": head_sha(root) or "none",
        "index_tree": write_tree(root) or "unknown",
        "operation": "rewrite" if in_rewrite_state(root) else "normal",
    }
    node_documents = score.get("nodes", [])
    capabilities = sorted({
        str(capability)
        for node in node_documents
        if isinstance(node, dict)
        for capability in node.get("capabilities", [])
    })
    profiles = sorted({
        str(node.get("profile"))
        for node in node_documents
        if isinstance(node, dict) and node.get("profile")
    })
    workspace_modes = sorted({
        str(node.get("workspace"))
        for node in node_documents
        if isinstance(node, dict) and node.get("workspace")
    })
    budgets = dict(score.get("defaults", {}))
    issues: list[str] = []
    if configured_project and configured_project != project:
        issues.append(
            f"score project {configured_project!r} does not match requested project {project!r}"
        )
    if expiry <= issued:
        issues.append("grant expiry must be later than issuance")
    if (expiry - issued).total_seconds() > MAX_GRANT_SECONDS:
        issues.append(f"grant lifetime exceeds the {MAX_GRANT_SECONDS}-second ceiling")
    if repository["operation"] != "normal":
        issues.append("repository is in a rewrite operation")
    status_repo = status_binding["repository"]
    if not status_repo.get("clean"):  # type: ignore[union-attr]
        issues.append("repository workspace is not clean")
    if not status_binding.get("rails_healthy"):
        issues.append("Delivery Workbench rails are unhealthy")
    if not status_binding.get("roadmap_healthy"):
        issues.append("roadmap validation is unhealthy")
    if story_document["status"] != "in-progress":
        issues.append(
            f"story {story_document['id']} must be in-progress, not {story_document['status']}"
        )
    standing, standing_issues = _normalize_standing_nudges(standing_nudges)
    issues.extend(standing_issues)
    channel = str(signal_channel or "").strip()
    if channel and "/" not in channel:
        issues.append("signal channel must be remote/branch")
    rule_signals = {
        str(rule.get("signal"))
        for rule in score.get("nudges", [])
        if isinstance(rule, dict)
    }
    for matcher in standing:
        if matcher.partition("=")[0] not in rule_signals:
            issues.append(
                f"standing nudge rule {matcher!r} covers no declared score rule"
            )
    if channel and not rule_signals - {"waiting-input-timeout"}:
        issues.append("signal channel is bound but the score declares no SCM nudge rules")

    request = {
        "score": score_selector,
        "project": project,
        "story": story_document["id"],
        "issued_at": _format_time(issued),
        "expires_at": _format_time(expiry),
        "standing_nudges": standing,
        "signal_channel": channel,
    }
    score_binding = {
        "selector": score_selector,
        "slug": score.get("slug"),
        "title": score.get("title"),
        "path": rel(score_path, root),
        "semantic_hash": compiled["semantic_hash"],
        "document_hash": compiled["document_hash"],
    }
    status_summary = {
        "hash": _sha(status_binding),
        "binding": status_binding,
    }
    authority = {
        "capabilities": capabilities,
        "profiles": profiles,
        "workspace_modes": workspace_modes,
        "budgets": budgets,
        "standing_nudge_rules": [
            {"signal": matcher.partition("=")[0], "target": matcher.partition("=")[2]}
            for matcher in standing
        ],
        "signal_channel": channel,
        "permanent_exclusions": list(PERMANENT_EXCLUSIONS),
        "revocation_generation": 0,
    }
    unsigned: dict[str, object] = {
        "kind": RUN_PLAN_KIND,
        "schema_version": RUN_SCHEMA_VERSION,
        "applicable": not issues,
        "issues": issues,
        "request": request,
        "repository": repository,
        "status": status_summary,
        "story": story_document,
        "score": score_binding,
        "authority": authority,
        "starts_work": False,
        "writes_run_state": False,
    }
    return {**unsigned, "start_token": _sha(unsigned)}


def _validate_plan_shape(plan: object) -> dict[str, object]:
    if not isinstance(plan, dict):
        raise DwError("run start plan must be a JSON object")
    unknown = sorted(set(plan) - _PLAN_KEYS)
    missing = sorted(_PLAN_KEYS - set(plan))
    if unknown or missing:
        raise DwError(
            "run plan has non-exact keys"
            + (f"; unknown: {', '.join(unknown)}" if unknown else "")
            + (f"; missing: {', '.join(missing)}" if missing else "")
        )
    request = plan.get("request")
    if not isinstance(request, dict) or set(request) != _REQUEST_KEYS:
        raise DwError("run plan request has non-exact keys")
    if plan.get("kind") != RUN_PLAN_KIND or plan.get("schema_version") != RUN_SCHEMA_VERSION:
        raise DwError("unsupported run plan kind or schema version")
    return plan


def _write_json(path: Path, value: object, mode: int = 0o600) -> None:
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
    detail: dict[str, object],
    prev_hash: str | None,
    now: datetime,
) -> dict[str, object]:
    allowed = _EVENT_DETAIL_KEYS.get(event)
    detail_keys = set(detail)
    legacy_external = (
        event == "external_commit_observed"
        and detail_keys == _EXTERNAL_COMMIT_LEGACY_KEYS
    )
    legacy_node_receipt = (
        event == "node_receipt"
        and detail_keys == _NODE_RECEIPT_LEGACY_KEYS
    )
    if allowed is None or (
        detail_keys != allowed and not legacy_external and not legacy_node_receipt
    ):
        raise DwError(f"event {event!r} has non-exact detail keys")
    for key, value in detail.items():
        if isinstance(value, (dict, list)) or value is None:
            raise DwError(f"event detail {key!r} must be a scalar")
        if isinstance(value, str) and (len(value) > 200 or "\n" in value or "\0" in value):
            raise DwError(f"event detail {key!r} is not content-safe")
    unsigned: dict[str, object] = {
        "kind": RUN_EVENT_KIND,
        "schema_version": RUN_SCHEMA_VERSION,
        "run_id": run_id,
        "seq": seq,
        "event": event,
        "ts": _format_time(now),
        "detail": detail,
        "prev_hash": prev_hash,
    }
    return {**unsigned, "event_hash": _sha(unsigned)}


def _write_cache(run_dir: Path, projection: dict[str, object]) -> None:
    path = run_dir / "projection.json"
    try:
        fd, temp_name = tempfile.mkstemp(prefix=".projection.", dir=str(run_dir))
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                json.dump(projection, handle, indent=2, sort_keys=True)
                handle.write("\n")
                handle.flush()
                os.fsync(handle.fileno())
            os.chmod(temp_name, 0o600)
            os.replace(temp_name, path)
        finally:
            if os.path.exists(temp_name):
                os.unlink(temp_name)
    except OSError:
        # The ledger is authoritative; a disposable cache can always vanish.
        return


def start_run(
    root: Path,
    plan: object,
    expect: str,
    *,
    approved: bool,
    approved_by: str,
    now: datetime | None = None,
) -> dict[str, object]:
    """Atomically create one immutable score/grant and initial ledger event."""
    document = _validate_plan_shape(plan)
    if not approved:
        raise DwError("run start requires one explicit approval")
    if not isinstance(approved_by, str) or not approved_by.strip():
        raise DwError("run start requires a non-empty operator identity")
    approved_by = approved_by.strip()
    if len(approved_by) > 200 or "\n" in approved_by or "\0" in approved_by:
        raise DwError("operator identity must be a bounded single line")
    supplied = str(expect or "")
    if supplied != document.get("start_token"):
        raise DwError("stale run start token refused; no run state was written")
    request = document["request"]  # type: ignore[index]
    rebuilt = build_run_plan(
        root,
        str(request["score"]),  # type: ignore[index]
        str(request["project"]),  # type: ignore[index]
        str(request["story"]),  # type: ignore[index]
        issued_at=str(request["issued_at"]),  # type: ignore[index]
        expires_at=str(request["expires_at"]),  # type: ignore[index]
        standing_nudges=request.get("standing_nudges", []),  # type: ignore[union-attr]
        signal_channel=str(request.get("signal_channel", "")),  # type: ignore[union-attr]
    )
    if canonical_json(rebuilt) != canonical_json(document):
        raise DwError("run plan is stale or altered; no run state was written")
    if not document.get("applicable"):
        raise DwError("run plan is not applicable: " + "; ".join(document.get("issues", [])))
    current = (now or _utc_now()).astimezone(timezone.utc).replace(microsecond=0)
    if current < _parse_time(request["issued_at"], "issued_at"):  # type: ignore[index]
        raise DwError("run plan is not yet valid; no run state was written")
    if current >= _parse_time(request["expires_at"], "expires_at"):  # type: ignore[index]
        raise DwError("run plan expired before approval; no run state was written")

    token_hex = supplied.split(":", 1)[-1]
    run_id = "run-" + token_hex[:24]
    compiled = compile_score_path(find_score_path(root, str(request["score"])))  # type: ignore[index]
    approved_at = _format_time(current)
    grant: dict[str, object] = {
        "kind": RUN_GRANT_KIND,
        "schema_version": RUN_SCHEMA_VERSION,
        "run_id": run_id,
        "grant_hash": "",
        "start_token": supplied,
        "repository": document["repository"],
        "status_hash": document["status"]["hash"],  # type: ignore[index]
        "score": document["score"],
        "project": request["project"],  # type: ignore[index]
        "story": document["story"],
        "capabilities": document["authority"]["capabilities"],  # type: ignore[index]
        "profiles": document["authority"]["profiles"],  # type: ignore[index]
        "workspace_modes": document["authority"]["workspace_modes"],  # type: ignore[index]
        "budgets": document["authority"]["budgets"],  # type: ignore[index]
        "standing_nudge_rules": document["authority"]["standing_nudge_rules"],  # type: ignore[index]
        "signal_channel": document["authority"]["signal_channel"],  # type: ignore[index]
        "issued_at": request["issued_at"],  # type: ignore[index]
        "expires_at": request["expires_at"],  # type: ignore[index]
        "approved_at": approved_at,
        "approved_by": approved_by,
        "revocation_generation": 0,
        "permanent_exclusions": list(PERMANENT_EXCLUSIONS),
    }
    grant["grant_hash"] = _grant_hash(grant)
    initial = _event_document(
        run_id,
        0,
        "run_started",
        {
            "semantic_hash": str(document["score"]["semantic_hash"]),  # type: ignore[index]
            "status_hash": str(document["status"]["hash"]),  # type: ignore[index]
            "expires_at": str(request["expires_at"]),  # type: ignore[index]
        },
        None,
        current,
    )

    with _store_lock(root) as store:
        runs = store / "runs"
        runs.mkdir(mode=0o700, exist_ok=True)
        final = runs / run_id
        if final.exists():
            raise DwError("run start token was already consumed; no second run was created")
        temp = Path(tempfile.mkdtemp(prefix=f".{run_id}.", dir=str(runs)))
        try:
            _write_json(temp / "plan.json", document, 0o400)
            _write_json(temp / "score.json", compiled, 0o400)
            _write_json(temp / "grant.json", grant, 0o400)
            ledger = temp / "ledger.jsonl"
            with ledger.open("xb") as handle:
                os.chmod(ledger, 0o600)
                handle.write((canonical_json(initial) + "\n").encode("utf-8"))
                handle.flush()
                os.fsync(handle.fileno())
            os.rename(temp, final)
        except Exception:
            shutil.rmtree(temp, ignore_errors=True)
            raise
        projection = replay_run(root, run_id, now=current)
        _write_cache(final, projection)
        return projection


def _load_exact_json(path: Path, label: str) -> dict[str, object]:
    try:
        raw = path.read_text(encoding="utf-8")
        value = json.loads(raw)
    except (OSError, json.JSONDecodeError) as exc:
        raise DwError(f"cannot read {label}: {exc}") from exc
    if not isinstance(value, dict):
        raise DwError(f"{label} must be a JSON object")
    return value


def _load_run_documents(root: Path, run_id: str) -> tuple[Path, dict[str, object], dict[str, object]]:
    run_dir = _run_dir(root, run_id)
    grant = _load_exact_json(run_dir / "grant.json", "run grant")
    if set(grant) != _GRANT_KEYS:
        raise DwError("run grant has non-exact keys")
    if grant.get("kind") != RUN_GRANT_KIND or grant.get("schema_version") != RUN_SCHEMA_VERSION:
        raise DwError("unsupported run grant kind or schema version")
    if grant.get("run_id") != run_id or grant.get("grant_hash") != _grant_hash(grant):
        raise DwError("run grant integrity check failed")
    if grant.get("permanent_exclusions") != list(PERMANENT_EXCLUSIONS):
        raise DwError("run grant permanent exclusions were altered")
    compiled = _load_exact_json(run_dir / "score.json", "compiled run score")
    if compiled.get("semantic_hash") != grant.get("score", {}).get("semantic_hash"):  # type: ignore[union-attr]
        raise DwError("immutable run score semantic hash does not match the grant")
    if compiled.get("document_hash") != grant.get("score", {}).get("document_hash"):  # type: ignore[union-attr]
        raise DwError("immutable run score document hash does not match the grant")
    raw_score = dict(compiled.get("score", {}))
    raw_score["layout"] = compiled.get("layout", {})
    verified = compile_score(raw_score)
    if (
        verified["semantic_hash"] != compiled.get("semantic_hash")
        or verified["document_hash"] != compiled.get("document_hash")
    ):
        raise DwError("immutable compiled run score failed read-back compilation")
    return run_dir, grant, compiled


def _read_events(run_dir: Path, run_id: str) -> list[dict[str, object]]:
    path = run_dir / "ledger.jsonl"
    try:
        raw = path.read_bytes()
    except OSError as exc:
        raise DwError(f"cannot read run ledger: {exc}") from exc
    if not raw or not raw.endswith(b"\n"):
        raise DwError("run ledger is empty or truncated")
    events: list[dict[str, object]] = []
    previous: str | None = None
    previous_time: datetime | None = None
    for offset, line in enumerate(raw.splitlines()):
        try:
            event = json.loads(line)
        except json.JSONDecodeError as exc:
            raise DwError(f"run ledger line {offset + 1} is corrupt") from exc
        if not isinstance(event, dict) or set(event) != _EVENT_KEYS:
            raise DwError(f"run ledger line {offset + 1} has non-exact keys")
        if (
            event.get("kind") != RUN_EVENT_KIND
            or event.get("schema_version") != RUN_SCHEMA_VERSION
            or event.get("run_id") != run_id
            or event.get("seq") != offset
            or event.get("prev_hash") != previous
        ):
            raise DwError(f"run ledger line {offset + 1} breaks sequence or chain identity")
        unsigned = {key: value for key, value in event.items() if key != "event_hash"}
        if event.get("event_hash") != _sha(unsigned):
            raise DwError(f"run ledger line {offset + 1} hash check failed")
        kind = event.get("event")
        detail = event.get("detail")
        if kind not in _EVENT_DETAIL_KEYS or not isinstance(detail, dict):
            raise DwError(f"run ledger line {offset + 1} has an unsupported event")
        # Re-run the content/privacy guard over persisted bytes.
        _event_document(run_id, offset, str(kind), detail, previous, _parse_time(event.get("ts"), "event ts"))
        timestamp = _parse_time(event.get("ts"), "event ts")
        if previous_time is not None and timestamp < previous_time:
            raise DwError(f"run ledger line {offset + 1} moves time backwards")
        previous_time = timestamp
        previous = str(event["event_hash"])
        events.append(event)
    return events


def _writeback_status(run_dir: Path) -> dict[str, object] | None:
    path = run_dir / "memory" / "writeback-status.json"
    failure = {
        "status": "action-needed", "terminal_event_ref": "unknown",
        "reason": "terminal writeback status is malformed",
    }
    if path.is_symlink():
        return failure
    if not path.is_file():
        return None
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, ValueError):
        return {**failure, "reason": "terminal writeback status is unreadable"}
    if (
        not isinstance(value, dict)
        or set(value) != {
            "kind", "schema_version", "terminal_event_ref", "status",
            "writeback_id", "record_hash", "reason",
        }
        or value.get("schema_version") != 1
        or value.get("status") not in {"persisted", "action-needed"}
    ):
        return failure
    return value


def replay_run(
    root: Path,
    run_id: str,
    *,
    now: datetime | None = None,
) -> dict[str, object]:
    """Replay the authoritative ledger; projection.json is never trusted."""
    run_dir, grant, compiled = _load_run_documents(root, run_id)
    events = _read_events(run_dir, run_id)
    if not events or events[0]["event"] != "run_started":
        raise DwError("run ledger must begin with run_started")
    state = "active"
    generation = int(grant.get("revocation_generation", 0))
    active: dict[str, dict[str, object]] = {}
    completed: dict[str, dict[str, object]] = {}
    receipts: dict[str, list[dict[str, object]]] = {}
    routes: list[dict[str, object]] = []
    checkpoints: list[dict[str, object]] = []
    pending_checkpoint: dict[str, object] | None = None
    outstanding: dict[str, dict[str, object]] = {}
    request_history: list[dict[str, object]] = []
    request_refusals: list[dict[str, object]] = []
    latest_decision = ""
    fact_binding: dict[str, object] | None = None
    external_commits: list[dict[str, object]] = []
    claimed_attempts: set[tuple[str, int]] = set()
    idempotency_keys: set[str] = set()
    nudges: list[dict[str, object]] = []
    memory_recalls: list[dict[str, object]] = []
    memory_attachments: list[dict[str, object]] = []
    terminal_event_ref: str | None = None
    counters = {
        "agent_starts": 0, "check_starts": 0, "artifact_bytes": 0,
        "nudges": 0,
    }
    for offset, event in enumerate(events):
        kind = str(event["event"])
        detail = event["detail"]
        if offset == 0:
            if detail["semantic_hash"] != grant["score"]["semantic_hash"]:  # type: ignore[index]
                raise DwError("run_started semantic hash does not match the grant")
            if detail["status_hash"] != grant["status_hash"]:
                raise DwError("run_started status hash does not match the grant")
            if detail["expires_at"] != grant["expires_at"]:
                raise DwError("run_started expiry does not match the grant")
            continue
        if kind == "run_paused":
            if state not in {"active", "awaiting-approval"}:
                raise DwError("invalid run_paused transition")
            generation += 1
            if detail["generation"] != generation:
                raise DwError("run_paused generation is not monotonic")
            state = "paused"
        elif kind == "run_resumed":
            if state != "paused":
                raise DwError("invalid run_resumed transition")
            generation += 1
            if detail["generation"] != generation:
                raise DwError("run_resumed generation is not monotonic")
            state = (
                "awaiting-approval"
                if any(item["kind"] == "checkpoint" for item in outstanding.values())
                else "active"
            )
        elif kind == "run_revoked":
            if state not in {"active", "paused", "awaiting-approval"}:
                raise DwError("invalid run_revoked transition")
            generation += 1
            if detail["generation"] != generation:
                raise DwError("run_revoked generation is not monotonic")
            state = "revoked"
            terminal_event_ref = str(event["event_hash"])
        elif kind == "run_cancelled":
            if state not in {"active", "paused", "awaiting-approval"}:
                raise DwError("invalid run_cancelled transition")
            generation += 1
            if detail["generation"] != generation:
                raise DwError("run_cancelled generation is not monotonic")
            state = "cancelled"
            terminal_event_ref = str(event["event_hash"])
        elif kind == "node_claimed":
            if state != "active":
                raise DwError("node claim exists while run is not active")
            node_id = str(detail["node_id"])
            attempt = int(detail["attempt"])
            claim_id = str(detail["claim_id"])
            idem = str(detail["idempotency_key"])
            if detail["generation"] != generation:
                raise DwError("node claim uses a stale control generation")
            if (node_id, attempt) in claimed_attempts or idem in idempotency_keys or claim_id in active or claim_id in completed:
                raise DwError("duplicate node claim or idempotency key in ledger")
            claimed_attempts.add((node_id, attempt))
            idempotency_keys.add(idem)
            active[claim_id] = dict(detail)
            receipts[claim_id] = []
            if detail["node_type"] == "agent":
                counters["agent_starts"] += 1
            elif detail["node_type"] == "check":
                counters["check_starts"] += 1
        elif kind == "node_released":
            claim_id = str(detail["claim_id"])
            claim = active.pop(claim_id, None)
            if claim is None:
                raise DwError("node release has no active claim")
            if claim["node_id"] != detail["node_id"] or claim["attempt"] != detail["attempt"]:
                raise DwError("node release does not match its claim")
            completed[claim_id] = {
                **claim,
                **dict(detail),
                "release_seq": offset,
                "receipts": list(receipts.get(claim_id, [])),
            }
            counters["artifact_bytes"] += int(detail["artifact_bytes"])
        elif kind == "node_receipt":
            claim_id = str(detail["claim_id"])
            claim = active.get(claim_id)
            if claim is None:
                raise DwError("node receipt has no active claim")
            if claim["node_id"] != detail["node_id"] or claim["attempt"] != detail["attempt"]:
                raise DwError("node receipt does not match its claim")
            receipts.setdefault(claim_id, []).append({"seq": offset, **dict(detail)})
            claim["last_receipt"] = dict(detail)
        elif kind == "activity_observed":
            claim_id = str(detail["claim_id"])
            claim = active.get(claim_id)
            if claim is None:
                raise DwError("activity observation has no active claim")
            if claim["node_id"] != detail["node_id"] or claim["attempt"] != detail["attempt"]:
                raise DwError("activity observation does not match its claim")
            claim["last_activity"] = {
                "activity": detail["activity"],
                "session_id": detail["session_id"],
                "seq": offset,
                "ts": event["ts"],
            }
        elif kind == "nudge_delivered":
            if state == "awaiting-certification":
                # The only sanctioned wake from a terminal state: a granted,
                # budgeted, receipted nudge re-opens the run for one more
                # bounded round. Certification authority is untouched.
                state = "active"
                terminal_event_ref = None
            elif state != "active":
                raise DwError("nudge delivery recorded in an inactive run")
            counters["nudges"] += 1
            nudges.append({"seq": offset, "delivered": True, **dict(detail)})
            for request in request_history:
                if (
                    request["kind"] == "nudge"
                    and request["origin"] == detail["rule"]
                    and request["signal_hash"] == detail["signal_hash"]
                    and request.get("status") == "approved"
                ):
                    request["status"] = "applied"
                    request["applied_seq"] = offset
        elif kind == "nudge_refused":
            nudges.append({"seq": offset, "delivered": False, **dict(detail)})
            if detail["reason"] == "no-standing-rule":
                correlation = _request_correlation(event)
                rule = next(
                    (
                        item for item in compiled["score"].get("nudges", [])
                        if item.get("id") == detail["rule"]
                    ),
                    {},
                )
                request = {
                    "correlation_id": correlation,
                    "kind": "nudge",
                    "origin": str(detail["rule"]),
                    "origin_node": str(rule.get("target") or ""),
                    "checkpoint": "",
                    "mode": "nudge",
                    "signal": str(detail["signal"]),
                    "signal_hash": str(detail["signal_hash"]),
                    "opened_seq": offset,
                    "opened_at": event["ts"],
                    "expires_at": grant["expires_at"],
                    "parent_correlation_id": latest_decision,
                    "request_schema": {
                        "kind": "nudge-preview@1",
                        "required": ["correlation_id", "rule", "signal_hash"],
                    },
                    "response_schema": {"decision": ["approve", "reject"]},
                    "schema_summary": "decision: approve | reject",
                    "preview": {
                        "ledger_head": event["event_hash"],
                        "state": state,
                        "control_generation": generation,
                        "rule": str(detail["rule"]),
                        "signal": str(detail["signal"]),
                        "signal_hash": str(detail["signal_hash"]),
                        "target": str(rule.get("target") or ""),
                        "expires_at": grant["expires_at"],
                    },
                    "republished_generations": [],
                    "status": "pending",
                }
                outstanding[correlation] = request
                request_history.append(request)
        elif kind == "failure_routed":
            source = next(
                (
                    item for item in completed.values()
                    if item["node_id"] == detail["node_id"]
                    and item["attempt"] == detail["attempt"]
                ),
                None,
            )
            if source is None or source["outcome"] == "succeeded":
                raise DwError("failure route has no matching failed node attempt")
            if any(
                item["node_id"] == detail["node_id"]
                and item["attempt"] == detail["attempt"]
                for item in routes
            ):
                raise DwError("node failure already has a recorded route")
            routes.append({"seq": offset, "resolved": False, **dict(detail)})
        elif kind == "route_resolved":
            route = next(
                (
                    item for item in reversed(routes)
                    if item["node_id"] == detail["node_id"]
                    and item["attempt"] == detail["attempt"]
                    and item["target"] == detail["target"]
                    and item["target_attempt"] == detail["target_attempt"]
                    and item["visit"] == detail["visit"]
                ),
                None,
            )
            if route is None or route["resolved"]:
                raise DwError("route resolution has no matching open route")
            target = next(
                (
                    item for item in completed.values()
                    if item["node_id"] == detail["target"]
                    and item["attempt"] == detail["target_attempt"]
                ),
                None,
            )
            if target is None or target["outcome"] != detail["outcome"]:
                raise DwError("route resolution does not match its target outcome")
            route["resolved"] = True
            route["resolution_seq"] = offset
            route["outcome"] = detail["outcome"]
        elif kind == "checkpoint_reached":
            if state != "active" or pending_checkpoint is not None:
                raise DwError("checkpoint reached while the run cannot accept one")
            correlation = _request_correlation(event)
            checkpoint = {
                "seq": offset, "correlation_id": correlation, **dict(detail),
            }
            checkpoints.append(checkpoint)
            terminal = str(detail["terminal"])
            if terminal != "none":
                # A terminal approval node is a completed handoff, not an
                # unanswered request.  A later sanctioned nudge may wake the
                # run and reach the handoff again after its bounded repair.
                pending_checkpoint = None
                state = terminal
                terminal_event_ref = str(event["event_hash"])
            else:
                pending_checkpoint = checkpoint
                node = next(
                    (
                        item for item in compiled["score"]["nodes"]
                        if item.get("id") == detail["node_id"]
                    ),
                    {},
                )
                options = (
                    list(node.get("options", ["approve", "reject"]))
                    if node.get("type") == "approval"
                    else ["approve", "reject"]
                )
                request = {
                    "correlation_id": correlation,
                    "kind": "checkpoint",
                    "origin": str(detail["checkpoint"]),
                    "origin_node": str(detail["node_id"]),
                    "checkpoint": str(detail["checkpoint"]),
                    "mode": str(detail["mode"]),
                    "signal": "",
                    "signal_hash": "",
                    "opened_seq": offset,
                    "opened_at": event["ts"],
                    "expires_at": grant["expires_at"],
                    "parent_correlation_id": latest_decision,
                    "request_schema": {
                        "kind": "checkpoint-request@1",
                        "required": ["correlation_id", "checkpoint", "preview_hash"],
                    },
                    "response_schema": {"decision": options},
                    "schema_summary": "decision: " + " | ".join(options),
                    "preview": {
                        "ledger_head": event["event_hash"],
                        "state": "awaiting-approval",
                        "control_generation": generation,
                        "node_id": str(detail["node_id"]),
                        "checkpoint": str(detail["checkpoint"]),
                        "mode": str(detail["mode"]),
                        "reason": str(detail["reason"]),
                        "expires_at": grant["expires_at"],
                    },
                    "republished_generations": [],
                    "status": "pending",
                }
                outstanding[correlation] = request
                request_history.append(request)
                state = "awaiting-approval"
        elif kind == "checkpoint_decided":
            if state != "awaiting-approval" or pending_checkpoint is None:
                raise DwError("checkpoint decision has no pending checkpoint")
            for key in ("node_id", "checkpoint", "mode"):
                if pending_checkpoint[key] != detail[key]:
                    raise DwError("checkpoint decision does not match the pending checkpoint")
            pending_checkpoint["decision"] = detail["decision"]
            pending_checkpoint["decision_seq"] = offset
            correlation = str(pending_checkpoint.get("correlation_id") or "")
            request = outstanding.pop(correlation, None)
            if request is not None:
                request["preview"] = {
                    **request["preview"],
                    "ledger_head": event["prev_hash"],
                    "state": state,
                    "control_generation": generation,
                }
                request["decision"] = detail["decision"]
                request["decision_seq"] = offset
                request["status"] = (
                    "approved" if detail["decision"] == "approve" else "rejected"
                )
                latest_decision = correlation
            state = "active" if detail["decision"] == "approve" else "blocked"
            if state == "blocked":
                terminal_event_ref = str(event["event_hash"])
            pending_checkpoint = None
        elif kind == "request_republished":
            correlation = str(detail["correlation_id"])
            request = outstanding.get(correlation)
            if request is None:
                raise DwError("request republish has no matching outstanding request")
            if _parse_time(event["ts"], "event ts") >= _parse_time(
                request["expires_at"], "request expires_at"
            ):
                raise DwError("expired request was republished")
            if detail["generation"] != generation:
                raise DwError("request republish uses a stale control generation")
            generations = request["republished_generations"]
            if generation in generations:
                raise DwError("request was republished twice in one control generation")
            generations.append(generation)
            request.setdefault("republished", []).append({
                "seq": offset, "ts": event["ts"], "generation": generation,
            })
        elif kind == "request_decided":
            correlation = str(detail["correlation_id"])
            request = outstanding.pop(correlation, None)
            if request is None:
                raise DwError("request decision has no matching outstanding request")
            if _parse_time(event["ts"], "event ts") >= _parse_time(
                request["expires_at"], "request expires_at"
            ):
                raise DwError("expired request received a decision")
            options = request["response_schema"]["decision"]
            if detail["decision"] not in options:
                raise DwError("request decision violates its response schema")
            request["preview"] = {
                **request["preview"],
                "ledger_head": event["prev_hash"],
                "state": state,
                "control_generation": generation,
            }
            request["decision"] = detail["decision"]
            request["decision_seq"] = offset
            request["response_hash"] = detail["response_hash"]
            request["status"] = (
                "approved" if detail["decision"] == "approve" else "rejected"
            )
            latest_decision = correlation
            if request["kind"] == "checkpoint":
                if state != "awaiting-approval" or pending_checkpoint is None:
                    raise DwError("checkpoint response has no pending checkpoint")
                if pending_checkpoint.get("correlation_id") != correlation:
                    raise DwError("checkpoint response correlation does not match")
                pending_checkpoint["decision"] = detail["decision"]
                pending_checkpoint["decision_seq"] = offset
                state = "active" if detail["decision"] == "approve" else "blocked"
                pending_checkpoint = None
        elif kind == "request_refused":
            correlation = str(detail["correlation_id"])
            reason = str(detail["reason"])
            request = outstanding.get(correlation)
            request_refusals.append({
                "seq": offset,
                "ts": event["ts"],
                **dict(detail),
            })
            if reason == "expired":
                if request is None:
                    raise DwError("expired refusal has no matching outstanding request")
                outstanding.pop(correlation)
                request["status"] = "expired"
                request["refusal_seq"] = offset
                request["response_hash"] = detail["response_hash"]
                if request["kind"] == "checkpoint":
                    if (
                        pending_checkpoint is None
                        or pending_checkpoint.get("correlation_id") != correlation
                    ):
                        raise DwError("expired checkpoint request has no pending checkpoint")
                    pending_checkpoint["refusal"] = "expired"
                    pending_checkpoint["refusal_seq"] = offset
                    pending_checkpoint = None
                    if state not in {"revoked", "cancelled"}:
                        state = "blocked"
                        terminal_event_ref = str(event["event_hash"])
            elif reason == "invalid-response":
                if request is None:
                    raise DwError("invalid response refusal has no matching request")
            elif reason == "correlation-mismatch" and request is not None:
                raise DwError("correlation mismatch unexpectedly names a live request")
        elif kind == "run_aborted":
            if state not in {"active", "paused", "awaiting-approval"}:
                raise DwError("invalid run_aborted transition")
            generation += 1
            if detail["generation"] != generation:
                raise DwError("run_aborted generation is not monotonic")
            state = "blocked"
            terminal_event_ref = str(event["event_hash"])
        elif kind == "run_terminal":
            if state != "active":
                raise DwError("run terminal handoff requires an active run")
            state = str(detail["meaning"])
            terminal_event_ref = str(event["event_hash"])
        elif kind == "rail_advanced":
            if state != "active":
                raise DwError("rail fact advance requires an active run")
            if not any(item["node_id"] == detail["node_id"] for item in active.values()):
                raise DwError("rail fact advance has no active node claim")
            fact_binding = dict(detail)
        elif kind == "external_commit_observed":
            if state not in {"awaiting-certification", "complete", "blocked"}:
                raise DwError("external commit observation requires a terminal handoff")
            external_commits.append({"seq": offset, **dict(detail)})
        elif kind == "memory-recall-built":
            if state != "active":
                raise DwError("memory recall was built while the run was inactive")
            if any(
                item["audience"] == detail["audience"]
                and item["source_revision"] == detail["source_revision"]
                for item in memory_recalls
            ):
                raise DwError("memory recall audience was built more than once")
            memory_recalls.append({"seq": offset, **dict(detail)})
        elif kind == "memory-recall-attached":
            if state != "active":
                raise DwError("memory recall was attached while the run was inactive")
            claim = active.get(str(detail["claim_id"]))
            if claim is None or claim["node_id"] != detail["node_id"]:
                raise DwError("memory recall attachment has no matching active claim")
            built = next((
                item for item in memory_recalls
                if item["recall_id"] == detail["recall_id"]
                and item["audience"] == detail["audience"]
            ), None)
            if built is None:
                raise DwError("memory recall attachment has no built recall")
            if any(item["claim_id"] == detail["claim_id"] for item in memory_attachments):
                raise DwError("node claim received more than one memory recall")
            memory_attachments.append({"seq": offset, **dict(detail)})
        else:
            raise DwError(f"unsupported event transition: {kind}")

    observed = (now or _utc_now()).astimezone(timezone.utc).replace(microsecond=0)
    expired = observed >= _parse_time(grant["expires_at"], "expires_at")
    outstanding_requests = [
        {
            **item,
            "age_seconds": max(
                0,
                int((observed - _parse_time(item["opened_at"], "opened_at")).total_seconds()),
            ),
        }
        for item in sorted(
            outstanding.values(), key=lambda value: int(value["opened_seq"])
        )
    ]
    budgets = grant["budgets"]
    budget_state = {
        "max_concurrency": {
            "used": len(active), "limit": budgets["max_concurrency"],
        },
        "max_agent_starts": {
            "used": counters["agent_starts"], "limit": budgets["max_agent_starts"],
        },
        "max_check_starts": {
            "used": counters["check_starts"], "limit": budgets["max_check_starts"],
        },
        "max_artifact_bytes": {
            "used": counters["artifact_bytes"], "limit": budgets["max_artifact_bytes"],
        },
        "max_wall_seconds": {
            "used": max(0, int((observed - _parse_time(grant["approved_at"], "approved_at")).total_seconds())),
            "limit": budgets["max_wall_seconds"],
        },
        "max_nudges": {
            "used": counters["nudges"],
            "limit": int(budgets.get("max_nudges", 0)),
        },
    }
    wall_exhausted = budget_state["max_wall_seconds"]["used"] >= budget_state["max_wall_seconds"]["limit"]
    node_order = {
        str(node["id"]): index
        for index, node in enumerate(compiled["score"]["nodes"])
    }
    memory_writeback = _writeback_status(run_dir)
    return {
        "kind": RUN_KIND,
        "schema_version": RUN_SCHEMA_VERSION,
        "run_id": run_id,
        "state": state,
        "expired": expired,
        "dispatch_allowed": state == "active" and not expired and not wall_exhausted,
        "control_generation": generation,
        "grant_hash": grant["grant_hash"],
        "head_sha": grant["repository"]["head"],
        "terminal_event_ref": terminal_event_ref,
        "memory_writeback": memory_writeback,
        "score": grant["score"],
        "project": grant["project"],
        "story": grant["story"],
        "capabilities": grant["capabilities"],
        "profiles": grant["profiles"],
        "workspace_modes": grant["workspace_modes"],
        "signal_channel": str(grant.get("signal_channel") or ""),
        "budgets": budget_state,
        "nudges": nudges,
        "memory_recalls": memory_recalls,
        "memory_attachments": memory_attachments,
        "active_claims": sorted(
            active.values(),
            key=lambda item: (node_order[str(item["node_id"])], int(item["attempt"])),
        ),
        "completed_claims": sorted(
            completed.values(),
            key=lambda item: (node_order[str(item["node_id"])], int(item["attempt"])),
        ),
        "node_receipts": sorted(
            [item for values in receipts.values() for item in values],
            key=lambda item: int(item["seq"]),
        ),
        "routes": routes,
        "checkpoints": checkpoints,
        "pending_checkpoint": pending_checkpoint,
        "outstanding_requests": outstanding_requests,
        "request_history": request_history,
        "request_refusals": request_refusals,
        "fact_binding": fact_binding,
        "external_commits": external_commits,
        "ledger_events": len(events),
        "ledger_head": events[-1]["event_hash"],
        "expires_at": grant["expires_at"],
        "permanent_exclusions": grant["permanent_exclusions"],
        "starts_work": False,
    }


def _append_event_locked(
    root: Path,
    run_id: str,
    projection: dict[str, object],
    event: str,
    detail: dict[str, object],
    now: datetime,
) -> dict[str, object]:
    run_dir = _run_dir(root, run_id)
    document = _event_document(
        run_id,
        int(projection["ledger_events"]),
        event,
        detail,
        str(projection["ledger_head"]),
        now,
    )
    ledger = run_dir / "ledger.jsonl"
    data = (canonical_json(document) + "\n").encode("utf-8")
    with ledger.open("ab", buffering=0) as handle:
        written = handle.write(data)
        if written != len(data):
            raise DwError("short write while appending the run ledger")
        os.fsync(handle.fileno())
    updated = replay_run(root, run_id, now=now)
    _write_cache(run_dir, updated)
    return updated


def _validate_runtime_transition(
    projection: dict[str, object],
    compiled: dict[str, object],
    event: str,
    detail: dict[str, object],
) -> None:
    """Refuse a bad runtime event before any authoritative bytes are written."""
    _event_document(
        str(projection["run_id"]), int(projection["ledger_events"]), event,
        detail, str(projection["ledger_head"]), _utc_now(),
    )
    nodes = {
        str(node["id"]): node
        for node in compiled["score"]["nodes"]  # type: ignore[index]
    }
    state = str(projection["state"])
    active = {
        str(item["claim_id"]): item for item in projection["active_claims"]
    }
    completed = list(projection["completed_claims"])
    if event == "node_receipt":
        claim = active.get(str(detail["claim_id"]))
        if claim is None or any(
            claim[key] != detail[key] for key in ("node_id", "attempt")
        ):
            raise DwError("node receipt does not match an active claim")
        if detail["executor"] not in {"driver", "check", "rail", "collect"}:
            raise DwError("node receipt names an unsupported executor")
        if detail["state"] not in {
            "running", "succeeded", "failed", "cancelled", "lost", "refused"
        }:
            raise DwError("node receipt has an unsupported state")
        if not re.fullmatch(r"sha256:[0-9a-f]{64}", str(detail["receipt_hash"])):
            raise DwError("node receipt hash is malformed")
    elif event == "activity_observed":
        claim = active.get(str(detail["claim_id"]))
        if claim is None or any(
            claim[key] != detail[key] for key in ("node_id", "attempt")
        ):
            raise DwError("activity observation does not match an active claim")
        if detail["activity"] not in ACTIVITY_STATES:
            raise DwError("activity observation has an unsupported state")
    elif event == "nudge_delivered":
        if state not in {"active", "awaiting-certification"}:
            raise DwError(
                "nudge delivery requires an active or awaiting-certification run"
            )
        if projection["expired"]:
            raise DwError("nudge delivery refused on an expired grant")
        target = nodes.get(str(detail["node_id"]))
        if target is None or target.get("type") != "agent":
            raise DwError("nudge delivery must target a declared agent node")
        rules = {
            str(rule.get("id")): rule
            for rule in compiled["score"].get("nudges", [])  # type: ignore[union-attr]
            if isinstance(rule, dict)
        }
        rule = rules.get(str(detail["rule"]))
        if rule is None:
            raise DwError("nudge delivery names an undeclared rule")
        if not re.fullmatch(r"sha256:[0-9a-f]{64}", str(detail["signal_hash"])):
            raise DwError("nudge signal hash is malformed")
        attempt = detail["attempt"]
        if isinstance(attempt, bool) or not isinstance(attempt, int) or not 1 <= attempt <= 20:
            raise DwError("nudge attempt is outside its finite bound")
        budget = projection["budgets"]["max_nudges"]
        if int(budget["used"]) >= int(budget["limit"]):
            raise DwError("nudge budget is exhausted; no delivery may be recorded")
        delivered = [
            item for item in projection["nudges"]
            if item.get("delivered")
            and item["rule"] == detail["rule"]
        ]
        per_signal = [
            item for item in delivered
            if item["signal_hash"] == detail["signal_hash"]
        ]
        if len(per_signal) >= int(rule.get("max_per_signal", 1)):
            raise DwError(
                "nudge replay refused: this signal already received its delivery"
            )
        if len(delivered) >= int(rule.get("max_total", 1)):
            raise DwError("nudge rule ceiling reached; no delivery may be recorded")
    elif event == "nudge_refused":
        if detail["reason"] not in _NUDGE_REFUSAL_REASONS:
            raise DwError("nudge refusal has an unsupported reason")
        if any(
            not item.get("delivered")
            and item["rule"] == detail["rule"]
            and item["signal_hash"] == detail["signal_hash"]
            and item["reason"] == detail["reason"]
            for item in projection["nudges"]
        ):
            raise DwError("duplicate nudge refusal for the same signal and reason")
    elif event == "failure_routed":
        source = next(
            (
                item for item in completed
                if item["node_id"] == detail["node_id"]
                and item["attempt"] == detail["attempt"]
            ),
            None,
        )
        if source is None or source["outcome"] == "succeeded":
            raise DwError("failure route has no matching failed attempt")
        if any(
            item["node_id"] == detail["node_id"]
            and item["attempt"] == detail["attempt"]
            for item in projection["routes"]
        ):
            raise DwError("node failure already has a route receipt")
        if detail["action"] not in {
            "retry", "route", "approval", "pause", "abort", "exhausted"
        }:
            raise DwError("failure route has an unsupported action")
        for key in ("attempt", "visit", "target_attempt"):
            value = detail[key]
            if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 20:
                raise DwError(f"failure route {key} is outside its finite bound")
    elif event == "route_resolved":
        route = next(
            (
                item for item in reversed(projection["routes"])
                if item["node_id"] == detail["node_id"]
                and item["attempt"] == detail["attempt"]
                and item["target"] == detail["target"]
                and item["target_attempt"] == detail["target_attempt"]
                and item["visit"] == detail["visit"]
            ),
            None,
        )
        target = next(
            (
                item for item in completed
                if item["node_id"] == detail["target"]
                and item["attempt"] == detail["target_attempt"]
            ),
            None,
        )
        if route is None or route.get("resolved") or target is None:
            raise DwError("route resolution does not match an open completed route")
        if target["outcome"] != detail["outcome"]:
            raise DwError("route resolution outcome does not match the target")
    elif event == "checkpoint_reached":
        if state != "active" or projection["pending_checkpoint"] is not None:
            raise DwError("run cannot accept another checkpoint")
        if detail["node_id"] not in nodes:
            raise DwError("checkpoint source is absent from the immutable score")
        if detail["mode"] not in {"normal", "failure"}:
            raise DwError("checkpoint mode is unsupported")
        if detail["terminal"] not in {
            "none", "complete", "blocked", "cancelled", "awaiting-certification"
        }:
            raise DwError("checkpoint terminal meaning is unsupported")
    elif event == "checkpoint_decided":
        pending = projection["pending_checkpoint"]
        if state != "awaiting-approval" or not isinstance(pending, dict):
            raise DwError("checkpoint decision has no pending checkpoint")
        if any(pending[key] != detail[key] for key in ("node_id", "checkpoint", "mode")):
            raise DwError("checkpoint decision does not match the pending checkpoint")
        if detail["decision"] not in {"approve", "reject"}:
            raise DwError("checkpoint decision must be approve or reject")
    elif event in {"request_republished", "request_decided", "request_refused"}:
        requests = {
            str(item["correlation_id"]): item
            for item in projection["outstanding_requests"]
        }
        correlation = str(detail["correlation_id"])
        request = requests.get(correlation)
        if not re.fullmatch(r"(?:req|unmatched)-[0-9a-f]{24}", correlation):
            raise DwError("request correlation id is malformed")
        if event == "request_republished":
            if request is None:
                raise DwError("request republish has no matching outstanding request")
            if projection["expired"]:
                raise DwError("expired request cannot be republished")
            if detail["generation"] != projection["control_generation"]:
                raise DwError("request republish uses a stale control generation")
            if detail["generation"] in request["republished_generations"]:
                raise DwError("request was already republished in this generation")
        elif event == "request_decided":
            if request is None:
                raise DwError("request decision has no matching outstanding request")
            if projection["expired"]:
                raise DwError("expired request cannot receive a decision")
            if detail["decision"] not in request["response_schema"]["decision"]:
                raise DwError("request response violates the declared schema")
            if request["kind"] == "checkpoint" and state != "awaiting-approval":
                raise DwError("checkpoint response requires an awaiting-approval run")
            if not re.fullmatch(r"sha256:[0-9a-f]{64}", str(detail["response_hash"])):
                raise DwError("request response hash is malformed")
        else:
            reason = str(detail["reason"])
            if reason not in _REQUEST_REFUSAL_REASONS:
                raise DwError("request refusal has an unsupported reason")
            if not re.fullmatch(r"sha256:[0-9a-f]{64}", str(detail["response_hash"])):
                raise DwError("request response hash is malformed")
            if reason == "correlation-mismatch" and request is not None:
                raise DwError("correlation mismatch names a live request")
            if reason in {"invalid-response", "expired"} and request is None:
                raise DwError("request refusal has no matching outstanding request")
            if reason == "invalid-response" and projection["expired"]:
                raise DwError("expired request must use the expired refusal")
            if (
                reason == "expired"
                and not projection["expired"]
                and state not in _REQUEST_CLOSED_STATES
            ):
                raise DwError("request cannot expire before its grant")
    elif event == "run_aborted":
        if state not in {"active", "paused", "awaiting-approval"}:
            raise DwError("run cannot be aborted from its current state")
        if detail["generation"] != int(projection["control_generation"]) + 1:
            raise DwError("run abort uses a stale control generation")
    elif event == "run_terminal":
        if state != "active":
            raise DwError("terminal handoff requires an active run")
        if detail["meaning"] not in {
            "complete", "blocked", "cancelled", "awaiting-certification"
        }:
            raise DwError("terminal meaning is unsupported")
    elif event == "rail_advanced":
        claim = next(
            (item for item in active.values() if item["node_id"] == detail["node_id"]),
            None,
        )
        node = nodes.get(str(detail["node_id"]))
        if state != "active" or claim is None or node is None or node["type"] != "rail":
            raise DwError("rail fact advance has no matching active rail claim")
        if detail["action"] != node["action"]:
            raise DwError("rail fact advance action differs from the immutable score")
    elif event == "external_commit_observed":
        if state not in {"awaiting-certification", "complete", "blocked"}:
            raise DwError("external commit observation requires terminal handoff")
        if detail["relation"] not in {"fast-forward", "diverged", "rewritten"}:
            raise DwError("external commit relation is unsupported")
        if set(detail) == _EXTERNAL_COMMIT_BOUND_KEYS:
            for key in ("repository_id", "status_hash", "story_hash"):
                if not re.fullmatch(r"sha256:[0-9a-f]{64}", str(detail[key])):
                    raise DwError(f"external commit {key} is malformed")
            if not isinstance(detail["rebindable"], bool):
                raise DwError("external commit rebindable verdict must be boolean")
            if detail["operation"] not in {"normal", "rewrite"}:
                raise DwError("external commit operation is unsupported")
            if detail["rebindable"] and (
                detail["relation"] != "fast-forward"
                or detail["operation"] != "normal"
            ):
                raise DwError("external commit cannot rebind unsafe facts")


def record_runtime_event(
    root: Path,
    run_id: str,
    event: str,
    detail: dict[str, object],
    expect: str,
    *,
    now: datetime | None = None,
) -> dict[str, object]:
    """Append one exact conductor/checkpoint receipt under the ledger lock."""
    if event not in _RUNTIME_EVENTS:
        raise DwError(f"unsupported conductor runtime event: {event}")
    current = (now or _utc_now()).astimezone(timezone.utc).replace(microsecond=0)
    with _store_lock(root):
        projection = replay_run(root, run_id, now=current)
        if str(expect or "") != projection["ledger_head"]:
            raise DwError("stale conductor event token refused; no event was appended")
        _run_path, _grant, compiled = _load_run_documents(root, run_id)
        _validate_runtime_transition(projection, compiled, event, detail)
        return _append_event_locked(root, run_id, projection, event, detail, current)


def decide_checkpoint(
    root: Path,
    run_id: str,
    decision: str,
    expect: str,
    *,
    now: datetime | None = None,
) -> dict[str, object]:
    projection = replay_run(root, run_id, now=now)
    pending = projection.get("pending_checkpoint")
    if not isinstance(pending, dict):
        raise DwError("run has no pending checkpoint")
    correlation = str(pending.get("correlation_id") or "")
    if not correlation:
        raise DwError("pending checkpoint has no request correlation id")
    return decide_outstanding_request(
        root, run_id, correlation, decision, expect, now=now,
        expected_kind="checkpoint",
    )


def _response_hash(correlation_id: object, decision: object) -> str:
    return _sha({
        "correlation_id": str(correlation_id),
        "decision": str(decision),
    })


def _stored_correlation(
    correlation_id: object, *, force_unmatched: bool = False
) -> str:
    value = str(correlation_id or "").strip()
    if not force_unmatched and re.fullmatch(r"req-[0-9a-f]{24}", value):
        return value
    return "unmatched-" + _sha(value).partition(":")[2][:24]


def decide_outstanding_request(
    root: Path,
    run_id: str,
    correlation_id: str,
    decision: str,
    expect: str,
    *,
    now: datetime | None = None,
    expected_kind: str | None = None,
) -> dict[str, object]:
    """Validate one typed response and ledger either its act or refusal.

    Correlation and schema failures are outcomes, not invisible adapter
    errors: after a fresh exact-token preview they append a content-free
    refusal and leave the original request outstanding.
    """
    current = (now or _utc_now()).astimezone(timezone.utc).replace(microsecond=0)
    raw_correlation = str(correlation_id or "").strip()
    raw_decision = str(decision or "").strip().lower()
    response_hash = _response_hash(raw_correlation, raw_decision)
    with _store_lock(root):
        projection = replay_run(root, run_id, now=current)
        if str(expect or "") != projection["ledger_head"]:
            raise DwError("stale request response token refused; no event was appended")
        _run_path, _grant, compiled = _load_run_documents(root, run_id)
        requests = {
            str(item["correlation_id"]): item
            for item in projection["outstanding_requests"]
        }
        request = requests.get(raw_correlation)
        wrong_kind = (
            request is not None
            and expected_kind is not None
            and request.get("kind") != expected_kind
        )
        if wrong_kind:
            request = None
        stored_correlation = _stored_correlation(
            raw_correlation, force_unmatched=wrong_kind
        )
        if request is None:
            detail = {
                "correlation_id": stored_correlation,
                "reason": "correlation-mismatch",
                "response_hash": response_hash,
            }
            _validate_runtime_transition(projection, compiled, "request_refused", detail)
            return _append_event_locked(
                root, run_id, projection, "request_refused", detail, current
            )
        if projection["expired"]:
            detail = {
                "correlation_id": raw_correlation,
                "reason": "expired",
                "response_hash": response_hash,
            }
            _validate_runtime_transition(projection, compiled, "request_refused", detail)
            return _append_event_locked(
                root, run_id, projection, "request_refused", detail, current
            )
        options = request["response_schema"]["decision"]
        if (
            not raw_decision
            or len(raw_decision) > 200
            or "\n" in raw_decision
            or "\0" in raw_decision
            or raw_decision not in options
        ):
            detail = {
                "correlation_id": raw_correlation,
                "reason": "invalid-response",
                "response_hash": response_hash,
            }
            _validate_runtime_transition(projection, compiled, "request_refused", detail)
            return _append_event_locked(
                root, run_id, projection, "request_refused", detail, current
            )
        detail = {
            "correlation_id": raw_correlation,
            "decision": raw_decision,
            "response_hash": response_hash,
        }
        _validate_runtime_transition(projection, compiled, "request_decided", detail)
        updated = _append_event_locked(
            root, run_id, projection, "request_decided", detail, current
        )
        if (
            updated["state"] in _REQUEST_CLOSED_STATES
            and updated["outstanding_requests"]
        ):
            updated = _maintain_outstanding_locked(
                root, run_id, updated, current, republish=False,
                force_expire=True,
            )
        return updated


def _maintain_outstanding_locked(
    root: Path,
    run_id: str,
    projection: dict[str, object],
    current: datetime,
    *,
    republish: bool,
    force_expire: bool = False,
) -> dict[str, object]:
    """Expire or once-per-generation republish every live request."""
    _run_path, _grant, compiled = _load_run_documents(root, run_id)
    for snapshot in list(projection["outstanding_requests"]):
        correlation = str(snapshot["correlation_id"])
        request = next(
            (
                item for item in projection["outstanding_requests"]
                if item["correlation_id"] == correlation
            ),
            None,
        )
        if request is None:
            continue
        if projection["expired"] or force_expire:
            detail = {
                "correlation_id": correlation,
                "reason": "expired",
                "response_hash": _response_hash(correlation, "expired"),
            }
            _validate_runtime_transition(projection, compiled, "request_refused", detail)
            projection = _append_event_locked(
                root, run_id, projection, "request_refused", detail, current
            )
            continue
        generation = int(projection["control_generation"])
        if republish and generation not in request["republished_generations"]:
            detail = {"correlation_id": correlation, "generation": generation}
            _validate_runtime_transition(
                projection, compiled, "request_republished", detail
            )
            projection = _append_event_locked(
                root, run_id, projection, "request_republished", detail, current
            )
    return projection


def maintain_outstanding_requests(
    root: Path,
    run_id: str,
    expect: str,
    *,
    now: datetime | None = None,
    republish: bool = True,
    force_expire: bool = False,
) -> dict[str, object]:
    """One restart-safe maintenance pass over ledger-derived requests."""
    current = (now or _utc_now()).astimezone(timezone.utc).replace(microsecond=0)
    with _store_lock(root):
        projection = replay_run(root, run_id, now=current)
        if str(expect or "") != projection["ledger_head"]:
            raise DwError("stale request maintenance token refused; no event was appended")
        return _maintain_outstanding_locked(
            root, run_id, projection, current, republish=republish,
            force_expire=force_expire,
        )


def _grant_freshness_issues(
    root: Path,
    grant: dict[str, object],
    projection: dict[str, object] | None = None,
) -> list[str]:
    """Re-observe local facts before dispatch/resume; never consult source score.

    The immutable compiled score remains authoritative for an active run, so a
    later tracked score edit is deliberately irrelevant unless it also changes
    the bound repository/status facts.  This check prevents a grant from
    crossing clones, branches, HEADs, workspace states, or story transitions.
    """
    root = root.resolve()
    checkpoint = projection.get("fact_binding") if projection else None
    external = None
    if projection and projection.get("external_commits"):
        latest = projection["external_commits"][-1]
        if latest.get("rebindable") is True:
            external = latest
    binding = external or checkpoint
    expected = grant["repository"] if not binding else {
        "id": binding["repository_id"],
        "branch": binding["branch"],
        "head": binding["head"],
        "index_tree": binding["index_tree"],
        "operation": binding["operation"],
    }
    observed = {
        "id": _repository_id(root),
        "branch": current_branch(root),
        "head": head_sha(root) or "none",
        "index_tree": write_tree(root) or "unknown",
        "operation": "rewrite" if in_rewrite_state(root) else "normal",
    }
    issues = [
        f"repository {key} changed"
        for key in ("id", "branch", "head", "index_tree", "operation")
        if observed[key] != expected.get(key)  # type: ignore[union-attr]
    ]
    try:
        status_hash = _sha(_status_binding(build_status(root, str(grant["project"]))))
        expected_status = binding["status_hash"] if binding else grant["status_hash"]
        if status_hash != expected_status:
            issues.append("Delivery Workbench status binding changed")
        story = _story_facts(root, str(grant["project"]), str(grant["story"]["id"]))  # type: ignore[index]
        story_matches = (
            _sha(story) == binding["story_hash"]
            if binding else canonical_json(story) == canonical_json(grant["story"])
        )
        if not story_matches:
            issues.append("roadmap story facts changed")
    except DwError as exc:
        issues.append(f"bound project/story cannot be re-observed: {exc.message}")
    return issues


def observed_fact_binding(
    root: Path,
    grant: dict[str, object],
    node_id: str,
    action: str,
) -> dict[str, object]:
    """Return the closed post-rail fact checkpoint stored in the ledger."""
    root = root.resolve()
    story = _story_facts(root, str(grant["project"]), str(grant["story"]["id"]))  # type: ignore[index]
    return {
        "node_id": node_id,
        "action": action,
        "repository_id": _repository_id(root),
        "branch": current_branch(root),
        "head": head_sha(root) or "none",
        "index_tree": write_tree(root) or "unknown",
        "operation": "rewrite" if in_rewrite_state(root) else "normal",
        "status_hash": _sha(_status_binding(build_status(root, str(grant["project"])))),
        "story_hash": _sha(story),
    }


def observed_external_fact_binding(
    root: Path,
    grant: dict[str, object],
    relation: str,
) -> dict[str, object]:
    """Return a closed post-operator checkpoint and its rebindability verdict."""
    root = root.resolve()
    story = _story_facts(
        root, str(grant["project"]), str(grant["story"]["id"])  # type: ignore[index]
    )
    status = build_status(root, str(grant["project"]))
    repository = status["repository"]  # type: ignore[index]
    repository_id = _repository_id(root)
    branch = current_branch(root)
    operation = "rewrite" if in_rewrite_state(root) else "normal"
    story_unchanged = canonical_json(story) == canonical_json(grant["story"])
    rebindable = (
        relation == "fast-forward"
        and repository_id == grant["repository"]["id"]  # type: ignore[index]
        and branch == grant["repository"]["branch"]  # type: ignore[index]
        and operation == "normal"
        and repository.get("clean") is True  # type: ignore[union-attr]
        and story.get("status") == "in-progress"
        and story_unchanged
    )
    return {
        "repository_id": repository_id,
        "branch": branch,
        "head": head_sha(root) or "none",
        "index_tree": write_tree(root) or "unknown",
        "operation": operation,
        "status_hash": _sha(_status_binding(status)),
        "story_hash": _sha(story),
        "rebindable": rebindable,
    }


def transition_run(
    root: Path,
    run_id: str,
    action: str,
    expect: str,
    *,
    reason: str = "",
    now: datetime | None = None,
) -> dict[str, object]:
    event_by_action = {
        "pause": "run_paused", "resume": "run_resumed",
        "revoke": "run_revoked", "cancel": "run_cancelled",
    }
    if action not in event_by_action:
        raise DwError(f"unsupported run transition: {action}")
    reason = " ".join(str(reason or "").split())
    if action in {"pause", "revoke", "cancel"} and not reason:
        raise DwError(f"run {action} requires a reason")
    if action == "resume" and reason:
        raise DwError("run resume does not accept a reason")
    if len(reason) > 200:
        raise DwError("run transition reason exceeds 200 characters")
    current = (now or _utc_now()).astimezone(timezone.utc).replace(microsecond=0)
    with _store_lock(root):
        projection = replay_run(root, run_id, now=current)
        if str(expect or "") != projection["ledger_head"]:
            raise DwError("stale run transition token refused; no event was appended")
        state = projection["state"]
        valid = {
            "pause": (
                (state == "active" and projection["dispatch_allowed"])
                or (state == "awaiting-approval" and bool(projection["outstanding_requests"]))
            ),
            "resume": (
                state == "paused"
                and (
                    not projection["expired"]
                    or bool(projection["outstanding_requests"])
                )
            ),
            "revoke": state in {"active", "paused", "awaiting-approval"},
            "cancel": state in {"active", "paused", "awaiting-approval"},
        }[action]
        if not valid:
            raise DwError(f"cannot {action} a run in state {state}")
        if action == "resume":
            _run_path, grant, _compiled = _load_run_documents(root, run_id)
            freshness = _grant_freshness_issues(root, grant, projection)
            if freshness:
                raise DwError("run grant facts are stale: " + "; ".join(freshness))
        generation = int(projection["control_generation"]) + 1
        detail: dict[str, object] = {"generation": generation}
        if action != "resume":
            detail["reason"] = reason
        updated = _append_event_locked(
            root, run_id, projection, event_by_action[action], detail, current
        )
        if action == "resume":
            updated = _maintain_outstanding_locked(
                root, run_id, updated, current, republish=True
            )
        elif action in {"revoke", "cancel"} and updated["outstanding_requests"]:
            updated = _maintain_outstanding_locked(
                root, run_id, updated, current, republish=False,
                force_expire=True,
            )
        return updated


def claim_node(
    root: Path,
    run_id: str,
    node_id: str,
    attempt: int,
    idempotency_key: str,
    expect: str,
    *,
    now: datetime | None = None,
) -> dict[str, object]:
    if not _SAFE_NODE_RE.fullmatch(node_id or ""):
        raise DwError(f"unsafe node id: {node_id!r}")
    if isinstance(attempt, bool) or not isinstance(attempt, int) or not 1 <= attempt <= 20:
        raise DwError("node attempt must be an integer from 1 through 20")
    if not _SAFE_ID_RE.fullmatch(idempotency_key or ""):
        raise DwError("idempotency key must be a bounded selector")
    current = (now or _utc_now()).astimezone(timezone.utc).replace(microsecond=0)
    with _store_lock(root):
        projection = replay_run(root, run_id, now=current)
        if str(expect or "") != projection["ledger_head"]:
            raise DwError("stale node claim token refused; no event was appended")
        if not projection["dispatch_allowed"]:
            raise DwError("run grant does not currently permit dispatch")
        _run_path, grant, compiled = _load_run_documents(root, run_id)
        freshness = _grant_freshness_issues(root, grant, projection)
        if freshness:
            raise DwError("run grant facts are stale: " + "; ".join(freshness))
        node = next(
            (item for item in compiled["score"]["nodes"] if item["id"] == node_id),
            None,
        )
        if node is None:
            raise DwError(f"node is not present in the immutable run score: {node_id}")
        attempts = {
            (str(item["node_id"]), int(item["attempt"]))
            for item in projection["active_claims"] + projection["completed_claims"]
        }
        idempotency = {
            str(item.get("idempotency_key"))
            for item in projection["active_claims"]
            if item.get("idempotency_key")
        }
        # Completed projections intentionally omit idempotency keys; ledger
        # replay remains the authority for preventing reuse.
        run_dir = _run_dir(root, run_id)
        for event in _read_events(run_dir, run_id):
            if event["event"] == "node_claimed":
                idempotency.add(str(event["detail"]["idempotency_key"]))
        if (node_id, attempt) in attempts:
            raise DwError("that node attempt was already claimed")
        if idempotency_key in idempotency:
            raise DwError("that idempotency key was already consumed")
        concurrency = projection["budgets"]["max_concurrency"]
        if concurrency["used"] >= concurrency["limit"]:
            raise DwError("maximum concurrency budget is exhausted")
        node_type = str(node["type"])
        if node_type == "agent":
            budget = projection["budgets"]["max_agent_starts"]
            if budget["used"] >= budget["limit"]:
                raise DwError("maximum agent-start budget is exhausted")
        elif node_type == "check":
            budget = projection["budgets"]["max_check_starts"]
            if budget["used"] >= budget["limit"]:
                raise DwError("maximum check-start budget is exhausted")
        claim_id = _sha({
            "run_id": run_id,
            "node_id": node_id,
            "attempt": attempt,
            "idempotency_key": idempotency_key,
            "generation": projection["control_generation"],
        })
        return _append_event_locked(
            root,
            run_id,
            projection,
            "node_claimed",
            {
                "node_id": node_id,
                "node_type": node_type,
                "attempt": attempt,
                "claim_id": claim_id,
                "idempotency_key": idempotency_key,
                "generation": projection["control_generation"],
            },
            current,
        )


def release_node_claim(
    root: Path,
    run_id: str,
    claim_id: str,
    outcome: str,
    artifact_bytes: int,
    expect: str,
    *,
    now: datetime | None = None,
) -> dict[str, object]:
    if outcome not in {"succeeded", "failed", "cancelled", "lost"}:
        raise DwError("unsupported node claim outcome")
    if isinstance(artifact_bytes, bool) or not isinstance(artifact_bytes, int) or artifact_bytes < 0:
        raise DwError("artifact_bytes must be a non-negative integer")
    current = (now or _utc_now()).astimezone(timezone.utc).replace(microsecond=0)
    with _store_lock(root):
        projection = replay_run(root, run_id, now=current)
        if str(expect or "") != projection["ledger_head"]:
            raise DwError("stale node release token refused; no event was appended")
        claim = next(
            (item for item in projection["active_claims"] if item["claim_id"] == claim_id),
            None,
        )
        if claim is None:
            raise DwError("node claim is absent or already released")
        artifact_budget = projection["budgets"]["max_artifact_bytes"]
        if artifact_budget["used"] + artifact_bytes > artifact_budget["limit"]:
            raise DwError("maximum artifact-byte budget would be exceeded")
        return _append_event_locked(
            root,
            run_id,
            projection,
            "node_released",
            {
                "node_id": claim["node_id"],
                "attempt": claim["attempt"],
                "claim_id": claim_id,
                "outcome": outcome,
                "artifact_bytes": artifact_bytes,
            },
            current,
        )


def run_inventory(root: Path, *, now: datetime | None = None) -> dict[str, object]:
    store = run_store_dir(root)
    runs_dir = store / "runs"
    items: list[dict[str, object]] = []
    if runs_dir.is_dir():
        for path in sorted(runs_dir.iterdir(), key=lambda item: item.name):
            if not path.is_dir() or not _RUN_ID_RE.fullmatch(path.name):
                continue
            try:
                projection = replay_run(root, path.name, now=now)
                items.append({"run_id": path.name, "valid": True, "run": projection})
            except DwError as exc:
                items.append({"run_id": path.name, "valid": False, "error": exc.message})
    return {
        "kind": "delivery-workbench-run-inventory",
        "schema_version": RUN_SCHEMA_VERSION,
        "runs": items,
    }
