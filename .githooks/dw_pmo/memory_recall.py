"""Pure, deterministic, explainable recall over caller-supplied facts.

This module projects already-read repository knowledge.  It deliberately has no
adapter for Git, files, clocks, environment variables, randomness, or networks.
Callers freeze those inputs first and pass them to :func:`build_memory_recall`.
"""

from __future__ import annotations

import hashlib
import json
import re
from typing import Iterable, Mapping, Optional


MEMORY_RECALL_KIND = "delivery-workbench-memory-recall"
MEMORY_RECALL_SCHEMA_VERSION = 1
DEFAULT_MEMORY_RECALL_BYTES = 32_768
MINIMUM_MEMORY_RECALL_BYTES = 1_024
MAXIMUM_MEMORY_RECALL_BYTES = 65_536
MAX_RECALL_ITEMS = 64
MAX_RECALL_EXCLUSIONS = 128
MAX_SOURCE_HEADS = 32
MAX_ITEMS_BYTES = 49_152
MAX_EXCLUSIONS_BYTES = 12_288

SOURCE_KINDS = (
    "grounding",
    "repository-snippet",
    "test-reference",
    "evidence-digest",
    "lesson",
    "terminal-outcome",
    "decision",
)
AUDIENCES = ("coordinator", "implementer", "verifier", "judge", "shared")
EXCLUSION_REASONS = (
    "byte-budget",
    "stale-source",
    "superseded",
    "low-score",
    "audience-filter",
)

_AUTHORITY_MARKERS = {
    "starts_work": False,
    "authorizes": False,
    "satisfies_gate": False,
    "substitutes_for_evidence": False,
}
_TOKEN_RE = re.compile(r"[A-Za-z0-9_]+")
_STORY_RE = re.compile(r"^([A-Za-z][A-Za-z0-9]*)-([0-9]+)-[0-9]+$")
_SIZE_CONVERGENCE_ATTEMPTS = 8

_SIGNAL_WEIGHTS = {
    "failure-signature": 16_000,
    "story": 14_000,
    "phase": 12_000,
    "symbol": 10_000,
    "test": 9_000,
    "file": 8_000,
    "grounded-location": 7_000,
    "orchestration-tag": 6_000,
}
_DELIVERY_BONUS = {
    "confirmed": 600,
    "complete": 600,
    "succeeded": 600,
    "delivered": 600,
    "certified-not-integrated": 450,
    "candidate": 300,
    "unknown": 0,
}
_CONFIDENCE_SCORE = {
    "certain": 100,
    "high": 90,
    "medium": 60,
    "low": 30,
    "unknown": 0,
}
_GROUP_KINDS = (
    ("grounding", "grounding"),
    ("repository_snippets", "repository-snippet"),
    ("test_references", "test-reference"),
    ("evidence_digests", "evidence-digest"),
    ("lessons", "lesson"),
    ("terminal_outcomes", "terminal-outcome"),
    ("decisions", "decision"),
)


class MemoryRecallRefusal(ValueError):
    """The supplied snapshot cannot form a bounded recall document."""


def _canonical_json(value: object) -> str:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
        allow_nan=False,
    )


def _sha(value: object) -> str:
    return "sha256:" + hashlib.sha256(
        _canonical_json(value).encode("utf-8")
    ).hexdigest()


def _json_value(value: object, field: str) -> object:
    if value is None or isinstance(value, (bool, int, str)):
        return value
    if isinstance(value, Mapping):
        normalized = {}
        for key in sorted(value, key=lambda item: str(item)):
            if not isinstance(key, str):
                raise MemoryRecallRefusal("memory recall %s keys must be strings" % field)
            normalized[key] = _json_value(value[key], field)
        return normalized
    if isinstance(value, (list, tuple)):
        return [_json_value(item, field) for item in value]
    raise MemoryRecallRefusal(
        "memory recall %s must contain deterministic JSON values" % field
    )


def _text(value: object, field: str, maximum: int, *, empty: bool = False) -> str:
    if not isinstance(value, str):
        raise MemoryRecallRefusal("memory recall %s must be a string" % field)
    result = value.strip()
    if not empty and not result:
        raise MemoryRecallRefusal("memory recall %s must not be empty" % field)
    if len(result) > maximum:
        raise MemoryRecallRefusal(
            "memory recall %s must be at most %d characters" % (field, maximum)
        )
    if "\x00" in result:
        raise MemoryRecallRefusal("memory recall %s contains a NUL" % field)
    return result


