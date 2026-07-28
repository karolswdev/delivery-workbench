"""Guarded, atomic application of front-door setup proposals."""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import tempfile
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any

from .gitio import current_branch, head_sha, run_git, run_git_bytes
from .model import DwError, Project
from .orchestration_driver import (
    DRIVER_CONFIG_KIND,
    DRIVER_SCHEMA_VERSION,
    driver_config_path,
    validate_driver_config,
)
from .parse import discover_projects
from .paths import read_text, rel, roadmap_dir, slugify
from .repofacts import git_dir
from .setup_proposal import canonical_json as canonical_proposal_json
from .setup_proposal import load_proposal, transition_state, validate_proposal

SETUP_PREVIEW_KIND = "delivery-workbench-setup-preview"
SETUP_APPLY_KIND = "delivery-workbench-setup-apply"
SETUP_SCHEMA_VERSION = 1
_SETUP_TOKEN_PREFIX = "setup-sha256:"
_SETUP_ID_PREFIX = "setup:"
_SAFE_POLICY_SLUG = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}$")
_POLICY_DIRS = ("programs", "workflows", "organizations", "rubrics")


@dataclass(frozen=True)
class SetupChange:
    path: Path
    relative_path: str
    tracked: bool
    before: bytes | None
    after: bytes


def _canonical(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)


def _hash(data: bytes | None) -> str | None:
    return None if data is None else "sha256:" + hashlib.sha256(data).hexdigest()


def _read_optional(path: Path) -> bytes | None:
    try:
        return path.read_bytes()
    except FileNotFoundError:
        return None


def _json_bytes(value: object) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False, allow_nan=False) + "\n").encode("utf-8")


def _lease_dir(root: Path) -> Path:
    return git_dir(root) / "pmo-setup-leases"


def _claims_generation(root: Path) -> str:
    claims = _lease_dir(root) / "claims"
    names = sorted(path.name for path in claims.glob("*.claim")) if claims.is_dir() else []
    return "sha256:" + hashlib.sha256("\n".join(names).encode("utf-8")).hexdigest()


def _repository_identity(root: Path) -> str:
    common = (run_git(root, "rev-parse", "--git-common-dir") or "").strip()
    common_path = Path(common)
    if common and not common_path.is_absolute():
        common_path = (root / common_path).resolve()
    facts = {"root": str(root.resolve()), "git_common_dir": str(common_path)}
    return "sha256:" + hashlib.sha256(_canonical(facts).encode("utf-8")).hexdigest()


def _snapshot_tree(base: Path) -> list[dict[str, object]]:
    if not base.exists():
        return []
    rows: list[dict[str, object]] = []
    for path in sorted((item for item in base.rglob("*") if item.is_file()), key=lambda item: str(item)):
        rows.append({"path": str(path.relative_to(base)).replace(os.sep, "/"), "hash": _hash(path.read_bytes())})
    return rows


def _observed_state(root: Path) -> dict[str, object]:
    roadmap = roadmap_dir(root)
    policy = root / "pm"
    index_bytes = run_git_bytes(root, "ls-files", "--stage", "-z")
    return {
        "repository_identity": _repository_identity(root),
        "branch": current_branch(root),
        "head": head_sha(root),
        "index_tree": _hash(index_bytes),
        "roadmap": _snapshot_tree(roadmap),
        "policy": {
            name: _snapshot_tree(policy / name)
            for name in _POLICY_DIRS
        },
        "driver_roster": _hash(_read_optional(driver_config_path(root))),
    }


