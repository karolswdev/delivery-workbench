"""Pure, deterministic compiler from setup answers to an inert program proposal."""

from __future__ import annotations

import copy
import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from .model import DwError
from .orchestration_driver import load_driver_config, validate_driver_config
from .parse import discover_phases, discover_projects, parse_story_rows
from .programs import BUDGET_LIMITS as PROGRAM_BUDGET_LIMITS
from .programs import validate_program
from .setup_proposal import SCHEMA as PROPOSAL_SCHEMA
from .setup_proposal import canonical_json as canonical_proposal_json
from .setup_proposal import validate_proposal


def _roadmap_from_base(
    base: dict[str, object], answers: dict[str, object]
) -> dict[str, object]:
    """Scope-check the answers against the base proposal's own roadmap.

    In build mode the roadmap does not exist in the repository yet — the
    proposal is what will create it — so the conversation's draft is the
    only truthful roadmap source. The scaffold never filters or edits
    it; it only refuses scope selections the draft cannot satisfy.
    """
    scope = answers["scope"]
    project_answer = answers["project"]
    assert isinstance(scope, dict) and isinstance(project_answer, dict)
    base_project = base["project"]
    assert isinstance(base_project, dict)
    for field in ("slug", "prefix", "title"):
        if base_project[field] != project_answer[field]:
            _refuse(
                "/project/%s" % field,
                "answers do not match the base proposal's project identity",
            )
    roadmap = base["tracked_content"]["roadmap"]  # type: ignore[index]
    assert isinstance(roadmap, dict)
    phases = roadmap["phases"]
    assert isinstance(phases, list)
    known_phases = {int(item["number"]) for item in phases}  # type: ignore[index]
    known_stories = {
        str(story["id_sketch"])  # type: ignore[index]
        for item in phases
        for story in item["stories"]  # type: ignore[index]
    }
    missing_phases = sorted(set(scope["phase_numbers"]) - known_phases)
    if missing_phases:
        _refuse("/scope/phase_numbers", "the base proposal does not contain selected phases")
    missing = sorted(set(scope["story_ids"]) - known_stories)
    if missing:
        _refuse(
            "/scope/story_ids",
            "the base proposal does not contain: %s" % ", ".join(missing),
        )
    return copy.deepcopy(roadmap)


ANSWERS_SCHEMA = "delivery-workbench-program-scaffold-answers@1"
ANSWERS_KEYS = {
    "schema", "project", "scope", "profiles", "verification", "size",
    "autonomy_mode",
}
REQUIRED_ANSWERS_KEYS = ANSWERS_KEYS - {"autonomy_mode"}
PROJECT_KEYS = {"slug", "prefix", "title", "mode", "idea"}
SCOPE_KEYS = {"phase_numbers", "story_ids"}
PROFILE_KEYS = {"implementer", "verifier"}
VERIFICATION_KEYS = {"built_in_checks", "regression_argv"}
SIZE_KEYS = {"complexity", "fan_out", "repair_rounds"}
AUTONOMY_MODES = {"advisory", "checkpointed"}
COMPLEXITY_WEIGHTS = {"small": 1, "medium": 2, "large": 4}
# Only checks the conductor conducts AND the answers can fully
# configure belong here. diff-scope is the governance guard: the
# candidate diff must stay inside ordinary project paths, so a
# candidate touching pm/roadmap/ or .githooks/ fails its own check.
BUILT_IN_CHECKS = {"diff-scope"}
DIFF_SCOPE_ALLOWED_PATHS = [
    "src/**", "tests/**", "docs/**", "*.py", "*.md", "*.toml",
    "*.cfg", "*.txt", "Makefile", ".gitignore",
]
EXCLUDED_CAPABILITIES = {
    "git:commit", "git:push", "merge", "release", "deploy", "publish",
    "arbitrary-shell", "arbitrary-network", "integration:apply",
    "contract:generate", "certification:objective", "certification:verdict",
}
REQUESTED_CAPABILITIES = [
    "program:select", "agent:dispatch", "check:execute", "workspace:write",
    "verdict:issue",
    # The safest generated program still learns: certified handoffs may
    # persist bounded delivery-state-labeled lessons (WLA-30-09) without
    # gaining any integration, certification, commit, or push authority.
    "knowledge:lesson-writeback",
]
_SAFE_SLUG_RE = re.compile(r"^[a-z][a-z0-9]*(?:-[a-z0-9]+)*$")
_SAFE_PREFIX_RE = re.compile(r"^[A-Z][A-Z0-9]{0,15}$")
_SAFE_PROFILE_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}$")
_STORY_RE = re.compile(r"^[A-Z][A-Z0-9]*-\d+-\d+$")


def _ptr(parent: str, item: object) -> str:
    token = str(item).replace("~", "~0").replace("/", "~1")
    return (parent + "/" + token) if parent else ("/" + token)


def _refuse(pointer: str, message: str) -> None:
    raise DwError("%s: %s" % (pointer or "/", message))


