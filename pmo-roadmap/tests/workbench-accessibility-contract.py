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
MEMORY_PATH = ROOT / "pmo-roadmap" / "workbench" / "memory-panel.js"
CORE_PATH = ROOT / "pmo-roadmap" / "workbench" / "core.js"
ROUTER_PATH = ROOT / "pmo-roadmap" / "workbench" / "app.js"
INTERACTIONS_PATH = ROOT / "pmo-roadmap" / "workbench" / "interactions.js"
GLOBAL_EVENTS_PATH = ROOT / "pmo-roadmap" / "workbench" / "global-events.js"
EDITOR_PATH = ROOT / "pmo-roadmap" / "workbench" / "editor.js"
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
        "focusVisible: true",
        "focus-restored",
        "focusMain: true",
        'role="dialog"',
        'role="tablist"',
        'role="tabpanel"',
    ):
        if marker not in app:
            issues.append(f"app-marker-missing:{marker}")
    for marker in (
        ":where(a, button, input, select, textarea, summary, [tabindex]):focus",
        ".skip-link:focus",
        "[aria-current=\"page\"]",
        "[role=\"dialog\"]",
        "@media (prefers-reduced-motion: reduce)",
        "@media (forced-colors: active)",
        "overflow-x: clip",
        "overflow-wrap: anywhere",
    ):
        if marker not in css:
            issues.append(f"css-marker-missing:{marker}")
    for reset in ("outline: none", "outline:none"):
        if reset in css:
            issues.append(f"css-outline-reset-present:{reset}")
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


def validate_memory_panel() -> list[str]:
    """Keep the AgentGlass pane connected to every promised shell surface."""
    issues: list[str] = []
    if not MEMORY_PATH.is_file():
        return ["memory-panel-missing"]

    memory = MEMORY_PATH.read_text(encoding="utf-8")
    index = INDEX_PATH.read_text(encoding="utf-8")
    css = CSS_PATH.read_text(encoding="utf-8")
    sources = {
        name: (APP_DIR / name).read_text(encoding="utf-8")
        for name in (
            "runs.js", "session-panel.js", "outcomes-panel.js",
            "needs-you.js", "command-palette.js",
        )
    }

    checks = {
        "memory-shell-load": 'src="memory-panel.js"' in index,
        "memory-custom-panel": 'document.createElement("dw-panel")' in memory,
        "memory-dialog-label": 'setAttribute("role", "dialog")' in memory,
        "memory-non-modal": 'setAttribute("aria-modal", "false")' in memory,
        "memory-focus-return": "rememberReturnFocus(\"memory-panel\"" in memory,
        "memory-escape-close": 'event.key !== "Escape"' in memory,
        "memory-run-route": "/api/${kind === \"program\" ? \"programs\" : \"runs\"}" in memory,
        "memory-summary-recall-time": "Recall time" in memory,
        "memory-summary-freshness": "Freshness" in memory,
        "memory-summary-included": "Included" in memory,
        "memory-summary-excluded": "Excluded" in memory,
        "memory-summary-sources": "Sources" in memory,
        "memory-summary-writeback": "Writeback" in memory,
        "memory-available-language": "Available to the agent" in memory,
        "memory-decision-language": "Referenced by a decision" in memory,
        "memory-writeback-language": "Written after completion" in memory,
        "memory-no-causation": "never caused or permitted an action" in memory,
        "memory-match-reasons": "match_reasons" in memory,
        "memory-source-path": "receipt_path" in memory and "ledger_coordinates" in memory,
        "memory-supersession": "Supersession" in memory,
        "memory-refusal-missing": "missing:" in memory,
        "memory-refusal-stale": "stale:" in memory,
        "memory-refusal-tampered": "tampered:" in memory,
        "memory-empty-state": "No memory records yet" in memory,
        "memory-technical-fold": '<dw-fold label=\"Technical details\">' in memory,
        "memory-run-entry": 'data-memory-kind=\"run\"' in sources["runs.js"],
        "memory-program-entry": 'data-memory-kind=\"program\"' in sources["runs.js"],
        "memory-session-entry": "session-memory-btn" in sources["session-panel.js"],
        "memory-outcomes-entry": "outcomes-memory" in sources["outcomes-panel.js"],
        "memory-needs-you-entry": "needs-you-memory" in sources["needs-you.js"],
        "memory-palette-entry": 'category: "memory"' in sources["command-palette.js"],
        "decision-timeline-heading": 'id="decision-basis-title"' in memory,
        "decision-timeline-list": 'class="decision-basis-list"' in memory,
        "decision-native-button": 'type="button" class="decision-basis-select"' in memory,
        "decision-selection-state": 'aria-pressed=' in memory,
        "decision-selected-region": 'role="region" aria-label="Selected decision basis"' in memory,
        "decision-origin-link": 'class="decision-origin-link"' in memory,
        "decision-authority-labels": all(
            marker in memory
            for marker in (
                "mechanical", "agent-reported", "panel-derived", "operator-supplied",
            )
        ),
        "decision-authority-distinction": "mechanical checks are not model or council judgments" in memory,
        "decision-memory-highlight": "decision-memory-highlight" in memory and "data-recall-id" in memory,
        "decision-sse-event-id-dedup": "_decisionByEventId" in memory and "event_id" in memory,
        "decision-session-stream": "_refreshDecisions" in sources["session-panel.js"] and "_eventId" in sources["session-panel.js"],
        "memory-narrow-layout": "@media (max-width: 520px)" in css and ".memory-panel" in css,
        "memory-theme-tokens": all(
            marker in css
            for marker in (
                ".memory-panel", "var(--surface-panel)",
                "var(--text-primary)", "var(--border-standard)",
            )
        ),
    }
    for name, passed in checks.items():
        if not passed:
            issues.append(f"{name}-missing")
    return issues


