"""Pure Phase-26 program policy compilation and roadmap planning.

This planning layer deliberately stops before grants or execution.  It reads a
tracked program plus its referenced policy documents, validates the explicit
roadmap scope and binding rules, derives one stable frontier selection, and
uses the organization compiler to assign capability- and visibility-bounded
team roles against the existing local driver roster.  It never creates a
program store, grant, ledger, observer, workspace, or roadmap write.

The contract is ``docs/programs.md`` (WLA-26-01/02/03/04).
"""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any

from .gitio import current_branch, head_sha, in_rewrite_state, write_tree
from .grounding import (
    ground_story_path,
    grounding_refusal,
    parse_localization_hints,
)
from .model import (
    CUT_STATUSES,
    DONE_STATUSES,
    HOLD_STATUSES,
    STORY_STATUSES,
    DwError,
    normalize_status,
)
from .orchestration import NUDGE_SIGNALS, canonical_json
from .orchestration_driver import (
    driver_config_path,
    driver_inventory,
    load_driver_config,
    validate_driver_config,
)
from .program_organization import (
    DUTIES,
    ORGANIZATION_KIND,
    OrganizationValidationError,
    assign_organization_team,
    compile_organization,
    validate_workflow_team,
)
from .program_workflow import (
    NODE_TYPES,
    WorkflowValidationError,
    compile_workflow,
)
from .program_verdict import (
    RUBRIC_KIND,
    RubricValidationError,
    compile_rubric,
)
from .parse import (
    discover_phases,
    discover_projects,
    link_target,
    parse_story_rows,
    phase_header_status,
    split_table_row,
)
from .paths import read_text
from .validate import check_project, project_warnings


PROGRAM_KIND = "delivery-workbench-program"
PROGRAM_SCHEMA_VERSION = 1
WORKFLOW_KIND = "delivery-workbench-workflow"

VALIDATION_KIND = "delivery-workbench-program-validation"
COMPILED_KIND = "delivery-workbench-compiled-program"
INVENTORY_KIND = "delivery-workbench-program-list"
SIMULATION_KIND = "delivery-workbench-program-simulation"
PLAN_KIND = "delivery-workbench-program-plan"

MODE_CEILINGS = ("advisory", "checkpointed", "continuous")
SELECTION_POLICIES = ("roadmap-frontier-v1",)
BLOCKED_POLICIES = ("stop",)

PROGRAM_CAPABILITIES = (
    "program:select",
    "agent:dispatch",
    "check:execute",
    "workspace:write",
    "verdict:issue",
    "council:decide",
    "obligation:record",
    "obligation:materialize",
    "obligation:disposition",
    "nudge:deliver",
    "notification:send",
    "evidence:materialize",
    "knowledge:lesson-writeback",
    "integration:apply",
    "contract:generate",
    "certification:objective",
    "certification:verdict",
    "git:commit",
    "git:push",
    "roadmap:story-start",
    "roadmap:story-complete",
    "roadmap:phase-advance",
)

BUDGET_DEFAULTS = {
    "max_phases": 1,
    "max_stories": 20,
    "max_child_runs": 100,
    "max_agent_starts": 200,
    "max_provider_starts": 200,
    "max_model_starts": 200,
    "max_check_starts": 500,
    "max_loop_rounds": 100,
    "max_debate_rounds": 20,
    "max_councils": 20,
    "max_repairs_per_story": 3,
    "max_verdicts": 200,
    "max_obligations": 200,
    "max_obligation_materializations": 50,
    "max_obligation_dispositions": 200,
    "max_integrations": 20,
    "max_commits": 20,
    "max_pushes": 20,
    "max_nudges": 50,
    "max_lesson_writebacks": 5,
    "max_lessons": 5,
    "max_artifact_bytes": 50_000_000,
    "max_tokens": 20_000_000,
    "max_observed_cost_microunits": 1_000_000_000,
    "max_wall_seconds": 172_800,
}
BUDGET_LIMITS = {
    "max_phases": 100,
    "max_stories": 2_000,
    "max_child_runs": 20_000,
    "max_agent_starts": 50_000,
    "max_provider_starts": 50_000,
    "max_model_starts": 50_000,
    "max_check_starts": 100_000,
    "max_loop_rounds": 20_000,
    "max_debate_rounds": 2_000,
    "max_councils": 2_000,
    "max_repairs_per_story": 100,
    "max_verdicts": 50_000,
    "max_obligations": 50_000,
    "max_obligation_materializations": 10_000,
    "max_obligation_dispositions": 50_000,
    "max_integrations": 2_000,
    "max_commits": 2_000,
    "max_pushes": 2_000,
    "max_nudges": 10_000,
    "max_lesson_writebacks": 10_000,
    "max_lessons": 50,
    "max_artifact_bytes": 10_000_000_000,
    "max_tokens": 10_000_000_000,
    "max_observed_cost_microunits": 10_000_000_000_000,
    "max_wall_seconds": 31_536_000,
}

STOP_CONDITIONS = (
    "scope-complete",
    "checkpoint-required",
    "unresolved-dissent",
    "architect-veto",
    "blocked-frontier",
    "budget-exhausted",
    "grant-expired",
    "grant-revoked",
)

_SAFE_ID_RE = re.compile(r"^[a-z][a-z0-9]*(?:[-_][a-z0-9]+)*$")
_STORY_ID_RE = re.compile(r"^[A-Z][A-Z0-9]*-\d+-\d+$")
_DEPENDENCY_RE = re.compile(r"[A-Z][A-Z0-9]*-\d+-\d+")

_PROGRAM_KEYS = {
    "kind", "schema_version", "slug", "title", "description", "scope",
    "organization", "bindings", "phase_gates", "nudges", "mode_ceiling",
    "requested_capabilities", "budgets", "stop_conditions", "layout",
}
_SCOPE_KEYS = {
    "project", "phases", "stories", "selection", "blocked_policy",
}
_PHASE_RANGE_KEYS = {"from", "through"}
_PHASE_INCLUDE_KEYS = {"include"}
_STORY_SELECTOR_KEYS = {"include"}
_BINDING_KEYS = {"id", "priority", "match", "workflow", "with", "team", "rubrics"}
_MATCH_KEYS = {"phase_from", "phase_through", "story_ids"}
_PHASE_GATE_KEYS = {"id", "when", "role", "rubric", "on_fail"}
_PROGRAM_NUDGE_KEYS = {
    "id", "signal", "binding", "target", "max_per_signal", "max_total",
    "expectation",
}
_PROGRAM_NUDGE_SIGNALS = tuple(
    signal for signal in NUDGE_SIGNALS if signal != "waiting-input-timeout"
)
_WORKFLOW_TARGET_RE = re.compile(
    r"^[a-z][a-z0-9]*(?:[-_][a-z0-9]+)*(?:/[a-z][a-z0-9]*(?:[-_][a-z0-9]+)*)*$"
)

_WORKFLOW_KEYS = {
    "kind", "schema_version", "slug", "title", "description", "version",
    "parameters", "defaults", "nodes", "terminals", "layout",
}
_RUBRIC_KEYS = {
    "kind", "schema_version", "slug", "title", "description", "version",
    "subject_type", "result_vocabulary", "freshness", "criteria",
    "aggregation", "layout",
}
_LOCAL_DRIVER_ROSTER = object()
_DRIVER_ROSTER_SOURCE = ".git/pmo-orchestration/drivers.json"
_TRACKED_EXECUTABLE_KEYS = frozenset({"binary", "command", "executable"})
_TRACKED_ARGV_KEYS = frozenset({"args", "arguments", "argv"})
_TRACKED_ENVIRONMENT_KEYS = frozenset({
    "env", "environment", "environment-variables", "environment_variables",
})
_TRACKED_DRIVER_FLAG_KEYS = frozenset({
    "adapter_flags", "cli_flags", "driver-flags", "driver_flags", "flags",
})
_SENSITIVE_DIAGNOSTIC_VALUE_RE = re.compile(
    r"(?:secret|token|credential|password|api[_-]?key|bearer|sk-[A-Za-z0-9])",
    re.I,
)


class ProgramValidationError(DwError):
    """A deterministic validation refusal with all diagnostics attached."""

    def __init__(self, diagnostics: list[dict[str, str]]) -> None:
        self.diagnostics = diagnostics
        first = diagnostics[0] if diagnostics else {
            "source": "program", "pointer": "/", "message": "program is invalid",
        }
        super().__init__(
            "program invalid at "
            f"{first['source']}:{first['pointer']}: {first['message']}"
        )


class _DuplicateJSONKey(ValueError):
    pass


def _object_without_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise _DuplicateJSONKey(f"duplicate JSON object key: {key}")
        result[key] = value
    return result


def _sha(value: object) -> str:
    return "sha256:" + hashlib.sha256(
        canonical_json(value).encode("utf-8")
    ).hexdigest()


def parse_program_text(text: str, source: str = "program") -> dict[str, object]:
    """Parse policy JSON while refusing duplicate keys and non-finite values."""
    try:
        value = json.loads(
            text,
            object_pairs_hook=_object_without_duplicates,
            parse_constant=lambda token: (_ for _ in ()).throw(
                ValueError(f"non-finite JSON number: {token}")
            ),
        )
    except (_DuplicateJSONKey, json.JSONDecodeError, ValueError) as exc:
        raise DwError(f"cannot parse program policy {source}: {exc}") from exc
    if not isinstance(value, dict):
        raise DwError(f"program policy {source} must be a JSON object")
    return value


def load_program(path: Path) -> dict[str, object]:
    try:
        return parse_program_text(path.read_text(encoding="utf-8"), str(path))
    except OSError as exc:
        raise DwError(f"cannot read program policy {path}: {exc}") from exc


def _pointer_part(value: object) -> str:
    return str(value).replace("~", "~0").replace("/", "~1")


_SANCTIONED_RUNNER_KEYS = {"kind", "argv", "cwd", "writes", "output_bytes"}


def _is_sanctioned_check_runner(value: object) -> bool:
    """The one legal command shape in tracked policy: a check node's runner.

    The orchestration contract sanctions exactly one command channel —
    a check node's ``runner`` carrying exact tokenized argv from the
    reviewed score (no shell-string mode, no environment, no extra
    keys). The Phase 29 exit-exam bundle runs its declared regression
    command through precisely this shape and the conductor's baseline
    subtraction depends on it, so validation must accept the conforming
    form and refuse every deviation, not blanket-refuse the channel.
    """
    if not isinstance(value, dict) or value.get("kind") != "command":
        return False
    if not set(value).issubset(_SANCTIONED_RUNNER_KEYS):
        return False
    argv = value.get("argv")
    if not isinstance(argv, list) or not argv:
        return False
    if any(not isinstance(item, str) or not item for item in argv):
        return False
    writes = value.get("writes", [])
    if not isinstance(writes, list) or any(not isinstance(item, str) for item in writes):
        return False
    return isinstance(value.get("cwd", "."), str)


