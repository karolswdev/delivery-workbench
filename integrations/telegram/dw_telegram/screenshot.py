"""Terminal text → PNG: the pane becomes a picture.

Transmuted from ccgram v4.3.11 ``screenshot.py`` (MIT, lineage in
docs/absorption-ccgram.md): the SGR state machine, the 256-color
approximation, and the non-SGR stripping carry over; the async
wrapper, structlog, and the three-tier CJK font chain do not. One
bundled font (JetBrains Mono, OFL-1.1, license file alongside)
covers Latin, box-drawing, and blocks — a missing glyph renders as
tofu, which is honest until a real pane needs more.

Pillow is OPTIONAL. The module imports without it; ``AVAILABLE``
says whether rendering works, ``unavailable_reason()`` says why
not, and ``text_to_image`` returns None instead of raising. Callers
own the fallback (send the text capture instead).

This module is an import-pure leaf: it imports nothing from
dw_telegram (fitness-enforced), so the renderer can be reasoned
about — and tested — in complete isolation.
"""

from __future__ import annotations

import io
import re
from pathlib import Path

try:  # the one optional dependency, probed once
    from PIL import Image, ImageDraw, ImageFont

    _PIL_ERROR: str | None = None
except Exception as _exc:  # pragma: no cover - depends on environment
    Image = ImageDraw = ImageFont = None  # type: ignore[assignment]
    _PIL_ERROR = f"{type(_exc).__name__}: Pillow is not installed"

AVAILABLE = _PIL_ERROR is None

_RE_SGR = re.compile(r"\x1b\[([0-9;]*)m")

# Non-SGR escapes stripped before rendering: OSC strings (BEL or ST
# terminated), CSI sequences not ending in 'm', charset designators
# (ESC ( B and kin — three bytes, which upstream's two-byte rule
# half-stripped, leaving a stray letter), and two-byte ESC
# designators. ESC[...m passes through so color parsing still works.
_RE_NON_SGR = re.compile(
    r"\x1b\](?:[^\x07\x1b]|\x1b(?!\\))*(?:\x07|\x1b\\)"
    r"|\x1b\[[\x30-\x3f]*[\x20-\x2f]*[\x40-\x6c\x6e-\x7e]"
    r"|\x1b[()*+][\x20-\x7e]"
    r"|\x1b[^\[\]]"
)

# VS Code-ish 16-color palette, same values ccgram ships.
_ANSI_COLORS = {
    0: (0, 0, 0), 1: (205, 49, 49), 2: (13, 188, 121),
    3: (229, 229, 16), 4: (36, 114, 200), 5: (188, 63, 188),
    6: (17, 168, 205), 7: (229, 229, 229), 8: (102, 102, 102),
    9: (241, 76, 76), 10: (35, 209, 139), 11: (245, 245, 67),
    12: (59, 142, 234), 13: (214, 112, 214), 14: (41, 184, 219),
    15: (255, 255, 255),
}
_DEFAULT_FG = (212, 212, 212)
_DEFAULT_BG = (30, 30, 30)

_FONT_PATH = Path(__file__).parent / "fonts" / "JetBrainsMono-Regular.ttf"
_font_cache: dict = {}


def unavailable_reason() -> str | None:
    """None when rendering works; otherwise the human-readable why."""
    return _PIL_ERROR


def strip_non_sgr(text: str) -> str:
    """Drop cursor moves, OSC titles/hyperlinks, and mode sets;
    keep SGR color sequences intact. Pure string work — usable
    (and tested) without Pillow."""
    return _RE_NON_SGR.sub("", text)


class _Style:
    __slots__ = ("fg", "bg")

    def __init__(self, fg=_DEFAULT_FG, bg=None):
        self.fg = fg
        self.bg = bg