def _values(value: object, singular_keys: tuple = ()) -> set:
    """Normalize scalar/list/dict references into comparable case-folded text."""
    if value is None:
        return set()
    if isinstance(value, str):
        raw = [value]
    elif isinstance(value, Mapping):
        raw = []
        for key in singular_keys:
            if key in value:
                raw.append(value[key])
                break
    else:
        try:
            raw = list(value)  # type: ignore[arg-type]
        except TypeError:
            raw = [value]
    result = set()
    for item in raw:
        if isinstance(item, Mapping):
            selected = None
            for key in singular_keys:
                if key in item:
                    selected = item[key]
                    break
            if selected is None:
                continue
            item = selected
        text = str(item).strip()
        if text:
            result.add(text.casefold())
    return result


def _candidate_values(candidate: Mapping[str, object], plural: str,
                      singular: str, aliases: tuple = ()) -> set:
    values = set()
    for key in (plural, singular) + aliases:
        if key in candidate:
            values.update(_values(candidate[key], (singular, "value", "name")))
    return values


def _locations(candidate: Mapping[str, object]) -> tuple:
    files = _candidate_values(candidate, "files", "file", ("path",))
    symbols = _candidate_values(candidate, "symbols", "symbol")
    raw_locations = candidate.get("locations", candidate.get("location", ()))
    if isinstance(raw_locations, Mapping):
        raw_locations = [raw_locations]
    if not isinstance(raw_locations, str):
        try:
            locations = list(raw_locations)  # type: ignore[arg-type]
        except TypeError:
            locations = []
        for location in locations:
            if not isinstance(location, Mapping):
                continue
            files.update(_values(location, ("file", "path")))
            symbols.update(_values(location, ("symbol", "qualified_name", "name")))
    return files, symbols


def _story_phases(stories: Iterable[str]) -> set:
    phases = set()
    for story in stories:
        match = _STORY_RE.match(story)
        if match:
            phases.add(match.group(2).casefold())
            phases.add((match.group(1) + "-" + match.group(2)).casefold())
    return phases


def _tokens(value: object) -> set:
    return {
        token.casefold()
        for token in _TOKEN_RE.findall(str(value))
        if len(token) > 1
    }


def _confidence(value: object) -> tuple:
    if isinstance(value, bool):
        raise MemoryRecallRefusal("memory recall confidence must not be boolean")
    if isinstance(value, int):
        if value < 0 or value > 100:
            raise MemoryRecallRefusal("memory recall confidence integer must be 0..100")
        return value, value
    text = _text(value if value is not None else "unknown", "confidence", 32)
    folded = text.casefold()
    if folded not in _CONFIDENCE_SCORE:
        raise MemoryRecallRefusal("memory recall confidence is not recognized: " + text)
    return text, _CONFIDENCE_SCORE[folded]


def _recency(candidate: Mapping[str, object]) -> int:
    value = candidate.get("recency", candidate.get("recency_rank", candidate.get("seq", 0)))
    if isinstance(value, bool) or not isinstance(value, int):
        raise MemoryRecallRefusal("memory recall recency must be an integer")
    return max(0, min(value, 99))


def _source_reference(candidate: Mapping[str, object]) -> str:
    for key in (
        "source_ref", "source_reference", "record_hash", "receipt_id",
        "decision_id", "reference", "ref",
    ):
        if candidate.get(key):
            return _text(candidate[key], "source_ref", 500)
    raise MemoryRecallRefusal("memory recall candidate requires a stable source_ref")


def _summary(candidate: Mapping[str, object]) -> str:
    for key in ("summary", "claim", "factual_summary"):
        if candidate.get(key):
            return _text(candidate[key], "summary", 1_000)
    raise MemoryRecallRefusal("memory recall candidate requires a factual summary")


def _source_kind(candidate: Mapping[str, object], default: Optional[str]) -> str:
    raw = candidate.get("source_kind", default if default is not None else candidate.get("kind"))
    kind = _text(raw, "source_kind", 32) if raw is not None else ""
    if kind not in SOURCE_KINDS:
        raise MemoryRecallRefusal("memory recall source kind is not supported: " + kind)
    return kind


def _head_value(value: object) -> str:
    if isinstance(value, Mapping):
        for key in ("revision", "head", "hash", "index_tree"):
            if value.get(key) is not None:
                return str(value[key])
    return str(value)


def _is_stale(candidate: Mapping[str, object], source_heads: object) -> bool:
    if candidate.get("stale") is True:
        return True
    head_name = candidate.get("source_head")
    if not head_name or not isinstance(source_heads, Mapping):
        return False
    if head_name not in source_heads:
        return True
    candidate_revision = candidate.get("source_revision")
    if candidate_revision is None:
        return False
    return str(candidate_revision) != _head_value(source_heads[head_name])


