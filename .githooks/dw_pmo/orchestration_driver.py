"""Provider-neutral agent packets, drivers, workspaces, and artifacts.

The score names logical profiles and requested capabilities.  Provider
executables and machine defaults live only in local driver configuration; the
packet passed across the seam is a closed, bounded data document.  Drivers
return content-free receipts, while artifact bytes stay in the local run
store and must pass deterministic conventions before fan-in.
"""

from __future__ import annotations

import fcntl
import fnmatch
import hashlib
import json
import os
import re
import shutil
import subprocess
import tempfile
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Iterator

from .gitio import head_sha
from .knowledge_packet import build_repository_knowledge_packet
from .model import DwError
from .orchestration import CAPABILITIES, WORKSPACE_MODES, canonical_json
from .orchestration_run import (
    ACTIVITY_STATES,
    RUN_SCHEMA_VERSION,
    _format_time,
    _grant_freshness_issues,
    _load_run_documents,
    _parse_time,
    _run_dir,
    _sha,
    replay_run,
    run_store_dir,
)
from .paths import rel
from .status import build_status


DRIVER_CONFIG_KIND = "delivery-workbench-driver-config"
DRIVER_CAPABILITY_KIND = "delivery-workbench-driver-capability"
WORK_PACKET_KIND = "delivery-workbench-work-packet"
DRIVER_RECEIPT_KIND = "delivery-workbench-driver-receipt"
ARTIFACT_RECEIPT_KIND = "delivery-workbench-artifact-receipt"
DRIVER_SCHEMA_VERSION = 1

MAX_CONTEXT_BYTES = 262_144
MAX_CONTEXT_FILE_BYTES = 65_536
MAX_CONTEXT_FILES = 64
MAX_STREAM_BYTES = 100_000
MAX_PACKET_BYTES = 1_500_000

_SAFE_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}$")
_SECRET_KEY_RE = re.compile(r"(?:secret|token|credential|password|api[_-]?key)", re.I)
_CONFIG_KEYS = {"kind", "schema_version", "workspace_root", "profiles"}
_PROFILE_KEYS = {
    "adapter", "capabilities", "workspace_modes", "command", "model",
    "network", "max_context_bytes", "max_stream_bytes", "timeout_ceiling",
    "principal", "available", "adapter_version", "max_concurrency",
    "router", "provider", "provider_family", "model_vendor", "model_family",
    "model_revision", "model_binding", "auth_domain",
}

# A provider family is an adapter declaration, never a guess derived from an
# executable or model name.  Fixture profiles may override their built-in
# family so deterministic exams can model more than one provider.  If a future
# adapter is added without a declaration, its capabilities expose ``None`` and
# provider-diversity policy fails closed.
ADAPTER_PROVIDER_FAMILIES = {
    "fixture": "fixture",
    "codex-exec": "openai",
    "claude-exec": "anthropic",
    "pi-exec": "pi",
}
_PACKET_KEYS = {
    "kind", "schema_version", "packet_hash", "run_id", "node_id", "attempt",
    "claim_id", "idempotency_key", "role", "profile", "prompt",
    "capabilities", "workspace", "resource_groups", "context", "inputs",
    "outputs", "timeout_seconds", "deadline", "max_stream_bytes",
    "permanent_exclusions", "knowledge",
}
_RECEIPT_KEYS = {
    "kind", "schema_version", "run_id", "node_id", "attempt", "claim_id",
    "profile", "adapter", "session_id", "idempotency_key", "packet_hash",
    "state", "started", "exit_code", "reason", "started_at", "updated_at",
    "stdout_bytes", "stderr_bytes", "activity", "usage",
}
_ARTIFACT_KEYS = {
    "kind", "schema_version", "run_id", "node_id", "attempt", "name",
    "format", "bytes", "sha256", "path", "valid", "checks",
}
_ADAPTER_RESULT_KEYS = {
    "state", "exit_code", "reason", "polls_remaining", "final_state",
    "stdout_bytes", "stderr_bytes", "activity_plan", "usage",
}
_USAGE_KEYS = {
    "status", "input_tokens", "output_tokens", "total_tokens",
    "cost_microunits",
}
_MAX_ACTIVITY_PLAN = 64
_DRIVER_STATES = {"running", "succeeded", "failed", "cancelled", "lost", "refused"}
_DRIVER_REASONS = {
    "running", "completed", "failed", "cancelled", "lost", "timeout",
    "oversized-stream", "nonzero-exit", "malformed-output", "workspace-refused",
    "adapter-unavailable", "unsupported-output-shape", "profile-unconfigured",
    "unsupported-capability", "unsupported-workspace", "interrupt-unconfirmed",
    "interrupted", "packet-expired", "grant-stale", "dispatch-refused",
}


def _exact_keys(value: object, expected: set[str], label: str) -> dict[str, object]:
    if not isinstance(value, dict):
        raise DwError(f"{label} must be a JSON object")
    unknown = sorted(set(value) - expected)
    missing = sorted(expected - set(value))
    if unknown or missing:
        raise DwError(
            f"{label} has non-exact keys"
            + (f"; unknown: {', '.join(unknown)}" if unknown else "")
            + (f"; missing: {', '.join(missing)}" if missing else "")
        )
    return value


def normalize_driver_usage(value: object = None) -> dict[str, object]:
    """Keep an absent backend measurement unknown; explicit zero stays zero."""
    if value is None:
        return {
            "status": "unknown", "input_tokens": None,
            "output_tokens": None, "total_tokens": None,
            "cost_microunits": None,
        }
    raw = _exact_keys(value, _USAGE_KEYS, "driver usage")
    fields = ("input_tokens", "output_tokens", "total_tokens", "cost_microunits")
    for field in fields:
        item = raw[field]
        if item is not None and (
            isinstance(item, bool) or not isinstance(item, int) or item < 0
        ):
            raise DwError("driver usage %s must be a nonnegative integer or null" % field)
    measured = [raw[field] is not None for field in fields]
    expected_status = "reported" if all(measured) else "partial" if any(measured) else "unknown"
    if raw["status"] != expected_status:
        raise DwError("driver usage status does not match its measurements")
    if raw["total_tokens"] is not None and raw["input_tokens"] is not None and raw["output_tokens"] is not None:
        if raw["total_tokens"] != raw["input_tokens"] + raw["output_tokens"]:
            raise DwError("driver usage total_tokens does not equal input plus output")
    return dict(raw)


def _validate_driver_receipt(value: object) -> dict[str, object]:
    """Accept replay of pre-usage receipts while validating new receipts closed."""
    if not isinstance(value, dict):
        raise DwError("driver receipt must be a JSON object")
    keys = set(value)
    legacy = _RECEIPT_KEYS - {"usage"}
    if keys == legacy:
        return value
    receipt = _exact_keys(value, _RECEIPT_KEYS, "driver receipt")
    normalize_driver_usage(receipt["usage"])
    return receipt


def _contains_secret_key(value: object) -> bool:
    if isinstance(value, dict):
        return any(_SECRET_KEY_RE.search(str(key)) or _contains_secret_key(item)
                   for key, item in value.items())
    if isinstance(value, list):
        return any(_contains_secret_key(item) for item in value)
    return False