def _tracked_policy_controls(
    value: object,
    *,
    source: str,
    pointer: str = "",
) -> list[dict[str, str]]:
    """Reject local execution controls wherever tracked bundle data hides them."""
    diagnostics: list[dict[str, str]] = []
    if isinstance(value, dict):
        if (
            value.get("type") == "check"
            and _is_sanctioned_check_runner(value.get("runner"))
        ):
            rest = {key: item for key, item in value.items() if key != "runner"}
            return _tracked_policy_controls(rest, source=source, pointer=pointer)
        if value.get("kind") == "command":
            diagnostics.append({
                "source": source,
                "pointer": f"{pointer}/kind" or "/kind",
                "code": "tracked-executable",
                "message": "tracked program policy cannot select a command executable",
                "remediation": "replace the command runner with a closed built-in check",
            })
        for key, item in sorted(value.items(), key=lambda pair: str(pair[0])):
            item_pointer = f"{pointer}/{_pointer_part(key)}"
            key_text = str(key)
            if key_text in _TRACKED_EXECUTABLE_KEYS:
                diagnostics.append({
                    "source": source,
                    "pointer": item_pointer,
                    "code": "tracked-executable",
                    "message": "tracked program policy cannot name a local executable",
                    "remediation": "move executable selection to the local driver roster or use a closed built-in rail",
                })
            elif key_text in _TRACKED_ARGV_KEYS:
                diagnostics.append({
                    "source": source,
                    "pointer": item_pointer,
                    "code": "tracked-argv",
                    "message": "tracked program policy cannot supply arbitrary argv",
                    "remediation": "use a closed built-in check or keep adapter arguments in local driver code",
                })
            elif key_text in _TRACKED_ENVIRONMENT_KEYS:
                diagnostics.append({
                    "source": source,
                    "pointer": item_pointer,
                    "code": "tracked-environment",
                    "message": "tracked program policy cannot supply environment variables",
                    "remediation": "configure non-secret environment controls in the local adapter implementation",
                })
            elif key_text in _TRACKED_DRIVER_FLAG_KEYS:
                diagnostics.append({
                    "source": source,
                    "pointer": item_pointer,
                    "code": "tracked-driver-flags",
                    "message": "tracked program policy cannot supply driver flags",
                    "remediation": "remove the flags; only declared local adapter behavior may form driver argv",
                })
            diagnostics.extend(
                _tracked_policy_controls(
                    item, source=source, pointer=item_pointer,
                )
            )
    elif isinstance(value, list):
        for index, item in enumerate(value):
            diagnostics.extend(
                _tracked_policy_controls(
                    item, source=source, pointer=f"{pointer}/{index}",
                )
            )
    return diagnostics


def _redact_diagnostic_value(value: object) -> object:
    if isinstance(value, str):
        return (
            "[redacted]"
            if _SENSITIVE_DIAGNOSTIC_VALUE_RE.search(value) else value
        )
    if isinstance(value, list):
        return [_redact_diagnostic_value(item) for item in value]
    if isinstance(value, dict):
        return {
            str(key): _redact_diagnostic_value(item)
            for key, item in value.items()
        }
    return value


def _driver_roster_diagnostics(
    config: dict[str, object],
) -> dict[str, object]:
    inventory = driver_inventory(config)
    profiles = []
    for raw in inventory["profiles"]:
        profiles.append(_redact_diagnostic_value({
            "profile": raw["profile"],
            "available": raw["available"],
            "adapter": {
                "kind": raw["adapter"],
                "version": raw["adapter_version"],
            },
            "provider_family": raw["provider_family"],
            "capabilities": raw["capabilities"],
            "principal": raw["principal"],
            "workspace_modes": raw["workspace_modes"],
            "model": {
                "alias": raw["model"],
                "binding": raw["model_binding"],
                "revision": raw["model_revision"],
            },
        }))
    return {
        "status": "available",
        "source": _DRIVER_ROSTER_SOURCE,
        "profiles": profiles,
        "stores_credentials": False,
    }


def _policy_dir(root: Path, name: str) -> Path:
    root = root.resolve()
    path = (root / "pm" / name).resolve()
    if path != root and root not in path.parents:
        raise DwError(f"pm/{name} resolves outside the repository")
    return path


def _discover_json(root: Path, name: str) -> list[Path]:
    allowed = _policy_dir(root, name)
    if not allowed.is_dir():
        return []
    paths: list[Path] = []
    for candidate in sorted(allowed.glob("*.json"), key=lambda item: item.name):
        resolved = candidate.resolve()
        if resolved.parent != allowed:
            raise DwError(f"policy escapes pm/{name}: {candidate.name}")
        if resolved.is_file():
            paths.append(resolved)
    return paths


def discover_program_paths(root: Path) -> list[Path]:
    return _discover_json(root, "programs")


def find_program_path(root: Path, selector: str) -> Path:
    if not _SAFE_ID_RE.fullmatch(selector or ""):
        raise DwError(f"unsafe program selector: {selector!r}")
    paths = discover_program_paths(root)
    matches: list[Path] = []
    for path in paths:
        if path.stem == selector and path not in matches:
            matches.append(path)
        try:
            if load_program(path).get("slug") == selector and path not in matches:
                matches.append(path)
        except DwError:
            continue
    if not matches:
        raise DwError(f"program not found: {selector}")
    if len(matches) > 1:
        raise DwError(f"ambiguous program selector: {selector}")
    return matches[0]


def _reference_paths(root: Path, family: str) -> list[Path]:
    return _discover_json(root, family)


def _reference_by_slug(
    root: Path,
    family: str,
    slug: str,
) -> tuple[Path, dict[str, object]] | None:
    matches: list[tuple[Path, dict[str, object]]] = []
    for path in _reference_paths(root, family):
        try:
            raw = parse_program_text(path.read_text(encoding="utf-8"), str(path))
        except (DwError, OSError):
            continue
        if raw.get("slug") == slug or path.stem == slug:
            matches.append((path, raw))
    if len(matches) != 1:
        return None
    return matches[0]


def _phase_index_statuses(project_path: Path) -> dict[int, str]:
    """Read the project phase-index status column without owning a new dialect."""
    readme = project_path / "README.md"
    if not readme.is_file():
        return {}
    statuses: dict[int, str] = {}
    header: dict[str, int] | None = None
    for line in read_text(readme).splitlines():
        cells = split_table_row(line)
        if header is None:
            lowered = [cell.strip().lower() for cell in cells]
            if all(name in lowered for name in ("phase", "status", "folder")):
                header = {name: lowered.index(name) for name in ("phase", "status", "folder")}
            continue
        if not line.strip().startswith("|"):
            if statuses:
                break
            continue
        if not cells or all(set(cell) <= {"-", ":"} for cell in cells):
            continue
        try:
            number = int(re.sub(r"\D", "", cells[header["phase"]]))
        except (ValueError, IndexError):
            continue
        statuses[number] = normalize_status(cells[header["status"]])
    return statuses


def _story_dependencies(path: Path) -> list[str]:
    if not path.is_file():
        return []
    for line in read_text(path).splitlines():
        match = re.match(r"^- \*\*Depends on:\*\*\s*(.+)$", line)
        if not match:
            continue
        raw = match.group(1).strip()
        if raw.lower() in {"none", "n/a", "-"}:
            return []
        return _DEPENDENCY_RE.findall(raw)
    return []


def _project_story_inventory(project: object) -> list[dict[str, object]]:
    phase_statuses = _phase_index_statuses(project.path)  # type: ignore[attr-defined]
    stories: list[dict[str, object]] = []
    for phase in discover_phases(project):  # type: ignore[arg-type]
        phase_file = phase.path / "current-phase-status.md"
        phase_status = normalize_status(phase_header_status(phase_file))
        if not phase_status:
            phase_status = phase_statuses.get(phase.number, "")
        for order, row in enumerate(parse_story_rows(phase_file)):
            story_path = (phase.path / link_target(row.story_file)).resolve()
            stories.append({
                "id": row.story_id.replace("~~", "").strip(),
                "title": row.title,
                "phase": phase.number,
                "phase_slug": phase.path.name,
                "phase_status": phase_status,
                "order": order,
                "status": normalize_status(row.status),
                "status_raw": row.status,
                "story_path": str(story_path),
                "dependencies": _story_dependencies(story_path),
            })
    return stories


def _proposed_story_inventory(roadmap: dict[str, object]) -> list[dict[str, object]]:
    """Story rows for a proposal roadmap that has not been applied yet."""
    stories: list[dict[str, object]] = []
    for phase in roadmap.get("phases", []):
        if not isinstance(phase, dict):
            continue
        for order, story in enumerate(phase.get("stories", [])):
            if not isinstance(story, dict):
                continue
            stories.append({
                "id": str(story.get("id_sketch", "")),
                "title": str(story.get("title", "")),
                "phase": int(phase.get("number", 0)),
                "phase_slug": "proposed-phase-%s" % phase.get("number"),
                "phase_status": "proposed",
                "order": order,
                "status": "backlog",
                "status_raw": "backlog",
                "story_path": "",
                "dependencies": [
                    str(item.get("id_sketch", ""))
                    for item in story.get("dependencies", [])
                    if isinstance(item, dict)
                ],
            })
    return stories