def _intersection(left: set, right: set) -> Optional[str]:
    overlap = sorted(left & right)
    return overlap[0] if overlap else None


def _rank(candidate: Mapping[str, object], query: dict) -> tuple:
    reasons = []
    relevance = 0

    stories = _candidate_values(candidate, "story_ids", "story_id", ("stories", "story"))
    phases = _candidate_values(candidate, "phase_ids", "phase_id", ("phases", "phase"))
    phases.update(_story_phases(stories))
    files, symbols = _locations(candidate)
    tests = _candidate_values(candidate, "test_names", "test_name", ("tests", "test"))
    failures = _candidate_values(
        candidate, "failure_signatures", "failure_signature", ("failures",)
    )
    tags = _candidate_values(
        candidate, "orchestration_tags", "orchestration_tag", ("tags",)
    )

    signals = (
        ("failure-signature", failures, query["failures"]),
        ("story", stories, query["stories"]),
        ("phase", phases, query["phases"]),
        ("symbol", symbols, query["symbols"]),
        ("test", tests, query["tests"]),
        ("file", files, query["files"]),
        ("orchestration-tag", tags, query["tags"]),
    )
    for name, candidate_values, query_values in signals:
        matched = _intersection(candidate_values, query_values)
        if matched is not None:
            relevance += _SIGNAL_WEIGHTS[name]
            reasons.append("exact-%s:%s" % (name, matched))

    if (files & query["files"]) or (symbols & query["symbols"]):
        relevance += _SIGNAL_WEIGHTS["grounded-location"]
        reasons.append("grounded-location-overlap")

    searchable = [candidate.get("summary"), candidate.get("claim")]
    searchable.extend(sorted(stories | phases | files | symbols | tests | failures | tags))
    overlap = sorted(query["criteria_terms"] & _tokens(" ".join(
        str(value) for value in searchable if value is not None
    )))
    if overlap:
        bounded_overlap = overlap[:20]
        relevance += len(bounded_overlap) * 250
        reasons.append("criteria-term-overlap:" + ",".join(bounded_overlap[:8]))

    state = str(candidate.get("delivery_state", "candidate")).strip().casefold()
    delivery_bonus = _DELIVERY_BONUS.get(state, 0)
    confidence, confidence_score = _confidence(candidate.get("confidence", "unknown"))
    recency = _recency(candidate)
    score = relevance + delivery_bonus + confidence_score + recency
    reasons.extend((
        "delivery-state:%s" % state,
        "confidence:%s" % str(confidence).casefold(),
        "recency:%d" % recency,
    ))
    return score, relevance, reasons, confidence, state, recency


def _normalize_candidate(candidate: object, default_kind: Optional[str],
                         source_revision: str, source_heads: object,
                         query: dict, audience: str) -> dict:
    if not isinstance(candidate, Mapping):
        raise MemoryRecallRefusal("memory recall candidates must be objects")
    raw = dict(candidate)
    kind = _source_kind(raw, default_kind)
    source_ref = _source_reference(raw)
    revision = _text(
        raw.get("source_revision", source_revision), "candidate source_revision", 500
    )
    summary = _summary(raw)
    score, relevance, reasons, confidence, state, recency = _rank(raw, query)
    audiences = _values(raw.get("audiences", raw.get("audience", AUDIENCES)))
    unknown_audiences = audiences - set(AUDIENCES)
    if unknown_audiences:
        raise MemoryRecallRefusal(
            "memory recall candidate has unknown audiences: "
            + ", ".join(sorted(unknown_audiences))
        )
    item_identity = {
        "source_kind": kind,
        "source_ref": source_ref,
        "source_revision": revision,
    }
    return {
        "item": {
            "item_id": _sha(item_identity),
            "source_ref": source_ref,
            "source_kind": kind,
            "confidence": confidence,
            "delivery_state": state,
            "source_revision": revision,
            "summary": summary,
            "score": score,
            "match_reasons": reasons,
        },
        "relevance": relevance,
        "recency": recency,
        "audience_match": audience.casefold() in audiences,
        "stale": _is_stale(raw, source_heads),
        "superseded": state == "superseded" or bool(raw.get("superseded_by")),
        "tie_hash": _sha({"identity": item_identity, "candidate": _json_value(raw, "candidate")}),
    }


