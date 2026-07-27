"""Read-only grounding of advisory story localization hints.

Hints use one optional Markdown section::

    ## Localization hints

    - **Affected files:**
      - `path/to/existing.py`
      - `path/to/planned.py` (new)
    - **Target symbols:**
      - `qualified.or_terminal_name`
      - `planned_symbol` (new)

``(new)`` is an explicit claim, not an inference.  It classifies an absent hint
as new only after the symbol map and its declared grep-fallback coverage both
record no match.  An unmarked absence is unknown, and an incomplete fallback
scan can never establish newness.

The fallback deliberately scans the already-selected tracked blob bytes through
``repofacts`` rather than spawning private ``git grep``.  This preserves the
repository-facts boundary and gives equivalent exact-text evidence for files the
map marks out of structural coverage.  Output and work are bounded, and every
bound is reported in the result.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Callable, Dict, Iterable, List, Optional, Tuple

from . import repofacts
from .knowledge import KnowledgeRefusal
from .model import DwError, Project
from .parse import discover_phases, link_target, parse_story_rows
from .paths import read_text, rel, strip_code
from .repository_map import read_symbol_map
from .symbol_map import GREP_FALLBACK, SYMBOL_MAP_KIND, SYMBOL_MAP_SCHEMA_VERSION


GROUNDING_KIND = "delivery-workbench-story-grounding"
GROUNDING_SCHEMA_VERSION = 1
MAX_SUGGESTIONS = 3
MAX_GREP_MATCHES = 8
MAX_GREP_FILE_BYTES = 1_000_000
MAX_GREP_TOTAL_BYTES = 16_000_000

_SECTION_HEADING_RE = re.compile(r"^##\s+Localization hints\s*$", re.IGNORECASE)
_LEVEL_TWO_HEADING_RE = re.compile(r"^##\s+")
_HINT_GROUP_RE = re.compile(
    r"^-\s+\*\*(Affected files|Target symbols):\*\*\s*(.*)$",
    re.IGNORECASE,
)
_HINT_ITEM_RE = re.compile(r"^\s*-\s+(.+?)\s*$")
_NEW_MARKER_RE = re.compile(r"\s*\(new\)\s*$", re.IGNORECASE)
_CODE_TOKEN_RE = re.compile(r"`([^`\r\n]+)`")
_IDENTIFIER_RE = re.compile(
    r"^(?:[a-z_][A-Za-z0-9_]*_[A-Za-z0-9_]*|"
    r"[A-Z][a-z0-9]+(?:[A-Z][A-Za-z0-9]*)+)$"
)


def _authority_markers() -> dict:
    return {
        "starts_work": False,
        "authorizes": False,
        "satisfies_gate": False,
        "substitutes_for_evidence": False,
    }


def _parse_hint_item(raw: str) -> Tuple[str, bool]:
    declared_new = bool(_NEW_MARKER_RE.search(raw))
    if declared_new:
        raw = _NEW_MARKER_RE.sub("", raw)
    return strip_code(raw.strip()).strip(), declared_new


def _section_lines(text: str, heading_re: re.Pattern) -> List[Tuple[int, str]]:
    lines = text.splitlines()
    start = None  # type: Optional[int]
    for index, line in enumerate(lines):
        if heading_re.match(line.strip()):
            start = index + 1
            break
    if start is None:
        return []
    found = []
    for index in range(start, len(lines)):
        if _LEVEL_TWO_HEADING_RE.match(lines[index].strip()):
            break
        found.append((index + 1, lines[index]))
    return found


def parse_localization_hints(text: str) -> dict:
    """Parse the optional, advisory hint section without touching gate parsing."""
    section = _section_lines(text, _SECTION_HEADING_RE)
    result = {
        "present": bool(section),
        "affected_files": [],
        "target_symbols": [],
        "diagnostics": [],
    }
    if not section:
        return result
    current = None  # type: Optional[str]
    in_comment = False
    for line_number, line in section:
        stripped = line.strip()
        if in_comment:
            if "-->" in stripped:
                in_comment = False
            continue
        if "<!--" in stripped:
            if "-->" not in stripped.split("<!--", 1)[1]:
                in_comment = True
            continue
        if not stripped:
            continue
        group = _HINT_GROUP_RE.match(stripped)
        if group:
            current = (
                "affected_files"
                if group.group(1).lower() == "affected files"
                else "target_symbols"
            )
            inline = group.group(2).strip()
            if inline:
                result["diagnostics"].append({
                    "line": line_number,
                    "message": "put each localization hint on its own nested list item",
                })
            continue
        item = _HINT_ITEM_RE.match(line)
        if item and current:
            value, declared_new = _parse_hint_item(item.group(1))
            if not value:
                result["diagnostics"].append({
                    "line": line_number,
                    "message": "localization hint may not be empty",
                })
                continue
            result[current].append({
                "value": value,
                "declared_new": declared_new,
                "line": line_number,
            })
            continue
        result["diagnostics"].append({
            "line": line_number,
            "message": "unrecognized localization hint syntax",
        })
    return result


def _line_count(source: bytes) -> int:
    return max(1, len(source.splitlines()))


def _location(file_name: str, line_start: int, line_end: int,
              authority: str) -> dict:
    return {
        "file": file_name,
        "line_start": line_start,
        "line_end": line_end,
        "authority": authority,
    }


def _edit_distance(left: str, right: str) -> int:
    """Bounded-input Levenshtein distance with deterministic integer work."""
    if left == right:
        return 0
    if not left:
        return len(right)
    if not right:
        return len(left)
    previous = list(range(len(right) + 1))
    for row, left_char in enumerate(left, 1):
        current = [row]
        for column, right_char in enumerate(right, 1):
            current.append(min(
                current[-1] + 1,
                previous[column] + 1,
                previous[column - 1] + (left_char != right_char),
            ))
        previous = current
    return previous[-1]


def _suggestion_limit(value: str) -> int:
    return max(1, min(4, len(value) // 3))


def _symbol_suggestions(value: str, symbols: Iterable[dict]) -> List[dict]:
    target = value.rsplit(".", 1)[-1]
    candidates = []
    seen = set()
    for symbol in symbols:
        qualified = str(symbol["qualified_name"])
        if qualified in seen:
            continue
        seen.add(qualified)
        distance = min(
            _edit_distance(target, str(symbol["name"])),
            _edit_distance(value, qualified),
        )
        if distance <= _suggestion_limit(target):
            candidates.append((distance, qualified, symbol))
    candidates.sort(key=lambda item: (item[0], item[1]))
    return [
        {
            "name": item[2]["name"],
            "qualified_name": item[2]["qualified_name"],
            "file": item[2]["file"],
            "line_start": item[2]["line_start"],
            "line_end": item[2]["line_end"],
            "distance": item[0],
        }
        for item in candidates[:MAX_SUGGESTIONS]
    ]


def _file_suggestions(value: str, tracked: Iterable[dict]) -> List[dict]:
    candidates = []
    for item in tracked:
        path = str(item["path"])
        distance = _edit_distance(value, path)
        if distance <= _suggestion_limit(value):
            candidates.append((distance, path))
    candidates.sort()
    return [
        {"file": path, "distance": distance}
        for distance, path in candidates[:MAX_SUGGESTIONS]
    ]


def _grep_gaps(value: str, model: dict,
               read_blob: Callable[[str], bytes],
               exclude_paths: Iterable[str] = ()) -> dict:
    tracked = {item["path"]: item for item in model["tracked_files"]}
    matches = []
    scanned_files = 0
    scanned_bytes = 0
    skipped = []
    truncated = False
    excluded = set(exclude_paths)
    gap_paths = [
        gap["file"] for gap in model["gaps"]
        if gap.get("reason") == GREP_FALLBACK
        and gap["file"] not in excluded
    ]
    for path in gap_paths:
        item = tracked.get(path)
        if item is None:
            skipped.append({"file": path, "reason": "missing tracked blob metadata"})
            continue
        size = int(item["size"])
        if size > MAX_GREP_FILE_BYTES:
            skipped.append({"file": path, "reason": "per-file byte bound"})
            continue
        if scanned_bytes + size > MAX_GREP_TOTAL_BYTES:
            skipped.append({"file": path, "reason": "total byte bound"})
            continue
        source = read_blob(str(item["blob"]))
        scanned_files += 1
        scanned_bytes += len(source)
        text = source.decode("utf-8", "replace")
        for line_number, line in enumerate(text.splitlines(), 1):
            if value not in line:
                continue
            if len(matches) < MAX_GREP_MATCHES:
                matches.append(_location(path, line_number, line_number,
                                         "tracked-blob-text-fallback"))
            else:
                truncated = True
        if len(matches) >= MAX_GREP_MATCHES:
            truncated = True
            break
    complete = not skipped and not truncated and scanned_files == len(gap_paths)
    return {
        "rule": GREP_FALLBACK,
        "excluded_declaring_files": sorted(excluded),
        "gap_files": len(gap_paths),
        "files_scanned": scanned_files,
        "bytes_scanned": scanned_bytes,
        "max_file_bytes": MAX_GREP_FILE_BYTES,
        "max_total_bytes": MAX_GREP_TOTAL_BYTES,
        "max_matches": MAX_GREP_MATCHES,
        "matches": matches,
        "skipped": skipped,
        "complete": complete,
        "truncated": truncated,
    }


def _classify_file(hint: dict, model: dict,
                   read_blob: Callable[[str], bytes]) -> dict:
    value = hint["value"]
    tracked = {item["path"]: item for item in model["tracked_files"]}
    item = tracked.get(value)
    matches = []
    if item is not None:
        matches.append(_location(
            value, 1, _line_count(read_blob(str(item["blob"]))), "symbol-map"
        ))
    evidence = {
        "symbol_map_exact_matches": len(matches),
        "no_match": not matches,
    }
    classification = "verified" if matches else (
        "new" if hint["declared_new"] else "unknown"
    )
    return {
        "kind": "affected-file",
        "hint": value,
        "declared_new": hint["declared_new"],
        "classification": classification,
        "locations": matches,
        "suggestions": [] if matches else _file_suggestions(value, model["tracked_files"]),
        "evidence": evidence,
    }


def _classify_symbol(hint: dict, model: dict,
                     read_blob: Callable[[str], bytes],
                     exclude_paths: Iterable[str] = ()) -> dict:
    value = hint["value"]
    matches = [
        symbol for symbol in model["symbols"]
        if value in {symbol["name"], symbol["qualified_name"]}
    ]
    locations = [
        _location(
            str(symbol["file"]), int(symbol["line_start"]),
            int(symbol["line_end"]), "symbol-map"
        )
        for symbol in matches
    ]
    grep = None
    if not matches:
        grep = _grep_gaps(value, model, read_blob, exclude_paths)
    no_match = not matches and grep is not None and not grep["matches"]
    new_supported = (
        bool(hint["declared_new"])
        and no_match
        and bool(grep["complete"])
    )
    classification = "verified" if matches else (
        "new" if new_supported else "unknown"
    )
    evidence = {
        "symbol_map_exact_matches": len(matches),
        "grep_fallback": grep,
        "no_match": no_match,
        "no_match_complete": bool(no_match and grep and grep["complete"]),
    }
    return {
        "kind": "target-symbol",
        "hint": value,
        "declared_new": hint["declared_new"],
        "classification": classification,
        "locations": locations,
        "suggestions": [] if matches else _symbol_suggestions(value, model["symbols"]),
        "evidence": evidence,
    }


def ground_hints(model: dict, parsed: dict,
                 read_blob: Callable[[str], bytes],
                 exclude_paths: Iterable[str] = ()) -> dict:
    """Classify parsed hints against one already freshness-checked map value."""
    if (model.get("kind") != SYMBOL_MAP_KIND
            or model.get("schema_version") != SYMBOL_MAP_SCHEMA_VERSION):
        raise DwError("grounding requires a compatible symbol and structure map")
    files = [
        _classify_file(hint, model, read_blob)
        for hint in parsed["affected_files"]
    ]
    symbols = [
        _classify_symbol(hint, model, read_blob, exclude_paths)
        for hint in parsed["target_symbols"]
    ]
    all_hints = files + symbols
    return {
        "affected_files": files,
        "target_symbols": symbols,
        "summary": {
            status: sum(item["classification"] == status for item in all_hints)
            for status in ("verified", "new", "unknown")
        },
    }


def _story_result(root: Path, story_path: Path, parsed: dict,
                  document: dict, derivation: repofacts.Derivation) -> dict:
    model = document["value"]
    grounded = ground_hints(
        model,
        parsed,
        lambda blob: repofacts.blob_content(root, blob, derivation),
        exclude_paths=(rel(story_path, root),),
    )
    return {
        "kind": GROUNDING_KIND,
        "schema_version": GROUNDING_SCHEMA_VERSION,
        "status": "grounded",
        "story": rel(story_path, root),
        "index_tree": document["index_tree"],
        "hint_syntax": {
            "affected_files": "nested list under **Affected files:**",
            "target_symbols": "nested list under **Target symbols:**",
            "new_marker": "append (new); accepted only with complete no-match evidence",
        },
        "diagnostics": parsed["diagnostics"],
        **grounded,
        **_authority_markers(),
    }


def ground_story_path(root: Path, story_path: Path,
                      parsed: Optional[dict] = None) -> dict:
    """Ground one story, refusing rather than reading a missing or stale map."""
    root = Path(root).resolve()
    story_path = Path(story_path).resolve()
    parsed = parsed if parsed is not None else parse_localization_hints(
        read_text(story_path)
    )
    derivation = repofacts.Derivation(root)
    document = read_symbol_map(root, derivation)
    return _story_result(root, story_path, parsed, document, derivation)


def _find_project_story(project: Project, selector: str) -> Path:
    matches = []
    for phase in discover_phases(project):
        for row in parse_story_rows(phase.path / "current-phase-status.md"):
            target = link_target(row.story_file)
            path = (phase.path / target).resolve()
            selectors = {
                row.story_id.replace("~~", "").strip(),
                Path(target).name,
                Path(target).stem,
            }
            if selector in selectors:
                matches.append(path)
    if not matches:
        raise DwError("story not found in %s: %s" % (project.slug, selector))
    if len(matches) != 1:
        raise DwError("story selector is ambiguous in %s: %s"
                      % (project.slug, selector))
    return matches[0]


def ground_project_story(root: Path, project: Project, selector: str) -> dict:
    return ground_story_path(root, _find_project_story(project, selector))


def grounding_refusal(root: Path, story_path: Path, exc: Exception) -> dict:
    """Return a non-answer suitable for advisory planner output."""
    return {
        "kind": GROUNDING_KIND,
        "schema_version": GROUNDING_SCHEMA_VERSION,
        "status": "refused",
        "story": rel(story_path, root),
        "reason": str(exc),
        **_authority_markers(),
    }


def _acceptance_identifier_lines(text: str, model: dict) -> List[Tuple[int, str]]:
    heading = re.compile(r"^##\s+Acceptance criteria\s*$", re.IGNORECASE)
    exact = set()
    for symbol in model["symbols"]:
        exact.add(str(symbol["name"]))
        exact.add(str(symbol["qualified_name"]))
    found = []
    for line_number, line in _section_lines(text, heading):
        for token in _CODE_TOKEN_RE.findall(line):
            token = token.strip()
            terminal = token.rsplit(".", 1)[-1]
            if token in exact and _IDENTIFIER_RE.fullmatch(terminal):
                found.append((line_number, token))
    return found


def _story_warning_lines(root: Path, story_path: Path, result: dict,
                         parsed: dict, text: str, model: dict) -> List[str]:
    path = rel(story_path, root)
    warnings = []
    for diagnostic in parsed["diagnostics"]:
        warnings.append(
            "%s:%d: %s" % (path, diagnostic["line"], diagnostic["message"])
        )
    for item in result["affected_files"] + result["target_symbols"]:
        if item["classification"] == "unknown":
            suggestions = ", ".join(
                suggestion.get("qualified_name", suggestion.get("file", ""))
                for suggestion in item["suggestions"]
            ) or "none"
            warnings.append(
                "%s: localization %s hint `%s` is unknown; near misses: %s"
                % (path, item["kind"], item["hint"], suggestions)
            )
        elif item["classification"] == "verified" and item["declared_new"]:
            warnings.append(
                "%s: localization %s hint `%s` is marked new but already exists"
                % (path, item["kind"], item["hint"])
            )
    for line_number, token in _acceptance_identifier_lines(text, model):
        warnings.append(
            "%s:%d: acceptance criteria name exact code identifier `%s`; "
            "keep behavior in criteria and put identifiers in Localization hints"
            % (path, line_number, token)
        )
    return warnings


def grounding_warnings(project: Project, root: Path) -> List[str]:
    """Return advisory lints; callers must never promote them to errors."""
    root = Path(root).resolve()
    stories = []
    needs_map = False
    for phase in discover_phases(project):
        for row in parse_story_rows(phase.path / "current-phase-status.md"):
            story_path = (phase.path / link_target(row.story_file)).resolve()
            if not story_path.is_file():
                continue
            text = read_text(story_path)
            parsed = parse_localization_hints(text)
            if parsed["present"] or _section_lines(
                    text, re.compile(r"^##\s+Acceptance criteria\s*$", re.IGNORECASE)):
                needs_map = True
            stories.append((story_path, text, parsed))
    if not needs_map:
        return []

    derivation = repofacts.Derivation(root)
    try:
        document = read_symbol_map(root, derivation)
    except (KnowledgeRefusal, DwError) as exc:
        hinted = [item for item in stories if item[2]["present"]]
        if not hinted:
            return []
        return [
            "%s: grounding unavailable: %s" % (rel(path, root), exc)
            for path, _text, _parsed in hinted
        ]

    warnings = []
    model = document["value"]
    for story_path, text, parsed in stories:
        if parsed["present"]:
            result = _story_result(root, story_path, parsed, document, derivation)
        else:
            result = {"affected_files": [], "target_symbols": []}
        warnings.extend(_story_warning_lines(
            root, story_path, result, parsed, text, model
        ))
    return warnings