def _color_256(idx: int):
    if idx < 16:
        return _ANSI_COLORS[idx]
    if idx < 232:  # 6x6x6 cube
        idx -= 16
        return ((idx // 36) * 51, ((idx % 36) // 6) * 51, (idx % 6) * 51)
    gray = 8 + (idx - 232) * 10  # grayscale ramp
    return (gray, gray, gray)


def _apply_sgr(style: _Style, codes: str) -> _Style:
    new = _Style(style.fg, style.bg)
    try:
        parts = [int(c) for c in codes.split(";") if c]
    except ValueError:
        return new  # garbage params: keep the current style
    if not parts:
        return _Style()
    i = 0
    while i < len(parts):
        code = parts[i]
        if code == 0:
            new = _Style()
        elif 30 <= code <= 37:
            new.fg = _ANSI_COLORS[code - 30]
        elif code == 38 and i + 2 < len(parts) and parts[i + 1] == 5:
            new.fg = _color_256(parts[i + 2] % 256)
            i += 2
        elif code == 38 and i + 4 < len(parts) and parts[i + 1] == 2:
            new.fg = tuple(min(255, max(0, v)) for v in parts[i + 2 : i + 5])
            i += 4
        elif code == 39:
            new.fg = _DEFAULT_FG
        elif 40 <= code <= 47:
            new.bg = _ANSI_COLORS[code - 40]
        elif code == 48 and i + 2 < len(parts) and parts[i + 1] == 5:
            new.bg = _color_256(parts[i + 2] % 256)
            i += 2
        elif code == 48 and i + 4 < len(parts) and parts[i + 1] == 2:
            new.bg = tuple(min(255, max(0, v)) for v in parts[i + 2 : i + 5])
            i += 4
        elif code == 49:
            new.bg = None
        elif 90 <= code <= 97:
            new.fg = _ANSI_COLORS[code - 90 + 8]
        elif 100 <= code <= 107:
            new.bg = _ANSI_COLORS[code - 100 + 8]
        elif code == 7:  # reverse video: swap, treating no-bg as canvas
            new.fg, new.bg = (new.bg or _DEFAULT_BG), new.fg
        # bold/dim/italic/underline (1,2,3,4,…) are legibility hints a
        # 28px render does not need — tolerated and ignored.
        i += 1
    return new


def _parse_line(line: str) -> list:
    """One line → [(text, _Style)], SGR state threaded through."""
    segments = []
    style = _Style()
    pos = 0
    for match in _RE_SGR.finditer(line):
        if line[pos : match.start()]:
            segments.append((line[pos : match.start()], style))
        style = _apply_sgr(style, match.group(1))
        pos = match.end()
    if line[pos:]:
        segments.append((line[pos:], style))
    return segments or [("", _Style())]


def _load_font(size: int):
    if size not in _font_cache:
        try:
            _font_cache[size] = ImageFont.truetype(str(_FONT_PATH), size)
        except OSError:
            _font_cache[size] = ImageFont.load_default()
    return _font_cache[size]


def text_to_image(
    text: str, font_size: int = 28, live: bool = False
) -> bytes | None:
    """Render pane text (ANSI SGR honored) to PNG bytes, or None
    when Pillow is absent — the caller states the fallback. ``live``
    trades fidelity for weight: smaller font, 32-color quantize,
    max compression (repeated editMessageMedia stays cheap)."""
    if not AVAILABLE:
        return None
    size = 20 if live else font_size
    font = _load_font(size)
    lines = strip_non_sgr(text).split("\n")
    parsed = [_parse_line(line) for line in lines]

    padding = 16
    line_height = int(size * 1.4)
    probe = ImageDraw.Draw(Image.new("RGB", (1, 1)))

    def _width(seg_text, f):
        box = probe.textbbox((0, 0), seg_text, font=f)
        return box[2] - box[0]

    max_width = max(
        (sum(_width(t, font) for t, _ in segs) for segs in parsed),
        default=0,
    )
    img = Image.new(
        "RGB",
        (
            max(int(max_width) + padding * 2, 200),
            max(line_height * len(lines) + padding * 2,
                line_height + padding * 2),
        ),
        _DEFAULT_BG,
    )
    draw = ImageDraw.Draw(img)
    y = padding
    for segs in parsed:
        x = padding
        for seg_text, style in segs:
            if style.bg is not None:
                draw.rectangle(
                    [x, y, x + _width(seg_text, font), y + line_height],
                    fill=style.bg,
                )
            draw.text((x, y), seg_text, fill=style.fg, font=font)
            x += _width(seg_text, font)
        y += line_height

    buf = io.BytesIO()
    if live:
        img = img.quantize(colors=32)
        img.save(buf, format="PNG", optimize=True, compress_level=9)
    else:
        img.save(buf, format="PNG")
    return buf.getvalue()
