#!/usr/bin/env python3
"""Structural and red-fixture checks for the Phase 27 language contract.

This checker intentionally owns no product wording beyond stable ids. The
reviewed JSON contract is the vocabulary source of truth; this script proves
that it is complete, source-linked, internally unambiguous, documented, and
able to reject engineering-language leakage from everyday regions.
"""

from __future__ import annotations

import copy
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
SURFACE_DISPOSITIONS_PATH = (
    ROOT / "pmo-roadmap" / "tests" / "product-language-surfaces-v1.json"
)
SNAPSHOT_PATH = (
    ROOT / "pmo-roadmap" / "tests"
    / "everyday-presentation-snapshots-v1.json"
)
README_PATH = ROOT / "README.md"
EVERYDAY_GUIDE_PATH = ROOT / "docs" / "everyday-delivery.md"
WORKFLOW_PATH = ROOT / ".github" / "workflows" / "validation.yml"
INTEROP_PATH = ROOT / "docs" / "interop.md"
LIB_PATH = ROOT / "pmo-roadmap" / "lib"

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


def scan_everyday_source(
    text: str, reserved: list[tuple[str, re.Pattern[str]]]
) -> list[str]:
    """Scan source copy while excluding quoted mapping keys.

    Mapping keys are code identifiers (for example an exact command or event
    kind); the values beside them remain fully scanned as everyday copy.
    """
    without_keys = re.sub(
        r'(?m)^(\s*)("[^"\\]*(?:\\.[^"\\]*)*")(\s*:)',
        r'\1""\3',
        text,
    )
    return scan_everyday(without_keys, reserved)


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


def validate_surface_dispositions(
    document: dict[str, Any],
    surface_rows: list[dict[str, Any]],
    reserved: list[tuple[str, re.Pattern[str]]],
    errors: list[str],
) -> tuple[int, int]:
    exact_keys(
        document,
        {
            "kind",
            "schema_version",
            "contract_schema_version",
            "surfaces",
            "executable_regions",
            "snapshots",
        },
        "surface_dispositions",
        errors,
    )
    if (
        document.get("kind")
        != "delivery-workbench-product-language-surface-dispositions"
    ):
        errors.append("surface_dispositions.kind: unsupported kind")
    if document.get("schema_version") != 1:
        errors.append(
            "surface_dispositions.schema_version: only version 1 is supported"
        )
    if document.get("contract_schema_version") != 1:
        errors.append(
            "surface_dispositions.contract_schema_version: must match contract"
        )
    if document.get("snapshots") != str(SNAPSHOT_PATH.relative_to(ROOT)):
        errors.append(
            "surface_dispositions.snapshots: must name the executable snapshot file"
        )

    contract_by_id = {
        str(row.get("id")): row
        for row in surface_rows
        if isinstance(row, dict)
    }
    rows = document.get("surfaces")
    found: set[str] = set()
    migrated = 0
    if not isinstance(rows, list):
        errors.append("surface_dispositions.surfaces: expected list")
        rows = []
    for index, row in enumerate(rows):
        location = f"surface_dispositions.surfaces[{index}]"
        if not exact_keys(
            row,
            {
                "id",
                "classification",
                "disposition",
                "reason",
                "presentation_sources",
                "proofs",
            },
            location,
            errors,
        ):
            continue
        surface_id = str(row["id"])
        if surface_id in found:
            errors.append(f"{location}.id: duplicate {surface_id!r}")
        found.add(surface_id)
        contract_row = contract_by_id.get(surface_id)
        if contract_row is None:
            errors.append(f"{location}.id: not present in the language contract")
            continue
        classification = row["classification"]
        if classification != contract_row.get("classification"):
            errors.append(
                f"{location}.classification: differs from contract "
                f"{contract_row.get('classification')!r}"
            )
        expected_disposition = (
            "technical_audit"
            if classification == "technical_audit"
            else "migrated"
        )
        if row["disposition"] != expected_disposition:
            errors.append(
                f"{location}.disposition: {classification!r} requires "
                f"{expected_disposition!r}"
            )
        if row["disposition"] == "migrated":
            migrated += 1
        if not nonempty_text(row["reason"]):
            errors.append(f"{location}.reason: expected non-empty text")
        presentation_sources = row["presentation_sources"]
        if not isinstance(presentation_sources, list) or not all(
            nonempty_text(item) for item in presentation_sources
        ):
            errors.append(
                f"{location}.presentation_sources: expected a text list"
            )
            presentation_sources = []
        if expected_disposition == "migrated" and not presentation_sources:
            errors.append(
                f"{location}.presentation_sources: migrated surface needs a source"
            )
        if expected_disposition == "technical_audit" and presentation_sources:
            errors.append(
                f"{location}.presentation_sources: technical audit stays exact"
            )
        proofs = row["proofs"]
        if not list_of_text(proofs):
            errors.append(f"{location}.proofs: expected non-empty text list")
            proofs = []
        for field, paths in (
            ("presentation_sources", presentation_sources),
            ("proofs", proofs),
        ):
            for value in paths:
                if not (ROOT / value).exists():
                    errors.append(
                        f"{location}.{field}: missing repository path {value}"
                    )
    if found != set(contract_by_id):
        errors.append(
            "surface_dispositions.surfaces: contract inventory differs "
            f"(missing={sorted(set(contract_by_id) - found)}, "
            f"extra={sorted(found - set(contract_by_id))})"
        )

    regions = document.get("executable_regions")
    region_count = 0
    region_ids: set[str] = set()
    if not isinstance(regions, list) or not regions:
        errors.append(
            "surface_dispositions.executable_regions: expected non-empty list"
        )
        regions = []
    for index, region in enumerate(regions):
        location = f"surface_dispositions.executable_regions[{index}]"
        if not exact_keys(
            region, {"id", "path", "start", "end"}, location, errors
        ):
            continue
        region_id = str(region["id"])
        if region_id in region_ids:
            errors.append(f"{location}.id: duplicate {region_id!r}")
        region_ids.add(region_id)
        path_value = region["path"]
        start = region["start"]
        end = region["end"]
        if not all(nonempty_text(item) for item in (path_value, start, end)):
            errors.append(f"{location}: path/start/end must be non-empty text")
            continue
        path = ROOT / path_value
        try:
            source = path.read_text(encoding="utf-8")
        except OSError as exc:
            errors.append(f"{location}.path: cannot read {path_value}: {exc}")
            continue
        if source.count(start) != 1 or source.count(end) != 1:
            errors.append(
                f"{location}: boundary markers must each occur exactly once"
            )
            continue
        left = source.index(start) + len(start)
        right = source.index(end)
        if right <= left:
            errors.append(f"{location}: end marker must follow start marker")
            continue
        leaked = scan_everyday_source(source[left:right], reserved)
        if leaked:
            errors.append(f"{location}: everyday source leaks {leaked}")
        region_count += 1
    return migrated, region_count


