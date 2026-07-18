"""Pure orchestration-score compilation and scheduling simulation.

The score is tracked configuration, never execution authority.  This module
therefore has no subprocess, network, Git-mutation, run-ledger, or agent
imports: it parses exact schema-v1 JSON, normalizes defaults, validates every
runtime-bearing field, produces stable hashes, and explains the graph that a
later grant may authorize.
"""

from __future__ import annotations

import hashlib
import json
import math
import re
from pathlib import Path
from typing import Any

from .model import DwError


SCORE_KIND = "delivery-workbench-orchestration"
SCORE_SCHEMA_VERSION = 1
COMPILED_SCORE_KIND = "delivery-workbench-compiled-orchestration"
COMPILED_SCORE_SCHEMA_VERSION = 1
VALIDATION_KIND = "delivery-workbench-orchestration-validation"
SIMULATION_KIND = "delivery-workbench-orchestration-simulation"

ROLE_PRESETS = (
    "research",
    "synthesis",
    "implementation",
    "review",
    "verification",
    "documentation",
    "repair",
)
NODE_TYPES = ("agent", "check", "rail", "approval", "collect")
CAPABILITIES = (
    "repository-read",
    "repository-write",
    "network",
    "tools-read",
    "tools-write",
)
WORKSPACE_MODES = ("none", "read-only", "isolated-worktree")
OUTPUT_FORMATS = ("markdown", "json", "text", "git-diff", "directory")
TERMINALS = ("complete", "blocked", "cancelled", "awaiting-certification")
FAILURE_ACTIONS = ("retry", "route", "approval", "pause", "abort")
BUILTIN_CHECKS = ("file-exists", "json-schema", "diff-scope", "rail-status")

DEFAULTS = {
    "max_concurrency": 1,
    "max_wall_seconds": 3600,
    "max_agent_starts": 32,
    "max_check_starts": 64,
    "default_timeout_seconds": 900,
    "max_artifact_bytes": 1_000_000,
}
DEFAULT_LIMITS = {
    "max_concurrency": 64,
    "max_wall_seconds": 86_400,
    "max_agent_starts": 1_000,
    "max_check_starts": 2_000,
    "default_timeout_seconds": 86_400,
    "max_artifact_bytes": 10_000_000,
}

_SELECTOR_RE = re.compile(r"^[a-z][a-z0-9]*(?:-[a-z0-9]+)*$")
_ROLE_RE = re.compile(r"^[a-z][a-z0-9]*(?:[-_][a-z0-9]+)*$")
_RESOURCE_RE = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9_.:-]{0,127}$")

_TOP_KEYS = {
    "kind", "schema_version", "slug", "title", "description", "project",
    "defaults", "nodes", "layout",
}
_DEFAULT_KEYS = set(DEFAULTS)
_COMMON_NODE_KEYS = {
    "id", "type", "title", "description", "activation", "needs",
    "resource_groups", "timeout_seconds", "on_failure",
}
_NODE_KEYS = {
    "agent": _COMMON_NODE_KEYS | {
        "role", "profile", "prompt", "context", "capabilities", "workspace",
        "inputs", "outputs",
    },
    "check": _COMMON_NODE_KEYS | {"runner", "expect"},
    "rail": _COMMON_NODE_KEYS | {"action"},
    "approval": _COMMON_NODE_KEYS | {"prompt", "options", "terminal"},
    "collect": _COMMON_NODE_KEYS | {"inputs", "outputs"},
}
_OUTPUT_KEYS = {
    "name", "format", "path", "schema", "required_sections", "citations",
    "max_bytes", "allowed_paths",
}
_ARTIFACT_INPUT_KEYS = {"artifact", "format"}
_FAILURE_KEYS = {"action", "max_attempts", "node", "checkpoint", "max_visits"}
_COMMAND_RUNNER_KEYS = {"kind", "argv", "cwd", "timeout_seconds", "output_bytes", "writes"}
_BUILTIN_RUNNER_KEYS = {"kind", "name", "path", "schema", "allowed_paths", "timeout_seconds", "output_bytes"}
_EXPECT_KEYS = {"exit_code"}
_LAYOUT_KEYS = {"nodes", "viewport"}
_NODE_LAYOUT_KEYS = {"x", "y"}
_VIEWPORT_KEYS = {"x", "y", "zoom"}


class OrchestrationValidationError(DwError):
    """A score refusal carrying the complete deterministic diagnostic set."""

    def __init__(self, diagnostics: list[dict[str, str]]) -> None:
        self.diagnostics = diagnostics
        first = diagnostics[0] if diagnostics else {
            "pointer": "/", "message": "score is invalid"
        }
        super().__init__(
            f"orchestration score invalid at {first['pointer']}: {first['message']}"
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


def canonical_json(value: object) -> str:
    """The byte representation used by every orchestration hash/adapter."""
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    )


def _hash(value: object) -> str:
    return "sha256:" + hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def parse_score_text(text: str, source: str = "score") -> dict[str, object]:
    """Parse JSON while refusing duplicate object keys and non-object roots."""
    try:
        value = json.loads(
            text,
            object_pairs_hook=_object_without_duplicates,
            parse_constant=lambda token: (_ for _ in ()).throw(
                ValueError(f"non-finite JSON number: {token}")
            ),
        )
    except (_DuplicateJSONKey, json.JSONDecodeError, ValueError) as exc:
        raise DwError(f"cannot parse orchestration score {source}: {exc}") from exc
    if not isinstance(value, dict):
        raise DwError(f"orchestration score {source} must be a JSON object")
    return value


def load_score(path: Path) -> dict[str, object]:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise DwError(f"cannot read orchestration score {path}: {exc}") from exc
    return parse_score_text(text, str(path))


def orchestration_dir(root: Path) -> Path:
    return root.resolve() / "pm" / "orchestration"


