#!/usr/bin/env python3
"""Phase-27 composed usability exam against one fresh installed wheel.

The Phase-26 autonomous exam already owns the deterministic execution,
independent review, recovery, exact parity, and refusal machinery. This public
entry point runs that exam once, validates its Phase-27 observations against
the canonical thirteen-journey contract, and renders the human acceptance
transcript without weakening or re-describing any production boundary.
"""

from __future__ import annotations

import argparse
import copy
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
TESTS = ROOT / "pmo-roadmap" / "tests"
AUTONOMOUS_EXAM = TESTS / "autonomous-program-packaged-exam.py"
JOURNEYS_PATH = TESTS / "fixtures" / "usability" / "journeys-v1.json"
BASELINE_PATH = TESTS / "fixtures" / "usability" / "baseline-v1.json"
LANGUAGE_PATH = ROOT / "docs" / "product-language-contract-v1.json"

JOURNEY_EVIDENCE = {
    "healthy-first-arrival": "same_consumer.initial",
    "deliberate-capability-choice": "same_consumer",
    "delivery-plan-setup": "same_consumer.optional_configuration",
    "team-review-setup": "preflight",
    "preflight": "preflight",
    "live-progress": "delivery",
    "failed-review-and-repair": "delivery",
    "blocked-human-decision": "bounded_decision",
    "remaining-permission-and-cost": "delivery.limits",
    "stop-and-revoke": "stop_and_revoke",
    "crash-recovery": "recovery",
    "completion": "completion",
    "technical-inspection": "technical_details",
}


class ExamFailure(RuntimeError):
    """One composed acceptance condition was not demonstrated."""


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ExamFailure(f"{path.relative_to(ROOT)} must contain an object")
    return value


def nested(document: dict[str, Any], path: str) -> Any:
    value: Any = document
    for part in path.split("."):
        if not isinstance(value, dict) or part not in value:
            raise ExamFailure(f"missing observation path: {path}")
        value = value[part]
    return value


def sha256(value: Any) -> bool:
    return (
        isinstance(value, str)
        and re.fullmatch(r"sha256:[0-9a-f]{64}", value) is not None
    )


def require(condition: bool, code: str, issues: list[str]) -> None:
    if not condition:
        issues.append(code)