class _Compiler:
    def __init__(
        self,
        root: Path,
        raw: object,
        source: str = "program",
        *,
        bundle_documents: dict[str, object] | None = None,
        roadmap_document: dict[str, object] | None = None,
    ) -> None:
        self.root = root.resolve()
        self.raw = raw
        self.source = source
        self.bundle_documents = bundle_documents
        self.roadmap_document = roadmap_document
        self.diagnostics: list[dict[str, str]] = []
        self.bundle_diagnostics: list[dict[str, str]] = []
        self.references: dict[str, object] = {
            "organization": None,
            "workflows": {},
            "workflow_instances": {},
            "rubrics": {},
        }
        self.project: object | None = None
        self.stories: list[dict[str, object]] = []

    def _proposed_roadmap_inventory(self, project_slug: str):
        document = self.roadmap_document
        if document is None:
            return None
        project = document.get("project")
        roadmap = document.get("roadmap")
        if not isinstance(project, dict) or not isinstance(roadmap, dict):
            return None
        if project.get("slug") != project_slug:
            return None
        return project, _proposed_story_inventory(roadmap)

    def diag(
        self,
        pointer: str,
        code: str,
        message: str,
        remediation: str,
        source: str | None = None,
    ) -> None:
        self.diagnostics.append({
            "source": source or self.source,
            "pointer": pointer or "/",
            "code": code,
            "message": message,
            "remediation": remediation,
        })

    def bundle_diag(
        self,
        pointer: str,
        code: str,
        message: str,
        remediation: str,
        source: str | None = None,
    ) -> None:
        """Whole-bundle preflight findings (WLA-30-06).

        These reject a bundle at validate time and gate grant planning,
        but deliberately do not fail plain ``compile_program`` — the
        compiler's document semantics are unchanged so studio editing,
        simulation, and legacy fixtures keep compiling while the
        validate surface and the grant path refuse.
        """
        self.bundle_diagnostics.append({
            "source": source or self.source,
            "pointer": pointer or "/",
            "code": code,
            "message": message,
            "remediation": remediation,
        })

    def exact_keys(
        self,
        value: dict[str, object],
        allowed: set[str],
        pointer: str,
        *,
        source: str | None = None,
    ) -> None:
        for key in sorted(set(value) - allowed):
            self.diag(
                f"{pointer}/{key}" if pointer else f"/{key}",
                "unknown-key",
                f"unknown key {key!r}",
                "remove the key or use a contracted schema field",
                source,
            )

    def string(
        self,
        value: object,
        pointer: str,
        *,
        pattern: re.Pattern[str] | None = None,
        maximum: int = 500,
        source: str | None = None,
    ) -> str:
        if not isinstance(value, str) or not value or len(value) > maximum:
            self.diag(pointer, "invalid-value", "expected a non-empty bounded string", "provide a bounded string", source)
            return ""
        if pattern is not None and not pattern.fullmatch(value):
            self.diag(pointer, "unsafe-selector", f"unsafe selector {value!r}", "use a stable lowercase selector", source)
            return ""
        return value

    def positive_int(
        self,
        value: object,
        pointer: str,
        default: int,
        maximum: int,
        *,
        source: str | None = None,
    ) -> int:
        if value is None:
            return default
        if isinstance(value, bool) or not isinstance(value, int) or not 1 <= value <= maximum:
            self.diag(pointer, "invalid-bound", f"expected an integer from 1 through {maximum}", "choose a finite positive bound", source)
            return default
        return value

    def phase_scope(self, value: object) -> list[int]:
        if not isinstance(value, dict):
            self.diag("/scope/phases", "invalid-phase-range", "phases must be an inclusive range or explicit list", "use {from, through} or {include}")
            return []
        keys = set(value)
        if keys == _PHASE_RANGE_KEYS:
            start = value.get("from")
            through = value.get("through")
            if (
                isinstance(start, bool) or not isinstance(start, int)
                or isinstance(through, bool) or not isinstance(through, int)
                or start < 0 or through < start or through - start > 99
            ):
                self.diag("/scope/phases", "invalid-phase-range", "phase range must be ordered, non-negative, and span at most 100 phases", "fix from/through")
                return []
            return list(range(start, through + 1))
        if keys == _PHASE_INCLUDE_KEYS:
            include = value.get("include")
            if (
                not isinstance(include, list) or not include or len(include) > 100
                or any(isinstance(item, bool) or not isinstance(item, int) or item < 0 for item in include)
                or len(set(include)) != len(include)
            ):
                self.diag("/scope/phases/include", "invalid-phase-range", "phase include must be a non-empty unique bounded integer list", "provide explicit unique phase numbers")
                return []
            return sorted(include)
        self.exact_keys(value, _PHASE_RANGE_KEYS | _PHASE_INCLUDE_KEYS, "/scope/phases")
        self.diag("/scope/phases", "invalid-phase-range", "choose exactly range form or include form", "use {from, through} or {include}, not both")
        return []

    def story_scope(self, value: object) -> str | list[str]:
        if value == "all":
            return "all"
        if not isinstance(value, dict):
            self.diag("/scope/stories", "invalid-story-scope", "stories must be 'all' or an include object", "use 'all' or {include: [...]}")
            return []
        self.exact_keys(value, _STORY_SELECTOR_KEYS, "/scope/stories")
        include = value.get("include")
        if (
            not isinstance(include, list) or not include or len(include) > 2_000
            or any(not isinstance(item, str) or not _STORY_ID_RE.fullmatch(item) for item in include)
            or len(set(include)) != len(include)
        ):
            self.diag("/scope/stories/include", "invalid-story-scope", "story include must be a non-empty unique story-id list", "provide exact roadmap story ids")
            return []
        return list(include)

    def _reference(
        self,
        family: str,
        slug: str,
    ) -> tuple[str, dict[str, object]] | None:
        """Resolve one tracked or proposal-embedded policy document."""
        if self.bundle_documents is not None:
            family_documents = self.bundle_documents.get(family)
            if not isinstance(family_documents, dict):
                return None
            raw = family_documents.get(slug)
            if not isinstance(raw, dict):
                return None
            return f"setup-proposal:/tracked_content/policy/{family}/{slug}", raw
        found = _reference_by_slug(self.root, family, slug)
        if found is None:
            return None
        path, raw = found
        return str(path.relative_to(self.root)), raw

    def load_reference(
        self,
        family: str,
        slug: str,
        kind: str,
        allowed_keys: set[str],
        pointer: str,
    ) -> dict[str, object] | None:
        found = self._reference(family, slug)
        if found is None:
            self.diag(pointer, f"dangling-{kind.split('-')[-1]}-reference", f"cannot resolve {kind} {slug!r}", f"add one unambiguous pm/{family}/{slug}.json policy")
            return None
        source, raw = found
        self.exact_keys(raw, allowed_keys, "", source=source)
        if raw.get("kind") != kind:
            self.diag("/kind", "wrong-kind", f"expected {kind!r}", f"set kind to {kind}", source)
        if raw.get("schema_version") != 1:
            self.diag("/schema_version", "unsupported-schema", "only schema version 1 is supported", "use schema_version 1", source)
        if raw.get("slug") != slug:
            self.diag("/slug", "reference-slug-mismatch", f"reference resolved to slug {raw.get('slug')!r}", f"set slug to {slug!r}", source)
        self.string(raw.get("title"), "/title", source=source)
        semantic_document = {
            key: value for key, value in raw.items() if key != "layout"
        }
        return {
            "path": source,
            "document": raw,
            "semantic_document": semantic_document,
            "semantic_hash": _sha(semantic_document),
            "document_hash": _sha(raw),
        }

    def load_rubric_reference(
        self,
        slug: str,
        pointer: str,
    ) -> dict[str, object] | None:
        reference = self.load_reference(
            "rubrics", slug, RUBRIC_KIND, _RUBRIC_KEYS, pointer,
        )
        if reference is None:
            return None
        try:
            compiled = compile_rubric(
                self.root,
                reference["document"],
                str(reference["path"]),
            )
        except RubricValidationError as exc:
            self.diagnostics.extend(exc.diagnostics)
            self.bundle_diagnostics.extend(_tracked_policy_controls(
                reference["document"], source=str(reference["path"]),
            ))
            return None
        reference.update({
            "semantic_document": compiled["rubric"],
            "semantic_hash": compiled["semantic_hash"],
            "document_hash": compiled["document_hash"],
            "version": compiled["rubric"]["version"],
            "subject_type": compiled["rubric"]["subject_type"],
            "compiled": compiled,
        })
        return reference

    def normalize_organization(self, slug: str) -> dict[str, object]:
        found = self._reference("organizations", slug)
        if found is None:
            self.diag(
                "/organization", "dangling-organization-reference",
                f"cannot resolve organization {slug!r}",
                f"add one unambiguous pm/organizations/{slug}.json policy",
            )
            return {
                "slug": slug, "agents": [], "pools": [], "teams": [],
                "councils": [], "compiled": None,
            }
        source, raw = found
        try:
            compiled = compile_organization(self.root, raw, source)
        except OrganizationValidationError as exc:
            self.diagnostics.extend(exc.diagnostics)
            self.bundle_diagnostics.extend(_tracked_policy_controls(
                raw, source=source,
            ))
            return {
                "slug": slug, "agents": [], "pools": [], "teams": [],
                "councils": [], "compiled": None,
            }
        runtime = compiled["organization"]
        assert isinstance(runtime, dict)
        normalized = {
            **runtime,
            "path": source,
            "semantic_hash": compiled["semantic_hash"],
            "document_hash": compiled["document_hash"],
            "compiled": compiled,
        }
        self.references["organization"] = normalized
        return normalized

    def normalize_scope(self, value: object) -> dict[str, object]:
        if not isinstance(value, dict):
            self.diag("/scope", "wrong-type", "scope must be an object", "provide project, phases, stories, selection, and blocked_policy")
            value = {}
        self.exact_keys(value, _SCOPE_KEYS, "/scope")
        project_slug = self.string(value.get("project"), "/scope/project", pattern=_SAFE_ID_RE)
        phases = self.phase_scope(value.get("phases"))
        stories = self.story_scope(value.get("stories"))
        selection = value.get("selection")
        if selection not in SELECTION_POLICIES:
            self.diag("/scope/selection", "unsupported-selection", f"unsupported selection policy {selection!r}", "use roadmap-frontier-v1")
            selection = SELECTION_POLICIES[0]
        blocked = value.get("blocked_policy")
        if blocked not in BLOCKED_POLICIES:
            self.diag("/scope/blocked_policy", "unsupported-blocked-policy", f"unsupported blocked policy {blocked!r}", "use stop")
            blocked = BLOCKED_POLICIES[0]

        proposed = self._proposed_roadmap_inventory(project_slug)
        if proposed is not None:
            # A setup proposal's roadmap is the truthful source before
            # `dw setup apply` creates it in the repository (WLA-30-07
            # base-proposal scaffolding); scope resolves against it.
            self.project, self.stories = proposed
            existing_phases = {story["phase"] for story in self.stories}
            missing_phases = sorted(set(phases) - existing_phases)
            if missing_phases:
                self.diag("/scope/phases", "invalid-phase-range", f"scope names missing phases: {', '.join(map(str, missing_phases))}", "use existing phase numbers")
        else:
            projects = [project for project in discover_projects(self.root) if project.slug == project_slug]
            if len(projects) != 1:
                self.diag("/scope/project", "scope-project-missing", f"roadmap project {project_slug!r} does not resolve uniquely", "choose one existing roadmap project")
            else:
                self.project = projects[0]
                existing_phases = {phase.number for phase in discover_phases(projects[0])}
                missing_phases = sorted(set(phases) - existing_phases)
                if missing_phases:
                    self.diag("/scope/phases", "invalid-phase-range", f"scope names missing phases: {', '.join(map(str, missing_phases))}", "use existing phase numbers")
                self.stories = _project_story_inventory(projects[0])

        all_ids = {str(story["id"]) for story in self.stories}
        if stories != "all":
            missing_stories = [story_id for story_id in stories if story_id not in all_ids]
            if missing_stories:
                self.diag("/scope/stories/include", "scope-story-missing", f"scope names missing stories: {', '.join(missing_stories)}", "use existing story ids")
        scoped = [
            story for story in self.stories
            if story["phase"] in phases and (stories == "all" or story["id"] in stories)
        ]
        if not scoped and self.project is not None:
            self.diag("/scope", "empty-scope", "scope can never select a roadmap story", "include at least one existing story")
        for story in scoped:
            status = str(story["status"])
            if status not in STORY_STATUSES | CUT_STATUSES:
                self.diag(
                    f"/roadmap/{story['id']}/status",
                    "unsupported-status",
                    f"scoped story has unsupported status {story['status_raw']!r}",
                    "use the canonical roadmap story status vocabulary",
                    str(Path(str(story["story_path"])).relative_to(self.root)),
                )
        return {
            "project": project_slug,
            "phases": phases,
            "stories": stories,
            "selection": selection,
            "blocked_policy": blocked,
            "story_ids": [str(story["id"]) for story in scoped],
        }

    @staticmethod
    def _binding_matches(binding: dict[str, object], story: dict[str, object]) -> bool:
        match = binding["match"]
        assert isinstance(match, dict)
        phase = int(story["phase"])
        if phase < int(match["phase_from"]) or phase > int(match["phase_through"]):
            return False
        story_ids = match.get("story_ids")
        return not story_ids or story["id"] in story_ids

    def normalize_bindings(
        self,
        value: object,
        scope: dict[str, object],
        organization: dict[str, object],
    ) -> tuple[list[dict[str, object]], dict[str, str]]:
        if not isinstance(value, list) or not value:
            self.diag("/bindings", "missing-bindings", "program requires ordered binding rules", "declare at least one workflow/team/rubric binding")
            value = []
        if len(value) > 1_000:
            self.diag("/bindings", "unbounded-value", "binding count exceeds 1000", "split the program scope")
            value = value[:1000]
        bindings: list[dict[str, object]] = []
        ids: set[str] = set()
        team_ids = {str(team["id"]) for team in organization.get("teams", [])}
        for index, raw in enumerate(value):
            pointer = f"/bindings/{index}"
            if not isinstance(raw, dict):
                self.diag(pointer, "wrong-type", "binding must be an object", "provide a binding object")
                continue
            self.exact_keys(raw, _BINDING_KEYS, pointer)
            binding_id = self.string(raw.get("id"), f"{pointer}/id", pattern=_SAFE_ID_RE)
            if binding_id in ids:
                self.diag(f"{pointer}/id", "duplicate-id", f"duplicate binding id {binding_id!r}", "use unique binding ids")
            ids.add(binding_id)
            priority = self.positive_int(raw.get("priority"), f"{pointer}/priority", 100, 10_000)
            match_raw = raw.get("match")
            if not isinstance(match_raw, dict):
                self.diag(f"{pointer}/match", "wrong-type", "binding match must be an object", "provide phase_from and phase_through")
                match_raw = {}
            self.exact_keys(match_raw, _MATCH_KEYS, f"{pointer}/match")
            phase_from = match_raw.get("phase_from")
            phase_through = match_raw.get("phase_through")
            if (
                isinstance(phase_from, bool) or not isinstance(phase_from, int)
                or isinstance(phase_through, bool) or not isinstance(phase_through, int)
                or phase_from < 0 or phase_through < phase_from
            ):
                self.diag(f"{pointer}/match", "invalid-phase-range", "binding phase range is invalid", "provide an ordered inclusive range")
                phase_from = phase_through = 0
            story_ids = match_raw.get("story_ids", [])
            if (
                not isinstance(story_ids, list)
                or any(not isinstance(item, str) or not _STORY_ID_RE.fullmatch(item) for item in story_ids)
                or len(set(story_ids)) != len(story_ids)
            ):
                self.diag(f"{pointer}/match/story_ids", "invalid-story-scope", "story_ids must be a unique story-id list", "use exact story ids or omit the field")
                story_ids = []
            workflow = self.string(raw.get("workflow"), f"{pointer}/workflow", pattern=_SAFE_ID_RE)
            workflow_ref = self.load_reference(
                "workflows", workflow, WORKFLOW_KIND, _WORKFLOW_KEYS,
                f"{pointer}/workflow",
            )
            workflow_instance: dict[str, object] | None = None
            workflow_bindings = raw.get("with", {})
            if not isinstance(workflow_bindings, dict):
                self.diag(f"{pointer}/with", "wrong-type", "workflow parameter bindings must be an object", "map declared parameters to typed literal/context expressions")
                workflow_bindings = {}
            if workflow_ref is not None:
                try:
                    workflow_instance = compile_workflow(
                        self.root,
                        workflow_ref["document"],
                        bindings=workflow_bindings,
                        require_bound=True,
                        source=str(workflow_ref["path"]),
                    )
                except WorkflowValidationError as exc:
                    self.diagnostics.extend(exc.diagnostics)
                else:
                    workflow_ref["semantic_hash"] = workflow_instance["semantic_hash"]
                    workflow_ref["document_hash"] = workflow_instance["document_hash"]
                    workflow_ref["version"] = workflow_instance["version"]
                    workflow_ref["source_hashes"] = workflow_instance["source_hashes"]
                    self.references["workflow_instances"][binding_id] = workflow_instance  # type: ignore[index]
                self.references["workflows"][workflow] = workflow_ref  # type: ignore[index]
            team = self.string(raw.get("team"), f"{pointer}/team", pattern=_SAFE_ID_RE)
            if team and team not in team_ids:
                self.diag(f"{pointer}/team", "dangling-role-reference", f"team {team!r} is not declared by the organization", "reference a declared team")
            rubrics_raw = raw.get("rubrics")
            if (
                not isinstance(rubrics_raw, list) or not rubrics_raw
                or any(not isinstance(item, str) or not _SAFE_ID_RE.fullmatch(item) for item in rubrics_raw)
                or len(set(rubrics_raw)) != len(rubrics_raw)
            ):
                self.diag(f"{pointer}/rubrics", "invalid-rubrics", "rubrics must be a unique non-empty slug list", "declare verifier rubric references")
                rubrics_raw = []
            for rubric in rubrics_raw:
                rubric_ref = self.load_rubric_reference(
                    rubric, f"{pointer}/rubrics",
                )
                if rubric_ref is not None:
                    self.references["rubrics"][rubric] = rubric_ref  # type: ignore[index]
            bindings.append({
                "id": binding_id,
                "priority": priority,
                "match": {
                    "phase_from": phase_from,
                    "phase_through": phase_through,
                    "story_ids": list(story_ids),
                },
                "workflow": workflow,
                "with": (
                    workflow_instance["bindings"]
                    if workflow_instance is not None else dict(workflow_bindings)
                ),
                "workflow_version": (
                    workflow_instance["version"]
                    if workflow_instance is not None else None
                ),
                "workflow_semantic_hash": (
                    workflow_instance["semantic_hash"]
                    if workflow_instance is not None else None
                ),
                "workflow_bundle_hash": (
                    workflow_instance["bundle_hash"]
                    if workflow_instance is not None else None
                ),
                "workflow_envelope": (
                    workflow_instance["envelope"]
                    if workflow_instance is not None else None
                ),
                "team": team,
                "rubrics": list(rubrics_raw),
            })

        bindings.sort(key=lambda item: (int(item["priority"]), str(item["id"])))
        scoped_ids = set(scope["story_ids"])
        binding_by_story: dict[str, str] = {}
        bound_count = 0
        for story in self.stories:
            if story["id"] not in scoped_ids:
                continue
            matches = [binding for binding in bindings if self._binding_matches(binding, story)]
            if not matches:
                continue
            best_priority = min(int(binding["priority"]) for binding in matches)
            best = [binding for binding in matches if int(binding["priority"]) == best_priority]
            if len(best) > 1:
                self.diag(
                    "/bindings",
                    "binding-ambiguous",
                    f"story {story['id']} matches equal-priority bindings: "
                    + ", ".join(str(binding["id"]) for binding in best),
                    "make priorities unique at every overlapping story",
                )
                continue
            binding_by_story[str(story["id"])] = str(best[0]["id"])
            bound_count += 1
        if scoped_ids and not bound_count:
            self.diag("/bindings", "scope-unselectable", "no scoped story matches a valid binding", "add a binding that covers the explicit scope")
        return bindings, binding_by_story

    def normalize_phase_gates(
        self,
        value: object,
        organization: dict[str, object],
    ) -> list[dict[str, object]]:
        if value is None:
            return []
        if not isinstance(value, list):
            self.diag("/phase_gates", "wrong-type", "phase_gates must be an array", "provide an array or remove it")
            return []
        role_duties = {
            str(role["duty"])
            for team in organization.get("teams", [])
            for role in team.get("roles", [])
        }
        gates: list[dict[str, object]] = []
        ids: set[str] = set()
        for index, raw in enumerate(value):
            pointer = f"/phase_gates/{index}"
            if not isinstance(raw, dict):
                self.diag(pointer, "wrong-type", "phase gate must be an object", "provide a phase gate object")
                continue
            self.exact_keys(raw, _PHASE_GATE_KEYS, pointer)
            gate_id = self.string(raw.get("id"), f"{pointer}/id", pattern=_SAFE_ID_RE)
            if gate_id in ids:
                self.diag(f"{pointer}/id", "duplicate-id", f"duplicate phase gate id {gate_id!r}", "use unique ids")
            ids.add(gate_id)
            when = raw.get("when")
            if when != "before-phase-complete":
                self.diag(f"{pointer}/when", "unsupported-value", "phase gate supports only before-phase-complete", "use before-phase-complete")
                when = "before-phase-complete"
            role = raw.get("role")
            if role not in role_duties:
                self.diag(f"{pointer}/role", "dangling-role-reference", f"organization has no {role!r} duty", "declare that role duty in a team")
            rubric = self.string(raw.get("rubric"), f"{pointer}/rubric", pattern=_SAFE_ID_RE)
            rubric_ref = self.load_rubric_reference(
                rubric, f"{pointer}/rubric",
            )
            if rubric_ref is not None:
                self.references["rubrics"][rubric] = rubric_ref  # type: ignore[index]
            on_fail = raw.get("on_fail")
            if on_fail not in {"block", "checkpoint", "abort"}:
                self.diag(f"{pointer}/on_fail", "unsupported-value", "unsupported phase-gate failure route", "use block, checkpoint, or abort")
                on_fail = "block"
            gates.append({
                "id": gate_id,
                "when": when,
                "role": role,
                "rubric": rubric,
                "on_fail": on_fail,
            })
        return gates

    def normalize_nudges(
        self,
        value: object,
        bindings: list[dict[str, object]],
    ) -> list[dict[str, object]]:
        if value is None:
            return []
        if not isinstance(value, list):
            self.diag(
                "/nudges", "wrong-type",
                "program nudges must be an array of standing rules",
                "provide a bounded rule array or remove the section",
            )
            return []
        if len(value) > 20:
            self.diag(
                "/nudges", "unbounded-value",
                "program nudges exceed the 20-rule bound",
                "keep the standing-rule set small and exact",
            )
            value = value[:20]
        binding_ids = {str(binding["id"]) for binding in bindings}
        instances = self.references["workflow_instances"]
        assert isinstance(instances, dict)
        rules: list[dict[str, object]] = []
        ids: set[str] = set()
        for index, raw in enumerate(value):
            pointer = f"/nudges/{index}"
            if not isinstance(raw, dict):
                self.diag(
                    pointer, "wrong-type",
                    "program nudge rule must be an object",
                    "provide id, signal, binding, target, and finite bounds",
                )
                continue
            self.exact_keys(raw, _PROGRAM_NUDGE_KEYS, pointer)
            rule_id = self.string(
                raw.get("id"), f"{pointer}/id", pattern=_SAFE_ID_RE,
            )
            if rule_id in ids:
                self.diag(
                    f"{pointer}/id", "duplicate-id",
                    f"duplicate program nudge rule {rule_id!r}",
                    "use a unique standing-rule id",
                )
            ids.add(rule_id)
            signal = raw.get("signal")
            if signal not in _PROGRAM_NUDGE_SIGNALS:
                self.diag(
                    f"{pointer}/signal", "unsupported-program-signal",
                    f"program-level nudge signal {signal!r} is unsupported",
                    "use ci-failed, changes-requested, or merge-conflict; "
                    "keep waiting-input-timeout inside a bounded child score",
                )
                signal = _PROGRAM_NUDGE_SIGNALS[0]
            binding = self.string(
                raw.get("binding"),
                f"{pointer}/binding",
                pattern=_SAFE_ID_RE,
            )
            if binding not in binding_ids:
                self.diag(
                    f"{pointer}/binding", "dangling-nudge-binding",
                    f"program nudge binding {binding!r} does not exist",
                    "reference one declared program binding",
                )
            target = self.string(
                raw.get("target"),
                f"{pointer}/target",
                pattern=_WORKFLOW_TARGET_RE,
            )
            instance = instances.get(binding)
            if isinstance(instance, dict):
                matches = [
                    node for node in instance.get("expanded_nodes", [])
                    if isinstance(node, dict) and node.get("address") == target
                ]
                if len(matches) != 1:
                    self.diag(
                        f"{pointer}/target", "dangling-nudge-target",
                        f"program nudge target {target!r} does not resolve "
                        f"uniquely in binding {binding!r}",
                        "use one exact expanded workflow node address",
                    )
                elif matches[0].get("type") != "agent":
                    self.diag(
                        f"{pointer}/target", "unsafe-nudge-target",
                        "a program nudge target must be an agent node",
                        "target the exact already-declared agent to rerun",
                    )
                elif "{round}" in target:
                    self.diag(
                        f"{pointer}/target", "ambiguous-nudge-target",
                        "a program nudge cannot target a round template",
                        "target a stable agent outside a structural loop",
                    )
            expectation = raw.get("expectation")
            if expectation is not None and (
                not isinstance(expectation, str)
                or not expectation
                or len(expectation) > 500
                or "\0" in expectation
            ):
                self.diag(
                    f"{pointer}/expectation", "invalid-value",
                    "nudge expectation must be a bounded non-empty string",
                    "use at most 500 characters or remove it",
                )
                expectation = None
            max_per_signal = self.positive_int(
                raw.get("max_per_signal"),
                f"{pointer}/max_per_signal",
                1,
                5,
            )
            max_total = self.positive_int(
                raw.get("max_total"),
                f"{pointer}/max_total",
                1,
                20,
            )
            if max_per_signal > max_total:
                self.diag(
                    f"{pointer}/max_per_signal",
                    "invalid-bound",
                    "per-signal ceiling exceeds the rule's total ceiling",
                    "lower max_per_signal or raise max_total",
                )
            rule: dict[str, object] = {
                "id": rule_id,
                "signal": signal,
                "binding": binding,
                "target": target,
                "max_per_signal": max_per_signal,
                "max_total": max_total,
            }
            if expectation is not None:
                rule["expectation"] = expectation
            rules.append(rule)
        return rules

    def _workflow_node_location(
        self,
        instance: dict[str, object],
        expanded: dict[str, object],
    ) -> tuple[str, str]:
        workflow = str(expanded.get("workflow") or instance.get("slug") or "")
        version = str(expanded.get("version") or instance.get("version") or "")
        source_record = instance.get("sources", {}).get(f"{workflow}@{version}")  # type: ignore[union-attr]
        source = str(
            source_record.get("path")
            if isinstance(source_record, dict) else instance.get("source", self.source)
        )
        try:
            document = parse_program_text(
                (self.root / source).read_text(encoding="utf-8"), source,
            )
        except (DwError, OSError):
            return source, "/nodes"
        for index, node in enumerate(document.get("nodes", [])):
            if isinstance(node, dict) and node.get("id") == expanded.get("node"):
                return source, f"/nodes/{index}"
        return source, "/nodes"

    def _bundle_policy_controls(self) -> None:
        documents: list[tuple[str, object]] = [(self.source, self.raw)]
        organization = self.references.get("organization")
        if isinstance(organization, dict):
            compiled = organization.get("compiled")
            if isinstance(compiled, dict):
                documents.append((str(organization["path"]), compiled["organization"]))
        for family in ("workflows", "rubrics"):
            references = self.references.get(family, {})
            if not isinstance(references, dict):
                continue
            for reference in references.values():
                if isinstance(reference, dict):
                    documents.append((str(reference["path"]), reference["document"]))
        instances = self.references.get("workflow_instances", {})
        if isinstance(instances, dict):
            for instance in instances.values():
                if not isinstance(instance, dict):
                    continue
                for source_record in instance.get("sources", {}).values():
                    if not isinstance(source_record, dict):
                        continue
                    source_path = str(source_record.get("path") or "")
                    try:
                        document = parse_program_text(
                            (self.root / source_path).read_text(encoding="utf-8"),
                            source_path,
                        )
                    except (DwError, OSError):
                        continue
                    documents.append((source_path, document))
        seen: set[tuple[str, str, str]] = set()
        for source, document in documents:
            for diagnostic in _tracked_policy_controls(document, source=source):
                key = (
                    diagnostic["source"], diagnostic["pointer"],
                    diagnostic["code"],
                )
                if key in seen:
                    continue
                seen.add(key)
                self.bundle_diagnostics.append(diagnostic)

    def _bundle_node_and_route_checks(self) -> None:
        # Imported lazily because the conductor itself imports this module.
        from .program_conductor import CONDUCTOR_BUILTIN_CHECKS, CONDUCTOR_NODE_TYPES

        compiler_only = set(NODE_TYPES) - set(CONDUCTOR_NODE_TYPES)
        workflows = self.references.get("workflows", {})
        if isinstance(workflows, dict):
            # The Phase 30 exam's first attempt reached a live tick before
            # discovering rail-status is separately authorized; builtin
            # runner NAMES now share the node-type parity rule, read from
            # the workflow documents the compiler actually loaded.
            for reference in workflows.values():
                if not isinstance(reference, dict):
                    continue
                document = reference.get("document")
                if not isinstance(document, dict):
                    continue
                for index, node in enumerate(document.get("nodes", [])):
                    if not isinstance(node, dict) or node.get("type") != "check":
                        continue
                    runner = node.get("runner")
                    if (
                        isinstance(runner, dict)
                        and runner.get("kind") == "builtin"
                        and str(runner.get("name")) not in CONDUCTOR_BUILTIN_CHECKS
                    ):
                        self.bundle_diag(
                            f"/nodes/{index}/runner/name",
                            "unconductable-builtin-check",
                            f"the program conductor does not conduct builtin check {runner.get('name')!r}",
                            "use a conductor-supported builtin (%s) or an exact command check"
                            % ", ".join(sorted(CONDUCTOR_BUILTIN_CHECKS)),
                            str(reference.get("path") or self.source),
                        )
        instances = self.references.get("workflow_instances", {})
        if not isinstance(instances, dict):
            return
        for binding_id, instance in sorted(instances.items()):
            if not isinstance(instance, dict):
                continue
            for expanded in instance.get("expanded_nodes", []):
                if not isinstance(expanded, dict):
                    continue
                node_type = str(expanded.get("type") or "")
                if node_type not in compiler_only:
                    continue
                source, pointer = self._workflow_node_location(instance, expanded)
                self.bundle_diag(
                    f"{pointer}/type",
                    "unconductable-node-type",
                    f"compiler accepts node type {node_type!r}, but the program conductor does not conduct it",
                    "replace it with a conductor-supported node or add conductor support before granting the program",
                    source,
                )
            green_route = instance.get("green_route", {})
            if not isinstance(green_route, dict) or not green_route.get("complete"):
                source = str(instance.get("source") or self.source)
                self.bundle_diag(
                    "/terminals",
                    "no-complete-green-route",
                    f"binding {binding_id!r} has no reachable all-green route to a complete terminal",
                    "route a reachable success/pass/consensus outcome to a complete or awaiting-certification terminal",
                    source,
                )

    def _bundle_rubric_fact_checks(
        self,
        bindings: list[dict[str, object]],
    ) -> None:
        instances = self.references.get("workflow_instances", {})
        rubrics = self.references.get("rubrics", {})
        if not isinstance(instances, dict) or not isinstance(rubrics, dict):
            return
        checked_rubrics: set[str] = set()
        all_producers: set[str] = set()

        def producers_for(instance: dict[str, object]) -> set[str]:
            # Every check/rail node in the conducted graph produces its
            # fact: repair-leg checks live on the FAILURE route by
            # design (a passing first verdict goes straight to the
            # terminal), and a repair rubric consumed only on that
            # route legitimately names them. The attempt-7 defect this
            # guard exists for was a fact-id NAME mismatch, which
            # whole-graph matching still catches.
            return {
                str(node.get("node"))
                for node in instance.get("expanded_nodes", [])
                if (
                    isinstance(node, dict)
                    and node.get("type") in {"check", "rail"}
                )
            }

        def check_rubric(
            rubric_slug: object,
            producers: set[str],
            binding_label: str,
        ) -> None:
            reference = rubrics.get(str(rubric_slug))
            if not isinstance(reference, dict):
                return
            checked_rubrics.add(str(rubric_slug))
            document = reference.get("document", {})
            if not isinstance(document, dict):
                return
            for index, criterion in enumerate(document.get("criteria", [])):
                evaluation = (
                    criterion.get("evaluation")
                    if isinstance(criterion, dict) else None
                )
                if not isinstance(evaluation, dict) or evaluation.get("kind") != "mechanical-fact":
                    continue
                fact = str(evaluation.get("fact") or "")
                if fact in producers:
                    continue
                self.bundle_diag(
                    f"/criteria/{index}/evaluation/fact",
                    "mechanical-fact-unproduced",
                    f"mechanical fact {fact!r} is not produced by a reachable check or trusted rail {binding_label}",
                    "name the producing check/rail node id exactly or make that producer reachable on the green route",
                    str(reference["path"]),
                )

        for binding in bindings:
            instance = instances.get(str(binding["id"]))
            if not isinstance(instance, dict):
                continue
            producers = producers_for(instance)
            all_producers.update(producers)
            for rubric_slug in binding.get("rubrics", []):
                check_rubric(
                    rubric_slug, producers,
                    f"in binding {binding['id']!r}",
                )
        for rubric_slug in sorted(set(rubrics) - checked_rubrics):
            check_rubric(
                rubric_slug, all_producers, "in the linked workflow bundle",
            )

    def _bundle_team_budget_checks(
        self,
        organization: dict[str, object],
        bindings: list[dict[str, object]],
        budgets: dict[str, int],
        phase_gates: list[dict[str, object]],
    ) -> None:
        compiled = organization.get("compiled")
        runtime = compiled.get("organization") if isinstance(compiled, dict) else None
        if not isinstance(runtime, dict):
            return
        instances = self.references.get("workflow_instances", {})
        if not isinstance(instances, dict):
            return
        teams = {str(team["id"]): team for team in runtime.get("teams", [])}
        source = str(organization.get("path") or self.source)
        gate_duties = {str(gate["role"]) for gate in phase_gates}
        for binding in bindings:
            team = teams.get(str(binding["team"]))
            instance = instances.get(str(binding["id"]))
            if not isinstance(team, dict) or not isinstance(instance, dict):
                continue
            workflow_roles = {
                str(lane["role"])
                for lane in instance.get("role_lanes", [])
                if isinstance(lane, dict) and lane.get("role")
            }
            required_roles = [
                role for role in team.get("roles", [])
                if isinstance(role, dict) and (
                    role.get("required")
                    or role.get("id") in workflow_roles
                    or role.get("duty") in gate_duties
                )
            ]
            minimum = sum(int(role["cardinality"]) for role in required_roles)
            verifier_slots = sum(
                int(role["cardinality"])
                for role in required_roles if role.get("duty") == "verifier"
            )
            for budget_key in (
                "max_child_runs", "max_agent_starts", "max_provider_starts",
                "max_model_starts",
            ):
                if budgets[budget_key] >= minimum:
                    continue
                self.bundle_diag(
                    f"/budgets/{budget_key}",
                    "team-exceeds-budget",
                    f"binding {binding['id']!r} requires at least {minimum} distinct team starts, but {budget_key}={budgets[budget_key]}",
                    "raise the finite budget to the bound team's required cardinality or reduce required role slots",
                )
            if budgets["max_verdicts"] < verifier_slots:
                self.bundle_diag(
                    "/budgets/max_verdicts",
                    "verifier-exceeds-budget",
                    f"binding {binding['id']!r} requires {verifier_slots} independent verifier verdict(s), but max_verdicts={budgets['max_verdicts']}",
                    "raise max_verdicts to cover every required verifier slot",
                )
            implementer = next(
                (role for role in required_roles if role.get("duty") == "implementer"),
                None,
            )
            verifier = next(
                (role for role in required_roles if role.get("duty") == "verifier"),
                None,
            )
            if implementer is not None and verifier is not None and minimum < 2:
                team_index = list(runtime.get("teams", [])).index(team)
                self.bundle_diag(
                    f"/teams/{team_index}/roles",
                    "separation-violation",
                    "implementer/verifier separation requires at least two role slots",
                    "declare distinct required singleton implementer and verifier roles",
                    source,
                )

    def compile(self) -> tuple[dict[str, object], list[dict[str, str]], dict[str, object]]:
        if not isinstance(self.raw, dict):
            self.diag("/", "wrong-type", "program must be an object", "provide a program object")
            raw: dict[str, object] = {}
        else:
            raw = self.raw
        self.exact_keys(raw, _PROGRAM_KEYS, "")
        if raw.get("kind") != PROGRAM_KIND:
            self.diag("/kind", "wrong-kind", f"expected {PROGRAM_KIND!r}", f"set kind to {PROGRAM_KIND}")
        if raw.get("schema_version") != PROGRAM_SCHEMA_VERSION:
            self.diag("/schema_version", "unsupported-schema", "only schema version 1 is supported", "use schema_version 1")
        slug = self.string(raw.get("slug"), "/slug", pattern=_SAFE_ID_RE)
        title = self.string(raw.get("title"), "/title")
        description = raw.get("description")
        if description is not None and (not isinstance(description, str) or len(description) > 5_000):
            self.diag("/description", "invalid-value", "description must be a bounded string", "shorten the description")
            description = None
        scope = self.normalize_scope(raw.get("scope"))
        organization_slug = self.string(raw.get("organization"), "/organization", pattern=_SAFE_ID_RE)
        organization = self.normalize_organization(organization_slug)
        bindings, binding_by_story = self.normalize_bindings(raw.get("bindings"), scope, organization)
        phase_gates = self.normalize_phase_gates(raw.get("phase_gates", []), organization)
        nudges = self.normalize_nudges(raw.get("nudges"), bindings)
        mode = raw.get("mode_ceiling", "advisory")
        if mode not in MODE_CEILINGS:
            self.diag("/mode_ceiling", "unsupported-mode", f"unsupported mode {mode!r}", "use advisory, checkpointed, or continuous")
            mode = "advisory"
        capabilities = raw.get("requested_capabilities", [])
        if (
            not isinstance(capabilities, list)
            or any(capability not in PROGRAM_CAPABILITIES for capability in capabilities)
            or len(set(capabilities)) != len(capabilities)
        ):
            self.diag("/requested_capabilities", "unsupported-capability", "requested capabilities must be a unique contracted list", "use only Phase 26 capability names")
            capabilities = []
        if phase_gates:
            missing_gate_capabilities = sorted(
                {"agent:dispatch", "verdict:issue"} - set(capabilities)
            )
            if missing_gate_capabilities:
                self.diag(
                    "/phase_gates",
                    "workflow-capability-missing",
                    (
                        "phase architecture gates require requested "
                        "capabilities: "
                        + ", ".join(missing_gate_capabilities)
                    ),
                    "request the exact architect dispatch/verdict authority or remove the gate",
                )
        missing_nudge_capabilities = sorted(
            {"program:select", "nudge:deliver"} - set(capabilities)
        )
        if nudges and missing_nudge_capabilities:
            self.diag(
                "/requested_capabilities",
                "workflow-capability-missing",
                "program standing nudge rules require requested capabilities: "
                + ", ".join(missing_nudge_capabilities),
                "request exact observation/delivery authority or remove the standing rules",
            )
        budgets_raw = raw.get("budgets", {})
        if not isinstance(budgets_raw, dict):
            self.diag("/budgets", "wrong-type", "budgets must be an object", "provide finite named limits")
            budgets_raw = {}
        self.exact_keys(budgets_raw, set(BUDGET_DEFAULTS), "/budgets")
        budgets = {
            key: self.positive_int(budgets_raw.get(key), f"/budgets/{key}", default, BUDGET_LIMITS[key])
            for key, default in BUDGET_DEFAULTS.items()
        }
        if budgets["max_phases"] < len(scope["phases"]):
            self.diag("/budgets/max_phases", "scope-exceeds-budget", "phase scope exceeds max_phases", "raise the policy budget or narrow scope")
        if budgets["max_stories"] < len(scope["story_ids"]):
            self.diag("/budgets/max_stories", "scope-exceeds-budget", "story scope exceeds max_stories", "raise the policy budget or narrow scope")
        nudge_ceiling = sum(int(rule["max_total"]) for rule in nudges)
        if budgets["max_nudges"] < nudge_ceiling:
            self.diag(
                "/budgets/max_nudges", "workflow-exceeds-budget",
                f"standing-rule worst case {nudge_ceiling} exceeds "
                f"max_nudges={budgets['max_nudges']}",
                "raise max_nudges or lower the finite rule ceilings",
            )
        workflow_instances = self.references["workflow_instances"]
        assert isinstance(workflow_instances, dict)
        envelope_budget_keys = {
            "child_runs": "max_child_runs",
            "agent_starts": "max_agent_starts",
            "check_starts": "max_check_starts",
            "loop_rounds": "max_loop_rounds",
            "debate_rounds": "max_debate_rounds",
            "wall_seconds": "max_wall_seconds",
            "artifact_bytes": "max_artifact_bytes",
        }
        requested = set(capabilities)
        binding_by_id = {str(binding["id"]): binding for binding in bindings}
        organization_compiled = organization.get("compiled")
        for binding_id, workflow_instance in sorted(workflow_instances.items()):
            binding = binding_by_id.get(str(binding_id))
            if binding is not None and isinstance(organization_compiled, dict):
                role_requirements, role_issues = validate_workflow_team(
                    organization_compiled,
                    str(binding["team"]),
                    workflow_instance,
                    requested,
                    source=str(organization.get("path") or self.source),
                )
                workflow_instance["organization_requirements"] = role_requirements
                for issue in role_issues:
                    self.diag(
                        issue["pointer"], issue["code"], issue["message"],
                        issue["remediation"], issue["source"],
                    )
            required = {
                capability
                for values in workflow_instance["required_capabilities"].values()
                for capability in values
            }
            missing = sorted(required - requested)
            if missing:
                self.diag(
                    "/requested_capabilities",
                    "workflow-capability-missing",
                    f"binding {binding_id!r} workflow requires undeclared capabilities: "
                    + ", ".join(missing),
                    "request every compiled workflow capability explicitly",
                )
            envelope = workflow_instance["envelope"]
            nudge_starts = sum(
                int(rule["max_total"])
                for rule in nudges
                if rule.get("binding") == binding_id
            )
            for envelope_key, budget_key in envelope_budget_keys.items():
                effective = int(envelope[envelope_key])
                if envelope_key in {"child_runs", "agent_starts"}:
                    effective += nudge_starts
                if effective > int(budgets[budget_key]):
                    self.diag(
                        f"/budgets/{budget_key}",
                        "workflow-exceeds-budget",
                        f"binding {binding_id!r} worst-case {envelope_key}="
                        f"{effective} exceeds {budget_key}={budgets[budget_key]}",
                        "raise the finite program budget or lower workflow bounds",
                    )
            provider_starts = (
                int(envelope["agent_starts"]) + nudge_starts
            )
            for budget_key in (
                "max_provider_starts",
                "max_model_starts",
            ):
                if provider_starts > int(budgets[budget_key]):
                    self.diag(
                        f"/budgets/{budget_key}",
                        "workflow-exceeds-budget",
                        f"binding {binding_id!r} worst-case agent starts="
                        f"{provider_starts} exceeds {budget_key}="
                        f"{budgets[budget_key]}",
                        "raise the finite program budget or lower workflow/nudge bounds",
                    )
        self._bundle_policy_controls()
        self._bundle_node_and_route_checks()
        self._bundle_rubric_fact_checks(bindings)
        self._bundle_team_budget_checks(
            organization, bindings, budgets, phase_gates,
        )
        stops = raw.get("stop_conditions", list(STOP_CONDITIONS))
        if (
            not isinstance(stops, list) or not stops
            or any(stop not in STOP_CONDITIONS for stop in stops)
            or len(set(stops)) != len(stops)
        ):
            self.diag("/stop_conditions", "unsupported-stop", "stop_conditions must be a unique contracted list", "use contracted stop conditions")
            stops = list(STOP_CONDITIONS)
        layout = raw.get("layout", {})
        if not isinstance(layout, dict):
            self.diag("/layout", "wrong-type", "layout must be an object", "provide editor layout or remove it")
            layout = {}

        normalized: dict[str, object] = {
            "kind": PROGRAM_KIND,
            "schema_version": PROGRAM_SCHEMA_VERSION,
            "slug": slug,
            "title": title,
            "scope": scope,
            "organization": organization_slug,
            "bindings": bindings,
            "phase_gates": phase_gates,
            "nudges": nudges,
            "mode_ceiling": mode,
            "requested_capabilities": sorted(capabilities),
            "budgets": budgets,
            "stop_conditions": list(stops),
            "layout": layout,
        }
        if description is not None:
            normalized["description"] = description
        analysis = {
            "binding_by_story": dict(sorted(binding_by_story.items())),
            "scoped_story_count": len(scope["story_ids"]),
            "scoped_phase_count": len(scope["phases"]),
            "candidate_order": [str(story["id"]) for story in self.stories],
        }
        self.diagnostics.sort(
            key=lambda item: (item["source"], item["pointer"], item["code"], item["message"])
        )
        return normalized, self.diagnostics, analysis


