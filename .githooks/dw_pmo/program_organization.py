"""Pure Phase-26 organization compilation and deterministic assignment.

Tracked organization policy names logical agents, pools, role duties, packet
visibility, separation, councils, concurrency, and finite replacement rules.
Operator-local driver configuration resolves those logical candidates to
available principals and adapter capability fingerprints.  Every function in
this module is read-only: it starts no agent, creates no grant or session, and
writes no policy, roadmap, or run state.

The contract is ``docs/programs.md`` (WLA-26-01/04).
"""

from __future__ import annotations

import hashlib
import itertools
import json
import re
from pathlib import Path
from typing import Any

from .model import DwError
from .orchestration import CAPABILITIES as DRIVER_CAPABILITIES
from .orchestration import canonical_json
from .orchestration_driver import (
    driver_capability,
    driver_inventory,
    validate_driver_config,
)
from .program_workflow import ARTIFACT_KINDS, PROGRAM_CAPABILITIES


ORGANIZATION_KIND = "delivery-workbench-organization"
ORGANIZATION_SCHEMA_VERSION = 1
COMPILED_ORGANIZATION_KIND = "delivery-workbench-compiled-organization"
VALIDATION_KIND = "delivery-workbench-organization-validation"
INVENTORY_KIND = "delivery-workbench-organization-list"
SIMULATION_KIND = "delivery-workbench-organization-simulation"
ASSIGNMENT_KIND = "delivery-workbench-team-assignment"
REPLACEMENT_KIND = "delivery-workbench-assignment-replacement"

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
WORKSPACE_MODES = ("read-only", "isolated-worktree")
CONTEXT_CHANNELS = (
    "story",
    "phase",
    "roadmap",
    "workflow-inputs",
    "candidate-diff",
    "mechanical-receipts",
    "prior-verdicts",
    "dissent",
    "proposal",
    "public-artifacts",
)
EXPRESSION_KINDS = ("context", "parameter", "literal", "artifact")
REPLACEMENT_REASONS = (
    "unavailable",
    "lost",
    "failed",
    "refused",
    "conflicted",
)
EXHAUSTION_ROUTES = ("block", "escalate", "checkpoint", "abort")
JUDGMENT_DUTIES = {"verifier", "meta-verifier", "master-architect", "judge"}

_SAFE_ID_RE = re.compile(r"^[a-z][a-z0-9]*(?:[-_][a-z0-9]+)*$")
_SCHEMA_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_.:/@-]{0,199}$")
_ORG_KEYS = {
    "kind", "schema_version", "slug", "title", "description", "agents",
    "pools", "teams", "councils", "layout",
}
_AGENT_KEYS = {
    "id", "profile", "duties", "workspace_domain", "capability_ceiling",
    "max_concurrency", "weight",
}
_POOL_KEYS = {"id", "agents"}
_TEAM_KEYS = {"id", "roles"}
_ROLE_KEYS = {
    "id", "duty", "pool", "required", "cardinality",
    "capability_ceiling", "driver_capabilities", "workspace", "context",
    "artifacts", "output_schema", "verdict_schema", "max_concurrency",
    "resource_groups", "may_request", "may_judge", "independent_from",
    "replacement",
}
_CONTEXT_KEYS = {"allow", "expressions", "max_bytes"}
_ARTIFACT_KEYS = {"read", "write", "max_bytes"}
_REPLACEMENT_KEYS = {
    "reasons", "max_replacements", "fallback_pools", "on_exhausted",
    "preserve_history",
}
_COUNCIL_KEYS = {
    "id", "members", "judge", "quorum", "meta_verifier",
    "distinct_principals", "decision", "audit", "budgets",
}
_COUNCIL_REQUIRED_KEYS = {
    "id", "members", "judge", "quorum", "meta_verifier",
    "distinct_principals",
}
_COUNCIL_DECISION_KEYS = {"method", "weights", "threshold", "veto_roles"}
_COUNCIL_AUDIT_KEYS = {
    "mode", "sample_size", "on_overturn", "on_escalate",
}
_COUNCIL_BUDGET_KEYS = {
    "max_rounds", "max_speaker_starts", "max_artifacts",
    "max_output_bytes", "max_tokens", "max_wall_seconds",
}
COUNCIL_DECISION_METHODS = ("majority", "weighted", "unanimous", "judge")
COUNCIL_AUDIT_MODES = ("none", "sample", "full")
COUNCIL_RESULT_ROUTES = ("repair", "escalate", "block", "checkpoint", "abort")

_COUNCIL_BUDGET_DEFAULTS = {
    "max_rounds": 20,
    "max_speaker_starts": 2_048,
    "max_artifacts": 2_048,
    "max_output_bytes": 100_000_000,
    "max_tokens": 10_000_000,
    "max_wall_seconds": 1_728_000,
}
_COUNCIL_BUDGET_LIMITS = {
    "max_rounds": 100,
    "max_speaker_starts": 100_000,
    "max_artifacts": 100_000,
    "max_output_bytes": 10_000_000_000,
    "max_tokens": 1_000_000_000,
    "max_wall_seconds": 31_536_000,
}

_MAX_AGENTS = 128
_MAX_POOLS = 64
_MAX_TEAMS = 64
_MAX_ROLES = 64
_MAX_ROLE_CARDINALITY = 16
_MAX_TOTAL_SLOTS = 128
_MAX_REPLACEMENTS = 20
_MAX_CONTEXT_BYTES = 2_000_000
_MAX_ARTIFACT_BYTES = 100_000_000


class OrganizationValidationError(DwError):
    """A deterministic organization refusal carrying every diagnostic."""

    def __init__(self, diagnostics: list[dict[str, str]]) -> None:
        self.diagnostics = diagnostics
        first = diagnostics[0] if diagnostics else {
            "source": "organization",
            "pointer": "/",
            "message": "organization is invalid",
        }
        super().__init__(
            "organization invalid at "
            f"{first['source']}:{first['pointer']}: {first['message']}"
        )


class _DuplicateJSONKey(ValueError):
    pass