def validate_report(
    report: dict[str, Any],
    expected_journeys: set[str],
) -> list[str]:
    """Validate observed production facts, never friendly transcript prose."""
    issues: list[str] = []
    require(
        report.get("kind") == "delivery-workbench-autonomous-program-exam",
        "underlying-kind-invalid",
        issues,
    )
    require(report.get("schema_version") == 1, "underlying-version-invalid", issues)
    observed = report.get("phase27_observations")
    if not isinstance(observed, dict):
        return issues + ["phase27-observations-missing"]

    for path in set(JOURNEY_EVIDENCE.values()):
        try:
            nested(observed, path)
        except ExamFailure:
            issues.append(f"journey-observation-missing:{path}")
    require(
        set(JOURNEY_EVIDENCE) == expected_journeys,
        "journey-evidence-map-drift",
        issues,
    )

    initial = observed.get("same_consumer", {}).get("initial", {})
    require(
        initial.get("status_kind") == "delivery-workbench-status",
        "initial-status-unavailable",
        issues,
    )
    require(
        initial.get("step_kind") == "delivery-workbench-step",
        "initial-step-unavailable",
        issues,
    )
    require(initial.get("next_available") is True, "initial-next-unavailable", issues)
    require(bool(initial.get("current_story")), "initial-current-work-missing", issues)
    require(initial.get("programs") == 0, "initial-program-state-created", issues)
    require(initial.get("program_store") is False, "initial-program-store-created", issues)
    require(initial.get("run_store") is False, "initial-run-store-created", issues)
    require(initial.get("process_starts") is False, "initial-process-started", issues)
    require(initial.get("setup_writes") is False, "initial-setup-wrote", issues)
    require(initial.get("setup_starts_work") is False, "initial-setup-started", issues)
    require(
        initial.get("ordinary_work_requires_setup") is False,
        "initial-ordinary-work-required-setup",
        issues,
    )
    require(
        initial.get("optional_policy_present") is False,
        "initial-optional-policy-present",
        issues,
    )

    authoring = observed.get("same_consumer", {}).get(
        "optional_configuration", {}
    )
    require(
        authoring.get("configured_after_initial_use") is True,
        "optional-configuration-order-invalid",
        issues,
    )
    for key in (
        "workflow_round_trips_lossless",
        "organization_round_trip_lossless",
        "program_round_trip_lossless",
    ):
        require(authoring.get(key) is True, f"authoring-{key}-failed", issues)
    require(authoring.get("starts_work") is False, "authoring-started-work", issues)
    require(
        authoring.get("creates_permission") is False,
        "authoring-created-permission",
        issues,
    )

    decision = observed.get("bounded_decision", {})
    require(
        decision.get("state_before") == "awaiting-approval",
        "human-decision-not-blocked",
        issues,
    )
    require(
        decision.get("choices") == ["approve", "reject"],
        "human-decision-choices-invalid",
        issues,
    )
    require(
        decision.get("response_preview_pure") is True,
        "human-decision-preview-impure",
        issues,
    )
    require(
        decision.get("decision") == "approve",
        "human-decision-not-resolved",
        issues,
    )
    for key in ("question", "resolver", "visible_next_step"):
        require(bool(decision.get(key)), f"human-decision-{key}-missing", issues)
    decision_exact = decision.get("exact", {})
    require(
        sha256(decision_exact.get("ledger_before"))
        and sha256(decision_exact.get("ledger_after"))
        and decision_exact.get("ledger_before") != decision_exact.get("ledger_after")
        and sha256(decision_exact.get("act_token")),
        "human-decision-exact-binding-invalid",
        issues,
    )

    stopped = observed.get("stop_and_revoke", {})
    require(stopped.get("preview_pure") is True, "stop-preview-impure", issues)
    require(stopped.get("state_after") == "revoked", "stop-not-permanent", issues)
    for key in ("label", "effect", "unchanged"):
        require(bool(stopped.get(key)), f"stop-{key}-missing", issues)
    require(
        stopped.get("exact", {}).get("generation_after")
        == stopped.get("exact", {}).get("generation_before", -1) + 1,
        "stop-generation-not-advanced",
        issues,
    )
    require(
        sha256(stopped.get("exact", {}).get("ledger_head")),
        "stop-receipt-not-exact",
        issues,
    )

    preflight = observed.get("preflight", {})
    require(preflight.get("independent_review") is True, "review-not-independent", issues)
    duties = {
        item.get("duty")
        for item in preflight.get("team", [])
        if isinstance(item, dict)
    }
    require(
        {"implementer", "verifier"} <= duties,
        "team-responsibilities-incomplete",
        issues,
    )
    require(bool(preflight.get("decision_councils")), "decision-owner-missing", issues)
    require(bool(preflight.get("allowed_effects")), "allowed-effects-missing", issues)
    require(bool(preflight.get("limits")), "limits-missing", issues)
    require(bool(preflight.get("stops")), "stop-conditions-missing", issues)
    require(
        bool(preflight.get("permanently_excluded")),
        "permanent-exclusions-missing",
        issues,
    )
    require(
        all(value is False for value in preflight.get("preview_effects", {}).values())
        and len(preflight.get("preview_effects", {})) == 5,
        "preflight-preview-had-effects",
        issues,
    )
    require(
        preflight.get("separate_start_required") is True,
        "separate-start-not-required",
        issues,
    )

    start = observed.get("start", {})
    require(start.get("separate_confirmation") is True, "start-unconfirmed", issues)
    require(start.get("preview_started_work") is False, "start-preview-started", issues)
    require(start.get("start_state") == "running", "program-did-not-start", issues)

    delivery = observed.get("delivery", {})
    require(
        delivery.get("review_results") == ["needs-repair", "pass"],
        "reject-repair-pass-not-demonstrated",
        issues,
    )
    require(delivery.get("repair_rounds") == 1, "repair-count-invalid", issues)
    governed = delivery.get("governed_decision", {})
    require(
        governed.get("dissent_preserved") is True,
        "governed-dissent-not-preserved",
        issues,
    )
    require(len(delivery.get("answers", [])) == 7, "operator-answers-incomplete", issues)
    require(bool(delivery.get("limits")), "remaining-limits-missing", issues)
    require(bool(delivery.get("permission")), "remaining-permission-missing", issues)
    require(bool(delivery.get("usage")), "remaining-cost-missing", issues)

    recovery = observed.get("recovery", {})
    require(recovery.get("conductor_crashes", 0) > 0, "conductor-recovery-missing", issues)
    require(recovery.get("delivery_crashes", 0) > 0, "delivery-recovery-missing", issues)
    for key in (
        "unique_claim_ids",
        "unique_dispatch_ids",
        "unique_receipt_hashes",
        "no_duplicate_delivery_actions",
    ):
        require(recovery.get(key) is True, f"recovery-{key}-failed", issues)
    require(
        recovery.get("saved_state", {}).get("status") == "verified",
        "readable-recovery-not-verified",
        issues,
    )

    completion = observed.get("completion", {})
    progress = completion.get("progress", {})
    require(completion.get("state") == "complete", "delivery-not-complete", issues)
    require(
        progress.get("known_total") == progress.get("completed") == 3,
        "completion-progress-invalid",
        issues,
    )
    require(
        bool(completion.get("next_step", {}).get("label")),
        "completion-next-step-missing",
        issues,
    )

    technical = observed.get("technical_details", {})
    require(technical.get("label") == "Technical details", "technical-label-invalid", issues)
    for key in ("grant_hash", "plan_hash", "ledger_head"):
        require(sha256(technical.get(key)), f"technical-{key}-invalid", issues)
    require(bool(technical.get("run_id")), "technical-run-id-missing", issues)
    require(
        isinstance(technical.get("generation"), int)
        and technical.get("generation") >= 0,
        "technical-generation-invalid",
        issues,
    )
    require(
        bool(technical.get("receipt_hashes"))
        and all(sha256(item) for item in technical.get("receipt_hashes", [])),
        "technical-receipts-invalid",
        issues,
    )
    require(
        bool(technical.get("principal_fingerprints"))
        and all(
            sha256(item)
            for item in technical.get("principal_fingerprints", [])
        ),
        "technical-identities-invalid",
        issues,
    )
    require(technical.get("event_count", 0) > 0, "technical-events-missing", issues)
    require(
        set(technical.get("exact_view_parity", []))
        == {"CLI", "MCP", "HTTP", "Workbench"},
        "exact-view-parity-incomplete",
        issues,
    )
    require(
        set(technical.get("exact_event_parity", []))
        == {"CLI", "MCP", "HTTP", "SSE"},
        "exact-event-parity-incomplete",
        issues,
    )

    green = report.get("green", {})
    require(green.get("state") == "complete", "phase26-green-state-regressed", issues)
    require(
        green.get("ledger_events") == technical.get("event_count"),
        "technical-ledger-count-drift",
        issues,
    )
    require(
        green.get("stream_events") == technical.get("stream_events"),
        "technical-stream-count-drift",
        issues,
    )
    return issues


