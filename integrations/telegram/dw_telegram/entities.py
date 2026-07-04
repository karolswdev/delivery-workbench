"""Entity-based formatting (WLA-14-03, absorption map §2 idea #1).

The ccgram lesson absorbed at the representation level: never
escape MarkdownV2 — convert markdown to plain text plus explicit
entity offsets, so there is no syntax left to break. The only
remaining failure mode is an API error, which the send layer
answers with the plain text alone (the two-phase fallback).

Telegram counts offsets and lengths in UTF-16 code units, not
Python characters — an emoji is length 2. Getting this wrong
garbles every message after the first emoji, so the arithmetic
lives in one place here and the tests feed it emoji on purpose.

Deliberately minimal dialect — exactly what this interface and the
agents it relays actually emit: ```pre blocks```, `inline code`,
**bold**. Everything else passes through as text. Splitting
happens only here, in the send layer's service (`chunk`) — never
in renderers, which keep full content.
"""

from __future__ import annotations

import re

TELEGRAM_LIMIT = 4096

_TOKEN_RE = re.compile(
    r"```(?:[a-zA-Z0-9_+-]*\n)?(.*?)```"  # pre (optional language line)
    r"|`([^`\n]+)`"  # inline code
    r"|\*\*([^*\n][^*]*?)\*\*",  # bold
    re.DOTALL,
)


def _utf16_len(text: str) -> int:
    return len(text.encode("utf-16-le")) // 2


def to_entities(markdown: str) -> tuple[str, list[dict]]:
    """(plain_text, entities) — entities in Telegram's wire shape:
    {"type", "offset", "length"} with UTF-16 units."""
    plain_parts: list[str] = []
    entities: list[dict] = []
    cursor = 0  # UTF-16 offset of the text emitted so far
    last_end = 0
    for match in _TOKEN_RE.finditer(markdown):
        before = markdown[last_end : match.start()]
        plain_parts.append(before)
        cursor += _utf16_len(before)
        pre, code, bold = match.groups()
        if pre is not None:
            content, kind = pre.strip("\n"), "pre"
        elif code is not None:
            content, kind = code, "code"
        else:
            content, kind = bold, "bold"
        if content:
            entities.append(
                {
                    "type": kind,
                    "offset": cursor,
                    "length": _utf16_len(content),
                }
            )
        plain_parts.append(content)
        cursor += _utf16_len(content)
        last_end = match.end()
    plain_parts.append(markdown[last_end:])
    return "".join(plain_parts), entities


def chunk(
    text: str, entities: list[dict], limit: int = TELEGRAM_LIMIT
) -> list[tuple[str, list[dict]]]:
    """Split at the send layer, preferring line boundaries. Entities
    are re-scoped per chunk; one crossing a boundary is dropped
    rather than allowed to corrupt offsets."""
    if _utf16_len(text) <= limit:
        return [(text, entities)]
    chunks: list[tuple[str, list[dict]]] = []
    pos = 0  # python-char cursor into text
    offset16 = 0  # UTF-16 units consumed so far
    total = len(text)
    while pos < total:
        # Largest char count whose UTF-16 length fits (binary search:
        # surrogate pairs make chars != units).
        lo, hi = 1, total - pos
        while lo < hi:
            mid = (lo + hi + 1) // 2
            if _utf16_len(text[pos : pos + mid]) <= limit:
                lo = mid
            else:
                hi = mid - 1
        cut = lo
        if pos + cut < total:
            newline = text.rfind("\n", pos + max(0, cut - 400), pos + cut)
            if newline > pos:
                cut = newline + 1 - pos
        piece = text[pos : pos + cut]
        piece16 = _utf16_len(piece)
        scoped = [
            {**entity, "offset": entity["offset"] - offset16}
            for entity in entities
            if entity["offset"] >= offset16
            and entity["offset"] + entity["length"] <= offset16 + piece16
        ]
        chunks.append((piece, scoped))
        pos += cut
        offset16 += piece16
    return chunks
