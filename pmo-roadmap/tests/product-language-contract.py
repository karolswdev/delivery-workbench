#!/usr/bin/env python3
"""Structural and red-fixture checks for the Phase 27 language contract.

This checker intentionally owns no product wording beyond stable ids. The
reviewed JSON contract is the vocabulary source of truth; this script proves
that it is complete, source-linked, internally unambiguous, documented, and
able to reject engineering-language leakage from everyday regions.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
CONTRACT_PATH = ROOT / "docs" / "product-language-contract-v1.json"
DOC_PATH = ROOT / "docs" / "product-language.md"
FIXTURE_PATH = (
    ROOT / "pmo-roadmap" / "tests" / "product-language-fixtures-v1.json"
)
README_PATH = ROOT / "README.md"
WORKFLOW_PATH = ROOT / ".github" / "workflows" / "validation.yml"
INTEROP_PATH = ROOT / "docs" / "interop.md"

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
PROJECTION_RULE_IDS = {
    "canonical-facts-only",
    "semantic-owner-stays-core",
    "unknown-beats-guessed",
    "source-trace",
    "safety-adjacent",
    "explicit-audit-boundary",
    "no-machine-schema-change",
    "action-authority-stays-separate",
}
RESERVED_TERMS = {
    "grant",
    "ledger",
    "preview token",
    "start token",
    "act token",
    "content boundary",
    "certification",
    "capability",
    "projection",
    "conductor",
    "frontier",
    "receipt",
    "correlation id",
    "schema version",
    "rubric",
    "quorum",
    "meta-verifier",
    "hash",
}
SURFACE_IDS = {
    "workbench-orientation-roadmap",
    "workbench-health-and-edit",
    "workbench-mission-control-and-history",
    "workbench-bounded-delivery",
    "workbench-delivery-studio",
    "workbench-live-delivery",
    "cli-orientation-and-roadmap",
    "cli-setup-health-help-and-errors",
    "cli-bounded-delivery",
    "cli-program-delivery",
    "machine-json-adapters",
    "operator-notifications-and-telegram",
    "agent-riders-and-holdspeak",
    "readme-and-first-use",
    "everyday-product-guides",
    "architecture-and-protocol-contracts",
    "exact-events-streams-and-files",
    "cross-surface-errors-and-refusals",
}
CLASSIFICATIONS = {"everyday", "mixed", "technical_audit"}
ALLOWED_CONTEXTS = {
    "machine_contract",
    "architecture",
    "technical_audit",
    "copyable_command",
    "code_identifier",
}


def load_json(path: Path, errors: list[str]) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(f"{path.relative_to(ROOT)}: cannot load JSON: {exc}")
        return {}
    if not isinstance(value, dict):
        errors.append(f"{path.relative_to(ROOT)}: root must be an object")
        return {}
    return value


def exact_keys(
    value: Any,
    expected: set[str],
    location: str,
    errors: list[str],
) -> bool:
    if not isinstance(value, dict):
        errors.append(f"{location}: expected object")
        return False
    actual = set(value)
    if actual != expected:
        errors.append(
            f"{location}: exact keys differ "
            f"(missing={sorted(expected - actual)}, extra={sorted(actual - expected)})"
        )
        return False
    return True


def nonempty_text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def list_of_text(value: Any) -> bool:
    return (
        isinstance(value, list)
        and bool(value)
        and all(nonempty_text(item) for item in value)
    )


def compiled_reserved(
    contract: dict[str, Any], errors: list[str]
) -> list[tuple[str, re.Pattern[str]]]:
    result: list[tuple[str, re.Pattern[str]]] = []
    entries = contract.get("reserved_terms")
    if not isinstance(entries, list):
        errors.append("contract.reserved_terms: expected list")
        return result
    seen: set[str] = set()
    for index, entry in enumerate(entries):
        location = f"contract.reserved_terms[{index}]"
        if not exact_keys(
            entry,
            {
                "term",
                "pattern",
                "replacement",
                "allowed_contexts",
                "leak_example",
            },
            location,
            errors,
        ):
            continue
        term = entry["term"]
        if not nonempty_text(term):
            errors.append(f"{location}.term: expected non-empty text")
            continue
        if term in seen:
            errors.append(f"{location}.term: duplicate {term!r}")
        seen.add(term)
        if not nonempty_text(entry["replacement"]):
            errors.append(f"{location}.replacement: expected non-empty text")
        contexts = entry["allowed_contexts"]
        if (
            not isinstance(contexts, list)
            or not contexts
            or not all(item in ALLOWED_CONTEXTS for item in contexts)
        ):
            errors.append(
                f"{location}.allowed_contexts: expected a non-empty subset of "
                f"{sorted(ALLOWED_CONTEXTS)}"
            )
        try:
            pattern = re.compile(str(entry["pattern"]), re.IGNORECASE)
        except re.error as exc:
            errors.append(f"{location}.pattern: invalid regex: {exc}")
            continue
        leak_example = entry["leak_example"]
        if not nonempty_text(leak_example) or not pattern.search(leak_example):
            errors.append(
                f"{location}.leak_example: must exercise its own pattern"
            )
        result.append((term, pattern))
    if seen != RESERVED_TERMS:
        errors.append(
            "contract.reserved_terms: term inventory differs "
            f"(missing={sorted(RESERVED_TERMS - seen)}, "
            f"extra={sorted(seen - RESERVED_TERMS)})"
        )
    return result


def scan_everyday(
    text: str, reserved: list[tuple[str, re.Pattern[str]]]
) -> list[str]:
    return sorted(
        {
            f"reserved-term:{term}"
            for term, pattern in reserved
            if pattern.search(text)
        }
    )


def validate_contract(
    contract: dict[str, Any],
    reserved: list[tuple[str, re.Pattern[str]]],
    errors: list[str],
) -> tuple[dict[str, str], list[dict[str, Any]]]:
    exact_keys(
        contract,
        {
            "kind",
            "schema_version",
            "title",
            "projection",
            "concepts",
            "reserved_terms",
            "surfaces",
        },
        "contract",
        errors,
    )
    if contract.get("kind") != "delivery-workbench-application-language":
        errors.append("contract.kind: unsupported kind")
    if contract.get("schema_version") != 1:
        errors.append("contract.schema_version: only version 1 is supported")
    if not nonempty_text(contract.get("title")):
        errors.append("contract.title: expected non-empty text")

    projection = contract.get("projection")
    if exact_keys(
        projection,
        {
            "input_contract",
            "output_contract",
            "technical_view_label",
            "unknown_policy",
            "versioning",
            "rules",
        },
        "contract.projection",
        errors,
    ):
        for field in (
            "input_contract",
            "output_contract",
            "technical_view_label",
            "unknown_policy",
            "versioning",
        ):
            if not nonempty_text(projection[field]):
                errors.append(f"contract.projection.{field}: expected text")
        if projection["technical_view_label"] != "Technical details":
            errors.append(
                "contract.projection.technical_view_label: "
                "the explicit boundary label must be 'Technical details'"
            )
        rules = projection["rules"]
        found_rules: set[str] = set()
        if not isinstance(rules, list):
            errors.append("contract.projection.rules: expected list")
        else:
            for index, rule in enumerate(rules):
                location = f"contract.projection.rules[{index}]"
                if not exact_keys(
                    rule, {"id", "requirement"}, location, errors
                ):
                    continue
                if rule["id"] in found_rules:
                    errors.append(f"{location}.id: duplicate {rule['id']!r}")
                found_rules.add(rule["id"])
                if not nonempty_text(rule["requirement"]):
                    errors.append(f"{location}.requirement: expected text")
            if found_rules != PROJECTION_RULE_IDS:
                errors.append(
                    "contract.projection.rules: rule inventory differs "
                    f"(missing={sorted(PROJECTION_RULE_IDS - found_rules)}, "
                    f"extra={sorted(found_rules - PROJECTION_RULE_IDS)})"
                )

    concepts = contract.get("concepts")
    preferred: dict[str, str] = {}
    preferred_values: set[str] = set()
    source_models: set[str] = set()
    if not isinstance(concepts, list):
        errors.append("contract.concepts: expected list")
    else:
        for index, concept in enumerate(concepts):
            location = f"contract.concepts[{index}]"
            if not exact_keys(
                concept,
                {
                    "id",
                    "preferred",
                    "definition",
                    "relationship",
                    "source_facts",
                    "good",
                    "bad",
                    "safety",
                },
                location,
                errors,
            ):
                continue
            concept_id = concept["id"]
            name = concept["preferred"]
            if concept_id in preferred:
                errors.append(f"{location}.id: duplicate {concept_id!r}")
            if not nonempty_text(name):
                errors.append(f"{location}.preferred: expected text")
                continue
            normalized_name = name.casefold()
            if normalized_name in preferred_values:
                errors.append(
                    f"{location}.preferred: duplicate product name {name!r}"
                )
            preferred_values.add(normalized_name)
            preferred[concept_id] = name
            for field in (
                "definition",
                "relationship",
                "good",
                "bad",
                "safety",
            ):
                if not nonempty_text(concept[field]):
                    errors.append(f"{location}.{field}: expected text")
            if normalized_name not in str(concept["good"]).casefold():
                errors.append(
                    f"{location}.good: must use preferred name {name!r}"
                )
            leaked = scan_everyday(str(concept["good"]), reserved)
            if leaked:
                errors.append(
                    f"{location}.good: everyday example leaks {leaked}"
                )
            source_facts = concept["source_facts"]
            if not isinstance(source_facts, list) or not source_facts:
                errors.append(f"{location}.source_facts: expected non-empty list")
            else:
                for source_index, source in enumerate(source_facts):
                    source_location = (
                        f"{location}.source_facts[{source_index}]"
                    )
                    if not exact_keys(
                        source, {"model", "facts"}, source_location, errors
                    ):
                        continue
                    if not nonempty_text(source["model"]):
                        errors.append(f"{source_location}.model: expected text")
                    else:
                        source_models.add(source["model"])
                    if not list_of_text(source["facts"]):
                        errors.append(
                            f"{source_location}.facts: expected non-empty text list"
                        )
    found_concepts = set(preferred)
    if found_concepts != CONCEPT_IDS:
        errors.append(
            "contract.concepts: concept inventory differs "
            f"(missing={sorted(CONCEPT_IDS - found_concepts)}, "
            f"extra={sorted(found_concepts - CONCEPT_IDS)})"
        )
    try:
        interop = INTEROP_PATH.read_text(encoding="utf-8")
    except OSError as exc:
        errors.append(f"{INTEROP_PATH.relative_to(ROOT)}: cannot read: {exc}")
    else:
        for model in sorted(source_models):
            if f"`{model}`" not in interop:
                errors.append(
                    f"contract.concepts: source model {model!r} is not "
                    f"declared in {INTEROP_PATH.relative_to(ROOT)}"
                )

    surfaces = contract.get("surfaces")
    surface_rows: list[dict[str, Any]] = []
    found_surfaces: set[str] = set()
    if not isinstance(surfaces, list):
        errors.append("contract.surfaces: expected list")
    else:
        for index, surface in enumerate(surfaces):
            location = f"contract.surfaces[{index}]"
            if not exact_keys(
                surface,
                {
                    "id",
                    "channel",
                    "classification",
                    "sources",
                    "entry_points",
                    "boundary",
                    "owner_stories",
                },
                location,
                errors,
            ):
                continue
            surface_id = surface["id"]
            if surface_id in found_surfaces:
                errors.append(f"{location}.id: duplicate {surface_id!r}")
            found_surfaces.add(surface_id)
            if not nonempty_text(surface["channel"]):
                errors.append(f"{location}.channel: expected text")
            classification = surface["classification"]
            if classification not in CLASSIFICATIONS:
                errors.append(
                    f"{location}.classification: expected one of "
                    f"{sorted(CLASSIFICATIONS)}"
                )
            if not list_of_text(surface["sources"]):
                errors.append(f"{location}.sources: expected non-empty text list")
            else:
                for source in surface["sources"]:
                    if not (ROOT / source).exists():
                        errors.append(
                            f"{location}.sources: missing repository path {source}"
                        )
            if not list_of_text(surface["entry_points"]):
                errors.append(
                    f"{location}.entry_points: expected non-empty text list"
                )
            if not nonempty_text(surface["boundary"]):
                errors.append(f"{location}.boundary: expected text")
            if (
                classification == "mixed"
                and "technical details" not in surface["boundary"].casefold()
            ):
                errors.append(
                    f"{location}.boundary: mixed surfaces must name "
                    "the Technical details boundary"
                )
            owners = surface["owner_stories"]
            if (
                not list_of_text(owners)
                or not all(re.fullmatch(r"WLA-27-\d{2}", item) for item in owners)
            ):
                errors.append(
                    f"{location}.owner_stories: expected WLA-27 story ids"
                )
            surface_rows.append(surface)
    if found_surfaces != SURFACE_IDS:
        errors.append(
            "contract.surfaces: surface inventory differs "
            f"(missing={sorted(SURFACE_IDS - found_surfaces)}, "
            f"extra={sorted(found_surfaces - SURFACE_IDS)})"
        )
    found_classes = {
        str(surface.get("classification")) for surface in surface_rows
    }
    if found_classes != CLASSIFICATIONS:
        errors.append(
            "contract.surfaces: every classification requires an inventory row"
        )
    return preferred, surface_rows


def lint_fixture(
    case: dict[str, Any],
    preferred: dict[str, str],
    reserved: list[tuple[str, re.Pattern[str]]],
    technical_label: str,
) -> list[str]:
    issues: list[str] = []
    classification = case.get("classification")
    if classification == "everyday":
        issues.extend(scan_everyday(str(case.get("text", "")), reserved))
    elif classification == "mixed":
        if (
            case.get("technical_label") != technical_label
            or case.get("technical_explicit") is not True
        ):
            issues.append("mixed-boundary-missing")
        regions = case.get("regions")
        if not isinstance(regions, list) or not regions:
            issues.append("mixed-regions-missing")
        else:
            region_classes = {
                region.get("classification")
                for region in regions
                if isinstance(region, dict)
            }
            if region_classes != {"everyday", "technical_audit"}:
                issues.append("mixed-regions-incomplete")
            for region in regions:
                if (
                    isinstance(region, dict)
                    and region.get("classification") == "everyday"
                ):
                    issues.extend(
                        scan_everyday(str(region.get("text", "")), reserved)
                    )
    elif classification != "technical_audit":
        issues.append("classification-invalid")

    names = case.get("concept_names")
    if not isinstance(names, dict):
        issues.append("concept-names-invalid")
    else:
        for concept_id, name in names.items():
            if concept_id not in preferred:
                issues.append(f"concept-unknown:{concept_id}")
            elif str(name).casefold() != preferred[concept_id].casefold():
                issues.append(f"conflicting-name:{concept_id}")
    return sorted(set(issues))


def validate_fixtures(
    fixtures: dict[str, Any],
    preferred: dict[str, str],
    reserved: list[tuple[str, re.Pattern[str]]],
    technical_label: str,
    errors: list[str],
) -> int:
    exact_keys(
        fixtures,
        {"kind", "schema_version", "cases"},
        "fixtures",
        errors,
    )
    if fixtures.get("kind") != "delivery-workbench-product-language-fixtures":
        errors.append("fixtures.kind: unsupported kind")
    if fixtures.get("schema_version") != 1:
        errors.append("fixtures.schema_version: only version 1 is supported")
    cases = fixtures.get("cases")
    if not isinstance(cases, list) or not cases:
        errors.append("fixtures.cases: expected non-empty list")
        return 0
    seen: set[str] = set()
    classifications: set[str] = set()
    red_count = 0
    for index, case in enumerate(cases):
        location = f"fixtures.cases[{index}]"
        if not isinstance(case, dict):
            errors.append(f"{location}: expected object")
            continue
        case_id = case.get("id")
        if not nonempty_text(case_id):
            errors.append(f"{location}.id: expected text")
            continue
        if case_id in seen:
            errors.append(f"{location}.id: duplicate {case_id!r}")
        seen.add(case_id)
        classification = case.get("classification")
        classifications.add(str(classification))
        expected = case.get("expected")
        if (
            not isinstance(expected, list)
            or not all(nonempty_text(item) for item in expected)
            or expected != sorted(set(expected))
        ):
            errors.append(
                f"{location}.expected: expected a sorted unique text list"
            )
            continue
        if expected:
            red_count += 1
        actual = lint_fixture(case, preferred, reserved, technical_label)
        if actual != expected:
            errors.append(
                f"{location} ({case_id}): expected {expected}, got {actual}"
            )
    if classifications != CLASSIFICATIONS:
        errors.append(
            "fixtures.cases: everyday, mixed, and technical_audit "
            "cases are all required"
        )
    if red_count < 4:
        errors.append("fixtures.cases: at least four red cases are required")
    return len(cases)


def validate_documentation(
    preferred: dict[str, str],
    surface_rows: list[dict[str, Any]],
    errors: list[str],
) -> None:
    try:
        doc = DOC_PATH.read_text(encoding="utf-8")
    except OSError as exc:
        errors.append(f"{DOC_PATH.relative_to(ROOT)}: cannot read: {exc}")
        return
    for concept_id, name in preferred.items():
        if f"`{name}`" not in doc:
            errors.append(
                f"{DOC_PATH.relative_to(ROOT)}: missing preferred term "
                f"{concept_id}={name!r}"
            )
    for surface in surface_rows:
        if f"`{surface['id']}`" not in doc:
            errors.append(
                f"{DOC_PATH.relative_to(ROOT)}: missing inventory row "
                f"{surface['id']!r}"
            )
    if "product-language-contract-v1.json" not in doc:
        errors.append(
            f"{DOC_PATH.relative_to(ROOT)}: missing contract JSON link"
        )
    try:
        readme = README_PATH.read_text(encoding="utf-8")
    except OSError as exc:
        errors.append(f"{README_PATH.relative_to(ROOT)}: cannot read: {exc}")
    else:
        if "./docs/product-language.md" not in readme:
            errors.append("README.md: missing product-language guide link")
    try:
        workflow = WORKFLOW_PATH.read_text(encoding="utf-8")
    except OSError as exc:
        errors.append(f"{WORKFLOW_PATH.relative_to(ROOT)}: cannot read: {exc}")
    else:
        command = "python3 pmo-roadmap/tests/product-language-contract.py"
        if command not in workflow:
            errors.append(
                f"{WORKFLOW_PATH.relative_to(ROOT)}: checker is not wired into CI"
            )


def main() -> int:
    errors: list[str] = []
    contract = load_json(CONTRACT_PATH, errors)
    fixtures = load_json(FIXTURE_PATH, errors)
    reserved = compiled_reserved(contract, errors)
    preferred, surfaces = validate_contract(contract, reserved, errors)

    projection = contract.get("projection")
    technical_label = (
        str(projection.get("technical_view_label", ""))
        if isinstance(projection, dict)
        else ""
    )
    case_count = validate_fixtures(
        fixtures, preferred, reserved, technical_label, errors
    )

    # Every reserved term carries a planted everyday leak that must trip its
    # own rule. This makes a relaxed or drifted regex fail the checker itself.
    for entry in contract.get("reserved_terms", []):
        if not isinstance(entry, dict):
            continue
        term = entry.get("term")
        actual = scan_everyday(str(entry.get("leak_example", "")), reserved)
        if f"reserved-term:{term}" not in actual:
            errors.append(
                f"contract.reserved_terms[{term!r}]: self-test did not fail"
            )

    validate_documentation(preferred, surfaces, errors)
    if errors:
        for message in errors:
            print(f"ERROR {message}")
        return 1
    print(
        "product-language-contract: ok "
        f"({len(preferred)} concepts, {len(surfaces)} surfaces, "
        f"{len(reserved)} reserved terms, {case_count} fixtures)"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
