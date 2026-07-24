"""Pure Program Studio models and guarded tracked-policy edits.

The Studio is an optional authoring surface over the Phase-26 program,
workflow, and organization compilers.  It deliberately owns no runtime
semantics: graph cards, diagnostics, simulations, and authority explanations
are projections of the same compiler documents used by the CLI.  Preview and
apply can touch one direct-contained tracked JSON policy, but can never create
a grant, run, agent, check, observer, notification, integration, or roadmap
act.

This module is the Workbench boundary for WLA-26-06.  Keeping it independent
from the HTTP and browser adapters makes parity and no-program behavior
testable without starting a server.
"""

from __future__ import annotations

import difflib
import hashlib
import json
import os
import re
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from .model import DwError
from .orchestration import canonical_json
from .orchestration_driver import driver_capability, load_driver_config
from .plan_authoring import build_delivery_plan_authoring
from .program_organization import (
    compile_organization,
    find_organization_path,
    load_organization,
    organization_inventory,
    simulate_organization,
    validate_organization,
)
from .program_workflow import (
    compile_workflow,
    find_workflow_path,
    load_workflow,
    simulate_workflow,
    validate_workflow,
    workflow_inventory,
)
from .programs import (
    compile_program,
    find_program_path,
    load_program,
    program_inventory,
    simulate_program,
    validate_program,
)


STUDIO_KIND = "delivery-workbench-program-studio"
STUDIO_DOCUMENT_KIND = "delivery-workbench-program-studio-document"
STUDIO_GRAPH_KIND = "delivery-workbench-program-studio-graph"
STUDIO_AUTHORITY_KIND = "delivery-workbench-program-studio-authority-preview"
STUDIO_ROUND_TRIP_KIND = "delivery-workbench-program-studio-round-trip"
STUDIO_MUTATION_PREVIEW_KIND = "delivery-workbench-program-studio-mutation-preview"
STUDIO_MUTATION_RESULT_KIND = "delivery-workbench-program-studio-mutation-result"
STUDIO_SCHEMA_VERSION = 1

FAMILIES = ("program", "workflow", "organization")
_SAFE_ID_RE = re.compile(r"^[a-z][a-z0-9]*(?:[-_][a-z0-9]+)*$")

