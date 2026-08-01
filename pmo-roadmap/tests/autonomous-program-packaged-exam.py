#!/usr/bin/env python3
"""Phase-26 exit exam against fresh wheel-installed consumers.

The green path grants one finite continuous program and then requires no
further human act.  Deterministic fixture adapters are injected behind exact
Claude/Sonnet-like and pi/OpenRouter/Kimi-like execution bindings so CI proves
the authority, scheduling, deliberation, delivery, and recovery machinery
without treating credentials or variable model output as a release oracle.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import http.client
import json
import os
import shutil
import subprocess
import sys
import tempfile
import threading
from datetime import datetime, timedelta, timezone
from http.server import ThreadingHTTPServer
from pathlib import Path


def run(argv, *, cwd, check=True, input_text=None, env=None):
    result = subprocess.run(
        [str(part) for part in argv],
        cwd=str(cwd),
        input=input_text,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env,
    )
    if check and result.returncode:
        raise AssertionError(
            "command failed ({}): {}\nstdout:\n{}\nstderr:\n{}".format(
                result.returncode, argv, result.stdout, result.stderr
            )
        )
    return result


def git(root, *argv, check=True, input_text=None, env=None):
    return run(
        ["git", "-C", root] + list(argv),
        cwd=root,
        check=check,
        input_text=input_text,
        env=env,
    )


def write_text(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def write_json(path, document):
    write_text(path, json.dumps(document, indent=2, sort_keys=True) + "\n")


def file_snapshot(root):
    result = {}
    for path in root.rglob("*"):
        if not path.is_file() or "__pycache__" in path.parts or path.suffix == ".pyc":
            continue
        try:
            result[str(path.relative_to(root))] = hashlib.sha256(path.read_bytes()).hexdigest()
        except FileNotFoundError:
            # Transient .git maintenance files may vanish mid-walk on CI.
            continue
    return result


def parse_sse(body):
    frames = []
    for block in body.split("\n\n"):
        fields = {}
        for line in block.splitlines():
            if ":" in line and not line.startswith(":"):
                key, _, value = line.partition(":")
                fields[key.strip()] = value.strip()
        if "data" in fields:
            frames.append((int(fields["id"]), json.loads(fields["data"])))
    return frames


def story_document(story_id, title, status, depends):
    return (
        "# {} - {}\n\n"
        "- **Project:** autonomous\n"
        "- **Phase:** {}\n"
        "- **Status:** {}\n"
        "- **Depends on:** {}\n"
        "- **Owner:** autonomous-program\n\n"
        "## Problem\n\n"
        "Prove one exact segment of the installed autonomous program.\n"
    ).format(story_id, title, story_id.split("-")[1], status, depends)


def author_roadmap(root):
    project = root / "pm/roadmap/autonomous"
    phase1 = project / "phase-1-foundation"
    phase2 = project / "phase-2-continuation"
    write_text(
        project / "README.md",
        """# Autonomous - Roadmap

**Last updated:** 2026-07-23.
**Current phase:** [Phase 1 - Foundation](./phase-1-foundation/current-phase-status.md).
**Status:** active.

## Phase index

| Phase | Goal (one line) | Status | Folder |
|---|---|---|---|
| 1 | Repair, deliberate, and cross a governed phase gate | in-progress | [phase-1-foundation](./phase-1-foundation/) |
| 2 | Continue under the same grant | planned | [phase-2-continuation](./phase-2-continuation/) |

## Project metadata

- **Slug:** `autonomous`
- **Story ID prefix:** AX
""",
    )
    write_text(
        phase1 / "current-phase-status.md",
        """# Phase 1 - Foundation

**Last updated:** 2026-07-23.

## Story status

| ID | Story | Status | Story file | Evidence |
|---|---|---|---|---|
| AX-1-01 | Repair an independently rejected candidate | in-progress | [story-01-repair](./story-01-repair.md) | - |
| AX-1-02 | Reach a governed council decision | backlog | [story-02-council](./story-02-council.md) | - |
""",
    )
    write_text(
        phase2 / "current-phase-status.md",
        """# Phase 2 - Continuation

**Last updated:** 2026-07-23.

## Story status

