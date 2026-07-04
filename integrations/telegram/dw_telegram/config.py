"""Operator configuration.

Lives at ``~/.config/delivery-workbench/telegram.json`` — outside the
repo, chmod 600, authored by the operator, read only at runtime. The
bot token may instead ride ``TELEGRAM_BOT_TOKEN``. Nothing in this
module ever logs, prints, or embeds the token; errors mention the
path, never the content.

Recognized keys::

    {
      "bot_token": "…",                  // or TELEGRAM_BOT_TOKEN
      "workspace_roots": ["~/dev"],      // lifecycle allow-list (§4 ring 2)
      "default_repo": "~/dev/somerepo",  // initial active rails repo
      "state_path": "…",                 // runtime state (default beside config)
      "registry_path": "…",              // sessions registry override
      "dw_cli": ["/path/to/dw"],         // explicit dw argv prefix
      "agent_events_path": "…"           // dw hook stream override
    }
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path

DEFAULT_CONFIG_PATH = (
    Path.home() / ".config" / "delivery-workbench" / "telegram.json"
)
TOKEN_ENV = "TELEGRAM_BOT_TOKEN"


class ConfigError(ValueError):
    """Bad or missing operator configuration; message is path-only."""


@dataclass
class Config:
    bot_token: str
    workspace_roots: list[Path] = field(default_factory=list)
    default_repo: Path | None = None
    state_path: Path | None = None
    registry_path: Path | None = None
    dw_cli: list[str] | None = None
    agent_events_path: Path | None = None

    def resolved_state_path(self) -> Path:
        if self.state_path is not None:
            return self.state_path
        return DEFAULT_CONFIG_PATH.parent / "telegram-state.json"

    def resolved_agent_events_path(self) -> Path:
        if self.agent_events_path is not None:
            return self.agent_events_path
        return DEFAULT_CONFIG_PATH.parent / "agent-events.jsonl"


def _expand(raw: object) -> Path:
    return Path(os.path.expanduser(str(raw))).resolve()


def load_config(
    path: Path | None = None, env: dict[str, str] | None = None
) -> Config:
    path = path or DEFAULT_CONFIG_PATH
    env = os.environ if env is None else env
    doc: dict = {}
    if path.exists():
        try:
            parsed = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError, ValueError) as exc:
            raise ConfigError(f"unreadable config at {path}") from exc
        if not isinstance(parsed, dict):
            raise ConfigError(f"config at {path} is not a JSON object")
        doc = parsed
    token = str(env.get(TOKEN_ENV) or doc.get("bot_token") or "").strip()
    if not token:
        raise ConfigError(
            f"no bot token: set {TOKEN_ENV} or bot_token in {path}"
        )
    roots = [
        _expand(item)
        for item in (doc.get("workspace_roots") or [])
        if str(item).strip()
    ]
    dw_cli_raw = doc.get("dw_cli")
    dw_cli = (
        [str(item) for item in dw_cli_raw]
        if isinstance(dw_cli_raw, list) and dw_cli_raw
        else None
    )
    return Config(
        bot_token=token,
        workspace_roots=roots,
        default_repo=(
            _expand(doc["default_repo"]) if doc.get("default_repo") else None
        ),
        state_path=(
            _expand(doc["state_path"]) if doc.get("state_path") else None
        ),
        registry_path=(
            _expand(doc["registry_path"])
            if doc.get("registry_path")
            else None
        ),
        dw_cli=dw_cli,
        agent_events_path=(
            _expand(doc["agent_events_path"])
            if doc.get("agent_events_path")
            else None
        ),
    )