def _exclusion(candidate: dict, reason: str) -> dict:
    item = candidate["item"]
    return {
        "source_ref": item["source_ref"],
        "source_kind": item["source_kind"],
        "score": item["score"],
        "reason": reason,
    }


def _rank_key(candidate: dict) -> tuple:
    item = candidate["item"]
    return (-int(item["score"]), str(candidate["tie_hash"]))


def _render(subject: str, audience: str, source_revision: str,
            source_heads: object, byte_budget: int, included: list,
            exclusions: list, used_bytes: int = 0) -> dict:
    unsigned = {
        "kind": MEMORY_RECALL_KIND,
        "schema_version": MEMORY_RECALL_SCHEMA_VERSION,
        "subject": subject,
        "audience": audience,
        "source_revision": source_revision,
        "source_heads": source_heads,
        "items": [candidate["item"] for candidate in included],
        "exclusions": exclusions,
        "byte_budget": byte_budget,
        "used_bytes": used_bytes,
        **_AUTHORITY_MARKERS,
    }
    return {
        "kind": unsigned["kind"],
        "schema_version": unsigned["schema_version"],
        "recall_id": _sha(unsigned),
        **{key: value for key, value in unsigned.items()
           if key not in {"kind", "schema_version"}},
    }


def _with_exact_size(subject: str, audience: str, source_revision: str,
                     source_heads: object, byte_budget: int, included: list,
                     exclusions: list) -> tuple:
    used = 0
    for _attempt in range(_SIZE_CONVERGENCE_ATTEMPTS):
        document = _render(
            subject, audience, source_revision, source_heads, byte_budget,
            included, exclusions, used,
        )
        updated = len(_canonical_json(document).encode("utf-8"))
        if updated == used:
            return document, updated
        used = updated
    raise MemoryRecallRefusal("memory recall serialized size did not converge")


def _field_bytes(value: object) -> int:
    return len(_canonical_json(value).encode("utf-8"))


def _query(story_criteria: str, grounded_files: object,
           grounded_symbols: object, test_names: object,
           failure_signatures: object, story_ids: object,
           phase_ids: object, orchestration_tags: object) -> dict:
    stories = _values(story_ids, ("story_id", "story", "value"))
    phases = _values(phase_ids, ("phase_id", "phase", "value"))
    phases.update(_story_phases(stories))
    return {
        "criteria_terms": _tokens(story_criteria),
        "files": _values(grounded_files, ("file", "path", "value")),
        "symbols": _values(
            grounded_symbols, ("symbol", "qualified_name", "name", "value")
        ),
        "tests": _values(test_names, ("test_name", "test", "name", "value")),
        "failures": _values(
            failure_signatures, ("failure_signature", "signature", "value")
        ),
        "stories": stories,
        "phases": phases,
        "tags": _values(orchestration_tags, ("tag", "name", "value")),
    }