| ID | Story | Status | Story file | Evidence |
|---|---|---|---|---|
| AX-2-01 | Continue without another human act | backlog | [story-01-continuation](./story-01-continuation.md) | - |
| AX-2-02 | Hold the release decision outside program authority | on-hold (release decision) | [story-02-release-decision](./story-02-release-decision.md) | - |
""",
    )
    write_text(
        phase1 / "story-01-repair.md",
        story_document(
            "AX-1-01",
            "Repair an independently rejected candidate",
            "in-progress",
            "none",
        ),
    )
    write_text(
        phase1 / "story-02-council.md",
        story_document(
            "AX-1-02",
            "Reach a governed council decision",
            "backlog",
            "AX-1-01",
        ),
    )
    write_text(
        phase2 / "story-01-continuation.md",
        story_document(
            "AX-2-01",
            "Continue without another human act",
            "backlog",
            "AX-1-02",
        ),
    )
    write_text(
        phase2 / "story-02-release-decision.md",
        story_document(
            "AX-2-02",
            "Hold the release decision outside program authority",
            "on-hold",
            "AX-2-01",
        ),
    )


def agent_node(node_id, task):
    return {
        "id": node_id,
        "type": "agent",
        "role": "implementer",
        "task": task,
        "workspace": "isolated-worktree",
        "capability_ceiling": ["agent:dispatch", "workspace:write"],
        "timeout_seconds": 900,
        "max_attempts": 1,
        "inputs": {
            "story": {"kind": "parameter", "name": "story-id"},
        },
        "outputs": [{
            "id": "candidate",
            "kind": "git-diff",
            "max_bytes": 1_000_000,
        }],
        "on_failure": {"kind": "action", "target": "block"},
    }


def closed_check(node_id, needs, candidate):
    inputs = {}
    if candidate:
        inputs["candidate"] = {
            "kind": "artifact",
            "name": "{}.candidate".format(candidate),
        }
    return {
        "id": node_id,
        "type": "check",
        "needs": list(needs),
        "inputs": inputs,
        "runner": {
            "kind": "builtin",
            "name": "file-exists",
            "path": "pm/programs/autonomous-exit.json",
            "output_bytes": 50_000,
        },
        "expect": {"exit_code": 0},
        "timeout_seconds": 60,
        "max_attempts": 1,
        "outputs": [{
            "id": "fact",
            "kind": "mechanical-fact",
            "max_bytes": 20_000,
        }],
        "on_failure": {"kind": "action", "target": "block"},
    }


def workflow_document(slug, title, nodes):
    return {
        "kind": "delivery-workbench-workflow",
        "schema_version": 1,
        "slug": slug,
        "title": title,
        "version": "1.0.0",
        "parameters": [{
            "id": "story-id",
            "type": "string",
            "required": True,
            "max_bytes": 128,
        }],
        "defaults": {},
        "nodes": nodes,
        "terminals": [{"id": "complete", "meaning": "complete"}],
        "layout": {
            "nodes": {
                str(node["id"]): {
                    "x": 80 + (index * 300),
                    "y": 100 + ((index % 2) * 120),
                }
                for index, node in enumerate(nodes)
            },
            "viewport": {"x": 0, "y": 0, "zoom": 1},
        },
    }


def usability_decision_score():
    """One real bounded decision used by the Phase-27 composed exit exam."""
    return {
        "kind": "delivery-workbench-orchestration",
        "schema_version": 1,
        "slug": "usability-decision",
        "title": "Review one delivery decision",
        "project": "autonomous",
        "defaults": {
            "max_concurrency": 1,
            "max_wall_seconds": 3_600,
            "max_agent_starts": 1,
            "max_check_starts": 1,
            "default_timeout_seconds": 60,
            "max_artifact_bytes": 100_000,
        },
        "nodes": [{
            "id": "review",
            "type": "approval",
            "prompt": "Approve or reject the reviewed delivery decision.",
            "options": ["approve", "reject"],
        }],
        "layout": {
            "nodes": {"review": {"x": 180, "y": 100}},
            "viewport": {"x": 0, "y": 0, "zoom": 1},
        },
    }


def rubric_document(slug, subject_type, architect=False):
    if architect:
        vocabulary = ["pass", "fail", "approve", "veto", "escalate"]
        aggregation = {
            "method": "all",
            "threshold": 1,
            "on_pass": "approve",
            "on_fail": "veto",
            "on_abstain": "escalate",
            "on_inconclusive": "escalate",
        }
    else:
        vocabulary = ["pass", "fail", "needs-repair", "escalate"]
        aggregation = {
            "method": "all",
            "threshold": 1,
            "on_pass": "pass",
            "on_fail": "needs-repair",
            "on_abstain": "escalate",
            "on_inconclusive": "needs-repair",
        }
    return {
        "kind": "delivery-workbench-rubric",
        "schema_version": 1,
        "slug": slug,
        "title": slug.replace("-", " ").title(),
        "version": "1.0.0",
        "subject_type": subject_type,
        "result_vocabulary": vocabulary,
        "freshness": {
            "max_age_seconds": 3_600,
            "bind": [
                "subject",
                "repository",
                "program",
                "assignment",
                "rubric",
                "ledger",
            ],
        },
        "criteria": [{
            "id": "quality",
            "question": "Does the exact subject satisfy its contract?",
            "evaluation": {"kind": "agent-judgment", "fact": None},
            "required_evidence_kinds": [
                "markdown" if architect else "git-diff"
            ],
            "min_citations": 1,
            "allowed_results": [
                "pass",
                "fail",
                "abstain",
                "inconclusive",
            ],
            "veto": True,
            "rationale_max_bytes": 2_000,
        }],
        "aggregation": aggregation,
    }


def fixture_agent(agent_id, profile, duties, writer=False):
    capabilities = ["agent:dispatch"]
    if writer:
        capabilities.append("workspace:write")
    elif any(
        duty in {"verifier", "judge", "meta-verifier", "master-architect"}
        for duty in duties
    ):
        capabilities.append("verdict:issue")
        if "judge" in duties:
            capabilities.extend(["council:decide", "obligation:record"])
    return {
        "id": agent_id,
        "profile": profile,
        "duties": duties,
        "workspace_domain": agent_id,
        "capability_ceiling": capabilities,
        "max_concurrency": 1,
        "weight": 1,
    }


def fixture_role(role_id, duty, pool, independent=(), required=True):
    writer = duty in {"implementer", "repairer"}
    judgment = duty in {
        "verifier",
        "judge",
        "meta-verifier",
        "master-architect",
    }
    capabilities = ["agent:dispatch"]
    if writer:
        capabilities.append("workspace:write")
    elif judgment:
        capabilities.append("verdict:issue")
        if duty in {"verifier", "judge"}:
            capabilities.extend(["council:decide", "obligation:record"])
    return {
        "id": role_id,
        "duty": duty,
        "pool": pool,
        "required": required,
        "cardinality": 1,
        "capability_ceiling": capabilities,
        "driver_capabilities": (
            ["repository-read", "repository-write"]
            if writer
            else ["repository-read"]
        ),
        "workspace": "isolated-worktree" if writer else "read-only",
        "context": {
            "allow": [
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
            ],
            "expressions": [
                "context",
                "parameter",
                "literal",
                "artifact",
            ],
            "max_bytes": 500_000,
        },
        "artifacts": {
            "read": [
                "markdown",
                "json",
                "text",
                "git-diff",
                "verdict",
                "decision",
                "mechanical-fact",
            ],
            "write": (
                ["markdown", "json", "text", "git-diff"]
                if writer
                else ["verdict", "decision"]
            ),
            "max_bytes": 50_000_000,
        },
        "output_schema": None if judgment else "fixture-output@1",
        "verdict_schema": "fixture-verdict@1" if judgment else None,
        "max_concurrency": 1,
        "resource_groups": ["repository-writer"] if writer else [],
        "may_request": [],
        "may_judge": ["implementer"] if duty == "verifier" else [],
        "independent_from": list(independent),
        "replacement": {
            "reasons": [],
            "max_replacements": 0,
            "fallback_pools": [],
            "on_exhausted": "block",
            "preserve_history": True,
        },
    }


def author_policy(root):
    write_json(
        root / "pm/orchestration/usability-decision.json",
        usability_decision_score(),
    )
    a_implement = agent_node(
        "implement",
        "Implement Story A under the exact selected contract.",
    )
    a_check = closed_check("closed-check", ["implement"], "implement")
    a_check["on_success"] = {"kind": "terminal", "target": "complete"}
    workflow_a = workflow_document(
        "repair-story",
        "Implement, check, independently verify, and repair once",
        [a_implement, a_check],
    )

    council_check = closed_check("council-evidence", [], None)
    council_check.pop("on_success", None)
    debate = {
        "id": "design-council",
        "type": "debate",
        "needs": ["council-evidence"],
        "inputs": {
            "evidence": {
                "kind": "artifact",
                "name": "council-evidence.fact",
            },
        },
        "participants": ["architect", "critic"],
        "judge_role": "verifier",
        "max_rounds": 1,
        "quorum": 2,
        "artifact_max_bytes": 30_000,
        "artifact_max_tokens": 4_000,
        "round_timeout_seconds": 600,
        "tie_policy": "judge",
        "dissent_policy": "preserve",
        "on_consensus": {"kind": "node", "target": "implement"},
        "on_repair": {"kind": "action", "target": "block"},
        "on_dissent": {"kind": "action", "target": "checkpoint"},
        "on_quorum_lost": {"kind": "action", "target": "escalate"},
        "on_exhausted": {"kind": "action", "target": "escalate"},
        "outputs": [{
            "id": "judgment",
            "kind": "decision",
            "max_bytes": 50_000,
        }],
    }
    b_implement = agent_node(
        "implement",
        "Implement Story B after the bounded governed decision.",
    )
    b_implement["activation"] = "route"
    b_implement["on_success"] = {"kind": "terminal", "target": "complete"}
    workflow_b = workflow_document(
        "council-story",
        "Propose, critique, rebut, decide, audit, and implement",
        [council_check, debate, b_implement],
    )

    c_implement = agent_node(
        "implement",
        "Implement Story C under the unchanged continuous grant.",
    )
    c_check = closed_check("closed-check", ["implement"], "implement")
    c_check["on_success"] = {"kind": "terminal", "target": "complete"}
    workflow_c = workflow_document(
        "continuation-story",
        "Continue in the next phase",
        [c_implement, c_check],
    )
    for workflow in (workflow_a, workflow_b, workflow_c):
        write_json(
            root / "pm/workflows/{}.json".format(workflow["slug"]),
            workflow,
        )

    write_json(
        root / "pm/rubrics/story-quality.json",
        rubric_document("story-quality", "diff"),
    )
    write_json(
        root / "pm/rubrics/phase-architecture.json",
        rubric_document(
            "phase-architecture",
            "phase-snapshot",
            architect=True,
        ),
    )

    organization = {
        "kind": "delivery-workbench-organization",
        "schema_version": 1,
        "slug": "autonomous-cell",
        "title": "Autonomous multi-provider story cell",
        "agents": [
            fixture_agent(
                "builder-a",
                "claude-builder",
                ["implementer", "repairer"],
                writer=True,
            ),
            fixture_agent(
                "builder-b",
                "claude-repairer",
                ["implementer", "repairer"],
                writer=True,
            ),
            fixture_agent(
                "verifier-a",
                "pi-verifier",
                ["verifier", "judge"],
            ),
            fixture_agent("meta-a", "pi-meta", ["meta-verifier"]),
            fixture_agent(
                "architect-a",
                "claude-architect",
                ["master-architect"],
            ),
            fixture_agent("critic-a", "pi-critic", ["critic"]),
        ],
        "pools": [
            {"id": "builders", "agents": ["builder-a", "builder-b"]},
            {"id": "verifiers", "agents": ["verifier-a"]},
            {"id": "auditors", "agents": ["meta-a"]},
            {"id": "architects", "agents": ["architect-a"]},
            {"id": "critics", "agents": ["critic-a"]},
        ],
        "teams": [{
            "id": "story-cell",
            "roles": [
                fixture_role("implementer", "implementer", "builders"),
                fixture_role(
                    "verifier",
                    "verifier",
                    "verifiers",
                    independent=("implementer",),
                ),
                fixture_role(
                    "meta",
                    "meta-verifier",
                    "auditors",
                    independent=("implementer", "verifier"),
                    required=False,
                ),
                fixture_role(
                    "architect",
                    "master-architect",
                    "architects",
                    independent=("implementer", "verifier"),
                    required=False,
                ),
                fixture_role(
                    "critic",
                    "critic",
                    "critics",
                    required=False,
                ),
            ],
        }],
        "councils": [{
            "id": "quality-council",
            "members": ["architect", "critic", "verifier"],
            "judge": "verifier",
            "quorum": 2,
            "meta_verifier": "meta",
            "distinct_principals": True,
            "decision": {
                "method": "majority",
                "threshold": 1,
                "veto_roles": [],
            },
            "audit": {
                "mode": "full",
                "sample_size": 3,
                "on_overturn": "repair",
                "on_escalate": "escalate",
            },
        }],
        "layout": {
            "nodes": {
                "builders": {"x": 80, "y": 100},
                "quality-council": {"x": 430, "y": 240},
                "architects": {"x": 760, "y": 410},
            },
            "viewport": {"x": 0, "y": 0, "zoom": 1},
        },
    }
    write_json(root / "pm/organizations/autonomous-cell.json", organization)

    capabilities = [
        "program:select",
        "agent:dispatch",
        "check:execute",
        "workspace:write",
        "verdict:issue",
        "council:decide",
        "obligation:record",
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
    ]
    budgets = {
        "max_phases": 2,
        "max_stories": 3,
        "max_child_runs": 60,
        "max_agent_starts": 60,
        "max_provider_starts": 60,
        "max_model_starts": 60,
        "max_check_starts": 30,
        "max_loop_rounds": 12,
        "max_debate_rounds": 3,
        "max_councils": 3,
        "max_repairs_per_story": 1,
        "max_verdicts": 30,
        "max_obligations": 10,
        "max_obligation_materializations": 10,
        "max_obligation_dispositions": 10,
        "max_integrations": 3,
        "max_commits": 3,
        "max_pushes": 3,
        "max_nudges": 1,
        "max_artifact_bytes": 50_000_000,
        "max_tokens": 2_000_000,
        "max_observed_cost_microunits": 100_000_000,
        "max_wall_seconds": 7_200,
    }
    bindings = []
    for priority, story_id, workflow in (
        (10, "AX-1-01", "repair-story"),
        (20, "AX-1-02", "council-story"),
        (30, "AX-2-01", "continuation-story"),
    ):
        bindings.append({
            "id": story_id.lower(),
            "priority": priority,
            "match": {
                "phase_from": int(story_id.split("-")[1]),
                "phase_through": int(story_id.split("-")[1]),
                "story_ids": [story_id],
            },
            "workflow": workflow,
            "with": {
                "story-id": {"kind": "context", "name": "story.id"},
            },
            "team": "story-cell",
            "rubrics": ["story-quality"],
        })
    program = {
        "kind": "delivery-workbench-program",
        "schema_version": 1,
        "slug": "autonomous-exit",
        "title": "Fully autonomous two-phase exit exam",
        "scope": {
            "project": "autonomous",
            "phases": {"from": 1, "through": 2},
            "stories": {
                "include": ["AX-1-01", "AX-1-02", "AX-2-01"],
            },
            "selection": "roadmap-frontier-v1",
            "blocked_policy": "stop",
        },
        "organization": "autonomous-cell",
        "bindings": bindings,
        "phase_gates": [{
            "id": "architecture-gate",
            "when": "before-phase-complete",
            "role": "master-architect",
            "rubric": "phase-architecture",
            "on_fail": "block",
        }],
        "mode_ceiling": "continuous",
        "requested_capabilities": capabilities,
        "budgets": budgets,
        "stop_conditions": [
            "scope-complete",
            "checkpoint-required",
            "unresolved-dissent",
            "architect-veto",
            "blocked-frontier",
            "budget-exhausted",
            "grant-expired",
            "grant-revoked",
        ],
        "layout": {
            "nodes": {
                "roadmap-scope": {"x": 60, "y": 80},
                "binding:ax-1-01": {"x": 330, "y": 160},
                "binding:ax-1-02": {"x": 600, "y": 260},
                "gate:architecture-gate": {"x": 880, "y": 390},
                "binding:ax-2-01": {"x": 1160, "y": 170},
            },
            "viewport": {"x": 0, "y": 0, "zoom": 1},
        },
    }
    write_json(root / "pm/programs/autonomous-exit.json", program)
    return {
        "workflows": {
            item["slug"]: item
            for item in (workflow_a, workflow_b, workflow_c)
        },
        "organization": organization,
        "program": program,
        "rubrics": {
            "story-quality": rubric_document("story-quality", "diff"),
            "phase-architecture": rubric_document(
                "phase-architecture",
                "phase-snapshot",
                architect=True,
            ),
        },
    }


def driver_profile(adapter, principal, provider, vendor, family, model, writer):
    profile = {
        "adapter": adapter,
        "capabilities": (
            ["repository-read", "repository-write"]
            if writer
            else ["repository-read"]
        ),
        "workspace_modes": (
            ["isolated-worktree"] if writer else ["read-only"]
        ),
        "command": ["claude" if adapter == "claude-exec" else "pi"],
        "network": False,
        "principal": principal,
        "router": "openrouter" if provider == "openrouter" else "direct",
        "provider": provider,
        "model_vendor": vendor,
        "model_family": family,
        "model": model,
        "model_binding": "requested-alias",
        "auth_domain": "auth-{}".format(principal),
        "adapter_version": (
            "pi-cli@0.40.0"
            if adapter == "pi-exec"
            else "claude-cli-fixture-binding-v1"
        ),
        "available": True,
        "max_concurrency": 1,
    }
    return profile


def driver_document():
    return {
        "kind": "delivery-workbench-driver-config",
        "schema_version": 1,
        "workspace_root": None,
        "profiles": {
            "claude-builder": driver_profile(
                "claude-exec",
                "claude-builder",
                "anthropic",
                "anthropic",
                "claude-sonnet",
                "claude/sonnet",
                True,
            ),
            "claude-repairer": driver_profile(
                "claude-exec",
                "claude-repairer",
                "anthropic",
                "anthropic",
                "claude-sonnet",
                "claude/sonnet",
                True,
            ),
            "claude-architect": driver_profile(
                "claude-exec",
                "claude-architect",
                "anthropic",
                "anthropic",
                "claude-sonnet",
                "claude/sonnet",
                False,
            ),
            "pi-verifier": driver_profile(
                "pi-exec",
                "pi-verifier",
                "openrouter",
                "moonshot",
                "kimi",
                "moonshot/kimi",
                False,
            ),
            "pi-meta": driver_profile(
                "pi-exec",
                "pi-meta",
                "openrouter",
                "moonshot",
                "kimi",
                "moonshot/kimi",
                False,
            ),
            "pi-critic": driver_profile(
                "pi-exec",
                "pi-critic",
                "openrouter",
                "moonshot",
                "kimi",
                "moonshot/kimi",
                False,
            ),
        },
    }


def call_mcp(mcp, root, name, arguments):
    request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {"name": name, "arguments": arguments},
    }
    result = run(
        [mcp, "--root", root],
        cwd=root,
        input_text=json.dumps(request) + "\n",
    )
    payload = json.loads(result.stdout)["result"]
    assert not payload.get("isError"), payload
    return payload["structuredContent"]


def expect_error(callable_, contains=None):
    try:
        callable_()
    except Exception as exc:
        if contains:
            message = str(exc).lower()
            assert any(item.lower() in message for item in contains), message
        return str(exc)
    raise AssertionError("expected a refusal")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dw", required=True, type=Path)
    parser.add_argument("--keep", action="store_true")
    args = parser.parse_args()
    global_dw = args.dw.resolve()
    assert global_dw.is_file(), global_dw

    temporary = Path(
        tempfile.mkdtemp(prefix="dw-autonomous-program-exam.")
    ).resolve()
    root = temporary / "consumer"
    remote = temporary / "origin.git"
    baseline_remote = temporary / "baseline.git"
    vanilla = temporary / "vanilla"
    server = None
    try:
        root.mkdir()
        run(["git", "init", "--bare", "-q", remote], cwd=temporary)
        run(
            [
                "git", "--git-dir", remote, "symbolic-ref",
                "HEAD", "refs/heads/main",
            ],
            cwd=temporary,
        )
        git(root, "init", "-q", "-b", "main")
        git(root, "config", "user.name", "Autonomous Program Exam")
        git(root, "config", "user.email", "autonomous-exam@example.test")
        run(
            [global_dw, "install", root, "--skip-bootstrap"],
            cwd=temporary,
        )
        dw = root / ".githooks/dw"
        mcp = root / ".githooks/dw-mcp"
        for executable in (dw, mcp, root / ".githooks/dw-workbench"):
            assert executable.is_file(), executable
        author_roadmap(root)
        git(root, "remote", "add", "origin", remote)
        git(root, "add", "pm/roadmap")
        git(
            root,
            "-c",
            "core.hooksPath=/dev/null",
            "commit",
            "-qm",
            "Bootstrap ordinary roadmap consumer",
        )

        # Phase 27 begins on this exact consumer before optional policy exists.
        # Status, next-work inspection, and setup are all read-only; none may
        # manufacture a run/program store, process, or optional configuration.
        before_initial_use = file_snapshot(root)
        initial_program_result = run(
            [dw, "--root", root, "program", "list", "--json"],
            cwd=root,
        )
        initial_programs = json.loads(initial_program_result.stdout)
        assert initial_programs["healthy"]
        assert initial_programs["programs"] == []
        for key in (
            "starts_work",
            "writes_events",
            "creates_grant",
            "creates_program_store",
            "starts_process",
            "starts_stream",
            "starts_poller",
            "sends_notifications",
        ):
            assert initial_programs[key] is False, (
                key,
                initial_programs,
            )
        initial_status_result = run(
            [dw, "--root", root, "status", "autonomous", "--json"],
            cwd=root,
            check=False,
        )
        assert initial_status_result.returncode in (0, 1)
        initial_status = json.loads(initial_status_result.stdout)
        initial_step_result = run(
            [dw, "--root", root, "step", "autonomous", "--json"],
            cwd=root,
            check=False,
        )
        assert initial_step_result.returncode in (0, 1)
        initial_step = json.loads(initial_step_result.stdout)
        initial_next_result = run(
            [dw, "--root", root, "next", "autonomous", "--json"],
            cwd=root,
            check=False,
        )
        assert initial_next_result.returncode in (0, 2)
        initial_next = json.loads(initial_next_result.stdout)
        assert "AX-1-01" in initial_next_result.stdout
        initial_setup = run(
            [
                dw, "--root", root,
                "setup", "autonomous", "--technical",
            ],
            cwd=root,
            check=False,
        )
        assert initial_setup.returncode in (0, 1)
        for label in (
            "Continue with the roadmap",
            "Review one bounded delivery",
            "Set up an optional delivery program",
            "Technical details:",
        ):
            assert label in initial_setup.stdout, initial_setup.stdout
        assert before_initial_use == file_snapshot(root)
        for optional_path in (
            root / "pm/workflows",
            root / "pm/organizations",
            root / "pm/programs",
            root / "pm/rubrics",
            root / ".git/pmo-runs",
            root / ".git/pmo-programs",
        ):
            assert not optional_path.exists(), optional_path
        same_consumer_initial = {
            "status_kind": initial_status["kind"],
            "step_kind": initial_step["kind"],
            "next_available": True,
            "current_story": "AX-1-01",
            "programs": 0,
            "program_store": False,
            "run_store": False,
            "process_starts": initial_programs["starts_process"],
            "setup_writes": False,
            "setup_starts_work": False,
            "ordinary_work_requires_setup": False,
            "optional_policy_present": False,
        }

        # The next commit is the deliberate optional configuration act. It is
        # separate from the read-only setup comparison and from runtime start.
        authored = author_policy(root)
        git(root, "add", "-A")
        git(
            root,
            "-c",
            "core.hooksPath=/dev/null",
            "commit",
            "-qm",
            "Configure reviewed optional delivery",
        )
        git(root, "push", "-qu", "-u", "origin", "main")
        assert not git(root, "status", "--porcelain").stdout
        shutil.copytree(remote, baseline_remote)

        # Import only the package vendored by this installation.
        sys.path.insert(0, str(root / ".githooks"))
        from dw_pmo import DwError  # noqa: E402
        import dw_pmo.mcpserver as mcpserver  # noqa: E402
        from dw_pmo.decision_basis import read_decision_bases  # noqa: E402
        import dw_pmo.orchestration_conductor as run_conductor  # noqa: E402
        import dw_pmo.orchestration_run as run_authority  # noqa: E402
        import dw_pmo.orchestration_surface as run_surface  # noqa: E402
        import dw_pmo.program_conductor as conductor  # noqa: E402
        import dw_pmo.program_delivery as delivery  # noqa: E402
        import dw_pmo.program_run as authority  # noqa: E402
        import dw_pmo.program_surface as surface  # noqa: E402
        import dw_pmo.workbench as workbench  # noqa: E402
        from dw_pmo.notifications import build_notifications  # noqa: E402
        from dw_pmo.orchestration_driver import (  # noqa: E402
            load_driver_config,
            validate_driver_config,
            write_driver_config,
        )
        from dw_pmo.program_organization import (  # noqa: E402
            assign_organization_team,
            compile_organization,
            validate_organization,
        )
        from dw_pmo.program_studio import graph_config_round_trip  # noqa: E402
        from dw_pmo.program_verdict import (  # noqa: E402
            compile_rubric,
            validate_mechanical_fact,
            validate_verdict_document,
            verdict_freshness_issues,
        )
        from dw_pmo.program_workflow import validate_workflow  # noqa: E402
        from dw_pmo.programs import (  # noqa: E402
            build_program_plan,
            compile_program,
            validate_program,
        )

        write_driver_config(root, driver_document())
        config = load_driver_config(root)
        adapters = {}

        obligation = {
            "id": "carry-council-technical-debt",
            "kind": "technical-debt",
            "statement": "Retain the minority council concern as visible debt.",
            "priority": "medium",
            "blocking": False,
            "accountable_role": "architect",
            "target": "AX-1-02",
            "citations": ["evidence:council-evidence"],
            "acceptance": "A later bounded story may discharge the concern.",
            "state": "open",
        }

        class ExamDriver(conductor.ProgramFixtureDriver):
            def __init__(self, architect_veto=False):
                super().__init__()
                self.architect_veto = architect_veto
                self.packets = []

            def _response(self, packet):
                self.packets.append(copy.deepcopy(packet))
                try:
                    prompt = json.loads(str(packet.get("prompt") or "{}"))
                except ValueError:
                    prompt = {}
                address = str(prompt.get("address") or "")
                action_kind = str(prompt.get("action_kind") or "")
                stage = str(prompt.get("deliberation_stage") or "")
                role = str(packet.get("role") or "")
                if (
                    "story/AX-1-01/" in address
                    and action_kind == "story-verification"
                    and "/attempt/1" in address
                ):
                    return {"judgment_result": "fail"}
                if action_kind == "council-judgment":
                    return {"obligations": [obligation]}
                if stage == "rebuttal" and role == "critic":
                    return {"vote": "repair"}
                if action_kind == "architect-verdict" and self.architect_veto:
                    return {"judgment_result": "fail"}
                if action_kind in {"agent", "repair"}:
                    if "story/AX-1-01/" in address:
                        name = "story_a"
                    elif "story/AX-1-02/" in address:
                        name = "story_b"
                    else:
                        name = "story_c"
                    content = (
                        "candidate=repair-pass\n"
                        if action_kind == "repair"
                        else "candidate=initial\n"
                    )
                    return {
                        "workspace_files": {
                            "src/{}.txt".format(name): content,
                        },
                    }
                return {}

        driver = ExamDriver()
        adapters.update({
            "fixture": driver,
            "claude-exec": driver,
            "pi-exec": driver,
        })

        # Every tracked policy is compiler-valid and survives the Studio's
        # semantic/document/layout round trip without starting work.
        for workflow in authored["workflows"].values():
            validation = validate_workflow(root, workflow)
            assert validation["valid"], validation["diagnostics"]
            round_trip = graph_config_round_trip(root, "workflow", workflow)
            assert (
                round_trip["lossless"]
                and round_trip["semantic_hash_preserved"]
                and round_trip["layout_hash_preserved"]
            ), round_trip
        organization_validation = validate_organization(
            root, authored["organization"]
        )
        assert organization_validation["valid"], organization_validation
        organization_round_trip = graph_config_round_trip(
            root, "organization", authored["organization"]
        )
        assert organization_round_trip["lossless"], organization_round_trip
        program_validation = validate_program(root, authored["program"])
        assert program_validation["valid"], program_validation["diagnostics"]
        program_round_trip = graph_config_round_trip(
            root, "program", authored["program"]
        )
        assert program_round_trip["lossless"], program_round_trip
        phase27_authoring = {
            "configured_after_initial_use": True,
            "workflow_count": len(authored["workflows"]),
            "organization": authored["organization"]["slug"],
            "program": authored["program"]["slug"],
            "rubrics": sorted(authored["rubrics"]),
            "workflow_round_trips_lossless": True,
            "organization_round_trip_lossless": True,
            "program_round_trip_lossless": True,
            "starts_work": False,
            "creates_permission": False,
        }

        # Compiler/assignment red matrix: all are pure documents or pure
        # assignment simulations and create no grant or child process.
        red = {}
        unbounded = copy.deepcopy(authored["workflows"]["repair-story"])
        unbounded["nodes"][1]["on_success"] = {
            "kind": "node",
            "target": "implement",
        }
        result = validate_workflow(root, unbounded)
        assert not result["valid"], result
        red["unbounded-loop"] = [
            item["code"] for item in result["diagnostics"]
        ]

        impossible_quorum = copy.deepcopy(authored["organization"])
        impossible_quorum["councils"][0]["quorum"] = 4
        result = validate_organization(root, impossible_quorum)
        assert not result["valid"], result
        red["quorum-loss"] = [
            item["code"] for item in result["diagnostics"]
        ]

        fallback = copy.deepcopy(authored["organization"])
        fallback["teams"][0]["roles"][0]["replacement"].update({
            "reasons": ["unavailable"],
            "max_replacements": 1,
            "fallback_pools": ["undeclared-provider-pool"],
        })
        result = validate_organization(root, fallback)
        assert not result["valid"], result
        red["undeclared-provider-fallback"] = [
            item["code"] for item in result["diagnostics"]
        ]

        compiled_org = compile_organization(
            root, authored["organization"]
        )
        compiled_program = compile_program(root, authored["program"])
        workflow_runtime = compiled_program["references"][
            "workflow_instances"
        ]["ax-1-01"]

        # Provider-family diversity is an opt-in organization rule. Fixture
        # profiles declare their families explicitly so this fresh-wheel exam
        # proves both the only allowed pairing and the pre-dispatch refusal.
        diversity_org = copy.deepcopy(authored["organization"])
        diversity_org["diversity"] = [{
            "id": "cross-family-review",
            "kind": "provider-family",
            "roles": ["implementer", "verifier"],
        }]
        compiled_diversity_org = compile_organization(root, diversity_org)
        fixture_families = copy.deepcopy(config)
        for profile_id, profile in fixture_families["profiles"].items():
            profile["adapter"] = "fixture"
            profile["provider_family"] = (
                "author-family"
                if profile_id in {"claude-builder", "claude-repairer"}
                else "review-family"
            )
        diverse_assignment = assign_organization_team(
            compiled_diversity_org,
            "story-cell",
            driver_config=fixture_families,
            policy_bundle_hash=compiled_program["policy_bundle_hash"],
            story_id="AX-1-01",
            workflow_address=(
                "program/autonomous-exit/phase/1/story/AX-1-01/"
                "workflow/ax-1-01"
            ),
            program_capabilities=authored["program"][
                "requested_capabilities"
            ],
            workflow=workflow_runtime,
        )
        assert diverse_assignment["applicable"], diverse_assignment
        assert diverse_assignment["diversity"]["passed"], diverse_assignment
        same_family = copy.deepcopy(fixture_families)
        same_family["profiles"]["pi-verifier"][
            "provider_family"
        ] = "author-family"
        refused_diversity = assign_organization_team(
            compiled_diversity_org,
            "story-cell",
            driver_config=same_family,
            policy_bundle_hash=compiled_program["policy_bundle_hash"],
            story_id="AX-1-01",
            workflow_address=(
                "program/autonomous-exit/phase/1/story/AX-1-01/"
                "workflow/ax-1-01"
            ),
            program_capabilities=authored["program"][
                "requested_capabilities"
            ],
            workflow=workflow_runtime,
        )
        assert not refused_diversity["applicable"], refused_diversity
        diversity_diagnostic = next(
            item for item in refused_diversity["issues"]
            if item["code"] == "provider-diversity-unsatisfied"
        )
        assert "cross-family-review" in diversity_diagnostic["message"]
        assert "missing a family different from author-family" in (
            diversity_diagnostic["message"]
        )
        red["provider-family-diversity"] = [
            item["code"] for item in refused_diversity["issues"]
        ]
        provider_diversity_observation = {
            "rule": "cross-family-review",
            "satisfying_families": diverse_assignment["diversity"][
                "rules"
            ][0]["families"],
            "unsatisfied_code": diversity_diagnostic["code"],
            "refused_before_start": not refused_diversity["starts_work"],
            "fixture_families_declared": True,
        }
        colliding = copy.deepcopy(config)
        for profile_id in ("claude-builder", "claude-repairer"):
            colliding["profiles"][profile_id]["principal"] = "shared-writer"
        colliding["profiles"]["pi-verifier"] = copy.deepcopy(
            colliding["profiles"]["claude-architect"]
        )
        colliding["profiles"]["pi-verifier"]["principal"] = "shared-writer"
        assignment = assign_organization_team(
            compiled_org,
            "story-cell",
            driver_config=colliding,
            policy_bundle_hash=compiled_program["policy_bundle_hash"],
            story_id="AX-1-01",
            workflow_address=(
                "program/autonomous-exit/phase/1/story/AX-1-01/"
                "workflow/ax-1-01"
            ),
            program_capabilities=authored["program"][
                "requested_capabilities"
            ],
            workflow=workflow_runtime,
        )
        assert not assignment["applicable"], assignment
        red["self-verifier-impossible-separation"] = [
            item["code"] for item in assignment["issues"]
        ]

        blocked_config = copy.deepcopy(config)
        blocked_config["profiles"]["claude-builder"]["available"] = False
        blocked_config["profiles"]["claude-repairer"]["available"] = False
        assignment = assign_organization_team(
            compiled_org,
            "story-cell",
            driver_config=blocked_config,
            policy_bundle_hash=compiled_program["policy_bundle_hash"],
            story_id="AX-1-01",
            workflow_address=(
                "program/autonomous-exit/phase/1/story/AX-1-01/"
                "workflow/ax-1-01"
            ),
            program_capabilities=authored["program"][
                "requested_capabilities"
            ],
            workflow=workflow_runtime,
        )
        assert not assignment["applicable"], assignment
        red["blocked-agent"] = [
            item["code"] for item in assignment["issues"]
        ]
        unknown_config = copy.deepcopy(config)
        del unknown_config["profiles"]["claude-builder"]
        del unknown_config["profiles"]["claude-repairer"]
        assignment = assign_organization_team(
            compiled_org,
            "story-cell",
            driver_config=unknown_config,
            policy_bundle_hash=compiled_program["policy_bundle_hash"],
            story_id="AX-1-01",
            workflow_address=(
                "program/autonomous-exit/phase/1/story/AX-1-01/"
                "workflow/ax-1-01"
            ),
            program_capabilities=authored["program"][
                "requested_capabilities"
            ],
            workflow=workflow_runtime,
        )
        assert not assignment["applicable"], assignment
        red["unknown-agent-profile"] = [
            item["code"] for item in assignment["issues"]
        ]

        now = datetime.now(timezone.utc).replace(microsecond=0)
        issued = now.strftime("%Y-%m-%dT%H:%M:%SZ")
        expires = (now + timedelta(hours=1)).strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        )
        request = {
            "program": "autonomous-exit",
            "mode": "continuous",
            "operator": "phase-26-exam",
            "reason": "Run the reviewed finite two-phase exit program.",
            "intent_id": "phase-26-green",
            "issued_at": issued,
            "expires_at": expires,
            "remote": "origin",
            "remote_ref": "refs/remotes/origin/main",
        }

        # The same installed consumer crosses one real bounded decision and
        # one permanent-stop boundary. These are ordinary Phase-27 journeys,
        # but their previews and receipts are the existing exact run models.
        decision_plan = run_authority.build_run_plan(
            root,
            "usability-decision",
            "autonomous",
            "AX-1-01",
            issued_at=now,
            expires_at=now + timedelta(hours=1),
        )
        assert decision_plan["applicable"], decision_plan["issues"]
        assert not decision_plan["starts_work"]
        assert not decision_plan["writes_run_state"]
        decision_started = run_authority.start_run(
            root,
            decision_plan,
            decision_plan["start_token"],
            approved=True,
            approved_by="Phase 27 fresh-wheel exam",
            now=now,
        )
        run_conductor.tick_run(
            root,
            decision_started["run_id"],
            now=now,
        )
        decision_waiting = run_authority.replay_run(
            root, decision_started["run_id"], now=now
        )
        assert decision_waiting["state"] == "awaiting-approval"
        assert len(decision_waiting["outstanding_requests"]) == 1
        decision_view = run_surface.build_run_view(
            root, decision_started["run_id"], now=now
        )
        decision_request = decision_waiting["outstanding_requests"][0]
        decision_inbox = next(
            item
            for item in decision_view["bounded_actions"]["inbox"]
            if item["id"].endswith(decision_request["correlation_id"])
        )
        before_decision_preview = file_snapshot(root)
        decision_preview = run_surface.build_run_act_preview(
            root,
            decision_started["run_id"],
            "checkpoint",
            decision="approve",
            correlation_id=decision_request["correlation_id"],
            now=now,
        )
        assert decision_preview["applicable"], decision_preview["issues"]
        assert not decision_preview["starts_work"]
        assert before_decision_preview == file_snapshot(root)
        decision_after = run_surface.apply_run_act(
            root,
            decision_started["run_id"],
            "checkpoint",
            decision_preview["act_token"],
            decision="approve",
            correlation_id=decision_request["correlation_id"],
            now=now,
        )
        assert not decision_after["outstanding_requests"]
        assert (
            decision_after["ledger_head"]
            != decision_waiting["ledger_head"]
        )
        bounded_decision_observation = {
            "run_id": decision_started["run_id"],
            "start_preview_pure": True,
            "state_before": decision_waiting["state"],
            "question": decision_inbox["why"],
            "resolver": decision_inbox["resolver"],
            "choices": [
                item["decision"]
                for item in decision_inbox["valid_choices"]
            ],
            "visible_next_step": decision_view[
                "live_progress"
            ]["next_step"]["label"],
            "response_preview_pure": True,
            "decision": "approve",
            "state_after": decision_after["state"],
            "exact": {
                "correlation_id": decision_request["correlation_id"],
                "ledger_before": decision_waiting["ledger_head"],
                "ledger_after": decision_after["ledger_head"],
                "act_token": decision_preview["act_token"],
            },
        }

        stop_time = now + timedelta(seconds=1)
        stop_plan = run_authority.build_run_plan(
            root,
            "usability-decision",
            "autonomous",
            "AX-1-01",
            issued_at=stop_time,
            expires_at=stop_time + timedelta(hours=1),
        )
        assert stop_plan["applicable"], stop_plan["issues"]
        stop_started = run_authority.start_run(
            root,
            stop_plan,
            stop_plan["start_token"],
            approved=True,
            approved_by="Phase 27 fresh-wheel exam",
            now=stop_time,
        )
        run_conductor.tick_run(
            root,
            stop_started["run_id"],
            now=stop_time,
        )
        stop_waiting = run_authority.replay_run(
            root, stop_started["run_id"], now=stop_time
        )
        assert stop_waiting["state"] == "awaiting-approval"
        stop_view = run_surface.build_run_view(
            root, stop_started["run_id"], now=stop_time
        )
        revoke_action = next(
            item
            for item in stop_view["bounded_actions"]["actions"]
            if item.get("action") == "revoke"
        )
        before_revoke_preview = file_snapshot(root)
        revoke_preview = run_surface.build_run_act_preview(
            root,
            stop_started["run_id"],
            "revoke",
            reason="Permanently stop the reviewed bounded delivery.",
            now=stop_time,
        )
        assert revoke_preview["applicable"], revoke_preview["issues"]
        assert not revoke_preview["starts_work"]
        assert before_revoke_preview == file_snapshot(root)
        revoked = run_surface.apply_run_act(
            root,
            stop_started["run_id"],
            "revoke",
            revoke_preview["act_token"],
            reason="Permanently stop the reviewed bounded delivery.",
            now=stop_time,
        )
        assert revoked["state"] == "revoked"
        assert revoked["control_generation"] == (
            stop_waiting["control_generation"] + 1
        )
        bounded_stop_observation = {
            "run_id": stop_started["run_id"],
            "state_before": stop_waiting["state"],
            "label": revoke_action["label"],
            "effect": revoke_action["consequences"]["effect"],
            "unchanged": revoke_action["consequences"]["unchanged"],
            "preview_pure": True,
            "state_after": revoked["state"],
            "exact": {
                "generation_before": stop_waiting[
                    "control_generation"
                ],
                "generation_after": revoked["control_generation"],
                "ledger_head": revoked["ledger_head"],
                "act_token": revoke_preview["act_token"],
            },
        }

        missing_model = copy.deepcopy(config)
        profile = missing_model["profiles"]["pi-verifier"]
        profile.pop("model")
        red["missing-model-fingerprint"] = expect_error(
            lambda: validate_driver_config(missing_model),
            ["model", "binding", "requires"],
        )

        before_preview = file_snapshot(root)
        planning = build_program_plan(root, "autonomous-exit")
        assert planning["applicable"], planning["issues"]
        assert len(planning["scope"]["stories"]) == 3
        plan = authority.build_program_start_plan(
            root,
            request["program"],
            mode=request["mode"],
            operator=request["operator"],
            approval_reason=request["reason"],
            intent_id=request["intent_id"],
            issued_at=issued,
            expires_at=expires,
            remote=request["remote"],
            remote_ref=request["remote_ref"],
        )
        assert plan["applicable"], plan["issues"]
        assert plan["authority"]["mode"] == "continuous"
        assert plan["worst_case"]["includes_failure_branches"]
        assert len(plan["scope"]["stories"]) == 3
        assert {
            seat["execution"]["provider"]
            for seat in plan["roster"]["seats"]
        } >= {"anthropic", "openrouter"}
        assert before_preview == file_snapshot(root)
        assert not (root / ".git/pmo-programs").exists()
        phase27_preflight = {
            "program": plan["program"]["slug"],
            "scope": {
                "project": plan["scope"]["project"],
                "stories": list(plan["scope"]["story_ids"]),
                "phases": plan["scope"]["phases"],
            },
            "team": [
                {
                    "role": seat["role"],
                    "duty": seat["duty"],
                    "agent": seat["agent"],
                    "provider": seat["execution"]["provider"],
                    "model": seat["execution"]["model"],
                    "workspace_domain": seat["workspace_domain"],
                }
                for seat in plan["roster"]["seats"]
            ],
            "independent_review": bool(
                plan["roster"]["separation"].get("passed")
            ),
            "decision_councils": [
                {
                    "id": item["id"],
                    "quorum": item["quorum"],
                    "primary_authority": item["primary_authority"],
                    "tie_authority": item["tie_authority"],
                }
                for item in plan["roster"]["councils"]
            ],
            "allowed_effects": plan["authority"]["capabilities"],
            "limits": plan["authority"]["budgets"],
            "stops": plan["authority"]["stop_conditions"],
            "permanently_excluded": plan[
                "authority"
            ]["permanent_exclusions"],
            "cost_accounting": plan["authority"]["cost_accounting"],
            "failure_branches_included": plan[
                "worst_case"
            ]["includes_failure_branches"],
            "preview_effects": {
                key: plan[key]
                for key in (
                    "starts_work",
                    "writes_policy",
                    "writes_roadmap",
                    "writes_run_state",
                    "creates_grant",
                )
            },
            "separate_start_required": True,
        }

        cli_plan = json.loads(
            run(
                [
                    dw,
                    "--root",
                    root,
                    "program",
                    "plan",
                    request["program"],
                    "--mode",
                    request["mode"],
                    "--operator",
                    request["operator"],
                    "--reason",
                    request["reason"],
                    "--intent",
                    request["intent_id"],
                    "--issued-at",
                    issued,
                    "--expires-at",
                    expires,
                    "--remote",
                    "origin",
                    "--remote-ref",
                    "refs/remotes/origin/main",
                    "--json",
                ],
                cwd=root,
            ).stdout
        )
        mcp_plan = call_mcp(
            mcp,
            root,
            "dw_program_plan",
            request,
        )
        status, http_plan = workbench.handle_mutation(
            root, "/api/programs/plan", request
        )
        assert status == 200, http_plan
        for observed_plan in (
            cli_plan,
            mcp_plan,
            http_plan["data"],
        ):
            assert (
                surface.document_bytes(observed_plan)
                == surface.document_bytes(plan)
            )
        assert before_preview == file_snapshot(root)

        # A would-be decider cannot rewrite its preassigned seat in the
        # reviewed grant. The altered plan is rejected before store creation.
        self_selected = copy.deepcopy(plan)
        self_selected["roster"]["councils"][0][
            "decider_seat"
        ] = self_selected["roster"]["councils"][0]["members"][0]
        red["decider-self-selection"] = expect_error(
            lambda: authority.start_program(
                root,
                self_selected,
                start_token=self_selected["start_token"],
                now=issued,
            ),
            ["hash", "changed", "token", "plan", "decider", "authority"],
        )
        assert not (root / ".git/pmo-programs").exists()
        red["authority-free-stream"] = expect_error(
            lambda: surface.read_program_stream(
                root,
                "program-000000000000000000000000",
                "session-000000000000000000000000",
                "stdout",
            ),
            ["absent", "missing", "not found", "no such"],
        )
        red["no-grant"] = expect_error(
            lambda: authority.build_program_claim_preview(
                root,
                "program-000000000000000000000000",
                category="selection",
                subject={
                    "kind": "story",
                    "id": "AX-1-01",
                    "hash": "sha256:" + ("a" * 64),
                    "phase": 1,
                    "story": "AX-1-01",
                },
                idempotency_key="no-grant",
                reason="This must not reserve work.",
                now=issued,
            ),
            ["absent", "missing", "not found", "no such"],
        )

        plan_path = root / ".git/phase-26-start-plan.json"
        write_json(plan_path, plan)
        started = json.loads(
            run(
                [
                    dw,
                    "--root",
                    root,
                    "program",
                    "start",
                    "--plan",
                    plan_path,
                    "--expect",
                    plan["start_token"],
                    "--approve",
                    "--json",
                ],
                cwd=root,
            ).stdout
        )
        run_id = started["run_id"]
        assert started["state"] == "running"
        assert len(surface.program_summary_inventory(root)["runs"]) == 1
        # The CLI owns the exact grant-start timestamp. Subsequent fixture
        # receipts use one deterministic instant just after that act so the
        # ledger remains monotonic even on a slow package builder.
        issued = (
            datetime.now(timezone.utc).replace(microsecond=0)
            + timedelta(seconds=2)
        ).strftime("%Y-%m-%dT%H:%M:%SZ")

        # Runtime freshness binds both the requested model alias and the
        # authoritative roadmap snapshot. Restore exact bytes after each
        # planted drift so the reviewed program can continue unchanged.
        original_config = load_driver_config(root)
        changed = copy.deepcopy(original_config)
        changed["profiles"]["pi-verifier"]["model"] = "moonshot/kimi-changed"
        write_driver_config(root, changed)
        red["changed-model-fingerprint"] = expect_error(
            lambda: conductor.derive_program_frontier(
                root, run_id, driver_config=changed, now=issued
            ),
            ["changed", "stale", "roster", "driver", "fingerprint"],
        )
        write_driver_config(root, original_config)
        config = load_driver_config(root)
        roadmap_path = (
            root
            / "pm/roadmap/autonomous/phase-1-foundation/"
            "story-01-repair.md"
        )
        roadmap_bytes = roadmap_path.read_bytes()
        roadmap_path.write_bytes(roadmap_bytes + b"\nPlanted drift.\n")
        red["stale-roadmap"] = expect_error(
            lambda: conductor.derive_program_frontier(
                root, run_id, driver_config=config, now=issued
            ),
            ["roadmap", "changed", "stale", "repository"],
        )
        roadmap_path.write_bytes(roadmap_bytes)
        assert not git(root, "status", "--porcelain").stdout

        crash_counts = {
            "conductor": 0,
            "delivery": 0,
        }
        injected_conductor = set()
        failed_delivery_refusal = None

        def crash_tick(action_kind, boundary):
            def hook(name, _detail):
                if name == boundary:
                    raise RuntimeError(
                        "planted conductor {} {}".format(
                            action_kind, boundary
                        )
                    )

            try:
                conductor.tick_program(
                    root,
                    run_id,
                    driver_config=config,
                    adapters=adapters,
                    now=issued,
                    boundary_hook=hook,
                )
            except RuntimeError as exc:
                assert "planted conductor" in str(exc)
                crash_counts["conductor"] += 1
                return
            raise AssertionError(
                "conductor boundary did not fire: {} {}".format(
                    action_kind, boundary
                )
            )

        def conduct_story(story_id):
            nonlocal failed_delivery_refusal
            for _index in range(160):
                frontier = conductor.derive_program_frontier(
                    root, run_id, driver_config=config, now=issued
                )
                if (
                    frontier["state"] == "story-certified"
                    and frontier["stop"] == "integration-required"
                    and frontier["lineage"]["story"] == story_id
                ):
                    return frontier
                actions = frontier["next_actions"]
                assert actions, frontier
                action_kind = actions[0]["kind"]
                marker = (story_id, action_kind)
                if (
                    story_id == "AX-1-01"
                    and action_kind == "agent"
                    and marker not in injected_conductor
                ):
                    crash_tick(action_kind, "before-dispatch")
                    crash_tick(action_kind, "after-dispatch")
                    injected_conductor.add(marker)
                elif (
                    story_id == "AX-1-01"
                    and action_kind == "story-verification"
                    and marker not in injected_conductor
                ):
                    crash_tick(action_kind, "after-claim")
                    crash_tick(action_kind, "after-receipt")
                    failed_delivery_refusal = (
                        delivery.build_program_delivery_preview(
                            root,
                            run_id,
                            driver_config=config,
                            now=issued,
                        )
                    )
                    assert not failed_delivery_refusal["applicable"]
                    injected_conductor.add(marker)
                elif (
                    story_id == "AX-1-02"
                    and action_kind == "debate-rebuttal"
                    and marker not in injected_conductor
                ):
                    crash_tick(action_kind, "after-claim")
                    crash_tick(action_kind, "after-receipt")
                    injected_conductor.add(marker)
                elif (
                    story_id == "AX-1-02"
                    and action_kind == "architect-verdict"
                    and marker not in injected_conductor
                ):
                    crash_tick(action_kind, "after-claim")
                    crash_tick(action_kind, "after-receipt")
                    injected_conductor.add(marker)
                conductor.tick_program(
                    root,
                    run_id,
                    driver_config=config,
                    adapters=adapters,
                    now=issued,
                )
            raise AssertionError(
                "story did not certify: {}".format(story_id)
            )

        def claim_and_complete(category, subject, key, receipt_character):
            preview = authority.build_program_claim_preview(
                root,
                run_id,
                category=category,
                subject=subject,
                idempotency_key=key,
                reason="Reserve the exact exit-exam refusal specimen.",
                now=issued,
                driver_config=config,
            )
            assert preview["applicable"], preview["issues"]
            claimed = authority.apply_program_claim(
                root,
                preview,
                claim_token=preview["claim_token"],
                now=issued,
                driver_config=config,
            )
            claim = claimed["claim"]
            completion = authority.build_program_completion_preview(
                root,
                run_id,
                claim_id=claim["claim_id"],
                result="succeeded",
                receipt_hash="sha256:" + (receipt_character * 64),
                reason="Complete the exact exit-exam refusal specimen.",
                now=issued,
            )
            assert completion["applicable"], completion["issues"]
            authority.apply_program_completion(
                root,
                completion,
                completion_token=completion["completion_token"],
                now=issued,
            )
            return claim

        def record_blocking_obligation():
            decision_hash = "sha256:" + ("d" * 64)
            item = {
                "id": "blocking-exam-obligation",
                "kind": "technical-debt",
                "statement": "This planted blocking debt must stop delivery.",
                "priority": "high",
                "blocking": True,
                "accountable_role": "implementer",
                "target": "AX-1-01",
                "citations": ["evidence:planted"],
                "acceptance": "The refusal is observed and the debt is waived.",
                "state": "open",
            }
            item_hash = authority._sha({
                "decision_hash": decision_hash,
                "obligation": item,
            })
            claim = claim_and_complete(
                "obligation-record",
                {
                    "kind": "program-obligation",
                    "id": item["id"],
                    "hash": item_hash,
                    "phase": 1,
                    "story": "AX-1-01",
                },
                "exam/blocking-obligation",
                "e",
            )
            authority.record_program_obligation(
                root,
                run_id,
                claim_id=claim["claim_id"],
                decision_hash=decision_hash,
                obligation=item,
                now=issued,
            )
            refused = delivery.build_program_delivery_preview(
                root,
                run_id,
                driver_config=config,
                now=issued,
            )
            assert not refused["applicable"], refused
            assert "blocking-obligation-open" in {
                issue["code"] for issue in refused["issues"]
            }
            red["blocking-obligation"] = [
                issue["code"] for issue in refused["issues"]
            ]
            disposition = {
                "obligation_id": item["id"],
                "from_state": "open",
                "to_state": "waived",
                "actor": "phase-26-exam",
                "authority": "exit-exam-fixture",
                "reason": "The planted refusal has been observed.",
                "replacement_id": None,
            }
            claim = claim_and_complete(
                "obligation-disposition",
                {
                    "kind": "program-obligation-disposition",
                    "id": item["id"],
                    "hash": authority._sha(disposition),
                    "phase": 1,
                    "story": "AX-1-01",
                },
                "exam/dispose-blocking-obligation",
                "f",
            )
            authority.dispose_program_obligation(
                root,
                run_id,
                claim_id=claim["claim_id"],
                obligation_id=disposition["obligation_id"],
                to_state=disposition["to_state"],
                actor=disposition["actor"],
                authority=disposition["authority"],
                reason=disposition["reason"],
                replacement_id=disposition["replacement_id"],
                now=issued,
            )

        remote_divergence_proved = False

        def plant_remote_divergence():
            current = run(
                ["git", "--git-dir", remote, "rev-parse", "main"],
                cwd=temporary,
            ).stdout.strip()
            tree = run(
                [
                    "git",
                    "--git-dir",
                    remote,
                    "rev-parse",
                    "{}^{{tree}}".format(current),
                ],
                cwd=temporary,
            ).stdout.strip()
            environment = dict(os.environ)
            environment.update({
                "GIT_AUTHOR_NAME": "Divergence Fixture",
                "GIT_AUTHOR_EMAIL": "divergence@example.test",
                "GIT_COMMITTER_NAME": "Divergence Fixture",
                "GIT_COMMITTER_EMAIL": "divergence@example.test",
                "GIT_AUTHOR_DATE": issued,
                "GIT_COMMITTER_DATE": issued,
            })
            divergent = run(
                [
                    "git",
                    "--git-dir",
                    remote,
                    "commit-tree",
                    tree,
                    "-p",
                    current,
                ],
                cwd=temporary,
                input_text="planted remote divergence\n",
                env=environment,
            ).stdout.strip()
            run(
                [
                    "git",
                    "--git-dir",
                    remote,
                    "update-ref",
                    "refs/heads/main",
                    divergent,
                    current,
                ],
                cwd=temporary,
            )
            return current, divergent

        def crash_delivery_tick(delivery_id, action_kind, boundary):
            def hook(name, detail):
                if (
                    name == boundary
                    and detail.get("action_kind") == action_kind
                ):
                    raise RuntimeError(
                        "planted delivery {} {}".format(
                            action_kind, boundary
                        )
                    )

            try:
                delivery.tick_program_delivery(
                    root,
                    run_id,
                    delivery_id,
                    driver_config=config,
                    now=issued,
                    boundary_hook=hook,
                )
            except RuntimeError as exc:
                assert "planted delivery" in str(exc)
                crash_counts["delivery"] += 1
                return
            raise AssertionError(
                "delivery boundary did not fire: {} {}".format(
                    action_kind, boundary
                )
            )

        deliveries = []
        delivery_crash_kinds = {
            "integration",
            "evidence",
            "story-complete",
            "phase-advance",
            "commit",
            "push",
        }
        injected_delivery = set()

        def deliver_story(story_id):
            nonlocal remote_divergence_proved
            preview = delivery.build_program_delivery_preview(
                root, run_id, driver_config=config, now=issued
            )
            assert preview["applicable"], preview["issues"]
            assert preview["binding"]["story"] == story_id
            frontier = delivery.start_program_delivery(
                root,
                preview,
                delivery_token=preview["delivery_token"],
                driver_config=config,
            )
            delivery_id = frontier["delivery_id"]
            deliveries.append((story_id, delivery_id, preview))
            for expected in [
                action["kind"] for action in preview["actions"]
            ]:
                if (
                    expected in delivery_crash_kinds
                    and expected not in injected_delivery
                ):
                    crash_delivery_tick(
                        delivery_id, expected, "after-claim"
                    )
                    if expected == "push" and not remote_divergence_proved:
                        prior, divergent = plant_remote_divergence()
                        red["remote-diverged"] = expect_error(
                            lambda: delivery.tick_program_delivery(
                                root,
                                run_id,
                                delivery_id,
                                driver_config=config,
                                now=issued,
                            ),
                            ["diverged", "remote"],
                        )
                        run(
                            [
                                "git",
                                "--git-dir",
                                remote,
                                "update-ref",
                                "refs/heads/main",
                                prior,
                                divergent,
                            ],
                            cwd=temporary,
                        )
                        remote_divergence_proved = True
                    crash_delivery_tick(
                        delivery_id, expected, "after-effect"
                    )
                    crash_delivery_tick(
                        delivery_id, expected, "after-receipt"
                    )
                    injected_delivery.add(expected)
                recovered = delivery.tick_program_delivery(
                    root,
                    run_id,
                    delivery_id,
                    driver_config=config,
                    now=issued,
                )
                assert recovered["action"]["kind"] == expected, recovered
            replayed = delivery.replay_program_delivery(
                root, run_id, delivery_id, now=issued
            )
            assert replayed["complete"], replayed
            assert len(replayed["receipts"]) == len(preview["actions"])
            assert len({
                item["receipt_hash"] for item in replayed["receipts"]
            }) == len(replayed["receipts"])
            return replayed

        initial_commit_count = int(
            git(root, "rev-list", "--count", "HEAD").stdout.strip()
        )
        conduct_story("AX-1-01")
        assert driver.packets
        for work_packet in driver.packets:
            assert work_packet["knowledge"]["kind"] == "delivery-workbench-knowledge-packet"
            recall = work_packet["memory_recall"]
            assert recall["kind"] == "delivery-workbench-memory-recall"
            assert recall["source_revision"]
            assert recall["used_bytes"] > 0
        program_events = authority._events(
            authority._run_dir(root, run_id), run_id
        )
        built_events = [
            item for item in program_events
            if item["event"] == "memory-recall-built"
            and item["detail"]["source_revision"]
            == driver.packets[0]["memory_recall"]["source_revision"]
        ]
        attached_events = [
            item for item in program_events
            if item["event"] == "memory-recall-attached"
        ]
        assert {item["detail"]["audience"] for item in built_events} == {
            "coordinator", "implementer", "verifier", "judge", "shared",
        }
        first_agent_claim_seq = next(
            item["seq"] for item in program_events
            if item["event"] == "claim_reserved"
            and item["detail"]["category"] == "agent"
        )
        assert max(item["seq"] for item in built_events) < first_agent_claim_seq
        dispatch_by_claim = {
            item["detail"]["claim_id"]: item for item in program_events
            if item["event"] == "claim_dispatched"
        }
        assert attached_events
        assert all(
            item["seq"] < dispatch_by_claim[item["detail"]["claim_id"]]["seq"]
            for item in attached_events
            if item["detail"]["claim_id"] in dispatch_by_claim
        )
        story_scope = (
            root / ".git" / "pmo-programs" / "runs" / run_id
            / "memory" / "scopes"
        )
        assert list(story_scope.glob("scope-*/manifest.json"))
        assert failed_delivery_refusal is not None
        red["failed-or-dissenting-verdict"] = [
            issue["code"]
            for issue in failed_delivery_refusal["issues"]
        ]

        first_conductor = conductor.replay_program_conductor(
            root, run_id, now=issued
        )
        story_a_verdicts = sorted(
            [
                item
                for item in first_conductor["receipts"]
                if item["action_kind"] == "story-verification"
                and item["story"] == "AX-1-01"
            ],
            key=lambda item: item["attempt"],
        )
        assert [
            (item["attempt"], item["result"])
            for item in story_a_verdicts
        ] == [(1, "needs-repair"), (2, "pass")]
        assert len([
            item
            for item in first_conductor["receipts"]
            if item["action_kind"] == "repair"
            and item["story"] == "AX-1-01"
        ]) == 1

        failed_artifact = next(
            item
            for item in story_a_verdicts[0]["artifacts"]
            if item["name"] == "issued-verdict"
        )
        fresh_artifact = next(
            item
            for item in story_a_verdicts[1]["artifacts"]
            if item["name"] == "issued-verdict"
        )
        failed_verdict = validate_verdict_document(json.loads(
            conductor._artifact_content(
                root, run_id, failed_artifact
            )
        ))
        fresh_verdict = validate_verdict_document(json.loads(
            conductor._artifact_content(
                root, run_id, fresh_artifact
            )
        ))
        rubric = compile_rubric(root, "story-quality")
        stale_issues = verdict_freshness_issues(
            failed_verdict,
            fresh_verdict["subject"],
            rubric,
            issued,
        )
        assert stale_issues, stale_issues
        red["stale-verdict"] = [
            issue["code"] for issue in stale_issues
        ]

        check_receipt = next(
            item
            for item in first_conductor["receipts"]
            if item["action_kind"] == "check"
            and item["story"] == "AX-1-01"
        )
        fact_artifact = next(
            item
            for item in check_receipt["artifacts"]
            if item["artifact_kind"] == "mechanical-fact"
        )
        fact = json.loads(
            conductor._artifact_content(
                root, run_id, fact_artifact
            )
        )
        assert validate_mechanical_fact(fact) == fact
        forged = copy.deepcopy(fact)
        forged["result"] = (
            "fail" if forged["result"] == "pass" else "pass"
        )
        red["forged-mechanical-fact"] = expect_error(
            lambda: validate_mechanical_fact(forged),
            ["hash", "changed", "payload"],
        )

        record_blocking_obligation()
        dirty = root / "unexpected-dirty-file.txt"
        write_text(dirty, "planted dirty repository\n")
        dirty_preview = delivery.build_program_delivery_preview(
            root, run_id, driver_config=config, now=issued
        )
        assert not dirty_preview["applicable"], dirty_preview
        assert "repository-not-clean" in {
            issue["code"] for issue in dirty_preview["issues"]
        }
        red["dirty-repository"] = [
            issue["code"] for issue in dirty_preview["issues"]
        ]
        dirty.unlink()
        deliver_story("AX-1-01")

        conduct_story("AX-1-02")
        second_conductor = conductor.replay_program_conductor(
            root, run_id, now=issued
        )
        council_receipt = next(
            item
            for item in second_conductor["receipts"]
            if item["action_kind"] == "council-decision"
            and item["story"] == "AX-1-02"
        )
        council_artifact = next(
            item
            for item in council_receipt["artifacts"]
            if item["name"] == "issued-decision"
        )
        decision = json.loads(
            conductor._artifact_content(
                root, run_id, council_artifact
            )
        )
        assert decision["dissent"], decision
        assert decision["authority"]["kind"] in {"rule", "judge"}, decision
        if decision["authority"]["kind"] == "judge":
            assert (
                decision["authority"]["decider_seat"]
                == decision["chair_seat"]
            )
        assert decision["obligations"] == [obligation]
        assert len([
            item
            for item in second_conductor["receipts"]
            if item["action_kind"] == "meta-verdict-issuance"
            and item["story"] == "AX-1-02"
        ]) == 1
        architect = next(
            item
            for item in second_conductor["receipts"]
            if item["action_kind"] == "architect-verdict"
            and item["story"] == "AX-1-02"
        )
        assert architect["result"] == "approve"
        assert any(
            item["id"] == obligation["id"]
            and not item["blocking"]
            for item in second_conductor["authority"]["open_obligations"]
        )
        deliver_story("AX-1-02")

        readme = (
            root / "pm/roadmap/autonomous/README.md"
        ).read_text(encoding="utf-8")
        assert (
            "**Current phase:** [Phase 2 - Continuation]"
            "(./phase-2-continuation/current-phase-status.md)."
        ) in readme
        assert (
            root
            / "pm/roadmap/autonomous/phase-1-foundation/final-summary.md"
        ).is_file()

        conduct_story("AX-2-01")
        deliver_story("AX-2-01")
        assert injected_delivery == delivery_crash_kinds, (
            injected_delivery,
            delivery_crash_kinds,
        )

        def scope_crash(name, detail):
            if (
                name == "after-receipt"
                and detail.get("receipt_kind") == "scope-completion"
            ):
                raise RuntimeError("planted scope completion crash")

        try:
            conductor.tick_program(
                root,
                run_id,
                driver_config=config,
                adapters=adapters,
                now=issued,
                boundary_hook=scope_crash,
            )
        except RuntimeError as exc:
            assert "scope completion" in str(exc)
            crash_counts["conductor"] += 1
        else:
            raise AssertionError("scope-completion boundary did not fire")
        completed = conductor.tick_program(
            root,
            run_id,
            driver_config=config,
            adapters=adapters,
            now=issued,
        )
        assert completed["action"]["kind"] == "scope-completion"
        assert completed["terminal"]

        final_conductor = conductor.replay_program_conductor(
            root, run_id, now=issued
        )
        final_authority = authority.replay_program(
            root, run_id, now=issued
        )
        assert final_authority["state"] == "complete"
        assert final_authority["memory_writeback"]["status"] == "persisted"
        writeback_files = sorted(
            (authority._run_dir(root, run_id) / "memory" / "writebacks").glob("*.json")
        )
        assert len(writeback_files) == 1
        writeback = json.loads(writeback_files[0].read_text(encoding="utf-8"))
        assert writeback["terminal_state"] == "complete"
        assert writeback["memory_state"] == "confirmed"
        assert writeback["story_ids"] == ["AX-1-01", "AX-1-02", "AX-2-01"]
        assert set(writeback["recalled_memory_ids"]) == {
            item["recall_id"] for item in final_authority["memory_recalls"]
        }
        assert writeback["changed_files"]
        assert isinstance(writeback["accepted_lesson_hashes"], list)
        assert not any(
            key in writeback
            for key in ("prompt", "transcript", "tool_output", "credentials", "thinking")
        )
        replayed_terminal = conductor.tick_program(
            root, run_id, driver_config=config, adapters=adapters, now=issued
        )
        assert replayed_terminal["terminal"]
        assert len(list(writeback_files[0].parent.glob("*.json"))) == 1
        assert final_authority["selected_stories"] == [
            "AX-1-01",
            "AX-1-02",
            "AX-2-01",
        ]
        assert (
            int(git(root, "rev-list", "--count", "HEAD").stdout.strip())
            == initial_commit_count + 3
        )
        assert git(root, "status", "--porcelain").stdout == ""
        local_head = git(root, "rev-parse", "HEAD").stdout.strip()
        remote_head = run(
            ["git", "--git-dir", remote, "rev-parse", "main"],
            cwd=temporary,
        ).stdout.strip()
        assert local_head == remote_head

        claim_ids = [
            item["claim_id"] for item in final_authority["claims"]
        ]
        dispatch_ids = [
            item["operation_id"] for item in final_authority["dispatches"]
        ]
        receipt_hashes = final_conductor["receipt_hashes"]
        assert len(claim_ids) == len(set(claim_ids))
        assert len(dispatch_ids) == len(set(dispatch_ids))
        assert len(receipt_hashes) == len(set(receipt_hashes))
        delivery_categories = [
            item["category"]
            for item in final_authority["claims"]
            if str(item["idempotency_key"]).startswith(
                "program-delivery/"
            )
        ]
        for category in (
            "integration",
            "evidence",
            "story-complete",
            "commit",
            "push",
        ):
            assert delivery_categories.count(category) == 3, (
                category,
                delivery_categories,
            )
        assert delivery_categories.count("phase-advance") == 1

        # Canonical view/tail equality across installed CLI, MCP, direct HTTP,
        # Workbench, and a real finite SSE response.
        expected_view = surface.build_program_view(root, run_id)
        cli_view = json.loads(
            run(
                [
                    dw,
                    "--root",
                    root,
                    "program",
                    "show",
                    run_id,
                    "--json",
                ],
                cwd=root,
            ).stdout
        )
        mcp_view = call_mcp(
            mcp, root, "dw_program_show", {"run_id": run_id}
        )
        status, http_view = workbench.handle_api(
            root, "/api/programs/{}/view".format(run_id), {}
        )
        assert status == 200
        for document in (cli_view, mcp_view, http_view["data"]):
            assert (
                surface.document_bytes(document)
                == surface.document_bytes(expected_view)
            )
        expected_tail = surface.tail_program_events(
            root, run_id, after_seq=0, limit=1_000
        )
        cli_tail = json.loads(
            run(
                [
                    dw,
                    "--root",
                    root,
                    "program",
                    "tail",
                    run_id,
                    "--after",
                    "0",
                    "--json",
                ],
                cwd=root,
            ).stdout
        )
        mcp_tail = call_mcp(
            mcp,
            root,
            "dw_program_tail",
            {"run_id": run_id, "after": 0, "limit": 1_000},
        )
        status, http_tail = workbench.handle_api(
            root,
            "/api/programs/{}/tail".format(run_id),
            {"after": ["0"], "limit": ["1000"]},
        )
        assert status == 200
        assert cli_tail == mcp_tail == http_tail["data"] == expected_tail

        server = ThreadingHTTPServer(
            ("127.0.0.1", 0),
            workbench.create_handler(root, None),
        )
        thread = threading.Thread(
            target=server.serve_forever, daemon=True
        )
        thread.start()
        connection = http.client.HTTPConnection(
            "127.0.0.1", server.server_address[1], timeout=10
        )
        connection.request(
            "GET",
            "/api/programs/{}/events?from=0&follow=0".format(run_id),
        )
        response = connection.getresponse()
        body = response.read().decode("utf-8")
        connection.close()
        assert response.status == 200
        frames = parse_sse(body)
        snapshot_sequence, snapshot = frames[0]
        assert snapshot_sequence == 0
        assert snapshot["run_id"] == run_id
        assert snapshot["ledger_head"] == expected_tail["ledger_head"]
        assert snapshot["event_count"] == expected_tail["head_seq"]
        ledger_frames = frames[1:]
        assert [
            item for _sequence, item in ledger_frames
        ] == expected_tail["events"]
        assert [
            sequence for sequence, _item in ledger_frames
        ] == [
            item["seq"] for item in expected_tail["events"]
        ]
        server.shutdown()
        server.server_close()
        server = None

        # A separate baseline clone proves budget/capability/revocation
        # refusals without contaminating the completed green authority.
        red_root = temporary / "authority-red"
        run(["git", "clone", "-q", baseline_remote, red_root], cwd=temporary)
        assert (
            red_root / "pm/programs/autonomous-exit.json"
        ).is_file(), "authority refusal clone did not check out main"
        git(red_root, "config", "user.name", "Authority Red Exam")
        git(red_root, "config", "user.email", "authority-red@example.test")
        write_driver_config(red_root, driver_document())
        red_config = load_driver_config(red_root)

        def start_red(intent, budget_overrides):
            red_plan = authority.build_program_start_plan(
                red_root,
                "autonomous-exit",
                mode="continuous",
                operator="phase-26-red",
                approval_reason="Exercise a bounded refusal.",
                intent_id=intent,
                budgets=budget_overrides,
                issued_at=issued,
                expires_at=expires,
                remote="origin",
                remote_ref="refs/remotes/origin/main",
                driver_config=red_config,
            )
            assert red_plan["applicable"], red_plan["issues"]
            return authority.start_program(
                red_root,
                red_plan,
                start_token=red_plan["start_token"],
                now=issued,
                driver_config=red_config,
            )

        def red_subject(story, phase, kind="story", identifier=None):
            return {
                "kind": kind,
                "id": identifier or story,
                "hash": authority._sha({
                    "kind": kind,
                    "story": story,
                    "phase": phase,
                    "id": identifier or story,
                }),
                "phase": phase,
                "story": story,
            }

        def red_claim_complete(run_projection, category, subject, key):
            preview = authority.build_program_claim_preview(
                red_root,
                run_projection["run_id"],
                category=category,
                subject=subject,
                idempotency_key=key,
                reason="Reserve a bounded red-matrix claim.",
                now=issued,
                driver_config=red_config,
            )
            assert preview["applicable"], preview["issues"]
            claimed = authority.apply_program_claim(
                red_root,
                preview,
                claim_token=preview["claim_token"],
                now=issued,
                driver_config=red_config,
            )
            completion = authority.build_program_completion_preview(
                red_root,
                run_projection["run_id"],
                claim_id=claimed["claim"]["claim_id"],
                result="succeeded",
                receipt_hash=authority._sha({"red": key}),
                reason="Complete the bounded red-matrix claim.",
                now=issued,
            )
            assert completion["applicable"], completion["issues"]
            authority.apply_program_completion(
                red_root,
                completion,
                completion_token=completion["completion_token"],
                now=issued,
            )

        phase_budget = start_red(
            "phase-round-integration-red",
            {
                "max_phases": 1,
                "max_stories": 3,
                "max_debate_rounds": 1,
                "max_loop_rounds": 1,
                "max_integrations": 1,
                "max_pushes": 1,
            },
        )
        red_claim_complete(
            phase_budget,
            "selection",
            red_subject("AX-1-01", 1),
            "red/select-phase-one",
        )
        phase_refusal = authority.build_program_claim_preview(
            red_root,
            phase_budget["run_id"],
            category="selection",
            subject=red_subject("AX-2-01", 2),
            idempotency_key="red/select-phase-two",
            reason="Exhaust the one-phase grant.",
            now=issued,
            driver_config=red_config,
        )
        assert not phase_refusal["applicable"]
        red["phase-budget-exhausted"] = [
            item["code"] for item in phase_refusal["issues"]
        ]
        for category, label in (
            ("debate-round", "round"),
            ("integration", "integration"),
            ("push", "push"),
        ):
            red_claim_complete(
                phase_budget,
                category,
                red_subject("AX-1-01", 1),
                "red/{}/one".format(label),
            )
            refused = authority.build_program_claim_preview(
                red_root,
                phase_budget["run_id"],
                category=category,
                subject=red_subject("AX-1-01", 1),
                idempotency_key="red/{}/two".format(label),
                reason="Exhaust the bounded {} counter.".format(label),
                now=issued,
                driver_config=red_config,
            )
            assert not refused["applicable"], refused
            red["{}-budget-exhausted".format(label)] = [
                item["code"] for item in refused["issues"]
            ]
        denied = authority.build_program_claim_preview(
            red_root,
            phase_budget["run_id"],
            category="notification",
            subject=red_subject("AX-1-01", 1),
            idempotency_key="red/no-notification-capability",
            reason="No notification authority was granted.",
            now=issued,
            driver_config=red_config,
        )
        assert not denied["applicable"], denied
        red["missing-capability"] = [
            item["code"] for item in denied["issues"]
        ]
        revoke = authority.build_program_control_preview(
            red_root,
            phase_budget["run_id"],
            action="revoke",
            decision="approve",
            reason="End the red authority.",
            now=issued,
        )
        assert revoke["applicable"], revoke["issues"]
        authority.apply_program_control(
            red_root,
            revoke,
            control_token=revoke["control_token"],
            now=issued,
            driver_config=red_config,
        )
        revoked_claim = authority.build_program_claim_preview(
            red_root,
            phase_budget["run_id"],
            category="selection",
            subject=red_subject("AX-1-02", 1),
            idempotency_key="red/after-revoke",
            reason="Revoked authority must reserve nothing.",
            now=issued,
            driver_config=red_config,
        )
        assert not revoked_claim["applicable"], revoked_claim
        red["grant-revoked"] = [
            item["code"] for item in revoked_claim["issues"]
        ]

        story_budget = start_red(
            "story-budget-red",
            {"max_phases": 2, "max_stories": 1},
        )
        red_claim_complete(
            story_budget,
            "selection",
            red_subject("AX-1-01", 1),
            "red/story-one",
        )
        story_refusal = authority.build_program_claim_preview(
            red_root,
            story_budget["run_id"],
            category="selection",
            subject=red_subject("AX-1-02", 1),
            idempotency_key="red/story-two",
            reason="Exhaust the one-story grant.",
            now=issued,
            driver_config=red_config,
        )
        assert not story_refusal["applicable"], story_refusal
        red["story-budget-exhausted"] = [
            item["code"] for item in story_refusal["issues"]
        ]

        # A separate Story-B frontier proves architect veto before integration.
        veto_root = temporary / "architect-veto"
        run(["git", "clone", "-q", baseline_remote, veto_root], cwd=temporary)
        assert (
            veto_root / "pm/programs/autonomous-exit.json"
        ).is_file(), "architect veto clone did not check out main"
        git(veto_root, "config", "user.name", "Architect Veto Exam")
        git(veto_root, "config", "user.email", "veto@example.test")
        phase_status = (
            veto_root
            / "pm/roadmap/autonomous/phase-1-foundation/"
            "current-phase-status.md"
        )
        text = phase_status.read_text(encoding="utf-8")
        text = text.replace(
            "| AX-1-01 | Repair an independently rejected candidate | in-progress | [story-01-repair](./story-01-repair.md) | - |",
            "| AX-1-01 | Repair an independently rejected candidate | done | [story-01-repair](./story-01-repair.md) | [evidence-story-01](./evidence-story-01.md) |",
        ).replace(
            "| AX-1-02 | Reach a governed council decision | backlog |",
            "| AX-1-02 | Reach a governed council decision | in-progress |",
        )
        phase_status.write_text(text, encoding="utf-8")
        story_a = (
            veto_root
            / "pm/roadmap/autonomous/phase-1-foundation/"
            "story-01-repair.md"
        )
        story_a.write_text(
            story_a.read_text(encoding="utf-8").replace(
                "- **Status:** in-progress",
                "- **Status:** done",
            ),
            encoding="utf-8",
        )
        story_b = (
            veto_root
            / "pm/roadmap/autonomous/phase-1-foundation/"
            "story-02-council.md"
        )
        story_b.write_text(
            story_b.read_text(encoding="utf-8").replace(
                "- **Status:** backlog",
                "- **Status:** in-progress",
            ),
            encoding="utf-8",
        )
        write_text(
            veto_root
            / "pm/roadmap/autonomous/phase-1-foundation/"
            "evidence-story-01.md",
            """# Evidence - AX-1-01