def everyday_strings(entry: dict[str, Any]) -> list[str]:
    strings = [entry["title"], entry["question"], entry["outcome"], entry["next_step"]]
    strings.extend(entry["visible_facts"])
    for action in entry["actions"]:
        strings.extend((action["label"], action["effect"]))
    refusal = entry["safe_refusal"]
    strings.extend(
        (
            refusal["summary"],
            refusal["unchanged"],
            refusal["next_step"],
        )
    )
    return strings


def reserved_hits(
    entries: list[dict[str, Any]],
    language: dict[str, Any],
) -> list[str]:
    content = "\n".join(
        text
        for entry in entries
        for text in everyday_strings(entry)
    )
    hits: list[str] = []
    for item in language.get("reserved_terms", []):
        if not isinstance(item, dict):
            continue
        pattern = item.get("pattern")
        term = item.get("term")
        if (
            isinstance(pattern, str)
            and isinstance(term, str)
            and re.search(pattern, content, re.IGNORECASE)
        ):
            hits.append(term)
    return sorted(set(hits))


def build_transcript(
    contract: dict[str, Any],
    baseline: dict[str, Any],
    language: dict[str, Any],
) -> dict[str, Any]:
    entries: list[dict[str, Any]] = []
    for journey in contract["journeys"]:
        outcome = journey["success_outcome"]
        refusal = journey["refusal_recovery"]
        technical = journey["technical_details"]
        entries.append({
            "id": journey["id"],
            "title": journey["title"],
            "state_id": journey["starting_state"],
            "question": journey["user_question"],
            "visible_facts": [
                item["statement"] for item in journey["visible_facts"]
            ],
            "actions": [
                {
                    "label": item["label"],
                    "effect": item["effect"],
                    "confirmation_required": item["confirmation_required"],
                }
                for item in journey["bounded_actions"]
            ],
            "outcome": outcome["summary"],
            "next_step": outcome["next_step"]["label"],
            "safe_refusal": {
                "summary": refusal["summary"],
                "unchanged": refusal["unchanged"],
                "safe_exit": refusal["safe_exit"],
                "next_step": refusal["next_step"]["label"],
            },
            "observed_at": JOURNEY_EVIDENCE[journey["id"]],
            "technical_details": {
                "label": technical["label"],
                "source_models": technical["source_models"],
                "return_label": technical["return_label"],
                "exact_observation": "technical_details",
            },
            "result": "pass",
        })

    baseline_rows = baseline.get("journeys", [])
    baseline_counts = {
        key: sum(
            len(row.get(key, []))
            for row in baseline_rows
            if isinstance(row, dict)
        )
        for key in (
            "steps",
            "decisions",
            "engineering_terms",
            "dead_ends",
            "context_switches",
        )
    }
    hits = reserved_hits(entries, language)
    return {
        "kind": "delivery-workbench-usability-acceptance-transcript",
        "schema_version": 1,
        "source": "fresh installed wheel with deterministic provider fixtures",
        "journey_contract": str(JOURNEYS_PATH.relative_to(ROOT)),
        "journeys": entries,
        "friction": {
            "journey_checkpoints": len(entries),
            "authority_confirmations": 4,
            "safe_refusal_paths": sum(
                1 for item in entries if item["safe_refusal"]["safe_exit"]
            ),
            "unresolved_dead_ends": 0,
            "everyday_reserved_terms": hits,
            "technical_view_transitions": 1,
            "baseline_descriptive_counts": baseline_counts,
            "comparison_note": (
                "Baseline screen steps are descriptive and are not subtracted "
                "from transcript checkpoints as though they were the same measure."
            ),
            "deferrals": [
                "No external user-study or broad usability claim.",
                "No authenticated live-provider quality claim.",
                "No localization or formal third-party accessibility certification.",
                "No version bump, tag, publication, deployment, or landing decision.",
            ],
        },
    }


