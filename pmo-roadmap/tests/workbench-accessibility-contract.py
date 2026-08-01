#!/usr/bin/env python3
"""Validate the Phase 27 keyboard, viewport, and assistive-use evidence.

The browser exam proves behavior against live fixture servers. This checker
keeps its reviewed journey matrix complete and prevents the semantic/focus
contracts from becoming unreferenced prose.
"""

from __future__ import annotations

import copy
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
TESTS = ROOT / "pmo-roadmap" / "tests"
MANIFEST_PATH = TESTS / "accessibility-journeys-v1.json"
JOURNEYS_PATH = TESTS / "fixtures" / "usability" / "journeys-v1.json"
STATES_PATH = TESTS / "fixtures" / "usability" / "states-v1.json"
BROWSER_PATH = TESTS / "workbench-accessibility.py"
INDEX_PATH = ROOT / "pmo-roadmap" / "workbench" / "index.html"
APP_DIR = ROOT / "pmo-roadmap" / "workbench"
CSS_PATH = ROOT / "pmo-roadmap" / "workbench" / "style.css"
DOC_PATH = ROOT / "docs" / "accessibility.md"

REQUIRED_JOURNEY_FIELDS = {
    "id",
    "state_id",
    "suite",
    "keyboard_path",
    "focus_contract",
    "semantics",
    "layout_review",
    "live_update_contract",
    "manual_review",
}
REQUIRED_MANUAL_FIELDS = {"wide", "narrow", "assistive", "result"}


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path.relative_to(ROOT)}: root must be an object")
    return value


def text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def text_list(value: Any, minimum: int = 1) -> bool:
    return (
        isinstance(value, list)
        and len(value) >= minimum
        and all(text(item) for item in value)
    )


def validate(
    manifest: dict[str, Any],
    journey_contract: dict[str, Any],
    states_contract: dict[str, Any],
) -> list[str]:
    issues: list[str] = []
    if manifest.get("kind") != "delivery-workbench-accessibility-journeys":
        issues.append("manifest-kind-invalid")
    if manifest.get("schema_version") != 1:
        issues.append("manifest-version-invalid")
    if not text(manifest.get("reviewed_at")):
        issues.append("review-date-missing")
    if not text_list(manifest.get("browser_matrix"), 2):
        issues.append("browser-matrix-incomplete")
    if not text(manifest.get("manual_review_method")):
        issues.append("manual-method-missing")

    viewports = manifest.get("viewports")
    expected_viewports = {
        "wide": {"width": 1440, "height": 900},
        "narrow": {"width": 390, "height": 844},
    }
    if viewports != expected_viewports:
        issues.append("viewport-matrix-invalid")

    expected = {
        item["id"]: item["starting_state"]
        for item in journey_contract.get("journeys", [])
        if isinstance(item, dict) and text(item.get("id"))
    }
    states = {
        item["id"]: item
        for item in states_contract.get("states", [])
        if isinstance(item, dict) and text(item.get("id"))
    }
    entries = manifest.get("journeys")
    if not isinstance(entries, list):
        return issues + ["journeys-not-list"]

    actual: dict[str, dict[str, Any]] = {}
    for index, item in enumerate(entries):
        where = f"journeys[{index}]"
        if not isinstance(item, dict):
            issues.append(f"journey-shape-invalid:{where}")
            continue
        missing = REQUIRED_JOURNEY_FIELDS - set(item)
        if missing:
            issues.append(f"journey-fields-missing:{where}:{','.join(sorted(missing))}")
        journey_id = item.get("id")
        if not text(journey_id):
            issues.append(f"journey-id-invalid:{where}")
            continue
        if journey_id in actual:
            issues.append(f"journey-duplicate:{journey_id}")
        actual[journey_id] = item
        state_id = item.get("state_id")
        if state_id != expected.get(journey_id):
            issues.append(f"journey-state-mismatch:{journey_id}")
        if state_id not in states:
            issues.append(f"journey-state-missing:{journey_id}")
        if item.get("suite") not in {"core", "program"}:
            issues.append(f"journey-suite-invalid:{journey_id}")
        for field, minimum in (
            ("keyboard_path", 3),
            ("focus_contract", 3),
            ("semantics", 3),
            ("layout_review", 2),
        ):
            if not text_list(item.get(field), minimum):
                issues.append(f"journey-{field}-incomplete:{journey_id}")
        if not text(item.get("live_update_contract")):
            issues.append(f"journey-live-contract-missing:{journey_id}")
        manual = item.get("manual_review")
        if not isinstance(manual, dict) or set(manual) != REQUIRED_MANUAL_FIELDS:
            issues.append(f"journey-manual-shape-invalid:{journey_id}")
        else:
            for field in ("wide", "narrow", "assistive"):
                if not text(manual.get(field)) or "pass" not in manual[field].lower():
                    issues.append(f"journey-manual-{field}-missing:{journey_id}")
            if manual.get("result") != "pass":
                issues.append(f"journey-manual-result-not-pass:{journey_id}")

    missing_ids = set(expected) - set(actual)
    extra_ids = set(actual) - set(expected)
    if missing_ids:
        issues.append(f"journey-coverage-missing:{','.join(sorted(missing_ids))}")
    if extra_ids:
        issues.append(f"journey-coverage-extra:{','.join(sorted(extra_ids))}")

    # Every canonical state must still point at a real route and capture.
    for journey_id, item in actual.items():
        state = states.get(item.get("state_id"), {})
        if not text(state.get("route")) or not text(state.get("capture_id")):
            issues.append(f"journey-state-unreachable:{journey_id}")

    return issues