def validate_slick_workbench() -> list[str]:
    """Pin the WLA-35-09 speed, motion, density, and recovery contracts."""
    index = INDEX_PATH.read_text(encoding="utf-8")
    css = CSS_PATH.read_text(encoding="utf-8")
    core = CORE_PATH.read_text(encoding="utf-8")
    router = ROUTER_PATH.read_text(encoding="utf-8")
    interactions = INTERACTIONS_PATH.read_text(encoding="utf-8")
    events = GLOBAL_EVENTS_PATH.read_text(encoding="utf-8")
    memory = MEMORY_PATH.read_text(encoding="utf-8")
    editor = EDITOR_PATH.read_text(encoding="utf-8")
    browser = BROWSER_PATH.read_text(encoding="utf-8")
    checks = {
        "slick-shell-skeleton": "route-skeleton" in index and "routeSkeletonHtml" in router,
        "slick-incremental-route": "updateRouteSkeleton" in router and "Promise" in router,
        "slick-sync-snapshot-guard": "if (!SNAPSHOT_MODE)" in core and 'xhr.open("GET", path, false)' in core,
        "slick-density-control": 'id="density-toggle"' in index and "applyDensity" in core,
        "slick-density-persistence": "DENSITY_STORAGE_KEY" in core and "localStorage.setItem" in core and "test_slick_workbench" in browser,
        "slick-density-modes": ':root[data-density="compact"]' in css and '"comfortable"' in core,
        "slick-density-targets": "--target-min" in css and "min-block-size: var(--target-min)" in css,
        "slick-motion-tokens": all(token in css for token in ("--motion-short", "--motion-panel", "--motion-route", "--motion-ease")),
        "slick-motion-manager": "motionDuration" in interactions and "--motion-panel" in interactions,
        "slick-reduced-motion": "animation: none !important" in css and "transition-duration: 0s !important" in css and "set_reduced_motion" in browser,
        "slick-reconnect-states": all(state in events for state in ("disconnected", "retrying", "caught-up", "restored")),
        "slick-reconnect-announcement": "announceLiveUpdate" in events and 'new CustomEvent("dw-stream-state"' in events,
        "slick-subscriber-cap": "response.status === 503" in events and "Retry in a moment" in events,
        "slick-copy-action": "dataset.copyText" in core and "copyToClipboard" in core,
        "slick-memory-copy": "copyableIdentifierHtml" in memory and "originating_receipt_ref" in memory,
        "slick-copy-feedback": "Identifier copied." in core and "Could not copy" in core,
        "slick-form-description": "aria-describedby" in editor and "aria-invalid" in editor,
        "slick-project-error-description": 'aria-describedby="project-selector-error"' in core,
        "slick-bounded-identifiers": ".copyable-id" in css and "overflow-wrap: anywhere" in css,
        "slick-no-body-overflow": "overflow-x: clip" in css and "max-width: 100%" in css,
    }
    return [f"{name}-missing" for name, passed in checks.items() if not passed]


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
    issues.extend(validate_memory_panel())
    issues.extend(validate_slick_workbench())
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
        f"({len(expected_ids)} journeys, 2 viewports, 45 memory-pane checks, "
        "20 slick-workbench checks, keyboard/focus/semantics/manual evidence)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
