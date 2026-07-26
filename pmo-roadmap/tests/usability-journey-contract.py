#!/usr/bin/env python3
"""Validate the Phase 27 whole-task journey and baseline contract.

The JSON fixtures are the reviewed source of truth. This checker keeps them
complete, source-linked, reachable through the existing Workbench fixture
harness, explicit about authority and tier changes, and reusable by later UI
and fresh-wheel tests. It also mutates valid journeys with planted red cases
so each important refusal remains executable rather than aspirational.
"""

from __future__ import annotations

import copy
import json
import re
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
FIXTURE_DIR = ROOT / "pmo-roadmap" / "tests" / "fixtures" / "usability"
JOURNEYS_PATH = FIXTURE_DIR / "journeys-v1.json"
STATES_PATH = FIXTURE_DIR / "states-v1.json"
BASELINE_PATH = FIXTURE_DIR / "baseline-v1.json"
RED_PATH = FIXTURE_DIR / "red-fixtures-v1.json"
LANGUAGE_PATH = ROOT / "docs" / "product-language-contract-v1.json"
INTEROP_PATH = ROOT / "docs" / "interop.md"
HARNESS_PATH = ROOT / "pmo-roadmap" / "tests" / "workbench-ui-smoke.sh"
EXIT_EXAM_PATH = ROOT / "pmo-roadmap" / "tests" / "usability-packaged-exam.py"
AUTONOMOUS_EXAM_PATH = (
    ROOT / "pmo-roadmap" / "tests" / "autonomous-program-packaged-exam.py"
)
PACKAGE_SMOKE_PATH = ROOT / "pmo-roadmap" / "tests" / "package-smoke.sh"
DOC_PATH = ROOT / "docs" / "usability-journeys.md"
README_PATH = ROOT / "README.md"
WORKFLOW_PATH = ROOT / ".github" / "workflows" / "validation.yml"

CAPABILITY_TIERS = {"vanilla", "bounded-run", "program"}
CONCEPT_IDS = {
    "delivery_plan",
    "team",
    "work",
    "review",
    "decision",
    "blocker",
    "permission",
    "progress",
    "cost",
    "next_step",
}
JOURNEY_IDS = {
    "healthy-first-arrival",
    "deliberate-capability-choice",
    "delivery-plan-setup",
    "team-review-setup",
    "preflight",
    "live-progress",
    "failed-review-and-repair",
    "blocked-human-decision",
    "remaining-permission-and-cost",
    "stop-and-revoke",
    "crash-recovery",
    "completion",
    "technical-inspection",
}
OPERATOR_QUESTIONS = {
    "delivery": "What are we delivering?",
    "team-review": "Who is doing and reviewing it?",
    "passed": "What passed?",
    "blocked": "What is blocked?",
    "decision": "Who needs to decide?",
    "permission-cost": "What may the delivery still change or spend?",
    "next": "What happens next?",
}
SCREEN_STORIES = {f"WLA-27-{number:02d}" for number in range(3, 11)}
REUSERS = {"workbench-ui", "fresh-wheel-exit-exam"}

JOURNEY_KEYS = {
    "id",
    "title",
    "starting_state",
    "capability_tiers",
    "user_question",
    "operator_questions",
    "visible_facts",
    "bounded_actions",
    "success_outcome",
    "refusal_recovery",
    "technical_details",
    "screen_slices",
    "reusable_by",
}
ACTION_KEYS = {
    "id",
    "label",
    "effect_id",
    "effect",
    "authority_source",
    "available_in_tiers",
    "resulting_tier",
    "confirmation_required",
}


def issue(
    issues: list[str], code: str, location: str, message: str
) -> None:
    issues.append(f"{code} {location}: {message}")


def issue_codes(issues: list[str]) -> set[str]:
    return {item.split(" ", 1)[0] for item in issues}


def nonempty_text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def text_list(value: Any) -> bool:
    return (
        isinstance(value, list)
        and bool(value)
        and all(nonempty_text(item) for item in value)
    )


def exact_keys(
    value: Any,
    expected: set[str],
    location: str,
    issues: list[str],
    code: str = "shape-invalid",
) -> bool:
    if not isinstance(value, dict):
        issue(issues, code, location, "expected object")
        return False
    actual = set(value)
    if actual != expected:
        issue(
            issues,
            code,
            location,
            "exact keys differ "
            f"(missing={sorted(expected - actual)}, "
            f"extra={sorted(actual - expected)})",
        )
        return False
    return True


def load_json(path: Path, issues: list[str]) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        issue(
            issues,
            "fixture-unreadable",
            str(path.relative_to(ROOT)),
            str(exc),
        )
        return {}
    if not isinstance(value, dict):
        issue(
            issues,
            "shape-invalid",
            str(path.relative_to(ROOT)),
            "root must be an object",
        )
        return {}
    return value


def declared_models(issues: list[str]) -> set[str]:
    try:
        interop = INTEROP_PATH.read_text(encoding="utf-8")
    except OSError as exc:
        issue(
            issues,
            "source-model-missing",
            str(INTEROP_PATH.relative_to(ROOT)),
            str(exc),
        )
        return set()
    return set(re.findall(r"`(delivery-workbench-[a-z0-9-]+)`", interop))


def harness_capture_ids(issues: list[str]) -> set[str]:
    try:
        harness = HARNESS_PATH.read_text(encoding="utf-8")
    except OSError as exc:
        issue(
            issues,
            "capture-missing",
            str(HARNESS_PATH.relative_to(ROOT)),
            str(exc),
        )
        return set()

    captures = {
        f"{name}-{viewport}"
        for name, viewport in re.findall(
            r'shot "([a-z0-9-]+)-(desktop|mobile)"', harness
        )
    }
    views = re.search(r'^VIEWS="([^"]+)"', harness, re.MULTILINE)
    if views:
        for spec in views.group(1).split():
            name = spec.split(":", 1)[0]
            captures.add(f"{name}-desktop")
            captures.add(f"{name}-mobile")
    if "1440,900" not in harness or "390,844" not in harness:
        issue(
            issues,
            "viewport-proof-missing",
            str(HARNESS_PATH.relative_to(ROOT)),
            "wide and narrow viewport geometries must both be present",
        )
    return captures