def validate_sources(expected_ids: set[str]) -> list[str]:
    issues: list[str] = []
    index = INDEX_PATH.read_text(encoding="utf-8")
    app = "\n".join(f.read_text(encoding="utf-8") for f in sorted(APP_DIR.glob("*.js")))
    css = CSS_PATH.read_text(encoding="utf-8")
    browser = BROWSER_PATH.read_text(encoding="utf-8")
    documentation = DOC_PATH.read_text(encoding="utf-8")

    for marker in (
        'id="skip-link"',
        'aria-label="Primary"',
        'aria-label="Breadcrumb"',
        'id="route-status"',
        'id="live-status"',
        'aria-busy="true"',
    ):
        if marker not in index:
            issues.append(f"shell-marker-missing:{marker}")
    for marker in (
        "captureAppFocus",
        "restoreAppFocus",
        "rememberReturnFocus",
        "restoreReturnFocus",
        "wireDismissibleRegion",
        "enhanceSemantics",
        "announceLiveUpdate",
        "wireTablist",
        "wireArrowGroup",
        "focusMain: true",
        'role="dialog"',
        'role="tablist"',
        'role="tabpanel"',
    ):
        if marker not in app:
            issues.append(f"app-marker-missing:{marker}")
    for marker in (
        ":focus-visible",
        ".skip-link",
        "[aria-current=\"page\"]",
        "[role=\"dialog\"]",
        "@media (prefers-reduced-motion: reduce)",
        "@media (forced-colors: active)",
        "overflow-x: clip",
        "overflow-wrap: anywhere",
    ):
        if marker not in css:
            issues.append(f"css-marker-missing:{marker}")
    for marker in (
        "WebDriver:SetWindowRect",
        "WebDriver:PerformActions",
        "audit_page",
        "assert_focus_preserved",
        "assert_dialog_round_trip",
        "wide",
        "narrow",
    ):
        if marker not in browser:
            issues.append(f"browser-marker-missing:{marker}")
    for journey_id in expected_ids:
        if journey_id not in browser:
            issues.append(f"browser-journey-missing:{journey_id}")
    for marker in (
        "Keyboard contract",
        "Focus and dynamic updates",
        "Assistive semantics",
        "Viewport contract",
        "Manual review record",
    ):
        if marker not in documentation:
            issues.append(f"documentation-marker-missing:{marker}")
    return issues


def planted_red_cases(
    manifest: dict[str, Any],
    journey_contract: dict[str, Any],
    states_contract: dict[str, Any],
) -> list[str]:
    failures: list[str] = []

    missing = copy.deepcopy(manifest)
    missing["journeys"] = missing["journeys"][:-1]
    if not any(
        item.startswith("journey-coverage-missing:")
        for item in validate(missing, journey_contract, states_contract)
    ):
        failures.append("planted missing journey was accepted")

    failed_review = copy.deepcopy(manifest)
    failed_review["journeys"][0]["manual_review"]["result"] = "fail"
    if not any(
        item.startswith("journey-manual-result-not-pass:")
        for item in validate(failed_review, journey_contract, states_contract)
    ):
        failures.append("planted failed manual review was accepted")

    wrong_state = copy.deepcopy(manifest)
    wrong_state["journeys"][0]["state_id"] = "capability-choice"
    if not any(
        item.startswith("journey-state-mismatch:")
        for item in validate(wrong_state, journey_contract, states_contract)
    ):
        failures.append("planted state mismatch was accepted")

    wrong_viewport = copy.deepcopy(manifest)
    wrong_viewport["viewports"]["narrow"]["width"] = 640
    if "viewport-matrix-invalid" not in validate(
        wrong_viewport, journey_contract, states_contract
    ):
        failures.append("planted viewport drift was accepted")
    return failures


def main() -> int:
    manifest = load(MANIFEST_PATH)
    journey_contract = load(JOURNEYS_PATH)
    states_contract = load(STATES_PATH)
    expected_ids = {
        item["id"] for item in journey_contract.get("journeys", [])
    }
    issues = validate(manifest, journey_contract, states_contract)
    issues.extend(validate_sources(expected_ids))
    issues.extend(
        f"red-case-failed:{item}"
        for item in planted_red_cases(manifest, journey_contract, states_contract)
    )
    if issues:
        for item in issues:
            print(f"workbench-accessibility-contract.py: {item}", file=sys.stderr)
        return 1
    print(
        "workbench-accessibility-contract.py: ok "
        f"({len(expected_ids)} journeys, 2 viewports, "
        "keyboard/focus/semantics/manual evidence)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