def discover_score_paths(root: Path) -> list[Path]:
    """Discover only direct, contained JSON scores; escaped symlinks refuse."""
    allowed = orchestration_dir(root).resolve()
    resolved_root = root.resolve()
    if allowed != resolved_root and resolved_root not in allowed.parents:
        raise DwError("pm/orchestration resolves outside the repository")
    if not allowed.is_dir():
        return []
    paths: list[Path] = []
    for candidate in sorted(allowed.glob("*.json"), key=lambda p: p.name):
        resolved = candidate.resolve()
        if resolved.parent != allowed:
            raise DwError(f"orchestration score escapes pm/orchestration: {candidate.name}")
        if resolved.is_file():
            paths.append(resolved)
    return paths


def find_score_path(root: Path, selector: str) -> Path:
    if not _SELECTOR_RE.fullmatch(selector or ""):
        raise DwError(f"unsafe orchestration score selector: {selector!r}")
    paths = discover_score_paths(root)
    filename_matches = [path for path in paths if path.stem == selector]
    slug_matches: list[Path] = []
    for path in paths:
        try:
            raw = load_score(path)
        except DwError:
            continue
        if raw.get("slug") == selector:
            slug_matches.append(path)
    matches = []
    for path in filename_matches + slug_matches:
        if path not in matches:
            matches.append(path)
    if not matches:
        raise DwError(f"orchestration score not found: {selector}")
    if len(matches) > 1:
        raise DwError(f"ambiguous orchestration score selector: {selector}")
    return matches[0]


