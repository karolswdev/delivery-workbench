"""Guarded preview/apply boundary for tracked orchestration scores.

This module is deliberately about score content only.  It cannot create a run,
grant, event, claim, agent, check, commit, or staged file.  A preview binds the
exact current score bytes to the exact normalized replacement; apply rebuilds
that plan and refuses stale state before one atomic contained write/delete.
"""

from __future__ import annotations

import difflib
import hashlib
import json
import os
import tempfile
from dataclasses import dataclass
from pathlib import Path

from .model import DwError
from .orchestration import (
    _SELECTOR_RE,
    canonical_json,
    compile_score,
    load_score,
    orchestration_dir,
    simulate_score,
    validate_score,
)


SCORE_MUTATION_PREVIEW_KIND = "delivery-workbench-orchestration-mutation-preview"
SCORE_MUTATION_RESULT_KIND = "delivery-workbench-orchestration-mutation-result"
SCORE_MUTATION_SCHEMA_VERSION = 1


@dataclass(frozen=True)
class ScoreMutationPlan:
    root: Path
    action: str
    name: str
    target: Path
    relative_path: str
    before: bytes | None
    after: bytes | None
    validation: dict[str, object] | None
    compiled: dict[str, object] | None
    simulation: dict[str, object] | None
    fingerprint: str


def _safe_target(root: Path, name: str) -> tuple[Path, str]:
    if not _SELECTOR_RE.fullmatch(name or ""):
        raise DwError(f"unsafe orchestration score name: {name!r}")
    root = root.resolve()
    allowed = orchestration_dir(root).resolve()
    if allowed != root and root not in allowed.parents:
        raise DwError("pm/orchestration resolves outside the repository")
    target = (allowed / f"{name}.json").resolve(strict=False)
    if target.parent != allowed:
        raise DwError(f"orchestration score escapes pm/orchestration: {name}")
    return target, str(Path("pm") / "orchestration" / f"{name}.json")


def _read_optional(path: Path) -> bytes | None:
    try:
        return path.read_bytes()
    except FileNotFoundError:
        return None
    except OSError as exc:
        raise DwError(f"cannot read orchestration score {path}: {exc}") from exc


def _fingerprint(action: str, relative_path: str, before: bytes | None, after: bytes | None) -> str:
    facts = {
        "action": action,
        "path": relative_path,
        "before": "absent" if before is None else "sha256:" + hashlib.sha256(before).hexdigest(),
        "after": "absent" if after is None else "sha256:" + hashlib.sha256(after).hexdigest(),
    }
    return "sha256:" + hashlib.sha256(canonical_json(facts).encode("utf-8")).hexdigest()


def _render_score(normalized: dict[str, object]) -> bytes:
    return (json.dumps(normalized, indent=2, ensure_ascii=False) + "\n").encode("utf-8")


def build_score_mutation_plan(
    root: Path,
    action: str,
    name: str,
    score: object | None = None,
) -> ScoreMutationPlan:
    """Build a pure plan. Invalid saves remain previewable but not applicable."""
    if action not in {"save", "delete"}:
        raise DwError("orchestration mutation action must be save or delete")
    root = root.resolve()
    target, relative = _safe_target(root, name)
    before = _read_optional(target)
    validation = None
    compiled = None
    simulation = None
    after = None
    if action == "delete":
        if before is None:
            raise DwError(f"orchestration score does not exist: {name}")
    else:
        if not isinstance(score, dict):
            raise DwError("orchestration save requires score as a JSON object")
        validation = validate_score(score)
        if validation["valid"]:
            normalized = validation["normalized"]
            if not isinstance(normalized, dict):
                raise DwError("valid orchestration score is missing normalized content")
            if normalized.get("slug") != name:
                raise DwError(
                    f"score name {name!r} must match its slug {normalized.get('slug')!r}"
                )
            compiled = compile_score(normalized)
            simulation = simulate_score(compiled)
            after = _render_score(normalized)
    fingerprint = _fingerprint(action, relative, before, after)
    return ScoreMutationPlan(
        root=root,
        action=action,
        name=name,
        target=target,
        relative_path=relative,
        before=before,
        after=after,
        validation=validation,
        compiled=compiled,
        simulation=simulation,
        fingerprint=fingerprint,
    )


def _decode(value: bytes | None) -> str:
    return "" if value is None else value.decode("utf-8", errors="replace")


