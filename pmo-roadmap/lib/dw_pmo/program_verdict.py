"""Pure governed quality facts, verdicts, and gate proofs for Phase 26.

Mechanical facts and agent judgments are intentionally different document
types.  A trusted check/rail receipt can become a mechanical fact; an assigned
read-only judgment role can issue a rubric-bound verdict.  Neither operation
starts work, writes state, grants authority, materializes evidence, integrates
code, or advances a roadmap.

The gate evaluator is likewise pure.  It validates hashes and freshness,
resolves supersession without erasing history, composes independent review
panels, deterministic meta-audits, architect gates, vetoes, and dissent, and
returns one closed pass/fail/pending/refused proof packet.  A later conductor
may act on that packet only through separately granted rails.

The contract is ``docs/programs.md`` (WLA-26-07).
"""

from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from .model import DwError
from .orchestration import canonical_json
from .test_baseline import build_failure_projection
from .program_deliberation import (
    DeliberationError,
    validate_council_decision,
)


RUBRIC_KIND = "delivery-workbench-rubric"
RUBRIC_SCHEMA_VERSION = 1
COMPILED_RUBRIC_KIND = "delivery-workbench-compiled-rubric"
RUBRIC_VALIDATION_KIND = "delivery-workbench-rubric-validation"
RUBRIC_INVENTORY_KIND = "delivery-workbench-rubric-list"

MECHANICAL_RECEIPT_KIND = "delivery-workbench-mechanical-receipt"
MECHANICAL_FACT_KIND = "delivery-workbench-mechanical-fact"
VERDICT_ASSIGNMENT_KIND = "delivery-workbench-verdict-assignment"
TEAM_ASSIGNMENT_KIND = "delivery-workbench-team-assignment"
VERDICT_KIND = "delivery-workbench-verdict"
QUALITY_GATE_KIND = "delivery-workbench-quality-gate"
QUALITY_PROOF_KIND = "delivery-workbench-quality-proof"
VERDICT_SCHEMA_VERSION = 1

CRITERION_RESULTS = ("pass", "fail", "abstain", "inconclusive")
VERDICT_RESULTS = (
    "pass", "fail", "repair", "needs-repair", "abstain", "inconclusive", "escalate",
    "approve", "veto", "uphold", "overturn",
)
GREEN_RESULTS = {"pass", "approve", "uphold"}
RED_RESULTS = {"fail", "repair", "needs-repair", "veto", "overturn"}
NEUTRAL_RESULTS = {"abstain", "inconclusive", "escalate"}
VERDICT_TYPES = (
    "agent-verdict", "panel-verdict", "meta-verdict",
    "architect-verdict",
)
SUBJECT_TYPES = (
    "diff", "tree", "artifact-set", "phase-snapshot", "verdict-set",
)
EVIDENCE_KINDS = (
    "markdown", "json", "text", "git-diff", "directory", "check-result",
    "mechanical-fact", "verdict", "decision", "citation-index",
)
MECHANICAL_PREDICATES = (
    "check-receipt", "artifact-conformance", "schema-conformance",
    "citation-conformance", "diff-scope", "roadmap-health",
    "contract-health", "signal-state", "history-condition",
    "verification-command",
)
PREDICATE_VALIDATES_EXIT_CODE = {
    predicate: predicate in {"check-receipt", "verification-command"}
    for predicate in MECHANICAL_PREDICATES
}
FRESHNESS_BINDINGS = (
    "subject", "repository", "program", "assignment", "rubric", "ledger",
)
AGGREGATION_METHODS = ("all", "any", "at_least")
GATE_REQUIREMENT_KINDS = ("independent", "panel", "council", "architect")
META_AUDIT_MODES = ("none", "random", "full")
JUDGMENT_DUTIES = {
    "verifier", "reviewer", "judge", "meta-verifier", "master-architect",
    "panel",
}

_SAFE_ID_RE = re.compile(r"^[a-z][a-z0-9]*(?:[-_][a-z0-9]+)*$")
_VERSION_RE = re.compile(r"^[0-9]+\.[0-9]+\.[0-9]+(?:[-+][A-Za-z0-9.-]+)?$")
_HASH_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
_REF_RE = re.compile(r"^(?:\.|[A-Za-z0-9][A-Za-z0-9_.:/@#=+,-]{0,1023})$")
_STORY_RE = re.compile(r"^[A-Z][A-Z0-9]*-[0-9]+-[0-9]+$")

_RUBRIC_KEYS = {
    "kind", "schema_version", "slug", "title", "description", "version",
    "subject_type", "result_vocabulary", "freshness", "criteria",
    "aggregation", "layout",
}
_FRESHNESS_KEYS = {"max_age_seconds", "bind"}
_CRITERION_KEYS = {
    "id", "question", "evaluation", "required_evidence_kinds",
    "min_citations", "allowed_results", "veto", "rationale_max_bytes",
}
_EVALUATION_KEYS = {"kind", "fact"}
_AGGREGATION_KEYS = {
    "method", "threshold", "on_pass", "on_fail", "on_abstain",
    "on_inconclusive",
}
_SUBJECT_KEYS = {
    "kind", "hash", "repository_hash", "program_hash", "program_run_id",
    "phase", "story", "workflow_address", "assignment_hash",
    "assignment_generation", "ledger_head", "implementer_principals",
}
_ASSIGNMENT_KEYS = {
    "kind", "schema_version", "assignment_hash", "story",
    "workflow_address", "role", "duty", "address",
    "assignment_generation", "principal_fingerprint", "workspace_domain",
    "session_binding_key", "packet_policy_hash", "execution",
    "independent_from",
}
_EXECUTION_KEYS = {
    "harness", "adapter", "adapter_version", "router", "provider",
    "model_vendor", "model_family", "model", "model_revision",
    "model_binding", "auth_domain_fingerprint", "capability_fingerprint",
}
_INDEPENDENCE_KEYS = {
    "role", "address", "principal_fingerprint", "workspace_domain",
    "session_binding_key",
}
_RECEIPT_KEYS = {
    "kind", "schema_version", "adapter_kind", "adapter_id",
    "adapter_fingerprint", "capability", "predicate", "passed",
    "receipt_hash", "observation_ref", "observation_hash",
    "observation_bytes", "command", "issued_at",
}
_COMMAND_KEYS = {"argv", "cwd", "exit_code"}
_FACT_KEYS = {
    "kind", "schema_version", "id", "predicate", "subject", "issuer",
    "result", "validates_exit_code", "observation", "issued_at",
    "payload_hash", "fact_hash",
}
_FACT_ISSUER_KEYS = {
    "kind", "id", "fingerprint", "capability", "receipt_hash",
}
_OBSERVATION_KEYS = {"ref", "hash", "bytes", "command"}
_EVIDENCE_KEYS = {"id", "kind", "hash", "ref"}
_CITATION_KEYS = {"id", "evidence_id", "locator", "hash"}
_CRITERION_RESULT_KEYS = {
    "id", "result", "evidence", "citations", "rationale",
    "mechanical_fact_hash",
}
_ATTESTATION_KEYS = {"kind", "receipt_hash", "payload_hash"}
_VERDICT_KEYS = {
    "kind", "schema_version", "verdict_type", "rubric", "subject",
    "assignment", "issuer", "criteria", "result", "dissent",
    "source_verdict_hashes", "supersedes", "composition", "issued_at",
    "expires_at", "idempotency_key", "judgment_not_mechanical",
    "payload_hash", "attestation", "verdict_hash",
}
_VERDICT_RUBRIC_KEYS = {"slug", "version", "semantic_hash"}
_ISSUER_KEYS = {
    "role", "duty", "address", "principal_fingerprint",
    "assignment_generation",
}
_DISSENT_KEYS = {"source", "role", "result", "reason"}
_PANEL_POLICY_KEYS = {
    "id", "method", "threshold", "quorum", "veto_roles",
    "dissent_policy",
}
_COMPOSITION_KEYS = {
    "policy_hash", "method", "threshold", "quorum_required",
    "quorum_observed", "distinct_principals", "member_verdicts",
    "veto_roles", "dissent_policy", "vetoed",
    "original_verdicts_preserved",
}
_GATE_KEYS = {
    "kind", "schema_version", "id", "subject_type", "mechanical_facts",
    "requirements", "operator", "threshold", "dissent_policy", "routes",
    "repair",
}
_FACT_REQUIREMENT_KEYS = {"id", "max_age_seconds"}
_REQUIREMENT_KEYS = {
    "id", "kind", "rubric", "roles", "method", "threshold",
    "veto_roles", "meta_audit",
}
_META_AUDIT_KEYS = {"mode", "sample_size", "rubric", "role"}
_ROUTE_KEYS = {"pass", "fail", "pending", "refused"}
_REPAIR_KEYS = {"max_rounds", "on_exhausted"}


class VerdictError(DwError):
    """A typed rubric, receipt, verdict, or gate refusal."""

    def __init__(self, code: str, message: str, pointer: str = "/") -> None:
        normalized_pointer = pointer or "/"
        super().__init__(f"{code} at {normalized_pointer}: {message}")
        # DwError reserves ``code`` for a numeric CLI exit status.  Governed
        # refusals intentionally expose a stable string code instead.
        self.code = code  # type: ignore[assignment]
        self.message = message
        self.pointer = normalized_pointer


class RubricValidationError(VerdictError):
    """A rubric refusal carrying source-aware compiler diagnostics."""

    def __init__(self, diagnostics: list[dict[str, str]]) -> None:
        self.diagnostics = diagnostics
        first = diagnostics[0]
        super().__init__(first["code"], first["message"], first["pointer"])


class _DuplicateJSONKey(ValueError):
    pass