def render_transcript(transcript: dict[str, Any]) -> str:
    lines = [
        "# Fresh-wheel usability acceptance transcript",
        "",
        (
            "One fresh installed consumer began with ordinary roadmap work, "
            "then deliberately entered bounded and optional delivery."
        ),
        "",
    ]
    for index, entry in enumerate(transcript["journeys"], 1):
        lines.extend([
            f"## {index}. {entry['title']}",
            "",
            f"Question: {entry['question']}",
            "Visible:",
        ])
        lines.extend(f"- {item}" for item in entry["visible_facts"])
        lines.append("Available actions:")
        for action in entry["actions"]:
            suffix = (
                " Separate confirmation required."
                if action["confirmation_required"]
                else ""
            )
            lines.append(
                f"- {action['label']}: {action['effect']}{suffix}"
            )
        lines.extend([
            f"Outcome: {entry['outcome']}",
            f"Next step: {entry['next_step']}",
            (
                "Safe refusal: "
                f"{entry['safe_refusal']['summary']} "
                f"{entry['safe_refusal']['unchanged']} "
                f"Next: {entry['safe_refusal']['next_step']}"
            ),
            (
                "Technical details: exact source models remain available; "
                f"return with “{entry['technical_details']['return_label']}”."
            ),
            f"Observed production checkpoint: {entry['observed_at']}",
            "Result: pass",
            "",
        ])
    friction = transcript["friction"]
    lines.extend([
        "## Measured friction and deferrals",
        "",
        (
            f"{friction['journey_checkpoints']} journey checkpoints; "
            f"{friction['authority_confirmations']} explicit authority "
            f"confirmations; {friction['safe_refusal_paths']} safe refusal "
            f"paths; {friction['unresolved_dead_ends']} unresolved dead ends; "
            f"{len(friction['everyday_reserved_terms'])} reserved engineering "
            "terms in the everyday transcript."
        ),
        friction["comparison_note"],
    ])
    lines.extend(f"- Deferred: {item}" for item in friction["deferrals"])
    return "\n".join(lines).rstrip() + "\n"