def _validate_local_bundle_roster(
    compiler: _Compiler,
    normalized: dict[str, object],
    analysis: dict[str, object],
    driver_config: object,
) -> tuple[dict[str, object], list[dict[str, str]], list[dict[str, str]]]:
    root = compiler.root
    roster_source = _DRIVER_ROSTER_SOURCE
    findings: list[dict[str, str]] = []
    if driver_config is _LOCAL_DRIVER_ROSTER:
        try:
            path = driver_config_path(root)
        except DwError:
            # A root with no git repository (pure fixtures, studio
            # sandboxes) cannot hold a .git-local roster; that is the
            # same honest answer as roster-absent, not a refusal.
            path = None
        if path is None or not path.is_file():
            findings.append({
                "source": roster_source,
                "pointer": "/",
                "code": "driver-roster-unverifiable-locally",
                "type": "unverifiable-locally",
                "message": "the linked bundle is structurally valid, but local driver feasibility cannot be verified because no roster is present",
                "remediation": "configure the local non-secret driver roster, then validate again before requesting a grant",
            })
            return {
                "status": "unverifiable-locally",
                "source": roster_source,
                "profiles": [],
                "stores_credentials": False,
            }, [], findings
        try:
            config = load_driver_config(root)
        except DwError:
            return {
                "status": "invalid",
                "source": roster_source,
                "profiles": [],
                "stores_credentials": False,
            }, [{
                "source": roster_source,
                "pointer": "/",
                "code": "driver-roster-invalid",
                "message": "local driver roster is invalid",
                "remediation": "remove credentials and unsupported fields, then provide closed non-secret driver profiles",
            }], findings
    elif driver_config is None:
        findings.append({
            "source": roster_source,
            "pointer": "/",
            "code": "driver-roster-unverifiable-locally",
            "type": "unverifiable-locally",
            "message": "local driver feasibility was not supplied for this validation",
            "remediation": "validate with a closed local driver roster before requesting a grant",
        })
        return {
            "status": "unverifiable-locally",
            "source": roster_source,
            "profiles": [],
            "stores_credentials": False,
        }, [], findings
    else:
        try:
            config = validate_driver_config(driver_config)
        except DwError:
            return {
                "status": "invalid",
                "source": roster_source,
                "profiles": [],
                "stores_credentials": False,
            }, [{
                "source": roster_source,
                "pointer": "/",
                "code": "driver-roster-invalid",
                "message": "local driver roster is invalid",
                "remediation": "remove credentials and unsupported fields, then provide closed non-secret driver profiles",
            }], findings

    roster = _driver_roster_diagnostics(config)
    diagnostics: list[dict[str, str]] = []
    organization = compiler.references.get("organization")
    instances = compiler.references.get("workflow_instances", {})
    if not isinstance(organization, dict) or not isinstance(instances, dict):
        return roster, diagnostics, findings
    organization_compiled = organization.get("compiled")
    if not isinstance(organization_compiled, dict):
        return roster, diagnostics, findings
    story_bindings = analysis.get("binding_by_story", {})
    for binding in normalized.get("bindings", []):
        if not isinstance(binding, dict):
            continue
        binding_id = str(binding["id"])
        instance = instances.get(binding_id)
        if not isinstance(instance, dict):
            continue
        story_id = next(
            (
                str(candidate) for candidate, candidate_binding
                in sorted(story_bindings.items())
                if candidate_binding == binding_id
            ),
            "bundle-validation",
        )
        assignment = assign_organization_team(
            organization_compiled,
            str(binding["team"]),
            driver_config=config,
            policy_bundle_hash=_sha({
                "program": normalized,
                "purpose": "bundle-validation",
            }),
            story_id=story_id,
            workflow_address=(
                f"program/{normalized['slug']}/story/{story_id}/workflow/{binding_id}"
            ),
            program_capabilities=normalized.get("requested_capabilities", []),
            workflow=instance,
        )
        if assignment.get("applicable"):
            continue
        organization_runtime = organization_compiled["organization"]
        teams = list(organization_runtime.get("teams", []))
        team_index = next(
            (
                index for index, team in enumerate(teams)
                if team.get("id") == binding["team"]
            ),
            0,
        )
        diversity = list(organization_runtime.get("diversity", []))
        for issue in assignment.get("issues", []):
            if not isinstance(issue, dict):
                continue
            code = str(issue.get("code") or "role-unavailable")
            if code == "provider-diversity-unsatisfied":
                pointer = (
                    f"/diversity/{next((index for index, rule in enumerate(diversity) if str(rule.get('id')) in str(issue.get('message'))), 0)}"
                )
            else:
                pointer = f"/teams/{team_index}/roles"
            diagnostics.append({
                "source": str(organization["path"]),
                "pointer": pointer,
                "code": code,
                "message": str(_redact_diagnostic_value(
                    str(issue.get("message") or "local roster cannot satisfy the bound team")
                )),
                "remediation": "configure enough available, capability-compatible, independently-principalled local profiles with the required provider families",
            })
    unique: list[dict[str, str]] = []
    seen: set[tuple[str, str, str, str]] = set()
    for diagnostic in diagnostics:
        key = (
            diagnostic["source"], diagnostic["pointer"],
            diagnostic["code"], diagnostic["message"],
        )
        if key in seen:
            continue
        seen.add(key)
        unique.append(diagnostic)
    unique.sort(
        key=lambda item: (
            item["source"], item["pointer"], item["code"], item["message"],
        )
    )
    return roster, unique, findings