def _object(
    value: object,
    keys: Set[str],
    pointer: str,
    *,
    required: Optional[Set[str]] = None,
) -> Dict[str, Any]:
    if not isinstance(value, dict):
        _refuse(pointer, "must be an object")
    if any(not isinstance(key, str) for key in value):
        _refuse(_ptr(pointer, "<key>"), "object keys must be strings")
    unknown = sorted(set(value) - keys)
    missing = sorted((required if required is not None else keys) - set(value))
    if unknown:
        _refuse(_ptr(pointer, unknown[0]), "unknown field")
    if missing:
        _refuse(_ptr(pointer, missing[0]), "field is required")
    return value


def _string(
    value: object,
    pointer: str,
    maximum: int,
    pattern: Optional[re.Pattern[str]] = None,
) -> str:
    if not isinstance(value, str) or not value or len(value) > maximum or "\0" in value:
        _refuse(pointer, "must be a non-empty bounded string (maximum %d characters)" % maximum)
    if pattern is not None and not pattern.fullmatch(value):
        _refuse(pointer, "must use the contracted identifier form")
    return value


def _positive_int(value: object, pointer: str, maximum: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or not 1 <= value <= maximum:
        _refuse(pointer, "must be an integer from 1 through %d" % maximum)
    return value


def _unique_list(
    value: object,
    pointer: str,
    maximum: int,
    predicate: Any,
    label: str,
) -> List[Any]:
    if (
        not isinstance(value, list) or not value or len(value) > maximum
        or any(not predicate(item) for item in value)
        or len({str(item) for item in value}) != len(value)
    ):
        _refuse(pointer, "must be a non-empty unique bounded list of %s" % label)
    return list(value)


class _DuplicateJSONKey(ValueError):
    pass


def _object_without_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise _DuplicateJSONKey("duplicate JSON object key: %s" % key)
        result[key] = value
    return result


def load_scaffold_answers(text: object) -> dict[str, object]:
    """Parse bounded UTF-8 answer JSON and normalize it fail-closed."""
    if isinstance(text, bytes):
        try:
            text = text.decode("utf-8")
        except UnicodeError as exc:
            raise DwError("/: scaffold answers must be UTF-8 JSON") from exc
    if not isinstance(text, str) or len(text.encode("utf-8")) > 262_144:
        _refuse("/", "scaffold answers JSON must be a bounded string or bytes")
    try:
        value = json.loads(
            text,
            object_pairs_hook=_object_without_duplicates,
            parse_constant=lambda token: (_ for _ in ()).throw(
                ValueError("non-finite JSON number: %s" % token)
            ),
        )
    except (_DuplicateJSONKey, ValueError, json.JSONDecodeError) as exc:
        raise DwError("/: cannot parse scaffold answers JSON: %s" % exc) from exc
    return normalize_scaffold_answers(value)


def normalize_scaffold_answers(answers: object) -> dict[str, object]:
    """Validate the closed answers object and apply the sole safe default."""
    raw = _object(
        answers, ANSWERS_KEYS, "", required=REQUIRED_ANSWERS_KEYS,
    )
    if raw["schema"] != ANSWERS_SCHEMA:
        _refuse("/schema", "unsupported scaffold answers schema")

    project = _object(raw["project"], PROJECT_KEYS, "/project")
    mode = project["mode"]
    if mode not in {"build", "maintain"}:
        _refuse("/project/mode", "must be build or maintain")
    normalized_project = {
        "slug": _string(project["slug"], "/project/slug", 128, _SAFE_SLUG_RE),
        "prefix": _string(project["prefix"], "/project/prefix", 16, _SAFE_PREFIX_RE),
        "title": _string(project["title"], "/project/title", 300),
        "mode": mode,
        "idea": _string(project["idea"], "/project/idea", 20_000),
    }

    scope = _object(raw["scope"], SCOPE_KEYS, "/scope")
    phases = _unique_list(
        scope["phase_numbers"], "/scope/phase_numbers", 100,
        lambda item: not isinstance(item, bool) and isinstance(item, int) and 0 <= item <= 9999,
        "phase numbers",
    )
    stories = _unique_list(
        scope["story_ids"], "/scope/story_ids", 2_000,
        lambda item: isinstance(item, str) and bool(_STORY_RE.fullmatch(item)),
        "story ids",
    )

    profiles = _object(raw["profiles"], PROFILE_KEYS, "/profiles")
    implementer = _string(
        profiles["implementer"], "/profiles/implementer", 128, _SAFE_PROFILE_RE,
    )
    verifier = _string(
        profiles["verifier"], "/profiles/verifier", 128, _SAFE_PROFILE_RE,
    )
    if implementer == verifier:
        _refuse("/profiles/verifier", "must name an independent verifier profile")

    verification = _object(
        raw["verification"], VERIFICATION_KEYS, "/verification",
    )
    checks = _unique_list(
        verification["built_in_checks"], "/verification/built_in_checks", 10,
        lambda item: isinstance(item, str), "built-in check names",
    )
    for index, name in enumerate(checks):
        if name not in BUILT_IN_CHECKS:
            _refuse(
                _ptr("/verification/built_in_checks", index),
                "unknown built-in check %r" % name,
            )
    regression = verification["regression_argv"]
    if regression is not None:
        regression = _unique_list(
            regression, "/verification/regression_argv", 100,
            lambda item: isinstance(item, str) and bool(item) and len(item) <= 2_000 and "\0" not in item,
            "exact argv tokens",
        )

    size = _object(raw["size"], SIZE_KEYS, "/size")
    complexity = size["complexity"]
    if complexity not in COMPLEXITY_WEIGHTS:
        _refuse("/size/complexity", "must be small, medium, or large")
    fan_out = _positive_int(size["fan_out"], "/size/fan_out", 8)
    repair_rounds = _positive_int(
        size["repair_rounds"], "/size/repair_rounds", 3,
    )
    if repair_rounds != 1:
        _refuse(
            "/size/repair_rounds",
            "this scaffold supports exactly one finite repair round",
        )

    autonomy = raw.get("autonomy_mode", "checkpointed")
    if autonomy not in AUTONOMY_MODES:
        _refuse("/autonomy_mode", "must be advisory or checkpointed")

    return {
        "schema": ANSWERS_SCHEMA,
        "project": normalized_project,
        "scope": {
            "phase_numbers": sorted(phases),
            "story_ids": sorted(stories),
        },
        "profiles": {"implementer": implementer, "verifier": verifier},
        "verification": {
            "built_in_checks": sorted(checks),
            "regression_argv": list(regression) if regression is not None else None,
        },
        "size": {
            "complexity": complexity,
            "fan_out": fan_out,
            "repair_rounds": repair_rounds,
        },
        "autonomy_mode": autonomy,
    }


def derive_program_budgets(answers: dict[str, object]) -> dict[str, int]:
    """Derive every finite budget from scope, shape, retries, and autonomy."""
    scope = answers["scope"]
    size = answers["size"]
    verification = answers["verification"]
    assert isinstance(scope, dict) and isinstance(size, dict) and isinstance(verification, dict)
    stories = len(scope["story_ids"])
    phases = len(scope["phase_numbers"])
    checks = len(verification["built_in_checks"]) + (
        1 if verification["regression_argv"] is not None else 0
    )
    if stories < 1 or phases < 1 or checks < 1:
        _refuse("/size", "cannot derive budgets without scope and verification checks")
    weight = COMPLEXITY_WEIGHTS[str(size["complexity"])]
    fan_out = int(size["fan_out"])
    repairs = int(size["repair_rounds"])
    mode_factor = 1 if answers["autonomy_mode"] == "advisory" else 2
    team_slots = 2

    # Four bounded role starts per story cover implement, initial verify, one
    # repair, and final verify. Fan-out and mode scale the execution envelope;
    # no number is copied from a sample policy.
    role_starts = stories * (team_slots + repairs + 1) * fan_out * mode_factor
    check_starts = stories * checks * (repairs + 1) * fan_out
    units = stories * weight * fan_out * (repairs + 1) * mode_factor
    budgets = {
        "max_phases": phases,
        "max_stories": stories,
        "max_child_runs": role_starts,
        "max_agent_starts": role_starts,
        "max_provider_starts": role_starts,
        "max_model_starts": role_starts,
        "max_check_starts": check_starts,
        "max_loop_rounds": stories * (repairs + 1) * mode_factor,
        "max_debate_rounds": max(1, stories * repairs),
        "max_councils": max(1, fan_out - 1),
        "max_repairs_per_story": repairs,
        "max_verdicts": stories * (repairs + 1) * fan_out,
        "max_obligations": stories * (repairs + 1),
        "max_obligation_materializations": stories * repairs,
        "max_obligation_dispositions": stories * (repairs + 1),
        "max_integrations": stories,
        "max_commits": stories,
        "max_pushes": stories,
        "max_nudges": stories * fan_out,
        "max_lessons": min(50, stories * weight),
        "max_lesson_writebacks": stories * (repairs + 1),
        "max_artifact_bytes": (
            stories * fan_out * mode_factor * (4_160_000 + (4_000_000 * checks))
        ),
        "max_tokens": units * 275_000,
        "max_observed_cost_microunits": units * 3_750_000,
        "max_wall_seconds": (
            stories * fan_out * mode_factor
            * ((1_500 * weight) + (2_400 * checks) + 7_200)
        ),
    }
    for key, value in budgets.items():
        if value > PROGRAM_BUDGET_LIMITS[key]:
            _refuse(
                "/size",
                "derived %s=%d exceeds the contracted program limit"
                % (key, value),
            )
    return budgets


def _provenance(kind: str, note: str) -> dict[str, str]:
    return {"kind": kind, "source_note": note}


def _roadmap_document(root: Path, answers: dict[str, object]) -> dict[str, object]:
    project_answer = answers["project"]
    scope = answers["scope"]
    assert isinstance(project_answer, dict) and isinstance(scope, dict)
    matches = [
        project for project in discover_projects(root.resolve())
        if project.slug == project_answer["slug"]
    ]
    if len(matches) != 1:
        _refuse(
            "/project/slug",
            "repository facts do not resolve one roadmap project; before the "
            "roadmap exists, pass the conversation's draft with --proposal "
            "so the scaffold scopes against it",
        )
    project = matches[0]
    selected_phases = set(scope["phase_numbers"])
    selected_stories = set(scope["story_ids"])
    phase_documents: list[dict[str, object]] = []
    found_stories: set[str] = set()
    for phase in discover_phases(project):
        if phase.number not in selected_phases:
            continue
        status_path = phase.path / "current-phase-status.md"
        rows = parse_story_rows(status_path)
        stories: list[dict[str, object]] = []
        for row in rows:
            if row.story_id not in selected_stories:
                continue
            found_stories.add(row.story_id)
            source = str(status_path.relative_to(root.resolve()))
            note = "Repository roadmap row %s in %s." % (row.story_id, source)
            stories.append({
                "id_sketch": row.story_id,
                "title": row.title,
                "problem": "Deliver the scoped roadmap story under the generated governed program.",
                "scope_in": [{
                    "text": "Implement only the selected roadmap story.",
                    "provenance": _provenance("repository-fact", note),
                }],
                "scope_out": [{
                    "text": "Commit, push, merge, release, deploy, and publish remain outside program authority.",
                    "provenance": _provenance("recommendation", "Safe scaffold boundary."),
                }],
                "acceptance_criteria": [{
                    "text": "Declared checks pass and an independent verifier certifies handoff readiness.",
                    "provenance": _provenance("recommendation", "Generated verification contract."),
                }],
                "dependencies": [],
                "provenance": _provenance("repository-fact", note),
            })
        if stories:
            phase_documents.append({
                "number": phase.number,
                "title": phase.path.name.replace("-", " ").title(),
                "goal": "Deliver the selected stories through a bounded implement-and-review cell.",
                "provenance": _provenance(
                    "repository-fact",
                    "Repository phase %d at %s." % (
                        phase.number, str(phase.path.relative_to(root.resolve())),
                    ),
                ),
                "stories": stories,
            })
    missing = sorted(selected_stories - found_stories)
    if missing:
        _refuse("/scope/story_ids", "repository facts do not contain: %s" % ", ".join(missing))
    missing_phases = sorted(selected_phases - {int(item["number"]) for item in phase_documents})
    if missing_phases:
        _refuse("/scope/phase_numbers", "repository facts do not contain selected phases")
    return {
        "phases": phase_documents,
        "exit_criteria": [{
            "text": "Every selected story reaches a certified handoff without program authority to commit or publish.",
            "provenance": _provenance("recommendation", "Generated safe terminal."),
        }],
    }


def _check_specs(answers: dict[str, object], suffix: str = "") -> list[dict[str, object]]:
    verification = answers["verification"]
    assert isinstance(verification, dict)
    specs: list[dict[str, object]] = []
    for name in verification["built_in_checks"]:
        runner: dict[str, object] = {
            "kind": "builtin", "name": name, "output_bytes": 100_000,
        }
        if name == "diff-scope":
            runner["allowed_paths"] = list(DIFF_SCOPE_ALLOWED_PATHS)
        specs.append({
            "id": "check-%s%s" % (name, suffix),
            "runner": runner,
        })
    if verification["regression_argv"] is not None:
        specs.append({
            "id": "declared-regression%s" % suffix,
            "runner": {
                "kind": "command",
                "argv": list(verification["regression_argv"]),
                "cwd": ".",
                "writes": [],
                "output_bytes": 1_000_000,
            },
        })
    return specs


def _rubric(slug: str, title: str, check_ids: list[str]) -> dict[str, object]:
    criteria: list[dict[str, object]] = []
    for check_id in check_ids:
        criteria.append({
            "id": "fact-%s" % check_id,
            "question": "Did the producing check node %s pass?" % check_id,
            "evaluation": {"kind": "mechanical-fact", "fact": check_id},
            "required_evidence_kinds": [],
            "min_citations": 0,
            "allowed_results": ["pass", "fail", "abstain", "inconclusive"],
            "veto": True,
            "rationale_max_bytes": 512,
        })
    criteria.append({
        "id": "scope-and-quality",
        "question": "Is the candidate confined to the selected story, maintainable, and ready for operator-controlled handoff?",
        "evaluation": {"kind": "agent-judgment", "fact": None},
        "required_evidence_kinds": ["git-diff"],
        "min_citations": 1,
        "allowed_results": ["pass", "fail", "abstain", "inconclusive"],
        "veto": True,
        "rationale_max_bytes": 3_000,
    })
    return {
        "kind": "delivery-workbench-rubric",
        "schema_version": 1,
        "slug": slug,
        "title": title,
        "description": "Mechanical checks plus independent diff-cited judgment.",
        "version": "1.0.0",
        "subject_type": "diff",
        "result_vocabulary": ["pass", "fail", "needs-repair", "escalate"],
        "freshness": {
            "max_age_seconds": 3_600,
            "bind": ["subject", "repository", "program", "assignment", "rubric", "ledger"],
        },
        "criteria": criteria,
        "aggregation": {
            "method": "all", "threshold": len(criteria), "on_pass": "pass",
            "on_fail": "needs-repair", "on_abstain": "escalate",
            "on_inconclusive": "needs-repair",
        },
        "layout": {},
    }


def _organization(slug: str, answers: dict[str, object]) -> dict[str, object]:
    profiles = answers["profiles"]
    assert isinstance(profiles, dict)

    def role(
        role_id: str,
        duty: str,
        pool: str,
        workspace: str,
        driver_capabilities: list[str],
        ceiling: list[str],
        independent: list[str],
    ) -> dict[str, object]:
        return {
            "id": role_id,
            "duty": duty,
            "pool": pool,
            "required": True,
            "cardinality": 1,
            "capability_ceiling": ceiling,
            "driver_capabilities": driver_capabilities,
            "workspace": workspace,
            "context": {
                "allow": [
                    "story", "phase", "roadmap", "workflow-inputs",
                    "candidate-diff", "mechanical-receipts", "prior-verdicts",
                    "public-artifacts",
                ],
                "expressions": ["context", "parameter", "literal", "artifact"],
                "max_bytes": 750_000,
            },
            "artifacts": {
                "read": ["markdown", "json", "text", "git-diff", "mechanical-fact", "verdict"],
                "write": ["git-diff", "markdown", "json", "text", "lesson"] if duty == "implementer" else ["verdict"],
                "max_bytes": 10_000_000,
            },
            "output_schema": "delivery-workbench-implementation-output@1" if duty == "implementer" else None,
            "verdict_schema": "delivery-workbench-agent-verdict@1" if duty == "verifier" else None,
            "max_concurrency": 1,
            "resource_groups": ["repository-writer"] if duty == "implementer" else ["independent-verification"],
            "may_request": [],
            "may_judge": ["implementer"] if duty == "verifier" else [],
            "independent_from": independent,
            "replacement": {
                "reasons": ["unavailable", "lost", "failed", "refused", "conflicted"],
                "max_replacements": 0,
                "fallback_pools": [],
                "on_exhausted": "block",
                "preserve_history": True,
            },
        }

    return {
        "kind": "delivery-workbench-organization",
        "schema_version": 1,
        "slug": slug,
        "title": "Generated implement and review cell",
        "description": "One isolated implementer and one read-only independent verifier.",
        "agents": [
            {
                "id": "implementer-agent", "profile": profiles["implementer"],
                "duties": ["implementer"], "workspace_domain": "implementation",
                "capability_ceiling": ["agent:dispatch", "workspace:write"],
                "max_concurrency": 1, "weight": 1,
            },
            {
                "id": "verifier-agent", "profile": profiles["verifier"],
                "duties": ["verifier"], "workspace_domain": "verification",
                "capability_ceiling": ["agent:dispatch", "verdict:issue"],
                "max_concurrency": 1, "weight": 1,
            },
        ],
        "pools": [
            {"id": "implementers", "agents": ["implementer-agent"]},
            {"id": "verifiers", "agents": ["verifier-agent"]},
        ],
        "teams": [{
            "id": "delivery-cell",
            "roles": [
                role(
                    "implementer", "implementer", "implementers",
                    "isolated-worktree", ["repository-read", "repository-write"],
                    ["agent:dispatch", "workspace:write"], [],
                ),
                role(
                    "verifier", "verifier", "verifiers", "read-only",
                    ["repository-read"], ["agent:dispatch", "verdict:issue"],
                    ["implementer"],
                ),
            ],
        }],
        "councils": [],
        "diversity": [{
            "id": "cross-provider-review", "kind": "provider-family",
            "roles": ["implementer", "verifier"],
        }],
        "layout": {},
    }


def _workflow(slug: str, answers: dict[str, object], initial_rubric: str, repair_rubric: str) -> dict[str, object]:
    size = answers["size"]
    assert isinstance(size, dict)
    initial_checks = _check_specs(answers)
    repair_checks = _check_specs(answers, "-after-repair")
    nodes: list[dict[str, object]] = [{
        "id": "implement", "type": "agent", "role": "implementer",
        "task": (
            "Implement only the supplied story. Do not edit roadmap status "
            "or evidence, certify, commit, push, merge, release, deploy, or "
            "publish. Also write the optional lesson output: one JSON "
            "document {\"kind\": \"delivery-workbench-lesson-output\", "
            "\"schema_version\": 1, \"lessons\": [{\"claim\": <one bounded "
            "sentence a future implementer of this repository should know>, "
            "\"locations\": [<file or file:symbol references>], "
            "\"confidence\": \"low\"|\"medium\"|\"high\", "
            "\"supersedes\": \"\"}]} with at most three lessons."
        ),
        "workspace": "isolated-worktree",
        "capability_ceiling": ["agent:dispatch", "workspace:write"],
        "timeout_seconds": 900 * COMPLEXITY_WEIGHTS[str(size["complexity"])],
        "max_attempts": 1,
        "inputs": {"story": {"kind": "parameter", "name": "story-id"}},
        "outputs": [
            {"id": "candidate", "kind": "git-diff", "max_bytes": 2_000_000},
            # The safest generated run still learns (WLA-30-09): the
            # implementer leaves bounded lessons that persist at the
            # certified handoff. Declared outputs are mandatory by the
            # conductor's materialization contract, so the task text
            # spells out the exact document shape.
            {"id": "lesson", "kind": "lesson", "max_bytes": 16_384},
        ],
        "on_failure": {"kind": "action", "target": "block"},
    }]
    for spec in initial_checks:
        nodes.append({
            "id": spec["id"], "type": "check", "needs": ["implement"],
            "inputs": {"candidate": {"kind": "artifact", "name": "implement.candidate"}},
            "runner": spec["runner"], "expect": {"exit_code": 0},
            "timeout_seconds": 1_200, "max_attempts": 1,
            "outputs": [{"id": "fact", "kind": "mechanical-fact", "max_bytes": 1_000_000}],
            "on_failure": {"kind": "action", "target": "block"},
        })
    initial_ids = [str(spec["id"]) for spec in initial_checks]
    nodes.append({
        "id": "verify-initial", "type": "verdict", "needs": initial_ids,
        "role": "verifier", "rubric": initial_rubric,
        "subject": {"kind": "artifact", "name": "implement.candidate"},
        "freshness_seconds": 3_600, "max_rationale_bytes": 30_000,
        "max_attempts": 1, "results": ["pass", "fail", "abstain", "inconclusive"],
        "routes": {
            # A passing first verdict goes straight to the certified
            # handoff; only failure takes the bounded repair leg. The
            # Phase 30 exam's live run proved the alternative absurd:
            # a repair seat handed a passing candidate has nothing to
            # fix and honestly refuses with an empty diff.
            "pass": {"kind": "terminal", "target": "certified-handoff"},
            "fail": {"kind": "node", "target": "repair-once"},
            "abstain": {"kind": "action", "target": "checkpoint"},
            "inconclusive": {"kind": "action", "target": "block"},
        },
        "outputs": [{"id": "verdict", "kind": "verdict", "max_bytes": 50_000}],
    })
    nodes.append({
        "id": "repair-once", "type": "agent", "activation": "route",
        "needs": ["verify-initial"],
        "role": "implementer",
        "task": "Apply at most one bounded repair responding only to the verifier findings, then stop.",
        "workspace": "isolated-worktree",
        "capability_ceiling": ["agent:dispatch", "workspace:write"],
        "timeout_seconds": 600 * COMPLEXITY_WEIGHTS[str(size["complexity"])],
        "max_attempts": 1,
        "inputs": {
            "candidate": {"kind": "artifact", "name": "implement.candidate"},
            "verdict": {"kind": "artifact", "name": "verify-initial.verdict"},
        },
        "outputs": [{"id": "candidate", "kind": "git-diff", "max_bytes": 2_000_000}],
        "on_failure": {"kind": "action", "target": "block"},
    })
    for spec in repair_checks:
        nodes.append({
            "id": spec["id"], "type": "check", "needs": ["repair-once"],
            "inputs": {"candidate": {"kind": "artifact", "name": "repair-once.candidate"}},
            "runner": spec["runner"], "expect": {"exit_code": 0},
            "timeout_seconds": 1_200, "max_attempts": 1,
            "outputs": [{"id": "fact", "kind": "mechanical-fact", "max_bytes": 1_000_000}],
            "on_failure": {"kind": "action", "target": "block"},
        })
    repair_ids = [str(spec["id"]) for spec in repair_checks]
    nodes.append({
        "id": "verify-repair", "type": "verdict", "needs": repair_ids,
        "role": "verifier", "rubric": repair_rubric,
        "subject": {"kind": "artifact", "name": "repair-once.candidate"},
        "freshness_seconds": 3_600, "max_rationale_bytes": 30_000,
        "max_attempts": 1, "results": ["pass", "fail", "abstain", "inconclusive"],
        "routes": {
            "pass": {"kind": "terminal", "target": "certified-handoff"},
            "fail": {"kind": "action", "target": "block"},
            "abstain": {"kind": "action", "target": "checkpoint"},
            "inconclusive": {"kind": "action", "target": "block"},
        },
        "outputs": [{"id": "verdict", "kind": "verdict", "max_bytes": 50_000}],
    })
    return {
        "kind": "delivery-workbench-workflow", "schema_version": 1,
        "slug": slug, "title": "Generated bounded delivery workflow",
        "description": "Implement, check, independently verify, permit one finite repair, and stop at certified handoff.",
        "version": "1.0.0",
        "parameters": [{"id": "story-id", "type": "string", "required": True, "max_bytes": 128}],
        "defaults": {}, "nodes": nodes,
        "terminals": [{
            "id": "certified-handoff", "meaning": "complete",
            "description": "Independent verification passed; stop before operator certification, commit, or publication.",
        }],
        "layout": {},
    }


def _program(
    slug: str,
    workflow_slug: str,
    organization_slug: str,
    rubric_slugs: list[str],
    answers: dict[str, object],
) -> dict[str, object]:
    scope = answers["scope"]
    project = answers["project"]
    assert isinstance(scope, dict) and isinstance(project, dict)
    phase_numbers = list(scope["phase_numbers"])
    story_ids = list(scope["story_ids"])
    return {
        "kind": "delivery-workbench-program", "schema_version": 1,
        "slug": slug, "title": "%s governed delivery" % project["title"],
        "description": "Generated checkpointed no-commit program with independent verification.",
        "scope": {
            "project": project["slug"],
            "phases": {"include": phase_numbers},
            "stories": {"include": story_ids},
            "selection": "roadmap-frontier-v1", "blocked_policy": "stop",
        },
        "organization": organization_slug,
        "bindings": [{
            "id": "generated-delivery", "priority": 10,
            "match": {
                "phase_from": min(phase_numbers), "phase_through": max(phase_numbers),
                "story_ids": story_ids,
            },
            "workflow": workflow_slug,
            "with": {"story-id": {"kind": "context", "name": "story.id"}},
            "team": "delivery-cell", "rubrics": rubric_slugs,
        }],
        "phase_gates": [], "nudges": [],
        "mode_ceiling": answers["autonomy_mode"],
        "requested_capabilities": list(REQUESTED_CAPABILITIES),
        "budgets": derive_program_budgets(answers),
        "stop_conditions": [
            "scope-complete", "checkpoint-required", "unresolved-dissent",
            "blocked-frontier", "budget-exhausted", "grant-expired", "grant-revoked",
        ],
        "layout": {},
    }


def _embedded_documents(policy: dict[str, object]) -> dict[str, object]:
    workflows = policy["workflows"]
    rubrics = policy["rubrics"]
    assert isinstance(workflows, list) and isinstance(rubrics, list)
    organization = policy["organization"]
    assert isinstance(organization, dict)
    return {
        "workflows": {
            str(wrapper["document"]["slug"]): wrapper["document"]
            for wrapper in workflows
        },
        "organizations": {
            str(organization["document"]["slug"]): organization["document"],
        },
        "rubrics": {
            str(wrapper["document"]["slug"]): wrapper["document"]
            for wrapper in rubrics
        },
    }


def simulate_scaffold_proposal(proposal: object) -> dict[str, object]:
    """Purely prove the generated bounded green and failure routes."""
    validated = validate_proposal(proposal)
    policy = validated["tracked_content"]["policy"]
    assert isinstance(policy, dict)
    workflow = policy["workflows"][0]["document"]
    nodes = workflow["nodes"]
    by_id = {str(node["id"]): node for node in nodes}
    for node in nodes:
        if node["type"] in {"agent", "check", "verdict"}:
            assert isinstance(node.get("max_attempts"), int) and node["max_attempts"] == 1
    initial = by_id["verify-initial"]
    final = by_id["verify-repair"]
    assert initial["routes"]["pass"] == {"kind": "terminal", "target": "certified-handoff"}
    assert initial["routes"]["fail"] == {"kind": "node", "target": "repair-once"}
    assert final["routes"]["pass"] == {"kind": "terminal", "target": "certified-handoff"}
    assert final["routes"]["fail"] == {"kind": "action", "target": "block"}
    initial_checks = [str(node["id"]) for node in nodes if node["type"] == "check" and not str(node["id"]).endswith("-after-repair")]
    repaired_checks = [str(node["id"]) for node in nodes if node["type"] == "check" and str(node["id"]).endswith("-after-repair")]
    return {
        "kind": "delivery-workbench-program-scaffold-simulation",
        "schema_version": 1,
        "bounded": True,
        "green_route": ["implement"] + initial_checks + ["verify-initial", "repair-once"] + repaired_checks + ["verify-repair", "certified-handoff"],
        "repair_route": ["verify-initial:fail", "repair-once"] + repaired_checks + ["verify-repair", "certified-handoff"],
        "failure_routes": [
            {"type": "check-failed", "target": "block"},
            {"type": "verifier-abstained", "target": "checkpoint"},
            {"type": "repair-failed", "target": "block"},
            {"type": "final-verdict-failed", "target": "block"},
            {"type": "budget-exhausted", "target": "stop"},
        ],
        "starts_work": False,
        "writes_state": False,
    }


def scaffold_program(
    root: Path,
    answers: object,
    *,
    driver_config: Optional[object] = None,
    base_proposal: Optional[object] = None,
) -> dict[str, object]:
    """Return one validated, inert, unsaved setup proposal; write nothing."""
    normalized = normalize_scaffold_answers(answers)
    validated_base: Optional[dict[str, object]] = (
        validate_proposal(base_proposal) if base_proposal is not None else None
    )
    config = (
        load_driver_config(root.resolve())
        if driver_config is None
        else validate_driver_config(driver_config)
    )
    profiles = normalized["profiles"]
    assert isinstance(profiles, dict)
    config_profiles = config["profiles"]
    assert isinstance(config_profiles, dict)
    selected: dict[str, dict[str, object]] = {}
    for role in ("implementer", "verifier"):
        name = str(profiles[role])
        raw = config_profiles.get(name)
        if not isinstance(raw, dict) or not raw.get("available"):
            _refuse("/profiles/%s" % role, "named local profile is missing or unavailable")
        required_capabilities = (
            {"repository-read", "repository-write"}
            if role == "implementer" else {"repository-read"}
        )
        if not required_capabilities.issubset(set(raw["capabilities"])):
            _refuse("/profiles/%s" % role, "named local profile lacks required capabilities")
        required_mode = "isolated-worktree" if role == "implementer" else "read-only"
        if required_mode not in raw["workspace_modes"]:
            _refuse("/profiles/%s" % role, "named local profile lacks required workspace mode")
        if not raw.get("model"):
            _refuse("/profiles/%s" % role, "named local profile must preserve a bounded model alias")
        selected[role] = raw
    if selected["implementer"].get("principal") == selected["verifier"].get("principal"):
        _refuse("/profiles/verifier", "verifier must use an independent local principal")
    implementer_family = selected["implementer"].get("provider_family")
    verifier_family = selected["verifier"].get("provider_family")
    if not implementer_family or not verifier_family or implementer_family == verifier_family:
        _refuse("/profiles/verifier", "named profiles do not satisfy provider-family diversity")

    project = normalized["project"]
    assert isinstance(project, dict)
    base = str(project["slug"])
    program_slug = base + "-generated-program"
    workflow_slug = base + "-generated-delivery"
    organization_slug = base + "-generated-cell"
    initial_rubric_slug = base + "-generated-quality"
    repair_rubric_slug = base + "-generated-repair-quality"
    initial_checks = [str(item["id"]) for item in _check_specs(normalized)]
    repair_checks = [str(item["id"]) for item in _check_specs(normalized, "-after-repair")]
    program = _program(
        program_slug, workflow_slug, organization_slug,
        [initial_rubric_slug, repair_rubric_slug], normalized,
    )
    workflow = _workflow(
        workflow_slug, normalized, initial_rubric_slug, repair_rubric_slug,
    )
    organization = _organization(organization_slug, normalized)
    rubrics = [
        _rubric(initial_rubric_slug, "Generated initial quality", initial_checks),
        _rubric(repair_rubric_slug, "Generated repair quality", repair_checks),
    ]
    recommendation = _provenance(
        "recommendation", "Deterministic dw program scaffold output.",
    )
    policy = {
        "program": {"document": program, "provenance": recommendation},
        "workflows": [{"document": workflow, "provenance": recommendation}],
        "organization": {"document": organization, "provenance": recommendation},
        "rubrics": [
            {"document": rubric, "provenance": recommendation}
            for rubric in rubrics
        ],
        "provenance": recommendation,
    }
    driver_bindings: dict[str, object] = {}
    for role in ("implementer", "verifier"):
        name = str(profiles[role])
        raw = selected[role]
        driver_bindings[name] = {
            "adapter": raw["adapter"],
            "model": raw["model"],
            "provider": raw["provider"],
            "provenance": _provenance(
                "repository-fact", "Validated local profile %s." % name,
            ),
        }
    if validated_base is not None:
        roadmap = _roadmap_from_base(validated_base, normalized)
        base_bindings = validated_base["local_content"]["driver_bindings"]  # type: ignore[index]
        assert isinstance(base_bindings, dict)
        for name, binding in sorted(base_bindings.items()):
            if name in driver_bindings and driver_bindings[name] != binding:
                _refuse(
                    "/profiles",
                    "base proposal binds profile %r differently" % name,
                )
            driver_bindings.setdefault(name, copy.deepcopy(binding))
        state = str(validated_base["state"])
        unresolved = copy.deepcopy(validated_base["unresolved_questions"])
        source_intent = copy.deepcopy(validated_base["source_intent"])
    else:
        roadmap = _roadmap_document(root.resolve(), normalized)
        state = "draft"
        unresolved = []
        source_intent = {
            "idea": project["idea"], "mode": project["mode"],
            "provenance": _provenance("user-answer", "Scaffold project intent."),
        }
    proposal = {
        "schema": PROPOSAL_SCHEMA,
        "state": state,
        "project": {
            "slug": project["slug"], "prefix": project["prefix"],
            "title": project["title"],
            "provenance": _provenance("user-answer", "Scaffold project identity."),
        },
        "source_intent": source_intent,
        "tracked_content": {
            "roadmap": roadmap,
            "policy": policy,
        },
        "local_content": {"driver_bindings": driver_bindings},
        "unresolved_questions": unresolved,
        "starts_work": False, "creates_grant": False,
        "certifies": False, "commits": False,
    }
    validate_proposal(proposal)
    validation = validate_program(
        root.resolve(), program,
        "setup-proposal:/tracked_content/policy/program/document",
        driver_config=config,
        bundle_documents=_embedded_documents(policy),
        roadmap_document=(
            {"project": {"slug": project["slug"]}, "roadmap": roadmap}
            if validated_base is not None
            else None
        ),
    )
    assert validation["valid"], "scaffold generated invalid bundle: %r" % validation["diagnostics"]
    simulation = simulate_scaffold_proposal(proposal)
    assert simulation["bounded"] and simulation["green_route"]
    assert not EXCLUDED_CAPABILITIES.intersection(program["requested_capabilities"])
    # Canonical serialization is the determinism post-condition and catches
    # accidental non-JSON values before the proposal leaves this pure function.
    canonical_proposal_json(proposal)
    return copy.deepcopy(proposal)
