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

from .gitio import current_branch, head_sha, in_rewrite_state, run_git, write_tree
from .model import DwError, normalize_status
from .orchestration import canonical_json, compile_score, compile_score_path, find_score_path
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
_REQUEST_KEYS = {"score", "project", "story", "issued_at", "expires_at"}
_GRANT_KEYS = {
    "kind", "schema_version", "run_id", "grant_hash", "start_token",
    "repository", "status_hash", "score", "project", "story",
    "capabilities", "profiles", "workspace_modes", "budgets",
    "issued_at", "expires_at", "approved_at", "approved_by",
    "revocation_generation", "permanent_exclusions",
}
_EVENT_KEYS = {
    "kind", "schema_version", "run_id", "seq", "event", "ts", "detail",
    "prev_hash", "event_hash",
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
        "state", "reason", "receipt_hash",
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
    "run_aborted": {"node_id", "reason", "generation"},
    "run_terminal": {"node_id", "meaning"},
    "rail_advanced": {
        "node_id", "action", "repository_id", "branch", "head",
        "index_tree", "operation", "status_hash", "story_hash",
    },
    "external_commit_observed": {"previous_head", "head", "relation"},
}

_RUNTIME_EVENTS = {
    "node_receipt", "failure_routed", "route_resolved",
    "checkpoint_reached", "checkpoint_decided", "run_aborted",
    "run_terminal", "rail_advanced", "external_commit_observed",
}


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


def _file_sha(path: Path | None) -> str | None:
    if path is None or not path.is_file():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return "sha256:" + digest.hexdigest()


def _git_dir(root: Path) -> Path:
    root = root.resolve()
    direct = root / ".git"
    if direct.is_dir():
        return direct.resolve()
    raw = run_git(root, "rev-parse", "--git-dir")
    if not raw:
        raise DwError("orchestration runs require a Git repository")
    path = Path(raw.strip())
    if not path.is_absolute():
        path = root / path
    path = path.resolve()
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


def build_run_plan(
    root: Path,
    score_selector: str,
    project: str | None,
    story: str | None,
    *,
    expires_at: str | datetime | None = None,
    issued_at: str | datetime | None = None,
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

    request = {
        "score": score_selector,
        "project": project,
        "story": story_document["id"],
        "issued_at": _format_time(issued),
        "expires_at": _format_time(expiry),
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
    if allowed is None or set(detail) != allowed:
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
    fact_binding: dict[str, object] | None = None
    external_commits: list[dict[str, object]] = []
    claimed_attempts: set[tuple[str, int]] = set()
    idempotency_keys: set[str] = set()
    counters = {"agent_starts": 0, "check_starts": 0, "artifact_bytes": 0}
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
            if state != "active":
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
            state = "active"
        elif kind == "run_revoked":
            if state not in {"active", "paused", "awaiting-approval"}:
                raise DwError("invalid run_revoked transition")
            generation += 1
            if detail["generation"] != generation:
                raise DwError("run_revoked generation is not monotonic")
            state = "revoked"
        elif kind == "run_cancelled":
            if state not in {"active", "paused", "awaiting-approval"}:
                raise DwError("invalid run_cancelled transition")
            generation += 1
            if detail["generation"] != generation:
                raise DwError("run_cancelled generation is not monotonic")
            state = "cancelled"
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
            pending_checkpoint = {"seq": offset, **dict(detail)}
            checkpoints.append(pending_checkpoint)
            terminal = str(detail["terminal"])
            state = terminal if terminal != "none" else "awaiting-approval"
        elif kind == "checkpoint_decided":
            if state != "awaiting-approval" or pending_checkpoint is None:
                raise DwError("checkpoint decision has no pending checkpoint")
            for key in ("node_id", "checkpoint", "mode"):
                if pending_checkpoint[key] != detail[key]:
                    raise DwError("checkpoint decision does not match the pending checkpoint")
            pending_checkpoint["decision"] = detail["decision"]
            pending_checkpoint["decision_seq"] = offset
            state = "active" if detail["decision"] == "approve" else "blocked"
            pending_checkpoint = None
        elif kind == "run_aborted":
            if state not in {"active", "paused", "awaiting-approval"}:
                raise DwError("invalid run_aborted transition")
            generation += 1
            if detail["generation"] != generation:
                raise DwError("run_aborted generation is not monotonic")
            state = "blocked"
        elif kind == "run_terminal":
            if state != "active":
                raise DwError("run terminal handoff requires an active run")
            state = str(detail["meaning"])
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
        else:
            raise DwError(f"unsupported event transition: {kind}")

    observed = (now or _utc_now()).astimezone(timezone.utc).replace(microsecond=0)
    expired = observed >= _parse_time(grant["expires_at"], "expires_at")
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
    }
    wall_exhausted = budget_state["max_wall_seconds"]["used"] >= budget_state["max_wall_seconds"]["limit"]
    node_order = {
        str(node["id"]): index
        for index, node in enumerate(compiled["score"]["nodes"])
    }
    return {
        "kind": RUN_KIND,
        "schema_version": RUN_SCHEMA_VERSION,
        "run_id": run_id,
        "state": state,
        "expired": expired,
        "dispatch_allowed": state == "active" and not expired and not wall_exhausted,
        "control_generation": generation,
        "grant_hash": grant["grant_hash"],
        "score": grant["score"],
        "project": grant["project"],
        "story": grant["story"],
        "capabilities": grant["capabilities"],
        "profiles": grant["profiles"],
        "workspace_modes": grant["workspace_modes"],
        "budgets": budget_state,
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
    return record_runtime_event(
        root,
        run_id,
        "checkpoint_decided",
        {
            "node_id": pending["node_id"],
            "checkpoint": pending["checkpoint"],
            "mode": pending["mode"],
            "decision": decision,
        },
        expect,
        now=now,
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
    expected = grant["repository"] if not checkpoint else {
        "id": checkpoint["repository_id"],
        "branch": checkpoint["branch"],
        "head": checkpoint["head"],
        "index_tree": checkpoint["index_tree"],
        "operation": checkpoint["operation"],
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
        expected_status = checkpoint["status_hash"] if checkpoint else grant["status_hash"]
        if status_hash != expected_status:
            issues.append("Delivery Workbench status binding changed")
        story = _story_facts(root, str(grant["project"]), str(grant["story"]["id"]))  # type: ignore[index]
        story_matches = (
            _sha(story) == checkpoint["story_hash"]
            if checkpoint else canonical_json(story) == canonical_json(grant["story"])
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
            "pause": state == "active" and projection["dispatch_allowed"],
            "resume": state == "paused" and not projection["expired"],
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
        return _append_event_locked(
            root, run_id, projection, event_by_action[action], detail, current
        )


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
