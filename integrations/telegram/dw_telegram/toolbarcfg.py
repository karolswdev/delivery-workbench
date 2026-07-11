"""Toolbar configuration — per-harness button grids as data.

Transmuted from ccgram v4.3.11 ``toolbar_config.py``: the grid/style/
action-type model carries over; TOML becomes a JSON object under the
``"toolbar"`` key of ``telegram.json`` (the 3.9 floor has no
tomllib), and the builtin table is CLOSED — a config can rearrange,
relabel, or drop buttons, never mint capability.

Action types:
  - ``key``:     one named key through the driver (the only door).
  - ``text``:    literal text + Enter through the driver.
  - ``builtin``: a special handler from the closed set below.

The loader never raises: malformed entries are skipped and returned
as warnings for the caller to surface. This module is an import-pure
leaf — no Telegram, no tmux, no siblings — so the whole config story
is testable in isolation.

Config shape (all keys optional)::

    "toolbar": {
      "style": "emoji" | "text" | "emoji_text",
      "actions": {
        "deep": {"emoji": "🧠", "text": "Deep",
                  "type": "text", "payload": "/think"}
      },
      "grids": {"claude": [["deep", "esc"], ["screen", "dismiss"]]}
    }
"""

from __future__ import annotations

BUILTINS = frozenset({"screen", "live", "dismiss"})
STYLES = frozenset({"emoji", "text", "emoji_text"})
_TYPES = frozenset({"key", "text", "builtin"})

DEFAULT_STYLE = "emoji_text"

# id -> (emoji, label, type, payload)
DEFAULT_ACTIONS: dict = {
    "enter": ("⏎", "Enter", "key", "Enter"),
    "esc": ("⎋", "Esc", "key", "Escape"),
    "up": ("↑", "Up", "key", "Up"),
    "down": ("↓", "Down", "key", "Down"),
    "tab": ("⇥", "Tab", "key", "Tab"),
    "screen": ("📸", "Screen", "builtin", "screen"),
    "live": ("📺", "Live", "builtin", "live"),
    "dismiss": ("✖", "Close", "builtin", "dismiss"),
}

# Per-harness grids, keyed by the HARNESS names the driver knows.
# The claude grid is also the unknown-harness fallback.
DEFAULT_GRIDS: dict = {
    "claude": [
        ["screen", "live", "dismiss"],
        ["enter", "esc", "tab"],
        ["up", "down"],
    ],
    "codex": [
        ["screen", "live", "dismiss"],
        ["enter", "esc"],
        ["up", "down"],
    ],
    "pi": [
        ["screen", "live", "dismiss"],
        ["enter", "esc"],
    ],
}


class ToolbarAction:
    __slots__ = ("action_id", "emoji", "text", "kind", "payload")

    def __init__(self, action_id, emoji, text, kind, payload):
        self.action_id = action_id
        self.emoji = emoji
        self.text = text
        self.kind = kind  # "key" | "text" | "builtin"
        self.payload = payload


class ToolbarConfig:
    def __init__(self, actions, grids, style):
        self._actions = actions  # id -> ToolbarAction
        self._grids = grids  # harness -> [[id, ...], ...]
        self.style = style

    def action(self, action_id: str):
        return self._actions.get(action_id)

    def grid_for(self, harness: str):
        return self._grids.get(harness) or self._grids["claude"]

    def label(self, action) -> str:
        if self.style == "emoji" and action.emoji:
            return action.emoji
        if self.style == "text" or not action.emoji:
            return action.text
        return f"{action.emoji} {action.text}"

    def buttons_for(self, harness: str):
        """The inline keyboard: key actions ride the existing kb:
        channel (one door); text/builtin resolve at TAP time through
        tb:<id>, so a config change never leaves a stale payload
        armed inside an old message."""
        rows = []
        for row in self.grid_for(harness):
            built = []
            for action_id in row:
                action = self._actions.get(action_id)
                if action is None:
                    continue
                data = (
                    f"kb:{action.payload}"
                    if action.kind == "key"
                    else f"tb:{action.action_id}"
                )
                built.append((self.label(action), data))
            if built:
                rows.append(built)
        return rows


def _default_actions() -> dict:
    return {
        action_id: ToolbarAction(action_id, *spec)
        for action_id, spec in DEFAULT_ACTIONS.items()
    }


def load_toolbar(doc) -> tuple:
    """(ToolbarConfig, warnings). Garbage in any position degrades to
    the defaults for that position, with a warning naming it; the
    loader never raises and never mints a builtin."""
    warnings: list[str] = []
    actions = _default_actions()
    grids = {k: [list(r) for r in v] for k, v in DEFAULT_GRIDS.items()}
    style = DEFAULT_STYLE
    if doc is None:
        return ToolbarConfig(actions, grids, style), warnings
    if not isinstance(doc, dict):
        return (
            ToolbarConfig(actions, grids, style),
            ["toolbar config is not an object; defaults kept"],
        )

    raw_style = doc.get("style")
    if raw_style is not None:
        if isinstance(raw_style, str) and raw_style in STYLES:
            style = raw_style
        else:
            warnings.append(f"unknown toolbar style {raw_style!r}; kept {style}")

    raw_actions = doc.get("actions")
    if raw_actions is not None and not isinstance(raw_actions, dict):
        warnings.append("toolbar actions is not an object; defaults kept")
        raw_actions = None
    for action_id, spec in (raw_actions or {}).items():
        name = str(action_id)
        if not isinstance(spec, dict):
            warnings.append(f"action {name!r} is not an object; skipped")
            continue
        kind = spec.get("type")
        payload = spec.get("payload")
        if kind not in _TYPES:
            warnings.append(f"action {name!r} has unknown type {kind!r}; skipped")
            continue
        if kind == "builtin" and payload not in BUILTINS:
            # The closed table: capability is never config.
            warnings.append(
                f"action {name!r} names builtin {payload!r} which does "
                f"not exist; the builtin table is closed — skipped"
            )
            continue
        if not isinstance(payload, str) or not payload:
            warnings.append(f"action {name!r} has no payload; skipped")
            continue
        actions[name] = ToolbarAction(
            name,
            str(spec.get("emoji") or ""),
            str(spec.get("text") or name),
            kind,
            payload,
        )

    raw_grids = doc.get("grids")
    if raw_grids is not None and not isinstance(raw_grids, dict):
        warnings.append("toolbar grids is not an object; defaults kept")
        raw_grids = None
    for harness, raw_grid in (raw_grids or {}).items():
        if not isinstance(raw_grid, list):
            warnings.append(f"grid for {harness!r} is not a list; skipped")
            continue
        cleaned = []
        for row in raw_grid:
            if not isinstance(row, list):
                warnings.append(f"grid row {row!r} for {harness!r} is not a list; skipped")
                continue
            kept = []
            for cell in row:
                if str(cell) in actions:
                    kept.append(str(cell))
                else:
                    warnings.append(
                        f"grid cell {cell!r} for {harness!r} names no "
                        f"action; skipped"
                    )
            if kept:
                cleaned.append(kept)
        if cleaned:
            grids[str(harness)] = cleaned
        else:
            warnings.append(f"grid for {harness!r} came out empty; default kept")
    return ToolbarConfig(actions, grids, style), warnings