class _Compiler:
    def __init__(self, raw: object) -> None:
        self.raw = raw
        self.diagnostics: list[dict[str, str]] = []
        self.node_indexes: dict[str, int] = {}
        self.output_producers: dict[str, tuple[int, dict[str, object]]] = {}

    def diag(self, pointer: str, code: str, message: str, remediation: str) -> None:
        self.diagnostics.append({
            "pointer": pointer,
            "code": code,
            "message": message,
            "remediation": remediation,
        })

    def exact_keys(self, value: dict[str, object], allowed: set[str], pointer: str) -> None:
        for key in sorted(set(value) - allowed):
            self.diag(
                f"{pointer}/{key}",
                "unknown-key",
                f"{key!r} is not part of schema v1",
                "remove the field or move editor-only coordinates under /layout",
            )

    def required_string(
        self,
        value: object,
        pointer: str,
        *,
        pattern: re.Pattern[str] | None = None,
        max_length: int = 512,
    ) -> str:
        if not isinstance(value, str) or not value.strip():
            self.diag(pointer, "required-string", "a non-empty string is required", "provide a non-empty string")
            return ""
        result = value.strip()
        if len(result) > max_length:
            self.diag(pointer, "string-too-long", f"string exceeds {max_length} characters", "shorten the value")
        if pattern is not None and not pattern.fullmatch(result):
            self.diag(pointer, "unsafe-selector", f"{result!r} is not a safe selector", "use lowercase letters, digits, and internal hyphens")
        return result

    def optional_string(self, value: object, pointer: str, max_length: int = 20_000) -> str | None:
        if value is None:
            return None
        if not isinstance(value, str):
            self.diag(pointer, "wrong-type", "expected a string", "use a JSON string or remove the field")
            return None
        if len(value) > max_length:
            self.diag(pointer, "string-too-long", f"string exceeds {max_length} characters", "shorten the value")
        return value

    def positive_int(self, value: object, pointer: str, default: int, maximum: int) -> int:
        if value is None:
            return default
        if isinstance(value, bool) or not isinstance(value, int):
            self.diag(pointer, "wrong-type", "expected a positive integer", f"use an integer from 1 through {maximum}")
            return default
        if value < 1 or value > maximum:
            self.diag(pointer, "unbounded-value", f"value must be from 1 through {maximum}", "choose an explicit finite value inside the supported bound")
            return default
        return value

    def string_list(
        self,
        value: object,
        pointer: str,
        *,
        default: list[str] | None = None,
        choices: tuple[str, ...] | None = None,
        resource: bool = False,
        unique: bool = True,
    ) -> list[str]:
        if value is None:
            return list(default or [])
        if not isinstance(value, list):
            self.diag(pointer, "wrong-type", "expected an array of strings", "use a JSON string array")
            return list(default or [])
        result: list[str] = []
        for offset, item in enumerate(value):
            item_pointer = f"{pointer}/{offset}"
            if not isinstance(item, str) or not item:
                self.diag(item_pointer, "wrong-type", "expected a non-empty string", "use a non-empty JSON string")
                continue
            if choices is not None and item not in choices:
                self.diag(item_pointer, "unsupported-value", f"unsupported value {item!r}", f"choose one of: {', '.join(choices)}")
            if resource and not _RESOURCE_RE.fullmatch(item):
                self.diag(item_pointer, "unsafe-selector", f"unsafe resource selector {item!r}", "use letters, digits, dot, colon, underscore, or hyphen")
            if unique and item in result:
                self.diag(item_pointer, "duplicate-value", f"duplicate value {item!r}", "list each value once")
                continue
            result.append(item)
        return result

    def safe_path(self, value: object, pointer: str, *, glob: bool, workspace: bool = False) -> str:
        if not isinstance(value, str) or not value:
            self.diag(pointer, "required-path", "a non-empty relative path is required", "use a contained repository-relative path")
            return ""
        if workspace and value == "workspace":
            return value
        unsafe = (
            len(value) > 512
            or value.startswith(("/", "~"))
            or "\\" in value
            or "\0" in value
            or any(part in {"", ".", ".."} for part in value.split("/"))
            or value.split("/")[0] == ".git"
            or (not glob and any(mark in value for mark in "*?[]"))
        )
        if unsafe:
            self.diag(pointer, "unsafe-path", f"path {value!r} is not contained and selector-safe", "use a relative path without dot segments, backslashes, .git, or disallowed glob syntax")
        return value

    def normalize_layout(self, value: object) -> dict[str, object]:
        if value is None:
            return {"nodes": {}, "viewport": {"x": 0, "y": 0, "zoom": 1}}
        if not isinstance(value, dict):
            self.diag("/layout", "wrong-type", "layout must be an object", "use nodes and viewport objects")
            return {"nodes": {}, "viewport": {"x": 0, "y": 0, "zoom": 1}}
        self.exact_keys(value, _LAYOUT_KEYS, "/layout")
        nodes_raw = value.get("nodes", {})
        nodes: dict[str, object] = {}
        if not isinstance(nodes_raw, dict):
            self.diag("/layout/nodes", "wrong-type", "layout nodes must be an object keyed by node id", "map node ids to x/y objects")
        else:
            for node_id in sorted(nodes_raw):
                position = nodes_raw[node_id]
                pointer = f"/layout/nodes/{node_id}"
                if not isinstance(position, dict):
                    self.diag(pointer, "wrong-type", "node position must be an object", "provide numeric x and y")
                    continue
                self.exact_keys(position, _NODE_LAYOUT_KEYS, pointer)
                x = position.get("x", 0)
                y = position.get("y", 0)
                if isinstance(x, bool) or not isinstance(x, (int, float)) or not math.isfinite(x):
                    self.diag(f"{pointer}/x", "wrong-type", "x must be numeric", "provide a finite number")
                    x = 0
                if isinstance(y, bool) or not isinstance(y, (int, float)) or not math.isfinite(y):
                    self.diag(f"{pointer}/y", "wrong-type", "y must be numeric", "provide a finite number")
                    y = 0
                nodes[str(node_id)] = {"x": x, "y": y}
        viewport_raw = value.get("viewport", {})
        viewport: dict[str, object] = {"x": 0, "y": 0, "zoom": 1}
        if not isinstance(viewport_raw, dict):
            self.diag("/layout/viewport", "wrong-type", "viewport must be an object", "provide numeric x, y, and zoom")
        else:
            self.exact_keys(viewport_raw, _VIEWPORT_KEYS, "/layout/viewport")
            for key, default in (("x", 0), ("y", 0), ("zoom", 1)):
                raw = viewport_raw.get(key, default)
                if isinstance(raw, bool) or not isinstance(raw, (int, float)) or not math.isfinite(raw):
                    self.diag(f"/layout/viewport/{key}", "wrong-type", f"{key} must be numeric", "provide a finite number")
                    raw = default
                if key == "zoom" and raw <= 0:
                    self.diag("/layout/viewport/zoom", "unbounded-value", "zoom must be greater than zero", "provide a positive zoom")
                    raw = 1
                viewport[key] = raw
        return {"nodes": nodes, "viewport": viewport}

    def normalize_output(self, raw: object, pointer: str, default_bytes: int) -> dict[str, object]:
        if not isinstance(raw, dict):
            self.diag(pointer, "wrong-type", "output must be an object", "provide name, format, and path")
            raw = {}
        self.exact_keys(raw, _OUTPUT_KEYS, pointer)
        name = self.required_string(raw.get("name"), f"{pointer}/name", pattern=_SELECTOR_RE)
        fmt = self.required_string(raw.get("format"), f"{pointer}/format")
        if fmt and fmt not in OUTPUT_FORMATS:
            self.diag(f"{pointer}/format", "unsupported-value", f"unsupported output format {fmt!r}", f"choose one of: {', '.join(OUTPUT_FORMATS)}")
        path = self.safe_path(raw.get("path"), f"{pointer}/path", glob=False, workspace=fmt == "git-diff")
        schema = self.optional_string(raw.get("schema"), f"{pointer}/schema", max_length=512)
        if schema is not None:
            schema = self.safe_path(schema, f"{pointer}/schema", glob=False)
        sections = self.string_list(raw.get("required_sections"), f"{pointer}/required_sections")
        citations = raw.get("citations", "none")
        if citations not in ("none", "optional", "required"):
            self.diag(f"{pointer}/citations", "unsupported-value", f"unsupported citations policy {citations!r}", "choose none, optional, or required")
            citations = "none"
        max_bytes = self.positive_int(raw.get("max_bytes"), f"{pointer}/max_bytes", default_bytes, DEFAULT_LIMITS["max_artifact_bytes"])
        allowed_paths_raw = raw.get("allowed_paths")
        allowed_paths = self.string_list(allowed_paths_raw, f"{pointer}/allowed_paths")
        for offset, selector in enumerate(allowed_paths):
            self.safe_path(selector, f"{pointer}/allowed_paths/{offset}", glob=True)
        if fmt == "json" and sections:
            self.diag(f"{pointer}/required_sections", "incompatible-convention", "JSON outputs cannot require Markdown sections", "use a schema for JSON or change the format to markdown")
        if fmt == "git-diff" and not allowed_paths:
            self.diag(f"{pointer}/allowed_paths", "missing-bound", "git-diff outputs require an allowed path set", "declare at least one contained path selector")
        result: dict[str, object] = {
            "name": name,
            "format": fmt,
            "path": path,
            "required_sections": sections,
            "citations": citations,
            "max_bytes": max_bytes,
            "allowed_paths": allowed_paths,
        }
        if schema is not None:
            result["schema"] = schema
        return result

    def normalize_inputs(self, value: object, pointer: str) -> list[object]:
        if value is None:
            return []
        if not isinstance(value, list):
            self.diag(pointer, "wrong-type", "inputs must be an array", "use context selectors or artifact input objects")
            return []
        result: list[object] = []
        for offset, item in enumerate(value):
            item_pointer = f"{pointer}/{offset}"
            if isinstance(item, str):
                if item.startswith("artifact:"):
                    name = item[len("artifact:"):]
                    if not _SELECTOR_RE.fullmatch(name):
                        self.diag(item_pointer, "unsafe-selector", f"unsafe artifact selector {item!r}", "use artifact:<lowercase-id>")
                else:
                    self.safe_path(item, item_pointer, glob=True) if item not in {"story", "status", "architecture"} else None
                result.append(item)
                continue
            if isinstance(item, dict):
                self.exact_keys(item, _ARTIFACT_INPUT_KEYS, item_pointer)
                name = self.required_string(item.get("artifact"), f"{item_pointer}/artifact", pattern=_SELECTOR_RE)
                fmt = self.required_string(item.get("format"), f"{item_pointer}/format")
                if fmt and fmt not in OUTPUT_FORMATS:
                    self.diag(f"{item_pointer}/format", "unsupported-value", f"unsupported artifact format {fmt!r}", f"choose one of: {', '.join(OUTPUT_FORMATS)}")
                result.append({"artifact": name, "format": fmt})
                continue
            self.diag(item_pointer, "wrong-type", "input must be a selector string or typed artifact object", "use a string or {artifact, format}")
        return result

    def normalize_failure(self, value: object, pointer: str) -> dict[str, object] | None:
        if value is None:
            return None
        if not isinstance(value, dict):
            self.diag(pointer, "wrong-type", "failure policy must be an object", "provide a bounded action policy")
            return None
        self.exact_keys(value, _FAILURE_KEYS, pointer)
        action = self.required_string(value.get("action"), f"{pointer}/action")
        if action and action not in FAILURE_ACTIONS:
            self.diag(f"{pointer}/action", "unsupported-value", f"unsupported failure action {action!r}", f"choose one of: {', '.join(FAILURE_ACTIONS)}")
        result: dict[str, object] = {"action": action}
        if action == "retry":
            attempts = self.positive_int(value.get("max_attempts"), f"{pointer}/max_attempts", 0, 20)
            if value.get("max_attempts") is None:
                self.diag(f"{pointer}/max_attempts", "missing-bound", "retry requires an explicit finite max_attempts", "set max_attempts from 2 through 20")
            if attempts < 2:
                self.diag(f"{pointer}/max_attempts", "invalid-retry", "max_attempts must include at least one retry", "set max_attempts to 2 or greater")
            result["max_attempts"] = attempts
        elif action == "route":
            result["node"] = self.required_string(value.get("node"), f"{pointer}/node", pattern=_SELECTOR_RE)
            result["max_visits"] = self.positive_int(value.get("max_visits"), f"{pointer}/max_visits", 1, 20)
        elif action == "approval":
            result["checkpoint"] = self.required_string(value.get("checkpoint"), f"{pointer}/checkpoint", pattern=_SELECTOR_RE)
        for key in ("max_attempts", "node", "checkpoint", "max_visits"):
            if key in value and key not in result:
                self.diag(f"{pointer}/{key}", "inapplicable-field", f"{key} does not apply to {action!r}", "remove the field or choose the matching failure action")
        return result

    def normalize_runner(self, value: object, pointer: str, defaults: dict[str, int]) -> dict[str, object]:
        if not isinstance(value, dict):
            self.diag(pointer, "undeclared-executable", "check runner must be an exact object, never a shell string", "provide a command argv array or a named built-in check")
            return {"kind": "invalid"}
        kind = value.get("kind")
        if kind == "command":
            self.exact_keys(value, _COMMAND_RUNNER_KEYS, pointer)
            argv = value.get("argv")
            normalized_argv: list[str] = []
            if not isinstance(argv, list) or not argv:
                self.diag(f"{pointer}/argv", "undeclared-executable", "command argv must be a non-empty token array", "provide executable and arguments as separate strings")
            else:
                for offset, token in enumerate(argv):
                    if not isinstance(token, str) or not token or "\0" in token or len(token) > 2_000:
                        self.diag(f"{pointer}/argv/{offset}", "unsafe-argv", "argv tokens must be non-empty bounded strings without NUL", "provide one literal argument token")
                        continue
                    normalized_argv.append(token)
            if normalized_argv:
                executable = Path(normalized_argv[0]).name.lower()
                if Path(normalized_argv[0]).is_absolute():
                    self.diag(f"{pointer}/argv/0", "machine-specific-path", "command executable must not be an absolute machine path", "use a repository script or PATH-resolved executable name")
                if executable in {"sh", "bash", "zsh", "fish", "cmd", "powershell", "pwsh"} and any(token in {"-c", "/c", "-command"} for token in normalized_argv[1:]):
                    self.diag(f"{pointer}/argv", "shell-string", "inline shell command execution is prohibited", "invoke a tracked script by path or use direct tokenized argv")
            cwd = value.get("cwd", ".")
            if cwd not in {".", "workspace"}:
                cwd = self.safe_path(cwd, f"{pointer}/cwd", glob=False)
            timeout = self.positive_int(value.get("timeout_seconds"), f"{pointer}/timeout_seconds", defaults["default_timeout_seconds"], DEFAULT_LIMITS["default_timeout_seconds"])
            output_bytes = self.positive_int(value.get("output_bytes"), f"{pointer}/output_bytes", min(defaults["max_artifact_bytes"], 100_000), DEFAULT_LIMITS["max_artifact_bytes"])
            writes = self.string_list(value.get("writes"), f"{pointer}/writes")
            for offset, path in enumerate(writes):
                self.safe_path(path, f"{pointer}/writes/{offset}", glob=True)
            return {
                "kind": "command",
                "argv": normalized_argv,
                "cwd": cwd,
                "timeout_seconds": timeout,
                "output_bytes": output_bytes,
                "writes": writes,
            }
        if kind == "builtin":
            self.exact_keys(value, _BUILTIN_RUNNER_KEYS, pointer)
            name = self.required_string(value.get("name"), f"{pointer}/name")
            if name and name not in BUILTIN_CHECKS:
                self.diag(f"{pointer}/name", "unsupported-value", f"unsupported built-in check {name!r}", f"choose one of: {', '.join(BUILTIN_CHECKS)}")
            result: dict[str, object] = {
                "kind": "builtin",
                "name": name,
                "timeout_seconds": self.positive_int(value.get("timeout_seconds"), f"{pointer}/timeout_seconds", defaults["default_timeout_seconds"], DEFAULT_LIMITS["default_timeout_seconds"]),
                "output_bytes": self.positive_int(value.get("output_bytes"), f"{pointer}/output_bytes", min(defaults["max_artifact_bytes"], 100_000), DEFAULT_LIMITS["max_artifact_bytes"]),
            }
            if "path" in value:
                result["path"] = self.safe_path(value.get("path"), f"{pointer}/path", glob=False, workspace=True)
            if "schema" in value:
                result["schema"] = self.safe_path(value.get("schema"), f"{pointer}/schema", glob=False)
            if "allowed_paths" in value:
                paths = self.string_list(value.get("allowed_paths"), f"{pointer}/allowed_paths")
                for offset, path in enumerate(paths):
                    self.safe_path(path, f"{pointer}/allowed_paths/{offset}", glob=True)
                result["allowed_paths"] = paths
            required_by_name = {
                "file-exists": "path",
                "json-schema": "schema",
                "diff-scope": "allowed_paths",
            }
            required = required_by_name.get(name)
            if required and required not in result:
                self.diag(f"{pointer}/{required}", "missing-check-field", f"{name} requires {required}", f"declare {required}")
            return result
        self.diag(f"{pointer}/kind", "unsupported-value", f"unsupported runner kind {kind!r}", "choose command or builtin")
        return {"kind": str(kind or "invalid")}

    def normalize_node(self, raw: object, index: int, defaults: dict[str, int]) -> dict[str, object]:
        pointer = f"/nodes/{index}"
        if not isinstance(raw, dict):
            self.diag(pointer, "wrong-type", "node must be an object", "provide an exact typed node object")
            raw = {}
        node_type = self.required_string(raw.get("type"), f"{pointer}/type")
        if node_type not in NODE_TYPES:
            self.diag(f"{pointer}/type", "unsupported-node-type", f"unsupported node type {node_type!r}", f"choose one of: {', '.join(NODE_TYPES)}")
            allowed = _COMMON_NODE_KEYS
        else:
            allowed = _NODE_KEYS[node_type]
        self.exact_keys(raw, allowed, pointer)
        node_id = self.required_string(raw.get("id"), f"{pointer}/id", pattern=_SELECTOR_RE)
        if node_id:
            if node_id in self.node_indexes:
                self.diag(f"{pointer}/id", "duplicate-node-id", f"node id {node_id!r} is already used", "give every node a unique stable id")
            else:
                self.node_indexes[node_id] = index
        activation = raw.get("activation", "success")
        if activation not in ("success", "failure"):
            self.diag(f"{pointer}/activation", "unsupported-value", f"unsupported activation {activation!r}", "choose success or failure")
            activation = "success"
        needs = self.string_list(raw.get("needs"), f"{pointer}/needs", resource=True)
        groups = self.string_list(raw.get("resource_groups"), f"{pointer}/resource_groups", resource=True)
        result: dict[str, object] = {
            "id": node_id,
            "type": node_type,
            "activation": activation,
            "needs": needs,
            "resource_groups": groups,
        }
        title = self.optional_string(raw.get("title"), f"{pointer}/title", 500)
        description = self.optional_string(raw.get("description"), f"{pointer}/description", 5_000)
        if title is not None:
            result["title"] = title
        if description is not None:
            result["description"] = description
        failure = self.normalize_failure(raw.get("on_failure"), f"{pointer}/on_failure")
        if failure is not None:
            result["on_failure"] = failure

        if node_type == "agent":
            role = self.required_string(raw.get("role"), f"{pointer}/role", pattern=_ROLE_RE)
            profile = self.required_string(raw.get("profile"), f"{pointer}/profile", pattern=_ROLE_RE)
            capabilities = self.string_list(raw.get("capabilities"), f"{pointer}/capabilities", choices=CAPABILITIES)
            workspace = raw.get("workspace", "read-only")
            if workspace not in WORKSPACE_MODES:
                self.diag(f"{pointer}/workspace", "unsupported-value", f"unsupported workspace mode {workspace!r}", f"choose one of: {', '.join(WORKSPACE_MODES)}")
                workspace = "read-only"
            if "repository-write" in capabilities and workspace != "isolated-worktree":
                self.diag(f"{pointer}/workspace", "impossible-capability", "repository-write requires an isolated-worktree workspace", "choose isolated-worktree or remove repository-write")
            if workspace == "isolated-worktree" and "repository-write" not in capabilities:
                self.diag(f"{pointer}/capabilities", "impossible-workspace", "isolated-worktree requires repository-write capability", "request repository-write or choose a read-only workspace")
            outputs_raw = raw.get("outputs", [])
            if not isinstance(outputs_raw, list):
                self.diag(f"{pointer}/outputs", "wrong-type", "outputs must be an array", "provide typed output objects")
                outputs_raw = []
            outputs = [
                self.normalize_output(output, f"{pointer}/outputs/{offset}", defaults["max_artifact_bytes"])
                for offset, output in enumerate(outputs_raw)
            ]
            context = self.string_list(raw.get("context"), f"{pointer}/context")
            for offset, selector in enumerate(context):
                self.safe_path(selector, f"{pointer}/context/{offset}", glob=True)
            result.update({
                "role": role,
                "profile": profile,
                "prompt": self.optional_string(raw.get("prompt"), f"{pointer}/prompt") or "",
                "context": context,
                "capabilities": capabilities,
                "workspace": workspace,
                "inputs": self.normalize_inputs(raw.get("inputs"), f"{pointer}/inputs"),
                "outputs": outputs,
                "timeout_seconds": self.positive_int(raw.get("timeout_seconds"), f"{pointer}/timeout_seconds", defaults["default_timeout_seconds"], DEFAULT_LIMITS["default_timeout_seconds"]),
            })
        elif node_type == "check":
            result["runner"] = self.normalize_runner(raw.get("runner"), f"{pointer}/runner", defaults)
            expect = raw.get("expect", {"exit_code": 0})
            if not isinstance(expect, dict):
                self.diag(f"{pointer}/expect", "wrong-type", "expect must be an object", "provide an exact exit_code")
                expect = {"exit_code": 0}
            self.exact_keys(expect, _EXPECT_KEYS, f"{pointer}/expect")
            exit_code = expect.get("exit_code", 0)
            if isinstance(exit_code, bool) or not isinstance(exit_code, int) or not 0 <= exit_code <= 255:
                self.diag(f"{pointer}/expect/exit_code", "invalid-exit-code", "exit_code must be an integer from 0 through 255", "provide the exact expected exit code")
                exit_code = 0
            result["expect"] = {"exit_code": exit_code}
        elif node_type == "rail":
            action = self.required_string(raw.get("action"), f"{pointer}/action", pattern=_SELECTOR_RE)
            if action in {"commit", "certify-contract", "push", "release", "deploy"}:
                self.diag(f"{pointer}/action", "forbidden-authority", f"rail action {action!r} is permanently outside orchestration", "end at awaiting-certification and leave this act to the operator")
            result["action"] = action
            result["timeout_seconds"] = self.positive_int(raw.get("timeout_seconds"), f"{pointer}/timeout_seconds", defaults["default_timeout_seconds"], DEFAULT_LIMITS["default_timeout_seconds"])
        elif node_type == "approval":
            result["prompt"] = self.required_string(raw.get("prompt"), f"{pointer}/prompt", max_length=5_000)
            result["options"] = self.string_list(raw.get("options"), f"{pointer}/options", default=["approve", "reject"])
            terminal = raw.get("terminal")
            if terminal is not None:
                if terminal not in TERMINALS:
                    self.diag(f"{pointer}/terminal", "unsupported-value", f"unsupported terminal {terminal!r}", f"choose one of: {', '.join(TERMINALS)}")
                result["terminal"] = terminal
        elif node_type == "collect":
            outputs_raw = raw.get("outputs", [])
            if not isinstance(outputs_raw, list):
                self.diag(f"{pointer}/outputs", "wrong-type", "outputs must be an array", "provide typed output objects")
                outputs_raw = []
            result["inputs"] = self.normalize_inputs(raw.get("inputs"), f"{pointer}/inputs")
            result["outputs"] = [
                self.normalize_output(output, f"{pointer}/outputs/{offset}", defaults["max_artifact_bytes"])
                for offset, output in enumerate(outputs_raw)
            ]
            result["timeout_seconds"] = self.positive_int(raw.get("timeout_seconds"), f"{pointer}/timeout_seconds", defaults["default_timeout_seconds"], DEFAULT_LIMITS["default_timeout_seconds"])
        return result

    def graph_checks(self, nodes: list[dict[str, object]], layout: dict[str, object]) -> None:
        ids = {str(node.get("id")): index for index, node in enumerate(nodes) if node.get("id")}
        failure_targets: set[str] = set()
        for layout_id in (layout.get("nodes") or {}):
            if layout_id not in ids:
                self.diag(f"/layout/nodes/{layout_id}", "dangling-layout", f"layout references missing node {layout_id!r}", "remove the position or add the node")
        for index, node in enumerate(nodes):
            for offset, need in enumerate(node.get("needs", [])):
                if need not in ids:
                    self.diag(f"/nodes/{index}/needs/{offset}", "dangling-node-reference", f"dependency {need!r} does not exist", "reference an existing node id")
                if need == node.get("id"):
                    self.diag(f"/nodes/{index}/needs/{offset}", "success-cycle", "a node cannot depend on itself", "remove the self dependency")
            failure = node.get("on_failure")
            if isinstance(failure, dict) and failure.get("action") == "route":
                target = failure.get("node")
                if target not in ids:
                    self.diag(f"/nodes/{index}/on_failure/node", "dangling-failure-route", f"failure target {target!r} does not exist", "route to an existing failure-activated node")
                elif nodes[ids[str(target)]].get("activation") != "failure":
                    self.diag(f"/nodes/{ids[str(target)]}/activation", "unsafe-failure-route", "a failure-route target must have activation=failure", "mark the repair/escalation node as failure activated")
                else:
                    failure_targets.add(str(target))

        for index, node in enumerate(nodes):
            if node.get("activation") == "failure" and node.get("id") not in failure_targets:
                self.diag(
                    f"/nodes/{index}/activation",
                    "unreachable-node",
                    "failure-activated node is not targeted by any failure route",
                    "route a bounded failure policy to this node or remove it",
                )

        # Kahn's algorithm gives a deterministic cycle proof for success edges.
        indegree = {node_id: 0 for node_id in ids}
        dependents: dict[str, list[str]] = {node_id: [] for node_id in ids}
        for node in nodes:
            node_id = str(node.get("id") or "")
            for need in node.get("needs", []):
                if need in ids and node_id in indegree:
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
        cyclic = [node_id for node_id in ids if node_id not in visited]
        for node_id in cyclic:
            self.diag(f"/nodes/{ids[node_id]}/needs", "success-cycle", f"node {node_id!r} participates in a success dependency cycle", "remove a success edge; model retry/repair with a bounded failure policy")

        # Outputs have one producer; artifact inputs resolve and type-check.
        producers: dict[str, tuple[int, dict[str, object]]] = {}
        for index, node in enumerate(nodes):
            for offset, output in enumerate(node.get("outputs", [])):
                if not isinstance(output, dict):
                    continue
                name = str(output.get("name") or "")
                if not name:
                    continue
                if name in producers:
                    self.diag(f"/nodes/{index}/outputs/{offset}/name", "multiple-producers", f"artifact {name!r} already has a producer", "give every produced artifact a globally unique name")
                else:
                    producers[name] = (index, output)
        self.output_producers = producers

        ancestors: dict[str, set[str]] = {}

        def all_ancestors(node_id: str, seen: set[str] | None = None) -> set[str]:
            if node_id in ancestors:
                return ancestors[node_id]
            seen = set(seen or ())
            if node_id in seen:
                return set()
            seen.add(node_id)
            result: set[str] = set()
            node = nodes[ids[node_id]]
            for need in node.get("needs", []):
                if need in ids:
                    result.add(str(need))
                    result.update(all_ancestors(str(need), seen))
            ancestors[node_id] = result
            return result

        for index, node in enumerate(nodes):
            node_id = str(node.get("id") or "")
            permitted = all_ancestors(node_id) if node_id in ids else set()
            for offset, item in enumerate(node.get("inputs", [])):
                artifact = ""
                expected = None
                if isinstance(item, str) and item.startswith("artifact:"):
                    artifact = item[len("artifact:"):]
                elif isinstance(item, dict):
                    artifact = str(item.get("artifact") or "")
                    expected = item.get("format")
                if not artifact:
                    continue
                if artifact not in producers:
                    self.diag(f"/nodes/{index}/inputs/{offset}", "dangling-artifact", f"artifact {artifact!r} has no producer", "reference a declared output")
                    continue
                producer_index, output = producers[artifact]
                producer_id = str(nodes[producer_index].get("id") or "")
                if producer_id not in permitted:
                    self.diag(f"/nodes/{index}/inputs/{offset}", "artifact-order", f"artifact {artifact!r} is not produced by a dependency", "add the producer to needs directly or transitively")
                if expected is not None and expected != output.get("format"):
                    self.diag(f"/nodes/{index}/inputs/{offset}/format", "incompatible-artifact", f"consumer expects {expected!r} but producer emits {output.get('format')!r}", "align the consumer format with the declared output")

    def compile(self) -> tuple[dict[str, object], list[dict[str, str]]]:
        if not isinstance(self.raw, dict):
            self.diag("/", "wrong-type", "score must be a JSON object", "provide an object with kind, schema_version, slug, title, and nodes")
            raw: dict[str, object] = {}
        else:
            raw = self.raw
        self.exact_keys(raw, _TOP_KEYS, "")
        kind = raw.get("kind")
        if kind != SCORE_KIND:
            self.diag("/kind", "wrong-kind", f"expected {SCORE_KIND!r}, got {kind!r}", f"set kind to {SCORE_KIND}")
        version = raw.get("schema_version")
        if version != SCORE_SCHEMA_VERSION:
            self.diag("/schema_version", "unsupported-schema", f"expected schema_version 1, got {version!r}", "use schema version 1")
        slug = self.required_string(raw.get("slug"), "/slug", pattern=_SELECTOR_RE)
        title = self.required_string(raw.get("title"), "/title", max_length=500)
        description = self.optional_string(raw.get("description"), "/description", 5_000)
        project = self.optional_string(raw.get("project"), "/project", 128)
        if project is not None and not _SELECTOR_RE.fullmatch(project):
            self.diag("/project", "unsafe-selector", f"unsafe project selector {project!r}", "use a lowercase project slug")

        defaults_raw = raw.get("defaults", {})
        if not isinstance(defaults_raw, dict):
            self.diag("/defaults", "wrong-type", "defaults must be an object", "provide finite score bounds")
            defaults_raw = {}
        self.exact_keys(defaults_raw, _DEFAULT_KEYS, "/defaults")
        defaults = {
            key: self.positive_int(defaults_raw.get(key), f"/defaults/{key}", default, DEFAULT_LIMITS[key])
            for key, default in DEFAULTS.items()
        }
        layout = self.normalize_layout(raw.get("layout"))
        nodes_raw = raw.get("nodes")
        if not isinstance(nodes_raw, list) or not nodes_raw:
            self.diag("/nodes", "missing-nodes", "score requires a non-empty node array", "add at least one bounded node")
            nodes_raw = []
        if len(nodes_raw) > 500:
            self.diag("/nodes", "unbounded-graph", "score exceeds the 500-node schema bound", "split the orchestration into smaller scores")
            nodes_raw = nodes_raw[:500]
        nodes = [self.normalize_node(node, index, defaults) for index, node in enumerate(nodes_raw)]
        self.graph_checks(nodes, layout)
        normalized: dict[str, object] = {
            "kind": SCORE_KIND,
            "schema_version": SCORE_SCHEMA_VERSION,
            "slug": slug,
            "title": title,
            "defaults": defaults,
            "nodes": nodes,
            "layout": layout,
        }
        if description is not None:
            normalized["description"] = description
        if project is not None:
            normalized["project"] = project
        self.diagnostics.sort(key=lambda item: (item["pointer"], item["code"], item["message"]))
        return normalized, self.diagnostics