def reserved_patterns(
    language: dict[str, Any], issues: list[str]
) -> list[tuple[str, re.Pattern[str]]]:
    result: list[tuple[str, re.Pattern[str]]] = []
    entries = language.get("reserved_terms")
    if not isinstance(entries, list):
        issue(
            issues,
            "language-contract-invalid",
            "language.reserved_terms",
            "expected list",
        )
        return result
    for index, entry in enumerate(entries):
        if not isinstance(entry, dict):
            issue(
                issues,
                "language-contract-invalid",
                f"language.reserved_terms[{index}]",
                "expected object",
            )
            continue
        term = entry.get("term")
        pattern = entry.get("pattern")
        if not nonempty_text(term) or not nonempty_text(pattern):
            issue(
                issues,
                "language-contract-invalid",
                f"language.reserved_terms[{index}]",
                "term and pattern must be text",
            )
            continue
        try:
            result.append((term, re.compile(pattern, re.IGNORECASE)))
        except re.error as exc:
            issue(
                issues,
                "language-contract-invalid",
                f"language.reserved_terms[{index}].pattern",
                str(exc),
            )
    return result


def scan_everyday(
    strings: list[str], reserved: list[tuple[str, re.Pattern[str]]]
) -> set[str]:
    text = "\n".join(strings)
    return {
        term for term, pattern in reserved if pattern.search(text) is not None
    }


def validate_capabilities_and_authority(
    contract: dict[str, Any],
    models: set[str],
    issues: list[str],
) -> tuple[dict[str, dict[str, Any]], str]:
    technical_label = contract.get("technical_details_label")
    if technical_label != "Technical details":
        issue(
            issues,
            "technical-details-label-invalid",
            "journeys.technical_details_label",
            "must be exactly 'Technical details'",
        )

    tiers = contract.get("capability_tiers")
    found_tiers: dict[str, dict[str, Any]] = {}
    if not isinstance(tiers, list):
        issue(
            issues,
            "tier-inventory-invalid",
            "journeys.capability_tiers",
            "expected list",
        )
    else:
        for index, tier in enumerate(tiers):
            location = f"journeys.capability_tiers[{index}]"
            if not exact_keys(
                tier,
                {"id", "label", "optional", "entry_rule"},
                location,
                issues,
            ):
                continue
            tier_id = tier["id"]
            if tier_id in found_tiers:
                issue(
                    issues,
                    "tier-inventory-invalid",
                    f"{location}.id",
                    f"duplicate {tier_id!r}",
                )
            found_tiers[tier_id] = tier
            if not nonempty_text(tier["label"]) or not nonempty_text(
                tier["entry_rule"]
            ):
                issue(
                    issues,
                    "tier-inventory-invalid",
                    location,
                    "label and entry rule must be non-empty",
                )
            expected_optional = tier_id != "vanilla"
            if tier.get("optional") is not expected_optional:
                issue(
                    issues,
                    "tier-inventory-invalid",
                    f"{location}.optional",
                    f"{tier_id!r} optional must be {expected_optional}",
                )
    if set(found_tiers) != CAPABILITY_TIERS:
        issue(
            issues,
            "tier-inventory-invalid",
            "journeys.capability_tiers",
            f"expected exactly {sorted(CAPABILITY_TIERS)}",
        )

    sources = contract.get("authority_sources")
    authority: dict[str, dict[str, Any]] = {}
    if not isinstance(sources, list) or not sources:
        issue(
            issues,
            "authority-inventory-invalid",
            "journeys.authority_sources",
            "expected non-empty list",
        )
    else:
        for index, source in enumerate(sources):
            location = f"journeys.authority_sources[{index}]"
            if not exact_keys(
                source,
                {
                    "id",
                    "preview_model",
                    "result_model",
                    "effect_ids",
                    "confirmation_required",
                },
                location,
                issues,
            ):
                continue
            source_id = source["id"]
            if not nonempty_text(source_id):
                issue(
                    issues,
                    "authority-inventory-invalid",
                    f"{location}.id",
                    "expected text",
                )
                continue
            if source_id in authority:
                issue(
                    issues,
                    "authority-inventory-invalid",
                    f"{location}.id",
                    f"duplicate {source_id!r}",
                )
            authority[source_id] = source
            for field in ("preview_model", "result_model"):
                model = source.get(field)
                if source_id == "read-only-inspection":
                    if model is not None:
                        issue(
                            issues,
                            "authority-inventory-invalid",
                            f"{location}.{field}",
                            "read-only inspection must carry no authority model",
                        )
                elif model not in models:
                    issue(
                        issues,
                        "source-model-missing",
                        f"{location}.{field}",
                        f"{model!r} is not declared by docs/interop.md",
                    )
            effects = source.get("effect_ids")
            if (
                not text_list(effects)
                or len(effects) != len(set(effects))
                or effects != sorted(effects)
            ):
                issue(
                    issues,
                    "authority-inventory-invalid",
                    f"{location}.effect_ids",
                    "expected sorted unique non-empty text list",
                )
            if not isinstance(source.get("confirmation_required"), bool):
                issue(
                    issues,
                    "authority-inventory-invalid",
                    f"{location}.confirmation_required",
                    "expected boolean",
                )
    return authority, str(technical_label or "")