def _presentation_module(errors: list[str]) -> Any:
    if str(LIB_PATH) not in sys.path:
        sys.path.insert(0, str(LIB_PATH))
    try:
        from dw_pmo import presentation
    except Exception as exc:  # pragma: no cover - reported as contract error
        errors.append(f"runtime presentation module cannot import: {exc}")
        return None
    return presentation


def validate_runtime_catalog(
    contract: dict[str, Any],
    preferred: dict[str, str],
    errors: list[str],
) -> Any:
    presentation = _presentation_module(errors)
    if presentation is None:
        return None
    definitions = {
        str(item.get("id")): str(item.get("definition"))
        for item in contract.get("concepts", [])
        if isinstance(item, dict)
    }
    runtime = presentation.PRODUCT_CONCEPTS
    if set(runtime) != set(preferred):
        errors.append(
            "runtime presentation concepts differ from the reviewed contract"
        )
    for concept_id, name in preferred.items():
        item = runtime.get(concept_id)
        if not isinstance(item, dict):
            continue
        if item.get("preferred") != name:
            errors.append(
                f"runtime presentation preferred name differs: {concept_id}"
            )
        if item.get("definition") != definitions.get(concept_id):
            errors.append(
                f"runtime presentation definition differs: {concept_id}"
            )
    projection = contract.get("projection")
    technical_label = (
        projection.get("technical_view_label")
        if isinstance(projection, dict)
        else None
    )
    if presentation.TECHNICAL_DETAILS_LABEL != technical_label:
        errors.append("runtime presentation Technical details label drifted")
    catalog = presentation.build_presentation_catalog()
    if (
        catalog.get("kind") != presentation.PRESENTATION_KIND
        or catalog.get("schema_version")
        != presentation.PRESENTATION_SCHEMA_VERSION
        or catalog.get("surface") != "catalog"
    ):
        errors.append("runtime presentation catalog stamp is unsupported")
    for flag in (
        "starts_work",
        "writes_state",
        "selects_next_work",
        "grants_permission",
    ):
        if catalog.get(flag) is not False:
            errors.append(f"runtime presentation catalog.{flag}: must be false")
    try:
        shell = (ROOT / "pmo-roadmap/workbench/index.html").read_text(
            encoding="utf-8"
        )
    except OSError as exc:
        errors.append(f"workbench shell cannot be read: {exc}")
    else:
        fallbacks = dict(
            re.findall(
                r'data-presentation-copy="([a-z_]+)"[^>]*>([^<]+)</a>',
                shell,
            )
        )
        for copy_id, fallback in fallbacks.items():
            if catalog["copy"].get(copy_id) != fallback:
                errors.append(
                    f"workbench fallback copy differs: {copy_id}"
                )
    return presentation