def _render_story(project: dict[str, object], phase_number: int, number: int, story: dict[str, object], id_map: dict[str, str]) -> bytes:
    story_id = "%s-%d-%02d" % (project["prefix"], phase_number, number)
    dependencies = [id_map.get(str(item["id_sketch"]), str(item["id_sketch"])) for item in story["dependencies"]]  # type: ignore[index]
    depends = ", ".join(dependencies) if dependencies else "none"
    scope_in = "\n".join("- %s" % item["text"] for item in story["scope_in"]) or "- None."
    scope_out = "\n".join("- %s" % item["text"] for item in story["scope_out"]) or "- None."
    criteria = "\n".join("- [ ] %s" % item["text"] for item in story["acceptance_criteria"])
    text = f"""# {story_id} - {story['title']}

- **Project:** {project['slug']}
- **Phase:** {phase_number}
- **Status:** backlog
- **Depends on:** {depends}
- **Unblocks:** (optional)
- **Owner:** unassigned

## Problem

{story['problem']}

## Scope

### In

{scope_in}

### Out

{scope_out}

## Acceptance criteria

{criteria}

## Test plan

- **Unit:** n/a.
- **Integration:** n/a.
- **Manual / device:** n/a.

## Notes / open questions

Drafted through the front-door setup proposal.
"""
    return text.encode("utf-8")


def _render_phase(project: dict[str, object], phase: dict[str, object], story_rows: list[str]) -> bytes:
    text = f"""# Phase {phase['number']} - {phase['title']}

**Last updated:** {date.today().isoformat()}.

## Goal

{phase['goal']}

## Scope

- **In:** The stories listed in this phase.
- **Out:** Work not named by those stories.

## Exit criteria (evidence required)

- [ ] Every story below is done with evidence.

## Story status

| ID | Story | Status | Story file | Evidence |
|---|---|---|---|---|
{chr(10).join(story_rows)}

## Where we are

This phase was configured through one reviewed setup proposal.

## Active risks

| Risk | Likelihood | Mitigation | Stop signal |
|---|---|---|---|

## Decisions made (this phase)

- {date.today().isoformat()} - Phase configured by guarded setup apply - one atomic setup act - CLI, MCP, or HTTP.

## Decisions deferred

- None recorded.
"""
    return text.encode("utf-8")


def _merge_phase_rows(readme: str, phases: list[dict[str, object]]) -> bytes:
    lines = readme.splitlines()
    header = "| Phase | Goal (one line) | Status | Folder |"
    try:
        header_index = lines.index(header)
    except ValueError as exc:
        raise DwError("existing project README has no contracted phase index") from exc
    start = header_index + 2
    end = start
    rows: list[tuple[int, str]] = []
    numbers: set[int] = set()
    while end < len(lines) and lines[end].startswith("|"):
        cells = [cell.strip() for cell in lines[end].strip().strip("|").split("|")]
        try:
            number = int(cells[0])
        except (IndexError, ValueError) as exc:
            raise DwError("existing project README has a malformed phase index") from exc
        rows.append((number, lines[end]))
        numbers.add(number)
        end += 1
    for phase in phases:
        number = int(phase["number"])
        if number in numbers:
            raise DwError("setup phase %d already exists in the project README" % number)
        dirname = "phase-%s-%s" % (number, slugify(str(phase["title"])))
        rows.append((number, "| %s | %s | planned | [%s](./%s/) |" % (number, phase["goal"], dirname, dirname)))
        numbers.add(number)
    lines[start:end] = [row for _number, row in sorted(rows)]
    return ("\n".join(lines) + "\n").encode("utf-8")


def _render_project_readme(project: dict[str, object], phases: list[dict[str, object]], exit_criteria: list[dict[str, object]]) -> bytes:
    first = phases[0]
    first_dir = "phase-%s-%s" % (first["number"], slugify(str(first["title"])))
    rows = []
    for phase in phases:
        dirname = "phase-%s-%s" % (phase["number"], slugify(str(phase["title"])))
        rows.append("| %s | %s | planned | [%s](./%s/) |" % (phase["number"], phase["goal"], dirname, dirname))
    exits = "\n".join("- [ ] %s" % item["text"] for item in exit_criteria)
    text = f"""# {project['title']} - Roadmap

**Last updated:** {date.today().isoformat()}.
**Current phase:** [{first_dir}](./{first_dir}/current-phase-status.md).
**Status:** active.

## Vision

Configured from a reviewed front-door proposal.

## Exit criteria (evidence required)

{exits}

## Phase index

| Phase | Goal (one line) | Status | Folder |
|---|---|---|---|
{chr(10).join(rows)}

## Project metadata

- **Slug:** `{project['slug']}`
- **Story ID prefix:** {project['prefix']}
"""
    return text.encode("utf-8")