def validate_states(
    states_doc: dict[str, Any],
    models: set[str],
    captures: set[str],
    issues: list[str],
) -> dict[str, dict[str, Any]]:
    exact_keys(
        states_doc,
        {"kind", "schema_version", "harness", "viewports", "states"},
        "states",
        issues,
    )
    if states_doc.get("kind") != "delivery-workbench-usability-states":
        issue(issues, "shape-invalid", "states.kind", "unsupported kind")
    if states_doc.get("schema_version") != 1:
        issue(
            issues,
            "shape-invalid",
            "states.schema_version",
            "only version 1 is supported",
        )
    if states_doc.get("harness") != str(HARNESS_PATH.relative_to(ROOT)):
        issue(
            issues,
            "capture-missing",
            "states.harness",
            "must name the canonical Workbench viewport harness",
        )
    if states_doc.get("viewports") != {
        "wide": "1440x900",
        "narrow": "390x844",
    }:
        issue(
            issues,
            "viewport-proof-missing",
            "states.viewports",
            "expected the canonical wide and narrow geometries",
        )

    rows = states_doc.get("states")
    result: dict[str, dict[str, Any]] = {}
    if not isinstance(rows, list) or not rows:
        issue(issues, "state-inventory-invalid", "states.states", "expected list")
        return result
    for index, state in enumerate(rows):
        location = f"states.states[{index}]"
        if not exact_keys(
            state,
            {
                "id",
                "title",
                "capability_tier",
                "route",
                "capture_id",
                "canonical_models",
                "fact_paths",
            },
            location,
            issues,
        ):
            continue
        state_id = state["id"]
        if not nonempty_text(state_id):
            issue(
                issues,
                "state-inventory-invalid",
                f"{location}.id",
                "expected text",
            )
            continue
        if state_id in result:
            issue(
                issues,
                "state-inventory-invalid",
                f"{location}.id",
                f"duplicate {state_id!r}",
            )
        result[state_id] = state
        for field in ("title", "route", "capture_id"):
            if not nonempty_text(state.get(field)):
                issue(
                    issues,
                    "state-inventory-invalid",
                    f"{location}.{field}",
                    "expected text",
                )
        if state.get("capability_tier") not in CAPABILITY_TIERS:
            issue(
                issues,
                "state-inventory-invalid",
                f"{location}.capability_tier",
                f"expected one of {sorted(CAPABILITY_TIERS)}",
            )
        canonical_models = state.get("canonical_models")
        if not text_list(canonical_models):
            issue(
                issues,
                "state-inventory-invalid",
                f"{location}.canonical_models",
                "expected non-empty text list",
            )
        else:
            for model in canonical_models:
                if model not in models:
                    issue(
                        issues,
                        "source-model-missing",
                        f"{location}.canonical_models",
                        f"{model!r} is not declared by docs/interop.md",
                    )
        if not text_list(state.get("fact_paths")):
            issue(
                issues,
                "state-inventory-invalid",
                f"{location}.fact_paths",
                "expected non-empty text list",
            )
        capture_id = state.get("capture_id")
        for viewport in ("desktop", "mobile"):
            capture = f"{capture_id}-{viewport}"
            if capture not in captures:
                issue(
                    issues,
                    "capture-missing",
                    f"{location}.capture_id",
                    f"{capture!r} is not produced by the harness",
                )
    if {row.get("capability_tier") for row in result.values()} != CAPABILITY_TIERS:
        issue(
            issues,
            "tier-inventory-invalid",
            "states.states",
            "vanilla, bounded-run, and program states are all required",
        )
    return result


def validate_next_step(
    value: Any,
    location: str,
    action_ids: set[str],
    states: dict[str, dict[str, Any]],
    issues: list[str],
) -> None:
    if not isinstance(value, dict):
        issue(
            issues,
            "next-step-ambiguous",
            location,
            "expected exactly one next-step object",
        )
        return
    if set(value) != {"label", "target"}:
        issue(
            issues,
            "next-step-ambiguous",
            location,
            "expected exactly label and target",
        )
        return
    if not nonempty_text(value["label"]) or not nonempty_text(value["target"]):
        issue(
            issues,
            "next-step-ambiguous",
            location,
            "label and target must be non-empty",
        )
        return
    target = value["target"]
    if target.startswith("action:"):
        if target.split(":", 1)[1] not in action_ids:
            issue(
                issues,
                "next-step-ambiguous",
                f"{location}.target",
                f"unknown action target {target!r}",
            )
    elif target.startswith("state:"):
        if target.split(":", 1)[1] not in states:
            issue(
                issues,
                "next-step-ambiguous",
                f"{location}.target",
                f"unknown state target {target!r}",
            )
    else:
        issue(
            issues,
            "next-step-ambiguous",
            f"{location}.target",
            "target must be an exact action: or state: reference",
        )