def validate_snapshots(
    snapshots: dict[str, Any],
    presentation: Any,
    preferred: dict[str, str],
    reserved: list[tuple[str, re.Pattern[str]]],
    errors: list[str],
) -> int:
    exact_keys(
        snapshots,
        {"kind", "schema_version", "cases"},
        "snapshots",
        errors,
    )
    if (
        snapshots.get("kind")
        != "delivery-workbench-everyday-presentation-snapshots"
    ):
        errors.append("snapshots.kind: unsupported kind")
    if snapshots.get("schema_version") != 1:
        errors.append("snapshots.schema_version: only version 1 is supported")
    cases = snapshots.get("cases")
    if not isinstance(cases, list) or not cases:
        errors.append("snapshots.cases: expected non-empty list")
        return 0
    if presentation is None:
        return len(cases)
    builders = {
        "status": lambda value, _aux: presentation.build_status_presentation(
            value
        ),
        "step": lambda value, _aux: presentation.build_step_presentation(
            value
        ),
        "step-result": (
            lambda value, _aux:
            presentation.build_step_result_presentation(value)
        ),
        "live": lambda value, _aux: presentation.build_live_presentation(
            value
        ),
        "start": lambda value, _aux: presentation.build_start_presentation(
            value
        ),
        "action": lambda value, aux: presentation.build_action_presentation(
            value, aux
        ),
        "notification": (
            lambda value, _aux:
            presentation.build_notification_presentation(value)
        ),
    }
    found_builders: set[str] = set()
    found_concepts: set[str] = set()
    seen: set[str] = set()
    expected_keys = {
        "kind",
        "schema_version",
        "surface",
        "source",
        "title",
        "summary",
        "sections",
        "next_step",
        "technical_details",
        "starts_work",
        "writes_state",
        "selects_next_work",
        "grants_permission",
    }
    for index, case in enumerate(cases):
        location = f"snapshots.cases[{index}]"
        if not exact_keys(
            case,
            {"id", "builder", "input", "auxiliary", "expected"},
            location,
            errors,
        ):
            continue
        case_id = str(case["id"])
        if case_id in seen:
            errors.append(f"{location}.id: duplicate {case_id!r}")
        seen.add(case_id)
        builder_name = str(case["builder"])
        builder = builders.get(builder_name)
        if builder is None:
            errors.append(f"{location}.builder: unsupported {builder_name!r}")
            continue
        found_builders.add(builder_name)
        source_before = copy.deepcopy(case["input"])
        auxiliary_before = copy.deepcopy(case["auxiliary"])
        try:
            first = builder(case["input"], case["auxiliary"])
            second = builder(case["input"], case["auxiliary"])
            rendered = presentation.render_presentation(first)
        except Exception as exc:
            errors.append(f"{location}: presenter failed: {exc}")
            continue
        if first != second:
            errors.append(f"{location}: presentation is not repeatable")
        if (
            case["input"] != source_before
            or case["auxiliary"] != auxiliary_before
        ):
            errors.append(f"{location}: presenter mutated its source facts")
        if set(first) != expected_keys:
            errors.append(f"{location}: presentation document keys drifted")
        if rendered != case["expected"]:
            errors.append(f"{location}: rendered snapshot differs")
        if rendered.count("Technical details:\n") != 1:
            errors.append(
                f"{location}: rendered output needs one Technical details boundary"
            )
            everyday = rendered
        else:
            everyday = rendered.split("Technical details:\n", 1)[0]
        leaked = scan_everyday(everyday, reserved)
        if leaked:
            errors.append(f"{location}: everyday output leaks {leaked}")
        for flag in (
            "starts_work",
            "writes_state",
            "selects_next_work",
            "grants_permission",
        ):
            if first.get(flag) is not False:
                errors.append(f"{location}.{flag}: must be false")
        for section_index, section in enumerate(first.get("sections") or []):
            if not isinstance(section, dict):
                errors.append(
                    f"{location}.sections[{section_index}]: expected object"
                )
                continue
            found_concepts.update(str(item) for item in section.get("concepts") or [])
            source = section.get("source")
            if (
                not isinstance(source, dict)
                or not nonempty_text(source.get("model"))
                or not nonempty_text(source.get("path"))
            ):
                errors.append(
                    f"{location}.sections[{section_index}].source: "
                    "expected model and path"
                )
    if found_builders != set(builders):
        errors.append(
            "snapshots.cases: every shared presenter requires a snapshot"
        )
    if found_concepts != set(preferred):
        errors.append(
            "snapshots.cases: concept coverage differs "
            f"(missing={sorted(set(preferred) - found_concepts)}, "
            f"extra={sorted(found_concepts - set(preferred))})"
        )
    return len(cases)