def validate_program(
    root: Path,
    program: object,
    source: str = "program",
    *,
    driver_config: object = _LOCAL_DRIVER_ROSTER,
    bundle_documents: dict[str, object] | None = None,
    roadmap_document: dict[str, object] | None = None,
) -> dict[str, object]:
    compiler = _Compiler(
        root, program, source, bundle_documents=bundle_documents,
        roadmap_document=roadmap_document,
    )
    normalized, diagnostics, analysis = compiler.compile()
    diagnostics.extend(compiler.bundle_diagnostics)
    roster: dict[str, object] = {
        "status": "not-checked",
        "source": _DRIVER_ROSTER_SOURCE,
        "profiles": [],
        "stores_credentials": False,
    }
    findings: list[dict[str, str]] = []
    roster, roster_diagnostics, findings = _validate_local_bundle_roster(
        compiler, normalized, analysis, driver_config,
    )
    diagnostics.extend(roster_diagnostics)
    diagnostics.sort(
        key=lambda item: (
            item["source"], item["pointer"], item["code"], item["message"],
        )
    )
    return {
        "kind": VALIDATION_KIND,
        "schema_version": PROGRAM_SCHEMA_VERSION,
        "valid": not diagnostics,
        "diagnostics": diagnostics,
        "findings": findings,
        "driver_roster": roster,
        "normalized": normalized if not diagnostics else None,
        "starts_work": False,
        "writes_state": False,
        "writes_policy": False,
        "writes_roster": False,
        "writes_grant": False,
        "writes_run": False,
        "writes_roadmap": False,
    }