def validate_journey(
    journey: Any,
    location: str,
    states: dict[str, dict[str, Any]],
    authority: dict[str, dict[str, Any]],
    models: set[str],
    reserved: list[tuple[str, re.Pattern[str]]],
    technical_label: str,
    expected_slices: list[str],
) -> list[str]:
    issues: list[str] = []
    if not isinstance(journey, dict):
        issue(issues, "journey-incomplete", location, "expected object")
        return issues
    if "starting_state" not in journey:
        issue(
            issues,
            "journey-incomplete",
            location,
            "starting_state is required",
        )
    exact_keys(journey, JOURNEY_KEYS, location, issues, "journey-incomplete")

    journey_id = journey.get("id")
    for field in ("id", "title", "starting_state", "user_question"):
        if not nonempty_text(journey.get(field)):
            issue(
                issues,
                "journey-incomplete",
                f"{location}.{field}",
                "expected non-empty text",
            )
    if nonempty_text(journey.get("user_question")) and not journey[
        "user_question"
    ].endswith("?"):
        issue(
            issues,
            "journey-incomplete",
            f"{location}.user_question",
            "must be phrased as a question",
        )

    state_id = journey.get("starting_state")
    state = states.get(state_id)
    if state is None:
        issue(
            issues,
            "journey-incomplete",
            f"{location}.starting_state",
            f"unknown state {state_id!r}",
        )
    tiers = journey.get("capability_tiers")
    if (
        not text_list(tiers)
        or len(tiers) != len(set(tiers))
        or not set(tiers).issubset(CAPABILITY_TIERS)
    ):
        issue(
            issues,
            "journey-incomplete",
            f"{location}.capability_tiers",
            f"expected a unique non-empty subset of {sorted(CAPABILITY_TIERS)}",
        )
        tiers = []
    if state is not None and state.get("capability_tier") not in tiers:
        issue(
            issues,
            "journey-incomplete",
            f"{location}.capability_tiers",
            "must include the starting state's tier",
        )

    question_ids = journey.get("operator_questions")
    if (
        not text_list(question_ids)
        or len(question_ids) != len(set(question_ids))
        or not set(question_ids).issubset(OPERATOR_QUESTIONS)
    ):
        issue(
            issues,
            "question-coverage-invalid",
            f"{location}.operator_questions",
            "expected unique known question ids",
        )

    everyday: list[str] = []
    for field in ("title", "user_question"):
        if nonempty_text(journey.get(field)):
            everyday.append(journey[field])

    visible = journey.get("visible_facts")
    if not isinstance(visible, list) or not visible:
        issue(
            issues,
            "journey-incomplete",
            f"{location}.visible_facts",
            "expected non-empty list",
        )
    else:
        for index, fact in enumerate(visible):
            fact_location = f"{location}.visible_facts[{index}]"
            if not exact_keys(
                fact,
                {"concept_id", "statement", "source_model"},
                fact_location,
                issues,
                "journey-incomplete",
            ):
                continue
            if fact.get("concept_id") not in CONCEPT_IDS:
                issue(
                    issues,
                    "journey-incomplete",
                    f"{fact_location}.concept_id",
                    "unknown everyday concept",
                )
            statement = fact.get("statement")
            if not nonempty_text(statement):
                issue(
                    issues,
                    "journey-incomplete",
                    f"{fact_location}.statement",
                    "expected text",
                )
            else:
                everyday.append(statement)
            source_model = fact.get("source_model")
            if source_model not in models:
                issue(
                    issues,
                    "source-model-missing",
                    f"{fact_location}.source_model",
                    f"{source_model!r} is not declared by docs/interop.md",
                )
            if (
                state is not None
                and source_model not in state.get("canonical_models", [])
            ):
                issue(
                    issues,
                    "state-source-mismatch",
                    f"{fact_location}.source_model",
                    "must be reachable from the starting state's models",
                )

    actions = journey.get("bounded_actions")
    action_ids: set[str] = set()
    if not isinstance(actions, list) or not actions:
        issue(
            issues,
            "journey-incomplete",
            f"{location}.bounded_actions",
            "expected non-empty list",
        )
    else:
        for index, action in enumerate(actions):
            action_location = f"{location}.bounded_actions[{index}]"
            if not exact_keys(
                action,
                ACTION_KEYS,
                action_location,
                issues,
                "journey-incomplete",
            ):
                continue
            action_id = action.get("id")
            if not nonempty_text(action_id):
                issue(
                    issues,
                    "journey-incomplete",
                    f"{action_location}.id",
                    "expected text",
                )
                continue
            if action_id in action_ids:
                issue(
                    issues,
                    "journey-incomplete",
                    f"{action_location}.id",
                    f"duplicate {action_id!r}",
                )
            action_ids.add(action_id)
            for field in ("label", "effect", "effect_id"):
                if not nonempty_text(action.get(field)):
                    issue(
                        issues,
                        "journey-incomplete",
                        f"{action_location}.{field}",
                        "expected text",
                    )
            if nonempty_text(action.get("label")):
                everyday.append(action["label"])
            if nonempty_text(action.get("effect")):
                everyday.append(action["effect"])

            source_id = action.get("authority_source")
            source = authority.get(source_id)
            if source is None:
                issue(
                    issues,
                    "authority-invented",
                    f"{action_location}.authority_source",
                    f"{source_id!r} is not a canonical authority source",
                )
            else:
                if action.get("effect_id") not in source.get("effect_ids", []):
                    issue(
                        issues,
                        "authority-invented",
                        f"{action_location}.effect_id",
                        "effect is outside the named authority source",
                    )
                if action.get("confirmation_required") is not source.get(
                    "confirmation_required"
                ):
                    issue(
                        issues,
                        "authority-confirmation-mismatch",
                        f"{action_location}.confirmation_required",
                        "must match the canonical source boundary",
                    )
            available = action.get("available_in_tiers")
            if (
                not text_list(available)
                or len(available) != len(set(available))
                or not set(available).issubset(set(tiers))
            ):
                issue(
                    issues,
                    "journey-incomplete",
                    f"{action_location}.available_in_tiers",
                    "expected a unique non-empty subset of the journey tiers",
                )
                available = []
            resulting = action.get("resulting_tier")
            if resulting not in tiers:
                issue(
                    issues,
                    "journey-incomplete",
                    f"{action_location}.resulting_tier",
                    "must be one of the journey tiers",
                )
            if (
                any(tier != resulting for tier in available)
                and action.get("confirmation_required") is not True
            ):
                issue(
                    issues,
                    "tier-upgrade-silent",
                    action_location,
                    "a tier change requires explicit confirmation",
                )
            if not isinstance(action.get("confirmation_required"), bool):
                issue(
                    issues,
                    "journey-incomplete",
                    f"{action_location}.confirmation_required",
                    "expected boolean",
                )

    success = journey.get("success_outcome")
    if exact_keys(
        success,
        {"summary", "next_step"},
        f"{location}.success_outcome",
        issues,
        "journey-incomplete",
    ):
        if not nonempty_text(success["summary"]):
            issue(
                issues,
                "journey-incomplete",
                f"{location}.success_outcome.summary",
                "expected text",
            )
        else:
            everyday.append(success["summary"])
        validate_next_step(
            success["next_step"],
            f"{location}.success_outcome.next_step",
            action_ids,
            states,
            issues,
        )
        if isinstance(success["next_step"], dict) and nonempty_text(
            success["next_step"].get("label")
        ):
            everyday.append(success["next_step"]["label"])

    recovery = journey.get("refusal_recovery")
    if not isinstance(recovery, dict) or "safe_exit" not in recovery:
        issue(
            issues,
            "safe-exit-missing",
            f"{location}.refusal_recovery",
            "safe_exit is required",
        )
    if exact_keys(
        recovery,
        {"summary", "unchanged", "safe_exit", "next_step"},
        f"{location}.refusal_recovery",
        issues,
        "journey-incomplete",
    ):
        if recovery["safe_exit"] is not True:
            issue(
                issues,
                "safe-exit-missing",
                f"{location}.refusal_recovery.safe_exit",
                "must be true",
            )
        for field in ("summary", "unchanged"):
            if not nonempty_text(recovery[field]):
                issue(
                    issues,
                    "journey-incomplete",
                    f"{location}.refusal_recovery.{field}",
                    "expected text",
                )
            else:
                everyday.append(recovery[field])
        validate_next_step(
            recovery["next_step"],
            f"{location}.refusal_recovery.next_step",
            action_ids,
            states,
            issues,
        )
        if isinstance(recovery["next_step"], dict) and nonempty_text(
            recovery["next_step"].get("label")
        ):
            everyday.append(recovery["next_step"]["label"])

    details = journey.get("technical_details")
    if exact_keys(
        details,
        {
            "label",
            "state_id",
            "source_models",
            "return_label",
            "reachable",
        },
        f"{location}.technical_details",
        issues,
        "journey-incomplete",
    ):
        if details["label"] != technical_label:
            issue(
                issues,
                "technical-details-inaccessible",
                f"{location}.technical_details.label",
                f"must be exactly {technical_label!r}",
            )
        if details["reachable"] is not True:
            issue(
                issues,
                "technical-details-inaccessible",
                f"{location}.technical_details.reachable",
                "must be true",
            )
        if not nonempty_text(details["return_label"]):
            issue(
                issues,
                "technical-details-inaccessible",
                f"{location}.technical_details.return_label",
                "expected a return label",
            )
        detail_state = states.get(details["state_id"])
        if detail_state is None:
            issue(
                issues,
                "technical-details-inaccessible",
                f"{location}.technical_details.state_id",
                f"unknown state {details['state_id']!r}",
            )
        detail_models = details["source_models"]
        if not text_list(detail_models):
            issue(
                issues,
                "technical-details-inaccessible",
                f"{location}.technical_details.source_models",
                "expected non-empty source list",
            )
        elif detail_state is not None and not set(detail_models).issubset(
            set(detail_state.get("canonical_models", []))
        ):
            issue(
                issues,
                "technical-details-inaccessible",
                f"{location}.technical_details.source_models",
                "must be reachable from the technical-details state",
            )

    slices = journey.get("screen_slices")
    if slices != expected_slices:
        issue(
            issues,
            "screen-ownership-invalid",
            f"{location}.screen_slices",
            f"expected {expected_slices}",
        )
    reusers = journey.get("reusable_by")
    if not text_list(reusers) or set(reusers) != REUSERS:
        issue(
            issues,
            "reuse-contract-invalid",
            f"{location}.reusable_by",
            f"expected exactly {sorted(REUSERS)}",
        )

    leaked = scan_everyday(everyday, reserved)
    if leaked:
        issue(
            issues,
            "everyday-language-leak",
            location,
            f"reserved technical terms leaked: {sorted(leaked)}",
        )
    return issues


