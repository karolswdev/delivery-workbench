"""Pure Phase-26 program policy compilation and roadmap planning.

This first slice deliberately stops before grants or execution.  It reads a
tracked program plus its referenced policy documents, validates the explicit
roadmap scope and binding rules, derives one stable frontier selection, and
assigns logical team roles against the existing local driver roster.  It never
creates a program store, grant, ledger, observer, workspace, or roadmap write.

The contract is ``docs/programs.md`` (WLA-26-01/02).
"""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any

from .gitio import current_branch, head_sha, in_rewrite_state, write_tree
from .model import (
    CUT_STATUSES,
    DONE_STATUSES,
    HOLD_STATUSES,
    STORY_STATUSES,
    DwError,
    normalize_status,
)
from .orchestration import canonical_json
from .orchestration_driver import driver_capability, driver_inventory, load_driver_config
from .program_workflow import WorkflowValidationError, compile_workflow
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
ORGANIZATION_KIND = "delivery-workbench-organization"
RUBRIC_KIND = "delivery-workbench-rubric"

VALIDATION_KIND = "delivery-workbench-program-validation"
COMPILED_KIND = "delivery-workbench-compiled-program"
INVENTORY_KIND = "delivery-workbench-program-list"
SIMULATION_KIND = "delivery-workbench-program-simulation"
PLAN_KIND = "delivery-workbench-program-plan"

MODE_CEILINGS = ("advisory", "checkpointed", "continuous")
SELECTION_POLICIES = ("roadmap-frontier-v1",)
BLOCKED_POLICIES = ("stop",)