def _policy_target(root: Path, family: str, document: dict[str, object]) -> Path:
    slug = document.get("slug")
    if not isinstance(slug, str) or not _SAFE_POLICY_SLUG.fullmatch(slug):
        raise DwError("/tracked_content/policy/%s: embedded document needs a safe slug" % family)
    return root / "pm" / family / (slug + ".json")


def _driver_after(root: Path, bindings: dict[str, object]) -> bytes:
    current = _read_optional(driver_config_path(root))
    if current is None:
        raw: dict[str, Any] = {
            "kind": DRIVER_CONFIG_KIND,
            "schema_version": DRIVER_SCHEMA_VERSION,
            "workspace_root": None,
            "profiles": {},
        }
    else:
        try:
            raw = json.loads(current.decode("utf-8"))
        except (UnicodeError, json.JSONDecodeError) as exc:
            raise DwError("cannot parse local driver config: %s" % exc) from exc
    profiles = dict(raw.get("profiles") or {})
    for name, binding in sorted(bindings.items()):
        existing = profiles.get(name)
        if isinstance(existing, dict):
            # An operator's full profile is local configuration the
            # proposal may reference but never rewrite: verify the
            # binding names the same execution identity and keep the
            # profile untouched (capabilities, principal, and bounds
            # stay exactly as the operator wrote them).
            for field in ("adapter", "model", "provider"):
                if existing.get(field) != binding[field]:
                    raise DwError(
                        "/local_content/driver_bindings/%s/%s: existing local "
                        "profile disagrees with the proposal binding" % (name, field)
                    )
            continue
        profiles[name] = {
            "adapter": binding["adapter"],
            "model": binding["model"],
            "provider": binding["provider"],
        }
    raw["profiles"] = profiles
    return _json_bytes(validate_driver_config(raw))