def validate_contract(
    contract: dict[str, Any],
    states: dict[str, dict[str, Any]],
    authority: dict[str, dict[str, Any]],
    models: set[str],
    reserved: list[tuple[str, re.Pattern[str]]],
    technical_label: str,
    issues: list[str],
) -> tuple[dict[str, dict[str, Any]], dict[str, list[str]]]:
    exact_keys(
        contract,
        {
            "kind",
            "schema_version",
            "product_language_contract",
            "technical_details_label",
            "capability_tiers",
            "authority_sources",
            "operator_questions",
            "screen_slices",
            "journeys",
        },
        "journeys",
        issues,
    )
    if contract.get("kind") != "delivery-workbench-usability-journeys":
        issue(issues, "shape-invalid", "journeys.kind", "unsupported kind")
    if contract.get("schema_version") != 1:
        issue(
            issues,
            "shape-invalid",
            "journeys.schema_version",
            "only version 1 is supported",
        )
    if contract.get("product_language_contract") != str(
        LANGUAGE_PATH.relative_to(ROOT)
    ):
        issue(
            issues,
            "language-contract-invalid",
            "journeys.product_language_contract",
            "must reference the reviewed language contract",
        )

    questions = contract.get("operator_questions")
    found_questions: dict[str, str] = {}
    if not isinstance(questions, list):
        issue(
            issues,
            "question-coverage-invalid",
            "journeys.operator_questions",
            "expected list",
        )
    else:
        for index, question in enumerate(questions):
            location = f"journeys.operator_questions[{index}]"
            if not exact_keys(
                question, {"id", "text"}, location, issues
            ):
                continue
            found_questions[question["id"]] = question["text"]
    if found_questions != OPERATOR_QUESTIONS:
        issue(
            issues,
            "question-coverage-invalid",
            "journeys.operator_questions",
            "the seven Phase 26 questions must match exactly",
        )

    slices = contract.get("screen_slices")
    expected_by_journey = {journey_id: [] for journey_id in JOURNEY_IDS}
    found_screens: set[str] = set()
    if not isinstance(slices, list):
        issue(
            issues,
            "screen-ownership-invalid",
            "journeys.screen_slices",
            "expected list",
        )
    else:
        for index, row in enumerate(slices):
            location = f"journeys.screen_slices[{index}]"
            if not exact_keys(
                row, {"story", "title", "journey_ids"}, location, issues
            ):
                continue
            story = row["story"]
            if story in found_screens:
                issue(
                    issues,
                    "screen-ownership-invalid",
                    f"{location}.story",
                    f"duplicate {story!r}",
                )
            found_screens.add(story)
            if not nonempty_text(row["title"]):
                issue(
                    issues,
                    "screen-ownership-invalid",
                    f"{location}.title",
                    "expected text",
                )
            journey_ids = row["journey_ids"]
            if (
                not text_list(journey_ids)
                or len(journey_ids) != len(set(journey_ids))
                or not set(journey_ids).issubset(JOURNEY_IDS)
            ):
                issue(
                    issues,
                    "screen-ownership-invalid",
                    f"{location}.journey_ids",
                    "expected unique known journey ids",
                )
                continue
            for journey_id in journey_ids:
                expected_by_journey[journey_id].append(story)
    if found_screens != SCREEN_STORIES:
        issue(
            issues,
            "screen-ownership-invalid",
            "journeys.screen_slices",
            f"expected exactly {sorted(SCREEN_STORIES)}",
        )
    for story in ("WLA-27-08", "WLA-27-09", "WLA-27-10"):
        row = next(
            (
                item
                for item in slices or []
                if isinstance(item, dict) and item.get("story") == story
            ),
            {},
        )
        if set(row.get("journey_ids", [])) != JOURNEY_IDS:
            issue(
                issues,
                "screen-ownership-invalid",
                f"journeys.screen_slices[{story}]",
                "cross-surface, accessibility, and exit-exam slices own all journeys",
            )

    rows = contract.get("journeys")
    result: dict[str, dict[str, Any]] = {}
    covered_questions: set[str] = set()
    if not isinstance(rows, list) or not rows:
        issue(
            issues,
            "journey-incomplete",
            "journeys.journeys",
            "expected non-empty list",
        )
        return result, expected_by_journey
    for index, journey in enumerate(rows):
        journey_id = (
            journey.get("id") if isinstance(journey, dict) else f"index-{index}"
        )
        location = f"journeys.journeys[{index}]"
        if journey_id in result:
            issue(
                issues,
                "journey-incomplete",
                f"{location}.id",
                f"duplicate {journey_id!r}",
            )
        if isinstance(journey, dict) and nonempty_text(journey.get("id")):
            result[journey_id] = journey
            question_ids = journey.get("operator_questions")
            if isinstance(question_ids, list):
                covered_questions.update(
                    item for item in question_ids if isinstance(item, str)
                )
        issues.extend(
            validate_journey(
                journey,
                location,
                states,
                authority,
                models,
                reserved,
                technical_label,
                expected_by_journey.get(journey_id, []),
            )
        )
    if set(result) != JOURNEY_IDS:
        issue(
            issues,
            "journey-incomplete",
            "journeys.journeys",
            "journey inventory differs "
            f"(missing={sorted(JOURNEY_IDS - set(result))}, "
            f"extra={sorted(set(result) - JOURNEY_IDS)})",
        )
    if covered_questions != set(OPERATOR_QUESTIONS):
        issue(
            issues,
            "question-coverage-invalid",
            "journeys.journeys",
            f"uncovered questions: {sorted(set(OPERATOR_QUESTIONS) - covered_questions)}",
        )
    return result, expected_by_journey