def build_memory_recall(
    story_criteria: str,
    candidate_items: Iterable[dict] = (),
    *,
    subject: str,
    source_revision: str,
    source_heads: object,
    audience: str = "shared",
    grounded_files: Iterable[object] = (),
    grounded_symbols: Iterable[object] = (),
    test_names: Iterable[object] = (),
    failure_signatures: Iterable[object] = (),
    story_ids: Iterable[object] = (),
    phase_ids: Iterable[object] = (),
    orchestration_tags: Iterable[object] = (),
    grounding: Iterable[dict] = (),
    repository_snippets: Iterable[dict] = (),
    test_references: Iterable[dict] = (),
    evidence_digests: Iterable[dict] = (),
    lessons: Iterable[dict] = (),
    terminal_outcomes: Iterable[dict] = (),
    decisions: Iterable[dict] = (),
    byte_budget: int = DEFAULT_MEMORY_RECALL_BYTES,
    minimum_score: int = 1,
) -> dict:
    """Build a frozen recall document solely from caller-supplied values.

    Ranking uses exact structural matches first, then bounded lexical overlap,
    delivery state, confidence, and caller-supplied recency.  A stable hash is
    the final tie-breaker.  Candidates are never truncated: an item is included
    whole or named in ``exclusions``.
    """
    criteria = _text(story_criteria, "story_criteria", 100_000, empty=True)
    subject = _text(subject, "subject", 71)
    source_revision = _text(source_revision, "source_revision", 71)
    audience = _text(audience, "audience", 32).casefold()
    if audience not in AUDIENCES:
        raise MemoryRecallRefusal("memory recall audience is not supported: " + audience)
    if isinstance(byte_budget, bool) or not isinstance(byte_budget, int):
        raise MemoryRecallRefusal("memory recall byte budget must be an integer")
    if not MINIMUM_MEMORY_RECALL_BYTES <= byte_budget <= MAXIMUM_MEMORY_RECALL_BYTES:
        raise MemoryRecallRefusal(
            "memory recall byte budget must be between %d and %d"
            % (MINIMUM_MEMORY_RECALL_BYTES, MAXIMUM_MEMORY_RECALL_BYTES)
        )
    if isinstance(minimum_score, bool) or not isinstance(minimum_score, int):
        raise MemoryRecallRefusal("memory recall minimum score must be an integer")

    heads = _json_value(source_heads, "source_heads")
    if not isinstance(heads, (dict, list)):
        raise MemoryRecallRefusal("memory recall source_heads must be an object or list")
    if len(heads) > MAX_SOURCE_HEADS:
        raise MemoryRecallRefusal("memory recall has too many source heads")
    if _field_bytes(heads) > 8_192:
        raise MemoryRecallRefusal("memory recall source heads exceed their byte cap")

    query = _query(
        criteria, grounded_files, grounded_symbols, test_names,
        failure_signatures, story_ids, phase_ids, orchestration_tags,
    )
    grouped = [(candidate, None) for candidate in candidate_items]
    local_groups = {
        "grounding": grounding,
        "repository_snippets": repository_snippets,
        "test_references": test_references,
        "evidence_digests": evidence_digests,
        "lessons": lessons,
        "terminal_outcomes": terminal_outcomes,
        "decisions": decisions,
    }
    for group_name, kind in _GROUP_KINDS:
        grouped.extend((candidate, kind) for candidate in local_groups[group_name])
    if len(grouped) > MAX_RECALL_ITEMS + MAX_RECALL_EXCLUSIONS:
        raise MemoryRecallRefusal("memory recall has too many candidates to explain")

    normalized = [
        _normalize_candidate(
            candidate, default_kind, source_revision, heads, query, audience
        )
        for candidate, default_kind in grouped
    ]
    normalized.sort(key=lambda candidate: (
        candidate["item"]["source_kind"], candidate["item"]["source_ref"],
        candidate["tie_hash"],
    ))
    seen = {}
    unique = []
    for candidate in normalized:
        identity = (
            candidate["item"]["source_kind"], candidate["item"]["source_ref"]
        )
        prior = seen.get(identity)
        if prior is not None:
            if prior != candidate:
                raise MemoryRecallRefusal(
                    "memory recall has conflicting candidates for %s" % identity[1]
                )
            continue
        seen[identity] = candidate
        unique.append(candidate)

    included = []
    exclusions = []
    for candidate in unique:
        if candidate["stale"]:
            exclusions.append(_exclusion(candidate, "stale-source"))
        elif candidate["superseded"]:
            exclusions.append(_exclusion(candidate, "superseded"))
        elif not candidate["audience_match"]:
            exclusions.append(_exclusion(candidate, "audience-filter"))
        elif candidate["relevance"] < minimum_score:
            exclusions.append(_exclusion(candidate, "low-score"))
        else:
            included.append(candidate)

    included.sort(key=_rank_key)
    exclusions.sort(key=lambda item: (
        EXCLUSION_REASONS.index(item["reason"]), item["source_kind"],
        item["source_ref"],
    ))
    while len(included) > MAX_RECALL_ITEMS:
        dropped = included.pop()
        exclusions.append(_exclusion(dropped, "byte-budget"))

    while True:
        exclusions.sort(key=lambda item: (
            EXCLUSION_REASONS.index(item["reason"]), item["source_kind"],
            item["source_ref"],
        ))
        if len(exclusions) > MAX_RECALL_EXCLUSIONS:
            raise MemoryRecallRefusal("memory recall has too many exclusions")
        if _field_bytes(exclusions) > MAX_EXCLUSIONS_BYTES:
            raise MemoryRecallRefusal("memory recall exclusions exceed their byte cap")
        items = [candidate["item"] for candidate in included]
        document, used = _with_exact_size(
            subject, audience, source_revision, heads, byte_budget,
            included, exclusions,
        )
        within_bounds = (
            used <= byte_budget
            and used <= MAXIMUM_MEMORY_RECALL_BYTES
            and _field_bytes(items) <= MAX_ITEMS_BYTES
        )
        if within_bounds:
            return document
        if not included:
            raise MemoryRecallRefusal(
                "memory recall budget cannot hold the document and named exclusions"
            )
        dropped = included.pop()
        exclusions.append(_exclusion(dropped, "byte-budget"))
