#!/usr/bin/env python3
"""Lint visible Workbench template copy against the product language contract.

The checker reads JavaScript HTML template literals structurally, ignores exact
copy inside explicit Technical details folds (and code/pre regions), and reports
reserved engineering language that leaks into ordinary panel text.  Its built-in
red fixture plants one ordinary leak and one allowed Technical-details use so a
clean run also proves both sides of the boundary.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from html.parser import HTMLParser
from pathlib import Path
from typing import Any, Iterator


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SOURCE_DIR = ROOT / "pmo-roadmap" / "workbench"
CONTRACT_PATH = ROOT / "docs" / "product-language-contract-v1.json"

# These functions own ordinary, human-facing panels. Exact graph, timeline,
# stream, JSON, and source-document helpers are intentionally absent: their
# output is passed into an explicit Technical details fold by the owning shell.
ORDINARY_PANEL_FUNCTIONS = {
    "statusPanel", "arrivalPanel", "healthItem", "boardCard", "boardLane",
    "boardNotice", "boardPreviewFiles", "openMovePanel", "openCreatePanel",
    "openPhasePanel", "boardOverviewStrip", "provenanceHtml",
    "adoptionReviewTabs", "adoptionItemReviewHtml", "renderAdoptionMarks",
    "adoptionStoryHtml", "adoptionReviewBody", "viewLegacyAdoptionReview",
    "ideationStepIndicator", "ideationShell", "draftField", "renderDraftStep",
    "renderIdeaStep", "renderReviewStep", "previewChangesHtml",
    "renderPreviewStep", "renderAppliedStep", "field", "validateView",
    "grantPreviewHtml", "runEmptyHtml", "liveConnectionHtml",
    "liveAnswerGrid", "liveProgressGroups", "livePeopleHtml", "liveReviewHtml",
    "liveNextHtml", "liveLimitsHtml", "boundedMeasurementHtml",
    "boundedUsageTable", "boundedPermissionHtml", "boundedInboxHtml",
    "boundedFailureDetailsHtml", "boundedPreviewHtml", "boundedReceiptsHtml",
    "boundedActionButtonsHtml", "boundedActionCenterHtml", "liveActivityHtml",
    "liveProgressShell", "programInventoryHtml", "programNarrowingHtml",
    "programConsentHtml", "programStartHtml", "programOrganizationHtml",
    "liveMissionCard", "liveMissionInventoryHtml", "setupEffectList",
    "deliveryChoiceCard", "deliveryChoiceReview", "renderDeliverySetup",
    "studioPlanFactList", "studioPlanItemList", "studioPlanCorrections",
    "studioProgramPlanEditor", "studioWorkflowStepEditor",
    "studioWorkflowPlanEditor", "studioTeamResponsibilitiesEditor",
    "studioTeamIndependenceEditor", "studioTeamDecisionsEditor",
    "studioTeamEscalationEditor", "studioTeamAuditEditor",
    "studioTeamReviewEditor", "studioPlainSection", "studioReviewCriteriaHtml",
    "studioPlanReview", "studioValidationView", "studioSavePreviewHtml",
    "renderStudioBundle",
}


@dataclass
class StringToken:
    text: str
    line: int


@dataclass
class Element:
    tag: str
    line: int
    children: list["Element | str"] = field(default_factory=list)


class FragmentParser(HTMLParser):
    """Small tolerant tree builder for static HTML template fragments."""

    VOID = {
        "area", "base", "br", "col", "embed", "hr", "img", "input",
        "link", "meta", "param", "source", "track", "wbr",
    }

    def __init__(self, line: int) -> None:
        super().__init__(convert_charrefs=True)
        self.root = Element("fragment", line)
        self.stack = [self.root]

    def handle_starttag(
        self, tag: str, attrs: list[tuple[str, str | None]]
    ) -> None:
        del attrs
        child = Element(tag.casefold(), self.getpos()[0])
        self.stack[-1].children.append(child)
        if child.tag not in self.VOID:
            self.stack.append(child)

    def handle_startendtag(
        self, tag: str, attrs: list[tuple[str, str | None]]
    ) -> None:
        self.handle_starttag(tag, attrs)
        if self.stack[-1].tag == tag.casefold() and tag.casefold() not in self.VOID:
            self.stack.pop()

    def handle_endtag(self, tag: str) -> None:
        folded = tag.casefold()
        for index in range(len(self.stack) - 1, 0, -1):
            if self.stack[index].tag == folded:
                del self.stack[index:]
                return

    def handle_data(self, data: str) -> None:
        self.stack[-1].children.append(data)


def _skip_comment(source: str, index: int) -> int:
    if source.startswith("//", index):
        end = source.find("\n", index + 2)
        return len(source) if end < 0 else end
    if source.startswith("/*", index):
        end = source.find("*/", index + 2)
        return len(source) if end < 0 else end + 2
    return index


def _read_quoted(source: str, index: int) -> tuple[StringToken, int]:
    quote = source[index]
    line = source.count("\n", 0, index) + 1
    index += 1
    chunks: list[str] = []
    while index < len(source):
        char = source[index]
        if char == "\\":
            if index + 1 < len(source):
                chunks.append(source[index:index + 2])
                index += 2
                continue
        if char == quote:
            return StringToken("".join(chunks), line), index + 1
        chunks.append(char)
        index += 1
    return StringToken("".join(chunks), line), index


def js_strings(source: str) -> Iterator[StringToken]:
    """Yield JavaScript strings without needing a third-party JS parser.

    Template expressions are replaced by an inert marker. Nested strings are
    encountered by the recursive expression walk and yielded independently.
    The lexer also skips comments, where HTML examples are not rendered copy.
    """

    tokens: list[StringToken] = []

    def walk(start: int, stop: int | None = None) -> int:
        index = start
        brace_depth = 0
        while index < len(source):
            if stop is not None and source[index] == "}" and brace_depth == 0:
                return index + 1
            skipped = _skip_comment(source, index)
            if skipped != index:
                index = skipped
                continue
            char = source[index]
            if char in "'\"":
                token, index = _read_quoted(source, index)
                tokens.append(token)
                continue
            if char == "`":
                line = source.count("\n", 0, index) + 1
                index += 1
                chunks: list[str] = []
                while index < len(source):
                    if source[index] == "\\":
                        chunks.append(source[index:index + 2])
                        index += 2
                        continue
                    if source[index] == "`":
                        index += 1
                        break
                    if source.startswith("${", index):
                        chunks.append(" DW_TEMPLATE_VALUE ")
                        index = walk(index + 2, stop=1)
                        continue
                    chunks.append(source[index])
                    index += 1
                tokens.append(StringToken("".join(chunks), line))
                continue
            if stop is not None:
                if char == "{":
                    brace_depth += 1
                elif char == "}":
                    brace_depth -= 1
            index += 1
        return index

    walk(0)
    yield from sorted(tokens, key=lambda item: item.line)


def element_text(element: Element) -> str:
    return " ".join(
        child if isinstance(child, str) else element_text(child)
        for child in element.children
    )


def ordinary_text_nodes(root: Element, technical_label: str) -> Iterator[str]:
    ignored = {"code", "pre", "script", "style"}

    def walk(element: Element, technical: bool = False) -> Iterator[str]:
        if element.tag in ignored:
            return
        if element.tag == "details":
            summary = next(
                (
                    child for child in element.children
                    if isinstance(child, Element) and child.tag == "summary"
                ),
                None,
            )
            if summary is not None and element_text(summary).strip().casefold().startswith(
                technical_label.casefold()
            ):
                technical = True
        for child in element.children:
            if isinstance(child, str):
                text = re.sub(r"\s+", " ", child).strip()
                if text and not technical:
                    yield text
            else:
                yield from walk(child, technical)

    yield from walk(root)


def load_contract() -> tuple[str, list[tuple[str, re.Pattern[str]]]]:
    contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
    projection = contract.get("projection")
    if not isinstance(projection, dict):
        raise ValueError("contract.projection must be an object")
    technical_label = projection.get("technical_view_label")
    rules = projection.get("rules")
    if not isinstance(technical_label, str) or not technical_label.strip():
        raise ValueError("contract.projection.technical_view_label must be text")
    if not isinstance(rules, list) or not any(
        isinstance(rule, dict) and rule.get("id") == "explicit-audit-boundary"
        for rule in rules
    ):
        raise ValueError("contract is missing explicit-audit-boundary")
    reserved: list[tuple[str, re.Pattern[str]]] = []
    for index, entry in enumerate(contract.get("reserved_terms", [])):
        if not isinstance(entry, dict):
            raise ValueError(f"contract.reserved_terms[{index}] must be an object")
        term = entry.get("term")
        pattern = entry.get("pattern")
        if not isinstance(term, str) or not isinstance(pattern, str):
            raise ValueError(
                f"contract.reserved_terms[{index}] needs term and pattern text"
            )
        reserved.append((term, re.compile(pattern, re.IGNORECASE)))
    if not reserved:
        raise ValueError("contract.reserved_terms must not be empty")
    return technical_label, reserved


def function_by_line(source: str) -> dict[int, str]:
    """Map source lines to their containing named function declaration."""
    lines = source.splitlines()
    starts: list[tuple[int, str]] = []
    pattern = re.compile(r"^\s*(?:async\s+)?function\s+([A-Za-z_$][\w$]*)\s*\(")
    for line_number, line in enumerate(lines, 1):
        match = pattern.match(line)
        if match:
            starts.append((line_number, match.group(1)))
    result: dict[int, str] = {}
    for index, (start, name) in enumerate(starts):
        end = starts[index + 1][0] if index + 1 < len(starts) else len(lines) + 1
        for line_number in range(start, end):
            result[line_number] = name
    return result


def lint_source(
    source: str,
    *,
    display_path: str,
    technical_label: str,
    reserved: list[tuple[str, re.Pattern[str]]],
    ordinary_functions: set[str] | None = None,
) -> list[str]:
    errors: list[str] = []
    seen: set[tuple[int, str, str]] = set()
    owners = function_by_line(source) if ordinary_functions is not None else {}
    for token in js_strings(source):
        if ordinary_functions is not None and owners.get(token.line) not in ordinary_functions:
            continue
        if not re.search(r"<[a-zA-Z][^>]*>", token.text):
            continue
        parser = FragmentParser(token.line)
        try:
            parser.feed(token.text)
            parser.close()
        except Exception as exc:  # HTMLParser is tolerant; retain a stable refusal.
            errors.append(
                f"{display_path}:{token.line}: cannot inspect panel template: {exc}"
            )
            continue
        for text in ordinary_text_nodes(parser.root, technical_label):
            for term, pattern in reserved:
                match = pattern.search(text)
                if not match:
                    continue
                key = (token.line, term, text)
                if key in seen:
                    continue
                seen.add(key)
                errors.append(
                    f"{display_path}:{token.line}: forbidden term {term!r} "
                    f"in ordinary panel text: {text!r}"
                )
    return errors


def negative_fixture_check(
    technical_label: str,
    reserved: list[tuple[str, re.Pattern[str]]],
) -> tuple[bool, str]:
    term, _pattern = reserved[0]
    fixture_path = "<negative-fixture>/app.js"
    ordinary = (
        "function panel() { return `"
        f"<section><h2>Ordinary panel</h2><p>The {term} is visible here.</p>"
        "</section>`; }"
    )
    technical = (
        "function panel() { return `"
        f"<section><h2>Ordinary panel</h2><details><summary>{technical_label}"
        f"</summary><p>The {term} is visible here.</p></details></section>`; }}"
    )
    ordinary_errors = lint_source(
        ordinary,
        display_path=fixture_path,
        technical_label=technical_label,
        reserved=reserved,
    )
    technical_errors = lint_source(
        technical,
        display_path=fixture_path,
        technical_label=technical_label,
        reserved=reserved,
    )
    ok = bool(ordinary_errors) and not technical_errors
    proof = ordinary_errors[0] if ordinary_errors else "negative fixture was not refused"
    if technical_errors:
        proof = "Technical details fixture was incorrectly refused: " + technical_errors[0]
    return ok, proof


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--source",
        type=Path,
        default=None,
        help="JavaScript source to inspect (defaults to all Workbench JS files)",
    )
    parser.add_argument(
        "--no-self-test",
        action="store_true",
        help="omit the built-in negative fixture (intended only for focused debugging)",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    use_default = args.source is None
    try:
        technical_label, reserved = load_contract()
        if use_default:
            source = "\n".join(
                f.read_text(encoding="utf-8")
                for f in sorted(DEFAULT_SOURCE_DIR.glob("*.js"))
            )
        else:
            source = args.source.read_text(encoding="utf-8")
    except (OSError, ValueError, json.JSONDecodeError, re.error) as exc:
        print(f"ERROR {exc}")
        return 1

    if use_default:
        display_path = str(DEFAULT_SOURCE_DIR.relative_to(ROOT)) + "/*.js"
    else:
        try:
            display_path = str(args.source.resolve().relative_to(ROOT))
        except ValueError:
            display_path = str(args.source)
    errors = lint_source(
        source,
        display_path=display_path,
        technical_label=technical_label,
        reserved=reserved,
        ordinary_functions=(
            ORDINARY_PANEL_FUNCTIONS if use_default else None
        ),
    )
    if use_default:
        memory_path = DEFAULT_SOURCE_DIR / "memory-panel.js"
        errors.extend(lint_source(
            memory_path.read_text(encoding="utf-8"),
            display_path=str(memory_path.relative_to(ROOT)),
            technical_label=technical_label,
            reserved=reserved,
        ))
    fixture_proof = "not run"
    if not args.no_self_test:
        fixture_ok, fixture_proof = negative_fixture_check(technical_label, reserved)
        if not fixture_ok:
            errors.append(f"negative fixture contract failed: {fixture_proof}")

    if errors:
        for error in errors:
            print(f"ERROR {error}")
        return 1
    print(
        "workbench-language-lint.py: ok "
        f"({len(reserved)} reserved terms; negative fixture refused: {fixture_proof})"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