def score_mutation_preview(plan: ScoreMutationPlan) -> dict[str, object]:
    before_text = _decode(plan.before)
    after_text = _decode(plan.after)
    diff = "".join(difflib.unified_diff(
        before_text.splitlines(keepends=True),
        after_text.splitlines(keepends=True),
        fromfile=f"a/{plan.relative_path}",
        tofile=f"b/{plan.relative_path}",
    ))
    valid = plan.action == "delete" or bool(plan.validation and plan.validation["valid"])
    return {
        "kind": SCORE_MUTATION_PREVIEW_KIND,
        "schema_version": SCORE_MUTATION_SCHEMA_VERSION,
        "action": plan.action,
        "name": plan.name,
        "path": plan.relative_path,
        "fingerprint": plan.fingerprint,
        "exists": plan.before is not None,
        "valid": valid,
        "applicable": valid,
        "no_op": plan.before == plan.after,
        "diff": diff,
        "bytes_before": len(plan.before or b""),
        "bytes_after": len(plan.after or b""),
        "validation": plan.validation,
        "compiled": plan.compiled,
        "simulation": plan.simulation,
        "starts_work": False,
        "writes_events": False,
    }


def _atomic_write(path: Path, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, raw_tmp = tempfile.mkstemp(prefix=f".{path.stem}.", suffix=".tmp", dir=str(path.parent))
    tmp = Path(raw_tmp)
    try:
        os.fchmod(fd, 0o644)
        with os.fdopen(fd, "wb") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(str(tmp), str(path))
    except Exception:
        try:
            tmp.unlink()
        except OSError:
            pass
        raise


def _restore(path: Path, before: bytes | None) -> None:
    if before is None:
        try:
            path.unlink()
        except FileNotFoundError:
            pass
    else:
        _atomic_write(path, before)


def apply_score_mutation(plan: ScoreMutationPlan, expected_fingerprint: str) -> dict[str, object]:
    """Apply one fresh valid plan and verify/rollback the resulting score."""
    if expected_fingerprint != plan.fingerprint:
        raise DwError("stale orchestration preview: score bytes or desired content changed")
    if plan.action == "save" and not (plan.validation and plan.validation["valid"]):
        raise DwError("invalid orchestration scores cannot be applied")
    plan.target.parent.mkdir(parents=True, exist_ok=True)
    lock_path = plan.target.parent / f".{plan.name}.edit.lock"
    try:
        lock_fd = os.open(str(lock_path), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError as exc:
        raise DwError("orchestration score is being edited by another apply") from exc
    except OSError as exc:
        raise DwError(f"cannot claim orchestration score edit lock: {exc}") from exc
    os.close(lock_fd)
    try:
        if _read_optional(plan.target) != plan.before:
            raise DwError("stale orchestration preview: score bytes changed before apply")
        if plan.before == plan.after:
            return {
                "kind": SCORE_MUTATION_RESULT_KIND,
                "schema_version": SCORE_MUTATION_SCHEMA_VERSION,
                "action": plan.action,
                "name": plan.name,
                "path": plan.relative_path,
                "fingerprint": plan.fingerprint,
                "applied": True,
                "changed": False,
                "rolled_back": False,
                "semantic_hash": plan.compiled.get("semantic_hash") if plan.compiled else None,
                "starts_work": False,
                "writes_events": False,
            }
        if plan.action == "delete":
            plan.target.unlink()
        else:
            if plan.after is None:
                raise DwError("save plan has no normalized content")
            _atomic_write(plan.target, plan.after)
            # The read-back compile is the post-write invariant. It catches
            # storage corruption and ensures browser and runtime see the same score.
            reread = compile_score(load_score(plan.target))
            if reread["document_hash"] != plan.compiled["document_hash"]:  # type: ignore[index]
                raise DwError("saved orchestration score does not match the previewed document hash")
    except Exception as exc:
        if isinstance(exc, DwError) and exc.message.startswith("stale orchestration preview"):
            raise
        try:
            _restore(plan.target, plan.before)
        except Exception as rollback_exc:
            raise DwError(
                f"orchestration apply failed ({exc}) and rollback failed ({rollback_exc})"
            ) from exc
        if isinstance(exc, DwError):
            raise DwError(f"orchestration apply failed and was rolled back: {exc.message}") from exc
        raise DwError(f"orchestration apply failed and was rolled back: {exc}") from exc
    else:
        return {
            "kind": SCORE_MUTATION_RESULT_KIND,
            "schema_version": SCORE_MUTATION_SCHEMA_VERSION,
            "action": plan.action,
            "name": plan.name,
            "path": plan.relative_path,
            "fingerprint": plan.fingerprint,
            "applied": True,
            "changed": True,
            "rolled_back": False,
            "semantic_hash": plan.compiled.get("semantic_hash") if plan.compiled else None,
            "starts_work": False,
            "writes_events": False,
        }
    finally:
        try:
            lock_path.unlink()
        except FileNotFoundError:
            pass