def validate_baseline(
    baseline: dict[str, Any],
    journeys: dict[str, dict[str, Any]],
    states: dict[str, dict[str, Any]],
    captures: set[str],
    issues: list[str],
) -> dict[str, int]:
    exact_keys(
        baseline,
        {
            "kind",
            "schema_version",
            "observed_at",
            "source_harness",
            "method",
            "viewports",
            "journeys",
        },
        "baseline",
        issues,
    )
    if baseline.get("kind") != "delivery-workbench-usability-baseline":
        issue(issues, "baseline-invalid", "baseline.kind", "unsupported kind")
    if baseline.get("schema_version") != 1:
        issue(
            issues,
            "baseline-invalid",
            "baseline.schema_version",
            "only version 1 is supported",
        )
    if not nonempty_text(baseline.get("observed_at")):
        issue(
            issues,
            "baseline-invalid",
            "baseline.observed_at",
            "expected date",
        )
    if baseline.get("source_harness") != str(HARNESS_PATH.relative_to(ROOT)):
        issue(
            issues,
            "baseline-invalid",
            "baseline.source_harness",
            "must name the canonical viewport harness",
        )
    if not text_list(baseline.get("method")):
        issue(
            issues,
            "baseline-invalid",
            "baseline.method",
            "expected non-empty text list",
        )
    if baseline.get("viewports") != {
        "wide": "1440x900",
        "narrow": "390x844",
    }:
        issue(
            issues,
            "baseline-invalid",
            "baseline.viewports",
            "expected canonical wide and narrow geometries",
        )

    totals = {
        "steps": 0,
        "decisions": 0,
        "engineering_terms": 0,
        "dead_ends": 0,
        "context_switches": 0,
    }
    rows = baseline.get("journeys")
    seen: set[str] = set()
    if not isinstance(rows, list):
        issue(
            issues,
            "baseline-invalid",
            "baseline.journeys",
            "expected list",
        )
        return totals
    for index, row in enumerate(rows):
        location = f"baseline.journeys[{index}]"
        if not exact_keys(
            row,
            {
                "journey_id",
                "starting_capture",
                "technical_capture",
                "steps",
                "decisions",
                "engineering_terms",
                "dead_ends",
                "context_switches",
                "observations",
            },
            location,
            issues,
            "baseline-invalid",
        ):
            continue
        journey_id = row["journey_id"]
        if journey_id in seen:
            issue(
                issues,
                "baseline-invalid",
                f"{location}.journey_id",
                f"duplicate {journey_id!r}",
            )
        seen.add(journey_id)
        journey = journeys.get(journey_id)
        if journey is None:
            issue(
                issues,
                "baseline-invalid",
                f"{location}.journey_id",
                f"unknown journey {journey_id!r}",
            )
            continue
        start_state = states.get(journey["starting_state"], {})
        if row["starting_capture"] != start_state.get("capture_id"):
            issue(
                issues,
                "baseline-invalid",
                f"{location}.starting_capture",
                "must match the journey's reachable starting state",
            )
        detail_state = states.get(journey["technical_details"]["state_id"], {})
        if row["technical_capture"] != detail_state.get("capture_id"):
            issue(
                issues,
                "baseline-invalid",
                f"{location}.technical_capture",
                "must match the journey's reachable exact-detail state",
            )
        for capture_field in ("starting_capture", "technical_capture"):
            capture_id = row[capture_field]
            for viewport in ("desktop", "mobile"):
                if f"{capture_id}-{viewport}" not in captures:
                    issue(
                        issues,
                        "capture-missing",
                        f"{location}.{capture_field}",
                        f"{capture_id}-{viewport!s} is not produced",
                    )
        for field in totals:
            values = row[field]
            if not text_list(values):
                issue(
                    issues,
                    "baseline-invalid",
                    f"{location}.{field}",
                    "expected non-empty text list",
                )
            else:
                totals[field] += len(values)
        observations = row["observations"]
        if not exact_keys(
            observations,
            {"wide", "narrow"},
            f"{location}.observations",
            issues,
            "baseline-invalid",
        ):
            continue
        for viewport in ("wide", "narrow"):
            if not nonempty_text(observations[viewport]):
                issue(
                    issues,
                    "baseline-invalid",
                    f"{location}.observations.{viewport}",
                    "expected text",
                )
    if seen != JOURNEY_IDS:
        issue(
            issues,
            "baseline-invalid",
            "baseline.journeys",
            f"expected one row for every journey, got {sorted(seen)}",
        )
    return totals


