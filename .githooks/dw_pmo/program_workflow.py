"""Pure compiler for reusable, finite Phase-26 program workflows.

Workflow policy is tracked data, never execution authority.  This module only
parses, validates, resolves, hashes, expands, and simulates.  General graph and
reference cycles are invalid; repetition exists solely inside typed ``loop``
and ``debate`` nodes whose finite envelope is proven at compile time.
"""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any

from .model import DwError
from .orchestration import (
    TERMINALS as SCORE_TERMINALS,
    canonical_json,
    compile_score_path,
    find_score_path,
)


WORKFLOW_KIND = "delivery-workbench-workflow"
WORKFLOW_SCHEMA_VERSION = 1
COMPILED_WORKFLOW_KIND = "delivery-workbench-compiled-workflow"
VALIDATION_KIND = "delivery-workbench-workflow-validation"
SIMULATION_KIND = "delivery-workbench-workflow-simulation"
INVENTORY_KIND = "delivery-workbench-workflow-list"

NODE_TYPES = (
    "agent", "check", "collect", "bounded_run", "subflow", "loop",
    "debate", "verdict", "gate", "checkpoint", "rail",
)
PARAMETER_TYPES = ("string", "integer", "boolean", "string-list")
ARTIFACT_KINDS = (
    "markdown", "json", "text", "git-diff", "directory", "verdict",
    "decision", "mechanical-fact",
)
ACTIVATIONS = ("success", "route")
WORKSPACE_MODES = ("read-only", "isolated-worktree")
LOOP_PURPOSES = (
    "repeat-until", "retry", "repair", "review", "audit", "escalation",
)
PREDICATE_KINDS = (
    "check-result", "verdict-result", "artifact-valid", "decision-result",
)
PREDICATE_OPERATORS = ("equals", "not-equals", "contains", "valid", "green")
VERDICT_RESULTS = ("pass", "fail", "abstain", "inconclusive")
TERMINAL_MEANINGS = (
    "complete", "blocked", "checkpoint", "escalated", "aborted",
    "awaiting-certification",
)
ROUTE_ACTIONS = ("block", "escalate", "checkpoint", "abort")
PROGRAM_CAPABILITIES = (
    "agent:dispatch", "check:execute", "workspace:write", "nudge:deliver",
    "notification:send", "evidence:materialize", "integration:apply",
    "contract:generate", "certification:objective", "certification:verdict",
    "git:commit", "git:push", "roadmap:story-start",
    "roadmap:story-complete", "roadmap:phase-advance",
)
AGENT_NODE_CAPABILITIES = ("agent:dispatch", "workspace:write")

CONTEXT_TYPES = {
    "program.slug": "string",
    "roadmap.project": "string",
    "phase.number": "integer",
    "story.id": "string",
    "story.title": "string",
    "repository.branch": "string",
    "repository.head": "string",
}

RAIL_CAPABILITIES = {
    "evidence-materialize": "evidence:materialize",
    "integration-apply": "integration:apply",
    "contract-generate": "contract:generate",
    "certification-objective": "certification:objective",
    "certification-verdict": "certification:verdict",
    "git-commit": "git:commit",
    "git-push": "git:push",
    "roadmap-story-start": "roadmap:story-start",
    "roadmap-story-complete": "roadmap:story-complete",
    "roadmap-phase-advance": "roadmap:phase-advance",
}

ENVELOPE_KEYS = (
    "node_visits", "agent_starts", "check_starts", "child_runs",
    "loop_rounds", "debate_rounds", "rail_acts", "wall_seconds",
    "artifact_bytes",
)
ENVELOPE_LIMITS = {
    "node_visits": 10_000_000,
    "agent_starts": 1_000_000,
    "check_starts": 2_000_000,
    "child_runs": 100_000,
    "loop_rounds": 1_000_000,
    "debate_rounds": 100_000,
    "rail_acts": 100_000,
    "wall_seconds": 315_360_000,
    "artifact_bytes": 1_000_000_000_000,
}

_SAFE_ID_RE = re.compile(r"^[a-z][a-z0-9]*(?:[-_][a-z0-9]+)*$")
_VERSION_RE = re.compile(r"^[0-9]+\.[0-9]+\.[0-9]+(?:[-+][a-zA-Z0-9.-]+)?$")
_ARTIFACT_REF_RE = re.compile(
    r"^[a-z][a-z0-9]*(?:[-_][a-z0-9]+)*\."
    r"[a-z][a-z0-9]*(?:[-_][a-z0-9]+)*$"
)

_TOP_KEYS = {
    "kind", "schema_version", "slug", "title", "description", "version",
    "parameters", "defaults", "nodes", "terminals", "layout",
}
_PARAMETER_KEYS = {
    "id", "type", "required", "enum", "minimum", "maximum", "max_bytes",
}
_TERMINAL_KEYS = {"id", "meaning", "description"}
_LAYOUT_KEYS = {"nodes", "viewport"}
_NODE_LAYOUT_KEYS = {"x", "y"}
_VIEWPORT_KEYS = {"x", "y", "zoom"}
_EXPRESSION_KEYS = {"kind", "value", "name"}
_OUTPUT_KEYS = {"id", "kind", "max_bytes", "schema"}
_ROUTE_KEYS = {"kind", "target"}
_PREDICATE_KEYS = {"kind", "source", "operator", "value"}
_COMMON_NODE_KEYS = {
    "id", "type", "title", "description", "activation", "needs",
    "resource_groups", "inputs", "outputs",
}
_FAILABLE_NODE_KEYS = _COMMON_NODE_KEYS | {"on_success", "on_failure"}
_NODE_KEYS = {
    "agent": _FAILABLE_NODE_KEYS | {
        "role", "task", "workspace", "capability_ceiling",
        "timeout_seconds", "max_attempts",
    },
    "check": _FAILABLE_NODE_KEYS | {
        "runner", "expect", "timeout_seconds", "max_attempts",
    },
    "collect": _FAILABLE_NODE_KEYS | {"producers"},
    "bounded_run": _FAILABLE_NODE_KEYS | {
        "score", "expected_terminal", "capability_ceiling", "budgets",
    },
    "subflow": _FAILABLE_NODE_KEYS | {
        "workflow", "version", "with", "capability_ceiling",
    },
    "loop": _COMMON_NODE_KEYS | {
        "purpose", "workflow", "version", "with", "max_rounds", "until",
        "carry", "capability_ceiling", "on_success", "on_exhausted",
    },
    "debate": _COMMON_NODE_KEYS | {
        "participants", "judge_role", "max_rounds", "quorum",
        "artifact_max_bytes", "round_timeout_seconds", "tie_policy",
        "dissent_policy", "on_consensus", "on_dissent", "on_exhausted",
    },
    "verdict": _COMMON_NODE_KEYS | {
        "role", "rubric", "subject", "freshness_seconds",
        "max_rationale_bytes", "results", "routes",
    },
    "gate": _COMMON_NODE_KEYS | {
        "facts", "verdicts", "operator", "missing_policy",
        "dissent_policy", "routes",
    },
    "checkpoint": _COMMON_NODE_KEYS | {
        "prompt_id", "prompt", "expires_seconds", "options",
    },
    "rail": _FAILABLE_NODE_KEYS | {"action", "capability", "timeout_seconds"},
}
_COMMAND_RUNNER_KEYS = {"kind", "argv", "cwd", "writes", "output_bytes"}
_BUILTIN_RUNNER_KEYS = {
    "kind", "name", "path", "schema", "allowed_paths", "output_bytes",
}
_EXPECT_KEYS = {"exit_code"}
_BOUNDED_RUN_BUDGET_KEYS = {
    "max_agent_starts", "max_check_starts", "max_wall_seconds",
    "max_artifact_bytes",
}
_OPTION_KEYS = {"id", "label", "route"}