def _positive_int(value: object, label: str, maximum: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or not 1 <= value <= maximum:
        raise DwError(f"{label} must be an integer from 1 through {maximum}")
    return value


def driver_config_path(root: Path) -> Path:
    return run_store_dir(root) / "drivers.json"


def validate_driver_config(value: object) -> dict[str, object]:
    config = _exact_keys(value, _CONFIG_KEYS, "driver config")
    if config["kind"] != DRIVER_CONFIG_KIND or config["schema_version"] != DRIVER_SCHEMA_VERSION:
        raise DwError("unsupported driver config kind or schema version")
    if _contains_secret_key(config):
        raise DwError("driver config may not contain credential, token, password, or secret fields")
    workspace_root = config["workspace_root"]
    if workspace_root is not None and (
        not isinstance(workspace_root, str) or not Path(workspace_root).is_absolute()
    ):
        raise DwError("driver workspace_root must be null or an absolute local path")
    profiles = config["profiles"]
    if not isinstance(profiles, dict):
        raise DwError("driver config profiles must be an object")
    normalized: dict[str, object] = {}
    for name, raw in sorted(profiles.items()):
        if not _SAFE_ID_RE.fullmatch(str(name)):
            raise DwError(f"unsafe logical driver profile: {name!r}")
        if not isinstance(raw, dict):
            raise DwError(f"driver profile {name!r} must be an object")
        unknown = sorted(set(raw) - _PROFILE_KEYS)
        if unknown:
            raise DwError(f"driver profile {name!r} has unknown keys: {', '.join(unknown)}")
        adapter = raw.get("adapter")
        if adapter not in {"fixture", "codex-exec", "claude-exec", "pi-exec"}:
            raise DwError(f"driver profile {name!r} has unsupported adapter {adapter!r}")
        provider_family = raw.get(
            "provider_family", ADAPTER_PROVIDER_FAMILIES.get(str(adapter))
        )
        if provider_family is not None and (
            not isinstance(provider_family, str)
            or not _SAFE_ID_RE.fullmatch(provider_family)
        ):
            raise DwError(
                f"driver profile {name!r} provider_family must be a safe local identity"
            )
        if adapter != "fixture" and "provider_family" in raw and (
            provider_family != ADAPTER_PROVIDER_FAMILIES.get(str(adapter))
        ):
            raise DwError(
                f"driver profile {name!r} cannot override the shipped adapter provider_family"
            )
        capabilities = raw.get("capabilities", [])
        if (
            not isinstance(capabilities, list)
            or any(item not in CAPABILITIES for item in capabilities)
            or len(set(capabilities)) != len(capabilities)
        ):
            raise DwError(f"driver profile {name!r} has invalid capabilities")
        modes = raw.get("workspace_modes", [])
        if (
            not isinstance(modes, list)
            or any(item not in WORKSPACE_MODES for item in modes)
            or len(set(modes)) != len(modes)
        ):
            raise DwError(f"driver profile {name!r} has invalid workspace_modes")
        default_command = {
            "codex-exec": ["codex"],
            "claude-exec": ["claude"],
            "pi-exec": ["pi"],
        }.get(str(adapter), ["fixture"])
        command = raw.get("command", default_command)
        if (
            not isinstance(command, list) or len(command) != 1
            or not isinstance(command[0], str) or not command[0]
            or "\0" in command[0]
        ):
            raise DwError(f"driver profile {name!r} command must contain one executable")
        model = raw.get("model")
        if model is not None and (not isinstance(model, str) or not model or len(model) > 200):
            raise DwError(f"driver profile {name!r} model must be a bounded string")
        principal = raw.get("principal", name)
        if not isinstance(principal, str) or not _SAFE_ID_RE.fullmatch(principal):
            raise DwError(f"driver profile {name!r} principal must be a safe local identity")
        provider_default = {
            "fixture": "fixture",
            "codex-exec": "openai",
            "claude-exec": "anthropic",
            "pi-exec": "unresolved",
        }[str(adapter)]
        execution_ids: dict[str, str] = {}
        for field, default in (
            ("router", "direct"),
            ("provider", provider_default),
            ("model_vendor", "unresolved"),
            ("model_family", "unresolved"),
            ("auth_domain", str(principal)),
        ):
            candidate = raw.get(field, default)
            if not isinstance(candidate, str) or not _SAFE_ID_RE.fullmatch(candidate):
                raise DwError(
                    f"driver profile {name!r} {field} must be a safe local identity"
                )
            execution_ids[field] = candidate
        model_revision = raw.get("model_revision")
        if model_revision is not None and (
            not isinstance(model_revision, str)
            or not model_revision
            or len(model_revision.encode("utf-8")) > 200
        ):
            raise DwError(
                f"driver profile {name!r} model_revision must be bounded"
            )
        model_binding = raw.get(
            "model_binding",
            (
                "exact-revision" if model_revision is not None
                else "requested-alias" if model is not None
                else "adapter-default-unresolved"
            ),
        )
        if model_binding not in {
            "exact-revision", "requested-alias", "adapter-default-unresolved",
        }:
            raise DwError(
                f"driver profile {name!r} model_binding is unsupported"
            )
        if model_binding == "exact-revision" and (
            model is None or model_revision is None
        ):
            raise DwError(
                f"driver profile {name!r} exact-revision binding requires model and model_revision"
            )
        if model_binding == "requested-alias" and model is None:
            raise DwError(
                f"driver profile {name!r} requested-alias binding requires model"
            )
        if model_binding == "adapter-default-unresolved" and (
            model is not None or model_revision is not None
        ):
            raise DwError(
                f"driver profile {name!r} adapter-default-unresolved binding cannot name a model or revision"
            )
        available = raw.get("available", True)
        if not isinstance(available, bool):
            raise DwError(f"driver profile {name!r} available must be boolean")
        adapter_version = raw.get("adapter_version", "builtin-v1")
        if (
            not isinstance(adapter_version, str)
            or not adapter_version
            or len(adapter_version.encode("utf-8")) > 200
        ):
            raise DwError(f"driver profile {name!r} adapter_version must be bounded")
        if adapter == "pi-exec" and not re.fullmatch(
            r"pi-cli@[0-9]+\.[0-9]+\.[0-9]+(?:[-+][A-Za-z0-9.-]+)?",
            str(adapter_version),
        ):
            raise DwError(
                f"driver profile {name!r} pi-exec adapter_version must pin "
                "pi-cli@<semver> exactly"
            )
        max_concurrency = _positive_int(
            raw.get("max_concurrency", 1),
            f"driver profile {name!r} max_concurrency", 128,
        )
        network = raw.get("network", False)
        if not isinstance(network, bool):
            raise DwError(f"driver profile {name!r} network must be boolean")
        if ("network" in capabilities) != network:
            raise DwError(
                f"driver profile {name!r} network capability and network control must agree"
            )
        if "repository-write" in capabilities and "isolated-worktree" not in modes:
            raise DwError(
                f"driver profile {name!r} repository-write requires isolated-worktree"
            )
        if "isolated-worktree" in modes and "repository-write" not in capabilities:
            raise DwError(
                f"driver profile {name!r} isolated-worktree requires repository-write"
            )
        max_context = _positive_int(
            raw.get("max_context_bytes", MAX_CONTEXT_BYTES),
            f"driver profile {name!r} max_context_bytes", MAX_PACKET_BYTES,
        )
        max_stream = _positive_int(
            raw.get("max_stream_bytes", MAX_STREAM_BYTES),
            f"driver profile {name!r} max_stream_bytes", 10_000_000,
        )
        timeout = _positive_int(
            raw.get("timeout_ceiling", 7200),
            f"driver profile {name!r} timeout_ceiling", 86_400,
        )
        normalized_profile: dict[str, object] = {
            "adapter": adapter,
            "capabilities": sorted(capabilities),
            "workspace_modes": sorted(modes),
            "command": command,
            "network": network,
            "max_context_bytes": max_context,
            "max_stream_bytes": max_stream,
            "timeout_ceiling": timeout,
            "principal": principal,
            "available": available,
            "adapter_version": adapter_version,
            "provider_family": provider_family,
            "max_concurrency": max_concurrency,
            **execution_ids,
            "model_binding": model_binding,
        }
        if model is not None:
            normalized_profile["model"] = model
        if model_revision is not None:
            normalized_profile["model_revision"] = model_revision
        normalized[str(name)] = normalized_profile
    return {
        "kind": DRIVER_CONFIG_KIND,
        "schema_version": DRIVER_SCHEMA_VERSION,
        "workspace_root": workspace_root,
        "profiles": normalized,
    }


def load_driver_config(root: Path, value: object | None = None) -> dict[str, object]:
    if value is not None:
        return validate_driver_config(value)
    path = driver_config_path(root)
    try:
        return validate_driver_config(json.loads(path.read_text(encoding="utf-8")))
    except FileNotFoundError as exc:
        raise DwError(
            f"local driver config is absent: {path}; configure logical profiles before dispatch"
        ) from exc
    except json.JSONDecodeError as exc:
        raise DwError(f"cannot parse local driver config: {exc}") from exc


def write_driver_config(root: Path, value: object) -> Path:
    config = validate_driver_config(value)
    path = driver_config_path(root)
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    fd, temporary = tempfile.mkstemp(prefix=".drivers.", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(config, handle, indent=2, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(temporary, 0o600)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
    return path


def driver_capability(config: dict[str, object], profile: str) -> dict[str, object]:
    profiles = config["profiles"]
    raw = profiles.get(profile)  # type: ignore[union-attr]
    if raw is None:
        raise DwError(f"logical driver profile is not configured: {profile}")
    public = {
        "kind": DRIVER_CAPABILITY_KIND,
        "schema_version": DRIVER_SCHEMA_VERSION,
        "profile": profile,
        "adapter": raw["adapter"],
        "adapter_version": raw["adapter_version"],
        # A configured model is an authority- and quality-relevant execution
        # input.  Exposing the requested value here makes it part of the
        # capability/roster fingerprint; omitting it would let a profile move
        # to a different model while retaining an old assignment or grant.
        # The adapter can only prove that it requested this identifier, so the
        # public contract deliberately calls it an alias rather than claiming
        # a provider-side immutable revision.
        "harness": raw["adapter"],
        "router": raw["router"],
        "provider": raw["provider"],
        "provider_family": raw["provider_family"],
        "model_vendor": raw["model_vendor"],
        "model_family": raw["model_family"],
        "model": raw.get("model"),
        "model_revision": raw.get("model_revision"),
        "model_binding": raw["model_binding"],
        "principal": raw["principal"],
        "available": raw["available"],
        "max_concurrency": raw["max_concurrency"],
        "capabilities": raw["capabilities"],
        "workspace_modes": raw["workspace_modes"],
        "sandbox_owner": {
            "fixture": "fixture",
            "codex-exec": "codex-cli",
            "claude-exec": "claude-cli",
            "pi-exec": "pi-cli",
        }[str(raw["adapter"])],
        "network": "operator-enabled" if raw["network"] else "disabled",
        "supports_interrupt": raw["adapter"] == "fixture",
        "max_context_bytes": raw["max_context_bytes"],
        "max_stream_bytes": raw["max_stream_bytes"],
        "timeout_ceiling": raw["timeout_ceiling"],
        "stores_credentials": False,
    }
    public["auth_domain_fingerprint"] = "sha256:" + hashlib.sha256(
        canonical_json({
            "auth_domain": raw["auth_domain"],
            "harness": public["harness"],
            "router": public["router"],
            "provider": public["provider"],
        }).encode("utf-8")
    ).hexdigest()
    public["principal_fingerprint"] = "sha256:" + hashlib.sha256(
        canonical_json({
            "principal": public["principal"],
            "adapter": public["adapter"],
        }).encode("utf-8")
    ).hexdigest()
    public["capability_fingerprint"] = "sha256:" + hashlib.sha256(
        canonical_json({
            key: value for key, value in public.items()
            if key not in {"available", "principal_fingerprint"}
        }).encode("utf-8")
    ).hexdigest()
    return public


def driver_inventory(config: dict[str, object]) -> dict[str, object]:
    return {
        "kind": "delivery-workbench-driver-inventory",
        "schema_version": DRIVER_SCHEMA_VERSION,
        "profiles": [driver_capability(config, name) for name in sorted(config["profiles"])],
    }


def _workspace_base(root: Path, config: dict[str, object]) -> Path:
    configured = config.get("workspace_root")
    if configured:
        base = Path(str(configured))
    else:
        tag = hashlib.sha256(str(root.resolve()).encode("utf-8")).hexdigest()[:16]
        base = root.resolve().parent / ".delivery-workbench-workspaces" / tag
    if base.is_symlink():
        raise DwError("refusing symlinked driver workspace root")
    base.mkdir(parents=True, exist_ok=True, mode=0o700)
    os.chmod(base, 0o700)
    return base.resolve()


def _safe_child(base: Path, *parts: str) -> Path:
    for part in parts:
        if not _SAFE_ID_RE.fullmatch(part):
            raise DwError(f"unsafe workspace selector: {part!r}")
    path = base.joinpath(*parts)
    parent = path.parent.resolve()
    if parent != base and base not in parent.parents:
        raise DwError("driver workspace path escapes its local root")
    if path.is_symlink():
        raise DwError("refusing symlinked driver workspace")
    return path


def prepare_workspace(
    root: Path,
    run_id: str,
    node: dict[str, object],
    attempt: int,
    config: dict[str, object],
) -> dict[str, object]:
    mode = str(node.get("workspace") or "none")
    _run_path, grant, _compiled = _load_run_documents(root, run_id)
    groups = list(node.get("resource_groups", []))
    if mode == "none":
        return {
            "mode": "none", "path": None, "identity": "none",
            "base_head": grant["repository"]["head"], "resource_groups": groups,
            "integration": "not-applicable",
        }
    if mode == "read-only":
        return {
            "mode": "read-only", "path": str(root.resolve()),
            "identity": _sha({"root": str(root.resolve()), "head": grant["repository"]["head"]}),
            "base_head": grant["repository"]["head"], "resource_groups": groups,
            "integration": "not-applicable",
        }
    if mode != "isolated-worktree":
        raise DwError(f"unsupported workspace mode: {mode}")
    base = _workspace_base(root, config)
    name = f"{node['id']}-{attempt}"
    path = _safe_child(base, run_id, name)
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    if path.exists():
        if not (path / ".git").is_file():
            raise DwError(f"workspace path already exists and is not a Git worktree: {path}")
        observed = subprocess.run(
            ["git", "-C", str(path), "rev-parse", "HEAD"], text=True,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        )
        if observed.returncode or observed.stdout.strip() != grant["repository"]["head"]:
            raise DwError("existing isolated worktree does not match the granted HEAD")
    else:
        result = subprocess.run(
            ["git", "-C", str(root), "worktree", "add", "--detach", str(path),
             str(grant["repository"]["head"])],
            text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        )
        if result.returncode:
            raise DwError("cannot create isolated Git worktree: " + result.stderr.strip()[:500])
    identity = _sha({"run": run_id, "node": node["id"], "attempt": attempt, "path": str(path)})
    receipt = {
        "mode": "isolated-worktree", "path": str(path), "identity": identity,
        "base_head": grant["repository"]["head"], "resource_groups": groups,
        "integration": "review-required",
    }
    metadata_dir = _run_dir(root, run_id) / "workspaces" / str(node["id"])
    metadata_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
    metadata = metadata_dir / f"{attempt}.json"
    if not metadata.exists():
        metadata.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        os.chmod(metadata, 0o600)
    return receipt


def remove_workspace(root: Path, workspace: dict[str, object]) -> None:
    if workspace.get("mode") != "isolated-worktree":
        return
    path = Path(str(workspace["path"]))
    result = subprocess.run(
        ["git", "-C", str(root), "worktree", "remove", "--force", str(path)],
        text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )
    if result.returncode and path.exists():
        raise DwError("cannot remove isolated worktree: " + result.stderr.strip()[:500])


@contextmanager
def acquire_resource_groups(
    root: Path, run_id: str, groups: list[str]
) -> Iterator[None]:
    locks = _run_dir(root, run_id) / "resource-locks"
    locks.mkdir(parents=True, exist_ok=True, mode=0o700)
    handles = []
    try:
        for group in sorted(set(groups)):
            if not _SAFE_ID_RE.fullmatch(group):
                raise DwError(f"unsafe resource group: {group!r}")
            handle = (locks / f"{group}.lock").open("a+")
            try:
                fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError as exc:
                handle.close()
                raise DwError(f"resource group is already claimed: {group}") from exc
            handles.append(handle)
        yield
    finally:
        for handle in reversed(handles):
            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
            handle.close()


def _bounded_file(path: Path, selector: str, remaining: int) -> tuple[dict[str, object], int]:
    data = path.read_bytes()
    included = min(len(data), MAX_CONTEXT_FILE_BYTES, remaining)
    content = data[:included].decode("utf-8", "replace")
    return ({
        "selector": selector,
        "path": str(path),
        "bytes": len(data),
        "included_bytes": included,
        "sha256": "sha256:" + hashlib.sha256(data).hexdigest(),
        "truncated": included < len(data),
        "content": content,
    }, included)


def _context_documents(
    root: Path,
    grant: dict[str, object],
    selectors: list[str],
    max_bytes: int,
) -> tuple[list[dict[str, object]], bool]:
    root = root.resolve()
    documents: list[dict[str, object]] = []
    seen: set[Path] = set()
    used = 0
    truncated = False
    for selector in selectors:
        if selector == "status":
            data = canonical_json(build_status(root, str(grant["project"]))).encode("utf-8")
            included = min(len(data), max_bytes - used)
            documents.append({
                "selector": selector, "path": "@status", "bytes": len(data),
                "included_bytes": included,
                "sha256": "sha256:" + hashlib.sha256(data).hexdigest(),
                "truncated": included < len(data),
                "content": data[:included].decode("utf-8", "replace"),
            })
            used += included
            truncated = truncated or included < len(data)
            continue
        if selector == "story":
            candidates = [root / str(grant["story"]["story_path"])]
        elif selector == "architecture":
            candidates = [root / "docs" / "architecture.md"]
        else:
            candidates = sorted(root.glob(selector), key=lambda path: str(path))
        for candidate in candidates:
            if len(documents) >= MAX_CONTEXT_FILES or used >= max_bytes:
                truncated = True
                break
            if not candidate.is_file():
                continue
            resolved = candidate.resolve()
            if resolved != root and root not in resolved.parents:
                raise DwError(f"context selector escapes the repository: {selector}")
            if resolved in seen or ".git" in resolved.relative_to(root).parts:
                continue
            seen.add(resolved)
            entry, included = _bounded_file(resolved, selector, max_bytes - used)
            entry["path"] = rel(resolved, root)
            documents.append(entry)
            used += included
            truncated = truncated or bool(entry["truncated"])
        if len(documents) >= MAX_CONTEXT_FILES or used >= max_bytes:
            truncated = True
    return documents, truncated


def _artifact_inputs(
    root: Path,
    run_id: str,
    node: dict[str, object],
    max_bytes: int,
) -> list[dict[str, object]]:
    artifacts_root = _run_dir(root, run_id) / "artifacts"
    result = []
    used = 0
    for item in node.get("inputs", []):
        if not isinstance(item, dict):
            continue
        name = str(item["artifact"])
        matches = sorted(artifacts_root.glob(f"*/{name}/metadata.json")) if artifacts_root.is_dir() else []
        if len(matches) != 1:
            raise DwError(f"validated artifact input {name!r} is absent or ambiguous")
        receipt = _exact_keys(json.loads(matches[0].read_text()), _ARTIFACT_KEYS, "artifact receipt")
        if not receipt["valid"] or receipt["format"] != item["format"]:
            raise DwError(f"artifact input {name!r} failed its declared type contract")
        content_path = matches[0].parent / "content"
        data = content_path.read_bytes()
        digest = "sha256:" + hashlib.sha256(data).hexdigest()
        if digest != receipt["sha256"] or len(data) != receipt["bytes"]:
            raise DwError(f"artifact input {name!r} bytes do not match its receipt")
        if used + len(data) > max_bytes:
            raise DwError("validated artifact inputs exceed the work-packet byte cap")
        used += len(data)
        result.append({
            "artifact": name, "format": receipt["format"], "producer": receipt["node_id"],
            "bytes": len(data), "sha256": digest,
            "content": data.decode("utf-8", "replace"),
        })
    return result


def build_work_packet(
    root: Path,
    run_id: str,
    claim_id: str,
    config: dict[str, object],
    *,
    now: datetime | None = None,
) -> dict[str, object]:
    projection = replay_run(root, run_id, now=now)
    if not projection["dispatch_allowed"]:
        raise DwError("run grant does not currently permit a new work packet")
    claim = next(
        (item for item in projection["active_claims"] if item["claim_id"] == claim_id),
        None,
    )
    if claim is None:
        raise DwError("work packet requires one active node claim")
    _run_path, grant, compiled = _load_run_documents(root, run_id)
    node = next(item for item in compiled["score"]["nodes"] if item["id"] == claim["node_id"])
    if node["type"] != "agent":
        raise DwError("work packets are only valid for agent nodes")
    profile = str(node["profile"])
    capability = driver_capability(config, profile)
    unsupported = sorted(set(node["capabilities"]) - set(capability["capabilities"]))
    if unsupported:
        raise DwError("driver profile lacks requested capabilities: " + ", ".join(unsupported))
    if node["workspace"] not in capability["workspace_modes"]:
        raise DwError(f"driver profile does not support workspace mode {node['workspace']}")
    timeout = int(node["timeout_seconds"])
    if timeout > capability["timeout_ceiling"]:
        raise DwError("node timeout exceeds the configured driver ceiling")
    workspace = prepare_workspace(root, run_id, node, int(claim["attempt"]), config)
    selectors = list(node.get("context", [])) + [
        item for item in node.get("inputs", []) if isinstance(item, str)
    ]
    contexts, context_truncated = _context_documents(
        root, grant, selectors, int(capability["max_context_bytes"])
    )
    inputs = _artifact_inputs(
        root, run_id, node,
        min(MAX_PACKET_BYTES, int(grant["budgets"]["max_artifact_bytes"])),
    )
    nudge = next(
        (
            item for item in reversed(list(projection.get("nudges", [])))
            if item.get("delivered")
            and str(item["node_id"]) == str(claim["node_id"])
            and int(item["attempt"]) == int(claim["attempt"])
        ),
        None,
    )
    if nudge is not None:
        rules = {
            str(rule.get("id")): rule
            for rule in compiled["score"].get("nudges", [])
            if isinstance(rule, dict)
        }
        rule = rules.get(str(nudge["rule"]), {})
        data = canonical_json({
            "kind": "delivery-workbench-nudge-context",
            "rule": nudge["rule"],
            "signal": nudge["signal"],
            "signal_hash": nudge["signal_hash"],
            "signal_channel": str(grant.get("signal_channel") or ""),
            "expectation": str(rule.get("expectation") or ""),
        }).encode("utf-8")
        contexts.append({
            "selector": "@nudge", "path": "@nudge", "bytes": len(data),
            "included_bytes": len(data),
            "sha256": "sha256:" + hashlib.sha256(data).hexdigest(),
            "truncated": False,
            "content": data.decode("utf-8"),
        })
    created = (now or datetime.now(timezone.utc)).astimezone(timezone.utc).replace(microsecond=0)
    deadline = min(
        created + timedelta(seconds=timeout),
        _parse_time(grant["expires_at"], "expires_at"),
    )
    story = grant.get("story")
    if not isinstance(story, dict) or not story.get("story_path"):
        raise DwError("work packet has no bound story path for knowledge assembly")
    knowledge = build_repository_knowledge_packet(
        root, root / str(story["story_path"])
    )
    unsigned: dict[str, object] = {
        "kind": WORK_PACKET_KIND,
        "schema_version": DRIVER_SCHEMA_VERSION,
        "run_id": run_id,
        "node_id": node["id"],
        "attempt": claim["attempt"],
        "claim_id": claim_id,
        "idempotency_key": claim["idempotency_key"],
        "role": node["role"],
        "profile": profile,
        "prompt": node.get("prompt", ""),
        "capabilities": node["capabilities"],
        "workspace": workspace,
        "resource_groups": node["resource_groups"],
        "context": {"documents": contexts, "truncated": context_truncated},
        "inputs": inputs,
        "outputs": node["outputs"],
        "timeout_seconds": timeout,
        "deadline": _format_time(deadline),
        "max_stream_bytes": capability["max_stream_bytes"],
        "permanent_exclusions": projection["permanent_exclusions"],
        "knowledge": knowledge,
    }
    if len(canonical_json(unsigned).encode("utf-8")) > MAX_PACKET_BYTES:
        raise DwError("work packet exceeds the absolute byte ceiling")
    return {**unsigned, "packet_hash": _sha(unsigned)}


def validate_work_packet(packet: object) -> dict[str, object]:
    if not isinstance(packet, dict):
        raise DwError("work packet must be a JSON object")
    keys = set(packet)
    legacy_keys = _PACKET_KEYS - {"knowledge"}
    if keys != _PACKET_KEYS and keys != legacy_keys:
        expected = _PACKET_KEYS if "knowledge" in keys else legacy_keys
        value = _exact_keys(packet, expected, "work packet")
    else:
        value = packet
    if value["kind"] != WORK_PACKET_KIND or value["schema_version"] != DRIVER_SCHEMA_VERSION:
        raise DwError("unsupported work packet kind or schema version")
    unsigned = {key: item for key, item in value.items() if key != "packet_hash"}
    if value["packet_hash"] != _sha(unsigned):
        raise DwError("work packet hash check failed")
    if len(canonical_json(value).encode("utf-8")) > MAX_PACKET_BYTES:
        raise DwError("work packet exceeds the absolute byte ceiling")
    return value


def _terminal_activity(state: str) -> str:
    """An honest terminal mapping: a lost session's agent may still be
    alive somewhere (`unknown`); every other terminal means the session
    is over (`exited`)."""
    return "unknown" if state == "lost" else "exited"


def _receipt(
    packet: dict[str, object], adapter: str, session_id: str | None,
    idempotency_key: str, state: str, started: bool, exit_code: int | None,
    reason: str, started_at: str | None, updated_at: str,
    stdout_bytes: int = 0, stderr_bytes: int = 0,
    activity: str | None = None, usage: object = None,
) -> dict[str, object]:
    if state not in _DRIVER_STATES or reason not in _DRIVER_REASONS:
        raise DwError("driver receipt has an unsupported state or reason")
    if state == "running":
        activity = activity or "active"
        if activity not in ACTIVITY_STATES or activity == "exited":
            raise DwError("driver receipt has an unsupported activity state")
    else:
        activity = _terminal_activity(state)
    return {
        "activity": activity,
        "kind": DRIVER_RECEIPT_KIND,
        "schema_version": DRIVER_SCHEMA_VERSION,
        "run_id": packet["run_id"], "node_id": packet["node_id"],
        "attempt": packet["attempt"], "claim_id": packet["claim_id"],
        "profile": packet["profile"], "adapter": adapter,
        "session_id": session_id, "idempotency_key": idempotency_key,
        "packet_hash": packet["packet_hash"], "state": state,
        "started": started, "exit_code": exit_code, "reason": reason,
        "started_at": started_at, "updated_at": updated_at,
        "stdout_bytes": stdout_bytes, "stderr_bytes": stderr_bytes,
        "usage": normalize_driver_usage(usage),
    }


def _write_file(path: Path, content: object, fmt: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if fmt == "json" and not isinstance(content, str):
        text = json.dumps(content, indent=2, sort_keys=True) + "\n"
    else:
        text = str(content)
        if not text.endswith("\n"):
            text += "\n"
    path.write_text(text, encoding="utf-8")


class FixtureDriver:
    """Deterministic, filesystem-persisted driver used as the CI oracle."""

    adapter = "fixture"
    provider_family = ADAPTER_PROVIDER_FAMILIES[adapter]

    def __init__(self, responses: dict[str, dict[str, object]] | None = None) -> None:
        self.responses = responses or {}
        self.starts = 0

    def start(
        self, packet: dict[str, object], profile: dict[str, object], staging: Path
    ) -> dict[str, object]:
        self.starts += 1
        script = dict(self.responses.get(str(packet["node_id"]), {}))
        outputs = script.get("outputs", {})
        if not isinstance(outputs, dict):
            return {"state": "failed", "exit_code": 2, "reason": "malformed-output",
                    "polls_remaining": 0, "final_state": "failed",
                    "stdout_bytes": 0, "stderr_bytes": 0, "activity_plan": []}
        output_specs = {item["name"]: item for item in packet["outputs"]}
        output_dir = staging / "outputs"
        output_dir.mkdir(parents=True, exist_ok=True)
        for name, content in outputs.items():
            spec = output_specs.get(name)
            fmt = str(spec["format"]) if spec else "text"
            _write_file(output_dir / str(name), content, fmt)
        workspace_files = script.get("workspace_files", {})
        if workspace_files:
            if packet["workspace"]["mode"] != "isolated-worktree":
                return {"state": "failed", "exit_code": 2, "reason": "workspace-refused",
                        "polls_remaining": 0, "final_state": "failed",
                        "stdout_bytes": 0, "stderr_bytes": 0, "activity_plan": []}
            workspace = Path(str(packet["workspace"]["path"])).resolve()
            for name, content in workspace_files.items():  # type: ignore[union-attr]
                target = (workspace / str(name)).resolve()
                if target != workspace and workspace not in target.parents:
                    return {"state": "failed", "exit_code": 2, "reason": "workspace-refused",
                            "polls_remaining": 0, "final_state": "failed",
                            "stdout_bytes": 0, "stderr_bytes": 0, "activity_plan": []}
                _write_file(target, content, "text")
        final_state = str(script.get("state", "succeeded"))
        if final_state not in {"succeeded", "failed", "cancelled", "lost"}:
            final_state = "failed"
        polls = int(script.get("polls", 1))
        exit_code = script.get("exit_code", 0 if final_state == "succeeded" else 1)
        reason = str(script.get(
            "reason", "completed" if final_state == "succeeded" else final_state
        ))
        if exit_code not in {0, None}:
            final_state = "failed"
            reason = "nonzero-exit"
        if reason not in _DRIVER_REASONS:
            reason = "failed"
        activities = script.get("activities", [])
        if not isinstance(activities, list):
            activities = []
        return {
            "state": final_state if polls == 0 else "running",
            "exit_code": exit_code if polls == 0 else None,
            "reason": "running" if polls > 0 else reason,
            "polls_remaining": max(0, polls), "final_state": final_state,
            "stdout_bytes": int(script.get("stdout_bytes", 0)),
            "stderr_bytes": int(script.get("stderr_bytes", 0)),
            "activity_plan": [str(item) for item in activities],
            "usage": script.get("usage"),
        }

    def interrupt(self, _session: dict[str, object]) -> bool:
        return True

    def deliver_nudge(
        self, record: dict[str, object], packet: dict[str, object]
    ) -> bool:
        staging = Path(str(record.get("staging", "")))
        if not staging.is_dir():
            return False
        target = staging / "nudges"
        target.mkdir(exist_ok=True)
        name = str(packet.get("packet_hash", "nudge")).split(":", 1)[-1][:24]
        (target / f"{name}.json").write_text(
            json.dumps(packet, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        return True


class CodexExecDriver:
    """Real optional adapter over the stable non-interactive `codex exec`."""

    adapter = "codex-exec"
    provider_family = ADAPTER_PROVIDER_FAMILIES[adapter]

    @staticmethod
    def _prompt(packet: dict[str, object]) -> str:
        output_contract = json.dumps(packet["outputs"], indent=2, sort_keys=True)
        contexts = json.dumps(packet["context"], indent=2, sort_keys=True)
        inputs = json.dumps(packet["inputs"], indent=2, sort_keys=True)
        mode = packet["workspace"]["mode"]
        instruction = (
            "Do not modify any file; return only the declared artifact content."
            if mode == "read-only"
            else "Edit only the declared allowed paths in this isolated worktree; do not commit or merge."
        )
        return (
            f"Delivery Workbench work packet {packet['packet_hash']}\n"
            f"Role: {packet['role']}\nTask: {packet['prompt']}\n{instruction}\n"
            f"Permanent exclusions: {', '.join(packet['permanent_exclusions'])}\n"
            f"Declared outputs:\n{output_contract}\n"
            f"Validated artifact inputs:\n{inputs}\nBounded context:\n{contexts}\n"
        )

    @staticmethod
    def _safe_env() -> dict[str, str]:
        allowed = {
            "HOME", "PATH", "TMPDIR", "LANG", "LC_ALL", "TERM", "CODEX_HOME",
            "SSL_CERT_FILE", "SSL_CERT_DIR", "CODEX_API_KEY", "OPENAI_API_KEY",
            "HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY", "NO_PROXY",
            "http_proxy", "https_proxy", "all_proxy", "no_proxy",
        }
        return {key: value for key, value in os.environ.items() if key in allowed}

    def start(
        self, packet: dict[str, object], profile: dict[str, object], staging: Path
    ) -> dict[str, object]:
        command = str(profile["command"][0])
        executable = shutil.which(command)
        if executable is None:
            return {"state": "failed", "exit_code": None, "reason": "adapter-unavailable",
                    "polls_remaining": 0, "final_state": "failed",
                    "stdout_bytes": 0, "stderr_bytes": 0, "activity_plan": []}
        outputs = packet["outputs"]
        if packet["workspace"]["mode"] == "read-only" and len(outputs) != 1:
            return {"state": "failed", "exit_code": None, "reason": "unsupported-output-shape",
                    "polls_remaining": 0, "final_state": "failed",
                    "stdout_bytes": 0, "stderr_bytes": 0, "activity_plan": []}
        staging.mkdir(parents=True, exist_ok=True)
        output_dir = staging / "outputs"
        output_dir.mkdir(exist_ok=True)
        final_message = staging / "final-message.txt"
        stdout_path = staging / "stdout.log"
        stderr_path = staging / "stderr.log"
        sandbox = "workspace-write" if packet["workspace"]["mode"] == "isolated-worktree" else "read-only"
        argv = [executable]
        if profile["network"]:
            argv.append("--search")
        argv.extend([
            "exec", "--ephemeral", "--ignore-user-config", "--color", "never",
            "--sandbox", sandbox, "-c", 'approval_policy="never"',
            "-c", 'shell_environment_policy.inherit="none"',
            "--output-last-message", str(final_message),
            "-C", str(packet["workspace"]["path"]),
        ])
        if profile.get("model"):
            argv.extend(["--model", str(profile["model"])])
        if profile["network"] and sandbox == "workspace-write":
            argv.extend(["-c", "sandbox_workspace_write.network_access=true"])
        prompt = self._prompt(packet)
        reason = "completed"
        exit_code: int | None = None
        try:
            with stdout_path.open("wb") as stdout, stderr_path.open("wb") as stderr:
                result = subprocess.run(
                    argv + [prompt], stdout=stdout, stderr=stderr, stdin=subprocess.DEVNULL,
                    env=self._safe_env(), timeout=int(packet["timeout_seconds"]),
                )
                exit_code = result.returncode
        except subprocess.TimeoutExpired:
            reason = "timeout"
        stdout_bytes = stdout_path.stat().st_size if stdout_path.exists() else 0
        stderr_bytes = stderr_path.stat().st_size if stderr_path.exists() else 0
        max_stream = int(packet["max_stream_bytes"])
        if stdout_bytes > max_stream or stderr_bytes > max_stream:
            reason = "oversized-stream"
            exit_code = exit_code if exit_code is not None else 1
        if exit_code == 0 and final_message.is_file():
            if packet["workspace"]["mode"] == "read-only":
                target = output_dir / str(outputs[0]["name"])
                shutil.copyfile(final_message, target)
            state = "succeeded"
        else:
            state = "failed"
            if reason == "completed":
                reason = "nonzero-exit" if exit_code is not None else "lost"
        return {
            "state": state, "exit_code": exit_code, "reason": reason,
            "polls_remaining": 0, "final_state": state,
            "stdout_bytes": min(stdout_bytes, max_stream + 1),
            "stderr_bytes": min(stderr_bytes, max_stream + 1),
            # Non-interactive exec cannot observe prompt or permission
            # states; it may claim nothing richer than active/exited.
            "activity_plan": [],
        }

    def interrupt(self, _session: dict[str, object]) -> bool:
        # `start` is bounded and synchronous in this adapter version. A future
        # asynchronous process handle can add active interruption without
        # changing the provider-neutral receipt schema.
        return False


class ClaudeCodeExecDriver:
    """Real optional adapter over non-interactive `claude -p`.

    Least privilege by construction: the packet's workspace mode maps to
    a closed tool allowlist (never a shell tool in either mode), the
    environment is scrubbed to a small allowlist, authentication stays
    entirely harness-owned, and capability discovery pins the tested
    `claude` major version — outside the pin the adapter refuses
    content-free rather than degrading silently (the herdr version-skew
    lesson, recorded in WLA-25-07).
    """

    adapter = "claude-exec"
    provider_family = ADAPTER_PROVIDER_FAMILIES[adapter]

    # The tested major-version pin. A different major refuses with
    # adapter-unavailable instead of guessing at flag compatibility.
    TESTED_MAJORS = (2,)

    _READ_TOOLS = "Read,Grep,Glob"
    _WRITE_TOOLS = "Read,Grep,Glob,Write,Edit,MultiEdit"

    _prompt = staticmethod(CodexExecDriver._prompt)

    @staticmethod
    def _safe_env() -> dict[str, str]:
        allowed = {
            # USER/LOGNAME are identity, not secrets: macOS keychain
            # lookups (the harness-owned credential store) fail closed
            # without them.
            "HOME", "PATH", "TMPDIR", "LANG", "LC_ALL", "TERM",
            "USER", "LOGNAME",
            "SSL_CERT_FILE", "SSL_CERT_DIR", "ANTHROPIC_API_KEY",
            "CLAUDE_CODE_USE_BEDROCK", "CLAUDE_CODE_USE_VERTEX",
            "HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY", "NO_PROXY",
            "http_proxy", "https_proxy", "all_proxy", "no_proxy",
        }
        return {key: value for key, value in os.environ.items() if key in allowed}

    def _version_supported(self, executable: str) -> bool:
        try:
            probe = subprocess.run(
                [executable, "--version"], env=self._safe_env(),
                stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                timeout=20, text=True,
            )
        except (OSError, subprocess.TimeoutExpired):
            return False
        if probe.returncode != 0:
            return False
        match = re.match(r"\s*(\d+)\.", probe.stdout or "")
        return bool(match) and int(match.group(1)) in self.TESTED_MAJORS

    def start(
        self, packet: dict[str, object], profile: dict[str, object], staging: Path
    ) -> dict[str, object]:
        def refusal(reason: str) -> dict[str, object]:
            return {"state": "failed", "exit_code": None, "reason": reason,
                    "polls_remaining": 0, "final_state": "failed",
                    "stdout_bytes": 0, "stderr_bytes": 0, "activity_plan": []}

        command = str(profile["command"][0])
        executable = shutil.which(command)
        if executable is None:
            return refusal("adapter-unavailable")
        if not self._version_supported(executable):
            return refusal("adapter-unavailable")
        outputs = packet["outputs"]
        if packet["workspace"]["mode"] == "read-only" and len(outputs) != 1:
            return refusal("unsupported-output-shape")
        staging.mkdir(parents=True, exist_ok=True)
        output_dir = staging / "outputs"
        output_dir.mkdir(exist_ok=True)
        stdout_path = staging / "stdout.log"
        stderr_path = staging / "stderr.log"
        read_only = packet["workspace"]["mode"] == "read-only"
        tools = self._READ_TOOLS if read_only else self._WRITE_TOOLS
        if profile["network"]:
            tools += ",WebSearch,WebFetch"
        argv = [
            executable, "-p", "--output-format", "text",
            "--allowedTools", tools,
            "--disallowedTools", "Bash,Task,NotebookEdit",
            "--permission-mode", "default" if read_only else "acceptEdits",
        ]
        if profile.get("model"):
            argv.extend(["--model", str(profile["model"])])
        prompt = self._prompt(packet)
        reason = "completed"
        exit_code: int | None = None
        try:
            with stdout_path.open("wb") as stdout, stderr_path.open("wb") as stderr:
                result = subprocess.run(
                    argv + [prompt], stdout=stdout, stderr=stderr,
                    stdin=subprocess.DEVNULL,
                    env=self._safe_env(), timeout=int(packet["timeout_seconds"]),
                    cwd=str(packet["workspace"]["path"]),
                )
                exit_code = result.returncode
        except subprocess.TimeoutExpired:
            reason = "timeout"
        stdout_bytes = stdout_path.stat().st_size if stdout_path.exists() else 0
        stderr_bytes = stderr_path.stat().st_size if stderr_path.exists() else 0
        max_stream = int(packet["max_stream_bytes"])
        if stdout_bytes > max_stream or stderr_bytes > max_stream:
            reason = "oversized-stream"
            exit_code = exit_code if exit_code is not None else 1
        if exit_code == 0 and stdout_bytes > 0:
            if read_only:
                target = output_dir / str(outputs[0]["name"])
                shutil.copyfile(stdout_path, target)
            else:
                # Write mode mirrors the read-only response contract for
                # exactly one declared non-diff output: the final message
                # IS that output (the packet task tells the agent it must
                # be the pure typed document). The candidate itself is
                # collected from the worktree diff, never from stdout.
                # Found by the Phase 30 exam: a declared lesson output had
                # no materialization channel in write mode at all.
                non_diff = [
                    item for item in outputs
                    if str(item.get("format")) != "git-diff"
                ]
                if len(non_diff) == 1:
                    target = output_dir / str(non_diff[0]["name"])
                    shutil.copyfile(stdout_path, target)
            state = "succeeded"
        else:
            state = "failed"
            if reason == "completed":
                reason = "nonzero-exit" if exit_code is not None else "lost"
        return {
            "state": state, "exit_code": exit_code, "reason": reason,
            "polls_remaining": 0, "final_state": state,
            "stdout_bytes": min(stdout_bytes, max_stream + 1),
            "stderr_bytes": min(stderr_bytes, max_stream + 1),
            # Non-interactive print mode cannot observe prompt or
            # permission states; it may claim nothing richer than
            # active/exited.
            "activity_plan": [],
        }

    def interrupt(self, _session: dict[str, object]) -> bool:
        # `start` is bounded and synchronous, exactly like the codex
        # adapter; asynchronous interruption arrives with a future
        # interactive driver, not this one.
        return False


class PiExecDriver:
    """Closed non-interactive adapter for the pi coding-agent CLI.

    The profile pins the exact reported CLI semver.  Tracked policy cannot
    supply argv or credentials: this adapter renders one closed print-mode
    invocation, selects only the resolved provider/model binding, disables
    session persistence and update telemetry, and exposes no shell tool.
    """

    adapter = "pi-exec"
    provider_family = ADAPTER_PROVIDER_FAMILIES[adapter]
    _READ_TOOLS = "read,grep,find,ls"
    _WRITE_TOOLS = "read,write,edit,grep,find,ls"
    _prompt = staticmethod(CodexExecDriver._prompt)

    @staticmethod
    def _safe_env() -> dict[str, str]:
        allowed = {
            "HOME", "PATH", "TMPDIR", "LANG", "LC_ALL", "TERM",
            "USER", "LOGNAME", "SSL_CERT_FILE", "SSL_CERT_DIR",
            "ANTHROPIC_API_KEY", "OPENAI_API_KEY", "OPENROUTER_API_KEY",
            "GOOGLE_API_KEY", "GEMINI_API_KEY", "XAI_API_KEY",
            "MISTRAL_API_KEY", "GROQ_API_KEY", "DEEPSEEK_API_KEY",
            "AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY", "AWS_SESSION_TOKEN",
            "AWS_REGION", "AWS_DEFAULT_REGION",
            "HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY", "NO_PROXY",
            "http_proxy", "https_proxy", "all_proxy", "no_proxy",
        }
        env = {key: value for key, value in os.environ.items() if key in allowed}
        env.update({
            "PI_SKIP_VERSION_CHECK": "1",
            "PI_TELEMETRY": "0",
        })
        return env

    def _version_supported(
        self, executable: str, expected_adapter_version: str
    ) -> bool:
        try:
            probe = subprocess.run(
                [executable, "--version"],
                env=self._safe_env(),
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                timeout=20,
                text=True,
            )
        except (OSError, subprocess.TimeoutExpired):
            return False
        if probe.returncode != 0:
            return False
        match = re.search(
            r"(?<![0-9])([0-9]+\.[0-9]+\.[0-9]+(?:[-+][A-Za-z0-9.-]+)?)",
            probe.stdout or "",
        )
        return bool(match) and expected_adapter_version == f"pi-cli@{match.group(1)}"

    def start(
        self, packet: dict[str, object], profile: dict[str, object], staging: Path
    ) -> dict[str, object]:
        def refusal(reason: str) -> dict[str, object]:
            return {
                "state": "failed", "exit_code": None, "reason": reason,
                "polls_remaining": 0, "final_state": "failed",
                "stdout_bytes": 0, "stderr_bytes": 0, "activity_plan": [],
            }

        command = str(profile["command"][0])
        executable = shutil.which(command)
        if executable is None or not self._version_supported(
            executable, str(profile["adapter_version"])
        ):
            return refusal("adapter-unavailable")
        outputs = packet["outputs"]
        read_only = packet["workspace"]["mode"] == "read-only"
        if read_only and len(outputs) != 1:
            return refusal("unsupported-output-shape")
        staging.mkdir(parents=True, exist_ok=True)
        output_dir = staging / "outputs"
        output_dir.mkdir(exist_ok=True)
        stdout_path = staging / "stdout.log"
        stderr_path = staging / "stderr.log"
        tools = self._READ_TOOLS if read_only else self._WRITE_TOOLS
        argv = [
            executable,
            "-p",
            "--no-session",
            "--tools",
            tools,
        ]
        provider = str(profile.get("provider") or "")
        if provider and provider != "unresolved":
            argv.extend(["--provider", provider])
        if profile.get("model"):
            argv.extend(["--model", str(profile["model"])])
        prompt = self._prompt(packet)
        reason = "completed"
        exit_code: int | None = None
        try:
            with stdout_path.open("wb") as stdout, stderr_path.open("wb") as stderr:
                result = subprocess.run(
                    argv + [prompt],
                    stdout=stdout,
                    stderr=stderr,
                    stdin=subprocess.DEVNULL,
                    env=self._safe_env(),
                    timeout=int(packet["timeout_seconds"]),
                    cwd=str(packet["workspace"]["path"]),
                )
                exit_code = result.returncode
        except subprocess.TimeoutExpired:
            reason = "timeout"
        stdout_bytes = stdout_path.stat().st_size if stdout_path.exists() else 0
        stderr_bytes = stderr_path.stat().st_size if stderr_path.exists() else 0
        max_stream = int(packet["max_stream_bytes"])
        if stdout_bytes > max_stream or stderr_bytes > max_stream:
            reason = "oversized-stream"
            exit_code = exit_code if exit_code is not None else 1
        if exit_code == 0 and (not read_only or stdout_bytes > 0):
            if read_only:
                shutil.copyfile(stdout_path, output_dir / str(outputs[0]["name"]))
            state = "succeeded"
        else:
            state = "failed"
            if reason == "completed":
                reason = "nonzero-exit" if exit_code is not None else "lost"
        return {
            "state": state,
            "exit_code": exit_code,
            "reason": reason,
            "polls_remaining": 0,
            "final_state": state,
            "stdout_bytes": min(stdout_bytes, max_stream + 1),
            "stderr_bytes": min(stderr_bytes, max_stream + 1),
            "activity_plan": [],
        }

    def interrupt(self, _session: dict[str, object]) -> bool:
        return False


def _schema_check(value: object, schema: object, pointer: str = "$") -> list[str]:
    if not isinstance(schema, dict):
        return [f"{pointer}: schema must be an object"]
    errors: list[str] = []
    expected = schema.get("type")
    type_map = {
        "object": dict, "array": list, "string": str,
        "integer": int, "number": (int, float), "boolean": bool, "null": type(None),
    }
    if expected in type_map and (
        not isinstance(value, type_map[expected])
        or expected in {"integer", "number"} and isinstance(value, bool)
    ):
        return [f"{pointer}: expected {expected}"]
    if isinstance(value, dict):
        required = schema.get("required", [])
        if isinstance(required, list):
            for key in required:
                if key not in value:
                    errors.append(f"{pointer}: missing required property {key}")
        properties = schema.get("properties", {})
        if isinstance(properties, dict):
            for key, child in value.items():
                if key in properties:
                    errors.extend(_schema_check(child, properties[key], f"{pointer}.{key}"))
                elif schema.get("additionalProperties") is False:
                    errors.append(f"{pointer}: unexpected property {key}")
    if isinstance(value, list) and "items" in schema:
        for index, child in enumerate(value):
            errors.extend(_schema_check(child, schema["items"], f"{pointer}[{index}]"))
    return errors


def _git_diff_artifact(workspace: Path, allowed: list[str]) -> tuple[bytes, list[str]]:
    status = subprocess.run(
        [
            "git", "-C", str(workspace), "status", "--porcelain=v1", "-z",
            "--untracked-files=all",
        ],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )
    if status.returncode:
        raise DwError("cannot inspect isolated worktree changes")
    paths = []
    tokens = status.stdout.split(b"\0")
    index = 0
    while index < len(tokens):
        token = tokens[index]
        index += 1
        if len(token) < 4:
            continue
        code = token[:2].decode("ascii", "replace")
        paths.append(os.fsdecode(token[3:]))
        if (code[0] in {"R", "C"} or code[1] in {"R", "C"}) and index < len(tokens):
            index += 1
    paths = sorted(set(paths))
    if not paths:
        raise DwError("git-diff output contains no workspace changes")
    outside = [path for path in paths if not any(fnmatch.fnmatch(path, pattern) for pattern in allowed)]
    if outside:
        raise DwError("workspace diff escapes declared paths: " + ", ".join(outside))
    intent = subprocess.run(
        ["git", "-C", str(workspace), "add", "-N", "--", "."],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )
    if intent.returncode:
        raise DwError("cannot prepare untracked files for diff inspection")
    diff = subprocess.run(
        ["git", "-C", str(workspace), "diff", "--binary", "HEAD", "--"],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )
    if diff.returncode:
        raise DwError("cannot capture isolated worktree diff")
    return diff.stdout, paths


def validate_and_store_outputs(
    root: Path,
    packet: dict[str, object],
    staging: Path,
) -> list[dict[str, object]]:
    packet = validate_work_packet(packet)
    output_dir = staging / "outputs"
    declared = {str(item["name"]): item for item in packet["outputs"]}
    present = {path.name for path in output_dir.iterdir()} if output_dir.is_dir() else set()
    non_diff = {name for name, spec in declared.items() if spec["format"] != "git-diff"}
    if present - non_diff:
        raise DwError("driver produced undeclared output(s): " + ", ".join(sorted(present - non_diff)))
    prepared: list[tuple[dict[str, object], bytes]] = []
    for name, spec in declared.items():
        fmt = str(spec["format"])
        checks = ["declared", "contained"]
        if fmt == "git-diff":
            if packet["workspace"]["mode"] != "isolated-worktree":
                raise DwError("git-diff output requires an isolated worktree")
            data, paths = _git_diff_artifact(
                Path(str(packet["workspace"]["path"])), list(spec["allowed_paths"])
            )
            checks.append("diff-scope:" + ",".join(paths))
        elif fmt == "directory":
            source = output_dir / name
            if not source.is_dir() or source.is_symlink():
                raise DwError(f"declared directory output is missing or unsafe: {name}")
            members = []
            for child in sorted(source.rglob("*"), key=lambda item: str(item)):
                if child.is_symlink():
                    raise DwError(f"directory output {name!r} contains a symlink")
                if not child.is_file():
                    continue
                if len(members) >= MAX_CONTEXT_FILES:
                    raise DwError(f"directory output {name!r} exceeds the file-count bound")
                raw = child.read_bytes()
                members.append({
                    "path": str(child.relative_to(source)), "bytes": len(raw),
                    "sha256": "sha256:" + hashlib.sha256(raw).hexdigest(),
                    "content": raw.decode("utf-8", "replace"),
                })
            data = (canonical_json(members) + "\n").encode("utf-8")
            checks.append("directory-manifest")
        else:
            source = output_dir / name
            if not source.is_file() or source.is_symlink():
                raise DwError(f"declared output is missing or unsafe: {name}")
            data = source.read_bytes()
        if len(data) > int(spec["max_bytes"]):
            raise DwError(f"declared output {name!r} exceeds its byte bound")
        try:
            text = data.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise DwError(f"declared output {name!r} is not UTF-8") from exc
        checks.append("bytes")
        if fmt == "markdown":
            headings = {
                match.group(1).strip().lower()
                for match in re.finditer(r"(?m)^#{1,6}\s+(.+?)\s*$", text)
            }
            missing = [section for section in spec["required_sections"]
                       if str(section).strip().lower() not in headings]
            if missing:
                raise DwError(f"markdown output {name!r} lacks sections: {', '.join(missing)}")
            if spec["citations"] == "required" and not re.search(
                r"https?://|\[[^\]]+\]\([^)]+\)", text
            ):
                raise DwError(f"markdown output {name!r} requires at least one citation")
            checks.extend(["markdown-sections", "citations"])
        elif fmt == "json":
            try:
                value = json.loads(text)
            except json.JSONDecodeError as exc:
                raise DwError(f"JSON output {name!r} is malformed") from exc
            if spec.get("schema"):
                schema_path = (root.resolve() / str(spec["schema"])).resolve()
                if root.resolve() not in schema_path.parents or not schema_path.is_file():
                    raise DwError(f"JSON schema for {name!r} is absent or escaped")
                schema = json.loads(schema_path.read_text(encoding="utf-8"))
                errors = _schema_check(value, schema)
                if errors:
                    raise DwError(f"JSON output {name!r} failed schema: {errors[0]}")
                checks.append("json-schema")
            checks.append("json")
        elif fmt == "git-diff":
            checks.append("git-diff")
        elif fmt not in {"text", "directory"}:
            raise DwError(f"unsupported artifact format: {fmt}")
        receipt = {
            "kind": ARTIFACT_RECEIPT_KIND, "schema_version": DRIVER_SCHEMA_VERSION,
            "run_id": packet["run_id"], "node_id": packet["node_id"],
            "attempt": packet["attempt"], "name": name, "format": fmt,
            "bytes": len(data), "sha256": "sha256:" + hashlib.sha256(data).hexdigest(),
            "path": f"artifacts/{packet['node_id']}/{name}/content",
            "valid": True, "checks": checks,
        }
        prepared.append((receipt, data))
    artifacts = _run_dir(root, str(packet["run_id"])) / "artifacts" / str(packet["node_id"])
    written: list[Path] = []
    receipts: list[dict[str, object]] = []
    try:
        for receipt, data in prepared:
            destination = artifacts / str(receipt["name"])
            superseded: Path | None = None
            if destination.exists():
                existing = _exact_keys(
                    json.loads((destination / "metadata.json").read_text()),
                    _ARTIFACT_KEYS, "artifact receipt",
                )
                if canonical_json(existing) == canonical_json(receipt):
                    receipts.append(existing)
                    continue
                if int(existing.get("attempt", 0)) >= int(receipt["attempt"]):
                    raise DwError(f"artifact receipt already exists with different bytes: {receipt['name']}")
                # A nudge- or route-reactivated later attempt legitimately
                # re-produces the artifact: the newer validated bytes
                # supersede, atomically, and the retired copy is removed
                # only after the replacement is published.
                superseded = destination.parent / f".superseded-{existing['attempt']}-{receipt['name']}"
                shutil.rmtree(superseded, ignore_errors=True)
                os.rename(destination, superseded)
            temporary = Path(tempfile.mkdtemp(prefix=".artifact.", dir=str(artifacts.parent if artifacts.parent.exists() else _run_dir(root, str(packet["run_id"])))))
            try:
                temporary.mkdir(parents=True, exist_ok=True)
                (temporary / "content").write_bytes(data)
                (temporary / "metadata.json").write_text(
                    json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8"
                )
                os.chmod(temporary / "content", 0o600)
                os.chmod(temporary / "metadata.json", 0o600)
                destination.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
                os.rename(temporary, destination)
                written.append(destination)
                if superseded is not None:
                    shutil.rmtree(superseded, ignore_errors=True)
            finally:
                if temporary.exists():
                    shutil.rmtree(temporary, ignore_errors=True)
            receipts.append(receipt)
    except Exception:
        for path in written:
            shutil.rmtree(path, ignore_errors=True)
        raise
    return receipts


def artifact_inventory(root: Path, run_id: str) -> list[dict[str, object]]:
    """Re-verify every validated artifact receipt without returning content."""
    artifacts = _run_dir(root, run_id) / "artifacts"
    receipts: list[dict[str, object]] = []
    if not artifacts.is_dir():
        return receipts
    for metadata in sorted(artifacts.glob("*/*/metadata.json"), key=lambda item: str(item)):
        receipt = _exact_keys(
            json.loads(metadata.read_text(encoding="utf-8")),
            _ARTIFACT_KEYS,
            "artifact receipt",
        )
        if receipt["run_id"] != run_id or not receipt["valid"]:
            raise DwError("artifact inventory contains an invalid or cross-run receipt")
        content = metadata.parent / "content"
        if not content.is_file() or content.is_symlink():
            raise DwError(f"artifact content is absent or unsafe: {receipt['name']}")
        data = content.read_bytes()
        digest = "sha256:" + hashlib.sha256(data).hexdigest()
        if len(data) != receipt["bytes"] or digest != receipt["sha256"]:
            raise DwError(f"artifact content does not match its receipt: {receipt['name']}")
        receipts.append(receipt)
    return receipts


class DriverManager:
    """Receipt/idempotency wrapper around configured provider adapters."""

    def __init__(
        self,
        root: Path,
        config: object,
        adapters: dict[str, object] | None = None,
    ) -> None:
        self.root = root.resolve()
        self.config = load_driver_config(self.root, config)
        self.adapters = adapters or {
            "fixture": FixtureDriver(),
            "codex-exec": CodexExecDriver(),
            "claude-exec": ClaudeCodeExecDriver(),
            "pi-exec": PiExecDriver(),
        }

    def capability(self, profile: str) -> dict[str, object]:
        return driver_capability(self.config, profile)

    def _session_dir(self, run_id: str) -> Path:
        path = _run_dir(self.root, run_id) / "driver-sessions"
        path.mkdir(parents=True, exist_ok=True, mode=0o700)
        return path

    @contextmanager
    def _lock(self, run_id: str) -> Iterator[None]:
        path = self._session_dir(run_id) / ".lock"
        with path.open("a+") as handle:
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
            try:
                yield
            finally:
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)

    def _records(self, run_id: str) -> list[tuple[Path, dict[str, object]]]:
        records = []
        for path in sorted(self._session_dir(run_id).glob("session-*.json")):
            try:
                value = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError) as exc:
                raise DwError(f"driver session record is corrupt: {path.name}") from exc
            records.append((path, value))
        return records

    @staticmethod
    def _write_record(path: Path, value: dict[str, object]) -> None:
        temporary = path.with_name("." + path.name + ".tmp")
        temporary.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        os.chmod(temporary, 0o600)
        os.replace(temporary, path)

    def _refusal(
        self, packet: dict[str, object], profile: dict[str, object] | None,
        idempotency_key: str, reason: str,
    ) -> dict[str, object]:
        now = _format_time(datetime.now(timezone.utc))
        return _receipt(
            packet, str(profile["adapter"] if profile else "unconfigured"), None,
            idempotency_key, "refused", False, None, reason, None, now,
        )

    def start(self, packet: object, idempotency_key: str) -> dict[str, object]:
        packet = validate_work_packet(packet)
        if not _SAFE_ID_RE.fullmatch(idempotency_key or ""):
            raise DwError("driver idempotency key must be a bounded selector")
        run_id = str(packet["run_id"])
        with self._lock(run_id):
            for _path, record in self._records(run_id):
                if record["idempotency_key"] == idempotency_key:
                    if record["packet_hash"] != packet["packet_hash"]:
                        raise DwError("driver idempotency key is bound to a different packet")
                    return _validate_driver_receipt(record["receipt"])
            profile = self.config["profiles"].get(packet["profile"])  # type: ignore[union-attr]
            if profile is None:
                return self._refusal(packet, None, idempotency_key, "profile-unconfigured")
            capability = driver_capability(self.config, str(packet["profile"]))
            if set(packet["capabilities"]) - set(capability["capabilities"]):
                return self._refusal(packet, profile, idempotency_key, "unsupported-capability")
            if packet["workspace"]["mode"] not in capability["workspace_modes"]:
                return self._refusal(packet, profile, idempotency_key, "unsupported-workspace")
            adapter = self.adapters.get(str(profile["adapter"]))
            if adapter is None:
                return self._refusal(packet, profile, idempotency_key, "adapter-unavailable")
            projection = replay_run(self.root, run_id)
            claim = next(
                (item for item in projection["active_claims"]
                 if item["claim_id"] == packet["claim_id"]),
                None,
            )
            if claim is None or not projection["dispatch_allowed"]:
                return self._refusal(packet, profile, idempotency_key, "dispatch-refused")
            _run_path, grant, _compiled = _load_run_documents(self.root, run_id)
            if _grant_freshness_issues(self.root, grant, projection):
                return self._refusal(packet, profile, idempotency_key, "grant-stale")
            if datetime.now(timezone.utc) >= _parse_time(packet["deadline"], "packet deadline"):
                return self._refusal(packet, profile, idempotency_key, "packet-expired")
            session_id = "session-" + _sha({
                "packet_hash": packet["packet_hash"], "idempotency_key": idempotency_key,
                "adapter": profile["adapter"],
            }).split(":", 1)[1][:24]
            base = _workspace_base(self.root, self.config)
            staging = _safe_child(base, run_id, "sessions", session_id)
            staging.mkdir(parents=True, exist_ok=False, mode=0o700)
            packet_path = staging / "packet.json"
            packet_path.write_text(json.dumps(packet, indent=2, sort_keys=True) + "\n", encoding="utf-8")
            os.chmod(packet_path, 0o600)
            result = dict(adapter.start(packet, profile, staging))
            result["usage"] = normalize_driver_usage(result.get("usage"))
            _exact_keys(result, _ADAPTER_RESULT_KEYS, "adapter result")
            if (
                result["state"] not in _DRIVER_STATES - {"refused"}
                or result["final_state"] not in _DRIVER_STATES - {"running", "refused"}
                or result["reason"] not in _DRIVER_REASONS
                or isinstance(result["polls_remaining"], bool)
                or not isinstance(result["polls_remaining"], int)
                or result["polls_remaining"] < 0
            ):
                raise DwError("adapter returned an invalid bounded result")
            plan = result["activity_plan"]
            if (
                not isinstance(plan, list)
                or len(plan) > _MAX_ACTIVITY_PLAN
                or any(
                    item not in ACTIVITY_STATES or item == "exited"
                    for item in plan
                )
            ):
                raise DwError(
                    "adapter reported an activity state outside the "
                    "contracted vocabulary"
                )
            if (
                int(result["stdout_bytes"]) > int(packet["max_stream_bytes"])
                or int(result["stderr_bytes"]) > int(packet["max_stream_bytes"])
            ):
                result["state"] = "failed"
                result["final_state"] = "failed"
                result["reason"] = "oversized-stream"
                result["exit_code"] = result["exit_code"] if result["exit_code"] is not None else 1
                result["polls_remaining"] = 0
            now = _format_time(datetime.now(timezone.utc))
            receipt = _receipt(
                packet, str(profile["adapter"]), session_id, idempotency_key,
                str(result["state"]), True, result["exit_code"], str(result["reason"]),
                now, now, int(result["stdout_bytes"]), int(result["stderr_bytes"]),
                activity=str(plan[0]) if plan else None,
                usage=result["usage"],
            )
            record = {
                "session_id": session_id, "idempotency_key": idempotency_key,
                "packet_hash": packet["packet_hash"], "packet_path": str(packet_path),
                "staging": str(staging), "adapter": profile["adapter"],
                "polls_remaining": result["polls_remaining"],
                "final_state": result["final_state"], "receipt": receipt,
                "activity_plan": [str(item) for item in plan],
                "activity_index": 0,
            }
            self._write_record(self._session_dir(run_id) / f"{session_id}.json", record)
            return receipt

    def _find(self, run_id: str, session_id: str) -> tuple[Path, dict[str, object]]:
        if not session_id.startswith("session-") or not _SAFE_ID_RE.fullmatch(session_id):
            raise DwError(f"unsafe driver session id: {session_id!r}")
        path = self._session_dir(run_id) / f"{session_id}.json"
        if not path.is_file():
            raise DwError(f"driver session not found: {session_id}")
        return path, json.loads(path.read_text(encoding="utf-8"))

    def receipt_for_claim(
        self, run_id: str, claim_id: str
    ) -> dict[str, object] | None:
        """Return the one persisted session receipt bound to a ledger claim."""
        with self._lock(run_id):
            matches = [
                record["receipt"]
                for _path, record in self._records(run_id)
                if record.get("receipt", {}).get("claim_id") == claim_id
            ]
            if len(matches) > 1:
                raise DwError("multiple driver sessions are bound to one node claim")
            if not matches:
                return None
            return _validate_driver_receipt(matches[0])

    def poll(self, run_id: str, session_id: str) -> dict[str, object]:
        with self._lock(run_id):
            path, record = self._find(run_id, session_id)
            receipt = _validate_driver_receipt(record["receipt"])
            if receipt["state"] == "running":
                remaining = max(0, int(record["polls_remaining"]) - 1)
                record["polls_remaining"] = remaining
                if remaining == 0:
                    state = str(record["final_state"])
                    receipt["state"] = state
                    receipt["exit_code"] = (
                        0 if state == "succeeded" else (1 if state == "failed" else None)
                    )
                    receipt["reason"] = "completed" if state == "succeeded" else state
                    receipt["activity"] = _terminal_activity(state)
                else:
                    plan = record.get("activity_plan") or []
                    index = int(record.get("activity_index", 0)) + 1
                    record["activity_index"] = index
                    receipt["activity"] = (
                        str(plan[min(index, len(plan) - 1)]) if plan else "active"
                    )
                receipt["updated_at"] = _format_time(datetime.now(timezone.utc))
                record["receipt"] = receipt
                self._write_record(path, record)
            return receipt

    def can_nudge(self, run_id: str, session_id: str) -> bool:
        try:
            _path, record = self._find(run_id, session_id)
        except DwError:
            return False
        receipt = record.get("receipt", {})
        adapter = self.adapters.get(str(record.get("adapter")))
        return (
            isinstance(receipt, dict)
            and receipt.get("state") == "running"
            and adapter is not None
            and hasattr(adapter, "deliver_nudge")
        )

    def nudge_session(
        self, run_id: str, session_id: str, note: dict[str, object]
    ) -> bool:
        """Deliver one structured nudge packet into a live session."""
        with self._lock(run_id):
            path, record = self._find(run_id, session_id)
            receipt = _validate_driver_receipt(record["receipt"])
            if receipt["state"] != "running":
                return False
            adapter = self.adapters.get(str(record["adapter"]))
            deliver = getattr(adapter, "deliver_nudge", None)
            if deliver is None:
                return False
            packet = dict(note)
            packet["packet_hash"] = _sha(note)
            if not deliver(record, packet):
                return False
            receipt["activity"] = "active"
            receipt["updated_at"] = _format_time(datetime.now(timezone.utc))
            record["receipt"] = receipt
            self._write_record(path, record)
            return True

    def interrupt(self, run_id: str, session_id: str) -> dict[str, object]:
        with self._lock(run_id):
            path, record = self._find(run_id, session_id)
            receipt = _validate_driver_receipt(record["receipt"])
            if receipt["state"] == "running":
                adapter = self.adapters.get(str(record["adapter"]))
                if adapter is None or not adapter.interrupt(record):
                    receipt["state"] = "lost"
                    receipt["reason"] = "interrupt-unconfirmed"
                else:
                    receipt["state"] = "cancelled"
                    receipt["reason"] = "interrupted"
                receipt["activity"] = _terminal_activity(str(receipt["state"]))
                receipt["exit_code"] = None
                receipt["updated_at"] = _format_time(datetime.now(timezone.utc))
                record["receipt"] = receipt
                self._write_record(path, record)
            return receipt

    def collect(self, run_id: str, session_id: str) -> list[dict[str, object]]:
        with self._lock(run_id):
            _path, record = self._find(run_id, session_id)
            receipt = _validate_driver_receipt(record["receipt"])
            if receipt["state"] != "succeeded":
                raise DwError(f"driver session is not collectable: {receipt['state']}")
            packet = validate_work_packet(json.loads(Path(str(record["packet_path"])).read_text()))
            return validate_and_store_outputs(
                self.root, packet, Path(str(record["staging"])),
            )
