"""Deterministic, authority-free repository knowledge packets for agents."""

from __future__ import annotations

import hashlib
import re
from pathlib import Path
from typing import Callable, Iterable, Mapping, Optional

from . import repofacts
from .grounding import (
    GROUNDING_KIND,
    GROUNDING_SCHEMA_VERSION,
    ground_story_path,
    parse_localization_hints,
)
from .knowledge import (
    EarnedRecordStore,
    _canonical_json,
    decode_lesson_locations,
)
from .model import DwError
from .repository_map import read_symbol_map
from .symbol_map import SYMBOL_MAP_KIND, SYMBOL_MAP_SCHEMA_VERSION


KNOWLEDGE_PACKET_KIND = "delivery-workbench-knowledge-packet"
KNOWLEDGE_PACKET_SCHEMA_VERSION = 1
DEFAULT_KNOWLEDGE_PACKET_BYTES = 32_768
_MINIMUM_PACKET_BYTES = 1_024
_MAX_RELEVANT_LESSONS = 16
_SIZE_CONVERGENCE_ATTEMPTS = 8
_TOKEN_RE = re.compile(r"[A-Za-z0-9_]+")


class KnowledgePacketRefusal(DwError):
    """Typed refusal when fresh repository knowledge cannot be assembled."""


class StaleKnowledgePacket(KnowledgePacketRefusal):
    """The grounding and symbol map do not describe the same index tree."""


def _tokens(value: object) -> set[str]:
    return {
        item.lower()
        for item in _TOKEN_RE.findall(str(value))
        if len(item) > 1
    }


def _score(query: set[str], *values: object) -> int:
    terms = set()
    for value in values:
        terms.update(_tokens(value))
    overlap = query & terms
    # Integers make the score representation stable across Python versions.
    return len(overlap) * 1000 + sum(min(len(item), 40) for item in overlap)


def _preferred_lessons(records: Iterable[dict], query: set[str]) -> list[tuple]:
    """Return active superseding lessons with their auditable ancestry."""
    by_hash = {
        str(record.get("record_hash", "")): record
        for record in records
        if isinstance(record, dict) and record.get("record_kind") == "lesson"
        and isinstance(record.get("detail"), dict)
    }
    superseded = {
        str(record["detail"].get("supersedes", ""))
        for record in by_hash.values()
        if record["detail"].get("supersedes")
    }
    preferred = []
    for record_hash, record in sorted(by_hash.items()):
        if record_hash in superseded:
            continue
        chain = []
        scoring = []
        cursor = record
        while cursor is not None:
            detail = cursor["detail"]
            scoring.extend((detail.get("claim"), detail.get("locations")))
            prior_hash = str(detail.get("supersedes", ""))
            if not prior_hash:
                break
            chain.append(prior_hash)
            cursor = by_hash.get(prior_hash)
        score = _score(query, *scoring)
        if score > 0:
            preferred.append((score, record_hash, record, chain))
    return sorted(preferred, key=lambda item: (-item[0], item[1]))


def _source_lines(data: bytes, line_start: int, line_end: int) -> str:
    lines = data.decode("utf-8", "replace").splitlines(keepends=True)
    return "".join(lines[line_start - 1:line_end])


def _symbol_index(model: dict) -> dict[str, list[dict]]:
    by_file: dict[str, list[dict]] = {}
    for symbol in model.get("symbols", []):
        if not isinstance(symbol, dict):
            continue
        by_file.setdefault(str(symbol.get("file", "")), []).append(symbol)
    for symbols in by_file.values():
        symbols.sort(key=lambda item: (
            int(item.get("line_start", 0)),
            int(item.get("line_end", 0)),
            str(item.get("qualified_name", "")),
        ))
    return by_file


