"""Bounded test-failure baselines and fail-closed subtraction.

The parser deliberately recognizes only stable unittest and pytest failure
markers.  Output prose is never retained.  A non-zero command whose summary
cannot be reconciled exactly with the extracted identifiers is unparseable;
subtraction is then unavailable and every current failure is introduced.
"""

from __future__ import annotations

import hashlib
import re


BASELINE_PARSER = "unittest-pytest-failures-v1"
MAX_FAILURE_IDENTIFIERS = 200
MAX_FAILURE_IDENTIFIER_BYTES = 500

_PYTEST_LINE = re.compile(
    r"^(?:FAILED|ERROR)\s+([^\s]+(?:::[^\s]+)*)"
)
_PYTEST_TRAILING = re.compile(
    r"^([^\s]+(?:::[^\s]+)+)\s+(?:FAILED|ERROR)(?:\s|$)"
)
_UNITTEST_LINE = re.compile(r"^(?:FAIL|ERROR):\s+(.+?)\s*$")
_PYTEST_FAILED_COUNT = re.compile(r"(?<!\w)(\d+)\s+failed\b")
_PYTEST_ERROR_COUNT = re.compile(r"(?<!\w)(\d+)\s+errors?\b")
_UNITTEST_SUMMARY = re.compile(r"^FAILED\s*\(([^)]*)\)\s*$")
_UNITTEST_COUNT = re.compile(r"(?:failures|errors)=(\d+)")
_SAFE_OBLIGATION_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:@/-]{0,511}$")
_SAFE_OBLIGATION_REF = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_./:@+-]{0,511}$")
_TEST_DEBT_KEYS = {
    "id", "kind", "statement", "priority", "blocking",
    "accountable_role", "target", "citations", "acceptance", "state",
}


def _bounded_identifier(value: str) -> str | None:
    identifier = " ".join(value.strip().split())
    if not identifier or "\x00" in identifier:
        return None
    if len(identifier.encode("utf-8")) > MAX_FAILURE_IDENTIFIER_BYTES:
        return None
    return identifier


def extract_test_failures(
    output: str, exit_code: int, *, output_truncated: bool = False,
) -> dict[str, object]:
    """Return a bounded parse fact; never include source output or prose.

    Complete parsing requires a recognized summary count equal to the unique
    identifiers extracted from unittest ``FAIL:/ERROR:`` headers or pytest
    ``FAILED/ERROR node-id`` lines.  Any disagreement is unparseable.
    """
    if exit_code == 0:
        return {
            "parser": BASELINE_PARSER,
            "parse_status": "clean",
            "failure_count": 0,
            "failure_ids": [],
            "truncated": False,
        }

    identifiers: set[str] = set()
    summary_counts: list[int] = []
    for raw_line in output.splitlines():
        line = raw_line.strip()
        unittest = _UNITTEST_SUMMARY.match(line)
        if unittest is not None:
            values = [int(value) for value in _UNITTEST_COUNT.findall(unittest.group(1))]
            if values:
                summary_counts.append(sum(values))
        else:
            match = _PYTEST_LINE.match(line) or _PYTEST_TRAILING.match(line)
            if match is None:
                match = _UNITTEST_LINE.match(line)
            if match is not None:
                identifier = _bounded_identifier(match.group(1))
                if identifier is not None:
                    identifiers.add(identifier)
        pytest_counts = [
            int(value) for value in _PYTEST_FAILED_COUNT.findall(line)
        ] + [
            int(value) for value in _PYTEST_ERROR_COUNT.findall(line)
        ]
        if pytest_counts and ("=" in line or " short test summary " in line):
            summary_counts.append(sum(pytest_counts))

    ordered = sorted(identifiers)
    observed_count = max(summary_counts) if summary_counts else None
    complete = (
        not output_truncated
        and observed_count is not None
        and observed_count == len(ordered)
        and len(ordered) <= MAX_FAILURE_IDENTIFIERS
    )
    if not complete:
        return {
            "parser": BASELINE_PARSER,
            "parse_status": "unparseable",
            "failure_count": int(observed_count or max(1, len(ordered))),
            "failure_ids": [],
            "truncated": output_truncated or len(ordered) > MAX_FAILURE_IDENTIFIERS,
        }
    return {
        "parser": BASELINE_PARSER,
        "parse_status": "failures",
        "failure_count": len(ordered),
        "failure_ids": ordered,
        "truncated": False,
    }