def validate_program_path(root: Path, path: Path) -> dict[str, object]:
    return validate_program(root, load_program(path), str(path.relative_to(root.resolve())))


def compile_program(root: Path, program: object, source: str = "program") -> dict[str, object]:
    compiler = _Compiler(root, program, source)
    normalized, diagnostics, analysis = compiler.compile()
    if diagnostics:
        raise ProgramValidationError(diagnostics)
    bundle_diagnostics = list(compiler.bundle_diagnostics)
    runtime = {key: value for key, value in normalized.items() if key != "layout"}
    reference_payload = compiler.references
    organization = reference_payload["organization"]
    assert isinstance(organization, dict)
    reference_hashes = {
        "organization": {
            "slug": organization["slug"],
            "semantic_hash": organization["semantic_hash"],
        },
        "workflows": {
            slug: reference["semantic_hash"]
            for slug, reference in sorted(reference_payload["workflows"].items())
        },
        "workflow_instances": {
            binding_id: reference["bundle_hash"]
            for binding_id, reference in sorted(
                reference_payload["workflow_instances"].items()
            )
        },
        "rubrics": {
            slug: reference["semantic_hash"]
            for slug, reference in sorted(reference_payload["rubrics"].items())
        },
    }
    policy_bundle_hash = _sha({
        "compiler": {
            "kind": COMPILED_KIND,
            "schema_version": PROGRAM_SCHEMA_VERSION,
        },
        "program": runtime,
        "reference_hashes": reference_hashes,
    })
    return {
        "kind": COMPILED_KIND,
        "schema_version": PROGRAM_SCHEMA_VERSION,
        "semantic_hash": _sha(runtime),
        "document_hash": _sha(normalized),
        "policy_bundle_hash": policy_bundle_hash,
        "program": runtime,
        "layout": normalized["layout"],
        "references": reference_payload,
        "reference_hashes": reference_hashes,
        "analysis": analysis,
        "bundle_diagnostics": bundle_diagnostics,
    }