def _object_pairs(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise _DuplicateJSONKey(key)
        result[key] = value
    return result


def _sha(value: object) -> str:
    return "sha256:" + hashlib.sha256(
        canonical_json(value).encode("utf-8")
    ).hexdigest()


def organization_dir(root: Path) -> Path:
    return root.resolve() / "pm" / "organizations"


def discover_organization_paths(root: Path) -> list[Path]:
    directory = organization_dir(root)
    if not directory.is_dir():
        return []
    return sorted(
        path for path in directory.glob("*.json")
        if path.is_file() and not path.is_symlink()
    )


def parse_organization_text(text: str, source: str = "organization") -> dict[str, object]:
    try:
        value = json.loads(text, object_pairs_hook=_object_pairs)
    except _DuplicateJSONKey as exc:
        raise DwError(f"duplicate JSON key in {source}: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise DwError(f"cannot parse organization JSON {source}: {exc}") from exc
    if not isinstance(value, dict):
        raise DwError(f"organization document must be an object: {source}")
    return value


def load_organization(path: Path) -> dict[str, object]:
    try:
        return parse_organization_text(path.read_text(encoding="utf-8"), str(path))
    except FileNotFoundError as exc:
        raise DwError(f"organization policy not found: {path}") from exc


def find_organization_path(root: Path, selector: str) -> Path:
    if not isinstance(selector, str) or not _SAFE_ID_RE.fullmatch(selector):
        raise DwError(f"unsafe organization selector: {selector!r}")
    matches: list[Path] = []
    for path in discover_organization_paths(root):
        try:
            raw = load_organization(path)
        except DwError:
            if path.stem == selector:
                matches.append(path)
            continue
        if path.stem == selector or raw.get("slug") == selector:
            matches.append(path)
    unique = sorted(set(matches))
    if not unique:
        raise DwError(
            f"organization not found: {selector}; expected one direct-contained "
            "JSON file under pm/organizations"
        )
    if len(unique) != 1:
        raise DwError(f"organization selector is ambiguous: {selector}")
    return unique[0]


class _Compiler:
    def __init__(self, raw: object, source: str) -> None:
        self.raw = raw
        self.source = source
        self.diagnostics: list[dict[str, str]] = []

    def diag(
        self,
        pointer: str,
        code: str,
        message: str,
        remediation: str,
    ) -> None:
        self.diagnostics.append({
            "source": self.source,
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
        required: set[str] | None = None,
    ) -> None:
        for key in sorted(set(value) - allowed):
            self.diag(
                f"{pointer}/{key}", "unknown-key", f"unknown key {key!r}",
                "remove the field or use a contracted schema key",
            )
        for key in sorted((required or set()) - set(value)):
            self.diag(
                f"{pointer}/{key}", "missing-key", f"required key {key!r} is absent",
                "declare the field explicitly",
            )

    def string(
        self,
        value: object,
        pointer: str,
        *,
        maximum: int = 5000,
        pattern: re.Pattern[str] | None = None,
    ) -> str:
        if not isinstance(value, str) or not value.strip():
            self.diag(pointer, "required-string", "a non-empty string is required", "provide a string")
            return ""
        result = value.strip()
        if len(result.encode("utf-8")) > maximum:
            self.diag(pointer, "string-too-long", f"string exceeds {maximum} bytes", "shorten the value")
        if pattern is not None and not pattern.fullmatch(result):
            self.diag(pointer, "unsafe-selector", f"unsafe selector {result!r}", "use a stable safe id")
        return result

    def integer(
        self,
        value: object,
        pointer: str,
        minimum: int,
        maximum: int,
    ) -> int:
        if isinstance(value, bool) or not isinstance(value, int) or not minimum <= value <= maximum:
            self.diag(
                pointer, "invalid-bound",
                f"expected an integer from {minimum} through {maximum}",
                "declare an explicit finite integer",
            )
            return minimum
        return value

    def enum_list(
        self,
        value: object,
        pointer: str,
        allowed: tuple[str, ...] | list[str] | set[str],
        *,
        allow_empty: bool = False,
    ) -> list[str]:
        allowed_set = set(allowed)
        if (
            not isinstance(value, list)
            or (not allow_empty and not value)
            or any(not isinstance(item, str) or item not in allowed_set for item in value)
            or len(set(value)) != len(value)
        ):
            self.diag(
                pointer, "unsupported-value",
                "expected a unique list of contracted values",
                "use only documented values without duplicates",
            )
            return []
        return list(value)

    def id_list(
        self,
        value: object,
        pointer: str,
        *,
        allow_empty: bool = True,
    ) -> list[str]:
        if (
            not isinstance(value, list)
            or (not allow_empty and not value)
            or any(not isinstance(item, str) or not _SAFE_ID_RE.fullmatch(item) for item in value)
            or len(set(value)) != len(value)
        ):
            self.diag(
                pointer, "unsafe-selector", "expected a unique list of safe ids",
                "use lowercase stable ids without duplicates",
            )
            return []
        return list(value)

    def _agents(self, value: object) -> list[dict[str, object]]:
        if not isinstance(value, list) or not value:
            self.diag("/agents", "missing-agents", "organization needs logical agents", "declare at least one bounded logical agent")
            return []
        if len(value) > _MAX_AGENTS:
            self.diag("/agents", "organization-too-large", f"agent count exceeds {_MAX_AGENTS}", "split the organization")
        agents: list[dict[str, object]] = []
        ids: set[str] = set()
        for index, raw in enumerate(value[:_MAX_AGENTS]):
            pointer = f"/agents/{index}"
            if not isinstance(raw, dict):
                self.diag(pointer, "wrong-type", "agent must be an object", "provide an agent object")
                continue
            self.exact_keys(raw, _AGENT_KEYS, pointer, _AGENT_KEYS)
            agent_id = self.string(raw.get("id"), f"{pointer}/id", pattern=_SAFE_ID_RE)
            if agent_id in ids:
                self.diag(f"{pointer}/id", "duplicate-id", f"duplicate agent id {agent_id!r}", "use unique ids")
            ids.add(agent_id)
            profile = self.string(raw.get("profile"), f"{pointer}/profile", pattern=_SAFE_ID_RE)
            duties = self.enum_list(raw.get("duties"), f"{pointer}/duties", DUTIES)
            domain = self.string(raw.get("workspace_domain"), f"{pointer}/workspace_domain", pattern=_SAFE_ID_RE)
            ceiling = self.enum_list(
                raw.get("capability_ceiling"), f"{pointer}/capability_ceiling",
                PROGRAM_CAPABILITIES,
            )
            max_concurrency = self.integer(
                raw.get("max_concurrency"), f"{pointer}/max_concurrency", 1, 128,
            )
            weight = self.integer(raw.get("weight"), f"{pointer}/weight", 1, 100)
            agents.append({
                "id": agent_id,
                "profile": profile,
                "duties": duties,
                "workspace_domain": domain,
                "capability_ceiling": sorted(ceiling),
                "max_concurrency": max_concurrency,
                "weight": weight,
            })
        return agents

    def _pools(
        self,
        value: object,
        agent_ids: set[str],
    ) -> list[dict[str, object]]:
        if not isinstance(value, list) or not value:
            self.diag("/pools", "missing-pools", "organization needs logical pools", "declare at least one ordered agent pool")
            return []
        if len(value) > _MAX_POOLS:
            self.diag("/pools", "organization-too-large", f"pool count exceeds {_MAX_POOLS}", "split the organization")
        pools: list[dict[str, object]] = []
        ids: set[str] = set()
        for index, raw in enumerate(value[:_MAX_POOLS]):
            pointer = f"/pools/{index}"
            if not isinstance(raw, dict):
                self.diag(pointer, "wrong-type", "pool must be an object", "provide a pool object")
                continue
            self.exact_keys(raw, _POOL_KEYS, pointer, _POOL_KEYS)
            pool_id = self.string(raw.get("id"), f"{pointer}/id", pattern=_SAFE_ID_RE)
            if pool_id in ids:
                self.diag(f"{pointer}/id", "duplicate-id", f"duplicate pool id {pool_id!r}", "use unique ids")
            ids.add(pool_id)
            members = self.id_list(raw.get("agents"), f"{pointer}/agents", allow_empty=False)
            for offset, member in enumerate(members):
                if member not in agent_ids:
                    self.diag(
                        f"{pointer}/agents/{offset}", "dangling-agent-reference",
                        f"unknown logical agent {member!r}", "reference a declared agent",
                    )
            pools.append({"id": pool_id, "agents": members})
        return pools

    def _context(self, value: object, pointer: str) -> dict[str, object]:
        if not isinstance(value, dict):
            self.diag(pointer, "wrong-type", "context policy must be an object", "declare allow, expressions, and max_bytes")
            value = {}
        self.exact_keys(value, _CONTEXT_KEYS, pointer, _CONTEXT_KEYS)
        return {
            "allow": self.enum_list(value.get("allow"), f"{pointer}/allow", CONTEXT_CHANNELS, allow_empty=True),
            "expressions": self.enum_list(value.get("expressions"), f"{pointer}/expressions", EXPRESSION_KINDS, allow_empty=True),
            "max_bytes": self.integer(value.get("max_bytes"), f"{pointer}/max_bytes", 1, _MAX_CONTEXT_BYTES),
        }

    def _artifacts(self, value: object, pointer: str) -> dict[str, object]:
        if not isinstance(value, dict):
            self.diag(pointer, "wrong-type", "artifact policy must be an object", "declare read, write, and max_bytes")
            value = {}
        self.exact_keys(value, _ARTIFACT_KEYS, pointer, _ARTIFACT_KEYS)
        return {
            "read": self.enum_list(value.get("read"), f"{pointer}/read", ARTIFACT_KINDS, allow_empty=True),
            "write": self.enum_list(value.get("write"), f"{pointer}/write", ARTIFACT_KINDS, allow_empty=True),
            "max_bytes": self.integer(value.get("max_bytes"), f"{pointer}/max_bytes", 1, _MAX_ARTIFACT_BYTES),
        }

    def _replacement(
        self,
        value: object,
        pointer: str,
        pool_ids: set[str],
        duty: str,
    ) -> dict[str, object]:
        if not isinstance(value, dict):
            self.diag(pointer, "wrong-type", "replacement policy must be an object", "declare a finite replacement policy")
            value = {}
        self.exact_keys(value, _REPLACEMENT_KEYS, pointer, _REPLACEMENT_KEYS)
        reasons = self.enum_list(
            value.get("reasons"), f"{pointer}/reasons", REPLACEMENT_REASONS,
            allow_empty=True,
        )
        maximum = self.integer(
            value.get("max_replacements"), f"{pointer}/max_replacements", 0,
            _MAX_REPLACEMENTS,
        )
        if maximum and not reasons:
            self.diag(f"{pointer}/reasons", "replacement-unrouted", "positive replacement budget needs at least one reason", "declare eligible replacement reasons")
        fallback = self.id_list(value.get("fallback_pools"), f"{pointer}/fallback_pools")
        for offset, pool in enumerate(fallback):
            if pool not in pool_ids:
                self.diag(
                    f"{pointer}/fallback_pools/{offset}", "dangling-pool-reference",
                    f"unknown fallback pool {pool!r}", "reference a declared pool",
                )
        route = value.get("on_exhausted")
        if route not in EXHAUSTION_ROUTES:
            self.diag(f"{pointer}/on_exhausted", "unsupported-route", f"unsupported exhaustion route {route!r}", "use block, escalate, checkpoint, or abort")
            route = "block"
        preserve = value.get("preserve_history")
        if not isinstance(preserve, bool):
            self.diag(f"{pointer}/preserve_history", "wrong-type", "preserve_history must be boolean", "use true or false")
            preserve = False
        if duty in JUDGMENT_DUTIES and not preserve:
            self.diag(
                f"{pointer}/preserve_history", "dissent-erasure",
                "judgment-role replacement must preserve prior history and dissent",
                "set preserve_history to true",
            )
        return {
            "reasons": reasons,
            "max_replacements": maximum,
            "fallback_pools": fallback,
            "on_exhausted": route,
            "preserve_history": preserve,
        }

    def _teams(
        self,
        value: object,
        agents: list[dict[str, object]],
        pools: list[dict[str, object]],
    ) -> tuple[list[dict[str, object]], dict[str, dict[str, object]]]:
        if not isinstance(value, list) or not value:
            self.diag("/teams", "missing-teams", "organization needs at least one team", "declare a team with implementer and verifier duties")
            return [], {}
        if len(value) > _MAX_TEAMS:
            self.diag("/teams", "organization-too-large", f"team count exceeds {_MAX_TEAMS}", "split the organization")
        pool_ids = {str(pool["id"]) for pool in pools}
        teams: list[dict[str, object]] = []
        team_ids: set[str] = set()
        all_roles: dict[str, dict[str, object]] = {}
        total_slots = 0
        for team_index, raw in enumerate(value[:_MAX_TEAMS]):
            pointer = f"/teams/{team_index}"
            if not isinstance(raw, dict):
                self.diag(pointer, "wrong-type", "team must be an object", "provide a team object")
                continue
            self.exact_keys(raw, _TEAM_KEYS, pointer, _TEAM_KEYS)
            team_id = self.string(raw.get("id"), f"{pointer}/id", pattern=_SAFE_ID_RE)
            if team_id in team_ids:
                self.diag(f"{pointer}/id", "duplicate-id", f"duplicate team id {team_id!r}", "use unique ids")
            team_ids.add(team_id)
            raw_roles = raw.get("roles")
            if not isinstance(raw_roles, list) or not raw_roles:
                self.diag(f"{pointer}/roles", "missing-roles", "team needs role slots", "declare bounded role slots")
                raw_roles = []
            if len(raw_roles) > _MAX_ROLES:
                self.diag(f"{pointer}/roles", "organization-too-large", f"role count exceeds {_MAX_ROLES}", "split the team")
            roles: list[dict[str, object]] = []
            team_role_ids: set[str] = set()
            for role_index, raw_role in enumerate(raw_roles[:_MAX_ROLES]):
                role_pointer = f"{pointer}/roles/{role_index}"
                if not isinstance(raw_role, dict):
                    self.diag(role_pointer, "wrong-type", "role must be an object", "provide a role object")
                    continue
                self.exact_keys(raw_role, _ROLE_KEYS, role_pointer, _ROLE_KEYS)
                role_id = self.string(raw_role.get("id"), f"{role_pointer}/id", pattern=_SAFE_ID_RE)
                if role_id in team_role_ids or role_id in all_roles:
                    self.diag(f"{role_pointer}/id", "duplicate-id", f"ambiguous organization role id {role_id!r}", "use organization-wide unique role ids")
                team_role_ids.add(role_id)
                duty = raw_role.get("duty")
                if duty not in DUTIES:
                    self.diag(f"{role_pointer}/duty", "unsupported-duty", f"unsupported duty {duty!r}", "use a contracted duty")
                    duty = ""
                pool = self.string(raw_role.get("pool"), f"{role_pointer}/pool", pattern=_SAFE_ID_RE)
                if pool not in pool_ids:
                    self.diag(f"{role_pointer}/pool", "dangling-pool-reference", f"unknown pool {pool!r}", "reference a declared pool")
                required = raw_role.get("required")
                if not isinstance(required, bool):
                    self.diag(f"{role_pointer}/required", "wrong-type", "required must be boolean", "use true or false")
                    required = True
                cardinality = self.integer(
                    raw_role.get("cardinality"), f"{role_pointer}/cardinality", 1,
                    _MAX_ROLE_CARDINALITY,
                )
                total_slots += cardinality
                ceiling = self.enum_list(
                    raw_role.get("capability_ceiling"),
                    f"{role_pointer}/capability_ceiling", PROGRAM_CAPABILITIES,
                )
                driver_caps = self.enum_list(
                    raw_role.get("driver_capabilities"),
                    f"{role_pointer}/driver_capabilities", DRIVER_CAPABILITIES,
                )
                workspace = raw_role.get("workspace")
                if workspace not in WORKSPACE_MODES:
                    self.diag(f"{role_pointer}/workspace", "unsupported-workspace", f"unsupported workspace {workspace!r}", "use read-only or isolated-worktree")
                    workspace = "read-only"
                if "repository-read" not in driver_caps:
                    self.diag(f"{role_pointer}/driver_capabilities", "capability-missing", "every role needs repository-read", "include repository-read")
                if workspace == "isolated-worktree" and (
                    "workspace:write" not in ceiling
                    or "repository-write" not in driver_caps
                ):
                    self.diag(f"{role_pointer}/workspace", "capability-missing", "isolated role needs workspace:write and repository-write", "declare both write capabilities")
                if workspace == "read-only" and (
                    "workspace:write" in ceiling
                    or "repository-write" in driver_caps
                ):
                    self.diag(f"{role_pointer}/workspace", "capability-smuggling", "read-only role cannot carry write capability", "remove both write capabilities")
                context = self._context(raw_role.get("context"), f"{role_pointer}/context")
                artifacts = self._artifacts(raw_role.get("artifacts"), f"{role_pointer}/artifacts")
                output_schema = raw_role.get("output_schema")
                verdict_schema = raw_role.get("verdict_schema")
                for key, schema in (("output_schema", output_schema), ("verdict_schema", verdict_schema)):
                    if schema is not None and (
                        not isinstance(schema, str) or not _SCHEMA_RE.fullmatch(schema)
                    ):
                        self.diag(f"{role_pointer}/{key}", "unsafe-selector", f"invalid schema selector {schema!r}", "use a bounded schema id or null")
                if duty in JUDGMENT_DUTIES and verdict_schema is None:
                    self.diag(f"{role_pointer}/verdict_schema", "missing-verdict-schema", f"{duty} must declare a verdict schema", "name the exact verdict schema")
                if duty in JUDGMENT_DUTIES and "verdict:issue" not in ceiling:
                    self.diag(f"{role_pointer}/capability_ceiling", "capability-missing", f"{duty} must explicitly allow verdict:issue", "add verdict:issue to the role ceiling")
                if duty not in JUDGMENT_DUTIES and output_schema is None:
                    self.diag(f"{role_pointer}/output_schema", "missing-output-schema", f"{duty} must declare an output schema", "name the exact output schema")
                max_concurrency = self.integer(
                    raw_role.get("max_concurrency"),
                    f"{role_pointer}/max_concurrency", 1, 128,
                )
                groups = self.id_list(raw_role.get("resource_groups"), f"{role_pointer}/resource_groups")
                may_request = self.id_list(raw_role.get("may_request"), f"{role_pointer}/may_request")
                may_judge = self.id_list(raw_role.get("may_judge"), f"{role_pointer}/may_judge")
                independence = self.id_list(raw_role.get("independent_from"), f"{role_pointer}/independent_from")
                replacement = self._replacement(
                    raw_role.get("replacement"), f"{role_pointer}/replacement",
                    pool_ids, str(duty),
                )
                role = {
                    "id": role_id,
                    "duty": duty,
                    "pool": pool,
                    "required": required,
                    "cardinality": cardinality,
                    "capability_ceiling": sorted(ceiling),
                    "driver_capabilities": sorted(driver_caps),
                    "workspace": workspace,
                    "context": context,
                    "artifacts": artifacts,
                    "output_schema": output_schema,
                    "verdict_schema": verdict_schema,
                    "max_concurrency": max_concurrency,
                    "resource_groups": sorted(groups),
                    "may_request": may_request,
                    "may_judge": may_judge,
                    "independent_from": independence,
                    "replacement": replacement,
                }
                roles.append(role)
                all_roles[role_id] = role
            if total_slots > _MAX_TOTAL_SLOTS:
                self.diag(f"{pointer}/roles", "organization-too-large", f"total slot count exceeds {_MAX_TOTAL_SLOTS}", "lower cardinalities or split teams")
            order = {str(role["id"]): index for index, role in enumerate(roles)}
            for role_index, role in enumerate(roles):
                role_pointer = f"{pointer}/roles/{role_index}"
                for field in ("may_request", "may_judge", "independent_from"):
                    for offset, target in enumerate(role[field]):
                        if target not in team_role_ids:
                            self.diag(f"{role_pointer}/{field}/{offset}", "dangling-role-reference", f"unknown team role {target!r}", "reference a role in the same team")
                for offset, target in enumerate(role["independent_from"]):
                    if target in order and order[target] >= role_index:
                        self.diag(f"{role_pointer}/independent_from/{offset}", "role-order", f"independence prerequisite {target!r} must be assigned first", "move prerequisite roles earlier")
            implementers = [role for role in roles if role["duty"] == "implementer"]
            verifiers = [role for role in roles if role["duty"] == "verifier"]
            if len(implementers) != 1 or len(verifiers) != 1:
                self.diag(f"{pointer}/roles", "missing-separation", "every team requires exactly one implementer and verifier duty", "declare one of each")
            elif (
                not implementers[0]["required"]
                or not verifiers[0]["required"]
                or implementers[0]["cardinality"] != 1
                or verifiers[0]["cardinality"] != 1
            ):
                self.diag(f"{pointer}/roles", "missing-separation", "implementer and verifier must be required singleton roles", "set required true and cardinality 1")
            elif implementers[0]["id"] not in verifiers[0]["independent_from"]:
                self.diag(f"{pointer}/roles", "missing-separation", "verifier must declare independence from implementer", "add implementer to verifier independent_from")
            elif implementers[0]["id"] not in verifiers[0]["may_judge"]:
                self.diag(f"{pointer}/roles", "judgment-not-authorized", "verifier must explicitly be allowed to judge implementer", "add implementer to verifier may_judge")
            teams.append({"id": team_id, "roles": roles})
        return teams, all_roles

    def _councils(
        self,
        value: object,
        roles: dict[str, dict[str, object]],
    ) -> list[dict[str, object]]:
        if value is None:
            return []
        if not isinstance(value, list):
            self.diag("/councils", "wrong-type", "councils must be an array", "provide an array or remove it")
            return []
        councils: list[dict[str, object]] = []
        ids: set[str] = set()
        for index, raw in enumerate(value):
            pointer = f"/councils/{index}"
            if not isinstance(raw, dict):
                self.diag(pointer, "wrong-type", "council must be an object", "provide a council object")
                continue
            self.exact_keys(raw, _COUNCIL_KEYS, pointer, _COUNCIL_REQUIRED_KEYS)
            council_id = self.string(raw.get("id"), f"{pointer}/id", pattern=_SAFE_ID_RE)
            if council_id in ids:
                self.diag(f"{pointer}/id", "duplicate-id", f"duplicate council id {council_id!r}", "use unique ids")
            ids.add(council_id)
            members = self.id_list(raw.get("members"), f"{pointer}/members", allow_empty=False)
            for offset, member in enumerate(members):
                if member not in roles:
                    self.diag(f"{pointer}/members/{offset}", "dangling-role-reference", f"unknown council role {member!r}", "reference a declared role")
            judge = raw.get("judge")
            if not isinstance(judge, str) or judge not in members:
                self.diag(f"{pointer}/judge", "dangling-role-reference", "judge must name a council member role", "choose one declared member")
                judge = None
            elif roles.get(judge, {}).get("duty") not in {"judge", "verifier"}:
                self.diag(f"{pointer}/judge", "unsupported-duty", "council judge must have judge or verifier duty", "use a judgment role")
            elif not {"council:decide", "obligation:record"} <= set(roles[judge]["capability_ceiling"]):
                self.diag(f"{pointer}/judge", "capability-missing", "council judge must explicitly allow council:decide and obligation:record", "add both council decision capabilities to the judge role ceiling")
            meta = raw.get("meta_verifier")
            if meta is not None and (
                not isinstance(meta, str)
                or roles.get(meta, {}).get("duty") != "meta-verifier"
            ):
                self.diag(f"{pointer}/meta_verifier", "dangling-role-reference", "meta_verifier must name a meta-verifier role", "choose a declared meta-verifier or null")
                meta = None
            total_members = sum(int(roles.get(role, {}).get("cardinality", 0)) for role in members)
            quorum = self.integer(raw.get("quorum"), f"{pointer}/quorum", 1, 128)
            if quorum > total_members:
                self.diag(f"{pointer}/quorum", "impossible-quorum", f"quorum {quorum} exceeds {total_members} declared member slots", "lower quorum or raise cardinality")
            distinct = raw.get("distinct_principals")
            if distinct is not True:
                self.diag(f"{pointer}/distinct_principals", "duplicate-principal", "council quorum must require distinct principals", "set distinct_principals to true")

            decision_raw = raw.get("decision", {})
            if not isinstance(decision_raw, dict):
                self.diag(f"{pointer}/decision", "wrong-type", "council decision policy must be an object", "declare a closed decision policy")
                decision_raw = {}
            self.exact_keys(decision_raw, _COUNCIL_DECISION_KEYS, f"{pointer}/decision")
            method = decision_raw.get("method", "majority")
            if method not in COUNCIL_DECISION_METHODS:
                self.diag(f"{pointer}/decision/method", "unsupported-value", "unsupported council decision method", f"choose one of: {', '.join(COUNCIL_DECISION_METHODS)}")
                method = "majority"
            weights_raw = decision_raw.get("weights", {})
            if not isinstance(weights_raw, dict):
                self.diag(f"{pointer}/decision/weights", "wrong-type", "weights must map member role ids to positive integers", "declare a closed role-weight map")
                weights_raw = {}
            weights: dict[str, int] = {}
            for role_id, weight in sorted(weights_raw.items()):
                weight_pointer = f"{pointer}/decision/weights/{role_id}"
                if role_id not in members:
                    self.diag(weight_pointer, "dangling-role-reference", f"weight names non-member role {role_id!r}", "weight only declared council member roles")
                    continue
                weights[str(role_id)] = self.integer(weight, weight_pointer, 1, 100)
            for member in members:
                weights.setdefault(member, 1)
            voting_slots = sum(
                int(roles.get(role, {}).get("cardinality", 0))
                for role in members if role != judge
            )
            total_weight = sum(
                int(roles.get(role, {}).get("cardinality", 0)) * weights[role]
                for role in members if role != judge
            )
            default_threshold = {
                "majority": voting_slots // 2 + 1,
                "weighted": total_weight // 2 + 1,
                "unanimous": max(voting_slots, 1),
                "judge": 1,
            }[str(method)]
            threshold_max = max(total_weight if method == "weighted" else voting_slots, 1)
            threshold = self.integer(
                decision_raw.get("threshold", default_threshold),
                f"{pointer}/decision/threshold", 1, threshold_max,
            )
            if method == "unanimous" and threshold != max(voting_slots, 1):
                self.diag(f"{pointer}/decision/threshold", "invalid-threshold", "unanimous councils require every voting speaker", "set threshold to the voting speaker cardinality")
            veto_roles = self.id_list(
                decision_raw.get("veto_roles", []),
                f"{pointer}/decision/veto_roles",
            )
            for offset, role_id in enumerate(veto_roles):
                if role_id not in members:
                    self.diag(f"{pointer}/decision/veto_roles/{offset}", "dangling-role-reference", f"veto role {role_id!r} is not a council member", "name only council member roles")

            audit_raw = raw.get("audit", {})
            if not isinstance(audit_raw, dict):
                self.diag(f"{pointer}/audit", "wrong-type", "council audit policy must be an object", "declare a closed audit policy")
                audit_raw = {}
            self.exact_keys(audit_raw, _COUNCIL_AUDIT_KEYS, f"{pointer}/audit")
            audit_mode = audit_raw.get("mode", "none")
            if audit_mode not in COUNCIL_AUDIT_MODES:
                self.diag(f"{pointer}/audit/mode", "unsupported-value", "unsupported meta-audit mode", f"choose one of: {', '.join(COUNCIL_AUDIT_MODES)}")
                audit_mode = "none"
            sample_default = 0 if audit_mode == "none" else (total_members if audit_mode == "full" else 1)
            sample_minimum = 0 if audit_mode == "none" else 1
            sample_size = self.integer(
                audit_raw.get("sample_size", sample_default),
                f"{pointer}/audit/sample_size", sample_minimum, max(total_members, sample_minimum),
            )
            if audit_mode == "none" and sample_size != 0:
                self.diag(f"{pointer}/audit/sample_size", "invalid-bound", "disabled meta-audit requires sample_size 0", "set sample_size to 0")
            if audit_mode == "full" and sample_size != total_members:
                self.diag(f"{pointer}/audit/sample_size", "invalid-bound", "full meta-audit must cover every council member slot", "set sample_size to member cardinality")
            if audit_mode != "none" and meta is None:
                self.diag(f"{pointer}/meta_verifier", "missing-meta-verifier", "enabled audit requires a declared meta-verifier role", "name an independent meta-verifier")
            audit_routes: dict[str, str] = {}
            for field, default in (("on_overturn", "repair"), ("on_escalate", "escalate")):
                route = audit_raw.get(field, default)
                if route not in COUNCIL_RESULT_ROUTES:
                    self.diag(f"{pointer}/audit/{field}", "unsupported-value", f"unsupported audit route {route!r}", f"choose one of: {', '.join(COUNCIL_RESULT_ROUTES)}")
                    route = default
                audit_routes[field] = str(route)

            budgets_raw = raw.get("budgets", {})
            if not isinstance(budgets_raw, dict):
                self.diag(f"{pointer}/budgets", "wrong-type", "council budgets must be an object", "declare finite council budgets")
                budgets_raw = {}
            self.exact_keys(budgets_raw, _COUNCIL_BUDGET_KEYS, f"{pointer}/budgets")
            budgets = {
                key: self.integer(
                    budgets_raw.get(key, default),
                    f"{pointer}/budgets/{key}", 1, _COUNCIL_BUDGET_LIMITS[key],
                )
                for key, default in _COUNCIL_BUDGET_DEFAULTS.items()
            }
            councils.append({
                "id": council_id,
                "members": members,
                "judge": judge,
                "quorum": quorum,
                "member_cardinality": total_members,
                "meta_verifier": meta,
                "distinct_principals": True,
                "decision": {
                    "method": method,
                    "weights": weights,
                    "threshold": threshold,
                    "veto_roles": veto_roles,
                },
                "audit": {
                    "mode": audit_mode,
                    "sample_size": sample_size,
                    **audit_routes,
                },
                "budgets": budgets,
            })
        return councils

    @staticmethod
    def _logical_proof(
        team: dict[str, object],
        agents: list[dict[str, object]],
        pools: list[dict[str, object]],
    ) -> dict[str, object]:
        agent_by_id = {str(agent["id"]): agent for agent in agents}
        pool_by_id = {str(pool["id"]): list(pool["agents"]) for pool in pools}
        roles = list(team["roles"])
        slots: list[tuple[dict[str, object], int]] = []
        candidates: dict[tuple[str, int], list[dict[str, object]]] = {}
        for role in roles:
            if not role["required"]:
                continue
            for slot in range(1, int(role["cardinality"]) + 1):
                slots.append((role, slot))
                eligible = []
                for agent_id in pool_by_id.get(str(role["pool"]), []):
                    agent = agent_by_id.get(str(agent_id))
                    if agent is None or role["duty"] not in agent["duties"]:
                        continue
                    if not set(role["capability_ceiling"]) <= set(agent["capability_ceiling"]):
                        continue
                    eligible.append(agent)
                candidates[(str(role["id"]), slot)] = eligible

        selected: list[tuple[dict[str, object], int, dict[str, object]]] = []

        def conflict(
            role: dict[str, object],
            agent: dict[str, object],
            prior_role: dict[str, object],
            prior_agent: dict[str, object],
        ) -> bool:
            same_role = role["id"] == prior_role["id"]
            independent = (
                prior_role["id"] in role["independent_from"]
                or role["id"] in prior_role["independent_from"]
            )
            if same_role or independent:
                return bool(
                    agent["id"] == prior_agent["id"]
                    or agent["profile"] == prior_agent["profile"]
                    or agent["workspace_domain"] == prior_agent["workspace_domain"]
                )
            return False

        def search(offset: int) -> bool:
            if offset == len(slots):
                return True
            role, slot = slots[offset]
            for agent in candidates.get((str(role["id"]), slot), []):
                if any(conflict(role, agent, old_role, old_agent) for old_role, _old_slot, old_agent in selected):
                    continue
                selected.append((role, slot, agent))
                if search(offset + 1):
                    return True
                selected.pop()
            return False

        satisfiable = search(0)
        return {
            "team": team["id"],
            "required_slots": len(slots),
            "satisfiable": satisfiable,
            "witness": [
                {
                    "role": role["id"],
                    "slot": slot,
                    "agent": agent["id"],
                    "profile": agent["profile"],
                    "workspace_domain": agent["workspace_domain"],
                }
                for role, slot, agent in selected
            ] if satisfiable else [],
        }

    def compile(self) -> tuple[dict[str, object], list[dict[str, str]]]:
        if not isinstance(self.raw, dict):
            self.diag("/", "wrong-type", "organization must be an object", "provide a JSON object")
            raw: dict[str, object] = {}
        else:
            raw = self.raw
        self.exact_keys(
            raw, _ORG_KEYS, "",
            {"kind", "schema_version", "slug", "title", "agents", "pools", "teams", "councils"},
        )
        if raw.get("kind") != ORGANIZATION_KIND:
            self.diag("/kind", "wrong-kind", f"expected {ORGANIZATION_KIND!r}", f"set kind to {ORGANIZATION_KIND}")
        if raw.get("schema_version") != ORGANIZATION_SCHEMA_VERSION:
            self.diag("/schema_version", "unsupported-schema", "only schema version 1 is supported", "use schema_version 1")
        slug = self.string(raw.get("slug"), "/slug", pattern=_SAFE_ID_RE)
        title = self.string(raw.get("title"), "/title")
        description = raw.get("description")
        if description is not None and (
            not isinstance(description, str)
            or len(description.encode("utf-8")) > 5000
        ):
            self.diag("/description", "invalid-value", "description must be a bounded string", "shorten or remove it")
            description = None
        agents = self._agents(raw.get("agents"))
        pools = self._pools(raw.get("pools"), {str(agent["id"]) for agent in agents})
        teams, roles = self._teams(raw.get("teams"), agents, pools)
        councils = self._councils(raw.get("councils"), roles)
        proofs = [self._logical_proof(team, agents, pools) for team in teams]
        for team_index, proof in enumerate(proofs):
            if not proof["satisfiable"]:
                self.diag(
                    f"/teams/{team_index}/roles", "impossible-independence",
                    f"logical pools cannot satisfy required independent slots for team {proof['team']!r}",
                    "add distinct profiles/workspace domains or widen a declared pool",
                )
        layout = raw.get("layout", {})
        if not isinstance(layout, dict):
            self.diag("/layout", "wrong-type", "layout must be an object", "provide editor layout or remove it")
            layout = {}
        runtime: dict[str, object] = {
            "kind": ORGANIZATION_KIND,
            "schema_version": ORGANIZATION_SCHEMA_VERSION,
            "slug": slug,
            "title": title,
            "agents": agents,
            "pools": pools,
            "teams": teams,
            "councils": councils,
        }
        if description is not None:
            runtime["description"] = description
        normalized = {**runtime, "layout": layout}
        self.diagnostics.sort(
            key=lambda item: (item["source"], item["pointer"], item["code"], item["message"])
        )
        return {
            "kind": COMPILED_ORGANIZATION_KIND,
            "schema_version": ORGANIZATION_SCHEMA_VERSION,
            "semantic_hash": _sha(runtime),
            "document_hash": _sha(normalized),
            "organization": runtime,
            "layout": layout,
            "logical_assignment_proofs": proofs,
            "starts_work": False,
            "writes_state": False,
        }, self.diagnostics


def validate_organization(
    root: Path,
    organization: str | Path | object,
    source: str = "organization",
) -> dict[str, object]:
    try:
        if isinstance(organization, str):
            path = find_organization_path(root, organization)
            raw: object = load_organization(path)
            source = str(path.relative_to(root.resolve()))
        elif isinstance(organization, Path):
            path = organization.resolve()
            if path.parent != organization_dir(root):
                raise DwError("organization path must be direct-contained under pm/organizations")
            raw = load_organization(path)
            source = str(path.relative_to(root.resolve()))
        else:
            raw = organization
    except DwError as exc:
        return {
            "kind": VALIDATION_KIND,
            "schema_version": ORGANIZATION_SCHEMA_VERSION,
            "valid": False,
            "diagnostics": [{
                "source": source,
                "pointer": "/",
                "code": "parse-error",
                "message": exc.message,
                "remediation": "fix the organization document",
            }],
            "compiled": None,
            "starts_work": False,
            "writes_state": False,
        }
    compiled, diagnostics = _Compiler(raw, source).compile()
    return {
        "kind": VALIDATION_KIND,
        "schema_version": ORGANIZATION_SCHEMA_VERSION,
        "valid": not diagnostics,
        "diagnostics": diagnostics,
        "compiled": compiled if not diagnostics else None,
        "starts_work": False,
        "writes_state": False,
    }


def compile_organization(
    root: Path,
    organization: str | Path | object,
    source: str = "organization",
) -> dict[str, object]:
    validation = validate_organization(root, organization, source)
    if not validation["valid"]:
        raise OrganizationValidationError(validation["diagnostics"])  # type: ignore[arg-type]
    return validation["compiled"]  # type: ignore[return-value]


def _role_waves(team: dict[str, object]) -> list[list[str]]:
    slots = [
        (f"{role['id']}[{slot}]", set(role["resource_groups"]))
        for role in team["roles"]
        for slot in range(1, int(role["cardinality"]) + 1)
    ]
    waves: list[list[str]] = []
    wave_groups: list[set[str]] = []
    for address, groups in slots:
        target = None
        for index, occupied in enumerate(wave_groups):
            if not groups & occupied:
                target = index
                break
        if target is None:
            waves.append([address])
            wave_groups.append(set(groups))
        else:
            waves[target].append(address)
            wave_groups[target].update(groups)
    return waves


def simulate_organization(
    root: Path,
    organization: str | Path | object,
) -> dict[str, object]:
    compiled = compile_organization(root, organization)
    runtime = compiled["organization"]
    return {
        "kind": SIMULATION_KIND,
        "schema_version": ORGANIZATION_SCHEMA_VERSION,
        "organization": {
            "slug": runtime["slug"],
            "semantic_hash": compiled["semantic_hash"],
            "document_hash": compiled["document_hash"],
        },
        "teams": [
            {
                "id": team["id"],
                "roles": team["roles"],
                "logical_assignment_proof": next(
                    proof for proof in compiled["logical_assignment_proofs"]
                    if proof["team"] == team["id"]
                ),
                "concurrency_waves": _role_waves(team),
            }
            for team in runtime["teams"]
        ],
        "councils": runtime["councils"],
        "starts_work": False,
        "writes_policy": False,
        "writes_run_state": False,
        "creates_grant": False,
    }


def organization_inventory(root: Path) -> dict[str, object]:
    items: list[dict[str, object]] = []
    for path in discover_organization_paths(root):
        validation = validate_organization(root, path)
        raw: dict[str, object] = {}
        try:
            raw = load_organization(path)
        except DwError:
            pass
        item: dict[str, object] = {
            "name": path.stem,
            "path": str(path.relative_to(root.resolve())),
            "slug": raw.get("slug"),
            "title": raw.get("title"),
            "valid": validation["valid"],
            "diagnostics": validation["diagnostics"],
        }
        if validation["valid"]:
            compiled = validation["compiled"]
            item["semantic_hash"] = compiled["semantic_hash"]
            item["document_hash"] = compiled["document_hash"]
        items.append(item)
    return {
        "kind": INVENTORY_KIND,
        "schema_version": ORGANIZATION_SCHEMA_VERSION,
        "organizations": items,
        "healthy": all(bool(item["valid"]) for item in items),
        "starts_work": False,
        "writes_state": False,
    }


def workflow_role_requirements(workflow: dict[str, object] | None) -> dict[str, dict[str, object]]:
    if not workflow:
        return {}
    required_capabilities = workflow.get("required_capabilities", {})
    result: dict[str, dict[str, object]] = {}
    for lane in workflow.get("role_lanes", []):
        role = str(lane["role"])
        requirement = result.setdefault(role, {
            "capabilities": set(),
            "workspaces": set(),
            "context_expressions": set(),
            "artifact_reads": set(),
            "artifact_writes": set(),
            "addresses": [],
        })
        requirement["capabilities"].update(
            lane.get(
                "capabilities",
                required_capabilities.get(str(lane["node"]), []),
            )
        )
        workspace = lane.get("workspace")
        if workspace:
            requirement["workspaces"].add(str(workspace))
        requirement["context_expressions"].update(lane.get("context_reads", []))
        requirement["artifact_reads"].update(lane.get("artifact_reads", []))
        requirement["artifact_writes"].update(lane.get("artifact_writes", []))
        requirement["addresses"].append(str(lane["address"]))
    return {
        role: {
            "capabilities": sorted(value["capabilities"]),
            "workspaces": sorted(value["workspaces"]),
            "context_expressions": sorted(value["context_expressions"]),
            "artifact_reads": sorted(value["artifact_reads"]),
            "artifact_writes": sorted(value["artifact_writes"]),
            "addresses": sorted(value["addresses"]),
        }
        for role, value in sorted(result.items())
    }


def validate_workflow_team(
    organization: dict[str, object],
    team_id: str,
    workflow: dict[str, object] | None,
    program_capabilities: list[str] | tuple[str, ...] | set[str],
    *,
    source: str = "organization",
) -> tuple[dict[str, dict[str, object]], list[dict[str, str]]]:
    runtime = organization.get("organization", organization)
    team = next((item for item in runtime.get("teams", []) if item["id"] == team_id), None)
    if team is None:
        return {}, [{
            "source": source,
            "pointer": "/teams",
            "code": "team-unsatisfied",
            "message": f"team {team_id!r} is not declared",
            "remediation": "bind a declared organization team",
        }]
    roles = {str(role["id"]): role for role in team["roles"]}
    requirements = workflow_role_requirements(workflow)
    issues: list[dict[str, str]] = []
    granted = set(program_capabilities)
    for role_id, requirement in requirements.items():
        role = roles.get(role_id)
        if role is None:
            issues.append({
                "source": source,
                "pointer": f"/teams/{team_id}/roles",
                "code": "role-unavailable",
                "message": f"workflow requires undeclared role {role_id!r}",
                "remediation": "declare the exact role id in the bound team",
            })
            continue
        needed = set(requirement["capabilities"])
        role_ceiling = set(role["capability_ceiling"])
        if not needed <= role_ceiling:
            issues.append({
                "source": source,
                "pointer": f"/teams/{team_id}/roles/{role_id}/capability_ceiling",
                "code": "role-capability-denied",
                "message": "workflow requires capabilities outside role policy: " + ", ".join(sorted(needed - role_ceiling)),
                "remediation": "narrow the workflow or explicitly widen the role ceiling",
            })
        if not needed <= granted:
            issues.append({
                "source": source,
                "pointer": "/requested_capabilities",
                "code": "capability-denied",
                "message": "workflow role requires capabilities outside program authority: " + ", ".join(sorted(needed - granted)),
                "remediation": "request the exact capability or narrow the workflow",
            })
        workspaces = set(requirement["workspaces"])
        if workspaces and workspaces != {role["workspace"]}:
            issues.append({
                "source": source,
                "pointer": f"/teams/{team_id}/roles/{role_id}/workspace",
                "code": "workspace-denied",
                "message": f"workflow workspaces {sorted(workspaces)!r} do not match role workspace {role['workspace']!r}",
                "remediation": "use one exact compatible workspace lane",
            })
        context = set(requirement["context_expressions"])
        if not context <= set(role["context"]["expressions"]):
            issues.append({
                "source": source,
                "pointer": f"/teams/{team_id}/roles/{role_id}/context/expressions",
                "code": "visibility-denied",
                "message": "workflow reads undeclared context expression kinds: " + ", ".join(sorted(context - set(role["context"]["expressions"]))),
                "remediation": "narrow inputs or explicitly allow the expression kind",
            })
        reads = set(requirement["artifact_reads"])
        writes = set(requirement["artifact_writes"])
        if not reads <= set(role["artifacts"]["read"]):
            issues.append({
                "source": source,
                "pointer": f"/teams/{team_id}/roles/{role_id}/artifacts/read",
                "code": "visibility-denied",
                "message": "workflow reads undeclared artifact kinds: " + ", ".join(sorted(reads - set(role["artifacts"]["read"]))),
                "remediation": "narrow workflow inputs or allow the exact artifact kinds",
            })
        if not writes <= set(role["artifacts"]["write"]):
            issues.append({
                "source": source,
                "pointer": f"/teams/{team_id}/roles/{role_id}/artifacts/write",
                "code": "visibility-denied",
                "message": "workflow writes undeclared artifact kinds: " + ", ".join(sorted(writes - set(role["artifacts"]["write"]))),
                "remediation": "narrow workflow outputs or allow the exact artifact kinds",
            })
    issues.sort(key=lambda item: (item["pointer"], item["code"], item["message"]))
    return requirements, issues


def _candidate_conflicts(
    role: dict[str, object],
    candidate: dict[str, object],
    selected: list[tuple[dict[str, object], int, dict[str, object]]],
) -> str | None:
    for old_role, _slot, old in selected:
        same_role = role["id"] == old_role["id"]
        independent = (
            old_role["id"] in role["independent_from"]
            or role["id"] in old_role["independent_from"]
        )
        if same_role or independent:
            if candidate["principal_fingerprint"] == old["principal_fingerprint"]:
                return "same-principal"
            if candidate["workspace_domain"] == old["workspace_domain"]:
                return "same-workspace-domain"
        if candidate["principal_fingerprint"] == old["principal_fingerprint"]:
            used = sum(
                1 for _prior_role, _prior_slot, prior in selected
                if prior["principal_fingerprint"] == candidate["principal_fingerprint"]
            )
            if used >= int(candidate["max_concurrency"]):
                return "principal-concurrency-exhausted"
    return None


def assign_organization_team(
    organization: dict[str, object],
    team_id: str,
    *,
    driver_config: dict[str, object],
    policy_bundle_hash: str,
    story_id: str,
    workflow_address: str,
    program_capabilities: list[str] | tuple[str, ...] | set[str],
    workflow: dict[str, object] | None = None,
    active_principals: dict[str, int] | None = None,
    active_resource_groups: list[str] | tuple[str, ...] | set[str] = (),
) -> dict[str, object]:
    runtime = organization.get("organization", organization)
    team = next((item for item in runtime.get("teams", []) if item["id"] == team_id), None)
    config = validate_driver_config(driver_config)
    roster = driver_inventory(config)
    roster_hash = _sha(roster)
    base: dict[str, object] = {
        "kind": ASSIGNMENT_KIND,
        "schema_version": ORGANIZATION_SCHEMA_VERSION,
        "organization": runtime.get("slug"),
        "organization_semantic_hash": organization.get("semantic_hash"),
        "team": team_id,
        "story": story_id,
        "workflow_address": workflow_address,
        "roster_hash": roster_hash,
        "roles": [],
        "councils": [],
        "issues": [],
        "starts_work": False,
        "writes_state": False,
        "creates_grant": False,
    }
    if team is None:
        base["issues"] = [{"code": "role-unavailable", "message": f"team {team_id!r} is not declared"}]
        base["applicable"] = False
        base["assignment_hash"] = _sha({key: value for key, value in base.items() if key != "assignment_hash"})
        return base
    requirements, compatibility = validate_workflow_team(
        organization, team_id, workflow, program_capabilities,
    )
    workflow_roles = set(requirements)
    issues: list[dict[str, str]] = [
        {"code": item["code"], "message": item["message"]}
        for item in compatibility
    ]
    agents = {str(agent["id"]): agent for agent in runtime["agents"]}
    pools = {str(pool["id"]): list(pool["agents"]) for pool in runtime["pools"]}
    occupied_principals = dict(active_principals or {})
    occupied_groups = set(active_resource_groups)
    program_caps = set(program_capabilities)
    candidate_map: dict[tuple[str, int], list[dict[str, object]]] = {}
    exclusion_map: dict[str, list[dict[str, str]]] = {}
    roles = list(team["roles"])
    for role in roles:
        role_id = str(role["id"])
        exclusions: list[dict[str, str]] = []
        requirement = requirements.get(role_id, {})
        needed = set(requirement.get("capabilities", []))
        effective = sorted(needed & set(role["capability_ceiling"]) & program_caps)
        pool_order = [str(role["pool"])] + list(role["replacement"]["fallback_pools"])
        seen_agents: set[str] = set()
        all_candidates: list[dict[str, object]] = []
        for tier, pool_id in enumerate(pool_order):
            for agent_id in pools.get(pool_id, []):
                if agent_id in seen_agents:
                    continue
                seen_agents.add(str(agent_id))
                agent = agents.get(str(agent_id))
                if agent is None:
                    exclusions.append({"agent": str(agent_id), "reason": "agent-not-declared"})
                    continue
                if role["duty"] not in agent["duties"]:
                    exclusions.append({"agent": str(agent_id), "reason": "duty-not-allowed"})
                    continue
                if not set(role["capability_ceiling"]) <= set(agent["capability_ceiling"]):
                    exclusions.append({"agent": str(agent_id), "reason": "agent-capability-ceiling"})
                    continue
                try:
                    capability = driver_capability(config, str(agent["profile"]))
                except DwError:
                    exclusions.append({"agent": str(agent_id), "reason": "profile-unconfigured"})
                    continue
                if not capability["available"]:
                    exclusions.append({"agent": str(agent_id), "reason": "profile-unavailable"})
                    continue
                if not set(role["driver_capabilities"]) <= set(capability["capabilities"]):
                    exclusions.append({"agent": str(agent_id), "reason": "capability-mismatch"})
                    continue
                if role["workspace"] not in capability["workspace_modes"]:
                    exclusions.append({"agent": str(agent_id), "reason": "workspace-mismatch"})
                    continue
                if role["workspace"] == "read-only" and "repository-write" in capability["capabilities"]:
                    exclusions.append({"agent": str(agent_id), "reason": "read-only-profile-write-capable"})
                    continue
                principal = str(capability["principal_fingerprint"])
                maximum = min(int(agent["max_concurrency"]), int(capability["max_concurrency"]), int(role["max_concurrency"]))
                if occupied_principals.get(principal, 0) >= maximum:
                    exclusions.append({"agent": str(agent_id), "reason": "principal-concurrency-exhausted"})
                    continue
                if occupied_groups & set(role["resource_groups"]):
                    exclusions.append({"agent": str(agent_id), "reason": "resource-group-active"})
                    continue
                candidate = {
                    "agent": agent["id"],
                    "profile": agent["profile"],
                    "workspace_domain": agent["workspace_domain"],
                    "principal": capability["principal"],
                    "principal_fingerprint": capability["principal_fingerprint"],
                    "adapter": capability["adapter"],
                    "adapter_version": capability["adapter_version"],
                    "adapter_capability_fingerprint": capability["capability_fingerprint"],
                    "execution": {
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
                    },
                    "driver_capabilities": capability["capabilities"],
                    "workspace_modes": capability["workspace_modes"],
                    "max_concurrency": maximum,
                    "weight": agent["weight"],
                    "source_pool": pool_id,
                    "fallback": tier > 0,
                    "effective_capability_ceiling": effective,
                }
                all_candidates.append(candidate)
        for slot in range(1, int(role["cardinality"]) + 1):
            ranked: list[dict[str, object]] = []
            for candidate in all_candidates:
                rank_input = (
                    f"{policy_bundle_hash}|{story_id}|{workflow_address}|"
                    f"{role_id}|{slot}|{candidate['agent']}"
                )
                rank_int = int(hashlib.sha256(rank_input.encode("utf-8")).hexdigest(), 16)
                copy = dict(candidate)
                copy["rank"] = f"{rank_int * int(candidate['weight']):066x}"
                ranked.append(copy)
            ranked.sort(
                key=lambda item: (
                    -int(bool(item["fallback"])),
                    str(item["rank"]),
                    str(item["agent"]),
                ),
                reverse=True,
            )
            candidate_map[(role_id, slot)] = ranked
        exclusion_map[role_id] = exclusions

    slots = [
        (role, slot)
        for role in roles
        for slot in range(1, int(role["cardinality"]) + 1)
    ]
    selected: list[tuple[dict[str, object], int, dict[str, object]]] = []

    def search(offset: int) -> bool:
        if offset == len(slots):
            return True
        role, slot = slots[offset]
        role_id = str(role["id"])
        for candidate in candidate_map.get((role_id, slot), []):
            conflict = _candidate_conflicts(role, candidate, selected)
            if conflict is not None:
                continue
            selected.append((role, slot, candidate))
            if search(offset + 1):
                return True
            selected.pop()
        if not (role["required"] or str(role["id"]) in workflow_roles):
            if search(offset + 1):
                return True
        return False

    satisfiable = search(0)
    if not satisfiable:
        for role in roles:
            role_id = str(role["id"])
            if not (role["required"] or role_id in workflow_roles):
                continue
            available_slots = sum(
                1 for slot in range(1, int(role["cardinality"]) + 1)
                if candidate_map.get((role_id, slot))
            )
            if available_slots < int(role["cardinality"]):
                issues.append({
                    "code": "role-unavailable",
                    "message": (
                        f"required role {role_id!r} has candidates for "
                        f"{available_slots}/{role['cardinality']} slots"
                    ),
                })
        issues.append({
            "code": "separation-violation",
            "message": "available local principals cannot satisfy role cardinality and independence",
        })
        selected = []

    role_documents: list[dict[str, object]] = []
    selected_by_role: dict[str, list[dict[str, object]]] = {}
    for role, slot, candidate in selected:
        role_id = str(role["id"])
        address = f"{workflow_address}/role/{role_id}/slot/{slot}"
        member = dict(candidate)
        member.update({
            "slot": slot,
            "address": address,
            "assignment_generation": 1,
            "session_binding_key": _sha({
                "bundle": policy_bundle_hash,
                "story": story_id,
                "address": address,
                "generation": 1,
            }),
            "lineage": [{
                "generation": 1,
                "agent": candidate["agent"],
                "profile": candidate["profile"],
                "principal_fingerprint": candidate["principal_fingerprint"],
                "reason": "initial-assignment",
            }],
        })
        selected_by_role.setdefault(role_id, []).append(member)
    for role in roles:
        role_id = str(role["id"])
        members = selected_by_role.get(role_id, [])
        requirement = requirements.get(role_id, {
            "capabilities": [], "workspaces": [], "context_expressions": [],
            "artifact_reads": [], "artifact_writes": [], "addresses": [],
        })
        role_documents.append({
            "role": role_id,
            "duty": role["duty"],
            "required": bool(role["required"] or role_id in workflow_roles),
            "policy_required": role["required"],
            "workflow_required": role_id in workflow_roles,
            "cardinality": role["cardinality"],
            "members": members,
            "selected": members[0] if members else None,
            "candidates": candidate_map.get((role_id, 1), []),
            "candidates_by_slot": {
                str(slot): candidate_map.get((role_id, slot), [])
                for slot in range(1, int(role["cardinality"]) + 1)
            },
            "exclusions": exclusion_map.get(role_id, []),
            "independent_from": role["independent_from"],
            "may_request": role["may_request"],
            "may_judge": role["may_judge"],
            "resource_groups": role["resource_groups"],
            "packet_policy": {
                "workspace": role["workspace"],
                "driver_capabilities": role["driver_capabilities"],
                "effective_capability_ceiling": sorted(
                    set(requirement["capabilities"])
                    & set(role["capability_ceiling"])
                    & program_caps
                ),
                "context": role["context"],
                "artifacts": role["artifacts"],
                "output_schema": role["output_schema"],
                "verdict_schema": role["verdict_schema"],
                "workflow_requirements": requirement,
            },
            "capability_ceiling": role["capability_ceiling"],
            "replacement": role["replacement"],
        })

    role_by_id = {str(item["role"]): item for item in role_documents}
    implementer_role = next((item for item in role_documents if item["duty"] == "implementer"), None)
    verifier_role = next((item for item in role_documents if item["duty"] == "verifier"), None)
    implementer = implementer_role["selected"] if implementer_role else None
    verifier = verifier_role["selected"] if verifier_role else None
    separation_facts = {
        "implementer_role": implementer_role["role"] if implementer_role else None,
        "verifier_role": verifier_role["role"] if verifier_role else None,
        "different_agent": bool(implementer and verifier and implementer["agent"] != verifier["agent"]),
        "different_profile": bool(implementer and verifier and implementer["profile"] != verifier["profile"]),
        "different_principal": bool(implementer and verifier and implementer["principal_fingerprint"] != verifier["principal_fingerprint"]),
        "different_workspace_domain": bool(implementer and verifier and implementer["workspace_domain"] != verifier["workspace_domain"]),
        "different_session_binding": bool(implementer and verifier and implementer["session_binding_key"] != verifier["session_binding_key"]),
        "verifier_read_only": bool(verifier_role and verifier_role["packet_policy"]["workspace"] == "read-only"),
        "verifier_preassigned": verifier is not None,
    }
    separation_passed = all(separation_facts[key] for key in (
        "different_agent", "different_profile", "different_principal",
        "different_workspace_domain", "different_session_binding",
        "verifier_read_only", "verifier_preassigned",
    ))
    if not separation_passed and satisfiable:
        issues.append({
            "code": "separation-violation",
            "message": "implementer/verifier principal, profile, workspace, session, or read-only separation is not proven",
        })

    councils: list[dict[str, object]] = []
    for council in runtime["councils"]:
        member_receipts = [
            member
            for role_id in council["members"]
            for member in role_by_id.get(str(role_id), {}).get("members", [])
        ]
        distinct = {member["principal_fingerprint"] for member in member_receipts}
        councils.append({
            **council,
            "assigned_members": [member["address"] for member in member_receipts],
            "assigned_principals": sorted(distinct),
            "quorum_satisfiable": len(distinct) >= int(council["quorum"]),
        })
        if len(distinct) < int(council["quorum"]):
            issues.append({
                "code": "impossible-quorum",
                "message": f"council {council['id']!r} has only {len(distinct)} distinct assigned principals for quorum {council['quorum']}",
            })

    resource_conflicts = []
    for left, right in itertools.combinations(role_documents, 2):
        shared = sorted(set(left["resource_groups"]) & set(right["resource_groups"]))
        if shared:
            resource_conflicts.append({
                "left": left["role"], "right": right["role"], "groups": shared,
                "effect": "serialize",
            })

    unique_issues: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for issue in issues:
        key = (issue["code"], issue["message"])
        if key not in seen:
            unique_issues.append(issue)
            seen.add(key)
    base.update({
        "applicable": satisfiable and separation_passed and not unique_issues,
        "roles": role_documents,
        "implementer": implementer,
        "verifier": verifier,
        "meta_verifier": next((item["selected"] for item in role_documents if item["duty"] == "meta-verifier"), None),
        "master_architect": next((item["selected"] for item in role_documents if item["duty"] == "master-architect"), None),
        "councils": councils,
        "separation": {"passed": separation_passed, "facts": separation_facts},
        "resource_plan": {
            "conflicts": resource_conflicts,
            "concurrency_waves": _role_waves(team),
        },
        "issues": unique_issues,
        "why": (
            "filtered tracked pools by duty, role/agent/driver capability ceilings, "
            "availability, packet visibility, workspace, active capacity, and "
            "independence; then ranked exact role slots with rendezvous-sha256-v1"
        ),
    })
    base["assignment_hash"] = _sha({
        key: value for key, value in base.items()
        if key not in {"assignment_hash", "issues"}
    })
    return base


def plan_assignment_replacement(
    assignment: dict[str, object],
    role_id: str,
    reason: str,
    *,
    slot: int = 1,
) -> dict[str, object]:
    role = next((item for item in assignment.get("roles", []) if item["role"] == role_id), None)
    result: dict[str, object] = {
        "kind": REPLACEMENT_KIND,
        "schema_version": ORGANIZATION_SCHEMA_VERSION,
        "assignment_hash": assignment.get("assignment_hash"),
        "role": role_id,
        "slot": slot,
        "reason": reason,
        "applicable": False,
        "old": None,
        "new": None,
        "route": None,
        "invalidates": [],
        "preserved_lineage": [],
        "starts_work": False,
        "writes_state": False,
        "creates_grant": False,
    }
    if role is None:
        result["issues"] = [{"code": "role-unavailable", "message": f"unknown role {role_id!r}"}]
        return result
    old = next((member for member in role["members"] if member["slot"] == slot), None)
    result["old"] = old
    policy = role["replacement"]
    if reason not in policy["reasons"]:
        result["issues"] = [{"code": "replacement-not-allowed", "message": f"reason {reason!r} is not declared"}]
        return result
    lineage = list(old.get("lineage", [])) if old else []
    consumed = max(0, len(lineage) - 1)
    if consumed >= int(policy["max_replacements"]):
        result["route"] = policy["on_exhausted"]
        result["preserved_lineage"] = lineage
        result["issues"] = [{"code": "replacement-exhausted", "message": "finite replacement budget is exhausted"}]
        return result
    used_principals = {
        entry["principal_fingerprint"] for entry in lineage
        if entry.get("principal_fingerprint")
    }
    used_agents = {entry["agent"] for entry in lineage if entry.get("agent")}
    other_independent = {
        member["principal_fingerprint"]
        for other in assignment.get("roles", [])
        if other["role"] in role["independent_from"]
        for member in other["members"]
    }
    slot_candidates = role.get("candidates_by_slot", {}).get(
        str(slot), role["candidates"]
    )
    candidate = next((
        item for item in slot_candidates
        if item["principal_fingerprint"] not in used_principals
        and item["principal_fingerprint"] not in other_independent
        and item["agent"] not in used_agents
    ), None)
    if candidate is None:
        result["route"] = policy["on_exhausted"]
        result["preserved_lineage"] = lineage
        result["issues"] = [{"code": "replacement-exhausted", "message": "no declared independent replacement remains"}]
        return result
    generation = consumed + 2
    address = old["address"] if old else f"{assignment['workflow_address']}/role/{role_id}/slot/{slot}"
    new = dict(candidate)
    new.update({
        "slot": slot,
        "address": address,
        "assignment_generation": generation,
        "session_binding_key": _sha({
            "assignment": assignment.get("assignment_hash"),
            "address": address,
            "generation": generation,
        }),
    })
    lineage.append({
        "generation": generation,
        "agent": candidate["agent"],
        "profile": candidate["profile"],
        "principal_fingerprint": candidate["principal_fingerprint"],
        "reason": reason,
    })
    new["lineage"] = lineage
    result.update({
        "applicable": True,
        "new": new,
        "route": "replace",
        "invalidates": [address + "/outstanding-work", address + "/verdict"],
        "preserved_lineage": lineage,
        "preserves_history": policy["preserve_history"],
        "capability_unchanged": (
            old is None
            or old["effective_capability_ceiling"] == new["effective_capability_ceiling"]
        ),
        "issues": [],
    })
    return result