def validate_baseline_fact(value: object) -> dict[str, object]:
    """Validate the closed, bounded ledger fact shape."""
    if not isinstance(value, dict):
        raise ValueError("test baseline fact must be an object")
    keys = {
        "head_sha", "command_hash", "status", "parser", "exit_code",
        "failure_count", "failure_ids", "subtraction_available", "truncated",
    }
    if set(value) != keys:
        raise ValueError("test baseline fact has non-exact keys")
    head = value.get("head_sha")
    if not isinstance(head, str) or not re.fullmatch(r"[0-9a-f]{40}", head):
        raise ValueError("test baseline head SHA is invalid")
    command_hash = value.get("command_hash")
    if command_hash is not None and (
        not isinstance(command_hash, str)
        or not re.fullmatch(r"sha256:[0-9a-f]{64}", command_hash)
    ):
        raise ValueError("test baseline command hash is invalid")
    status = value.get("status")
    if status not in {"unavailable", "clean", "failures", "unparseable"}:
        raise ValueError("test baseline status is invalid")
    if value.get("parser") != BASELINE_PARSER:
        raise ValueError("test baseline parser is invalid")
    exit_code = value.get("exit_code")
    if exit_code is not None and (
        not isinstance(exit_code, int) or isinstance(exit_code, bool)
        or not 0 <= exit_code <= 255
    ):
        raise ValueError("test baseline exit code is invalid")
    count = value.get("failure_count")
    if not isinstance(count, int) or isinstance(count, bool) or not 0 <= count <= 1_000_000:
        raise ValueError("test baseline failure count is invalid")
    identifiers = value.get("failure_ids")
    if (
        not isinstance(identifiers, list)
        or identifiers != sorted(set(identifiers))
        or len(identifiers) > MAX_FAILURE_IDENTIFIERS
        or any(not isinstance(item, str) or _bounded_identifier(item) != item for item in identifiers)
    ):
        raise ValueError("test baseline failure identifiers are invalid")
    available = value.get("subtraction_available")
    if not isinstance(available, bool) or not isinstance(value.get("truncated"), bool):
        raise ValueError("test baseline availability flags are invalid")
    expected_available = status in {"clean", "failures"} and not value["truncated"]
    if available != expected_available:
        raise ValueError("test baseline subtraction availability is inconsistent")
    valid_status_shape = {
        "unavailable": (
            command_hash is None and exit_code is None
            and count == 0 and not identifiers
        ),
        "clean": (
            command_hash is not None and exit_code == 0
            and count == 0 and not identifiers
        ),
        "failures": (
            command_hash is not None and exit_code not in {None, 0}
            and count == len(identifiers) and bool(identifiers)
        ),
        "unparseable": (
            command_hash is not None and exit_code not in {None, 0}
            and count > 0 and not identifiers and not available
        ),
    }
    if not valid_status_shape[str(status)]:
        raise ValueError(f"{status} test baseline is inconsistent")
    return {
        "head_sha": head,
        "command_hash": command_hash,
        "status": status,
        "parser": BASELINE_PARSER,
        "exit_code": exit_code,
        "failure_count": count,
        "failure_ids": list(identifiers),
        "subtraction_available": available,
        "truncated": value["truncated"],
    }


def build_failure_projection(value: object) -> dict[str, object]:
    """Return the one bounded rendering shape used by every verdict surface."""
    if not isinstance(value, dict):
        raise ValueError("test failure analysis must be an object")
    introduced = value.get("introduced")
    pre_existing = value.get("pre_existing")
    if (
        not isinstance(introduced, list)
        or not isinstance(pre_existing, list)
        or len(introduced) > MAX_FAILURE_IDENTIFIERS
        or len(pre_existing) > MAX_FAILURE_IDENTIFIERS
        or any(not isinstance(item, str) for item in introduced + pre_existing)
        or introduced != sorted(set(introduced))
        or pre_existing != sorted(set(pre_existing))
        or any(
            _bounded_identifier(item) != item
            for item in introduced + pre_existing
        )
    ):
        raise ValueError("test failure sets must be bounded identifier lists")
    subtraction_available = bool(value.get("subtraction_available"))
    refusal_reason = value.get("refusal_reason")
    if refusal_reason is not None and not isinstance(refusal_reason, str):
        raise ValueError("test failure refusal reason is invalid")
    state = (
        "introduced-failures" if introduced
        else "no-introduced-failures-with-pre-existing" if pre_existing
        else "green"
    )
    summary = (
        f"{len(introduced)} introduced, {len(pre_existing)} pre-existing test failures."
        if introduced else
        f"No introduced failures; {len(pre_existing)} pre-existing test failures."
        if pre_existing else
        "The declared test command has no failures."
    )
    return {
        "introduced": list(introduced),
        "introduced_count": len(introduced),
        "pre_existing": list(pre_existing),
        "pre_existing_count": len(pre_existing),
        "subtraction_available": subtraction_available,
        "refusal_reason": refusal_reason,
        "state": state,
        "status": state,
        "summary": summary,
    }