def validate_runtime_wiring(errors: list[str]) -> None:
    required = {
        "pmo-roadmap/lib/dw_pmo/status.py": [
            "build_status_presentation",
            "render_presentation",
        ],
        "pmo-roadmap/lib/dw_pmo/step.py": [
            "build_step_presentation",
            "render_presentation",
        ],
        "pmo-roadmap/lib/dw_pmo/notifications.py": [
            "build_notification_presentation",
            "render_presentation",
        ],
        "pmo-roadmap/lib/dw_pmo/workbench.py": [
            'parts == ["api", "presentation"]',
            'parts == ["api", "presentation", "status"]',
        ],
        "pmo-roadmap/bin/dw": [
            "build_start_presentation",
            "build_live_presentation",
            "build_action_presentation",
            "build_step_result_presentation",
            'help_text("cli")',
        ],
        "pmo-roadmap/workbench/app.js": [
            'api(`/api/presentation/status${projectQuery}`)',
            'api("/api/presentation")',
            "data-presentation-copy",
        ],
    }
    for path_value, needles in required.items():
        path = ROOT / path_value
        try:
            source = path.read_text(encoding="utf-8")
        except OSError as exc:
            errors.append(f"{path_value}: cannot read for runtime wiring: {exc}")
            continue
        for needle in needles:
            if needle not in source:
                errors.append(
                    f"{path_value}: shared presentation wiring missing {needle!r}"
                )


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
        if "./docs/everyday-delivery.md" not in readme:
            errors.append("README.md: missing everyday-delivery guide link")
    try:
        everyday = EVERYDAY_GUIDE_PATH.read_text(encoding="utf-8")
    except OSError as exc:
        errors.append(
            f"{EVERYDAY_GUIDE_PATH.relative_to(ROOT)}: cannot read: {exc}"
        )
    else:
        for required in (
            "Arrive and find the current work",
            "Choose the delivery shape",
            "Review the delivery plan",
            "Follow live progress",
            "Resolve a blocker or decision",
            "Complete and prove the work",
            "Technical details",
        ):
            if required not in everyday:
                errors.append(
                    f"{EVERYDAY_GUIDE_PATH.relative_to(ROOT)}: "
                    f"missing task {required!r}"
                )
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
    dispositions = load_json(SURFACE_DISPOSITIONS_PATH, errors)
    snapshots = load_json(SNAPSHOT_PATH, errors)
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
    migrated_count, region_count = validate_surface_dispositions(
        dispositions, surfaces, reserved, errors
    )
    presentation = validate_runtime_catalog(contract, preferred, errors)
    snapshot_count = validate_snapshots(
        snapshots, presentation, preferred, reserved, errors
    )
    validate_runtime_wiring(errors)

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
        f"{migrated_count} migrated, {len(reserved)} reserved terms, "
        f"{case_count} fixtures, {snapshot_count} snapshots, "
        f"{region_count} source regions)"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