def compile_program_path(root: Path, path: Path) -> dict[str, object]:
    return compile_program(root, load_program(path), str(path.relative_to(root.resolve())))


def _binding_for(compiled: dict[str, object], story_id: str) -> dict[str, object] | None:
    binding_id = compiled["analysis"]["binding_by_story"].get(story_id)  # type: ignore[index,union-attr]
    if not binding_id:
        return None
    return next(
        (binding for binding in compiled["program"]["bindings"] if binding["id"] == binding_id),  # type: ignore[index,union-attr]
        None,
    )


def _roadmap_manifest(root: Path, project: object, phase_numbers: list[int]) -> dict[str, object]:
    paths = [project.path / "README.md"]  # type: ignore[attr-defined]
    for phase in discover_phases(project):  # type: ignore[arg-type]
        if phase.number not in phase_numbers:
            continue
        paths.append(phase.path / "current-phase-status.md")
        paths.extend(sorted(phase.path.glob("story-*.md"), key=lambda item: item.name))
    files: list[dict[str, object]] = []
    for path in paths:
        if not path.is_file():
            continue
        data = path.read_bytes()
        files.append({
            "path": str(path.relative_to(root.resolve())),
            "bytes": len(data),
            "sha256": "sha256:" + hashlib.sha256(data).hexdigest(),
        })
    files.sort(key=lambda item: str(item["path"]))
    return {"hash": _sha(files), "files": files}


def _candidate_base(
    story: dict[str, object],
    scope: dict[str, object],
    status_by_id: dict[str, str],
    binding: dict[str, object] | None,
) -> tuple[str, list[str]]:
    in_scope = story["phase"] in scope["phases"] and story["id"] in scope["story_ids"]
    if not in_scope:
        return "out-of-scope", []
    phase_status = str(story["phase_status"])
    status = str(story["status"])
    if phase_status in HOLD_STATUSES:
        return "phase-paused", []
    if phase_status in DONE_STATUSES and status not in DONE_STATUSES:
        return "phase-closed", []
    if status in DONE_STATUSES:
        return "already-done", []
    if status in CUT_STATUSES:
        return "closed", []
    if status in HOLD_STATUSES:
        return "story-held", []
    if status == "blocked":
        return "story-blocked", []
    if status not in {"backlog", "ready", "in-progress"}:
        return "status-not-startable", []
    incomplete = [
        dependency for dependency in story["dependencies"]
        if status_by_id.get(str(dependency)) not in DONE_STATUSES
    ]
    if incomplete:
        return "dependency-incomplete", incomplete
    if binding is None:
        return "binding-missing", []
    return "eligible", []


def _assign_team(
    compiled: dict[str, object],
    story: dict[str, object],
    binding: dict[str, object],
    driver_config: dict[str, object],
) -> tuple[dict[str, object] | None, list[dict[str, str]]]:
    organization = compiled["references"]["organization"]  # type: ignore[index]
    assert isinstance(organization, dict)
    organization_compiled = organization.get("compiled")
    if not isinstance(organization_compiled, dict):
        return None, [{
            "code": "role-unavailable",
            "message": "compiled organization policy is unavailable",
        }]
    workflow_instances = compiled["references"]["workflow_instances"]  # type: ignore[index]
    workflow_instance = workflow_instances.get(str(binding["id"]))
    if not isinstance(workflow_instance, dict):
        return None, [{
            "code": "role-unavailable",
            "message": f"workflow instance for binding {binding['id']!r} is unavailable",
        }]
    assignment_workflow = {
        **workflow_instance,
        "role_lanes": list(workflow_instance.get("role_lanes", [])),
    }
    team = next(
        (
            item for item in organization_compiled["organization"]["teams"]
            if item["id"] == binding["team"]
        ),
        None,
    )
    for gate in compiled["program"].get("phase_gates", []):
        duty = str(gate["role"])
        matches = [
            role for role in (team or {}).get("roles", [])
            if role.get("duty") == duty
        ]
        if len(matches) != 1:
            return None, [{
                "code": "role-unavailable",
                "message": (
                    f"phase gate {gate['id']!r} requires exactly one "
                    f"{duty!r} role in team {binding['team']!r}"
                ),
            }]
        role_id = str(matches[0]["id"])
        assignment_workflow["role_lanes"].append({
            "address": f"phase-gate/{gate['id']}/role/{role_id}",
            "artifact_reads": ["markdown"],
            "artifact_writes": ["verdict"],
            "capabilities": ["agent:dispatch", "verdict:issue"],
            "context_reads": ["artifact"],
            "duty": "architect-gate",
            "node": f"phase-gate/{gate['id']}",
            "role": role_id,
            "workspace": "read-only",
        })
    workflow_address = (
        f"program/{compiled['program']['slug']}/phase/{story['phase']}/"
        f"story/{story['id']}/workflow/{binding['id']}"
    )
    assignment = assign_organization_team(
        organization_compiled,
        str(binding["team"]),
        driver_config=driver_config,
        policy_bundle_hash=str(compiled["policy_bundle_hash"]),
        story_id=str(story["id"]),
        workflow_address=workflow_address,
        program_capabilities=compiled["program"]["requested_capabilities"],
        workflow=assignment_workflow,
    )
    issues = [
        {"code": str(issue["code"]), "message": str(issue["message"])}
        for issue in assignment.get("issues", [])
    ]
    return assignment, issues