def validate_score(score: object) -> dict[str, object]:
    normalized, diagnostics = _Compiler(score).compile()
    return {
        "kind": VALIDATION_KIND,
        "schema_version": 1,
        "valid": not diagnostics,
        "diagnostics": diagnostics,
        "normalized": normalized if not diagnostics else None,
    }


def _analysis(normalized: dict[str, object]) -> dict[str, object]:
    nodes = list(normalized["nodes"])  # type: ignore[arg-type]
    ids = {str(node["id"]): index for index, node in enumerate(nodes)}
    dependents: dict[str, list[str]] = {node_id: [] for node_id in ids}
    capabilities: set[str] = set()
    profiles: set[str] = set()
    failure_edges: list[dict[str, object]] = []
    outputs: list[dict[str, object]] = []
    consumers: dict[str, list[str]] = {}
    terminals: list[dict[str, str]] = []
    checkpoints: list[str] = []
    for node in nodes:
        node_id = str(node["id"])
        for need in node.get("needs", []):
            dependents[str(need)].append(node_id)
        capabilities.update(str(value) for value in node.get("capabilities", []))
        if node.get("profile"):
            profiles.add(str(node["profile"]))
        failure = node.get("on_failure")
        if isinstance(failure, dict):
            failure_edges.append({"source": node_id, **failure})
        if node.get("type") == "approval":
            checkpoints.append(node_id)
            if node.get("terminal"):
                terminals.append({"node": node_id, "meaning": str(node["terminal"])})
        for output in node.get("outputs", []):
            item = {"producer": node_id, **output}
            outputs.append(item)
            consumers[str(output["name"])] = []
    for node in nodes:
        for input_item in node.get("inputs", []):
            name = ""
            if isinstance(input_item, str) and input_item.startswith("artifact:"):
                name = input_item[len("artifact:"):]
            elif isinstance(input_item, dict):
                name = str(input_item.get("artifact") or "")
            if name in consumers:
                consumers[name].append(str(node["id"]))
    for output in outputs:
        output["consumers"] = consumers[str(output["name"])]
    success_edges = [
        {"source": str(need), "target": str(node["id"])}
        for node in nodes
        for need in node.get("needs", [])
    ]
    return {
        "node_order": [str(node["id"]) for node in nodes],
        "success_edges": success_edges,
        "failure_edges": failure_edges,
        "roots": [str(node["id"]) for node in nodes if node.get("activation") == "success" and not node.get("needs")],
        "fan_out": [node_id for node_id in ids if len(dependents[node_id]) > 1],
        "fan_in": [str(node["id"]) for node in nodes if len(node.get("needs", [])) > 1],
        "capabilities": sorted(capabilities),
        "profiles": sorted(profiles),
        "output_lineage": outputs,
        "checkpoints": checkpoints,
        "terminals": terminals,
        "role_presets": list(ROLE_PRESETS),
    }