def validate_test_debt_obligation(value: object) -> dict[str, object]:
    """Validate the exact non-blocking obligation emitted from test facts."""
    if not isinstance(value, dict) or set(value) != _TEST_DEBT_KEYS:
        raise ValueError("test debt obligation has non-exact keys")
    obligation_id = value.get("id")
    target = value.get("target")
    citations = value.get("citations")
    if not isinstance(obligation_id, str) or not _SAFE_OBLIGATION_ID.fullmatch(obligation_id):
        raise ValueError("test debt obligation id is invalid")
    if value.get("kind") != "technical-debt" or value.get("blocking") is not False:
        raise ValueError("test debt must be non-blocking technical debt")
    if value.get("priority") != "medium" or value.get("state") != "open":
        raise ValueError("test debt state or priority is invalid")
    if value.get("accountable_role") != "verifier":
        raise ValueError("test debt accountable role is invalid")
    if target is not None and (
        not isinstance(target, str) or not _SAFE_OBLIGATION_REF.fullmatch(target)
    ):
        raise ValueError("test debt target is invalid")
    if (
        not isinstance(citations, list) or len(citations) != 1
        or not isinstance(citations[0], str)
        or not _SAFE_OBLIGATION_REF.fullmatch(citations[0])
    ):
        raise ValueError("test debt citation is invalid")
    result = dict(value)
    for field in ("statement", "acceptance"):
        text = result.get(field)
        if not isinstance(text, str) or not text or len(text.encode("utf-8")) > 2_000:
            raise ValueError(f"test debt {field} is invalid")
    return result


def build_test_debt_obligations(
    failure_analysis: object, *, target: str | None,
) -> list[dict[str, object]]:
    """Decide and shape all obligations from one classified failure set."""
    projection = build_failure_projection(failure_analysis)
    obligations: list[dict[str, object]] = []
    for identifier in projection["pre_existing"]:
        digest = hashlib.sha256(str(identifier).encode("utf-8")).hexdigest()
        obligations.append(validate_test_debt_obligation({
            "id": "pre-existing-test-" + digest[:24],
            "kind": "technical-debt",
            "statement": f"Pre-existing failing test: {identifier}",
            "priority": "medium",
            "blocking": False,
            "accountable_role": "verifier",
            "target": target,
            "citations": ["test-failure:sha256-" + digest],
            "acceptance": f"The test passes: {identifier}",
            "state": "open",
        }))
    return obligations


def build_baseline_fact(
    *, head_sha: str, command_hash: str | None,
    exit_code: int | None = None, output: str = "",
    output_truncated: bool = False,
) -> dict[str, object]:
    if command_hash is None:
        return validate_baseline_fact({
            "head_sha": head_sha,
            "command_hash": None,
            "status": "unavailable",
            "parser": BASELINE_PARSER,
            "exit_code": None,
            "failure_count": 0,
            "failure_ids": [],
            "subtraction_available": False,
            "truncated": False,
        })
    if exit_code is None:
        raise ValueError("declared test command baseline requires an exit code")
    parsed = extract_test_failures(
        output, exit_code, output_truncated=output_truncated
    )
    status = str(parsed["parse_status"])
    return validate_baseline_fact({
        "head_sha": head_sha,
        "command_hash": command_hash,
        "status": status,
        "parser": BASELINE_PARSER,
        "exit_code": exit_code,
        "failure_count": parsed["failure_count"],
        "failure_ids": parsed["failure_ids"],
        "subtraction_available": status in {"clean", "failures"},
        "truncated": parsed["truncated"],
    })


def classify_test_failures(
    current: object,
    baseline: object,
    *, expected_head_sha: str,
    command_hash: str,
) -> dict[str, object]:
    """Classify current failures, refusing subtraction on every stale path."""
    if not isinstance(current, dict):
        raise ValueError("current test failure fact must be an object")
    current_status = current.get("parse_status")
    current_ids = current.get("failure_ids")
    if (
        current_status not in {"clean", "failures", "unparseable"}
        or not isinstance(current_ids, list)
        or any(not isinstance(item, str) for item in current_ids)
    ):
        raise ValueError("current test failure fact is invalid")

    reason: str | None = None
    baseline_fact: dict[str, object] | None = None
    try:
        baseline_fact = validate_baseline_fact(baseline)
    except (ValueError, TypeError):
        reason = "baseline-missing-or-invalid"
    if baseline_fact is not None:
        if baseline_fact["head_sha"] != expected_head_sha:
            reason = "baseline-foreign-head"
        elif baseline_fact["command_hash"] != command_hash:
            reason = "baseline-stale-command"
        elif not baseline_fact["subtraction_available"]:
            reason = "baseline-subtraction-unavailable"
    if current_status == "unparseable":
        reason = "current-failures-unparseable"

    current_set = set(current_ids)
    if reason is None and baseline_fact is not None:
        baseline_set = set(baseline_fact["failure_ids"])
        pre_existing = sorted(current_set & baseline_set)
        introduced = sorted(current_set - baseline_set)
    else:
        pre_existing = []
        introduced = sorted(current_set)
    if current_status == "unparseable" and not introduced:
        introduced = ["<unparseable-test-failure>"]
    projection = build_failure_projection({
        "introduced": introduced,
        "pre_existing": pre_existing,
        "subtraction_available": reason is None,
        "refusal_reason": reason,
    })
    return {
        **projection,
        "parser": BASELINE_PARSER,
        "current_failure_count": int(
            current.get("failure_count", len(current_set))
        ),
        "green": not introduced and not pre_existing,
    }