def build_program_plan(
    root: Path,
    program: str | Path | dict[str, object],
    *,
    driver_config: dict[str, object] | None = None,
) -> dict[str, object]:
    """Return one deterministic, side-effect-free roadmap selection plan."""
    root = root.resolve()
    if isinstance(program, str):
        path = find_program_path(root, program)
        compiled = compile_program_path(root, path)
        program_path = str(path.relative_to(root))
    elif isinstance(program, Path):
        compiled = compile_program_path(root, program.resolve())
        program_path = str(program.resolve().relative_to(root))
    else:
        compiled = compile_program(root, program)
        program_path = None
    # WLA-30-06: a node the conductor cannot conduct is rejected before
    # grant planning — the one whole-bundle finding that gates this path
    # (the rest reject at the validate surface).
    unconductable = [
        item
        for item in compiled.get("bundle_diagnostics", [])
        if item["code"] == "unconductable-node-type"
    ]
    if unconductable:
        raise ProgramValidationError(unconductable)
    scope = compiled["program"]["scope"]  # type: ignore[index]
    project = next(
        item for item in discover_projects(root)
        if item.slug == scope["project"]
    )
    stories = _project_story_inventory(project)
    status_by_id = {str(story["id"]): str(story["status"]) for story in stories}
    candidates: list[dict[str, object]] = []
    eligible_by_id: dict[str, dict[str, object]] = {}
    for story in stories:
        binding = _binding_for(compiled, str(story["id"]))
        reason, dependencies = _candidate_base(story, scope, status_by_id, binding)
        candidate = {
            "story": story["id"],
            "title": story["title"],
            "phase": story["phase"],
            "order": story["order"],
            "status": story["status"],
            "reason": reason,
            "dependency_blockers": dependencies,
            "binding": binding["id"] if binding else None,
            "workflow": binding["workflow"] if binding else None,
            "team": binding["team"] if binding else None,
        }
        candidates.append(candidate)
        if reason == "eligible":
            eligible_by_id[str(story["id"])] = candidate

    issues: list[dict[str, str]] = []
    selected: dict[str, object] | None = None
    candidate_by_id = {str(candidate["story"]): candidate for candidate in candidates}
    scoped_rows = [story for story in stories if story["id"] in scope["story_ids"]]
    active = [story for story in scoped_rows if story["status"] == "in-progress"]
    if len(active) > 1:
        issues.append({
            "code": "multiple-active-stories",
            "message": "more than one scoped writable story is already in progress",
        })
        for story in active:
            candidate_by_id[str(story["id"])]["reason"] = "already-active"
    elif len(active) == 1 and active[0]["id"] in eligible_by_id:
        selected_story = active[0]
        selected = eligible_by_id[str(selected_story["id"])]
        selected["reason"] = "resume-in-progress"
        for candidate in candidates:
            if candidate is not selected and candidate["reason"] == "eligible":
                candidate["reason"] = "already-active"
    else:
        incomplete_phases = sorted({
            int(story["phase"]) for story in scoped_rows
            if story["status"] not in DONE_STATUSES | CUT_STATUSES
        })
        if not incomplete_phases:
            issues.append({"code": "scope-complete", "message": "all scoped stories are done or closed"})
        else:
            frontier_phase = incomplete_phases[0]
            phase_rows = [story for story in scoped_rows if story["phase"] == frontier_phase]
            phase_rows.sort(key=lambda item: int(item["order"]))
            frontier_stop = next(
                (story for story in phase_rows if _candidate_base(
                    story, scope, status_by_id, _binding_for(compiled, str(story["id"]))
                )[0] in {"phase-paused", "phase-closed", "story-held", "story-blocked"}),
                None,
            )
            first_eligible = next(
                (story for story in phase_rows if story["id"] in eligible_by_id),
                None,
            )
            if frontier_stop is not None and (
                first_eligible is None or int(frontier_stop["order"]) < int(first_eligible["order"])
            ):
                issues.append({
                    "code": "frontier-blocked",
                    "message": f"{frontier_stop['id']} stops the roadmap frontier as {normalize_status(str(frontier_stop['status']))}",
                })
                for candidate in candidates:
                    if candidate["reason"] == "eligible":
                        candidate["reason"] = "frontier-stopped"
            elif first_eligible is not None:
                selected = eligible_by_id[str(first_eligible["id"])]
                selected["reason"] = "selected"
                for candidate in candidates:
                    if candidate is selected:
                        continue
                    if candidate["reason"] == "eligible":
                        candidate["reason"] = (
                            "phase-not-current"
                            if int(candidate["phase"]) != frontier_phase
                            else "frontier-stopped"
                        )
            else:
                issues.append({
                    "code": "no-eligible-work",
                    "message": f"phase {frontier_phase} has no eligible scoped story",
                })
                for candidate in candidates:
                    if candidate["reason"] == "eligible":
                        candidate["reason"] = "phase-not-current"

    selected_story_full = None
    binding = None
    assignment = None
    if selected is not None:
        selected_story_full = next(story for story in stories if story["id"] == selected["story"])
        binding = _binding_for(compiled, str(selected["story"]))
        assert binding is not None
        if driver_config is None:
            try:
                driver_config = load_driver_config(root)
            except DwError as exc:
                issues.append({"code": "role-unavailable", "message": exc.message})
        if driver_config is not None:
            assignment, assignment_issues = _assign_team(
                compiled, selected_story_full, binding, driver_config
            )
            issues.extend(assignment_issues)

    health_issues = check_project(project, root)
    for issue in health_issues:
        issues.append({"code": "roadmap-unhealthy", "message": issue})
    manifest = _roadmap_manifest(root, project, list(scope["phases"]))
    repository = {
        "root": str(root),
        "branch": current_branch(root),
        "head": head_sha(root) or "none",
        "index_tree": write_tree(root) or "unknown",
        "operation": "rewrite" if in_rewrite_state(root) else "normal",
    }
    roster_hash = assignment["roster_hash"] if assignment else None
    bundle_hash = _sha({
        "policy_bundle_hash": compiled["policy_bundle_hash"],
        "roster_hash": roster_hash,
    }) if roster_hash else None
    selection = None
    if selected is not None and selected_story_full is not None and binding is not None:
        workflow_ref = compiled["references"]["workflows"][binding["workflow"]]  # type: ignore[index]
        selection = {
            "story": selected["story"],
            "phase": selected["phase"],
            "status": selected["status"],
            "reason": selected["reason"],
            "why": (
                "resume the only eligible in-progress scoped story"
                if selected["reason"] == "resume-in-progress"
                else "choose the first eligible story in the earliest incomplete scoped phase"
            ),
            "binding": binding["id"],
            "workflow": {
                "slug": binding["workflow"],
                "schema_version": workflow_ref["document"]["schema_version"],
                "version": binding["workflow_version"],
                "semantic_hash": binding["workflow_semantic_hash"],
                "bundle_hash": binding["workflow_bundle_hash"],
                "bindings": binding["with"],
                "source_hashes": workflow_ref.get("source_hashes", {}),
                "envelope": binding["workflow_envelope"],
            },
            "team": binding["team"],
            "rubrics": [
                {
                    "slug": rubric,
                    "schema_version": compiled["references"]["rubrics"][rubric]["document"]["schema_version"],  # type: ignore[index]
                    "version": compiled["references"]["rubrics"][rubric]["document"].get("version"),  # type: ignore[index]
                    "semantic_hash": compiled["references"]["rubrics"][rubric]["semantic_hash"],  # type: ignore[index]
                }
                for rubric in binding["rubrics"]
            ],
            "phase_gates": compiled["program"]["phase_gates"],  # type: ignore[index]
        }
        story_path = Path(str(selected_story_full["story_path"]))
        parsed_hints = parse_localization_hints(read_text(story_path))
        if parsed_hints["affected_files"] or parsed_hints["target_symbols"]:
            try:
                selection["grounding"] = ground_story_path(
                    root, story_path, parsed=parsed_hints
                )
            except DwError as exc:
                # Knowledge is advisory. A stale or missing map refuses to answer,
                # but it does not change selection, applicability, or authority.
                selection["grounding"] = grounding_refusal(
                    root, story_path, exc
                )
    unique_issues: list[dict[str, str]] = []
    seen_issues: set[tuple[str, str]] = set()
    for issue in issues:
        key = (issue["code"], issue["message"])
        if key not in seen_issues:
            unique_issues.append(issue)
            seen_issues.add(key)
    blocking_codes = {
        "multiple-active-stories", "frontier-blocked", "no-eligible-work",
        "role-unavailable", "separation-violation",
        "provider-diversity-unsatisfied", "impossible-quorum",
        "capability-denied", "visibility-denied", "workspace-denied",
        "roadmap-unhealthy",
    }
    applicable = (
        selection is not None and assignment is not None
        and bool(assignment.get("applicable"))
        and not any(issue["code"] in blocking_codes for issue in unique_issues)
    )
    return {
        "kind": PLAN_KIND,
        "schema_version": PROGRAM_SCHEMA_VERSION,
        "applicable": applicable,
        "program": {
            "slug": compiled["program"]["slug"],  # type: ignore[index]
            "path": program_path,
            "semantic_hash": compiled["semantic_hash"],
            "policy_bundle_hash": compiled["policy_bundle_hash"],
            "bundle_hash": bundle_hash,
            "reference_hashes": compiled["reference_hashes"],
            "organization": {
                "slug": compiled["program"]["organization"],  # type: ignore[index]
                "semantic_hash": compiled["reference_hashes"]["organization"]["semantic_hash"],  # type: ignore[index]
            },
            "mode_ceiling": compiled["program"]["mode_ceiling"],  # type: ignore[index]
            "requested_capabilities": compiled["program"]["requested_capabilities"],  # type: ignore[index]
            "budgets": compiled["program"]["budgets"],  # type: ignore[index]
            "stop_conditions": compiled["program"]["stop_conditions"],  # type: ignore[index]
            "nudges": compiled["program"]["nudges"],  # type: ignore[index]
        },
        "repository": repository,
        "roadmap": {
            "project": project.slug,
            "healthy": not health_issues,
            "issues": health_issues,
            "warnings": project_warnings(project, root),
            "snapshot_hash": manifest["hash"],
            "files": manifest["files"],
        },
        "scope": scope,
        "candidates": candidates,
        "selection": selection,
        "assignment": assignment,
        "issues": unique_issues,
        "starts_work": False,
        "writes_policy": False,
        "writes_roadmap": False,
        "writes_run_state": False,
        "creates_grant": False,
    }


def simulate_program(
    root: Path,
    program: str | Path | dict[str, object],
    *,
    driver_config: dict[str, object] | None = None,
) -> dict[str, object]:
    plan = build_program_plan(root, program, driver_config=driver_config)
    return {
        "kind": SIMULATION_KIND,
        "schema_version": PROGRAM_SCHEMA_VERSION,
        "program": plan["program"],
        "scope": plan["scope"],
        "candidates": plan["candidates"],
        "selection": plan["selection"],
        "assignment": plan["assignment"],
        "issues": plan["issues"],
        "starts_work": False,
        "writes_policy": False,
        "writes_roadmap": False,
        "writes_run_state": False,
        "creates_grant": False,
    }


def program_inventory(root: Path) -> dict[str, object]:
    root = root.resolve()
    programs: list[dict[str, object]] = []
    for path in discover_program_paths(root):
        try:
            raw = load_program(path)
            validation = validate_program(root, raw, str(path.relative_to(root)))
            item: dict[str, object] = {
                "name": path.stem,
                "path": str(path.relative_to(root)),
                "slug": raw.get("slug"),
                "title": raw.get("title"),
                "valid": validation["valid"],
                "diagnostics": validation["diagnostics"],
            }
            if validation["valid"]:
                compiled = compile_program(root, raw, str(path.relative_to(root)))
                item["semantic_hash"] = compiled["semantic_hash"]
                item["policy_bundle_hash"] = compiled["policy_bundle_hash"]
            programs.append(item)
        except DwError as exc:
            programs.append({
                "name": path.stem,
                "path": str(path.relative_to(root)),
                "slug": None,
                "title": None,
                "valid": False,
                "diagnostics": [{
                    "source": str(path.relative_to(root)),
                    "pointer": "/",
                    "code": "parse-error",
                    "message": exc.message,
                    "remediation": "fix the JSON document",
                }],
            })
    return {
        "kind": INVENTORY_KIND,
        "schema_version": PROGRAM_SCHEMA_VERSION,
        "programs": programs,
        "healthy": all(bool(item["valid"]) for item in programs),
        "starts_work": False,
        "writes_state": False,
    }