- **Story:** AX-1-01 - Repair an independently rejected candidate
- **Status:** done
- **Date:** 2026-07-23

## Proof

- deterministic prerequisite fixture
""",
        )
        git(veto_root, "add", "pm/roadmap")
        git(
            veto_root,
            "-c",
            "core.hooksPath=/dev/null",
            "commit",
            "-qm",
            "Prepare architect veto frontier",
        )
        write_driver_config(veto_root, driver_document())
        veto_config = load_driver_config(veto_root)
        veto_plan = authority.build_program_start_plan(
            veto_root,
            "autonomous-exit",
            mode="continuous",
            operator="phase-26-veto",
            approval_reason="Prove the architect veto stop.",
            intent_id="architect-veto-red",
            issued_at=issued,
            expires_at=expires,
            remote="origin",
            remote_ref="refs/remotes/origin/main",
            driver_config=veto_config,
        )
        assert veto_plan["applicable"], veto_plan["issues"]
        veto_run = authority.start_program(
            veto_root,
            veto_plan,
            start_token=veto_plan["start_token"],
            now=issued,
            driver_config=veto_config,
        )
        veto_driver = ExamDriver(architect_veto=True)
        veto_result = conductor.supervise_program(
            veto_root,
            veto_run["run_id"],
            max_ticks=80,
            driver_config=veto_config,
            adapters={
                "fixture": veto_driver,
                "claude-exec": veto_driver,
                "pi-exec": veto_driver,
            },
            now=issued,
        )
        assert (
            veto_result["state"],
            veto_result["stop"],
        ) == ("stopped", "architect-veto"), veto_result
        veto_replay = conductor.replay_program_conductor(
            veto_root, veto_run["run_id"], now=issued
        )
        assert not any(
            item["category"] in {
                "integration",
                "story-complete",
                "phase-advance",
            }
            for item in veto_replay["authority"]["claims"]
        )
        red["architect-veto"] = veto_result["stop"]

        # The same installed payload in a separate ordinary consumer has no
        # program policy, store, process, observer, notification store, poller,
        # network call, route detour, or required setup.
        vanilla.mkdir()
        git(vanilla, "init", "-q", "-b", "main")
        git(vanilla, "config", "user.name", "Vanilla Consumer")
        git(vanilla, "config", "user.email", "vanilla@example.test")
        run(
            [
                global_dw,
                "install",
                vanilla,
                "--project-name",
                "Vanilla Consumer",
                "--project-slug",
                "vanilla",
                "--project-prefix",
                "VAN",
            ],
            cwd=temporary,
        )
        vanilla_dw = vanilla / ".githooks/dw"
        status_result = run(
            [vanilla_dw, "--root", vanilla, "status", "vanilla", "--json"],
            cwd=vanilla,
            check=False,
        )
        assert status_result.returncode in (0, 1), status_result.stderr
        vanilla_status = json.loads(status_result.stdout)
        step_result = run(
            [vanilla_dw, "--root", vanilla, "step", "vanilla", "--json"],
            cwd=vanilla,
            check=False,
        )
        assert step_result.returncode in (0, 1), step_result.stderr
        vanilla_step = json.loads(step_result.stdout)
        next_result = run(
            [vanilla_dw, "--root", vanilla, "next", "vanilla", "--json"],
            cwd=vanilla,
            check=False,
        )
        assert next_result.returncode in (0, 2), next_result.stderr
        json.loads(next_result.stdout)
        simulation = json.loads(
            run(
                [
                    vanilla_dw,
                    "--root",
                    vanilla,
                    "orchestration",
                    "simulate",
                    "research-build-review",
                    "--json",
                ],
                cwd=vanilla,
            ).stdout
        )
        assert simulation["starts_work"] is False
        gate = run(
            [vanilla_dw, "--root", vanilla, "gate", "--porcelain"],
            cwd=vanilla,
            check=False,
        )
        assert gate.returncode in (0, 1), gate.stderr
        vanilla_programs = surface.program_summary_inventory(vanilla)
        assert vanilla_programs["programs"] == []
        assert vanilla_programs["runs"] == []
        for key in (
            "starts_work",
            "writes_events",
            "creates_grant",
            "creates_program_store",
            "starts_process",
            "starts_stream",
            "starts_poller",
            "sends_notifications",
        ):
            assert vanilla_programs[key] is False, (
                key,
                vanilla_programs,
            )
        status, projects_api = workbench.handle_api(
            vanilla, "/api/projects", {}
        )
        assert status == 200 and projects_api["data"]["projects"]
        status, programs_api = workbench.handle_api(
            vanilla, "/api/programs", {}
        )
        assert status == 200
        assert programs_api["data"] == vanilla_programs
        status, studio_api = workbench.handle_api(
            vanilla, "/api/program-studio", {}
        )
        assert status == 200
        assert studio_api["data"]["empty"]
        assert studio_api["data"]["default_route"] == "#/"
        assert not studio_api["data"]["background_polling"]
        before_setup = file_snapshot(vanilla)
        status, setup_api = workbench.handle_api(
            vanilla, "/api/delivery-setup", {"project": ["vanilla"]}
        )
        assert status == 200
        setup = setup_api["data"]
        assert setup["kind"] == "delivery-workbench-delivery-setup"
        assert setup["delivery_scope"]["selected_project"] == "vanilla"
        assert [item["id"] for item in setup["choices"]] == [
            "roadmap", "bounded", "program",
        ]
        for key in (
            "starts_work", "writes_policy", "writes_roadmap",
            "writes_run_state", "creates_grant", "starts_process",
            "starts_observer", "sends_notification", "uses_network",
        ):
            assert setup[key] is False, (key, setup)
        setup_result = run(
            [
                vanilla_dw, "--root", vanilla,
                "setup", "vanilla", "--technical",
            ],
            cwd=vanilla,
            check=False,
        )
        assert setup_result.returncode in (0, 1), setup_result.stderr
        for choice in setup["choices"]:
            assert "{} — {}".format(
                choice["label"], choice["readiness"]
            ) in setup_result.stdout
        assert "Technical details:" in setup_result.stdout
        assert before_setup == file_snapshot(vanilla)
        notifications = build_notifications(vanilla)
        assert notifications["notifications"] == []
        assert not (vanilla / ".git/pmo-programs").exists()
        assert not (vanilla / ".git/pmo-notifications").exists()
        assert not (vanilla / "pm/programs").exists()
        assert not (vanilla / "pm/workflows").exists()
        assert not (vanilla / "pm/organizations").exists()
        assert not (vanilla / "pm/rubrics").exists()
        assert vanilla_status["kind"] == "delivery-workbench-status"
        assert vanilla_step["kind"] == "delivery-workbench-step"
        assert mcpserver.TOOLS["dw_status"]["inputSchema"][
            "additionalProperties"
        ] is False

        decision_documents = read_decision_bases(
            root / ".git" / "pmo-programs" / "runs" / run_id
        )
        decision_kinds = {item["decision_kind"] for item in decision_documents}
        decision_authorities = {item["basis_type"] for item in decision_documents}
        assert {"scheduler", "verdict", "council", "terminal"} <= decision_kinds
        assert {"mechanical", "agent-reported", "panel-derived"} <= decision_authorities
        assert {
            item["decision_id"] for item in decision_documents
        } == {
            item["decision_id"] for item in final_authority["decision_bases"]
        }
        assert any(item["dissent_refs"] for item in decision_documents)

        phase27_delivery = {
            "review_results": [
                item["result"] for item in story_a_verdicts
            ],
            "repair_rounds": len([
                item
                for item in first_conductor["receipts"]
                if item["action_kind"] == "repair"
                and item["story"] == "AX-1-01"
            ]),
            "governed_decision": {
                "result": council_receipt["result"],
                "dissent_preserved": bool(decision["dissent"]),
                "authority": decision["authority"]["kind"],
                "obligations": [
                    item["id"] for item in decision["obligations"]
                ],
            },
            "answers": expected_view["live_progress"]["answers"],
            "progress": expected_view["live_progress"]["progress"],
            "team": expected_view["live_progress"]["team"],
            "review": expected_view["live_progress"]["review"],
            "limits": expected_view["live_progress"]["limits"],
            "permission": expected_view[
                "bounded_actions"
            ]["permission"],
            "usage": expected_view["bounded_actions"]["usage"],
        }
        phase27_recovery = {
            "conductor_crashes": crash_counts["conductor"],
            "delivery_crashes": crash_counts["delivery"],
            "saved_state": expected_view["live_progress"]["recovery"],
            "ledger_events": final_authority["event_count"],
            "unique_claim_ids": len(claim_ids) == len(set(claim_ids)),
            "unique_dispatch_ids": (
                len(dispatch_ids) == len(set(dispatch_ids))
            ),
            "unique_receipt_hashes": (
                len(receipt_hashes) == len(set(receipt_hashes))
            ),
            "no_duplicate_delivery_actions": True,
        }
        phase27_completion = {
            "state": final_authority["state"],
            "status": expected_view["live_progress"]["status"],
            "progress": expected_view["live_progress"]["progress"],
            "next_step": expected_view["live_progress"]["next_step"],
            "completed_stories": final_authority["selected_stories"],
            "completed_phases": final_authority["selected_phases"],
        }
        phase27_technical = {
            "label": "Technical details",
            "run_id": run_id,
            "grant_hash": expected_view["grant_hash"],
            "plan_hash": expected_view["plan_hash"],
            "ledger_head": expected_view["ledger_head"],
            "event_count": expected_view["event_count"],
            "generation": expected_view["generation"],
            "receipt_hashes": receipt_hashes,
            "principal_fingerprints": sorted({
                seat["principal_fingerprint"]
                for seat in plan["roster"]["seats"]
            }),
            "exact_view_parity": [
                "CLI", "MCP", "HTTP", "Workbench",
            ],
            "exact_event_parity": [
                "CLI", "MCP", "HTTP", "SSE",
            ],
            "stream_events": len(expected_tail["events"]),
        }
        output = {
            "kind": "delivery-workbench-autonomous-program-exam",
            "schema_version": 1,
            "phase27_observations": {
                "same_consumer": {
                    "installed_from_wheel": True,
                    "initial": same_consumer_initial,
                    "optional_configuration": phase27_authoring,
                },
                "bounded_decision": bounded_decision_observation,
                "stop_and_revoke": bounded_stop_observation,
                "preflight": phase27_preflight,
                "start": {
                    "separate_confirmation": True,
                    "preview_started_work": False,
                    "start_state": started["state"],
                    "run_id": run_id,
                },
                "delivery": phase27_delivery,
                "recovery": phase27_recovery,
                "completion": phase27_completion,
                "technical_details": phase27_technical,
            },
            "green": {
                "run_id": run_id,
                "state": final_authority["state"],
                "selected_stories": final_authority[
                    "selected_stories"
                ],
                "selected_phases": final_authority[
                    "selected_phases"
                ],
                "repair_rounds": 1,
                "council_dissent_preserved": bool(
                    decision["dissent"]
                ),
                "meta_audits": len([
                    item
                    for item in final_conductor["receipts"]
                    if item["action_kind"]
                    == "meta-verdict-issuance"
                ]),
                "architect_gates": len([
                    item
                    for item in final_conductor["receipts"]
                    if item["action_kind"] == "architecture-gate"
                ]),
                "open_nonblocking_obligations": [
                    item["id"]
                    for item in final_authority["open_obligations"]
                    if not item["blocking"]
                ],
                "commits": 3,
                "pushes": delivery_categories.count("push"),
                "conductor_crashes": crash_counts["conductor"],
                "delivery_crashes": crash_counts["delivery"],
                "ledger_events": final_authority["event_count"],
                "stream_events": len(expected_tail["events"]),
                "surfaces": ["CLI", "MCP", "HTTP", "Workbench", "SSE"],
            },
            "red_matrix": red,
            "provider_family_diversity": provider_diversity_observation,
            "fixture_bindings": {
                "claude": {
                    "adapter": "claude-exec",
                    "provider": "anthropic",
                    "model": "claude/sonnet",
                    "execution": "deterministic injected fixture; no credentials",
                },
                "pi": {
                    "adapter": "pi-exec",
                    "router": "openrouter",
                    "provider": "openrouter",
                    "model": "moonshot/kimi",
                    "execution": "deterministic injected fixture; no credentials",
                },
            },
            "optional_live_specimen": {
                "status": "not-run",
                "reason": (
                    "No explicit authenticated live-agent request; "
                    "variable model output is not the CI oracle."
                ),
            },
            "vanilla_consumer": {
                "status_kind": vanilla_status["kind"],
                "step_kind": vanilla_step["kind"],
                "delivery_setup_kind": setup["kind"],
                "delivery_choices": [
                    item["id"] for item in setup["choices"]
                ],
                "setup_writes": False,
                "orchestration_starts_work": simulation["starts_work"],
                "programs": 0,
                "program_store": False,
                "notification_store": False,
                "default_route": studio_api["data"]["default_route"],
                "background_polling": False,
                "ambient_network": False,
            },
            "homebrew": {
                "status": "not-applicable",
                "reason": (
                    "The macOS formula/environment lane owns Homebrew "
                    "validation; this fresh-wheel exam does not simulate it."
                ),
            },
        }
        print(json.dumps(output, sort_keys=True))
    finally:
        if server is not None:
            server.shutdown()
            server.server_close()
        if args.keep:
            print(
                "autonomous-program-packaged-exam.py: kept {}".format(
                    temporary
                ),
                file=sys.stderr,
            )
        else:
            shutil.rmtree(temporary, ignore_errors=True)


if __name__ == "__main__":
    main()