class WorkflowValidationError(DwError):
    """A deterministic refusal carrying every workflow diagnostic."""

    def __init__(self, diagnostics: list[dict[str, str]]) -> None:
        self.diagnostics = diagnostics
        first = diagnostics[0] if diagnostics else {
            "source": "workflow", "pointer": "/", "message": "invalid workflow",
        }
        super().__init__(
            "workflow invalid at "
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


def _hash(value: object) -> str:
    return "sha256:" + hashlib.sha256(
        canonical_json(value).encode("utf-8")
    ).hexdigest()


def parse_workflow_text(text: str, source: str = "workflow") -> dict[str, object]:
    try:
        value = json.loads(
            text,
            object_pairs_hook=_object_without_duplicates,
            parse_constant=lambda token: (_ for _ in ()).throw(
                ValueError(f"non-finite JSON number: {token}")
            ),
        )
    except (_DuplicateJSONKey, json.JSONDecodeError, ValueError) as exc:
        raise DwError(f"cannot parse workflow policy {source}: {exc}") from exc
    if not isinstance(value, dict):
        raise DwError(f"workflow policy {source} must be a JSON object")
    return value


def load_workflow(path: Path) -> dict[str, object]:
    try:
        return parse_workflow_text(path.read_text(encoding="utf-8"), str(path))
    except OSError as exc:
        raise DwError(f"cannot read workflow policy {path}: {exc}") from exc


def workflow_dir(root: Path) -> Path:
    root = root.resolve()
    path = (root / "pm" / "workflows").resolve()
    if path != root and root not in path.parents:
        raise DwError("pm/workflows resolves outside the repository")
    return path


def discover_workflow_paths(root: Path) -> list[Path]:
    allowed = workflow_dir(root)
    if not allowed.is_dir():
        return []
    paths: list[Path] = []
    for candidate in sorted(allowed.glob("*.json"), key=lambda item: item.name):
        resolved = candidate.resolve()
        if resolved.parent != allowed:
            raise DwError(f"workflow escapes pm/workflows: {candidate.name}")
        if resolved.is_file():
            paths.append(resolved)
    return paths


def find_workflow_path(root: Path, selector: str) -> Path:
    if not _SAFE_ID_RE.fullmatch(selector or ""):
        raise DwError(f"unsafe workflow selector: {selector!r}")
    matches: list[Path] = []
    for path in discover_workflow_paths(root):
        if path.stem == selector:
            matches.append(path)
            continue
        try:
            if load_workflow(path).get("slug") == selector:
                matches.append(path)
        except DwError:
            continue
    matches = list(dict.fromkeys(matches))
    if not matches:
        raise DwError(f"workflow not found: {selector}")
    if len(matches) > 1:
        raise DwError(f"ambiguous workflow selector: {selector}")
    return matches[0]


def _empty_envelope() -> dict[str, int]:
    return {key: 0 for key in ENVELOPE_KEYS}


def _add_envelopes(*values: dict[str, int]) -> dict[str, int]:
    return {
        key: sum(int(value.get(key, 0)) for value in values)
        for key in ENVELOPE_KEYS
    }


def _scale_envelope(value: dict[str, int], count: int) -> dict[str, int]:
    return {key: int(value.get(key, 0)) * count for key in ENVELOPE_KEYS}


def _safe_relative_path(value: object) -> bool:
    if not isinstance(value, str) or not value or len(value) > 500:
        return False
    path = Path(value)
    return not path.is_absolute() and ".." not in path.parts and "\x00" not in value


class _RegistryCompiler:
    def __init__(self, root: Path) -> None:
        self.root = root.resolve()
        self.diagnostics: list[dict[str, str]] = []
        self.sources: dict[str, dict[str, object]] = {}
        self.expanded_node_count = 0

    def diag(
        self,
        source: str,
        pointer: str,
        code: str,
        message: str,
        remediation: str,
    ) -> None:
        self.diagnostics.append({
            "source": source,
            "pointer": pointer or "/",
            "code": code,
            "message": message,
            "remediation": remediation,
        })

    def exact_keys(
        self,
        value: dict[str, object],
        allowed: set[str],
        source: str,
        pointer: str,
    ) -> None:
        for key in sorted(set(value) - allowed):
            self.diag(
                source,
                f"{pointer}/{key}" if pointer else f"/{key}",
                "unknown-key",
                f"unknown key {key!r}",
                "remove the key or use a contracted workflow field",
            )

    def string(
        self,
        value: object,
        source: str,
        pointer: str,
        *,
        pattern: re.Pattern[str] | None = None,
        maximum: int = 5_000,
    ) -> str:
        if not isinstance(value, str) or not value or len(value) > maximum:
            self.diag(source, pointer, "invalid-value", "expected a non-empty bounded string", "provide a bounded string")
            return ""
        if pattern is not None and not pattern.fullmatch(value):
            self.diag(source, pointer, "unsafe-selector", f"unsafe selector {value!r}", "use a stable contracted selector")
            return ""
        return value

    def optional_string(
        self,
        value: object,
        source: str,
        pointer: str,
        maximum: int = 5_000,
    ) -> str | None:
        if value is None:
            return None
        if not isinstance(value, str) or len(value) > maximum:
            self.diag(source, pointer, "invalid-value", "expected a bounded string", "provide a bounded string or remove it")
            return None
        return value

    def positive_int(
        self,
        value: object,
        source: str,
        pointer: str,
        default: int,
        maximum: int,
    ) -> int:
        if value is None:
            return default
        if isinstance(value, bool) or not isinstance(value, int) or not 1 <= value <= maximum:
            self.diag(source, pointer, "invalid-bound", f"expected an integer from 1 through {maximum}", "provide a finite positive bound")
            return default
        return value

    def string_list(
        self,
        value: object,
        source: str,
        pointer: str,
        *,
        choices: tuple[str, ...] | None = None,
        minimum: int = 0,
        maximum: int = 100,
        pattern: re.Pattern[str] = _SAFE_ID_RE,
    ) -> list[str]:
        if (
            not isinstance(value, list)
            or not minimum <= len(value) <= maximum
            or any(not isinstance(item, str) or not pattern.fullmatch(item) for item in value)
            or len(set(value)) != len(value)
            or (choices is not None and any(item not in choices for item in value))
        ):
            self.diag(source, pointer, "invalid-list", "expected a unique bounded list of contracted strings", "provide valid unique values")
            return []
        return list(value)

    def normalize_layout(self, value: object, source: str) -> dict[str, object]:
        if value is None:
            return {"nodes": {}, "viewport": {"x": 0, "y": 0, "zoom": 1}}
        if not isinstance(value, dict):
            self.diag(source, "/layout", "wrong-type", "layout must be an object", "provide nodes and viewport")
            value = {}
        self.exact_keys(value, _LAYOUT_KEYS, source, "/layout")
        nodes_raw = value.get("nodes", {})
        if not isinstance(nodes_raw, dict):
            self.diag(source, "/layout/nodes", "wrong-type", "layout nodes must be an object", "map node ids to x/y positions")
            nodes_raw = {}
        nodes: dict[str, dict[str, int]] = {}
        for node_id, position in sorted(nodes_raw.items()):
            pointer = f"/layout/nodes/{node_id}"
            if not isinstance(node_id, str) or not _SAFE_ID_RE.fullmatch(node_id) or not isinstance(position, dict):
                self.diag(source, pointer, "invalid-layout", "layout entry must map a node id to an object", "use a declared node id and x/y values")
                continue
            self.exact_keys(position, _NODE_LAYOUT_KEYS, source, pointer)
            x = position.get("x")
            y = position.get("y")
            if any(isinstance(item, bool) or not isinstance(item, int) or abs(item) > 1_000_000 for item in (x, y)):
                self.diag(source, pointer, "invalid-layout", "x and y must be bounded integers", "provide bounded editor coordinates")
                continue
            nodes[node_id] = {"x": int(x), "y": int(y)}
        viewport_raw = value.get("viewport", {"x": 0, "y": 0, "zoom": 1})
        if not isinstance(viewport_raw, dict):
            self.diag(source, "/layout/viewport", "wrong-type", "viewport must be an object", "provide x, y, and zoom")
            viewport_raw = {"x": 0, "y": 0, "zoom": 1}
        self.exact_keys(viewport_raw, _VIEWPORT_KEYS, source, "/layout/viewport")
        viewport: dict[str, int | float] = {}
        for key, default in (("x", 0), ("y", 0), ("zoom", 1)):
            item = viewport_raw.get(key, default)
            if isinstance(item, bool) or not isinstance(item, (int, float)) or abs(item) > 1_000_000:
                self.diag(source, f"/layout/viewport/{key}", "invalid-layout", f"{key} must be a bounded number", "provide a bounded editor viewport")
                item = default
            viewport[key] = item
        return {"nodes": nodes, "viewport": viewport}

    @staticmethod
    def _value_matches(value: object, parameter: dict[str, object]) -> bool:
        kind = parameter["type"]
        if kind == "string":
            valid = isinstance(value, str) and len(value.encode("utf-8")) <= int(parameter["max_bytes"])
        elif kind == "integer":
            valid = isinstance(value, int) and not isinstance(value, bool)
            if valid and parameter.get("minimum") is not None:
                valid = int(value) >= int(parameter["minimum"])
            if valid and parameter.get("maximum") is not None:
                valid = int(value) <= int(parameter["maximum"])
        elif kind == "boolean":
            valid = isinstance(value, bool)
        else:
            valid = (
                isinstance(value, list)
                and len(value) <= 100
                and all(isinstance(item, str) and len(item.encode("utf-8")) <= int(parameter["max_bytes"]) for item in value)
            )
        enum = parameter.get("enum")
        return bool(valid and (not enum or value in enum))

    def normalize_parameters(
        self,
        value: object,
        defaults_value: object,
        source: str,
    ) -> tuple[list[dict[str, object]], dict[str, object]]:
        if value is None:
            value = []
        if not isinstance(value, list) or len(value) > 100:
            self.diag(source, "/parameters", "wrong-type", "parameters must be a bounded array", "declare at most 100 typed parameters")
            value = []
        parameters: list[dict[str, object]] = []
        ids: set[str] = set()
        for index, item in enumerate(value):
            pointer = f"/parameters/{index}"
            if not isinstance(item, dict):
                self.diag(source, pointer, "wrong-type", "parameter must be an object", "provide a typed parameter object")
                continue
            self.exact_keys(item, _PARAMETER_KEYS, source, pointer)
            parameter_id = self.string(item.get("id"), source, f"{pointer}/id", pattern=_SAFE_ID_RE)
            if parameter_id in ids:
                self.diag(source, f"{pointer}/id", "duplicate-id", f"duplicate parameter id {parameter_id!r}", "use unique parameter ids")
            ids.add(parameter_id)
            kind = item.get("type")
            if kind not in PARAMETER_TYPES:
                self.diag(source, f"{pointer}/type", "unsupported-type", f"unsupported parameter type {kind!r}", f"choose one of: {', '.join(PARAMETER_TYPES)}")
                kind = "string"
            required = item.get("required", True)
            if not isinstance(required, bool):
                self.diag(source, f"{pointer}/required", "wrong-type", "required must be boolean", "use true or false")
                required = True
            minimum = item.get("minimum")
            maximum = item.get("maximum")
            if kind != "integer" and (minimum is not None or maximum is not None):
                self.diag(source, pointer, "parameter-bound-type", "minimum/maximum apply only to integer parameters", "remove numeric bounds or use integer")
                minimum = maximum = None
            if kind == "integer":
                if minimum is not None and (isinstance(minimum, bool) or not isinstance(minimum, int)):
                    self.diag(source, f"{pointer}/minimum", "invalid-bound", "minimum must be an integer", "provide an integer bound")
                    minimum = None
                if maximum is not None and (isinstance(maximum, bool) or not isinstance(maximum, int)):
                    self.diag(source, f"{pointer}/maximum", "invalid-bound", "maximum must be an integer", "provide an integer bound")
                    maximum = None
                if minimum is not None and maximum is not None and int(minimum) > int(maximum):
                    self.diag(source, pointer, "invalid-bound", "parameter minimum exceeds maximum", "order the numeric bounds")
            max_bytes = self.positive_int(item.get("max_bytes"), source, f"{pointer}/max_bytes", 5_000, 1_000_000)
            enum = item.get("enum", [])
            if enum is None:
                enum = []
            if not isinstance(enum, list) or len(enum) > 100 or len({canonical_json(entry) for entry in enum}) != len(enum):
                self.diag(source, f"{pointer}/enum", "invalid-enum", "enum must be a unique bounded array", "provide unique values")
                enum = []
            parameter = {
                "id": parameter_id,
                "type": kind,
                "required": required,
                "enum": list(enum),
                "minimum": minimum,
                "maximum": maximum,
                "max_bytes": max_bytes,
            }
            if any(not self._value_matches(entry, {**parameter, "enum": []}) for entry in enum):
                self.diag(source, f"{pointer}/enum", "enum-type", "enum contains a value outside the declared type/bounds", "make every enum value match the parameter")
            parameters.append(parameter)
        defaults_raw = defaults_value if defaults_value is not None else {}
        if not isinstance(defaults_raw, dict):
            self.diag(source, "/defaults", "wrong-type", "defaults must be an object", "map parameter ids to literal values")
            defaults_raw = {}
        parameter_by_id = {str(item["id"]): item for item in parameters}
        defaults: dict[str, object] = {}
        for key, default in sorted(defaults_raw.items()):
            if key not in parameter_by_id:
                self.diag(source, f"/defaults/{key}", "unknown-parameter", f"default names undeclared parameter {key!r}", "declare the parameter or remove the default")
                continue
            if not self._value_matches(default, parameter_by_id[key]):
                self.diag(source, f"/defaults/{key}", "parameter-type", "default does not match the declared parameter type/bounds", "provide a typed default")
                continue
            defaults[key] = default
        return parameters, defaults

    def normalize_expression(
        self,
        value: object,
        source: str,
        pointer: str,
        parameter_types: dict[str, str],
        *,
        expected: dict[str, object] | None = None,
        allow_artifact: bool = True,
    ) -> dict[str, object]:
        if not isinstance(value, dict):
            self.diag(source, pointer, "unsafe-binding", "bindings must be typed expression objects, never text substitution", "use literal, parameter, context, or artifact expression syntax")
            return {"kind": "literal", "value": None}
        self.exact_keys(value, _EXPRESSION_KEYS, source, pointer)
        kind = value.get("kind")
        if kind == "literal":
            if set(value) != {"kind", "value"}:
                self.diag(source, pointer, "unsafe-binding", "literal expression requires exactly kind/value", "remove unrelated expression keys")
            literal = value.get("value")
            if expected is not None and not self._value_matches(literal, expected):
                self.diag(source, pointer, "parameter-type", "literal does not match the destination parameter", "bind a value of the declared type")
            return {"kind": "literal", "value": literal}
        if kind in {"parameter", "context", "artifact"}:
            if set(value) != {"kind", "name"}:
                self.diag(source, pointer, "unsafe-binding", f"{kind} expression requires exactly kind/name", "remove unrelated expression keys")
            name = value.get("name")
            if not isinstance(name, str):
                self.diag(source, f"{pointer}/name", "invalid-value", "expression name must be a string", "provide a declared name")
                name = ""
            expression_type: str | None = None
            if kind == "parameter":
                if name not in parameter_types:
                    self.diag(source, f"{pointer}/name", "unknown-parameter", f"parameter {name!r} is not declared by the caller", "reference a caller parameter")
                expression_type = parameter_types.get(str(name))
            elif kind == "context":
                if name not in CONTEXT_TYPES:
                    self.diag(source, f"{pointer}/name", "unsafe-context", f"context reference {name!r} is not contracted", "use a closed context reference")
                expression_type = CONTEXT_TYPES.get(str(name))
            else:
                if not allow_artifact or not _ARTIFACT_REF_RE.fullmatch(str(name)):
                    self.diag(source, f"{pointer}/name", "unsafe-artifact-reference", f"artifact reference {name!r} is invalid here", "reference a declared producer as node.output")
            if expected is not None and expression_type is not None and expression_type != expected["type"]:
                self.diag(source, pointer, "parameter-type", f"{kind} expression type {expression_type!r} does not match {expected['type']!r}", "bind a compatible typed value")
            return {"kind": kind, "name": str(name)}
        self.diag(source, f"{pointer}/kind", "unsupported-expression", f"unsupported expression kind {kind!r}", "use literal, parameter, context, or artifact")
        return {"kind": "literal", "value": None}

    def normalize_bindings(
        self,
        value: object,
        parameters: list[dict[str, object]],
        defaults: dict[str, object],
        source: str,
        pointer: str,
        parent_types: dict[str, str],
        *,
        require_bound: bool,
    ) -> dict[str, dict[str, object]]:
        if value is None:
            value = {}
        if not isinstance(value, dict):
            self.diag(source, pointer, "wrong-type", "parameter bindings must be an object", "map declared parameter ids to typed expressions")
            value = {}
        parameter_by_id = {str(item["id"]): item for item in parameters}
        result = {
            key: {"kind": "literal", "value": default}
            for key, default in sorted(defaults.items())
        }
        for key, expression in sorted(value.items()):
            if key not in parameter_by_id:
                self.diag(source, f"{pointer}/{key}", "unknown-parameter", f"binding names undeclared parameter {key!r}", "bind only declared parameters")
                continue
            result[key] = self.normalize_expression(
                expression, source, f"{pointer}/{key}", parent_types,
                expected=parameter_by_id[key], allow_artifact=False,
            )
        if require_bound:
            for parameter in parameters:
                parameter_id = str(parameter["id"])
                if parameter["required"] and parameter_id not in result:
                    self.diag(source, f"{pointer}/{parameter_id}", "parameter-unbound", f"required parameter {parameter_id!r} has no binding or default", "bind the parameter explicitly")
        return result

    def normalize_route(
        self,
        value: object,
        source: str,
        pointer: str,
    ) -> dict[str, str]:
        if not isinstance(value, dict):
            self.diag(source, pointer, "wrong-type", "route must be an object", "provide kind and target")
            value = {}
        self.exact_keys(value, _ROUTE_KEYS, source, pointer)
        kind = value.get("kind")
        target = value.get("target")
        if kind not in {"node", "terminal", "action"}:
            self.diag(source, f"{pointer}/kind", "unsupported-route", f"unsupported route kind {kind!r}", "use node, terminal, or action")
            kind = "action"
        if not isinstance(target, str) or not _SAFE_ID_RE.fullmatch(target):
            self.diag(source, f"{pointer}/target", "unsafe-selector", f"unsafe route target {target!r}", "use a stable target id")
            target = "abort"
        if kind == "action" and target not in ROUTE_ACTIONS:
            self.diag(source, f"{pointer}/target", "unsupported-route", f"unsupported route action {target!r}", f"choose one of: {', '.join(ROUTE_ACTIONS)}")
        return {"kind": str(kind), "target": str(target)}

    def normalize_outputs(
        self,
        value: object,
        source: str,
        pointer: str,
    ) -> list[dict[str, object]]:
        if value is None:
            return []
        if not isinstance(value, list) or len(value) > 100:
            self.diag(source, pointer, "wrong-type", "outputs must be a bounded array", "declare typed bounded artifacts")
            return []
        outputs: list[dict[str, object]] = []
        ids: set[str] = set()
        for index, item in enumerate(value):
            item_pointer = f"{pointer}/{index}"
            if not isinstance(item, dict):
                self.diag(source, item_pointer, "wrong-type", "output must be an object", "provide id, kind, and max_bytes")
                continue
            self.exact_keys(item, _OUTPUT_KEYS, source, item_pointer)
            output_id = self.string(item.get("id"), source, f"{item_pointer}/id", pattern=_SAFE_ID_RE)
            if output_id in ids:
                self.diag(source, f"{item_pointer}/id", "duplicate-id", f"duplicate output id {output_id!r}", "use unique output ids per node")
            ids.add(output_id)
            kind = item.get("kind")
            if kind not in ARTIFACT_KINDS:
                self.diag(source, f"{item_pointer}/kind", "unsupported-artifact", f"unsupported artifact kind {kind!r}", f"choose one of: {', '.join(ARTIFACT_KINDS)}")
                kind = "text"
            max_bytes = self.positive_int(item.get("max_bytes"), source, f"{item_pointer}/max_bytes", 100_000, 100_000_000)
            schema = item.get("schema")
            if schema is not None and not _safe_relative_path(schema):
                self.diag(source, f"{item_pointer}/schema", "unsafe-path", "schema must be a contained relative path", "use a repository-relative schema path")
                schema = None
            normalized = {"id": output_id, "kind": kind, "max_bytes": max_bytes}
            if schema is not None:
                normalized["schema"] = schema
            outputs.append(normalized)
        return outputs

    def normalize_predicate(
        self,
        value: object,
        source: str,
        pointer: str,
    ) -> dict[str, object]:
        if not isinstance(value, dict):
            self.diag(source, pointer, "wrong-type", "loop predicate must be an object", "declare a typed finite progress predicate")
            value = {}
        self.exact_keys(value, _PREDICATE_KEYS, source, pointer)
        kind = value.get("kind")
        if kind not in PREDICATE_KINDS:
            self.diag(source, f"{pointer}/kind", "unsupported-predicate", f"unsupported predicate kind {kind!r}", f"choose one of: {', '.join(PREDICATE_KINDS)}")
            kind = "artifact-valid"
        source_ref = value.get("source")
        if not isinstance(source_ref, str) or not source_ref or len(source_ref) > 250:
            self.diag(source, f"{pointer}/source", "invalid-value", "predicate source must name one typed child result", "name a check, verdict, artifact, or decision result")
            source_ref = "result"
        operator = value.get("operator")
        if operator not in PREDICATE_OPERATORS:
            self.diag(source, f"{pointer}/operator", "unsupported-predicate", f"unsupported predicate operator {operator!r}", f"choose one of: {', '.join(PREDICATE_OPERATORS)}")
            operator = "green"
        result: dict[str, object] = {
            "kind": kind,
            "source": source_ref,
            "operator": operator,
        }
        if "value" in value:
            literal = value.get("value")
            if isinstance(literal, (dict, list)) or not isinstance(literal, (str, int, bool, type(None))):
                self.diag(source, f"{pointer}/value", "unsafe-predicate", "predicate comparison value must be a JSON scalar", "use a closed scalar result")
            else:
                result["value"] = literal
        if operator in {"equals", "not-equals", "contains"} and "value" not in result:
            self.diag(source, f"{pointer}/value", "missing-predicate-value", f"operator {operator!r} requires a scalar value", "declare the comparison value")
        return result

    def normalize_runner(
        self,
        value: object,
        source: str,
        pointer: str,
    ) -> dict[str, object]:
        if not isinstance(value, dict):
            self.diag(source, pointer, "wrong-type", "check runner must be an object", "declare an exact command or built-in check")
            value = {}
        kind = value.get("kind")
        if kind == "command":
            self.exact_keys(value, _COMMAND_RUNNER_KEYS, source, pointer)
            argv = value.get("argv")
            if (
                not isinstance(argv, list) or not argv or len(argv) > 100
                or any(not isinstance(item, str) or not item or len(item) > 2_000 for item in argv)
            ):
                self.diag(source, f"{pointer}/argv", "unsafe-argv", "argv must be a non-empty bounded literal string array", "declare exact argv without parameter substitution")
                argv = []
            cwd = value.get("cwd", ".")
            if not _safe_relative_path(cwd):
                self.diag(source, f"{pointer}/cwd", "unsafe-path", "cwd must stay inside the repository", "use a contained relative path")
                cwd = "."
            writes = value.get("writes", [])
            if (
                not isinstance(writes, list) or len(writes) > 100
                or any(not _safe_relative_path(item) for item in writes)
                or len(set(writes)) != len(writes)
            ):
                self.diag(source, f"{pointer}/writes", "unsafe-path", "writes must be unique contained relative paths", "declare exact write scope")
                writes = []
            return {
                "kind": "command",
                "argv": list(argv),
                "cwd": cwd,
                "writes": list(writes),
                "output_bytes": self.positive_int(value.get("output_bytes"), source, f"{pointer}/output_bytes", 100_000, 10_000_000),
            }
        if kind == "builtin":
            self.exact_keys(value, _BUILTIN_RUNNER_KEYS, source, pointer)
            name = value.get("name")
            if name not in {"file-exists", "json-schema", "diff-scope", "rail-status"}:
                self.diag(source, f"{pointer}/name", "unsupported-check", f"unsupported built-in check {name!r}", "use a contracted built-in check")
                name = "file-exists"
            result: dict[str, object] = {
                "kind": "builtin",
                "name": name,
                "output_bytes": self.positive_int(value.get("output_bytes"), source, f"{pointer}/output_bytes", 100_000, 10_000_000),
            }
            for key in ("path", "schema"):
                if key in value:
                    if not _safe_relative_path(value.get(key)):
                        self.diag(source, f"{pointer}/{key}", "unsafe-path", f"{key} must be a contained relative path", "use a repository-relative path")
                    else:
                        result[key] = value[key]
            if "allowed_paths" in value:
                allowed = value.get("allowed_paths")
                if (
                    not isinstance(allowed, list) or len(allowed) > 100
                    or any(not _safe_relative_path(item) for item in allowed)
                    or len(set(allowed)) != len(allowed)
                ):
                    self.diag(source, f"{pointer}/allowed_paths", "unsafe-path", "allowed_paths must be unique contained paths", "declare exact relative paths")
                    allowed = []
                result["allowed_paths"] = list(allowed)
            required = {"file-exists": "path", "json-schema": "schema", "diff-scope": "allowed_paths"}.get(str(name))
            if required and required not in result:
                self.diag(source, f"{pointer}/{required}", "missing-check-field", f"{name} requires {required}", f"declare {required}")
            return result
        self.diag(source, f"{pointer}/kind", "unsupported-check", f"unsupported runner kind {kind!r}", "use command or builtin")
        return {"kind": "builtin", "name": "file-exists", "path": "missing"}

    def normalize_terminals(
        self,
        value: object,
        source: str,
    ) -> list[dict[str, str]]:
        if not isinstance(value, list) or not value or len(value) > 50:
            self.diag(source, "/terminals", "missing-terminals", "workflow needs a bounded non-empty terminal list", "declare terminal ids and meanings")
            value = []
        terminals: list[dict[str, str]] = []
        ids: set[str] = set()
        for index, item in enumerate(value):
            pointer = f"/terminals/{index}"
            if not isinstance(item, dict):
                self.diag(source, pointer, "wrong-type", "terminal must be an object", "provide id and meaning")
                continue
            self.exact_keys(item, _TERMINAL_KEYS, source, pointer)
            terminal_id = self.string(item.get("id"), source, f"{pointer}/id", pattern=_SAFE_ID_RE)
            if terminal_id in ids:
                self.diag(source, f"{pointer}/id", "duplicate-id", f"duplicate terminal id {terminal_id!r}", "use unique terminal ids")
            ids.add(terminal_id)
            meaning = item.get("meaning")
            if meaning not in TERMINAL_MEANINGS:
                self.diag(source, f"{pointer}/meaning", "unsupported-terminal", f"unsupported terminal meaning {meaning!r}", f"choose one of: {', '.join(TERMINAL_MEANINGS)}")
                meaning = "blocked"
            terminal = {"id": terminal_id, "meaning": str(meaning)}
            description = self.optional_string(item.get("description"), source, f"{pointer}/description")
            if description is not None:
                terminal["description"] = description
            terminals.append(terminal)
        return terminals

    def _normalize_common_node(
        self,
        raw: dict[str, object],
        index: int,
        source: str,
        parameter_types: dict[str, str],
    ) -> dict[str, object]:
        pointer = f"/nodes/{index}"
        node_id = self.string(raw.get("id"), source, f"{pointer}/id", pattern=_SAFE_ID_RE)
        node_type = raw.get("type")
        if node_type not in NODE_TYPES:
            self.diag(source, f"{pointer}/type", "unsupported-node-type", f"unsupported node type {node_type!r}", f"choose one of: {', '.join(NODE_TYPES)}")
            node_type = "collect"
        activation = raw.get("activation", "success")
        if activation not in ACTIVATIONS:
            self.diag(source, f"{pointer}/activation", "unsupported-value", f"unsupported activation {activation!r}", "use success or route")
            activation = "success"
        needs = self.string_list(raw.get("needs", []), source, f"{pointer}/needs", maximum=500)
        groups = self.string_list(raw.get("resource_groups", []), source, f"{pointer}/resource_groups", maximum=100)
        inputs_raw = raw.get("inputs", {})
        if not isinstance(inputs_raw, dict) or len(inputs_raw) > 100:
            self.diag(source, f"{pointer}/inputs", "wrong-type", "inputs must be a bounded object of typed expressions", "map stable input names to expressions")
            inputs_raw = {}
        inputs: dict[str, dict[str, object]] = {}
        for name, expression in sorted(inputs_raw.items()):
            if not isinstance(name, str) or not _SAFE_ID_RE.fullmatch(name):
                self.diag(source, f"{pointer}/inputs/{name}", "unsafe-selector", "input name is unsafe", "use a stable lowercase id")
                continue
            inputs[name] = self.normalize_expression(
                expression, source, f"{pointer}/inputs/{name}", parameter_types,
                allow_artifact=True,
            )
        result: dict[str, object] = {
            "id": node_id,
            "type": node_type,
            "activation": activation,
            "needs": needs,
            "resource_groups": groups,
            "inputs": inputs,
            "outputs": self.normalize_outputs(raw.get("outputs"), source, f"{pointer}/outputs"),
        }
        for key, maximum in (("title", 500), ("description", 5_000)):
            text = self.optional_string(raw.get(key), source, f"{pointer}/{key}", maximum)
            if text is not None:
                result[key] = text
        return result

    def normalize_node(
        self,
        raw_value: object,
        index: int,
        source: str,
        parameter_types: dict[str, str],
    ) -> dict[str, object]:
        pointer = f"/nodes/{index}"
        if not isinstance(raw_value, dict):
            self.diag(source, pointer, "wrong-type", "node must be an object", "provide an exact typed node")
            raw: dict[str, object] = {}
        else:
            raw = raw_value
        node_type = raw.get("type")
        allowed = _NODE_KEYS.get(str(node_type), _COMMON_NODE_KEYS)
        self.exact_keys(raw, allowed, source, pointer)
        node = self._normalize_common_node(raw, index, source, parameter_types)
        node_type = str(node["type"])
        output_bytes = sum(int(output["max_bytes"]) for output in node["outputs"])
        envelope = _empty_envelope()
        envelope["node_visits"] = 1

        if node_type in {"agent", "check", "collect", "bounded_run", "subflow", "rail"}:
            if "on_success" in raw:
                node["on_success"] = self.normalize_route(raw.get("on_success"), source, f"{pointer}/on_success")
            if "on_failure" in raw:
                node["on_failure"] = self.normalize_route(raw.get("on_failure"), source, f"{pointer}/on_failure")

        if node_type == "agent":
            node["role"] = self.string(raw.get("role"), source, f"{pointer}/role", pattern=_SAFE_ID_RE)
            node["task"] = self.string(raw.get("task"), source, f"{pointer}/task", maximum=10_000)
            workspace = raw.get("workspace", "read-only")
            if workspace not in WORKSPACE_MODES:
                self.diag(source, f"{pointer}/workspace", "unsupported-value", f"unsupported workspace {workspace!r}", "use read-only or isolated-worktree")
                workspace = "read-only"
            capabilities = self.string_list(
                raw.get("capability_ceiling", ["agent:dispatch"]), source,
                f"{pointer}/capability_ceiling", choices=AGENT_NODE_CAPABILITIES,
                minimum=1, maximum=len(AGENT_NODE_CAPABILITIES), pattern=re.compile(r"^[a-z]+:[a-z-]+$"),
            )
            if "agent:dispatch" not in capabilities:
                self.diag(source, f"{pointer}/capability_ceiling", "capability-missing", "agent node requires agent:dispatch", "include agent:dispatch in the ceiling")
            if workspace == "isolated-worktree" and "workspace:write" not in capabilities:
                self.diag(source, f"{pointer}/capability_ceiling", "capability-missing", "isolated writer requires workspace:write", "include workspace:write or use read-only")
            for key in ("timeout_seconds", "max_attempts"):
                if key not in raw:
                    self.diag(source, f"{pointer}/{key}", "missing-bound", f"agent must declare {key} explicitly", f"add a finite positive {key}")
            if not node["outputs"]:
                self.diag(source, f"{pointer}/outputs", "missing-output", "agent must declare at least one bounded typed output", "declare an output schema/kind and max_bytes")
            attempts = self.positive_int(raw.get("max_attempts"), source, f"{pointer}/max_attempts", 1, 20)
            timeout = self.positive_int(raw.get("timeout_seconds"), source, f"{pointer}/timeout_seconds", 900, 86_400)
            node.update({
                "workspace": workspace,
                "capability_ceiling": capabilities,
                "max_attempts": attempts,
                "timeout_seconds": timeout,
            })
            envelope.update({
                "node_visits": attempts,
                "agent_starts": attempts,
                "wall_seconds": attempts * timeout,
                "artifact_bytes": attempts * output_bytes,
            })
        elif node_type == "check":
            node["runner"] = self.normalize_runner(raw.get("runner"), source, f"{pointer}/runner")
            expect = raw.get("expect", {"exit_code": 0})
            if not isinstance(expect, dict):
                self.diag(source, f"{pointer}/expect", "wrong-type", "expect must be an object", "provide an exact exit_code")
                expect = {"exit_code": 0}
            self.exact_keys(expect, _EXPECT_KEYS, source, f"{pointer}/expect")
            exit_code = expect.get("exit_code", 0)
            if isinstance(exit_code, bool) or not isinstance(exit_code, int) or not 0 <= exit_code <= 255:
                self.diag(source, f"{pointer}/expect/exit_code", "invalid-exit-code", "exit_code must be from 0 through 255", "provide an exact expected exit code")
                exit_code = 0
            for key in ("timeout_seconds", "max_attempts"):
                if key not in raw:
                    self.diag(source, f"{pointer}/{key}", "missing-bound", f"check must declare {key} explicitly", f"add a finite positive {key}")
            attempts = self.positive_int(raw.get("max_attempts"), source, f"{pointer}/max_attempts", 1, 20)
            timeout = self.positive_int(raw.get("timeout_seconds"), source, f"{pointer}/timeout_seconds", 300, 86_400)
            node.update({"expect": {"exit_code": exit_code}, "max_attempts": attempts, "timeout_seconds": timeout})
            envelope.update({
                "node_visits": attempts,
                "check_starts": attempts,
                "wall_seconds": attempts * timeout,
                "artifact_bytes": attempts * (output_bytes + int(node["runner"].get("output_bytes", 0))),
            })
        elif node_type == "collect":
            node["producers"] = self.string_list(raw.get("producers", []), source, f"{pointer}/producers", minimum=1, maximum=100)
            envelope["artifact_bytes"] = output_bytes
        elif node_type == "bounded_run":
            score = self.string(raw.get("score"), source, f"{pointer}/score", pattern=_SAFE_ID_RE)
            expected = raw.get("expected_terminal")
            if expected not in SCORE_TERMINALS:
                self.diag(source, f"{pointer}/expected_terminal", "unsupported-terminal", f"unsupported score terminal {expected!r}", f"choose one of: {', '.join(SCORE_TERMINALS)}")
                expected = "awaiting-certification"
            capabilities = self.string_list(
                raw.get("capability_ceiling", []), source, f"{pointer}/capability_ceiling",
                choices=PROGRAM_CAPABILITIES, maximum=len(PROGRAM_CAPABILITIES),
                pattern=re.compile(r"^[a-z]+:[a-z-]+$"),
            )
            budgets_raw = raw.get("budgets")
            if not isinstance(budgets_raw, dict):
                self.diag(source, f"{pointer}/budgets", "wrong-type", "bounded_run budgets must be an object", "declare all finite child ceilings")
                budgets_raw = {}
            self.exact_keys(budgets_raw, _BOUNDED_RUN_BUDGET_KEYS, source, f"{pointer}/budgets")
            if set(budgets_raw) != _BOUNDED_RUN_BUDGET_KEYS:
                self.diag(source, f"{pointer}/budgets", "incomplete-budgets", "bounded_run must declare every child budget", "declare agent/check/wall/artifact ceilings")
            budgets = {
                "max_agent_starts": self.positive_int(budgets_raw.get("max_agent_starts"), source, f"{pointer}/budgets/max_agent_starts", 1, 10_000),
                "max_check_starts": self.positive_int(budgets_raw.get("max_check_starts"), source, f"{pointer}/budgets/max_check_starts", 1, 20_000),
                "max_wall_seconds": self.positive_int(budgets_raw.get("max_wall_seconds"), source, f"{pointer}/budgets/max_wall_seconds", 3_600, 31_536_000),
                "max_artifact_bytes": self.positive_int(budgets_raw.get("max_artifact_bytes"), source, f"{pointer}/budgets/max_artifact_bytes", 1_000_000, 10_000_000_000),
            }
            score_ref: dict[str, object] | None = None
            try:
                score_path = find_score_path(self.root, score)
                compiled_score = compile_score_path(score_path)
                score_ref = {
                    "path": str(score_path.relative_to(self.root)),
                    "semantic_hash": compiled_score["semantic_hash"],
                    "document_hash": compiled_score["document_hash"],
                }
            except DwError as exc:
                self.diag(source, f"{pointer}/score", "dangling-score-reference", exc.message, "add one valid Phase 24 score with the declared slug")
            node.update({
                "score": score,
                "expected_terminal": expected,
                "capability_ceiling": capabilities,
                "budgets": budgets,
                "score_reference": score_ref,
            })
            envelope.update({
                "child_runs": 1,
                "agent_starts": budgets["max_agent_starts"],
                "check_starts": budgets["max_check_starts"],
                "wall_seconds": budgets["max_wall_seconds"],
                "artifact_bytes": budgets["max_artifact_bytes"] + output_bytes,
            })
        elif node_type in {"subflow", "loop"}:
            node["workflow"] = self.string(raw.get("workflow"), source, f"{pointer}/workflow", pattern=_SAFE_ID_RE)
            node["version"] = self.string(raw.get("version"), source, f"{pointer}/version", pattern=_VERSION_RE)
            with_value = raw.get("with", {})
            if not isinstance(with_value, dict):
                self.diag(source, f"{pointer}/with", "wrong-type", "subflow bindings must be an object", "bind child parameters with typed expressions")
                with_value = {}
            node["with"] = dict(with_value)
            node["capability_ceiling"] = self.string_list(
                raw.get("capability_ceiling", []), source, f"{pointer}/capability_ceiling",
                choices=PROGRAM_CAPABILITIES, maximum=len(PROGRAM_CAPABILITIES),
                pattern=re.compile(r"^[a-z]+:[a-z-]+$"),
            )
            if node_type == "loop":
                purpose = raw.get("purpose")
                if purpose not in LOOP_PURPOSES:
                    self.diag(source, f"{pointer}/purpose", "unsupported-loop", f"unsupported loop purpose {purpose!r}", f"choose one of: {', '.join(LOOP_PURPOSES)}")
                    purpose = "repeat-until"
                if "max_rounds" not in raw:
                    self.diag(source, f"{pointer}/max_rounds", "missing-bound", "loop must declare max_rounds explicitly", "add a finite positive max_rounds")
                rounds = self.positive_int(raw.get("max_rounds"), source, f"{pointer}/max_rounds", 1, 100)
                carry = raw.get("carry", [])
                if (
                    not isinstance(carry, list) or len(carry) > 100
                    or any(not isinstance(item, str) or not _ARTIFACT_REF_RE.fullmatch(item) for item in carry)
                    or len(set(carry)) != len(carry)
                ):
                    self.diag(source, f"{pointer}/carry", "unsafe-artifact-reference", "carry must be a unique node.output list", "declare exact carried artifacts")
                    carry = []
                node.update({
                    "purpose": purpose,
                    "max_rounds": rounds,
                    "until": self.normalize_predicate(raw.get("until"), source, f"{pointer}/until"),
                    "carry": list(carry),
                    "on_success": self.normalize_route(raw.get("on_success"), source, f"{pointer}/on_success"),
                    "on_exhausted": self.normalize_route(raw.get("on_exhausted"), source, f"{pointer}/on_exhausted"),
                })
        elif node_type == "debate":
            participants = self.string_list(raw.get("participants"), source, f"{pointer}/participants", minimum=2, maximum=20)
            judge = self.string(raw.get("judge_role"), source, f"{pointer}/judge_role", pattern=_SAFE_ID_RE)
            if judge in participants:
                self.diag(source, f"{pointer}/judge_role", "separation-violation", "debate judge must be a separate role from speakers", "choose an independent judge role")
            if "max_rounds" not in raw:
                self.diag(source, f"{pointer}/max_rounds", "missing-bound", "debate must declare max_rounds explicitly", "add a finite positive max_rounds")
            rounds = self.positive_int(raw.get("max_rounds"), source, f"{pointer}/max_rounds", 1, 20)
            quorum = self.positive_int(raw.get("quorum"), source, f"{pointer}/quorum", len(participants), 20)
            if quorum > len(participants):
                self.diag(source, f"{pointer}/quorum", "impossible-quorum", "quorum exceeds participant slots", "lower quorum or add participants")
            tie_policy = raw.get("tie_policy")
            if tie_policy not in {"judge", "dissent", "checkpoint"}:
                self.diag(source, f"{pointer}/tie_policy", "unsupported-value", "tie_policy must be judge, dissent, or checkpoint", "choose a closed tie policy")
                tie_policy = "dissent"
            dissent_policy = raw.get("dissent_policy")
            if dissent_policy not in {"preserve", "veto"}:
                self.diag(source, f"{pointer}/dissent_policy", "unsupported-value", "dissent_policy must be preserve or veto", "choose a closed dissent policy")
                dissent_policy = "preserve"
            artifact_max = self.positive_int(raw.get("artifact_max_bytes"), source, f"{pointer}/artifact_max_bytes", 20_000, 1_000_000)
            round_timeout = self.positive_int(raw.get("round_timeout_seconds"), source, f"{pointer}/round_timeout_seconds", 1_800, 86_400)
            node.update({
                "participants": participants,
                "judge_role": judge,
                "max_rounds": rounds,
                "quorum": quorum,
                "artifact_max_bytes": artifact_max,
                "round_timeout_seconds": round_timeout,
                "tie_policy": tie_policy,
                "dissent_policy": dissent_policy,
                "on_consensus": self.normalize_route(raw.get("on_consensus"), source, f"{pointer}/on_consensus"),
                "on_dissent": self.normalize_route(raw.get("on_dissent"), source, f"{pointer}/on_dissent"),
                "on_exhausted": self.normalize_route(raw.get("on_exhausted"), source, f"{pointer}/on_exhausted"),
            })
            starts_per_round = len(participants) * 3 + 1
            envelope.update({
                "node_visits": rounds,
                "agent_starts": rounds * starts_per_round,
                "debate_rounds": rounds,
                "wall_seconds": rounds * round_timeout,
                "artifact_bytes": rounds * starts_per_round * artifact_max + output_bytes,
            })
        elif node_type == "verdict":
            node["role"] = self.string(raw.get("role"), source, f"{pointer}/role", pattern=_SAFE_ID_RE)
            node["rubric"] = self.string(raw.get("rubric"), source, f"{pointer}/rubric", pattern=_SAFE_ID_RE)
            node["subject"] = self.normalize_expression(raw.get("subject"), source, f"{pointer}/subject", parameter_types, allow_artifact=True)
            freshness = self.positive_int(raw.get("freshness_seconds"), source, f"{pointer}/freshness_seconds", 3_600, 31_536_000)
            rationale = self.positive_int(raw.get("max_rationale_bytes"), source, f"{pointer}/max_rationale_bytes", 20_000, 1_000_000)
            results = self.string_list(
                raw.get("results"), source, f"{pointer}/results",
                choices=VERDICT_RESULTS, minimum=1, maximum=len(VERDICT_RESULTS),
                pattern=_SAFE_ID_RE,
            )
            routes_raw = raw.get("routes")
            if not isinstance(routes_raw, dict):
                self.diag(source, f"{pointer}/routes", "wrong-type", "verdict routes must be an object", "route every allowed verdict result")
                routes_raw = {}
            for key in sorted(set(routes_raw) - set(results)):
                self.diag(source, f"{pointer}/routes/{key}", "unknown-result-route", f"route names undeclared result {key!r}", "route only declared results")
            routes = {
                result: self.normalize_route(routes_raw.get(result), source, f"{pointer}/routes/{result}")
                for result in results
            }
            node.update({
                "freshness_seconds": freshness,
                "max_rationale_bytes": rationale,
                "results": results,
                "routes": routes,
            })
            envelope.update({"agent_starts": 1, "wall_seconds": freshness, "artifact_bytes": rationale + output_bytes})
        elif node_type == "gate":
            facts = self.string_list(raw.get("facts", []), source, f"{pointer}/facts", maximum=100, pattern=re.compile(r"^[a-zA-Z0-9_.:-]+$"))
            verdicts = self.string_list(raw.get("verdicts", []), source, f"{pointer}/verdicts", maximum=100, pattern=re.compile(r"^[a-zA-Z0-9_.:-]+$"))
            if not facts and not verdicts:
                self.diag(source, pointer, "empty-gate", "gate must combine at least one fact or verdict", "declare governed inputs")
            operator = raw.get("operator")
            if operator not in {"all", "any"}:
                self.diag(source, f"{pointer}/operator", "unsupported-value", "gate operator must be all or any", "choose a closed operator")
                operator = "all"
            missing = raw.get("missing_policy")
            if missing not in {"fail", "block", "checkpoint"}:
                self.diag(source, f"{pointer}/missing_policy", "unsupported-value", "missing_policy must fail, block, or checkpoint", "choose a closed policy")
                missing = "block"
            dissent = raw.get("dissent_policy")
            if dissent not in {"preserve", "veto", "ignore"}:
                self.diag(source, f"{pointer}/dissent_policy", "unsupported-value", "dissent_policy must preserve, veto, or ignore", "choose a closed policy")
                dissent = "preserve"
            routes_raw = raw.get("routes")
            if not isinstance(routes_raw, dict):
                self.diag(source, f"{pointer}/routes", "wrong-type", "gate routes must be an object", "route pass/fail/missing/dissent")
                routes_raw = {}
            expected_routes = {"pass", "fail", "missing", "dissent"}
            if set(routes_raw) != expected_routes:
                self.diag(source, f"{pointer}/routes", "incomplete-routes", "gate must route pass, fail, missing, and dissent exactly", "declare all four routes")
            node.update({
                "facts": facts,
                "verdicts": verdicts,
                "operator": operator,
                "missing_policy": missing,
                "dissent_policy": dissent,
                "routes": {
                    result: self.normalize_route(routes_raw.get(result), source, f"{pointer}/routes/{result}")
                    for result in sorted(expected_routes)
                },
            })
            envelope["artifact_bytes"] = output_bytes
        elif node_type == "checkpoint":
            node["prompt_id"] = self.string(raw.get("prompt_id"), source, f"{pointer}/prompt_id", pattern=_SAFE_ID_RE)
            node["prompt"] = self.string(raw.get("prompt"), source, f"{pointer}/prompt", maximum=5_000)
            node["expires_seconds"] = self.positive_int(raw.get("expires_seconds"), source, f"{pointer}/expires_seconds", 86_400, 31_536_000)
            options_raw = raw.get("options")
            if not isinstance(options_raw, list) or not 2 <= len(options_raw) <= 20:
                self.diag(source, f"{pointer}/options", "invalid-options", "checkpoint requires 2 through 20 options", "declare a closed response set")
                options_raw = []
            options: list[dict[str, object]] = []
            option_ids: set[str] = set()
            for option_index, option in enumerate(options_raw):
                option_pointer = f"{pointer}/options/{option_index}"
                if not isinstance(option, dict):
                    self.diag(source, option_pointer, "wrong-type", "option must be an object", "provide id, label, and route")
                    continue
                self.exact_keys(option, _OPTION_KEYS, source, option_pointer)
                option_id = self.string(option.get("id"), source, f"{option_pointer}/id", pattern=_SAFE_ID_RE)
                if option_id in option_ids:
                    self.diag(source, f"{option_pointer}/id", "duplicate-id", f"duplicate option {option_id!r}", "use unique option ids")
                option_ids.add(option_id)
                options.append({
                    "id": option_id,
                    "label": self.string(option.get("label"), source, f"{option_pointer}/label", maximum=500),
                    "route": self.normalize_route(option.get("route"), source, f"{option_pointer}/route"),
                })
            node["options"] = options
            envelope["wall_seconds"] = int(node["expires_seconds"])
        elif node_type == "rail":
            action = raw.get("action")
            if action not in RAIL_CAPABILITIES:
                self.diag(source, f"{pointer}/action", "unsupported-rail", f"unsupported rail action {action!r}", "use an existing exact program rail")
                action = "evidence-materialize"
            capability = raw.get("capability")
            if capability != RAIL_CAPABILITIES[action]:
                self.diag(source, f"{pointer}/capability", "capability-mismatch", f"rail {action!r} requires {RAIL_CAPABILITIES[action]!r}", "declare the exact matching capability")
                capability = RAIL_CAPABILITIES[action]
            timeout = self.positive_int(raw.get("timeout_seconds"), source, f"{pointer}/timeout_seconds", 300, 86_400)
            node.update({"action": action, "capability": capability, "timeout_seconds": timeout})
            envelope.update({"rail_acts": 1, "wall_seconds": timeout, "artifact_bytes": output_bytes})
        node["envelope"] = envelope
        return node

    @staticmethod
    def node_routes(node: dict[str, object]) -> list[tuple[str, dict[str, str]]]:
        routes: list[tuple[str, dict[str, str]]] = []
        for key in ("on_success", "on_failure", "on_exhausted", "on_consensus", "on_dissent"):
            route = node.get(key)
            if isinstance(route, dict):
                routes.append((key.removeprefix("on_"), route))
        mapping = node.get("routes")
        if isinstance(mapping, dict):
            for outcome, route in sorted(mapping.items()):
                if isinstance(route, dict):
                    routes.append((str(outcome), route))
        options = node.get("options")
        if isinstance(options, list):
            for option in options:
                if isinstance(option, dict) and isinstance(option.get("route"), dict):
                    routes.append((f"option:{option.get('id')}", option["route"]))
        return routes

    def graph_checks(
        self,
        nodes: list[dict[str, object]],
        terminals: list[dict[str, str]],
        layout: dict[str, object],
        source: str,
    ) -> tuple[list[dict[str, object]], list[dict[str, object]], list[list[str]]]:
        ids: dict[str, int] = {}
        for index, node in enumerate(nodes):
            node_id = str(node.get("id") or "")
            if node_id in ids:
                self.diag(source, f"/nodes/{index}/id", "duplicate-id", f"duplicate node id {node_id!r}", "use unique stable node ids")
            elif node_id:
                ids[node_id] = index
        for layout_id in layout.get("nodes", {}):
            if layout_id not in ids:
                self.diag(source, f"/layout/nodes/{layout_id}", "dangling-layout", f"layout references missing node {layout_id!r}", "remove it or add the node")
        terminal_ids = {str(item["id"]) for item in terminals}
        dependents: dict[str, list[str]] = {node_id: [] for node_id in ids}
        indegree: dict[str, int] = {node_id: 0 for node_id in ids}
        for index, node in enumerate(nodes):
            node_id = str(node.get("id") or "")
            for offset, need in enumerate(node.get("needs", [])):
                if need not in ids:
                    self.diag(source, f"/nodes/{index}/needs/{offset}", "dangling-node-reference", f"dependency {need!r} does not exist", "reference a declared node")
                    continue
                if need == node_id:
                    self.diag(source, f"/nodes/{index}/needs/{offset}", "workflow-cycle", "node cannot depend on itself", "remove the cycle")
                    continue
                indegree[node_id] += 1
                dependents[str(need)].append(node_id)
        queue = [node_id for node_id in ids if indegree[node_id] == 0]
        visited: list[str] = []
        while queue:
            current = queue.pop(0)
            visited.append(current)
            for dependent in sorted(dependents[current], key=lambda item: ids[item]):
                indegree[dependent] -= 1
                if indegree[dependent] == 0:
                    queue.append(dependent)
        for node_id in ids:
            if node_id not in visited:
                self.diag(source, f"/nodes/{ids[node_id]}/needs", "workflow-cycle", f"node {node_id!r} participates in a dependency cycle", "remove the general graph cycle; use a typed loop node")

        route_edges: list[dict[str, object]] = []
        route_targets: set[str] = set()
        used_terminals: set[str] = set()
        for index, node in enumerate(nodes):
            node_id = str(node.get("id") or "")
            routes = self.node_routes(node)
            if node.get("activation") == "success" and not dependents.get(node_id) and not routes:
                self.diag(source, f"/nodes/{index}", "unhandled-terminal", "a success sink must route every outcome to a terminal, action, or route node", "declare explicit outcome routes")
            for outcome, route in routes:
                kind = route["kind"]
                target = route["target"]
                if kind == "node":
                    if target not in ids:
                        self.diag(source, f"/nodes/{index}", "dangling-route", f"route target {target!r} does not exist", "route to a declared route-activated node")
                    elif ids[target] <= index:
                        self.diag(source, f"/nodes/{index}", "workflow-cycle", f"route target {target!r} is not forward-only", "order route targets after their source; repetition belongs in loop/debate")
                    elif nodes[ids[target]].get("activation") != "route":
                        self.diag(source, f"/nodes/{ids[target]}/activation", "unsafe-route-target", "node route target must use activation=route", "mark it route-activated")
                    else:
                        route_targets.add(target)
                elif kind == "terminal":
                    if target not in terminal_ids:
                        self.diag(source, f"/nodes/{index}", "dangling-terminal", f"terminal {target!r} does not exist", "route to a declared terminal")
                    else:
                        used_terminals.add(target)
                route_edges.append({
                    "source": node_id,
                    "outcome": outcome,
                    "kind": kind,
                    "target": target,
                })
        for index, node in enumerate(nodes):
            if node.get("activation") == "route" and node.get("id") not in route_targets:
                self.diag(source, f"/nodes/{index}/activation", "unreachable-node", "route-activated node has no inbound outcome", "route a prior outcome here or remove it")
        for index, terminal in enumerate(terminals):
            if terminal["id"] not in used_terminals:
                self.diag(source, f"/terminals/{index}", "unreachable-terminal", f"terminal {terminal['id']!r} has no inbound route", "route a finite outcome to it or remove it")

        outputs = {
            f"{node['id']}.{output['id']}": (index, output)
            for index, node in enumerate(nodes)
            for output in node.get("outputs", [])
            if isinstance(output, dict)
        }
        ancestors: dict[str, set[str]] = {}

        def all_ancestors(node_id: str, seen: set[str] | None = None) -> set[str]:
            if node_id in ancestors:
                return ancestors[node_id]
            seen = set(seen or ())
            if node_id in seen or node_id not in ids:
                return set()
            seen.add(node_id)
            result: set[str] = set()
            for need in nodes[ids[node_id]].get("needs", []):
                if need in ids:
                    result.add(str(need))
                    result.update(all_ancestors(str(need), seen))
            ancestors[node_id] = result
            return result

        for index, node in enumerate(nodes):
            references: list[tuple[str, str]] = []
            for name, expression in node.get("inputs", {}).items():
                if isinstance(expression, dict) and expression.get("kind") == "artifact":
                    references.append((f"/nodes/{index}/inputs/{name}", str(expression.get("name"))))
            for pointer, reference in references:
                if reference not in outputs:
                    self.diag(source, pointer, "dangling-artifact-reference", f"artifact {reference!r} has no producer", "reference a declared node.output")
                    continue
                producer_id = reference.split(".", 1)[0]
                if node.get("activation") == "success" and producer_id not in all_ancestors(str(node.get("id"))):
                    self.diag(source, pointer, "artifact-before-producer", f"artifact producer {producer_id!r} is not a dependency", "add the producer to the dependency ancestry")
        waves: list[list[str]] = []
        completed: set[str] = set()
        remaining = [node for node in nodes if node.get("activation") == "success"]
        while remaining:
            eligible = [node for node in remaining if set(node.get("needs", [])) <= completed]
            if not eligible:
                break
            selected: list[dict[str, object]] = []
            locked: set[str] = set()
            for node in eligible:
                groups = {str(group) for group in node.get("resource_groups", [])}
                if groups & locked:
                    continue
                selected.append(node)
                locked.update(groups)
            if not selected:
                selected = [eligible[0]]
            wave = [str(node["id"]) for node in selected]
            waves.append(wave)
            for node in selected:
                completed.add(str(node["id"]))
                remaining.remove(node)
        success_edges = [
            {"source": str(need), "target": str(node["id"])}
            for node in nodes for need in node.get("needs", []) if need in ids
        ]
        return success_edges, route_edges, waves

    def _resolve_workflow(self, selector: str) -> tuple[Path, dict[str, object]] | None:
        try:
            path = find_workflow_path(self.root, selector)
            return path, load_workflow(path)
        except DwError:
            return None

    def _compile_instance(
        self,
        raw: object,
        source: str,
        *,
        bindings: object = None,
        parent_types: dict[str, str] | None = None,
        require_bound: bool = False,
        stack: tuple[str, ...] = (),
        address: str | None = None,
    ) -> dict[str, object]:
        if not isinstance(raw, dict):
            self.diag(source, "/", "wrong-type", "workflow must be an object", "provide a workflow object")
            raw = {}
        self.exact_keys(raw, _TOP_KEYS, source, "")
        if raw.get("kind") != WORKFLOW_KIND:
            self.diag(source, "/kind", "wrong-kind", f"expected {WORKFLOW_KIND!r}", f"set kind to {WORKFLOW_KIND}")
        if raw.get("schema_version") != WORKFLOW_SCHEMA_VERSION:
            self.diag(source, "/schema_version", "unsupported-schema", "only workflow schema version 1 is supported", "use schema_version 1")
        slug = self.string(raw.get("slug"), source, "/slug", pattern=_SAFE_ID_RE)
        title = self.string(raw.get("title"), source, "/title", maximum=500)
        version = self.string(raw.get("version"), source, "/version", pattern=_VERSION_RE)
        if slug in stack:
            cycle = " -> ".join(stack + (slug,))
            self.diag(source, "/slug", "workflow-recursive", f"recursive workflow reference: {cycle}", "remove the reference cycle")
        instance_address = address or slug
        parameters, defaults = self.normalize_parameters(raw.get("parameters"), raw.get("defaults"), source)
        parameter_types = {str(item["id"]): str(item["type"]) for item in parameters}
        bound_parameters = self.normalize_bindings(
            bindings, parameters, defaults, source, "/bindings",
            parent_types or {}, require_bound=require_bound,
        )
        layout = self.normalize_layout(raw.get("layout"), source)
        terminals = self.normalize_terminals(raw.get("terminals"), source)
        nodes_raw = raw.get("nodes")
        if not isinstance(nodes_raw, list) or not nodes_raw or len(nodes_raw) > 500:
            self.diag(source, "/nodes", "missing-nodes", "workflow requires 1 through 500 nodes", "declare a bounded non-empty graph")
            nodes_raw = []
        nodes = [
            self.normalize_node(item, index, source, parameter_types)
            for index, item in enumerate(nodes_raw)
        ]
        self.expanded_node_count += len(nodes)
        if self.expanded_node_count > 10_000:
            self.diag(source, "/nodes", "workflow-unbounded", "expanded hierarchy exceeds 10000 symbolic nodes", "split the workflow hierarchy")
        success_edges, route_edges, waves = self.graph_checks(nodes, terminals, layout, source)
        success_edges = [
            {
                "source": f"{instance_address}/{edge['source']}",
                "target": f"{instance_address}/{edge['target']}",
            }
            for edge in success_edges
        ]
        route_edges = [
            {
                **edge,
                "source": f"{instance_address}/{edge['source']}",
                "target": (
                    f"{instance_address}/{edge['target']}"
                    if edge["kind"] == "node"
                    else (
                        f"{instance_address}#terminal/{edge['target']}"
                        if edge["kind"] == "terminal"
                        else edge["target"]
                    )
                ),
            }
            for edge in route_edges
        ]

        children: list[dict[str, object]] = []
        loops: list[dict[str, object]] = []
        debates: list[dict[str, object]] = []
        source_hashes: dict[str, str] = {}
        expanded_nodes: list[dict[str, object]] = []
        expanded_artifacts: list[dict[str, object]] = []
        role_lanes: list[dict[str, str]] = []
        required_capabilities: dict[str, list[str]] = {}
        node_envelopes: dict[str, dict[str, int]] = {}
        total = _empty_envelope()
        for index, node in enumerate(nodes):
            node_id = str(node["id"])
            node_address = f"{instance_address}/{node_id}"
            node_type = str(node["type"])
            child: dict[str, object] | None = None
            if node_type in {"subflow", "loop"}:
                selector = str(node.get("workflow") or "")
                resolved = self._resolve_workflow(selector)
                if resolved is None:
                    self.diag(source, f"/nodes/{index}/workflow", "dangling-workflow-reference", f"cannot resolve workflow {selector!r}", "add one unambiguous pm/workflows policy")
                elif selector in stack + (slug,):
                    cycle = " -> ".join(stack + (slug, selector))
                    self.diag(source, f"/nodes/{index}/workflow", "workflow-recursive", f"recursive workflow reference: {cycle}", "remove the subflow cycle")
                elif len(stack) >= 31:
                    self.diag(source, f"/nodes/{index}/workflow", "workflow-unbounded", "subflow nesting exceeds 32 levels", "flatten or split the hierarchy")
                elif self.expanded_node_count > 10_000:
                    self.diag(source, f"/nodes/{index}/workflow", "workflow-unbounded", "subflow expansion ceiling is exhausted", "split the hierarchy")
                else:
                    child_path, child_raw = resolved
                    child_source = str(child_path.relative_to(self.root))
                    child = self._compile_instance(
                        child_raw,
                        child_source,
                        bindings=node.get("with", {}),
                        parent_types=parameter_types,
                        require_bound=True,
                        stack=stack + (slug,),
                        address=(
                            f"{node_address}/round/{{round}}/{selector}"
                            if node_type == "loop"
                            else f"{node_address}/{selector}"
                        ),
                    )
                    node["with"] = child.get("bindings", {})
                    if child.get("version") != node.get("version"):
                        self.diag(source, f"/nodes/{index}/version", "workflow-version-mismatch", f"reference requires {node.get('version')!r}, resolved {child.get('version')!r}", "pin the exact resolved workflow version")
                    source_hashes.update(child.get("source_hashes", {}))
                    child_capabilities = {
                        capability
                        for values in child.get("required_capabilities", {}).values()
                        for capability in values
                    }
                    missing_capabilities = sorted(
                        child_capabilities - set(node.get("capability_ceiling", []))
                    )
                    if missing_capabilities:
                        self.diag(
                            source,
                            f"/nodes/{index}/capability_ceiling",
                            "capability-smuggling",
                            "child workflow requires capabilities outside its ceiling: "
                            + ", ".join(missing_capabilities),
                            "add the explicit capabilities or narrow the child workflow",
                        )
                    if node_type == "loop":
                        child_nodes = child["workflow"]["nodes"]
                        child_outputs = {
                            f"{child_node['id']}.{output['id']}"
                            for child_node in child_nodes
                            for output in child_node.get("outputs", [])
                        }
                        child_types = {
                            str(child_node["id"]): str(child_node["type"])
                            for child_node in child_nodes
                        }
                        predicate = node["until"]
                        predicate_source = str(predicate["source"])
                        predicate_kind = str(predicate["kind"])
                        predicate_valid = (
                            predicate_source in child_outputs
                            if predicate_kind == "artifact-valid"
                            else child_types.get(predicate_source) == {
                                "check-result": "check",
                                "verdict-result": "verdict",
                                "decision-result": "checkpoint",
                            }.get(predicate_kind)
                        )
                        if predicate_kind == "decision-result" and child_types.get(predicate_source) == "debate":
                            predicate_valid = True
                        if not predicate_valid:
                            self.diag(
                                source,
                                f"/nodes/{index}/until/source",
                                "non-decreasing-loop",
                                f"predicate source {predicate_source!r} is not a typed result of child {selector!r}",
                                "bind convergence to one declared child check, verdict, decision, or artifact",
                            )
                        for offset, carry in enumerate(node.get("carry", [])):
                            if carry not in child_outputs:
                                self.diag(
                                    source,
                                    f"/nodes/{index}/carry/{offset}",
                                    "dangling-artifact-reference",
                                    f"carried artifact {carry!r} is not produced by child {selector!r}",
                                    "carry one exact child node.output artifact",
                                )
                    children.append({
                        "node": node_id,
                        "type": node_type,
                        "address": node_address,
                        "slug": child.get("slug"),
                        "version": child.get("version"),
                        "semantic_hash": child.get("semantic_hash"),
                        "bundle_hash": child.get("bundle_hash"),
                        "bindings": child.get("bindings"),
                        "envelope": child.get("envelope"),
                    })
                    children.extend(child.get("children", []))
                    child_envelope = dict(child.get("envelope", _empty_envelope()))
                    if node_type == "loop":
                        rounds = int(node["max_rounds"])
                        envelope = _scale_envelope(child_envelope, rounds)
                        envelope["loop_rounds"] += rounds
                        envelope["node_visits"] += rounds
                        envelope["artifact_bytes"] += sum(int(item["max_bytes"]) for item in node.get("outputs", []))
                        node["envelope"] = envelope
                        loops.append({
                            "address": node_address,
                            "purpose": node["purpose"],
                            "max_rounds": rounds,
                            "iterations": [
                                {"round": round_number, "address": f"{node_address}/round/{round_number}/{selector}"}
                                for round_number in range(1, rounds + 1)
                            ],
                            "until": node["until"],
                            "success_route": node["on_success"],
                            "exhaustion_route": node["on_exhausted"],
                            "envelope": envelope,
                        })
                    else:
                        envelope = _add_envelopes(child_envelope, dict(node["envelope"]))
                        node["envelope"] = envelope
                    expanded_nodes.extend(child.get("expanded_nodes", []))
                    expanded_artifacts.extend(child.get("expanded_artifacts", []))
                    role_lanes.extend(child.get("role_lanes", []))
                    loops.extend(child.get("loops", []))
                    debates.extend(child.get("debates", []))
                    route_edges.extend(child.get("routes", []))
            if node_type == "debate":
                debates.append({
                    "address": node_address,
                    "participants": node["participants"],
                    "judge_role": node["judge_role"],
                    "max_rounds": node["max_rounds"],
                    "rounds": [
                        {
                            "round": round_number,
                            "stages": ["proposal", "critique", "rebuttal", "judgment"],
                            "address": f"{node_address}/round/{round_number}",
                        }
                        for round_number in range(1, int(node["max_rounds"]) + 1)
                    ],
                    "routes": {outcome: route for outcome, route in self.node_routes(node)},
                    "envelope": node["envelope"],
                })
            envelope = dict(node["envelope"])
            node_envelopes[node_address] = envelope
            total = _add_envelopes(total, envelope)
            capabilities: set[str] = set()
            if node_type == "agent":
                capabilities.update(node.get("capability_ceiling", []))
            elif node_type == "check":
                capabilities.add("check:execute")
            elif node_type == "debate":
                capabilities.add("agent:dispatch")
            elif node_type == "verdict":
                capabilities.update({"agent:dispatch", "certification:verdict"})
            elif node_type == "bounded_run":
                capabilities.update(node.get("capability_ceiling", []))
            elif node_type == "subflow":
                if child is not None:
                    capabilities.update(
                        capability
                        for values in child.get("required_capabilities", {}).values()
                        for capability in values
                    )
                else:
                    capabilities.update(node.get("capability_ceiling", []))
            elif node_type == "loop":
                if child is not None:
                    capabilities.update(
                        capability
                        for values in child.get("required_capabilities", {}).values()
                        for capability in values
                    )
            elif node_type == "rail":
                capabilities.add(str(node["capability"]))
            if capabilities:
                required_capabilities[node_address] = sorted(capabilities)
            for output in node.get("outputs", []):
                expanded_artifacts.append({
                    "address": f"{node_address}/artifact/{output['id']}",
                    "producer": node_address,
                    "workflow": slug,
                    "node": node_id,
                    "id": output["id"],
                    "kind": output["kind"],
                    "max_bytes": output["max_bytes"],
                    "lineage": list(stack) + [slug],
                })
            if node_type in {"agent", "verdict"}:
                role_lanes.append({
                    "address": f"{node_address}/role/{node['role']}",
                    "node": node_address,
                    "role": str(node["role"]),
                    "duty": node_type,
                })
            elif node_type == "debate":
                role_lanes.extend([
                    {
                        "address": f"{node_address}/role/{role}",
                        "node": node_address,
                        "role": str(role),
                        "duty": "debate-speaker",
                    }
                    for role in node["participants"]
                ])
                role_lanes.append({
                    "address": f"{node_address}/role/{node['judge_role']}",
                    "node": node_address,
                    "role": str(node["judge_role"]),
                    "duty": "debate-judge",
                })
            expanded_nodes.insert(len(expanded_nodes) - len(child.get("expanded_nodes", [])) if child else len(expanded_nodes), {
                "address": node_address,
                "workflow": slug,
                "version": version,
                "node": node_id,
                "type": node_type,
                "activation": node["activation"],
                "needs": [f"{instance_address}/{need}" for need in node.get("needs", [])],
                "envelope": envelope,
                "lineage": list(stack) + [slug],
            })

        runtime: dict[str, object] = {
            "kind": WORKFLOW_KIND,
            "schema_version": WORKFLOW_SCHEMA_VERSION,
            "slug": slug,
            "title": title,
            "version": version,
            "parameters": parameters,
            "defaults": defaults,
            "nodes": [
                {key: value for key, value in node.items() if key != "envelope"}
                for node in nodes
            ],
            "terminals": terminals,
        }
        description = self.optional_string(raw.get("description"), source, "/description")
        if description is not None:
            runtime["description"] = description
        normalized = {**runtime, "layout": layout}
        semantic_hash = _hash(runtime)
        document_hash = _hash(normalized)
        source_key = f"{slug}@{version}"
        existing = self.sources.get(source_key)
        if existing and existing.get("semantic_hash") != semantic_hash:
            self.diag(source, "/slug", "ambiguous-workflow-reference", f"multiple semantics resolve as {source_key}", "use one unique slug/version source")
        self.sources[source_key] = {
            "slug": slug,
            "version": version,
            "path": source,
            "semantic_hash": semantic_hash,
            "document_hash": document_hash,
        }
        source_hashes[source_key] = semantic_hash
        for route in route_edges:
            if "envelope" not in route:
                route["envelope"] = node_envelopes.get(
                    str(route.get("source")), _empty_envelope()
                )
        bundle_hash = _hash({
            "root": semantic_hash,
            "bindings": bound_parameters,
            "sources": dict(sorted(source_hashes.items())),
        })
        for key, limit in ENVELOPE_LIMITS.items():
            if total[key] > limit:
                self.diag(source, "/nodes", "workflow-unbounded", f"finite envelope {key}={total[key]} exceeds compiler ceiling {limit}", "split the workflow or lower nested bounds")
        return {
            "slug": slug,
            "version": version,
            "source": source,
            "semantic_hash": semantic_hash,
            "document_hash": document_hash,
            "bundle_hash": bundle_hash,
            "workflow": runtime,
            "layout": layout,
            "bindings": bound_parameters,
            "source_hashes": dict(sorted(source_hashes.items())),
            "children": children,
            "success_edges": success_edges,
            "routes": route_edges,
            "waves": waves,
            "expanded_nodes": expanded_nodes,
            "expanded_artifacts": expanded_artifacts,
            "role_lanes": role_lanes,
            "loops": loops,
            "debates": debates,
            "node_envelopes": node_envelopes,
            "envelope": total,
            "required_capabilities": required_capabilities,
            "terminals": terminals,
        }

    def build(
        self,
        workflow: str | Path | dict[str, object],
        *,
        bindings: object = None,
        require_bound: bool = False,
        source: str = "workflow",
    ) -> dict[str, object]:
        if isinstance(workflow, str):
            path = find_workflow_path(self.root, workflow)
            raw = load_workflow(path)
            source = str(path.relative_to(self.root))
        elif isinstance(workflow, Path):
            path = workflow.resolve()
            allowed = workflow_dir(self.root)
            if path.parent != allowed:
                raise DwError("workflow path must be a direct contained pm/workflows JSON file")
            raw = load_workflow(path)
            source = str(path.relative_to(self.root))
        else:
            raw = workflow
        compiled = self._compile_instance(
            raw,
            source,
            bindings=bindings,
            parent_types={},
            require_bound=require_bound,
        )
        self.diagnostics.sort(
            key=lambda item: (
                item["source"], item["pointer"], item["code"], item["message"],
            )
        )
        compiled["sources"] = {
            key: self.sources[key] for key in sorted(self.sources)
        }
        return compiled


def validate_workflow(
    root: Path,
    workflow: str | Path | dict[str, object],
    *,
    bindings: object = None,
    require_bound: bool = False,
    source: str = "workflow",
) -> dict[str, object]:
    compiler = _RegistryCompiler(root)
    try:
        compiled = compiler.build(
            workflow,
            bindings=bindings,
            require_bound=require_bound,
            source=source,
        )
    except DwError as exc:
        compiler.diag(source, "/", "workflow-not-found", exc.message, "choose one contained workflow policy")
        compiled = None
    compiler.diagnostics.sort(
        key=lambda item: (
            item["source"], item["pointer"], item["code"], item["message"],
        )
    )
    return {
        "kind": VALIDATION_KIND,
        "schema_version": WORKFLOW_SCHEMA_VERSION,
        "valid": not compiler.diagnostics,
        "diagnostics": compiler.diagnostics,
        "compiled": compiled if not compiler.diagnostics else None,
        "starts_work": False,
        "writes_state": False,
    }


def compile_workflow(
    root: Path,
    workflow: str | Path | dict[str, object],
    *,
    bindings: object = None,
    require_bound: bool = False,
    source: str = "workflow",
) -> dict[str, object]:
    compiler = _RegistryCompiler(root)
    compiled = compiler.build(
        workflow,
        bindings=bindings,
        require_bound=require_bound,
        source=source,
    )
    if compiler.diagnostics:
        raise WorkflowValidationError(compiler.diagnostics)
    return {
        "kind": COMPILED_WORKFLOW_KIND,
        "schema_version": WORKFLOW_SCHEMA_VERSION,
        **compiled,
    }


def compile_workflow_path(
    root: Path,
    path: Path,
    *,
    bindings: object = None,
    require_bound: bool = False,
) -> dict[str, object]:
    return compile_workflow(
        root, path, bindings=bindings, require_bound=require_bound,
    )


def simulate_workflow(
    root: Path,
    workflow: str | Path | dict[str, object],
    *,
    bindings: object = None,
    require_bound: bool = False,
) -> dict[str, object]:
    compiled = compile_workflow(
        root,
        workflow,
        bindings=bindings,
        require_bound=require_bound,
    )
    return {
        "kind": SIMULATION_KIND,
        "schema_version": WORKFLOW_SCHEMA_VERSION,
        "workflow": {
            "slug": compiled["slug"],
            "version": compiled["version"],
            "semantic_hash": compiled["semantic_hash"],
            "bundle_hash": compiled["bundle_hash"],
        },
        "bindings": compiled["bindings"],
        "sources": compiled["sources"],
        "children": compiled["children"],
        "expanded_nodes": compiled["expanded_nodes"],
        "expanded_artifacts": compiled["expanded_artifacts"],
        "role_lanes": compiled["role_lanes"],
        "waves": compiled["waves"],
        "success_edges": compiled["success_edges"],
        "routes": compiled["routes"],
        "loops": compiled["loops"],
        "debates": compiled["debates"],
        "terminals": compiled["terminals"],
        "envelopes": {
            "by_node": compiled["node_envelopes"],
            "worst_case": compiled["envelope"],
        },
        "required_capabilities": compiled["required_capabilities"],
        "starts_work": False,
        "writes_policy": False,
        "writes_run_state": False,
        "creates_grant": False,
    }


def workflow_inventory(root: Path) -> dict[str, object]:
    root = root.resolve()
    workflows: list[dict[str, object]] = []
    for path in discover_workflow_paths(root):
        validation = validate_workflow(root, path)
        item: dict[str, object] = {
            "name": path.stem,
            "path": str(path.relative_to(root)),
            "valid": validation["valid"],
            "diagnostics": validation["diagnostics"],
        }
        compiled = validation.get("compiled")
        if isinstance(compiled, dict):
            item.update({
                "slug": compiled["slug"],
                "title": compiled["workflow"]["title"],
                "version": compiled["version"],
                "semantic_hash": compiled["semantic_hash"],
                "bundle_hash": compiled["bundle_hash"],
                "envelope": compiled["envelope"],
            })
        else:
            try:
                raw = load_workflow(path)
            except DwError:
                raw = {}
            item.update({
                "slug": raw.get("slug"),
                "title": raw.get("title"),
                "version": raw.get("version"),
            })
        workflows.append(item)
    return {
        "kind": INVENTORY_KIND,
        "schema_version": WORKFLOW_SCHEMA_VERSION,
        "workflows": workflows,
        "healthy": all(bool(item["valid"]) for item in workflows),
        "starts_work": False,
        "writes_state": False,
    }