def mutate(base: dict[str, Any], mutation: dict[str, Any]) -> dict[str, Any]:
    result = copy.deepcopy(base)
    parts = [
        item.replace("~1", "/").replace("~0", "~")
        for item in str(mutation["path"]).split("/")[1:]
    ]
    parent: Any = result
    for part in parts[:-1]:
        parent = parent[int(part)] if isinstance(parent, list) else parent[part]
    leaf = parts[-1]
    if mutation["op"] == "remove":
        if isinstance(parent, list):
            del parent[int(leaf)]
        else:
            del parent[leaf]
    elif mutation["op"] == "replace":
        if isinstance(parent, list):
            parent[int(leaf)] = mutation["value"]
        else:
            parent[leaf] = mutation["value"]
    else:
        raise ValueError(f"unsupported mutation op {mutation['op']!r}")
    return result


def validate_red_fixtures(
    red: dict[str, Any],
    journeys: dict[str, dict[str, Any]],
    states: dict[str, dict[str, Any]],
    authority: dict[str, dict[str, Any]],
    models: set[str],
    reserved: list[tuple[str, re.Pattern[str]]],
    technical_label: str,
    expected_by_journey: dict[str, list[str]],
    issues: list[str],
) -> int:
    exact_keys(
        red,
        {"kind", "schema_version", "cases"},
        "red",
        issues,
    )
    if red.get("kind") != "delivery-workbench-usability-red-fixtures":
        issue(issues, "red-fixture-invalid", "red.kind", "unsupported kind")
    if red.get("schema_version") != 1:
        issue(
            issues,
            "red-fixture-invalid",
            "red.schema_version",
            "only version 1 is supported",
        )
    cases = red.get("cases")
    if not isinstance(cases, list) or len(cases) < 6:
        issue(
            issues,
            "red-fixture-invalid",
            "red.cases",
            "at least six planted red cases are required",
        )
        return 0
    seen: set[str] = set()
    for index, case in enumerate(cases):
        location = f"red.cases[{index}]"
        if not exact_keys(
            case,
            {"id", "base_journey", "mutation", "expected_error"},
            location,
            issues,
            "red-fixture-invalid",
        ):
            continue
        case_id = case["id"]
        if not nonempty_text(case_id) or case_id in seen:
            issue(
                issues,
                "red-fixture-invalid",
                f"{location}.id",
                "expected unique non-empty text",
            )
        seen.add(case_id)
        base_id = case["base_journey"]
        base = journeys.get(base_id)
        if base is None:
            issue(
                issues,
                "red-fixture-invalid",
                f"{location}.base_journey",
                f"unknown journey {base_id!r}",
            )
            continue
        mutation = case["mutation"]
        if not exact_keys(
            mutation,
            {"op", "path", "value"},
            f"{location}.mutation",
            issues,
            "red-fixture-invalid",
        ):
            continue
        if mutation["op"] not in {"remove", "replace"} or not nonempty_text(
            mutation["path"]
        ):
            issue(
                issues,
                "red-fixture-invalid",
                f"{location}.mutation",
                "expected remove/replace and a JSON pointer",
            )
            continue
        try:
            changed = mutate(base, mutation)
        except (KeyError, IndexError, TypeError, ValueError) as exc:
            issue(
                issues,
                "red-fixture-invalid",
                f"{location}.mutation",
                str(exc),
            )
            continue
        if changed == base:
            issue(
                issues,
                "red-fixture-invalid",
                f"{location}.mutation",
                "mutation must change the base journey",
            )
            continue
        planted = validate_journey(
            changed,
            f"red[{case_id}]",
            states,
            authority,
            models,
            reserved,
            technical_label,
            expected_by_journey[base_id],
        )
        expected = case["expected_error"]
        if expected not in issue_codes(planted):
            issue(
                issues,
                "red-fixture-invalid",
                location,
                f"expected {expected!r}, got {sorted(issue_codes(planted))}",
            )
    return len(cases)