def build_setup_plan(
    root: Path,
    proposal: dict[str, object],
    *,
    require_reviewed: bool = True,
) -> list[SetupChange]:
    """Build every tracked and git-local write without mutating the repository.

    The reviewed-state gate belongs to lease minting: a preview is the
    step after a human reviewed the draft. The adoption-review view
    passes ``require_reviewed=False`` because a draft is exactly what a
    human reviews — the plan stays a pure read either way.
    """
    proposal = validate_proposal(proposal)
    if require_reviewed and proposal["state"] != "reviewed":
        raise DwError("/state: setup preview requires a reviewed proposal")
    project = proposal["project"]
    slug = str(project["slug"])
    if slug in {"preview", "apply"}:
        raise DwError("/project/slug: preview and apply are reserved setup subverbs")
    projects = [item for item in discover_projects(root) if item.slug == slug]
    mode = proposal["source_intent"]["mode"]
    if mode == "build" and projects:
        raise DwError("/project/slug: build proposal project already exists")
    if mode == "maintain" and len(projects) != 1:
        raise DwError("/project/slug: maintain proposal must name one existing project")
    if projects and projects[0].prefix != project["prefix"]:
        raise DwError("/project/prefix: does not match the existing project prefix")

    roadmap = proposal["tracked_content"]["roadmap"]
    phases = roadmap["phases"]
    project_dir = roadmap_dir(root) / slug
    desired: dict[Path, tuple[bytes, bool, bool]] = {}
    readme = project_dir / "README.md"
    if readme.exists():
        desired[readme] = (_merge_phase_rows(read_text(readme), phases), True, True)
    else:
        desired[readme] = (_render_project_readme(project, phases, roadmap["exit_criteria"]), True, False)

    id_map: dict[str, str] = {}
    for phase in phases:
        for index, story in enumerate(phase["stories"], 1):
            id_map[str(story["id_sketch"])] = "%s-%d-%02d" % (project["prefix"], phase["number"], index)
    for phase in phases:
        phase_dir = project_dir / ("phase-%s-%s" % (phase["number"], slugify(str(phase["title"]))))
        rows: list[str] = []
        for index, story in enumerate(phase["stories"], 1):
            story_slug = slugify(str(story["title"]))
            filename = "story-%02d-%s.md" % (index, story_slug)
            story_id = "%s-%d-%02d" % (project["prefix"], phase["number"], index)
            rows.append("| %s | %s | backlog | [%s](./%s) | - |" % (story_id, story["title"], filename[:-3], filename))
            desired[phase_dir / filename] = (_render_story(project, int(phase["number"]), index, story, id_map), True, False)
        desired[phase_dir / "current-phase-status.md"] = (_render_phase(project, phase, rows), True, False)

    policy = proposal["tracked_content"]["policy"]
    if policy is not None:
        program_doc = policy["program"]["document"]
        desired[_policy_target(root, "programs", program_doc)] = (_json_bytes(program_doc), True, False)
        organization_doc = policy["organization"]["document"]
        desired[_policy_target(root, "organizations", organization_doc)] = (_json_bytes(organization_doc), True, False)
        for wrapper in policy["workflows"]:
            document = wrapper["document"]
            desired[_policy_target(root, "workflows", document)] = (_json_bytes(document), True, False)
        for wrapper in policy["rubrics"]:
            document = wrapper["document"]
            desired[_policy_target(root, "rubrics", document)] = (_json_bytes(document), True, False)

    roster = driver_config_path(root)
    desired[roster] = (_driver_after(root, proposal["local_content"]["driver_bindings"]), False, True)
    changes: list[SetupChange] = []
    for path, (after, tracked, allow_update) in sorted(desired.items(), key=lambda item: str(item[0])):
        before = _read_optional(path)
        if before is not None and before != after and not allow_update:
            raise DwError("setup target already exists with different content: %s" % rel(path, root))
        changes.append(SetupChange(path, rel(path, root) if tracked else ".git/pmo-orchestration/drivers.json", tracked, before, after))
    return changes


def setup_plan_facts(
    proposal: dict[str, object], changes: list[SetupChange]
) -> dict[str, object]:
    """Return the non-authorizing facts shared by preview and review views."""
    proposal_bytes = canonical_proposal_json(proposal).encode("utf-8")
    return {
        "proposal_hash": _hash(proposal_bytes),
        "changes": [{
            "path": change.relative_path,
            "scope": "tracked" if change.tracked else "git-local",
            "before_hash": _hash(change.before),
            "after_hash": _hash(change.after),
            "action": (
                "create" if change.before is None
                else "unchanged" if change.before == change.after
                else "update"
            ),
        } for change in changes],
    }


def _proposal_id(proposal_hash: str) -> str:
    return _SETUP_ID_PREFIX + proposal_hash.removeprefix("sha256:")


def _preview_document(root: Path, proposal: dict[str, object], changes: list[SetupChange]) -> dict[str, object]:
    facts = setup_plan_facts(proposal, changes)
    proposal_hash = facts["proposal_hash"]
    observed = _observed_state(root)
    change_rows = facts["changes"]
    token_facts = {
        "type": "setup-lease",
        "proposal_hash": proposal_hash,
        "observed": observed,
        "changes": change_rows,
        "claims_generation": _claims_generation(root),
    }
    expect = _SETUP_TOKEN_PREFIX + hashlib.sha256(_canonical(token_facts).encode("utf-8")).hexdigest()
    return {
        "kind": SETUP_PREVIEW_KIND,
        "schema_version": SETUP_SCHEMA_VERSION,
        "proposal_id": _proposal_id(str(proposal_hash)),
        "proposal_hash": proposal_hash,
        "expect": expect,
        "applicable": True,
        "diagnostics": [],
        "observed": observed,
        "changes": change_rows,
        "starts_work": False,
        "creates_grant": False,
        "certifies": False,
        "commits": False,
    }