def _matching_symbols(location: dict, hint: str, by_file: dict[str, list[dict]],
                      query: set[str]) -> list[dict]:
    path = str(location.get("file", ""))
    start = int(location.get("line_start", 0))
    end = int(location.get("line_end", 0))
    symbols = []
    modules = []
    for item in by_file.get(path, []):
        if (int(item.get("line_start", 0)) < start
                or int(item.get("line_end", 0)) > end):
            continue
        (modules if item.get("kind") == "module" else symbols).append(item)
    exact = [
        item for item in symbols
        if hint in {str(item.get("name", "")), str(item.get("qualified_name", ""))}
    ]
    if exact:
        return exact
    if symbols:
        return sorted(
            symbols,
            key=lambda item: (
                -_score(query, hint, item.get("name"), item.get("qualified_name")),
                str(item.get("qualified_name", "")),
            ),
        )[:3]
    return modules[:1]


def _candidate(name: str, kind: str, score: int, payload: dict) -> dict:
    return {"name": name, "kind": kind, "score": score, "payload": payload}


def _render(story: str, index_tree: str, grounding_status: str,
            criteria_hash: str, byte_budget: int, candidates: list[dict],
            exclusions: list[dict], unverified: list[dict], used_bytes: int) -> dict:
    packet = {
        "kind": KNOWLEDGE_PACKET_KIND,
        "schema_version": KNOWLEDGE_PACKET_SCHEMA_VERSION,
        "story": story,
        "criteria_sha256": criteria_hash,
        "index_tree": index_tree,
        "grounding_status": grounding_status,
        "byte_budget": byte_budget,
        "used_bytes": used_bytes,
        "verified_locations": [],
        "snippets": [],
        "test_references": [],
        "lessons": [],
        "unverified_hints": unverified,
        "exclusions": exclusions,
        "starts_work": False,
        "authorizes": False,
        "satisfies_gate": False,
        "substitutes_for_evidence": False,
    }
    section = {
        "source": ("verified_locations", "snippets"),
        "test": ("test_references",),
        "lesson": ("lessons",),
    }
    for item in sorted(candidates, key=lambda value: value["name"]):
        targets = section[item["kind"]]
        if item["kind"] == "source":
            packet[targets[0]].append(item["payload"]["location"])
            packet[targets[1]].append(item["payload"]["snippet"])
        else:
            packet[targets[0]].append(item["payload"])
    return packet


def _with_exact_size(packet: dict) -> tuple[dict, int]:
    # Only the decimal width of used_bytes can change the serialized size, so
    # this fixed point normally settles in two passes. Keep a bounded guard and
    # refuse if a future serializer breaks that property.
    size = len(_canonical_json(packet).encode("utf-8"))
    for _attempt in range(_SIZE_CONVERGENCE_ATTEMPTS):
        packet["used_bytes"] = size
        updated = len(_canonical_json(packet).encode("utf-8"))
        if updated == size:
            return packet, size
        size = updated
    packet["used_bytes"] = size
    actual = len(_canonical_json(packet).encode("utf-8"))
    if actual != size:
        raise KnowledgePacketRefusal(
            "knowledge packet serialized size did not converge"
        )
    return packet, actual