WORK_AND_VERDICT_CAPABILITIES = (
    "program:select",
    "agent:dispatch",
    "check:execute",
    "workspace:write",
    "verdict:issue",
    "council:decide",
    "obligation:record",
    "nudge:deliver",
    "notification:send",
)
DELIVERY_CAPABILITIES = (
    "obligation:materialize",
    "obligation:disposition",
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


@dataclass(frozen=True)
class _Family:
    id: str
    plural: str
    label: str
    kind: str
    inventory_key: str
    inventory: Callable[[Path], dict[str, object]]
    finder: Callable[[Path, str], Path]
    loader: Callable[[Path], dict[str, object]]


_FAMILY: dict[str, _Family] = {
    "program": _Family(
        "program", "programs", "Programs", "delivery-workbench-program",
        "programs", program_inventory, find_program_path, load_program,
    ),
    "workflow": _Family(
        "workflow", "workflows", "Workflows", "delivery-workbench-workflow",
        "workflows", workflow_inventory, find_workflow_path, load_workflow,
    ),
    "organization": _Family(
        "organization", "organizations", "Organizations",
        "delivery-workbench-organization", "organizations",
        organization_inventory, find_organization_path, load_organization,
    ),
}


@dataclass(frozen=True)
class StudioMutationPlan:
    root: Path
    family: str
    action: str
    name: str
    target: Path
    relative_path: str
    before: bytes | None
    after: bytes | None
    document: dict[str, object] | None
    validation: dict[str, object] | None
    compiled: dict[str, object] | None
    simulation: dict[str, object] | None
    fingerprint: str


def _sha(value: object) -> str:
    return "sha256:" + hashlib.sha256(
        canonical_json(value).encode("utf-8")
    ).hexdigest()


def _family(family: str) -> _Family:
    try:
        return _FAMILY[family]
    except KeyError as exc:
        raise DwError(
            f"unknown Program Studio family {family!r}; choose program, workflow, or organization"
        ) from exc


def _policy_dir(root: Path, spec: _Family) -> Path:
    root = root.resolve()
    allowed = (root / "pm" / spec.plural).resolve()
    if allowed != root and root not in allowed.parents:
        raise DwError(f"pm/{spec.plural} resolves outside the repository")
    return allowed


def _safe_target(root: Path, family: str, name: str) -> tuple[Path, str]:
    spec = _family(family)
    if not _SAFE_ID_RE.fullmatch(name or ""):
        raise DwError(f"unsafe {family} policy name: {name!r}")
    allowed = _policy_dir(root, spec)
    target = (allowed / f"{name}.json").resolve(strict=False)
    if target.parent != allowed:
        raise DwError(f"{family} policy escapes pm/{spec.plural}: {name}")
    relative = str(Path("pm") / spec.plural / f"{name}.json")
    return target, relative


def _read_optional(path: Path) -> bytes | None:
    try:
        return path.read_bytes()
    except FileNotFoundError:
        return None
    except OSError as exc:
        raise DwError(f"cannot read Studio policy {path}: {exc}") from exc


def _render(document: dict[str, object]) -> bytes:
    return (json.dumps(document, indent=2, ensure_ascii=False) + "\n").encode("utf-8")


def _compile_document(
    root: Path,
    family: str,
    document: object,
    source: str,
    simulation_selector: str | Path | None = None,
) -> tuple[dict[str, object], dict[str, object] | None, dict[str, object] | None]:
    """Return the exact family validation, compilation, and pure simulation."""
    simulation_input = document if simulation_selector is None else simulation_selector
    if family == "program":
        validation = validate_program(root, document, source)
        compiled = compile_program(root, document, source) if validation["valid"] else None
        simulate = lambda: simulate_program(root, simulation_input)  # noqa: E731
    elif family == "workflow":
        validation = validate_workflow(root, document, source=source)  # type: ignore[arg-type]
        compiled = compile_workflow(root, document, source=source) if validation["valid"] else None  # type: ignore[arg-type]
        simulate = lambda: simulate_workflow(root, simulation_input)  # noqa: E731
    elif family == "organization":
        validation = validate_organization(root, document, source)
        compiled = compile_organization(root, document, source) if validation["valid"] else None
        simulate = lambda: simulate_organization(root, simulation_input)  # noqa: E731
    else:
        _family(family)
        raise AssertionError("unreachable")

    simulation: dict[str, object] | None = None
    if validation["valid"]:
        try:
            simulation = simulate()
        except DwError as exc:
            # A valid program can be unschedulable against current roadmap or
            # local roster facts.  That is a simulation refusal, not a policy
            # compiler disagreement and not a reason to make the file unsavable.
            simulation = {
                "kind": "delivery-workbench-program-studio-simulation-refusal",
                "schema_version": STUDIO_SCHEMA_VERSION,
                "applicable": False,
                "issues": [{
                    "code": "simulation-refused",
                    "message": exc.message,
                }],
                "starts_work": False,
                "writes_policy": False,
                "writes_run_state": False,
                "creates_grant": False,
            }
    return validation, compiled, simulation


def _hashes(compiled: dict[str, object] | None, document: object) -> dict[str, object]:
    layout = document.get("layout", {}) if isinstance(document, dict) else {}
    return {
        "semantic": compiled.get("semantic_hash") if compiled else None,
        "document": compiled.get("document_hash") if compiled else None,
        "layout": _sha(layout),
        "policy_bundle": compiled.get("policy_bundle_hash") if compiled else None,
    }


def _route_entries(node: dict[str, object]) -> list[tuple[str, dict[str, object]]]:
    entries: list[tuple[str, dict[str, object]]] = []
    for key in (
        "on_success", "on_failure", "on_exhausted", "on_consensus",
        "on_repair", "on_dissent", "on_quorum_lost",
    ):
        route = node.get(key)
        if isinstance(route, dict):
            entries.append((key.removeprefix("on_"), route))
    routes = node.get("routes")
    if isinstance(routes, dict):
        for outcome, route in sorted(routes.items()):
            if isinstance(route, dict):
                entries.append((str(outcome), route))
    options = node.get("options")
    if isinstance(options, list):
        for option in options:
            if isinstance(option, dict) and isinstance(option.get("route"), dict):
                entries.append((f"option:{option.get('id')}", option["route"]))
    return entries


def _position(layout: object, node_id: str, index: int, lane: int = 0) -> dict[str, int]:
    if isinstance(layout, dict):
        nodes = layout.get("nodes")
        if isinstance(nodes, dict):
            raw = nodes.get(node_id)
            if isinstance(raw, dict):
                x, y = raw.get("x"), raw.get("y")
                if isinstance(x, (int, float)) and isinstance(y, (int, float)):
                    return {"x": int(x), "y": int(y)}
    return {"x": 70 + (index % 4) * 280, "y": 85 + lane * 175 + (index // 4) * 145}


def _node_outputs(node: dict[str, object]) -> list[dict[str, object]]:
    outputs = node.get("outputs", [])
    return [dict(item) for item in outputs if isinstance(item, dict)] if isinstance(outputs, list) else []


def _workflow_graph(document: dict[str, object]) -> dict[str, object]:
    raw_nodes = document.get("nodes", [])
    nodes = [item for item in raw_nodes if isinstance(item, dict)] if isinstance(raw_nodes, list) else []
    layout = document.get("layout", {})
    roles: list[str] = []
    for node in nodes:
        for value in ([node.get("role")] if node.get("role") else []):
            if isinstance(value, str) and value not in roles:
                roles.append(value)
        participants = node.get("participants", [])
        if isinstance(participants, list):
            for value in participants:
                if isinstance(value, str) and value not in roles:
                    roles.append(value)
        judge = node.get("judge_role")
        if isinstance(judge, str) and judge not in roles:
            roles.append(judge)
    lane_index = {role: index for index, role in enumerate(roles)}
    graph_nodes: list[dict[str, object]] = []
    for index, node in enumerate(nodes):
        node_id = str(node.get("id", f"node-{index + 1}"))
        role = str(node.get("role") or "")
        node_type = str(node.get("type") or "unknown")
        bounds = {
            key: node[key] for key in (
                "max_rounds", "max_attempts", "timeout_seconds",
                "round_timeout_seconds", "artifact_max_bytes",
                "artifact_max_tokens", "quorum", "freshness_seconds",
            ) if key in node
        }
        graph_nodes.append({
            "id": node_id,
            "layout_key": node_id,
            "pointer": f"/nodes/{index}",
            "type": node_type,
            "label": str(node.get("title") or node_id),
            "role": role or None,
            "lane": role or ("council" if node_type == "debate" else "system"),
            "position": _position(layout, node_id, index, lane_index.get(role, len(roles))),
            "container": node_type in {"loop", "debate"},
            "drilldown": (
                {"family": "workflow", "name": node.get("workflow")}
                if node_type in {"subflow", "loop"} and isinstance(node.get("workflow"), str)
                else None
            ),
            "artifacts": _node_outputs(node),
            "capabilities": list(node.get("capability_ceiling", []))
            if isinstance(node.get("capability_ceiling"), list) else [],
            "bounds": bounds,
            "routes": [
                {"outcome": outcome, **route}
                for outcome, route in _route_entries(node)
            ],
            "summary": {
                "purpose": node.get("purpose"),
                "workflow": node.get("workflow"),
                "rubric": node.get("rubric"),
                "participants": node.get("participants"),
                "judge": node.get("judge_role"),
                "rail": node.get("action"),
            },
            "keyboard": True,
        })

    ids = {str(node.get("id")) for node in nodes}
    edges: list[dict[str, object]] = []
    for index, node in enumerate(nodes):
        target = str(node.get("id", f"node-{index + 1}"))
        needs = node.get("needs", [])
        if isinstance(needs, list):
            for need in needs:
                if isinstance(need, str) and need in ids:
                    edges.append({
                        "from": need, "to": target, "kind": "success",
                        "label": "needs", "keyboard": True,
                    })
        for outcome, route in _route_entries(node):
            if route.get("kind") == "node" and route.get("target") in ids:
                edges.append({
                    "from": target, "to": route["target"], "kind": "route",
                    "label": outcome, "keyboard": True,
                })

    in_degree = {node["id"]: 0 for node in graph_nodes}
    out_degree = {node["id"]: 0 for node in graph_nodes}
    for edge in edges:
        if edge["to"] in in_degree:
            in_degree[edge["to"]] += 1
        if edge["from"] in out_degree:
            out_degree[edge["from"]] += 1
    for node in graph_nodes:
        node["fan_in"] = in_degree[node["id"]]
        node["fan_out"] = out_degree[node["id"]]

    return {
        "nodes": graph_nodes,
        "edges": edges,
        "lanes": [
            {"id": role, "label": role, "kind": "role", "keyboard": True}
            for role in roles
        ] + [{"id": "system", "label": "system / governed rails", "kind": "system", "keyboard": True}],
        "containers": [
            {
                "id": node["id"], "type": node["type"],
                "max_rounds": node["bounds"].get("max_rounds"),
                "routes": node["routes"],
            }
            for node in graph_nodes if node["container"]
        ],
        "features": {
            "nested_subflows": any(node["type"] == "subflow" for node in graph_nodes),
            "bounded_loops": any(node["type"] == "loop" for node in graph_nodes),
            "debates": any(node["type"] == "debate" for node in graph_nodes),
            "verdicts": any(node["type"] in {"verdict", "gate"} for node in graph_nodes),
            "fan_out": any(value > 1 for value in out_degree.values()),
            "fan_in": any(value > 1 for value in in_degree.values()),
            "artifacts": any(node["artifacts"] for node in graph_nodes),
        },
    }


def _program_graph(document: dict[str, object]) -> dict[str, object]:
    layout = document.get("layout", {})
    graph_nodes: list[dict[str, object]] = [{
        "id": "roadmap-scope", "pointer": "/scope", "type": "scope",
        "layout_key": "roadmap-scope",
        "label": str(document.get("scope", {}).get("project", "roadmap scope"))
        if isinstance(document.get("scope"), dict) else "roadmap scope",
        "lane": "roadmap", "position": _position(layout, "roadmap-scope", 0),
        "summary": document.get("scope", {}), "keyboard": True,
    }]
    edges: list[dict[str, object]] = []
    bindings = document.get("bindings", [])
    if not isinstance(bindings, list):
        bindings = []
    for index, binding in enumerate(bindings):
        if not isinstance(binding, dict):
            continue
        node_id = f"binding:{binding.get('id', index + 1)}"
        graph_nodes.append({
            "id": node_id, "pointer": f"/bindings/{index}", "type": "binding",
            "layout_key": node_id,
            "label": str(binding.get("id", f"binding {index + 1}")),
            "lane": "story-workflows", "position": _position(layout, node_id, index + 1, 1),
            "drilldown": {"family": "workflow", "name": binding.get("workflow")},
            "summary": {
                "priority": binding.get("priority"), "match": binding.get("match"),
                "workflow": binding.get("workflow"), "team": binding.get("team"),
                "rubrics": binding.get("rubrics"),
            },
            "keyboard": True,
        })
        edges.append({"from": "roadmap-scope", "to": node_id, "kind": "selection", "label": "candidate", "keyboard": True})
    gates = document.get("phase_gates", [])
    if not isinstance(gates, list):
        gates = []
    for index, gate in enumerate(gates):
        if not isinstance(gate, dict):
            continue
        node_id = f"gate:{gate.get('id', index + 1)}"
        graph_nodes.append({
            "id": node_id, "pointer": f"/phase_gates/{index}", "type": "architect-gate",
            "layout_key": node_id,
            "label": str(gate.get("id", f"gate {index + 1}")), "lane": "phase-gates",
            "position": _position(layout, node_id, len(graph_nodes), 2),
            "role": gate.get("role"), "summary": dict(gate), "keyboard": True,
        })
        sources = [node["id"] for node in graph_nodes if node["type"] == "binding"] or ["roadmap-scope"]
        for source in sources:
            edges.append({"from": source, "to": node_id, "kind": "gate", "label": str(gate.get("when", "gate")), "keyboard": True})
    return {
        "nodes": graph_nodes,
        "edges": edges,
        "lanes": [
            {"id": "roadmap", "label": "roadmap selection", "kind": "scope", "keyboard": True},
            {"id": "story-workflows", "label": "story workflow bindings", "kind": "binding", "keyboard": True},
            {"id": "phase-gates", "label": "phase architecture gates", "kind": "gate", "keyboard": True},
        ],
        "containers": [],
        "features": {
            "candidate_rules": bool(bindings), "architect_gates": bool(gates),
            "budgets": isinstance(document.get("budgets"), dict),
            "stop_routes": bool(document.get("stop_conditions")),
        },
    }


def _organization_graph(document: dict[str, object]) -> dict[str, object]:
    layout = document.get("layout", {})
    graph_nodes: list[dict[str, object]] = []
    edges: list[dict[str, object]] = []
    teams = document.get("teams", [])
    if not isinstance(teams, list):
        teams = []
    role_addresses: dict[str, list[str]] = {}
    for team_index, team in enumerate(teams):
        if not isinstance(team, dict):
            continue
        team_id = str(team.get("id", f"team-{team_index + 1}"))
        roles = team.get("roles", [])
        if not isinstance(roles, list):
            roles = []
        for role_index, role in enumerate(roles):
            if not isinstance(role, dict):
                continue
            role_id = str(role.get("id", f"role-{role_index + 1}"))
            node_id = f"{team_id}/{role_id}"
            role_addresses.setdefault(role_id, []).append(node_id)
            duty = str(role.get("duty") or role_id)
            graph_nodes.append({
                "id": node_id,
                "layout_key": node_id,
                "pointer": f"/teams/{team_index}/roles/{role_index}",
                "type": duty,
                "label": role_id,
                "role": role_id,
                "lane": team_id,
                "position": _position(layout, node_id, len(graph_nodes), team_index),
                "capabilities": list(role.get("capability_ceiling", []))
                if isinstance(role.get("capability_ceiling"), list) else [],
                "artifacts": role.get("artifacts", {}),
                "summary": {
                    "duty": duty, "pool": role.get("pool"),
                    "cardinality": role.get("cardinality"),
                    "workspace": role.get("workspace"),
                    "required": role.get("required"),
                    "independent_from": role.get("independent_from", []),
                    "replacement": role.get("replacement", {}),
                },
                "keyboard": True,
            })
    for node in graph_nodes:
        independent = node.get("summary", {}).get("independent_from", [])
        if isinstance(independent, list):
            for role_id in independent:
                for target in role_addresses.get(str(role_id), []):
                    edges.append({
                        "from": node["id"], "to": target, "kind": "separation",
                        "label": "independent", "keyboard": True,
                    })
    councils = document.get("councils", [])
    if not isinstance(councils, list):
        councils = []
    for index, council in enumerate(councils):
        if not isinstance(council, dict):
            continue
        council_id = str(council.get("id", f"council-{index + 1}"))
        node_id = f"council:{council_id}"
        graph_nodes.append({
            "id": node_id, "pointer": f"/councils/{index}", "type": "council",
            "layout_key": node_id,
            "label": council_id, "lane": "councils",
            "position": _position(layout, node_id, len(graph_nodes), len(teams)),
            "role": council.get("judge"),
            "summary": {
                "members": council.get("members", []), "judge": council.get("judge"),
                "meta_verifier": council.get("meta_verifier"), "quorum": council.get("quorum"),
                "decision": council.get("decision", {}), "audit": council.get("audit", {}),
                "budgets": council.get("budgets", {}),
            },
            "container": True, "keyboard": True,
        })
        members = council.get("members", [])
        if isinstance(members, list):
            for member in members:
                for source in role_addresses.get(str(member), []):
                    edges.append({
                        "from": source, "to": node_id, "kind": "council",
                        "label": "member", "keyboard": True,
                    })
    return {
        "nodes": graph_nodes,
        "edges": edges,
        "lanes": [
            {"id": str(team.get("id", f"team-{index + 1}")),
             "label": str(team.get("id", f"team {index + 1}")),
             "kind": "team", "keyboard": True}
            for index, team in enumerate(teams) if isinstance(team, dict)
        ] + [{"id": "councils", "label": "councils and meta-audit", "kind": "council", "keyboard": True}],
        "containers": [
            {"id": node["id"], "type": "council", "summary": node["summary"]}
            for node in graph_nodes if node.get("type") == "council"
        ],
        "features": {
            "implementer_verifier_separation": any(edge["kind"] == "separation" for edge in edges),
            "councils": bool(councils),
            "meta_verifier": any(
                isinstance(council, dict) and bool(council.get("meta_verifier"))
                for council in councils
            ),
            "master_architect": any(node["type"] == "master-architect" for node in graph_nodes),
            "replacement": any(bool(node.get("summary", {}).get("replacement")) for node in graph_nodes),
        },
    }


def build_studio_graph(family: str, document: dict[str, object]) -> dict[str, object]:
    """Project one raw config into an accessible graph without changing it."""
    _family(family)
    if family == "workflow":
        graph = _workflow_graph(document)
    elif family == "program":
        graph = _program_graph(document)
    else:
        graph = _organization_graph(document)
    return {
        "kind": STUDIO_GRAPH_KIND,
        "schema_version": STUDIO_SCHEMA_VERSION,
        "family": family,
        "config": json.loads(json.dumps(document)),
        **graph,
        "layout_hash": _sha(document.get("layout", {})),
        "starts_work": False,
        "writes_policy": False,
        "writes_run_state": False,
        "creates_grant": False,
    }


def studio_graph_to_config(graph: object) -> dict[str, object]:
    if not isinstance(graph, dict) or graph.get("kind") != STUDIO_GRAPH_KIND:
        raise DwError("Program Studio graph has the wrong kind")
    family = str(graph.get("family", ""))
    _family(family)
    config = graph.get("config")
    if not isinstance(config, dict):
        raise DwError("Program Studio graph is missing its lossless config")
    return json.loads(json.dumps(config))


def graph_config_round_trip(
    root: Path,
    family: str,
    document: dict[str, object],
) -> dict[str, object]:
    """Prove graph/config identity plus compiler semantic/layout identity."""
    graph = build_studio_graph(family, document)
    restored = studio_graph_to_config(graph)
    before_validation, before_compiled, _before_simulation = _compile_document(
        root, family, document, "studio-round-trip-before",
    )
    after_validation, after_compiled, _after_simulation = _compile_document(
        root, family, restored, "studio-round-trip-after",
    )
    before_hashes = _hashes(before_compiled, document)
    after_hashes = _hashes(after_compiled, restored)
    return {
        "kind": STUDIO_ROUND_TRIP_KIND,
        "schema_version": STUDIO_SCHEMA_VERSION,
        "family": family,
        "lossless": canonical_json(document) == canonical_json(restored),
        "valid_before": before_validation["valid"],
        "valid_after": after_validation["valid"],
        "hashes_before": before_hashes,
        "hashes_after": after_hashes,
        "semantic_hash_preserved": (
            before_hashes["semantic"] is not None
            and before_hashes["semantic"] == after_hashes["semantic"]
        ),
        "document_hash_preserved": (
            before_hashes["document"] is not None
            and before_hashes["document"] == after_hashes["document"]
        ),
        "layout_hash_preserved": before_hashes["layout"] == after_hashes["layout"],
        "starts_work": False,
        "writes_policy": False,
        "writes_run_state": False,
        "creates_grant": False,
    }


def _diagnostic_targets(
    family: str,
    document: dict[str, object],
    diagnostics: object,
) -> list[dict[str, object]]:
    if not isinstance(diagnostics, list):
        return []
    result: list[dict[str, object]] = []
    for diagnostic in diagnostics:
        if not isinstance(diagnostic, dict):
            continue
        pointer = str(diagnostic.get("pointer", "/"))
        node_id: str | None = None
        patterns = {
            "workflow": r"^/nodes/(\d+)",
            "program": r"^/(bindings|phase_gates)/(\d+)",
            "organization": r"^/(teams)/(\d+)/roles/(\d+)|^/(councils)/(\d+)",
        }
        match = re.match(patterns[family], pointer)
        try:
            if match and family == "workflow":
                raw = document.get("nodes", [])[int(match.group(1))]  # type: ignore[index]
                node_id = str(raw.get("id")) if isinstance(raw, dict) else None
            elif match and family == "program":
                collection = str(match.group(1))
                raw = document.get(collection, [])[int(match.group(2))]  # type: ignore[index]
                prefix = "binding" if collection == "bindings" else "gate"
                node_id = f"{prefix}:{raw.get('id')}" if isinstance(raw, dict) else None
            elif match and family == "organization":
                if match.group(1) == "teams":
                    team = document.get("teams", [])[int(match.group(2))]  # type: ignore[index]
                    role = team.get("roles", [])[int(match.group(3))] if isinstance(team, dict) else None
                    if isinstance(team, dict) and isinstance(role, dict):
                        node_id = f"{team.get('id')}/{role.get('id')}"
                elif match.group(4) == "councils":
                    council = document.get("councils", [])[int(match.group(5))]  # type: ignore[index]
                    node_id = f"council:{council.get('id')}" if isinstance(council, dict) else None
        except (IndexError, KeyError, TypeError, ValueError):
            node_id = None
        result.append({
            **diagnostic,
            "target": {
                "pointer": pointer,
                "node_id": node_id,
                "field_id": "studio-field-" + re.sub(r"[^a-zA-Z0-9_-]+", "-", pointer).strip("-"),
            },
        })
    return result


def _requested_capabilities(
    family: str,
    document: dict[str, object],
    compiled: dict[str, object] | None,
) -> list[str]:
    if family == "program":
        raw = document.get("requested_capabilities", [])
        return sorted(str(item) for item in raw) if isinstance(raw, list) else []
    if family == "workflow" and compiled:
        required = compiled.get("required_capabilities", {})
        if isinstance(required, dict):
            aggregate: set[str] = set()
            for value in required.values():
                if isinstance(value, list):
                    aggregate.update(str(item) for item in value)
            return sorted(aggregate)
        if isinstance(required, list):
            return sorted(str(item) for item in required)
    if family == "organization":
        aggregate = set()
        teams = document.get("teams", [])
        if isinstance(teams, list):
            for team in teams:
                roles = team.get("roles", []) if isinstance(team, dict) else []
                if isinstance(roles, list):
                    for role in roles:
                        caps = role.get("capability_ceiling", []) if isinstance(role, dict) else []
                        if isinstance(caps, list):
                            aggregate.update(str(item) for item in caps)
        return sorted(aggregate)
    return []


def build_authority_preview(
    family: str,
    document: dict[str, object],
    compiled: dict[str, object] | None,
    *,
    root: Path | None = None,
) -> dict[str, object]:
    requested = _requested_capabilities(family, document, compiled)
    known = set(WORK_AND_VERDICT_CAPABILITIES) | set(DELIVERY_CAPABILITIES)
    ceiling = str(document.get("mode_ceiling", "advisory")) if family == "program" else "advisory"
    order = {"advisory": 0, "checkpointed": 1, "continuous": 2}
    modes = [
        {
            "id": "advisory", "label": "Advisory", "within_ceiling": True,
            "dispatch": False, "mutation": False, "checkpoint": False,
            "meaning": "Compile, explain, and simulate only; no dispatch or repository act.",
        },
        {
            "id": "checkpointed", "label": "Checkpointed",
            "within_ceiling": order.get(ceiling, 0) >= 1,
            "dispatch": True, "mutation": "only separately granted exact rails",
            "checkpoint": True,
            "meaning": "Finite authority stops at every declared decision port.",
        },
        {
            "id": "continuous", "label": "Continuous",
            "within_ceiling": order.get(ceiling, 0) >= 2,
            "dispatch": True, "mutation": "only separately granted exact rails",
            "checkpoint": False,
            "meaning": "Finite authority continues only until a declared stop, refusal, expiry, revocation, or exhaustion.",
        },
    ]
    execution_contract = _studio_execution_contract(
        root, family, document, compiled
    )
    return {
        "kind": STUDIO_AUTHORITY_KIND,
        "schema_version": STUDIO_SCHEMA_VERSION,
        "family": family,
        "mode_ceiling": ceiling,
        "modes": modes,
        "groups": [
            {
                "id": "work-and-verdict", "label": "work and governed verdicts",
                "capabilities": [
                    {"id": capability, "requested": capability in requested}
                    for capability in WORK_AND_VERDICT_CAPABILITIES
                ],
            },
            {
                "id": "delivery-rails", "label": "evidence, certification, delivery, Git, and roadmap rails",
                "capabilities": [
                    {"id": capability, "requested": capability in requested}
                    for capability in DELIVERY_CAPABILITIES
                ],
            },
        ],
        "unknown_capabilities": sorted(set(requested) - known),
        "budgets": document.get("budgets", {}) if family == "program" else {},
        "stop_conditions": document.get("stop_conditions", []) if family == "program" else [],
        "execution_contract": execution_contract,
        "requested_only": True,
        "grant_required": True,
        "starts_work": False,
        "writes_policy": False,
        "writes_run_state": False,
        "creates_grant": False,
    }


def _studio_execution_contract(
    root: Path | None,
    family: str,
    document: dict[str, object],
    compiled: dict[str, object] | None,
) -> dict[str, object]:
    """Project portable organization ports and safe local resolution facts.

    Tracked policies select logical profiles and govern duties, packet
    visibility, fallbacks, separation, councils, and obligation authority.
    Operator-local driver configuration resolves those portable selectors to
    harness/provider/model/auth-domain fingerprints.  The projection never
    returns the principal name, auth-domain name, credentials, argv, or
    commands.
    """
    organization: dict[str, object] | None = None
    if family == "organization":
        organization = (
            compiled.get("organization")
            if isinstance(compiled, dict)
            and isinstance(compiled.get("organization"), dict)
            else document
        )
    elif family == "program" and isinstance(compiled, dict):
        references = compiled.get("references")
        if isinstance(references, dict):
            candidate = references.get("organization")
            if isinstance(candidate, dict):
                organization = candidate

    local_config: dict[str, object] | None = None
    local_issue = ""
    if root is not None:
        try:
            local_config = load_driver_config(root)
        except DwError as exc:
            local_issue = exc.message[:500]

    ports: list[dict[str, object]] = []
    fallbacks: list[dict[str, object]] = []
    independence: list[dict[str, object]] = []
    councils: list[dict[str, object]] = []
    if isinstance(organization, dict):
        for agent in organization.get("agents", []):
            if not isinstance(agent, dict):
                continue
            profile = str(agent.get("profile") or "")
            resolution: dict[str, object] = {
                "configured": False,
                "available": False,
                "harness": None,
                "adapter": None,
                "router": None,
                "provider": None,
                "model_vendor": None,
                "model_family": None,
                "model": None,
                "model_revision": None,
                "model_binding": None,
                "auth_domain_fingerprint": None,
                "principal_fingerprint": None,
                "capability_fingerprint": None,
            }
            if local_config is not None and profile:
                try:
                    capability = driver_capability(local_config, profile)
                    resolution.update({
                        "configured": True,
                        "available": bool(capability["available"]),
                        "harness": capability["harness"],
                        "adapter": capability["adapter"],
                        "router": capability["router"],
                        "provider": capability["provider"],
                        "model_vendor": capability["model_vendor"],
                        "model_family": capability["model_family"],
                        "model": capability["model"],
                        "model_revision": capability["model_revision"],
                        "model_binding": capability["model_binding"],
                        "auth_domain_fingerprint": (
                            capability["auth_domain_fingerprint"]
                        ),
                        "principal_fingerprint": (
                            capability["principal_fingerprint"]
                        ),
                        "capability_fingerprint": (
                            capability["capability_fingerprint"]
                        ),
                    })
                except DwError:
                    pass
            ports.append({
                "agent": agent.get("id"),
                "selector": {
                    "kind": "logical-profile",
                    "profile": profile,
                    "portable": True,
                    "resolution": "operator-local",
                },
                "constraints": {
                    "duties": list(agent.get("duties", [])),
                    "workspace_domain": agent.get("workspace_domain"),
                    "capability_ceiling": list(
                        agent.get("capability_ceiling", [])
                    ),
                    "max_concurrency": agent.get("max_concurrency"),
                },
                "local_resolution": resolution,
            })
        for team in organization.get("teams", []):
            if not isinstance(team, dict):
                continue
            for role in team.get("roles", []):
                if not isinstance(role, dict):
                    continue
                replacement = role.get("replacement")
                if isinstance(replacement, dict):
                    fallbacks.append({
                        "team": team.get("id"),
                        "role": role.get("id"),
                        "primary_pool": role.get("pool"),
                        "fallback_pools": list(
                            replacement.get("fallback_pools", [])
                        ),
                        "reasons": list(replacement.get("reasons", [])),
                        "max_replacements": replacement.get(
                            "max_replacements"
                        ),
                        "on_exhausted": replacement.get("on_exhausted"),
                    })
                for other in role.get("independent_from", []):
                    independence.append({
                        "team": team.get("id"),
                        "role": role.get("id"),
                        "independent_from": other,
                        "principal": "must-differ",
                        "profile": "must-differ",
                        "workspace_domain": "must-differ",
                        "session_binding": "must-differ",
                    })
        for council in organization.get("councils", []):
            if not isinstance(council, dict):
                continue
            members = list(council.get("members", []))
            councils.append({
                "id": council.get("id"),
                "members": members,
                "perspectives": [
                    {"role": role, "perspective": role}
                    for role in members
                ],
                "judge": council.get("judge"),
                "meta_verifier": council.get("meta_verifier"),
                "quorum": council.get("quorum"),
                "principal_diversity": (
                    "distinct"
                    if council.get("distinct_principals")
                    else "not-declared"
                ),
                "decision_authority": (
                    council.get("decision", {}).get("method")
                    if isinstance(council.get("decision"), dict)
                    else None
                ),
                "veto_roles": (
                    list(council.get("decision", {}).get("veto_roles", []))
                    if isinstance(council.get("decision"), dict)
                    else []
                ),
                "audit": council.get("audit", {}),
                "obligation_policy": {
                    "required_on_judgment": True,
                    "allowed_kinds": [
                        "backlog", "technical-debt", "risk",
                        "research", "follow-up",
                    ],
                    "blocking_prevents_progress": True,
                    "record_authority_role": council.get("judge"),
                },
            })

    resolved = [
        item["local_resolution"]
        for item in ports
        if item["local_resolution"]["configured"]
    ]
    diversity = {
        "independence": independence,
        "councils_require_distinct_principals": all(
            item["principal_diversity"] == "distinct"
            for item in councils
        ) if councils else False,
        "resolved_provider_count": len({
            item["provider"] for item in resolved if item["provider"]
        }),
        "resolved_model_family_count": len({
            item["model_family"] for item in resolved
            if item["model_family"]
        }),
        "resolved_principal_count": len({
            item["principal_fingerprint"] for item in resolved
            if item["principal_fingerprint"]
        }),
        "resolved_auth_domain_count": len({
            item["auth_domain_fingerprint"] for item in resolved
            if item["auth_domain_fingerprint"]
        }),
        "observed_only_until_grant": True,
    }
    return {
        "ports": ports,
        "fallbacks": fallbacks,
        "councils": councils,
        "diversity": diversity,
        "local_resolution_available": local_config is not None,
        "local_resolution_issue": local_issue,
        "content_safe": True,
        "credentials_exposed": False,
        "commands_accepted": False,
        "starts_work": False,
    }


def _simulation_scenarios(family: str, graph: dict[str, object]) -> list[dict[str, object]]:
    features = graph.get("features", {})
    scenarios = [
        ("candidate-assignment", "choose the next work", family == "program", "selection"),
        ("nested", "use a detailed work flow", bool(features.get("nested_subflows")), "success"),
        ("debate-active", "compare perspectives", bool(features.get("debates") or features.get("councils")), "debate"),
        ("verifier-failed", "review asks for repair", bool(features.get("verdicts") or features.get("implementer_verifier_separation")), "failure"),
        ("budget-exhausted", "a finite limit is reached", bool(features.get("budgets") or features.get("bounded_loops") or features.get("debates")), "exhausted"),
        ("phase-transition", "review phase completion", bool(features.get("architect_gates")), "gate"),
        ("complete", "delivery complete", True, "terminal"),
    ]
    return [
        {
            "id": scenario_id, "label": label, "available": available,
            "route_kind": route_kind, "synthetic_preview": True,
        }
        for scenario_id, label, available, route_kind in scenarios
    ]


def build_studio_document(root: Path, family: str, selector: str) -> dict[str, object]:
    spec = _family(family)
    path = spec.finder(root, selector)
    document = spec.loader(path)
    source = str(path.relative_to(root.resolve()))
    validation, compiled, simulation = _compile_document(
        root, family, document, source, simulation_selector=path,
    )
    graph = build_studio_graph(family, document)
    round_trip = graph_config_round_trip(root, family, document)
    diagnostics = _diagnostic_targets(family, document, validation.get("diagnostics"))
    presented_validation = {**validation, "diagnostics": diagnostics}
    return {
        "kind": STUDIO_DOCUMENT_KIND,
        "schema_version": STUDIO_SCHEMA_VERSION,
        "family": family,
        "name": path.stem,
        "path": source,
        "raw": document,
        "validation": presented_validation,
        "compiled": compiled,
        "simulation": simulation,
        "simulation_scenarios": _simulation_scenarios(family, graph),
        "graph": graph,
        "authority": build_authority_preview(
            family, document, compiled, root=root
        ),
        "round_trip": round_trip,
        "authoring": build_delivery_plan_authoring(
            family, document, presented_validation, graph, round_trip
        ),
        "starts_work": False,
        "writes_policy": False,
        "writes_roadmap": False,
        "writes_run_state": False,
        "creates_grant": False,
        "background_polling": False,
    }


def new_studio_document(family: str, slug: str | None = None) -> dict[str, object]:
    """Return an unsaved authoring draft; adopting it remains an explicit save."""
    spec = _family(family)
    slug = slug or f"new-{family}"
    if not _SAFE_ID_RE.fullmatch(slug):
        raise DwError(f"unsafe {family} draft slug: {slug!r}")
    if family == "workflow":
        return {
            "kind": spec.kind, "schema_version": 1, "slug": slug,
            "title": "New governed workflow", "version": "1.0.0",
            "parameters": [], "defaults": {},
            "nodes": [{
                "id": "review", "type": "checkpoint", "prompt_id": "review",
                "prompt": "Review the bounded workflow outcome.", "expires_seconds": 86400,
                "options": [
                    {"id": "approve", "label": "Approve", "route": {"kind": "terminal", "target": "complete"}},
                    {"id": "block", "label": "Block", "route": {"kind": "action", "target": "block"}},
                ],
            }],
            "terminals": [{"id": "complete", "meaning": "complete"}],
            "layout": {"nodes": {"review": {"x": 90, "y": 110}}, "viewport": {"x": 0, "y": 0, "zoom": 1}},
        }
    if family == "program":
        return {
            "kind": spec.kind, "schema_version": 1, "slug": slug,
            "title": "New optional delivery program",
            "scope": {
                "project": "project", "phases": {"from": 1, "through": 1},
                "stories": "all", "selection": "roadmap-frontier-v1",
                "blocked_policy": "stop",
            },
            "organization": "organization", "bindings": [], "phase_gates": [],
            "mode_ceiling": "advisory", "requested_capabilities": [],
            "budgets": {"max_phases": 1, "max_stories": 20},
            "stop_conditions": ["scope-complete", "blocked-frontier", "budget-exhausted"],
            "layout": {"nodes": {}, "viewport": {"x": 0, "y": 0, "zoom": 1}},
        }
    return {
        "kind": spec.kind, "schema_version": 1, "slug": slug,
        "title": "New governed organization", "agents": [], "pools": [],
        "teams": [], "councils": [],
        "layout": {"nodes": {}, "viewport": {"x": 0, "y": 0, "zoom": 1}},
    }


def build_program_studio(root: Path) -> dict[str, object]:
    """Build the healthy optional inventory without creating policy folders."""
    families: list[dict[str, object]] = []
    configured = 0
    healthy = True
    for family in FAMILIES:
        spec = _family(family)
        inventory = spec.inventory(root)
        items = inventory.get(spec.inventory_key, [])
        items = items if isinstance(items, list) else []
        configured += len(items)
        healthy = healthy and bool(inventory.get("healthy", False))
        families.append({
            "id": family,
            "plural": spec.plural,
            "label": spec.label,
            "path": f"pm/{spec.plural}",
            "items": items,
            "healthy": inventory.get("healthy", False),
            "draft": new_studio_document(family),
        })
    return {
        "kind": STUDIO_KIND,
        "schema_version": STUDIO_SCHEMA_VERSION,
        "families": families,
        "configured": configured,
        "empty": configured == 0,
        "healthy": healthy,
        "optional": True,
        "ordinary_workbench_ready": True,
        "default_route": "#/",
        "studio_route": "#/program-studio",
        "empty_state": {
            "tone": "neutral",
            "title": "No autonomous policy configured",
            "detail": "Ordinary Delivery Workbench is ready. Program Studio is available only when you choose to author tracked policy.",
            "blocking": False,
            "setup_required": False,
        },
        "starts_work": False,
        "writes_policy": False,
        "writes_roadmap": False,
        "writes_run_state": False,
        "creates_grant": False,
        "background_polling": False,
        "changes_default_route": False,
    }


def _fingerprint(
    family: str,
    action: str,
    relative_path: str,
    before: bytes | None,
    after: bytes | None,
) -> str:
    facts = {
        "family": family,
        "action": action,
        "path": relative_path,
        "before": "absent" if before is None else "sha256:" + hashlib.sha256(before).hexdigest(),
        "after": "absent" if after is None else "sha256:" + hashlib.sha256(after).hexdigest(),
    }
    return _sha(facts)


def build_studio_mutation_plan(
    root: Path,
    family: str,
    action: str,
    name: str,
    document: object | None = None,
) -> StudioMutationPlan:
    if action not in {"save", "delete"}:
        raise DwError("Program Studio mutation action must be save or delete")
    spec = _family(family)
    root = root.resolve()
    target, relative = _safe_target(root, family, name)
    before = _read_optional(target)
    validation = None
    compiled = None
    simulation = None
    after = None
    if action == "delete":
        if before is None:
            raise DwError(f"{family} policy does not exist: {name}")
    else:
        if not isinstance(document, dict):
            raise DwError("Program Studio save requires document as a JSON object")
        validation, compiled, simulation = _compile_document(root, family, document, relative)
        if document.get("kind") != spec.kind:
            # The family compiler also diagnoses this, but keep filename/family
            # mismatch explicit at the mutation boundary.
            validation = dict(validation)
        if document.get("slug") != name:
            raise DwError(
                f"{family} policy name {name!r} must match its slug {document.get('slug')!r}"
            )
        if validation["valid"]:
            after = _render(document)
    fingerprint = _fingerprint(family, action, relative, before, after)
    return StudioMutationPlan(
        root=root, family=family, action=action, name=name,
        target=target, relative_path=relative, before=before, after=after,
        document=(json.loads(json.dumps(document)) if isinstance(document, dict) else None),
        validation=validation, compiled=compiled, simulation=simulation,
        fingerprint=fingerprint,
    )


def _decode(value: bytes | None) -> str:
    return "" if value is None else value.decode("utf-8", errors="replace")


def studio_mutation_preview(plan: StudioMutationPlan) -> dict[str, object]:
    before_text, after_text = _decode(plan.before), _decode(plan.after)
    diff = "".join(difflib.unified_diff(
        before_text.splitlines(keepends=True), after_text.splitlines(keepends=True),
        fromfile=f"a/{plan.relative_path}", tofile=f"b/{plan.relative_path}",
    ))
    valid = plan.action == "delete" or bool(plan.validation and plan.validation["valid"])
    studio = None
    if plan.document is not None:
        graph = build_studio_graph(plan.family, plan.document)
        validation = plan.validation or {}
        presented_validation = {
            **validation,
            "diagnostics": _diagnostic_targets(
                plan.family,
                plan.document,
                validation.get("diagnostics", []),
            ),
        }
        round_trip = graph_config_round_trip(
            plan.root, plan.family, plan.document,
        )
        studio = {
            "kind": STUDIO_DOCUMENT_KIND,
            "schema_version": STUDIO_SCHEMA_VERSION,
            "family": plan.family,
            "name": plan.name,
            "path": plan.relative_path,
            "raw": plan.document,
            "validation": presented_validation,
            "compiled": plan.compiled,
            "simulation": plan.simulation,
            "simulation_scenarios": _simulation_scenarios(plan.family, graph),
            "graph": graph,
            "authority": build_authority_preview(
                plan.family, plan.document, plan.compiled, root=plan.root,
            ),
            "round_trip": round_trip,
            "authoring": build_delivery_plan_authoring(
                plan.family,
                plan.document,
                presented_validation,
                graph,
                round_trip,
            ),
            "starts_work": False,
            "writes_policy": False,
            "writes_roadmap": False,
            "writes_run_state": False,
            "creates_grant": False,
            "background_polling": False,
        }
    return {
        "kind": STUDIO_MUTATION_PREVIEW_KIND,
        "schema_version": STUDIO_SCHEMA_VERSION,
        "family": plan.family, "action": plan.action, "name": plan.name,
        "path": plan.relative_path, "fingerprint": plan.fingerprint,
        "exists": plan.before is not None, "valid": valid, "applicable": valid,
        "no_op": plan.before == plan.after, "diff": diff,
        "bytes_before": len(plan.before or b""), "bytes_after": len(plan.after or b""),
        "validation": plan.validation, "compiled": plan.compiled,
        "simulation": plan.simulation,
        "studio": studio,
        "starts_work": False, "writes_policy": False, "writes_roadmap": False,
        "writes_run_state": False, "creates_grant": False,
        "starts_agent": False, "starts_check": False, "starts_observer": False,
        "sends_notification": False, "applies_integration": False,
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


def apply_studio_mutation(
    plan: StudioMutationPlan,
    expected_fingerprint: str,
) -> dict[str, object]:
    """Apply exactly one fresh valid policy write/delete and verify read-back."""
    if expected_fingerprint != plan.fingerprint:
        raise DwError("stale Program Studio preview: policy bytes or desired content changed")
    if plan.action == "save" and not (plan.validation and plan.validation["valid"]):
        raise DwError("invalid Program Studio policies cannot be applied")
    plan.target.parent.mkdir(parents=True, exist_ok=True)
    lock_path = plan.target.parent / f".{plan.name}.studio-edit.lock"
    try:
        lock_fd = os.open(str(lock_path), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError as exc:
        raise DwError("Program Studio policy is being edited by another apply") from exc
    except OSError as exc:
        raise DwError(f"cannot claim Program Studio edit lock: {exc}") from exc
    os.close(lock_fd)
    changed = plan.before != plan.after
    try:
        if _read_optional(plan.target) != plan.before:
            raise DwError("stale Program Studio preview: policy bytes changed before apply")
        if changed:
            if plan.action == "delete":
                plan.target.unlink()
            else:
                if plan.after is None or plan.compiled is None:
                    raise DwError("Program Studio save plan has no valid content")
                _atomic_write(plan.target, plan.after)
                spec = _family(plan.family)
                reread = spec.loader(plan.target)
                _validation, compiled, _simulation = _compile_document(
                    plan.root, plan.family, reread, plan.relative_path,
                )
                if not compiled or compiled.get("document_hash") != plan.compiled.get("document_hash"):
                    raise DwError("saved Program Studio policy does not match the previewed document hash")
    except Exception as exc:
        if isinstance(exc, DwError) and exc.message.startswith("stale Program Studio preview"):
            raise
        try:
            _restore(plan.target, plan.before)
        except Exception as rollback_exc:
            raise DwError(
                f"Program Studio apply failed ({exc}) and rollback failed ({rollback_exc})"
            ) from exc
        if isinstance(exc, DwError):
            raise DwError(f"Program Studio apply failed and was rolled back: {exc.message}") from exc
        raise DwError(f"Program Studio apply failed and was rolled back: {exc}") from exc
    finally:
        try:
            lock_path.unlink()
        except FileNotFoundError:
            pass
    return {
        "kind": STUDIO_MUTATION_RESULT_KIND,
        "schema_version": STUDIO_SCHEMA_VERSION,
        "family": plan.family, "action": plan.action, "name": plan.name,
        "path": plan.relative_path, "fingerprint": plan.fingerprint,
        "applied": True, "changed": changed, "rolled_back": False,
        "semantic_hash": plan.compiled.get("semantic_hash") if plan.compiled else None,
        "document_hash": plan.compiled.get("document_hash") if plan.compiled else None,
        "starts_work": False, "writes_policy": changed,
        "writes_only": [plan.relative_path] if changed else [],
        "writes_roadmap": False, "writes_run_state": False,
        "creates_grant": False, "starts_agent": False, "starts_check": False,
        "starts_observer": False, "sends_notification": False,
        "applies_integration": False,
    }