def compile_score(score: object) -> dict[str, object]:
    normalized, diagnostics = _Compiler(score).compile()
    if diagnostics:
        raise OrchestrationValidationError(diagnostics)
    runtime_score = {key: value for key, value in normalized.items() if key != "layout"}
    semantic_hash = _hash(runtime_score)
    document_hash = _hash(normalized)
    return {
        "kind": COMPILED_SCORE_KIND,
        "schema_version": COMPILED_SCORE_SCHEMA_VERSION,
        "semantic_hash": semantic_hash,
        "document_hash": document_hash,
        "score": runtime_score,
        "layout": normalized["layout"],
        "analysis": _analysis(normalized),
    }


def compile_score_path(path: Path) -> dict[str, object]:
    return compile_score(load_score(path))


def simulate_score(score_or_compiled: object) -> dict[str, object]:
    compiled = (
        score_or_compiled
        if isinstance(score_or_compiled, dict) and score_or_compiled.get("kind") == COMPILED_SCORE_KIND
        else compile_score(score_or_compiled)
    )
    if not isinstance(compiled, dict):  # defensive for type checkers/callers
        raise DwError("compiled orchestration document must be an object")
    score = compiled["score"]
    if not isinstance(score, dict):
        raise DwError("compiled orchestration document is missing score")
    nodes = list(score["nodes"])  # type: ignore[arg-type]
    defaults = score["defaults"]
    if not isinstance(defaults, dict):
        raise DwError("compiled orchestration document is missing defaults")
    max_concurrency = int(defaults["max_concurrency"])
    remaining = [node for node in nodes if node.get("activation") == "success"]
    completed: set[str] = set()
    waves: list[dict[str, object]] = []
    wave_number = 0
    while remaining:
        eligible = [node for node in remaining if set(node.get("needs", [])) <= completed]
        if not eligible:
            raise DwError("compiled orchestration graph cannot be scheduled")
        selected: list[dict[str, object]] = []
        locked: set[str] = set()
        for node in eligible:
            groups = set(str(group) for group in node.get("resource_groups", []))
            if groups & locked:
                continue
            selected.append(node)
            locked.update(groups)
            if len(selected) >= max_concurrency:
                break
        if not selected:
            selected = [eligible[0]]
        waves.append({
            "wave": wave_number,
            "eligible": [str(node["id"]) for node in eligible],
            "scheduled": [str(node["id"]) for node in selected],
            "resource_groups": sorted(locked),
        })
        for node in selected:
            completed.add(str(node["id"]))
            remaining.remove(node)
        wave_number += 1
    analysis = compiled["analysis"]
    return {
        "kind": SIMULATION_KIND,
        "schema_version": 1,
        "semantic_hash": compiled["semantic_hash"],
        "waves": waves,
        "fan_out": analysis["fan_out"],
        "fan_in": analysis["fan_in"],
        "capabilities": analysis["capabilities"],
        "profiles": analysis["profiles"],
        "output_lineage": analysis["output_lineage"],
        "checkpoints": analysis["checkpoints"],
        "failure_branches": analysis["failure_edges"],
        "budgets": defaults,
        "terminals": analysis["terminals"],
        "writes_events": False,
        "starts_work": False,
    }


def score_inventory(root: Path) -> dict[str, object]:
    scores: list[dict[str, object]] = []
    for path in discover_score_paths(root):
        raw = load_score(path)
        validation = validate_score(raw)
        item: dict[str, object] = {
            "name": path.stem,
            "path": str(path.relative_to(root.resolve())),
            "slug": raw.get("slug"),
            "title": raw.get("title"),
            "valid": validation["valid"],
            "diagnostics": validation["diagnostics"],
        }
        if validation["valid"]:
            compiled = compile_score(raw)
            item["semantic_hash"] = compiled["semantic_hash"]
            item["document_hash"] = compiled["document_hash"]
            item["nodes"] = len(compiled["score"]["nodes"])  # type: ignore[index]
        scores.append(item)
    return {
        "kind": "delivery-workbench-orchestration-list",
        "schema_version": 1,
        "scores": scores,
    }