def build_knowledge_packet(
    story_criteria: str,
    grounding: Optional[dict],
    symbol_map_document: Optional[dict],
    source_blobs: Mapping[str, bytes],
    earned_records: Iterable[dict] = (),
    *,
    story: str = "",
    index_tree: Optional[str] = None,
    byte_budget: int = DEFAULT_KNOWLEDGE_PACKET_BYTES,
) -> dict:
    """Build one deterministic packet from already-read, immutable facts.

    The function performs no filesystem, Git, clock, network, or authority read.
    Callers supply indexed blob bytes and the verified earned-record snapshot.
    """
    if isinstance(byte_budget, bool) or not isinstance(byte_budget, int):
        raise KnowledgePacketRefusal("knowledge packet byte budget must be an integer")
    if byte_budget < _MINIMUM_PACKET_BYTES:
        raise KnowledgePacketRefusal(
            "knowledge packet byte budget is too small to name its exclusions"
        )
    if symbol_map_document is not None:
        map_tree = str(symbol_map_document.get("index_tree", ""))
        model = symbol_map_document.get("value")
        if not isinstance(model, dict) or (
            model.get("kind") != SYMBOL_MAP_KIND
            or model.get("schema_version") != SYMBOL_MAP_SCHEMA_VERSION
        ):
            raise KnowledgePacketRefusal("knowledge packet requires a compatible symbol map")
    else:
        map_tree = str(index_tree or "")
        model = {
            "kind": SYMBOL_MAP_KIND,
            "schema_version": SYMBOL_MAP_SCHEMA_VERSION,
            "symbols": [],
            "test_map": {},
        }
    if not map_tree:
        raise KnowledgePacketRefusal("knowledge packet requires an index tree")
    if index_tree is not None and str(index_tree) != map_tree:
        raise StaleKnowledgePacket("symbol map does not match the requested index tree")

    grounded_items: list[dict] = []
    unverified: list[dict] = []
    if grounding is None:
        grounding_status = "ungrounded"
    else:
        if (grounding.get("kind") != GROUNDING_KIND
                or grounding.get("schema_version") != GROUNDING_SCHEMA_VERSION):
            raise KnowledgePacketRefusal("knowledge packet requires compatible grounding")
        if grounding.get("status") != "grounded":
            raise KnowledgePacketRefusal(
                "knowledge grounding refused: " + str(grounding.get("reason") or "unknown reason")
            )
        if str(grounding.get("index_tree", "")) != map_tree:
            raise StaleKnowledgePacket(
                "knowledge grounding and symbol map index trees differ"
            )
        grounding_status = "grounded"
        for section in ("affected_files", "target_symbols"):
            for raw in grounding.get(section, []):
                if not isinstance(raw, dict):
                    continue
                if raw.get("classification") == "verified":
                    grounded_items.append(raw)
                elif raw.get("classification") == "unknown":
                    unverified.append({
                        "kind": raw.get("kind"),
                        "hint": raw.get("hint"),
                        "label": "unverified",
                        "suggestions": raw.get("suggestions", []),
                    })
    if grounding is None and not grounded_items and not unverified:
        grounding_status = "hint-free" if symbol_map_document is None else "ungrounded"

    query = _tokens(story_criteria)
    for item in grounded_items:
        query.update(_tokens(item.get("hint", "")))
    by_file = _symbol_index(model)
    candidates: dict[str, dict] = {}
    selected_symbols: dict[str, dict] = {}
    for grounded in grounded_items:
        hint = str(grounded.get("hint", ""))
        for location in grounded.get("locations", []):
            if not isinstance(location, dict):
                continue
            for symbol in _matching_symbols(location, hint, by_file, query):
                path = str(symbol.get("file", ""))
                qualified = str(symbol.get("qualified_name", ""))
                data = source_blobs.get(path)
                if data is None:
                    raise KnowledgePacketRefusal(
                        "indexed source blob is unavailable for " + path
                    )
                start = int(symbol["line_start"])
                end = int(symbol["line_end"])
                name = "source:%s:%s" % (path, qualified)
                score = _score(query, hint, path, qualified)
                candidates[name] = _candidate(name, "source", score, {
                    "location": {
                        "file": path,
                        "symbol": qualified,
                        "line_start": start,
                        "line_end": end,
                        "score": score,
                        "verified": True,
                    },
                    "snippet": {
                        "file": path,
                        "symbol": qualified,
                        "line_start": start,
                        "line_end": end,
                        "score": score,
                        "content": _source_lines(data, start, end),
                    },
                })
                selected_symbols[qualified] = symbol

    test_map = model.get("test_map", {})
    if not isinstance(test_map, dict):
        test_map = {}
    for qualified, symbol in sorted(selected_symbols.items()):
        for test_path in sorted(set(str(item) for item in test_map.get(qualified, []))):
            name = "test:%s:%s" % (test_path, qualified)
            score = _score(query, qualified, test_path)
            candidates[name] = _candidate(name, "test", score, {
                "file": test_path,
                "symbol": qualified,
                "source_file": symbol.get("file"),
                "score": score,
            })

    lesson_records = earned_records if grounding_status == "grounded" else ()
    for score, record_hash, raw, chain in _preferred_lessons(
        lesson_records, query
    )[:_MAX_RELEVANT_LESSONS]:
        detail = raw["detail"]
        recorded_at = str(raw.get("timestamp", ""))
        name = "lesson:" + record_hash
        candidates[name] = _candidate(name, "lesson", score, {
            "record_hash": record_hash,
            "claim": detail.get("claim"),
            "locations": decode_lesson_locations(detail.get("locations")),
            "confidence": detail.get("confidence"),
            "supersedes": detail.get("supersedes"),
            "supersession_chain": chain,
            "origin_kind": raw.get("origin_kind"),
            "origin": raw.get("origin"),
            "head_sha": raw.get("head_sha"),
            "recorded_at": recorded_at,
            "age_label": "recorded-at:" + recorded_at,
            "score": score,
        })

    included = list(candidates.values())
    exclusions: list[dict] = []
    criteria_hash = "sha256:" + hashlib.sha256(
        story_criteria.encode("utf-8")
    ).hexdigest()
    while True:
        packet = _render(
            story, map_tree, grounding_status, criteria_hash, byte_budget,
            included, exclusions, sorted(unverified, key=lambda item: (
                str(item.get("kind", "")), str(item.get("hint", ""))
            )), 0,
        )
        packet, used = _with_exact_size(packet)
        if used <= byte_budget:
            return packet
        if not included:
            raise KnowledgePacketRefusal(
                "knowledge packet budget cannot hold the packet and named exclusions"
            )
        dropped = min(included, key=lambda item: (
            int(item["score"]), str(item["name"])
        ))
        included.remove(dropped)
        exclusions.append({
            "name": dropped["name"],
            "kind": dropped["kind"],
            "score": dropped["score"],
            "reason": "byte-budget",
        })