def canonical_setup_preview(preview: dict[str, object]) -> str:
    return _canonical(preview)


def preview_setup(root: Path, proposal_file: Path) -> dict[str, object]:
    try:
        proposal = load_proposal(proposal_file.read_bytes())
    except OSError as exc:
        raise DwError("setup proposal cannot be read: %s" % exc) from exc
    changes = build_setup_plan(root, proposal)
    preview = _preview_document(root, proposal, changes)
    storage = _lease_dir(root) / "pending"
    storage.mkdir(parents=True, exist_ok=True, mode=0o700)
    record = {
        "preview": preview,
        "proposal": proposal,
        "changes": [{
            "path": change.relative_path,
            "actual_path": str(change.path),
            "tracked": change.tracked,
            "before_hash": _hash(change.before),
            "after": change.after.decode("utf-8"),
        } for change in changes],
    }
    target = storage / (str(preview["proposal_id"]).removeprefix(_SETUP_ID_PREFIX) + ".json")
    _atomic_json(target, record)
    return preview


def _atomic_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    fd, temporary = tempfile.mkstemp(prefix=".setup.", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(_canonical(value) + "\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(temporary, 0o600)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def _claim(root: Path, expect: str) -> None:
    if not expect.startswith(_SETUP_TOKEN_PREFIX):
        raise DwError("wrong token type: setup apply requires a setup-sha256 token")
    claims = _lease_dir(root) / "claims"
    claims.mkdir(parents=True, exist_ok=True, mode=0o700)
    path = claims / (expect.removeprefix(_SETUP_TOKEN_PREFIX) + ".claim")
    try:
        with path.open("x", encoding="utf-8") as handle:
            handle.write("claimed\n")
    except FileExistsError as exc:
        raise DwError("setup lease was already used") from exc


def _apply_transaction(root: Path, changes: list[dict[str, object]], fail_after: int | None = None) -> None:
    journal_root = _lease_dir(root) / "journal"
    journal_root.mkdir(parents=True, exist_ok=True, mode=0o700)
    journal = Path(tempfile.mkdtemp(prefix="apply-", dir=str(journal_root)))
    originals: list[tuple[Path, Path | None, int | None]] = []
    created_dirs: list[Path] = []
    try:
        for index, change in enumerate(changes):
            target = Path(str(change["actual_path"]))
            before = _read_optional(target)
            if _hash(before) != change.get("before_hash"):
                raise DwError("stale setup lease: target changed before transaction: %s" % change.get("path"))
            backup = None
            mode = None
            if before is not None:
                backup = journal / ("before-%04d" % index)
                backup.write_bytes(before)
                mode = target.stat().st_mode & 0o777
            originals.append((target, backup, mode))
        _atomic_json(journal / "journal.json", {"state": "prepared", "paths": [str(item[0]) for item in originals]})
        original_modes = {target: mode for target, _backup, mode in originals}
        for index, change in enumerate(changes, 1):
            target = Path(str(change["actual_path"]))
            missing: list[Path] = []
            parent = target.parent
            while not parent.exists():
                missing.append(parent)
                parent = parent.parent
            target.parent.mkdir(parents=True, exist_ok=True)
            created_dirs.extend(reversed(missing))
            fd, temporary = tempfile.mkstemp(prefix=".dw-setup.", dir=str(target.parent))
            try:
                content = str(change["after"]).encode("utf-8")
                with os.fdopen(fd, "wb") as handle:
                    handle.write(content)
                    handle.flush()
                    os.fsync(handle.fileno())
                os.replace(temporary, target)
                os.chmod(target, original_modes.get(target) or (0o644 if change.get("tracked") else 0o600))
            finally:
                if os.path.exists(temporary):
                    os.unlink(temporary)
            if fail_after is not None and index >= fail_after:
                raise DwError("planted setup transaction failure after write %d" % index)
        _atomic_json(journal / "journal.json", {"state": "committed"})
    except Exception as exc:
        rollback_error: Exception | None = None
        for target, backup, mode in reversed(originals):
            try:
                if backup is None:
                    if target.exists():
                        target.unlink()
                else:
                    target.parent.mkdir(parents=True, exist_ok=True)
                    data = backup.read_bytes()
                    fd, temporary = tempfile.mkstemp(prefix=".dw-rollback.", dir=str(target.parent))
                    with os.fdopen(fd, "wb") as handle:
                        handle.write(data)
                        handle.flush()
                        os.fsync(handle.fileno())
                    os.replace(temporary, target)
                    if mode is not None:
                        os.chmod(target, mode)
            except Exception as restore_exc:
                rollback_error = restore_exc
        for directory in reversed(created_dirs):
            try:
                directory.rmdir()
            except OSError:
                pass
        if rollback_error is not None:
            raise DwError("setup apply failed and rollback failed: %s" % rollback_error) from exc
        raise
    finally:
        shutil.rmtree(journal, ignore_errors=True)


def apply_setup(root: Path, proposal_id: str, expect: str, *, fail_after: int | None = None) -> dict[str, object]:
    if not proposal_id.startswith(_SETUP_ID_PREFIX):
        raise DwError("unknown setup proposal id")
    record_path = _lease_dir(root) / "pending" / (proposal_id.removeprefix(_SETUP_ID_PREFIX) + ".json")
    try:
        record = json.loads(record_path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError) as exc:
        raise DwError("unknown setup proposal id") from exc
    preview = record.get("preview")
    if not isinstance(preview, dict) or preview.get("proposal_id") != proposal_id:
        raise DwError("unknown setup proposal id")
    if not expect.startswith(_SETUP_TOKEN_PREFIX):
        raise DwError("wrong token type: setup apply requires a setup-sha256 token")
    if expect != preview.get("expect"):
        raise DwError("stale setup lease: exact expect token does not match the proposal")
    claim_path = _lease_dir(root) / "claims" / (expect.removeprefix(_SETUP_TOKEN_PREFIX) + ".claim")
    if claim_path.exists():
        raise DwError("setup lease was already used")
    if _observed_state(root) != preview.get("observed"):
        raise DwError("stale setup lease: repository, branch, HEAD, index, roadmap, policy, or roster changed")
    proposal = validate_proposal(record.get("proposal"))
    fresh_plan = build_setup_plan(root, proposal)
    fresh_preview = _preview_document(root, proposal, fresh_plan)
    if fresh_preview != preview:
        raise DwError("stale or corrupt setup lease: proposal, paths, or desired content changed")
    changes = [{
        "path": change.relative_path,
        "actual_path": str(change.path),
        "tracked": change.tracked,
        "before_hash": _hash(change.before),
        "after": change.after.decode("utf-8"),
    } for change in fresh_plan]
    configured = transition_state(proposal["state"], "configured")
    _claim(root, expect)
    planted = fail_after
    if planted is None and os.environ.get("DW_SETUP_FAIL_AFTER"):
        try:
            planted = int(os.environ["DW_SETUP_FAIL_AFTER"])
        except ValueError as exc:
            raise DwError("DW_SETUP_FAIL_AFTER must be an integer") from exc
    _apply_transaction(root, changes, fail_after=planted)
    proposal["state"] = configured
    record["proposal"] = proposal
    record["journey_state"] = configured
    record["applied"] = True
    _atomic_json(record_path, record)
    return {
        "kind": SETUP_APPLY_KIND,
        "schema_version": SETUP_SCHEMA_VERSION,
        "proposal_id": proposal_id,
        "expect": expect,
        "outcome": "applied",
        "journey_state": configured,
        "changed": [change["path"] for change in changes],
        "starts_work": False,
        "creates_grant": False,
        "certifies": False,
        "commits": False,
    }