PROGRAM_CAPABILITIES = (
    "agent:dispatch",
    "check:execute",
    "workspace:write",
    "nudge:deliver",
    "notification:send",
    "evidence:materialize",
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
    "max_check_starts": 500,
    "max_loop_rounds": 100,
    "max_debate_rounds": 20,
    "max_repairs_per_story": 3,
    "max_verdicts": 200,
    "max_integrations": 20,
    "max_commits": 20,
    "max_pushes": 20,
    "max_nudges": 50,
    "max_artifact_bytes": 50_000_000,
    "max_wall_seconds": 172_800,
}
BUDGET_LIMITS = {
    "max_phases": 100,
    "max_stories": 2_000,
    "max_child_runs": 20_000,
    "max_agent_starts": 50_000,
    "max_check_starts": 100_000,
    "max_loop_rounds": 20_000,
    "max_debate_rounds": 2_000,
    "max_repairs_per_story": 100,
    "max_verdicts": 50_000,
    "max_integrations": 2_000,
    "max_commits": 2_000,
    "max_pushes": 2_000,
    "max_nudges": 10_000,
    "max_artifact_bytes": 10_000_000_000,
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

DUTIES = (
    "implementer",
    "verifier",
    "meta-verifier",
    "master-architect",
    "researcher",
    "reviewer",
    "repairer",
    "critic",
    "judge",
)

_SAFE_ID_RE = re.compile(r"^[a-z][a-z0-9]*(?:[-_][a-z0-9]+)*$")
_STORY_ID_RE = re.compile(r"^[A-Z][A-Z0-9]*-\d+-\d+$")
_DEPENDENCY_RE = re.compile(r"[A-Z][A-Z0-9]*-\d+-\d+")

_PROGRAM_KEYS = {
    "kind", "schema_version", "slug", "title", "description", "scope",
    "organization", "bindings", "phase_gates", "mode_ceiling",
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

_ORG_KEYS = {
    "kind", "schema_version", "slug", "title", "description", "agents",
    "pools", "teams", "councils", "layout",
}
_AGENT_KEYS = {"id", "profile", "duties", "workspace_domain", "weight"}
_POOL_KEYS = {"id", "agents"}
_TEAM_KEYS = {"id", "roles"}
_ROLE_KEYS = {"id", "duty", "pool", "required", "independent_from"}
_COUNCIL_KEYS = {"id", "members", "judge", "quorum", "meta_verifier"}

_WORKFLOW_KEYS = {
    "kind", "schema_version", "slug", "title", "description", "version",
    "parameters", "defaults", "nodes", "terminals", "layout",
}
_RUBRIC_KEYS = {
    "kind", "schema_version", "slug", "title", "description", "version",
    "subject_type", "result_vocabulary", "freshness", "criteria",
    "aggregation", "layout",
}


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


class _Compiler:
    def __init__(self, root: Path, raw: object, source: str = "program") -> None:
        self.root = root.resolve()
        self.raw = raw
        self.source = source
        self.diagnostics: list[dict[str, str]] = []
        self.references: dict[str, object] = {
            "organization": None,
            "workflows": {},
            "workflow_instances": {},
            "rubrics": {},
        }
        self.project: object | None = None
        self.stories: list[dict[str, object]] = []

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

    def load_reference(
        self,
        family: str,
        slug: str,
        kind: str,
        allowed_keys: set[str],
        pointer: str,
    ) -> dict[str, object] | None:
        found = _reference_by_slug(self.root, family, slug)
        if found is None:
            self.diag(pointer, f"dangling-{kind.split('-')[-1]}-reference", f"cannot resolve {kind} {slug!r}", f"add one unambiguous pm/{family}/{slug}.json policy")
            return None
        path, raw = found
        source = str(path.relative_to(self.root))
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

    def normalize_organization(self, slug: str) -> dict[str, object]:
        ref = self.load_reference(
            "organizations", slug, ORGANIZATION_KIND, _ORG_KEYS, "/organization"
        )
        if ref is None:
            return {"slug": slug, "agents": [], "pools": [], "teams": [], "councils": []}
        raw = ref["document"]
        assert isinstance(raw, dict)
        source = str(ref["path"])
        agents_raw = raw.get("agents")
        if not isinstance(agents_raw, list) or not agents_raw:
            self.diag("/agents", "missing-agents", "organization needs at least one logical agent", "declare bounded logical agents", source)
            agents_raw = []
        agents: list[dict[str, object]] = []
        agent_ids: set[str] = set()
        for index, item in enumerate(agents_raw):
            pointer = f"/agents/{index}"
            if not isinstance(item, dict):
                self.diag(pointer, "wrong-type", "agent must be an object", "provide an agent object", source)
                continue
            self.exact_keys(item, _AGENT_KEYS, pointer, source=source)
            agent_id = item.get("id")
            profile = item.get("profile")
            if not isinstance(agent_id, str) or not _SAFE_ID_RE.fullmatch(agent_id):
                self.diag(f"{pointer}/id", "unsafe-selector", "agent id is unsafe", "use a stable lowercase id", source)
                agent_id = ""
            if agent_id in agent_ids:
                self.diag(f"{pointer}/id", "duplicate-id", f"duplicate agent id {agent_id!r}", "use unique ids", source)
            agent_ids.add(str(agent_id))
            if not isinstance(profile, str) or not _SAFE_ID_RE.fullmatch(profile):
                self.diag(f"{pointer}/profile", "unsafe-selector", "profile selector is unsafe", "use a configured logical profile", source)
                profile = ""
            duties = item.get("duties")
            if (
                not isinstance(duties, list) or not duties
                or any(duty not in DUTIES for duty in duties)
                or len(set(duties)) != len(duties)
            ):
                self.diag(f"{pointer}/duties", "unsupported-duty", "duties must be a unique non-empty contracted duty list", "use contracted duty names", source)
                duties = []
            domain = item.get("workspace_domain")
            if not isinstance(domain, str) or not _SAFE_ID_RE.fullmatch(domain):
                self.diag(f"{pointer}/workspace_domain", "unsafe-selector", "workspace domain is unsafe", "use a stable isolation-domain id", source)
                domain = ""
            weight = self.positive_int(
                item.get("weight"), f"{pointer}/weight", 1, 100,
                source=source,
            )
            agents.append({
                "id": agent_id,
                "profile": profile,
                "duties": list(duties),
                "workspace_domain": domain,
                "weight": weight,
            })

        pools_raw = raw.get("pools")
        if not isinstance(pools_raw, list) or not pools_raw:
            self.diag("/pools", "missing-pools", "organization needs at least one agent pool", "declare explicit pools", source)
            pools_raw = []
        pools: list[dict[str, object]] = []
        pool_ids: set[str] = set()
        for index, item in enumerate(pools_raw):
            pointer = f"/pools/{index}"
            if not isinstance(item, dict):
                self.diag(pointer, "wrong-type", "pool must be an object", "provide a pool object", source)
                continue
            self.exact_keys(item, _POOL_KEYS, pointer, source=source)
            pool_id = item.get("id")
            members = item.get("agents")
            if not isinstance(pool_id, str) or not _SAFE_ID_RE.fullmatch(pool_id):
                self.diag(f"{pointer}/id", "unsafe-selector", "pool id is unsafe", "use a stable lowercase id", source)
                pool_id = ""
            if pool_id in pool_ids:
                self.diag(f"{pointer}/id", "duplicate-id", f"duplicate pool id {pool_id!r}", "use unique ids", source)
            pool_ids.add(str(pool_id))
            if (
                not isinstance(members, list) or not members
                or any(member not in agent_ids for member in members)
                or len(set(members)) != len(members)
            ):
                self.diag(f"{pointer}/agents", "dangling-agent-reference", "pool agents must be unique declared agent ids", "fix the pool membership", source)
                members = []
            pools.append({"id": pool_id, "agents": list(members)})

        teams_raw = raw.get("teams")
        if not isinstance(teams_raw, list) or not teams_raw:
            self.diag("/teams", "missing-teams", "organization needs at least one team", "declare a team with implementer and verifier roles", source)
            teams_raw = []
        teams: list[dict[str, object]] = []
        team_ids: set[str] = set()
        all_role_ids: set[str] = set()
        role_duties: dict[str, str] = {}
        for team_index, item in enumerate(teams_raw):
            pointer = f"/teams/{team_index}"
            if not isinstance(item, dict):
                self.diag(pointer, "wrong-type", "team must be an object", "provide a team object", source)
                continue
            self.exact_keys(item, _TEAM_KEYS, pointer, source=source)
            team_id = item.get("id")
            if not isinstance(team_id, str) or not _SAFE_ID_RE.fullmatch(team_id):
                self.diag(f"{pointer}/id", "unsafe-selector", "team id is unsafe", "use a stable lowercase id", source)
                team_id = ""
            if team_id in team_ids:
                self.diag(f"{pointer}/id", "duplicate-id", f"duplicate team id {team_id!r}", "use unique ids", source)
            team_ids.add(str(team_id))
            roles_raw = item.get("roles")
            if not isinstance(roles_raw, list) or not roles_raw:
                self.diag(f"{pointer}/roles", "missing-roles", "team needs role slots", "declare implementer and verifier slots", source)
                roles_raw = []
            roles: list[dict[str, object]] = []
            role_ids: set[str] = set()
            for role_index, role in enumerate(roles_raw):
                role_pointer = f"{pointer}/roles/{role_index}"
                if not isinstance(role, dict):
                    self.diag(role_pointer, "wrong-type", "role must be an object", "provide a role object", source)
                    continue
                self.exact_keys(role, _ROLE_KEYS, role_pointer, source=source)
                role_id = role.get("id")
                duty = role.get("duty")
                pool = role.get("pool")
                if not isinstance(role_id, str) or not _SAFE_ID_RE.fullmatch(role_id):
                    self.diag(f"{role_pointer}/id", "unsafe-selector", "role id is unsafe", "use a stable lowercase id", source)
                    role_id = ""
                if role_id in role_ids:
                    self.diag(f"{role_pointer}/id", "duplicate-id", f"duplicate role id {role_id!r}", "use unique team role ids", source)
                if role_id in all_role_ids:
                    self.diag(f"{role_pointer}/id", "duplicate-id", f"organization role id {role_id!r} is ambiguous across teams", "use organization-wide unique role ids", source)
                role_ids.add(str(role_id))
                all_role_ids.add(str(role_id))
                if duty not in DUTIES:
                    self.diag(f"{role_pointer}/duty", "unsupported-duty", f"unsupported duty {duty!r}", "use a contracted duty", source)
                    duty = ""
                role_duties[str(role_id)] = str(duty)
                if pool not in pool_ids:
                    self.diag(f"{role_pointer}/pool", "dangling-pool-reference", f"unknown pool {pool!r}", "reference a declared pool", source)
                    pool = ""
                required = role.get("required", True)
                if not isinstance(required, bool):
                    self.diag(f"{role_pointer}/required", "wrong-type", "required must be boolean", "use true or false", source)
                    required = True
                independence = role.get("independent_from", [])
                if (
                    not isinstance(independence, list)
                    or any(not isinstance(value, str) for value in independence)
                    or len(set(independence)) != len(independence)
                ):
                    self.diag(f"{role_pointer}/independent_from", "wrong-type", "independent_from must be a unique role-id list", "provide declared role ids", source)
                    independence = []
                roles.append({
                    "id": role_id,
                    "duty": duty,
                    "pool": pool,
                    "required": required,
                    "independent_from": list(independence),
                })
            for role_index, role in enumerate(roles):
                for dependency in role["independent_from"]:
                    if dependency not in role_ids:
                        self.diag(f"{pointer}/roles/{role_index}/independent_from", "dangling-role-reference", f"unknown role {dependency!r}", "reference a role in the same team", source)
                    elif next(
                        index for index, candidate in enumerate(roles)
                        if candidate["id"] == dependency
                    ) >= role_index:
                        self.diag(
                            f"{pointer}/roles/{role_index}/independent_from",
                            "role-order",
                            f"independence role {dependency!r} must be assigned first",
                            "order prerequisite roles before dependent roles",
                            source,
                        )
            implementers = [role for role in roles if role["duty"] == "implementer"]
            verifiers = [role for role in roles if role["duty"] == "verifier"]
            if len(implementers) != 1 or len(verifiers) != 1:
                self.diag(f"{pointer}/roles", "missing-separation", "a team requires exactly one implementer and one verifier slot in this slice", "declare one of each", source)
            elif not implementers[0]["required"] or not verifiers[0]["required"]:
                self.diag(f"{pointer}/roles", "missing-separation", "implementer and independent verifier slots must both be required", "set required to true for both delivery duties", source)
            elif implementers[0]["id"] not in verifiers[0]["independent_from"]:
                self.diag(f"{pointer}/roles", "missing-separation", "verifier must declare independence from implementer", "add the implementer role id to independent_from", source)
            teams.append({"id": team_id, "roles": roles})

        councils_raw = raw.get("councils", [])
        if not isinstance(councils_raw, list):
            self.diag("/councils", "wrong-type", "councils must be an array", "provide an array or remove it", source)
            councils_raw = []
        councils: list[dict[str, object]] = []
        council_ids: set[str] = set()
        for index, item in enumerate(councils_raw):
            pointer = f"/councils/{index}"
            if not isinstance(item, dict):
                self.diag(pointer, "wrong-type", "council must be an object", "provide a council object", source)
                continue
            self.exact_keys(item, _COUNCIL_KEYS, pointer, source=source)
            council_id = item.get("id")
            if not isinstance(council_id, str) or not _SAFE_ID_RE.fullmatch(council_id):
                self.diag(f"{pointer}/id", "unsafe-selector", "council id is unsafe", "use a stable lowercase id", source)
                council_id = ""
            if council_id in council_ids:
                self.diag(f"{pointer}/id", "duplicate-id", f"duplicate council id {council_id!r}", "use unique ids", source)
            council_ids.add(str(council_id))
            members = item.get("members", [])
            if (
                not isinstance(members, list) or not members
                or any(not isinstance(member, str) for member in members)
                or len(set(members)) != len(members)
                or any(member not in all_role_ids for member in members)
            ):
                self.diag(f"{pointer}/members", "dangling-role-reference", "council members must be unique declared team roles", "fix member roles", source)
                members = []
            judge = item.get("judge")
            if not isinstance(judge, str) or judge not in members:
                self.diag(f"{pointer}/judge", "dangling-role-reference", "council judge must name one declared member role", "choose one council member role", source)
                judge = None
            meta_verifier = item.get("meta_verifier")
            if meta_verifier is not None and (
                not isinstance(meta_verifier, str)
                or meta_verifier not in all_role_ids
                or role_duties.get(meta_verifier) != "meta-verifier"
            ):
                self.diag(f"{pointer}/meta_verifier", "dangling-role-reference", "meta_verifier must name a declared meta-verifier role", "choose a declared meta-verifier role or remove the field", source)
                meta_verifier = None
            quorum = self.positive_int(
                item.get("quorum"), f"{pointer}/quorum", 1, 50,
                source=source,
            )
            if members and quorum > len(members):
                self.diag(f"{pointer}/quorum", "impossible-quorum", "quorum exceeds declared member slots", "lower quorum or add members", source)
            councils.append({
                "id": council_id,
                "members": list(members),
                "judge": judge,
                "quorum": quorum,
                "meta_verifier": meta_verifier,
            })

        normalized = {
            "slug": slug,
            "agents": agents,
            "pools": pools,
            "teams": teams,
            "councils": councils,
            "path": source,
            "semantic_hash": ref["semantic_hash"],
            "document_hash": ref["document_hash"],
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
                rubric_ref = self.load_reference(
                    "rubrics", rubric, RUBRIC_KIND, _RUBRIC_KEYS,
                    f"{pointer}/rubrics",
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
            rubric_ref = self.load_reference(
                "rubrics", rubric, RUBRIC_KIND, _RUBRIC_KEYS,
                f"{pointer}/rubric",
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
        for binding_id, workflow_instance in sorted(workflow_instances.items()):
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
            for envelope_key, budget_key in envelope_budget_keys.items():
                if int(envelope[envelope_key]) > int(budgets[budget_key]):
                    self.diag(
                        f"/budgets/{budget_key}",
                        "workflow-exceeds-budget",
                        f"binding {binding_id!r} worst-case {envelope_key}="
                        f"{envelope[envelope_key]} exceeds {budget_key}={budgets[budget_key]}",
                        "raise the finite program budget or lower workflow bounds",
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


def validate_program(root: Path, program: object, source: str = "program") -> dict[str, object]:
    normalized, diagnostics, _analysis = _Compiler(root, program, source).compile()
    return {
        "kind": VALIDATION_KIND,
        "schema_version": PROGRAM_SCHEMA_VERSION,
        "valid": not diagnostics,
        "diagnostics": diagnostics,
        "normalized": normalized if not diagnostics else None,
        "starts_work": False,
        "writes_state": False,
    }


def validate_program_path(root: Path, path: Path) -> dict[str, object]:
    return validate_program(root, load_program(path), str(path.relative_to(root.resolve())))


def compile_program(root: Path, program: object, source: str = "program") -> dict[str, object]:
    compiler = _Compiler(root, program, source)
    normalized, diagnostics, analysis = compiler.compile()
    if diagnostics:
        raise ProgramValidationError(diagnostics)
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


def _role_requirements(duty: str) -> tuple[set[str], str, bool]:
    if duty in {"implementer", "repairer"}:
        return {"repository-read", "repository-write"}, "isolated-worktree", True
    return {"repository-read"}, "read-only", False


def _assign_team(
    compiled: dict[str, object],
    story: dict[str, object],
    binding: dict[str, object],
    driver_config: dict[str, object],
) -> tuple[dict[str, object] | None, list[dict[str, str]]]:
    organization = compiled["references"]["organization"]  # type: ignore[index]
    assert isinstance(organization, dict)
    team = next(
        (item for item in organization["teams"] if item["id"] == binding["team"]),
        None,
    )
    if team is None:
        return None, [{
            "code": "role-unavailable",
            "message": f"team {binding['team']!r} is not available",
        }]
    agents = {str(agent["id"]): agent for agent in organization["agents"]}
    pools = {str(pool["id"]): list(pool["agents"]) for pool in organization["pools"]}
    assignments: list[dict[str, object]] = []
    issues: list[dict[str, str]] = []
    assigned_by_role: dict[str, dict[str, object]] = {}
    roster = driver_inventory(driver_config)
    roster_hash = _sha(roster)
    for role in team["roles"]:
        candidates: list[dict[str, object]] = []
        exclusions: list[dict[str, str]] = []
        required_capabilities, workspace_mode, requires_write = _role_requirements(str(role["duty"]))
        for agent_id in pools.get(str(role["pool"]), []):
            agent = agents.get(agent_id)
            if agent is None:
                exclusions.append({"agent": agent_id, "reason": "agent-not-declared"})
                continue
            if role["duty"] not in agent["duties"]:
                exclusions.append({"agent": agent_id, "reason": "duty-not-allowed"})
                continue
            try:
                capability = driver_capability(driver_config, str(agent["profile"]))
            except DwError:
                exclusions.append({"agent": agent_id, "reason": "profile-unconfigured"})
                continue
            available_capabilities = set(capability["capabilities"])
            modes = set(capability["workspace_modes"])
            if not required_capabilities <= available_capabilities:
                exclusions.append({"agent": agent_id, "reason": "capability-mismatch"})
                continue
            if workspace_mode not in modes:
                exclusions.append({"agent": agent_id, "reason": "workspace-mismatch"})
                continue
            if not requires_write and "repository-write" in available_capabilities:
                exclusions.append({"agent": agent_id, "reason": "verifier-write-capable"})
                continue
            conflict = None
            for prior_role_id in role["independent_from"]:
                prior = assigned_by_role.get(str(prior_role_id))
                if prior is None:
                    continue
                if prior["profile"] == agent["profile"]:
                    conflict = "same-profile-principal"
                elif prior["workspace_domain"] == agent["workspace_domain"]:
                    conflict = "same-workspace-domain"
            if conflict:
                exclusions.append({"agent": agent_id, "reason": conflict})
                continue
            rank_input = (
                f"{compiled['policy_bundle_hash']}|{story['id']}|"
                f"program/{story['phase']}/{story['id']}|{role['id']}|{agent_id}"
            )
            rank_value = int(
                hashlib.sha256(rank_input.encode("utf-8")).hexdigest(), 16
            ) * int(agent["weight"])
            rank = f"{rank_value:066x}"
            candidates.append({
                "agent": agent_id,
                "profile": agent["profile"],
                "workspace_domain": agent["workspace_domain"],
                "weight": agent["weight"],
                "driver": capability,
                "rank": rank,
            })
        candidates.sort(key=lambda item: (str(item["rank"]), str(item["agent"])), reverse=True)
        if not candidates:
            if role["required"]:
                issues.append({
                    "code": "role-unavailable",
                    "message": f"required role {role['id']!r} has no eligible agent",
                })
            assignments.append({
                "role": role["id"],
                "duty": role["duty"],
                "required": role["required"],
                "selected": None,
                "candidates": [],
                "exclusions": exclusions,
            })
            continue
        selected = dict(candidates[0])
        selected["principal_fingerprint"] = _sha({
            "agent": selected["agent"],
            "profile": selected["profile"],
            "driver": selected["driver"],
            "roster_hash": roster_hash,
        })
        assigned_by_role[str(role["id"])] = selected
        assignments.append({
            "role": role["id"],
            "duty": role["duty"],
            "required": role["required"],
            "selected": selected,
            "candidates": candidates,
            "exclusions": exclusions,
        })
    implementer = next((item for item in assignments if item["duty"] == "implementer"), None)
    verifier = next((item for item in assignments if item["duty"] == "verifier"), None)
    if (
        implementer and verifier and implementer["selected"] and verifier["selected"]
        and (
            implementer["selected"]["profile"] == verifier["selected"]["profile"]
            or implementer["selected"]["workspace_domain"] == verifier["selected"]["workspace_domain"]
        )
    ):
        issues.append({
            "code": "separation-violation",
            "message": "implementer and verifier do not have independent profile/workspace identities",
        })
    if issues:
        return None, issues
    role_summary = {
        str(item["duty"]): item["selected"]
        for item in assignments if item["selected"] is not None
    }
    return {
        "team": team["id"],
        "roster_hash": roster_hash,
        "roles": assignments,
        "implementer": role_summary.get("implementer"),
        "verifier": role_summary.get("verifier"),
        "meta_verifier": role_summary.get("meta-verifier"),
        "master_architect": role_summary.get("master-architect"),
        "councils": organization["councils"],
        "why": (
            "filtered declared pools by duty, local profile capabilities, "
            "workspace mode, and independence; ranked remaining candidates "
            "with rendezvous-sha256-v1"
        ),
    }, []


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
    unique_issues: list[dict[str, str]] = []
    seen_issues: set[tuple[str, str]] = set()
    for issue in issues:
        key = (issue["code"], issue["message"])
        if key not in seen_issues:
            unique_issues.append(issue)
            seen_issues.add(key)
    blocking_codes = {
        "multiple-active-stories", "frontier-blocked", "no-eligible-work",
        "role-unavailable", "separation-violation", "roadmap-unhealthy",
    }
    applicable = (
        selection is not None and assignment is not None
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