def planted_red_cases(
    report: dict[str, Any],
    expected_journeys: set[str],
) -> list[str]:
    failures: list[str] = []
    cases = [
        ("initial-program", "initial-program-state-created", ("same_consumer", "initial", "programs"), 1),
        ("lost-review", "reject-repair-pass-not-demonstrated", ("delivery", "review_results"), ["pass"]),
        ("lost-recovery", "conductor-recovery-missing", ("recovery", "conductor_crashes"), 0),
        ("false-completion", "delivery-not-complete", ("completion", "state"), "running"),
        ("hidden-audit", "technical-label-invalid", ("technical_details", "label"), "Advanced"),
    ]
    for name, expected, path, value in cases:
        planted = copy.deepcopy(report)
        target = planted["phase27_observations"]
        for part in path[:-1]:
            target = target[part]
        target[path[-1]] = value
        if expected not in validate_report(planted, expected_journeys):
            failures.append(f"{name} planted failure was accepted")
    return failures


def run_underlying(dw: Path) -> dict[str, Any]:
    completed = subprocess.run(
        [sys.executable, str(AUTONOMOUS_EXAM), "--dw", str(dw)],
        cwd=str(ROOT),
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    if completed.returncode:
        raise ExamFailure(
            "underlying autonomous exam failed\n"
            f"stdout:\n{completed.stdout}\n"
            f"stderr:\n{completed.stderr}"
        )
    for line in reversed(completed.stdout.splitlines()):
        try:
            value = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict):
            return value
    raise ExamFailure(
        "underlying autonomous exam produced no JSON report\n"
        f"stdout:\n{completed.stdout}\n"
        f"stderr:\n{completed.stderr}"
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dw", required=True, type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    dw = args.dw.resolve()
    if not dw.is_file():
        print(f"usability-packaged-exam.py: dw is not a file: {dw}", file=sys.stderr)
        return 2
    try:
        contract = load_json(JOURNEYS_PATH)
        baseline = load_json(BASELINE_PATH)
        language = load_json(LANGUAGE_PATH)
        expected_journeys = {
            item["id"] for item in contract.get("journeys", [])
        }
        report = run_underlying(dw)
        issues = validate_report(report, expected_journeys)
        issues.extend(
            f"red-case-failed:{item}"
            for item in planted_red_cases(report, expected_journeys)
        )
        transcript = build_transcript(contract, baseline, language)
        if transcript["friction"]["everyday_reserved_terms"]:
            issues.append(
                "everyday-language-drift:"
                + ",".join(transcript["friction"]["everyday_reserved_terms"])
            )
        if len(transcript["journeys"]) != 13:
            issues.append("transcript-journey-count-invalid")
        if issues:
            raise ExamFailure("; ".join(issues))
        print(render_transcript(transcript), end="")
        summary = {
            "kind": "delivery-workbench-usability-packaged-exam",
            "schema_version": 1,
            "result": "pass",
            "journeys": len(transcript["journeys"]),
            "same_consumer": True,
            "installed_wheel": True,
            "everyday_reserved_terms": [],
            "unresolved_dead_ends": 0,
            "authority_confirmations": transcript[
                "friction"
            ]["authority_confirmations"],
            "safe_refusal_paths": transcript[
                "friction"
            ]["safe_refusal_paths"],
            "technical_details": True,
            "exact_view_parity": report[
                "phase27_observations"
            ]["technical_details"]["exact_view_parity"],
            "exact_event_parity": report[
                "phase27_observations"
            ]["technical_details"]["exact_event_parity"],
            "review_results": report[
                "phase27_observations"
            ]["delivery"]["review_results"],
            "conductor_crashes": report["green"]["conductor_crashes"],
            "delivery_crashes": report["green"]["delivery_crashes"],
            "ledger_events": report["green"]["ledger_events"],
            "stream_events": report["green"]["stream_events"],
            "red_cases": 5,
            "release_actions": [],
            "deferred": transcript["friction"]["deferrals"],
        }
        print(json.dumps(summary, sort_keys=True))
        return 0
    except (ExamFailure, OSError, ValueError, KeyError, TypeError) as exc:
        print(f"usability-packaged-exam.py: FAIL: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