def _object_pairs(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise _DuplicateJSONKey(key)
        result[key] = value
    return result


def _sha(value: object) -> str:
    return "sha256:" + hashlib.sha256(
        canonical_json(value).encode("utf-8")
    ).hexdigest()


def _refuse(condition: bool, code: str, message: str, pointer: str = "/") -> None:
    if not condition:
        raise VerdictError(code, message, pointer)


def _exact(value: object, keys: set[str], label: str) -> dict[str, object]:
    _refuse(isinstance(value, dict), "wrong-type", f"{label} must be an object", label)
    mapping = value
    _refuse(
        all(isinstance(key, str) for key in mapping),
        "unknown-key", f"{label} keys must be strings", label,
    )
    unknown = sorted(set(mapping) - keys)
    _refuse(
        not unknown,
        "unknown-key",
        f"{label} has unknown keys: {', '.join(unknown)}",
        label,
    )
    return mapping


def _safe_id(value: object, label: str) -> str:
    _refuse(
        isinstance(value, str) and bool(_SAFE_ID_RE.fullmatch(value)),
        "unsafe-value", f"{label} must be a stable lowercase id", label,
    )
    return value


def _reference(value: object, label: str) -> str:
    _refuse(
        isinstance(value, str) and bool(_REF_RE.fullmatch(value)),
        "unsafe-value", f"{label} must be a bounded reference", label,
    )
    return value


def _hash(value: object, label: str) -> str:
    _refuse(
        isinstance(value, str) and bool(_HASH_RE.fullmatch(value)),
        "invalid-hash", f"{label} must be sha256:<hex>", label,
    )
    return value


def _story(value: object, label: str) -> str | None:
    if value is None:
        return None
    _refuse(
        isinstance(value, str) and bool(_STORY_RE.fullmatch(value)),
        "invalid-story", f"{label} must be an exact story id or null", label,
    )
    return value


def _bounded_string(value: object, label: str, maximum: int) -> str:
    _refuse(
        isinstance(value, str) and 0 < len(value.encode("utf-8")) <= maximum,
        "invalid-value", f"{label} must be a non-empty bounded string", label,
    )
    return value


def _positive_int(value: object, label: str, maximum: int) -> int:
    _refuse(
        not isinstance(value, bool) and isinstance(value, int)
        and 1 <= value <= maximum,
        "invalid-bound", f"{label} must be an integer from 1 through {maximum}",
        label,
    )
    return value


def _nonnegative_int(value: object, label: str, maximum: int) -> int:
    _refuse(
        not isinstance(value, bool) and isinstance(value, int)
        and 0 <= value <= maximum,
        "invalid-bound", f"{label} must be an integer from 0 through {maximum}",
        label,
    )
    return value


def _timestamp(value: object, label: str) -> datetime:
    _refuse(
        isinstance(value, str) and value.endswith("Z"),
        "invalid-time", f"{label} must be a UTC timestamp ending in Z", label,
    )
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise VerdictError("invalid-time", f"{label} is not ISO-8601", label) from exc
    _refuse(parsed.tzinfo is not None, "invalid-time", f"{label} has no timezone", label)
    return parsed.astimezone(timezone.utc)


def _format_time(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat(timespec="seconds").replace(
        "+00:00", "Z"
    )


def _unique_strings(
    value: object,
    label: str,
    allowed: set[str] | tuple[str, ...],
    *,
    minimum: int = 0,
    maximum: int = 100,
) -> list[str]:
    allowed_set = set(allowed)
    _refuse(
        isinstance(value, list) and minimum <= len(value) <= maximum
        and all(isinstance(item, str) and item in allowed_set for item in value)
        and len(set(value)) == len(value),
        "invalid-value", f"{label} must be a unique contracted list", label,
    )
    return list(value)


def parse_rubric_text(text: str, source: str = "rubric") -> dict[str, object]:
    try:
        value = json.loads(
            text,
            object_pairs_hook=_object_pairs,
            parse_constant=lambda token: (_ for _ in ()).throw(
                ValueError(f"non-finite number {token}")
            ),
        )
    except (_DuplicateJSONKey, json.JSONDecodeError, ValueError) as exc:
        raise DwError(f"cannot parse rubric {source}: {exc}") from exc
    if not isinstance(value, dict):
        raise DwError(f"rubric document must be an object: {source}")
    return value


def rubric_dir(root: Path) -> Path:
    resolved_root = root.resolve()
    directory = (resolved_root / "pm" / "rubrics").resolve()
    if directory != resolved_root and resolved_root not in directory.parents:
        raise DwError("pm/rubrics resolves outside the repository")
    return directory


def discover_rubric_paths(root: Path) -> list[Path]:
    directory = rubric_dir(root)
    if not directory.is_dir():
        return []
    paths: list[Path] = []
    for candidate in sorted(directory.glob("*.json"), key=lambda item: item.name):
        resolved = candidate.resolve()
        if resolved.parent != directory:
            raise DwError(f"rubric escapes pm/rubrics: {candidate.name}")
        if resolved.is_file():
            paths.append(resolved)
    return paths


def load_rubric(path: Path) -> dict[str, object]:
    try:
        return parse_rubric_text(path.read_text(encoding="utf-8"), str(path))
    except OSError as exc:
        raise DwError(f"cannot read rubric {path}: {exc}") from exc


def find_rubric_path(root: Path, selector: str) -> Path:
    if not isinstance(selector, str) or not _SAFE_ID_RE.fullmatch(selector):
        raise DwError(f"unsafe rubric selector: {selector!r}")
    matches: list[Path] = []
    for path in discover_rubric_paths(root):
        if path.stem == selector:
            matches.append(path)
            continue
        try:
            document = load_rubric(path)
        except DwError:
            continue
        if document.get("slug") == selector:
            matches.append(path)
    if not matches:
        raise DwError(f"rubric not found: {selector}")
    if len(matches) != 1:
        raise DwError(f"rubric selector is ambiguous: {selector}")
    return matches[0]


def _resolve_rubric(
    root: Path,
    rubric: str | Path | object,
    source: str,
) -> tuple[dict[str, object], str]:
    if isinstance(rubric, str):
        path = find_rubric_path(root, rubric)
        return load_rubric(path), str(path.relative_to(root.resolve()))
    if isinstance(rubric, Path):
        path = rubric.resolve()
        _refuse(
            path.parent == rubric_dir(root),
            "path-outside-policy",
            "rubric path must be direct-contained under pm/rubrics",
            "/",
        )
        return load_rubric(path), str(path.relative_to(root.resolve()))
    _refuse(isinstance(rubric, dict), "wrong-type", "rubric must be an object", "/")
    return rubric, source


def _compile_rubric_document(raw: object) -> dict[str, object]:
    document = _exact(raw, _RUBRIC_KEYS, "/")
    _refuse(document.get("kind") == RUBRIC_KIND, "wrong-kind", f"expected {RUBRIC_KIND}", "/kind")
    _refuse(document.get("schema_version") == 1, "unsupported-schema", "only rubric schema 1 is supported", "/schema_version")
    slug = _safe_id(document.get("slug"), "/slug")
    title = _bounded_string(document.get("title"), "/title", 500)
    version = document.get("version")
    _refuse(isinstance(version, str) and bool(_VERSION_RE.fullmatch(version)), "invalid-version", "version must be semantic x.y.z", "/version")
    description = document.get("description")
    if description is not None:
        _bounded_string(description, "/description", 5_000)
    subject_type = document.get("subject_type")
    _refuse(subject_type in SUBJECT_TYPES, "unsupported-subject", "subject_type is unsupported", "/subject_type")
    vocabulary = _unique_strings(
        document.get("result_vocabulary"), "/result_vocabulary",
        VERDICT_RESULTS, minimum=2, maximum=len(VERDICT_RESULTS),
    )
    _refuse("pass" in vocabulary, "invalid-vocabulary", "result vocabulary must include pass", "/result_vocabulary")
    _refuse(bool(set(vocabulary) & (RED_RESULTS | NEUTRAL_RESULTS)), "invalid-vocabulary", "result vocabulary needs a non-pass result", "/result_vocabulary")

    freshness_raw = _exact(document.get("freshness"), _FRESHNESS_KEYS, "/freshness")
    max_age = _positive_int(freshness_raw.get("max_age_seconds"), "/freshness/max_age_seconds", 31_536_000)
    bind = _unique_strings(
        freshness_raw.get("bind"), "/freshness/bind", FRESHNESS_BINDINGS,
        minimum=len(FRESHNESS_BINDINGS), maximum=len(FRESHNESS_BINDINGS),
    )
    _refuse(set(bind) == set(FRESHNESS_BINDINGS), "freshness-incomplete", "rubric must bind every freshness dimension", "/freshness/bind")

    criteria_raw = document.get("criteria")
    _refuse(isinstance(criteria_raw, list) and 0 < len(criteria_raw) <= 100, "invalid-criteria", "criteria must be a non-empty bounded array", "/criteria")
    criteria: list[dict[str, object]] = []
    ids: set[str] = set()
    for index, item in enumerate(criteria_raw):
        pointer = f"/criteria/{index}"
        criterion = _exact(item, _CRITERION_KEYS, pointer)
        criterion_id = _safe_id(criterion.get("id"), f"{pointer}/id")
        _refuse(criterion_id not in ids, "duplicate-id", f"duplicate criterion {criterion_id}", f"{pointer}/id")
        ids.add(criterion_id)
        question = _bounded_string(criterion.get("question"), f"{pointer}/question", 2_000)
        evaluation_raw = _exact(criterion.get("evaluation"), _EVALUATION_KEYS, f"{pointer}/evaluation")
        evaluation_kind = evaluation_raw.get("kind")
        _refuse(evaluation_kind in {"agent-judgment", "mechanical-fact"}, "invalid-evaluation", "criterion evaluation kind is unsupported", f"{pointer}/evaluation/kind")
        fact = evaluation_raw.get("fact")
        if evaluation_kind == "mechanical-fact":
            fact = _safe_id(fact, f"{pointer}/evaluation/fact")
        else:
            _refuse(fact is None, "invalid-evaluation", "agent judgment cannot name a mechanical fact", f"{pointer}/evaluation/fact")
        evidence_kinds = _unique_strings(
            criterion.get("required_evidence_kinds"),
            f"{pointer}/required_evidence_kinds", EVIDENCE_KINDS, maximum=20,
        )
        min_citations = _nonnegative_int(criterion.get("min_citations"), f"{pointer}/min_citations", 20)
        allowed_results = _unique_strings(
            criterion.get("allowed_results"), f"{pointer}/allowed_results",
            CRITERION_RESULTS, minimum=2, maximum=len(CRITERION_RESULTS),
        )
        _refuse("pass" in allowed_results and "fail" in allowed_results, "invalid-results", "criterion must allow pass and fail", f"{pointer}/allowed_results")
        veto = criterion.get("veto")
        _refuse(isinstance(veto, bool), "wrong-type", "veto must be boolean", f"{pointer}/veto")
        rationale_max = _positive_int(criterion.get("rationale_max_bytes"), f"{pointer}/rationale_max_bytes", 20_000)
        criteria.append({
            "id": criterion_id,
            "question": question,
            "evaluation": {"kind": evaluation_kind, "fact": fact},
            "required_evidence_kinds": evidence_kinds,
            "min_citations": min_citations,
            "allowed_results": allowed_results,
            "veto": veto,
            "rationale_max_bytes": rationale_max,
        })

    aggregation_raw = _exact(document.get("aggregation"), _AGGREGATION_KEYS, "/aggregation")
    method = aggregation_raw.get("method")
    _refuse(method in AGGREGATION_METHODS, "invalid-aggregation", "aggregation method is unsupported", "/aggregation/method")
    threshold = aggregation_raw.get("threshold")
    if method == "all":
        expected_threshold = len(criteria)
    elif method == "any":
        expected_threshold = 1
    else:
        expected_threshold = _positive_int(threshold, "/aggregation/threshold", len(criteria))
    if method != "at_least":
        _refuse(threshold in {None, expected_threshold}, "invalid-threshold", f"{method} threshold must be null or {expected_threshold}", "/aggregation/threshold")
    outcomes: dict[str, str] = {}
    for name in ("on_pass", "on_fail", "on_abstain", "on_inconclusive"):
        value = aggregation_raw.get(name)
        _refuse(value in vocabulary, "invalid-outcome", f"{name} must use result_vocabulary", f"/aggregation/{name}")
        outcomes[name] = str(value)
    _refuse(outcomes["on_pass"] in GREEN_RESULTS, "invalid-outcome", "on_pass must be a green result", "/aggregation/on_pass")
    for name in ("on_fail", "on_abstain", "on_inconclusive"):
        _refuse(outcomes[name] not in GREEN_RESULTS, "invalid-outcome", f"{name} cannot map to green", f"/aggregation/{name}")

    layout = document.get("layout", {})
    _refuse(isinstance(layout, dict), "wrong-type", "layout must be an object", "/layout")
    _refuse(len(canonical_json(layout).encode("utf-8")) <= 1_000_000, "unbounded-value", "layout exceeds one megabyte", "/layout")
    normalized = {
        "kind": RUBRIC_KIND,
        "schema_version": RUBRIC_SCHEMA_VERSION,
        "slug": slug,
        "title": title,
        "description": description,
        "version": version,
        "subject_type": subject_type,
        "result_vocabulary": vocabulary,
        "freshness": {
            "max_age_seconds": max_age,
            "bind": list(FRESHNESS_BINDINGS),
        },
        "criteria": criteria,
        "aggregation": {
            "method": method,
            "threshold": expected_threshold,
            **outcomes,
        },
        "layout": layout,
    }
    runtime = {key: value for key, value in normalized.items() if key != "layout"}
    return {
        "kind": COMPILED_RUBRIC_KIND,
        "schema_version": RUBRIC_SCHEMA_VERSION,
        "semantic_hash": _sha(runtime),
        "document_hash": _sha(normalized),
        "rubric": runtime,
        "layout": layout,
        "criteria_by_id": {item["id"]: item for item in criteria},
        "starts_work": False,
        "writes_state": False,
        "creates_grant": False,
    }


def compile_rubric(
    root: Path,
    rubric: str | Path | object,
    source: str = "rubric",
) -> dict[str, object]:
    resolved_source = source
    try:
        raw, resolved_source = _resolve_rubric(root, rubric, source)
        compiled = _compile_rubric_document(raw)
    except VerdictError as exc:
        raise RubricValidationError([{
            "source": resolved_source,
            "pointer": exc.pointer,
            "code": exc.code,
            "message": exc.message,
            "remediation": "use the closed delivery-workbench-rubric schema",
        }]) from exc
    except DwError as exc:
        raise RubricValidationError([{
            "source": resolved_source,
            "pointer": "/",
            "code": "parse-error",
            "message": exc.message,
            "remediation": "fix the contained rubric JSON document",
        }]) from exc
    compiled["source"] = resolved_source
    compiled["document"] = raw
    return compiled


def validate_rubric(
    root: Path,
    rubric: str | Path | object,
    source: str = "rubric",
) -> dict[str, object]:
    try:
        compiled = compile_rubric(root, rubric, source)
    except RubricValidationError as exc:
        return {
            "kind": RUBRIC_VALIDATION_KIND,
            "schema_version": RUBRIC_SCHEMA_VERSION,
            "valid": False,
            "diagnostics": exc.diagnostics,
            "compiled": None,
            "starts_work": False,
            "writes_state": False,
        }
    return {
        "kind": RUBRIC_VALIDATION_KIND,
        "schema_version": RUBRIC_SCHEMA_VERSION,
        "valid": True,
        "diagnostics": [],
        "compiled": compiled,
        "starts_work": False,
        "writes_state": False,
    }


def rubric_inventory(root: Path) -> dict[str, object]:
    items: list[dict[str, object]] = []
    for path in discover_rubric_paths(root):
        validation = validate_rubric(root, path)
        raw: dict[str, object] = {}
        try:
            raw = load_rubric(path)
        except DwError:
            pass
        item: dict[str, object] = {
            "name": path.stem,
            "path": str(path.relative_to(root.resolve())),
            "slug": raw.get("slug"),
            "title": raw.get("title"),
            "valid": validation["valid"],
            "diagnostics": validation["diagnostics"],
        }
        if validation["valid"]:
            compiled = validation["compiled"]
            item.update({
                "semantic_hash": compiled["semantic_hash"],
                "document_hash": compiled["document_hash"],
                "version": compiled["rubric"]["version"],
                "subject_type": compiled["rubric"]["subject_type"],
            })
        items.append(item)
    return {
        "kind": RUBRIC_INVENTORY_KIND,
        "schema_version": RUBRIC_SCHEMA_VERSION,
        "rubrics": items,
        "healthy": all(bool(item["valid"]) for item in items),
        "starts_work": False,
        "writes_state": False,
    }


def _compiled_rubric(root: Path, value: object) -> dict[str, object]:
    if isinstance(value, dict) and value.get("kind") == COMPILED_RUBRIC_KIND:
        document = value.get("document")
        if not isinstance(document, dict):
            runtime = value.get("rubric")
            layout = value.get("layout")
            _refuse(isinstance(runtime, dict) and isinstance(layout, dict), "rubric-mismatch", "compiled rubric lacks a reproducible document")
            document = {**runtime, "layout": layout}
        recomputed = compile_rubric(
            root, document, str(value.get("source") or "compiled-rubric")
        )
        for field in ("semantic_hash", "document_hash", "rubric", "layout", "criteria_by_id"):
            _refuse(value.get(field) == recomputed[field], "rubric-mismatch", f"compiled rubric {field} does not match its document")
        return recomputed
    return compile_rubric(root, value)


def normalize_subject(value: object, label: str = "subject") -> dict[str, object]:
    subject = _exact(value, _SUBJECT_KEYS, label)
    kind = subject.get("kind")
    _refuse(kind in SUBJECT_TYPES, "unsupported-subject", "subject kind is unsupported", f"{label}/kind")
    phase = _nonnegative_int(subject.get("phase"), f"{label}/phase", 100_000)
    story = _story(subject.get("story"), f"{label}/story")
    generation = _positive_int(subject.get("assignment_generation"), f"{label}/assignment_generation", 1_000_000)
    principals = subject.get("implementer_principals")
    _refuse(
        isinstance(principals, list) and 0 < len(principals) <= 128
        and all(isinstance(item, str) and _HASH_RE.fullmatch(item) for item in principals)
        and len(set(principals)) == len(principals),
        "invalid-principals", "implementer principals must be non-empty unique hashes",
        f"{label}/implementer_principals",
    )
    return {
        "kind": kind,
        "hash": _hash(subject.get("hash"), f"{label}/hash"),
        "repository_hash": _hash(subject.get("repository_hash"), f"{label}/repository_hash"),
        "program_hash": _hash(subject.get("program_hash"), f"{label}/program_hash"),
        "program_run_id": _reference(subject.get("program_run_id"), f"{label}/program_run_id"),
        "phase": phase,
        "story": story,
        "workflow_address": _reference(subject.get("workflow_address"), f"{label}/workflow_address"),
        "assignment_hash": _hash(subject.get("assignment_hash"), f"{label}/assignment_hash"),
        "assignment_generation": generation,
        "ledger_head": _hash(subject.get("ledger_head"), f"{label}/ledger_head"),
        "implementer_principals": list(principals),
    }


def build_verdict_assignment(
    assignment: dict[str, object],
    role_id: str,
    *,
    member_address: str | None = None,
) -> dict[str, object]:
    """Project one assigned judgment member into an immutable verdict packet."""
    _refuse(assignment.get("kind") == TEAM_ASSIGNMENT_KIND, "assignment-invalid", "expected a compiled organization team assignment")
    _refuse(assignment.get("schema_version") == 1, "assignment-invalid", "team assignment schema is invalid")
    _refuse(bool(assignment.get("applicable")), "assignment-invalid", "team assignment is not applicable")
    assignment_hash = _hash(assignment.get("assignment_hash"), "assignment_hash")
    expected_hash = _sha({
        key: value for key, value in assignment.items()
        if key not in {"assignment_hash", "issues"}
    })
    _refuse(assignment_hash == expected_hash, "assignment-invalid", "team assignment hash does not match its exact contents")
    roles = assignment.get("roles")
    _refuse(isinstance(roles, list), "assignment-invalid", "assignment roles are absent")
    matches = [item for item in roles if item.get("role") == role_id]
    _refuse(len(matches) == 1, "role-unavailable", f"role {role_id!r} did not resolve uniquely")
    role = matches[0]
    _refuse(role.get("duty") in JUDGMENT_DUTIES - {"panel"}, "role-unavailable", "role is not a judgment duty")
    members = role.get("members")
    _refuse(isinstance(members, list) and members, "role-unavailable", "judgment role has no assigned member")
    if member_address is None:
        _refuse(len(members) == 1, "role-ambiguous", "select one judgment member address")
        member = members[0]
    else:
        selected = [item for item in members if item.get("address") == member_address]
        _refuse(len(selected) == 1, "role-unavailable", "judgment member address did not resolve")
        member = selected[0]
    packet = role.get("packet_policy")
    _refuse(isinstance(packet, dict), "assignment-invalid", "role packet policy is absent")
    _refuse(packet.get("workspace") == "read-only", "workspace-denied", "judgment role must be read-only")
    _refuse(bool(packet.get("verdict_schema")), "assignment-invalid", "judgment role has no verdict schema")
    effective = packet.get("effective_capability_ceiling")
    _refuse(isinstance(effective, list) and "verdict:issue" in effective, "capability-denied", "judgment role lacks verdict:issue")
    independent_roles = role.get("independent_from")
    _refuse(isinstance(independent_roles, list), "assignment-invalid", "independence policy is absent")
    if role.get("duty") == "verifier":
        implementer_roles = {
            str(item.get("role")) for item in roles if item.get("duty") == "implementer"
        }
        _refuse(bool(implementer_roles & set(independent_roles)), "separation-violation", "verifier is not declared independent from the implementer")
    independent: list[dict[str, str]] = []
    for other in roles:
        if other.get("role") not in independent_roles:
            continue
        for other_member in other.get("members", []):
            projected = {
                "role": str(other["role"]),
                "address": _reference(other_member.get("address"), "independent.address"),
                "principal_fingerprint": _hash(other_member.get("principal_fingerprint"), "independent.principal_fingerprint"),
                "workspace_domain": _reference(other_member.get("workspace_domain"), "independent.workspace_domain"),
                "session_binding_key": _hash(other_member.get("session_binding_key"), "independent.session_binding_key"),
            }
            _refuse(projected["principal_fingerprint"] != member.get("principal_fingerprint"), "separation-violation", "judgment member shares an independent principal")
            _refuse(projected["workspace_domain"] != member.get("workspace_domain"), "separation-violation", "judgment member shares an independent workspace")
            _refuse(projected["session_binding_key"] != member.get("session_binding_key"), "separation-violation", "judgment member shares an independent session")
            independent.append(projected)
    return {
        "kind": VERDICT_ASSIGNMENT_KIND,
        "schema_version": VERDICT_SCHEMA_VERSION,
        "assignment_hash": assignment_hash,
        "story": _story(assignment.get("story"), "assignment.story"),
        "workflow_address": _reference(assignment.get("workflow_address"), "assignment.workflow_address"),
        "role": _safe_id(role.get("role"), "assignment.role"),
        "duty": str(role["duty"]),
        "address": _reference(member.get("address"), "assignment.address"),
        "assignment_generation": _positive_int(member.get("assignment_generation"), "assignment.assignment_generation", 1_000_000),
        "principal_fingerprint": _hash(member.get("principal_fingerprint"), "assignment.principal_fingerprint"),
        "workspace_domain": _reference(member.get("workspace_domain"), "assignment.workspace_domain"),
        "session_binding_key": _hash(member.get("session_binding_key"), "assignment.session_binding_key"),
        "packet_policy_hash": _sha(packet),
        "execution": _normalize_execution(
            member.get("execution"), "assignment.execution"
        ),
        "independent_from": independent,
    }


def _normalize_execution(
    value: object,
    label: str = "execution",
) -> dict[str, object]:
    execution = _exact(value, _EXECUTION_KEYS, label)
    binding = execution.get("model_binding")
    _refuse(
        binding in {
            "exact-revision", "requested-alias",
            "adapter-default-unresolved",
        },
        "execution-invalid", f"{label} model binding is unsupported", label,
    )
    model = execution.get("model")
    revision = execution.get("model_revision")
    if model is not None:
        model = _bounded_string(model, f"{label}/model", 200)
    if revision is not None:
        revision = _bounded_string(revision, f"{label}/model_revision", 200)
    if binding == "exact-revision":
        _refuse(model is not None and revision is not None, "execution-invalid", "exact model binding is incomplete", label)
    elif binding == "requested-alias":
        _refuse(model is not None, "execution-invalid", "model alias binding omitted its model", label)
    else:
        _refuse(model is None and revision is None, "execution-invalid", "unresolved model binding names a model", label)
    return {
        "harness": _reference(execution.get("harness"), f"{label}/harness"),
        "adapter": _reference(execution.get("adapter"), f"{label}/adapter"),
        "adapter_version": _reference(execution.get("adapter_version"), f"{label}/adapter_version"),
        "router": _reference(execution.get("router"), f"{label}/router"),
        "provider": _reference(execution.get("provider"), f"{label}/provider"),
        "model_vendor": _reference(execution.get("model_vendor"), f"{label}/model_vendor"),
        "model_family": _reference(execution.get("model_family"), f"{label}/model_family"),
        "model": model,
        "model_revision": revision,
        "model_binding": binding,
        "auth_domain_fingerprint": _hash(execution.get("auth_domain_fingerprint"), f"{label}/auth_domain_fingerprint"),
        "capability_fingerprint": _hash(execution.get("capability_fingerprint"), f"{label}/capability_fingerprint"),
    }


def _normalize_assignment(value: object, label: str = "assignment") -> dict[str, object]:
    assignment = _exact(value, _ASSIGNMENT_KEYS, label)
    _refuse(assignment.get("kind") == VERDICT_ASSIGNMENT_KIND, "wrong-kind", "verdict assignment kind is invalid", f"{label}/kind")
    _refuse(assignment.get("schema_version") == 1, "unsupported-schema", "verdict assignment schema is invalid", f"{label}/schema_version")
    duty = assignment.get("duty")
    _refuse(duty in JUDGMENT_DUTIES, "role-unavailable", "assignment duty cannot issue a verdict", f"{label}/duty")
    independent_raw = assignment.get("independent_from")
    _refuse(isinstance(independent_raw, list) and len(independent_raw) <= 128, "invalid-principals", "independence proof must be bounded", f"{label}/independent_from")
    independent: list[dict[str, str]] = []
    for index, raw in enumerate(independent_raw):
        pointer = f"{label}/independent_from/{index}"
        item = _exact(raw, _INDEPENDENCE_KEYS, pointer)
        independent.append({
            "role": _safe_id(item.get("role"), f"{pointer}/role"),
            "address": _reference(item.get("address"), f"{pointer}/address"),
            "principal_fingerprint": _hash(item.get("principal_fingerprint"), f"{pointer}/principal_fingerprint"),
            "workspace_domain": _reference(item.get("workspace_domain"), f"{pointer}/workspace_domain"),
            "session_binding_key": _hash(item.get("session_binding_key"), f"{pointer}/session_binding_key"),
        })
    principal = _hash(assignment.get("principal_fingerprint"), f"{label}/principal_fingerprint")
    for key in (
        "address", "principal_fingerprint", "workspace_domain",
        "session_binding_key",
    ):
        _refuse(
            len({item[key] for item in independent}) == len(independent),
            "separation-violation",
            f"assignment independence proof repeats {key}",
            f"{label}/independent_from",
        )
    _refuse(all(item["principal_fingerprint"] != principal for item in independent), "separation-violation", "assignment independence proof collides with issuer", label)
    workspace = _reference(assignment.get("workspace_domain"), f"{label}/workspace_domain")
    session = _hash(assignment.get("session_binding_key"), f"{label}/session_binding_key")
    _refuse(all(item["workspace_domain"] != workspace for item in independent), "separation-violation", "assignment independence proof shares issuer workspace", label)
    _refuse(all(item["session_binding_key"] != session for item in independent), "separation-violation", "assignment independence proof shares issuer session", label)
    return {
        "kind": VERDICT_ASSIGNMENT_KIND,
        "schema_version": VERDICT_SCHEMA_VERSION,
        "assignment_hash": _hash(assignment.get("assignment_hash"), f"{label}/assignment_hash"),
        "story": _story(assignment.get("story"), f"{label}/story"),
        "workflow_address": _reference(assignment.get("workflow_address"), f"{label}/workflow_address"),
        "role": _safe_id(assignment.get("role"), f"{label}/role"),
        "duty": str(duty),
        "address": _reference(assignment.get("address"), f"{label}/address"),
        "assignment_generation": _positive_int(assignment.get("assignment_generation"), f"{label}/assignment_generation", 1_000_000),
        "principal_fingerprint": principal,
        "workspace_domain": workspace,
        "session_binding_key": session,
        "packet_policy_hash": _hash(assignment.get("packet_policy_hash"), f"{label}/packet_policy_hash"),
        "execution": _normalize_execution(
            assignment.get("execution"), f"{label}/execution"
        ),
        "independent_from": independent,
    }


def _normalize_command(value: object, label: str) -> dict[str, object] | None:
    if value is None:
        return None
    command = _exact(value, _COMMAND_KEYS, label)
    argv = command.get("argv")
    _refuse(
        isinstance(argv, list) and 0 < len(argv) <= 128
        and all(isinstance(item, str) and 0 < len(item.encode("utf-8")) <= 4_096 for item in argv),
        "invalid-command", "argv must be a non-empty bounded string list", f"{label}/argv",
    )
    exit_code = command.get("exit_code")
    _refuse(not isinstance(exit_code, bool) and isinstance(exit_code, int) and -255 <= exit_code <= 255, "invalid-command", "exit_code is invalid", f"{label}/exit_code")
    return {
        "argv": list(argv),
        "cwd": _reference(command.get("cwd"), f"{label}/cwd"),
        "exit_code": exit_code,
    }


def build_mechanical_fact(
    fact_id: str,
    receipt: object,
    subject: object,
) -> dict[str, object]:
    """Convert one exact trusted adapter receipt into a mechanical fact."""
    fact_id = _safe_id(fact_id, "fact id")
    raw = _exact(receipt, _RECEIPT_KEYS, "receipt")
    _refuse(raw.get("kind") == MECHANICAL_RECEIPT_KIND, "wrong-kind", "mechanical fact requires an adapter receipt", "receipt/kind")
    _refuse(raw.get("schema_version") == 1, "unsupported-schema", "mechanical receipt schema is invalid", "receipt/schema_version")
    adapter_kind = raw.get("adapter_kind")
    _refuse(adapter_kind in {"check-adapter", "rail-adapter"}, "issuer-invalid", "mechanical issuer must be a check or rail adapter", "receipt/adapter_kind")
    predicate = raw.get("predicate")
    _refuse(predicate in MECHANICAL_PREDICATES, "predicate-invalid", "mechanical predicate is unsupported", "receipt/predicate")
    capability = raw.get("capability")
    if adapter_kind == "check-adapter":
        _refuse(capability == "check:execute", "capability-denied", "check adapter fact requires check:execute", "receipt/capability")
        _refuse(predicate in set(MECHANICAL_PREDICATES[:5]) | {"verification-command"}, "issuer-invalid", "check adapter cannot issue this predicate", "receipt/predicate")
    else:
        _refuse(capability == "certification:objective", "capability-denied", "rail adapter fact requires certification:objective", "receipt/capability")
        _refuse(predicate in set(MECHANICAL_PREDICATES[5:9]), "issuer-invalid", "rail adapter cannot issue this predicate", "receipt/predicate")
    passed = raw.get("passed")
    _refuse(isinstance(passed, bool), "wrong-type", "mechanical passed value must be boolean", "receipt/passed")
    command = _normalize_command(raw.get("command"), "receipt/command")
    validates_exit_code = PREDICATE_VALIDATES_EXIT_CODE[str(predicate)]
    if validates_exit_code:
        _refuse(command is not None, "receipt-insufficient", "command predicate requires exact argv and exit code", "receipt/command")
        _refuse(passed == (command["exit_code"] == 0), "receipt-conflict", "passed conflicts with command exit code", "receipt/passed")
    else:
        _refuse(command is None, "unknown-content", "non-command predicate cannot carry argv", "receipt/command")
    issued_at = _format_time(_timestamp(raw.get("issued_at"), "receipt/issued_at"))
    normalized_subject = normalize_subject(subject)
    payload = {
        "kind": MECHANICAL_FACT_KIND,
        "schema_version": VERDICT_SCHEMA_VERSION,
        "id": fact_id,
        "predicate": predicate,
        "subject": normalized_subject,
        "issuer": {
            "kind": adapter_kind,
            "id": _safe_id(raw.get("adapter_id"), "receipt/adapter_id"),
            "fingerprint": _hash(raw.get("adapter_fingerprint"), "receipt/adapter_fingerprint"),
            "capability": capability,
            "receipt_hash": _hash(raw.get("receipt_hash"), "receipt/receipt_hash"),
        },
        "result": "pass" if passed else "fail",
        "validates_exit_code": validates_exit_code,
        "observation": {
            "ref": _reference(raw.get("observation_ref"), "receipt/observation_ref"),
            "hash": _hash(raw.get("observation_hash"), "receipt/observation_hash"),
            "bytes": _nonnegative_int(raw.get("observation_bytes"), "receipt/observation_bytes", 100_000_000),
            "command": command,
        },
        "issued_at": issued_at,
    }
    payload_hash = _sha(payload)
    stamped = {**payload, "payload_hash": payload_hash}
    return {**stamped, "fact_hash": _sha(stamped)}


def validate_mechanical_fact(value: object) -> dict[str, object]:
    fact = _exact(value, _FACT_KEYS, "fact")
    _refuse(fact.get("kind") == MECHANICAL_FACT_KIND, "wrong-kind", "expected mechanical fact", "fact/kind")
    _refuse(fact.get("schema_version") == 1, "unsupported-schema", "mechanical fact schema is invalid", "fact/schema_version")
    _safe_id(fact.get("id"), "fact/id")
    _refuse(fact.get("predicate") in MECHANICAL_PREDICATES, "predicate-invalid", "fact predicate is unsupported", "fact/predicate")
    normalize_subject(fact.get("subject"), "fact/subject")
    issuer = _exact(fact.get("issuer"), _FACT_ISSUER_KEYS, "fact/issuer")
    _refuse(issuer.get("kind") in {"check-adapter", "rail-adapter"}, "issuer-invalid", "fact issuer is not an adapter", "fact/issuer/kind")
    _safe_id(issuer.get("id"), "fact/issuer/id")
    _hash(issuer.get("fingerprint"), "fact/issuer/fingerprint")
    _hash(issuer.get("receipt_hash"), "fact/issuer/receipt_hash")
    _refuse(issuer.get("capability") in {"check:execute", "certification:objective"}, "capability-denied", "fact issuer capability is invalid", "fact/issuer/capability")
    if issuer.get("kind") == "check-adapter":
        _refuse(issuer.get("capability") == "check:execute", "capability-denied", "check fact lost check:execute", "fact/issuer/capability")
        _refuse(fact.get("predicate") in set(MECHANICAL_PREDICATES[:5]) | {"verification-command"}, "issuer-invalid", "check adapter issued a rail predicate", "fact/predicate")
    else:
        _refuse(issuer.get("capability") == "certification:objective", "capability-denied", "rail fact lost certification:objective", "fact/issuer/capability")
        _refuse(fact.get("predicate") in set(MECHANICAL_PREDICATES[5:9]), "issuer-invalid", "rail adapter issued a check predicate", "fact/predicate")
    _refuse(fact.get("result") in {"pass", "fail"}, "invalid-result", "mechanical result must be pass or fail", "fact/result")
    validates_exit_code = fact.get("validates_exit_code")
    _refuse(
        isinstance(validates_exit_code, bool)
        and validates_exit_code
        == PREDICATE_VALIDATES_EXIT_CODE[str(fact.get("predicate"))],
        "receipt-conflict", "fact exit-code policy conflicts with its predicate",
        "fact/validates_exit_code",
    )
    observation = _exact(fact.get("observation"), _OBSERVATION_KEYS, "fact/observation")
    _reference(observation.get("ref"), "fact/observation/ref")
    _hash(observation.get("hash"), "fact/observation/hash")
    _nonnegative_int(observation.get("bytes"), "fact/observation/bytes", 100_000_000)
    command = _normalize_command(observation.get("command"), "fact/observation/command")
    if validates_exit_code:
        _refuse(command is not None, "receipt-insufficient", "command fact lost argv", "fact/observation/command")
        _refuse((command["exit_code"] == 0) == (fact.get("result") == "pass"), "receipt-conflict", "fact result conflicts with exit code", "fact/result")
    else:
        _refuse(command is None, "unknown-content", "non-command fact cannot carry argv", "fact/observation/command")
    _timestamp(fact.get("issued_at"), "fact/issued_at")
    payload_hash = _hash(fact.get("payload_hash"), "fact/payload_hash")
    fact_hash = _hash(fact.get("fact_hash"), "fact/fact_hash")
    payload = {key: item for key, item in fact.items() if key not in {"payload_hash", "fact_hash"}}
    _refuse(_sha(payload) == payload_hash, "receipt-forged", "mechanical payload hash does not match", "fact/payload_hash")
    _refuse(_sha({**payload, "payload_hash": payload_hash}) == fact_hash, "receipt-forged", "mechanical fact hash does not match", "fact/fact_hash")
    return dict(fact)


def _normalize_evidence(value: object, label: str) -> list[dict[str, str]]:
    _refuse(isinstance(value, list) and len(value) <= 100, "invalid-evidence", f"{label} must be a bounded array", label)
    result: list[dict[str, str]] = []
    ids: set[str] = set()
    for index, raw in enumerate(value):
        pointer = f"{label}/{index}"
        item = _exact(raw, _EVIDENCE_KEYS, pointer)
        item_id = _safe_id(item.get("id"), f"{pointer}/id")
        _refuse(item_id not in ids, "duplicate-evidence", f"duplicate evidence id {item_id}", f"{pointer}/id")
        ids.add(item_id)
        kind = item.get("kind")
        _refuse(kind in EVIDENCE_KINDS, "invalid-evidence", "evidence kind is unsupported", f"{pointer}/kind")
        result.append({
            "id": item_id,
            "kind": str(kind),
            "hash": _hash(item.get("hash"), f"{pointer}/hash"),
            "ref": _reference(item.get("ref"), f"{pointer}/ref"),
        })
    return result


def _normalize_citations(
    value: object,
    evidence: list[dict[str, str]],
    label: str,
) -> list[dict[str, str]]:
    _refuse(isinstance(value, list) and len(value) <= 100, "invalid-citation", f"{label} must be a bounded array", label)
    evidence_ids = {item["id"] for item in evidence}
    result: list[dict[str, str]] = []
    ids: set[str] = set()
    for index, raw in enumerate(value):
        pointer = f"{label}/{index}"
        item = _exact(raw, _CITATION_KEYS, pointer)
        citation_id = _safe_id(item.get("id"), f"{pointer}/id")
        _refuse(citation_id not in ids, "duplicate-citation", f"duplicate citation {citation_id}", f"{pointer}/id")
        ids.add(citation_id)
        evidence_id = _safe_id(item.get("evidence_id"), f"{pointer}/evidence_id")
        _refuse(evidence_id in evidence_ids, "citation-missing", "citation references undeclared evidence", f"{pointer}/evidence_id")
        result.append({
            "id": citation_id,
            "evidence_id": evidence_id,
            "locator": _reference(item.get("locator"), f"{pointer}/locator"),
            "hash": _hash(item.get("hash"), f"{pointer}/hash"),
        })
    return result


def _aggregate_criteria(
    rubric: dict[str, object],
    criteria: list[dict[str, object]],
) -> tuple[str, list[dict[str, str]]]:
    pass_count = sum(item["result"] == "pass" for item in criteria)
    failed = [item for item in criteria if item["result"] == "fail"]
    vetoed = [
        item for item in failed
        if rubric["criteria_by_id"][item["id"]]["veto"]
    ]
    aggregation = rubric["rubric"]["aggregation"]
    dissent = [
        {
            "source": str(item["id"]),
            "role": "criterion",
            "result": str(item["result"]),
            "reason": "criterion did not pass",
        }
        for item in criteria if item["result"] != "pass"
    ]
    if not vetoed and pass_count >= int(aggregation["threshold"]):
        return str(aggregation["on_pass"]), dissent
    if failed:
        return str(aggregation["on_fail"]), dissent
    if any(item["result"] == "inconclusive" for item in criteria):
        return str(aggregation["on_inconclusive"]), dissent
    return str(aggregation["on_abstain"]), dissent


def _verdict_role_allowed(verdict_type: str, duty: str) -> bool:
    if verdict_type == "meta-verdict":
        return duty == "meta-verifier"
    if verdict_type == "architect-verdict":
        return duty == "master-architect"
    return duty in {"verifier", "reviewer", "judge"}


def _lineage_matches(left: dict[str, object], right: dict[str, object]) -> bool:
    return all((
        left["rubric"]["slug"] == right["rubric"]["slug"],
        left["rubric"]["version"] == right["rubric"]["version"],
        left["rubric"]["semantic_hash"] == right["rubric"]["semantic_hash"],
        left["assignment"]["role"] == right["assignment"]["role"],
        left["assignment"]["address"] == right["assignment"]["address"],
        left["subject"]["program_run_id"] == right["subject"]["program_run_id"],
        left["subject"]["phase"] == right["subject"]["phase"],
        left["subject"]["story"] == right["subject"]["story"],
        left["subject"]["workflow_address"] == right["subject"]["workflow_address"],
    ))


def issue_agent_verdict(
    root: Path,
    rubric: object,
    assignment: object,
    subject: object,
    criterion_results: object,
    *,
    issued_at: str,
    idempotency_key: str,
    attestation_receipt_hash: str,
    verdict_type: str = "agent-verdict",
    mechanical_facts: list[dict[str, object]] | None = None,
    source_verdicts: list[dict[str, object]] | None = None,
    superseded_verdicts: list[dict[str, object]] | None = None,
) -> dict[str, object]:
    """Issue one exact assigned judgment; overall result is rubric-derived."""
    _refuse(verdict_type in {"agent-verdict", "meta-verdict", "architect-verdict"}, "invalid-verdict-type", "issue_agent_verdict cannot create this type")
    compiled = _compiled_rubric(root, rubric)
    runtime = compiled["rubric"]
    assigned = _normalize_assignment(assignment)
    _refuse(_verdict_role_allowed(verdict_type, str(assigned["duty"])), "role-unavailable", f"{assigned['duty']} cannot issue {verdict_type}")
    normalized_subject = normalize_subject(subject)
    _refuse(runtime["subject_type"] == normalized_subject["kind"], "subject-mismatch", "rubric subject type does not match", "subject/kind")
    _refuse(assigned["assignment_hash"] == normalized_subject["assignment_hash"], "verdict-stale", "assignment hash differs from subject", "subject/assignment_hash")
    _refuse(assigned["assignment_generation"] == normalized_subject["assignment_generation"], "verdict-stale", "assignment generation differs from subject", "subject/assignment_generation")
    _refuse(assigned["story"] == normalized_subject["story"], "subject-mismatch", "assignment story differs from subject", "subject/story")
    _refuse(assigned["workflow_address"] == normalized_subject["workflow_address"], "subject-mismatch", "assignment workflow differs from subject", "subject/workflow_address")
    _refuse(assigned["principal_fingerprint"] not in normalized_subject["implementer_principals"], "separation-violation", "implementer cannot issue its own independent verdict", "assignment/principal_fingerprint")
    declared_independent = {
        item["principal_fingerprint"] for item in assigned["independent_from"]
    }
    _refuse(
        set(normalized_subject["implementer_principals"]) <= declared_independent,
        "separation-violation",
        "verdict assignment does not prove independence from every implementer",
        "assignment/independent_from",
    )

    raw_results = criterion_results
    _refuse(isinstance(raw_results, list) and len(raw_results) == len(runtime["criteria"]), "verdict-insufficient", "criterion result count does not match rubric", "criteria")
    by_id: dict[str, object] = {}
    for index, raw in enumerate(raw_results):
        item = _exact(raw, _CRITERION_RESULT_KEYS, f"criteria/{index}")
        criterion_id = _safe_id(item.get("id"), f"criteria/{index}/id")
        _refuse(criterion_id not in by_id, "duplicate-id", f"duplicate criterion result {criterion_id}", f"criteria/{index}/id")
        by_id[criterion_id] = item
    _refuse(set(by_id) == set(compiled["criteria_by_id"]), "verdict-insufficient", "criterion ids do not exactly match rubric", "criteria")
    supplied_facts = [
        validate_mechanical_fact(item) for item in (mechanical_facts or [])
    ]
    facts_by_hash = {str(item["fact_hash"]): item for item in supplied_facts}
    _refuse(
        len(facts_by_hash) == len(supplied_facts),
        "duplicate-evidence", "mechanical fact set repeats a hash",
        "mechanical_facts",
    )
    normalized_results: list[dict[str, object]] = []
    for criterion in runtime["criteria"]:
        raw = by_id[criterion["id"]]
        result = raw.get("result")
        _refuse(result in criterion["allowed_results"], "invalid-result", "criterion result is not allowed", f"criteria/{criterion['id']}/result")
        evidence = _normalize_evidence(raw.get("evidence"), f"criteria/{criterion['id']}/evidence")
        citations = _normalize_citations(raw.get("citations"), evidence, f"criteria/{criterion['id']}/citations")
        present_kinds = {item["kind"] for item in evidence}
        _refuse(set(criterion["required_evidence_kinds"]) <= present_kinds, "evidence-missing", "criterion lacks a required evidence kind", f"criteria/{criterion['id']}/evidence")
        _refuse(len(citations) >= int(criterion["min_citations"]), "citation-missing", "criterion has too few citations", f"criteria/{criterion['id']}/citations")
        rationale = raw.get("rationale")
        mechanical_hash = raw.get("mechanical_fact_hash")
        if criterion["evaluation"]["kind"] == "mechanical-fact":
            _refuse(isinstance(mechanical_hash, str) and _HASH_RE.fullmatch(mechanical_hash), "verdict-insufficient", "mechanical criterion must cite a fact hash", f"criteria/{criterion['id']}/mechanical_fact_hash")
            _refuse(rationale in {None, ""}, "mechanical-counterfeit", "agent prose cannot satisfy a mechanical criterion", f"criteria/{criterion['id']}/rationale")
            fact = facts_by_hash.get(str(mechanical_hash))
            _refuse(fact is not None, "verdict-insufficient", "mechanical criterion fact is not present", f"criteria/{criterion['id']}/mechanical_fact_hash")
            _refuse(fact["id"] == criterion["evaluation"]["fact"], "verdict-insufficient", "mechanical criterion names a different fact", f"criteria/{criterion['id']}/mechanical_fact_hash")
            _refuse(fact["subject"] == normalized_subject, "verdict-stale", "mechanical criterion fact covers a different subject", f"criteria/{criterion['id']}/mechanical_fact_hash")
            _refuse(result == fact["result"], "mechanical-counterfeit", "agent-selected result conflicts with mechanical fact", f"criteria/{criterion['id']}/result")
        else:
            _refuse(mechanical_hash is None, "mechanical-counterfeit", "agent criterion cannot masquerade as a mechanical fact", f"criteria/{criterion['id']}/mechanical_fact_hash")
            rationale = _bounded_string(rationale, f"criteria/{criterion['id']}/rationale", int(criterion["rationale_max_bytes"]))
        normalized_results.append({
            "id": criterion["id"],
            "result": result,
            "evidence": evidence,
            "citations": citations,
            "rationale": rationale or None,
            "mechanical_fact_hash": mechanical_hash,
        })
    result, dissent = _aggregate_criteria(compiled, normalized_results)
    now = _timestamp(issued_at, "issued_at")
    issued = _format_time(now)
    expires = _format_time(now + timedelta(seconds=int(runtime["freshness"]["max_age_seconds"])))
    idempotency = _reference(idempotency_key, "idempotency_key")

    sources = sorted(
        [validate_verdict_document(item) for item in (source_verdicts or [])],
        key=lambda item: str(item["verdict_hash"]),
    )
    source_hashes = [str(item["verdict_hash"]) for item in sources]
    if verdict_type == "meta-verdict":
        _refuse(bool(sources), "verdict-insufficient", "meta verdict requires underlying verdicts")
        _refuse(all(item["verdict_type"] != "meta-verdict" for item in sources), "invalid-lineage", "meta verdict cannot recursively audit another meta verdict")
        expected_hash = _sha({"verdicts": sorted(source_hashes)})
        _refuse(normalized_subject["kind"] == "verdict-set" and normalized_subject["hash"] == expected_hash, "subject-mismatch", "meta subject does not bind the exact verdict set", "subject/hash")
        for source in sources:
            for field in (
                "repository_hash", "program_hash", "program_run_id", "phase",
                "story", "workflow_address", "assignment_hash",
                "assignment_generation", "ledger_head",
                "implementer_principals",
            ):
                _refuse(source["subject"][field] == normalized_subject[field], "subject-mismatch", f"meta source {field} differs from verdict-set subject", "source_verdicts")
        source_principals = {item["issuer"]["principal_fingerprint"] for item in sources}
        _refuse(assigned["principal_fingerprint"] not in source_principals, "separation-violation", "meta-verifier shares an underlying verdict principal")
        _refuse(source_principals <= declared_independent, "separation-violation", "meta-verifier assignment does not prove independence from every verdict author")
    else:
        _refuse(not sources, "invalid-lineage", "only a meta verdict may carry source verdicts")
    superseded = sorted(
        [validate_verdict_document(item) for item in (superseded_verdicts or [])],
        key=lambda item: str(item["verdict_hash"]),
    )
    for prior in superseded:
        _refuse(_lineage_matches({
            "rubric": {
                "slug": runtime["slug"],
                "version": runtime["version"],
                "semantic_hash": compiled["semantic_hash"],
            },
            "assignment": assigned,
            "subject": normalized_subject,
        }, prior), "supersession-invalid", "superseded verdict is outside this issuer/rubric/story lineage")
        _refuse(_timestamp(prior["issued_at"], "prior issued_at") < now, "supersession-invalid", "superseded verdict is not older")
    supersedes = [str(item["verdict_hash"]) for item in superseded]
    rubric_ref = {
        "slug": runtime["slug"],
        "version": runtime["version"],
        "semantic_hash": compiled["semantic_hash"],
    }
    issuer = {
        "role": assigned["role"],
        "duty": assigned["duty"],
        "address": assigned["address"],
        "principal_fingerprint": assigned["principal_fingerprint"],
        "assignment_generation": assigned["assignment_generation"],
    }
    payload = {
        "kind": VERDICT_KIND,
        "schema_version": VERDICT_SCHEMA_VERSION,
        "verdict_type": verdict_type,
        "rubric": rubric_ref,
        "subject": normalized_subject,
        "assignment": assigned,
        "issuer": issuer,
        "criteria": normalized_results,
        "result": result,
        "dissent": dissent,
        "source_verdict_hashes": source_hashes,
        "supersedes": supersedes,
        "composition": None,
        "issued_at": issued,
        "expires_at": expires,
        "idempotency_key": idempotency,
        "judgment_not_mechanical": True,
    }
    payload_hash = _sha(payload)
    attestation = {
        "kind": "driver-receipt",
        "receipt_hash": _hash(attestation_receipt_hash, "attestation_receipt_hash"),
        "payload_hash": payload_hash,
    }
    stamped = {
        **payload,
        "payload_hash": payload_hash,
        "attestation": attestation,
    }
    return {**stamped, "verdict_hash": _sha(stamped)}


def build_verdict_set_subject(
    base_subject: object,
    verdicts: list[dict[str, object]],
) -> dict[str, object]:
    base = normalize_subject(base_subject)
    validated = [validate_verdict_document(item) for item in verdicts]
    hashes = sorted(str(item["verdict_hash"]) for item in validated)
    _refuse(bool(hashes), "verdict-insufficient", "verdict set cannot be empty")
    _refuse(len(set(hashes)) == len(hashes), "duplicate-verdict", "verdict set repeats a verdict")
    return {
        **base,
        "kind": "verdict-set",
        "hash": _sha({"verdicts": hashes}),
    }


def _panel_assignment(
    policy_id: str,
    members: list[dict[str, object]],
) -> dict[str, object]:
    first = members[0]["assignment"]
    principals = sorted({item["issuer"]["principal_fingerprint"] for item in members})
    synthetic_principal = _sha({"panel": policy_id, "principals": principals})
    return {
        "kind": VERDICT_ASSIGNMENT_KIND,
        "schema_version": VERDICT_SCHEMA_VERSION,
        "assignment_hash": first["assignment_hash"],
        "story": first["story"],
        "workflow_address": first["workflow_address"],
        "role": policy_id,
        "duty": "panel",
        "address": f"{first['workflow_address']}/panel/{policy_id}",
        "assignment_generation": max(int(item["assignment"]["assignment_generation"]) for item in members),
        "principal_fingerprint": synthetic_principal,
        "workspace_domain": f"panel-{policy_id}",
        "session_binding_key": _sha({"panel": policy_id, "members": [item["verdict_hash"] for item in members]}),
        "packet_policy_hash": _sha({"policy": policy_id}),
        "execution": {
            "harness": "delivery-workbench",
            "adapter": "deterministic-panel",
            "adapter_version": "builtin-v1",
            "router": "none",
            "provider": "local",
            "model_vendor": "none",
            "model_family": "none",
            "model": None,
            "model_revision": None,
            "model_binding": "adapter-default-unresolved",
            "auth_domain_fingerprint": _sha({"panel": policy_id}),
            "capability_fingerprint": _sha({
                "panel": policy_id, "policy": "deterministic-composition-v1",
            }),
        },
        "independent_from": [],
    }


def compose_panel_verdict(
    root: Path,
    rubric: object,
    subject: object,
    member_verdicts: list[dict[str, object]],
    policy: object,
    *,
    issued_at: str,
    idempotency_key: str,
) -> dict[str, object]:
    """Deterministically aggregate member verdicts and retain all dissent."""
    compiled = _compiled_rubric(root, rubric)
    runtime = compiled["rubric"]
    normalized_subject = normalize_subject(subject)
    members = sorted(
        [validate_verdict_document(item) for item in member_verdicts],
        key=lambda item: str(item["verdict_hash"]),
    )
    _refuse(bool(members) and len(members) <= 64, "quorum-lost", "panel needs a bounded member verdict set")
    raw_policy = _exact(policy, _PANEL_POLICY_KEYS, "panel_policy")
    policy_id = _safe_id(raw_policy.get("id"), "panel_policy/id")
    method = raw_policy.get("method")
    _refuse(method in {"any", "at_least", "unanimous"}, "invalid-aggregation", "panel method is unsupported", "panel_policy/method")
    threshold = _positive_int(raw_policy.get("threshold"), "panel_policy/threshold", len(members))
    quorum = _positive_int(raw_policy.get("quorum"), "panel_policy/quorum", len(members))
    _refuse(threshold <= quorum, "invalid-threshold", "panel threshold cannot exceed quorum", "panel_policy/threshold")
    if method == "any":
        _refuse(threshold == 1, "invalid-threshold", "any panel threshold must be one", "panel_policy/threshold")
    elif method == "unanimous":
        _refuse(threshold == quorum, "invalid-threshold", "unanimous panel threshold must equal quorum", "panel_policy/threshold")
    veto_roles = raw_policy.get("veto_roles")
    _refuse(isinstance(veto_roles, list) and len(veto_roles) <= 64 and len(set(veto_roles)) == len(veto_roles) and all(isinstance(item, str) and _SAFE_ID_RE.fullmatch(item) for item in veto_roles), "invalid-value", "veto_roles must be unique role ids", "panel_policy/veto_roles")
    dissent_policy = raw_policy.get("dissent_policy")
    _refuse(dissent_policy in {"preserve", "block", "escalate"}, "invalid-value", "dissent policy is unsupported", "panel_policy/dissent_policy")
    seen_principals: set[str] = set()
    seen_hashes: set[str] = set()
    for member in members:
        _refuse(member["verdict_type"] == "agent-verdict", "invalid-verdict-type", "panel members must be agent verdicts")
        _refuse(member["rubric"]["semantic_hash"] == compiled["semantic_hash"], "verdict-stale", "panel member rubric differs")
        _refuse(member["subject"] == normalized_subject, "verdict-stale", "panel member subject differs")
        _refuse(not verdict_freshness_issues(member, normalized_subject, compiled, issued_at), "verdict-stale", "panel member is not fresh at aggregation time")
        _refuse(member["verdict_hash"] not in seen_hashes, "duplicate-verdict", "panel repeats a verdict")
        seen_hashes.add(str(member["verdict_hash"]))
        principal = str(member["issuer"]["principal_fingerprint"])
        _refuse(principal not in seen_principals, "separation-violation", "two panel members share a principal")
        seen_principals.add(principal)
    observed = sum(member["result"] not in NEUTRAL_RESULTS for member in members)
    green = [member for member in members if member["result"] in GREEN_RESULTS]
    red = [member for member in members if member["result"] in RED_RESULTS]
    vetoed = any(member["issuer"]["role"] in veto_roles for member in red)
    if observed < quorum:
        result = str(runtime["aggregation"]["on_inconclusive"])
    elif vetoed:
        result = str(runtime["aggregation"]["on_fail"])
    elif method == "unanimous":
        result = str(runtime["aggregation"]["on_pass"] if len(green) == observed else runtime["aggregation"]["on_fail"])
    elif len(green) >= threshold:
        result = str(runtime["aggregation"]["on_pass"])
    elif red:
        result = str(runtime["aggregation"]["on_fail"])
    else:
        result = str(runtime["aggregation"]["on_abstain"])
    dissent = [
        {
            "source": str(member["verdict_hash"]),
            "role": str(member["issuer"]["role"]),
            "result": str(member["result"]),
            "reason": "member result differs from panel result",
        }
        for member in members if member["result"] != result
    ]
    if result in GREEN_RESULTS and dissent_policy == "block" and dissent:
        result = str(runtime["aggregation"]["on_fail"])
    elif result in GREEN_RESULTS and dissent_policy == "escalate" and dissent:
        result = str(runtime["aggregation"]["on_inconclusive"])
    criteria: list[dict[str, object]] = []
    for criterion in runtime["criteria"]:
        source_results = [
            next(item for item in member["criteria"] if item["id"] == criterion["id"])
            for member in members
        ]
        pass_count = sum(item["result"] == "pass" for item in source_results)
        criterion_result = "pass" if pass_count >= min(threshold, len(source_results)) else (
            "fail" if any(item["result"] == "fail" for item in source_results)
            else "inconclusive"
        )
        evidence: dict[str, dict[str, str]] = {}
        for source in source_results:
            for item in source["evidence"]:
                existing = evidence.get(str(item["id"]))
                _refuse(
                    existing is None or existing == item,
                    "evidence-conflict",
                    "panel members reuse an evidence id for different evidence",
                )
                evidence[str(item["id"])] = item
        citations: dict[str, dict[str, str]] = {}
        for source in source_results:
            for item in source["citations"]:
                if item["evidence_id"] not in evidence:
                    continue
                existing = citations.get(str(item["id"]))
                _refuse(
                    existing is None or existing == item,
                    "citation-conflict",
                    "panel members reuse a citation id for different citations",
                )
                citations[str(item["id"])] = item
        mechanical_hashes = {
            str(item["mechanical_fact_hash"])
            for item in source_results
            if item["mechanical_fact_hash"] is not None
        }
        if criterion["evaluation"]["kind"] == "mechanical-fact":
            _refuse(
                len(mechanical_hashes) == 1,
                "receipt-conflict",
                "panel members cite conflicting mechanical facts",
            )
        criteria.append({
            "id": criterion["id"],
            "result": criterion_result,
            "evidence": list(evidence.values()),
            "citations": list(citations.values()),
            "rationale": (
                None if criterion["evaluation"]["kind"] == "mechanical-fact"
                else f"deterministic {method} aggregation of {len(source_results)} member results"
            ),
            "mechanical_fact_hash": (
                next(iter(mechanical_hashes)) if mechanical_hashes else None
            ),
        })
    assignment = _panel_assignment(policy_id, members)
    issuer = {
        "role": policy_id,
        "duty": "panel",
        "address": assignment["address"],
        "principal_fingerprint": assignment["principal_fingerprint"],
        "assignment_generation": assignment["assignment_generation"],
    }
    policy_hash = _sha(raw_policy)
    now = _timestamp(issued_at, "issued_at")
    payload = {
        "kind": VERDICT_KIND,
        "schema_version": VERDICT_SCHEMA_VERSION,
        "verdict_type": "panel-verdict",
        "rubric": {
            "slug": runtime["slug"],
            "version": runtime["version"],
            "semantic_hash": compiled["semantic_hash"],
        },
        "subject": normalized_subject,
        "assignment": assignment,
        "issuer": issuer,
        "criteria": criteria,
        "result": result,
        "dissent": dissent,
        "source_verdict_hashes": [str(member["verdict_hash"]) for member in members],
        "supersedes": [],
        "composition": {
            "policy_hash": policy_hash,
            "method": method,
            "threshold": threshold,
            "quorum_required": quorum,
            "quorum_observed": observed,
            "distinct_principals": sorted(seen_principals),
            "member_verdicts": [str(member["verdict_hash"]) for member in members],
            "veto_roles": list(veto_roles),
            "dissent_policy": dissent_policy,
            "vetoed": vetoed,
            "original_verdicts_preserved": True,
        },
        "issued_at": _format_time(now),
        "expires_at": _format_time(now + timedelta(seconds=int(runtime["freshness"]["max_age_seconds"]))),
        "idempotency_key": _reference(idempotency_key, "idempotency_key"),
        "judgment_not_mechanical": True,
    }
    payload_hash = _sha(payload)
    stamped = {
        **payload,
        "payload_hash": payload_hash,
        "attestation": {
            "kind": "deterministic-aggregation",
            "receipt_hash": policy_hash,
            "payload_hash": payload_hash,
        },
    }
    return {**stamped, "verdict_hash": _sha(stamped)}


def validate_verdict_document(value: object) -> dict[str, object]:
    verdict = _exact(value, _VERDICT_KEYS, "verdict")
    _refuse(verdict.get("kind") == VERDICT_KIND, "wrong-kind", "expected governed verdict", "verdict/kind")
    _refuse(verdict.get("schema_version") == 1, "unsupported-schema", "verdict schema is invalid", "verdict/schema_version")
    verdict_type = verdict.get("verdict_type")
    _refuse(verdict_type in VERDICT_TYPES, "invalid-verdict-type", "verdict type is unsupported", "verdict/verdict_type")
    rubric = _exact(verdict.get("rubric"), _VERDICT_RUBRIC_KEYS, "verdict/rubric")
    _safe_id(rubric.get("slug"), "verdict/rubric/slug")
    _refuse(isinstance(rubric.get("version"), str) and _VERSION_RE.fullmatch(rubric["version"]), "invalid-version", "verdict rubric version is invalid", "verdict/rubric/version")
    _hash(rubric.get("semantic_hash"), "verdict/rubric/semantic_hash")
    subject = normalize_subject(verdict.get("subject"), "verdict/subject")
    assignment = _normalize_assignment(verdict.get("assignment"), "verdict/assignment")
    issuer = _exact(verdict.get("issuer"), _ISSUER_KEYS, "verdict/issuer")
    _safe_id(issuer.get("role"), "verdict/issuer/role")
    _refuse(issuer.get("duty") in JUDGMENT_DUTIES, "role-unavailable", "verdict issuer duty is invalid", "verdict/issuer/duty")
    _reference(issuer.get("address"), "verdict/issuer/address")
    principal = _hash(issuer.get("principal_fingerprint"), "verdict/issuer/principal_fingerprint")
    _positive_int(issuer.get("assignment_generation"), "verdict/issuer/assignment_generation", 1_000_000)
    for field in ("role", "duty", "address", "principal_fingerprint", "assignment_generation"):
        _refuse(issuer.get(field) == assignment[field], "assignment-invalid", f"verdict issuer {field} differs from assignment", "verdict/issuer")
    for field in ("assignment_hash", "assignment_generation", "story", "workflow_address"):
        _refuse(assignment[field] == subject[field], "assignment-invalid", f"verdict assignment {field} differs from subject", "verdict/assignment")
    _refuse(principal not in subject["implementer_principals"], "separation-violation", "implementer issued an independent verdict", "verdict/issuer/principal_fingerprint")
    if verdict_type == "panel-verdict":
        _refuse(assignment["duty"] == "panel", "role-unavailable", "panel verdict requires a panel assignment", "verdict/assignment/duty")
    else:
        _refuse(_verdict_role_allowed(str(verdict_type), str(assignment["duty"])), "role-unavailable", "assignment duty cannot issue this verdict type", "verdict/assignment/duty")
        declared_independent = {
            item["principal_fingerprint"] for item in assignment["independent_from"]
        }
        _refuse(
            set(subject["implementer_principals"]) <= declared_independent,
            "separation-violation",
            "verdict assignment does not prove independence from every implementer",
            "verdict/assignment/independent_from",
        )
    criteria = verdict.get("criteria")
    _refuse(isinstance(criteria, list) and 0 < len(criteria) <= 100, "verdict-insufficient", "verdict criteria must be non-empty and bounded", "verdict/criteria")
    ids: set[str] = set()
    for index, raw in enumerate(criteria):
        item = _exact(raw, _CRITERION_RESULT_KEYS, f"verdict/criteria/{index}")
        item_id = _safe_id(item.get("id"), f"verdict/criteria/{index}/id")
        _refuse(item_id not in ids, "duplicate-id", "verdict repeats a criterion", f"verdict/criteria/{index}/id")
        ids.add(item_id)
        _refuse(item.get("result") in CRITERION_RESULTS, "invalid-result", "criterion result is invalid", f"verdict/criteria/{index}/result")
        evidence = _normalize_evidence(item.get("evidence"), f"verdict/criteria/{index}/evidence")
        _normalize_citations(item.get("citations"), evidence, f"verdict/criteria/{index}/citations")
        rationale = item.get("rationale")
        if rationale is not None:
            _bounded_string(rationale, f"verdict/criteria/{index}/rationale", 20_000)
        mechanical = item.get("mechanical_fact_hash")
        if mechanical is not None:
            _hash(mechanical, f"verdict/criteria/{index}/mechanical_fact_hash")
    _refuse(verdict.get("result") in VERDICT_RESULTS, "invalid-result", "verdict result is invalid", "verdict/result")
    dissent = verdict.get("dissent")
    _refuse(isinstance(dissent, list) and len(dissent) <= 200, "invalid-dissent", "dissent must be bounded", "verdict/dissent")
    for index, raw in enumerate(dissent):
        item = _exact(raw, _DISSENT_KEYS, f"verdict/dissent/{index}")
        _reference(item.get("source"), f"verdict/dissent/{index}/source")
        _reference(item.get("role"), f"verdict/dissent/{index}/role")
        _reference(item.get("result"), f"verdict/dissent/{index}/result")
        _bounded_string(item.get("reason"), f"verdict/dissent/{index}/reason", 1_000)
    lineages: dict[str, list[str]] = {}
    for field in ("source_verdict_hashes", "supersedes"):
        values = verdict.get(field)
        _refuse(
            isinstance(values, list) and len(values) <= 200
            and all(isinstance(item, str) and _HASH_RE.fullmatch(item) for item in values)
            and len(set(values)) == len(values) and values == sorted(values),
            "invalid-lineage", f"{field} must contain sorted unique hashes",
            f"verdict/{field}",
        )
        lineages[field] = values
    source_hashes = lineages["source_verdict_hashes"]
    supersedes = lineages["supersedes"]
    _refuse(not set(source_hashes) & set(supersedes), "invalid-lineage", "a verdict cannot both source and supersede the same verdict", "verdict")
    composition = verdict.get("composition")
    if verdict_type == "panel-verdict":
        _refuse(bool(source_hashes) and not supersedes, "invalid-lineage", "panel verdict requires source members and cannot supersede", "verdict")
        comp = _exact(composition, _COMPOSITION_KEYS, "verdict/composition")
        policy_hash = _hash(comp.get("policy_hash"), "verdict/composition/policy_hash")
        _refuse(comp.get("method") in {"any", "at_least", "unanimous"}, "invalid-aggregation", "panel method is invalid", "verdict/composition/method")
        for field in ("threshold", "quorum_required"):
            _positive_int(comp.get(field), f"verdict/composition/{field}", len(source_hashes))
        _nonnegative_int(comp.get("quorum_observed"), "verdict/composition/quorum_observed", len(source_hashes))
        _refuse(comp["threshold"] <= comp["quorum_required"], "invalid-threshold", "panel threshold cannot exceed quorum", "verdict/composition/threshold")
        if comp["method"] == "any":
            _refuse(comp["threshold"] == 1, "invalid-threshold", "any panel threshold must be one", "verdict/composition/threshold")
        elif comp["method"] == "unanimous":
            _refuse(comp["threshold"] == comp["quorum_required"], "invalid-threshold", "unanimous panel threshold must equal quorum", "verdict/composition/threshold")
        principals = comp.get("distinct_principals")
        _refuse(
            isinstance(principals, list) and len(principals) == len(source_hashes)
            and all(isinstance(item, str) and _HASH_RE.fullmatch(item) for item in principals)
            and len(set(principals)) == len(principals)
            and principals == sorted(principals),
            "separation-violation",
            "panel composition must retain one sorted distinct principal per member",
            "verdict/composition/distinct_principals",
        )
        member_hashes = comp.get("member_verdicts")
        _refuse(member_hashes == source_hashes, "invalid-lineage", "panel member hashes differ from source lineage", "verdict/composition/member_verdicts")
        veto_roles = comp.get("veto_roles")
        _refuse(
            isinstance(veto_roles, list) and len(veto_roles) <= len(source_hashes)
            and all(isinstance(item, str) and _SAFE_ID_RE.fullmatch(item) for item in veto_roles)
            and len(set(veto_roles)) == len(veto_roles),
            "invalid-value", "panel veto roles must be unique role ids",
            "verdict/composition/veto_roles",
        )
        dissent_policy = comp.get("dissent_policy")
        _refuse(dissent_policy in {"preserve", "block", "escalate"}, "invalid-value", "panel dissent policy is invalid", "verdict/composition/dissent_policy")
        expected_policy = {
            "id": assignment["role"],
            "method": comp["method"],
            "threshold": comp["threshold"],
            "quorum": comp["quorum_required"],
            "veto_roles": veto_roles,
            "dissent_policy": dissent_policy,
        }
        _refuse(policy_hash == _sha(expected_policy), "receipt-forged", "panel composition policy hash does not match its exact policy", "verdict/composition/policy_hash")
        _refuse(isinstance(comp.get("vetoed"), bool), "wrong-type", "panel vetoed must be boolean", "verdict/composition/vetoed")
        _refuse(comp.get("original_verdicts_preserved") is True, "history-erased", "panel must preserve source verdicts", "verdict/composition/original_verdicts_preserved")
        _refuse(assignment["principal_fingerprint"] == _sha({"panel": assignment["role"], "principals": principals}), "receipt-forged", "panel synthetic principal differs from its members", "verdict/assignment/principal_fingerprint")
        _refuse(assignment["session_binding_key"] == _sha({"panel": assignment["role"], "members": source_hashes}), "receipt-forged", "panel session binding differs from its members", "verdict/assignment/session_binding_key")
    else:
        _refuse(composition is None, "unknown-content", "only panel verdicts carry composition", "verdict/composition")
        if verdict_type == "meta-verdict":
            _refuse(bool(source_hashes), "invalid-lineage", "meta verdict requires source verdicts", "verdict/source_verdict_hashes")
            _refuse(subject["kind"] == "verdict-set" and subject["hash"] == _sha({"verdicts": source_hashes}), "subject-mismatch", "meta subject does not bind its exact source verdict set", "verdict/subject/hash")
        else:
            _refuse(not source_hashes and subject["kind"] != "verdict-set", "invalid-lineage", "only meta verdicts may carry a verdict-set subject or sources", "verdict")
    issued = _timestamp(verdict.get("issued_at"), "verdict/issued_at")
    expires = _timestamp(verdict.get("expires_at"), "verdict/expires_at")
    _refuse(expires > issued, "invalid-time", "verdict expiry must follow issue time", "verdict/expires_at")
    _reference(verdict.get("idempotency_key"), "verdict/idempotency_key")
    _refuse(verdict.get("judgment_not_mechanical") is True, "mechanical-counterfeit", "verdict must remain labeled as judgment", "verdict/judgment_not_mechanical")
    payload_hash = _hash(verdict.get("payload_hash"), "verdict/payload_hash")
    attestation = _exact(verdict.get("attestation"), _ATTESTATION_KEYS, "verdict/attestation")
    expected_attestation = "deterministic-aggregation" if verdict_type == "panel-verdict" else "driver-receipt"
    _refuse(attestation.get("kind") == expected_attestation, "issuer-invalid", "verdict attestation kind does not match verdict type", "verdict/attestation/kind")
    receipt_hash = _hash(attestation.get("receipt_hash"), "verdict/attestation/receipt_hash")
    if verdict_type == "panel-verdict":
        _refuse(receipt_hash == policy_hash, "receipt-forged", "panel attestation differs from composition policy", "verdict/attestation/receipt_hash")
    _refuse(attestation.get("payload_hash") == payload_hash, "receipt-forged", "attestation does not bind payload", "verdict/attestation/payload_hash")
    verdict_hash = _hash(verdict.get("verdict_hash"), "verdict/verdict_hash")
    payload = {
        key: item for key, item in verdict.items()
        if key not in {"payload_hash", "attestation", "verdict_hash"}
    }
    _refuse(_sha(payload) == payload_hash, "receipt-forged", "verdict payload hash does not match", "verdict/payload_hash")
    stamped = {**payload, "payload_hash": payload_hash, "attestation": attestation}
    _refuse(_sha(stamped) == verdict_hash, "receipt-forged", "verdict hash does not match", "verdict/verdict_hash")
    return dict(verdict)


def verdict_rubric_issues(
    verdict: dict[str, object],
    rubric: dict[str, object],
) -> list[dict[str, str]]:
    """Re-evaluate a stored verdict against the exact current rubric."""
    issues: list[dict[str, str]] = []
    runtime = rubric["rubric"]
    expected = list(runtime["criteria"])
    by_id = {str(item["id"]): item for item in verdict["criteria"]}
    if set(by_id) != {str(item["id"]) for item in expected}:
        return [{
            "code": "verdict-insufficient",
            "message": "criterion ids no longer match the exact rubric",
        }]
    for criterion in expected:
        stored = by_id[str(criterion["id"])]
        if stored["result"] not in criterion["allowed_results"]:
            issues.append({
                "code": "verdict-insufficient",
                "message": f"criterion {criterion['id']} uses a disallowed result",
            })
        evidence_kinds = {item["kind"] for item in stored["evidence"]}
        if not set(criterion["required_evidence_kinds"]) <= evidence_kinds:
            issues.append({
                "code": "verdict-insufficient",
                "message": f"criterion {criterion['id']} lost required evidence",
            })
        if len(stored["citations"]) < int(criterion["min_citations"]):
            issues.append({
                "code": "verdict-insufficient",
                "message": f"criterion {criterion['id']} has too few citations",
            })
        if criterion["evaluation"]["kind"] == "mechanical-fact":
            if stored["mechanical_fact_hash"] is None or stored["rationale"] is not None:
                issues.append({
                    "code": "mechanical-counterfeit",
                    "message": f"criterion {criterion['id']} no longer cites only a mechanical fact",
                })
        elif stored["mechanical_fact_hash"] is not None:
            issues.append({
                "code": "mechanical-counterfeit",
                "message": f"criterion {criterion['id']} mislabeled judgment as mechanical",
            })
        rationale = stored["rationale"]
        if rationale is not None and len(str(rationale).encode("utf-8")) > int(criterion["rationale_max_bytes"]):
            issues.append({
                "code": "verdict-insufficient",
                "message": f"criterion {criterion['id']} rationale exceeds the rubric bound",
            })
    if verdict["verdict_type"] != "panel-verdict":
        recomputed, _dissent = _aggregate_criteria(rubric, list(by_id.values()))
        if recomputed != verdict["result"]:
            issues.append({
                "code": "verdict-insufficient",
                "message": "stored overall result does not match rubric aggregation",
            })
    issued = _timestamp(verdict["issued_at"], "verdict issued_at")
    expected_expiry = issued + timedelta(
        seconds=int(runtime["freshness"]["max_age_seconds"])
    )
    if _timestamp(verdict["expires_at"], "verdict expires_at") != expected_expiry:
        issues.append({
            "code": "verdict-stale",
            "message": "verdict expiry does not match rubric freshness",
        })
    return issues


def panel_composition_issues(
    verdict: dict[str, object],
    rubric: dict[str, object],
    verdicts_by_hash: dict[str, dict[str, object]],
) -> list[dict[str, str]]:
    """Recompute a deterministic panel outcome from retained members."""
    if verdict["verdict_type"] != "panel-verdict":
        return []
    composition = verdict["composition"]
    sources = [
        verdicts_by_hash[str(item)]
        for item in verdict["source_verdict_hashes"]
    ]
    observed = sum(item["result"] not in NEUTRAL_RESULTS for item in sources)
    green = [item for item in sources if item["result"] in GREEN_RESULTS]
    red = [item for item in sources if item["result"] in RED_RESULTS]
    runtime = rubric["rubric"]
    aggregation = runtime["aggregation"]
    if observed < int(composition["quorum_required"]):
        expected = str(aggregation["on_inconclusive"])
    elif bool(composition["vetoed"]):
        expected = str(aggregation["on_fail"])
    elif composition["method"] == "unanimous":
        expected = str(
            aggregation["on_pass"]
            if len(green) == observed else aggregation["on_fail"]
        )
    elif len(green) >= int(composition["threshold"]):
        expected = str(aggregation["on_pass"])
    elif red:
        expected = str(aggregation["on_fail"])
    else:
        expected = str(aggregation["on_abstain"])
    expected_dissent = [
        {
            "source": str(member["verdict_hash"]),
            "role": str(member["issuer"]["role"]),
            "result": str(member["result"]),
            "reason": "member result differs from panel result",
        }
        for member in sources if member["result"] != expected
    ]
    if expected in GREEN_RESULTS and expected_dissent:
        if composition["dissent_policy"] == "block":
            expected = str(aggregation["on_fail"])
        elif composition["dissent_policy"] == "escalate":
            expected = str(aggregation["on_inconclusive"])
    issues: list[dict[str, str]] = []
    if verdict["result"] != expected:
        issues.append({
            "code": "receipt-conflict",
            "message": "panel result differs from deterministic composition",
        })
    if verdict["dissent"] != expected_dissent:
        issues.append({
            "code": "invalid-dissent",
            "message": "panel dissent differs from retained member verdicts",
        })
    return issues


def verdict_freshness_issues(
    verdict: dict[str, object],
    subject: object,
    rubric: dict[str, object],
    now: str,
    *,
    verdict_set_hash: str | None = None,
) -> list[dict[str, str]]:
    current = normalize_subject(subject)
    issues: list[dict[str, str]] = []
    stored = verdict["subject"]
    if stored["kind"] == "verdict-set" and verdict_set_hash is not None:
        if stored["hash"] != verdict_set_hash:
            issues.append({"code": "verdict-stale", "message": "underlying verdict set changed"})
    elif stored["kind"] != current["kind"] or stored["hash"] != current["hash"]:
        issues.append({"code": "verdict-stale", "message": "subject kind or hash changed"})
    for field in (
        "repository_hash", "program_hash", "program_run_id", "phase", "story",
        "workflow_address", "assignment_hash", "assignment_generation",
        "ledger_head", "implementer_principals",
    ):
        if stored[field] != current[field]:
            issues.append({"code": "verdict-stale", "message": f"{field} changed"})
    if (
        verdict["rubric"]["slug"] != rubric["rubric"]["slug"]
        or verdict["rubric"]["version"] != rubric["rubric"]["version"]
    ):
        issues.append({"code": "verdict-stale", "message": "rubric slug or version changed"})
    elif verdict["rubric"]["semantic_hash"] != rubric["semantic_hash"]:
        issues.append({"code": "verdict-stale", "message": "rubric semantic hash changed"})
    else:
        issues.extend(verdict_rubric_issues(verdict, rubric))
    observed = _timestamp(now, "now")
    if observed < _timestamp(verdict["issued_at"], "verdict issued_at"):
        issues.append({"code": "verdict-stale", "message": "verdict is from the future"})
    if observed > _timestamp(verdict["expires_at"], "verdict expires_at"):
        issues.append({"code": "verdict-stale", "message": "verdict freshness window expired"})
    return issues


def _resolve_history(
    verdicts: list[dict[str, object]],
) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    by_hash = {str(item["verdict_hash"]): item for item in verdicts}
    _refuse(len(by_hash) == len(verdicts), "duplicate-verdict", "verdict set repeats a hash")
    for item in verdicts:
        sources: list[dict[str, object]] = []
        for source_hash in item["source_verdict_hashes"]:
            _refuse(source_hash in by_hash, "invalid-lineage", "source verdict is absent from proof history")
            sources.append(by_hash[source_hash])
        if item["verdict_type"] == "panel-verdict":
            _refuse(all(source["verdict_type"] == "agent-verdict" for source in sources), "invalid-lineage", "panel source is not an agent verdict")
            _refuse(all(source["subject"] == item["subject"] for source in sources), "invalid-lineage", "panel sources cover different subjects")
            _refuse(all(source["rubric"] == item["rubric"] for source in sources), "invalid-lineage", "panel sources use different rubrics")
            principals = sorted(
                str(source["issuer"]["principal_fingerprint"])
                for source in sources
            )
            _refuse(principals == item["composition"]["distinct_principals"], "separation-violation", "panel source principals differ from composition")
            observed = sum(source["result"] not in NEUTRAL_RESULTS for source in sources)
            _refuse(observed == item["composition"]["quorum_observed"], "receipt-conflict", "panel observed quorum differs from its sources")
            vetoed = any(
                source["result"] in RED_RESULTS
                and source["issuer"]["role"] in item["composition"]["veto_roles"]
                for source in sources
            )
            _refuse(vetoed == item["composition"]["vetoed"], "receipt-conflict", "panel veto state differs from its sources")
        elif item["verdict_type"] == "meta-verdict":
            _refuse(all(source["verdict_type"] != "meta-verdict" for source in sources), "invalid-lineage", "meta verdict recursively sources another meta verdict")
            for source in sources:
                for field in (
                    "repository_hash", "program_hash", "program_run_id",
                    "phase", "story", "workflow_address", "assignment_hash",
                    "assignment_generation", "ledger_head",
                    "implementer_principals",
                ):
                    _refuse(source["subject"][field] == item["subject"][field], "invalid-lineage", f"meta source {field} differs from its verdict-set subject")
            source_principals = {
                source["issuer"]["principal_fingerprint"] for source in sources
            }
            declared = {
                proof["principal_fingerprint"]
                for proof in item["assignment"]["independent_from"]
            }
            _refuse(item["issuer"]["principal_fingerprint"] not in source_principals and source_principals <= declared, "separation-violation", "meta verdict is not independent from every source author")
    superseded_by: dict[str, str] = {}
    for item in verdicts:
        for prior_hash in item["supersedes"]:
            _refuse(prior_hash in by_hash, "supersession-invalid", "superseded verdict is absent from history")
            prior = by_hash[prior_hash]
            _refuse(_lineage_matches(item, prior), "supersession-invalid", "supersession crosses a verdict lineage")
            _refuse(_timestamp(prior["issued_at"], "prior issued_at") < _timestamp(item["issued_at"], "issued_at"), "supersession-invalid", "supersession order is invalid")
            _refuse(prior_hash not in superseded_by, "supersession-conflict", "one verdict is superseded twice")
            superseded_by[prior_hash] = str(item["verdict_hash"])
    active = [item for item in verdicts if item["verdict_hash"] not in superseded_by]
    history = [
        {
            "verdict_hash": item["verdict_hash"],
            "verdict_type": item["verdict_type"],
            "result": item["result"],
            "issuer": item["issuer"],
            "subject_hash": item["subject"]["hash"],
            "active": item["verdict_hash"] not in superseded_by,
            "superseded_by": superseded_by.get(str(item["verdict_hash"])),
        }
        for item in sorted(verdicts, key=lambda value: (value["issued_at"], value["verdict_hash"]))
    ]
    return active, history


def _normalize_gate(value: object) -> dict[str, object]:
    gate = _exact(value, _GATE_KEYS, "gate")
    _refuse(gate.get("kind") == QUALITY_GATE_KIND, "wrong-kind", "expected quality gate", "gate/kind")
    _refuse(gate.get("schema_version") == 1, "unsupported-schema", "quality gate schema is invalid", "gate/schema_version")
    gate_id = _safe_id(gate.get("id"), "gate/id")
    _refuse(gate.get("subject_type") in set(SUBJECT_TYPES) - {"verdict-set"}, "unsupported-subject", "gate subject type is unsupported", "gate/subject_type")
    fact_raw = gate.get("mechanical_facts")
    _refuse(isinstance(fact_raw, list) and len(fact_raw) <= 100, "invalid-value", "mechanical requirements must be bounded", "gate/mechanical_facts")
    facts: list[dict[str, object]] = []
    fact_ids: set[str] = set()
    for index, raw in enumerate(fact_raw):
        item = _exact(raw, _FACT_REQUIREMENT_KEYS, f"gate/mechanical_facts/{index}")
        fact_id = _safe_id(item.get("id"), f"gate/mechanical_facts/{index}/id")
        _refuse(fact_id not in fact_ids, "duplicate-id", "gate repeats a mechanical fact", f"gate/mechanical_facts/{index}/id")
        fact_ids.add(fact_id)
        facts.append({
            "id": fact_id,
            "max_age_seconds": _positive_int(item.get("max_age_seconds"), f"gate/mechanical_facts/{index}/max_age_seconds", 31_536_000),
        })
    requirements_raw = gate.get("requirements")
    _refuse(isinstance(requirements_raw, list) and 0 < len(requirements_raw) <= 100, "verdict-insufficient", "gate requires at least one verdict requirement", "gate/requirements")
    requirements: list[dict[str, object]] = []
    requirement_ids: set[str] = set()
    for index, raw in enumerate(requirements_raw):
        pointer = f"gate/requirements/{index}"
        item = _exact(raw, _REQUIREMENT_KEYS, pointer)
        item_id = _safe_id(item.get("id"), f"{pointer}/id")
        _refuse(item_id not in requirement_ids, "duplicate-id", "gate repeats a requirement", f"{pointer}/id")
        requirement_ids.add(item_id)
        kind = item.get("kind")
        _refuse(kind in GATE_REQUIREMENT_KINDS, "invalid-value", "requirement kind is unsupported", f"{pointer}/kind")
        method = item.get("method")
        _refuse(method in {"all", "any", "at_least", "unanimous"}, "invalid-aggregation", "requirement method is unsupported", f"{pointer}/method")
        threshold = _positive_int(item.get("threshold"), f"{pointer}/threshold", 64)
        roles = item.get("roles")
        _refuse(isinstance(roles, list) and roles and len(roles) <= 64 and len(set(roles)) == len(roles) and all(isinstance(role, str) and _SAFE_ID_RE.fullmatch(role) for role in roles), "invalid-value", "requirement roles must be unique role ids", f"{pointer}/roles")
        veto_roles = item.get("veto_roles")
        _refuse(isinstance(veto_roles, list) and len(veto_roles) <= 64 and len(set(veto_roles)) == len(veto_roles) and all(isinstance(role, str) and _SAFE_ID_RE.fullmatch(role) for role in veto_roles), "invalid-value", "veto roles must be unique role ids", f"{pointer}/veto_roles")
        meta_raw = _exact(item.get("meta_audit"), _META_AUDIT_KEYS, f"{pointer}/meta_audit")
        mode = meta_raw.get("mode")
        _refuse(mode in META_AUDIT_MODES, "invalid-value", "meta audit mode is unsupported", f"{pointer}/meta_audit/mode")
        sample_size = _nonnegative_int(meta_raw.get("sample_size"), f"{pointer}/meta_audit/sample_size", 64)
        if mode == "none":
            _refuse(sample_size == 0 and meta_raw.get("rubric") is None and meta_raw.get("role") is None, "invalid-value", "disabled meta audit cannot name policy", f"{pointer}/meta_audit")
            meta_rubric = None
            meta_role = None
        else:
            if mode == "random":
                _refuse(sample_size > 0, "invalid-bound", "random meta audit needs a positive sample size", f"{pointer}/meta_audit/sample_size")
            else:
                _refuse(sample_size == 0, "invalid-bound", "full meta audit uses the entire set and requires sample_size zero", f"{pointer}/meta_audit/sample_size")
            meta_rubric = _safe_id(meta_raw.get("rubric"), f"{pointer}/meta_audit/rubric")
            meta_role = _safe_id(meta_raw.get("role"), f"{pointer}/meta_audit/role")
        if kind == "council":
            _refuse(
                mode == "none",
                "invalid-value",
                "council decisions carry their deliberation audit lineage; verdict meta-audit policy does not reclassify it",
                f"{pointer}/meta_audit",
            )
        requirements.append({
            "id": item_id,
            "kind": kind,
            "rubric": _safe_id(item.get("rubric"), f"{pointer}/rubric"),
            "roles": list(roles),
            "method": method,
            "threshold": threshold,
            "veto_roles": list(veto_roles),
            "meta_audit": {
                "mode": mode,
                "sample_size": sample_size,
                "rubric": meta_rubric,
                "role": meta_role,
            },
        })
    operator = gate.get("operator")
    _refuse(operator in AGGREGATION_METHODS, "invalid-aggregation", "gate operator is unsupported", "gate/operator")
    threshold = _positive_int(gate.get("threshold"), "gate/threshold", len(requirements))
    if operator == "all":
        _refuse(threshold == len(requirements), "invalid-threshold", "all gate threshold must equal its requirement count", "gate/threshold")
    elif operator == "any":
        _refuse(threshold == 1, "invalid-threshold", "any gate threshold must be one", "gate/threshold")
    dissent_policy = gate.get("dissent_policy")
    _refuse(dissent_policy in {"preserve", "block", "escalate"}, "invalid-value", "gate dissent policy is unsupported", "gate/dissent_policy")
    routes = _exact(gate.get("routes"), _ROUTE_KEYS, "gate/routes")
    allowed_routes = {
        "pass": {"advance", "complete"},
        "fail": {"repair", "escalate", "block"},
        "pending": {"wait", "checkpoint", "escalate", "block"},
        "refused": {"block", "escalate"},
    }
    normalized_routes: dict[str, str] = {}
    for outcome, allowed in allowed_routes.items():
        route = routes.get(outcome)
        _refuse(route in allowed, "invalid-route", f"{outcome} route is unsupported", f"gate/routes/{outcome}")
        normalized_routes[outcome] = str(route)
    repair_raw = _exact(gate.get("repair"), _REPAIR_KEYS, "gate/repair")
    repair = {
        "max_rounds": _positive_int(repair_raw.get("max_rounds"), "gate/repair/max_rounds", 100),
        "on_exhausted": repair_raw.get("on_exhausted"),
    }
    _refuse(repair["on_exhausted"] in {"escalate", "block"}, "invalid-route", "repair exhaustion route is unsupported", "gate/repair/on_exhausted")
    return {
        "kind": QUALITY_GATE_KIND,
        "schema_version": VERDICT_SCHEMA_VERSION,
        "id": gate_id,
        "subject_type": gate["subject_type"],
        "mechanical_facts": facts,
        "requirements": requirements,
        "operator": operator,
        "threshold": threshold,
        "dissent_policy": dissent_policy,
        "routes": normalized_routes,
        "repair": repair,
    }


def _rubric_map(root: Path, values: object) -> dict[str, dict[str, object]]:
    _refuse(isinstance(values, dict), "wrong-type", "rubrics must be a slug map", "rubrics")
    result: dict[str, dict[str, object]] = {}
    for slug, value in values.items():
        _safe_id(slug, "rubrics slug")
        compiled = _compiled_rubric(root, value)
        _refuse(compiled["rubric"]["slug"] == slug, "rubric-mismatch", "rubric map key differs from document slug")
        result[slug] = compiled
    return result


def council_decision_freshness_issues(
    decision: dict[str, object],
    subject: dict[str, object],
    rubric: dict[str, object],
    now: str,
) -> list[dict[str, str]]:
    """Explain why a validated deliberative decision cannot govern now."""
    issues: list[dict[str, str]] = []
    stored = decision["subject"]
    if set(stored) != set(subject):
        issues.append({
            "code": "decision-stale",
            "message": "council decision lacks the complete freshness-bound subject",
        })
    else:
        for field in subject:
            if stored[field] != subject[field]:
                issues.append({
                    "code": "decision-stale",
                    "message": f"council decision subject {field} changed",
                })
    for field in (
        "program_run_id", "phase", "story", "workflow_address",
        "assignment_hash",
    ):
        if decision[field] != subject[field]:
            issues.append({
                "code": "decision-stale",
                "message": f"council decision {field} changed",
            })
    expected_criteria = [
        item["id"] for item in rubric["rubric"]["criteria"]
    ]
    if (
        decision["rubric"]["slug"] != rubric["rubric"]["slug"]
        or decision["rubric"]["semantic_hash"] != rubric["semantic_hash"]
        or decision["rubric"]["criteria"] != expected_criteria
    ):
        issues.append({
            "code": "decision-stale",
            "message": "council decision rubric changed",
        })
    observed = _timestamp(now, "now")
    issued = _timestamp(decision["issued_at"], "decision issued_at")
    age = (observed - issued).total_seconds()
    if age < 0 or age > int(rubric["rubric"]["freshness"]["max_age_seconds"]):
        issues.append({
            "code": "decision-stale",
            "message": "council decision freshness window expired",
        })
    return issues


def _requirement_verdict_type(kind: str) -> str:
    return {
        "independent": "agent-verdict",
        "panel": "panel-verdict",
        "architect": "architect-verdict",
    }[kind]


def _audit_selection(
    gate_hash: str,
    candidates: list[dict[str, object]],
    mode: str,
    sample_size: int,
) -> list[dict[str, object]]:
    if mode == "none":
        return []
    ranked = sorted(
        candidates,
        key=lambda item: (
            _sha({"gate": gate_hash, "verdict": item["verdict_hash"]}),
            item["verdict_hash"],
        ),
    )
    return ranked if mode == "full" else ranked[:sample_size]


def evaluate_quality_gate(
    root: Path,
    gate: object,
    subject: object,
    rubrics: object,
    mechanical_facts: list[dict[str, object]],
    verdicts: list[dict[str, object]],
    *,
    council_decisions: list[dict[str, object]] | None = None,
    now: str,
    repair_round: int = 0,
    test_failures: dict[str, object] | None = None,
) -> dict[str, object]:
    """Return a closed authority-neutral quality proof, including refusals."""
    starts = {
        "starts_work": False,
        "writes_state": False,
        "writes_repository": False,
        "writes_roadmap": False,
        "materializes_evidence": False,
        "creates_grant": False,
    }
    failure_projection: dict[str, object] | None = None
    if test_failures is not None:
        try:
            failure_projection = build_failure_projection(test_failures)
        except ValueError as exc:
            raise VerdictError("wrong-type", str(exc), "test_failures") from exc
    policy: dict[str, object] | None = None
    current: dict[str, object] | None = None
    try:
        policy = _normalize_gate(gate)
        current = normalize_subject(subject)
        _refuse(policy["subject_type"] == current["kind"], "subject-mismatch", "gate subject type differs from current subject")
        compiled_rubrics = _rubric_map(root, rubrics)
        now_value = _timestamp(now, "now")
        repair_round = _nonnegative_int(repair_round, "repair_round", 100)
        _refuse(isinstance(mechanical_facts, list) and len(mechanical_facts) <= 500, "wrong-type", "mechanical facts must be a bounded list", "mechanical_facts")
        _refuse(isinstance(verdicts, list) and len(verdicts) <= 500, "wrong-type", "verdicts must be a bounded list", "verdicts")
        _refuse(
            council_decisions is None or (
                isinstance(council_decisions, list)
                and len(council_decisions) <= 500
            ),
            "wrong-type", "council decisions must be a bounded list",
            "council_decisions",
        )
        facts = [validate_mechanical_fact(item) for item in mechanical_facts]
        validated_verdicts = [validate_verdict_document(item) for item in verdicts]
        validated_decisions: list[dict[str, object]] = []
        for index, item in enumerate(council_decisions or []):
            try:
                validated_decisions.append(validate_council_decision(item))
            except DeliberationError as exc:
                raise VerdictError(
                    "decision-invalid", str(exc),
                    f"council_decisions/{index}",
                ) from exc
        _refuse(
            len({item["decision_hash"] for item in validated_decisions})
            == len(validated_decisions),
            "duplicate-decision", "council decision set repeats a hash",
            "council_decisions",
        )
        active_verdicts, history = _resolve_history(validated_verdicts)
    except (VerdictError, RubricValidationError) as exc:
        issue = {
            "code": exc.code,
            "message": exc.message,
            "pointer": exc.pointer,
        }
        refused = {
            "kind": QUALITY_PROOF_KIND,
            "schema_version": VERDICT_SCHEMA_VERSION,
            "gate": (
                {
                    "id": policy["id"],
                    "semantic_hash": _sha(policy),
                }
                if policy is not None else None
            ),
            "subject": current,
            "result": "refused",
            "route": (
                policy["routes"]["refused"]
                if policy is not None else "block"
            ),
            "mechanical": [],
            "requirements": [],
            "dissent": [],
            "history": [],
            "decision_history": [],
            "issues": [issue],
            "remediation": ["repair the refused typed input and evaluate again"],
            "evidence_preview": {
                "mechanical_fact_hashes": [],
                "verdict_hashes": [],
                "citations": [],
                "source_verdict_hashes": [],
                "decision_hashes": [],
                "decision_citations": [],
                "obligation_ids": [],
            },
            "authority": {
                "may_advance": False,
                "may_repair": False,
                "may_materialize_evidence": False,
            },
            **({"test_failures": failure_projection} if failure_projection is not None else {}),
            **starts,
        }
        refused["proof_hash"] = _sha(refused)
        return refused

    gate_hash = _sha(policy)
    verdicts_by_hash = {
        str(item["verdict_hash"]): item for item in validated_verdicts
    }
    decisions_by_hash = {
        str(item["decision_hash"]): item for item in validated_decisions
    }
    active_hashes = {
        str(item["verdict_hash"]) for item in active_verdicts
    }
    issues: list[dict[str, str]] = []
    mechanical_projection: list[dict[str, object]] = []
    facts_by_id: dict[str, list[dict[str, object]]] = {}
    for fact in facts:
        facts_by_id.setdefault(str(fact["id"]), []).append(fact)
    for requirement in policy["mechanical_facts"]:
        candidates = facts_by_id.get(str(requirement["id"]), [])
        if not candidates:
            mechanical_projection.append({
                "id": requirement["id"], "status": "missing", "fact_hash": None,
            })
            issues.append({"code": "verdict-insufficient", "message": f"mechanical fact {requirement['id']} is missing"})
            continue
        if len(candidates) != 1:
            mechanical_projection.append({
                "id": requirement["id"], "status": "refused", "fact_hash": None,
            })
            issues.append({"code": "fact-conflict", "message": f"mechanical fact {requirement['id']} is ambiguous"})
            continue
        fact = candidates[0]
        stale_fields = [
            field for field in (
                "kind", "hash", "repository_hash", "program_hash",
                "program_run_id", "phase", "story", "workflow_address",
                "assignment_hash", "assignment_generation", "ledger_head",
                "implementer_principals",
            )
            if fact["subject"][field] != current[field]
        ]
        age = (now_value - _timestamp(fact["issued_at"], "fact issued_at")).total_seconds()
        if stale_fields or age < 0 or age > int(requirement["max_age_seconds"]):
            status = "stale"
            issues.append({"code": "verdict-stale", "message": f"mechanical fact {requirement['id']} is stale"})
        else:
            status = str(fact["result"])
            if status == "fail":
                issues.append({"code": "mechanical-failed", "message": f"mechanical fact {requirement['id']} failed"})
        mechanical_projection.append({
            "id": requirement["id"],
            "predicate": fact["predicate"],
            "status": status,
            "fact_hash": fact["fact_hash"],
            "issuer": fact["issuer"],
        })

    requirement_projection: list[dict[str, object]] = []
    all_dissent: list[dict[str, object]] = []
    contributing_decision_hashes: set[str] = set()
    contributing_obligation_ids: set[str] = set()
    for requirement in policy["requirements"]:
        rubric = compiled_rubrics.get(str(requirement["rubric"]))
        if rubric is None:
            issues.append({"code": "rubric-missing", "message": f"requirement {requirement['id']} rubric is absent"})
            requirement_projection.append({
                "id": requirement["id"], "status": "refused", "contributors": [],
                "non_contributors": [], "meta_audit": [],
            })
            continue
        if requirement["kind"] == "council":
            candidates = [
                item for item in validated_decisions
                if item["rubric"]["slug"] == requirement["rubric"]
                and item["council_id"] in requirement["roles"]
            ]
            contributors: list[dict[str, object]] = []
            non_contributors: list[dict[str, object]] = []
            for candidate in candidates:
                freshness = council_decision_freshness_issues(
                    candidate, current, rubric, now,
                )
                if freshness:
                    non_contributors.append({
                        "decision_hash": candidate["decision_hash"],
                        "result": candidate["result"],
                        "reasons": freshness,
                    })
                else:
                    contributors.append(candidate)
            repeated_councils = {
                council_id for council_id in requirement["roles"]
                if sum(
                    item["council_id"] == council_id
                    for item in contributors
                ) > 1
            }
            green = [
                item for item in contributors if item["result"] == "advance"
            ]
            red = [
                item for item in contributors
                if item["result"] in {
                    "repair", "dissent", "quorum-lost", "exhausted",
                }
            ]
            method = requirement["method"]
            vetoed = any(
                item["council_id"] in requirement["veto_roles"]
                for item in red
            )
            if repeated_councils:
                status = "refused"
                issues.append({
                    "code": "decision-conflict",
                    "message": (
                        f"requirement {requirement['id']} has multiple active "
                        f"decisions for {', '.join(sorted(repeated_councils))}"
                    ),
                })
            elif vetoed:
                status = "fail"
            elif method in {"all", "unanimous"}:
                status = (
                    "pass"
                    if len(contributors) >= int(requirement["threshold"])
                    and len(green) == len(contributors)
                    else "fail" if red or non_contributors else "pending"
                )
            elif len(green) >= int(requirement["threshold"]):
                status = "pass"
            elif red or non_contributors:
                status = "fail"
            else:
                status = "pending"
            dissent = [
                {
                    "source": item["receipt_hash"],
                    "role": item["role"],
                    "result": item["vote"],
                    "reason": "council minority dissent is preserved",
                }
                for decision in contributors
                for item in decision["dissent"]
            ]
            if green and red:
                dissent.append({
                    "source": str(requirement["id"]),
                    "role": "gate",
                    "result": "conflict",
                    "reason": "active council decisions disagree",
                })
            all_dissent.extend(dissent)
            dissent_escalated = bool(
                dissent and policy["dissent_policy"] == "escalate"
            )
            if dissent and policy["dissent_policy"] == "block":
                status = "fail" if status != "refused" else status
            elif dissent_escalated:
                status = "pending" if status != "refused" else status
            if status != "pass":
                issues.append({
                    "code": (
                        "decision-refused" if status == "refused"
                        else "decision-insufficient"
                    ),
                    "message": f"requirement {requirement['id']} is {status}",
                })
            for decision in contributors:
                contributing_decision_hashes.add(
                    str(decision["decision_hash"])
                )
                contributing_obligation_ids.update(
                    str(item["id"]) for item in decision["obligations"]
                )
            requirement_projection.append({
                "id": requirement["id"],
                "kind": "council",
                "rubric": {
                    "slug": rubric["rubric"]["slug"],
                    "semantic_hash": rubric["semantic_hash"],
                },
                "status": status,
                "contributors": [
                    {
                        "decision_hash": item["decision_hash"],
                        "decision_type": item["decision_type"],
                        "council_id": item["council_id"],
                        "result": item["result"],
                        "authority": item["authority"],
                        "obligation_ids": [
                            obligation["id"]
                            for obligation in item["obligations"]
                        ],
                    }
                    for item in contributors
                ],
                "non_contributors": non_contributors,
                "method": method,
                "threshold": requirement["threshold"],
                "veto_roles": requirement["veto_roles"],
                "meta_audit": [],
                "dissent": dissent,
                "dissent_escalated": dissent_escalated,
            })
            continue
        wanted_type = _requirement_verdict_type(str(requirement["kind"]))
        candidates = [
            item for item in active_verdicts
            if item["verdict_type"] == wanted_type
            and item["rubric"]["slug"] == requirement["rubric"]
            and item["issuer"]["role"] in requirement["roles"]
        ]
        contributors: list[dict[str, object]] = []
        non_contributors: list[dict[str, object]] = []
        for candidate in candidates:
            freshness = verdict_freshness_issues(candidate, current, rubric, now)
            if candidate["verdict_type"] == "panel-verdict":
                freshness.extend(
                    panel_composition_issues(
                        candidate, rubric, verdicts_by_hash,
                    )
                )
            if any(
                source_hash not in active_hashes
                for source_hash in candidate["source_verdict_hashes"]
            ):
                freshness.append({
                    "code": "verdict-stale",
                    "message": "a source verdict was superseded",
                })
            for criterion in rubric["rubric"]["criteria"]:
                if criterion["evaluation"]["kind"] != "mechanical-fact":
                    continue
                stored_result = next(
                    item for item in candidate["criteria"]
                    if item["id"] == criterion["id"]
                )
                matching_facts = facts_by_id.get(
                    str(criterion["evaluation"]["fact"]), []
                )
                if not any(
                    item["fact_hash"] == stored_result["mechanical_fact_hash"]
                    and item["subject"] == current
                    and item["result"] == stored_result["result"]
                    for item in matching_facts
                ):
                    freshness.append({
                        "code": "verdict-stale",
                        "message": (
                            f"criterion {criterion['id']} no longer binds a "
                            "current mechanical fact"
                        ),
                    })
            if freshness:
                non_contributors.append({
                    "verdict_hash": candidate["verdict_hash"],
                    "result": candidate["result"],
                    "reasons": freshness,
                })
            else:
                contributors.append(candidate)
        stale_candidates = bool(non_contributors)
        principals = [item["issuer"]["principal_fingerprint"] for item in contributors]
        if len(set(principals)) != len(principals):
            issues.append({"code": "separation-violation", "message": f"requirement {requirement['id']} repeats a principal"})
            status = "refused"
        else:
            green = [item for item in contributors if item["result"] in GREEN_RESULTS]
            red = [item for item in contributors if item["result"] in RED_RESULTS]
            vetoed = any(item["issuer"]["role"] in requirement["veto_roles"] for item in red)
            method = requirement["method"]
            if vetoed:
                status = "fail"
            elif method in {"all", "unanimous"}:
                status = "pass" if len(contributors) >= int(requirement["threshold"]) and len(green) == len(contributors) else ("fail" if red else "pending")
            elif len(green) >= int(requirement["threshold"]):
                status = "pass"
            elif red or stale_candidates:
                status = "fail"
            else:
                status = "pending"
        conflict = bool(
            any(item["result"] in GREEN_RESULTS for item in contributors)
            and any(item["result"] in RED_RESULTS for item in contributors)
        )
        dissent = [entry for item in contributors for entry in item["dissent"]]
        if conflict:
            dissent.append({
                "source": str(requirement["id"]),
                "role": "gate",
                "result": "conflict",
                "reason": "active green and red verdicts disagree",
            })
        all_dissent.extend(dissent)

        audit_policy = requirement["meta_audit"]
        selected = _audit_selection(
            gate_hash, contributors, str(audit_policy["mode"]),
            int(audit_policy["sample_size"]),
        )
        audits: list[dict[str, object]] = []
        audit_shortfall = (
            audit_policy["mode"] == "random"
            and len(selected) < int(audit_policy["sample_size"])
        )
        if audit_shortfall:
            status = "pending" if status != "refused" else status
            audits.append({
                "sources": [item["verdict_hash"] for item in selected],
                "source": selected[0]["verdict_hash"] if len(selected) == 1 else None,
                "status": "sample-shortfall",
                "meta_verdict": None,
            })
        elif selected:
            meta_rubric = compiled_rubrics.get(str(audit_policy["rubric"]))
            if meta_rubric is None:
                audits.append({
                    "sources": [item["verdict_hash"] for item in selected],
                    "source": selected[0]["verdict_hash"] if len(selected) == 1 else None,
                    "status": "missing-rubric",
                    "meta_verdict": None,
                })
                status = "refused"
            else:
                selected_hashes = sorted(
                    str(item["verdict_hash"]) for item in selected
                )
                expected_set = _sha({"verdicts": selected_hashes})
                matches = [
                    item for item in active_verdicts
                    if item["verdict_type"] == "meta-verdict"
                    and item["rubric"]["slug"] == audit_policy["rubric"]
                    and item["issuer"]["role"] == audit_policy["role"]
                    and sorted(item["source_verdict_hashes"]) == selected_hashes
                ]
                fresh = [
                    item for item in matches
                    if not verdict_freshness_issues(
                        item, current, meta_rubric, now,
                        verdict_set_hash=expected_set,
                    )
                ]
                if len(fresh) != 1:
                    audit_status = "pending" if not fresh else "refused"
                    status = "pending" if status == "pass" and not fresh else (
                        "refused" if len(fresh) > 1 else status
                    )
                    audits.append({
                        "sources": selected_hashes,
                        "source": selected_hashes[0] if len(selected_hashes) == 1 else None,
                        "status": audit_status,
                        "meta_verdict": None,
                    })
                else:
                    meta = fresh[0]
                    if meta["result"] in {"uphold", "pass"}:
                        audit_status = "pass"
                    elif meta["result"] in {"overturn", "fail", "needs-repair"}:
                        audit_status = "fail"
                        status = "fail"
                    else:
                        audit_status = "pending"
                        if status == "pass":
                            status = "pending"
                    audits.append({
                        "sources": selected_hashes,
                        "source": selected_hashes[0] if len(selected_hashes) == 1 else None,
                        "status": audit_status,
                        "meta_verdict": meta["verdict_hash"],
                        "original_verdict_preserved": True,
                    })
        dissent_escalated = bool(
            dissent and policy["dissent_policy"] == "escalate"
        )
        if dissent and policy["dissent_policy"] == "block":
            status = "fail" if status != "refused" else status
        elif dissent_escalated:
            status = "pending" if status != "refused" else status
        if status != "pass":
            code = {
                "fail": "verdict-insufficient",
                "pending": "verdict-insufficient",
                "refused": "verdict-refused",
            }.get(status, "verdict-insufficient")
            issues.append({"code": code, "message": f"requirement {requirement['id']} is {status}"})
        requirement_projection.append({
            "id": requirement["id"],
            "kind": requirement["kind"],
            "rubric": {
                "slug": rubric["rubric"]["slug"],
                "semantic_hash": rubric["semantic_hash"],
            },
            "status": status,
            "contributors": [
                {
                    "verdict_hash": item["verdict_hash"],
                    "verdict_type": item["verdict_type"],
                    "role": item["issuer"]["role"],
                    "principal_fingerprint": item["issuer"]["principal_fingerprint"],
                    "result": item["result"],
                }
                for item in contributors
            ],
            "non_contributors": non_contributors,
            "method": requirement["method"],
            "threshold": requirement["threshold"],
            "veto_roles": requirement["veto_roles"],
            "meta_audit": audits,
            "dissent": dissent,
            "dissent_escalated": dissent_escalated,
        })

    fact_refused = any(item["status"] == "refused" for item in mechanical_projection)
    requirement_refused = any(item["status"] == "refused" for item in requirement_projection)
    fact_failed = any(item["status"] in {"fail", "stale"} for item in mechanical_projection)
    facts_missing = any(item["status"] == "missing" for item in mechanical_projection)
    passed_requirements = sum(item["status"] == "pass" for item in requirement_projection)
    failed_requirements = any(item["status"] == "fail" for item in requirement_projection)
    pending_requirements = any(item["status"] == "pending" for item in requirement_projection)
    if fact_refused or requirement_refused:
        result = "refused"
    elif fact_failed or failed_requirements:
        result = "fail"
    elif facts_missing or pending_requirements:
        result = "pending"
    elif policy["operator"] == "all" and passed_requirements == len(requirement_projection):
        result = "pass"
    elif policy["operator"] == "any" and passed_requirements >= 1:
        result = "pass"
    elif policy["operator"] == "at_least" and passed_requirements >= int(policy["threshold"]):
        result = "pass"
    else:
        result = "pending"
    route = policy["routes"][result]
    if failure_projection is not None and failure_projection["introduced_count"]:
        result = "fail"
        route = "block"
        issues.append({
            "code": "introduced-test-failure",
            "message": "introduced test failures block without a revision or exhaustion route",
        })
    if any(
        bool(item.get("dissent_escalated"))
        for item in requirement_projection
    ) and result != "refused" and not (
        failure_projection is not None
        and failure_projection["introduced_count"]
    ):
        route = "escalate"
    if result == "fail" and route == "repair" and repair_round >= int(policy["repair"]["max_rounds"]):
        route = policy["repair"]["on_exhausted"]
        issues.append({"code": "budget-exhausted", "message": "bounded repair rounds are exhausted"})
    contributing_hashes = {
        str(item["verdict_hash"])
        for requirement in requirement_projection
        for item in requirement["contributors"]
        if "verdict_hash" in item
    }
    contributing_hashes.update(
        str(audit["meta_verdict"])
        for requirement in requirement_projection
        for audit in requirement["meta_audit"]
        if audit.get("meta_verdict") is not None
    )
    source_hashes: set[str] = set()
    pending_lineage = list(contributing_hashes)
    while pending_lineage:
        verdict_hash = pending_lineage.pop()
        verdict = verdicts_by_hash[verdict_hash]
        for source_hash in verdict["source_verdict_hashes"]:
            if source_hash not in source_hashes:
                source_hashes.add(str(source_hash))
                pending_lineage.append(str(source_hash))
    preview_verdicts = contributing_hashes | source_hashes
    citations = [
        citation
        for verdict_hash in sorted(preview_verdicts)
        for criterion in verdicts_by_hash[verdict_hash]["criteria"]
        for citation in criterion["citations"]
    ]
    decision_citations = [
        citation
        for decision_hash in sorted(contributing_decision_hashes)
        for citation in decisions_by_hash[decision_hash]["citations"]
    ]
    proof = {
        "kind": QUALITY_PROOF_KIND,
        "schema_version": VERDICT_SCHEMA_VERSION,
        "gate": {
            "id": policy["id"],
            "semantic_hash": gate_hash,
            "operator": policy["operator"],
            "threshold": policy["threshold"],
            "dissent_policy": policy["dissent_policy"],
            "repair_round": repair_round,
            "max_repair_rounds": policy["repair"]["max_rounds"],
        },
        "subject": current,
        "result": result,
        "route": route,
        "mechanical": mechanical_projection,
        "requirements": requirement_projection,
        "dissent": all_dissent,
        "history": history,
        "decision_history": [
            {
                "decision_hash": item["decision_hash"],
                "council_id": item["council_id"],
                "result": item["result"],
                "authority": item["authority"],
                "obligation_ids": [
                    obligation["id"] for obligation in item["obligations"]
                ],
            }
            for item in sorted(
                validated_decisions,
                key=lambda value: (
                    value["issued_at"], value["decision_hash"],
                ),
            )
        ],
        "issues": issues,
        "remediation": sorted({
            "supply fresh exact receipts" if item["code"] == "verdict-stale"
            else "obtain the missing governed verdict or fact" if item["code"] == "verdict-insufficient"
            else "escalate after the bounded repair budget" if item["code"] == "budget-exhausted"
            else "repair the refused typed input"
            for item in issues
        }),
        "evidence_preview": {
            "mechanical_fact_hashes": sorted(
                str(item["fact_hash"])
                for item in mechanical_projection
                if item.get("fact_hash") is not None
            ),
            "verdict_hashes": sorted(contributing_hashes),
            "citations": citations,
            "source_verdict_hashes": sorted(source_hashes),
            "decision_hashes": sorted(contributing_decision_hashes),
            "decision_citations": decision_citations,
            "obligation_ids": sorted(contributing_obligation_ids),
        },
        "authority": {
            "may_advance": False,
            "may_repair": False,
            "may_materialize_evidence": False,
            "explanation": "the proof selects a declared route but grants and performs no act",
        },
        **({"test_failures": failure_projection} if failure_projection is not None else {}),
        **starts,
    }
    proof["proof_hash"] = _sha(proof)
    return proof