def validate_docs(
    journeys: dict[str, dict[str, Any]],
    totals: dict[str, int],
    issues: list[str],
) -> None:
    try:
        doc = DOC_PATH.read_text(encoding="utf-8")
    except OSError as exc:
        issue(
            issues,
            "docs-missing",
            str(DOC_PATH.relative_to(ROOT)),
            str(exc),
        )
        return
    for journey_id in sorted(journeys):
        if f"`{journey_id}`" not in doc:
            issue(
                issues,
                "docs-missing",
                str(DOC_PATH.relative_to(ROOT)),
                f"missing journey {journey_id!r}",
            )
    for question in OPERATOR_QUESTIONS.values():
        if question not in doc:
            issue(
                issues,
                "docs-missing",
                str(DOC_PATH.relative_to(ROOT)),
                f"missing operator question {question!r}",
            )
    for story in sorted(SCREEN_STORIES):
        if f"`{story}`" not in doc:
            issue(
                issues,
                "docs-missing",
                str(DOC_PATH.relative_to(ROOT)),
                f"missing screen owner {story!r}",
            )
    for filename in (
        "journeys-v1.json",
        "states-v1.json",
        "baseline-v1.json",
        "red-fixtures-v1.json",
        "usability-packaged-exam.py",
    ):
        if filename not in doc:
            issue(
                issues,
                "docs-missing",
                str(DOC_PATH.relative_to(ROOT)),
                f"missing fixture link {filename!r}",
            )
    for count in totals.values():
        if str(count) not in doc:
            issue(
                issues,
                "docs-missing",
                str(DOC_PATH.relative_to(ROOT)),
                f"missing baseline total {count}",
            )
    try:
        readme = README_PATH.read_text(encoding="utf-8")
    except OSError as exc:
        issue(
            issues,
            "docs-missing",
            str(README_PATH.relative_to(ROOT)),
            str(exc),
        )
    else:
        if "./docs/usability-journeys.md" not in readme:
            issue(
                issues,
                "docs-missing",
                "README.md",
                "missing usability-journeys guide link",
            )
    try:
        workflow = WORKFLOW_PATH.read_text(encoding="utf-8")
    except OSError as exc:
        issue(
            issues,
            "ci-wiring-missing",
            str(WORKFLOW_PATH.relative_to(ROOT)),
            str(exc),
        )
    else:
        command = "python3 pmo-roadmap/tests/usability-journey-contract.py"
        compile_path = "pmo-roadmap/tests/usability-journey-contract.py"
        exit_compile = "pmo-roadmap/tests/usability-packaged-exam.py"
        if (
            command not in workflow
            or compile_path not in workflow
            or exit_compile not in workflow
        ):
            issue(
                issues,
                "ci-wiring-missing",
                str(WORKFLOW_PATH.relative_to(ROOT)),
                "checker and fresh-wheel exit exam must compile in CI",
            )
    try:
        exit_exam = EXIT_EXAM_PATH.read_text(encoding="utf-8")
        autonomous_exam = AUTONOMOUS_EXAM_PATH.read_text(encoding="utf-8")
        package_smoke = PACKAGE_SMOKE_PATH.read_text(encoding="utf-8")
    except OSError as exc:
        issue(
            issues,
            "exit-exam-wiring-missing",
            "pmo-roadmap/tests",
            str(exc),
        )
    else:
        for marker in (
            "delivery-workbench-usability-packaged-exam",
            "validate_report",
            "build_transcript",
            "planted_red_cases",
            "everyday_reserved_terms",
            "Technical details",
        ):
            if marker not in exit_exam:
                issue(
                    issues,
                    "exit-exam-wiring-missing",
                    str(EXIT_EXAM_PATH.relative_to(ROOT)),
                    f"missing marker {marker!r}",
                )
        for journey_id in JOURNEY_IDS:
            if journey_id not in exit_exam:
                issue(
                    issues,
                    "exit-exam-wiring-missing",
                    str(EXIT_EXAM_PATH.relative_to(ROOT)),
                    f"missing journey binding {journey_id!r}",
                )
        for marker in (
            "phase27_observations",
            "same_consumer",
            "bounded_decision",
            "stop_and_revoke",
            "preflight",
            "technical_details",
        ):
            if marker not in autonomous_exam:
                issue(
                    issues,
                    "exit-exam-wiring-missing",
                    str(AUTONOMOUS_EXAM_PATH.relative_to(ROOT)),
                    f"missing production observation {marker!r}",
                )
        if "usability-packaged-exam.py" not in package_smoke:
            issue(
                issues,
                "exit-exam-wiring-missing",
                str(PACKAGE_SMOKE_PATH.relative_to(ROOT)),
                "package smoke must invoke the composed fresh-wheel exam",
            )


def main() -> int:
    issues: list[str] = []
    contract = load_json(JOURNEYS_PATH, issues)
    states_doc = load_json(STATES_PATH, issues)
    baseline = load_json(BASELINE_PATH, issues)
    red = load_json(RED_PATH, issues)
    language = load_json(LANGUAGE_PATH, issues)
    models = declared_models(issues)
    captures = harness_capture_ids(issues)
    reserved = reserved_patterns(language, issues)

    language_projection = language.get("projection")
    language_label = (
        language_projection.get("technical_view_label")
        if isinstance(language_projection, dict)
        else None
    )
    if contract.get("technical_details_label") != language_label:
        issue(
            issues,
            "language-contract-invalid",
            "journeys.technical_details_label",
            "must match the application-language contract",
        )

    authority, technical_label = validate_capabilities_and_authority(
        contract, models, issues
    )
    states = validate_states(states_doc, models, captures, issues)
    journeys, expected_by_journey = validate_contract(
        contract,
        states,
        authority,
        models,
        reserved,
        technical_label,
        issues,
    )
    totals = validate_baseline(
        baseline, journeys, states, captures, issues
    )
    red_count = validate_red_fixtures(
        red,
        journeys,
        states,
        authority,
        models,
        reserved,
        technical_label,
        expected_by_journey,
        issues,
    )
    validate_docs(journeys, totals, issues)

    if issues:
        for item in issues:
            print(f"ERROR {item}")
        return 1
    print(
        "usability-journey-contract: ok "
        f"({len(journeys)} journeys, {len(states)} reachable states, "
        f"{red_count} red fixtures; baseline "
        f"{totals['steps']} steps, {totals['decisions']} decisions, "
        f"{totals['engineering_terms']} engineering terms, "
        f"{totals['dead_ends']} dead ends, "
        f"{totals['context_switches']} context switches)"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