def _verified_file_paths(grounding: dict) -> set[str]:
    return {
        str(location.get("file", ""))
        for section in ("affected_files", "target_symbols")
        for hint in grounding.get(section, [])
        if isinstance(hint, dict) and hint.get("classification") == "verified"
        for location in hint.get("locations", [])
        if isinstance(location, dict)
    }


def build_hint_free_knowledge_packet(
    root: Path,
    story: str,
    *,
    byte_budget: int = DEFAULT_KNOWLEDGE_PACKET_BYTES,
) -> dict:
    """Build an honest no-hints packet without requiring a symbol-map cache."""
    root = Path(root).resolve()
    tree = repofacts.index_tree(root, repofacts.Derivation(root))
    return build_knowledge_packet(
        story, None, None, {}, EarnedRecordStore(root).read("lesson"),
        story=story, index_tree=tree, byte_budget=byte_budget,
    )


def build_repository_knowledge_packet(
    root: Path,
    story_path: Path,
    *,
    grounding: Optional[dict] = None,
    byte_budget: int = DEFAULT_KNOWLEDGE_PACKET_BYTES,
) -> dict:
    """Read fresh advisory facts, then call the pure packet builder."""
    root = Path(root).resolve()
    story_path = Path(story_path).resolve()
    story_text = story_path.read_text(encoding="utf-8")
    parsed = parse_localization_hints(story_text)
    has_hints = bool(parsed["affected_files"] or parsed["target_symbols"])
    if not has_hints:
        tree = repofacts.index_tree(root, repofacts.Derivation(root))
        return build_knowledge_packet(
            story_text, None, None, {}, EarnedRecordStore(root).read("lesson"),
            story=str(story_path.relative_to(root)), index_tree=tree,
            byte_budget=byte_budget,
        )
    grounded = grounding if grounding is not None else ground_story_path(
        root, story_path, parsed=parsed
    )
    derivation = repofacts.Derivation(root)
    document = read_symbol_map(root, derivation)
    if str(grounded.get("index_tree", "")) != str(document["index_tree"]):
        raise StaleKnowledgePacket(
            "knowledge grounding and current symbol map index trees differ"
        )
    tracked = document["value"].get("tracked_files", [])
    verified_paths = _verified_file_paths(grounded)
    blobs = {
        str(item["path"]): repofacts.blob_content(root, str(item["blob"]), derivation)
        for item in tracked
        if (isinstance(item, dict)
            and str(item.get("path", "")) in verified_paths)
    }
    return build_knowledge_packet(
        story_text,
        grounded,
        document,
        blobs,
        EarnedRecordStore(root).read("lesson"),
        story=str(story_path.relative_to(root)),
        byte_budget=byte_budget,
    )
